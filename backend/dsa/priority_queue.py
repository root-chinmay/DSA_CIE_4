"""
backend/dsa/priority_queue.py
Binary Min-Heap Priority Queue for Priority-Based File Transfer Scheduling.

Priority Levels:
- CRITICAL = 0 (Urgent control file / emergency sync)
- HIGH     = 1 (Urgent small files, interactive user requests)
- NORMAL   = 2 (Standard user transfers)
- LOW      = 3 (Background synchronization, bulk downloads)

Time Complexity:
- Push / Insertion: O(log N)
- Pop / Extraction: O(log N)
- Peek: O(1)
- Priority Update: O(log N)
- Removal: O(log N)
Space Complexity: O(N) array representation.
"""

from typing import Any, List, Optional, Dict
import threading
import time


class PriorityItem:
    """Wrapper holding priority, entry index, and transfer payload."""

    def __init__(self, priority: int, sequence: int, item: Any, item_id: str):
        self.priority: int = priority
        self.sequence: int = sequence
        self.item: Any = item
        self.item_id: str = str(item_id)
        self.enqueued_at: float = time.time()

    def __lt__(self, other: 'PriorityItem') -> bool:
        # Smaller priority integer = Higher urgency
        if self.priority != other.priority:
            return self.priority < other.priority
        # Secondary tie-breaker: FIFO sequence
        return self.sequence < other.sequence


class PriorityHeap:
    """
    Thread-safe Array-Based Binary Min-Heap Priority Queue.
    Maintains index position map for O(log N) priority updates and removals.
    """

    PRIORITY_NAMES = {
        0: "CRITICAL",
        1: "HIGH",
        2: "NORMAL",
        3: "LOW"
    }

    def __init__(self):
        self._heap: List[PriorityItem] = []
        self._index_map: Dict[str, int] = {}  # item_id -> index in _heap
        self._counter: int = 0
        self._lock: threading.Lock = threading.Lock()

    def _swap(self, i: int, j: int) -> None:
        self._heap[i], self._heap[j] = self._heap[j], self._heap[i]
        self._index_map[self._heap[i].item_id] = i
        self._index_map[self._heap[j].item_id] = j

    def _heapify_up(self, index: int) -> None:
        """Restores min-heap property upward from index."""
        while index > 0:
            parent = (index - 1) // 2
            if self._heap[index] < self._heap[parent]:
                self._swap(index, parent)
                index = parent
            else:
                break

    def _heapify_down(self, index: int) -> None:
        """Restores min-heap property downward from index."""
        size = len(self._heap)
        while True:
            left = 2 * index + 1
            right = 2 * index + 2
            smallest = index

            if left < size and self._heap[left] < self._heap[smallest]:
                smallest = left

            if right < size and self._heap[right] < self._heap[smallest]:
                smallest = right

            if smallest != index:
                self._swap(index, smallest)
                index = smallest
            else:
                break

    def push(self, item: Any, priority: int = 2, item_id: Optional[str] = None) -> None:
        """
        Inserts an item with given priority (0=Critical, 1=High, 2=Normal, 3=Low).
        Time Complexity: O(log N)
        """
        with self._lock:
            key = str(item_id or (getattr(item, "transfer_id", None) or (item.get("id") if isinstance(item, dict) else id(item))))
            self._counter += 1
            node = PriorityItem(priority, self._counter, item, key)

            index = len(self._heap)
            self._heap.append(node)
            self._index_map[key] = index
            self._heapify_up(index)

    def pop(self) -> Optional[Any]:
        """
        Extracts and returns the highest-priority item (minimum priority value).
        Time Complexity: O(log N)
        """
        with self._lock:
            if not self._heap:
                return None

            top = self._heap[0]
            last = self._heap.pop()
            del self._index_map[top.item_id]

            if self._heap:
                self._heap[0] = last
                self._index_map[last.item_id] = 0
                self._heapify_down(0)

            return top.item

    def peek(self) -> Optional[Any]:
        """
        Views the highest-priority item without extracting.
        Time Complexity: O(1)
        """
        with self._lock:
            return self._heap[0].item if self._heap else None

    def update_priority(self, item_id: str, new_priority: int) -> bool:
        """
        Dynamically changes priority of a queued item.
        Time Complexity: O(log N)
        """
        with self._lock:
            key = str(item_id)
            if key not in self._index_map:
                return False

            index = self._index_map[key]
            old_priority = self._heap[index].priority
            self._heap[index].priority = new_priority

            if new_priority < old_priority:
                self._heapify_up(index)
            else:
                self._heapify_down(index)
            return True

    def remove(self, item_id: str) -> Optional[Any]:
        """
        Removes an arbitrary item from the heap by ID.
        Time Complexity: O(log N)
        """
        with self._lock:
            key = str(item_id)
            if key not in self._index_map:
                return None

            index = self._index_map[key]
            removed = self._heap[index]

            last = self._heap.pop()
            del self._index_map[key]

            if index < len(self._heap):
                self._heap[index] = last
                self._index_map[last.item_id] = index
                self._heapify_up(index)
                self._heapify_down(index)

            return removed.item

    def size(self) -> int:
        with self._lock:
            return len(self._heap)

    def is_empty(self) -> bool:
        with self._lock:
            return len(self._heap) == 0

    def to_list(self) -> List[Dict[str, Any]]:
        """
        Returns all queued items with their priority names and metadata.
        """
        with self._lock:
            # Sort a copy by priority for display
            sorted_items = sorted(self._heap)
            return [
                {
                    "item_id": node.item_id,
                    "priority": node.priority,
                    "priority_name": self.PRIORITY_NAMES.get(node.priority, "NORMAL"),
                    "item": node.item,
                    "enqueued_at": node.enqueued_at
                }
                for node in sorted_items
            ]

    def to_heap_tree(self) -> List[Dict[str, Any]]:
        """
        Returns heap array with parent/child relationship indices
        for the DSA Visualizer binary tree renderer.
        """
        with self._lock:
            tree_nodes = []
            for i, node in enumerate(self._heap):
                left_idx = 2 * i + 1
                right_idx = 2 * i + 2
                tree_nodes.append({
                    "index": i,
                    "item_id": node.item_id,
                    "priority": node.priority,
                    "priority_name": self.PRIORITY_NAMES.get(node.priority, "NORMAL"),
                    "title": str(getattr(node.item, "file_name", None) or (node.item.get("file_name") if isinstance(node.item, dict) else node.item_id)),
                    "left_child": left_idx if left_idx < len(self._heap) else None,
                    "right_child": right_idx if right_idx < len(self._heap) else None
                })
            return tree_nodes
