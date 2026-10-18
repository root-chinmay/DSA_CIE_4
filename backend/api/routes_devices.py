"""
backend/api/routes_devices.py
API endpoints for device discovery, pairing, manual connection, and network graph topology.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any
from backend.core.config import get_config
from backend.networking.discovery import get_discovery
from backend.networking.ip_detector import IPDetector
from backend.security.pairing import PairingManager
from backend.networking.client import PeerClient

router = APIRouter(prefix="/api/devices", tags=["devices"])


class PairRequest(BaseModel):
    device_id: str
    device_name: str
    pairing_code: str


class ManualConnectRequest(BaseModel):
    ip_address: str
    port: int = 8000
    pairing_code: Optional[str] = None


@router.get("")
def list_devices():
    """Lists all active and known LAN devices from the local device registry."""
    discovery = get_discovery()
    return {"devices": discovery.get_devices()}


@router.get("/ping")
def ping_self():
    """Returns local host identity, IP, port, and pairing code."""
    config = get_config()
    local_ip = IPDetector.get_local_ip()
    return {
        "status": "online",
        "device_id": config.device_id,
        "device_name": config.device_name,
        "ip_address": local_ip,
        "port": config.port,
        "pairing_code": config.pairing_code,
        "demo_mode": config.demo_mode
    }


@router.post("/pair")
def pair_device(req: PairRequest):
    """Verifies pairing code and authorizes peer device."""
    res = PairingManager.verify_pairing(
        remote_device_id=req.device_id,
        submitted_code=req.pairing_code
    )
    if not res.get("success"):
        raise HTTPException(status_code=403, detail=res.get("error"))
    return res


@router.post("/connect")
def manual_connect(req: ManualConnectRequest):
    """
    Connects manually to an IP and Port when UDP broadcast discovery is restricted.
    """
    peer_info = PeerClient.ping(req.ip_address, req.port)
    if not peer_info:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to connect to peer at {req.ip_address}:{req.port}. Ensure the application is running on that device and both are on the same router."
        )

    discovery = get_discovery()
    discovery.register_peer(
        device_id=peer_info["device_id"],
        device_name=peer_info["device_name"],
        ip_address=req.ip_address,
        port=req.port,
        trusted=1 if req.pairing_code else 0
    )

    pairing_result = None
    if req.pairing_code:
        pairing_result = PeerClient.pair(req.ip_address, req.port, req.pairing_code)

    return {
        "success": True,
        "peer": peer_info,
        "pairing": pairing_result
    }


@router.get("/network")
def network_status():
    """Returns local network diagnostics and active LAN IP address."""
    config = get_config()
    return IPDetector.run_diagnostics(test_port=config.port)


@router.get("/graph")
def network_graph_topology():
    """Returns the NetworkGraph topology (nodes and edges)."""
    discovery = get_discovery()
    return discovery.graph.get_topology()


@router.get("/graph/bfs")
def run_graph_bfs(start_id: Optional[str] = None):
    """Runs Breadth-First Search traversal on the network graph."""
    config = get_config()
    discovery = get_discovery()
    root = start_id or config.device_id
    return {"start_node": root, "traversal": discovery.graph.bfs(root)}


@router.get("/graph/dfs")
def run_graph_dfs(start_id: Optional[str] = None):
    """Runs Depth-First Search traversal on the network graph."""
    config = get_config()
    discovery = get_discovery()
    root = start_id or config.device_id
    return {"start_node": root, "traversal": discovery.graph.dfs(root)}


@router.get("/graph/shortest_path")
def run_graph_shortest_path(start_id: str, end_id: str):
    """Computes Dijkstra shortest path routing between two devices."""
    discovery = get_discovery()
    path_info = discovery.graph.shortest_path(start_id, end_id)
    if not path_info:
        raise HTTPException(status_code=404, detail="No route found between the specified devices.")
    return path_info


@router.get("/scan-subnet")
def scan_subnet(port: int = Query(8000, ge=1, le=65535)):
    """
    Actively scans the local subnet for active devices and peer nodes on the offline network.
    Uses ARP cache inspection and concurrent socket probes.
    """
    return IPDetector.scan_subnet(port=port)


@router.get("/mobile-info")
def mobile_info():
    """
    Returns connection details for mobile devices on the same offline LAN router or mobile hotspot.
    """
    config = get_config()
    return IPDetector.get_mobile_info(port=config.port)


class PingIPRequest(BaseModel):
    ip_address: str
    port: int = 8000


@router.post("/ping-ip")
def ping_remote_ip(req: PingIPRequest):
    """
    Probes an IP address on LAN to check responsiveness and retrieve peer metadata.
    """
    info = PeerClient.probe_ip(req.ip_address, req.port)
    if not info:
        # Check basic socket connectivity if full LAN sync ping fails
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.6)
        port_open = False
        try:
            s.connect((req.ip_address, req.port))
            port_open = True
            s.close()
        except Exception:
            pass
        return {
            "reachable": port_open,
            "has_lan_sync": False,
            "ip_address": req.ip_address,
            "port": req.port,
            "device_name": "Generic Device" if port_open else "Unreachable"
        }

    return {
        "reachable": True,
        "has_lan_sync": True,
        "ip_address": req.ip_address,
        "port": req.port,
        "peer": info
    }

