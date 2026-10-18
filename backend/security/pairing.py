"""
backend/security/pairing.py
LAN Device Pairing & Authentication Manager.
Uses 6-digit numeric pairing codes to authorize peer connections on the local network.
"""

from typing import Dict, Any, Optional
from backend.core.config import get_config
from backend.database.db import get_db
from backend.core.logger import AppLogger
from backend.core.event_bus import get_event_bus


class PairingManager:
    """Manages secure peer pairing and trusted device state."""

    @classmethod
    def get_pairing_code(cls) -> str:
        """Returns the active 6-digit pairing code for this device."""
        config = get_config()
        return config.pairing_code

    @classmethod
    def regenerate_code(cls) -> str:
        """Regenerates a fresh random 6-digit pairing code."""
        config = get_config()
        new_code = config.regenerate_pairing_code()
        AppLogger.log("PAIRING_CODE_RESET", status="INFO", message=f"New pairing code generated: {new_code}")
        return new_code

    @classmethod
    def verify_pairing(
        cls,
        remote_device_id: str,
        submitted_code: str,
        role: str = "CONTRIBUTOR"
    ) -> Dict[str, Any]:
        """
        Validates the submitted pairing code against this host's code.
        If valid, upgrades remote device to trusted in SQLite.
        """
        config = get_config()
        if submitted_code.strip() != config.pairing_code.strip():
            AppLogger.log("PAIRING_FAILED", status="WARN", device=remote_device_id, message="Invalid pairing code provided.")
            return {
                "success": False,
                "error": "Invalid pairing code. Please verify the 6-digit code shown on the host laptop."
            }

        db = get_db()
        db.execute_write(
            """
            UPDATE devices SET trusted = 1, role = ? WHERE device_id = ?
            """,
            (role, remote_device_id)
        )

        AppLogger.log("PAIRING_SUCCESS", status="INFO", device=remote_device_id, message=f"Device paired successfully with role {role}.")
        try:
            get_event_bus().publish_sync("DEVICE_PAIRED", {
                "device_id": remote_device_id,
                "role": role
            })
        except Exception:
            pass

        return {
            "success": True,
            "message": "Paired successfully. Connection authorized.",
            "role": role,
            "host_device_id": config.device_id,
            "host_name": config.device_name
        }

    @classmethod
    def is_trusted(cls, device_id: str) -> bool:
        """Checks if a device is trusted."""
        config = get_config()
        if device_id == config.device_id:
            return True

        db = get_db()
        dev = db.execute_query_one("SELECT trusted FROM devices WHERE device_id = ?", (device_id,))
        return bool(dev and dev["trusted"] == 1)
