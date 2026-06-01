# bookmarks-mcp — Technical Assessment

**Repository**: `D:\Dev\repos\bookmarks-mcp`  
**Version assessed**: `0.2.0` (pyproject / manifest)  
**Assessment date**: 2026-06-01  
**Scope**: MCP tools, browser backends, web dashboard, tests, docs accuracy, extension to all commonly used browsers

---

## Executive summary

bookmarks-mcp is a **FastMCP 3.3 multi-portmanteau server** with a strong **Firefox-first** implementation (~35 modules under `tools/firefox/`) and a thinner **Chromium JSON layer** shared by Chrome, Edge, and Brave. The universal entry point `browser_bookmarks` works, but **feature parity is heavily skewed toward Firefox**. Documentation and changelog still claim **Safari (plist) support**, which **does not exist in source**.

The highest-value path to “all browsers in general use” is **not** N separate copy-paste modules (chrome/, edge/, brave/ today). It is:

1. **One Chromium adapter** driven by a browser registry (paths + process names + profile layout).
2. **One Gecko adapter** with per-fork path overrides (Firefox, Zen, LibreWolf, Waterfox, Tor).
3. **One Safari adapter** (macOS plist) as a separate storage family.
4. **Wire `BaseBrowserManager` / `ChromeManager` into `browser_bookmarks`** instead of parallel thin wrappers.

Estimated effort to cover **~90% of desktop users**: **2–3 weeks** focused refactor + tests. Full feature parity across families: **6–8 weeks**.

---

## What works today

### MCP surface (9 registered tools)

| Tool | Primary browser scope | Maturity |
|------|----------------------|----------|
| `browser_bookmarks` | firefox, chrome, edge, brave | Firefox: full ops; Chromium: CRUD + search only |
| `sync_bookmarks` | firefox ↔ chromium quartet | URL/title transfer; no folder tree |
| `firefox_profiles` | Firefox | Production-ready |
| `firefox_backup` | Firefox | Production-ready |
| `firefox_curated` | Firefox | Niche / curated lists |
| `firefox_tagging` | Firefox | Tag automation |
| `firefox_utils` | Firefox | Paths, locks, DB info |
| `chrome_profiles` | Chrome | Uses `ChromeManager`; multi-profile aware |
| `ai_bookmark_portmanteau` | Firefox (`places.sqlite`) | Scrape + heuristics; not LLM-backed |

Smoke test (`tests/unit/test_portmanteau_smoke.py`) confirms all nine tools register.

### Storage backends implemented

| Family | Browsers wired in code | Storage | Write lock behaviour |
|--------|------------------------|---------|-------------------|
| **Gecko** | `firefox` | `places.sqlite` | Must close browser (optional `force_access` read bypass) |
| **Chromium JSON** | `chrome`, `edge`, `brave` | `User Data/<Profile>/Bookmarks` | File rewrite; browser open is risky |
| **Safari plist** | *none* | — | — |

### Non-MCP deliverables

- **Web dashboard** (`web_sota/` + FastAPI `web.py`): CRUD, tree, search, sync wizard, activity log.
- **HTTP transport** on port 10803; frontend 10802; optional Tauri shell.
- **MCPB manifest** present (`manifest.json`, v0.2.0) — prior “no MCPB” fleet note is obsolete.
- **Industrial tooling**: Ruff, Justfile, pytest (minimal suite).

---

## Architecture snapshot

```
browser_bookmarks (portmanteau)
├── firefox  → firefox_bookmarks → tools/firefox/*  (SQLite, 20+ operations)
└── chrome|edge|brave → tools/{chrome,edge,brave}/__init__.py
                        └── chromium_common.py (read/write JSON, Default paths)

Parallel (mostly unused in portmanteau):
├── services/browser/base_browser.py   (abstract interface)
└── services/browser/chrome_core.py    (ChromeManager — only chrome_profiles uses it)

sync_bookmarks → list_* / add_* per browser (flat URL list)
```

**Key structural issue**: two competing Chromium stacks — `chromium_common` + per-browser `__init__.py` wrappers **vs** `ChromeManager` with proper profile discovery. `browser_bookmarks` uses the former and **hardcodes Default profile paths**; `chrome_profiles` uses the latter and supports Profile 1, Profile 2, etc.

---

## Browser support matrix

### Tier A — must support (global desktop share)

| Browser | Engine | Status in repo | Gap severity |
|---------|--------|----------------|--------------|
| **Google Chrome** | Chromium | Partial | Medium — Default profile only in `CHROME_BOOKMARK_PATHS` |
| **Microsoft Edge** | Chromium | Partial | Medium — same as Chrome |
| **Mozilla Firefox** | Gecko | **Full** | Low — reference implementation |
| **Apple Safari** | WebKit | **Not implemented** (docs lie) | **Critical** |
| **Brave** | Chromium | Partial | Medium — duplicate of Chrome pattern |
| **Opera** | Chromium | Missing | High — same JSON format, different path |
| **Vivaldi** | Chromium | Missing | High |
| **Arc** | Chromium | Missing | Medium (macOS-heavy) |
| **Chromium** (OSS) | Chromium | Missing | Medium (Linux default) |

