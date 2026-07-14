# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import copy_metadata

datas = [("src/browser_bookmarks_tools", "browser_bookmarks_tools")]
for pkg in (
    "fastmcp",
    "fastapi",
    "uvicorn",
    "pydantic",
    "starlette",
    "httpx",
    "aiohttp",
    "aiosqlite",
    "prefab_ui",
):
    datas += copy_metadata(pkg)

hiddenimports = [

    "_datetime",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.asyncio",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.httptools_impl",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "browser_bookmarks_tools.tools.browser_bookmarks",
    "browser_bookmarks_tools.tools.chrome_profiles",
    "browser_bookmarks_tools.tools.firefox_backup",
    "browser_bookmarks_tools.tools.firefox_bookmarks",
    "browser_bookmarks_tools.tools.firefox_curated",
    "browser_bookmarks_tools.tools.firefox_profiles",
    "browser_bookmarks_tools.tools.firefox_tagging",
    "browser_bookmarks_tools.tools.firefox_utils",
    "browser_bookmarks_tools.tools.sync_tools",
    "browser_bookmarks_tools.tools.firefox.ai_portmanteau",
    "browser_bookmarks_tools.tools.help_tools",
    "browser_bookmarks_tools.transport",
    "browser_bookmarks_tools.web",
    "browser_bookmarks_tools.ai",
    "_strptime",
]

a = Analysis(
    ["run_server.py"],
    pathex=["src"],
    binaries=[],
    
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    
    hooksconfig={},
    runtime_hooks=[],
    excludes=["torch", "transformers", "tensorflow"],
    noarchive=True,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    
    name="bookmarks-mcp-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)





