"""Point-level metrics over candidate tables (one row per (trip_id, point_idx, arc_id))."""
from __future__ import annotations

import numpy as np
import pandas as pd


def point_key(df: pd.DataFrame) -> np.ndarray:
    return df.trip_id.astype(np.int64).to_numpy() * 1_000_000 + df.point_idx.to_numpy()


def argmax_per_point(df: pd.DataFrame, score: np.ndarray) -> pd.DataFrame:
    """One row per point: the candidate with the highest score. Columns: trip_id, point_idx,
    pred_arc, pred_score, correct (pred_arc == label_arc_id; False when the label arc was missed)."""
    k = point_key(df)
    o = np.lexsort((-score, k))
    first = np.r_[True, k[o][1:] != k[o][:-1]]
    sel = o[first]
    r = df.iloc[sel][["trip_id", "point_idx", "arc_id", "label_arc_id", "label"]].reset_index(drop=True)
    r = r.rename(columns={"arc_id": "pred_arc"})
    r["pred_score"] = score[sel]
    r["correct"] = r.label.astype(bool)
    return r.drop(columns="label")


def top1(df: pd.DataFrame, score: np.ndarray) -> float:
    return float(argmax_per_point(df, score).correct.mean()) if len(df) else float("nan")
