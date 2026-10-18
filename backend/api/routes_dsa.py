"""
backend/api/routes_dsa.py
API endpoints powering the interactive DSA Visualizer & Complexity Analysis Dashboard.
Exposes deep internals of FileTree, HashTable, FilenameTrie, TransferQueue,
PriorityHeap, NetworkGraph, and Sorter.
"""

from fastapi import APIRouter
from typing import Dict, Any, List
from backend.file_manager.scanner import get_scanner
from backend.file_manager.transfer_manager import get_transfer_manager
from backend.networking.discovery import get_discovery
from backend.dsa.sorting import Sorter

router = APIRouter(prefix="/api/dsa", tags=["dsa"])


@router.get("/overview")
def get_dsa_overview() -> Dict[str, Any]:
    """
    Returns unified metrics and Big-O complexity documentation for all 8 DSA structures.
    """
    scanner = get_scanner()
    tx_manager = get_transfer_manager()
    discovery = get_discovery()

    tree_stats = scanner.tree.get_stats()
    hash_stats = scanner.hash_index.get_stats()
    trie_stats = scanner.trie.get_stats()
    graph_topology = discovery.graph.get_topology()

    complexity_matrix = [
        {
            "structure": "Hierarchical Tree (FileTree)",
            "purpose": "Hierarchical directory structure & recursive subtree sizing",
            "operations": [
                {"operation": "Insert Path", "time_avg": "O(k)", "time_worst": "O(k)", "space": "O(k)"},
                {"operation": "Find Node", "time_avg": "O(k)", "time_worst": "O(k)", "space": "O(1)"},
                {"operation": "Subtree Size Calculation", "time_avg": "O(N)", "time_worst": "O(N)", "space": "O(H)"},
                {"operation": "DFS Pre-Order Traversal", "time_avg": "O(N)", "time_worst": "O(N)", "space": "O(H)"},
                {"operation": "BFS Level-Order Traversal", "time_avg": "O(N)", "time_worst": "O(N)", "space": "O(W)"}
            ],
            "description": "Represents the nested folder and file relationships without relying on flat OS recursion."
        },
        {
            "structure": "Hash Table (Separate Chaining)",
            "purpose": "O(1) file metadata lookup & O(1) duplicate content clustering",
            "operations": [
                {"operation": "Key Lookup (get)", "time_avg": "O(1)", "time_worst": "O(N)", "space": "O(1)"},
                {"operation": "Key Insertion (put)", "time_avg": "O(1)", "time_worst": "O(N)", "space": "O(1)"},
                {"operation": "Key Deletion (delete)", "time_avg": "O(1)", "time_worst": "O(N)", "space": "O(1)"},
                {"operation": "Rehashing / Dynamic Resize", "time_avg": "O(N)", "time_worst": "O(N)", "space": "O(N)"}
            ],
            "description": f"Custom separate-chaining hash table with load factor threshold 0.75. Current load: {hash_stats['id_index']['load_factor']}."
        },
        {
            "structure": "Prefix Tree (FilenameTrie)",
            "purpose": "Instantaneous filename search and real-time autocomplete suggestions",
            "operations": [
                {"operation": "Token Insertion", "time_avg": "O(L)", "time_worst": "O(L)", "space": "O(L)"},
                {"operation": "Prefix Search", "time_avg": "O(P + K)", "time_worst": "O(P + K)", "space": "O(K)"},
                {"operation": "Autocomplete Query", "time_avg": "O(P + K)", "time_worst": "O(P + K)", "space": "O(K)"}
            ],
            "description": f"Indexed {trie_stats['total_words']} tokens across {trie_stats['total_nodes']} trie nodes for O(L) prefix evaluation."
        },
        {
            "structure": "FIFO Transfer Queue",
            "purpose": "Sequential transfer ordering via Doubly-Linked List",
            "operations": [
                {"operation": "Enqueue", "time_avg": "O(1)", "time_worst": "O(1)", "space": "O(1)"},
                {"operation": "Dequeue", "time_avg": "O(1)", "time_worst": "O(1)", "space": "O(1)"},
                {"operation": "Peek", "time_avg": "O(1)", "time_worst": "O(1)", "space": "O(1)"},
                {"operation": "Cancel by ID", "time_avg": "O(1)", "time_worst": "O(1)", "space": "O(1)"}
            ],
            "description": "Guarantees strict First-In First-Out scheduling for regular file downloads."
        },
        {
            "structure": "Binary Min-Heap (PriorityQueue)",
            "purpose": "Urgency-based transfer scheduling (Critical > High > Normal > Low)",
            "operations": [
                {"operation": "Push (heapify-up)", "time_avg": "O(log N)", "time_worst": "O(log N)", "space": "O(1)"},
                {"operation": "Pop Minimum (heapify-down)", "time_avg": "O(log N)", "time_worst": "O(log N)", "space": "O(1)"},
                {"operation": "Peek Top Priority", "time_avg": "O(1)", "time_worst": "O(1)", "space": "O(1)"},
                {"operation": "Priority Elevation", "time_avg": "O(log N)", "time_worst": "O(log N)", "space": "O(1)"}
            ],
            "description": "Enables urgent interactive requests to immediately leapfrog long background sync jobs."
        },
        {
            "structure": "Adjacency List Network Graph",
            "purpose": "LAN peer topology modeling, reachability, and shortest routing paths",
            "operations": [
                {"operation": "Add Node / Edge", "time_avg": "O(1)", "time_worst": "O(1)", "space": "O(1)"},
                {"operation": "BFS Hop Traversal", "time_avg": "O(V + E)", "time_worst": "O(V + E)", "space": "O(V)"},
                {"operation": "DFS Traversal", "time_avg": "O(V + E)", "time_worst": "O(V + E)", "space": "O(V)"},
                {"operation": "Dijkstra Shortest Path", "time_avg": "O((V+E) log V)", "time_worst": "O((V+E) log V)", "space": "O(V)"}
            ],
            "description": f"Models {graph_topology['total_devices']} active LAN devices and {graph_topology['total_links']} communication links."
        },
        {
            "structure": "Sorting Engine (Merge Sort & Quick Sort)",
            "purpose": "Multi-attribute file sorting by name, size, modified date, and type",
            "operations": [
                {"operation": "Merge Sort", "time_avg": "O(N log N)", "time_worst": "O(N log N)", "space": "O(N)"},
                {"operation": "Quick Sort", "time_avg": "O(N log N)", "time_worst": "O(N^2)", "space": "O(log N)"}
            ],
            "description": "Pure custom divide-and-conquer sorting implementations with comparison counter metrics."
        },
        {
            "structure": "Cryptographic Streaming Hasher (SHA-256)",
            "purpose": "File integrity verification, change detection, and duplicate clustering",
            "operations": [
                {"operation": "Chunk Hashing", "time_avg": "O(Bytes / 64KB)", "time_worst": "O(Bytes / 64KB)", "space": "O(1) (64KB RAM)"},
                {"operation": "Integrity Check", "time_avg": "O(1) hex compare", "time_worst": "O(1)", "space": "O(1)"}
            ],
            "description": "Never loads complete large files into RAM; computes digest using fixed 64KB memory blocks."
        }
    ]

    return {
        "tree_stats": tree_stats,
        "hash_stats": hash_stats,
        "trie_stats": trie_stats,
        "graph_stats": graph_topology,
        "active_queue_size": tx_manager.fifo_queue.size(),
        "priority_heap_size": tx_manager.priority_heap.size(),
        "complexities": complexity_matrix
    }


