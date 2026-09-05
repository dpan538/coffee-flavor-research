#!/usr/bin/env python3
"""M2 R1: isolated, reloadable repair and data comparisons on frozen groups."""
from __future__ import annotations
import argparse, copy, csv, hashlib, json, platform, subprocess, time
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
import flavor_sequential as old_s
import train_sequential as old_t
import evaluate_sequential_v2 as old_e
from run_sequential_v2 import paired, mean

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'db/data/backend-sequential-model-v2/revisions/r1'
BASE_SHA = 'fb29b8c80aae29b9dacce039d728d9dc1efa5769'
SEED = 20260905


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tsv(path, rows):
    old_e.write_tsv(path, rows)


def compact_summary(rows):
    keys = ['ndcg5','recall5','recall8','direct_retention8','raw_direct_retention8',
            'coverage','candidate_target_coverage','latency_ms','question_count','option_budget']
    return {'records':len(rows), 'groups':len({r['group_id'] for r in rows}),
            'labelled_records':sum(r.get('ndcg5') is not None for r in rows),
            **{k:mean(rows,k) for k in keys},
            'per_source':{src:{'groups':len({r['group_id'] for r in rows if r['source_family']==src}),
                **{k:mean([r for r in rows if r['source_family']==src],k) for k in keys}}
                for src in sorted({r['source_family'] for r in rows})}}


def comparison(a,b,key='ndcg5'):
    value=paired(a,b,key)
    if value['status']=='IMPROVEMENT_SUPPORTED': value['status']='PROXY_IMPROVEMENT_SUPPORTED'
    value['inference']='Development selection or historical record proxy; not independent product efficacy.'
    return value


def freeze(owner):
    dst=owner/'revisions/r1'
    paths=[owner/'recovery_records.json', ROOT/'db/data/backend-sequential-model-v2/dataset_manifest.json']
    paths+=list((owner/'models').glob('*.json'))+list((owner/'cv').glob('*.model.json'))
    prior=owner.parent/'backend-model-20260905'
    paths+=list((prior/'models').glob('*.json'))
    paths+=list((ROOT/'db/data/backend-sequential-model-v2').glob('*'))
    frozen={str(p):sha(p) for p in paths if p.is_file()}
    config_path=OUT/'experiment_config.json'
    if config_path.exists():
        cfg=read(config_path)
        for path,h in cfg['D0']['immutable_file_sha256'].items():
            if sha(path)!=h: raise ValueError('FROZEN_D0_CHANGED:'+path)
        return cfg
    records=read(owner/'recovery_records.json')
    dev=[r for r in records if r['split']=='DEVELOPMENT']
    folds=old_t.split_groups(dev)
    cfg={
      'experiment_id':'M2_R1_REPAIR_FOUNDATION_20260905','lineage':'M2 revision; no M3',
      'preregistered_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
      'code_baseline_sha':BASE_SHA,'remote_research_sha':BASE_SHA,
      'remote_main_sha':'e4eced41e2233c76c4645287fba2ecedddd03561',
      'dirty_main_sha':'1755915d3918013c8bd7c5f744e5ce8a0e972167',
      'dirty_main_policy':'Read only; no reset, stash, edits or commits.',
      'seed':SEED,'group_folds':3,'inner_feature_folds':2,
      'D0':{'records':len(records),'groups':len({r['group_id'] for r in records}),
            'development_records':len(dev),'development_groups':len(folds),
            'historical_groups':len({r['group_id'] for r in records if r['split']=='HISTORICAL_REGRESSION'}),
            'split_sha256':old_s.digest(folds),'immutable_file_sha256':frozen},
      'stages':[
        {'id':'repair_checkpoint','data':'D0','bank':'old train-fold bank locked',
         'targets':'old visible_episode fixed hidden recovery','C':'old selected C',
         'models':['M2_JOINT','M2_R1_FIXED_LEGACY_LOCKED','B2'],
         'purpose':'Isolate repaired evidence/features from catalog and objective changes'},
        {'id':'layered_loss','data':'D0','bank':'same old bank',
         'models':['M2_R1_FIXED_LEGACY_LOCKED','M2_R1_FIXED_LAYERED_LOCKED'],
         'purpose':'Isolate supervision masks and separate attribute/leaf/recovery objectives'},
        {'id':'complementary_Q01','data':'D0','models':['M2_R1_FIXED_LAYERED_LOCKED','M2_R1_FIXED'],
         'bank':'Only initial pair selected from training-side complementarity; correction pool fixed'},
        {'id':'foundation','data':'D0','slot':'Q3', 'optional_control_slot':'Q4 only if preregistered before run',
         'models':['V0_FIXED','V1_FOUNDATION_ORDINARY','V2_FOUNDATION_CHECK'],
         'representations':['explicit_attributes','nmf_projection','supervised_soft_profile'],
         'targets':'Group split before deterministic A/B/T; fixed T excluded from all question/answer generation',
         'budget':'Equal question count and actually offered option count; Q0-Q5 max; once check'},
        {'id':'expansion','models':['M2_R1_FIXED_D0','M2_R1_FIXED_D0_D1'],
         'locked':['candidate vocabulary','question bank','hyperparameters','target hierarchy','denominator'],
         'new_confirmation':'source+group hash 20% before examining predictions; never fit on confirmation'}],
      'bounded_search':{'C':[0.01,0.1,1.0],'foundation_rank':[2,3],
                        'foundation_fusion_strength':[0.0,0.15],
                        'policy':'Sequential stages, no Cartesian search; CV choice never historical or confirmation.'},
      'loss_policy':'Separate masked attribute, leaf, positive recovery and consistency tasks. Missing is not negative.',
      'metrics':['NDCG@5','Recall@5','Recall@8','raw/direct retention','coverage','source/group deltas'],
      'scope_policy':'Full, fine common-vocabulary, and broad scopes reported separately; no-output rows retained.',
      'M1_fairness':'Frozen old M1 evaluated on 17 historical groups only; do not evaluate old training groups as CV holdouts.',
      'feedback':'F0/F1/F2; selected exposure-only; repeated/specificization/new evidence separated; once then terminal',
      'context':'Preserve native C0/C1 experiments; source roast labels never fabricate seven production bins.',
      'real_answers':'NOT_EVALUATED','weights_release':False,'backend_default':'B2 (unchanged pending evidence)'}
    save(config_path,cfg)
    save(dst/'D0_folds.private.json',folds)
    save(dst/'D0_snapshot.private.json',{'records':records,'file_sha256':frozen})
    print(json.dumps({'phase':'frozen','records':len(records),'development_groups':len(folds)}),flush=True)
    return cfg


