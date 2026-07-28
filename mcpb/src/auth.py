import os
import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic(auto_error=False)


def auth_enabled() -> bool:
    return os.getenv("BOOKMARKS_WEB_AUTH", "1").lower() not in ("0", "false", "off", "no")


def authenticate(credentials: HTTPBasicCredentials | None = Depends(security)) -> str:
    """Authenticate via HTTP Basic when BOOKMARKS_WEB_AUTH is enabled."""
    if not auth_enabled():
        return "anonymous"

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Basic"},
        )

    correct_username = os.getenv("BOOKMARKS_WEB_USER", "admin")
    correct_password = os.getenv("BOOKMARKS_WEB_PASS", "mcp")

    is_correct_username = secrets.compare_digest(credentials.username, correct_username)
    is_correct_password = secrets.compare_digest(credentials.password, correct_password)

    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
