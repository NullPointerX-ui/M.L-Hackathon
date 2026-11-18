#!/usr/bin/env python3
"""Generate Round 2 Markdown reports from committed results. Run at repo root."""
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results" / "r2"

def csvr(name):
    with (R/name).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def js(name):
    return json.loads((R/name).read_text(encoding="utf-8"))

def num(x, d=4):
    return "N/A" if x in ("", None) else f"{float(x):.{d}f}"

def pct(x, d=2):
    return "N/A" if x in ("", None) else f"{100*float(x):.{d}f}%"

def src(x):
    return f"`results/r2/{x}`"

def mdtable(headers, rows):
    return "\n".join([
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"]*len(headers)) + " |",
        *("| " + " | ".join(str(v).replace("|", r"\|") for v in row) + " |" for row in rows)
    ])

models = csvr("model_comparison_v2_full.csv")
hpo_rows = csvr("hpo_tuned_vs_untuned.csv")
hmm_rows = csvr("hmm_comparison.csv")
ablation = csvr("ablation.csv")
scope = csvr("top1_by_scope_r1model.csv")
errors = csvr("error_analysis.csv")
inference = csvr("inference_check.csv")
maps = csvr("maps_index.csv")
labels = csvr("label_changes.csv")
quality = csvr("label_quality_trips.csv")
calibration = csvr("calibration_v2.csv")
importance = csvr("feature_importance_v2.csv")
features = js("feature_set_v2.json")
threshold = js("label_threshold.json")
hpo = js("hpo_best.json")
hmm = js("hmm_params.json")
hsel = js("hmm_selection.json")
sel = js("selection_v2.json")
train_size = js("train_size_decision.json")

def pick(rows, **conds):
    return next(x for x in rows if all(x[k] == v for k,v in conds.items()))

rt = pick(scope, partition="train", scope="reliable_ok_trips")
at = pick(scope, partition="train", scope="all_points")
rs = pick(scope, partition="student_test", scope="reliable_ok_trips")
ass = pick(scope, partition="student_test", scope="all_points")
hu = next(x for x in hpo_rows if "untuned" in x["model"].lower())
ht = next(x for x in hpo_rows if "tuned" in x["model"].lower())
hxtr = pick(hmm_rows, model="XGBoost", evaluated_on="train (OOF emissions; decoder tuned here)")
hxt = pick(hmm_rows, model="XGBoost", evaluated_on="student_test")
hltr = pick(hmm_rows, model="LightGBM", evaluated_on="train (OOF emissions; decoder tuned here)")
hlt = pick(hmm_rows, model="LightGBM", evaluated_on="student_test")
orig = pick(ablation, config="original_13")
final = pick(ablation, config="final_kept")
largest = max(inference, key=lambda x: float(x["points"]))
stslow = max((x for x in inference if x["partition"] == "student_test"), key=lambda x: float(x["total_s"]))
worst = next(x for x in maps if x["tag"] == "worst")

model_table = [[x["Model"], x["family"], x["config"], pct(x["cv_macro_f1"]), pct(x["cv_top1"]),
                pct(x["cv_top1_all"]), pct(x["st_top1"]), pct(x["st_top1_all"]),
                pct(x["st_macro_f1"]), num(x["st_log_loss"]), num(x["inference_ms_per_1k_points"],2)]
               for x in models]

