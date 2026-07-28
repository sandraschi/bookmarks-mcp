# bookmarks-mcp: Comprehensive User Guide and Workflow Manual

Welcome to the Bookmarks MCP ecosystem. This guide provides step-by-step instructions for managing browser bookmarks across Chrome, Firefox, Edge, Brave, Safari, and other browsers using natural language commands through your MCP client. Whether you are consolidating years of scattered bookmarks, performing a browser migration, or setting up an automated backup system this guide covers every aspect of the system.

## 1. Quick Start: Discovering Your Browser Bookmarks

The first step is discovering which browsers are installed on your system and where their bookmarks live. Use the browser discovery tools to get a complete inventory.

"Discover all browsers on this system and show me their profiles."

The server will call safari_browsers to detect Safari, gecko_browsers to detect Firefox-based browsers, and chromium_browsers to detect Chrome, Edge, Brave, and others. Each returns the browser name, version, installation path, and profile list. If a browser is not detected it may not be installed or its profile directory may be in a non-standard location.

## 2. Tutorial 1: Cross-Browser Bookmark Inventory

Goal: Get a complete view of all bookmarks across Chrome and Firefox.

Step 1: Detect browsers. Call chromium_browsers to find Chrome/Edge/Brave profiles. Call gecko_browsers to find Firefox profiles. Step 2: Read Chrome bookmarks using browser_bookmarks operation=list browser=chrome. This returns the full folder hierarchy and bookmark list. Step 3: Read Firefox bookmarks using browser_bookmarks operation=list browser=firefox. Step 4: Compare results. Chrome bookmarks come from the Bookmarks JSON file. Firefox bookmarks come from the places.sqlite SQLite database. The server normalizes both into the same format with title, url, folder_path, date_added, and date_modified. Step 5: Use bookmark_stats_ui to see counts and top domains across both browsers.

## 3. Tutorial 2: Finding Duplicate Bookmarks

Goal: Identify bookmarks with duplicate URLs across browsers.

Step 1: Read all bookmarks from Chrome using browser_bookmarks operation=list browser=chrome. Step 2: Read all bookmarks from Firefox browser=firefox. Step 3: Use sync_bookmarks with strategy=deduplicate. The sync engine compares URLs across both browser sets. Step 4: Review duplicates using sync_preview_ui which shows a diff view. Step 5: Resolve duplicates by choosing which copy to keep (typically the one with the most recent date_added or the one with tags/metadata). Step 6: Use sync_bookmarks strategy=merge to consolidate.

Parameter details: sync_bookmarks accepts browsers=["chrome", "firefox"], profiles=["Default", "default"], strategy="deduplicate". The strategy parameter supports three modes: merge (union of all bookmarks), deduplicate (merge plus removal of identical URLs), and mirror (copy from source to target).

## 4. Tutorial 3: Tagging All Bookmarks with Year-Based Tags

Goal: Automatically tag Firefox bookmarks by the year they were added for temporal filtering.

Step 1: Get Firefox profiles using firefox_profiles. Step 2: Read bookmarks using firefox_bookmarks with include_tags=false. Step 3: Use firefox_tagging operation=suggest to get AI-generated tag suggestions. Step 4: Use firefox_curated operation=analyze_folder_structure to understand the folder tree. Step 5: Apply year-based tags by extracting the year from date_added and using firefox_tagging operation=add_tags with tags=["2023", "reference"]. Step 6: Verify using firefox_tagging operation=list_tags to see all tags with bookmark counts.

Firefox tags are stored in the moz_keywords table using KEYWORD annotation entries linked to bookmarks via the moz_bookmarks_keyword_index join table. This provides native Firefox tag support that survives browser restarts and is visible in the Firefox Library.

## 5. Tutorial 4: Browser Migration from Chrome to Firefox

Goal: Migrate all Chrome bookmarks to Firefox with proper folder hierarchy preservation.

Step 1: Read Chrome bookmarks with browser_bookmarks operation=list browser=chrome to get the full tree. Step 2: Read Firefox current bookmarks with browser_bookmarks operation=list browser=firefox to understand the existing structure. Step 3: Use sync_bookmarks with browsers=["chrome", "firefox"] strategy=merge. Step 4: Preview results with sync_preview_ui. Step 5: Execute the merge. The sync engine preserves folder hierarchy by mapping Chrome folder structures to Firefox folder structures. Chrome bookmark bar items go to the Firefox Bookmarks Toolbar folder, Chrome Other Bookmarks go to the Firefox Other Bookmarks folder. Step 6: Verify with browser_bookmarks browser=firefox.

