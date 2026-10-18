"""
backend/file_manager/storage.py
Secure file storage access layer with strict path traversal prevention.
Ensures that all file operations are strictly confined within explicitly shared directories.
"""

import os
import shutil
from typing import Optional, List, Dict, Any, Tuple
from backend.database.db import get_db
from backend.core.logger import AppLogger


class SecurityError(Exception):
    """Raised when an unauthorized path traversal is detected."""
    pass


class StorageManager:
    """Manages allowed shared directories and enforces strict path boundaries."""

    @staticmethod
    def get_shared_folders() -> List[Dict[str, Any]]:
        """Returns all registered shared folders."""
        db = get_db()
        return db.execute_query("SELECT * FROM shared_folders WHERE enabled = 1")

    @staticmethod
    def add_shared_folder(folder_path: str, folder_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Registers a new folder for sharing.
        Validates that directory exists on local disk.
        """
        abs_path = os.path.abspath(folder_path)
        if not os.path.exists(abs_path):
            os.makedirs(abs_path, exist_ok=True)

        if not os.path.isdir(abs_path):
            raise ValueError(f"Path is not a valid directory: {abs_path}")

        name = folder_name or os.path.basename(abs_path) or "SharedFolder"
        db = get_db()
        existing = db.execute_query_one(
            "SELECT * FROM shared_folders WHERE folder_path = ?",
            (abs_path,)
        )
        if existing:
            # Re-enable if disabled
            db.execute_write(
                "UPDATE shared_folders SET enabled = 1, folder_name = ? WHERE id = ?",
                (name, existing["id"])
            )
            return db.execute_query_one("SELECT * FROM shared_folders WHERE id = ?", (existing["id"],))

        row_id = db.execute_write(
            """
            INSERT INTO shared_folders (folder_name, folder_path, enabled, created_at)
            VALUES (?, ?, 1, ?)
            """,
            (name, abs_path, os.path.getctime(abs_path) if os.path.exists(abs_path) else 0.0)
        )
        AppLogger.log("FOLDER_ADDED", status="INFO", message=f"Added shared folder '{name}' at {abs_path}")
        return db.execute_query_one("SELECT * FROM shared_folders WHERE id = ?", (row_id,))

    @staticmethod
    def remove_shared_folder(folder_id: int) -> bool:
        """Unregisters a shared folder (does not delete files from disk)."""
        db = get_db()
        folder = db.execute_query_one("SELECT * FROM shared_folders WHERE id = ?", (folder_id,))
        if folder:
            db.execute_write("DELETE FROM files WHERE folder_id = ?", (folder_id,))
            db.execute_write("DELETE FROM shared_folders WHERE id = ?", (folder_id,))
            AppLogger.log("FOLDER_REMOVED", status="INFO", message=f"Removed shared folder '{folder['folder_name']}'")
            return True
        return False

    @classmethod
    def validate_and_resolve_path(cls, relative_path: str, folder_id: Optional[int] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Validates that relative_path resolves strictly inside the authorized shared root.
        Prevents ../ directory traversal attacks.
        Returns (resolved_absolute_path, shared_folder_record).
        """
        db = get_db()
        if folder_id is not None:
            folder = db.execute_query_one("SELECT * FROM shared_folders WHERE id = ? AND enabled = 1", (folder_id,))
        else:
            folder = db.execute_query_one("SELECT * FROM shared_folders WHERE enabled = 1 ORDER BY id ASC LIMIT 1")

        if not folder:
            raise FileNotFoundError("No active shared folder found.")

        base_root = os.path.realpath(folder["folder_path"])
        # Clean relative path
        clean_rel = relative_path.replace("\\", "/").lstrip("/")
        candidate_path = os.path.realpath(os.path.join(base_root, clean_rel))

        # Security check: candidate path must start with base_root
        try:
            common = os.path.commonpath([base_root, candidate_path])
        except ValueError:
            raise SecurityError("Cross-drive or invalid path access forbidden.")

        if common != base_root:
            AppLogger.log("SECURITY_VIOLATION", status="ALERT", message=f"Directory traversal rejected: {relative_path}")
            raise SecurityError(f"Access denied: Path escapes shared directory root: {relative_path}")

        return candidate_path, folder

    @classmethod
    def safe_delete(cls, relative_path: str, folder_id: Optional[int] = None) -> bool:
        """Safely deletes a file within the shared folder."""
        abs_path, _ = cls.validate_and_resolve_path(relative_path, folder_id)
        if os.path.exists(abs_path):
            if os.path.isdir(abs_path):
                shutil.rmtree(abs_path)
            else:
                os.remove(abs_path)
            AppLogger.log("FILE_DELETED", status="INFO", file_name=relative_path, message="Deleted successfully")
            return True
        return False

    @classmethod
    def safe_rename(cls, old_relative_path: str, new_name: str, folder_id: Optional[int] = None) -> str:
        """Safely renames a file or subfolder."""
        old_abs, folder = cls.validate_and_resolve_path(old_relative_path, folder_id)
        if not os.path.exists(old_abs):
            raise FileNotFoundError(f"File not found: {old_relative_path}")

        parent_dir = os.path.dirname(old_abs)
        clean_name = os.path.basename(new_name.strip())
        new_abs = os.path.join(parent_dir, clean_name)

        # Validate that target also resolves within root
        base_root = os.path.realpath(folder["folder_path"])
        if os.path.commonpath([base_root, os.path.realpath(new_abs)]) != base_root:
            raise SecurityError("Rename target escapes root directory.")

        os.rename(old_abs, new_abs)
        new_rel = os.path.relpath(new_abs, base_root).replace("\\", "/")
        AppLogger.log("FILE_RENAMED", status="INFO", file_name=old_relative_path, message=f"Renamed to {new_name}")
        return new_rel
