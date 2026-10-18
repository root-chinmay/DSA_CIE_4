"""
backend/demo/demo_simulator.py
Single-Laptop Demo Simulator for academic evaluations.
Simulates Laptop A, Laptop B, and Laptop C on a local network with realistic files,
transfers, duplicate clusters, graph topology, and synchronization conflicts.
"""

import time
import os
from typing import Dict, Any
from backend.core.config import get_config
from backend.core.logger import AppLogger
from backend.database.db import get_db
from backend.file_manager.scanner import get_scanner
from backend.file_manager.storage import StorageManager
from backend.file_manager.transfer_manager import get_transfer_manager
from backend.networking.discovery import get_discovery
from backend.dsa.graph import DeviceNode


class DemoSimulator:
    """Manages demonstration scenarios for single-laptop evaluations."""

    @classmethod
    def populate_demo_data(cls) -> Dict[str, Any]:
        """
        Populates mock nodes, sample files, duplicate hashes, queued transfers,
        and sync conflicts for immediate demonstration.
        """
        config = get_config()
        db = get_db()
        scanner = get_scanner()
        discovery = get_discovery()
        tx_manager = get_transfer_manager()

        AppLogger.log("DEMO_INIT", status="INFO", message="Initializing Demonstration Environment.")

        # 1. Setup sample files on disk in data/shared_files
        shared_dir = config.default_shared_dir
        os.makedirs(os.path.join(shared_dir, "Documents"), exist_ok=True)
        os.makedirs(os.path.join(shared_dir, "Algorithms"), exist_ok=True)
        os.makedirs(os.path.join(shared_dir, "Projects"), exist_ok=True)

        sample_files = [
            ("Documents/report_final.pdf", b"PDF_DATA_CONTENT_DSA_2026_OFFLINE_LAN" * 200),
            ("Documents/report_final_copy.pdf", b"PDF_DATA_CONTENT_DSA_2026_OFFLINE_LAN" * 200),  # Duplicate!
            ("Documents/lecture_notes.txt", b"Notes on Trees, Heaps, and Tries for Offline File Sharing."),
            ("Algorithms/quick_sort.py", b"def quick_sort(arr): ... # DSA Implementation"),
            ("Algorithms/merge_sort.py", b"def merge_sort(arr): ... # Divide & Conquer"),
            ("Projects/offline_lan_presentation.pptx", b"PPTX_PRESENTATION_SLIDES_OFFLINE" * 500)
        ]

        for rel_path, content in sample_files:
            full = os.path.join(shared_dir, rel_path.replace("/", os.sep))
            if not os.path.exists(full):
                with open(full, "wb") as f:
                    f.write(content)

        # Register default shared folder
        StorageManager.add_shared_folder(shared_dir, "Demo Shared Directory")

        # Scan files to populate FileTree, FileHashIndex, FilenameTrie, and SQLite
        scanner.scan_all()

        # 2. Register Virtual Peer Laptops in NetworkGraph & SQLite
        now = time.time()
        # Laptop B (Peer Client)
        discovery.register_peer(
            device_id="dev_laptop_b",
            device_name="Laptop-B (Client)",
            ip_address="192.168.1.11",
            port=8000,
            trusted=1
        )
        # Laptop C (Storage Node)
        discovery.register_peer(
            device_id="dev_laptop_c",
            device_name="Laptop-C (Sync Peer)",
            ip_address="192.168.1.12",
            port=8000,
            trusted=0
        )

        # Add network edges
        discovery.graph.add_edge(config.device_id, "dev_laptop_b", latency_ms=1.8, bandwidth_mbps=150.0)
        discovery.graph.add_edge("dev_laptop_b", "dev_laptop_c", latency_ms=2.5, bandwidth_mbps=100.0)
        discovery.graph.add_edge(config.device_id, "dev_laptop_c", latency_ms=3.2, bandwidth_mbps=100.0)

        # 3. Enqueue Sample Transfers across Priority Levels (Critical=0, High=1, Normal=2, Low=3)
        tx_manager.enqueue_transfer(
            file_name="urgent_security_patch.bin",
            size=15 * 1024 * 1024,
            source_device="Laptop-A",
            destination_device="Laptop-B",
            direction="UPLOAD",
            priority=0  # CRITICAL
        )
        tx_manager.enqueue_transfer(
            file_name="offline_lan_presentation.pptx",
            size=45 * 1024 * 1024,
            source_device="Laptop-B",
            destination_device="Laptop-A",
            direction="DOWNLOAD",
            priority=1  # HIGH
        )
        tx_manager.enqueue_transfer(
            file_name="lecture_notes.txt",
            size=512 * 1024,
            source_device="Laptop-A",
            destination_device="Laptop-C",
            direction="UPLOAD",
            priority=2  # NORMAL
        )
        tx_manager.enqueue_transfer(
            file_name="dataset_backup.zip",
            size=120 * 1024 * 1024,
            source_device="Laptop-C",
            destination_device="Laptop-A",
            direction="DOWNLOAD",
            priority=3  # LOW (Background)
        )

        # 4. Create a Sample Sync Conflict
        db.execute_write(
            """
            INSERT INTO sync_conflicts (
                file_path, local_hash, remote_hash, local_modified, remote_modified, status, created_at
            ) VALUES (?, ?, ?, ?, ?, 'PENDING', ?)
            """,
            (
                "Documents/project_roadmap.docx",
                "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90",
                "f9e8d7c6b5a432109876543210fedcba9876543210fedcba9876543210fedcba",
                now - 300,
                now - 120,
                now
            )
        )

        config.update(demo_mode=True)
        AppLogger.log("DEMO_READY", status="SUCCESS", message="Demo mode initialized with virtual peers, priority queue, and sync conflicts.")

        return {
            "success": True,
            "message": "Demo mode data successfully loaded.",
            "mode": "DEMO MODE",
            "devices": 3,
            "sample_files": len(sample_files)
        }
