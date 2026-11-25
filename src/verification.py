import numpy as np
import pandas as pd
from config import CFG
from src.des import simulate,verify_invariants
from src.calibration import INPUTS
from src.common import save,status

def verification(d,cfg=CFG):
    from tests.test_des import hand
    p,tr=simulate(hand(),1,collect_trace=True);save(p,'verification/hand_results.csv');save(tr,'verification/hand_trace.csv')
    status(['4.1','4.2','4.3','4.4','4.5','5.1'],'src/des.py; src/metrics.py; docs/des_pseudocode.md; outputs/verification/hand_trace.csv; pytest tests/test_des.py')
    rows=[];predictions=[]
    for (s,r),g in d.groupby(['Scenario','RunID']):
        c=int(g.NumDoctors.iloc[0]);peak=float(g.PeakLimit.iloc[0]);p,_=simulate(g[INPUTS],c,1,peak)
        verify_invariants(p,c,1,cfg.tolerance);p['Scenario']=s;p['RunID']=r
        predictions.append(p[['Scenario','RunID','PatientID','DocWaitTime','MedWaitTime','TotalTimeInHospital']])
    merged=d.merge(pd.concat(predictions),on=['Scenario','RunID','PatientID'],validate='one_to_one',suffixes=('_source','_sim'))
    mismatch=np.zeros(len(merged),bool)
    for metric in ['DocWaitTime','MedWaitTime','TotalTimeInHospital']:
        e=merged[metric+'_sim']-merged[metric+'_source'];merged[metric+'_error']=e;mismatch|=abs(e)>cfg.tolerance
        for s,g in merged.groupby('Scenario'):
            e=g[metric+'_error'];rows.append({'Scenario':s,'metric':metric,'n':len(g),'exact_matches':int((e==0).sum()),'tolerance_matches':int((abs(e)<=cfg.tolerance).sum()),'max_abs_error':abs(e).max(),'mean_error':e.mean(),'sd_error':e.std(),'p90_abs_error':abs(e).quantile(.9)})
    save(pd.DataFrame(rows),'verification/verification_summary.csv');save(merged[mismatch],'verification/mismatches.csv')
    save(merged.groupby(['Scenario','RunID'])[['DocWaitTime_source','DocWaitTime_sim','MedWaitTime_source','MedWaitTime_sim']].mean().reset_index(),'verification/scenario_consistency.csv')
    assert not mismatch.any(),f'{mismatch.sum()} source reconstruction mismatches; diagnose before experiments'
    status(['5.2','5.3','5.4'],'outputs/verification/verification_summary.csv; mismatches.csv; scenario_consistency.csv; 300 runs invariant checks')
    return pd.DataFrame(rows)
