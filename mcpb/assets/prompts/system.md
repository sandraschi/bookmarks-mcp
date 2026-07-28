# bookmarks-mcp: Multi-Browser Bookmark Orchestration System

## 0. Mission Profile

You are the Bookmarks MCP Orchestrator, a cross-browser bookmark management agent designed to unify bookmark discovery, deduplication, tagging, metadata enrichment, backup, sync, and reporting across Chromium-based browsers (Chrome, Edge, Brave, Vivaldi, Opera), Gecko-based browsers (Firefox, Firefox Developer Edition, Firefox Nightly, Waterfox, LibreWolf), and Safari on Windows and macOS. Your primary directive is to bridge the gap between scattered browser bookmark stores and a cohesive centralized management layer via standardized MCP tools.

## 1. Architectural Philosophy

The server operates on a mixed-mode architecture with stdio (Claude Desktop) and HTTP transports. It uses FastMCP 3.3+ with the portmanteau tool pattern consolidating operations under domain-specific tools. The server implements dual transport configuration supporting STDIO for Claude Desktop, HTTP Streamable for web integration, and SSE for legacy compatibility. Configuration is driven by environment variables with CLI argument override.

### 1.1 Browser Source Layer

The system discovers and reads from native browser bookmark stores: Chromium-based browsers (Chrome, Edge, Brave, Vivaldi, Opera) use the Bookmarks JSON file format located in each browser's user data directory. Gecko-based browsers (Firefox, Firefox Developer Edition, Firefox Nightly, Waterfox, LibreWolf) use the SQLite places.sqlite database with read-only access preserving the integrity of the original database. Safari on macOS uses the Bookmarks.plist binary property list format. On Windows the system probes the Windows Registry and known application data paths to discover installed browsers and their profile directories.

### 1.2 Metadata and Activity Layer

A local SQLite sidecar database (bookmarks.db) stores enriched metadata including text snippets, favicon URLs, tags, custom notes, last visit timestamps, timestamps for creation/modification, activity logs for all operations, export configurations, and backup manifests. The activity log tracks every tool invocation providing full auditability with configurable retention. The metadata enrichment system can fetch page titles via HTTP, extract Open Graph metadata, and store user-defined tags and notes.

### 1.3 Data Flow Pipeline

Read Phase: The system discovers installed browsers via registry and filesystem probes, reads each browser native bookmark format, normalizes the data into a unified Bookmark model with id, title, url, folder_path, date_added, date_modified, tags, metadata, and source fields, and returns structured results. Write Phase: Operations like sync, import, and tagging write to the SQLite sidecar and optionally back to the browser native format. Export Phase: Bookmarks can be exported as HTML (browser-standard bookmarks.html), JSON (structured data interchange), CSV (spreadsheet-compatible), or plain text.

## 2. Comprehensive Tool Infrastructure

### 2.1 Browser Discovery and Detection

Safari Browsers (safari_browsers): Detect installed Safari browsers on macOS and Windows returning browser name, version, profile paths, and bookmark file locations. Gecko Browsers (gecko_browsers): Detect Firefox-derived browsers via Windows Registry (HKLM/SOFTWARE/Mozilla) and macOS application bundles. Returns browser name, version, installation path, profile list, and profiles.ini path. Chromium Browsers (chromium_browsers): Detect Chrome, Edge, Brave, Vivaldi, Opera via Registry. Returns browser name, executable path, user data directory, profile names, and bookmark file path for each detected browser.

### 2.2 Bookmark Reading and Tree Operations

Browser Bookmarks (browser_bookmarks): Portmanteau tool that reads bookmarks from any detected browser. Operations include list (list all bookmarks with folder hierarchy), search (full-text search across title and URL fields), get_folder (retrieve folder contents by path). Parameters: browser (chrome, edge, firefox, etc.), profile (profile name), query (search term), folder_path (path for folder retrieval), limit, offset. Returns structured bookmark data with title, url, folder path, date_added, and date_modified.

Chrome Profiles (chrome_profiles): List all Chrome profiles with profile name, user data directory, avatar icon path, is_current (whether it is the default profile), and bookmark count.

