# REST & WebSocket API Documentation

Base URL: `http://<LOCAL_LAN_IP>:8000`

---

## 1. Device Discovery & Pairing

### `GET /api/devices`
Returns all discovered peers on the LAN.
```json
{
  "devices": [
    {
      "device_id": "dev_laptop_b",
      "device_name": "Laptop-B (Client)",
      "ip_address": "192.168.1.11",
      "port": 8000,
      "status": "online",
      "trusted": 1,
      "role": "CONTRIBUTOR"
    }
  ]
}
```

### `GET /api/devices/ping`
Returns host identity, detected LAN IP, port, and pairing code.

### `POST /api/devices/pair`
Authenticates a peer device using the 6-digit pairing code.
- **Body**: `{"device_id": "dev_xyz", "device_name": "Laptop-B", "pairing_code": "583921"}`

### `POST /api/devices/connect`
Manually connects to a peer by IP and port when UDP broadcast is blocked.
- **Body**: `{"ip_address": "192.168.1.15", "port": 8000, "pairing_code": "583921"}`

### `GET /api/devices/graph`
Returns NetworkGraph topology vertices and weighted latency edges.

### `GET /api/devices/graph/bfs` & `/api/devices/graph/dfs`
Executes BFS or DFS traversal from given root node.

### `GET /api/devices/graph/shortest_path?start_id=...&end_id=...`
Computes Dijkstra's shortest path routing.

---

## 2. File Operations & Search

### `GET /api/files`
Returns indexed files with optional filtering and custom sorting.
- **Query Params**: `folder`, `sort_by` (name, size, modified_time, file_type), `algorithm` (merge_sort, quick_sort), `reverse` (true/false)

### `GET /api/files/tree`
Returns the hierarchical FileTree serialized as nested JSON.

### `GET /api/files/duplicates`
Returns duplicate file groups sharing identical SHA-256 hashes.

### `GET /api/files/search?q=...&autocomplete=true`
Prefix search and autocomplete powered by the FilenameTrie.

### `GET /api/files/{id}/download`
Chunked streaming download of file data with `X-File-SHA256` header.

### `POST /api/files/upload`
Multipart chunked file upload to shared folder.

### `POST /api/files/{id}/delete` & `POST /api/files/{id}/rename`
Safe file deletion and renaming.

---

## 3. Transfer Queue & Priority Scheduler

### `GET /api/transfers`
Returns FIFO queue, Priority Min-Heap items, heap tree structure, active transfers, and history.

### `POST /api/transfers`
Enqueues a new transfer task:
- **Body**: `{"file_name": "...", "size": 1024, "source_device": "...", "destination_device": "...", "priority": 1}`

### `POST /api/transfers/{id}/priority`
Dynamically elevates or reduces transfer priority in the Min-Heap.
- **Body**: `{"priority": 0}` (0=Critical, 1=High, 2=Normal, 3=Low)

---

## 4. File Synchronization & Conflicts

### `GET /api/sync/diff`
Computes tree diff matrix (SYNCED, NEW, MODIFIED, CONFLICT).

### `POST /api/sync/start`
Enqueues background transfer tasks for all pending diff items.

### `GET /api/sync/conflicts`
Lists active synchronization conflicts.

### `POST /api/sync/conflicts/{id}/resolve`
Resolves conflict (`KEEP_LOCAL`, `KEEP_REMOTE`, `KEEP_BOTH`).

---

## 5. WebSocket Real-Time Events (`/ws`)

Clients receive live JSON messages:
- `TRANSFER_PROGRESS`: `{ "transfer_id": "...", "percentage": 78.5, "speed": 8.4, "eta": 4.2 }`
- `TRANSFER_COMPLETED`: `{ "transfer_id": "...", "file_name": "...", "hash_verified": true }`
- `DEVICE_CONNECTED`: `{ "device_id": "...", "device_name": "...", "ip_address": "..." }`
- `CONFLICT_DETECTED`: `{ "file_path": "..." }`
- `LOG_EVENT`: `{ "timestamp": ..., "operation": "...", "message": "..." }`
