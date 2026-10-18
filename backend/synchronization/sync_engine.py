"""
backend/synchronization/sync_engine.py
Intelligent Tree-Based File Synchronization Engine.
Compares relative path, size, modification timestamp, and SHA-256 cryptographic hashes.
Eliminates redundant file transfers if hashes are identical (SYNCED).
"""

from typing import Dict, List, Any, Optional
import time
from backend.database.db import get_db
from backend.file_manager.scanner import get_scanner
from backend.core.logger import AppLogger
from backend.core.event_bus import get_event_bus


class SyncState:
    SYNCED = "SYNCED"
    NEW_LOCAL = "NEW_LOCAL"
    NEW_REMOTE = "NEW_REMOTE"
    MODIFIED_LOCAL = "MODIFIED_LOCAL"
    MODIFIED_REMOTE = "MODIFIED_REMOTE"
    CONFLICT = "CONFLICT"
    DUPLICATE = "DUPLICATE"


class SynchronizationEngine:
    """
    Diffs local FileTree/index against remote FileTree/index.
    Generates actionable diff matrix and sync transfer plan.
    """

    @classmethod
    def compare_trees(
        cls,
        local_files: List[Dict[str, Any]],
        remote_files: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Compares local and remote file listings.
        Time Complexity: O(N + M) using dictionary/hash table lookup.
        """
        local_map: Dict[str, Dict[str, Any]] = {
            f.get("relative_path", "").replace("\\", "/").strip("/"): f
            for f in local_files
        }
        remote_map: Dict[str, Dict[str, Any]] = {
            f.get("relative_path", "").replace("\\", "/").strip("/"): f
            for f in remote_files
        }

        all_paths = set(local_map.keys()).union(set(remote_map.keys()))
        diff_matrix: List[Dict[str, Any]] = []

        for path in sorted(all_paths):
            loc = local_map.get(path)
            rem = remote_map.get(path)

            if loc and not rem:
                diff_matrix.append({
                    "relative_path": path,
                    "file_name": loc.get("file_name") or loc.get("name"),
                    "state": SyncState.NEW_LOCAL,
                    "local_hash": loc.get("hash"),
                    "remote_hash": None,
                    "local_size": loc.get("size", 0),
                    "remote_size": None,
                    "local_mtime": loc.get("modified_time"),
                    "remote_mtime": None,
                    "action": "UPLOAD_TO_REMOTE"
                })
            elif rem and not loc:
                diff_matrix.append({
                    "relative_path": path,
                    "file_name": rem.get("file_name") or rem.get("name"),
                    "state": SyncState.NEW_REMOTE,
                    "local_hash": None,
                    "remote_hash": rem.get("hash"),
                    "local_size": None,
                    "remote_size": rem.get("size", 0),
                    "local_mtime": None,
                    "remote_mtime": rem.get("modified_time"),
                    "action": "DOWNLOAD_TO_LOCAL"
                })
            else:
                # Both exist: compare cryptographic hash
                loc_hash = (loc.get("hash") or "").lower()
                rem_hash = (rem.get("hash") or "").lower()

                if loc_hash == rem_hash and loc_hash != "":
                    # Identical content -> No transfer needed!
                    diff_matrix.append({
                        "relative_path": path,
                        "file_name": loc.get("file_name") or loc.get("name"),
                        "state": SyncState.SYNCED,
                        "local_hash": loc_hash,
                        "remote_hash": rem_hash,
                        "local_size": loc.get("size", 0),
                        "remote_size": rem.get("size", 0),
                        "local_mtime": loc.get("modified_time"),
                        "remote_mtime": rem.get("modified_time"),
                        "action": "NONE"
                    })
                else:
                    # Differing hashes -> Check timestamps
                    loc_mtime = loc.get("modified_time", 0.0)
                    rem_mtime = rem.get("modified_time", 0.0)
                    time_diff = abs(loc_mtime - rem_mtime)

                    # If timestamps are very close or both changed after baseline -> Conflict!
                    # For peer sync: if local is significantly newer -> MODIFIED_LOCAL
                    # If remote is significantly newer -> MODIFIED_REMOTE
                    # If both changed within a conflict window -> CONFLICT
                    if time_diff < 1.0 or (loc.get("size") != rem.get("size") and time_diff < 5.0):
                        state = SyncState.CONFLICT
                        action = "RESOLVE_CONFLICT"
                        cls._record_conflict(path, loc_hash, rem_hash, loc_mtime, rem_mtime)
                    elif loc_mtime > rem_mtime:
                        state = SyncState.MODIFIED_LOCAL
                        action = "UPLOAD_TO_REMOTE"
                    else:
                        state = SyncState.MODIFIED_REMOTE
                        action = "DOWNLOAD_TO_LOCAL"

                    diff_matrix.append({
                        "relative_path": path,
                        "file_name": loc.get("file_name") or loc.get("name"),
                        "state": state,
                        "local_hash": loc_hash,
                        "remote_hash": rem_hash,
                        "local_size": loc.get("size", 0),
                        "remote_size": rem.get("size", 0),
                        "local_mtime": loc_mtime,
                        "remote_mtime": rem_mtime,
                        "action": action
                    })

        return diff_matrix

    @classmethod
    def _record_conflict(
        cls,
        file_path: str,
        loc_hash: str,
        rem_hash: str,
        loc_mtime: float,
        rem_mtime: float
    ) -> None:
        db = get_db()
        existing = db.execute_query_one(
            "SELECT * FROM sync_conflicts WHERE file_path = ? AND status = 'PENDING'",
            (file_path,)
        )
        if not existing:
            db.execute_write(
                """
                INSERT INTO sync_conflicts (file_path, local_hash, remote_hash, local_modified, remote_modified, status, created_at)
                VALUES (?, ?, ?, ?, ?, 'PENDING', ?)
                """,
                (file_path, loc_hash, rem_hash, loc_mtime, rem_mtime, time.time())
            )
            AppLogger.log("CONFLICT_DETECTED", status="WARN", file_name=file_path, message="Concurrent edit conflict detected.")
            try:
                get_event_bus().publish_sync("CONFLICT_DETECTED", {"file_path": file_path})
            except Exception:
                pass