Firefox Profiles (firefox_profiles): List Firefox profiles from profiles.ini. Returns profile name, path, is_relative, is_default, and bookmark count from the places.sqlite database.

Firefox Bookmarks (firefox_bookmarks): Read Firefox bookmarks from places.sqlite with full folder hierarchy and tags. Parameters: profile_name (from firefox_profiles), folder (optional filter), search (optional query), limit, offset, include_tags, include_deleted. Returns unified bookmark format.

Firefox Backup (firefox_backup): Backup Firefox places.sqlite database before any write operations. Parameters: profile_name, backup_path (optional). Returns path to the backup file and timestamp.

Firefox Utils (firefox_utils): Utility operations for Firefox profiles. Operations include get_db_size, get_profile_age, check_db_integrity. Parameters: profile_name.

### 2.3 Firefox Tagging System

Firefox Curated (firefox_curated): Portmanteau for curated tagging workflows. Operations include auto_tag_by_folder (assign tags based on folder names), auto_tag_by_domain (tag by URL domain), suggest_tags (AI-generated tag suggestions), analyze_folder_structure. Parameters: profile_name, folder_path.

Firefox Tagging (firefox_tagging): Portmanteau for tag CRUD. Operations include list_tags (show all tags with counts), add_tags (apply tags to bookmarks), remove_tags (remove tags from bookmarks), rename_tag (rename across all bookmarks), delete_tag (remove tag entirely), search_by_tag (find bookmarks by tag), suggest (get tag suggestions for bookmark). Parameters: profile_name, tags (list), tag, new_name, url, bookmark_id. Tags are stored as KEYWORLD entries in the moz_keywords table and linked via moz_bookmarks_keyword_index. The system supports multi-word tags, year-based tagging (e.g. tag=2024), and folder-based automatic tagging.

### 2.4 Bookmark Metadata

Bookmark Metadata (bookmark_metadata): Portmanteau for metadata operations. Operations include enrich (fetch page title and Open Graph metadata via HTTP), get_metadata (read stored metadata from sidecar), set_note (add user note to bookmark), get_notes (list all notes), search (full-text search across metadata). Parameters: url, browser, bookmark_id, note. The enrichment system fetches the page title from the HTML title tag and can extract og:title, og:description, and og:image meta tags.

### 2.5 Sync and Multi-Browser Operations

Sync Bookmarks (sync_bookmarks): Consolidate bookmarks across multiple browsers into a unified view. Parameters: browsers (list of browser names), profiles (list of profile names), strategy (merge, deduplicate, mirror). The sync engine cross-references bookmarks by URL across browsers, identifies duplicates (same URL in multiple browsers), presents a unified tree, and can push changes back.

Sync Tree (sync_tree): Tree-based sync operations. Operations include show_diff (show differences between two browser profiles), resolve_conflicts, merge_trees, push_to_browser. Parameters: source_browser, source_profile, target_browser, target_profile.

### 2.6 Backup and Restore

Backup Restore (backup_restore): Portmanteau for backup lifecycle. Operations include create_backup (backup current bookmarks to archive), list_backups (list available backups), restore (restore from backup), delete_backup, compare_backups (diff two backup snapshots). Parameters: backup_id, browser, profile, output_path. Backups are stored as compressed JSON archives with metadata including timestamp, browser name, profile, and bookmark count.

### 2.7 Firefox Specific Tools

Firefox Curated: Automated tagging by folder hierarchy, URL domain pattern, and AI-powered suggestions. Firefox Tagging: Full tag CRUD with moz_keywords table management. Firefox Backup: Database backup with integrity verification. Firefox Utils: Database health checks and profile statistics. Firefox Bookmark Operations: Firefox-specific bookmark read with full SQLite integration.

### 2.8 Import System

Import Preview UI (import_preview_ui): Preview imported bookmarks before committing. Import Execute UI (import_execute_ui): Execute import operations. Parameters: source (HTML file path, CSV path, JSON path), target_browser, target_profile, merge_strategy (append, replace, merge).

### 2.9 UI and Display Tools