## 6. Tutorial 5: Metadata Enrichment and Notes

Goal: Enrich bookmark metadata with page titles and add personal notes.

Step 1: Select bookmarks to enrich using browser_bookmarks operation=search query="important". Step 2: Use bookmark_metadata operation=enrich url="https://example.com/article" to fetch the current page title and Open Graph metadata. Step 3: Use bookmark_metadata operation=set_note url="https://example.com/article" note="Key reference for project X" to add a personal note. Step 4: Use bookmark_metadata operation=get_notes to retrieve all bookmarks with notes. Step 5: Use bookmark_metadata operation=search query="project X" to full-text search across notes and enriched metadata.

The metadata enrichment system makes HTTP HEAD and GET requests to fetch page metadata. It respects robots.txt and rate limits. Enriched data is stored in the local SQLite sidecar database and is NOT written back to browser-native bookmark stores to avoid data loss.

## 7. Tutorial 6: Automated Backup Strategy

Goal: Set up regular bookmark backups with snapshot comparison.

Step 1: Use backup_restore operation=create_backup browser=chrome to create a backup. Step 2: Create a Firefox backup with backup_restore operation=create_backup browser=firefox. Step 3: List all backups with backup_restore operation=list_backups. Backups include timestamp, browser name, profile, and bookmark count. Step 4: After making changes, create another backup. Step 5: Use backup_restore operation=compare_backups backup_id_1=123 backup_id_2=124 to see what changed between snapshots. The diff shows added, removed, and modified bookmarks. Step 6: If needed, use backup_restore operation=restore backup_id=123 to revert to a previous state.

Backups are stored as compressed JSON archives in the sidecar database directory. Each backup contains the complete bookmark tree with metadata and can be exported separately using export_bookmarks_download.

## 8. Tutorial 7: Firefox Database Health Check

Goal: Check your Firefox places.sqlite database integrity and size.

Step 1: Get Firefox profiles with firefox_profiles. Step 2: Use firefox_utils operation=get_db_size profile_name="default" to check the database file size. Step 3: Use firefox_utils operation=check_db_integrity profile_name="default" to run SQLite PRAGMA integrity_check. Step 4: Use firefox_utils operation=get_profile_age to see when the profile was created and last used. Step 5: If the database is large, use firefox_backup operation=create_backup to make a safe copy. Step 6: Consider running Firefox Places Maintenance (Tools > Library > Maintenance) if integrity checks indicate issues.

Large places.sqlite databases (over 500 MB) may slow down bookmark operations. The automatic maintenance built into Firefox typically handles this but the backup tool provides a safety net.

## 9. Tutorial 8: Dead Link Detection and Cleanup

Goal: Find and remove bookmarks pointing to dead or redirected URLs.

Step 1: Export all bookmarks using export_bookmarks_download format=json. Step 2: Use ai_bookmark_portmanteau operation=clean browser=chrome profile="Default". The AI-powered cleaning operation analyzes bookmark URLs for common dead link patterns including 404 responses, DNS resolution failures, and excessive redirects. Step 3: Review the results showing dead links, the HTTP status code or error encountered, and the last known good URL if available. Step 4: Use bookmark_metadata to add notes to dead links marking them for manual review. Step 5: Remove dead bookmarks directly in the browser or use the sync tool to create a cleaned set. Step 6: Create a backup before making changes with backup_restore operation=create_backup.

The cleaning operation is read-only by default. It reports findings without modifying bookmarks. To actually remove dead links you must use the browser's native bookmark manager or the sync tool with explicit delete operations.

## 10. Tutorial 9: AI-Assisted Bookmark Organization

Goal: Use AI to suggest a better folder organization for your bookmark collection.

Step 1: Read all bookmarks from your primary browser using browser_bookmarks operation=list. Step 2: Use ai_bookmark_portmanteau operation=organize with a description of your preferred organization like "organize by topic: technology, recipes, travel, reference, and work". The AI analyzes bookmark titles, URLs, and existing folder structure to suggest a reorganization. Step 3: Use ai_bookmark_portmanteau operation=classify to categorize bookmarks by content type (article, video, tool, documentation, shopping, social). Step 4: Review the AI suggestions. Step 5: Apply the reorganization manually through your browser or use the sync tool's merge strategy to reorganize. Step 6: Use ai_bookmark_portmanteau operation=summarize to get a one-paragraph summary of your entire bookmark collection's topical focus.

