"""Cross-browser profile backup and restore (single + batch)."""

from __future__ import annotations

import shutil
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from browser_bookmarks_tools.services.browser.chromium_registry import (
    is_chromium_browser,
    list_chromium_browser_ids,
)
from browser_bookmarks_tools.services.browser.gecko_paths import resolve_profile_directory
from browser_bookmarks_tools.services.browser.gecko_paths import parse_profiles_ini
from browser_bookmarks_tools.services.browser.gecko_registry import (
    is_gecko_browser,
    list_gecko_browser_ids,
)
from browser_bookmarks_tools.services.browser.safari_registry import (
    is_safari_browser,
    resolve_safari_bookmarks_plist,
    safari_supported_on_platform,
)
from browser_bookmarks_tools.services.browser.chromium_manager import ChromiumManager


def default_backup_root() -> Path:
    root = Path.home() / ".bookmarks-mcp" / "backups"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _timestamp() -> str:
    return datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")


async def list_backup_targets() -> dict[str, Any]:
    targets: list[dict[str, Any]] = []

    for browser_id in list_gecko_browser_ids():
        profiles = list(parse_profiles_ini(browser_id).keys()) or ["default"]
        for profile_name in profiles:
            profile_dir = resolve_profile_directory(browser_id, profile_name)
            targets.append(
                {
                    "browser": browser_id,
                    "browser_family": "gecko",
                    "profile_name": profile_name,
                    "available": profile_dir is not None and profile_dir.exists(),
                }
            )

    for browser_id in list_chromium_browser_ids():
        manager = ChromiumManager(browser_id)
        profiles: list[str] = []
        if manager.user_data_dir and manager.user_data_dir.exists():
            try:
                profiles = await manager.get_profiles()
            except Exception:
                profiles = []
        if not profiles:
            targets.append(
                {
                    "browser": browser_id,
                    "browser_family": "chromium",
                    "profile_name": "Default",
                    "available": False,
                }
            )
            continue
        for profile_name in profiles:
            targets.append(
                {
                    "browser": browser_id,
                    "browser_family": "chromium",
                    "profile_name": profile_name,
                    "available": True,
                }
            )

    if safari_supported_on_platform():
        plist = resolve_safari_bookmarks_plist()
        targets.append(
            {
                "browser": "safari",
                "browser_family": "safari",
                "profile_name": "default",
                "available": plist is not None,
            }
        )

    return {"success": True, "targets": targets, "count": len(targets)}


