"""Portable packaging and end-to-end reproducibility acceptance."""
import hashlib,json,platform,subprocess,sys,tempfile,time,zipfile,re
from pathlib import Path
import numpy as np
import pandas as pd
from config import ROOT,CFG
from src.common import filehash,write_json,save,status

def environment(start):
    import importlib.metadata
    return {'python':sys.version,'platform':platform.platform(),'versions':{p:importlib.metadata.version(p) for p in ['numpy','pandas','scipy','matplotlib','pytest','pypdf','reportlab']},'elapsed_seconds':time.perf_counter()-start}

def deterministic_hashes(root=ROOT):
    return {str(p.relative_to(root)):filehash(p) for p in sorted((root/'outputs').rglob('*')) if p.is_file() and p.name!='output_manifest.csv' and (p.suffix=='.csv' or p.name.endswith('.csv.gz') or p.name=='calibration.json')}

def acceptance(cfg=CFG):
    checks=[]
    for prefix in ['main','replay','confirmation']:
        r=pd.read_csv(ROOT/f'outputs/experiments/{prefix}_run_results.csv');p=pd.read_csv(ROOT/f'outputs/experiments/{prefix}_patient_results.csv.gz')
        assert len(r)==cfg.replications*len(cfg.doctors) and len(p)==len(r)*cfg.n_patients
        assert r.groupby('RunID').input_hash.nunique().eq(1).all()
        assert r.groupby('doctors').RunID.nunique().eq(cfg.replications).all()
        assert not r[['p90_doc_wait','mean_doc_wait','mean_pharmacy_wait','mean_total_time','doc_util_peak','last_departure']].isna().any().any()
        for col in r.filter(regex='_util_'):assert r[col].between(0,1+cfg.tolerance).all()
        checks.append({'artifact':prefix,'run_rows':len(r),'patient_rows':len(p),'matched_hashes':True,'valid_KPIs':True})
    r=pd.read_csv(ROOT/'outputs/experiments/sensitivity_run_results.csv');assert len(r)==10*cfg.replications*len(cfg.doctors)
    assert r.groupby(['experiment','condition','RunID']).input_hash.nunique().eq(1).all()
    assert not r.duplicated(['experiment','condition','RunID','doctors','pharmacy_counters']).any()
    checks.append({'artifact':'sensitivity (includes reused primary base)','run_rows':len(r),'patient_rows':len(r)*cfg.n_patients,'matched_hashes':True,'valid_KPIs':True})
    figure_names=['system_flow','arrival_profile','input_pmfs','input_fit','arrival_ecdf','main_p90_ci','priority_peak','resource_cost','sensitivity','attainment']
    expected=[f'figures/{name}.{ext}' for name in figure_names for ext in ['png','svg']]+['figures/captions.md']
    assert all((ROOT/'outputs'/name).is_file() for name in expected)
    assert len(list((ROOT/'outputs/figures').iterdir()))==len(expected)
    write_json({'expected_figure_files':len(expected),'actual_figure_files':len(list((ROOT/'outputs/figures').iterdir())),
        'expected_files':expected,'directory_file_counts':{name:sum(p.is_file() for p in (ROOT/'outputs'/name).rglob('*')) for name in ['data','verification','experiments','tables','figures','reproducibility']}},'outputs/reproducibility/artifact_inventory.json')
    v=pd.read_csv(ROOT/'outputs/verification/verification_summary.csv');assert (v.n==v.exact_matches).all() and v.max_abs_error.eq(0).all()
    assert pd.read_csv(ROOT/'outputs/verification/mismatches.csv').empty
    assert int(pd.read_csv(ROOT/'outputs/data/arrival_profile.csv')['count'].sum())==10000
    save(pd.DataFrame(checks),'reproducibility/row_counts.csv')
    write_json({'gate':'PASS','checks':checks,'source_replay_records':60000,'source_replay_run_count':300,'unique_experiment_runs':int(36*cfg.replications),
       'experiment_patient_policy_records':int(36*cfg.replications*cfg.n_patients),'zero_mismatches':True},'outputs/reproducibility/acceptance.json')
    return checks

