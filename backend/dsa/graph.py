"""
backend/dsa/graph.py
Network Graph representation of LAN devices using Adjacency Lists.

Time Complexity:
- Add Node: O(1)
- Add Edge: O(1)
- BFS Traversal: O(V + E)
- DFS Traversal: O(V + E)
- Shortest Path (Dijkstra): O((V + E) log V)
Space Complexity: O(V + E) where V is number of devices and E is LAN links.
"""

from typing import Dict, List, Optional, Set, Tuple, Any
from collections import deque
import heapq
import time


class DeviceNode:
    """Represents a device node in the LAN network graph."""

    def __init__(
        self,
        device_id: str,
        device_name: str,
        ip_address: str,
        port: int = 8000,
        status: str = "online",
        is_self: bool = False
    ):
        self.device_id: str = device_id
        self.device_name: str = device_name
        self.ip_address: str = ip_address
        self.port: int = port
        self.status: str = status  # "online", "offline", "unpaired"
        self.is_self: bool = is_self
        self.last_seen: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "device_name": self.device_name,
            "ip_address": self.ip_address,
            "port": self.port,
            "status": self.status,
            "is_self": self.is_self,
            "last_seen": self.last_seen
        }


class NetworkEdge:
    """Represents a connection link between two devices on the LAN."""

    def __init__(self, target_id: str, latency_ms: float = 1.0, bandwidth_mbps: float = 100.0):
        self.target_id: str = target_id
        self.latency_ms: float = latency_ms
        self.bandwidth_mbps: float = bandwidth_mbps


class NetworkGraph:
    """
    Adjacency List Graph for managing LAN peer network topology.
    Supports BFS/DFS traversals, shortest path calculation, and topology visualization.
    """

    def __init__(self):
        self.nodes: Dict[str, DeviceNode] = {}
        self.adj: Dict[str, List[NetworkEdge]] = {}

    def add_node(self, device: DeviceNode) -> None:
        """Adds a device node to the graph."""
        self.nodes[device.device_id] = device
        if device.device_id not in self.adj:
            self.adj[device.device_id] = []

    def remove_node(self, device_id: str) -> None:
        """Removes a device node and all incident edges."""
        if device_id in self.nodes:
            del self.nodes[device_id]
        if device_id in self.adj:
            del self.adj[device_id]

        for edges in self.adj.values():
            edges[:] = [edge for edge in edges if edge.target_id != device_id]

    def add_edge(
        self,
        u_id: str,
        v_id: str,
        latency_ms: float = 1.0,
        bandwidth_mbps: float = 100.0,
        bidirectional: bool = True
    ) -> None:
        """
        Adds a network edge between devices u and v.
        Time Complexity: O(1)
        """
        if u_id in self.nodes and v_id in self.nodes:
            # Check if edge already exists
            existing_u = [e for e in self.adj[u_id] if e.target_id == v_id]
            if existing_u:
                existing_u[0].latency_ms = latency_ms
                existing_u[0].bandwidth_mbps = bandwidth_mbps
            else:
                self.adj[u_id].append(NetworkEdge(v_id, latency_ms, bandwidth_mbps))

            if bidirectional:
                existing_v = [e for e in self.adj[v_id] if e.target_id == u_id]
                if existing_v:
                    existing_v[0].latency_ms = latency_ms
                    existing_v[0].bandwidth_mbps = bandwidth_mbps
                else:
                    self.adj[v_id].append(NetworkEdge(u_id, latency_ms, bandwidth_mbps))

    def bfs(self, start_id: str) -> List[Dict[str, Any]]:
        """
        Breadth-First Search traversal starting from start_id.
        Computes hop distances to all reachable devices.
        Time Complexity: O(V + E)
        """
        if start_id not in self.nodes:
            return []

        visited: Set[str] = {start_id}
        queue: deque = deque([(start_id, 0)])
        traversal: List[Dict[str, Any]] = []

        while queue:
            current_id, hops = queue.popleft()
            node = self.nodes[current_id]
            traversal.append({
                "device_id": current_id,
                "device_name": node.device_name,
                "hops": hops,
                "ip": node.ip_address
            })

            for edge in self.adj.get(current_id, []):
                if edge.target_id not in visited and edge.target_id in self.nodes:
                    visited.add(edge.target_id)
                    queue.append((edge.target_id, hops + 1))

        return traversal

    def dfs(self, start_id: str) -> List[Dict[str, Any]]:
        """
        Depth-First Search traversal starting from start_id.
        Time Complexity: O(V + E)
        """
        if start_id not in self.nodes:
            return []

        visited: Set[str] = set()
        traversal: List[Dict[str, Any]] = []

        def _dfs_helper(node_id: str, depth: int) -> None:
            visited.add(node_id)
            node = self.nodes[node_id]
            traversal.append({
                "device_id": node_id,
                "device_name": node.device_name,
                "depth": depth,
                "ip": node.ip_address
            })
            for edge in self.adj.get(node_id, []):
                if edge.target_id not in visited and edge.target_id in self.nodes:
                    _dfs_helper(edge.target_id, depth + 1)

        _dfs_helper(start_id, 0)
        return traversal

    def shortest_path(self, start_id: str, end_id: str) -> Optional[Dict[str, Any]]:
        """
        Dijkstra's Shortest Path algorithm based on connection latency.
        Time Complexity: O((V + E) log V)
        """
        if start_id not in self.nodes or end_id not in self.nodes:
            return None

        # Min-heap priority queue: (cumulative_latency, current_node_id, path_list)
        pq: List[Tuple[float, str, List[str]]] = [(0.0, start_id, [start_id])]
        min_cost: Dict[str, float] = {start_id: 0.0}

        while pq:
            cost, current, path = heapq.heappop(pq)

            if current == end_id:
                return {
                    "start_id": start_id,
                    "end_id": end_id,
                    "path_ids": path,
                    "path_names": [self.nodes[nid].device_name for nid in path],
                    "total_latency_ms": round(cost, 2),
                    "hop_count": len(path) - 1
                }

            if cost > min_cost.get(current, float('inf')):
                continue

            for edge in self.adj.get(current, []):
                next_node = edge.target_id
                if next_node not in self.nodes:
                    continue
                new_cost = cost + edge.latency_ms
                if new_cost < min_cost.get(next_node, float('inf')):
                    min_cost[next_node] = new_cost
                    heapq.heappush(pq, (new_cost, next_node, path + [next_node]))

        return None

    def get_topology(self) -> Dict[str, Any]:
        """
        Returns full graph serialized for visual rendering.
        """
        nodes_data = [node.to_dict() for node in self.nodes.values()]
        edges_data = []
        seen_edges: Set[Tuple[str, str]] = set()

        for source_id, edge_list in self.adj.items():
            for edge in edge_list:
                edge_pair = tuple(sorted([source_id, edge.target_id]))
                if edge_pair not in seen_edges:
                    seen_edges.add(edge_pair)
                    edges_data.append({
                        "source": source_id,
                        "target": edge.target_id,
                        "latency_ms": edge.latency_ms,
                        "bandwidth_mbps": edge.bandwidth_mbps
                    })

        return {
            "nodes": nodes_data,
            "edges": edges_data,
            "total_devices": len(nodes_data),
            "total_links": len(edges_data)
        }
