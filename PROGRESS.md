# PathSnap Round 2 - progress log

Factual status per step. Numbers are copied from the result files named in each line.
Round 1 state is tagged `round1-demo`; Round 1 outputs are untouched; Round 2 outputs live in `*/r2/`.

## Phase 1 - data foundation (done, commit 97f6894)
- Frozen label rules from TRAIN only (`src/pathsnap/labels/quality.py`): point unreliable if align_dist_m > 50 m;
  trip low_quality if median > 30 m or > 25% unreliable. Evidence: `reports/figures/r2/label_threshold.png`.
- Low-quality trips: train 00000033, 00000054; student_test 00000056 (`results/r2/label_changes.csv`).
- Shared training size: 36,000 points (~306k rows) per fit (`results/r2/train_size_benchmark.csv`, `train_size_decision.json`).
- Round 1 XGBoost config on new labels: CV Top-1 0.8808 (eligible), 0.7789 (all points); student_test 0.8688 / 0.7725
  (`results/r2/top1_by_scope_r1model.csv`). Errors: reverse twin 42.9%, adjacent arc 33.3%, other 22.2%,
  candidate miss 1.6% (CV; `results/r2/error_analysis.csv`).

## Phase 2 - features v2 (done, commit e767fee)
- 30 v2 features in 6 groups (`src/pathsnap/features_v2.py`), label-free, built per trip (`scripts/r2_build_features_v2.py`).
- Ablation (`results/r2/ablation.csv`, rule pre-registered in `ablation_rule.json`): all 15 runs completed.
  original 13: 0.8810; all 43: 0.9141; kept set: 0.9131 CV Top-1 (eligible).
- Kept groups: heading, temporal, graph (31 features, `results/r2/feature_set_v2.json`). Dropped: smooth, along, relative
  (leave-one-out drop < 0.001).
- Known redundancy: v2_hcos_2 / v2_habs_2 are identical to heading_cos / heading_abs (kept; harmless for trees).
- FINAL feature set for the rest of Round 2 (deadline decision 12:30): the 31 features above. No further ablation.

## Phase 3 - model comparison (in progress)
- Scope cut for the deadline: exactly 5 models (LogisticRegression, RandomForest, LightGBM, XGBoost, MLP),
  same 36,000-point sample per fit, same 31 features, GroupKFold(5) by trip, n_jobs <= 4.
- Done (commit below), runtime 640 s, n_jobs 4. `results/r2/model_comparison_v2.csv` (deliverables 3.1 columns),
  `model_comparison_v2_full.csv`, `cv_folds_v2.csv`, `calibration_v2.csv`, figures in `reports/figures/r2/*_v2.png`.
- CV Top-1 (eligible) / train-fold / student_test Top-1: LightGBM 0.9123 / 0.9398 / 0.8981; XGBoost 0.9117 / 0.9390 / 0.8994;
  RandomForest 0.9092 / 0.9342 / 0.8973; MLP 0.9053 / 0.9301 / 0.9059; LogisticRegression 0.8960 / 0.8985 / 0.8756.
- Overfit check: largest train-CV gap 2.75 pts (LightGBM); none > 5 pts.
- Isotonic calibration (inside CV) did not help: CV log loss LightGBM 0.0583 -> 0.0595, XGBoost 0.0578 -> 0.0596. Use raw probabilities.
- Selection (rule pre-registered in `selection_rule_v2.json`): LightGBM, XGBoost, RandomForest within 0.005 CV Top-1 ->
  deferred to Phase 5 (HMM); provisional pick for HPO: LightGBM (`selection_v2.json`).
- Not run (deadline cut): KNN, ExtraTrees, XGBRanker (code exists in `src/pathsnap/models/zoo.py`).
