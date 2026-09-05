"""Bounded same-level positive-recovery repair after the binary-loss failure."""
from __future__ import annotations
import argparse, copy, json, time
from pathlib import Path
import train_m2_r1 as tr
import flavor_m2_r1 as rt
from run_m2_r1 import OUT, ROOT, read, save, freeze, old_s, enrich, compact_summary, comparison, scope_row


def run(owner):
    cfg=freeze(owner); dst=owner/'revisions/r1'
    prereg=dst/'conditional_plan.private.json'
    if prereg.exists(): plan=read(prereg)
    else:
        plan={'registered_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
            'trigger':'Binary positive-only layered recovery regressed in D0 CV; preserve that failure.',
            'loss':'layered_conditional','C':[0.01,0.1],
            'bank':'Frozen old M2 per-fold question bank; old candidate vocabulary, episodes, split and targets.',
            'decision_metric':'grouped development NDCG@5; retain all models; no historical tuning',
            'changes':'Only recovery objective compared with M2_R1_FIXED_LAYERED_LOCKED at C=.01; C=.1 is separate regularization ablation.'}
        save(prereg,plan)
        cfg['initial_plan_hash']=cfg.get('initial_plan_hash',old_s.digest(cfg))
        cfg['bounded_followup_after_failure']=plan
        save(OUT/'experiment_config.json',cfg)
    manifest=old_s.digest([cfg['D0'],plan])
    records=read(owner/'recovery_records.json');dev=[r for r in records if r['split']=='DEVELOPMENT']
    historic=[r for r in records if r['split']=='HISTORICAL_REGRESSION'];folds=read(dst/'D0_folds.private.json')
    rows_by={}; fitlog=[]
    for C in plan['C']:
        label='M2_R1_CONDITIONAL_C'+str(C); rows=[]
        for fold in range(3):
            path=dst/f'cv/{label}_fold{fold}.model.json'
            train=[r for r in dev if folds[r['group_id']]!=fold];held=[r for r in dev if folds[r['group_id']]==fold]
            old=read(owner/f'cv/M2_JOINT_fold{fold}.model.json')
            if path.exists(): b=read(path)
            else:
                b,rec=tr.fit(train,manifest,C=C,vocabulary=old['candidate_vocabulary'],tag=label+':fold'+str(fold),bank_override=old['question_bank'],loss_mode='layered_conditional')
                b['experiment_variant']=label;save(path,b)
            fitlog.append({'variant':label,'fold':fold,**b['fit_receipt']})
            for r in held:
                row=enrich(tr.evaluate_record(r,b),r,rt,b);row['model']=label;row['fold']=fold;rows.append(row)
            print(json.dumps({'phase':'conditional','model':label,'fold':fold,'NDCG5':compact_summary(rows)['ndcg5']}),flush=True)
        rows_by[label]=rows;save(dst/f'cv/{label}.private.json',rows)
    chosen=max(rows_by,key=lambda x:compact_summary(rows_by[x])['ndcg5'])
    C=float(chosen.split('_C')[-1]);oldfull=read(owner/'models/M2_JOINT.model.json')
    path=dst/f'models/{chosen}.model.json'
    if path.exists(): b=read(path)
    else:
        b,rec=tr.fit(dev,manifest,C=C,vocabulary=oldfull['candidate_vocabulary'],tag=chosen+':all-development',bank_override=oldfull['question_bank'],loss_mode='layered_conditional')
        b['experiment_variant']=chosen;save(path,b)
    fitlog.append({'variant':chosen,'fold':'ALL_DEVELOPMENT',**b['fit_receipt']})
    hist=[enrich(tr.evaluate_record(r,b),r,rt,b) for r in historic]
    save(dst/f'cv/{chosen}_historical.private.json',hist);save(dst/'conditional_fit_log.private.json',fitlog)
    binary=read(dst/'cv/M2_R1_FIXED_LAYERED_LOCKED.private.json');legacy=read(dst/'cv/M2_R1_FIXED_LEGACY_LOCKED.private.json');old=read(dst/'cv/M2_JOINT_REPRODUCED.private.json')
    metrics=read(OUT/'metrics.json')
    metrics['conditional_recovery_repair']={'models':{k:compact_summary(v) for k,v in rows_by.items()},
        'same_C_minus_binary':comparison(rows_by['M2_R1_CONDITIONAL_C0.01'],binary),
        'selected_minus_semantic_legacy':comparison(rows_by[chosen],legacy),
        'selected_minus_old':comparison(rows_by[chosen],old),
        'selected_model':chosen,'selected_C':C,'historical':compact_summary(hist),'fit_count':len(fitlog),
        'all_variants_retained':True,'original_binary_failure_unchanged':True}
    save(OUT/'metrics.json',metrics)
    save(dst/'conditional_selection.private.json',{'model':chosen,'C':C,'loss_mode':'layered_conditional','bank':'legacy_locked',
        'model_file':str(path),'manifest_hash':manifest,'fit_count':len(fitlog)})
    return metrics['conditional_recovery_repair']


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--owner-dir',type=Path,required=True)
    print(json.dumps(run(p.parse_args().owner_dir)),flush=True)
