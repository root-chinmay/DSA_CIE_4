"""
backend/api/routes_folders.py
API endpoints for managing shared folders and triggering disk rescans.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.file_manager.storage import StorageManager
from backend.file_manager.scanner import get_scanner

router = APIRouter(prefix="/api/folders", tags=["folders"])


class AddFolderRequest(BaseModel):
    folder_path: str
    folder_name: Optional[str] = None


@router.get("")
def list_shared_folders():
    """Lists all registered shared folders with file counts and total sizes."""
    folders = StorageManager.get_shared_folders()
    scanner = get_scanner()
    # Enrich with file count and size from scanner
    enriched = []
    for f in folders:
        f_dict = dict(f)
        matching_files = [x for x in scanner.get_all_files() if x.get("folder_id") == f["id"]]
        f_dict["file_count"] = len(matching_files)
        f_dict["total_size"] = sum(x.get("size", 0) for x in matching_files)
        enriched.append(f_dict)
    return {"folders": enriched}


@router.post("")
def add_shared_folder(req: AddFolderRequest):
    """Registers a new shared folder and immediately scans it."""
    try:
        folder = StorageManager.add_shared_folder(req.folder_path, req.folder_name)
        scanner = get_scanner()
        stats = scanner.scan_all()
        return {"success": True, "folder": folder, "scan_summary": stats}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{folder_id}")
def remove_shared_folder(folder_id: int):
    """Unregisters a shared folder."""
    success = StorageManager.remove_shared_folder(folder_id)
    if success:
        scanner = get_scanner()
        scanner.scan_all()
        return {"success": True, "folder_id": folder_id}
    raise HTTPException(status_code=404, detail="Shared folder not found.")


@router.post("/scan")
def trigger_disk_rescan(force_rehash: bool = False):
    """Triggers complete re-indexing of all shared folders into Tree, Hash Table, and Trie."""
    scanner = get_scanner()
    stats = scanner.scan_all(force_rehash=force_rehash)
    return {"success": True, "summary": stats}
