"""
backend/core/config.py
System configuration, persistence of local device identity, and LAN runtime settings.
"""

import os
import uuid
import socket
import random
from typing import Dict, Any
from backend.database.db import get_db


class AppConfig:
    """Singleton application configuration."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppConfig, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        db = get_db()

        # Device ID
        stored_device_id = db.get_setting("device_id")
        if not stored_device_id:
            stored_device_id = f"dev_{uuid.uuid4().hex[:8]}"
            db.set_setting("device_id", stored_device_id)
        self.device_id: str = stored_device_id

        # Device Name
        stored_name = db.get_setting("device_name")
        if not stored_name:
            try:
                hostname = socket.gethostname()
            except Exception:
                hostname = "Laptop"
            stored_name = f"{hostname}"
            db.set_setting("device_name", stored_name)
        self.device_name: str = stored_name

        # Server Port
        stored_port = db.get_setting("port")
        self.port: int = int(stored_port) if stored_port else 8000

        # Pairing Code (6-digit random code)
        stored_code = db.get_setting("pairing_code")
        if not stored_code:
            stored_code = f"{random.randint(100000, 999999)}"
            db.set_setting("pairing_code", stored_code)
        self.pairing_code: str = stored_code

        # Chunk Size (default 2 MB)
        stored_chunk = db.get_setting("chunk_size_mb")
        self.chunk_size: int = int(stored_chunk or 2) * 1024 * 1024

        # Max Concurrent Transfers
        stored_concurrency = db.get_setting("max_transfers")
        self.max_concurrent_transfers: int = int(stored_concurrency or 3)

        # Demo mode toggle
        self.demo_mode: bool = (db.get_setting("demo_mode", "false").lower() == "true")

        # Base directories
        self.workspace_root: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.data_dir: str = os.path.join(self.workspace_root, "data")
        self.default_shared_dir: str = os.path.join(self.data_dir, "shared_files")
        self.downloads_dir: str = os.path.join(self.data_dir, "downloads")

        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.default_shared_dir, exist_ok=True)
        os.makedirs(self.downloads_dir, exist_ok=True)

    def refresh(self) -> None:
        """Reload configuration from database."""
        self._load_config()

    def update(self, **kwargs) -> None:
        """Updates and persists configuration values."""
        db = get_db()
        for key, val in kwargs.items():
            db.set_setting(key, str(val))
            if hasattr(self, key):
                setattr(self, key, val)
        self.refresh()

    def regenerate_pairing_code(self) -> str:
        """Generates a fresh 6-digit numeric pairing code."""
        new_code = f"{random.randint(100000, 999999)}"
        self.update(pairing_code=new_code)
        return new_code

    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "device_name": self.device_name,
            "port": self.port,
            "pairing_code": self.pairing_code,
            "chunk_size_mb": self.chunk_size // (1024 * 1024),
            "max_concurrent_transfers": self.max_concurrent_transfers,
            "demo_mode": self.demo_mode,
            "default_shared_dir": self.default_shared_dir,
            "downloads_dir": self.downloads_dir
        }


def get_config() -> AppConfig:
    return AppConfig()
