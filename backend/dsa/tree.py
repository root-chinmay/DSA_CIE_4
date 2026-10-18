"""
backend/dsa/tree.py
Hierarchical Directory Tree Data Structure.

Time Complexity:
- Insert path (length k segments): O(k)
- Find node by path: O(k)
- Delete node by path: O(k)
- Subtree size calculation: O(N) where N is number of descendant nodes
- DFS Traversal: O(N)
- BFS Traversal: O(N)
Space Complexity: O(N) for storing the directory hierarchy.
"""

from typing import Dict, List, Optional, Tuple, Any, Generator
from collections import deque
import os
import time


class FileNode:
    """Represents a file or directory node in the FileTree."""

    def __init__(
        self,
        name: str,
        relative_path: str,
        is_dir: bool = False,
        size: int = 0,
        hash_val: Optional[str] = None,
        modified_time: float = 0.0,
        file_type: str = "folder",
        full_path: str = ""
    ):
        self.name: str = name
        self.relative_path: str = relative_path.replace("\\", "/").strip("/")
        self.is_dir: bool = is_dir
        self.size: int = size
        self.hash_val: Optional[str] = hash_val
        self.modified_time: float = modified_time or time.time()
        self.file_type: str = file_type if not is_dir else "folder"
        self.full_path: str = full_path
        self.parent: Optional['FileNode'] = None
        self.children: Dict[str, 'FileNode'] = {}

    def add_child(self, child: 'FileNode') -> None:
        """Adds a child node and links parent pointer."""
        child.parent = self
        self.children[child.name] = child

    def remove_child(self, name: str) -> Optional['FileNode']:
        """Removes a child node by name and unlinks parent pointer."""
        if name in self.children:
            child = self.children.pop(name)
            child.parent = None
            return child
        return None

    def get_child(self, name: str) -> Optional['FileNode']:
        """Retrieves child node by name in O(1) time."""
        return self.children.get(name)

    def calculate_subtree_size(self) -> int:
        """
        Recursively calculates the aggregate size of this node and all descendants.
        Time Complexity: O(descendants)
        """
        if not self.is_dir:
            return self.size
        total = sum(child.calculate_subtree_size() for child in self.children.values())
        self.size = total
        return total

    def count_elements(self) -> Tuple[int, int]:
        """
        Returns (file_count, folder_count) in the subtree rooted at this node.
        """
        files = 0
        folders = 0
        for child in self.children.values():
            if child.is_dir:
                folders += 1
                f_sub, d_sub = child.count_elements()
                files += f_sub
                folders += d_sub
            else:
                files += 1
        return files, folders

    def to_dict(self, max_depth: Optional[int] = None, current_depth: int = 0) -> Dict[str, Any]:
        """
        Serializes node to a clean JSON-friendly dictionary suitable for
        frontend tree visualizers and explorer tree rendering.
        """
        node_dict = {
            "name": self.name,
            "relative_path": self.relative_path,
            "is_dir": self.is_dir,
            "size": self.size,
            "hash": self.hash_val,
            "modified_time": self.modified_time,
            "file_type": self.file_type,
            "full_path": self.full_path,
            "children_count": len(self.children)
        }
        if self.is_dir:
            if max_depth is None or current_depth < max_depth:
                node_dict["children"] = [
                    child.to_dict(max_depth, current_depth + 1)
                    for child in sorted(self.children.values(), key=lambda c: (not c.is_dir, c.name.lower()))
                ]
            else:
                node_dict["children"] = []
        return node_dict


