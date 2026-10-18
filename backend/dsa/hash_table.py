"""
backend/dsa/hash_table.py
Custom Hash Table implementation using Separate Chaining.

Time Complexity:
- Average Search: O(1)
- Worst Case Search (all keys collide): O(N)
- Average Insertion: O(1)
- Average Deletion: O(1)
- Rehashing: O(N) when load factor exceeds threshold (default 0.75)
Space Complexity: O(M + N) where M is bucket capacity and N is number of elements.
"""

from typing import Any, List, Optional, Tuple, Dict


class HashNode:
    """A node in a separate-chaining linked list."""

    def __init__(self, key: str, value: Any, next_node: Optional['HashNode'] = None):
        self.key: str = key
        self.value: Any = value
        self.next: Optional['HashNode'] = next_node


class HashTable:
    """
    Custom Hash Table utilizing polynomial rolling hash and separate chaining.
    Includes collision tracking, dynamic rehashing, and visualization inspection.
    """

    def __init__(self, initial_capacity: int = 16, load_factor_threshold: float = 0.75):
        self.capacity: int = max(4, initial_capacity)
        self.load_factor_threshold: float = load_factor_threshold
        self.size: int = 0
        self.buckets: List[Optional[HashNode]] = [None] * self.capacity
        self.total_collisions: int = 0

    def _hash(self, key: str) -> int:
        """
        Polynomial rolling hash function.
        hash(s) = (s[0]*p^(n-1) + s[1]*p^(n-2) + ... + s[n-1]) % capacity
        """
        p = 31
        hash_val = 0
        for char in key:
            hash_val = (hash_val * p + ord(char)) % self.capacity
        return hash_val

    def put(self, key: str, value: Any) -> int:
        """
        Inserts or updates a key-value pair.
        Returns the number of collisions encountered during insertion.
        Time Complexity: Average O(1), Worst O(N)
        """
        if (self.size + 1) / self.capacity > self.load_factor_threshold:
            self._resize(self.capacity * 2)

        index = self._hash(key)
        current = self.buckets[index]
        collisions = 0

        # Check if key already exists
        head = current
        while head:
            if head.key == key:
                head.value = value
                return collisions
            collisions += 1
            head = head.next

        # If bucket is not empty, this is a collision
        if current is not None:
            self.total_collisions += 1

        # Insert at head of the chain (O(1) insertion)
        new_node = HashNode(key, value, next_node=current)
        self.buckets[index] = new_node
        self.size += 1
        return collisions

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieves the value for a given key.
        Time Complexity: Average O(1), Worst O(N)
        """
        index = self._hash(key)
        current = self.buckets[index]
        while current:
            if current.key == key:
                return current.value
            current = current.next
        return default

    def contains(self, key: str) -> bool:
        """Checks if key is present in the hash table."""
        return self.get(key) is not None

    def delete(self, key: str) -> bool:
        """
        Deletes a key-value pair.
        Time Complexity: Average O(1), Worst O(N)
        """
        index = self._hash(key)
        current = self.buckets[index]
        prev: Optional[HashNode] = None

        while current:
            if current.key == key:
                if prev:
                    prev.next = current.next
                else:
                    self.buckets[index] = current.next
                self.size -= 1
                return True
            prev = current
            current = current.next
        return False

    def _resize(self, new_capacity: int) -> None:
        """
        Doubles the bucket array and rehashes all elements.
        Time Complexity: O(N)
        """
        old_buckets = self.buckets
        self.capacity = new_capacity
        self.buckets = [None] * new_capacity
        self.size = 0
        self.total_collisions = 0

        for head in old_buckets:
            current = head
            while current:
                self.put(current.key, current.value)
                current = current.next

    def items(self) -> List[Tuple[str, Any]]:
        """Returns all (key, value) pairs."""
        result = []
        for head in self.buckets:
            current = head
            while current:
                result.append((current.key, current.value))
                current = current.next
        return result

    def keys(self) -> List[str]:
        return [k for k, _ in self.items()]

    def values(self) -> List[Any]:
        return [v for _, v in self.items()]

    def clear(self) -> None:
        """Clears all entries and resets buckets."""
        self.buckets = [None] * self.capacity
        self.size = 0
        self.total_collisions = 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Returns load factor, collision counts, and chain distribution
        metrics for the DSA Visualizer.
        """
        chain_lengths = []
        occupied_buckets = 0

        for head in self.buckets:
            length = 0
            current = head
            while current:
                length += 1
                current = current.next
            chain_lengths.append(length)
            if length > 0:
                occupied_buckets += 1

        max_chain = max(chain_lengths) if chain_lengths else 0
        avg_chain = (sum(chain_lengths) / occupied_buckets) if occupied_buckets > 0 else 0.0

        return {
            "capacity": self.capacity,
            "size": self.size,
            "load_factor": round(self.size / self.capacity, 3),
            "load_factor_threshold": self.load_factor_threshold,
            "total_collisions": self.total_collisions,
            "occupied_buckets": occupied_buckets,
            "empty_buckets": self.capacity - occupied_buckets,
            "max_chain_length": max_chain,
            "avg_chain_length": round(avg_chain, 2)
        }

    def to_visual_dict(self) -> List[Dict[str, Any]]:
        """
        Produces bucket breakdown for interactive visualizer.
        """
        result = []
        for i, head in enumerate(self.buckets):
            chain = []
            current = head
            while current:
                chain.append({
                    "key": current.key,
                    "value_preview": str(current.value)[:40] if current.value is not None else "None"
                })
                current = current.next
            result.append({
                "bucket_index": i,
                "chain_length": len(chain),
                "entries": chain
            })
        return result


