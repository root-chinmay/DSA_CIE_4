"""
backend/dsa/queue.py
Custom FIFO Transfer Queue implemented via Doubly Linked List.

Time Complexity:
- Enqueue: O(1)
- Dequeue: O(1)
- Peek: O(1)
- Is Empty: O(1)
- Size: O(1)
- Remove by ID: O(1) using internal node pointer map
Space Complexity: O(N) where N is number of queued transfer tasks.
"""

from typing import Any, Optional, List, Dict
import threading


class QueueNode:
    """A node in a doubly-linked queue."""

    def __init__(self, value: Any):
        self.value: Any = value
        self.prev: Optional['QueueNode'] = None
        self.next: Optional['QueueNode'] = None


class TransferQueue:
    """
    Thread-safe Doubly-Linked FIFO Queue with fast cancellation by ID.
    Used for standard FIFO file transfer scheduling.
    """

    def __init__(self):
        self.head: Optional[QueueNode] = None  # Front of queue (dequeued from here)
        self.tail: Optional[QueueNode] = None  # Rear of queue (enqueued here)
        self._size: int = 0
        self._node_map: Dict[str, QueueNode] = {}  # task_id -> QueueNode for O(1) removal
        self._lock: threading.Lock = threading.Lock()

    def enqueue(self, item: Any, item_id: Optional[str] = None) -> None:
        """
        Adds an item to the rear of the queue.
        Time Complexity: O(1)
        """
        with self._lock:
            new_node = QueueNode(item)
            if not self.tail:
                self.head = new_node
                self.tail = new_node
            else:
                new_node.prev = self.tail
                self.tail.next = new_node
                self.tail = new_node

            self._size += 1

            # Map identifier for O(1) random-access removal (e.g. transfer cancellation)
            key = item_id or (getattr(item, "transfer_id", None) or (item.get("id") if isinstance(item, dict) else None))
            if key:
                self._node_map[str(key)] = new_node

    def dequeue(self) -> Optional[Any]:
        """
        Removes and returns the item from the front of the queue.
        Time Complexity: O(1)
        """
        with self._lock:
            if not self.head:
                return None

            removed_node = self.head
            item = removed_node.value

            self.head = removed_node.next
            if self.head:
                self.head.prev = None
            else:
                self.tail = None

            self._size -= 1

            # Remove from node map
            key = getattr(item, "transfer_id", None) or (item.get("id") if isinstance(item, dict) else None)
            if key and str(key) in self._node_map:
                del self._node_map[str(key)]

            return item

    def peek(self) -> Optional[Any]:
        """
        Returns the front item without removing it.
        Time Complexity: O(1)
        """
        with self._lock:
            return self.head.value if self.head else None

    def remove(self, item_id: str) -> Optional[Any]:
        """
        Removes an arbitrary item by ID in O(1) time using node pointer map.
        Time Complexity: O(1)
        """
        with self._lock:
            node = self._node_map.get(str(item_id))
            if not node:
                return None

            if node.prev:
                node.prev.next = node.next
            else:
                self.head = node.next

            if node.next:
                node.next.prev = node.prev
            else:
                self.tail = node.prev

            self._size -= 1
            del self._node_map[str(item_id)]
            return node.value

    def is_empty(self) -> bool:
        """Checks if queue contains no elements."""
        with self._lock:
            return self._size == 0

    def size(self) -> int:
        """Returns the number of elements in the queue."""
        with self._lock:
            return self._size

    def to_list(self) -> List[Any]:
        """
        Returns list of items from Front to Rear.
        Time Complexity: O(N)
        """
        with self._lock:
            items = []
            current = self.head
            while current:
                items.append(current.value)
                current = current.next
            return items

    def clear(self) -> None:
        """Clears all elements."""
        with self._lock:
            self.head = None
            self.tail = None
            self._size = 0
            self._node_map.clear()
