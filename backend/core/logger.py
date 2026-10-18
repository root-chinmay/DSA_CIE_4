"""
backend/core/logger.py
Application logger persisting audit trails into SQLite and broadcasting to UI.
"""

import time
import sys
from typing import Optional, Dict, Any, List
from backend.database.db import get_db
from backend.core.event_bus import get_event_bus


class AppLogger:
    """Centralized logger logging to DB, console, and real-time event bus."""

    @staticmethod
    def log(
        operation: str,
        status: str = "INFO",
        file_name: Optional[str] = None,
        device: Optional[str] = None,
        message: Optional[str] = None
    ) -> None:
        timestamp = time.time()
        time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
        status_upper = status.upper()

        # Format console log
        prefix = f"[{time_str}] [{status_upper}]"
        context = f"[{device or 'Local'}]"
        details = f"{operation}"
        if file_name:
            details += f" ({file_name})"
        if message:
            details += f": {message}"

        print(f"{prefix} {context} {details}", flush=True)

        # Insert into SQLite database
        try:
            db = get_db()
            db.execute_write(
                """
                INSERT INTO logs (timestamp, device, operation, file_name, status, message)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (timestamp, device or "Local", operation, file_name, status_upper, message)
            )
        except Exception as e:
            print(f"[Logger Error] DB insert failed: {e}", file=sys.stderr)

        # Broadcast via EventBus
        try:
            event_bus = get_event_bus()
            event_bus.publish_sync("LOG_EVENT", {
                "timestamp": timestamp,
                "time_formatted": time_str,
                "device": device or "Local",
                "operation": operation,
                "file_name": file_name,
                "status": status_upper,
                "message": message
            })
        except Exception:
            pass

    @staticmethod
    def get_recent_logs(limit: int = 100) -> List[Dict[str, Any]]:
        db = get_db()
        return db.execute_query(
            "SELECT * FROM logs ORDER BY id DESC LIMIT ?",
            (limit,)
        )
