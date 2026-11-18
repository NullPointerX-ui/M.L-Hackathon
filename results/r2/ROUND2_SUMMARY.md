# PathSnap Round 2 Summary

Generated from committed Round 2 result files. Reliable-point Top-1 means eligible points in trips labelled `ok`; all-point Top-1 is shown separately. Student-test was not used for selection.

## Pipeline

| Stage | Method / output | Evidence |
| --- | --- | --- |
| Data quality | TRAIN-only label threshold | `results/r2/label_threshold.json` |
| Feature engineering | Ablation and 31-feature set | `results/r2/ablation.csv` |
| Model comparison | Five classifiers; GroupKFold by trip | `results/r2/model_comparison_v2_full.csv` |
| Bayesian HPO | Optuna TPE on LightGBM | `results/r2/hpo_best.json` |
| Route decoding | HMM + Viterbi | `results/r2/hmm_comparison.csv` |
| Inference | Per-trip timing | `results/r2/inference_check.csv` |
| Maps | Best, median, worst examples | `results/r2/maps_index.csv` |

## 2. Dataset understanding, EDA and preprocessing

The point reliability threshold was selected using TRAIN only: alignment distance > 50.0 m marks a point unreliable. A trip is low quality when median alignment distance > 30.0 m or its unreliable-point fraction > 25.00%. The Round 1 threshold was 148.08 m. Sources: `results/r2/label_threshold.json`, `results/r2/label_changes.csv`, `results/r2/label_quality_trips.csv`.

TRAIN points over the threshold: 1116.42%; accepted TRAIN-trip points over threshold: 138.87%. Source: `results/r2/label_threshold.json`.

Round 1 XGBoost baseline:
| Partition / scope | Points | Top-1 | Candidate miss |
| --- | --- | --- | --- |
| TRAIN CV reliable accepted trips | 180715 | 88.08% | 0.18% |
| TRAIN CV all points | 208417 | 77.89% | 10.94% |
| Student-test reliable accepted trips | 15202 | 86.88% | 0.08% |
| Student-test all points | 19160 | 77.25% | 11.16% |

The final feature set has 31 features. Kept groups: heading, temporal, graph; dropped groups: smooth, along, relative. Original 13-feature CV eligible Top-1: 88.10%; final set: 91.31%. Sources: `results/r2/feature_set_v2.json`, `results/r2/ablation.csv`, `results/r2/feature_importance_v2.csv`.

## 3. Model experimentation and comparison

| Model | Algorithm family | Key configuration | CV Macro F1 | CV Top-1 reliable | CV Top-1 all | ST Top-1 reliable | ST Top-1 all | ST Macro F1 | ST log loss | Inference ms/1k |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LightGBM | Boosting | <=500 rounds, lr 0.05, 63 leaves, early stop 30 (10% group holdout) | 94.81% | 91.23% | 81.32% | 89.81% | 79.78% | 94.11% | 0.0569 | 18.40 |
| XGBoost | Boosting (GPU) | <=500 rounds, lr 0.05, depth 8, hist, early stop 30 (10% group holdout) | 94.77% | 91.17% | 81.25% | 89.94% | 79.89% | 94.13% | 0.0565 | 3.71 |
| RandomForest | Ensemble (bagging) | 200 trees, max_depth=20, min_samples_leaf=5 | 94.51% | 90.92% | 81.20% | 89.73% | 79.66% | 93.42% | 0.0608 | 34.01 |
| MLP | Neural network | hidden (64,32), relu, adam, early_stopping | 94.10% | 90.53% | 80.68% | 90.59% | 80.30% | 93.88% | 0.0647 | 4.54 |
| LogisticRegression | Linear | class_weight=balanced, C=1, lbfgs; median impute + scale | 86.33% | 89.60% | 80.15% | 87.56% | 77.61% | 86.31% | 0.1494 | 2.56 |

The train-minus-CV gaps are recorded in `results/r2/model_comparison_v2_full.csv`; none exceeded 5 percentage points. Selection was pre-registered and student-test was not used. Initial contenders: LightGBM, XGBoost, RandomForest; provisional HPO model: LightGBM. The v2 comparison ran five models: LogisticRegression, RandomForest, LightGBM, XGBoost and MLP. KNN, ExtraTrees and XGBRanker were not run. Isotonic calibration was not adopted; see `results/r2/calibration_v2.csv`.

## 4. Bayesian hyperparameter optimisation

