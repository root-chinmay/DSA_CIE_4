# Two-Laptop Offline Router Setup & Testing Guide

This guide details how to demonstrate the project with **two laptops connected to the same router with Internet completely disabled**.

---

## 1. Network Preparation (Internet = OFF)

1. Connect both laptops to the same Wi-Fi router or plug them into Ethernet ports on the same router.
2. **Unplug the WAN / DSL cable from the router** (or disable mobile data hotspots). Verify that neither laptop can open external websites like `google.com`.
3. Check that the router has assigned local IP addresses (e.g. `192.168.1.10` and `192.168.1.11`).

---

## 2. Laptop A (Host Mode)

### Step 1: Start Backend Server
Open terminal in the project directory:
```powershell
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### Step 2: Observe Terminal Banner
The startup banner will print:
```text
========================================================================
  DSA-BASED OFFLINE LAN FILE SHARING & SYNCHRONIZATION SYSTEM
========================================================================
  Status:        ONLINE (OFFLINE-FIRST LAN READY)
  Local LAN IP:  192.168.1.10
  Server Port:   8000
  Dashboard:     http://192.168.1.10:8000/
  Device ID:     dev_a1b2c3d4
  Device Name:   Laptop-A
  Pairing Code:  583921
========================================================================
```

### Step 3: Open Dashboard on Laptop A
In browser on Laptop A, open:
```text
http://127.0.0.1:8000/
```
Or use the detected LAN IP:
```text
http://192.168.1.10:8000/
```

Note the **6-Digit Pairing Code** (e.g. `583921`) displayed in the top bar.

---

## 3. Laptop B (Client Mode)

Laptop B does **not need Python or Node.js installed** to browse and download files!

### Option A: Web Browser Client
1. On Laptop B, open Chrome, Edge, or Firefox.
2. In the address bar, type the LAN IP of Laptop A:
   ```text
   http://192.168.1.10:8000/
   ```
3. The dashboard loads directly from Laptop A over the offline LAN.
4. Click **"Pair Device"** or enter the 6-digit code `583921` to authorize connection.
5. Browse the FileTree, download files with streaming SHA-256 verification, and drag-and-drop new files to upload.

### Option B: Running Full Peer Instance
If you want Laptop B to also act as a full Host/Peer:
1. Copy the project folder to Laptop B.
2. Run `python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000`.
3. Both laptops will automatically discover each other via UDP broadcast on port `42424`!

---

## 4. Single-Laptop Demo Mode (For College Evaluation)

If only one laptop is available during presentation:
1. Open the dashboard at `http://127.0.0.1:8000/`.
2. Click the **"🧪 Demo Mode"** button in the topbar.
3. The system instantly generates virtual nodes (`Laptop-B`, `Laptop-C`), seeds sample files in the FileTree, populates the Priority Heap and FIFO Queue, creates a mock sync conflict, and renders the multi-node network graph!
4. Evaluator can test all features (BFS, Dijkstra, Priority Queue elevation, Conflict resolution) right on the spot!
