"""Week 4 output analysis; Week 6 matched replication inference and decisions."""
import numpy as np
import pandas as pd
from src.metrics import ci,quant
from src.common import save,status
from config import CFG
KEYS=['experiment','condition','doctors','pharmacy_counters']
CORE=['p90_doc_wait','mean_doc_wait','mean_pharmacy_wait','mean_total_time','p90_peak','p90_nonpeak','p90_priority1','p90_priority2','p90_priority3']

def summarize(runs):
    metadata={'RunID','run_seed','input_hash','config_hash','policy','experiment','condition','doctors','pharmacy_counters'}
    rows=[]
    for key,g in runs.groupby(KEYS):
        for metric in [x for x in g.select_dtypes('number').columns if x not in metadata]:rows.append({**dict(zip(KEYS,key)),'metric':metric,**ci(g[metric])})
    return pd.DataFrame(rows)

def paired(runs):
    diffs=[];rows=[]
    for (exp,cond),g in runs.groupby(['experiment','condition']):
        for new,ref in [(3,2),(4,2),(4,3)]:
            a=g[g.doctors==new].set_index('RunID');b=g[g.doctors==ref].set_index('RunID');assert a.index.equals(b.index)
            assert (a.input_hash==b.input_hash).all()
            for metric in CORE:
                delta=a[metric]-b[metric];assert np.isclose(delta.mean(),a[metric].mean()-b[metric].mean(),equal_nan=True)
                for r,v in delta.items():diffs.append({'experiment':exp,'condition':cond,'comparison':f'{new}-{ref}','metric':metric,'RunID':r,'difference':v,'input_hash':a.loc[r,'input_hash']})
                denom=b[metric].mean();rows.append({'experiment':exp,'condition':cond,'comparison':f'{new}-{ref}','metric':metric,**ci(delta),'percent_change':100*delta.mean()/denom if denom else np.nan,'percent_defined':bool(denom)})
    return pd.DataFrame(diffs),pd.DataFrame(rows)

def targets(runs,patients,cfg):
    rows=[]
    for key,g in runs.groupby(KEYS):
        mask=np.ones(len(patients),bool)
        for col,val in zip(KEYS,key):mask &= (patients[col].to_numpy()==val)
        pooled=quant(patients.loc[mask,'DocWaitTime'])
        for target in cfg.targets:
            s=ci(g[f'sl_{target:g}']);att=ci(g[f'attain_{target:g}'])
            rows.append({**dict(zip(KEYS,key)),'target':target,'n':len(g),'run_attainment':att['mean'],'service_level':s['mean'],'sl_lo':s['lo'],'sl_hi':s['hi'],'pooled_p90_context':pooled})
    return pd.DataFrame(rows)

def decisions(summary,cfg):
    rows=[]
    for (exp,cond),g in summary[summary.metric=='p90_doc_wait'].groupby(['experiment','condition']):
        g=g.sort_values('doctors')
        for target in cfg.targets:
            point=g[g['mean']<=target];supported=g[g.hi<=target];uncertain=g[(g.lo<=target)&(g.hi>target)]
            rows.append({'experiment':exp,'condition':cond,'target':target,'point_choice':str(int(point.doctors.iloc[0])) if len(point) else 'none',
               'supported_choice':str(int(supported.doctors.iloc[0])) if len(supported) else 'none','uncertain_candidates':','.join(uncertain.doctors.astype(str)) or 'none',
               'rule':'minimum scheduled doctor cost; second counter performance only'})
    return pd.DataFrame(rows)

def analyze_main(runs,patients,cfg=CFG):
    s=summarize(runs);save(s,'tables/policy_summary.csv')
    save(s[s.metric.str.contains('priority')],'tables/priority_summary.csv');save(s[s.metric.str.contains('peak|nonpeak')],'tables/peak_summary.csv')
    diffs,p=paired(runs);save(diffs,'tables/paired_differences.csv');save(p,'tables/paired_ci.csv')
    target=targets(runs,patients,cfg);save(target,'tables/target_achievement.csv')
    status(['8.1','8.2','8.3'],'outputs/tables/policy_summary.csv; priority_summary.csv; peak_summary.csv; paired_differences.csv; paired_ci.csv; target_achievement.csv; known-vector test')
    return s,p,target

