import os
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

security = HTTPBasic()


def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    """
    Authenticates the user via basic auth.
    Uses BOOKMARKS_WEB_USER and BOOKMARKS_WEB_PASS environment variables.
    """
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