The AI bookmark tools require a sampling-capable MCP client (Claude Desktop, Cursor). They use ctx.sample() to generate suggestions based on the connected LLM. Results are suggestions only and should be reviewed before applying.

## 11. Tutorial 10: Exporting Bookmarks for Sharing

Goal: Export bookmarks in various formats for sharing or archiving.

Step 1: Select the source browser and profile. Step 2: Use export_bookmarks_download format=html browser=chrome to create a standard bookmarks.html file. This format is compatible with all major browsers and can be imported directly. Step 3: Export as JSON using format=json for machine-readable interchange. The JSON export includes all metadata fields (tags, notes, enriched data) that the browser-native HTML format does not support. Step 4: Export as CSV using format=csv for spreadsheet analysis in Excel or Google Sheets. Step 5: For selective export, search first with browser_bookmarks then use export_bookmarks_download with a query parameter. Step 6: Share the exported file or import it into another browser using its built-in import functionality.

## 12. Configuration Reference

Transport: Set MCP_TRANSPORT=http for HTTP mode (default stdio). Port: Set MCP_PORT=10803 for the HTTP server port. Host: Set MCP_HOST=127.0.0.1 for the bind address. Path: Set MCP_PATH=/mcp for the HTTP endpoint path. Auth: Set BOOKMARKS_MCP_AUTH_TOKEN for HTTP bearer authentication. Sidecar DB: Set SIDECAR_DB_PATH for a custom sidecar database location (defaults to the server data directory). Logging: Set LOG_LEVEL=DEBUG for verbose output.

## 13. API Reference

GET /health returns server health status. GET /api/v1/tools lists all registered MCP tools. POST /api/v1/control/{tool_name} dispatches a tool call via REST (parameters in JSON body). GET /api/v1/status returns server runtime status. The web dashboard serves on port 10803 by default with React-based UI for browsing, stats, import previews, sync previews, and backup management.

## 14. Troubleshooting

Browser not detected: Run the browser once to ensure profiles are initialized. Check that the browser is installed in a standard location. On Windows check %LOCALAPPDATA%, %APPDATA%, and Program Files. Firefox database locked: Close Firefox before reading its places.sqlite. The server uses read-only connections that fail gracefully if the database is locked. Permission errors: Run your MCP client with appropriate permissions. On Windows some browser profile directories require user-level access. Sidecar database issues: Delete the sidecar DB file to force re-creation (bookmark data is preserved in browser-native stores). Large bookmark sets: Use pagination parameters (limit, offset) for large collections. Firefox operations use LIMIT clauses directly on SQLite queries for efficiency.

## 15. Advanced Use Cases

### 15.1 Yearly Bookmark Archiving
Archive bookmarks by year for historical analysis: 1) Export all bookmarks as JSON with export_bookmarks_download format=json. 2) Use firefox_tagging operation=add_tags with year-based tags (e.g. tags=["2020"]) applied to bookmarks from each calendar year. 3) Use backup_restore operation=create_backup to preserve the current state. 4) Create an HTML export of each year's bookmarks using the search tool with date filters. 5) The backup snapshots can be compared year-over-year to visualize browsing habit evolution. 6) Use ai_bookmark_portmanteau operation=summarize to get an AI-generated summary of each year's bookmark themes.

### 15.2 Cross-Browser Deduplication Workflow
Complete deduplication and consolidation across multiple browsers: 1) Detect all browsers (chromium_browsers, gecko_browsers, safari_browsers). 2) Read all bookmarks from every detected browser. 3) Use sync_bookmarks strategy=deduplicate with all browsers listed. The sync engine identifies bookmarks with identical URLs across browser sources. 4) For each duplicate group, compare metadata: the bookmark with the newest date_added, the most tags, or the longest retention in a browser. 5) Use backup_restore operation=create_backup to secure pre-merge state. 6) Use sync_bookmarks strategy=merge to consolidate the deduplicated set into a single browser or export. 7) Verify with bookmark_stats_ui to see the consolidated counts.

