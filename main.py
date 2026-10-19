"""
main.py
Root entrypoint for Vercel and local development.
Exposes the root FastAPI application instance.
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.main import app

if __name__ == "__main__":
    import uvicorn
    from backend.core.config import get_config
    cfg = get_config()
    uvicorn.run("main:app", host="0.0.0.0", port=cfg.port, reload=False)