class FileTree:
    """
    Logical File Tree representing a shared folder structure.
    Separates logical hierarchy from raw OS filesystem calls.
    """

    def __init__(self, root_name: str = "root", root_full_path: str = ""):
        self.root: FileNode = FileNode(
            name=root_name,
            relative_path="",
            is_dir=True,
            full_path=root_full_path
        )

    def insert(
        self,
        relative_path: str,
        is_dir: bool = False,
        size: int = 0,
        hash_val: Optional[str] = None,
        modified_time: float = 0.0,
        full_path: str = ""
    ) -> FileNode:
        """
        Inserts a file or folder into the tree given its relative path.
        Creates intermediate directory nodes if they do not exist.
        Time Complexity: O(k) where k is the number of path segments.
        """
        clean_path = relative_path.replace("\\", "/").strip("/")
        if not clean_path:
            return self.root

        segments = clean_path.split("/")
        current = self.root
        accumulated_path = ""

        for i, segment in enumerate(segments):
            accumulated_path = f"{accumulated_path}/{segment}".strip("/")
            is_last = (i == len(segments) - 1)

            if segment not in current.children:
                if is_last:
                    ext = os.path.splitext(segment)[1].lower().lstrip(".") if not is_dir else "folder"
                    node = FileNode(
                        name=segment,
                        relative_path=accumulated_path,
                        is_dir=is_dir,
                        size=size if not is_dir else 0,
                        hash_val=hash_val,
                        modified_time=modified_time,
                        file_type=ext or "file",
                        full_path=full_path if is_last else ""
                    )
                else:
                    node = FileNode(
                        name=segment,
                        relative_path=accumulated_path,
                        is_dir=True,
                        file_type="folder"
                    )
                current.add_child(node)
                current = node
            else:
                current = current.children[segment]
                if is_last:
                    # Update metadata if existing node re-inserted
                    current.size = size
                    current.hash_val = hash_val
                    current.modified_time = modified_time
                    if full_path:
                        current.full_path = full_path

        # Recalculate root sizes
        self.root.calculate_subtree_size()
        return current

    def find(self, relative_path: str) -> Optional[FileNode]:
        """
        Searches for a node by relative path.
        Time Complexity: O(k) where k is the depth / number of segments.
        """
        clean_path = relative_path.replace("\\", "/").strip("/")
        if not clean_path:
            return self.root

        segments = clean_path.split("/")
        current = self.root
        for segment in segments:
            current = current.get_child(segment)
            if not current:
                return None
        return current

    def delete(self, relative_path: str) -> bool:
        """
        Deletes a node from the tree.
        Time Complexity: O(k)
        """
        clean_path = relative_path.replace("\\", "/").strip("/")
        if not clean_path:
            return False

        segments = clean_path.split("/")
        target_name = segments[-1]
        parent_path = "/".join(segments[:-1])

        parent_node = self.find(parent_path)
        if parent_node and target_name in parent_node.children:
            parent_node.remove_child(target_name)
            self.root.calculate_subtree_size()
            return True
        return False

    def dfs(self, start_node: Optional[FileNode] = None) -> Generator[FileNode, None, None]:
        """
        Depth-First Search (pre-order) traversal of the tree.
        Time Complexity: O(N)
        Space Complexity: O(H) call stack where H is tree height.
        """
        start = start_node or self.root
        yield start
        for child in start.children.values():
            yield from self.dfs(child)

    def bfs(self, start_node: Optional[FileNode] = None) -> Generator[Tuple[int, FileNode], None, None]:
        """
        Breadth-First Search (level-order) traversal of the tree.
        Yields (level, node).
        Time Complexity: O(N)
        Space Complexity: O(W) where W is max tree width.
        """
        start = start_node or self.root
        queue: deque = deque([(0, start)])
        while queue:
            level, current = queue.popleft()
            yield level, current
            for child in current.children.values():
                queue.append((level + 1, child))

    def search_by_name(self, substring: str) -> List[FileNode]:
        """
        Searches for all nodes whose name contains the query substring.
        Time Complexity: O(N)
        """
        query = substring.lower()
        results = []
        for node in self.dfs():
            if node != self.root and query in node.name.lower():
                results.append(node)
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Returns overall tree statistics."""
        self.root.calculate_subtree_size()
        file_count, folder_count = self.root.count_elements()

        # Compute max depth using BFS
        max_depth = 0
        for level, _ in self.bfs():
            if level > max_depth:
                max_depth = level

        return {
            "root_name": self.root.name,
            "total_files": file_count,
            "total_folders": folder_count,
            "total_size": self.root.size,
            "max_depth": max_depth
        }

    def to_dict(self, max_depth: Optional[int] = None) -> Dict[str, Any]:
        """Serializes the entire tree to JSON structure."""
        self.root.calculate_subtree_size()
        return self.root.to_dict(max_depth=max_depth)
