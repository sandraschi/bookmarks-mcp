# Browser Bookmarks Tools (MCP)

<p align="center">
  <a href="https://github.com/casey/just"><img src="https://img.shields.io/badge/just-ready_to_go-7c5cfc?style=flat-square&logo=just&logoColor=white" alt="Just"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.13+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/PrefectHQ/fastmcp"><img src="https://img.shields.io/badge/FastMCP-3.3-7c5cfc?style=flat-square" alt="FastMCP"></a>
</p>


> 📖 **[Installation Guide](INSTALL.md)** — quick start, manual setup, and troubleshooting

FastMCP 3.3 MCP server with **multiple portmanteau tools** (not one mega `bookmarks` tool). Ported from database-operations-mcp.

## MCP Tools (portmanteau surfaces)

| Tool | Purpose |
|------|---------|
| `browser_bookmarks` | Universal CRUD/search/export across Firefox, Chrome, Edge, Brave |
| `firefox_profiles` | Firefox profile create/load/portmanteau profiles |
| `firefox_backup` | Backup/restore Firefox profile data |
| `firefox_curated` | Curated bookmark source collections |
| `firefox_tagging` | Folder/year-based auto-tagging |
| `firefox_utils` | Firefox paths, lock checks, places DB info |
| `sync_bookmarks` | Cross-browser sync (dry-run supported) |
| `chrome_profiles` | Chromium profile management |
| `ai_bookmark_portmanteau` | AI categorize, dedupe, curate, maintain, export |

`firefox_bookmarks` remains an internal helper used by `browser_bookmarks` for Firefox-specific SQLite operations.

## Quick Start

```powershell
git clone https://github.com/sandraschi/bookmarks-mcp
cd bookmarks-mcp
just
```

This opens an interactive dashboard showing all available commands. Run `just bootstrap` to install dependencies, then `just serve` or `just dev` to start.

##  Installation