summary = f"""# PathSnap Round 2 Summary

Generated from committed Round 2 result files. Reliable-point Top-1 means eligible points in trips labelled `ok`; all-point Top-1 is shown separately. Student-test was not used for selection.

## Pipeline

{mdtable(["Stage","Method / output","Evidence"],[
["Data quality","TRAIN-only label threshold",src("label_threshold.json")],
["Feature engineering","Ablation and 31-feature set",src("ablation.csv")],
["Model comparison","Five classifiers; GroupKFold by trip",src("model_comparison_v2_full.csv")],
["Bayesian HPO","Optuna TPE on LightGBM",src("hpo_best.json")],
["Route decoding","HMM + Viterbi",src("hmm_comparison.csv")],
["Inference","Per-trip timing",src("inference_check.csv")],
["Maps","Best, median, worst examples",src("maps_index.csv")],
])}

## 2. Dataset understanding, EDA and preprocessing

The point reliability threshold was selected using TRAIN only: alignment distance > {num(threshold['rules']['point_threshold_m'],1)} m marks a point unreliable. A trip is low quality when median alignment distance > {num(threshold['rules']['trip_median_max_m'],1)} m or its unreliable-point fraction > {pct(threshold['rules']['trip_unreliable_max'])}. The Round 1 threshold was {num(threshold['round1_threshold_m'],2)} m. Sources: {src("label_threshold.json")}, {src("label_changes.csv")}, {src("label_quality_trips.csv")}.

TRAIN points over the threshold: {pct(threshold['train_point_pct_over_threshold'])}; accepted TRAIN-trip points over threshold: {pct(threshold['train_ok_trips_point_pct_over_threshold'])}. Source: {src("label_threshold.json")}.

Round 1 XGBoost baseline:
{mdtable(["Partition / scope","Points","Top-1","Candidate miss"],[
["TRAIN CV reliable accepted trips",rt["points"],pct(rt["xgb_r1config_top1"]),pct(rt["candidate_miss_rate"])],
["TRAIN CV all points",at["points"],pct(at["xgb_r1config_top1"]),pct(at["candidate_miss_rate"])],
["Student-test reliable accepted trips",rs["points"],pct(rs["xgb_r1config_top1"]),pct(rs["candidate_miss_rate"])],
["Student-test all points",ass["points"],pct(ass["xgb_r1config_top1"]),pct(ass["candidate_miss_rate"])],
])}

The final feature set has {features['n_features']} features. Kept groups: {", ".join(features['kept_groups'])}; dropped groups: {", ".join(features['dropped_groups'])}. Original 13-feature CV eligible Top-1: {pct(orig['cv_top1'])}; final set: {pct(final['cv_top1'])}. Sources: {src("feature_set_v2.json")}, {src("ablation.csv")}, {src("feature_importance_v2.csv")}.

## 3. Model experimentation and comparison

{mdtable(["Model","Algorithm family","Key configuration","CV Macro F1","CV Top-1 reliable","CV Top-1 all","ST Top-1 reliable","ST Top-1 all","ST Macro F1","ST log loss","Inference ms/1k"],model_table)}

The train-minus-CV gaps are recorded in {src("model_comparison_v2_full.csv")}; none exceeded 5 percentage points. Selection was pre-registered and student-test was not used. Initial contenders: {", ".join(sel['contenders'])}; provisional HPO model: {sel['provisional_for_hpo']}. The v2 comparison ran five models: LogisticRegression, RandomForest, LightGBM, XGBoost and MLP. KNN, ExtraTrees and XGBRanker were not run. Isotonic calibration was not adopted; see {src("calibration_v2.csv")}.

## 4. Bayesian hyperparameter optimisation

Model: {hpo['model']}; sampler: {hpo['sampler']}; pruner: {hpo['pruner']}. Trials requested/completed/pruned: {hpo['n_trials_requested']}/{hpo['trials_complete']}/{hpo['trials_pruned']}. CV: {hpo['cv']}. Objective: {hpo['objective']}. Best parameters: `{json.dumps(hpo['best_params'],sort_keys=True)}`. Sources: {src("hpo_best.json")}, {src("hpo_trials.csv")}.

{mdtable(["Metric","Untuned","Tuned"],[
["CV eligible Top-1",pct(hu["cv_top1"]),pct(ht["cv_top1"])],
["CV Macro F1",pct(hu["cv_macro_f1"]),pct(ht["cv_macro_f1"])],
["Student-test eligible Top-1",pct(hu["st_top1"]),pct(ht["st_top1"])],
["Student-test all-point Top-1",pct(hu["st_top1_all"]),pct(ht["st_top1_all"])],
["Student-test Macro F1",pct(hu["st_macro_f1"]),pct(ht["st_macro_f1"])],
["Student-test log loss",num(hu["st_log_loss"]),num(ht["st_log_loss"])],
["Inference ms / 1k",num(hu["inference_ms_per_1k_points"],2),num(ht["inference_ms_per_1k_points"],2)],
])}

Tuned CV Top-1 gain: {num(float(ht['cv_top1'])-float(hu['cv_top1']),6)}. Tuned student-test eligible Top-1 was lower; tuned inference was {num(float(ht['inference_ms_per_1k_points'])/float(hu['inference_ms_per_1k_points']),1)}x slower. The pre-registered CV rule selected tuned LightGBM for HMM; student-test was not used.

## 5. HMM and Viterbi route reconstruction

Candidate road arcs are hidden states. Classifier probabilities provide emissions; transitions use a bounded road-network shortest-path lattice. Viterbi decoding runs in log space with break/restart handling. Parameters tuned on TRAIN LightGBM OOF: tau={num(hmm['tau'],3)}, beta={num(hmm['beta'],3)}, v_max={num(hmm['v_max'],3)} m/s, gap threshold={num(hmm['gap_threshold_s'],1)} s, subgraph={num(hmm['subgraph_m'],1)} m, cutoff={num(hmm['cutoff_m'],1)} m, back epsilon={num(hmm['back_eps_m'],1)} m. Source: {src("hmm_params.json")}.

{mdtable(["Model / partition","Reliable Top-1 classifier","Reliable Top-1 HMM","All Top-1 classifier","All Top-1 HMM","Route F1 classifier","Route F1 HMM","Continuity classifier","Continuity HMM","Breaks"],[
["LightGBM TRAIN OOF",pct(hltr["clf_top1_eligible"]),pct(hltr["hmm_top1_eligible"]),pct(hltr["clf_top1_all"]),pct(hltr["hmm_top1_all"]),num(hltr["clf_route_f1_mean"]),num(hltr["hmm_route_f1_mean"]),pct(hltr["clf_continuity"]),pct(hltr["hmm_continuity"]),hltr["breaks"]],
["LightGBM student-test",pct(hlt["clf_top1_eligible"]),pct(hlt["hmm_top1_eligible"]),pct(hlt["clf_top1_all"]),pct(hlt["hmm_top1_all"]),num(hlt["clf_route_f1_mean"]),num(hlt["hmm_route_f1_mean"]),pct(hlt["clf_continuity"]),pct(hlt["hmm_continuity"]),hlt["breaks"]],
["XGBoost TRAIN OOF",pct(hxtr["clf_top1_eligible"]),pct(hxtr["hmm_top1_eligible"]),pct(hxtr["clf_top1_all"]),pct(hxtr["hmm_top1_all"]),num(hxtr["clf_route_f1_mean"]),num(hxtr["hmm_route_f1_mean"]),pct(hxtr["clf_continuity"]),pct(hxtr["hmm_continuity"]),hxtr["breaks"]],
["XGBoost student-test",pct(hxt["clf_top1_eligible"]),pct(hxt["hmm_top1_eligible"]),pct(hxt["clf_top1_all"]),pct(hxt["hmm_top1_all"]),num(hxt["clf_route_f1_mean"]),num(hxt["hmm_route_f1_mean"]),pct(hxt["clf_continuity"]),pct(hxt["hmm_continuity"]),hxt["breaks"]],
])}

Final selection: {hsel['selected']} using TRAIN OOF HMM Top-1. RandomForest was not decoded due to time; decoder parameters were tuned on LightGBM OOF and reused for XGBoost. TRAIN HMM values are slightly optimistic because decoder tuning used TRAIN trips. Sources: {src("hmm_selection.json")}, {src("hmm_comparison.csv")}.

## 6. Geographical visualisation using Folium

{mdtable(["Trip","Example","Classifier reliable Top-1","HMM reliable Top-1","HMM route F1","HMM continuity","Interactive map"],[
[r["trip_id"],r["tag"],pct(r["classifier_only_top1_reliable"]),pct(r["hmm_top1_reliable"]),num(r["hmm_route_f1"]),pct(r["hmm_continuity"]),f"`{r['file']}`"] for r in maps
])}

Maps are committed HTML outputs with the route layers and controls described in the repository. Source: {src("maps_index.csv")}.

## 7. API, UI and deployment

Largest measured trip: {largest['points']} points in {num(largest['total_s'],2)} s. Slowest measured student-test trip: {stslow['points']} points in {num(stslow['total_s'],2)} s. Source: {src("inference_check.csv")}.

The repository progress log records FastAPI and Streamlit integration. Insert actual UI and receiving-laptop API screenshots into the final PDF; this script does not fabricate screenshots.

## Limitations and protocol notes

- Student-test was not used for model selection.
- Decoder parameters were tuned on TRAIN LightGBM OOF emissions and reused for XGBoost; TRAIN HMM results are slightly optimistic.
- RandomForest was not decoded due to time.
- KNN, ExtraTrees and XGBRanker were not run in the v2 comparison.
- HMM can hurt individual trips; see {src("hmm_per_trip.csv")}.
- Missing-value analysis and API/UI screenshots must be supplied separately if required; no values are invented here.
"""