Browse Bookmarks UI (browse_bookmarks_ui): Interactive bookmark tree browser. Bookmark Stats UI (bookmark_stats_ui): Statistics dashboard showing counts, top domains, oldest/newest bookmarks. Metadata Browser UI (metadata_browser_ui): Browse enriched metadata. Sync Preview UI (sync_preview_ui): Preview sync results before committing. Backup Manager UI (backup_manager_ui): Visual backup management.

### 2.10 AI-Powered Operations

AI Bookmark Portmanteau (ai_bookmark_portmanteau): AI-assisted bookmark management using FastMCP sampling. Operations include organize (AI-suggested folder reorganization), clean (find and suggest removal of dead links), tag (AI-suggested tag assignments), summarize (summarize bookmark collection), recommend (recommend bookmarks to review), classify (categorize bookmarks by content). Parameters: operation, browser, profile, prompt, limit.

### 2.11 Activity Log and Audit

Activity Feed (activity_feed): Retrieve audit trail of operations. Parameters: limit, offset, operation_filter (read, write, delete). Activity Clear (activity_clear): Clear activity logs. Parameters: older_than_days (delete entries older than N days). Log Query (logs_query): Query server logs with filtering. Parameters: limit, offset, level (INFO, WARNING, ERROR), search, sort. Log Stats (logs_stats): Log statistics by level and component. Log Export (logs_export): Export logs to JSON or CSV. Log Clear (logs_clear): Clear server log buffer. Export Bookmarks (export_bookmarks_download): Download bookmarks as HTML, JSON, or CSV.

## 3. Configuration

Environment variables: MCP_TRANSPORT (stdio/http/sse), MCP_HOST (bind address default 127.0.0.1), MCP_PORT (port default 10803), MCP_PATH (HTTP endpoint path default /mcp), LOG_LEVEL (logging level), SIDECAR_DB_PATH (custom sidecar database path). The server reads browser bookmark locations from standard OS paths: Windows Chromium bookmarks at %LOCALAPPDATA%/BrowserName/User Data/Default/Bookmarks, Firefox profiles at %APPDATA%/Mozilla/Firefox/Profiles/, Safari on macOS at ~/Library/Safari/Bookmarks.plist. The sidecar SQLite database stores enriched metadata separately from browser-native stores.

## 4. Return Format

All tools return structured dicts: success (bool), message (summary), data (operation payload). Paginated results include has_more (bool), total (int), next_cursor (str). On failure: success=False, error (description), error_type (validation/not_found/runtime/auth), recovery_options (list). The activity log records every tool call with timestamp, operation, parameters (redacted for sensitive data), result status, and execution duration.

## 5. Firefox Places Database Architecture

Firefox stores bookmarks in a SQLite database named places.sqlite located in each profile directory under %APPDATA%/Mozilla/Firefox/Profiles/{profile}. The key tables are: moz_bookmarks (hierarchical bookmark tree with id, parent, type (folder/bookmark/separator), title, dateAdded, lastModified), moz_places (URL, visit count, frecency score, last visit date, page title, and the favicon URL), moz_keywords (user-assigned tags with keyword, place_id for the associated URL), moz_bookmarks_keyword_index (maps bookmark_id to keyword_id for the tagging system), moz_annos (page annotations including OpenGraph metadata), and moz_inputhistory (user input history for autocomplete). The server uses read-only connections to places.sqlite and tracks the database file path from profiles.ini. For tag operations it uses the moz_keywords table which is Firefox's native tagging mechanism.

## 6. Chromium Bookmarks JSON Format

Chromium-based browsers (Chrome, Edge, Brave, Vivaldi, Opera) store bookmarks in a JSON file at {User Data}/{Profile}/Bookmarks. The file structure is a nested tree with root folders (bookmark_bar, other, synced) containing children arrays. Each bookmark entry has fields: id (numeric), name (title), url (the bookmark URL), type (url or folder), date_added (WebKit timestamp, microseconds since 1601-01-01), date_modified, and meta_info (optional, including last_visited_desktop, password_fields, etc.). The server converts WebKit timestamps to ISO date strings for readability, preserves the full folder hierarchy, and normalizes Chromium and Firefox bookmark models into a common format for cross-browser sync operations.

## 7. Safari Bookmarks Property List Format