### Prerequisites
- [uv](https://docs.astral.sh/uv/) installed (RECOMMENDED)
- Python 3.12+

###  Quick Start
Run immediately via `uvx`:
```bash
uvx bookmarks-mcp
```

###  Claude Desktop Integration
Add to your `claude_desktop_config.json`:
```json
"mcpServers": {
  "bookmarks-mcp": {
    "command": "uv",
    "args": ["--directory", "D:/Dev/repos/bookmarks-mcp", "run", "bookmarks-mcp"]
  }
}
```
### Running the Server

#### As a Python Module (Recommended for MCP clients)
```bash
python -m browser_bookmarks_tools
```

#### As a Direct Script (Development)
```bash
python src/browser_bookmarks_tools/mcp_server.py
```

#### With uv
```bash
uv run python -m browser_bookmarks_tools
```

## MCP Client Configuration

### Cursor IDE (mcp.json)
```json
{
  "mcpServers": {
    "bookmarks-mcp": {
      "command": "python",
      "args": ["-m", "browser_bookmarks_tools"],
      "env": {
        "PYTHONPATH": "D:/Dev/repos/bookmarks-mcp/src",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

### Claude Desktop (claude_desktop_config.json)
```json
{
  "mcpServers": {
    "bookmarks-mcp": {
      "command": "python",
      "args": ["-m", "browser_bookmarks_tools"],
      "env": {
        "PYTHONPATH": "/path/to/bookmarks-mcp/src"
      }
    }
  }
}
```

## Available Operations

See tool docstrings for full operation lists. Primary entry points:

- **`browser_bookmarks`** — `list_bookmarks`, `add_bookmark`, `search_bookmarks`, `find_duplicates`, `export_bookmarks`, tag ops, age analysis, broken links, etc.
- **`sync_bookmarks`** — cross-browser transfer with `dry_run`
- **`ai_bookmark_portmanteau`** — `categorize`, `dedupe`, `curate`, `maintain`, `export`

## Browser Support Details

### Firefox (Primary)
- **Storage:** `places.sqlite` database
- **Features:** Full history, tags, folders, favicons
- **Path:** `~/.mozilla/firefox/*/places.sqlite`

### Chrome/Edge/Brave
- **Storage:** JSON bookmark files
- **Features:** Basic bookmarks with folders
- **Path:** `~/Library/Application Support/Google/Chrome/Default/Bookmarks`

### Safari (macOS only)
- **Storage:** Binary plist files
- **Features:** Basic bookmarks
- **Path:** `~/Library/Safari/Bookmarks.plist`

## Development

### Project Structure
```
bookmarks-mcp/
 src/browser_bookmarks_tools/
    __init__.py          # Package initialization
    __main__.py          # Module entry point for `python -m`
    mcp_server.py       # FastMCP server implementation
    bookmarks/           # Core bookmark operations
       manager.py       # CRUD operations
       organizer.py     # Organization features
       portmanteau.py   # Main tool interface
       sync.py          # Cross-browser sync
    ai/                  # AI-powered features
       analyzer.py      # Content analysis
       summarizer.py    # Summary generation
       tagger.py        # Smart tagging
    browsers/            # Browser-specific implementations
 tests/
 pyproject.toml
```

### Running Tests
```bash
python -m pytest tests/
```

### Code Quality
```bash
# Format code
black src/

# Lint code
ruff check src/

# Type checking
mypy src/
```

## Troubleshooting

### "Module not found" errors
Ensure `PYTHONPATH` includes the `src` directory:
```bash
export PYTHONPATH="/path/to/bookmarks-mcp/src:$PYTHONPATH"
```

### Browser permission issues
- **Firefox:** Ensure Firefox is not running when accessing `places.sqlite`
- **Chrome/Edge:** No special permissions needed for reading bookmark files
- **Safari:** Requires macOS and appropriate file permissions

### MCP connection issues
- Verify the server starts without errors when run manually
- Check that `PYTHONPATH` is correctly set in your MCP client configuration
- Ensure no firewall/antivirus is blocking the connection

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request


## 🛡️ Industrial Quality Stack

This project adheres to **SOTA 14.1** industrial standards for high-fidelity agentic orchestration:

- **Python (Core)**: [Ruff](https://astral.sh/ruff) for linting and formatting. Zero-tolerance for `print` statements in core handlers (`T201`).
- **Webapp (UI)**: [Biome](https://biomejs.dev/) for sub-millisecond linting. Strict `noConsoleLog` enforcement.
- **Protocol Compliance**: Hardened `stdout/stderr` isolation to ensure crash-resistant JSON-RPC communication.
- **Automation**: [Justfile](./justfile) recipes for all fleet operations (`just lint`, `just fix`, `just dev`).
- **Security**: Automated audits via `bandit` and `safety`.

## License

[Add appropriate license information]

## Changelog

### v0.1.0
- Initial FastMCP 3.1.0 compliant implementation
- Firefox, Chrome, Edge, Brave, and Safari support
- Unified portmanteau tool interface
- AI-powered bookmark analysis and tagging
- Cross-browser synchronization


## Web dashboard

| Service | Port | Notes |
|---------|------|-------|
| Frontend (Vite) | **10802** | `web_sota/start.ps1` |
| Backend (FastAPI + MCP) | **10803** | `MCP_TRANSPORT=http` |

Pages: Dashboard, Bookmarks (CRUD + pagination), Search (folder/tag filters), Tree, Bulk ops (sync wizard, export download), Tags, AI Command, MCP Tools, Settings, Help.

### Production auth

HTTP Basic auth is **enabled by default** on `/api/*` routes.

| Variable | Default | Purpose |
|----------|---------|---------|
| `BOOKMARKS_WEB_AUTH` | `1` | Set `0` to disable (dev only) |
| `BOOKMARKS_WEB_USER` | `admin` | Username |
| `BOOKMARKS_WEB_PASS` | `mcp` | Password |

Configure credentials in **Settings → API auth** (stored in browser localStorage as Basic auth header).

Root `/health` is unauthenticated for load balancers.

### Tauri desktop

```powershell
cd native
.\build.ps1
```

Spawns the MCP backend sidecar on 10803 and loads the built SPA.

##  Webapp Dashboard

This MCP server includes a React web interface for monitoring and control.
By default, the web dashboard runs on port **10802**.
*(Assigned ports: **10802** (Web dashboard frontend), **10803** (Web dashboard backend))*

To start the webapp:
1. Navigate to the `webapp` (or `web`, `frontend`) directory.
2. Run `start.bat` (Windows) or `./start.ps1` (PowerShell).
3. Open `http://localhost:10802` in your browser.
