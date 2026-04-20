# Browser Bookmarks Tools (MCP)

[![FastMCP Version](https://img.shields.io/badge/FastMCP-3.1.0-blue?style=flat-square&logo=python&logoColor=white)](https://github.com/sandraschi/fastmcp) [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![Linted with Biome](https://img.shields.io/badge/Linted_with-Biome-60a5fa?style=flat-square&logo=biome&logoColor=white)](https://biomejs.dev/) [![Built with Just](https://img.shields.io/badge/Built_with-Just-000000?style=flat-square&logo=gnu-bash&logoColor=white)](https://github.com/casey/just)

FastMCP 3.1.0 compliant MCP server providing a unified `bookmarks` portmanteau tool for CRUD operations, organization, sync, and AI-powered helpers.

## Features

- **Primary Browser:** Firefox (SQLite-based bookmarks)
- **Secondary Browsers:** Chrome, Edge, Brave (JSON-based bookmarks)
- **Optional:** Safari (plist-based bookmarks)
- **AI Features:** Smart tagging, summarization, and content analysis
- **Cross-browser Sync:** Import/export between different browsers
- **Organization:** Automatic categorization and duplicate detection

## Quick Start

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

The `bookmarks` tool supports the following operations:

- **`create`** - Add new bookmarks with metadata
- **`read`** - Retrieve bookmarks by URL, title, or tags
- **`update`** - Modify existing bookmarks
- **`delete`** - Remove bookmarks
- **`organize`** - Auto-categorize and clean up bookmarks
- **`sync`** - Import/export between browsers
- **`analyze`** - AI-powered content analysis and tagging
- **`tag`** - Smart tag generation and management
- **`summarize`** - Create bookmark summaries

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


##  Webapp Dashboard

This MCP server includes a free, premium web interface for monitoring and control.
By default, the web dashboard runs on port **10802**.
*(Assigned ports: **10802** (Web dashboard frontend), **10803** (Web dashboard backend))*

To start the webapp:
1. Navigate to the `webapp` (or `web`, `frontend`) directory.
2. Run `start.bat` (Windows) or `./start.ps1` (PowerShell).
3. Open `http://localhost:10802` in your browser.