@router.get("/tree")
def get_dsa_tree():
    """Returns Tree structure and traversal orders."""
    scanner = get_scanner()
    dfs_nodes = [{"name": n.name, "path": n.relative_path, "size": n.size, "is_dir": n.is_dir} for n in scanner.tree.dfs()]
    bfs_nodes = [{"level": lvl, "name": n.name, "path": n.relative_path, "is_dir": n.is_dir} for lvl, n in scanner.tree.bfs()]
    return {
        "tree_hierarchy": scanner.tree.to_dict(),
        "dfs_traversal": dfs_nodes,
        "bfs_traversal": bfs_nodes
    }


@router.get("/hash_table")
def get_dsa_hash_table():
    """Returns Hash Table bucket distribution and entries."""
    scanner = get_scanner()
    return {
        "id_index_stats": scanner.hash_index.id_index.get_stats(),
        "id_index_buckets": scanner.hash_index.id_index.to_visual_dict(),
        "hash_index_stats": scanner.hash_index.hash_index.get_stats(),
        "duplicates": scanner.hash_index.find_duplicates()
    }


@router.get("/trie")
def get_dsa_trie(depth: int = 3):
    """Returns Trie visual hierarchy and stats."""
    scanner = get_scanner()
    return {
        "stats": scanner.trie.get_stats(),
        "visual_trie": scanner.trie.to_visual_dict(max_depth=depth)
    }


@router.get("/heap")
def get_dsa_heap():
    """Returns Priority Heap tree structure and priority items."""
    tx_manager = get_transfer_manager()
    return {
        "heap_tree": tx_manager.priority_heap.to_heap_tree(),
        "heap_items": tx_manager.priority_heap.to_list()
    }


@router.post("/benchmark_sort")
def benchmark_sort(by: str = "size"):
    """Runs both Merge Sort and Quick Sort side-by-side to compare comparisons and timing."""
    scanner = get_scanner()
    files = scanner.get_all_files()

    _, merge_metrics = Sorter.merge_sort(files, by)
    _, quick_metrics = Sorter.quick_sort(files, by)

    return {
        "total_items": len(files),
        "sorted_by": by,
        "merge_sort": merge_metrics,
        "quick_sort": quick_metrics
    }