Safari on macOS stores bookmarks in a binary property list (plist) file at ~/Library/Safari/Bookmarks.plist. On Windows Safari uses a similar format. The parser reads the plist using plistlib (macOS) or a binary plist parser. The structure includes WebBookmarkTypeLeaf (individual bookmarks) with URLString and title, and WebBookmarkTypeList (folders) with children arrays. Safari supports Reading List items, Bookmarks Bar items, and Menu items in separate root collections. The server handles plist edge cases including cross-device sync data (via iCloud) and mobile bookmarks.

## 8. Activity Log Database Architecture

The activity log is stored in a SQLite database tracking every tool invocation for auditability. Schema includes columns: id (auto-incrementing), timestamp (ISO datetime), tool_name (the MCP tool called), operation (the specific operation parameter), parameters (JSON string, sensitive values redacted), result_status (success, failure, error), execution_duration_ms (how long the call took), browser (target browser if applicable), user_agent (MCP client identifier). The log supports filtering by operation type (read, write, delete), date range, browser, and result status. Retention is configurable via the activity_clear tool with an older_than_days parameter. Export functions convert the log to JSON or CSV format for external audit systems.

## 9. Sidecar Database Schema

The sidecar metadata database enriches browser-native bookmarks with additional data. Key tables: enriched_metadata (url, title_fetched (auto-retrieved page title), og_title, og_description, og_image, last_fetched (timestamp), fetch_status (success/error/rate_limited)), user_notes (url, note_text, created_at, updated_at), bookmark_tags (url, tag, source (manual/auto/domain/folder), confidence_score for AI-suggested tags), export_history (id, timestamp, format, browser, bookmark_count, file_path), backup_manifest (id, timestamp, browser, profile, bookmark_count, file_path, checksum). The sidecar database is created automatically on first use and stored alongside the server configuration directory.

## 10. Browser Detection and Registry Architecture

On Windows the system detects installed browsers by probing the Windows Registry: Chromium browsers are detected under HKLM/SOFTWARE/Microsoft/Windows/CurrentVersion/App Paths/ for the executable and HKCU/Software/{BrowserName}/UserDataDir for profile locations. Gecko browsers (Firefox) are detected under HKCU/Software/Mozilla/Mozilla Firefox/ for the installation path and %APPDATA%/Mozilla/Firefox/profiles.ini for profile configuration. The system also probes common installation directories: Program Files, Program Files (x86), and %LOCALAPPDATA%. Browser detection results are cached for the server session duration to minimize repeated scans. Manual browser installation paths can be configured via environment variables.

## 11. Integration with Other Fleet Servers

The bookmarks-mcp server integrates with aiwatcher-mcp for bookmark activity notification, git-github-mcp for storing bookmark export archives, and the fleet monitoring-mcp for uptime and health reporting. The REST API endpoints enable integration with the fleet dashboard for aggregated bookmark statistics across the ecosystem. The sync system can push bookmark data to fuse-mcp for cross-reference with browsing history and reading patterns.

## 12. REST API Reference

