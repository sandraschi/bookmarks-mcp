"""Utility functions for Gecko bookmark management (Firefox and forks)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from browser_bookmarks_tools.services.browser.gecko_paths import (
    get_profiles_ini_path as _get_profiles_ini_path,
    parse_profiles_ini as _parse_profiles_ini,
    resolve_places_db_path,
    resolve_profile_directory,
)


def get_platform() -> str:
    if os.name == "nt":
        return "windows"
    if os.name == "posix" and "darwin" in os.uname().sysname.lower():
        return "darwin"
    return "linux"


def get_profiles_ini_path(browser_id: str = "firefox") -> Path | None:
    return _get_profiles_ini_path(browser_id)


def parse_profiles_ini(browser_id: str = "firefox") -> dict[str, dict[str, Any]]:
    return _parse_profiles_ini(browser_id)


def get_profile_directory(profile_name: str | None = None, browser_id: str = "firefox") -> Path | None:
    return resolve_profile_directory(browser_id, profile_name)


def get_places_db_path(profile_name: str | None = None, browser_id: str = "firefox") -> Path | None:
    return resolve_places_db_path(browser_id, profile_name)


def get_firefox_platform() -> dict[str, Any]:
    platform = get_platform()
    return {"platform": platform, "os_name": os.name, "message": f"Detected platform: {platform}"}


def get_firefox_profiles(browser_id: str = "firefox") -> dict[str, Any]:
    profiles = parse_profiles_ini(browser_id)
    profiles_ini_path = get_profiles_ini_path(browser_id)
    return {
        "profiles": profiles,
        "profiles_ini_path": str(profiles_ini_path) if profiles_ini_path else None,
        "count": len(profiles),
        "browser": browser_id,
        "message": f"Found {len(profiles)} profile(s) for {browser_id}",
    }


def get_firefox_profile_directory(profile_name: str | None = None, browser_id: str = "firefox") -> dict[str, Any]:
    profile_dir = get_profile_directory(profile_name, browser_id)
    if not profile_dir:
        return {
            "success": False,
            "message": f"Profile '{profile_name or 'default'}' not found for {browser_id}",
            "profile_directory": None,
        }
    return {
        "success": True,
        "profile_name": profile_name,
        "browser": browser_id,
        "profile_directory": str(profile_dir),
        "message": f"Found profile directory: {profile_dir}",
    }


def get_firefox_places_db_path(profile_name: str | None = None, browser_id: str = "firefox") -> dict[str, Any]:
    db_path = get_places_db_path(profile_name, browser_id)
    if not db_path:
        return {
            "success": False,
            "message": f"Could not find places.sqlite for {browser_id} profile '{profile_name or 'default'}'",
            "database_path": None,
        }
    return {
        "success": True,
        "profile_name": profile_name,
        "browser": browser_id,
        "database_path": str(db_path),
        "exists": db_path.exists(),
        "message": f"Found places.sqlite at: {db_path}",
    }
