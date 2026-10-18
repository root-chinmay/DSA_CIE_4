"""
api/index.py
Standard Vercel serverless function entrypoint for FastAPI.
Exposes the root FastAPI application instance.
"""

import os
import sys

# Ensure root workspace directory is in sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.main import app
