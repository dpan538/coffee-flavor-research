"""Reuse the native context model; new compact per-coffee sensitivity receipt."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from collections import defaultdict
import numpy as np
from flavor_context import VARIANTS, fit_context, predict_context, NATIVE_ROASTS
from prepare_sequential_data import numerical
from run_m2_r1 import OUT, read, save, tsv


def run(owner):
    data=numerical(owner)['datasets']
    extra=owner/'revisions/r1/context_records.private.json'
    if extra.exists():
        # Only source-native, rights-admitted complete matrices prepared by source adapter.
        for name,rows in read(extra).items():
            if name in data: raise ValueError('OLD_DATASET_OVERWRITE')
            data[name]=rows
    rows_out=[]; models={}; fits=0
    for dataset,rows in data.items():
        groups=sorted({r['group_id'] for r in rows})
        if len(groups)<2:
            rows_out.append({'dataset':dataset,'groups':len(groups),'status':'NOT_ESTIMABLE',
                             'reason':'No independent coffee group available to train and hold out.'})
            continue
        for group in groups:
            train=[r for r in rows if r['group_id']!=group]
            held=[r for r in rows if r['group_id']==group]
            baselines={}
            for variant in VARIANTS:
                model=fit_context(train,variant); fits+=1
                models[dataset+':'+variant+':'+str(groups.index(group))]=model
                losses=[]; altered_losses=defaultdict(list)
                for r in held:
                    target=np.array(r['targets']); scale=np.array(model['scaler_parameters']['scale'])
                    pred=np.array(predict_context(r,model)); losses.append(float(np.mean(np.abs((pred-target)/scale))))
                    for mode in ['c0_other','c1_other','both']:
                        alt=dict(r); changed=False
                        if mode in ['c0_other','both']:
                            vals=sorted({x['c0'] for x in train if x['c0'] and x['c0']!=r['c0']})
                            if vals: alt['c0']=vals[0]; changed=True
                        if mode in ['c1_other','both']:
                            vals=sorted({x['source_roast'] for x in train if x['source_roast'] and x['source_roast']!=r['source_roast']})
                            if vals and r['source_roast']: alt['source_roast']=vals[0]; changed=True
                        if changed:
                            p=np.array(predict_context(alt,model))
                            altered_losses[mode].append(float(np.mean(np.abs((p-target)/scale))))
                loss=float(np.mean(losses)); baselines[variant]=loss
                rows_out.append({'dataset':dataset,'model':variant,'groups':len(groups),
                    'held_group_index':groups.index(group),'held_conditions':len(held),
                    'stage':'CONTEXT_ONLY_SOURCE_NATIVE','standardized_mae':loss,
                    'delta_from_base':loss-baselines['C_BASE'],
                    **{k+'_error_increase':float(np.mean(v))-loss for k,v in altered_losses.items()},
                    'status':'INCONCLUSIVE','scope':'Source-native aggregate; per-group results, no small-n confidence claim'})
        for stage in ['INITIAL_EXTRACTION','FOUNDATION_CHECK','FINAL_RESULT']:
            rows_out.append({'dataset':dataset,'groups':len(groups),'stage':stage,'status':'NOT_ESTIMABLE',
                'reason':'No verified production seven-bin C1 + independent stage answers + common specific targets; source-native labels not substituted.'})
    save(owner/'revisions/r1/models/context_native.model.json',models)
    tsv(OUT/'context_effects.tsv',rows_out)
    result={'actual_fits':fits,'datasets':len(data),'per_group_table':'context_effects.tsv',
            'production_C1_to_leaf':'NOT_ESTIMABLE','source_native_small_groups':'Report group deltas/range, not robust generalization.',
            'means':{dataset:{variant:float(np.mean([r['standardized_mae'] for r in rows_out if r.get('dataset')==dataset and r.get('model')==variant]))
                  for variant in VARIANTS} for dataset in data if len({r['group_id'] for r in data[dataset]})>=2}}
    metrics=read(OUT/'metrics.json'); metrics['context']=result; save(OUT/'metrics.json',metrics)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--owner-dir',type=Path,required=True)
    print(json.dumps(run(p.parse_args().owner_dir)))
