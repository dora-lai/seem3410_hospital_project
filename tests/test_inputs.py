import json
import numpy as np
import pandas as pd
from config import CFG,ROOT
from src.inputs import base_draws,generate,input_hash,poisson_next
from src.des import simulate

def model():
    # Refit the tiny input model directly from immutable raw inputs, so tests work before any outputs exist.
    from src.calibration import pmf
    b=pd.read_csv(ROOT/'data/raw/archive.zip');b=b[b.Scenario==CFG.baseline_scenario]
    x=b.sort_values(['RunID','ArrivalTime']);prev=x.groupby('RunID').ArrivalTime.shift(fill_value=0);gap=x.ArrivalTime-prev
    last=x.groupby('RunID').ArrivalTime.max()
    m={'gap_peak':pmf(gap[prev<=240]),'gap_late':pmf(gap[prev>240]),
       'peak_rate':(x.ArrivalTime<=240).sum()/(50*240),'late_rate':(x.ArrivalTime>240).sum()/np.maximum(last-240,0).sum()}
    for key in ['Priority','DocServiceTime','MedServiceTime']:m[key]=pmf(b[key])
    return m
def test_streams_and_crn():
    a,l=base_draws(3410,3,200);b,_=base_draws(3410,3,200)
    assert all(np.array_equal(x,y) for x,y in zip(a,b));assert not np.array_equal(a[0],a[1])
    p=generate(a[0],model(),CFG);h=input_hash(p)
    for c in [2,3,4]:
        for k in [1,2]:
            q,_=simulate(p,c,k);assert input_hash(q)==h
    pd.testing.assert_frame_equal(generate(b[0],model(),CFG),p)

def test_poisson_boundary():
    assert poisson_next(230,3,240,.2,.1)==250
    assert poisson_next(230,1,240,.2,.1)==235
    assert poisson_next(240,1,240,.2,.1)==250

def test_matched_perturbation():
    a,_=base_draws(3410,1,200);p=generate(a[0],model(),CFG);q=generate(a[0],model(),CFG,doctor_factor=1.1)
    assert np.array_equal(p.ArrivalTime,q.ArrivalTime);assert np.allclose(q.DocServiceTime,1.1*p.DocServiceTime)
    f=generate(a[0],model(),CFG,arrival_factor=1.1)
    assert np.allclose(f.Priority,p.Priority);assert f.ArrivalTime.iloc[-1]<p.ArrivalTime.iloc[-1]

def test_experiment_metadata_and_target_summary():
    from src.experiments import execute
    from src.analysis import targets
    u,_=base_draws(3410,1,200);p=generate(u[0],model(),CFG)
    patients,row=execute(p,2,1,'empirical','base',1,'3410:0',CFG)
    q=targets(pd.DataFrame([row]),patients,CFG)
    assert len(q)==4 and q['n'].eq(1).all()
