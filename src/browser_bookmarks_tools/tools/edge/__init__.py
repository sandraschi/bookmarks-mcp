"""Edge bookmark tools — delegates to unified chromium adapter."""

from typing import Any

from ..chromium import (
    add_chromium_bookmark,
    delete_chromium_bookmark,
    edit_chromium_bookmark,
    list_chromium_bookmarks,
)

_BROWSER = "edge"


async def list_edge_bookmarks(
    bookmarks_path: str | None = None,
    profile_name: str | None = None,
) -> dict[str, Any]:
    return await list_chromium_bookmarks(_BROWSER, profile_name=profile_name, bookmarks_path=bookmarks_path)


async def add_edge_bookmark(
    title: str,
    url: str,
    folder: str | None = None,
    bookmarks_path: str | None = None,
    profile_name: str | None = None,
) -> dict[str, Any]:
    return await add_chromium_bookmark(
        _BROWSER,
        title=title,
        url=url,
        folder=folder,
        profile_name=profile_name,
        bookmarks_path=bookmarks_path,
    )


async def edit_edge_bookmark(
    *,
    id: str | None = None,
    url: str | None = None,
    new_title: str | None = None,
    new_folder: str | None = None,
    allow_duplicates: bool = False,
    create_folders: bool = True,
    dry_run: bool = False,
    bookmarks_path: str | None = None,
    profile_name: str | None = None,
) -> dict[str, Any]:
    return await edit_chromium_bookmark(
        _BROWSER,
        id=id,
        url=url,
        new_title=new_title,
        new_folder=new_folder,
        allow_duplicates=allow_duplicates,
        create_folders=create_folders,
        dry_run=dry_run,
        profile_name=profile_name,
        bookmarks_path=bookmarks_path,
    )


async def delete_edge_bookmark(
    *,
    id: str | None = None,
    url: str | None = None,
    dry_run: bool = False,
    bookmarks_path: str | None = None,
    profile_name: str | None = None,
) -> dict[str, Any]:
    return await delete_chromium_bookmark(
        _BROWSER,
        id=id,
        url=url,
        dry_run=dry_run,
        profile_name=profile_name,
        bookmarks_path=bookmarks_path,
    )
