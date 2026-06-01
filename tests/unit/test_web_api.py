import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("BOOKMARKS_WEB_AUTH", "0")

from browser_bookmarks_tools.mcp_server import web_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(web_app)


def test_root_health(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_health(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["mcp"] == "bookmarks-mcp"


def test_api_tools(client: TestClient):
    response = client.get("/api/tools")
    assert response.status_code == 200
    names = {tool["name"] for tool in response.json()["tools"]}
    assert "browser_bookmarks" in names
    assert len(names) >= 9


def test_activity_feed(client: TestClient):
    response = client.get("/api/activity")
    assert response.status_code == 200
    assert "entries" in response.json()


def test_tool_call_logs_activity(client: TestClient):
    client.post(
        "/api/tools/call",
        json={
            "name": "browser_bookmarks",
            "arguments": {
                "operation": "list_bookmarks",
                "browser": "chrome",
                "limit": 1,
            },
        },
    )
    entries = client.get("/api/activity").json()["entries"]
    assert any(entry["kind"] == "tool_call" for entry in entries)
