# Checklist status

Generated evidence log; PASS records execution, HUMAN REVIEW remains outstanding.

| Task | Status | Command | Evidence | Unresolved |
|---|---|---|---|---|
| 0 | PASS | `source inventory and text extraction` | docs/sources/; docs/assumptions.md | No starter ZIP supplied; unrelated Python keyword hits excluded |
| 1.1 | PASS | `python run_all.py` | config.py; docs/model_spec.md; docs/metrics.md; outputs/tables/policies.csv | None |
| 1.2 | PASS | `python run_all.py` | config.py; docs/model_spec.md; docs/metrics.md; outputs/tables/policies.csv | None |
| 1.3 | PASS | `python run_all.py` | config.py; docs/model_spec.md; docs/metrics.md; outputs/tables/policies.csv | None |
| 2.1 | PASS | `python run_all.py` | outputs/data/data_audit.json; cleaning_log.md | None |
| 2.2 | PASS | `python run_all.py` | outputs/data/baseline_inputs.csv; scenario_summary.csv; data_dictionary.csv | None |
| 2.3 | PASS | `python run_all.py` | outputs/data/arrival_profile.csv; interarrival_distribution.csv; observed_arrival_runs.csv | None |
| 2.4 | PASS | `python run_all.py` | outputs/data/input_summary.csv; input_distributions.csv; dependence.csv; spearman_dependence.csv; serial_dependence.csv | None |
| 2.5 | PASS | `python run_all.py` | outputs/data/calibration.json; arrival_timestamp_conditioning.csv; docs/assumptions.md | None |
| 2.6 | PASS | `python run_all.py` | outputs/data/queue_rule_evidence.csv; queue_rule_evidence.md | None |
| 2.7 | PASS | `python run_all.py` | outputs/tables/input_parameters.csv; docs/assumptions.md | None |
| 3.1 | PASS | `python run_all.py` | outputs/tables/capacity_analysis.csv; docs/analytical_checks.md | None |
| 3.2 | PASS | `python run_all.py` | outputs/tables/capacity_analysis.csv; docs/analytical_checks.md | None |
| 4.1 | PASS | `python run_all.py` | src/des.py; src/metrics.py; docs/des_pseudocode.md; outputs/verification/hand_trace.csv; pytest tests/test_des.py | None |
| 4.2 | PASS | `python run_all.py` | src/des.py; src/metrics.py; docs/des_pseudocode.md; outputs/verification/hand_trace.csv; pytest tests/test_des.py | None |
| 4.3 | PASS | `python run_all.py` | src/des.py; src/metrics.py; docs/des_pseudocode.md; outputs/verification/hand_trace.csv; pytest tests/test_des.py | None |
| 4.4 | PASS | `python run_all.py` | src/des.py; src/metrics.py; docs/des_pseudocode.md; outputs/verification/hand_trace.csv; pytest tests/test_des.py | None |
| 4.5 | PASS | `python run_all.py` | src/des.py; src/metrics.py; docs/des_pseudocode.md; outputs/verification/hand_trace.csv; pytest tests/test_des.py | None |
| 5.1 | PASS | `python run_all.py` | src/des.py; src/metrics.py; docs/des_pseudocode.md; outputs/verification/hand_trace.csv; pytest tests/test_des.py | None |
| 5.2 | PASS | `python run_all.py` | outputs/verification/verification_summary.csv; mismatches.csv; scenario_consistency.csv; 300 runs invariant checks | None |
| 5.3 | PASS | `python run_all.py` | outputs/verification/verification_summary.csv; mismatches.csv; scenario_consistency.csv; 300 runs invariant checks | None |
| 5.4 | PASS | `python run_all.py` | outputs/verification/verification_summary.csv; mismatches.csv; scenario_consistency.csv; 300 runs invariant checks | None |
| 6.1 | PASS | `python run_all.py` | outputs/experiments/seed_ledger.csv; base_uniforms.csv.gz; generated_base_inputs.csv.gz | None |
| 6.2 | PASS | `python run_all.py` | outputs/data/generated_input_fit.csv; generated_gaps.csv.gz; tests/test_inputs.py | None |
| 6.3 | PASS | `python run_all.py` | outputs/data/generated_input_fit.csv; generated_gaps.csv.gz; tests/test_inputs.py | None |
| 7.1 | PASS | `python run_all.py` | outputs/experiments/main_run_results.csv; replay_run_results.csv; corresponding *_patient_results.csv.gz; row/hash assertions | None |
| 7.2 | PASS | `python run_all.py` | outputs/experiments/main_run_results.csv; replay_run_results.csv; corresponding *_patient_results.csv.gz; row/hash assertions | None |
| 7.3 | PASS | `python run_all.py` | outputs/experiments/main_run_results.csv; replay_run_results.csv; corresponding *_patient_results.csv.gz; row/hash assertions | None |
| 6.1 | PASS | `python run_all.py` | outputs/experiments/seed_ledger.csv; base_uniforms.csv.gz; generated_base_inputs.csv.gz | None |
| 6.2 | PASS | `python run_all.py` | outputs/data/generated_input_fit.csv; generated_gaps.csv.gz; tests/test_inputs.py | None |
| 6.3 | PASS | `python run_all.py` | outputs/data/generated_input_fit.csv; generated_gaps.csv.gz; tests/test_inputs.py | None |
| 7.1 | PASS | `python run_all.py` | outputs/experiments/main_run_results.csv; replay_run_results.csv; corresponding *_patient_results.csv.gz; row/hash assertions | None |
| 7.2 | PASS | `python run_all.py` | outputs/experiments/main_run_results.csv; replay_run_results.csv; corresponding *_patient_results.csv.gz; row/hash assertions | None |
| 7.3 | PASS | `python run_all.py` | outputs/experiments/main_run_results.csv; replay_run_results.csv; corresponding *_patient_results.csv.gz; row/hash assertions | None |
| 8.1 | PASS | `python run_all.py` | outputs/tables/policy_summary.csv; priority_summary.csv; peak_summary.csv; paired_differences.csv; paired_ci.csv; target_achievement.csv; known-vector test | None |
| 8.2 | PASS | `python run_all.py` | outputs/tables/policy_summary.csv; priority_summary.csv; peak_summary.csv; paired_differences.csv; paired_ci.csv; target_achievement.csv; known-vector test | None |
| 8.3 | PASS | `python run_all.py` | outputs/tables/policy_summary.csv; priority_summary.csv; peak_summary.csv; paired_differences.csv; paired_ci.csv; target_achievement.csv; known-vector test | None |
| 8.4 | PASS | `python run_all.py` | outputs/tables/confirmation_summary.csv; confirmation_paired_ci.csv; root=93410; all 3 candidates; unresolved target-straddling cases explicitly flagged | None |
| 6.1 | PASS | `python run_all.py` | outputs/experiments/seed_ledger.csv; base_uniforms.csv.gz; generated_base_inputs.csv.gz | None |
| 6.2 | PASS | `python run_all.py` | outputs/data/generated_input_fit.csv; generated_gaps.csv.gz; tests/test_inputs.py | None |
| 6.3 | PASS | `python run_all.py` | outputs/data/generated_input_fit.csv; generated_gaps.csv.gz; tests/test_inputs.py | None |
| 7.1 | PASS | `python run_all.py` | outputs/experiments/main_run_results.csv; replay_run_results.csv; corresponding *_patient_results.csv.gz; row/hash assertions | None |
| 7.2 | PASS | `python run_all.py` | outputs/experiments/main_run_results.csv; replay_run_results.csv; corresponding *_patient_results.csv.gz; row/hash assertions | None |
| 7.3 | PASS | `python run_all.py` | outputs/experiments/main_run_results.csv; replay_run_results.csv; corresponding *_patient_results.csv.gz; row/hash assertions | None |
| 8.1 | PASS | `python run_all.py` | outputs/tables/policy_summary.csv; priority_summary.csv; peak_summary.csv; paired_differences.csv; paired_ci.csv; target_achievement.csv; known-vector test | None |
| 8.2 | PASS | `python run_all.py` | outputs/tables/policy_summary.csv; priority_summary.csv; peak_summary.csv; paired_differences.csv; paired_ci.csv; target_achievement.csv; known-vector test | None |
| 8.3 | PASS | `python run_all.py` | outputs/tables/policy_summary.csv; priority_summary.csv; peak_summary.csv; paired_differences.csv; paired_ci.csv; target_achievement.csv; known-vector test | None |
| 8.4 | PASS | `python run_all.py` | outputs/tables/confirmation_summary.csv; confirmation_paired_ci.csv; root=93410; all 3 candidates; unresolved target-straddling cases explicitly flagged | None |
| 9.1 | PASS | `python run_all.py` | outputs/experiments/sensitivity_run_results.csv; sensitivity_patient_results.csv.gz; sensitivity_inputs.csv.gz | None |
| 9.2 | PASS | `python run_all.py` | outputs/experiments/sensitivity_run_results.csv; sensitivity_patient_results.csv.gz; sensitivity_inputs.csv.gz | None |
| 9.3 | PASS | `python run_all.py` | outputs/tables/sensitivity_summary.csv; decision_matrix.csv; sensitivity_targets.csv; sensitivity_paired_ci.csv | None |
| 9.4 | PASS | `python run_all.py` | outputs/tables/factorial_interaction.csv; existing 3x2 cells reused | None |
| 10.1 | PASS | `python run_all.py` | outputs/tables/cost_summary.csv; wage_sensitivity.csv; recommendation.csv; explicit positive-wage ranking check | None |
| 10.2 | PASS | `python run_all.py` | outputs/tables/cost_summary.csv; wage_sensitivity.csv; recommendation.csv; explicit positive-wage ranking check | None |
| 10.3 | PASS | `python run_all.py` | outputs/tables/cost_summary.csv; wage_sensitivity.csv; recommendation.csv; explicit positive-wage ranking check | None |
| 11.1 | PASS | `python run_all.py` | outputs/figures/*.png and *.svg; captions.md; all figures read saved outputs | None |
| 11.2 | PASS | `python run_all.py` | outputs/tables/report_table_section*.csv; all values assembled from saved output CSVs | None |
| 11.3 | PASS | `python run_all.py` | docs/report_draft.md; submission/final_report.pdf; outputs/reproducibility/report_checks.json | Team proofread, assumptions and AI statement require human approval |
| 11.4 | PASS | `python run_all.py` | docs/report_draft.md; submission/final_report.pdf; outputs/reproducibility/report_checks.json | Team proofread, assumptions and AI statement require human approval |
| 11.1 | PASS | `python run_all.py` | outputs/figures/*.png and *.svg; captions.md; all figures read saved outputs | None |
| 11.2 | PASS | `python run_all.py` | outputs/tables/report_table_section*.csv; all values assembled from saved output CSVs | None |
| 11.3 | PASS | `python run_all.py` | docs/report_draft.md; submission/final_report.pdf; outputs/reproducibility/report_checks.json | Team proofread, assumptions and AI statement require human approval |
| 11.4 | PASS | `python run_all.py` | docs/report_draft.md; submission/final_report.pdf; outputs/reproducibility/report_checks.json | Team proofread, assumptions and AI statement require human approval |