def analyze_confirmation(runs,patients,cfg=CFG):
    s=summarize(runs);save(s,'tables/confirmation_summary.csv');_,p=paired(runs);save(p,'tables/confirmation_paired_ci.csv');save(targets(runs,patients,cfg),'tables/confirmation_targets.csv')
    status(['8.4'],'outputs/tables/confirmation_summary.csv; confirmation_paired_ci.csv; root=93410; all 3 candidates; unresolved target-straddling cases explicitly flagged')
    return s

def analyze_sensitivity(runs,patients,cfg=CFG):
    s=summarize(runs);save(s,'tables/sensitivity_summary.csv');decision=decisions(s,cfg);save(decision,'tables/decision_matrix.csv')
    save(targets(runs,patients,cfg),'tables/sensitivity_targets.csv');dd,pc=paired(runs);save(pc,'tables/sensitivity_paired_ci.csv')
    status(['9.3'],'outputs/tables/sensitivity_summary.csv; decision_matrix.csv; sensitivity_targets.csv; sensitivity_paired_ci.csv')
    rows=[]
    e=runs[runs.experiment=='empirical'];v=e.pivot(index='RunID',columns=['condition','doctors'],values='p90_doc_wait')
    for new,ref in [(3,2),(4,2),(4,3)]:
        delta=(v[('doctor_slow',new)]-v[('doctor_slow',ref)])-(v[('base',new)]-v[('base',ref)])
        rows.append({'comparison':f'{new}-{ref}','effect':'paired difference-in-differences (unhalved interaction contrast)','metric':'p90_doc_wait',**ci(delta)})
    save(pd.DataFrame(rows),'tables/factorial_interaction.csv');status(['9.4'],'outputs/tables/factorial_interaction.csv; existing 3x2 cells reused')
    return s,decision

def costs(runs,summary,cfg=CFG):
    rows=[]
    for key,g in runs.groupby(KEYS):
        exp,cond,c,k=key;scheduled=c*cfg.doctor_wage*cfg.horizon/60
        base=runs[(runs.experiment==exp)&(runs.condition==cond)&(runs.doctors==2)]
        rows.append({**dict(zip(KEYS,key)),'scheduled_cost':scheduled,'extra_vs_2':(c-2)*cfg.doctor_wage*cfg.horizon/60,
            'p90_reduction_vs_2':base.p90_doc_wait.mean()-g.p90_doc_wait.mean(),'mean_doc_overtime':g.doc_overtime.mean(),'mean_pharmacy_overtime':g.pharmacy_overtime.mean(),
            'fraction_work_after_H':g.work_after_H.mean(),'fraction_arrival_after_H':(g.arrivals_after_H>0).mean(),'mean_last_arrival':g.last_arrival.mean(),
            'mean_last_doc_end':g.last_doc_end.mean(),'mean_last_departure':g.last_departure.mean(),
            **{f'busy_time_cost_premium_{f:g}':scheduled+f*cfg.doctor_wage*g.doc_overtime.mean()/60 for f in cfg.overtime_premiums}})
    table=pd.DataFrame(rows);save(table,'tables/cost_summary.csv')
    wages=pd.DataFrame([{'wage':cfg.doctor_wage*f,'doctors':c,'scheduled_cost':c*cfg.doctor_wage*f*cfg.horizon/60} for f in cfg.wage_factors for c in cfg.doctors]);save(wages,'tables/wage_sensitivity.csv')
    assert all(g.sort_values('doctors').scheduled_cost.is_monotonic_increasing for _,g in wages.groupby('wage'))
    d=decisions(summary,cfg);rec=d[d.target==cfg.target].copy();save(rec,'tables/recommendation.csv')
    status(['10.1','10.2','10.3'],'outputs/tables/cost_summary.csv; wage_sensitivity.csv; recommendation.csv; explicit positive-wage ranking check')
    return table,rec
