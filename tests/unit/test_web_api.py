import httpx
import pytest
from fastapi.testclient import TestClient

from browser_bookmarks_tools.mcp_server import web_app
from browser_bookmarks_tools.web import _extract_llm_error


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


def test_logs_query_and_export(client: TestClient):
    client.post(
        "/api/tools/call",
        json={
            "name": "browser_bookmarks",
            "arguments": {"operation": "list_bookmarks", "browser": "chrome", "limit": 1},
        },
    )
    logs = client.get("/api/logs?limit=10&kind=tool_call").json()
    assert logs["total"] >= 1
    assert "level" in logs["entries"][0]

    stats = client.get("/api/logs/stats").json()
    assert stats["max_entries"] >= 100
    assert "by_level" in stats

    export = client.get("/api/logs/export?format=json&kind=tool_call")
    assert export.status_code == 200
    assert "application/json" in export.headers.get("content-type", "")

    cleared = client.delete("/api/logs")
    assert cleared.status_code == 200
    assert client.get("/api/logs/stats").json()["total"] == 1


def test_llm_test_unknown_provider(client: TestClient):
    response = client.post("/api/llm/test", json={"provider": "not-a-real-provider", "model": "x"})
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert "Unknown provider" in data["message"]


def test_llm_test_connect_error_surfaces_clearly(client: TestClient):
    response = client.post(
        "/api/llm/test",
        json={"provider": "ollama", "model": "llama3.2:3b", "endpoint": "http://127.0.0.1:1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert "Could not connect" in data["message"]


def test_extract_llm_error_prefers_json_error_field():
    resp = httpx.Response(500, json={"error": "llama-server binary not found"})
    assert _extract_llm_error(resp) == "llama-server binary not found"


def test_extract_llm_error_falls_back_to_status_and_body():
    resp = httpx.Response(503, text="Service Unavailable")
    message = _extract_llm_error(resp)
    assert "503" in message
    assert "Service Unavailable" in message
