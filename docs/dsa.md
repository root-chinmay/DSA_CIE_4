# Data Structures & Algorithms (DSA) Specification & Analysis

## Overview

In the **Offline LAN File Sharing & Synchronization System**, Data Structures and Algorithms (DSA) are not superficial additions; they form the operational foundation of every networking, indexing, scheduling, and synchronization subsystem.

---

## 1. Hierarchical Directory Tree (`FileTree`)

### Problem Solved
Filesystems are inherently hierarchical. Storing and transmitting nested folder structures as flat paths creates redundant path parsing, makes subtree size calculations expensive ($O(N^2)$), and prevents efficient hierarchical browsing and level-order serialization.

### Solution
A logical tree structure composed of `FileNode` instances, decoupled from OS filesystem operations.

```text
SharedRoot
├── Documents [Size: 45.2 MB]
│   ├── report_final.pdf [Size: 42.0 MB]
│   └── notes.txt [Size: 3.2 MB]
└── Algorithms [Size: 12.8 KB]
    ├── merge_sort.py [Size: 6.4 KB]
    └── quick_sort.py [Size: 6.4 KB]
```

### Operations & Complexity
| Operation | Average Time | Worst Time | Space Complexity | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Insert Path** | $O(k)$ | $O(k)$ | $O(k)$ | $k$ = path depth; traverses or creates intermediate folder nodes |
| **Find Node** | $O(k)$ | $O(k)$ | $O(1)$ | Direct segment traversal via child hash maps |
| **Delete Node** | $O(k)$ | $O(k)$ | $O(1)$ | Unlinks target node from parent's children dictionary |
| **Subtree Size** | $O(N)$ | $O(N)$ | $O(H)$ | Post-order traversal aggregating child sizes into parent ($H$ = tree height) |
| **DFS Traversal** | $O(N)$ | $O(N)$ | $O(H)$ | Pre-order depth-first traversal for recursive directory scans |
| **BFS Traversal** | $O(N)$ | $O(N)$ | $O(W)$ | Level-order queue traversal ($W$ = max width) for hierarchical rendering |

---

## 2. Separate-Chaining Hash Table (`HashTable` & `FileHashIndex`)

### Problem Solved
When thousands of files are shared on a LAN, looking up metadata or verifying if a file is already indexed must not require linear $O(N)$ list scanning. Furthermore, detecting whether an incoming file already exists on disk requires instantaneous content matching.

### Solution
A custom separate-chaining Hash Table with polynomial rolling hash function, dynamic rehashing at load factor $\lambda = 0.75$, and collision metric tracking.

$$hash(s) = \left( \sum_{i=0}^{L-1} s[i] \cdot 31^{L-1-i} \right) \pmod M$$

### Operations & Complexity
| Operation | Average Time | Worst Case | Space Complexity | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **`put(key, value)`** | $O(1)$ | $O(N)$ | $O(1)$ | Inserts at head of bucket chain; collision tracked |
| **`get(key)`** | $O(1)$ | $O(N)$ | $O(1)$ | Traverses bucket linked list |
| **`delete(key)`** | $O(1)$ | $O(N)$ | $O(1)$ | Unlinks node from bucket chain |
| **`_resize(2M)`** | $O(N)$ | $O(N)$ | $O(N)$ | Triggered when $\lambda = \frac{N}{M} > 0.75$ |

### Multi-Index System (`FileHashIndex`)
1. **Primary Index**: `file_id -> FileMetadata` ($O(1)$ lookup)
2. **Duplicate Content Index**: `sha256_hash -> List[file_id]` ($O(1)$ duplicate grouping)
3. **Path Index**: `relative_path -> file_id` ($O(1)$ path resolution)

---

## 3. Cryptographic Streaming Hasher (SHA-256)

### Problem Solved
Comparing files solely by filename or file size leads to false positives (two distinct files can share identical names/sizes) or silent corruption during network transfer. Loading entire multi-gigabyte files into RAM crashes standard laptops.

### Solution
Chunk-buffered cryptographic hashing. Reads 64KB blocks sequentially into `hashlib.sha256()`.

```text
File on Disk (e.g. 500 MB)
 ├── Block 1 (64 KB) ──► SHA-256 Engine
 ├── Block 2 (64 KB) ──► SHA-256 Engine
 └── Block N (64 KB) ──► Final Digest: a8f9c7e2...
RAM Usage: Fixed 64 KB constant footprint
```

### Complexity
- **Time Complexity**: $O\left(\frac{\text{File Size}}{\text{Block Size}}\right) = O(B)$
- **Space Complexity**: $O(1)$ (64 KB constant buffer)

---

## 4. First-In First-Out Transfer Queue (`TransferQueue`)

### Problem Solved
Uncontrolled concurrent network downloads saturate router Wi-Fi bandwidth, increase packet drop rates, and cause timeouts. Standard file transfers require predictable sequential processing.

