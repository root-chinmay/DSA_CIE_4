"""
backend/api/routes_sync.py
API endpoints for intelligent file synchronization and conflict resolution.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from backend.file_manager.scanner import get_scanner
from backend.synchronization.sync_engine import SynchronizationEngine
from backend.synchronization.conflict import ConflictManager
from backend.file_manager.transfer_manager import get_transfer_manager
from backend.networking.client import PeerClient
from backend.database.db import get_db

router = APIRouter(prefix="/api/sync", tags=["synchronization"])


class ResolveConflictRequest(BaseModel):
    resolution: str  # 'KEEP_LOCAL', 'KEEP_REMOTE', 'KEEP_BOTH'


class StartSyncRequest(BaseModel):
    peer_ip: Optional[str] = None
    peer_port: int = 8000
    files_to_sync: Optional[List[str]] = None  # List of relative paths


@router.get("/diff")
def get_sync_diff(peer_ip: Optional[str] = None, peer_port: int = 8000):
    """
    Compares local FileTree with peer FileTree or generates simulated diff in demo mode.
    Classifies files into SYNCED, NEW, MODIFIED, and CONFLICT.
    """
    scanner = get_scanner()
    local_files = scanner.get_all_files()

    remote_files = []
    if peer_ip:
        peer_data = PeerClient.fetch_peer_files(peer_ip, peer_port)
        if peer_data and "files" in peer_data:
            remote_files = peer_data["files"]
    else:
        # Fallback / simulated comparison for demo
        db = get_db()
        conflicts = db.execute_query("SELECT * FROM sync_conflicts WHERE status = 'PENDING'")
        # Generate simulated peer file set
        for f in local_files:
            remote_files.append(dict(f))
        # Add a modified file and a new remote file for presentation
        if remote_files:
            remote_files[0]["hash"] = "different_hash_from_remote_change_123"
            remote_files[0]["modified_time"] = time_now = remote_files[0].get("modified_time", 0) + 100
        remote_files.append({
            "file_name": "remote_announcement.pdf",
            "name": "remote_announcement.pdf",
            "relative_path": "Documents/remote_announcement.pdf",
            "size": 2048576,
            "hash": "b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3",
            "modified_time": 1700000000,
            "file_type": "pdf"
        })

    diff_matrix = SynchronizationEngine.compare_trees(local_files, remote_files)
    return {
        "diff_matrix": diff_matrix,
        "total_items": len(diff_matrix),
        "synced_count": sum(1 for d in diff_matrix if d["state"] == "SYNCED"),
        "new_local_count": sum(1 for d in diff_matrix if d["state"] == "NEW_LOCAL"),
        "new_remote_count": sum(1 for d in diff_matrix if d["state"] == "NEW_REMOTE"),
        "modified_count": sum(1 for d in diff_matrix if "MODIFIED" in d["state"]),
        "conflict_count": sum(1 for d in diff_matrix if d["state"] == "CONFLICT")
    }


@router.post("/start")
def start_synchronization(req: StartSyncRequest):
    """
    Launches prioritized background file synchronization for pending sync items.
    """
    scanner = get_scanner()
    tx_manager = get_transfer_manager()
    diff_res = get_sync_diff(req.peer_ip, req.peer_port)
    diff_matrix = diff_res["diff_matrix"]

    enqueued_tasks = []
    for item in diff_matrix:
        rel_path = item["relative_path"]
        if req.files_to_sync and rel_path not in req.files_to_sync:
            continue

        action = item["action"]
        if action == "DOWNLOAD_TO_LOCAL":
            task = tx_manager.enqueue_transfer(
                file_name=item["file_name"],
                size=item["remote_size"] or 1048576,
                source_device=req.peer_ip or "Remote Peer",
                destination_device="Local Host",
                direction="DOWNLOAD",
                priority=3,  # LOW priority for background sync
                expected_hash=item["remote_hash"]
            )
            enqueued_tasks.append(task.to_dict())
        elif action == "UPLOAD_TO_REMOTE":
            task = tx_manager.enqueue_transfer(
                file_name=item["file_name"],
                size=item["local_size"] or 1048576,
                source_device="Local Host",
                destination_device=req.peer_ip or "Remote Peer",
                direction="UPLOAD",
                priority=3,  # LOW priority for background sync
                expected_hash=item["local_hash"]
            )
            enqueued_tasks.append(task.to_dict())

    return {
        "success": True,
        "enqueued_count": len(enqueued_tasks),
        "tasks": enqueued_tasks
    }


@router.get("/conflicts")
def list_conflicts():
    """Lists pending synchronization conflicts."""
    return {"conflicts": ConflictManager.list_conflicts(status="PENDING")}


@router.post("/conflicts/{conflict_id}/resolve")
def resolve_conflict(conflict_id: int, req: ResolveConflictRequest):
    """
    Resolves a synchronization conflict.
    Options: 'KEEP_LOCAL', 'KEEP_REMOTE', 'KEEP_BOTH'.
    """
    res = ConflictManager.resolve_conflict(conflict_id=conflict_id, resolution=req.resolution)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res
