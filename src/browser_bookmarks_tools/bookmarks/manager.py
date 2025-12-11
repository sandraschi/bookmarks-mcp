from typing import Any, Dict


async def create_bookmark(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new bookmark.

    Parameters:
        payload: Should include url, title, optional tags and folder

    Returns:
        dict: {"status": "created", "bookmark": {...}}

    Usage:
        await create_bookmark({"url": "https://example.com", "title": "Example"})

    Examples:
        See tests.

    Notes:
        Firefox adapter will be added subsequently.

    See Also:
        read_bookmark, update_bookmark, delete_bookmark
    """
    return {"status": "created", "bookmark": payload}


async def read_bookmark(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {"status": "ok", "bookmark": payload}


async def update_bookmark(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {"status": "updated", "bookmark": payload}


async def delete_bookmark(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {"status": "deleted", "bookmark": payload}
