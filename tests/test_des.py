import numpy as np
import pandas as pd
import pytest
from src.des import simulate,verify_invariants,queue_integral
from src.metrics import ci

def patients(rows):return pd.DataFrame(rows,columns=['PatientID','ArrivalTime','Priority','DocServiceTime','MedServiceTime'])
def hand():return patients([(1,0,1,10,5),(2,1,1,4,3),(3,2,3,3,2),(4,3,2,2,2)])

def test_hand():
    p,tr=simulate(hand(),1,collect_trace=True)
    assert list(p.sort_values('DocStart').PatientID)==[1,3,4,2]
    assert list(p.DocWaitTime)==[0,14,8,10]
    assert list(p.MedWaitTime)==[0,0,2,2]
    assert list(p.PharmacyEnd)==[15,22,17,19]
    verify_invariants(p,1,1);assert len(tr)==8

def test_fcfs_nonpreemption():
    p,_=simulate(patients([(1,0,1,10,1),(2,1,1,2,1),(3,2,3,1,1),(4,3,1,1,1)]),1)
    assert list(p.sort_values('DocStart').PatientID)==[1,3,2,4];assert p.DocEnd.iloc[0]==10

def test_arrival_completion_tie():
    p,_=simulate(patients([(1,0,1,5,1),(2,1,1,5,1),(3,5,3,1,1)]),1)
    assert list(p.sort_values('DocStart').PatientID)==[1,3,2]

def test_simultaneous_pharmacy_tie():
    p,_=simulate(patients([(2,0,1,5,2),(1,0,1,5,3)]),2)
    assert list(p.PharmacyStart)==[5,8];verify_invariants(p,2,1)

@pytest.mark.parametrize('c,k',[(1,1),(2,1),(4,2),(8,3)])
def test_capacity_drain_and_reproducibility(c,k):
    rng=np.random.default_rng(13);n=60
    x=patients(zip(range(n),np.cumsum(rng.integers(1,4,n)),rng.integers(1,4,n),rng.integers(1,12,n),rng.integers(1,6,n)))
    before=x.copy(deep=True);p,_=simulate(x,c,k);q,_=simulate(x,c,k)
    pd.testing.assert_frame_equal(p,q);pd.testing.assert_frame_equal(x,before);verify_invariants(p,c,k)
    assert len(p)==n and np.isfinite(p.PharmacyEnd).all()

def test_one():
    p,_=simulate(patients([(1,0,3,4,2)]),2,2);assert p.PharmacyEnd.iloc[0]==6

def test_empty():
    p,_=simulate(patients([]).astype(float),2);assert len(p)==0

@pytest.mark.parametrize('c,k',[(0,1),(1,0),(1.5,1),(True,1)])
def test_invalid_capacity(c,k):
    with pytest.raises(ValueError):simulate(hand(),c,k)

@pytest.mark.parametrize('col,value',[('ArrivalTime',-1),('Priority',4),('DocServiceTime',0),('MedServiceTime',-1),('ArrivalTime',np.nan),('PatientID',2)])
def test_invalid_data(col,value):
    x=hand();x.loc[0,col]=value
    with pytest.raises(ValueError):simulate(x,1)

def test_statistics_known_vector():
    q=ci([1,2,3,4,5]);assert q['n']==5;assert q['mean']==3
    assert np.isclose(q['sd'],np.sqrt(2.5));assert np.isclose(q['se'],np.sqrt(.5))
    assert np.isclose(q['lo'],1.0367568385);assert ci([0]*50)['hi']==0

def test_area_known():assert queue_integral([0,1,4],[3,4,4])==(6.,2)

def test_fractional_clock_tie():
    x=patients([(1,0,1,.1+.2,1),(2,.1,1,1,1),(3,.3,3,1,1)])
    p,_=simulate(x,1);assert list(p.sort_values('DocStart').PatientID)==[1,3,2];verify_invariants(p,1,1)

def test_simultaneous_priority_when_idle():
    x=patients([(1,0,1,5,1),(2,0,3,2,1),(3,0,2,2,1)])
    p,_=simulate(x,1);assert list(p.sort_values('DocStart').PatientID)==[2,3,1]
    verify_invariants(p,1,1)

def test_clipped_busy_and_queue_areas():
    from src.metrics import overlap
    assert overlap(np.array([1,8]),np.array([6,14]),10)==7
    assert queue_integral([1,4],[5,9],6)==(6.,2)
