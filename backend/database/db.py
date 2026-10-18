"""
backend/database/db.py
SQLite Database Manager for persistent application state.
Thread-safe access with automatic connection pooling / context managers.
"""

import sqlite3
import os
import threading
from typing import List, Dict, Any, Optional

DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
DB_PATH = os.path.join(DB_DIR, "offline_sharing.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


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
        with self.get_connection() as conn:
            with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                conn.executescript(f.read())
            conn.commit()

    def get_connection(self) -> sqlite3.Connection:
        """Returns thread-local database connection with row factory."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
            # Enable WAL mode for high concurrency
            self._local.conn.execute("PRAGMA journal_mode=WAL;")
            self._local.conn.execute("PRAGMA foreign_keys=ON;")
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
