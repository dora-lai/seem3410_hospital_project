"""Week 5: scope, audit, explore, empirical calibration; Week 2 capacity."""
import zipfile,json
import numpy as np
import pandas as pd
from config import ROOT,CFG
from src.common import save,write_json,filehash,status
INPUTS=['PatientID','ArrivalTime','Priority','DocServiceTime','MedServiceTime']

def pmf(v):
    z=pd.Series(v).value_counts().sort_index();return {'values':z.index.astype(float).tolist(),'probabilities':(z/z.sum()).tolist(),'n':int(z.sum())}

def calibrate(cfg=CFG):
    raw=ROOT/'data/raw/archive.zip'
    with zipfile.ZipFile(raw) as z:
        name='hospital_sim_6_scenarios.csv'; payload=z.read(name)
    import io,hashlib
    d=pd.read_csv(io.BytesIO(payload));keys=['Scenario','RunID','PatientID']
    checks={'shape':d.shape== (60000,14),'missing':int(d.isna().sum().sum())==0,'duplicates':not d.duplicated(keys).any(),
            'priorities':set(d.Priority)=={1,2,3},'services':bool((d[['DocServiceTime','MedServiceTime']]>0).all().all()),
            'nonnegative':bool((d[['ArrivalTime','DocWaitTime','MedWaitTime','TotalTimeInHospital']]>=0).all().all()),
            'doctor_ids':bool(((d.DoctorID>=1)&(d.DoctorID<=d.NumDoctors)).all()),
            'peak_flag':bool((d.IsPeakArrival==(d.ArrivalTime<=d.PeakLimit)).all()),
            'time_identity':bool(np.allclose(d.TotalTimeInHospital,d.DocWaitTime+d.DocServiceTime+d.MedWaitTime+d.MedServiceTime)),
            'run_sizes':bool((d.groupby(['Scenario','RunID']).size()==200).all()),
            'scenario_runs':bool((d.groupby('Scenario').RunID.nunique()==50).all()),
            'chronology':all(g.ArrivalTime.is_monotonic_increasing for _,g in d.groupby(['Scenario','RunID']))}
    write_json({'zip_sha256':filehash(raw),'csv_sha256':hashlib.sha256(payload).hexdigest(),'rows':len(d),'columns':len(d.columns),
        'checks':checks,'dtypes':d.dtypes.astype(str).to_dict(),'missing':d.isna().sum().to_dict()},'outputs/data/data_audit.json')
    save(pd.DataFrame([{'check':k,'pass':v} for k,v in checks.items()]),'data/data_audit.csv');assert all(checks.values()),checks
    (ROOT/'outputs/data/cleaning_log.md').write_text('No cleaning, deletion, deduplication or outcome alteration. All audit checks passed.\n')
    status(['2.1'],'outputs/data/data_audit.json; cleaning_log.md')
    b=d[d.Scenario==cfg.baseline_scenario].copy();assert len(b)==10000
    save(b[['RunID']+INPUTS],'data/baseline_inputs.csv')
    save(d.groupby('Scenario').agg(rows=('PatientID','size'),runs=('RunID','nunique'),doctors=('NumDoctors','first'),peak_limit=('PeakLimit','first'),mean_doc_wait=('DocWaitTime','mean'),mean_pharmacy_wait=('MedWaitTime','mean')) .reset_index(),'data/scenario_summary.csv')
    dictionary=[]
    for c in d:
        dictionary.append({'column':c,'type':str(d[c].dtype),'role':'input' if c in INPUTS else 'source metadata' if c in ['RunID','Scenario','NumDoctors','PeakLimit','IsPeakArrival'] else 'recorded outcome; forbidden as simulator input','unit':'minutes' if 'Time' in c or c=='PeakLimit' else 'identifier/count/category'})
    save(pd.DataFrame(dictionary),'data/data_dictionary.csv');status(['2.2'],'outputs/data/baseline_inputs.csv; scenario_summary.csv; data_dictionary.csv')
    gaps=[];bins=[]
    for r,g in b.groupby('RunID'):
        g=g.sort_values(['ArrivalTime','PatientID']);t=g.ArrivalTime.to_numpy();prev=np.r_[0,t[:-1]]
        gaps.extend({'RunID':r,'PatientID':p,'previous':a,'arrival':x,'gap':x-a,'period':'peak' if a<=cfg.peak_limit else 'late','timestamp_period':'peak' if x<=cfg.peak_limit else 'late'} for p,a,x in zip(g.PatientID,prev,t))
        for lo in np.arange(0,np.ceil(t[-1]/60)*60,60):
            hi=lo+60;exp=max(0,min(hi,t[-1])-lo)
            bins.append({'RunID':r,'bin_start':lo,'count':int(((t>=lo)&((t<hi)|((t==hi)&(t==t[-1])))).sum()),'exposure':exp})
    gaps=pd.DataFrame(gaps);assert (gaps.gap>0).all();save(gaps,'data/interarrival_gaps.csv')
    profile=pd.DataFrame(bins).groupby('bin_start').agg(count=('count','sum'),exposure=('exposure','sum'),observed_runs=('RunID','nunique')).reset_index();profile['rate_per_min']=profile['count']/profile.exposure;assert int(profile['count'].sum())==len(b);save(profile,'data/arrival_profile.csv')
    gapdist=gaps.groupby(['period','gap']).size().rename('count').reset_index();gapdist['probability']=gapdist['count']/gapdist.groupby('period')['count'].transform('sum');save(gapdist,'data/interarrival_distribution.csv')
    last=b.groupby('RunID').ArrivalTime.max();npeak=int((b.ArrivalTime<=cfg.peak_limit).sum());late_exposure=float(np.maximum(last-cfg.peak_limit,0).sum())
    arrival_summary=b.groupby('RunID').agg(last_arrival=('ArrivalTime','max'),peak_count=('IsPeakArrival','sum'));arrival_summary['late_count']=200-arrival_summary.peak_count;save(arrival_summary.reset_index(),'data/observed_arrival_runs.csv')
    model={'peak_rate':npeak/(50*cfg.peak_limit),'late_rate':(len(b)-npeak)/late_exposure,'peak_count':npeak,'late_exposure':late_exposure,
        'gap_peak':pmf(gaps[gaps.period=='peak'].gap),'gap_late':pmf(gaps[gaps.period=='late'].gap)}
    status(['2.3'],'outputs/data/arrival_profile.csv; interarrival_distribution.csv; observed_arrival_runs.csv')
    summaries=[];dists=[];dep=[]
    for col in ['Priority','DocServiceTime','MedServiceTime']:
        v=b[col];model[col]=pmf(v)
        summaries.append({'variable':col,'n':len(v),'mean':v.mean(),'median':v.median(),'sd':v.std(),'p10':v.quantile(.1),'p90':v.quantile(.9),'min':v.min(),'max':v.max()})
        f=model[col]
        for value,prob in zip(f['values'],f['probabilities']):dists.append({'variable':col,'value':value,'probability':prob})
    save(pd.DataFrame(summaries),'data/input_summary.csv');save(pd.DataFrame(dists),'data/input_distributions.csv')
    for col in ['DocServiceTime','MedServiceTime']:
        for grouping in ['Priority','IsPeakArrival']:
            for key,g in b.groupby(grouping):dep.append({'variable':col,'grouping':grouping,'group':key,'n':len(g),'mean':g[col].mean(),'sd':g[col].std(),'p90':g[col].quantile(.9)})
    save(pd.DataFrame(dep),'data/dependence.csv')
    corr=b[['Priority','ArrivalTime','DocServiceTime','MedServiceTime']].corr(method='spearman');save(corr.reset_index(),'data/spearman_dependence.csv')
    serial=[]
    for r,g in b.groupby('RunID'):
        for col in ['DocServiceTime','MedServiceTime','Priority']:serial.append({'RunID':r,'variable':col,'lag1_correlation':g[col].autocorr()})
    save(pd.DataFrame(serial),'data/serial_dependence.csv');status(['2.4'],'outputs/data/input_summary.csv; input_distributions.csv; dependence.csv; spearman_dependence.csv; serial_dependence.csv')
    alternative=gaps.groupby(['timestamp_period','gap']).size().rename('count').reset_index();alternative['probability']=alternative['count']/alternative.groupby('timestamp_period')['count'].transform('sum');save(alternative,'data/arrival_timestamp_conditioning.csv')
    for key in ['gap_peak','gap_late','Priority','DocServiceTime','MedServiceTime']:assert np.isclose(sum(model[key]['probabilities']),1)
    write_json(model,'outputs/data/calibration.json');status(['2.5'],'outputs/data/calibration.json; arrival_timestamp_conditioning.csv; docs/assumptions.md')
    evidence=[]
    for (s,r),g in d.groupby(['Scenario','RunID']):
        g=g.sort_values(['ArrivalTime','PatientID']);a=g.ArrivalTime.to_numpy();start=(g.ArrivalTime+g.DocWaitTime).to_numpy();p=g.Priority.to_numpy()
        overt=(a[:,None]<a[None,:])&(start[:,None]>start[None,:])
        overlap=0
        for _,h in g.groupby('DoctorID'):
            h=h.assign(start=h.ArrivalTime+h.DocWaitTime).sort_values('start');overlap+=int((h.start.to_numpy()[1:]<(h.start+h.DocServiceTime).to_numpy()[:-1]).sum())
        evidence.append({'Scenario':s,'RunID':r,'strict_overtakes':int(overt.sum()),'same_class':int((overt&(p[:,None]==p[None,:])).sum()),'higher_overtakes_lower':int((overt&(p[:,None]<p[None,:])).sum()),'lower_overtakes_higher':int((overt&(p[:,None]>p[None,:])).sum()),'server_overlaps':overlap})
    save(pd.DataFrame(evidence),'data/queue_rule_evidence.csv')
    (ROOT/'outputs/data/queue_rule_evidence.md').write_text('Strict overtakes compare strictly different arrival and start times. Higher-class overtakes and zero same/lower-class overtakes support compatibility. They do not identify undocumented source code. Exact replay is an additional compatibility check, not hospital validation.\n')
    status(['2.6'],'outputs/data/queue_rule_evidence.csv; queue_rule_evidence.md')
    rows=[]
    for key,unit in [('gap_peak','minutes'),('gap_late','minutes'),('Priority','class'),('DocServiceTime','minutes'),('MedServiceTime','minutes')]:rows.append({'input':key,'source':'estimated from synthetic baseline','rule':'empirical PMF','parameters':json.dumps(model[key]),'unit':unit})
    for key in ['peak_rate','late_rate']:rows.append({'input':key,'source':'estimated from synthetic baseline','rule':'Poisson alternative','parameters':model[key],'unit':'patients/minute'})
    for key,val,unit in [('wage',cfg.doctor_wage,'cost units/doctor-hour'),('schedule',cfg.horizon,'minutes'),('target',cfg.target,'minutes')]:rows.append({'input':key,'source':'illustrative assumption','rule':'fixed','parameters':val,'unit':unit})
    save(pd.DataFrame(rows),'tables/input_parameters.csv');status(['2.7'],'outputs/tables/input_parameters.csv; docs/assumptions.md')
    return d,b,model

