# results/

Every file here is written by a script in `scripts/`; no numbers are typed by hand.

## Start here
| File | What it is |
|---|---|
| `r2/ROUND2_SUMMARY.md` | Round 2 summary (final pipeline: classifier + HMM) |
| `r2/FINDINGS.md` | Round 2 facts per report section, each with its source file |
| `r2/summary_table.md` | Final results table (also in the main README) |
| `ROUND1_SUMMARY.md` | Round 1 summary |

## Round 1 (top level and `eda/`)
| File | What it is |
|---|---|
| `eda/inventory.csv` | Per-trip data-quality checks |
| `eda/label_alignment.csv`, `eda/label_threshold.json` | Round 1 label alignment (148 m p95 rule) |
| `eda/candidates.json` | Candidate miss rates, row counts |
| `eda/feature_missing.csv`, `eda/feature_importance.csv` | Missing values and importance, Round 1 features |
| `model_comparison.csv`, `baseline_nearest_arc.csv`, `selection.json` | Round 1 six-model comparison |
| `experiments.csv`, `train_models.log` | Experiment log and the training run log |
| `optuna_best.json`, `optuna_trials.csv` | Optuna XGBoost tuning on Round 1 features |

## Round 2 (`r2/`)
| Topic | Files |
|---|---|
| Labels (50 m rule, low-quality trips) | `label_threshold.json`, `label_changes.csv`, `label_quality_trips.csv` |
| Error analysis | `error_analysis.csv`, `top1_by_scope_r1model.csv`, `per_trip_top1_r1model.csv`, `cv_folds_r1model.csv` |
| Training size | `train_size_benchmark.csv`, `train_size_decision.json` |
| Features | `ablation.csv`, `ablation_rule.json`, `feature_set_v2.json`, `feature_importance_v2.csv` |
| Model comparison | `model_comparison_v2.csv` (deliverables 3.1 format), `model_comparison_v2_full.csv`, `cv_folds_v2.csv`, `calibration_v2.csv`, `selection_rule_v2.json`, `selection_v2.json` |
| HPO | `hpo_trials.csv`, `hpo_best.json`, `hpo_tuned_vs_untuned.csv`, `optuna.db` |
| HMM | `hmm_comparison.csv`, `hmm_per_trip.csv`, `hmm_params.json`, `hmm_trials.csv`, `hmm_selection.json` |
| Inference and maps | `inference_check.csv`, `maps_index.csv` |
| Run logs | `logs/` (ablation, model comparison, HPO, HMM, live API test) |
