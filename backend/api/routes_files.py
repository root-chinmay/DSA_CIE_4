"""
backend/api/routes_files.py
API endpoints for file browsing, tree visualization, streaming chunk download/upload,
duplicate detection, Trie prefix search, and custom MergeSort/QuickSort sorting.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import aiofiles
from backend.file_manager.scanner import get_scanner
from backend.file_manager.storage import StorageManager
from backend.file_manager.hasher import StreamingHasher
from backend.dsa.sorting import Sorter
from backend.core.logger import AppLogger
from backend.database.db import get_db

router = APIRouter(prefix="/api/files", tags=["files"])


class RenameRequest(BaseModel):
    new_name: str


class SortRequest(BaseModel):
    by: str = "name"              # "name", "size", "modified_time", "file_type"
    algorithm: str = "merge_sort" # "merge_sort" or "quick_sort"
    reverse: bool = False


@router.get("")
def list_files(
    folder: Optional[str] = None,
    sort_by: str = "name",
    algorithm: str = "merge_sort",
    reverse: bool = False,
    file_type: Optional[str] = None
):
    """
    Returns files indexed in the Hash Table.
    Applies custom Merge Sort or Quick Sort with algorithm statistics.
    """
    scanner = get_scanner()
    files = scanner.get_all_files()

    # Filter by folder if specified
    if folder:
        clean_folder = folder.replace("\\", "/").strip("/")
        files = [
            f for f in files
            if f.get("relative_path", "").startswith(clean_folder)
        ]

    # Filter by type if specified
    if file_type and file_type != "all":
        files = [
            f for f in files
            if f.get("file_type", "").lower() == file_type.lower()
        ]

    # Apply Custom Sorting (Merge Sort or Quick Sort)
    sorted_files, metrics = Sorter.sort(
        items=files,
        by=sort_by,
        algorithm=algorithm,
        reverse=reverse
    )

    return {
        "files": sorted_files,
        "total": len(sorted_files),
        "sort_metrics": metrics
    }


@router.get("/tree")
def get_file_tree(max_depth: Optional[int] = None):
    """Returns the logical FileTree hierarchy for visualization and explorer tree view."""
    scanner = get_scanner()
    return scanner.tree.to_dict(max_depth=max_depth)


@router.get("/duplicates")
def get_duplicate_files():
    """
    Detects duplicate files sharing identical SHA-256 cryptographic hashes
    using the secondary Hash Table index in O(1) lookup per hash cluster.
    """
    scanner = get_scanner()
    duplicates = scanner.hash_index.find_duplicates()
    return {
        "duplicate_groups": duplicates,
        "total_groups": len(duplicates),
        "total_duplicate_files": sum(d["count"] for d in duplicates),
        "total_wasted_bytes": sum(d["wasted_size"] for d in duplicates)
    }


@router.get("/search")
def search_files(q: str, autocomplete: bool = False, limit: int = 20):
    """
    Prefix search and autocomplete powered by the Filename Trie in O(L) time.
    """
    scanner = get_scanner()
    if autocomplete:
        suggestions = scanner.trie.autocomplete(prefix=q, limit=limit)
        return {"query": q, "suggestions": suggestions}
    else:
        results = scanner.trie.search_prefix(prefix=q, max_results=limit)
        return {
            "query": q,
            "results": results,
            "count": len(results),
            "algorithm": "Trie Prefix Search (O(L + K))"
        }


@router.post("/sort")
def execute_custom_sort(req: SortRequest):
    """
    Executes and benchmarks Merge Sort vs Quick Sort on the current file dataset.
    """
    scanner = get_scanner()
    files = scanner.get_all_files()

    sorted_files, metrics = Sorter.sort(
        items=files,
        by=req.by,
        algorithm=req.algorithm,
        reverse=req.reverse
    )
    return {
        "metrics": metrics,
        "sorted_files": sorted_files[:50]  # preview first 50
    }


@router.get("/{file_id}")
def get_file_details(file_id: str):
    """Retrieves file metadata from the primary Hash Table index in O(1) time."""
    scanner = get_scanner()
    meta = scanner.get_file_by_id(file_id)
    if not meta:
        raise HTTPException(status_code=404, detail="File not found in index.")
    return meta


@router.get("/{file_id}/download")
def download_file_stream(file_id: str):
    """
    Streams file chunks to client without loading into RAM.
    """
    scanner = get_scanner()
    meta = scanner.get_file_by_id(file_id)
    if not meta:
        raise HTTPException(status_code=404, detail="File not found in index.")

    filepath = meta.get("full_path")
    if not filepath or not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="File missing on host storage.")

    def iterfile():
        chunk_size = 65536  # 64 KB buffer
        with open(filepath, "rb") as f:
            while chunk := f.read(chunk_size):
                yield chunk

    filename = meta.get("file_name") or os.path.basename(filepath)
    file_size = meta.get("size", os.path.getsize(filepath))

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Length": str(file_size),
        "X-File-SHA256": meta.get("hash") or ""
    }

    AppLogger.log("DOWNLOAD_SERVED", status="INFO", file_name=filename, message=f"Serving {file_size} bytes")
    return StreamingResponse(iterfile(), media_type="application/octet-stream", headers=headers)


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    folder_path: str = Form(""),
    folder_id: Optional[int] = Form(None)
):
    """
    Uploads a file via streaming chunks, validates path safety,
    hashes with SHA-256 in flight, and re-indexes into Tree, Hash Table, and Trie.
    """
    db = get_db()
    scanner = get_scanner()

    # Determine destination directory safely
    relative_target = os.path.join(folder_path, file.filename).replace("\\", "/").lstrip("/")
    try:
        abs_dest_path, folder_record = StorageManager.validate_and_resolve_path(
            relative_target, folder_id=folder_id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    os.makedirs(os.path.dirname(abs_dest_path), exist_ok=True)

    # Stream upload directly to disk
    chunk_size = 65536
    transferred = 0
    async with aiofiles.open(abs_dest_path, "wb") as out_file:
        while chunk := await file.read(chunk_size):
            await out_file.write(chunk)
            transferred += len(chunk)

    # Compute SHA-256 digest
    file_hash = StreamingHasher.hash_file(abs_dest_path) or ""

    # Rescan to update Tree, Hash Table, and Trie
    scanner.scan_all()
    AppLogger.log("UPLOAD_RECEIVED", status="INFO", file_name=file.filename, message=f"Saved {transferred} bytes (SHA-256: {file_hash[:8]}...)")

    return {
        "success": True,
        "file_name": file.filename,
        "relative_path": relative_target,
        "size": transferred,
        "hash": file_hash
    }


@router.post("/{file_id}/delete")
def delete_file(file_id: str):
    """Safely deletes file from shared storage and memory structures."""
    scanner = get_scanner()
    meta = scanner.get_file_by_id(file_id)
    if not meta:
        raise HTTPException(status_code=404, detail="File not found in index.")

    rel_path = meta.get("relative_path")
    folder_id = meta.get("folder_id")

    success = StorageManager.safe_delete(rel_path, folder_id)
    if success:
        scanner.scan_all()
        return {"success": True, "file_id": file_id, "deleted": rel_path}
    raise HTTPException(status_code=500, detail="Failed to delete file.")


@router.post("/{file_id}/rename")
def rename_file(file_id: str, req: RenameRequest):
    """Safely renames a file."""
    scanner = get_scanner()
    meta = scanner.get_file_by_id(file_id)
    if not meta:
        raise HTTPException(status_code=404, detail="File not found in index.")

    rel_path = meta.get("relative_path")
    folder_id = meta.get("folder_id")

    try:
        new_rel = StorageManager.safe_rename(rel_path, req.new_name, folder_id)
        scanner.scan_all()
        return {"success": True, "file_id": file_id, "new_path": new_rel}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
