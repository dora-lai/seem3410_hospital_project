import pandas as pd
from config import CFG
from src.analysis import decisions,paired

def test_decisions_none_uncertain_and_supported():
    s=pd.DataFrame([dict(experiment='empirical',condition='base',doctors=c,pharmacy_counters=1,metric='p90_doc_wait',mean=m,lo=lo,hi=hi) for c,m,lo,hi in [(2,50,45,55),(3,14,12,16),(4,4,3,5)]])
    d=decisions(s,CFG).set_index('target')
    assert d.loc[15,'point_choice']=='3' and d.loc[15,'supported_choice']=='4'
    assert d.loc[15,'uncertain_candidates']=='3'
    s['mean']+=100;s['lo']+=100;s['hi']+=100
    assert decisions(s,CFG).point_choice.eq('none').all()

def test_paired_known_values_and_sign():
    from src.analysis import CORE
    r=[]
    for c,values in [(2,[10,20,30]),(3,[8,16,24]),(4,[4,8,12])]:
        for run,v in enumerate(values,1):r.append({'experiment':'test','condition':'base','doctors':c,'RunID':run,'input_hash':str(run),**{m:v for m in CORE}})
    _,s=paired(pd.DataFrame(r));g=s[(s.comparison=='3-2')&(s.metric=='p90_doc_wait')].iloc[0]
    assert g['mean']==-4 and g.n==3 and g.percent_change==-20
