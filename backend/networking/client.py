"""
backend/networking/client.py
HTTP Client for communicating with peer laptops across the offline LAN.
Handles pairing requests, tree synchronization, and streaming chunk transfers.
"""

import os
import requests
import time
from typing import Dict, Any, Optional, Callable
from backend.file_manager.hasher import StreamingHasher
from backend.core.logger import AppLogger
from backend.core.config import get_config


class PeerClient:
    """Interacts with remote peer nodes over HTTP."""

    TIMEOUT = 5.0  # seconds

    @classmethod
    def ping(cls, ip: str, port: int) -> Optional[Dict[str, Any]]:
        """
        Pings a peer node to verify LAN connectivity and obtain device metadata.
        """
        url = f"http://{ip}:{port}/api/devices/ping"
        try:
            resp = requests.get(url, timeout=cls.TIMEOUT)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return None

    @classmethod
    def pair(cls, ip: str, port: int, pairing_code: str) -> Dict[str, Any]:
        """
        Sends pairing request to peer device.
        """
        config = get_config()
        url = f"http://{ip}:{port}/api/devices/pair"
        payload = {
            "device_id": config.device_id,
            "device_name": config.device_name,
            "pairing_code": pairing_code.strip()
        }
        try:
            resp = requests.post(url, json=payload, timeout=cls.TIMEOUT)
            return resp.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def fetch_peer_tree(cls, ip: str, port: int) -> Optional[Dict[str, Any]]:
        """Retrieves remote peer's FileTree."""
        url = f"http://{ip}:{port}/api/files/tree"
        try:
            resp = requests.get(url, timeout=cls.TIMEOUT)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            AppLogger.log("PEER_TREE_ERROR", status="ERROR", message=f"Failed to fetch tree from {ip}:{port}: {e}")
        return None

    @classmethod
    def fetch_peer_files(cls, ip: str, port: int) -> Optional[Dict[str, Any]]:
        """Retrieves flat list of remote peer's files."""
        url = f"http://{ip}:{port}/api/files"
        try:
            resp = requests.get(url, timeout=cls.TIMEOUT)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return None

    @classmethod
    def download_file_chunked(
        cls,
        ip: str,
        port: int,
        file_id: str,
        save_path: str,
        expected_hash: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int, float], None]] = None
    ) -> Dict[str, Any]:
        """
        Downloads a file from peer in streaming chunks without loading into RAM.
        Verifies SHA-256 cryptographic digest upon completion.
        """
        url = f"http://{ip}:{port}/api/files/{file_id}/download"
        start_time = time.time()
        os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)

        try:
            with requests.get(url, stream=True, timeout=15.0) as resp:
                if resp.status_code != 200:
                    return {"success": False, "error": f"HTTP {resp.status_code}"}

                total_size = int(resp.headers.get("content-length", 0))
                transferred = 0
                chunk_size = 65536  # 64 KB streaming buffer

                with open(save_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=chunk_size):
                        if not chunk:
                            break
                        f.write(chunk)
                        transferred += len(chunk)
                        elapsed = max(0.001, time.time() - start_time)
                        speed_mbps = (transferred / (1024 * 1024)) / elapsed

                        if progress_callback:
                            progress_callback(transferred, total_size, speed_mbps)

            # Integrity verification
            actual_hash = StreamingHasher.hash_file(save_path)
            hash_verified = True
            if expected_hash and actual_hash:
                hash_verified = (actual_hash.lower() == expected_hash.lower())

            duration = time.time() - start_time
            avg_speed = (transferred / (1024 * 1024)) / max(0.001, duration)

            return {
                "success": hash_verified,
                "transferred_bytes": transferred,
                "total_size": total_size,
                "duration_seconds": round(duration, 2),
                "speed_mbps": round(avg_speed, 2),
                "actual_hash": actual_hash,
                "hash_verified": hash_verified,
                "error": None if hash_verified else "SHA-256 Integrity Verification Failed!"
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def upload_file_chunked(
        cls,
        ip: str,
        port: int,
        file_path: str,
        folder_path: str = "",
        progress_callback: Optional[Callable[[int, int, float], None]] = None
    ) -> Dict[str, Any]:
        """
        Uploads a local file to a peer node at ip:port over the offline LAN.
        Streams in chunks and verifies the SHA-256 returned by the receiver.
        """
        if not os.path.isfile(file_path):
            return {"success": False, "error": f"Local file not found: {file_path}"}

        url = f"http://{ip}:{port}/api/files/upload"
        start_time = time.time()
        file_name = os.path.basename(file_path)
        total_size = os.path.getsize(file_path)
        local_hash = StreamingHasher.hash_file(file_path)

        try:
            class ProgressFile:
                def __init__(self, filepath, callback):
                    self._f = open(filepath, "rb")
                    self._transferred = 0
                    self._total = total_size
                    self._cb = callback
                    self._start = time.time()

                def read(self, size=-1):
                    chunk = self._f.read(size)
                    if chunk:
                        self._transferred += len(chunk)
                        if self._cb:
                            elapsed = max(0.001, time.time() - self._start)
                            speed_mbps = (self._transferred / (1024 * 1024)) / elapsed
                            self._cb(self._transferred, self._total, speed_mbps)
                    return chunk

                def __len__(self):
                    return self._total

                def close(self):
                    self._f.close()

            prog_file = ProgressFile(file_path, progress_callback)
            files = {"file": (file_name, prog_file, "application/octet-stream")}
            data = {"folder_path": folder_path}

            resp = requests.post(url, files=files, data=data, timeout=60.0)
            prog_file.close()

            if resp.status_code != 200:
                return {"success": False, "error": f"Peer responded with HTTP {resp.status_code}: {resp.text}"}

            res_json = resp.json()
            remote_hash = res_json.get("hash")
            hash_verified = True
            if local_hash and remote_hash:
                hash_verified = (local_hash.lower() == remote_hash.lower())

            duration = time.time() - start_time
            avg_speed = (total_size / (1024 * 1024)) / max(0.001, duration)

            return {
                "success": hash_verified,
                "transferred_bytes": total_size,
                "total_size": total_size,
                "duration_seconds": round(duration, 2),
                "speed_mbps": round(avg_speed, 2),
                "actual_hash": local_hash,
                "remote_hash": remote_hash,
                "hash_verified": hash_verified,
                "error": None if hash_verified else "SHA-256 Checksum Mismatch with Peer!"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def probe_ip(cls, ip: str, port: int = 8000, timeout: float = 0.5) -> Optional[Dict[str, Any]]:
        """
        Fast probe to verify if a device at ip:port is reachable on LAN and running LAN Sync.
        """
        try:
            url = f"http://{ip}:{port}/api/devices/ping"
            resp = requests.get(url, timeout=timeout)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return None

