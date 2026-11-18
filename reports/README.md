# reports/

## Main report
**[PathSnap_Report.pdf](PathSnap_Report.pdf)**: the final technical report.

## Round 1: [`round1/`](round1/)
| File | What it is |
|---|---|
| [ROUND1_SUMMARY.md](round1/ROUND1_SUMMARY.md) | Round 1 summary: preprocessing, labels, candidates, features, 6-model comparison |

## Round 2: [`round2/`](round2/)
| File | What it is |
|---|---|
| [ROUND2_SUMMARY.md](round2/ROUND2_SUMMARY.md) | Round 2 summary: final pipeline (classifier + HMM), results |
| [FINDINGS.md](round2/FINDINGS.md) | Facts and numbers per report section, each with its source file |
| [PROGRESS.md](round2/PROGRESS.md) | Step-by-step decision log for Round 2 |
| [screenshots/](round2/screenshots/) | UI screenshots (`ui_trip_<id>.jpeg`), taken on the evaluator data |

## Figures
| Folder | Contents |
|---|---|
| [`figures/`](figures/) | Round 1: model comparison (`cv_macro_f1`, `student_test_top1`, `confusion_matrix_XGBoost`, `mlp_loss_curve`) and EDA (`eda_*`: gaps, road network, trip map in metres, label alignment, missing values, feature distributions, feature importance) |
| [`figures/r2/`](figures/r2/) | Round 2: label threshold, error taxonomy, per-trip Top-1, ablation, feature importance, model comparison (`*_v2`), calibration, HPO history and parameter importance, HMM comparison |

Interactive Folium maps: [`../maps/`](../maps/) (Round 1) and [`../maps/r2/`](../maps/r2/) (Round 2: best, median and worst student_test trip).

Note: the figure folders stay where the scripts write them. The summary generators still write to `results/`
(`scripts/write_summary.py` -> `results/ROUND1_SUMMARY.md`; `scripts/r2_write_summary.py` -> `results/r2/`).
The committed copies live here; copy the files over if you regenerate them.