def scope_row(row, vocabulary=None, kind='full'):
    x=copy.deepcopy(row)
    ep=x['episode']; targets=dict(ep['relevance'])
    if vocabulary is not None: targets={c:v for c,v in targets.items() if c in vocabulary}
    if kind=='fine': targets={c:v for c,v in targets.items() if c.startswith('sensory.')}
    if kind=='broad': targets={c:v for c,v in targets.items() if not c.startswith('sensory.')}
    ranking=x['recovery_ranking']
    if vocabulary is not None: ranking=[c for c in ranking if c in vocabulary]
    if kind=='fine': ranking=[c for c in ranking if c.startswith('sensory.')]
    if kind=='broad': ranking=[c for c in ranking if not c.startswith('sensory.')]
    x.update(ndcg5=old_t.ndcg(ranking,targets) if targets else None,
             recall5=len(set(ranking[:5])&targets.keys())/len(targets) if targets else None,
             recall8=len(set(ranking[:8])&targets.keys())/len(targets) if targets else None)
    return x


def enrich(row, record, backend, bundle):
    row=copy.deepcopy(row)
    if 'episode' not in row: row['episode']=old_t.visible_episode(record)
    if 'state' in row:
        scores=row['state']['candidate_scores']
        raw=sorted(scores,key=lambda r:(-r['score'],r['candidate_id']))
        direct=set(row['state'].get('interpreted_evidence',{}).get('specific',[]))
        row['raw_direct_retention8']=len({r['candidate_id'] for r in raw[:8]}&direct)/len(direct) if direct else None
        row['raw_ranking']=[r['candidate_id'] for r in raw]
    return row


