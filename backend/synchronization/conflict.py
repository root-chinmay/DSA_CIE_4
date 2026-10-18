"""
backend/synchronization/conflict.py
Conflict Resolution Manager.
Guarantees user files are never silently overwritten during concurrent edits.
Supports Keep Local, Keep Remote, and Keep Both (renaming both versions).
"""

import os
import shutil
import time
from typing import Dict, Any, List, Optional
from backend.database.db import get_db
from backend.file_manager.storage import StorageManager
from backend.core.logger import AppLogger
from backend.core.event_bus import get_event_bus


class ConflictManager:
    """Manages detection, listing, and resolution of synchronization conflicts."""

    @staticmethod
    def list_conflicts(status: str = "PENDING") -> List[Dict[str, Any]]:
        db = get_db()
        return db.execute_query(
            "SELECT * FROM sync_conflicts WHERE status = ? ORDER BY id DESC",
            (status,)
        )

    @classmethod
    def resolve_conflict(
        cls,
        conflict_id: int,
        resolution: str,
        remote_data_bytes: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """
        Resolves a conflict with explicit user choice:
        - 'KEEP_LOCAL': Retain local version; remote copy will be overwritten.
        - 'KEEP_REMOTE': Overwrite local version with remote content.
        - 'KEEP_BOTH': Keep local version as 'filename_local.ext' and remote as 'filename_remote.ext'.
        """
        db = get_db()
        conflict = db.execute_query_one("SELECT * FROM sync_conflicts WHERE id = ?", (conflict_id,))
        if not conflict:
            return {"success": False, "error": "Conflict not found."}

        rel_path = conflict["file_path"]
        try:
            abs_local_path, _ = StorageManager.validate_and_resolve_path(rel_path)
        except Exception as e:
            return {"success": False, "error": str(e)}

        res_upper = resolution.upper()

        if res_upper == "KEEP_LOCAL":
            # Local remains as-is
            pass

        elif res_upper == "KEEP_REMOTE":
            if remote_data_bytes is not None:
                with open(abs_local_path, "wb") as f:
                    f.write(remote_data_bytes)

        elif res_upper == "KEEP_BOTH":
            dirname = os.path.dirname(abs_local_path)
            basename = os.path.basename(abs_local_path)
            name, ext = os.path.splitext(basename)

            local_renamed = os.path.join(dirname, f"{name}_local{ext}")
            remote_renamed = os.path.join(dirname, f"{name}_remote{ext}")

            # 1. Rename existing local file to _local
            if os.path.exists(abs_local_path):
                shutil.move(abs_local_path, local_renamed)

            # 2. Save remote version as _remote
            if remote_data_bytes is not None:
                with open(remote_renamed, "wb") as f:
                    f.write(remote_data_bytes)

        else:
            return {"success": False, "error": f"Unsupported resolution: {resolution}"}

        # Mark conflict resolved in DB
        db.execute_write(
            """
            UPDATE sync_conflicts
            SET status = 'RESOLVED', resolution = ?
            WHERE id = ?
            """,
            (res_upper, conflict_id)
        )

        AppLogger.log("CONFLICT_RESOLVED", status="INFO", file_name=rel_path, message=f"Resolved with {res_upper}")
        try:
            get_event_bus().publish_sync("CONFLICT_RESOLVED", {
                "conflict_id": conflict_id,
                "file_path": rel_path,
                "resolution": res_upper
            })
        except Exception:
            pass

        return {"success": True, "resolution": res_upper, "file_path": rel_path}
