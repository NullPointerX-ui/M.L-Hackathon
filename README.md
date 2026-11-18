# Two-laptop demo skeleton

FastAPI server on one laptop, Streamlit UI on the other. Predictions are dummy
(the "predicted route" is just the raw GPS line) so the wiring, the map and the
logs can be tested today and the real model dropped in later.

```
api/main.py                 the server. GET /health, GET /trips, POST /predict
ui/app.py                   the Streamlit UI
tools/make_fake_trips.py    fake trips, so the network test needs no real data
tools/smoke_test.py         proves the API is reachable, before blaming Streamlit
requirements-api.txt        install on the API laptop
requirements-ui.txt         install on the UI laptop
```

Two project rules this code enforces:

- **The ground-truth route never reaches the UI.** `api/main.py` contains no code
  that opens a `.route` file at all. Keep it that way when the real model goes in.
- **The evaluators read the API logs on the laptop that receives the requests.**
  Every request prints one line to stdout with a timestamp, and `/predict` prints
  a second line with `trip_id` and latency.

---

## 1. Check you are on python.org Python

MSYS2/MinGW Python will not install these packages. On **both** laptops:

```powershell
python -c "import sys; print(sys.version); print(sys.executable)"
```

The path must look like `C:\Users\<you>\AppData\Local\Programs\Python\Python312\python.exe`
or `C:\Python312\python.exe`. If it contains `msys64`, `mingw` or `/usr/bin`, install
3.11 or 3.12 from python.org and use its full path below.

## 2. Install

API laptop:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-api.txt
```

UI laptop:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-ui.txt
```

## 3. Data

Real data, once `Student folder.zip` is unzipped:

```powershell
python api\main.py --eval-dir C:\path\to\student_test --port 8000
```

Fake data, to test the network now:

```powershell
python tools\make_fake_trips.py --out fake_test --trips 4
python api\main.py --eval-dir fake_test --port 8000
```

Both trip layouts work — one folder per trip containing a `.track`, or flat
`<trip_id>.track` files — because we have not seen the real folder yet.
`GET /health` reports which layout it detected and how many trips it found.

## 4. Run the API (API laptop)

```powershell
python api\main.py --eval-dir fake_test --host 0.0.0.0 --port 8000
```

Keep a copy of the log as well as showing it on screen, so the evaluators can
see it even after the terminal scrolls:

```powershell
mkdir logs
python api\main.py --eval-dir fake_test 2>&1 | Tee-Object -FilePath logs\api.log
```

Two things to confirm in the first lines of output:

- `trips=` is not 0
- it is serving on `0.0.0.0:8000`, **not** `127.0.0.1:8000` (127.0.0.1 is
  unreachable from the other laptop)

## 5. Find the API laptop's IP

```powershell
ipconfig
```

Use the **IPv4 Address** of the adapter connected to the demo-day hotspot —
usually "Wireless LAN adapter Wi-Fi". Ignore `169.254.x.x` (no DHCP) and any
VirtualBox/WSL/Hyper-V adapter. Phone hotspots typically hand out
`192.168.43.x`, `192.168.137.x` or `172.20.10.x`.

## 6. Open port 8000 in Windows Firewall (API laptop)

PowerShell **as Administrator**:

```powershell
netsh advfirewall firewall add rule name="MapMatch API 8000" dir=in action=allow protocol=TCP localport=8000 profile=any
```

`profile=any` matters: Windows usually classifies a phone hotspot as a Public
network, and a rule limited to Private will not apply.

To check or remove it later:

```powershell
netsh advfirewall firewall show rule name="MapMatch API 8000"
netsh advfirewall firewall delete rule name="MapMatch API 8000"
```

## 7. Prove reachability before starting the UI

On the **UI laptop**:

```powershell
ping 192.168.43.12
python tools\smoke_test.py http://192.168.43.12:8000
```

`smoke_test.py` hits all three endpoints and prints what it got. If it passes,
the network and server are fine and anything that still fails is in the UI.

## 8. Run the UI (UI laptop)

```powershell
streamlit run ui\app.py
```

Put `http://192.168.43.12:8000` in the sidebar, press **Check API**, pick a trip,
press **Run prediction**. The panel on the right shows server timings and the
round trip, so the gap between them is the network cost between the laptops.

---

## Troubleshooting

| What you see | Cause | Fix |
|---|---|---|
| `ping` fails both ways | Hotspot client isolation (AP isolation) | Turn it off in the phone's hotspot settings, or use another phone. **Check this today** — it is the one failure you cannot fix from the laptops. |
| `ping` works, API times out | Firewall | Run the `netsh` rule in step 6, with `profile=any` |
| `ConnectionRefused` | Server not running, or bound to 127.0.0.1 | Start it with `--host 0.0.0.0` |
| Reachable from the same laptop only | Bound to localhost | Same as above |
| `/trips` returns `[]` | Wrong `--eval-dir`, or no `.track` files under it | Check `GET /health`: it prints `eval_dir`, `layout`, `trips` |
| Map draws in the ocean near Africa | lon/lat swapped | Everything is swapped once in `latlon()` in `ui/app.py` |
| `pip install` fails compiling wheels | MSYS2/MinGW Python | Step 1 |
| UI works on the API laptop but not the other one | Network, not code | Step 7 |

### A note on CORS

CORS is enabled, which is cheap insurance, but it is probably **not** what will
break. Streamlit calls the API from its own Python process, not from the
browser, so there is no origin check and no preflight involved. The real
failures are the firewall rule, binding to `127.0.0.1`, and hotspot client
isolation.

---

## Plugging in the real model

In `api/main.py`, `/predict` has one block marked `DUMMY PREDICTION`. Replace it
with:

```python
from predictor import predict_trip
result = predict_trip(trip_dir)          # trip_dir is already resolved per trip
route_coords = result["route_coords"]    # [[lon, lat], ...]
```

and fill `payload["metrics"]` from `result["metrics"]`. The metrics are
deliberately `null` in this skeleton rather than plausible-looking numbers, so
nothing from the demo build can be mistaken for a result and end up in the
report. Nothing else in the file needs to change.