### Tier B — meaningful niche / fork coverage

| Browser | Engine | Notes | Recommended approach |
|---------|--------|-------|---------------------|
| **Zen Browser** | Gecko | Firefox fork | Gecko registry entry |
| **LibreWolf / Waterfox** | Gecko | Hardened Firefox forks | Gecko registry entry |
| **Tor Browser** | Gecko | Isolated profile paths | Gecko registry + safety warnings |
| **Yandex / Sidekick / Coc Coc** | Chromium | Regional Chromium shells | Chromium registry entry |
| **Samsung Internet** | Chromium (mobile) | No desktop JSON path | Export/import (HTML) only |
| **DuckDuckGo browser** | Chromium-based | Growing share | Chromium registry entry |

### Tier C — legacy / out of scope unless requested

| Browser | Reason to defer |
|---------|-----------------|
| Internet Explorer | Retired; bookmark migration only via export |
| Legacy Edge (EdgeHTML) | Replaced; different storage |
| Netscape / ancient | Import-only |

---

## Feature parity matrix

Operations exposed on `browser_bookmarks` (`operation_types.py`):

| Operation | Firefox | Chrome | Edge | Brave | Target (all Tier A) |
|-----------|:-------:|:------:|:----:|:-----:|:-------------------:|
| list_bookmarks | ✅ | ✅ | ✅ | ✅ | ✅ |
| get_bookmark | ✅ | ✅ | ✅ | ✅ | ✅ |
| add_bookmark | ✅ | ✅ | ✅ | ✅ | ✅ |
| edit_bookmark | ✅ | ✅ | ✅ | ✅ | ✅ |
| delete_bookmark | ✅ | ✅ | ✅ | ✅ | ✅ |
| search / search_bookmarks | ✅ | ✅ | ✅ | ✅ | ✅ |
| sync_bookmarks | ✅ | ✅ | ✅ | ✅ | ✅ (with folders) |
| find_duplicates | ✅ | ❌ | ❌ | ❌ | ✅ (Chromium + Safari) |
| export_bookmarks | ✅ | ❌ | ❌ | ❌ | ✅ (HTML/JSON/Netscape) |
| list_tags | ✅ | ❌ | ❌ | ❌ | N/A Chromium; ✅ Safari keywords |
| batch_update_tags | ✅ | ❌ | ❌ | ❌ | Gecko only |
| tag merge/cleanup ops | ✅ | ❌ | ❌ | ❌ | Gecko only |
| find_old / forgotten | ✅ | ❌ | ❌ | ❌ | ✅ (use `date_added` in JSON) |
| find_broken_links | ✅ | ❌ | ❌ | ❌ | ✅ (browser-agnostic HTTP) |
| get_bookmark_stats | ✅ | ❌ | ❌ | ❌ | ✅ |
| refresh_bookmarks | ✅ | ❌ | ❌ | ❌ | Low priority |

**Firefox-only MCP tools** (6/9): profiles, backup, curated, tagging, utils, AI portmanteau — acceptable if documented as Gecko-exclusive, but several (backup, broken links, export, dedupe) are **browser-agnostic** and should lift to `browser_bookmarks`.

---

## Gaps analysis

### Critical

| ID | Gap | Evidence | Impact |
|----|-----|----------|--------|
| C1 | **Safari claimed, not built** | README + CHANGELOG mention plist; `grep safari` in `src/` = 0 | User/agent trust; macOS users blocked |
| C2 | **Chromium stuck on Default profile** | `CHROME_BOOKMARK_PATHS` etc. point to `...\Default\Bookmarks` only | Multi-profile Chrome/Edge users see wrong data |
| C3 | **Dual Chromium architectures** | `chromium_common` vs `ChromeManager`; portmanteau uses weaker path | Bugs, drift, duplicate fixes |
| C4 | **`browser_bookmarks` ignores `profile_name` for Chromium** | Docstring: “Used only for Firefox” | `chrome_profiles` can list Profile 1; CRUD cannot target it |
| C5 | **Sync drops folder hierarchy** | `sync_tools._normalize` → `{title, url}` only | Cross-browser migration loses organization |

### Important

