"""
backend/api/routes_settings.py
API endpoints for application settings, pairing code regeneration, demo mode toggle, and logs.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.core.config import get_config
from backend.security.pairing import PairingManager
from backend.core.logger import AppLogger
from backend.demo.demo_simulator import DemoSimulator
from backend.database.db import get_db

router = APIRouter(prefix="/api/settings", tags=["settings"])


class UpdateSettingsRequest(BaseModel):
    device_name: Optional[str] = None
    port: Optional[int] = None
    chunk_size_mb: Optional[int] = None
    max_transfers: Optional[int] = None


@router.get("")
def get_settings():
    """Returns current device configuration."""
    config = get_config()
    return config.to_dict()


@router.post("")
def update_settings(req: UpdateSettingsRequest):
    """Updates configuration parameters."""
    config = get_config()
    updates = {}
    if req.device_name:
        updates["device_name"] = req.device_name
    if req.port:
        updates["port"] = req.port
    if req.chunk_size_mb:
        updates["chunk_size_mb"] = req.chunk_size_mb
    if req.max_transfers:
        updates["max_transfers"] = req.max_transfers

    config.update(**updates)
    AppLogger.log("SETTINGS_UPDATED", status="INFO", message="Configuration saved.")
    return {"success": True, "settings": config.to_dict()}


@router.post("/pairing-code/reset")
def reset_pairing_code():
    """Generates a fresh 6-digit numeric pairing code."""
    new_code = PairingManager.regenerate_code()
    return {"success": True, "pairing_code": new_code}


@router.post("/demo/toggle")
def toggle_demo_mode():
    """Toggles Demo Mode on/off, populating virtual peers and demo datasets if enabled."""
    config = get_config()
    new_state = not config.demo_mode
    config.update(demo_mode=new_state)

    if new_state:
        res = DemoSimulator.populate_demo_data()
        return {"success": True, "demo_mode": True, "details": res}
    else:
        AppLogger.log("DEMO_DISABLED", status="INFO", message="Demo mode deactivated. Switched to normal LAN mode.")
        return {"success": True, "demo_mode": False}


@router.get("/logs")
def get_logs(limit: int = 100):
    """Returns audit log records."""
    return {"logs": AppLogger.get_recent_logs(limit=limit)}