def capacity(model,cfg=CFG):
    mean=lambda key:np.dot(model[key]['values'],model[key]['probabilities'])
    mu=1/mean('DocServiceTime');mup=1/mean('MedServiceTime');rows=[]
    for period in ['peak','late']:
        rate=model[period+'_rate']
        for c in cfg.doctors:rows.append({'period':period,'doctors':c,'lambda_per_min':rate,'mu_doc_per_min':mu,'mu_pharmacy_per_min':mup,'offered_doctor_load':rate/mu,'rho_doc':rate/(c*mu),'pharmacy_nominal_rho':rate/mup})
    save(pd.DataFrame(rows),'tables/capacity_analysis.csv')
    (ROOT/'docs/analytical_checks.md').write_text('Week 2 offered load a=lambda*mean service and rho=a/c are nominal demands. rho>1 during peak means temporary overload, not realized utilization >100%. Pharmacy ratio uses external arrivals only as a rough reference. Erlang C/M/M/c assumes steady-state homogeneous Poisson arrivals, exponential service and FCFS; the finite priority network violates these conditions. No exact Erlang waiting predictions are claimed. The optional controlled M/M/1 experiment is omitted. Finite-run queue-area conservation is checked independently.\n')
    status(['3.1','3.2'],'outputs/tables/capacity_analysis.csv; docs/analytical_checks.md')
