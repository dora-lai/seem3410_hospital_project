# Final review — Hospital Outpatient Clinic

All required computational phases executed. See CHECKLIST_STATUS.md for task IDs, evidence and commands. No software claim of course submission, professor approval or live rehearsal is made.

## Completed and outstanding items

- PASS: phases 1–10, audit/calibration, capacity, independent DES, exact source replay, random generation/CRN, primary and replay experiments, run-level inference, fresh confirmation, required sensitivities, optional factorial interaction, costs and computed decisions.
- PASS: phase 11 seven-section report source/PDF, generated numerical tables and figures, policy-brief count and claim scan; visual QA recorded separately.
- PASS: phase 12 presentation outline, editable slide materials, two 5-minute allocations, six Q&A, README, course mapping and portable packaging checks (see evidence below).
- HUMAN REVIEW: confirm synthetic inputs acceptable; approve assumptions, metric/cost definitions, team details and AI statement; authors understand code; proofread report; course submission; assigned date and live rehearsal.
- Optional calibration bootstrap/holdout and controlled long-run M/M/1 benchmark omitted; neither is required. No external hospital validation or generator/license documentation was available.

## Actual primary and replay results

Mean run-level P90 doctor wait, minutes; two-sided 95% Student-t interval, independent runs.

| Experiment | Doctors | R | Mean | 95% CI |
|---|---:|---:|---:|---|
| empirical | 2 | 50 | 359.820 | [350.318, 369.322] |
| empirical | 3 | 50 | 11.326 | [8.722, 13.930] |
| empirical | 4 | 50 | 0.000 | [0.000, 0.000] |
| replay | 2 | 50 | 360.884 | [349.686, 372.082] |
| replay | 3 | 50 | 10.598 | [8.334, 12.862] |
| replay | 4 | 50 | 0.000 | [0.000, 0.000] |
| confirmation | 2 | 50 | 360.256 | [349.039, 371.473] |
| confirmation | 3 | 50 | 10.002 | [7.998, 12.006] |
| confirmation | 4 | 50 | 0.000 | [0.000, 0.000] |

Primary paired differences (new minus reference), minutes:
- 3-2: -348.494 [-356.944, -340.044].
- 4-2: -359.820 [-369.322, -350.318].
- 4-3: -11.326 [-13.930, -8.722].

| Doctors | Run attainment at 15 | Mean patient service level | Pooled P90 context (min) |
|---|---:|---:|---:|
| 2 | 0.0% | 35.50% | 360.00 |
| 3 | 76.0% | 93.94% | 9.00 |
| 4 | 100.0% | 100.00% | 0.00 |

## Verification

- Automated suite: **31 passed in 1.42s**. Log: outputs/verification/pytest.txt.
- Exact matches: 60,000/60,000 each for doctor wait, pharmacy wait and total hospital time; maximum absolute error 0 min. All 300 original runs checked with their own staffing/peak settings.
- Hand example matched doctor order A,C,D,B, waits 0/14/8/10, pharmacy waits 0/0/2/2 and departures 15/22/17/19. Trace retained.
- Every executed run checks all patients depart, nonnegative waits, interval identities, resource bounds/non-overlap, eligible priority/FCFS ordering, pharmacy FCFS and waiting-area conservation. Source replay is synthetic compatibility, not hospital validation.

## Recommendation and sensitivity
Primary point-estimate choice: **3 doctors**. Lowest-cost confidence-supported choice: **3 doctors**. The recommendation is derived by enumeration in src/analysis.py, with the primary model fixed before results.

| Model / condition | 3-doctor P90 [95% CI] | 4-doctor P90 [95% CI] | Supported choice at 15 |
|---|---|---|---|
| empirical / arrivals_fast | 38.473 [33.579, 43.367] | 0.343 [0.180, 0.505] | 4 |
| empirical / arrivals_slow | 2.512 [1.941, 3.082] | 0.000 [0.000, 0.000] | 3 |
| empirical / base | 11.326 [8.722, 13.930] | 0.000 [0.000, 0.000] | 3 |
| empirical / doctor_fast | 2.523 [1.967, 3.079] | 0.000 [0.000, 0.000] | 3 |
| empirical / doctor_slow | 37.155 [32.128, 42.181] | 0.279 [0.127, 0.431] | 4 |
| empirical / pharmacy_slow | 11.326 [8.722, 13.930] | 0.000 [0.000, 0.000] | 3 |
| empirical / two_counters | 11.326 [8.722, 13.930] | 0.000 [0.000, 0.000] | 3 |
| poisson / arrivals_fast | 70.088 [56.172, 84.005] | 11.277 [9.219, 13.335] | 4 |
| poisson / base | 40.481 [31.706, 49.256] | 6.911 [5.853, 7.968] | 4 |
| poisson / doctor_slow | 72.820 [58.122, 87.518] | 11.856 [9.742, 13.970] | 4 |

