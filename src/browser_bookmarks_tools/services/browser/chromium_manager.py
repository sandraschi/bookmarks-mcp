"""Unified Chromium bookmark manager backed by the browser registry."""

from __future__ import annotations

import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import psutil

from browser_bookmarks_tools.services.browser.base_browser import BaseBrowserManager
from browser_bookmarks_tools.services.browser.chromium_registry import (
    ProfileLayout,
    get_chromium_spec,
    resolve_user_data_dir,
)


class ChromiumManager(BaseBrowserManager):
    """Chromium-family bookmark manager (Chrome, Edge, Brave, Opera, Vivaldi, …)."""

    def __init__(self, browser_id: str):
        self.spec = get_chromium_spec(browser_id)
        self.browser_id = self.spec.id
        self.user_data_dir = resolve_user_data_dir(self.browser_id)

    async def get_profiles(self) -> list[str]:
        if self.user_data_dir is None or not self.user_data_dir.exists():
            raise RuntimeError(f"{self.spec.display_name} is not installed or User Data directory not found")

        if self.spec.profile_layout == ProfileLayout.FLAT_PROFILE:
            bookmarks = self.user_data_dir / "Bookmarks"
            return ["Default"] if bookmarks.exists() else []

        profiles: list[str] = []
        default_dir = self.user_data_dir / self.spec.default_profile
        if default_dir.exists() and (default_dir / "Bookmarks").exists():
            profiles.append(self.spec.default_profile)

        for item in self.user_data_dir.iterdir():
            if item.is_dir() and item.name.startswith("Profile ") and (item / "Bookmarks").exists():
                profiles.append(item.name)

        return sorted(profiles)

    async def get_profile_path(self, profile_name: str) -> str:
        if self.user_data_dir is None:
            raise RuntimeError(f"{self.spec.display_name} is not installed")

        if self.spec.profile_layout == ProfileLayout.FLAT_PROFILE:
            if profile_name not in (self.spec.default_profile, "Default"):
                raise RuntimeError(f'{self.spec.display_name} uses a single profile; use "{self.spec.default_profile}"')
            return str(self.user_data_dir)

        profile_path = self.user_data_dir / profile_name
        if not profile_path.exists():
            raise RuntimeError(f'{self.spec.display_name} profile "{profile_name}" not found')
        return str(profile_path)

    async def parse_bookmarks(self, profile_name: str) -> list[dict[str, Any]]:
        db_path = self.get_database_path(profile_name)
        bookmarks_file = Path(db_path)
        if not bookmarks_file.exists():
            raise RuntimeError(f"Bookmarks file not found: {db_path}")

        with open(bookmarks_file, encoding="utf-8") as handle:
            data = json.load(handle)

        bookmarks: list[dict[str, Any]] = []
        roots = data.get("roots", {})
        for root_name in ("bookmark_bar", "other", "synced"):
            root = roots.get(root_name)
            if isinstance(root, dict):
                bookmarks.extend(self._parse_bookmark_node(root, root_name, ""))
        return bookmarks

    def _parse_bookmark_node(self, node: dict[str, Any], root_name: str, folder_path: str) -> list[dict[str, Any]]:
        bookmarks: list[dict[str, Any]] = []
        node_type = node.get("type", "unknown")

        if node_type == "url":
            bookmarks.append(
                {
                    "id": str(node.get("id", "")),
                    "title": node.get("name", ""),
                    "url": node.get("url", ""),
                    "folder_path": folder_path,
                    "parent": folder_path or root_name,
                    "added_date": node.get("date_added", "0"),
                    "last_modified": node.get("date_modified", "0"),
                    "tags": node.get("tags", []),
                    "root": root_name,
                }
            )
        elif node_type == "folder":
            folder_name = node.get("name", "Unknown")
            new_folder_path = f"{folder_path}/{folder_name}" if folder_path else folder_name
            for child in node.get("children", []) or []:
                if isinstance(child, dict):
                    bookmarks.extend(self._parse_bookmark_node(child, root_name, new_folder_path))

        return bookmarks

    async def list_tags(self, profile_name: str) -> list[str]:
        bookmarks = await self.parse_bookmarks(profile_name)
        tags: set[str] = set()
        for bookmark in bookmarks:
            bookmark_tags = bookmark.get("tags", [])
            if isinstance(bookmark_tags, list):
                tags.update(str(tag) for tag in bookmark_tags if tag)
            elif bookmark_tags:
                tags.add(str(bookmark_tags))
        return sorted(tags)

    async def search_bookmarks(
        self,
        profile_name: str,
        query: str,
        tags: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        bookmarks = await self.parse_bookmarks(profile_name)
        query_lower = query.lower()
        results: list[dict[str, Any]] = []

        for bookmark in bookmarks:
            title = str(bookmark.get("title", "")).lower()
            url = str(bookmark.get("url", "")).lower()
            if query_lower not in title and query_lower not in url:
                continue

            if tags:
                bookmark_tags = bookmark.get("tags", [])
                bookmark_tags = [bookmark_tags] if isinstance(bookmark_tags, str) else bookmark_tags
                if not any(tag in bookmark_tags for tag in tags):
                    continue

            results.append(bookmark)
            if len(results) >= limit:
                break

        return results

    def get_database_path(self, profile_name: str) -> str:
        if self.user_data_dir is None:
            raise RuntimeError(f"{self.spec.display_name} is not installed")

        profile = profile_name or self.spec.default_profile

        if self.spec.profile_layout == ProfileLayout.FLAT_PROFILE:
            return str(self.user_data_dir / "Bookmarks")

        return str(self.user_data_dir / profile / "Bookmarks")

    async def is_database_locked(self, profile_name: str) -> bool:
        del profile_name
        for proc in psutil.process_iter(["name"]):
            try:
                name = (proc.info.get("name") or "").lower()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            for process_name in self.spec.process_names:
                if process_name.lower() in name:
                    return True
        return False

    async def backup_profile(self, profile_name: str, backup_path: str) -> str:
        profile_path = Path(await self.get_profile_path(profile_name))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{self.browser_id}_{profile_name}_{timestamp}.zip"
        backup_file = Path(backup_path) / backup_name
        shutil.make_archive(str(backup_file.with_suffix("")), "zip", str(profile_path))
        return str(backup_file)

    async def restore_profile(self, profile_name: str, backup_file: str, overwrite: bool = False) -> dict[str, Any]:
        backup_path = Path(backup_file)
        if not backup_path.exists():
            raise RuntimeError(f"Backup file not found: {backup_file}")

        profile_path = Path(await self.get_profile_path(profile_name))
        if profile_path.exists() and not overwrite:
            raise RuntimeError(f"Profile {profile_name} already exists. Use overwrite=True to replace.")

        with zipfile.ZipFile(backup_file, "r") as archive:
            archive.extractall(profile_path)

        return {
            "success": True,
            "profile_name": profile_name,
            "items_restored": {"bookmarks": 0, "settings": 0},
            "warnings": [],
        }

    def get_browser_type(self) -> str:
        return self.browser_id
