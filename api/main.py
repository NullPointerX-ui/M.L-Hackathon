"""
Map-matching demo API (two-laptop setup).

Runs on the SERVER laptop. The Streamlit UI runs on the other laptop and talks
to this process over the hotspot.

Run:
    python api/main.py --eval-dir ../student_test --port 8000

Endpoints:
    GET  /health            -> status + which eval-dir and layout was detected
    GET  /trips             -> JSON array of trip ids
    POST /predict           -> {"trip_id": "..."} -> GeoJSON + metrics + timings

IMPORTANT (project rule): the ground-truth route must never reach the UI.
This file contains NO code that opens a .route file. Keep it that way.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------------------------------------------------------------- logging ----
# Evaluators read these logs on this laptop, so everything goes to stdout in a
# fixed, greppable shape:  2026-11-18T10:30:01 INFO predict trip_id=... latency_ms=...
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger("api")


# ------------------------------------------------------------ trip lookup ----
class TripIndex:
    """Finds trips under eval_dir.

    Two layouts are supported, because we have not unzipped the real data yet:
      folder-per-trip : <eval_dir>/<trip_id>/<something>.track   (expected)
      flat-files      : <eval_dir>/<trip_id>.track
    """

    def __init__(self, eval_dir: Path) -> None:
        self.eval_dir = eval_dir
        self.layout = "empty"
        self.tracks: dict[str, Path] = {}  # trip_id -> .track file
        self.dirs: dict[str, Path] = {}    # trip_id -> folder passed to predict_trip()
        self.refresh()

    def refresh(self) -> None:
        tracks: dict[str, Path] = {}
        dirs: dict[str, Path] = {}

        if not self.eval_dir.is_dir():
            self.layout = "missing-eval-dir"
            self.tracks, self.dirs = {}, {}
            return

        for child in sorted(self.eval_dir.iterdir()):
            if child.is_dir():
                found = sorted(child.glob("*.track"))
                if found:
                    tracks[child.name] = found[0]
                    dirs[child.name] = child

        if tracks:
            self.layout = "folder-per-trip"
        else:
            for track in sorted(self.eval_dir.glob("*.track")):
                tracks[track.stem] = track
                dirs[track.stem] = self.eval_dir
            self.layout = "flat-files" if tracks else "no-tracks-found"

        self.tracks, self.dirs = tracks, dirs

    def ids(self) -> list[str]:
        return list(self.tracks.keys())


# ------------------------------------------------------------ .track file ----
def read_track(path: Path) -> tuple[list[list[float]], list[float | None], int]:
    """Parse a whitespace-separated .track file: lon lat t, no header.

    Returns ([[lon, lat], ...], [t, ...], n_skipped_lines).
    Tolerant on purpose: blank lines, extra columns and a stray header are
    skipped rather than crashing the demo.
    """
    coords: list[list[float]] = []
    times: list[float | None] = []
    skipped = 0

    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            parts = line.split()
            if len(parts) < 2:
                if line.strip():
                    skipped += 1
                continue
            try:
                lon = float(parts[0])
                lat = float(parts[1])
            except ValueError:
                skipped += 1  # header row or junk
                continue

            t: float | None = None
            if len(parts) >= 3:
                try:
                    t = float(parts[2])
                except ValueError:
                    t = None

            coords.append([lon, lat])
            times.append(t)

    return coords, times, skipped


# --------------------------------------------------------------- app ---------
app = FastAPI(title="Map-matching demo API", version="0.1.0-skeleton")

# Cheap insurance. Note: Streamlit calls this API from its own Python process,
# not from the browser, so CORS is usually NOT what breaks the two-laptop test.
# The firewall rule and hotspot client isolation are.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATE: dict[str, Any] = {"index": None}


def index() -> TripIndex:
    idx = STATE.get("index")
    if idx is None:
        eval_dir = Path(os.environ.get("EVAL_DIR", "student_test")).expanduser().resolve()
        idx = TripIndex(eval_dir)
        STATE["index"] = idx
        log.info(
            "trip index ready eval_dir=%s layout=%s trips=%d",
            idx.eval_dir, idx.layout, len(idx.tracks),
        )
        if not idx.tracks:
            log.warning("no trips found under %s - check --eval-dir", idx.eval_dir)
    return idx


@app.middleware("http")
async def log_requests(request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    client = request.client.host if request.client else "?"
    log.info(
        "%s %s -> %d %.1fms client=%s",
        request.method, request.url.path, response.status_code, elapsed_ms, client,
    )
    return response


class PredictRequest(BaseModel):
    trip_id: str


@app.get("/health")
def health() -> dict[str, Any]:
    idx = index()
    return {
        "status": "ok",
        "eval_dir": str(idx.eval_dir),
        "layout": idx.layout,
        "trips": len(idx.tracks),
        "dummy_predictions": True,
    }


@app.get("/trips")
def trips() -> list[str]:
    return index().ids()


@app.post("/trips/refresh")
def refresh_trips() -> dict[str, Any]:
    """Re-scan eval-dir without restarting (useful once the real zip lands)."""
    idx = index()
    idx.refresh()
    log.info("trip index refreshed layout=%s trips=%d", idx.layout, len(idx.tracks))
    return {"layout": idx.layout, "trips": len(idx.tracks)}


@app.post("/predict")
def predict(req: PredictRequest) -> dict[str, Any]:
    t_request = time.perf_counter()
    idx = index()

    # Also the path-traversal guard: only ids we discovered ourselves are valid,
    # so a trip_id like "../../secrets" can never reach the filesystem.
    track_path = idx.tracks.get(req.trip_id)
    if track_path is None:
        log.warning("predict rejected unknown trip_id=%r", req.trip_id)
        raise HTTPException(status_code=404, detail=f"unknown trip_id: {req.trip_id}")

    trip_dir = idx.dirs[req.trip_id]

    t_parse = time.perf_counter()
    coords, times, skipped = read_track(track_path)
    parse_ms = (time.perf_counter() - t_parse) * 1000.0

    if not coords:
        raise HTTPException(status_code=422, detail=f"no parsable GPS points in {track_path.name}")

    # ------------------------------------------------------------------
    # DUMMY PREDICTION - replace this block with the real model.
    #
    #     from predictor import predict_trip
    #     result = predict_trip(trip_dir)          # -> {"route_coords": [[lon, lat], ...],
    #                                              #     "metrics": {...}}
    #     route_coords = result["route_coords"]
    #
    # For now the "predicted route" is just the raw GPS line, so the wiring,
    # the map and the logs can all be tested before the model exists.
    # ------------------------------------------------------------------
    t_predict = time.perf_counter()
    route_coords = coords
    predict_ms = (time.perf_counter() - t_predict) * 1000.0

    gps_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "gps_line", "n_points": len(coords)},
                "geometry": {"type": "LineString", "coordinates": coords},
            },
            {
                "type": "Feature",
                "properties": {"name": "gps_points", "n_points": len(coords)},
                "geometry": {"type": "MultiPoint", "coordinates": coords},
            },
        ],
    }

    route_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "predicted_route", "dummy": True},
                "geometry": {"type": "LineString", "coordinates": route_coords},
            }
        ],
    }

    total_ms = (time.perf_counter() - t_request) * 1000.0

    payload: dict[str, Any] = {
        "trip_id": req.trip_id,
        "dummy": True,
        "n_points": len(coords),
        "skipped_lines": skipped,
        "t_first": times[0],
        "t_last": times[-1],
        "gps": gps_geojson,
        "predicted_route": route_geojson,
        # Deliberately null, not fake numbers: nothing from this skeleton should
        # ever be mistaken for a result and end up in the report.
        "metrics": {
            "top1_accuracy": None,
            "macro_f1": None,
            "route_precision": None,
            "route_recall": None,
            "note": "placeholder - real metrics come from predict_trip()",
        },
        "timings_ms": {
            "parse": round(parse_ms, 2),
            "predict": round(predict_ms, 2),
            "total": round(total_ms, 2),
        },
    }

    log.info(
        "predict trip_id=%s points=%d parse_ms=%.1f predict_ms=%.1f latency_ms=%.1f dir=%s",
        req.trip_id, len(coords), parse_ms, predict_ms, total_ms, trip_dir.name,
    )
    return payload


# -------------------------------------------------------------- entrypoint ---
def main() -> None:
    parser = argparse.ArgumentParser(description="Map-matching demo API")
    parser.add_argument("--eval-dir", default=os.environ.get("EVAL_DIR", "student_test"),
                        help="folder holding the trips (e.g. the student_test folder)")
    parser.add_argument("--host", default="0.0.0.0",
                        help="bind address; keep 0.0.0.0 so the other laptop can reach it")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    eval_dir = Path(args.eval_dir).expanduser().resolve()
    os.environ["EVAL_DIR"] = str(eval_dir)
    STATE["index"] = TripIndex(eval_dir)

    idx = STATE["index"]
    log.info("eval_dir=%s layout=%s trips=%d", idx.eval_dir, idx.layout, len(idx.tracks))
    if not idx.tracks:
        log.warning("no trips found - the UI dropdown will be empty")
    log.info("serving on http://%s:%d (other laptop uses this machine's LAN IP)", args.host, args.port)

    import uvicorn

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