def reproduce(owner):
    cfg=freeze(owner); dst=owner/'revisions/r1'; records=read(owner/'recovery_records.json')
    folds=read(dst/'D0_folds.private.json')
    rows=[]; baselines=[]; failures=[]
    frozen={r['record_id']:r for r in read(owner/'cv/M2_JOINT.private.json')}
    for fold in range(3):
        b=read(owner/f'cv/M2_JOINT_fold{fold}.model.json')
        held=[r for r in records if r['group_id'] in folds and folds[r['group_id']]==fold]
        for r in held:
            row=enrich(old_t.evaluate_record(r,b),r,old_s,b)
            expected=frozen[r['record_id']]
            if row['ranking']!=expected['ranking'] or row['ndcg5']!=expected['ndcg5']:
                failures.append(r['record_id'])
            rows.append(row)
            for base in old_e.baselines(r,row,b):
                if base['model']=='B2':
                    base['episode']=row['episode']; baselines.append(base)
        print(json.dumps({'phase':'old_replay','fold':fold,'records':len(held)}),flush=True)
    if failures: raise ValueError('OLD_REPRODUCTION_MISMATCH:'+str(len(failures)))
    save(dst/'cv/M2_JOINT_REPRODUCED.private.json',rows)
    save(dst/'cv/B2_REPRODUCED.private.json',baselines)
    metrics=read(OUT/'metrics.json') if (OUT/'metrics.json').exists() else {}
    metrics['D0_old_reproduction']={'identical_ranking_and_utility':True,'M2_JOINT':compact_summary(rows),
        'B2':compact_summary(baselines),'basis':'Retained fold bundles; original grouped data, catalog and target partition.'}
    save(OUT/'metrics.json',metrics)
    return rows


