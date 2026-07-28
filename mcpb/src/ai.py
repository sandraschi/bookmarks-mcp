import httpx
from browser_bookmarks_tools.auth import authenticate
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/ai", tags=["ai"], dependencies=[Depends(authenticate)])


class ChatRequest(BaseModel):
    message: str
    provider: str | None = "ollama"
    model: str | None = "gemini-2.0-flash-exp"
    endpoint: str | None = "http://localhost:11434"


class ChatResponse(BaseModel):
    response: str
    tool_calls: list[str] | None = []


@router.post("/chat", response_model=ChatResponse)
async def chat_with_llm(request: ChatRequest):
    try:
        if request.provider == "ollama":
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{request.endpoint}/api/generate",
                    json={"model": request.model, "prompt": request.message, "stream": False},
                    timeout=30.0,
                )
                resp.raise_for_status()
                data = resp.json()
                return ChatResponse(response=data.get("response", "No response from Ollama"))

        elif request.provider == "lmstudio":
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{request.endpoint}/v1/chat/completions",
                    json={
                        "messages": [{"role": "user", "content": request.message}],
                        "model": request.model,
                        "temperature": 0.7,
                    },
                    timeout=30.0,
                )
                resp.raise_for_status()
                data = resp.json()
                return ChatResponse(response=data["choices"][0]["message"]["content"])

        else:
            raise HTTPException(status_code=400, detail=f"Provider {request.provider} not supported")

    except Exception as e:
        return ChatResponse(response=f"AI Bridge Error: {e!s}")
