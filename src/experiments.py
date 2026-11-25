import numpy as np
import pandas as pd
from config import CFG
from src.inputs import base_draws,generate,input_hash
from src.des import simulate,verify_invariants
from src.calibration import INPUTS
from src.metrics import metrics
from src.common import save,status,write_json

def generate_inputs(model,cfg=CFG):
    draws,ledger=base_draws(cfg.root_seed,cfg.replications,cfg.n_patients)
    confirm,cl=base_draws(cfg.confirmation_seed,cfg.replications,cfg.n_patients)
    save(pd.concat([ledger,cl]),'experiments/seed_ledger.csv')
    urows=[];tables={}
    for name,us,root in [('main',draws,cfg.root_seed),('confirmation',confirm,cfg.confirmation_seed)]:
        for r,u in enumerate(us,1):
            x=pd.DataFrame(u,columns=['u_arrival','u_priority','u_doctor','u_pharmacy']);x['RunID']=r;x['root_seed']=root;x['PatientID']=np.arange(1,len(u)+1);urows.append(x)
            tables[(name,r)]=generate(u,model,cfg)
    save(pd.concat(urows),'experiments/base_uniforms.csv.gz')
    save(pd.concat([p.assign(RunID=r,experiment=name) for (name,r),p in tables.items()]),'experiments/generated_base_inputs.csv.gz')
    assert len({input_hash(p) for p in tables.values()})==2*cfg.replications
    aa,_=base_draws(cfg.root_seed,cfg.replications,cfg.n_patients)
    assert all(np.array_equal(x,y) for x,y in zip(aa,draws))
    status(['6.1'],'outputs/experiments/seed_ledger.csv; base_uniforms.csv.gz; generated_base_inputs.csv.gz')
    fit=[];gaps=[]
    for kind in ['empirical','poisson']:
        for r,u in enumerate(draws,1):
            p=generate(u,model,cfg,kind);t=p.ArrivalTime.to_numpy();gap=np.diff(np.r_[0,t])
            fit.append({'model':kind,'RunID':r,'peak_count':int((t<=cfg.peak_limit).sum()),'last_arrival':t[-1],'gap_mean':gap.mean(),'gap_sd':gap.std(ddof=1),'priority1':(p.Priority==1).mean(),'priority2':(p.Priority==2).mean(),'priority3':(p.Priority==3).mean(),'doctor_mean':p.DocServiceTime.mean(),'pharmacy_mean':p.MedServiceTime.mean()})
            gaps.append(pd.DataFrame({'model':kind,'RunID':r,'gap':gap,'previous':np.r_[0,t[:-1]]}))
    save(pd.DataFrame(fit),'data/generated_input_fit.csv');save(pd.concat(gaps),'data/generated_gaps.csv.gz')
    status(['6.2','6.3'],'outputs/data/generated_input_fit.csv; generated_gaps.csv.gz; tests/test_inputs.py')
    return draws,confirm,tables

def execute(p,c,k,experiment,condition,r,seed,cfg):
    h=input_hash(p);q,_=simulate(p,c,k,cfg.peak_limit,time_decimals=cfg.time_decimals);assert input_hash(p)==h and input_hash(q)==h
    verify_invariants(q,c,k,cfg.tolerance)
    meta={'doctors':c,'pharmacy_counters':k,'experiment':experiment,'condition':condition,'RunID':r,'policy':f'{c}D_{k}P','run_seed':seed,'input_hash':h,'config_hash':cfg.digest()}
    q=q.assign(**meta)
    return q,{**meta,**metrics(q,c,k,cfg)}