### 15.3 Automated Link Rot Checking
Periodically verify bookmark URLs are still accessible: 1) Export all bookmarks as JSON. 2) Use bookmark_metadata operation=enrich on each URL to verify accessibility (the enrich tool attempts HTTP HEAD and reports fetch_status). 3) Bookmark URLs that fail with HTTP 404, 410, or DNS errors are flagged as dead. 4) Use ai_bookmark_portmanteau operation=organize with a "clean dead links" prompt to generate cleanup suggestions. 5) For dead links with known replacements, use bookmark_metadata operation=set_note to record the alternative URL. 6) Export the dead link report using export_bookmarks_download format=csv for external tracking.

### 15.4 Multi-User Profile Management
For shared workstations: 1) List all Chrome profiles with chrome_profiles. 2) List all Firefox profiles with firefox_profiles. 3) Compare bookmarks across user profiles to find common resources. 4) Use sync_bookmarks to create a shared bookmarks set between selected profiles. 5) Tag cross-profile bookmarks with a "work" or "shared" tag using firefox_tagging. 6) Use backup_restore to create per-profile backups before any destructive operations.

## 16. FAQ

Q: Can I recover deleted bookmarks? A: If you have a backup (created via backup_restore operation=create_backup), use backup_restore operation=restore to recover. Firefox keeps recently deleted bookmarks in a 30-day undo history accessible through the Firefox Library. Chromium deletes bookmarks permanently after emptying the trash.

Q: Does the server modify my browser data directly? A: Read operations never modify browser data. Write operations (tagging, sync, import) explicitly modify Firefox's moz_keywords table (for tags) or the Bookmarks JSON file (for Chromium imports). Always create a backup before write operations.

Q: Why are some bookmarks missing from Firefox results? A: Firefox places.sqlite may have schema differences across versions. Very large bookmark sets (over 10000) require pagination. Firefox database locks prevent read access while Firefox is running.

Q: Can I use this with remote browsers? A: The server reads local browser profiles only. Remote browsers require mounting the remote profile directory locally or using a file sync tool to copy bookmark data first.

Q: How are Chromium timestamps handled? A: Chromium uses WebKit timestamps (microseconds since 1601-01-01 UTC). The server converts these to ISO 8601 date strings, but the conversion accounts for the 11644473600-second offset between the WebKit epoch and the Unix epoch.

## 17. Data Export Formats Reference

The export_bookmarks_download tool supports three format types, each suited to different use cases. HTML format: Standard Netscape bookmark format compatible with all major browsers. The output includes DOCTYPE declaration, META tags for character encoding and generator identification, nested DL/DT/DD structure with folder hierarchy preserved, H3 tags for folder names, A tags for bookmarks with HREF, ADD_DATE, LAST_VISIT, LAST_MODIFIED, and ICON attributes, and HR tags for separators. This format is ideal for browser import. JSON format: Complete structured data with all metadata fields. The output includes root-level metadata (export_timestamp, source_browser, source_profile, total_count, version), nested folder structure with id, title, date_added, children arrays, bookmark entries with id, title, url, date_added, date_modified, icon_uri, tags array, notes string, metadata dictionary (enriched_title, og_description, last_verified). This format preserves all enriched metadata that the browser-native HTML format loses. CSV format: Flat table suitable for spreadsheet analysis. Columns include id, title, url, folder_path, date_added, date_modified, tags, notes, browser, profile. Each bookmark is a single row. Folder structure is represented as hierarchical path (e.g. "Bookmarks Bar/Work/Projects").

## 18. Server Command Line Reference

The server supports CLI arguments for startup configuration. Default mode: stdio for Claude Desktop. HTTP mode: --http flag enables the REST API and web dashboard on MCP_PORT (default 10803). TCP binding: --host flag sets the bind address (default 127.0.0.1). Port selection: --port overrides MCP_PORT (e.g. --port 8080). Endpoint path: --path for HTTP MCP endpoint (default /mcp). Debug mode: --debug enables verbose logging for troubleshooting. Legacy SSE: --sse for SSE transport (deprecated). Transport precedence: CLI flags override environment variables which override defaults. The server also supports MCP_TRANSPORT=http MCP_HOST=0.0.0.0 MCP_PORT=10803 for network-accessible HTTP mode. The web dashboard is served by the REST API with React SPA for browsing, statistics, import previews, sync previews, and backup management.

## 19. Firefox Profiles Deep Dive