Model: LightGBM; sampler: TPE(seed=42); pruner: MedianPruner(n_startup_trials=3). Trials requested/completed/pruned: 10/5/5. CV: GroupKFold(3) by trip, train only. Objective: mean CV Top-1 on eligible points. Best parameters: `{"colsample_bytree": 0.6558555380447055, "learning_rate": 0.011240768803005551, "min_child_samples": 12, "n_estimators": 1000, "num_leaves": 197, "reg_alpha": 0.00023641892308789696, "reg_lambda": 0.12030178871154672, "subsample": 0.831261142176991}`. Sources: `results/r2/hpo_best.json`, `results/r2/hpo_trials.csv`.

| Metric | Untuned | Tuned |
| --- | --- | --- |
| CV eligible Top-1 | 91.44% | 91.44% |
| CV Macro F1 | 94.94% | 94.94% |
| Student-test eligible Top-1 | 89.76% | 89.76% |
| Student-test all-point Top-1 | 79.78% | 79.78% |
| Student-test Macro F1 | 94.02% | 94.02% |
| Student-test log loss | 0.0570 | 0.0570 |
| Inference ms / 1k | 18.69 | 18.69 |

Tuned CV Top-1 gain: 0.000000. Tuned student-test eligible Top-1 was lower; tuned inference was 1.0x slower. The pre-registered CV rule selected tuned LightGBM for HMM; student-test was not used.

## 5. HMM and Viterbi route reconstruction

Candidate road arcs are hidden states. Classifier probabilities provide emissions; transitions use a bounded road-network shortest-path lattice. Viterbi decoding runs in log space with break/restart handling. Parameters tuned on TRAIN LightGBM OOF: tau=1.380, beta=22.815, v_max=75.033 m/s, gap threshold=30.0 s, subgraph=400.0 m, cutoff=2000.0 m, back epsilon=15.0 m. Source: `results/r2/hmm_params.json`.

| Model / partition | Reliable Top-1 classifier | Reliable Top-1 HMM | All Top-1 classifier | All Top-1 HMM | Route F1 classifier | Route F1 HMM | Continuity classifier | Continuity HMM | Breaks |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LightGBM TRAIN OOF | 91.43% | 92.83% | 80.86% | 82.11% | 0.8991 | 0.9260 | 76.90% | 88.71% | 535 |
| LightGBM student-test | 89.44% | 90.21% | 79.54% | 80.55% | 0.9091 | 0.9321 | 79.15% | 89.84% | 7 |
| XGBoost TRAIN OOF | 91.31% | 92.92% | 80.69% | 82.21% | 0.8979 | 0.9269 | 76.85% | 88.77% | 535 |
| XGBoost student-test | 89.84% | 90.60% | 79.86% | 80.88% | 0.9081 | 0.9326 | 79.60% | 89.95% | 7 |

Final selection: XGBoost using TRAIN OOF HMM Top-1. RandomForest was not decoded due to time; decoder parameters were tuned on LightGBM OOF and reused for XGBoost. TRAIN HMM values are slightly optimistic because decoder tuning used TRAIN trips. Sources: `results/r2/hmm_selection.json`, `results/r2/hmm_comparison.csv`.

## 6. Geographical visualisation using Folium

| Trip | Example | Classifier reliable Top-1 | HMM reliable Top-1 | HMM route F1 | HMM continuity | Interactive map |
| --- | --- | --- | --- | --- | --- | --- |
| 00000077 | worst | 79.93% | 78.19% | 0.9403 | 91.33% | `maps\r2\student_test_00000077_worst.html` |
| 00000091 | median | 92.22% | 94.97% | 0.8627 | 84.78% | `maps\r2\student_test_00000091_median.html` |
| 00000052 | best | 98.85% | 100.00% | 0.9266 | 87.65% | `maps\r2\student_test_00000052_best.html` |

Maps are committed HTML outputs with the route layers and controls described in the repository. Source: `results/r2/maps_index.csv`.

## 7. API, UI and deployment

Largest measured trip: 19313 points in 13.11 s. Slowest measured student-test trip: 3958 points in 1.02 s. Source: `results/r2/inference_check.csv`.

The repository progress log records FastAPI and Streamlit integration. Insert actual UI and receiving-laptop API screenshots into the final PDF; this script does not fabricate screenshots.

## Limitations and protocol notes

- Student-test was not used for model selection.
- Decoder parameters were tuned on TRAIN LightGBM OOF emissions and reused for XGBoost; TRAIN HMM results are slightly optimistic.
- RandomForest was not decoded due to time.
- KNN, ExtraTrees and XGBRanker were not run in the v2 comparison.
- HMM can hurt individual trips; see `results/r2/hmm_per_trip.csv`.
- Missing-value analysis and API/UI screenshots must be supplied separately if required; no values are invented here.
