"""Independent Week 3–4 DES. No recorded outputs enter this function."""
import heapq
import itertools
import numpy as np
import pandas as pd
from src.calibration import INPUTS
from config import CFG

def validate(patients,n_doctors,n_pharmacy):
    for c in [n_doctors,n_pharmacy]:
        if isinstance(c,bool) or not isinstance(c,(int,np.integer)) or c<1:raise ValueError('capacities must be positive integers')
    if not set(INPUTS)<=set(patients.columns):raise ValueError('missing input columns')
    p=patients[INPUTS].copy(deep=True)
    for col in INPUTS:
        if not pd.api.types.is_numeric_dtype(p[col]) or not np.isfinite(p[col].to_numpy(dtype=float)).all():raise ValueError('finite numeric inputs required')
    if p.PatientID.duplicated().any() or (p.PatientID%1!=0).any():raise ValueError('unique integer patient IDs required')
    if (p.ArrivalTime<0).any() or (p[['DocServiceTime','MedServiceTime']]<=0).any().any():raise ValueError('invalid times')
    if not p.Priority.isin([1,2,3]).all():raise ValueError('invalid priority')
    return p.sort_values('PatientID').reset_index(drop=True)

def simulate(patients,n_doctors,n_pharmacy=1,peak_limit=240,collect_trace=False,time_decimals=CFG.time_decimals):
    p=validate(patients,n_doctors,n_pharmacy)
    if not np.isfinite(peak_limit) or peak_limit<0:raise ValueError('invalid peak limit')
    p[['ArrivalTime','DocServiceTime','MedServiceTime']]=p[['ArrivalTime','DocServiceTime','MedServiceTime']].round(time_decimals)
    if (p[['DocServiceTime','MedServiceTime']]<=0).any().any():raise ValueError('duration below clock resolution')
    n=len(p);a=p.ArrivalTime.to_numpy(float);priority=p.Priority.to_numpy(int);service=p.DocServiceTime.to_numpy(float);pid=p.PatientID.to_numpy(int)
    start=np.zeros(n);end=np.zeros(n);doctor=np.zeros(n,int)
    fel=[];seq=itertools.count();idle=list(range(1,n_doctors+1));heapq.heapify(idle);waiting=[];trace=[]
    # FEL rank 0 arrival, 1 completion; sequence disambiguates deterministic ties.
    for i in sorted(range(n),key=lambda i:(a[i],pid[i])):heapq.heappush(fel,(a[i],0,next(seq),i,0))
    def dispatch(t):
        while idle and waiting:
            _,_,_,i=heapq.heappop(waiting);doc=heapq.heappop(idle)
            start[i]=t;end[i]=round(t+service[i],time_decimals);doctor[i]=doc
            heapq.heappush(fel,(end[i],1,next(seq),i,doc))
    while fel:
        t,rank,_,i,doc=heapq.heappop(fel)
        if rank==0:
            heapq.heappush(waiting,(-priority[i],a[i],pid[i],i))
            # Batch simultaneous arrivals so every eligible class is visible.
            if not(fel and fel[0][0]==t and fel[0][1]==0):dispatch(t)
        else:
            heapq.heappush(idle,doc);dispatch(t)
        if collect_trace:
            trace.append({'t':t,'event':'arrival' if rank==0 else 'doctor_completion','PatientID':pid[i],
                'q1':sum(x[0]==-1 for x in waiting),'q2':sum(x[0]==-2 for x in waiting),'q3':sum(x[0]==-3 for x in waiting),
                'busy':n_doctors-len(idle),'pending_fel':len(fel)})
    p['SimDoctorID']=doctor;p['DocStart']=start;p['DocEnd']=end
    # Exact separate downstream calendar: no blocking or feedback to doctors.
    available=[(0.,j) for j in range(1,n_pharmacy+1)];heapq.heapify(available)
    ps=np.zeros(n);pe=np.zeros(n);counter=np.zeros(n,int)
    for i in sorted(range(n),key=lambda i:(end[i],pid[i])):
        free,j=heapq.heappop(available);ps[i]=max(end[i],free);pe[i]=round(ps[i]+float(p.MedServiceTime.iloc[i]),time_decimals);counter[i]=j
        heapq.heappush(available,(pe[i],j))
    p['CounterID']=counter;p['PharmacyStart']=ps;p['PharmacyEnd']=pe
    p['DocWaitTime']=start-a;p['MedWaitTime']=ps-end;p['TotalTimeInHospital']=pe-a;p['IsPeakArrival']=(a<=peak_limit).astype(int)
    return p,pd.DataFrame(trace)

def queue_integral(begin,end,T=np.inf):
    """Independent sweep, group tied timestamps; excludes zero-length intervals."""
    events={}
    for a,b in zip(begin,end):
        a=max(0,float(a));b=min(float(b),T)
        if b>a:events[a]=events.get(a,0)+1;events[b]=events.get(b,0)-1
    area=0.;last=0.;q=0;maximum=0
    for t,dq in sorted(events.items()):
        area+=q*(t-last);q+=dq;assert q>=0;maximum=max(maximum,q);last=t
    assert q==0
    return area,maximum

def verify_invariants(p,c,k,tol=1e-8):
    assert p.PatientID.is_unique
    if len(p)==0:return
    assert (p.DocStart+tol>=p.ArrivalTime).all() and (p.PharmacyStart+tol>=p.DocEnd).all()
    assert np.allclose(p.DocEnd-p.DocStart,p.DocServiceTime) and np.allclose(p.PharmacyEnd-p.PharmacyStart,p.MedServiceTime)
    assert np.allclose(p.TotalTimeInHospital,p.DocWaitTime+p.DocServiceTime+p.MedWaitTime+p.MedServiceTime)
    for col,s,e,cap in [('SimDoctorID','DocStart','DocEnd',c),('CounterID','PharmacyStart','PharmacyEnd',k)]:
        assert p[col].between(1,cap).all()
        for _,g in p.groupby(col):
            g=g.sort_values(s);assert (g[s].to_numpy()[1:]+tol>=g[e].to_numpy()[:-1]).all()
    a=p.ArrivalTime.to_numpy();s=p.DocStart.to_numpy();priority=p.Priority.to_numpy();ids=p.PatientID.to_numpy()
    for i,t in enumerate(s):
        eligible=(a<=t)&(s>t)
        assert not np.any(eligible&(priority>priority[i]))
        assert not np.any(eligible&(priority==priority[i])&((a<a[i]-tol)|((abs(a-a[i])<=tol)&(ids<ids[i]))))
    h=p.sort_values(['DocEnd','PatientID']);assert (np.diff(h.PharmacyStart)>=-tol).all()
    for b,e,w in [('ArrivalTime','DocStart','DocWaitTime'),('DocEnd','PharmacyStart','MedWaitTime')]:assert np.isclose(queue_integral(p[b],p[e])[0],p[w].sum())
