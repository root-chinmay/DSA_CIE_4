"""
tests/test_api_endpoints.py
Integration tests for backend FastAPI endpoints using TestClient.
"""

import unittest
import os
import sys

# Ensure root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.main import app as main_app
from backend.demo.demo_simulator import DemoSimulator


class TestAPIEndpoints(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(main_app)
        # Populate demo dataset for consistent tests
        DemoSimulator.populate_demo_data()

    def test_ping(self):
        resp = self.client.get("/api/devices/ping")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "online")
        self.assertIn("device_id", data)
        self.assertIn("pairing_code", data)

    def test_network_diagnostics(self):
        resp = self.client.get("/api/devices/network")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("local_ip", data)
        self.assertIn("diagnostics", data)
        self.assertTrue(len(data["diagnostics"]) >= 4)

    def test_list_files_and_tree(self):
        # Flat list
        resp = self.client.get("/api/files")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("files", data)
        self.assertIn("sort_metrics", data)
        self.assertTrue(len(data["files"]) > 0)

        # Hierarchical Tree
        resp_tree = self.client.get("/api/files/tree")
        self.assertEqual(resp_tree.status_code, 200)
        tree_data = resp_tree.json()
        self.assertIn("children", tree_data)

    def test_trie_search_and_autocomplete(self):
        resp = self.client.get("/api/files/search?q=report")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("results", data)
        self.assertTrue(any("report" in r["name"].lower() for r in data["results"]))

        # Autocomplete
        resp_auto = self.client.get("/api/files/search?q=rep&autocomplete=true")
        self.assertEqual(resp_auto.status_code, 200)
        auto_data = resp_auto.json()
        self.assertIn("suggestions", auto_data)

    def test_duplicate_detection(self):
        resp = self.client.get("/api/files/duplicates")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("duplicate_groups", data)
        # We seeded report_final.pdf and report_final_copy.pdf with identical content
        self.assertTrue(data["total_groups"] >= 1)

    def test_transfers_queue_and_priority_elevation(self):
        resp = self.client.get("/api/transfers")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("fifo_queue", data)
        self.assertIn("priority_heap", data)
        self.assertIn("heap_tree", data)

        # Enqueue new transfer
        payload = {
            "file_name": "api_test_file.dat",
            "size": 1048576,
            "source_device": "Laptop-A",
            "destination_device": "Laptop-B",
            "direction": "DOWNLOAD",
            "priority": 2
        }
        create_resp = self.client.post("/api/transfers", json=payload)
        self.assertEqual(create_resp.status_code, 200)
        tx_data = create_resp.json()
        tx_id = tx_data["task"]["transfer_id"]

        # Elevate priority to CRITICAL (0)
        elevate_resp = self.client.post(f"/api/transfers/{tx_id}/priority", json={"priority": 0})
        self.assertEqual(elevate_resp.status_code, 200)

    def test_dsa_overview(self):
        resp = self.client.get("/api/dsa/overview")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("complexities", data)
        self.assertEqual(len(data["complexities"]), 8)  # 8 core DSA structures documented!

    def test_sync_diff(self):
        resp = self.client.get("/api/sync/diff")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("diff_matrix", data)
        self.assertTrue(len(data["diff_matrix"]) > 0)


if __name__ == "__main__":
    unittest.main()