| ID | Gap | Evidence | Impact |
|----|-----|----------|--------|
| I1 | **No browser registry / auto-discovery** | Hardcoded path lists per browser | Every new Chromium browser = new module |
| I2 | **Advanced ops Firefox-only without clear agent guidance** | Error message points to Firefox | Agents retry wrong browser |
| I3 | **Chromium search loads entire bookmark set** | `browser_bookmarks` lists all then filters | Slow on 10k+ bookmarks |
| I4 | **Lock detection brittle for Chromium** | `ChromeManager.is_database_locked` checks `chrome.exe` substring | False positives/negatives (Edge, Brave, Arc) |
| I5 | **Test coverage thin** | 4 test files; no Firefox integration; fixture JSON only | Regressions likely on refactor |
| I6 | **Documentation drift** | README project tree shows `bookmarks/manager.py` — not present | Onboarding friction |
| I7 | **`browsers/` package empty** | `browsers/__init__.py` is empty | Missed central registration point |
| I8 | **AI portmanteau is Firefox-only** | Uses `FirefoxDB` | Dashboard “AI Command” misleading for Chrome users |

### Minor

| ID | Gap | Notes |
|----|-----|-------|
| M1 | License placeholder in README | “Add appropriate license” vs MIT in pyproject |
| M2 | CHANGELOG still says FastMCP 2.13 / Safari added | Stale |
| M3 | `bookmarks/` subpackage stub only | Dead structure |
| M4 | Windows-centric path fallbacks in `chromium_common` | macOS/Linux paths exist in `ChromeManager` but not in portmanteau paths |
| M5 | No HTML/Netscape import/export for universal interchange | Standard migration path |

---

## Extension plan — all browsers in general use

### Design principle: three storage families, one portmanteau

```
                    browser_bookmarks
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    GeckoAdapter    ChromiumAdapter   SafariAdapter
    (places.sqlite) (Bookmarks JSON)  (Bookmarks.plist)
           │               │               │
    firefox, zen,     chrome, edge,     safari
    librewolf,        brave, opera,
    waterfox, tor     vivaldi, arc, …
```

### Phase 1 — Chromium unification (covers ~8 browsers, ~1 week)

**Goal**: Replace `tools/chrome|edge|brave/__init__.py` triplication with one module.

1. Add `services/browser/chromium_registry.py`:

```python
@dataclass(frozen=True)
class ChromiumBrowserSpec:
    id: str                    # "chrome", "edge", "brave", "opera", "vivaldi", …
    display_name: str
    user_data_dirs: list[Path] # platform-ordered candidates
    process_names: set[str]    # for lock detection
    default_profile: str = "Default"
```

2. Register Tier A + B Chromium browsers with platform paths:

| id | Windows User Data (typical) |
|----|----------------------------|
| chrome | `%LOCALAPPDATA%\Google\Chrome\User Data` |
| edge | `%LOCALAPPDATA%\Microsoft\Edge\User Data` |
| brave | `%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data` |
| opera | `%APPDATA%\Opera Software\Opera Stable` *or* `%LOCALAPPDATA%\Opera Software\Opera GX Stable` |
| vivaldi | `%LOCALAPPDATA%\Vivaldi\User Data` |
| arc | `~/Library/Application Support/Arc/User Data` (macOS) |
| chromium | `%LOCALAPPDATA%\Chromium\User Data` / `~/.config/chromium` |

3. Merge `chromium_common` + `ChromeManager` → `ChromiumManager(BaseBrowserManager)`.
4. Route `browser_bookmarks` Chromium branch through `ChromiumManager(spec, profile_name)`.
5. Extend `sync_bookmarks` `_read` / `_write` to use registry keys.
6. Update web dashboard browser selector from registry (`list_supported_browsers()`).

**Acceptance**: CRUD + search on Chrome Profile 1; Opera + Vivaldi list/add; single test fixture per family.

### Phase 2 — Gecko fork registry (~3 days)

**Goal**: One `GeckoManager` with path templates.

| id | Profile root (Windows) |
|----|------------------------|
| firefox | `%APPDATA%\Mozilla\Firefox\Profiles` |
| zen | `%APPDATA%\zen\Profiles` |
| librewolf | `%APPDATA%\LibreWolf\Profiles` |
| waterfox | `%APPDATA%\Waterfox\Profiles` |
| tor | `%LOCALAPPDATA%\Tor Browser\Browser\TorBrowser\Data\Browser\profile.default` (single profile; document caution) |

Reuse existing `tools/firefox/*` by parameterizing profile resolution (`get_places_db_path(browser_id, profile_name)`).

**Acceptance**: `browser_bookmarks(browser="zen", …)` passes smoke CRUD on a test profile.

### Phase 3 — Safari adapter (macOS only, ~1 week)

**Goal**: Honest Tier A coverage on darwin.

1. Read/write `~/Library/Safari/Bookmarks.plist` via `plistlib`.
2. Map WebKit folder tree to shared bookmark dict shape.
3. Document: Safari must be closed; SIP / Full Disk Access may be required on recent macOS.
4. Gate tool with platform check — return structured error on Windows/Linux.

**Acceptance**: list/add/delete on macOS CI runner or documented manual test.

