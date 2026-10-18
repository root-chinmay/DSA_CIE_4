# DSA-Based Offline LAN File Sharing and Synchronization System

A production-grade, offline-first peer-to-peer file sharing and synchronization platform engineered specifically for local area networks (LAN / Wi-Fi / Ethernet routers) where **Internet access is completely unavailable**.

Data Structures and Algorithms (DSA) form the operational foundation of every networking, indexing, scheduling, and synchronization subsystem.

---

## 1. Problem Statement

Standard modern file-sharing and synchronization services (Google Drive, Dropbox, OneDrive, iCloud) strictly require high-speed Internet connectivity to function. In offline environments—such as college labs, emergency disaster response zones, remote research stations, internal corporate networks, or partitioned Wi-Fi routers—these cloud-dependent solutions are non-functional.

Traditional offline alternatives (USB thumb drives) lack real-time peer discovery, introduce malware vulnerabilities, cannot detect concurrent edits or synchronization conflicts, and provide no systematic transfer queueing or deduplication.

---

## 2. Objective

To design, engineer, and validate a robust **Offline LAN File Sharing & Synchronization System** that:
- Operates reliably on a local router with **Internet = OFF**.
- Seamlessly discovers devices via UDP broadcast with manual fallback.
- Guarantees data integrity using streaming SHA-256 cryptographic hashing without loading large files into memory.
- Actively demonstrates eight fundamental Data Structures and Algorithms solving real networking problems:
  - **Tree**: Hierarchical directory modeling & subtree size aggregation.
  - **Hash Table**: Separate chaining index for $O(1)$ file lookup and duplicate detection.
  - **Trie**: Character-level prefix tree for instantaneous filename search and autocomplete.
  - **FIFO Queue**: Sequential doubly-linked queue for standard file transfer scheduling.
  - **Priority Heap**: Binary min-heap for urgency-based transfer prioritization (Critical > High > Normal > Low).
  - **Graph**: Adjacency list LAN topology modeling with BFS, DFS, and Dijkstra shortest path routing.
  - **Sorting Algorithms**: Custom Merge Sort & Quick Sort implementations with benchmark metrics.
  - **Cryptographic Hasher**: Streaming 64KB block SHA-256 digest calculation.

---

## 3. Key Features

- **Zero-Internet Operation**: No cloud services, external CDN dependencies, or external APIs.
- **Offline Direct IP File Transfer**: Peer-to-peer file transfer directly using device IP addresses across Wi-Fi or Mobile Hotspot with zero internet.
- **Mobile Touch-Portal & Offline QR Code**: Instant pure client-side QR code generator lets mobile phones connect and transfer files with camera scan.
- **Offline Subnet IP Scanner**: Concurrently probes active LAN IPs and inspects OS ARP cache to discover connected phones, laptops, and tablets.
- **100% Responsive Mobile Interface**: Touch-first responsive slide-out drawer, mobile sticky bottom navigation, fluid cards, and touch file uploads.
- **LAN Device Discovery**: Automatic UDP broadcast announcements (port 42424) + heartbeat sweepers.
- **Hierarchical FileTree**: Full directory tree navigation, recursive sizing, and level-order traversal.
- **Streaming Chunked File Transfer**: 64KB - 2MB chunk buffering; handles multi-gigabyte files with constant RAM footprint.
- **SHA-256 Integrity Verification**: End-to-end checksum verification prevents corruption or tampering.
- **Priority Queue Transfer Scheduler**: Urgent small files leapfrog long background synchronization jobs.
- **Intelligent Synchronization Engine**: Tree diffing detects `SYNCED`, `NEW`, `MODIFIED`, and `CONFLICT`.
- **Conflict Resolution**: Never overwrites files silently; provides `KEEP_LOCAL`, `KEEP_REMOTE`, and `KEEP_BOTH` (automatic suffix renaming).
- **Duplicate File Detection**: $O(1)$ duplicate clustering by SHA-256 hash with 1-click cleanup.
- **Interactive DSA Visualizer**: Dedicated college evaluation dashboard exposing internal bucket chains, heap trees, and graph algorithms.
- **6-Digit Pairing Security**: Numeric pairing authorization with role-based permissions (`READ_ONLY`, `DOWNLOADER`, `CONTRIBUTOR`, `FULL_ACCESS`).
- **Path Traversal Barrier**: Strict root verification prevents directory traversal attacks (`../`).
- **Single-Laptop Demo Mode**: Built-in simulator generating virtual peer nodes (`Laptop-A`, `Laptop-B`, `Laptop-C`) for solo evaluations.

---

## 4. Architecture

```text
                 OFFLINE LOCAL ROUTER (Internet: OFF)
                                │
        ┌───────────────────────┴───────────────────────┐
        │                                               │
   [Laptop A]                                      [Laptop B]
   IP: 192.168.1.10                                IP: 192.168.1.11
   Role: Host / Peer                               Role: Client / Peer
        │                                               │
   ├── FastAPI Server (:8000)                      ├── Web Browser / FastAPI
   ├── FileTree & Trie                             ├── FileTree & Trie
   ├── Hash Table Index (O(1))                     ├── Hash Table Index (O(1))
   ├── Priority Heap Transfer Scheduler            ├── Priority Heap Transfer Scheduler
   └── Streaming Hasher (SHA-256)                  └── Streaming Hasher (SHA-256)
```

---

## 5. Technology Stack

- **Backend**: Python 3.10+ • FastAPI • Uvicorn • WebSockets
- **Networking**: Python `socket` (UDP Broadcast on port 42424) • `requests`
- **Database**: SQLite3 with Write-Ahead Logging (WAL mode)
- **Frontend**: Vanilla CSS Glassmorphism • Vanilla Modern JavaScript • HTML5 Semantic Design
- **Typography**: Google Fonts Outfit & JetBrains Mono (cached locally)

