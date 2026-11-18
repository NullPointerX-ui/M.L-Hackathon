# scripts/

Every script runs from the repo root (`python scripts\<name>.py` or `python -m scripts.<name>`) and writes its
outputs to `results/`, `reports/`, `maps/` or `artifacts/`.

## One-command runners
| Script | What it does |
|---|---|
| `run_all.py` | Round 1 pipeline (`--skip-train` = data steps only) |
| `run_all_r2.py` | Round 2 pipeline (`--quick` = labels, features, HMM, artifacts, maps) |
| `demo.py` | Prints the Round 1 numbers, opens the map and figures (`--no-open` = print only) |

## Round 1 (in order)
| Step | Script | Output |
|---|---|---|
| 1 | `preprocess.py` | per-trip projection, `results/eda/inventory.csv`, `maps/trip_00000001_raw.html` |
| 2 | `make_labels.py` | per-point labels (monotonic DP), `results/eda/label_*.csv` |
| 3 | `build_features.py` | candidates + 13 features |
| 3b | `eda_plots.py` | EDA and feature figures, `reports/figures/eda_*.png` |
| 4 | `train_models.py` | 6-model comparison, `results/model_comparison.csv` |
| 5 | `write_summary.py` | `results/ROUND1_SUMMARY.md` |
| - | `optuna_tuning.py` | Optuna XGBoost tuning on Round 1 features (`results/optuna_*.json/csv`) |

## Round 2 (in order)
| Step | Script | Output (all under `results/r2/` unless noted) |
|---|---|---|
| 1 | `r2_labels.py` | frozen 50 m rule + trip label_quality, `label_threshold.png` |
| 1 | `r2_size_benchmark.py` | shared training size (36,000 points) |
| 1 | `r2_error_analysis.py` | error taxonomy, per-trip Top-1 |
| 2 | `r2_build_features_v2.py` | 30 v2 features (data/processed/r2) |
| 2 | `r2_ablation.py` | feature-group ablation, kept set `feature_set_v2.json` |
| 3 | `r2_model_comparison.py` | 5-model comparison `model_comparison_v2.csv`, calibration |
| 4 | `r2_hpo.py` | Optuna TPE on LightGBM, tuned vs untuned |
| 5 | `r2_hmm.py` | HMM/Viterbi, classifier vs HMM `hmm_comparison.csv` |
| 6 | `r2_export_artifacts.py` | `artifacts/r2/*`, inference stress test |
| 7 | `r2_make_maps.py` | `maps/r2/*.html` |
| 8 | `r2_summary_table.py`, `r2_write_summary.py` | `summary_table.md`, `ROUND2_SUMMARY.md`, `FINDINGS.md` |

`r2_common.py` holds shared loaders; `__init__.py` puts `src/` on the import path.