Firefox profile management through the Windows Registry and filesystem: The profiles.ini file at %APPDATA%/Mozilla/Firefox/profiles.ini contains section headers for each profile (Profile0, Profile1, etc.) with Name, Path (relative or absolute), IsRelative (1 for relative to profiles.ini directory), Default (1 for default profile), Locked (1 for enterprise-managed). The server reads this INI file to enumerate all profiles. Each profile directory contains: places.sqlite (bookmarks and history database), favicons.sqlite (favicon cache), key4.db (password encryption keys), logins.json (saved credentials), cert9.db (certificate store), prefs.js (user preferences), xulstore.json (window state). The server primarily accesses places.sqlite and favicons.sqlite. The places.sqlite database can be read even while Firefox is running in read-only mode but writes (tagging) require Firefox to be closed. The server automatically detects the default profile and provides profile switching via the profile_name parameter. Non-default profiles must be explicitly specified.

## 20. Chromium Profile Deep Dive

Chromium profiles are stored under User Data directory in the browser's application data folder. Standard paths: Chrome: %LOCALAPPDATA%/Google/Chrome/User Data/{Profile}, Edge: %LOCALAPPDATA%/Microsoft/Edge/User Data/{Profile}, Brave: %LOCALAPPDATA%/BraveSoftware/Brave-Browser/User Data/{Profile}, Opera: %APPDATA%/Opera Software/Opera Stable, Vivaldi: %LOCALAPPDATA%/Vivaldi/User Data/{Profile}. Each profile directory contains: Bookmarks (JSON file with bookmark tree), Favicons (SQLite database), Top Sites (SQLite database for most visited sites), History (SQLite database of browsing history), Login Data (SQLite database of saved passwords), Cookies (SQLite database), Preferences (JSON file with user preferences), Extensions directory (installed extensions). The server reads the Bookmarks JSON file which uses WebKit timestamps. The Profile detection uses the Local State file at the User Data root which contains profile info dictionary with profile names, user names, avatar icons, and creation dates. The chrome_profiles tool reads this Local State file to provide profile metadata.

## 21. Advanced Sync Workflows

The sync system supports complex multi-browser synchronization scenarios. Strategy deep dive: The merge strategy creates a union of all bookmarks from all specified browsers. When the same URL exists in multiple browsers, it keeps the entry with the most recent date_added and merges tags and metadata. The deduplicate strategy adds an additional pass that identifies identical URLs across browsers and removes duplicates keeping the best entry (highest metadata richness). The mirror strategy copies all bookmarks from the source browser to the target browser, replacing the target's existing bookmarks. Conflict resolution follows configurable rules: newest_wins (default), source_wins, target_wins, or manual (returns conflicts for user resolution). The sync tree tool (available through the sync UI tools) shows a visual diff before applying changes. The diff includes: new bookmarks (exists in source but not target), removed bookmarks (exists in target but not source), modified bookmarks (same URL with different title or folder), and unchanged bookmarks (same in both). The sync preview UI presents these diff categories with counts and allows selective application of changes.

## 22. Server Command Line Reference