findings = f"""# Round 2 Findings

## §2 Data/EDA and preprocessing
- Point reliability threshold: > {num(threshold['rules']['point_threshold_m'],1)} m. Source: {src("label_threshold.json")}.
- Low-quality trip rule: median > {num(threshold['rules']['trip_median_max_m'],1)} m OR unreliable fraction > {pct(threshold['rules']['trip_unreliable_max'])}. Source: {src("label_threshold.json")}.
- Threshold selected from TRAIN only. Source: {src("label_threshold.json")}.
- TRAIN points above threshold: {pct(threshold['train_point_pct_over_threshold'])}. Source: {src("label_threshold.json")}.
- Accepted TRAIN-trip points above threshold: {pct(threshold['train_ok_trips_point_pct_over_threshold'])}. Source: {src("label_threshold.json")}.
- Round 1 TRAIN CV baseline: reliable accepted-trip Top-1 {pct(rt['xgb_r1config_top1'])}; all-point Top-1 {pct(at['xgb_r1config_top1'])}. Source: {src("top1_by_scope_r1model.csv")}.
- Round 1 student-test baseline: reliable accepted-trip Top-1 {pct(rs['xgb_r1config_top1'])}; all-point Top-1 {pct(ass['xgb_r1config_top1'])}. Source: {src("top1_by_scope_r1model.csv")}.
- Final feature count: {features['n_features']}; retained groups: {", ".join(features['kept_groups'])}; dropped groups: {", ".join(features['dropped_groups'])}. Source: {src("feature_set_v2.json")}.
- Ablation CV eligible Top-1: original {pct(orig['cv_top1'])}; final {pct(final['cv_top1'])}. Source: {src("ablation.csv")}.
- Missing-value statistics are not contained in the inspected result files. Source checked: {src("label_quality_trips.csv")}.

## §3 Model comparison
""" + "\n".join(
f"- {x['Model']}: CV reliable Top-1 {pct(x['cv_top1'])}; CV all-point Top-1 {pct(x['cv_top1_all'])}; student-test reliable Top-1 {pct(x['st_top1'])}; student-test all-point Top-1 {pct(x['st_top1_all'])}; student-test Macro F1 {pct(x['st_macro_f1'])}; log loss {num(x['st_log_loss'])}; train-CV gap {num(x['train_minus_cv_pts'],2)} points. Source: {src('model_comparison_v2_full.csv')}."
for x in models) + f"""

## §4 Bayesian HPO
- Model/sampler/pruner: {hpo['model']} / {hpo['sampler']} / {hpo['pruner']}. Source: {src("hpo_best.json")}.
- Trials requested/completed/pruned: {hpo['n_trials_requested']}/{hpo['trials_complete']}/{hpo['trials_pruned']}. Source: {src("hpo_best.json")}.
- Objective: {hpo['objective']}. Source: {src("hpo_best.json")}.
- Best parameters: `{json.dumps(hpo['best_params'],sort_keys=True)}`. Source: {src("hpo_best.json")}.
- CV reliable Top-1 tuned/untuned: {pct(ht['cv_top1'])}/{pct(hu['cv_top1'])}. Source: {src("hpo_tuned_vs_untuned.csv")}.
- Student-test reliable Top-1 tuned/untuned: {pct(ht['st_top1'])}/{pct(hu['st_top1'])}. Source: {src("hpo_tuned_vs_untuned.csv")}.
- Inference ms/1k tuned/untuned: {num(ht['inference_ms_per_1k_points'],2)}/{num(hu['inference_ms_per_1k_points'],2)}. Source: {src("hpo_tuned_vs_untuned.csv")}.

## §5 HMM/Viterbi
- Parameters: tau {num(hmm['tau'],3)}, beta {num(hmm['beta'],3)}, v_max {num(hmm['v_max'],3)} m/s, gap threshold {num(hmm['gap_threshold_s'],1)} s. Source: {src("hmm_params.json")}.
- Tuning source: {hmm['tuned_on']}. Source: {src("hmm_params.json")}.
- XGBoost student-test reliable Top-1 classifier/HMM: {pct(hxt['clf_top1_eligible'])}/{pct(hxt['hmm_top1_eligible'])}. Source: {src("hmm_comparison.csv")}.
- XGBoost student-test all-point Top-1 classifier/HMM: {pct(hxt['clf_top1_all'])}/{pct(hxt['hmm_top1_all'])}. Source: {src("hmm_comparison.csv")}.
- XGBoost student-test route F1 classifier/HMM: {num(hxt['clf_route_f1_mean'])}/{num(hxt['hmm_route_f1_mean'])}. Source: {src("hmm_comparison.csv")}.
- XGBoost student-test continuity classifier/HMM: {pct(hxt['clf_continuity'])}/{pct(hxt['hmm_continuity'])}. Source: {src("hmm_comparison.csv")}.
- Breaks TRAIN/student-test: {hxtr['breaks']}/{hxt['breaks']}. Source: {src("hmm_comparison.csv")}.
- Selected model: {hsel['selected']}. Source: {src("hmm_selection.json")}.

## §6 Folium maps
""" + "\n".join(
f"- Trip {x['trip_id']} ({x['tag']}): classifier reliable Top-1 {pct(x['classifier_only_top1_reliable'])}; HMM reliable Top-1 {pct(x['hmm_top1_reliable'])}; map `{x['file']}`. Source: {src('maps_index.csv')}."
for x in maps) + f"""

## §7 API/UI/deployment
- Largest trip: {largest['points']} points, {num(largest['total_s'],2)} s. Source: {src("inference_check.csv")}.
- Slowest student-test trip: {stslow['points']} points, {num(stslow['total_s'],2)} s. Source: {src("inference_check.csv")}.
- Screenshots must come from the actual running API/UI. Source: `docs/deliverables.md`.

## Known issues / limitations
- Student-test was not used for model selection. Source: {src("selection_v2.json")}.
- Decoder tuned on TRAIN LightGBM OOF and shared with XGBoost. Source: {src("hmm_params.json")} and {src("hmm_selection.json")}.
- RandomForest not HMM-decoded due to time. Source: {src("hmm_selection.json")}.
- Worst indexed trip {worst['trip_id']}: reliable Top-1 {pct(worst['classifier_only_top1_reliable'])} to {pct(worst['hmm_top1_reliable'])} after HMM. Source: {src("maps_index.csv")}.
- Only five models run; KNN, ExtraTrees and XGBRanker not run. Source: `PROGRESS.md`.
- Isotonic calibration not adopted. Source: {src("calibration_v2.csv")}.
- Missing-value analysis and screenshots require separate evidence. Source: `docs/deliverables.md`.
"""

(R/"ROUND2_SUMMARY.md").write_text(summary.strip()+"\n",encoding="utf-8")
(R/"FINDINGS.md").write_text(findings.strip()+"\n",encoding="utf-8")
print("Wrote results/r2/ROUND2_SUMMARY.md")
print("Wrote results/r2/FINDINGS.md")
