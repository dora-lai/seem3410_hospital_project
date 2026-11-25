"""Portable 10-minute outline and editable HTML slides; PPTX is separately authored."""
import json,html
from config import ROOT,CFG
from src.common import write_json,status

def presentation(cfg=CFG):
    d=json.loads((ROOT/'outputs/tables/deck_data.json').read_text())
    slides=[
      ('Doctor staffing policy',60,'Lai Sin Hang',['Which of 2, 3, 4 doctors meets a 15-minute target at lowest cost?','Primary metric: mean run-level P90 doctor wait','Synthetic finite-run clinic; 200 patients'],
       'Introduce the decision. Each P90 includes all patients in a run; average these values across replications. Explain that the target and wage are illustrative. Keep the synthetic-data limitation visible.'),
      ('Data and calibration',90,'Lai Sin Hang',['60,000 synthetic records; six scenarios','Calibration: 50 baseline runs, 10,000 patients','Empirical gap, priority and service PMFs'],
       'Show input_pmfs.png and arrival_profile.png. Explain previous-clock conditioning, rates from exposure and fixed-200 stopping. Source data estimate inputs; recorded waits never enter the simulator. Common service PMFs are provisional after descriptive dependence checks.'),
      ('DES model',80,'Lai Sin Hang',['Priority 3 > 2 > 1; non-preemptive consultation','FCFS within class; FCFS pharmacy','200 arrivals, empty start, complete drain'],
       'Walk through system_flow.svg. Explain state, clock, future-event list, priority waiting heap and immediate starts. Pharmacy is an exact separate availability calendar with no blocking feedback. Arrivals precede completions at a tie; patient priority is different from event rank.'),
      ('Verification evidence',70,'Lai Sin Hang',[f'{d["test_count"]} automated tests','60,000/60,000 exact matches for each wait and total time','All-run resource, queue and conservation checks'],
       'Use verification_summary.csv. Explain the hand order A,C,D,B and departures15,22,17,19. Tests cover ties, non-preemption, capacities, invalid inputs and drain. Exact source replay is compatibility with synthetic records; it is not clinical validation.'),
      ('Experiment design and CRN',70,'Lee Ka Tung',['50 fresh replications per policy; root 3410','Matched patient tables and input hashes','Independent confirmation root 93410'],
       'Same replication means identical patient inputs across staffing. Four separate streams avoid policy-dependent draws. New replication seeds are independent. Student-t confidence intervals use run-level statistics; paired differences are proposal minus reference. Sensitivities share underlying uniforms after transformation.'),
      ('Primary results',100,'Lee Ka Tung',[f'{i+2} doctors: {v} min' for i,v in enumerate(d['p90_ci'])]+[f'Confirmation for {d["choice"]} doctors: {d["confirmation"]} min',f'Run attainment: {d["attainment"]:.0%}; patient service level: {d["service_level"]:.2%}'],
       f'Show main_p90_ci.png and report_table_section5.csv. The paired 3-2 change is {d["paired"]} minutes. Compare illustrative scheduled costs {d["cost"]}. Distinguish primary fresh generation, replay and independent confirmation. Discuss subgroup peak waits and the small measured pharmacy wait increase. Zero observed P90 variation is not universal certainty.'),
      ('Sensitivity',80,'Lee Ka Tung',['Faster arrivals and longer consultations select four doctors',f'Poisson base selects {d["poisson_choice"]} doctors','Targets 10/15/20/30 evaluated from saved outputs'],
       'Show sensitivity.png and decision_matrix.csv. Each empirical perturbation changes one factor. Rate increases compress the same 200-person cohort; they do not add patients within a fixed shift. Continuous Poisson gaps add variability. Two counters is performance-only because its wage is not defined. Call out confidence-straddling target cells as inconclusive.'),
      ('Recommendation and limitation',50,'Lee Ka Tung',[f'Provisional empirical policy: {d["choice"]} doctors','Review four doctors under changed input conditions','Collect actual timing records before real deployment'],d['brief'])]
    assert len(slides)==8 and sum(x[1] for x in slides)==600
    qa=[('Why priority and event rank?', 'Patient class chooses the next waiting patient. Event rank orders simultaneous FEL events; arrivals precede completions.'),
        ('Why continue after 240 minutes?', '240 is the peak boundary. The finite cohort has exactly 200 arrivals and the simulation ends only after all pharmacy departures.'),
        ('Why empirical and Poisson models?', 'Discrete source gaps justify empirical calibration. Poisson is a structurally different sensitivity with higher short-gap variability, not a proven source generator.'),
        ('What does CRN change?', 'It matches input realizations within each replication across policies. Paired differences then estimate staffing effects with conditional Monte Carlo uncertainty.'),
        ('Does mean P90<=15 guarantee 90% every run?', f'No. For the selected primary policy, run attainment was {d["attainment"]:.0%} and average patient service level was {d["service_level"]:.2%}. Mean run P90, pooled P90 and these fractions differ.'),
        ('Are costs real payroll?', 'No. Scheduled cost uses an illustrative positive common wage and horizon. Busy-minute overtime is only a proxy; staff remain to drain, and no second-counter wage is specified.')]
    md=['# 10-minute presentation','\n8 slides, 600 seconds. Lai Sin Hang: first four slides, 5 minutes. Lee Ka Tung: last four slides, 5 minutes. Timing is a rehearsal plan, not evidence of rehearsal.']
    sections=[]
    for i,(title,secs,name,bullets,note) in enumerate(slides,1):
        md+= [f'\n## {i}. {title}',f'Presenter: {name}; {secs} seconds.','\n'+'\n'.join('- '+x for x in bullets),'\nSpeaker notes: '+note,'\nSources: supplied hospital proposal, Week 1–6 SEEM3410 notes and outputs/tables.']
        sections.append('<section><small>SEEM3410 · Synthetic clinic · '+name+'</small><h1>'+html.escape(title)+'</h1><ul>'+''.join('<li>'+html.escape(b)+'</li>' for b in bullets)+'</ul><details><summary>Speaker notes</summary><p>'+html.escape(note)+'</p></details><footer>'+str(i)+' / 8</footer></section>')
    md+=['\n## Six likely questions']+[f'\n**{q}** {a}' for q,a in qa]
    (ROOT/'docs/presentation_outline.md').write_text('\n'.join(md)+'\n')
    htmlout='<!doctype html><html lang="en"><meta charset="utf-8"><title>SEEM3410 staffing presentation</title><style>body{margin:0;background:#eaf2f7;color:#173753;font:24px Arial,sans-serif}section{box-sizing:border-box;background:white;position:relative;min-height:720px;padding:56px 70px;margin:20px auto;max-width:1280px}h1{font-size:44px;line-height:1.15}li{font-size:30px;margin:24px 0}small,footer{font-size:18px;color:#4b5a68}footer{position:absolute;bottom:24px;right:50px}details{font-size:18px;line-height:1.4}@media print{section{page-break-after:always;margin:0}details{display:none}}</style>'+''.join(sections)+'</html>'
    (ROOT/'submission/presentation.html').write_text(htmlout)
    write_json({'slides':8,'planned_seconds':600,'presenters':{'Lai Sin Hang':300,'Lee Ka Tung':300},'qa_count':len(qa),'rehearsal':'HUMAN REVIEW'},'outputs/reproducibility/presentation_plan.json')
    status(['12.1'],'docs/presentation_outline.md; submission/presentation.html; submission/presentation.pptx (separate editable rendering)',issue='Live rehearsal and assigned date are human tasks')