The server supports these CLI flags: --stdio (stdin/stdout JSON-RPC mode for Claude Desktop, default), --http (HTTP Streamable mode for web access on port 10803), --sse (legacy SSE mode, deprecated), --host (bind address for HTTP mode, default 127.0.0.1), --port (HTTP port override, default 10803), --path (HTTP MCP endpoint path, default /mcp), --debug (enable DEBUG logging for troubleshooting). In HTTP mode the server serves both the MCP tool endpoint and the React web dashboard on the same port. Environment variables take precedence over defaults but CLI flags override environment variables. Example: MCP_TRANSPORT=http MCP_PORT=8080 python -m browser_bookmarks_tools runs HTTP mode on port 8080 without CLI arguments. The server registers the FastAPI application with CORS middleware configured for the web dashboard (port 10802), Tauri desktop client (tauri://localhost), and local development origins.

## 23. Firefox Tag Storage Architecture Deep Dive

Firefox's moz_keywords table uses a unique constraint on (keyword, place_id) allowing the same tag on multiple bookmarks but preventing duplicate tags on the same bookmark. When tags are added via firefox_tagging operation=add_tags, the server inserts rows into moz_keywords and links them via the keyword_index table. The operation is transactional -- if any insertion fails the entire operation is rolled back to prevent partial tagging. Firefox's tagging system is exposed in the browser UI through the Library window (Bookmarks > Show All Bookmarks > Tags column) and the bookmark properties dialog. Tags appear as comma-separated values in the bookmark editing panel. Tags are also searchable from the Firefox address bar using keyword:tag_name syntax (e.g. keyword:reference filters bookmarks tagged reference). The server preserves these Firefox-native tag behaviors. External Firefox add-ons that use the tag system (like "Auto Tag", "TagSieve") are compatible with tags created by the MCP server since both use the same moz_keywords table. Tag operations require Firefox to be closed because SQLite writes to places.sqlite are locked while Firefox is running. The server checks for the lock file (places.sqlite-wal and places.sqlite-shm) and returns a clear error if Firefox is running, suggesting the user close Firefox before tagging operations.

## 24. Performing a Full Cross-Browser Audit

Complete audit workflow for a thorough bookmark inventory: 1) Detect all browsers on the system by calling chromium_browsers, gecko_browsers, and safari_browsers. 2) For each detected browser, read all bookmarks using browser_bookmarks operation=list with the appropriate browser parameter. 3) Run bookmarks_stats_ui on each browser to get statistical overview (total count, top domains, oldest/newest bookmarks, folder depth, tags in use). 4) Use find_duplicate_tags or the tag statistics tool to identify tag inconsistencies across browsers. 5) Run backup_restore operation=create_backup for each browser before making changes. 6) For cross-browser deduplication, use sync_bookmarks with all detected browsers listed and strategy=deduplicate. 7) Use ai_bookmark_portmanteau operation=organize to present an AI-generated reorganization suggestion based on the full audit results. 8) Review the suggestions and apply acceptable changes through targeted tool calls. 9) Create a final backup recording the clean state. 10) Export the complete inventory as JSON for off-system archiving using export_bookmarks_download format=json.

## 25. Bookmark Data Export Format Reference

The export_bookmarks_download with format=json produces structured JSON: root object with export_metadata (date, source_browser, bookmark_count, version), structure containing the folder hierarchy as nested objects with id, parent_id, name, type (folder/separator), and children (array of nested folder/bookmark objects), and items array containing all bookmarks as flat list with id, title, url, folder_path, date_added_iso, date_modified_iso, tags, notes, metadata (enriched_title, og_description, og_image, last_fetched). The HTML export (format=html) produces a standards-compliant bookmark file with DOCTYPE html, meta charset, title element, and nested DL structure. DL contains DT elements for folder names (H3), bookmark links (A with HREF), and separators (HR). The file can be imported into any browser. The CSV export (format=csv) produces UTF-8 BOM-prefixed CSV with header row: id, title, url, folder_path, date_added, date_modified, tags, notes, browser, profile. The CSV is compatible with Excel and Google Sheets. The JSON export is the richest format preserving all metadata.

## 26. Troubleshooting Firewall and Permission Issues

Complete guide for resolving access problems: Windows permission errors: Run your MCP client as the logged-in user (not Administrator, not SYSTEM). Some Chrome profile directories have permission restrictions for non-interactive logins. Firefox places.sqlite read errors: Ensure Firefox is closed. Check for lock files (places.sqlite-wal, places.sqlite-shm). If Firefox crashed, delete these lock files before retrying. Sidecar database corruption: If metadata enrichment fails, delete the sidecar.db file (bookmarks data is preserved in browser-native stores). The server recreates the database on next start. Backup restore failures: Ensure the backup file was created by the same server version. Cross-version restore is supported but metadata format differences may occur. Network timeout for enrichment: The metadata enrichment system has a 10-second HTTP timeout per URL. For large collections, enrichment runs in the background with rate limiting. Web dashboard connection refused: Ensure the server is running in HTTP mode (--http flag) and the port is not blocked by firewall. Default port is 10803 for the REST API.

## 27. Firefox Performance Optimization for Large Libraries

Firefox places.sqlite performance degrades with very large bookmark collections. Optimization tips: run Firefox's built-in maintenance (Library > All Bookmarks > Maintenance > Check Integrity and Maintenance > Run Maintenance), periodically create and restore from backup to defragment the database, use folder-based organization rather than thousands of flat bookmarks for better SQLite query performance, and run database VACUUM using firefox_utils operation=check_db_integrity which reports fragmentation. The server's tagging performance is dependent on places.sqlite index efficiency. For libraries over 50000 bookmarks, tag operations may take 2-5 seconds. For libraries over 100000 bookmarks, consider using Chromium-based browsers which have faster bookmark storage (JSON file vs SQLite database).

