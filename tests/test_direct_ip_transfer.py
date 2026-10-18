"""
tests/test_direct_ip_transfer.py
Unit and integration tests for direct offline IP file transfer,
subnet scanning, and mobile connection info endpoints.
"""

import unittest
from fastapi.testclient import TestClient
from backend.main import app
from backend.networking.ip_detector import IPDetector


class TestDirectIPTransfer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_mobile_info_endpoint(self):
        """Tests that /api/devices/mobile-info returns valid connection URL and pairing code."""
        resp = self.client.get("/api/devices/mobile-info")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("local_ip", data)
        self.assertIn("port", data)
        self.assertIn("url", data)
        self.assertIn("pairing_code", data)
        self.assertTrue(data["url"].startswith("http://"))

    def test_scan_subnet_endpoint(self):
        """Tests that /api/devices/scan-subnet runs without error and returns structured device list."""
        resp = self.client.get("/api/devices/scan-subnet")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("local_ip", data)
        self.assertIn("subnet", data)
        self.assertIn("devices_found", data)
        self.assertIn("total_found", data)
        self.assertIsInstance(data["devices_found"], list)

    def test_ping_remote_ip_endpoint(self):
        """Tests /api/devices/ping-ip reachability test."""
        resp = self.client.post("/api/devices/ping-ip", json={"ip_address": "127.0.0.1", "port": 8000})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("reachable", data)
        self.assertIn("has_lan_sync", data)

    def test_direct_ip_transfer_enqueue(self):
        """Tests submitting a direct IP transfer task to PriorityHeap and FIFO Queue."""
        payload = {
            "target_ip": "192.168.1.99",
            "target_port": 8000,
            "file_name": "test_direct_doc.pdf",
            "direction": "UPLOAD",
            "priority": 0  # CRITICAL
        }
        resp = self.client.post("/api/transfers/direct-ip", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertIn("task", data)
        self.assertEqual(data["task"]["file_name"], "test_direct_doc.pdf")
        self.assertEqual(data["task"]["priority"], 0)
        self.assertEqual(data["task"]["priority_name"], "CRITICAL")


if __name__ == "__main__":
    unittest.main()
