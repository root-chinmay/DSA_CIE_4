"""
tests/test_dsa.py
Comprehensive unit tests for all DSA data structures.
"""

import unittest
import os
import sys

# Ensure backend is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.dsa.tree import FileTree, FileNode
from backend.dsa.hash_table import HashTable, FileHashIndex
from backend.dsa.trie import FilenameTrie
from backend.dsa.queue import TransferQueue
from backend.dsa.priority_queue import PriorityHeap
from backend.dsa.graph import NetworkGraph, DeviceNode
from backend.dsa.sorting import Sorter


class TestFileTree(unittest.TestCase):

    def setUp(self):
        self.tree = FileTree(root_name="SharedFolder")

    def test_insert_and_find(self):
        self.tree.insert("Documents/report.pdf", is_dir=False, size=1024, hash_val="hash123")
        self.tree.insert("Documents/notes.txt", is_dir=False, size=512, hash_val="hash456")
        self.tree.insert("Projects/Code/app.py", is_dir=False, size=2048, hash_val="hash789")

        # Find file node
        node = self.tree.find("Documents/report.pdf")
        self.assertIsNotNone(node)
        self.assertEqual(node.name, "report.pdf")
        self.assertEqual(node.size, 1024)
        self.assertEqual(node.hash_val, "hash123")
        self.assertFalse(node.is_dir)

        # Find intermediate directory node
        doc_node = self.tree.find("Documents")
        self.assertIsNotNone(doc_node)
        self.assertTrue(doc_node.is_dir)
        self.assertEqual(doc_node.name, "Documents")

        # Find non-existent path
        self.assertIsNone(self.tree.find("NonExistent/file.txt"))

    def test_subtree_size_calculation(self):
        self.tree.insert("Docs/f1.txt", is_dir=False, size=100)
        self.tree.insert("Docs/f2.txt", is_dir=False, size=200)
        self.tree.insert("Images/photo.jpg", is_dir=False, size=500)

        docs_node = self.tree.find("Docs")
        self.assertEqual(docs_node.size, 300)
        self.assertEqual(self.tree.root.size, 800)

    def test_delete_node(self):
        self.tree.insert("Docs/f1.txt", is_dir=False, size=100)
        self.tree.insert("Docs/f2.txt", is_dir=False, size=200)

        deleted = self.tree.delete("Docs/f1.txt")
        self.assertTrue(deleted)
        self.assertIsNone(self.tree.find("Docs/f1.txt"))
        self.assertIsNotNone(self.tree.find("Docs/f2.txt"))

    def test_dfs_and_bfs(self):
        self.tree.insert("A/b.txt", size=10)
        self.tree.insert("A/c.txt", size=20)
        self.tree.insert("D/e.txt", size=30)

        dfs_names = [n.name for n in self.tree.dfs()]
        self.assertIn("SharedFolder", dfs_names)
        self.assertIn("A", dfs_names)
        self.assertIn("b.txt", dfs_names)

        bfs_levels = [level for level, _ in self.tree.bfs()]
        self.assertEqual(bfs_levels[0], 0)  # root level 0
        self.assertTrue(max(bfs_levels) >= 2)

    def test_search_by_name(self):
        self.tree.insert("Docs/annual_report.pdf")
        self.tree.insert("Docs/project_report.docx")
        self.tree.insert("Images/sunset.jpg")

        results = self.tree.search_by_name("report")
        self.assertEqual(len(results), 2)
        names = [r.name for r in results]
        self.assertIn("annual_report.pdf", names)
        self.assertIn("project_report.docx", names)