def main_experiments(b,tables,cfg=CFG):
    allrows=[];allpatients=[]
    for name in ['replay','empirical']:
        rows=[];patients=[]
        for r in range(1,cfg.replications+1):
            p=b[b.RunID==r][INPUTS].copy() if name=='replay' else tables[('main',r)]
            for c in cfg.doctors:
                q,row=execute(p,c,cfg.pharmacy_counters,name,'base',r,f'original:{r}' if name=='replay' else f'{cfg.root_seed}:{r-1}',cfg);rows.append(row);patients.append(q)
        frame=pd.DataFrame(rows);patientframe=pd.concat(patients,ignore_index=True)
        assert len(frame)==cfg.replications*len(cfg.doctors) and len(patientframe)==len(frame)*cfg.n_patients
        assert frame.groupby('RunID').input_hash.nunique().eq(1).all()
        prefix='replay' if name=='replay' else 'main'
        save(frame,f'experiments/{prefix}_run_results.csv');save(patientframe,f'experiments/{prefix}_patient_results.csv.gz')
        allrows.append(frame);allpatients.append(patientframe)
    status(['7.1','7.2','7.3'],'outputs/experiments/main_run_results.csv; replay_run_results.csv; corresponding *_patient_results.csv.gz; row/hash assertions')
    return pd.concat(allrows,ignore_index=True),pd.concat(allpatients,ignore_index=True)

def confirmation(tables,cfg=CFG):
    rows=[];patients=[]
    for r in range(1,cfg.replications+1):
        for c in cfg.doctors:
            q,row=execute(tables[('confirmation',r)],c,cfg.pharmacy_counters,'confirmation','base',r,f'{cfg.confirmation_seed}:{r-1}',cfg);rows.append(row);patients.append(q)
    save(pd.DataFrame(rows),'experiments/confirmation_run_results.csv');save(pd.concat(patients),'experiments/confirmation_patient_results.csv.gz')
    return pd.DataFrame(rows),pd.concat(patients)

def sensitivities(model,draws,main_rows,main_patients,cfg=CFG):
    # Base cells reuse main output; no redundant DES execution for target changes.
    rows=[main_rows[main_rows.experiment=='empirical']];patients=[main_patients[main_patients.experiment=='empirical']];inputs=[]
    conditions=[('empirical','arrivals_fast',{'arrival_factor':cfg.arrival_factors[1]},1),('empirical','arrivals_slow',{'arrival_factor':cfg.arrival_factors[0]},1),
        ('empirical','doctor_slow',{'doctor_factor':cfg.doctor_service_factors[1]},1),('empirical','doctor_fast',{'doctor_factor':cfg.doctor_service_factors[0]},1),
        ('empirical','pharmacy_slow',{'pharmacy_factor':cfg.pharmacy_service_factor},1),('empirical','two_counters',{},2),
        ('poisson','base',{},1),('poisson','arrivals_fast',{'arrival_factor':cfg.arrival_factors[1]},1),('poisson','doctor_slow',{'doctor_factor':cfg.doctor_service_factors[1]},1)]
    for kind,condition,factors,k in conditions:
        rr=[];pp=[]
        for r,u in enumerate(draws,1):
            p=generate(u,model,cfg,kind,**factors);inputs.append(p.assign(experiment=kind,condition=condition,RunID=r))
            for c in cfg.doctors:
                q,row=execute(p,c,k,kind,condition,r,f'{cfg.root_seed}:{r-1}',cfg);rr.append(row);pp.append(q)
        rows.append(pd.DataFrame(rr));patients.append(pd.concat(pp))
    runs=pd.concat(rows,ignore_index=True);pp=pd.concat(patients,ignore_index=True)
    assert len(runs)==10*cfg.replications*len(cfg.doctors)
    assert runs.groupby(['experiment','condition','RunID']).input_hash.nunique().eq(1).all()
    save(runs,'experiments/sensitivity_run_results.csv');save(pp,'experiments/sensitivity_patient_results.csv.gz');save(pd.concat(inputs),'experiments/sensitivity_inputs.csv.gz')
    status(['9.1','9.2'],'outputs/experiments/sensitivity_run_results.csv; sensitivity_patient_results.csv.gz; sensitivity_inputs.csv.gz')
    return runs,pp
