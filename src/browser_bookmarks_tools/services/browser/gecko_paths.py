"""Gecko profile and places.sqlite path resolution."""

from __future__ import annotations

import configparser
from pathlib import Path
from typing import Any

from browser_bookmarks_tools.services.browser.gecko_registry import (
    GeckoProfileLayout,
    get_gecko_spec,
    is_gecko_browser,
    list_gecko_browser_ids,
    list_gecko_browsers,
    resolve_install_root,
)


def get_profiles_ini_path(browser_id: str = "firefox") -> Path | None:
    spec = get_gecko_spec(browser_id)
    if spec.profile_layout == GeckoProfileLayout.SINGLE_PROFILE:
        return None

    root = resolve_install_root(browser_id)
    if root is None:
        return None

    profiles_ini = root / "profiles.ini"
    if profiles_ini.exists():
        return profiles_ini

    parent_ini = root.parent / "profiles.ini"
    if parent_ini.exists():
        return parent_ini

    return None


def _profile_ini_value(profile: dict[str, Any], key: str) -> str | None:
    lower_key = key.lower()
    for option, value in profile.items():
        if option.lower() == lower_key:
            return value
    return None


def parse_profiles_ini(browser_id: str = "firefox") -> dict[str, dict[str, Any]]:
    profiles_ini = get_profiles_ini_path(browser_id)
    if not profiles_ini or not profiles_ini.exists():
        return {}

    config = configparser.ConfigParser()
    config.read(profiles_ini)

    profiles: dict[str, dict[str, Any]] = {}
    for section in config.sections():
        if section.startswith("Profile"):
            profile = dict(config[section])
            path_value = _profile_ini_value(profile, "Path")
            if path_value:
                name_value = _profile_ini_value(profile, "Name") or path_value
                profiles[name_value] = profile
    return profiles


def resolve_profile_directory(browser_id: str, profile_name: str | None = None) -> Path | None:
    spec = get_gecko_spec(browser_id)

    if spec.profile_layout == GeckoProfileLayout.SINGLE_PROFILE:
        root = resolve_install_root(browser_id)
        if root is None:
            return None
        if (root / "places.sqlite").exists():
            return root
        return root if root.is_dir() else None

    profiles = parse_profiles_ini(browser_id)
    if not profiles:
        return None

    selected = profile_name
    if not selected:
        for name, profile in profiles.items():
            if (_profile_ini_value(profile, "Default") or "0") == "1":
                selected = name
                break
        else:
            selected = next(iter(profiles.keys()), None)

    if not selected or selected not in profiles:
        return None

    profile = profiles[selected]
    profiles_ini = get_profiles_ini_path(browser_id)
    if profiles_ini is None:
        return None

    path_value = _profile_ini_value(profile, "Path")
    if not path_value:
        return None

    is_relative = (_profile_ini_value(profile, "IsRelative") or "1") == "1"
    if is_relative:
        return profiles_ini.parent / path_value
    return Path(path_value)


def resolve_places_db_path(browser_id: str, profile_name: str | None = None) -> Path | None:
    profile_dir = resolve_profile_directory(browser_id, profile_name)
    if not profile_dir:
        return None
    return profile_dir / "places.sqlite"


__all__ = [
    "get_profiles_ini_path",
    "is_gecko_browser",
    "list_gecko_browser_ids",
    "list_gecko_browsers",
    "parse_profiles_ini",
    "resolve_places_db_path",
    "resolve_profile_directory",
]
