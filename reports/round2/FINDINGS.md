# Round 2 Findings

## §2 Data/EDA and preprocessing
- Point reliability threshold: > 50.0 m. Source: `results/r2/label_threshold.json`.
- Low-quality trip rule: median > 30.0 m OR unreliable fraction > 25.00%. Source: `results/r2/label_threshold.json`.
- Threshold selected from TRAIN only. Source: `results/r2/label_threshold.json`.
- TRAIN points above threshold: 1116.42%. Source: `results/r2/label_threshold.json`.
- Accepted TRAIN-trip points above threshold: 138.87%. Source: `results/r2/label_threshold.json`.
- Round 1 TRAIN CV baseline: reliable accepted-trip Top-1 88.08%; all-point Top-1 77.89%. Source: `results/r2/top1_by_scope_r1model.csv`.
- Round 1 student-test baseline: reliable accepted-trip Top-1 86.88%; all-point Top-1 77.25%. Source: `results/r2/top1_by_scope_r1model.csv`.
- Final feature count: 31; retained groups: heading, temporal, graph; dropped groups: smooth, along, relative. Source: `results/r2/feature_set_v2.json`.
- Ablation CV eligible Top-1: original 88.10%; final 91.31%. Source: `results/r2/ablation.csv`.
- Missing-value statistics are not contained in the inspected result files. Source checked: `results/r2/label_quality_trips.csv`.

## §3 Model comparison
- LightGBM: CV reliable Top-1 91.23%; CV all-point Top-1 81.32%; student-test reliable Top-1 89.81%; student-test all-point Top-1 79.78%; student-test Macro F1 94.11%; log loss 0.0569; train-CV gap 2.75 points. Source: `results/r2/model_comparison_v2_full.csv`.
- XGBoost: CV reliable Top-1 91.17%; CV all-point Top-1 81.25%; student-test reliable Top-1 89.94%; student-test all-point Top-1 79.89%; student-test Macro F1 94.13%; log loss 0.0565; train-CV gap 2.72 points. Source: `results/r2/model_comparison_v2_full.csv`.
- RandomForest: CV reliable Top-1 90.92%; CV all-point Top-1 81.20%; student-test reliable Top-1 89.73%; student-test all-point Top-1 79.66%; student-test Macro F1 93.42%; log loss 0.0608; train-CV gap 2.50 points. Source: `results/r2/model_comparison_v2_full.csv`.
- MLP: CV reliable Top-1 90.53%; CV all-point Top-1 80.68%; student-test reliable Top-1 90.59%; student-test all-point Top-1 80.30%; student-test Macro F1 93.88%; log loss 0.0647; train-CV gap 2.49 points. Source: `results/r2/model_comparison_v2_full.csv`.
- LogisticRegression: CV reliable Top-1 89.60%; CV all-point Top-1 80.15%; student-test reliable Top-1 87.56%; student-test all-point Top-1 77.61%; student-test Macro F1 86.31%; log loss 0.1494; train-CV gap 0.25 points. Source: `results/r2/model_comparison_v2_full.csv`.

## §4 Bayesian HPO
- Model/sampler/pruner: LightGBM / TPE(seed=42) / MedianPruner(n_startup_trials=3). Source: `results/r2/hpo_best.json`.
- Trials requested/completed/pruned: 10/5/5. Source: `results/r2/hpo_best.json`.
- Objective: mean CV Top-1 on eligible points. Source: `results/r2/hpo_best.json`.
- Best parameters: `{"colsample_bytree": 0.6558555380447055, "learning_rate": 0.011240768803005551, "min_child_samples": 12, "n_estimators": 1000, "num_leaves": 197, "reg_alpha": 0.00023641892308789696, "reg_lambda": 0.12030178871154672, "subsample": 0.831261142176991}`. Source: `results/r2/hpo_best.json`.
- CV reliable Top-1 tuned/untuned: 91.44%/91.44%. Source: `results/r2/hpo_tuned_vs_untuned.csv`.
- Student-test reliable Top-1 tuned/untuned: 89.76%/89.76%. Source: `results/r2/hpo_tuned_vs_untuned.csv`.
- Inference ms/1k tuned/untuned: 18.69/18.69. Source: `results/r2/hpo_tuned_vs_untuned.csv`.

## §5 HMM/Viterbi
- Parameters: tau 1.380, beta 22.815, v_max 75.033 m/s, gap threshold 30.0 s. Source: `results/r2/hmm_params.json`.
- Tuning source: train trips only (LightGBM out-of-fold emissions). Source: `results/r2/hmm_params.json`.
- XGBoost student-test reliable Top-1 classifier/HMM: 89.84%/90.60%. Source: `results/r2/hmm_comparison.csv`.
- XGBoost student-test all-point Top-1 classifier/HMM: 79.86%/80.88%. Source: `results/r2/hmm_comparison.csv`.
- XGBoost student-test route F1 classifier/HMM: 0.9081/0.9326. Source: `results/r2/hmm_comparison.csv`.
- XGBoost student-test continuity classifier/HMM: 79.60%/89.95%. Source: `results/r2/hmm_comparison.csv`.
- Breaks TRAIN/student-test: 535/7. Source: `results/r2/hmm_comparison.csv`.
- Selected model: XGBoost. Source: `results/r2/hmm_selection.json`.

## §6 Folium maps
- Trip 00000077 (worst): classifier reliable Top-1 79.93%; HMM reliable Top-1 78.19%; map `maps\r2\student_test_00000077_worst.html`. Source: `results/r2/maps_index.csv`.
- Trip 00000091 (median): classifier reliable Top-1 92.22%; HMM reliable Top-1 94.97%; map `maps\r2\student_test_00000091_median.html`. Source: `results/r2/maps_index.csv`.
- Trip 00000052 (best): classifier reliable Top-1 98.85%; HMM reliable Top-1 100.00%; map `maps\r2\student_test_00000052_best.html`. Source: `results/r2/maps_index.csv`.

## §7 API/UI/deployment
- Largest trip: 19313 points, 13.11 s. Source: `results/r2/inference_check.csv`.
- Slowest student-test trip: 3958 points, 1.02 s. Source: `results/r2/inference_check.csv`.
- Screenshots must come from the actual running API/UI. Source: `docs/deliverables.md`.

## Known issues / limitations
- Student-test was not used for model selection. Source: `results/r2/selection_v2.json`.
- Decoder tuned on TRAIN LightGBM OOF and shared with XGBoost. Source: `results/r2/hmm_params.json` and `results/r2/hmm_selection.json`.
- RandomForest not HMM-decoded due to time. Source: `results/r2/hmm_selection.json`.
- Worst indexed trip 00000077: reliable Top-1 79.93% to 78.19% after HMM. Source: `results/r2/maps_index.csv`.
- Only five models run; KNN, ExtraTrees and XGBRanker not run. Source: `PROGRESS.md`.
- Isotonic calibration not adopted. Source: `results/r2/calibration_v2.csv`.
- Missing-value analysis and screenshots require separate evidence. Source: `docs/deliverables.md`.
