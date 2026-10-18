"""
backend/api/routes_transfers.py
API endpoints for transfer management, FIFO queue inspection, and heap priority adjustments.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.file_manager.transfer_manager import get_transfer_manager

router = APIRouter(prefix="/api/transfers", tags=["transfers"])


class EnqueueTransferRequest(BaseModel):
    file_name: str
    size: int
    source_device: str
    destination_device: str
    direction: str = "DOWNLOAD"
    priority: int = 2  # 0=Critical, 1=High, 2=Normal, 3=Low
    file_id: Optional[str] = None
    source_path: str = ""
    dest_path: str = ""
    remote_ip: str = ""
    remote_port: int = 8000
    expected_hash: Optional[str] = None


class PriorityUpdateRequest(BaseModel):
    priority: int  # 0=Critical, 1=High, 2=Normal, 3=Low


@router.get("")
def get_transfers_status():
    """
    Returns current snapshot of:
    1. FIFO TransferQueue
    2. Binary Min-Heap PriorityQueue
    3. Heap tree structure for DSA visualizer
    4. Active transfers with speed and ETA
    5. Completed transfer history
    """
    manager = get_transfer_manager()
    return manager.get_queue_status()


@router.post("")
def enqueue_transfer(req: EnqueueTransferRequest):
    """Submits a file transfer task to the PriorityHeap and FIFO Queue."""
    manager = get_transfer_manager()
    task = manager.enqueue_transfer(
        file_name=req.file_name,
        size=req.size,
        source_device=req.source_device,
        destination_device=req.destination_device,
        direction=req.direction,
        priority=req.priority,
        file_id=req.file_id,
        source_path=req.source_path,
        dest_path=req.dest_path,
        remote_ip=req.remote_ip,
        remote_port=req.remote_port,
        expected_hash=req.expected_hash
    )
    return {"success": True, "task": task.to_dict()}


@router.post("/{transfer_id}/priority")
def update_priority(transfer_id: str, req: PriorityUpdateRequest):
    """Dynamically alters transfer priority in the Min-Heap."""
    manager = get_transfer_manager()
    success = manager.update_task_priority(transfer_id, req.priority)
    if not success:
        raise HTTPException(status_code=404, detail="Active transfer not found.")
    return {"success": True, "transfer_id": transfer_id, "new_priority": req.priority}


@router.post("/{transfer_id}/cancel")
def cancel_transfer(transfer_id: str):
    """Cancels a pending or active transfer."""
    manager = get_transfer_manager()
    success = manager.cancel_transfer(transfer_id)
    return {"success": True, "transfer_id": transfer_id, "status": "CANCELLED"}


class DirectIPTransferRequest(BaseModel):
    target_ip: str
    target_port: int = 8000
    file_id: Optional[str] = None
    file_name: Optional[str] = None
    direction: str = "UPLOAD"  # "UPLOAD" or "DOWNLOAD"
    priority: int = 2          # 0=Critical, 1=High, 2=Normal, 3=Low
    expected_hash: Optional[str] = None


@router.post("/direct-ip")
def transfer_direct_ip(req: DirectIPTransferRequest):
    """
    Initiates an offline peer-to-peer file transfer directly to/from another device IP on the same LAN router/hotspot.
    Leverages the PriorityHeap min-heap scheduler and FIFO Queue.
    """
    from backend.core.config import get_config
    from backend.file_manager.scanner import get_scanner
    from backend.file_manager.storage import StorageManager
    import os

    config = get_config()
    scanner = get_scanner()
    manager = get_transfer_manager()

    file_meta = None
    if req.file_id:
        file_meta = scanner.get_file_by_id(req.file_id)

    file_name = req.file_name or (file_meta.get("file_name") if file_meta else "unnamed_transfer")
    size = file_meta.get("size", 0) if file_meta else 0
    source_path = file_meta.get("full_path", "") if file_meta else ""
    expected_hash = req.expected_hash or (file_meta.get("hash") if file_meta else None)

    if req.direction.upper() == "UPLOAD":
        src_dev = f"{config.device_name} (Host)"
        dst_dev = f"Device @ {req.target_ip}:{req.target_port}"
        dest_path = ""
    else:
        src_dev = f"Device @ {req.target_ip}:{req.target_port}"
        dst_dev = f"{config.device_name} (Host)"
        dest_path = os.path.join(config.default_shared_dir, file_name)

    task = manager.enqueue_transfer(
        file_name=file_name,
        size=size,
        source_device=src_dev,
        destination_device=dst_dev,
        direction=req.direction.upper(),
        priority=req.priority,
        file_id=req.file_id,
        source_path=source_path,
        dest_path=dest_path,
        remote_ip=req.target_ip.strip(),
        remote_port=req.target_port,
        expected_hash=expected_hash
    )

    return {
        "success": True,
        "message": f"Transfer task submitted to PriorityHeap min-heap for {req.target_ip}:{req.target_port}",
        "task": task.to_dict()
    }


from fastapi import UploadFile, File, Form
import aiofiles


@router.post("/upload-to-ip")
async def upload_direct_to_ip(
    file: UploadFile = File(...),
    target_ip: str = Form(...),
    target_port: int = Form(8000),
    priority: int = Form(2)
):
    """
    Accepts file from browser/mobile and streams it directly to target IP address via offline LAN.
    """
    from backend.core.config import get_config
    import tempfile
    import os
    config = get_config()

    # Save to temp cache first
    temp_dir = os.path.join(config.default_shared_dir, ".direct_transfers")
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, file.filename)

    chunk_size = 65536
    total_size = 0
    async with aiofiles.open(temp_path, "wb") as f:
        while chunk := await file.read(chunk_size):
            await f.write(chunk)
            total_size += len(chunk)

    manager = get_transfer_manager()
    task = manager.enqueue_transfer(
        file_name=file.filename,
        size=total_size,
        source_device=f"{config.device_name} (Host)",
        destination_device=f"Device @ {target_ip}:{target_port}",
        direction="UPLOAD",
        priority=priority,
        source_path=temp_path,
        remote_ip=target_ip.strip(),
        remote_port=target_port
    )

    return {
        "success": True,
        "message": f"File queued for streaming to IP {target_ip}",
        "task": task.to_dict()
    }