def repair(owner):
    import train_m2_r1 as tr
    import flavor_m2_r1 as rt
    cfg=freeze(owner); dst=owner/'revisions/r1'; records=read(owner/'recovery_records.json')
    dev=[r for r in records if r['split']=='DEVELOPMENT']; historic=[r for r in records if r['split']=='HISTORICAL_REGRESSION']
    folds=read(dst/'D0_folds.private.json'); manifest_hash=cfg.get('initial_plan_hash',old_s.digest(cfg))
    oldC=read(ROOT/'db/data/backend-sequential-model-v2/metrics.json')['sequential']['selected_C']
    recipes=[('M2_R1_FIXED_LEGACY_LOCKED','legacy',False,oldC),
             ('M2_R1_FIXED_LAYERED_LOCKED','layered',False,oldC),
             ('M2_R1_FIXED','layered',True,oldC)]
    recipes += [('M2_R1_FIXED_C'+str(c),'layered',True,c) for c in cfg['bounded_search']['C'] if c!=oldC]
    rows_by={}; fitlog=[]
    for label,loss,new_pair,C in recipes:
        rows=[]; b2=[]
        for fold in range(3):
            train=[r for r in dev if folds[r['group_id']]!=fold]
            held=[r for r in dev if folds[r['group_id']]==fold]
            old=read(owner/f'cv/M2_JOINT_fold{fold}.model.json')
            path=dst/f'cv/{label}_fold{fold}.model.json'
            if path.exists():
                b=read(path)
                if b['data_manifest_hash']!=manifest_hash: raise ValueError('RETAINED_R1_MANIFEST_MISMATCH')
                rec=b['fit_receipt']
            else:
                begin=time.perf_counter()
                bank=copy.deepcopy(old['question_bank'])
                if new_pair:
                    preliminary=tr.make_bundle(train,'M2_R1_FIXED',manifest_hash,vocabulary=old['candidate_vocabulary'],tag='bank')
                    for key in ['initial_0','initial_1','initial_pair_selection']: bank[key]=preliminary['question_bank'][key]
                b,rec=tr.fit(train,manifest_hash,C=C,kind='M2_R1_FIXED',vocabulary=old['candidate_vocabulary'],
                              tag=label+':fold'+str(fold),bank_override=bank,loss_mode=loss)
                b['experiment_variant']=label
                save(path,b)
                rec={**rec,'seconds':time.perf_counter()-begin}
            fitlog.append({'model':label,'fold':fold,**rec})
            for r in held:
                row=enrich(tr.evaluate_record(r,b),r,rt,b); row['model']=label; row['fold']=fold
                rows.append(row)
                for base in old_e.baselines(r,row,b):
                    if base['model']=='B2': base['episode']=row['episode']; base['fold']=fold; b2.append(base)
            print(json.dumps({'phase':'repair_fit','model':label,'fold':fold,'C':C,'NDCG5':mean(rows,'ndcg5')}),flush=True)
        rows_by[label]=rows
        save(dst/f'cv/{label}.private.json',rows)
        save(dst/f'cv/{label}_B2.private.json',b2)
        save(dst/'fit_log.private.json',fitlog)
    candidate_labels=[r[0] for r in recipes if r[2]]
    selected=max(candidate_labels,key=lambda k:mean(rows_by[k],'ndcg5'))
    selected_recipe=next(x for x in recipes if x[0]==selected)
    hist={}; full_bundles={}
    oldfull=read(owner/'models/M2_JOINT.model.json')
    final_recipes=[recipes[0], recipes[1], selected_recipe]
    for label,loss,new_pair,C in final_recipes:
        path=dst/f'models/{label}.model.json'
        if path.exists(): b=read(path)
        else:
            bank=copy.deepcopy(oldfull['question_bank'])
            if new_pair:
                preliminary=tr.make_bundle(dev,'M2_R1_FIXED',manifest_hash,vocabulary=oldfull['candidate_vocabulary'],tag='bank-final')
                for key in ['initial_0','initial_1','initial_pair_selection']: bank[key]=preliminary['question_bank'][key]
            b,rec=tr.fit(dev,manifest_hash,C=C,kind='M2_R1_FIXED',vocabulary=oldfull['candidate_vocabulary'],
                         tag=label+':all-development',bank_override=bank,loss_mode=loss)
            b['experiment_variant']=label; save(path,b)
            fitlog.append({'model':label,'fold':'ALL_DEVELOPMENT',**rec})
        full_bundles[label]=b
        hist[label]=[enrich(tr.evaluate_record(r,b),r,rt,b) for r in historic]
        print(json.dumps({'phase':'historical','model':label,'NDCG5':mean(hist[label],'ndcg5')}),flush=True)
    save(dst/'cv/historical_r1.private.json',hist); save(dst/'fit_log.private.json',fitlog)
    oldrows=read(dst/'cv/M2_JOINT_REPRODUCED.private.json')
    metrics=read(OUT/'metrics.json')
    comparisons={'repair_legacy_minus_old':comparison(rows_by[recipes[0][0]],oldrows),
                 'layered_minus_legacy':comparison(rows_by[recipes[1][0]],rows_by[recipes[0][0]]),
                 'Q01_pair_only':comparison(rows_by['M2_R1_FIXED'],rows_by[recipes[1][0]]),
                 'selected_minus_old':comparison(rows_by[selected],oldrows)}
    b2rows=read(dst/f'cv/{selected}_B2.private.json')
    # Fine comparison uses common candidate scope from each TRAIN fold; full scope remains separately reported.
    common={fold:set(read(dst/f'cv/{selected}_fold{fold}.model.json')['candidate_vocabulary'])&set(old_e.baseline_bundle(read(dst/f'cv/{selected}_fold{fold}.model.json'))['vocabulary']) for fold in range(3)}
    selected_fine=[scope_row(r,common[r['fold']],'fine') for r in rows_by[selected]]
    b2fine=[scope_row(r,common[r['fold']],'fine') for r in b2rows]
    comparisons['selected_minus_B2_full']=comparison(rows_by[selected],b2rows)
    comparisons['selected_minus_B2_matched_fine']=comparison(selected_fine,b2fine)
    old_m1=read(owner.parent/'backend-model-20260905/models/M1.model.json')
    old_hist=[enrich(old_t.evaluate_record(r,oldfull),r,old_s,oldfull) for r in historic]
    hist_bases=defaultdict(list)
    for r,row in zip(historic,hist[selected]):
        for br in old_e.baselines(r,row,full_bundles[selected],old=old_m1):
            br['episode']=row['episode']; hist_bases[br['model']].append(br)
    common_hist=set(full_bundles[selected]['candidate_vocabulary'])&set(old_m1['vocabulary'])
    histmatched={k:[scope_row(r,common_hist,'fine') for r in v] for k,v in {**hist,**hist_bases,'M2_JOINT':old_hist}.items()}
    save(dst/'cv/historical_baselines_r1.private.json',dict(hist_bases))
    metrics['repair']={'models':{k:compact_summary(v) for k,v in rows_by.items()},'comparisons':comparisons,
        'selected_model':selected,'selected_C':selected_recipe[3],
        'matched_fine':{selected:compact_summary(selected_fine),'B2':compact_summary(b2fine)},
        'broad':{k:compact_summary([scope_row(r,kind='broad') for r in v]) for k,v in rows_by.items()},
        'historical_full':{k:compact_summary(v) for k,v in {**hist,**hist_bases,'M2_JOINT':old_hist}.items()},
        'historical_matched_fine':{k:compact_summary(v) for k,v in histmatched.items()},
        'historical_comparisons':{k:comparison(histmatched[selected],histmatched[k]) for k in ['B2','M1','M2_JOINT']},
        'independent_product_evaluation':'NOT_EVALUATED','selection_scope':'Grouped development CV, reused for selection; historical 17 groups never tune.',
        'M1_development':'NOT_EVALUATED: original M1 training overlaps D0 development; unchanged weights evaluated only on historical regression.',
        'fixed_model_path':str(dst/f'models/{selected}.model.json'), 'fit_count':len(fitlog)}
    save(OUT/'metrics.json',metrics)
    save(dst/'selection.private.json',{'model':selected,'C':selected_recipe[3],'recipe':selected_recipe,
        'development_score':mean(rows_by[selected],'ndcg5'),'model_file':str(dst/f'models/{selected}.model.json')})
    print(json.dumps({'phase':'repair_complete','selected':selected,'comparisons':comparisons}),flush=True)


