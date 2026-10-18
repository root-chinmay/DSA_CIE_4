"""
backend/database/db.py
SQLite Database Manager for persistent application state.
Thread-safe access with automatic connection pooling / context managers.
"""

import sqlite3
import os
import tempfile
import threading
from typing import List, Dict, Any, Optional

if os.environ.get("VERCEL"):
    DB_DIR = os.path.join(tempfile.gettempdir(), "data")
else:
    DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
DB_PATH = os.path.join(DB_DIR, "offline_sharing.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

DEFAULT_SCHEMA = """-- SQLite Database Schema for Offline LAN File Sharing & Synchronization

CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT UNIQUE NOT NULL,
    device_name TEXT NOT NULL,
    ip_address TEXT NOT NULL,
    port INTEGER DEFAULT 8000,
    status TEXT DEFAULT 'online', -- 'online', 'offline', 'unpaired'
    last_seen REAL NOT NULL,
    trusted INTEGER DEFAULT 0,    -- 0 = unverified, 1 = paired/trusted
    role TEXT DEFAULT 'READ_ONLY', -- 'READ_ONLY', 'DOWNLOADER', 'CONTRIBUTOR', 'FULL_ACCESS'
    pairing_code TEXT,
    created_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS shared_folders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_name TEXT NOT NULL,
    folder_path TEXT UNIQUE NOT NULL,
    enabled INTEGER DEFAULT 1,
    created_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id TEXT UNIQUE NOT NULL,
    folder_id INTEGER NOT NULL,
    file_name TEXT NOT NULL,
    relative_path TEXT NOT NULL,
    size INTEGER DEFAULT 0,
    hash TEXT,
    modified_time REAL NOT NULL,
    file_type TEXT,
    FOREIGN KEY(folder_id) REFERENCES shared_folders(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS transfers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transfer_id TEXT UNIQUE NOT NULL,
    file_id TEXT,
    file_name TEXT NOT NULL,
    source_device TEXT NOT NULL,
    destination_device TEXT NOT NULL,
    direction TEXT NOT NULL, -- 'UPLOAD' or 'DOWNLOAD'
    size INTEGER DEFAULT 0,
    transferred_bytes INTEGER DEFAULT 0,
    status TEXT DEFAULT 'WAITING', -- 'WAITING', 'TRANSFERRING', 'COMPLETED', 'FAILED', 'CANCELLED'
    priority INTEGER DEFAULT 2,     -- 0=Critical, 1=High, 2=Normal, 3=Low
    started_at REAL,
    completed_at REAL,
    speed REAL DEFAULT 0.0,
    hash_verified INTEGER DEFAULT 0,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS sync_conflicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    local_hash TEXT,
    remote_hash TEXT,
    local_modified REAL,
    remote_modified REAL,
    status TEXT DEFAULT 'PENDING', -- 'PENDING', 'RESOLVED'
    resolution TEXT,              -- 'KEEP_LOCAL', 'KEEP_REMOTE', 'KEEP_BOTH'
    created_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    device TEXT,
    operation TEXT NOT NULL,
    file_name TEXT,
    status TEXT NOT NULL,
    message TEXT
);

CREATE INDEX IF NOT EXISTS idx_files_hash ON files(hash);
CREATE INDEX IF NOT EXISTS idx_files_folder ON files(folder_id);
CREATE INDEX IF NOT EXISTS idx_transfers_status ON transfers(status);
CREATE INDEX IF NOT EXISTS idx_devices_status ON devices(status);
"""


class DatabaseManager:
    """Singleton-style thread-safe SQLite database manager."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, db_path: str = DB_PATH):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabaseManager, cls).__new__(cls)
                cls._instance._init_db(db_path)
            return cls._instance

    def _init_db(self, db_path: str) -> None:
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._local = threading.local()

        # Run schema script
        schema_sql = ""
        if os.path.exists(SCHEMA_PATH):
            try:
                with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                    schema_sql = f.read()
            except Exception:
                schema_sql = ""
        if not schema_sql:
            schema_sql = DEFAULT_SCHEMA

        with self.get_connection() as conn:
            conn.executescript(schema_sql)
            conn.commit()

    def get_connection(self) -> sqlite3.Connection:
        """Returns thread-local database connection with row factory."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
            # Enable WAL mode for high concurrency
            try:
                self._local.conn.execute("PRAGMA journal_mode=WAL;")
            except Exception:
                pass
            try:
                self._local.conn.execute("PRAGMA foreign_keys=ON;")
            except Exception:
                pass
        return self._local.conn

    def execute_write(self, query: str, params: tuple = ()) -> int:
        """Executes INSERT/UPDATE/DELETE and returns lastrowid."""
        with self._lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Executes SELECT query and returns list of dictionaries."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def execute_query_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Executes SELECT query and returns a single dictionary or None."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None

    # Settings helpers
    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        res = self.execute_query_one("SELECT value FROM settings WHERE key = ?", (key,))
        return res["value"] if res else default

    def set_setting(self, key: str, value: str) -> None:
        self.execute_write(
            "INSERT INTO settings(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, str(value))
        )


def get_db() -> DatabaseManager:
    """Helper to retrieve DatabaseManager instance."""
    return DatabaseManager()
