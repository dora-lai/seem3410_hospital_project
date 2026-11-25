import numpy as np
from scipy.stats import t
from src.des import queue_integral

def ci(values):
    x=np.asarray(values,float);x=x[np.isfinite(x)];n=len(x)
    if n==0:return {'n':0,'mean':np.nan,'sd':np.nan,'se':np.nan,'lo':np.nan,'hi':np.nan}
    mean=x.mean();sd=x.std(ddof=1) if n>1 else np.nan;se=sd/np.sqrt(n);half=t.ppf(.975,n-1)*se if n>1 else np.nan
    return dict(n=n,mean=mean,sd=sd,se=se,lo=mean-half,hi=mean+half)

def quant(x):return float(np.quantile(x,.9,method='linear')) if len(x) else np.nan

def overlap(start,end,T):return float(np.maximum(0,np.minimum(end,T)-np.maximum(start,0)).sum())

def metrics(p,c,k,cfg):
    last=float(p.PharmacyEnd.max());w=p.DocWaitTime
    m={'n_patients':len(p),'doctors':c,'pharmacy_counters':k,'mean_doc_wait':w.mean(),'p90_doc_wait':quant(w),
       'sum_doc_wait':w.sum(),'sum_sq_doc_wait':(w*w).sum(),'mean_pharmacy_wait':p.MedWaitTime.mean(),'mean_total_time':p.TotalTimeInHospital.mean(),
       'last_arrival':p.ArrivalTime.max(),'last_doc_end':p.DocEnd.max(),'last_departure':last,'arrivals_after_H':int((p.ArrivalTime>cfg.horizon).sum()),
       'work_after_H':int(last>cfg.horizon),'doc_overtime':np.maximum(0,p.DocEnd-np.maximum(p.DocStart,cfg.horizon)).sum(),
       'pharmacy_overtime':np.maximum(0,p.PharmacyEnd-np.maximum(p.PharmacyStart,cfg.horizon)).sum()}
    for target in cfg.targets:
        m[f'sl_{target:g}']=float((w<=target).mean());m[f'attain_{target:g}']=int(quant(w)<=target)
    for label,mask in [('peak',p.ArrivalTime<=cfg.peak_limit),('nonpeak',p.ArrivalTime>cfg.peak_limit)]+[(f'priority{j}',p.Priority==j) for j in [1,2,3]]:
        x=w[mask];m[f'n_{label}']=len(x);m[f'mean_{label}']=x.mean();m[f'p90_{label}']=quant(x)
    for label,T in [('peak',cfg.peak_limit),('schedule',cfg.horizon),('whole',last)]:
        m[f'doc_util_{label}']=overlap(p.DocStart,p.DocEnd,T)/(c*T)
        m[f'pharmacy_util_{label}']=overlap(p.PharmacyStart,p.PharmacyEnd,T)/(k*T)
        for queue,a,b in [('doc','ArrivalTime','DocStart'),('pharmacy','DocEnd','PharmacyStart')]:
            area,maximum=queue_integral(p[a],p[b],T);m[f'{queue}_qmean_{label}']=area/T;m[f'{queue}_qmax_{label}']=maximum
    return m
