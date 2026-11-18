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

## Phase 4 - HPO (done)
- Optuna TPE (seed 42) on LightGBM, 10 trials (5 complete, 5 pruned by MedianPruner), GroupKFold(3) by trip, n_jobs 4,
  timeout 480 s; HPO compute 252 s (`results/r2/hpo_trials.csv`, `hpo_best.json`, `optuna.db`, `reports/figures/r2/hpo_history.png`).
- Tuned vs untuned, both refit on all 1,519,806 eligible train rows (`results/r2/hpo_tuned_vs_untuned.csv`):
  CV Top-1 0.9151 vs 0.9144; ST Top-1 0.8944 vs 0.8976; ST macro-F1 0.9393 vs 0.9402; ST log loss 0.0579 vs 0.0570;
  inference 540 vs 18.7 ms / 1k points.
- Rule (CV Top-1) selects TUNED for the HMM. Note: the CV gain (+0.0007) is well inside the fold std (0.014) and tuned is
  29x slower; student_test was not used to choose.

## Phase 5 - HMM + Viterbi (done)
- `src/pathsnap/hmm/` (lattice of network distances via bounded Dijkstra on a 400 m road subgraph, cached in
  data/processed/r2/hmm_cache; Viterbi in log space with break/restart). Toy tests: `tests/test_viterbi.py`.
- Emissions: train = out-of-fold (GroupKFold 5) probabilities; student_test = model refit on all eligible train rows.
- Decoder params tuned by Optuna TPE (25 trials) on TRAIN only (LightGBM OOF): tau 1.38, beta 22.8, v_max 75 m/s
  (`results/r2/hmm_params.json`, `hmm_trials.csv`).
- `results/r2/hmm_comparison.csv` (Top-1 on eligible points, classifier -> HMM):
  XGBoost train-OOF 0.9131 -> 0.9292 (decoder tuned on train); student_test 0.8984 -> 0.9060.
  LightGBM train-OOF 0.9143 -> 0.9283; student_test 0.8944 -> 0.9021.
  All points (XGBoost, student_test): 0.7986 -> 0.8088. Route F1 0.908 -> 0.933; continuity 0.796 -> 0.900.
- Selection (pre-registered: contenders within 0.005 decided after HMM on train OOF): XGBoost (0.9292 vs 0.9283).
  Deviations: RandomForest not decoded (time); decoder params tuned on LightGBM OOF and shared with XGBoost.
- HMM hurt on some train trips (e.g. 00000079: 0.961 -> 0.837); 535 breaks on train (315 of them in low_quality
  trip 00000054), 7 on student_test. See `results/r2/hmm_per_trip.csv`.

## Phase 6/7 - inference + API (done)
- `src/pathsnap/inference.py` (`Predictor.predict_trip`, reads only .track/.nodes/.arcs); no-label-import test passes.
- Artifacts `artifacts/r2/`: xgb_selected.json (XGBoost refit on all eligible train rows), feature_spec.json,
  hmm_config.json, versions.json. Largest trip (19,313 points) 13.1 s; all 10 student_test trips <= 1.0 s
  (`results/r2/inference_check.csv`).
- API = teammate's FastAPI skeleton (branch api-ui, files api/ ui/ tools/) with the dummy block replaced by
  predict_trip + separate evaluator `pathsnap.eval.server_eval` (only server code that reads .route; returns aggregates).
  JSON errors, model loaded at startup, structured log line per request. `tests/test_api_smoke.py` passes.
- UI (Streamlit, teammate's ui/app.py extended): HMM / classifier-only / confidence-coloured GPS layers, metric cards, session table.

## Step 5 - maps + README (done)
- `scripts/r2_make_maps.py` -> `maps/r2/student_test_{00000052_best,00000091_median,00000077_worst}.html` (raw GPS,
  road network, reference, classifier-only, HMM; legend + LayerControl). 00000077 is also the trip where the HMM hurt
  (0.799 -> 0.782, `results/r2/maps_index.csv`).
- README: Round 2 section (results table generated by `scripts/r2_summary_table.py`, reproduce commands, two-laptop
  demo with firewall/IP steps, structure). `scripts/run_all_r2.py` (Round 1 `run_all.py` unchanged). optuna pinned.
- Live check: API on 0.0.0.0:8000 served /health, /trips, /predict (859 ms for 00000065) and logged the evaluator line;
  Streamlit UI served HTTP 200 on 8501.

- Round 2 report generator, summary, and findings completed and committed.
