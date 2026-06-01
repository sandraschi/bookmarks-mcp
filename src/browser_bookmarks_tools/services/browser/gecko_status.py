"""Gecko-family process and database lock checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import psutil

from browser_bookmarks_tools.services.browser.gecko_registry import get_gecko_spec


class GeckoStatusChecker:
    @staticmethod
    def is_browser_running(browser_id: str) -> dict[str, Any]:
        spec = get_gecko_spec(browser_id)
        try:
            matches = []
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    name = (proc.info.get("name") or "").lower()
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                if any(token.lower() in name for token in spec.process_names):
                    matches.append(
                        {
                            "pid": proc.info.get("pid"),
                            "name": proc.info.get("name"),
                            "cmdline": (proc.info.get("cmdline") or [])[:3],
                        }
                    )

            is_running = len(matches) > 0
            return {
                "is_running": is_running,
                "browser": browser_id,
                "process_count": len(matches),
                "processes": matches,
                "message": (
                    f"{spec.display_name} is {'running' if is_running else 'not running'} "
                    f"({len(matches)} processes)"
                ),
            }
        except Exception as exc:
            return {
                "is_running": False,
                "browser": browser_id,
                "error": f"Could not check {spec.display_name} status: {exc!s}",
                "message": f"Unable to determine {spec.display_name} status",
            }

    @staticmethod
    def check_database_access_safe(browser_id: str, profile_path: Path | None = None) -> dict[str, Any]:
        status = GeckoStatusChecker.is_browser_running(browser_id)
        spec = get_gecko_spec(browser_id)

        if status.get("error"):
            return {
                "safe": False,
                "reason": "status_check_failed",
                "message": status["message"],
                "details": status,
            }

        if status["is_running"]:
            return {
                "safe": False,
                "reason": "browser_running",
                "message": (
                    f"{spec.display_name} is currently running. Close it before accessing "
                    "places.sqlite to prevent data corruption."
                ),
                "details": status,
            }

        if profile_path:
            if not profile_path.exists():
                return {
                    "safe": False,
                    "reason": "profile_not_found",
                    "message": f"Profile not found at: {profile_path}",
                    "details": {"profile_path": str(profile_path)},
                }

            places_db = profile_path / "places.sqlite"
            if not places_db.exists():
                return {
                    "safe": False,
                    "reason": "database_not_found",
                    "message": f"places.sqlite not found at: {places_db}",
                    "details": {"database_path": str(places_db)},
                }

        return {"safe": True, "message": f"Safe to access {spec.display_name} databases", "details": status}