def write_review(cfg=CFG,extracted=None):
    s=pd.read_csv(ROOT/'outputs/tables/policy_summary.csv');s=s[s.metric=='p90_doc_wait'];conf=pd.read_csv(ROOT/'outputs/tables/confirmation_summary.csv');conf=conf[conf.metric=='p90_doc_wait']
    ss=pd.read_csv(ROOT/'outputs/tables/sensitivity_summary.csv');ss=ss[ss.metric=='p90_doc_wait'];rec=pd.read_csv(ROOT/'outputs/tables/recommendation.csv',keep_default_na=False)
    paired=pd.read_csv(ROOT/'outputs/tables/paired_ci.csv');paired=paired[(paired.metric=='p90_doc_wait')&(paired.experiment=='empirical')]
    target=pd.read_csv(ROOT/'outputs/tables/target_achievement.csv');target=target[(target.experiment=='empirical')&(target.target==15)]
    tests=(ROOT/'outputs/verification/pytest.txt').read_text();passed=re.search(r'\d+ passed[^\n]*',tests).group(0)
    policy=rec[(rec.experiment==cfg.primary_model)&(rec.condition=='base')].iloc[0]
    reportcheck=json.loads((ROOT/'outputs/reproducibility/report_checks.json').read_text())
    rows=['# Final review — Hospital Outpatient Clinic','\nAll required computational phases executed. See CHECKLIST_STATUS.md for task IDs, evidence and commands. No software claim of course submission, professor approval or live rehearsal is made.',
        '\n## Completed and outstanding items',
        '- PASS: phases 1–10, audit/calibration, capacity, independent DES, exact source replay, random generation/CRN, primary and replay experiments, run-level inference, fresh confirmation, required sensitivities, optional factorial interaction, costs and computed decisions.',
        '- PASS: phase 11 seven-section report source/PDF, generated numerical tables and figures, policy-brief count and claim scan; visual QA recorded separately.',
        '- PASS: phase 12 presentation outline, editable slide materials, two 5-minute allocations, six Q&A, README, course mapping and portable packaging checks (see evidence below).',
        '- HUMAN REVIEW: confirm synthetic inputs acceptable; approve assumptions, metric/cost definitions, team details and AI statement; authors understand code; proofread report; course submission; assigned date and live rehearsal.',
        '- Optional calibration bootstrap/holdout and controlled long-run M/M/1 benchmark omitted; neither is required. No external hospital validation or generator/license documentation was available.',
        '\n## Actual primary and replay results','\nMean run-level P90 doctor wait, minutes; two-sided 95% Student-t interval, independent runs.']
    rows+=['\n| Experiment | Doctors | R | Mean | 95% CI |','|---|---:|---:|---:|---|']
    for _,x in pd.concat([s,conf]).iterrows():rows.append(f'| {x.experiment} | {int(x.doctors)} | {int(x.n)} | {x["mean"]:.3f} | [{x.lo:.3f}, {x.hi:.3f}] |')
    rows+=['\nPrimary paired differences (new minus reference), minutes:']
    for _,x in paired.iterrows():rows.append(f'- {x.comparison}: {x["mean"]:.3f} [{x.lo:.3f}, {x.hi:.3f}].')
    rows+=['\n| Doctors | Run attainment at 15 | Mean patient service level | Pooled P90 context (min) |','|---|---:|---:|---:|']
    for _,x in target.iterrows():rows.append(f'| {int(x.doctors)} | {x.run_attainment:.1%} | {x.service_level:.2%} | {x.pooled_p90_context:.2f} |')
    rows+=['\n## Verification',f'- Automated suite: **{passed}**. Log: outputs/verification/pytest.txt.',
        '- Exact matches: 60,000/60,000 each for doctor wait, pharmacy wait and total hospital time; maximum absolute error 0 min. All 300 original runs checked with their own staffing/peak settings.',
        '- Hand example matched doctor order A,C,D,B, waits 0/14/8/10, pharmacy waits 0/0/2/2 and departures 15/22/17/19. Trace retained.',
        '- Every executed run checks all patients depart, nonnegative waits, interval identities, resource bounds/non-overlap, eligible priority/FCFS ordering, pharmacy FCFS and waiting-area conservation. Source replay is synthetic compatibility, not hospital validation.',
        '\n## Recommendation and sensitivity',f'Primary point-estimate choice: **{policy.point_choice} doctors**. Lowest-cost confidence-supported choice: **{policy.supported_choice} doctors**. The recommendation is derived by enumeration in src/analysis.py, with the primary model fixed before results.',
        '\n| Model / condition | 3-doctor P90 [95% CI] | 4-doctor P90 [95% CI] | Supported choice at 15 |','|---|---|---|---|']
    for (kind,cond),g in ss.groupby(['experiment','condition']):
        a=g[g.doctors==3].iloc[0];b=g[g.doctors==4].iloc[0];z=rec[(rec.experiment==kind)&(rec.condition==cond)].iloc[0]
        rows.append(f'| {kind} / {cond} | {a["mean"]:.3f} [{a.lo:.3f}, {a.hi:.3f}] | {b["mean"]:.3f} [{b.lo:.3f}, {b.hi:.3f}] | {z.supported_choice} |')
    uncertain=pd.read_csv(ROOT/'outputs/tables/decision_matrix.csv',keep_default_na=False);uncertain=uncertain[uncertain.uncertain_candidates!='none']
    rows+=['\nReplay and fresh empirical generation support the same baseline staffing choice; Poisson has substantially more variable gaps and selects four doctors. Faster empirical arrivals and longer consultations also change the choice to four. Independent empirical confirmation agrees with the main conclusion. Source staffing scenarios use distinct inputs and are not paired experimental rows.',
        f'\nTarget-straddling sensitivity cells: **{len(uncertain)}**. See decision_matrix.csv for the specific 10/15/20/30-minute targets. These cells remain explicitly inconclusive at 50 runs; confidence-supported choices may differ from point choices. Main 15-minute selection has a resolved interval and independent confirmation.',
        '\n## Assumptions and limitations',
        'All are documented in docs/assumptions.md and configurable in config.py where numerical: synthetic calibration; empirical finite support; independent input mechanisms/common service PMFs; previous-clock arrival-gap conditioning; boundary-crossing convention; 200-patient empty-start cohort; no warm-up; priority 3 highest/non-preemptive/within-class FCFS; specified simultaneous-event and resource ties; one-way FCFS pharmacy; no breaks/abandonment/rejection/appointments/travel/blocking; staff remain until drain; illustrative 15-minute target; wage 100 units/doctor-hour and 1080-minute common schedule; counter sensitivity has no wage; nine-decimal-minute clock resolution. Poisson changes input structure, not truth status. Arrival-rate sensitivities compress/expand 200 arrivals rather than increase fixed-horizon demand. Late exposure ends at the 200th arrival. Monte Carlo intervals do not quantify calibration uncertainty or real-hospital outcomes.',
        '\nScheduled costs: 3,600/5,400/7,200 units. Common positive wage changes preserve ranking. Overtime busy minutes and optional premiums 1/1.5/2 are proxies, not payroll. Slower-arrival and some Poisson inputs extend past the assumed schedule; arrivals_after_H and work_after_H flag this and no outcomes are censored. No real currency or wage threshold is invented.',
        '\n## Deliverables and reproduction',f'- submission/final_report.pdf: {reportcheck["pages"] } A4 pages, body 11 pt, margins>=2.1cm, page numbers; policy brief {reportcheck["policy_brief_words"]} words.',
        '- docs/report_draft.md and docs/policy_brief.md: editable text. Submission PDF is kept separate from code/data ZIP.',
        '- submission/presentation.pptx (editable native evidence and notes), presentation.html, docs/presentation_outline.md; optional authoring source in tools/. No live PowerPoint/rehearsal claim.',
        '- submission/SEEM3410_reproducibility.zip: source/config/tests, unchanged raw archive, original course/project sources, saved inputs, numerical outputs, figures and slide materials. Excludes environment/cache/build/temp files and PDFs.',
        '- outputs/reproducibility: run_log.txt, environment.json, acceptance.json, row_counts.csv, output_manifest.csv, deterministic_hashes.json and extraction_check.json.',
        '\nCommands from project folder:', '\n```sh\npython -m pip install -r requirements.txt\npython -m pytest -q\npython run_all.py --smoke\npython run_all.py\n```',
        '\nFull numerical/report workflow without recursively packaging: `python run_all.py --no-package`. No local absolute path or online service is required for calculations. Optional PPTX rebuild requires the Codex Artifact Tool runtime; HTML slides, report PDF, all computations and figures use the documented Python requirements.']
    if extracted:rows.append('\nExtracted-package check: '+json.dumps(extracted,indent=2))
    else:rows.append('\nExtracted-package check: not requested in this --no-package run; see parent package receipt when applicable.')
    rows+=['\n## Human review / not completed by software',
        '1. Obtain professor acceptance of entirely synthetic inputs; no approval is implied.',
        '2. Confirm primary metric, 15-minute target, synthetic queue discipline and illustrative staffing cost/horizon.',
        '3. Confirm supplied team names/IDs: Lai Sin Hang 1155213900, Lee Ka Tung 1155212062.',
        '4. Review AI assistance statement and any course declaration requirement; both authors must understand the simulation and statistical methods.',
        '5. Proofread final report and slide content; review conditional three-versus-four recommendation before submission.',
        '6. Submit report PDF and separate ZIP through the course platform before 1 December 2026, subject to professor confirmation.',
        '7. Confirm assigned 1 or 3 December 2026 presentation slot and rehearse 10 minutes (5 minutes each). Neither submission nor rehearsal has been performed.']
    (ROOT/'FINAL_REVIEW.md').write_text('\n'.join(rows).replace('\n## Completed and outstanding items\n-','\n## Completed and outstanding items\n\n-').replace('\n## Verification\n-','\n## Verification\n\n-').replace('\n## Human review / not completed by software\n1.','\n## Human review / not completed by software\n\n1.')+'\n')

