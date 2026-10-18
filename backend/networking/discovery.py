"""
backend/networking/discovery.py
UDP Broadcast Device Discovery & Heartbeat Manager for local router LAN.
Includes automatic offline state detection and manual fallback connection.
"""

import socket
import json
import threading
import time
from typing import Dict, Any, List, Optional
from backend.core.config import get_config
from backend.core.logger import AppLogger
from backend.core.event_bus import get_event_bus
from backend.database.db import get_db
from backend.dsa.graph import NetworkGraph, DeviceNode
from backend.networking.ip_detector import IPDetector


class UDPDeviceDiscovery:
    """
    Manages peer discovery over UDP broadcast port 42424.
    Updates NetworkGraph and SQLite devices table in real time.
    """

    BROADCAST_PORT = 42424
    MAGIC_HEADER = "OFFLINE_LAN_DSA_SYNC"
    HEARTBEAT_INTERVAL = 3.0  # seconds between broadcasts
    OFFLINE_TIMEOUT = 12.0     # seconds without packet to mark offline

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(UDPDeviceDiscovery, cls).__new__(cls)
                cls._instance._init_discovery()
            return cls._instance

    def _init_discovery(self) -> None:
        self.config = get_config()
        self.graph = NetworkGraph()
        self.is_running = False
        self._threads: List[threading.Thread] = []

        # Add self node to graph
        local_ip = IPDetector.get_local_ip()
        self_node = DeviceNode(
            device_id=self.config.device_id,
            device_name=self.config.device_name,
            ip_address=local_ip,
            port=self.config.port,
            status="online",
            is_self=True
        )
        self.graph.add_node(self_node)

    def start(self) -> None:
        """Starts broadcaster, listener, and heartbeat sweeper threads."""
        if self.is_running:
            return
        self.is_running = True

        t_broadcaster = threading.Thread(target=self._broadcast_loop, daemon=True, name="UDP-Broadcaster")
        t_listener = threading.Thread(target=self._listen_loop, daemon=True, name="UDP-Listener")
        t_sweeper = threading.Thread(target=self._sweeper_loop, daemon=True, name="Heartbeat-Sweeper")

        self._threads = [t_broadcaster, t_listener, t_sweeper]
        for t in self._threads:
            t.start()

        AppLogger.log("DISCOVERY_STARTED", status="INFO", message=f"UDP discovery listening on port {self.BROADCAST_PORT}")

    def stop(self) -> None:
        self.is_running = False

    def _broadcast_loop(self) -> None:
        """Periodically announces device presence over UDP broadcast."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        while self.is_running:
            try:
                local_ip = IPDetector.get_local_ip()
                message = {
                    "magic": self.MAGIC_HEADER,
                    "device_id": self.config.device_id,
                    "device_name": self.config.device_name,
                    "ip_address": local_ip,
                    "port": self.config.port,
                    "features": ["chunked_transfer", "sync", "priority_queue", "dsa_visualizer"],
                    "timestamp": time.time()
                }
                data = json.dumps(message).encode("utf-8")
                # Broadcast to subnet / local broadcast address
                sock.sendto(data, ("<broadcast>", self.BROADCAST_PORT))
            except Exception as e:
                # Some OS socket stacks require fallback to 255.255.255.255
                try:
                    sock.sendto(data, ("255.255.255.255", self.BROADCAST_PORT))
                except Exception:
                    pass
            time.sleep(self.HEARTBEAT_INTERVAL)
        sock.close()

    def _listen_loop(self) -> None:
        """Listens for peer UDP announcements."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("", self.BROADCAST_PORT))
        except Exception as e:
            AppLogger.log("DISCOVERY_BIND_ERROR", status="WARN", message=f"Cannot bind UDP port {self.BROADCAST_PORT}: {e}")
            return

        while self.is_running:
            try:
                data, addr = sock.recvfrom(4096)
                if not data:
                    continue

                msg = json.loads(data.decode("utf-8"))
                if msg.get("magic") != self.MAGIC_HEADER:
                    continue

                peer_id = msg.get("device_id")
                # Ignore self announcements
                if not peer_id or peer_id == self.config.device_id:
                    continue

                peer_name = msg.get("device_name", "Unknown Peer")
                peer_ip = msg.get("ip_address") or addr[0]
                peer_port = int(msg.get("port", 8000))

                self.register_peer(
                    device_id=peer_id,
                    device_name=peer_name,
                    ip_address=peer_ip,
                    port=peer_port
                )
            except Exception:
                pass
        sock.close()

    def register_peer(
        self,
        device_id: str,
        device_name: str,
        ip_address: str,
        port: int,
        trusted: Optional[int] = None
    ) -> None:
        """
        Registers or updates a peer in SQLite and the NetworkGraph.
        """
        db = get_db()
        now = time.time()

        existing = db.execute_query_one("SELECT * FROM devices WHERE device_id = ?", (device_id,))
        is_new = (existing is None)

        if is_new:
            db.execute_write(
                """
                INSERT INTO devices (device_id, device_name, ip_address, port, status, last_seen, trusted, role, created_at)
                VALUES (?, ?, ?, ?, 'online', ?, ?, 'READ_ONLY', ?)
                """,
                (device_id, device_name, ip_address, port, now, 1 if trusted else 0, now)
            )
            AppLogger.log("DEVICE_DISCOVERED", status="INFO", device=device_name, message=f"New device at {ip_address}:{port}")
        else:
            db.execute_write(
                """
                UPDATE devices SET
                    device_name = ?,
                    ip_address = ?,
                    port = ?,
                    status = 'online',
                    last_seen = ?
                WHERE device_id = ?
                """,
                (device_name, ip_address, port, now, device_id)
            )

        # Update NetworkGraph
        node = DeviceNode(
            device_id=device_id,
            device_name=device_name,
            ip_address=ip_address,
            port=port,
            status="online"
        )
        self.graph.add_node(node)
        self.graph.add_edge(self.config.device_id, device_id, latency_ms=1.5, bandwidth_mbps=100.0)

        # Notify via EventBus if newly discovered
        if is_new:
            try:
                get_event_bus().publish_sync("DEVICE_CONNECTED", node.to_dict())
            except Exception:
                pass

    def _sweeper_loop(self) -> None:
        """Periodically checks last_seen timestamps to mark inactive devices offline."""
        while self.is_running:
            time.sleep(4.0)
            now = time.time()
            db = get_db()
            online_devices = db.execute_query("SELECT * FROM devices WHERE status = 'online'")

            for dev in online_devices:
                dev_id = dev["device_id"]
                if dev_id == self.config.device_id:
                    continue

                if (now - dev["last_seen"]) > self.OFFLINE_TIMEOUT:
                    db.execute_write(
                        "UPDATE devices SET status = 'offline' WHERE device_id = ?",
                        (dev_id,)
                    )
                    if dev_id in self.graph.nodes:
                        self.graph.nodes[dev_id].status = "offline"

                    AppLogger.log("DEVICE_OFFLINE", status="WARN", device=dev["device_name"], message="Device timed out")
                    try:
                        get_event_bus().publish_sync("DEVICE_DISCONNECTED", {"device_id": dev_id})
                    except Exception:
                        pass

    def get_devices(self) -> List[Dict[str, Any]]:
        """Returns all discovered devices from database."""
        db = get_db()
        return db.execute_query("SELECT * FROM devices ORDER BY status ASC, last_seen DESC")


def get_discovery() -> UDPDeviceDiscovery:
    return UDPDeviceDiscovery()
