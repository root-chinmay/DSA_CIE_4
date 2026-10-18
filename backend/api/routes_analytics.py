"""
backend/api/routes_analytics.py
API endpoints for system analytics, storage breakdown, and transfer performance metrics.
"""

from fastapi import APIRouter
from typing import Dict, Any
from backend.file_manager.scanner import get_scanner
from backend.database.db import get_db
from backend.networking.discovery import get_discovery

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("")
def get_analytics() -> Dict[str, Any]:
    """
    Computes storage distribution, transfer statistics, duplicate ratio, and network throughput.
    """
    scanner = get_scanner()
    db = get_db()
    discovery = get_discovery()

    files = scanner.get_all_files()
    total_files = len(files)
    total_storage = sum(f.get("size", 0) for f in files)

    # File type breakdown
    type_counts: Dict[str, int] = {}
    type_sizes: Dict[str, int] = {}
    for f in files:
        ftype = f.get("file_type", "other").lower() or "other"
        type_counts[ftype] = type_counts.get(ftype, 0) + 1
        type_sizes[ftype] = type_sizes.get(ftype, 0) + f.get("size", 0)

    # Transfers breakdown
    transfers = db.execute_query("SELECT * FROM transfers")
    completed_tx = [t for t in transfers if t["status"] == "COMPLETED"]
    failed_tx = [t for t in transfers if t["status"] == "FAILED"]
    cancelled_tx = [t for t in transfers if t["status"] == "CANCELLED"]

    total_transferred_bytes = sum(t["transferred_bytes"] for t in completed_tx)
    avg_speed = (sum(t["speed"] for t in completed_tx) / len(completed_tx)) if completed_tx else 0.0

    # Duplicates breakdown
    duplicates = scanner.hash_index.find_duplicates()
    wasted_duplicate_bytes = sum(d["wasted_size"] for d in duplicates)

    # Conflicts
    conflicts = db.execute_query("SELECT * FROM sync_conflicts")
    pending_conflicts = [c for c in conflicts if c["status"] == "PENDING"]

    # Connected devices
    devices = discovery.get_devices()
    online_devices = [d for d in devices if d["status"] == "online"]

    return {
        "overview": {
            "total_files": total_files,
            "total_storage_bytes": total_storage,
            "total_storage_mb": round(total_storage / (1024 * 1024), 2),
            "online_devices_count": len(online_devices),
            "total_devices_count": len(devices),
            "pending_conflicts_count": len(pending_conflicts),
            "duplicate_groups_count": len(duplicates),
            "wasted_duplicate_mb": round(wasted_duplicate_bytes / (1024 * 1024), 2)
        },
        "type_distribution": {
            "counts": type_counts,
            "sizes": type_sizes
        },
        "transfers": {
            "total_count": len(transfers),
            "completed_count": len(completed_tx),
            "failed_count": len(failed_tx),
            "cancelled_count": len(cancelled_tx),
            "total_data_transferred_bytes": total_transferred_bytes,
            "total_data_transferred_mb": round(total_transferred_bytes / (1024 * 1024), 2),
            "average_speed_mbps": round(avg_speed, 2)
        }
    }