Replay and fresh empirical generation support the same baseline staffing choice; Poisson has substantially more variable gaps and selects four doctors. Faster empirical arrivals and longer consultations also change the choice to four. Independent empirical confirmation agrees with the main conclusion. Source staffing scenarios use distinct inputs and are not paired experimental rows.

Target-straddling sensitivity cells: **5**. See decision_matrix.csv for the specific 10/15/20/30-minute targets. These cells remain explicitly inconclusive at 50 runs; confidence-supported choices may differ from point choices. Main 15-minute selection has a resolved interval and independent confirmation.

## Assumptions and limitations
All are documented in docs/assumptions.md and configurable in config.py where numerical: synthetic calibration; empirical finite support; independent input mechanisms/common service PMFs; previous-clock arrival-gap conditioning; boundary-crossing convention; 200-patient empty-start cohort; no warm-up; priority 3 highest/non-preemptive/within-class FCFS; specified simultaneous-event and resource ties; one-way FCFS pharmacy; no breaks/abandonment/rejection/appointments/travel/blocking; staff remain until drain; illustrative 15-minute target; wage 100 units/doctor-hour and 1080-minute common schedule; counter sensitivity has no wage; nine-decimal-minute clock resolution. Poisson changes input structure, not truth status. Arrival-rate sensitivities compress/expand 200 arrivals rather than increase fixed-horizon demand. Late exposure ends at the 200th arrival. Monte Carlo intervals do not quantify calibration uncertainty or real-hospital outcomes.

Scheduled costs: 3,600/5,400/7,200 units. Common positive wage changes preserve ranking. Overtime busy minutes and optional premiums 1/1.5/2 are proxies, not payroll. Slower-arrival and some Poisson inputs extend past the assumed schedule; arrivals_after_H and work_after_H flag this and no outcomes are censored. No real currency or wage threshold is invented.

## Deliverables and reproduction
- submission/final_report.pdf: 7 A4 pages, body 11 pt, margins>=2.1cm, page numbers; policy brief 160 words.
- docs/report_draft.md and docs/policy_brief.md: editable text. Submission PDF is kept separate from code/data ZIP.
- submission/presentation.pptx (editable native evidence and notes), presentation.html, docs/presentation_outline.md; optional authoring source in tools/. No live PowerPoint/rehearsal claim.
- submission/SEEM3410_reproducibility.zip: source/config/tests, unchanged raw archive, original course/project sources, saved inputs, numerical outputs, figures and slide materials. Excludes environment/cache/build/temp files and PDFs.
- outputs/reproducibility: run_log.txt, environment.json, acceptance.json, row_counts.csv, output_manifest.csv, deterministic_hashes.json and extraction_check.json.

Commands from project folder:

```sh
python -m pip install -r requirements.txt
python -m pytest -q
python run_all.py --smoke
python run_all.py
```

Full numerical/report workflow without recursively packaging: `python run_all.py --no-package`. No local absolute path or online service is required for calculations. Optional PPTX rebuild requires the Codex Artifact Tool runtime; HTML slides, report PDF, all computations and figures use the documented Python requirements.

Extracted-package check: {
  "status": "PASS",
  "full_extracted_run": true,
  "exit_code": 0,
  "deterministic_artifacts_compared": 62,
  "mismatching_hashes": 0,
  "wall_seconds": 57.06468345801113,
  "extracted_tests": "31 passed in 2.31s",
  "archive_members_initial": 7262,
  "local_absolute_path_dependency": false
}

## Human review / not completed by software

1. Obtain professor acceptance of entirely synthetic inputs; no approval is implied.
2. Confirm primary metric, 15-minute target, synthetic queue discipline and illustrative staffing cost/horizon.
3. Confirm supplied team names/IDs: Lai Sin Hang 1155213900, Lee Ka Tung 1155212062.
4. Review AI assistance statement and any course declaration requirement; both authors must understand the simulation and statistical methods.
5. Proofread final report and slide content; review conditional three-versus-four recommendation before submission.
6. Submit report PDF and separate ZIP through the course platform before 1 December 2026, subject to professor confirmation.
7. Confirm assigned 1 or 3 December 2026 presentation slot and rehearse 10 minutes (5 minutes each). Neither submission nor rehearsal has been performed.
