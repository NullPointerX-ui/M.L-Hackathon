"""
Map-matching demo UI (two-laptop setup).

Runs on the UI laptop. Point it at the API laptop's LAN IP in the sidebar.

Run:
    streamlit run ui/app.py

Note on coordinates: the .track files and the GeoJSON use [lon, lat].
folium wants [lat, lon]. Everything is swapped in one place (latlon()) -- if the
route shows up in the sea off West Africa, that swap is what went wrong.
"""

from __future__ import annotations

import time
from typing import Any

import folium
import requests
import streamlit as st
from streamlit_folium import st_folium

DEFAULT_API = "http://localhost:8000"
TIMEOUT = 30

st.set_page_config(page_title="Map matching demo", layout="wide")


# ----------------------------------------------------------------- helpers ---
def latlon(coords: list[list[float]]) -> list[list[float]]:
    """[[lon, lat], ...] -> [[lat, lon], ...] for folium."""
    return [[c[1], c[0]] for c in coords]


def geometry(fc: dict[str, Any] | None, geom_type: str) -> list[list[float]]:
    """Pull the first geometry of a given type out of a FeatureCollection."""
    if not fc:
        return []
    for feature in fc.get("features", []):
        geom = feature.get("geometry") or {}
        if geom.get("type") == geom_type:
            return geom.get("coordinates") or []
    return []


def connection_help(base: str, err: Exception) -> None:
    st.error(f"Could not reach the API at {base}")
    st.caption(f"{type(err).__name__}: {err}")
    st.markdown(
        "Work through these in order, on the **API laptop** unless stated:\n\n"
        "1. Is the server running, and does its log say `0.0.0.0:8000` (not `127.0.0.1`)?\n"
        "2. Is the URL above the API laptop's **hotspot** IPv4 from `ipconfig`, not its Wi-Fi/Ethernet one?\n"
        "3. Is inbound TCP 8000 allowed in Windows Firewall? (`profile=any` — the hotspot often "
        "counts as a Public network.)\n"
        "4. From **this** laptop: `ping <api-laptop-ip>`. If that fails, the hotspot has client "
        "isolation on — turn it off in the phone's hotspot settings, or use a different hotspot.\n"
        "5. Then: `python tools/smoke_test.py http://<api-laptop-ip>:8000`"
    )


# ----------------------------------------------------------------- sidebar ---
st.sidebar.header("Connection")
api_base = st.sidebar.text_input("API base URL", value=st.session_state.get("api_base", DEFAULT_API))
st.session_state["api_base"] = api_base.rstrip("/")
base = st.session_state["api_base"]

col_a, col_b = st.sidebar.columns(2)
check = col_a.button("Check API")
reload_trips = col_b.button("Reload trips")

if check:
    try:
        r = requests.get(f"{base}/health", timeout=5)
        r.raise_for_status()
        info = r.json()
        st.sidebar.success(f"OK - {info.get('trips', 0)} trips")
        st.sidebar.caption(f"eval_dir: {info.get('eval_dir')}")
        st.sidebar.caption(f"layout: {info.get('layout')}")
    except Exception as exc:  # noqa: BLE001 - demo UI, show anything that goes wrong
        st.sidebar.error(f"{type(exc).__name__}")
        st.sidebar.caption(str(exc)[:300])

if reload_trips:
    st.session_state.pop("trips", None)


# ------------------------------------------------------------------- trips ---
st.title("GPS map matching - demo")
st.caption("Skeleton build: the API returns a dummy prediction (the raw GPS line) and no metrics yet.")

if "trips" not in st.session_state:
    try:
        r = requests.get(f"{base}/trips", timeout=10)
        r.raise_for_status()
        payload = r.json()
        # Accept either a bare list or {"trips": [...]} so a later API change can't break the UI.
        st.session_state["trips"] = payload if isinstance(payload, list) else payload.get("trips", [])
    except Exception as exc:  # noqa: BLE001
        connection_help(base, exc)
        st.stop()

trip_ids: list[str] = st.session_state["trips"]
if not trip_ids:
    st.warning("The API is reachable but reports no trips. Check its --eval-dir, then press Reload trips.")
    st.stop()

left, right = st.columns([3, 1])

with left:
    trip_id = st.selectbox("Trip", trip_ids, index=0)
    run = st.button("Run prediction", type="primary")

if run:
    with st.spinner(f"Predicting {trip_id}..."):
        started = time.perf_counter()
        try:
            r = requests.post(f"{base}/predict", json={"trip_id": trip_id}, timeout=TIMEOUT)
            r.raise_for_status()
            st.session_state["result"] = r.json()
            st.session_state["round_trip_ms"] = (time.perf_counter() - started) * 1000.0
        except Exception as exc:  # noqa: BLE001
            connection_help(base, exc)
            st.stop()

result: dict[str, Any] | None = st.session_state.get("result")


# -------------------------------------------------------------------- view ---
if result is None:
    with left:
        st.info("Pick a trip and press **Run prediction**.")
else:
    gps_coords = geometry(result.get("gps"), "LineString")
    route_coords = geometry(result.get("predicted_route"), "LineString")

    with left:
        if gps_coords:
            gps_ll = latlon(gps_coords)
            mid = gps_ll[len(gps_ll) // 2]
            fmap = folium.Map(location=mid, zoom_start=14, tiles="OpenStreetMap")

            folium.PolyLine(gps_ll, color="#2563eb", weight=3, opacity=0.65, tooltip="GPS track").add_to(fmap)
            if route_coords:
                folium.PolyLine(
                    latlon(route_coords), color="#dc2626", weight=4, opacity=0.85,
                    dash_array="8,6", tooltip="Predicted route (dummy)",
                ).add_to(fmap)

            folium.CircleMarker(gps_ll[0], radius=6, color="#16a34a", fill=True, tooltip="start").add_to(fmap)
            folium.CircleMarker(gps_ll[-1], radius=6, color="#111827", fill=True, tooltip="end").add_to(fmap)

            lats = [p[0] for p in gps_ll]
            lons = [p[1] for p in gps_ll]
            fmap.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])

            st_folium(fmap, width=None, height=560, returned_objects=[])
        else:
            st.warning("The response contained no GPS LineString to draw.")

    with right:
        st.subheader("Metrics")
        metrics = result.get("metrics") or {}
        for key in ("top1_accuracy", "macro_f1", "route_precision", "route_recall"):
            value = metrics.get(key)
            st.metric(key.replace("_", " "), "-" if value is None else f"{value:.4f}")
        if result.get("dummy"):
            st.caption("Dummy response - metrics are intentionally empty until the real model is plugged in.")

        st.subheader("Timings")
        timings = result.get("timings_ms") or {}
        st.write(
            {
                "server parse ms": timings.get("parse"),
                "server predict ms": timings.get("predict"),
                "server total ms": timings.get("total"),
                "round trip ms": round(st.session_state.get("round_trip_ms", 0.0), 1),
            }
        )
        st.caption("Round trip minus server total is the network cost between the laptops.")

        st.subheader("Trip")
        st.write(
            {
                "trip_id": result.get("trip_id"),
                "gps points": result.get("n_points"),
                "skipped lines": result.get("skipped_lines"),
                "t first": result.get("t_first"),
                "t last": result.get("t_last"),
            }
        )

        with st.expander("Raw response"):
            trimmed = {k: v for k, v in result.items() if k not in ("gps", "predicted_route")}
            st.json(trimmed)