class TestHashTable(unittest.TestCase):

    def test_put_and_get(self):
        ht = HashTable(initial_capacity=4)
        ht.put("key1", "value1")
        ht.put("key2", "value2")
        ht.put("key3", "value3")

        self.assertEqual(ht.get("key1"), "value1")
        self.assertEqual(ht.get("key2"), "value2")
        self.assertEqual(ht.get("key3"), "value3")
        self.assertIsNone(ht.get("key4"))

    def test_dynamic_resizing_and_collisions(self):
        ht = HashTable(initial_capacity=4, load_factor_threshold=0.75)
        self.assertEqual(ht.capacity, 4)

        for i in range(20):
            ht.put(f"item_{i}", i * 10)

        self.assertEqual(ht.size, 20)
        self.assertGreater(ht.capacity, 4)  # Resized
        for i in range(20):
            self.assertEqual(ht.get(f"item_{i}"), i * 10)

    def test_delete(self):
        ht = HashTable(initial_capacity=8)
        ht.put("del_me", 999)
        self.assertTrue(ht.contains("del_me"))
        self.assertTrue(ht.delete("del_me"))
        self.assertFalse(ht.contains("del_me"))
        self.assertFalse(ht.delete("del_me"))

    def test_file_hash_index(self):
        idx = FileHashIndex()
        idx.index_file({"file_id": "1", "hash": "abc", "relative_path": "a.txt", "size": 100})
        idx.index_file({"file_id": "2", "hash": "abc", "relative_path": "b.txt", "size": 100})
        idx.index_file({"file_id": "3", "hash": "xyz", "relative_path": "c.txt", "size": 200})

        # O(1) ID lookup
        self.assertEqual(idx.get_by_id("1")["relative_path"], "a.txt")
        # O(1) Path lookup
        self.assertEqual(idx.get_by_path("c.txt")["hash"], "xyz")

        # Duplicate detection by SHA-256
        duplicates = idx.find_duplicates()
        self.assertEqual(len(duplicates), 1)
        self.assertEqual(duplicates[0]["hash"], "abc")
        self.assertEqual(duplicates[0]["count"], 2)


class TestFilenameTrie(unittest.TestCase):

    def setUp(self):
        self.trie = FilenameTrie()
        self.trie.insert("project_report_2026.pdf", {"file_id": "1", "name": "project_report_2026.pdf"})
        self.trie.insert("project_presentation.pptx", {"file_id": "2", "name": "project_presentation.pptx"})
        self.trie.insert("annual_budget.xlsx", {"file_id": "3", "name": "annual_budget.xlsx"})

    def test_prefix_search(self):
        results = self.trie.search_prefix("proj")
        self.assertEqual(len(results), 2)
        names = [r["name"] for r in results]
        self.assertIn("project_report_2026.pdf", names)
        self.assertIn("project_presentation.pptx", names)

    def test_subtoken_search(self):
        # "report" is a subtoken in "project_report_2026.pdf"
        results = self.trie.search_prefix("repo")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "project_report_2026.pdf")

    def test_autocomplete(self):
        suggestions = self.trie.autocomplete("pro")
        self.assertTrue(len(suggestions) > 0)
        self.assertTrue(any(s.startswith("pro") for s in suggestions))


class TestTransferQueue(unittest.TestCase):

    def test_fifo_ordering(self):
        q = TransferQueue()
        self.assertTrue(q.is_empty())

        q.enqueue({"id": "t1", "file": "f1.txt"})
        q.enqueue({"id": "t2", "file": "f2.txt"})
        q.enqueue({"id": "t3", "file": "f3.txt"})

        self.assertEqual(q.size(), 3)
        self.assertEqual(q.peek()["id"], "t1")

        # First In First Out
        self.assertEqual(q.dequeue()["id"], "t1")
        self.assertEqual(q.dequeue()["id"], "t2")
        self.assertEqual(q.dequeue()["id"], "t3")
        self.assertIsNone(q.dequeue())
        self.assertTrue(q.is_empty())

    def test_remove_by_id(self):
        q = TransferQueue()
        q.enqueue({"id": "t1", "file": "f1.txt"})
        q.enqueue({"id": "t2", "file": "f2.txt"})
        q.enqueue({"id": "t3", "file": "f3.txt"})

        # Remove middle element
        removed = q.remove("t2")
        self.assertIsNotNone(removed)
        self.assertEqual(removed["id"], "t2")
        self.assertEqual(q.size(), 2)

        items = [i["id"] for i in q.to_list()]
        self.assertEqual(items, ["t1", "t3"])


