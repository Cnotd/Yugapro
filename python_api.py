#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Entry point for the thesis-aligned Flask REST API.

The implementation now lives in `src.web_api`:
- routes: HTTP/JSON API surface
- services: task scheduling, upload storage, assessment pipeline
- persistence/auth: SQLite and token/session helpers
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from src.web_api import create_app


app = create_app()


def main() -> None:
    host = os.environ.get("YOGA_API_HOST", "0.0.0.0")
    port = int(os.environ.get("YOGA_API_PORT", "5000"))
    debug = os.environ.get("YOGA_API_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}

    print("\n" + "=" * 56)
    print("Starting Yoga Assessment Flask REST API")
    print(f"Address: http://{host}:{port}")
    print("API prefix: /api")
    print("=" * 56 + "\n")
    app.run(host=host, port=port, debug=debug, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