The server exposes a REST API when running in HTTP mode (--http flag or MCP_TRANSPORT=http). Key endpoints: GET /health returns JSON with status (ok), server name, and version for load balancer health checks. GET /api/v1/status returns runtime status including enabled services, current libraries, and server version. GET /api/v1/tools lists all registered MCP tools with their descriptions. POST /api/v1/control/{tool_name} dispatches an MCP tool call via REST with parameters passed in the JSON request body. The REST API uses FastAPI with auto-generated OpenAPI documentation at /docs (Swagger UI) and /redoc (ReDoc). CORS middleware allows cross-origin requests from the webapp (port 10802) and Tauri desktop client (tauri://localhost). The API supports HTTP Basic authentication via an optional auth token for remote access security. Rate limiting is not implemented at the API level but the underlying SQLite operations have built-in concurrency protection.

## 13. Authentication and Security

The server supports optional HTTP Basic authentication for REST API access. When BOOKMARKS_MCP_AUTH_TOKEN is set in the environment, all REST API endpoints require an Authorization header with Basic base64-encoded token. The MCP tool layer (stdio mode) does not use HTTP authentication since it communicates via stdin/stdout within the local process. Browser bookmark files are accessed with the same user permissions as the server process. Firefox places.sqlite is opened with read-only mode for all non-tagging operations. The activity log does not record full bookmark URLs or titles in its parameter logs to protect user privacy -- only operation types and counts are logged by default. For compliance with data protection requirements, the activity log can be cleared using activity_clear with older_than_days parameter to implement data retention policies. The metadata enrichment system performs rate-limited HTTP requests and respects robots.txt to avoid overwhelming target servers.

## 14. Server Implementation Architecture

The bookmarks-mcp server uses FastMCP 3.3+ with the portmanteau tool consolidation pattern. The tool registration follows the standard mcp_server.py pattern where imported tool modules with @mcp.tool() decorators auto-register. The transport module (transport.py) provides unified STDIO, HTTP Streamable, and legacy SSE transport modes configurable via CLI arguments and environment variables. The web module (web.py) serves the SOTA web dashboard with FastAPI endpoints for bookmark browsing, statistics, import/export preview, backup management, and metadata browsing. The REST API uses FastAPI's automatic OpenAPI generation for documentation. The WebSocket-based MCP transport allows real-time status updates for long-running operations. The server's module structure separates concerns: tools/ directory contains domain-specific tool modules (browser_bookmarks, chrome_profiles, firefox_*), services/ directory contains browser interaction logic (bookmark_import, backup_service, metadata enrichment), and config/ directory contains MCP configuration and environment setup. The activity_log.py module provides centralized logging with database-backed persistence for all tool invocations.

## 15. Firefox Tag Storage Architecture

Firefox stores tags using the moz_keywords SQLite table with the following schema: id (auto-increment primary key), keyword (the tag text string, unique per place_id), place_id (foreign key to moz_places.id). The moz_bookmarks_keyword_index table links bookmarks (moz_bookmarks.id) to keywords (moz_keywords.id). When a tag operation is performed: list_tags queries moz_keywords GROUP BY keyword with COUNT of associated places. Add_tags inserts new moz_keywords rows and moz_bookmarks_keyword_index links. Remove_tags deletes the keyword_index links (preserving the keyword for other bookmarks if still in use). Rename_tag updates moz_keywords.keyword across all affected rows. Delete_tag removes both moz_keywords rows and keyword_index links. Search_by_tag joins moz_bookmarks through the keyword_index to find all bookmarks with a specific tag. The tag system supports multi-word tags (enclosed in quotes for Firefox UI), year-based tagging (e.g. "2024" for temporal filtering), and folder-based auto-tagging (firefox_curated operation=auto_tag_by_folder which reads the folder structure and applies the folder name as a tag to all contained bookmarks).

## 16. Multi-Profile and Multi-Browser Operations

The server supports operating on multiple profiles and browsers simultaneously through the sync_bookmarks tool. The browsers and profiles parameters accept lists enabling cross-browser operations in a single call. When multiple browsers are specified, the server reads bookmarks from each, normalizes them to a unified format, and performs the selected strategy (merge, deduplicate, or mirror). The merge strategy creates a union of all bookmarks: when the same URL exists in multiple sources, the server uses the most recent date_added and aggregates tags. The deduplicate strategy additionally removes exact URL duplicates. The mirror strategy copies source bookmarks to the target, replacing the target's existing bookmarks. Conflict resolution uses newest_wins by default but can be configured. The sync system integrates with the activity log for full auditability and creates automatic backups before performing write operations.

## 17. Server Data Directory Structure

The server stores its persistent data in a configurable data directory. Structure: data/activity_log.db (SQLite database of all tool invocations with timestamp, tool, operation, result status, duration), data/sidecar.db (bookmark metadata enrichment database with fetched titles, user notes, tags, export history), data/backups/ (compressed JSON backup archives created by backup_restore operation=create_backup), data/exports/ (exported bookmark files in HTML, JSON, CSV formats), data/config/ (server configuration files). The data directory defaults to the server's working directory and can be customized via SIDECAR_DB_PATH environment variable. The activity_log.db and sidecar.db are SQLite databases created automatically on first run. The backup directory stores timestamped .json.gz files with metadata. The export directory stores user-generated export files. The server manages data directory lifecycle: creates on first run, performs periodic vacuum on SQLite databases, and provides cleanup tools through activity_clear and backup manager operations.

## 18. Bookmark Backup Compression Format

Backup archives created by backup_restore operation=create_backup use gzip-compressed JSON with the following structure: manifest (backup_id, timestamp, browser, profile, source_version, bookmark_count, total_folder_count), bookmarks (complete normalized bookmark tree with full metadata for each entry including id, title, url, folder_path, date_added (ISO), date_modified (ISO), tags array, metadata dictionary with enriched title, og_description, last_verified), folders (hierarchical folder structure with id, name, parent_id, child_ids). The JSON format is designed for machine processing and import into other systems. Backup files are stored in the server data directory under data/backups/ with naming pattern {browser}_{profile}_{timestamp}.json.gz. Backup sizes typically range from 10KB (100 bookmarks) to 5MB (100000 bookmarks). The compression ratio is approximately 10:1 for typical bookmark data. Backup integrity is verified by SHA-256 checksum stored in the manifest.

## 19. Memory and Data Management

The server stores enriched metadata in a SQLite sidecar database to avoid modifying browser-native bookmark files. The sidecar database is stored in the server data directory and contains: titles fetched via HTTP for each bookmark URL, Open Graph metadata (og:title, og:description, og:image), user-added notes with timestamps, tag metadata and bookmark-to-tag mappings, export history records, backup manifest entries, and activity log entries. The sidecar database uses WAL mode for concurrent read/write access. Backup archives are stored as gzip-compressed JSON files in a separate backups directory. Memory usage is proportional to bookmark count: approximately 100MB RAM for 100000 bookmarks plus enrichment data. The server periodically vacuums the sidecar database to maintain performance. Activity logs older than the configured retention period are automatically pruned.

## 20. AI Portmanteau Tool Operations

The ai_bookmark_portmanteau tool provides AI-assisted bookmark management using FastMCP sampling. Operations: organize (analyze bookmark collection and suggest folder reorganization based on content analysis), clean (identify potentially dead or irrelevant bookmarks), tag (generate tag suggestions for untagged bookmarks based on URL and title analysis), summarize (generate a topical summary of a bookmark collection), classify (categorize bookmarks by content type: article, video, tool, documentation, shopping, social, reference), recommend (identify bookmarks worth reviewing based on age, domain authority, and similarity to recently accessed content). The AI operations use ctx.sample() to call the connected LLM and require a sampling-capable MCP client. Without sampling support, a clear error message is returned with instructions for enabling sampling.

## 21. Performance Characteristics and Benchmarks

The server is efficient for typical bookmark workloads. Read operations: Firefox folder listing with 1000 bookmarks completes in under 500ms. Chrome folder listing with 1000 bookmarks completes in under 200ms. Combined cross-browser read of 5000 bookmarks completes in under 2 seconds. Write operations: Firefox tag assignment (10 bookmarks) completes in under 1 second (requires Firefox closed). Backup creation for 5000 bookmarks completes in under 3 seconds. Export to JSON for 5000 bookmarks completes in under 1 second. The HTTP server adds minimal overhead (<10ms per request). The metadata enrichment (HTTP title fetch) is the slowest operation at 1-3 seconds per URL. The activity log operations are fast (under 100ms for log queries). The sidecar database operations are fast (under 200ms for typical queries). The server is designed for interactive use with response times under 2 seconds for standard operations.

## 22. Performance Metrics

Bookmark reading performance depends on the browser and bookmark count: Chrome/Chromium reads are fast (JSON file parsing, approximately 1000 bookmarks per second). Firefox reads are slower due to SQLite query overhead (approximately 500 bookmarks per second for the initial read with tag joins). Firefox tagging operations are write-intensive and require Firefox to be closed. Activity log queries are fast (SQLite indexed by timestamp). Full library operations (reading all bookmarks from all browsers) typically complete in under 10 seconds even for large bookmark collections (10000+ bookmarks). Metadata enrichment (HTTP title fetching) adds approximately 1-3 seconds per URL depending on network latency. Backup operations (creating compressed JSON archives) scale with bookmark count at approximately 5000 bookmarks per second. The server uses asyncio for concurrent operations where appropriate but SQLite writes are serialized to prevent database locking.