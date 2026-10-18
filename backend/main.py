"""
backend/main.py
Main entrypoint for the DSA-Based Offline LAN File Sharing & Synchronization System.
FastAPI application with REST endpoints, WebSocket streaming, and static UI delivery.
"""

import os
import sys
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Ensure root is in sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.core.config import get_config
from backend.core.logger import AppLogger
from backend.core.event_bus import get_event_bus
from backend.networking.ip_detector import IPDetector
from backend.networking.discovery import get_discovery
from backend.file_manager.scanner import get_scanner
from backend.file_manager.storage import StorageManager
from backend.api import (
    devices_router,
    files_router,
    folders_router,
    transfers_router,
    sync_router,
    dsa_router,
    settings_router,
    analytics_router,
    ws_manager,
    websocket_bridge_task
)

FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
if not os.path.exists(FRONTEND_DIR):
    cwd_fe = os.path.join(os.getcwd(), "frontend")
    if os.path.exists(cwd_fe):
        FRONTEND_DIR = cwd_fe


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event handler for server startup and teardown."""
    is_vercel = bool(os.environ.get("VERCEL"))
    config = get_config()
    local_ip = IPDetector.get_local_ip()
    event_bus = get_event_bus()

    # Bind active event loop to event bus
    loop = asyncio.get_running_loop()
    event_bus.set_loop(loop)

    # Start background WebSocket bridge task
    bridge_task = asyncio.create_task(websocket_bridge_task())

    # Ensure default shared folder exists and is registered
    os.makedirs(config.default_shared_dir, exist_ok=True)
    StorageManager.add_shared_folder(config.default_shared_dir, "Shared Files")

    # Initial disk scan to populate Tree, Hash Table, and Trie
    scanner = get_scanner()
    scanner.scan_all()

    # If running on Vercel preview, populate demo data so dashboard and visualizer are populated
    if is_vercel:
        try:
            from backend.demo.demo_simulator import DemoSimulator
            DemoSimulator.populate_demo_data()
        except Exception as e:
            AppLogger.log("DEMO_POPULATE_WARN", status="WARN", message=f"Vercel demo init: {e}")

    # Start UDP LAN broadcast discovery (offline LAN only, disabled in serverless cloud)
    discovery = None
    if not is_vercel:
        try:
            discovery = get_discovery()
            discovery.start()
        except Exception as e:
            AppLogger.log("DISCOVERY_START_ERROR", status="WARN", message=f"Discovery error: {e}")

    banner = f"""
========================================================================
  DSA-BASED OFFLINE LAN FILE SHARING & SYNCHRONIZATION SYSTEM
========================================================================
  Status:        ONLINE ({"VERCEL CLOUD PREVIEW" if is_vercel else "OFFLINE-FIRST LAN READY"})
  Local LAN IP:  {local_ip}
  Server Port:   {config.port}
  Dashboard:     http://{local_ip}:{config.port}/
  Device ID:     {config.device_id}
  Device Name:   {config.device_name}
  Pairing Code:  {config.pairing_code}
  Shared Dir:    {config.default_shared_dir}
========================================================================
"""
    print(banner, flush=True)
    AppLogger.log("SYSTEM_STARTUP", status="SUCCESS", message=f"Host listening on http://{local_ip}:{config.port}")

    yield

    # Shutdown
    if discovery:
        try:
            discovery.stop()
        except Exception:
            pass
    try:
        bridge_task.cancel()
    except Exception:
        pass
    AppLogger.log("SYSTEM_SHUTDOWN", status="INFO", message="Server gracefully stopped.")


app = FastAPI(
    title="DSA-Based Offline LAN File Sharing and Synchronization System",
    description="Offline-first LAN file sharing, synchronization, and DSA demonstration engine.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration allowing any LAN client to interact
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Mount REST API Routers
app.include_router(devices_router)
app.include_router(files_router)
app.include_router(folders_router)
app.include_router(transfers_router)
app.include_router(sync_router)
app.include_router(dsa_router)
app.include_router(settings_router)
app.include_router(analytics_router)


# Real-time WebSocket connection endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection open; receive client pings if any
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


# Serve Static Frontend Files
if os.path.exists(FRONTEND_DIR):
    css_dir = os.path.join(FRONTEND_DIR, "css")
    js_dir = os.path.join(FRONTEND_DIR, "js")
    if os.path.exists(css_dir):
        app.mount("/css", StaticFiles(directory=css_dir), name="css")
    if os.path.exists(js_dir):
        app.mount("/js", StaticFiles(directory=js_dir), name="js")


@app.get("/")
async def serve_index():
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {
        "status": "DSA-Based Offline LAN File Sharing System is running.",
        "mode": "Vercel Serverless" if os.environ.get("VERCEL") else "Local LAN",
        "frontend_dir": FRONTEND_DIR
    }


if __name__ == "__main__":
    import uvicorn
    cfg = get_config()
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=cfg.port,
        reload=False,
        log_level="info"
    )
