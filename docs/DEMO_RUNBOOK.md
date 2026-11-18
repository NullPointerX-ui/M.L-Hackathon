
# PathSnap Demo Runbook (Windows)

This document explains how to run the PathSnap map-matching demo using two Windows laptops connected to the same Wi-Fi or mobile hotspot.

## Laptop 1 - API Server

Laptop 1 runs the FastAPI backend and provides prediction results to Laptop 2.

### 1. Open the project folder

Open Command Prompt and navigate to the cloned project folder:

```cmd
cd /d C:\path\to\M.L-Hackathon
```

Use the actual project folder path on Laptop 1 if it is different.

### 2. Activate the virtual environment

```cmd
.venv\Scripts\activate
```

### 3. Start the API server

Run the API using the evaluator's dataset folder:

```cmd
python api\main.py --eval-dir "C:\Users\Sarah\Downloads\ML\evaluator_test" --port 8000
```

Keep this Command Prompt window open while the demo is running.

### 4. Allow TCP port 8000 through Windows Firewall

Open Command Prompt as Administrator and run:

```cmd
netsh advfirewall firewall add rule name="PathSnap API Port 8000" dir=in action=allow protocol=TCP localport=8000
```

This allows incoming TCP connections on port 8000.

### 5. Find Laptop 1's IPv4 address

On Laptop 1, open another Command Prompt and run:

```cmd
ipconfig
```

Find the active Wi-Fi or hotspot network adapter and note its IPv4 Address.

Use the address belonging to the network shared with Laptop 2.

For example, if the IPv4 address is `192.168.1.10`, Laptop 2 will use:

```text
http://192.168.1.10:8000
```

## Laptop 2 - Streamlit UI

Laptop 2 runs the Streamlit interface and connects to the API on Laptop 1.

### 1. Clone the GitHub repository

Open Command Prompt and navigate to the folder where you want the project:

```cmd
cd /d C:\Users\%USERNAME%\Downloads
```

Clone the repository:

```cmd
git clone https://github.com/NullPointerX-ui/M.L-Hackathon.git
```

Enter the project folder:

```cmd
cd M.L-Hackathon
```

### 2. Create a Python 3.12 virtual environment

```cmd
py -3.12 -m venv .venv
```

### 3. Activate the virtual environment

```cmd
.venv\Scripts\activate
```

### 4. Install UI dependencies

```cmd
python -m pip install -r requirements-ui.txt
```

### 5. Start the Streamlit UI

```cmd
streamlit run ui\app.py
```

The Streamlit application will open in the browser.

### 6. Connect the UI to Laptop 1

In the Streamlit sidebar, find the **API base URL** field.

Enter:

```text
http://<Laptop 1 IP>:8000
```

Replace `<Laptop 1 IP>` with the IPv4 address found using `ipconfig` on Laptop 1.

For example:

```text
http://192.168.1.10:8000
```

Click **Check API** to verify the connection.

Select a trip and click **Run prediction** to run map matching.

## Troubleshooting

### 1. Firewall blocks the connection

If Laptop 2 cannot reach the API, check that the API is running and that TCP port 8000 is allowed through Windows Firewall.

Run the firewall command from an Administrator Command Prompt on Laptop 1:

```cmd
netsh advfirewall firewall add rule name="PathSnap API Port 8000" dir=in action=allow protocol=TCP localport=8000
```

Also verify that the API is listening on `0.0.0.0:8000`, not only `127.0.0.1:8000`.

### 2. Hotspot client isolation

If both laptops are connected to the same mobile hotspot but cannot communicate, the hotspot may have client isolation enabled.

Check the phone's hotspot settings and disable client isolation or AP isolation if that option is available.

If it cannot be disabled, connect both laptops through another network that permits communication between devices.

### 3. Port 8000 is already in use

If the API reports that port 8000 is already in use, another process may be using it.

Check the process:

```cmd
netstat -ano | findstr :8000
```

Note the PID shown in the final column.

If the process is an old API instance that you own and no longer need, stop it:

```cmd
taskkill /PID <PID> /F
```

Replace `<PID>` with the actual process ID. Then start the API again.

### 4. Wrong trip list is displayed

If the UI displays an unexpected trip list or no trips, the API may have been started with the wrong evaluation folder.

Stop the API using `Ctrl + C` and restart it with the correct folder:

```cmd
python api\main.py --eval-dir "C:\Users\Sarah\Downloads\ML\evaluator_test" --port 8000
```

On Laptop 2, click **Reload trips** in the Streamlit sidebar after the API has restarted.

## Demo Checklist

- Laptop 1 API server is running.
- Laptop 1 and Laptop 2 are connected to the same network.
- TCP port 8000 is allowed through Windows Firewall.
- Laptop 1 IPv4 address is known.
- Laptop 2 UI dependencies are installed.
- Streamlit UI is running.
- API base URL on Laptop 2 points to Laptop 1.
- **Check API** succeeds.
- A trip can be selected and a prediction can be run.