class FileHashIndex:
    """
    High-performance indexing system using HashTable:
    1. Primary index: file_id -> FileMetadata (O(1) lookup)
    2. Content index: sha256_hash -> List[file_id] (O(1) duplicate detection)
    3. Path index: relative_path -> file_id (O(1) path resolution)
    """

    def __init__(self):
        self.id_index: HashTable = HashTable(initial_capacity=32)
        self.hash_index: HashTable = HashTable(initial_capacity=32)
        self.path_index: HashTable = HashTable(initial_capacity=32)

    def index_file(self, file_metadata: Dict[str, Any]) -> None:
        """
        Indexes a file across ID, Hash, and Path indices.
        """
        file_id = str(file_metadata.get("file_id") or file_metadata.get("id"))
        sha256 = file_metadata.get("hash")
        rel_path = file_metadata.get("relative_path", "")

        # 1. Primary index
        self.id_index.put(file_id, file_metadata)

        # 2. Path index
        if rel_path:
            self.path_index.put(rel_path, file_id)

        # 3. Duplicate content index
        if sha256:
            existing_ids = self.hash_index.get(sha256, [])
            if file_id not in existing_ids:
                updated_ids = list(existing_ids) + [file_id]
                self.hash_index.put(sha256, updated_ids)

    def remove_file(self, file_id: str) -> None:
        """Removes a file from all indices."""
        meta = self.id_index.get(file_id)
        if meta:
            self.id_index.delete(file_id)
            rel_path = meta.get("relative_path")
            if rel_path:
                self.path_index.delete(rel_path)
            sha256 = meta.get("hash")
            if sha256:
                existing_ids = self.hash_index.get(sha256, [])
                updated_ids = [fid for fid in existing_ids if fid != file_id]
                if updated_ids:
                    self.hash_index.put(sha256, updated_ids)
                else:
                    self.hash_index.delete(sha256)

    def get_by_id(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Average O(1) file metadata lookup."""
        return self.id_index.get(file_id)

    def get_by_path(self, relative_path: str) -> Optional[Dict[str, Any]]:
        """Average O(1) path lookup."""
        file_id = self.path_index.get(relative_path)
        if file_id:
            return self.id_index.get(file_id)
        return None

    def find_duplicates(self) -> List[Dict[str, Any]]:
        """
        Finds all files sharing identical SHA-256 hashes.
        Average O(U) where U is number of unique hashes.
        """
        duplicates = []
        for sha256, file_ids in self.hash_index.items():
            if len(file_ids) > 1:
                files = [self.id_index.get(fid) for fid in file_ids if self.id_index.get(fid)]
                if len(files) > 1:
                    duplicates.append({
                        "hash": sha256,
                        "count": len(files),
                        "files": files,
                        "wasted_size": sum(f.get("size", 0) for f in files[1:])
                    })
        return duplicates

    def get_stats(self) -> Dict[str, Any]:
        """Returns statistics for all 3 underlying hash tables."""
        return {
            "id_index": self.id_index.get_stats(),
            "hash_index": self.hash_index.get_stats(),
            "path_index": self.path_index.get_stats(),
            "total_indexed_files": self.id_index.size,
            "unique_content_hashes": self.hash_index.size
        }
