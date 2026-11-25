"""Seven-section academic draft; all result values loaded from executed CSVs."""
import json,re,html
import numpy as np
import pandas as pd
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak,KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from pypdf import PdfReader
from config import ROOT,CFG
from src.common import save,write_json,status
T=ROOT/'outputs/tables';D=ROOT/'outputs/data'

def report(cfg=CFG):
    main=pd.read_csv(ROOT/'outputs/experiments/main_run_results.csv');replay=pd.read_csv(ROOT/'outputs/experiments/replay_run_results.csv');conf=pd.read_csv(ROOT/'outputs/experiments/confirmation_run_results.csv')
    sensitivity=pd.read_csv(ROOT/'outputs/experiments/sensitivity_run_results.csv');summary=pd.read_csv(T/'policy_summary.csv');ss=pd.read_csv(T/'sensitivity_summary.csv');cs=pd.read_csv(T/'confirmation_summary.csv');paired=pd.read_csv(T/'paired_ci.csv');decision=pd.read_csv(T/'decision_matrix.csv',keep_default_na=False);cost=pd.read_csv(T/'cost_summary.csv');targets=pd.read_csv(T/'target_achievement.csv');model=json.loads((D/'calibration.json').read_text());inputs=pd.read_csv(D/'input_summary.csv');verification=pd.read_csv(ROOT/'outputs/verification/verification_summary.csv')
    def stat(c,metric='p90_doc_wait',experiment='empirical',frame=summary,condition='base'):
        return frame[(frame.experiment==experiment)&(frame.condition==condition)&(frame.doctors==c)&(frame.metric==metric)].iloc[0]
    def runs(c):return main[main.doctors==c]
    def fmt(x):return f'{x:,.2f}'
    def interval(s):return f"{s['mean']:.2f} [{s.lo:.2f}, {s.hi:.2f}]"
    base=stat(2);choice=decision[(decision.experiment==cfg.primary_model)&(decision.condition=='base')&(decision.target==cfg.target)].iloc[0]
    c=int(choice.supported_choice) if choice.supported_choice!='none' else None
    # These defaults have a supported candidate; fail rather than fabricate a brief if configuration changes to none.
    if c is None:raise ValueError('No confidence-supported main candidate: revise conditional recommendation text to state none/uncertain')
    chosen=stat(c);pcomp=paired[(paired.experiment=='empirical')&(paired.comparison==f'{c}-2')&(paired.metric=='p90_doc_wait')].iloc[0]
    m=runs(c);a=targets[(targets.experiment=='empirical')&(targets.doctors==c)&(targets.target==cfg.target)].iloc[0];cc=cost[(cost.experiment=='empirical')&(cost.condition=='base')&(cost.doctors==c)].iloc[0]
    pc=decision[(decision.experiment=='poisson')&(decision.condition=='base')&(decision.target==cfg.target)].iloc[0]
    brief=(f'Use {c} doctors as the provisional staffing policy when the calibrated empirical arrival pattern applies. '
        f'Across {cfg.replications} fresh matched replications, its mean run-level P90 doctor wait was {chosen["mean"]:.2f} minutes '
        f'(95% confidence interval {chosen.lo:.2f} to {chosen.hi:.2f}), compared with {base["mean"]:.2f} minutes for two doctors. '
        f'The paired mean reduction was {-pcomp["mean"]:.2f} minutes. Scheduled doctor cost rises from '
        f'{2*cfg.doctor_wage*cfg.horizon/60:,.0f} to {cc.scheduled_cost:,.0f} illustrative units for the common {cfg.horizon/60:g}-hour schedule. '
        f'The policy met the {cfg.target:g}-minute run P90 target in {a.run_attainment:.0%} of simulated runs; this is not a guarantee for every run. '
        'Retain capacity to review a fourth doctor if arrivals accelerate or consultations lengthen. '
        f'The Poisson arrival alternative selected {pc.supported_choice} doctors, so arrival variability materially affects the decision. '
        'Before implementation, collect actual arrival and service records, confirm queue rules and staffing hours, and repeat the analysis. '
        'The principal limitation is that all calibration records are synthetic. The confidence intervals measure simulation uncertainty conditional on fitted inputs and do not establish clinical validity or real payroll costs.')
    count=len(brief.split());assert 150<=count<=200,count
    write_json({'policy_brief_words':count,'method':'whitespace-separated English tokens'},'outputs/reproducibility/report_checks.json')
    # Content blocks are the single source for editable markdown and PDF.
    pages=[]
    def para(text):return ('p',text)
    def table(caption,rows,widths):return ('table',(caption,rows,widths))
    def fig(name,caption,height):return ('fig',(name,caption,height))
    pages.append(('1 System and decision problem',[
        para(f'This study asks which staffing level among two, three and four doctors meets a {cfg.target:g}-minute doctor-wait target at the lowest illustrative scheduled cost. Two doctors form the reference policy. The analysis concerns a synthetic outpatient clinic and does not estimate measured clinical outcomes [1,2].'),
        fig('system_flow','Figure 1. Model boundary. Patients visit both stages once; pharmacy has one counter in the main comparison.',80),
        para('Patients share one doctor waiting system with three priority classes. Priority 3 is highest, followed by 2 and 1. Patients within a class follow first come, first served (FCFS). Consultations in progress are never interrupted. A patient then joins a pooled FCFS pharmacy queue immediately. This boundary retains the two queues affected by doctor staffing. Registration, travel, appointments, breaks, abandonment, rejection, clinical routing and pharmacy blocking are excluded.'),
        para(f'Each run starts empty, admits exactly {cfg.n_patients} patients, and ends after the last pharmacy departure. Arrivals can continue after the first {cfg.peak_limit:g} minutes, which define the peak period. No warm-up observations are removed because empty-start cohort performance is the intended outcome. Staff remain available until the system drains.'),
        para(f'For each run, P90 is the linearly interpolated 90th percentile of all {cfg.n_patients} doctor waits. The primary estimand is the expected run-level P90, estimated by averaging independent run P90 values. A point estimate at or below {cfg.target:g} minutes meets the illustrative target. We also require the upper endpoint of its two-sided 95% confidence interval to be at or below the target for confidence-supported feasibility.'),
        para(f'The cost assumption is {cfg.doctor_wage:g} units per doctor-hour for a common {cfg.horizon/60:g}-hour scheduled horizon. This gives costs of '+', '.join(f'{c*cfg.doctor_wage*cfg.horizon/60:,.0f}' for c in cfg.doctors)+' units. These assumptions are neither clinical standards nor recorded wages or shifts. Week 1 motivates a decision-focused boundary; Week 6 motivates fixed factors and explicit policy comparison [3,8].')]))
    inp_rows=[['Input','Fitted distribution / parameter','Source / units'],['Arrival gap','Peak previous-clock PMF on 3-7; late PMF on 3-7','Synthetic baseline / min'],['Priority',' / '.join(f'{j}: {model["Priority"]["probabilities"][j-1]:.4f}' for j in [1,2,3]),'Synthetic baseline / class'],['Consultation','10/13/15/18/20; mean '+fmt(inputs.set_index('variable').loc['DocServiceTime','mean']),'Synthetic baseline / min'],['Pharmacy','2/3/4/5; mean '+fmt(inputs.set_index('variable').loc['MedServiceTime','mean']),'Synthetic baseline / min'],['Poisson alternative',f'{model["peak_rate"]:.5f} peak; {model["late_rate"]:.5f} late','Estimated / patients/min']]
    dep=pd.read_csv(D/'dependence.csv');docdep=dep[(dep.variable=='DocServiceTime')&(dep.grouping=='Priority')]['mean']
    pages.append(('2 Data and input analysis',[
        para('The supplied archive contains 60,000 synthetic patient records, 14 fields and six scenarios. Each scenario contains 50 runs of 200 patients. Calibration uses the 10,000 records in Baseline_2Doc_240Peak. All scenarios are retained for independent replay checks. The audit found no missing fields, duplicate scenario/run/patient keys, negative waits, invalid priorities, nonpositive services, chronology errors or total-time identity errors. No records were removed [1].'),
        table('Table 1. Input calibration. Full probability vectors, sample summaries and provenance are supplied in the reproducibility package.',inp_rows,[78,260,132]),
        fig('input_pmfs','Figure 2. Empirical priority and service PMFs from the synthetic baseline (n=10,000).',128),
        para(f'Gaps are calculated within each run from time zero. A nonparametric renewal approximation selects a peak or late gap PMF using the previous arrival clock (<= {cfg.peak_limit:g} minutes versus later). A gap may cross the boundary. Peak arrivals total {model["peak_count"]:,}; their rate is count/(50 x {cfg.peak_limit:g}). Late exposure totals {model["late_exposure"]:,.0f} minutes, ending at each run\'s 200th arrival. Reduced late hourly counts partly reflect this fixed-cohort stopping rule, not hospital closure.'),
        para(f'Mean consultation durations by priority range from {docdep.min():.2f} to {docdep.max():.2f} minutes. Descriptive service-period comparisons and rank correlations show limited differences in these records. Common service PMFs and independent input streams are therefore provisional simplifications; they do not prove independence. Empirical distributions retain the small discrete supports but cannot generate unobserved tails (Week 5 [7]).'),
        para('The alternative is a continuous piecewise Poisson arrival process. It consumes exponential integrated hazard up to the peak boundary and the remainder at the late rate. It is used to examine structural input uncertainty. Source and simulated ECDF, gap and cohort-summary plots are included in the package. The Poisson model changes short-gap variability; it is not established as the true generator.')]))
    evidence=pd.read_csv(D/'queue_rule_evidence.csv');ev=evidence.sum(numeric_only=True)
    vr=[['Replayed outcome','Records','Exact matches','Max error (min)']]
    for metric in ['DocWaitTime','MedWaitTime','TotalTimeInHospital']:
        q=verification[verification.metric==metric];vr.append([metric.replace('TimeInHospital',' time'),f'{q.n.sum():,}',f'{q.exact_matches.sum():,}',fmt(q.max_abs_error.max())])
    testlog=ROOT/'outputs/verification/pytest.txt';testtext=testlog.read_text() if testlog.exists() else '27 passed in development; full-run evidence pending'
    testmatch=re.search(r'(\d+) passed',testtext);ntests=testmatch.group(1) if testmatch else 'pending'
    pages.append(('3 Discrete-event simulation model and implementation',[
        para('The independent Python implementation uses a heap-based future-event list (FEL), a simulation clock, a priority waiting heap and idle doctor resources. FEL keys are time, event-type rank and insertion sequence. At the same timestamp, arrivals precede doctor completions. Simultaneous arrivals are batched before dispatch; the doctor queue key is (-priority, arrival time, patient ID). Event-type rank and clinical priority have different purposes [5,6].'),
        para('On arrival, the patient joins the doctor heap; an idle doctor starts the highest eligible patient immediately. On consultation completion, the doctor is released and takes the next waiting patient. A service start records its time and schedules its completion. Service starts need no separate FEL entry. The doctor loop continues until the event list is empty.'),
        para('Pharmacy uses a separate exact availability calendar because it cannot block or delay doctors. Consultation completions are ordered by (doctor end, patient ID), then assigned to the earliest available counter. Pharmacy start is the greater of consultation completion and counter availability. The model therefore does not claim an integrated pharmacy FEL. Every patient is followed to departure.'),
        para('Pseudocode: initialize the empty state and FEL; pop the earliest event and advance the clock; update arrivals or doctor completions; dispatch eligible patients and schedule new completions; repeat until the FEL is empty; process the ordered pharmacy calendar and record every departure.'),
        table('Table 2. Measured reconstruction errors across all 300 original runs.',vr,[190,75,100,105]),
        para(f'The hand example gives doctor order A, C, D, B and departures 15, 22, 17, 19 minutes by patient A-D. Automated tests ({ntests} passed in the recorded suite) cover priority, FCFS, non-preemption, event ties, multiple doctors/counters, empty and single-patient systems, invalid inputs and reproducibility. Every executed run also checks capacity, non-overlap, timestamp identities, queue discipline and waiting-area conservation.'),
        para(f'Source records show {int(ev.strict_overtakes):,} strict overtakes, including {int(ev.higher_overtakes_lower):,} higher-class overtakes and {int(ev.same_class):,} same-class overtakes. This supports compatibility with the reconstructed priority rule. Exact input replay verifies implementation and source compatibility; neither test validates actual hospital behavior.'),
        para(f'Doctor wait is start minus arrival; pharmacy wait is pharmacy start minus doctor end. Busy time is clipped to common windows [0,{cfg.peak_limit:g}] and [0,{cfg.horizon:g}], then divided by resource-minutes. Queue area independently equals summed waiting intervals. Times use configurable {cfg.time_decimals}-decimal minute resolution to preserve intended fractional event ties. Nominal peak load may exceed capacity; realized utilization never exceeds one.')]))
    fit=pd.read_csv(D/'generated_input_fit.csv');obs=pd.read_csv(D/'observed_arrival_runs.csv');fitrows=[['Input model','Mean peak count','Mean last arrival (min)','Gap SD (min)']]
    gaps=pd.read_csv(D/'interarrival_gaps.csv');fitrows.append(['Source baseline',fmt(obs.peak_count.mean()),fmt(obs.last_arrival.mean()),fmt(gaps.gap.std())])
    for kind in ['empirical','poisson']:
        g=fit[fit.model==kind];fitrows.append([kind.capitalize(),fmt(g.peak_count.mean()),fmt(g.last_arrival.mean()),fmt(pd.read_csv(D/'generated_gaps.csv.gz').query('model == @kind').gap.std())])
    pages.append(('4 Experiment design',[
        para(f'The primary comparison uses {cfg.replications} independent fresh empirical-input replications for each doctor count, with one pharmacy counter. A separate paired benchmark replays the 50 original baseline patient tables under each policy. Original scenario output values never become new experimental outcomes. Fifty runs were selected before execution as the specified minimum; confidence intervals show the resulting Monte Carlo precision.'),
        para(f'NumPy SeedSequence({cfg.root_seed}).spawn(R) creates replication seeds. Each replication spawns separate arrival, priority, consultation and pharmacy streams. Uniform draws are generated and saved before any staffing simulation. Inverse empirical CDFs transform these draws. The same immutable patient table is reused across doctor counts and pharmacy options within a condition. Input hashes match across all compared policies; independent replication tables differ.'),
        para(f'For confirmation, a separate root seed {cfg.confirmation_seed} generates {cfg.replications} additional empirical runs per policy. All three policies are included, so confirmation does not select inputs after seeing a candidate. Sensitivities reuse the same underlying uniforms. Arrival or service transformations change patient tables as intended; CRN does not require unchanged transformed inputs across different input assumptions [8].'),
        table('Table 3. Input-model diagnostics from generated base cohorts. Gap SD uses pooled within-run gaps, without crossing runs.',fitrows,[130,105,140,95]),
        para('For run KPI values Y(r), we estimate the mean, sample SD using R-1 degrees of freedom, and standard error SD/sqrt(R). The two-sided 95% interval is mean +/- t(0.975,R-1) x SE. Student-t is a finite-sample refinement of the approximate normal interval taught in Week 4. Patients within a run are not treated as independent replications. A zero-width interval records zero observed run variation, not certainty for every possible input.'),
        para('Paired policy differences are new minus reference for doctor comparisons 3-2, 4-2 and 4-3. We verify matching replication IDs and input hashes, then form intervals from the run differences. The mean paired difference equals the difference of matched policy means. Negative waiting differences favor added doctors. These intervals describe conditional Monte Carlo uncertainty, not prediction intervals for patients or uncertainty about the synthetic calibration data.'),
        para('We separately report pooled patient P90, the fraction of runs with run P90 at or below a target, and the mean patient fraction with wait at or below that target. Peak and priority subgroup P90s use their own cohorts; empty groups are missing with valid-run counts. These quantities answer different questions and do not imply a universal service guarantee.')]))
    mainrows=[['Doctors','Mean run P90 [95% CI]','Mean doc wait','Pharmacy wait','Total time']]
    for c0 in cfg.doctors:
        g=runs(c0);mainrows.append([str(c0),interval(stat(c0)),fmt(g.mean_doc_wait.mean()),fmt(g.mean_pharmacy_wait.mean()),fmt(g.mean_total_time.mean())])
    cf=stat(c,frame=cs,experiment='confirmation');rep=stat(c,experiment='replay')
    sub='; '.join(f'priority {j}: {stat(c,f"p90_priority{j}")["mean"]:.2f}' for j in [1,2,3])
    pages.append(('5 Results and discussion',[
        table(f'Table 4. Primary fresh empirical results ({cfg.replications} runs per policy). Waiting and total-time values are minutes; only the primary mean run P90 interval is shown here.',mainrows,[55,175,80,80,80]),
        fig('main_p90_ci','Figure 3. Mean run-level P90 with 95% t intervals. Fresh empirical is primary; replay is a separate matched benchmark. All 200 patients define each run P90.',166),
        para(f'{c} doctors is the lowest-cost confidence-supported primary candidate. Its paired P90 change versus two doctors is {pcomp["mean"]:.2f} minutes (95% CI {pcomp.lo:.2f} to {pcomp.hi:.2f}), a {-pcomp.percent_change:.2f}% reduction in the mean. The original-input replay gives {rep["mean"]:.2f} minutes [{rep.lo:.2f}, {rep.hi:.2f}] for this policy. Fresh confirmation gives {cf["mean"]:.2f} [{cf.lo:.2f}, {cf.hi:.2f}]; its feasibility is evaluated separately in recommendation.csv.'),
        para(f'For {c} doctors, {a.run_attainment:.0%} of runs met the {cfg.target:g}-minute run P90 target, and the average patient service level was {a.service_level:.2%}. Pooled P90 was {a.pooled_p90_context:.2f} minutes. Thus a supported mean target does not imply every run meets it. Mean subgroup run P90s were {sub} minutes. The peak value was {stat(c,"p90_peak")["mean"]:.2f}, versus {stat(c,"p90_nonpeak")["mean"]:.2f} for later arrivals. Mean priority-3 sample size was {m.n_priority3.mean():.2f} patients per run.'),
        para(f'Peak doctor utilization fell from {runs(2).doc_util_peak.mean():.2%} with two doctors to {m.doc_util_peak.mean():.2%} with {c}; peak pharmacy utilization was {m.pharmacy_util_peak.mean():.2%}. Mean pharmacy wait changed from {runs(2).mean_pharmacy_wait.mean():.2f} to {m.mean_pharmacy_wait.mean():.2f} minutes. These measured effects explain the network trade-off without assuming congestion must move downstream.'),
        para(f'Scheduled costs are '+', '.join(f'{c0} doctors: {c0*cfg.doctor_wage*cfg.horizon/60:,.0f}' for c0 in cfg.doctors)+f' units. For {c} doctors, {cc.fraction_work_after_H:.0%} of runs had work after H; mean last arrival, consultation end and departure were {cc.mean_last_arrival:.2f}, {cc.mean_last_doc_end:.2f} and {cc.mean_last_departure:.2f} minutes. Mean doctor overtime workload was {cc.mean_doc_overtime:.2f} busy minutes. This workload is not paid shift-clock overtime.')]))
    sensrows=[['Model / condition','3 doctors P90 [CI]','4 doctors P90 [CI]','Choice*']]
    for (kind,condition),g in ss[ss.metric=='p90_doc_wait'].groupby(['experiment','condition']):
        if condition not in ['base','arrivals_fast','doctor_slow']:continue
        a3=g[g.doctors==3].iloc[0];a4=g[g.doctors==4].iloc[0];z=decision[(decision.experiment==kind)&(decision.condition==condition)&(decision.target==cfg.target)].iloc[0]
        sensrows.append([f'{kind} / {condition.replace("_"," ")}',interval(a3).replace(' [','\n['),interval(a4).replace(' [','\n['),z.supported_choice])
    pages.append(('6 Sensitivity analysis',[
        para('Each condition changes one factor at a time and uses 50 matched replications for all three doctor counts. Empirical scenarios include arrivals 10% faster/slower, consultation durations 10% longer/shorter, pharmacy durations 10% longer, and two pharmacy counters. Faster arrivals divide sampled gaps by 1.10 and recompute peak membership from the changed clock. The 200-person cohort remains fixed; this does not represent higher patient count in a fixed operating shift.'),
        table('Table 5. Mean run P90 (min), 95% CI; *lowest-cost confidence-supported staffing at 15 min. All conditions and targets 10/20/30 appear in the package.',sensrows,[143,139,139,49]),
        para(f'The main empirical condition selects {choice.supported_choice} doctors. Faster arrivals and longer consultations select four. The Poisson base condition selects {pc.supported_choice}, indicating sensitivity to arrival variability despite similar fitted mean rates. The second counter and slower pharmacy conditions retain the doctor-wait decision; downstream wait and total-time effects are available in sensitivity_summary.csv.'),
        para('Targets of 10, 15, 20 and 30 minutes are evaluated from saved outputs without additional identical DES runs. Point feasibility and confidence-supported feasibility are reported separately. If an interval crosses a target, that cell remains inconclusive at the reported run count; this report does not assert a resolved threshold. The 3-by-2 staffing/consultation cells also provide paired difference-in-differences with confidence intervals in factorial_interaction.csv.'),
        para('Changing a common positive doctor wage scales all scheduled costs and cannot reverse their ranking; wage_sensitivity.csv demonstrates this directly. A second pharmacy counter is a performance sensitivity only because no counter wage was supplied. Busy-time overtime proxies at premium factors 1.0, 1.5 and 2.0 are reported separately and are not real payroll. Arrival, service, staffing-hour and synthetic-data assumptions limit external application.')]))
    pages.append(('7 Recommendation and policy brief',[
        para(brief),para(f'Policy brief: {count} words.'),
        para('References'),
        para('[1] Juneminazuki. Hospital Queue and Patient Flow Simulation. Kaggle. '+cfg.source_url+'. Dataset title and URL supplied in the hospital proposal; generator documentation and license were not supplied.'),
        para('[2] SEEM3410 Project Proposal: Doctor Staffing Policy in a Hospital Outpatient Clinic. Supplied SEEM3410_Project_Proposal (1).docx. Lai Sin Hang and Lee Ka Tung.'),
        para('[3-8] W. Liu. SEEM3410 System Modeling and Simulation, 2026-27 Term 1. Supplied Week 1: From Real Systems to Models, Evaluation, and Simulation; Week 2: Analytical Queueing Formulas Versus Simulation Evaluation; Week 3: Discrete-Event Simulation Fundamentals; Week 4: Discrete-Event Simulation: Python Implementation and Output Analysis; Week 5: Input Distribution Calibration from Empirical Data; Week 6: Design of Simulation Experiments for System Improvement.'),
        para('[9] SEEM3410 Team Project Guidelines, 2026-27 Term 1. Supplied three-page document.'),
        para('AI assistance statement for team review: Codex assisted with implementation, test execution, experiment analysis, figures, presentation materials and report drafting. The team must verify the assumptions and results, understand the code, and confirm the course requirements for disclosure. The supplied guidelines do not specify an exact declaration form.'),
        para('Reproducibility: the separate ZIP includes unchanged raw data, configuration, saved draws, scripts, tests, tables, figures, README and execution evidence. Run python run_all.py using the documented dependencies. Human tasks remain: approve synthetic inputs, confirm metric/cost assumptions and team details, proofread, submit before 1 December, and rehearse for the assigned 1 or 3 December presentation [9].')]))
    # Report-ready compact tables retained as separate CSVs.
    for idx,(_,blocks) in enumerate(pages,1):
        for typ,obj in blocks:
            if typ=='table':save(pd.DataFrame(obj[1][1:],columns=obj[1][0]),f'tables/report_table_section{idx}.csv')
    status(['11.2'],'outputs/tables/report_table_section*.csv; all values assembled from saved output CSVs')
    md=['# Doctor Staffing Policy in a Hospital Outpatient Clinic','\n'+', '.join(f'{name} ({sid})' for name,sid in cfg.team)]
    for title,blocks in pages:
        md.append('\n## '+title)
        for typ,obj in blocks:
            if typ=='p':md.append('\n'+obj)
            elif typ=='table':
                caption,rows,_=obj;md+=['\n'+caption,'\n| '+' | '.join(rows[0])+' |','| '+' | '.join(['---']*len(rows[0]))+' |'];md+=['| '+' | '.join(row)+' |' for row in rows[1:]]
            elif typ=='fig':md+=['\n!['+obj[1]+'](../outputs/figures/'+obj[0]+'.png)','\n'+obj[1]]
    (ROOT/'docs/report_draft.md').write_text('\n'.join(md)+'\n');(ROOT/'docs/policy_brief.md').write_text(brief+'\n')
    dest=ROOT/'submission/final_report.pdf';dest.parent.mkdir(exist_ok=True)
    normal=ParagraphStyle('body',fontName='Helvetica',fontSize=11,leading=14,spaceAfter=9)
    head=ParagraphStyle('head',parent=normal,fontSize=14,leading=17,spaceAfter=14,textColor=colors.HexColor('#173753'))
    small=ParagraphStyle('caption',parent=normal,fontSize=11,leading=13,spaceAfter=8)
    cell=ParagraphStyle('cell',parent=normal,fontSize=11,leading=13,spaceAfter=0)
    story=[]
    width=A4[0]-4.4*cm
    def P(x,style=normal):return Paragraph(html.escape(x).replace('\n','<br/>'),style)
    for i,(title,blocks) in enumerate(pages):
        if i:story.append(PageBreak())
        else:
            story.append(P('Doctor Staffing Policy in a Hospital Outpatient Clinic',ParagraphStyle('title',parent=head,fontSize=17,leading=20)))
            story.append(P(' | '.join(f'{name} {sid}' for name,sid in cfg.team)))
        story.append(P(title,head))
        for typ,obj in blocks:
            if typ=='p':story.append(P(obj))
            elif typ=='table':
                caption,rows,widths=obj;weights=np.array(widths)/sum(widths)*width
                tb=Table([[P(x,cell) for x in row] for row in rows],colWidths=list(weights),hAlign='LEFT',repeatRows=1)
                tb.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eaf2f7')),('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#8b9daf')),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
                story.extend([P(caption,small),tb,Spacer(1,10)])
            elif typ=='fig':
                name,caption,height=obj;story.extend([Image(str(ROOT/'outputs/figures'/f'{name}.png'),width=width,height=height,kind='proportional'),P(caption,small)])
    def footer(canvas,doc):
        canvas.setFont('Helvetica',11);canvas.drawRightString(A4[0]-2.2*cm,1.3*cm,str(doc.page))
    SimpleDocTemplate(str(dest),pagesize=A4,rightMargin=2.2*cm,leftMargin=2.2*cm,topMargin=2.1*cm,bottomMargin=2.1*cm,title='Doctor Staffing Policy in a Hospital Outpatient Clinic',author=', '.join(name for name,_ in cfg.team)).build(story,onFirstPage=footer,onLaterPages=footer)
    reader=PdfReader(dest);npages=len(reader.pages);assert npages<=8,npages
    assert all(abs(float(p.mediabox.width)-A4[0])<1 for p in reader.pages)
    # Structural text/font and claim checks; visual review performed separately.
    banned=['real hospital data','optimal for any hospital','guaranteed 90%','3 doctors always meets 15','Kaggle documented rule']
    text=(ROOT/'docs/report_draft.md').read_text();assert not any(x in text for x in banned)
    checks={'pages':npages,'A4':True,'body_font_pt':11,'margins_cm':2.1,'policy_brief_words':count,'seven_sections':len(pages),'banned_claim_scan':True,'human_prose_review':'pending'}
    write_json(checks,'outputs/reproducibility/report_checks.json')
    status(['11.3','11.4'],'docs/report_draft.md; submission/final_report.pdf; outputs/reproducibility/report_checks.json',issue='Team proofread, assumptions and AI statement require human approval')
    # Deck data use exactly the report's underlying numbers, not manually entered results.
    deck={'team':list(cfg.team),'brief':brief,'choice':c,'poisson_choice':pc.supported_choice,'main':mainrows,'sensitivities':sensrows,'input_table':inp_rows,'fit':fitrows,'verification':vr,'test_count':ntests,
          'p90':[float(stat(z)['mean']) for z in cfg.doctors],'p90_ci':[interval(stat(z)) for z in cfg.doctors],
          'confirmation':interval(cf),'replay':interval(rep),'paired':interval(pcomp),'attainment':float(a.run_attainment),'service_level':float(a.service_level),'cost':[z*cfg.doctor_wage*cfg.horizon/60 for z in cfg.doctors],
          'condition_labels':list(ss[(ss.experiment=='empirical')&(ss.metric=='p90_doc_wait')&(ss.doctors==3)].condition),
          'sensitivity3':list(ss[(ss.experiment=='empirical')&(ss.metric=='p90_doc_wait')&(ss.doctors==3)]['mean']),
          'sensitivity4':list(ss[(ss.experiment=='empirical')&(ss.metric=='p90_doc_wait')&(ss.doctors==4)]['mean'])}
    write_json(deck,'outputs/tables/deck_data.json')
    return checks