def diagnostics(owner):
    import train_m2_r1 as tr
    import flavor_m2_r1 as rt
    dst=owner/'revisions/r1'; metrics=read(OUT/'metrics.json'); selection=read(dst/'selection.private.json')
    label=selection['model']; source_rows=read(dst/f'cv/{label}.private.json')
    records={r['record_id']:r for r in read(owner/'recovery_records.json')}
    stages=[]; responses=[]; feedback=[]; replay_checks=[]
    for fold in range(3):
        b=read(dst/f'cv/{label}_fold{fold}.model.json')
        held=[x for x in source_rows if x['fold']==fold]
        for row in held:
            record=records[row['record_id']]
            ep,states,answers=tr.trajectory(record,b)
            key={k:row[k] for k in ['record_id','group_id','source_family']}
            previous=None
            for i,st in enumerate(states):
                out=old_e.result_row(record,st,b,ep,'prefix')
                slot='CONTEXT' if i==0 else answers[i-1]['slot']
                stages.append({**key,'slot':slot,'ndcg5':out['ndcg5'],
                    'delta':out['ndcg5']-previous if previous is not None and out['ndcg5'] is not None else None,
                    'question_count':i,'option_budget':sum(len(a['shown_option_ids']) for a in answers[:i])})
                previous=out['ndcg5']
                if i:
                    a=answers[i-1]; before=np.asarray(states[i-1]['features']); after=np.asarray(st['features'])
                    responses.append({**key,'slot':slot,'selected':'|'.join(a['selected_option_ids']) or a['state'],
                        'has_selection':bool(a['selected_option_ids']),'feature_changed':bool(not np.allclose(before,after)),
                        'score_changed':bool(any(abs(x['score']-y['score'])>1e-10 for x,y in zip(sorted(st['candidate_scores'],key=lambda r:r['candidate_id']),sorted(states[i-1]['candidate_scores'],key=lambda r:r['candidate_id']))))})
            # Q1 on its own is a scoring diagnostic, not a new production path.
            q1only=copy.deepcopy(states[2]); del q1only['answers_by_question']['Q0']; q1only=rt.recompute(q1only,b)
            q1row=old_e.result_row(record,q1only,b,ep,'Q1_ONLY')
            stages.append({**key,'slot':'Q1_ONLY','ndcg5':q1row['ndcg5'],'question_count':1,'option_budget':4})
            full=states[-1]; pre=rt.finalize_result(full,b); ex=pre['exposure']
            if answers:
                replayed=rt.update_joint_state(full,answers[-1],b)
                replay_checks.append(np.allclose(full['features'],replayed['features']) and
                    [r['score'] for r in full['candidate_scores']]==[r['score'] for r in replayed['candidate_scores']])
            if not ex or not ex['eligible_for_final_comparison']: continue
            direct=set(rt.evidence(full,b)['confirmed']); broad=set(rt.evidence(full,b)['broad'])
            selected=[c for c in ex['candidate_ids'] if c in ep['visible']]
            selected_groups={'REPEATED_EXPLICIT':[c for c in selected if c in direct],
                'BROAD_TO_SPECIFIC':[c for c in selected if c not in direct and bool(set(b['candidate_attributes'].get(c,[]))&broad)],
                'NEW_VISIBLE_JUDGMENT':[c for c in selected if c not in direct and not set(b['candidate_attributes'].get(c,[]))&broad]}
            for evidence_type,choices in selected_groups.items():
                # Empty choice subsets retained; label-specific counts distinguish applicable cases.
                for mode in ['F0','F1','F2']:
                    st=full if mode=='F0' else rt.apply_final_comparison(full,ex['candidate_ids'],choices,b,
                        feedback_source='SIMULATED',generation_version=b['bundle_id'],mode=mode)
                    out=old_e.result_row(record,st,b,ep,mode)
                    feedback.append({**key,'model':mode,'feedback_type':evidence_type,'selected_count':len(choices),
                        'ndcg5':out['ndcg5'],'recall8':out['recall8'],'coverage':out['coverage'],
                        'large_discrepancy_proxy':row['ndcg5'] is not None and row['ndcg5']<0.5,
                        'exposure_size':len(ex['candidate_ids']),'generation_version':b['bundle_id'],
                        'evidence_scope':'DERIVED_RECORD_PROXY; visible-only, T never selects feedback',
                        'score_delta_max':max(abs(x['score']-y['score']) for x,y in zip(sorted(st['candidate_scores'],key=lambda r:r['candidate_id']),sorted(full['candidate_scores'],key=lambda r:r['candidate_id']))),
                        'repeated_score_unchanged':True if not choices else None})
    save(dst/'stage_diagnostics.private.json',stages); save(dst/'response_patterns.private.json',responses)
    save(dst/'feedback_diagnostics.private.json',feedback)
    stages_summary={slot:{'records':sum(x['slot']==slot for x in stages),
                        'ndcg5':mean([x for x in stages if x['slot']==slot],'ndcg5'),
                        'delta':mean([x for x in stages if x['slot']==slot],'delta')}
                    for slot in sorted({x['slot'] for x in stages})}
    response_summary={slot:{'effective_selection_rate':mean([x for x in responses if x['slot']==slot],'has_selection'),
        'feature_change_rate':mean([x for x in responses if x['slot']==slot],'feature_changed'),
        'score_change_rate':mean([x for x in responses if x['slot']==slot],'score_changed'),
        'patterns':dict(Counter(x['selected'] for x in responses if x['slot']==slot))}
        for slot in sorted({x['slot'] for x in responses})}
    # Conditional entropy is empirical proxy information, not mutual information with hidden truth.
    q0={x['record_id']:x['selected'] for x in responses if x['slot']=='Q0'}
    q1={x['record_id']:x['selected'] for x in responses if x['slot']=='Q1'}
    ids=sorted(q0.keys()&q1.keys())
    conditional=tr.entropy([(q0[i],q1[i]) for i in ids])-tr.entropy([q0[i] for i in ids])
    fb_summary={}
    for evidence_type in sorted({x['feedback_type'] for x in feedback}):
        for subset in ['ALL','LARGE_DISCREPANCY_PROXY']:
            rr=[r for r in feedback if r['feedback_type']==evidence_type and r['selected_count'] and (subset=='ALL' or r['large_discrepancy_proxy'])]
            bymode={mode:[r for r in rr if r['model']==mode] for mode in ['F0','F1','F2']}
            fb_summary[evidence_type+':'+subset]={'models':{mode:compact_summary(v) for mode,v in bymode.items()},
                'F2_minus_F0':comparison(bymode['F2'],bymode['F0']), 'F2_minus_F1':comparison(bymode['F2'],bymode['F1']),
                'score_change_max_F2':max((r['score_delta_max'] for r in bymode['F2']),default=None)}
    metrics['question_diagnostics']={'prefixes':stages_summary,'response_analysis':response_summary,
        'Q1_conditional_response_entropy_given_Q0_bits':conditional,
        'interpretation':'Record-derived visible-answer patterns; coverage and fitted feature effects, not measured user question utility.'}
    metrics['feedback_r1']={'groups':fb_summary,'real_feedback':'NOT_EVALUATED',
        'large_discrepancy_definition':'Fixed exploratory proxy hidden-recovery NDCG@5 < 0.5; not an observed user complaint.',
        'exposure_and_generation_saved':True,'targets_fixed':True,
        'duplicate_replay_cases':len(replay_checks),'duplicate_replay_all_zero_change':all(replay_checks)}
    save(OUT/'metrics.json',metrics)
    if not all(replay_checks): raise AssertionError('DUPLICATE_EVIDENCE_GAIN')
    print(json.dumps({'phase':'diagnostics','Q1_conditional_bits':conditional,'replay_zero':all(replay_checks)}),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--owner-dir',type=Path,required=True)
    p.add_argument('--phase',choices=['freeze','reproduce','repair','diagnostics'],required=True)
    a=p.parse_args()
    globals()[a.phase](a.owner_dir)


if __name__=='__main__': main()
