# Mobile browser import workflow

Most mobile browsers do not expose bookmark files to MCP tools directly. Use **export → import** instead.

## Samsung Internet (Android)

1. Samsung Internet → **Bookmarks** → **⋮** → **Export bookmarks**
2. Transfer the exported HTML file to your PC (USB, cloud drive, email)
3. Import into bookmarks-mcp:

```json
{
  "name": "browser_bookmarks",
  "arguments": {
    "operation": "import_html",
    "browser": "chrome",
    "profile_name": "Default",
    "import_path": "D:\\Downloads\\samsung_bookmarks.html",
    "dry_run": true
  }
}
```

4. Set `"dry_run": false` to write bookmarks into the target browser.

## iOS Safari

1. On Mac: Safari → **File → Export Bookmarks…** (HTML)
2. Or sync via iCloud and export from macOS Safari
3. Import with `import_html` targeting `safari` on macOS

## Preserve descriptions and tags (sidecar)

Mobile HTML exports rarely include descriptions. Use the **sidecar metadata DB** for enrichment:

| Field | Native browser | Sidecar (`bookmark_metadata`) |
|-------|----------------|--------------------------------|
| title, url, folder | yes | optional mirror |
| description | Firefox only | yes |
| user comment | no | yes |
| tags (portable) | Firefox / HTML TAGS attr | yes |
| starred (0–5) | no | yes |
| read_count / last_read_at | no | yes |

**DB location:** `~/.bookmarks-mcp/metadata.db`  
**Override:** set `BOOKMARKS_MCP_DATA_DIR`

### Examples

Import mobile HTML metadata only (no browser write):

```json
{
  "name": "browser_bookmarks",
  "arguments": {
    "operation": "import_html",
    "browser": "import",
    "import_path": "/path/to/export.html",
    "import_to_metadata": true,
    "dry_run": false
  }
}
```

Set metadata for a URL:

```json
{
  "name": "bookmark_metadata",
  "arguments": {
    "operation": "set_metadata",
    "url": "https://example.com",
    "browser": "chrome",
    "profile_name": "Default",
    "description": "Project docs",
    "tags": ["work", "docs"],
    "starred": 5,
    "user_comment": "Check release notes monthly"
  }
}
```

List bookmarks with sidecar merged:

```json
{
  "name": "browser_bookmarks",
  "arguments": {
    "operation": "list_bookmarks",
    "browser": "chrome",
    "include_metadata": true,
    "limit": 50
  }
}
```

## Scope model

Sidecar rows are keyed by `(url, browser, profile_name)`.

- **Scoped:** same URL in Chrome Default vs Firefox work profile can have different notes
- **Global fallback:** rows with empty `browser` and `profile_name` apply when no scoped row exists
- **Gecko native tags** remain in `places.sqlite`; sidecar tags are portable across browsers
