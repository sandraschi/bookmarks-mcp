# Bookmarks MCP — User Guide

## Quick start

1. Install the `.mcpb` bundle in Claude Desktop (drag-and-drop).
2. Ask: "List my Chrome bookmarks" or "Search Firefox bookmarks for python".
3. For cross-browser copy: "Preview syncing Firefox bookmarks to Edge" (dry run first).

## Common requests

### List and search

```
List bookmarks in Chrome
Search my Firefox default profile for "kubernetes"
Show the next page of Firefox bookmarks (offset 100, limit 50)
Find bookmarks tagged "dev" in Firefox
```

### Add, edit, delete

```
Add https://example.com to Chrome bookmarks folder "Dev"
Rename my Firefox bookmark for example.com to "Example Site"
Delete the Chrome bookmark with URL https://old.example.com
```

### Sync between browsers

```
Preview sync from Firefox to Brave (dry run)
Sync Firefox bookmarks to Edge for real
Copy new Chrome bookmarks into Firefox
```

### Firefox profiles

```
List all Firefox profiles
Create a Firefox profile named "research"
Suggest portmanteau profile combinations
Create a portmanteau profile "dev-cooking" from developer_tools and cooking presets
```

### Tagging (Firefox)

```
Tag all bookmarks in folder "Archive/2024" with prefix "archive-2024"
Batch tag bookmarks from year 2023 with prefix "y2023"
Preview folder tagging without applying (dry run)
```

### Backup and curated sources

```
Backup Firefox bookmarks for profile default
List curated bookmark sources
Import curated source "awesome_python"
```

### AI curation

```
Categorize bookmarks in Firefox profile work
Find duplicate bookmarks in Firefox profile default
Curate bookmarks from awesome_repos about python and ai
Clean up broken links in profile work
```

### Chrome profile admin

```
List Chrome profiles
Check if Chrome is running
Get bookmarks database path for Chrome profile Default
```

## Tips

- **Close Firefox** before writes that modify `places.sqlite`.
- Use **dry_run=True** on sync and bulk tagging until the user confirms.
- Use **pagination** (`limit`, `offset`) for large libraries.
- Prefer **`browser_bookmarks`** for everyday tasks; use specialized portmanteau tools when the operation is Firefox- or Chrome-specific.

## Troubleshooting

| Problem | What to try |
|---------|-------------|
| Database locked | Close the browser; retry; Firefox: `force_access=True` |
| Empty Chromium results | Verify browser installed; check Default profile exists |
| Sync skipped duplicates | Expected — review dry-run diff before forcing |
| Unknown operation | Check `available_operations` in the error payload |
