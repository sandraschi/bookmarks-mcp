# MCP Configuration Guide

This guide explains how to configure the Browser Bookmarks MCP server with various MCP clients.

## Cursor IDE

Add the following to your `~/.cursor/mcp.json`:

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

### Windows Path Example
```json
{
  "mcpServers": {
    "bookmarks-mcp": {
      "command": "python",
      "args": ["-m", "browser_bookmarks_tools"],
      "env": {
        "PYTHONPATH": "D:\\Dev\\repos\\bookmarks-mcp\\src",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

## Claude Desktop

Add the following to your `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or the appropriate config file for your platform:

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

## Antigravity IDE

Add the following to your `settings.json`:

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

## Troubleshooting

### "Module not found" errors
- Ensure `PYTHONPATH` points to the `src` directory containing `browser_bookmarks_tools`
- Verify the path uses forward slashes (Unix-style) in JSON, even on Windows
- Check that Python can import the module: `python -c "import browser_bookmarks_tools"`

### Server won't start
- Test manually: `PYTHONPATH=src python -m browser_bookmarks_tools`
- Check for missing dependencies: `pip install -e .`
- Verify Python version >= 3.11

### Permission issues
- Ensure read access to browser bookmark files
- For Firefox: Close Firefox before accessing `places.sqlite`
- For system browsers: May require elevated permissions on some systems

## Environment Variables

- `PYTHONPATH`: Must include the `src` directory
- `PYTHONUNBUFFERED`: Recommended for better logging in MCP stdio mode

## Alternative Configuration (Direct Script)

If module execution doesn't work, you can run the server directly:

```json
{
  "mcpServers": {
    "bookmarks-mcp": {
      "command": "python",
      "args": ["D:/Dev/repos/bookmarks-mcp/src/browser_bookmarks_tools/mcp_server.py"],
      "env": {
        "PYTHONPATH": "D:/Dev/repos/bookmarks-mcp/src",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

This bypasses the `__main__.py` entry point and runs the server script directly.
