# 10-minute presentation

8 slides, 600 seconds. Lai Sin Hang: first four slides, 5 minutes. Lee Ka Tung: last four slides, 5 minutes. Timing is a rehearsal plan, not evidence of rehearsal.

## 1. Doctor staffing policy
Presenter: Lai Sin Hang; 60 seconds.

- Which of 2, 3, 4 doctors meets a 15-minute target at lowest cost?
- Primary metric: mean run-level P90 doctor wait
- Synthetic finite-run clinic; 200 patients

Speaker notes: Introduce the decision. Each P90 includes all patients in a run; average these values across replications. Explain that the target and wage are illustrative. Keep the synthetic-data limitation visible.

Sources: supplied hospital proposal, Week 1–6 SEEM3410 notes and outputs/tables.

## 2. Data and calibration
Presenter: Lai Sin Hang; 90 seconds.

- 60,000 synthetic records; six scenarios
- Calibration: 50 baseline runs, 10,000 patients
- Empirical gap, priority and service PMFs

Speaker notes: Show input_pmfs.png and arrival_profile.png. Explain previous-clock conditioning, rates from exposure and fixed-200 stopping. Source data estimate inputs; recorded waits never enter the simulator. Common service PMFs are provisional after descriptive dependence checks.

Sources: supplied hospital proposal, Week 1–6 SEEM3410 notes and outputs/tables.

## 3. DES model
Presenter: Lai Sin Hang; 80 seconds.

- Priority 3 > 2 > 1; non-preemptive consultation
- FCFS within class; FCFS pharmacy
- 200 arrivals, empty start, complete drain

Speaker notes: Walk through system_flow.svg. Explain state, clock, future-event list, priority waiting heap and immediate starts. Pharmacy is an exact separate availability calendar with no blocking feedback. Arrivals precede completions at a tie; patient priority is different from event rank.

Sources: supplied hospital proposal, Week 1–6 SEEM3410 notes and outputs/tables.

## 4. Verification evidence
Presenter: Lai Sin Hang; 70 seconds.

- 31 automated tests
- 60,000/60,000 exact matches for each wait and total time
- All-run resource, queue and conservation checks

Speaker notes: Use verification_summary.csv. Explain the hand order A,C,D,B and departures15,22,17,19. Tests cover ties, non-preemption, capacities, invalid inputs and drain. Exact source replay is compatibility with synthetic records; it is not clinical validation.

Sources: supplied hospital proposal, Week 1–6 SEEM3410 notes and outputs/tables.

## 5. Experiment design and CRN
Presenter: Lee Ka Tung; 70 seconds.

- 50 fresh replications per policy; root 3410
- Matched patient tables and input hashes
- Independent confirmation root 93410

Speaker notes: Same replication means identical patient inputs across staffing. Four separate streams avoid policy-dependent draws. New replication seeds are independent. Student-t confidence intervals use run-level statistics; paired differences are proposal minus reference. Sensitivities share underlying uniforms after transformation.

Sources: supplied hospital proposal, Week 1–6 SEEM3410 notes and outputs/tables.

## 6. Primary results
Presenter: Lee Ka Tung; 100 seconds.

- 2 doctors: 359.82 [350.32, 369.32] min
- 3 doctors: 11.33 [8.72, 13.93] min
- 4 doctors: 0.00 [0.00, 0.00] min
- Confirmation for 3 doctors: 10.00 [8.00, 12.01] min
- Run attainment: 76%; patient service level: 93.94%

Speaker notes: Show main_p90_ci.png and report_table_section5.csv. The paired 3-2 change is -348.49 [-356.94, -340.04] minutes. Compare illustrative scheduled costs [3600.0, 5400.0, 7200.0]. Distinguish primary fresh generation, replay and independent confirmation. Discuss subgroup peak waits and the small measured pharmacy wait increase. Zero observed P90 variation is not universal certainty.

Sources: supplied hospital proposal, Week 1–6 SEEM3410 notes and outputs/tables.

## 7. Sensitivity
Presenter: Lee Ka Tung; 80 seconds.

- Faster arrivals and longer consultations select four doctors
- Poisson base selects 4 doctors
- Targets 10/15/20/30 evaluated from saved outputs

Speaker notes: Show sensitivity.png and decision_matrix.csv. Each empirical perturbation changes one factor. Rate increases compress the same 200-person cohort; they do not add patients within a fixed shift. Continuous Poisson gaps add variability. Two counters is performance-only because its wage is not defined. Call out confidence-straddling target cells as inconclusive.

Sources: supplied hospital proposal, Week 1–6 SEEM3410 notes and outputs/tables.

## 8. Recommendation and limitation
Presenter: Lee Ka Tung; 50 seconds.

- Provisional empirical policy: 3 doctors
- Review four doctors under changed input conditions
- Collect actual timing records before real deployment

Speaker notes: Use 3 doctors as the provisional staffing policy when the calibrated empirical arrival pattern applies. Across 50 fresh matched replications, its mean run-level P90 doctor wait was 11.33 minutes (95% confidence interval 8.72 to 13.93), compared with 359.82 minutes for two doctors. The paired mean reduction was 348.49 minutes. Scheduled doctor cost rises from 3,600 to 5,400 illustrative units for the common 18-hour schedule. The policy met the 15-minute run P90 target in 76% of simulated runs; this is not a guarantee for every run. Retain capacity to review a fourth doctor if arrivals accelerate or consultations lengthen. The Poisson arrival alternative selected 4 doctors, so arrival variability materially affects the decision. Before implementation, collect actual arrival and service records, confirm queue rules and staffing hours, and repeat the analysis. The principal limitation is that all calibration records are synthetic. The confidence intervals measure simulation uncertainty conditional on fitted inputs and do not establish clinical validity or real payroll costs.

Sources: supplied hospital proposal, Week 1–6 SEEM3410 notes and outputs/tables.

## Six likely questions

**Why priority and event rank?** Patient class chooses the next waiting patient. Event rank orders simultaneous FEL events; arrivals precede completions.

**Why continue after 240 minutes?** 240 is the peak boundary. The finite cohort has exactly 200 arrivals and the simulation ends only after all pharmacy departures.

**Why empirical and Poisson models?** Discrete source gaps justify empirical calibration. Poisson is a structurally different sensitivity with higher short-gap variability, not a proven source generator.

**What does CRN change?** It matches input realizations within each replication across policies. Paired differences then estimate staffing effects with conditional Monte Carlo uncertainty.

**Does mean P90<=15 guarantee 90% every run?** No. For the selected primary policy, run attainment was 76% and average patient service level was 93.94%. Mean run P90, pooled P90 and these fractions differ.

**Are costs real payroll?** No. Scheduled cost uses an illustrative positive common wage and horizon. Busy-minute overtime is only a proxy; staff remain to drain, and no second-counter wage is specified.