async def backup_browser_profile(
    browser: str,
    profile_name: str | None = None,
    backup_destination: str | None = None,
) -> dict[str, Any]:
    browser_key = browser.lower()
    profile = profile_name or "Default"
    dest = Path(backup_destination) if backup_destination else default_backup_root()
    dest.mkdir(parents=True, exist_ok=True)

    if is_gecko_browser(browser_key):
        profile_dir = resolve_profile_directory(browser_key, profile_name or "default")
        if profile_dir is None or not profile_dir.exists():
            return {
                "success": False,
                "browser": browser_key,
                "profile_name": profile_name or "default",
                "error": f"Gecko profile not found: {browser_key}/{profile_name or 'default'}",
            }
        archive_base = dest / f"{browser_key}_{profile_name or 'default'}_{_timestamp()}"
        backup_file = shutil.make_archive(str(archive_base), "zip", str(profile_dir))
        return {
            "success": True,
            "browser": browser_key,
            "browser_family": "gecko",
            "profile_name": profile_name or "default",
            "backup_path": backup_file,
        }

    if is_chromium_browser(browser_key):
        manager = ChromiumManager(browser_key)
        chromium_profile = profile if profile != "default" else "Default"
        backup_file = await manager.backup_profile(chromium_profile, str(dest))
        return {
            "success": True,
            "browser": browser_key,
            "browser_family": "chromium",
            "profile_name": chromium_profile,
            "backup_path": backup_file,
        }

    if is_safari_browser(browser_key):
        if not safari_supported_on_platform():
            return {"success": False, "browser": "safari", "error": "Safari backup requires macOS"}
        plist = resolve_safari_bookmarks_plist()
        if plist is None or not plist.exists():
            return {"success": False, "browser": "safari", "error": "Safari Bookmarks.plist not found"}
        archive_base = dest / f"safari_default_{_timestamp()}"
        backup_file = f"{archive_base}.zip"
        with zipfile.ZipFile(backup_file, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.write(plist, arcname="Bookmarks.plist")
        return {
            "success": True,
            "browser": "safari",
            "browser_family": "safari",
            "profile_name": "default",
            "backup_path": backup_file,
        }

    return {"success": False, "browser": browser, "error": f"Unsupported browser: {browser}"}


async def restore_browser_profile(
    browser: str,
    backup_file: str,
    profile_name: str | None = None,
    *,
    overwrite: bool = False,
) -> dict[str, Any]:
    browser_key = browser.lower()
    backup_path = Path(backup_file)
    if not backup_path.exists():
        return {"success": False, "error": f"Backup file not found: {backup_file}"}

    if is_gecko_browser(browser_key):
        profile_dir = resolve_profile_directory(browser_key, profile_name or "default")
        if profile_dir is None:
            return {"success": False, "error": "Target gecko profile directory not found"}
        if profile_dir.exists() and not overwrite:
            return {
                "success": False,
                "error": "Profile exists; set overwrite=True to restore",
                "profile_path": str(profile_dir),
            }
        profile_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(backup_path, "r") as archive:
            archive.extractall(profile_dir)
        return {
            "success": True,
            "browser": browser_key,
            "browser_family": "gecko",
            "profile_name": profile_name or "default",
            "profile_path": str(profile_dir),
        }

    if is_chromium_browser(browser_key):
        manager = ChromiumManager(browser_key)
        chromium_profile = profile_name or "Default"
        result = await manager.restore_profile(chromium_profile, backup_file, overwrite=overwrite)
        result["browser"] = browser_key
        result["browser_family"] = "chromium"
        return result

    if is_safari_browser(browser_key):
        if not safari_supported_on_platform():
            return {"success": False, "error": "Safari restore requires macOS"}
        plist = resolve_safari_bookmarks_plist()
        if plist is None:
            return {"success": False, "error": "Safari Bookmarks.plist path not resolved"}
        if plist.exists() and not overwrite:
            return {"success": False, "error": "Safari plist exists; set overwrite=True"}
        with zipfile.ZipFile(backup_path, "r") as archive:
            archive.extract("Bookmarks.plist", path=str(plist.parent))
        return {
            "success": True,
            "browser": "safari",
            "browser_family": "safari",
            "profile_name": "default",
            "bookmarks_path": str(plist),
        }

    return {"success": False, "error": f"Unsupported browser: {browser}"}


async def batch_backup_profiles(
    *,
    browsers: list[str] | None = None,
    backup_destination: str | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    targets = (await list_backup_targets())["targets"]
    if browsers:
        allowed = {b.lower() for b in browsers}
        targets = [t for t in targets if t["browser"] in allowed]

    planned = [t for t in targets if t.get("available")]
    if dry_run:
        return {
            "success": True,
            "status": "planned",
            "dry_run": True,
            "count": len(planned),
            "backup_destination": str(backup_destination or default_backup_root()),
            "targets": planned,
        }

    results: list[dict[str, Any]] = []
    for target in planned:
        result = await backup_browser_profile(
            target["browser"],
            target.get("profile_name"),
            backup_destination,
        )
        results.append(result)

    succeeded = sum(1 for item in results if item.get("success"))
    return {
        "success": succeeded == len(results),
        "status": "done",
        "attempted": len(results),
        "succeeded": succeeded,
        "failed": len(results) - succeeded,
        "results": results,
    }


async def batch_restore_profiles(
    restore_plan: list[dict[str, Any]],
    *,
    overwrite: bool = False,
    dry_run: bool = True,
) -> dict[str, Any]:
    if dry_run:
        return {
            "success": True,
            "status": "planned",
            "dry_run": True,
            "count": len(restore_plan),
            "plan": restore_plan[:20],
        }

    results: list[dict[str, Any]] = []
    for item in restore_plan:
        backup_file = item.get("backup_file") or item.get("backup_path")
        if not backup_file:
            results.append({"success": False, "error": "backup_file required", "item": item})
            continue
        result = await restore_browser_profile(
            item["browser"],
            backup_file,
            item.get("profile_name"),
            overwrite=overwrite,
        )
        results.append(result)

    succeeded = sum(1 for item in results if item.get("success"))
    return {
        "success": succeeded == len(results) if results else False,
        "status": "done",
        "attempted": len(results),
        "succeeded": succeeded,
        "failed": len(results) - succeeded,
        "results": results,
    }
