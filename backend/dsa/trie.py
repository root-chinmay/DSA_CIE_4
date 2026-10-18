"""
backend/dsa/trie.py
Prefix Tree (Trie) Data Structure for Fast Filename Search & Autocomplete.

Time Complexity:
- Insertion: O(L) where L is length of filename
- Prefix Search: O(P + K) where P is prefix length and K is number of matched nodes
- Autocomplete: O(P + K)
- Space Complexity: O(ALPHABET_SIZE * L * N) where N is number of unique filename tokens
"""

from typing import Dict, List, Optional, Any, Set
import re


class TrieNode:
    """A node in the Filename Trie."""

    def __init__(self, char: str = ""):
        self.char: str = char
        self.children: Dict[str, 'TrieNode'] = {}
        self.is_end_of_word: bool = False
        self.file_entries: List[Dict[str, Any]] = []  # Stores matching file metadata
        self.frequency: int = 0


class FilenameTrie:
    """
    Trie specialized for real-time filename prefix search and autocomplete.
    Splits filenames into alphanumeric tokens for multi-keyword prefix matching.
    """

    def __init__(self):
        self.root: TrieNode = TrieNode()
        self.total_words: int = 0
        self.total_nodes: int = 1

    def _tokenize(self, text: str) -> List[str]:
        """
        Extracts lowercase search tokens from filenames.
        Example: "Annual_Report-2026.final.pdf" -> ["annual", "report", "2026", "final", "pdf", "annual_report-2026.final.pdf"]
        """
        clean = text.lower().strip()
        tokens = set(re.split(r'[^a-z0-9]+', clean))
        tokens.discard("")
        tokens.add(clean)
        return list(tokens)

    def insert(self, filename: str, file_metadata: Dict[str, Any]) -> None:
        """
        Inserts filename and all its constituent tokens into the Trie.
        Time Complexity: O(Sum of L_i for each token)
        """
        tokens = self._tokenize(filename)
        for token in tokens:
            self._insert_token(token, file_metadata)

    def _insert_token(self, token: str, file_metadata: Dict[str, Any]) -> None:
        current = self.root
        for char in token:
            if char not in current.children:
                new_node = TrieNode(char)
                current.children[char] = new_node
                self.total_nodes += 1
            current = current.children[char]

        if not current.is_end_of_word:
            current.is_end_of_word = True
            self.total_words += 1

        # Prevent duplicate entries for the same file under this token
        file_id = file_metadata.get("file_id") or file_metadata.get("id")
        if not any((e.get("file_id") or e.get("id")) == file_id for e in current.file_entries):
            current.file_entries.append(file_metadata)

    def search_prefix(self, prefix: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Finds all files matching the given prefix.
        Time Complexity: O(P + K) where P is prefix length, K is subtree size.
        """
        clean_prefix = prefix.lower().strip()
        if not clean_prefix:
            return []

        # 1. Traverse to the prefix end node
        current = self.root
        for char in clean_prefix:
            if char not in current.children:
                return []
            current = current.children[char]

        # 2. Collect all descendant file entries via DFS
        results_map: Dict[str, Dict[str, Any]] = {}
        self._collect_entries(current, results_map, max_results)
        return list(results_map.values())

    def _collect_entries(
        self,
        node: TrieNode,
        results_map: Dict[str, Dict[str, Any]],
        max_results: int
    ) -> None:
        if len(results_map) >= max_results:
            return

        if node.is_end_of_word:
            for entry in node.file_entries:
                fid = entry.get("file_id") or entry.get("id") or entry.get("relative_path")
                if fid and fid not in results_map:
                    results_map[fid] = entry
                    if len(results_map) >= max_results:
                        return

        for child in node.children.values():
            self._collect_entries(child, results_map, max_results)

    def autocomplete(self, prefix: str, limit: int = 10) -> List[str]:
        """
        Returns a list of filename word suggestions for search input.
        """
        clean_prefix = prefix.lower().strip()
        if not clean_prefix:
            return []

        current = self.root
        for char in clean_prefix:
            if char not in current.children:
                return []
            current = current.children[char]

        suggestions: List[str] = []
        self._collect_words(current, clean_prefix, suggestions, limit)
        return suggestions

    def _collect_words(
        self,
        node: TrieNode,
        current_word: str,
        suggestions: List[str],
        limit: int
    ) -> None:
        if len(suggestions) >= limit:
            return

        if node.is_end_of_word:
            suggestions.append(current_word)

        for char, child in sorted(node.children.items()):
            self._collect_words(child, current_word + char, suggestions, limit)

    def remove_file(self, file_id: str) -> None:
        """
        Removes file occurrences from all Trie nodes.
        """
        self._remove_from_node(self.root, file_id)

    def _remove_from_node(self, node: TrieNode, file_id: str) -> None:
        if node.is_end_of_word:
            node.file_entries = [
                e for e in node.file_entries
                if (e.get("file_id") or e.get("id")) != file_id
            ]
        for child in node.children.values():
            self._remove_from_node(child, file_id)

    def get_stats(self) -> Dict[str, Any]:
        """Returns statistics for the Trie."""
        return {
            "total_words": self.total_words,
            "total_nodes": self.total_nodes
        }

    def to_visual_dict(self, max_depth: int = 3) -> Dict[str, Any]:
        """
        Generates serializable subtree dictionary for DSA Visualizer.
        """
        def serialize_node(node: TrieNode, depth: int) -> Dict[str, Any]:
            children_list = []
            if depth < max_depth:
                for char, child in sorted(node.children.items()):
                    children_list.append(serialize_node(child, depth + 1))
            return {
                "char": node.char or "ROOT",
                "is_word": node.is_end_of_word,
                "matches_count": len(node.file_entries),
                "children": children_list
            }

        return serialize_node(self.root, 0)
