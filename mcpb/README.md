# bookmarks-mcp (MCPB Bundle)

FastMCP 3.3 MCP server — multi-portmanteau browser bookmark management

## Usage

Add to \claude_desktop_config.json\:
\\\json
{
  "mcpServers": {
    "bookmarks-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "\D:\Dev\repos", "python", "-m", "bookmarks_mcp"],
      "env": { "PYTHONPATH": "\D:\Dev\repos/src" }
    }
  }
}
\\\

## Tools

- **health**: health
- **main_stdio**: main(stdio)
- **main_http**: main(http)
- **main_sse**: main(sse)
- **api_health**: api_health
- **api_status**: api_status
- **list_tools**: list_tools
- **call_tool_endpoint**: call_tool_endpoint
- **execute_tool_legacy**: execute_tool_legacy
- **safari_browsers**: safari_browsers
- **gecko_browsers**: gecko_browsers
- **chromium_browsers**: chromium_browsers
- **bookmark_tree**: bookmark_tree
- **activity_feed**: activity_feed
- **activity_clear**: activity_clear
- **logs_query**: logs_query
- **logs_stats**: logs_stats
- **logs_export**: logs_export
- **logs_clear**: logs_clear
- **export_bookmarks_download**: export_bookmarks_download
- **backup_restore**: backup_restore
- **bookmark_metadata**: bookmark_metadata
- **browser_bookmarks**: browser_bookmarks
- **chrome_profiles**: chrome_profiles
- **firefox_backup**: firefox_backup
- **firefox_bookmarks**: firefox_bookmarks
- **firefox_curated**: firefox_curated
- **firefox_profiles**: firefox_profiles
- **firefox_tagging**: firefox_tagging
- **firefox_utils**: firefox_utils
- **browse_bookmarks_ui**: browse_bookmarks_ui
- **bookmark_stats_ui**: bookmark_stats_ui
- **import_preview_ui**: import_preview_ui
- **metadata_browser_ui**: metadata_browser_ui
- **sync_preview_ui**: sync_preview_ui
- **backup_manager_ui**: backup_manager_ui
- **import_execute_ui**: import_execute_ui
- **sync_bookmarks**: sync_bookmarks
- **ai_bookmark_portmanteau**: ai_bookmark_portmanteau

## Requirements

- Python 3.12+
- uv