### Solution
A thread-safe Doubly-Linked List FIFO queue with an internal index dictionary for instantaneous $O(1)$ cancellation by ID.

```text
HEAD (Front)                                             TAIL (Rear)
 ┌─────────┐      ┌─────────┐      ┌─────────┐      ┌─────────┐
 │ File 1  │◄────►│ File 2  │◄────►│ File 3  │◄────►│ File 4  │
 └─────────┘      └─────────┘      └─────────┘      └─────────┘
      ▲                                                  ▲
   Dequeue                                            Enqueue
```

### Operations & Complexity
| Operation | Time Complexity | Space Complexity |
| :--- | :--- | :--- |
| **Enqueue** | $O(1)$ | $O(1)$ |
| **Dequeue** | $O(1)$ | $O(1)$ |
| **Peek** | $O(1)$ | $O(1)$ |
| **Remove by ID** | $O(1)$ | $O(1)$ via hash pointer |

---

## 5. Binary Min-Heap Priority Queue (`PriorityHeap`)

### Problem Solved
In a peer-to-peer system, background synchronization of large bulk archives (e.g. a 5GB backup folder) would starve small, urgent interactive requests (e.g. a 500KB presentation or security token) if scheduled strictly via FIFO queueing.

### Solution
A Binary Min-Heap Priority Queue where lower integer values signify higher urgency:
- `CRITICAL = 0`: Urgent emergency control packets & security tokens
- `HIGH = 1`: Interactive user-requested single files
- `NORMAL = 2`: Standard user transfers
- `LOW = 3`: Background folder synchronization & bulk mirroring

$$\text{Parent}(i) = \left\lfloor \frac{i - 1}{2} \right\rfloor, \quad \text{Left}(i) = 2i + 1, \quad \text{Right}(i) = 2i + 2$$

### Operations & Complexity
| Operation | Time Complexity | Space Complexity |
| :--- | :--- | :--- |
| **`push(item, priority)`** | $O(\log N)$ | $O(1)$ (amortized) |
| **`pop()`** | $O(\log N)$ | $O(1)$ |
| **`peek()`** | $O(1)$ | $O(1)$ |
| **`update_priority(id, p)`** | $O(\log N)$ | $O(1)$ |

---

## 6. Prefix Tree / Trie (`FilenameTrie`)

### Problem Solved
Linear filename search ($O(N \cdot M)$) degrades responsiveness as shared files multiply. Users expect real-time autocomplete suggestions as they type each character.

### Solution
A 26-way+ character Trie indexing both complete filenames and constituent alphanumeric tokens (e.g., `"annual_report_2026.pdf"` produces tokens `"annual"`, `"report"`, `"2026"`, `"pdf"`).

```text
            (ROOT)
           /      \
        'p'        'r'
        /            \
      'r'            'e'
      /                \
    'o'                'p'
    /                    \
  'j' [WORD: project]    'o'
                           \
                           'r'
                             \
                             't' [WORD: report]
```

### Operations & Complexity
| Operation | Time Complexity | Space Complexity |
| :--- | :--- | :--- |
| **Token Insertion** | $O(L)$ ($L$ = token length) | $O(L \cdot |\Sigma|)$ |
| **Prefix Search** | $O(P + K)$ ($P$ = prefix length, $K$ = matches) | $O(K)$ |
| **Autocomplete** | $O(P + K)$ | $O(K)$ |

---

## 7. Adjacency List Network Graph (`NetworkGraph`)

### Problem Solved
Devices on a router form an ad-hoc local network mesh. The system must determine device reachability, compute minimum hop distances, and choose optimal transfer routes.

### Solution
An Adjacency List Graph $G = (V, E)$ where vertices represent laptops and edges represent communication channels annotated with latency (ms) and bandwidth (Mbps).

### Graph Algorithms
1. **Breadth-First Search (BFS)**: Computes minimum network hop counts from the host to all reachable LAN peers ($O(V + E)$).
2. **Depth-First Search (DFS)**: Recursively traverses connected LAN subgraphs ($O(V + E)$).
3. **Dijkstra's Shortest Path**: Employs a min-heap to determine the lowest-latency communication route across multi-hop peer topologies ($O((V + E) \log V)$).

---

## 8. Custom Sorting Engine (`MergeSort` & `QuickSort`)

### Problem Solved
File explorers require flexible sorting across multiple dimensions: Name, Size, Date Modified, and Type.

### Solution
Pure divide-and-conquer custom sorting implementations with empirical comparison counters and timing instrumentation:
1. **Merge Sort**: Stable sorting algorithm with guaranteed $O(N \log N)$ worst-case performance; ideal when preserving relative order is critical.
2. **Quick Sort**: In-place partitioning algorithm with $O(N \log N)$ average performance and minimal $O(\log N)$ memory overhead.
