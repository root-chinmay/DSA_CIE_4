# System Architecture: Offline LAN File Sharing & Synchronization

## 1. Physical & Network Topology

The architecture operates strictly in local area networks (LAN) where the router has **no Internet connectivity**.

```text
                  LOCAL ROUTER / ACCESS POINT
                  (Internet = COMPLETELY OFFLINE)
                                │
        ┌───────────────────────┴───────────────────────┐
        │                                               │
   [Laptop A]                                      [Laptop B]
   IP: 192.168.1.10                                IP: 192.168.1.11
   Role: Host / Peer                               Role: Client / Peer
        │                                               │
   ├── FastAPI Server (:8000)                      ├── FastAPI Server (:8000)
   ├── UDP Broadcaster (:42424)                    ├── UDP Broadcaster (:42424)
   ├── Directory Scanner                           ├── Directory Scanner
   └── Shared Folder Storage                       └── Shared Folder Storage
```

---

## 2. Software Layers & Component Interaction

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        WEB FRONTEND DASHBOARD                          │
│  (Modern Vanilla CSS Glassmorphism • Google Fonts • Real-Time UI)     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP REST & WebSockets (/ws)
┌───────────────────────────────────▼────────────────────────────────────┐
│                       FASTAPI APPLICATION LAYER                         │
│  ├── Routes: Devices, Files, Folders, Transfers, Sync, DSA, Analytics   │
│  ├── WebSocket Broadcast Manager                                       │
│  └── CORS & Path Security Middleware                                   │
└───────────────────┬───────────────────────────────┬────────────────────┘
                    │                               │
┌───────────────────▼──────────────────┐ ┌──────────▼────────────────────┐
│      FILE MANAGER & STORAGE          │ │      DATA STRUCTURES &        │
│  ├── Streaming SHA-256 Hasher        │ │      ALGORITHMS (DSA)         │
│  ├── Directory Scanner               │ │  ├── FileTree (Hierarchical)  │
│  ├── Path Traversal Barrier          │ │  ├── HashTable & HashIndex    │
│  └── Transfer Priority Scheduler     │ │  ├── FilenameTrie (Prefix)    │
└───────────────────┬──────────────────┘ │  ├── FIFO TransferQueue       │
                    │                    │  ├── Priority Min-Heap        │
┌───────────────────▼──────────────────┐ │  ├── Adjacency NetworkGraph   │
│       SQLITE LOCAL DATABASE          │ │  └── Merge / Quick Sorter     │
│  (devices, files, transfers, logs)   │ └───────────────────────────────┘
└──────────────────────────────────────┘
```

---

## 3. Streaming Chunked Transfer Protocol

To guarantee that multi-gigabyte files do not cause Out-Of-Memory (OOM) crashes:
1. Sender opens file via `aiofiles` / `open(path, 'rb')`.
2. Chunks of size 64KB (or configurable 1MB-5MB) are read iteratively into HTTP stream.
3. Receiver writes each chunk immediately to disk (`open(dest, 'wb')`).
4. Upon stream completion, Receiver computes SHA-256 on the written file and compares with sender's `X-File-SHA256` header.
5. If hashes match $\to$ `COMPLETED` & `hash_verified = 1`. If mismatched $\to$ `FAILED`.

---

## 4. Directory Traversal Security Barrier

To prevent malicious clients from accessing sensitive OS files:
```python
base_root = os.path.realpath(shared_folder_path)
candidate = os.path.realpath(os.path.join(base_root, relative_path.lstrip("/")))
if os.path.commonpath([base_root, candidate]) != base_root:
    raise SecurityError("Directory traversal rejected.")
```
Any path containing `../` or targeting parent directories triggers an instant `400 Bad Request` and logs a security alert.
