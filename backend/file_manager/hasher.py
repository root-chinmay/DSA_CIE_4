"""
backend/file_manager/hasher.py
Cryptographic SHA-256 Hashing Engine with Streaming Chunk Support.

Prevents loading large files into RAM by reading buffered 64KB blocks.
Time Complexity: O(File Size / Block Size)
Space Complexity: O(Block Size) = 64KB constant RAM footprint.
"""

import hashlib
import os
from typing import Optional


class StreamingHasher:
    """Computes SHA-256 digests in fixed-size memory chunks."""

    BLOCK_SIZE = 65536  # 64 KB chunk

    @classmethod
    def hash_file(cls, filepath: str) -> Optional[str]:
        """
        Calculates SHA-256 hash of a file path without loading into memory.
        Returns hex digest string or None if unreadable.
        """
        if not os.path.isfile(filepath):
            return None

        sha256 = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                while True:
                    data = f.read(cls.BLOCK_SIZE)
                    if not data:
                        break
                    sha256.update(data)
            return sha256.hexdigest()
        except Exception as e:
            print(f"[Hasher Error] Failed to hash {filepath}: {e}")
            return None

    @classmethod
    def hash_bytes(cls, data_bytes: bytes) -> str:
        """Computes SHA-256 digest of in-memory bytes."""
        sha256 = hashlib.sha256()
        sha256.update(data_bytes)
        return sha256.hexdigest()

    @classmethod
    def verify_file_hash(cls, filepath: str, expected_hash: str) -> bool:
        """
        Verifies downloaded file integrity against expected SHA-256 digest.
        """
        actual_hash = cls.hash_file(filepath)
        if not actual_hash or not expected_hash:
            return False
        return actual_hash.lower() == expected_hash.lower()