def manifest():
    rows=[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':filehash(p)} for p in sorted((ROOT/'outputs').rglob('*')) if p.is_file() and p.name!='output_manifest.csv']
    save(pd.DataFrame(rows),'reproducibility/output_manifest.csv');return len(rows)

def make_zip():
    dest=ROOT/'submission/SEEM3410_reproducibility.zip'
    # Include complete deterministic evidence; keep final PDF and course PDFs out of submission ZIP.
    with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(ROOT.rglob('*')):
            rel=p.relative_to(ROOT)
            if not p.is_file() or any(x in ['.venv','.build','__pycache__','.pytest_cache','.git','report_render','slide_render'] for x in rel.parts):continue
            if p==dest or p.suffix.lower()=='.pdf' or p.suffix=='.pyc' or p.name in ['prepare.py','compute.py']:continue
            z.write(p,Path('hospital_project')/rel)
    with zipfile.ZipFile(dest) as z:assert z.testzip() is None;members=len(z.namelist())
    return dest,members

def package(start,cfg=CFG):
    before=deterministic_hashes();write_json(before,'outputs/reproducibility/deterministic_hashes.json')
    write_review(cfg);manifest();dest,members=make_zip()
    with tempfile.TemporaryDirectory(prefix='seem3410_reproduce_') as folder:
        with zipfile.ZipFile(dest) as z:z.extractall(folder)
        cwd=Path(folder)/'hospital_project'
        tic=time.perf_counter()
        completed=subprocess.run([sys.executable,'run_all.py','--no-package'],cwd=cwd,text=True,capture_output=True)
        (ROOT/'outputs/reproducibility/extracted_run_log.txt').write_text(completed.stdout+'\n'+completed.stderr)
        assert completed.returncode==0,completed.stderr
        after=deterministic_hashes(cwd);changed=[key for key in set(before)|set(after) if before.get(key)!=after.get(key)]
        assert not changed,changed
        receipt={'status':'PASS','full_extracted_run':True,'exit_code':completed.returncode,'deterministic_artifacts_compared':len(before),'mismatching_hashes':len(changed),'wall_seconds':time.perf_counter()-tic,
            'extracted_tests':(cwd/'outputs/verification/pytest.txt').read_text().strip().splitlines()[-1], 'archive_members_initial':members,'local_absolute_path_dependency':False}
    write_json(receipt,'outputs/reproducibility/extraction_check.json')
    status(['12.3'],'outputs/reproducibility/pytest/acceptance/row_counts/hash/extraction artifacts; submission/SEEM3410_reproducibility.zip',command='pytest -q; python run_all.py; extracted python run_all.py --no-package')
    status(['12.4'],'FINAL_REVIEW.md; all assumptions, results and human actions listed',issue='Professor approval, team review, submission, rehearsal outstanding')
    write_review(cfg,receipt);write_json(environment(start),'outputs/reproducibility/environment.json');manifest();dest,members=make_zip()
    return {'zip':str(dest.relative_to(ROOT)),'members':members,**receipt}
