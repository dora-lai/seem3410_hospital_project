# Metric definitions
Times in minutes. Doctor wait = DocStart-ArrivalTime. Pharmacy wait = PharmacyStart-DocEnd. Total time = PharmacyEnd-ArrivalTime = both waits + both services.

For each replication, P90=np.quantile(all 200 doctor waits,.9,method='linear'). Primary estimand is E[run P90]; estimate is the arithmetic mean across independent runs. Pooled P90 is a different descriptive quantity across patient-policy records. Peak cohort has ArrivalTime<=240, nonpeak >240; class-specific measures use original patient priority. Empty subsets produce NaN and valid-run counts, never zero.

Attainment(target) is fraction of runs with run P90<=target. Service level is within-run fraction of patients with wait<=target, then averaged across runs. These do not guarantee every run or patient meets target. Confidence intervals describe Monte Carlo uncertainty of mean KPI conditional on fitted distributions, not individual predictions or calibration/model uncertainty.

For any common window [0,T], busy overlap=sum(max(0,min(end,T)-max(start,0))); utilization=overlap/(resources*T). Report T=240 and T=H=1080. Whole-run utilization uses final pharmacy departure as denominator and is policy-dependent. Queue area=sum clipped waiting intervals, independently checked using a sweep of queue changes; mean queue=area/T. Max queue counts only positive-duration waits after simultaneous changes are grouped. Full queue areas equal summed patient waiting times.

Doctor overtime workload=sum(max(0,end-max(start,H))); pharmacy separately. Work-after-H indicator uses final departure>H. Arrivals after H flagged. Busy-minute overtime cost proxy is scheduled doctor cost + premium*wage*doctor overtime workload/60; this is not paid shift payroll. Scheduled cost=c*wage*H/60, illustrative units. Cost excludes pharmacy; second counter is performance sensitivity only.

CI: valid independent run values, mean +/- t(.975,R-1)*s/sqrt(R), sample SD ddof=1. Zero observed variance yields zero width, not certainty. Paired differences=new-reference after matching RunID/input hash. Negative waiting differences improve; percentage change=100*(new mean-reference mean)/reference mean, undefined for zero reference. Point feasible if mean P90<=target; confidence-supported if CI upper<=target; uncertain if CI straddles target. Select minimum scheduled cost among feasible; report none if empty.
