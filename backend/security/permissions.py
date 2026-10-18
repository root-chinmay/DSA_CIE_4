"""
backend/security/permissions.py
Role-Based Authorization & Permission Tiers for LAN clients.
"""

from enum import Enum
from typing import Set, Dict, Optional
from backend.database.db import get_db
from backend.core.config import get_config


class Action(str, Enum):
    READ = "READ"          # Browse tree, search files, view metadata
    DOWNLOAD = "DOWNLOAD"  # Download file chunks
    UPLOAD = "UPLOAD"      # Upload new files
    DELETE = "DELETE"      # Delete files or folders
    ADMIN = "ADMIN"        # Settings, pairing code reset


ROLE_PERMISSIONS: Dict[str, Set[Action]] = {
    "READ_ONLY": {Action.READ},
    "DOWNLOADER": {Action.READ, Action.DOWNLOAD},
    "CONTRIBUTOR": {Action.READ, Action.DOWNLOAD, Action.UPLOAD},
    "FULL_ACCESS": {Action.READ, Action.DOWNLOAD, Action.UPLOAD, Action.DELETE},
    "HOST": {Action.READ, Action.DOWNLOAD, Action.UPLOAD, Action.DELETE, Action.ADMIN}
}


class PermissionManager:
    """Checks device authorization for specific file operations."""

    @classmethod
    def get_device_role(cls, device_id: str) -> str:
        config = get_config()
        if device_id == config.device_id or device_id == "local":
            return "HOST"

        db = get_db()
        dev = db.execute_query_one("SELECT role, trusted FROM devices WHERE device_id = ?", (device_id,))
        if not dev or dev["trusted"] != 1:
            return "READ_ONLY"  # Default un-paired role is restricted read-only

        return dev.get("role", "READ_ONLY")

    @classmethod
    def can_perform(cls, device_id: str, action: Action) -> bool:
        """Verifies if device is permitted to perform the specified action."""
        role = cls.get_device_role(device_id)
        allowed_actions = ROLE_PERMISSIONS.get(role, set())
        return action in allowed_actions
