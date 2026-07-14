"""PyInstaller entrypoint for bookmarks-mcp HTTP sidecar."""

import _strptime  # noqa: F401 -- PyInstaller must bundle this eagerly
import os
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    base = Path(sys._MEIPASS)
    sys.path.insert(0, str(base / "src"))
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

os.environ.setdefault("MCP_TRANSPORT", "http")
os.environ.setdefault("MCP_PORT", "10803")

from browser_bookmarks_tools.mcp_server import main

if __name__ == "__main__":
    if "--http" not in sys.argv:
        sys.argv.append("--http")
    main()