class TestPriorityHeap(unittest.TestCase):

    def test_priority_scheduling(self):
        heap = PriorityHeap()
        # 0=Critical, 1=High, 2=Normal, 3=Low
        heap.push({"file": "background_sync.zip"}, priority=3, item_id="sync")
        heap.push({"file": "normal_doc.pdf"}, priority=2, item_id="normal")
        heap.push({"file": "urgent_patch.bin"}, priority=0, item_id="critical")
        heap.push({"file": "quick_photo.jpg"}, priority=1, item_id="high")

        # Extraction must yield in priority order: 0, 1, 2, 3
        self.assertEqual(heap.pop()["file"], "urgent_patch.bin")      # Critical (0)
        self.assertEqual(heap.pop()["file"], "quick_photo.jpg")       # High (1)
        self.assertEqual(heap.pop()["file"], "normal_doc.pdf")        # Normal (2)
        self.assertEqual(heap.pop()["file"], "background_sync.zip")   # Low (3)
        self.assertTrue(heap.is_empty())

    def test_priority_elevation(self):
        heap = PriorityHeap()
        heap.push({"file": "task_low.txt"}, priority=3, item_id="t_low")
        heap.push({"file": "task_norm.txt"}, priority=2, item_id="t_norm")

        # Elevate task_low from Low (3) to Critical (0)
        elevated = heap.update_priority("t_low", 0)
        self.assertTrue(elevated)

        # Now task_low must come out first!
        self.assertEqual(heap.pop()["file"], "task_low.txt")
        self.assertEqual(heap.pop()["file"], "task_norm.txt")


class TestNetworkGraph(unittest.TestCase):

    def test_topology_and_traversals(self):
        graph = NetworkGraph()
        n_a = DeviceNode("node_a", "Laptop-A", "192.168.1.10", is_self=True)
        n_b = DeviceNode("node_b", "Laptop-B", "192.168.1.11")
        n_c = DeviceNode("node_c", "Laptop-C", "192.168.1.12")
        n_d = DeviceNode("node_d", "Laptop-D", "192.168.1.13")

        graph.add_node(n_a)
        graph.add_node(n_b)
        graph.add_node(n_c)
        graph.add_node(n_d)

        # A - B - C
        # |       |
        # +--- D -+
        graph.add_edge("node_a", "node_b", latency_ms=2.0)
        graph.add_edge("node_b", "node_c", latency_ms=4.0)
        graph.add_edge("node_a", "node_d", latency_ms=1.0)
        graph.add_edge("node_d", "node_c", latency_ms=2.0)

        # BFS from node_a
        bfs_res = graph.bfs("node_a")
        self.assertEqual(len(bfs_res), 4)
        hops_map = {item["device_id"]: item["hops"] for item in bfs_res}
        self.assertEqual(hops_map["node_a"], 0)
        self.assertEqual(hops_map["node_b"], 1)
        self.assertEqual(hops_map["node_d"], 1)
        self.assertEqual(hops_map["node_c"], 2)

        # Shortest path Dijkstra from node_a to node_c:
        # Route 1: A -> B -> C = 2 + 4 = 6ms
        # Route 2: A -> D -> C = 1 + 2 = 3ms (Shortest!)
        sp = graph.shortest_path("node_a", "node_c")
        self.assertIsNotNone(sp)
        self.assertEqual(sp["path_ids"], ["node_a", "node_d", "node_c"])
        self.assertEqual(sp["total_latency_ms"], 3.0)


class TestSortingAlgorithms(unittest.TestCase):

    def setUp(self):
        self.files = [
            {"name": "zebra.png", "size": 500, "modified_time": 100},
            {"name": "apple.txt", "size": 1500, "modified_time": 300},
            {"name": "mango.pdf", "size": 200, "modified_time": 200},
            {"name": "banana.docx", "size": 800, "modified_time": 400}
        ]

    def test_merge_sort_by_name(self):
        sorted_files, metrics = Sorter.sort(self.files, by="name", algorithm="merge_sort")
        names = [f["name"] for f in sorted_files]
        self.assertEqual(names, ["apple.txt", "banana.docx", "mango.pdf", "zebra.png"])
        self.assertEqual(metrics["algorithm"], "Merge Sort")
        self.assertGreater(metrics["comparisons"], 0)

    def test_quick_sort_by_size(self):
        sorted_files, metrics = Sorter.sort(self.files, by="size", algorithm="quick_sort")
        sizes = [f["size"] for f in sorted_files]
        self.assertEqual(sizes, [200, 500, 800, 1500])
        self.assertEqual(metrics["algorithm"], "Quick Sort")

    def test_reverse_sort_by_date(self):
        sorted_files, _ = Sorter.sort(self.files, by="modified_time", algorithm="merge_sort", reverse=True)
        dates = [f["modified_time"] for f in sorted_files]
        self.assertEqual(dates, [400, 300, 200, 100])


if __name__ == "__main__":
    unittest.main()
