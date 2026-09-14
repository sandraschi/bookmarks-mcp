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

**Platform constraint, not a bookmarks-mcp limitation:** iOS Safari has no
"import bookmarks from a file" feature at all - unlike every desktop browser
(including macOS Safari), there's no Settings screen or share-sheet action
that accepts an HTML bookmarks file. No export *format* choice on our end
changes this; it's an Apple-imposed platform gap. The only way bookmarks
reach iOS Safari is through **iCloud Bookmarks sync** - a shared store that
both macOS/Windows and iOS read from, never a local file transfer.

### With a Mac

1. Safari → **File → Export Bookmarks…** (HTML), or skip straight to step 2
   if you'll write bookmarks into macOS Safari directly
2. Import with `import_html` targeting `safari` on macOS (writes real
   bookmarks into Safari, not just a sidecar note)
3. Enable iCloud Bookmarks sync on the Mac (System Settings → Apple ID →
   iCloud → Safari) and on the iPhone (Settings → [name] → iCloud → Safari) -
   bookmarks appear on iOS automatically, no file transfer step

### Without a Mac (Windows only)

1. Install **iCloud for Windows** and enable its **Bookmarks** feature - it
   installs a browser extension for Edge or Chrome and syncs *that browser's*
   bookmarks into the same iCloud Bookmarks store iOS Safari reads from
2. Write your curated bookmarks into whichever browser iCloud for Windows is
   bound to, using the existing write path (already browser-agnostic, works
   the same as any other add/import):

```json
{
  "name": "browser_bookmarks",
  "arguments": {
    "operation": "import_html",
    "browser": "edge",
    "profile_name": "Default",
    "import_path": "D:\\exports\\curated.html",
    "dry_run": false
  }
}
```

   Or write a single collection's worth (e.g. after curating an "ai"
   collection in the webapp) via repeated `add_bookmark` calls, or export a
   filtered set with `export_bookmarks` (`export_format: "html"`) first, then
   `import_html` that file into Edge/Chrome as above.
3. Enable iCloud Bookmarks sync on the iPhone (Settings → [name] → iCloud →
   Safari) - the Windows browser's bookmarks propagate through iCloud within
   a few minutes, no cable or file transfer

Either path relies on Apple's iCloud sync doing the actual delivery to the
phone; bookmarks-mcp's job stops at "get the right bookmarks into a browser
iCloud is already watching."

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
