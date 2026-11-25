"""Report figures use only saved calibration and executed experimental outputs."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from config import ROOT,CFG
from src.common import status
F=ROOT/'outputs/figures';T=ROOT/'outputs/tables';D=ROOT/'outputs/data'
COLORS=['#0072B2','#D55E00','#009E73']

def chart_finish(fig,name):
    fig.tight_layout();fig.savefig(F/(name+'.png'),dpi=250,bbox_inches='tight');fig.savefig(F/(name+'.svg'),bbox_inches='tight');plt.close(fig)

def system_flow():
    F.mkdir(parents=True,exist_ok=True)
    fig,ax=plt.subplots(figsize=(9,1.5));ax.axis('off')
    labels=['Arrival','Priority\n3 > 2 > 1','Doctor\n2 / 3 / 4','Pharmacy\nFCFS','Departure']
    for j,label in enumerate(labels):
        x=j*2.;ax.text(x,0,label,fontsize=16,ha='center',va='center',bbox=dict(boxstyle='round,pad=.6',fc='#eef5f9',ec='#0072B2'))
        if j<4:ax.annotate('',xy=(x+1.4,0),xytext=(x+.65,0),arrowprops={'arrowstyle':'->','color':'#425466'})
    ax.set(xlim=(-1,9),ylim=(-.8,.8));chart_finish(fig,'system_flow')

def plots(cfg=CFG):
    F.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.prop_cycle':plt.cycler(color=COLORS)})
    system_flow()
    profile=pd.read_csv(D/'arrival_profile.csv');gd=pd.read_csv(D/'interarrival_distribution.csv');fit=pd.read_csv(D/'generated_input_fit.csv');ggen=pd.read_csv(D/'generated_gaps.csv.gz')
    fig,axs=plt.subplots(1,2,figsize=(10,3.1));ax=axs[0]
    ax.plot(profile.bin_start+30,profile.rate_per_min,'o-',label='Source baseline');ax.axvline(cfg.peak_limit,color='gray',ls='--');ax.set(xlabel='Minutes from empty start',ylabel='Count / observed exposure (patients/min)',title='Fixed 200 patients; late bins truncated')
    for period,g in gd.groupby('period'):axs[1].plot(g.gap,g.probability,'o-',label=f'Previous clock: {period}')
    axs[1].set(xlabel='Interarrival gap (min)',ylabel='Probability',title='Empirical gap PMFs');axs[1].legend();chart_finish(fig,'arrival_profile')
    plt.rcParams.update({'font.size':17})
    inp=pd.read_csv(D/'input_distributions.csv');fig,axs=plt.subplots(1,3,figsize=(10,2.7))
    for ax,var,label in zip(axs,['Priority','DocServiceTime','MedServiceTime'],['Priority class','Consultation (min)','Pharmacy service (min)']):
        x=inp[inp.variable==var];ax.bar(x.value.astype(str),x.probability,color=COLORS[0]);ax.set(xlabel=label,ylabel='Probability')
    chart_finish(fig,'input_pmfs')
    plt.rcParams.update({'font.size':10})
    fig,axs=plt.subplots(1,2,figsize=(10,2.8))
    for ax,metric in zip(axs,['peak_count','last_arrival']):
        obs=pd.read_csv(D/'observed_arrival_runs.csv')[metric];ax.boxplot([obs]+[fit[fit.model==k][metric] for k in ['empirical','poisson']],tick_labels=['Source','Empirical','Poisson']);ax.set(ylabel='Patients' if metric=='peak_count' else 'Minutes',title=metric.replace('_',' ').capitalize())
    chart_finish(fig,'input_fit')
    fig,axs=plt.subplots(1,2,figsize=(10,3))
    for kind,g in ggen.groupby('model'):
        for ax,period in zip(axs,['peak','late']):
            v=g.loc[(g.previous<=cfg.peak_limit) if period=='peak' else (g.previous>cfg.peak_limit),'gap'].sort_values().to_numpy();ax.step(v,np.arange(1,len(v)+1)/len(v),where='post',label=kind)
            ax.set(xlabel='Gap (min)',ylabel='ECDF',title='Previous-clock '+period,xlim=(0,30))
    for ax,period in zip(axs,['peak','late']):
        g=gd[gd.period==period];ax.step(g.gap,g.probability.cumsum(),where='post',label='source',color='black',ls='--');ax.legend()
    chart_finish(fig,'arrival_ecdf')
    plt.rcParams.update({'font.size':13})
    s=pd.read_csv(T/'policy_summary.csv');fig,ax=plt.subplots(figsize=(7.5,2.8))
    for offset,(exp,label) in zip([-.04,.04],[('empirical','Fresh empirical (primary)'),('replay','Original baseline replay')]):
        g=s[(s.experiment==exp)&(s.metric=='p90_doc_wait')];ax.errorbar(g.doctors+offset,g['mean'],yerr=[g['mean']-g.lo,g.hi-g['mean']],fmt='o-',capsize=4,label=label)
    ax.axhline(cfg.target,color='gray',ls='--',label=f'{cfg.target:g}-min target');ax.set(xticks=cfg.doctors,xlabel='Number of doctors',ylabel='Mean run-level P90 doctor wait (min)');ax.legend(fontsize=12);chart_finish(fig,'main_p90_ci')
    plt.rcParams.update({'font.size':10})
    fig,axs=plt.subplots(1,2,figsize=(10,3))
    for metric,label in [(f'p90_priority{i}',f'Priority {i}') for i in [1,2,3]]:
        g=s[(s.experiment=='empirical')&(s.metric==metric)];axs[0].plot(g.doctors,g['mean'],'o-',label=label)
    for metric,label in [('p90_peak','Peak arrivals'),('p90_nonpeak','Later arrivals')]:
        g=s[(s.experiment=='empirical')&(s.metric==metric)];axs[1].errorbar(g.doctors,g['mean'],yerr=g.hi-g['mean'],fmt='o-',capsize=3,label=label)
    for ax in axs:ax.set(xticks=cfg.doctors,xlabel='Doctors',ylabel='Mean subgroup run P90 (min)');ax.legend()
    chart_finish(fig,'priority_peak')
    fig,axs=plt.subplots(1,3,figsize=(11,3))
    for metric in ['doc_util_peak','pharmacy_util_peak']:
        g=s[(s.experiment=='empirical')&(s.metric==metric)];axs[0].plot(g.doctors,g['mean'],'o-',label=metric.replace('_',' '))
    axs[0].set(ylabel='Busy overlap / resource minutes');axs[0].legend(fontsize=8)
    for metric in ['mean_pharmacy_wait','mean_total_time']:
        g=s[(s.experiment=='empirical')&(s.metric==metric)];axs[1].plot(g.doctors,g['mean'],'o-',label=metric.replace('_',' '))
    axs[1].set(ylabel='Minutes');axs[1].legend(fontsize=8)
    g=pd.read_csv(T/'cost_summary.csv');g=g[(g.experiment=='empirical')&(g.condition=='base')];axs[2].plot(g.scheduled_cost,s[(s.experiment=='empirical')&(s.metric=='p90_doc_wait')]['mean'],'o-');axs[2].set(xlabel='Illustrative scheduled doctor cost',ylabel='Mean run P90 (min)')
    for ax in axs[:2]:ax.set(xlabel='Doctors',xticks=cfg.doctors)
    chart_finish(fig,'resource_cost')
    ss=pd.read_csv(T/'sensitivity_summary.csv');fig,axs=plt.subplots(1,2,figsize=(11,3.5))
    for ax,kind in zip(axs,['empirical','poisson']):
        g=ss[(ss.experiment==kind)&(ss.metric=='p90_doc_wait')];conds=list(g.condition.unique());x=np.arange(len(conds))
        for j,c in enumerate(cfg.doctors):
            h=g[g.doctors==c].set_index('condition').loc[conds];ax.errorbar(x+(j-1)*.12,h['mean'],yerr=h.hi-h['mean'],fmt='o',capsize=2,label=f'{c} doctors')
        ax.axhline(cfg.target,color='gray',ls='--');ax.set(xticks=x,xticklabels=[z.replace('_','\n') for z in conds],ylabel='Mean run P90 (min)',title=kind.capitalize());ax.legend(fontsize=8)
    chart_finish(fig,'sensitivity')
    ta=pd.read_csv(T/'target_achievement.csv');ta=ta[(ta.experiment=='empirical')&(ta.target==cfg.target)];fig,ax=plt.subplots(figsize=(7,2.8));x=np.arange(len(ta));ax.bar(x-.18,ta.run_attainment,.36,label='Runs with P90 <=15');ax.bar(x+.18,ta.service_level,.36,label='Mean patient service level');ax.set(xticks=x,xticklabels=ta.doctors.astype(str),xlabel='Doctors',ylabel='Fraction',ylim=(0,1.08));ax.legend();chart_finish(fig,'attainment')
    (F/'captions.md').write_text('Recommended compact report figures: system_flow (boundary); input_pmfs (synthetic baseline fitted PMFs); main_p90_ci (fresh empirical primary and separate original-input replay; two-sided 95% t CIs of mean run P90); sensitivity (empirical and Poisson alternatives; 50 matched runs/cell). Additional evidence: arrival_profile (fixed-count exposure caveat), arrival_ecdf (continuous alternative changes variability), input_fit, priority_peak (subgroup run P90), resource_cost and attainment. All units are minutes unless otherwise labelled. CIs are conditional Monte Carlo mean intervals.\n')
    status(['11.1'],'outputs/figures/*.png and *.svg; captions.md; all figures read saved outputs')
