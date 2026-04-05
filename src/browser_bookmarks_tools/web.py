from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from .ai import router as ai_router
from pydantic import BaseModel


class ToolExecutionRequest(BaseModel):
    arguments: dict = {}


router = APIRouter(prefix="/api")

# Directory configuration
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
dist_dir = project_root / "web_sota" / "dist"


def setup_webapp(app, mcp_app=None):
    if mcp_app:

        @router.get("/tools")
        async def list_tools():
            return {
                "tools": [
                    {"name": t.name, "description": t.description} for t in mcp_app.list_tools()
                ]
            }

        @router.post("/tools/{tool_name}")
        async def execute_tool(tool_name: str, request: ToolExecutionRequest):
            try:
                result = await mcp_app.call_tool(tool_name, request.arguments)
                return {"result": result}
            except Exception as e:
                return {"error": str(e)}

    app.include_router(router)
    app.include_router(ai_router)

    if dist_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(dist_dir / "assets")), name="assets")

        @app.get("/{full_path:path}", response_class=HTMLResponse)
        async def serve_spa(request: Request, full_path: str):
            if full_path.startswith("api/") or full_path.startswith("mcp"):
                return None
            index_path = dist_dir / "index.html"
            if index_path.exists():
                return FileResponse(index_path)
            return HTMLResponse(content="<h1>Frontend not built</h1>", status_code=404)
    else:

        @app.get("/", response_class=HTMLResponse)
        async def dev_hint():
            return HTMLResponse(content="<h1>Static files missing</h1>")