### Phase 4 — Feature lift (browser-agnostic ops, ~2 weeks)

| Operation | Implementation notes |
|-----------|---------------------|
| find_duplicates | URL hash across any adapter |
| export_bookmarks | HTML (Netscape), JSON, CSV from normalized list |
| find_broken_links | httpx HEAD/GET; no browser dependency |
| get_bookmark_stats | Count by folder root, age histogram from `date_added` |
| find_old_bookmarks | Chromium JSON exposes microsecond timestamps |
| sync with folders | Walk source tree; map folders on target; dry-run diff |

Promote **backup/restore** to `chromium_profiles` portmanteau (mirror `firefox_backup`).

### Phase 5 — Interchange & mobile (~1 week, optional)

- **Import**: Netscape HTML, Chrome/Firefox JSON export files (path override — no live browser required).
- **Samsung Internet / mobile**: document export-to-HTML workflow; optional `import_html` operation.

---

## Recommended API changes (non-breaking)

| Change | Rationale |
|--------|-----------|
| Add `browser` enum expansion in errors: `supported_browsers` from registry | Agents pick valid ids dynamically |
| `profile_name` honored for all Chromium browsers | Align with `chrome_profiles` |
| Add optional `bookmarks_path` override on all ops | CI, portable installs, non-default locations |
| Add `browser_family: gecko|chromium|safari` in responses | Helps agents route advanced ops |
| Deprecate separate `tools/chrome`, `tools/edge`, `tools/brave` modules | Re-export from `chromium` for one release |

---

## Test strategy gaps → targets

| Area | Current | Target |
|------|---------|--------|
| Portmanteau registration | 1 smoke test | Keep |
| Chromium CRUD | JSON fixture | + multi-profile fixture + edit/delete |
| Firefox | None in CI | Temp SQLite places DB fixture |
| Sync | None | dry-run + folder-preserving sync golden test |
| Safari | None | macOS-only optional job |
| Registry discovery | None | Parametrize `list_supported_browsers()` per platform |
| Web API | Basic mock | Contract tests per browser id |

---

## Documentation corrections (immediate, no code)

1. Remove Safari from “supported” lists until Phase 3 ships — or mark **planned**.
2. Fix README project tree to match `src/browser_bookmarks_tools/tools/`.
3. Align CHANGELOG with FastMCP 3.3 and actual v0.2.0 scope.
4. Document **profile_name** behaviour per browser family in `MCP_CONFIGURATION.md`.
5. State clearly: **6 tools are Gecko-exclusive**; advanced maintenance requires Firefox or future lifted ops.

---

## Priority roadmap

| Priority | Work item | Closes |
|----------|-----------|--------|
| P0 | Chromium registry + profile_name in `browser_bookmarks` | C2, C3, C4, I1 |
| P0 | Fix Safari documentation or implement Phase 3 | C1 |
| P1 | Folder-aware sync | C5 |
| P1 | Lift export + dedupe + broken links to all adapters | I2, feature matrix |
| P2 | Gecko fork registry (Zen, LibreWolf, Tor) | Tier B |
| P2 | Opera, Vivaldi, Arc registry entries | Tier A gaps |
| P3 | Safari plist adapter | macOS Tier A |
| P3 | HTML import/export | M5, mobile |

---

## Risk register

| Risk | Mitigation |
|------|------------|
| Browser open during JSON write corrupts Bookmarks | Pre-write copy; checksum field; document close-browser |
| Firefox SQLite lock | Keep `force_access` read-only; never write under lock |
| macOS privacy (Safari, Full Disk Access) | Detect permission error; link to System Settings path |
| Tor Browser path / legal sensitivity | Read-only default; explicit flag for writes |
| Agent selects unsupported op on Chromium | Return `supported_operations` + `browser_family` in every error |

---

## Conclusion

bookmarks-mcp is **production-viable for Firefox power users** and **adequate for basic Chromium CRUD on the Default profile**. It is **not yet a universal bookmark MCP** despite README/marketing language.

The fastest route to general-use browser coverage:

1. **Registry-driven Chromium adapter** (eliminates triplicated modules, unlocks Opera/Vivaldi/Arc/Chromium).
2. **Profile-aware portmanteau** (fix the `chrome_profiles` vs `browser_bookmarks` split).
3. **Gecko fork paths** (cheap wins from existing Firefox code).
4. **Safari plist** (macOS credibility).
5. **Lift browser-agnostic intelligence** (export, dedupe, link check, stats) out of Firefox-only modules.

After Phase 1–2, the project supports **all major desktop browsers in general use** with consistent CRUD. After Phase 4, it supports **credible cross-browser migration and maintenance** — the actual user-facing promise of the repo.

---

*Assessment authored 2026-06-01 from source review of `D:\Dev\repos\bookmarks-mcp` (v0.2.0).*