---

## 6. Data Structures and Algorithms (DSA) Concepts

| Data Structure / Algorithm | System Subsystem | Practical Problem Solved | Average Time Complexity | Worst Case Complexity | Space Complexity |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Hierarchical Tree (`FileTree`)** | File System Manager | Directory nesting, recursive sizing & subtree aggregation | $O(k)$ per path depth | $O(k)$ | $O(N)$ |
| **Separate Chaining `HashTable`** | Metadata & Duplicate Index | $O(1)$ file lookup and duplicate SHA-256 clustering | $O(1)$ | $O(N)$ (if all collide) | $O(M + N)$ |
| **Prefix Tree (`FilenameTrie`)** | Real-time Search | Instant autocomplete without scanning entire directory list | $O(P + K)$ | $O(P + K)$ | $O(\Sigma \cdot L)$ |
| **Doubly-Linked FIFO `Queue`** | Transfer Queue | Sequential First-In First-Out transfer ordering | $O(1)$ | $O(1)$ | $O(N)$ |
| **Binary Min-Heap (`PriorityHeap`)** | Transfer Scheduler | Urgent requests leapfrog background synchronization | $O(\log N)$ | $O(\log N)$ | $O(N)$ |
| **Adjacency List `NetworkGraph`** | Topology Manager | BFS hop counts, DFS reachability & Dijkstra routing | $O(V + E)$ | $O((V+E) \log V)$ | $O(V + E)$ |
| **Merge Sort & Quick Sort** | Multi-attribute Sorter | Benchmarking stable vs in-place sorting on file catalogs | $O(N \log N)$ | $O(N^2)$ (Quick) | $O(N)$ / $O(\log N)$ |
| **Streaming SHA-256 Hasher** | Integrity & Sync Diffing | Fixed 64KB RAM chunk verification for gigabyte files | $O(\text{Bytes}/64\text{KB})$ | $O(\text{Bytes}/64\text{KB})$ | $O(1)$ constant |

---

## 7. Installation & Quick Start

### Prerequisites
- Python 3.10 or higher
- Windows, macOS, or Linux

### Installation Commands

1. **Clone or enter the project directory**:
   ```bash
   cd DSA_CIE_4
   ```

2. **Create and activate a virtual environment (optional but recommended)**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the application**:
   ```bash
   python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
   ```

5. **Open the web dashboard**:
   Navigate to `http://127.0.0.1:8000/` in your browser.

---

## 8. Two-Laptop Offline Router Setup

To test and demonstrate the system across two laptops without Internet access:

1. **Connect both laptops to the same Wi-Fi or Ethernet router**.
2. **Unplug the router's WAN / DSL cable** so the router has zero Internet connection.
3. **On Laptop A (Host)**:
   - Run `python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000`
   - Observe the terminal banner displaying the local LAN IP (e.g. `192.168.1.10`) and 6-digit pairing code (e.g. `583921`).
4. **On Laptop B (Client)**:
   - Open browser and navigate to `http://192.168.1.10:8000/`.
   - Enter the pairing code `583921` to pair and authorize.
   - Browse files, download with streaming progress, and drag-and-drop files to upload.

---

## 9. Academic Demo Mode (Single Laptop)

If presenting on a single machine:
1. Open `http://127.0.0.1:8000/`.
2. Click the **"🧪 Demo Mode"** button in the topbar.
3. The system generates virtual nodes (`Laptop-B`, `Laptop-C`), creates sample files in the FileTree, seeds priority transfers, creates a mock sync conflict, and renders the interactive network topology graph!

---

## 10. Automated Test Suite

All 28 unit and integration tests execute cleanly in under 0.3 seconds:
```bash
python -m unittest discover tests
```

Tests include:
- `tests/test_dsa.py`: Comprehensive test suite for all 8 DSA data structures.
- `tests/test_api_endpoints.py`: Integration tests for FastAPI endpoints, streaming transfers, and sync diffing.

---

## 11. Database Schema

The system persists state locally in `data/offline_sharing.db` (SQLite):
- `devices`: `device_id`, `device_name`, `ip_address`, `port`, `status`, `last_seen`, `trusted`, `role`, `pairing_code`
- `shared_folders`: `id`, `folder_name`, `folder_path`, `enabled`, `created_at`
- `files`: `file_id`, `folder_id`, `file_name`, `relative_path`, `size`, `hash`, `modified_time`, `file_type`
- `transfers`: `transfer_id`, `file_name`, `source_device`, `destination_device`, `direction`, `size`, `transferred_bytes`, `status`, `priority`, `speed`, `hash_verified`
- `sync_conflicts`: `id`, `file_path`, `local_hash`, `remote_hash`, `local_modified`, `remote_modified`, `status`, `resolution`
- `logs`: `id`, `timestamp`, `device`, `operation`, `file_name`, `status`, `message`

---

## 12. Future Extensions

- **Multi-Hop Store-and-Forward**: Transferring files between laptops that cannot communicate directly by routing through an intermediate laptop.
- **Delta/Differential Sync (rsync)**: Transferring only modified byte blocks of a file rather than entire files.
- **QR-Code Mobile Client**: Allowing mobile smartphones connected to local Wi-Fi to scan a QR code to pair and sync instantly.
- **End-to-End ChaCha20/AES-GCM Encryption**: Encrypting streaming file chunks across untrusted local routers.

---

## 13. License

Developed for Academic Demonstration & Data Structures and Algorithms Evaluation.
