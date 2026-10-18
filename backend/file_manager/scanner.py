"""
backend/file_manager/scanner.py
Directory Scanner integrating FileTree, FileHashIndex, and FilenameTrie.
Synchronizes physical filesystem hierarchy with logical DSA data structures and SQLite.
"""

import os
import uuid
import time
from typing import Dict, List, Any, Optional
from backend.dsa.tree import FileTree
from backend.dsa.hash_table import FileHashIndex
from backend.dsa.trie import FilenameTrie
from backend.database.db import get_db
from backend.file_manager.hasher import StreamingHasher
from backend.file_manager.storage import StorageManager
from backend.core.logger import AppLogger
from backend.core.event_bus import get_event_bus


class DirectoryScanner:
    """
    Central file manager linking physical files to DSA memory structures.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DirectoryScanner, cls).__new__(cls)
            cls._instance._init_structures()
        return cls._instance

    def _init_structures(self) -> None:
        self.tree: FileTree = FileTree(root_name="SharedRoot")
        self.hash_index: FileHashIndex = FileHashIndex()
        self.trie: FilenameTrie = FilenameTrie()
        self.last_scan_time: float = 0.0

    def scan_all(self, force_rehash: bool = False) -> Dict[str, Any]:
        """
        Scans all enabled shared folders and re-builds DSA structures.
        Time Complexity: O(N) where N is number of files.
        """
        db = get_db()
        folders = StorageManager.get_shared_folders()

        # Reset memory structures
        self.tree = FileTree(root_name="SharedRoot")
        self.hash_index = FileHashIndex()
        self.trie = FilenameTrie()

        current_file_ids = set()
        files_scanned = 0

        for folder in folders:
            folder_id = folder["id"]
            folder_path = folder["folder_path"]
            folder_name = folder["folder_name"]

            if not os.path.exists(folder_path):
                continue

            for root, dirs, files in os.walk(folder_path):
                # Calculate relative path from shared root
                rel_dir = os.path.relpath(root, folder_path).replace("\\", "/")
                if rel_dir == ".":
                    rel_dir = ""

                # Insert directory into tree
                if rel_dir:
                    self.tree.insert(
                        relative_path=rel_dir,
                        is_dir=True,
                        full_path=root
                    )

                for fname in files:
                    file_full_path = os.path.join(root, fname)
                    rel_file_path = os.path.join(rel_dir, fname).replace("\\", "/").lstrip("/")

                    try:
                        stat = os.stat(file_full_path)
                        size = stat.st_size
                        mtime = stat.st_mtime
                    except OSError:
                        continue

                    # Check if already in DB with same mtime and size to avoid redundant hashing
                    existing_db = db.execute_query_one(
                        """
                        SELECT file_id, hash, modified_time, size FROM files
                        WHERE folder_id = ? AND relative_path = ?
                        """,
                        (folder_id, rel_file_path)
                    )

                    file_hash = None
                    file_id = None

                    if existing_db and not force_rehash:
                        if existing_db["size"] == size and abs(existing_db["modified_time"] - mtime) < 0.001:
                            file_hash = existing_db["hash"]
                            file_id = existing_db["file_id"]

                    if not file_hash:
                        file_hash = StreamingHasher.hash_file(file_full_path) or ""
                        if not file_id:
                            file_id = f"file_{uuid.uuid4().hex[:10]}"

                        # Upsert into SQLite
                        db.execute_write(
                            """
                            INSERT INTO files (file_id, folder_id, file_name, relative_path, size, hash, modified_time, file_type)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(file_id) DO UPDATE SET
                                size=excluded.size,
                                hash=excluded.hash,
                                modified_time=excluded.modified_time
                            """,
                            (
                                file_id,
                                folder_id,
                                fname,
                                rel_file_path,
                                size,
                                file_hash,
                                mtime,
                                os.path.splitext(fname)[1].lstrip(".").lower() or "file"
                            )
                        )
                    else:
                        # Existing unchanged file
                        pass

                    current_file_ids.add(file_id)

                    file_metadata = {
                        "file_id": file_id,
                        "folder_id": folder_id,
                        "folder_name": folder_name,
                        "file_name": fname,
                        "name": fname,
                        "relative_path": rel_file_path,
                        "path": rel_file_path,
                        "size": size,
                        "hash": file_hash,
                        "modified_time": mtime,
                        "file_type": os.path.splitext(fname)[1].lstrip(".").lower() or "file",
                        "full_path": file_full_path,
                        "is_dir": False
                    }

                    # 1. Insert into FileTree
                    self.tree.insert(
                        relative_path=rel_file_path,
                        is_dir=False,
                        size=size,
                        hash_val=file_hash,
                        modified_time=mtime,
                        full_path=file_full_path
                    )

                    # 2. Insert into FileHashIndex (O(1) lookup & duplicate clustering)
                    self.hash_index.index_file(file_metadata)

                    # 3. Insert into FilenameTrie (O(L) prefix search & autocomplete)
                    self.trie.insert(fname, file_metadata)

                    files_scanned += 1

        # Clean up files deleted from disk
        if current_file_ids:
            placeholders = ",".join(["?"] * len(current_file_ids))
            db.execute_write(
                f"DELETE FROM files WHERE file_id NOT IN ({placeholders})",
                tuple(current_file_ids)
            )
        elif folders:
            db.execute_write("DELETE FROM files")

        self.last_scan_time = time.time()
        stats = self.get_summary()
        AppLogger.log("SCAN_COMPLETED", status="INFO", message=f"Indexed {files_scanned} files across {len(folders)} shared folders.")

        # Notify event bus
        try:
            get_event_bus().publish_sync("FILES_UPDATED", stats)
        except Exception:
            pass

        return stats

    def get_summary(self) -> Dict[str, Any]:
        """Returns aggregated summary from DSA structures."""
        tree_stats = self.tree.get_stats()
        hash_stats = self.hash_index.get_stats()
        trie_stats = self.trie.get_stats()
        duplicates = self.hash_index.find_duplicates()

        return {
            "total_files": tree_stats["total_files"],
            "total_folders": tree_stats["total_folders"],
            "total_size": tree_stats["total_size"],
            "max_tree_depth": tree_stats["max_depth"],
            "unique_hashes": hash_stats["unique_content_hashes"],
            "duplicate_groups_count": len(duplicates),
            "duplicate_files_count": sum(d["count"] for d in duplicates),
            "wasted_duplicate_bytes": sum(d["wasted_size"] for d in duplicates),
            "trie_tokens": trie_stats["total_words"],
            "last_scan_time": self.last_scan_time
        }

    def get_all_files(self) -> List[Dict[str, Any]]:
        """Returns all indexed files from Hash Table primary index."""
        return self.hash_index.id_index.values()

    def get_file_by_id(self, file_id: str) -> Optional[Dict[str, Any]]:
        return self.hash_index.get_by_id(file_id)

    def get_file_by_path(self, relative_path: str) -> Optional[Dict[str, Any]]:
        return self.hash_index.get_by_path(relative_path)


def get_scanner() -> DirectoryScanner:
    return DirectoryScanner()