## 28. Server Transport Configuration

The server supports three transport modes: stdio (default, communicates with MCP client via stdin/stdout JSON-RPC, ideal for Claude Desktop), http (FastAPI-based HTTP Streamable transport for web integration and REST API access, default port 10803), and sse (legacy SSE transport for backward compatibility, deprecated). The transport mode is configured via the MCP_TRANSPORT environment variable or CLI flags. In HTTP mode, the server also serves a SOTA React web dashboard for visual bookmark management. The HTTP server supports CORS for cross-origin access and can be configured to bind to a specific host and port. For production deployments, run behind a reverse proxy (nginx, IIS) for TLS termination and authentication.

## 29. Browser-Specific Bookmark Location Reference

Chrome/Edge bookmarks file: %LOCALAPPDATA%/Google/Chrome/User Data/Default/Bookmarks (Chrome), %LOCALAPPDATA%/Microsoft/Edge/User Data/Default/Bookmarks (Edge). Firefox places.sqlite file: %APPDATA%/Mozilla/Firefox/Profiles/{profile}/places.sqlite. Brave bookmarks: %LOCALAPPDATA%/BraveSoftware/Brave-Browser/User Data/Default/Bookmarks. Opera bookmarks: %APPDATA%/Opera Software/Opera Stable/Bookmarks. Safari bookmarks (macOS): ~/Library/Safari/Bookmarks.plist. The server detects these paths automatically but custom locations are supported by directly calling the browser read tools with explicit paths. Each browser handles bookmark files differently (JSON for Chromium, SQLite for Firefox, plist for Safari). The server normalizes all formats into the same bookmark model for cross-browser operations.

## 30. Version History and Changelog

The server follows semantic versioning (MAJOR.MINOR.PATCH). The version is reported via the health and status endpoints. Breaking changes are documented in the server's CHANGELOG. Major version increments indicate backward-incompatible tool signature changes. Minor version increments add new tools and operations. Patch version increments fix bugs without API changes. The server version is available via the health tool and REST API.

## 31. BrowserBookmarksTool Architecture

The core browser_bookmarks portmanteau tool reads bookmarks from any supported browser using browser-specific backends. The backend for each browser normalizes the bookmark data into a common format: title (str), url (str), folder_path (str), date_added (ISO datetime), date_modified (ISO datetime), tags (list of str), and metadata (dict). The common format enables cross-browser comparison and sync operations. The architecture supports adding new browser backends by implementing the browser-specific reader and registering it in the tool's dispatch table. The server handles browser-specific quirks: Chromium's WebKit timestamp conversion from microseconds since 1601 to ISO datetime, Firefox's folder type differentiation (bookmark vs folder vs separator vs dynamic container), and Safari's Reading List item handling.

## 32. Data Privacy and Security

The server handles bookmark data which may contain sensitive URLs, passwords, and personal browsing history. Security practices: all bookmark data is processed locally on the machine where the server runs. No bookmark data is sent to external services except metadata enrichment (optional HTTP title fetching). The activity log stores operation metadata without bookmark content. The backup files contain the full bookmark tree and should be stored securely. The REST API supports optional authentication. The server does not log bookmark URLs by default. Users handling sensitive bookmarks should disable metadata enrichment or configure it to use local-only sources.

## 33. Scripting and Automation

Advanced users can script bookmark operations through the REST API. Example automation workflow: 1) Set up a scheduled task (Windows Task Scheduler) to run daily bookmark backup. 2) The script calls backup_restore(operation=create_backup, browser=chrome) and backup_restore(operation=create_backup, browser=firefox). 3) The script checks backup success by verifying the response success field. 4) Export a daily bookmark summary: export_bookmarks_download(browser=chrome, format=csv). 5) Delete backups older than 30 days: enumerate backup_restore(operation=list_backups), compare timestamps, call backup_restore(operation=delete_backup) for old entries. 6) The REST API POST /api/v1/control/{tool_name} enables calling any tool from any programming language with HTTP. Example curl: curl -X POST http://localhost:10803/api/v1/control/backup_restore -H "Content-Type: application/json" -d '{"operation":"create_backup","browser":"chrome"}' This automation capability allows integrating bookmark management into broader IT workflows including backup rotations, compliance reporting, and cross-team bookmark sharing.