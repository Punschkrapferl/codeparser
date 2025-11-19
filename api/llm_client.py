import json
import os, httpx

from fastapi import HTTPException

OLLAMA_HOST  = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL_NAME   = os.getenv("MODEL_NAME", "mistral:latest")

async def call_llm(prompt: str) -> str:
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"num_ctx": 8192},
    }

    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            r = await client.post(f"{OLLAMA_HOST}/api/chat", json=payload)
            r.raise_for_status()

            # JSON parsing (mocked json() may be async)
            try:
                data = r.json()
                if callable(getattr(data, "__await__", None)):
                    data = await data
            except (json.JSONDecodeError, ValueError) as e:
                raise HTTPException(status_code=502, detail=f"Ollama JSON decode error: {e}") from e

    except httpx.HTTPStatusError as e:
        body = e.response.text[:400] if e.response is not None else ""
        raise HTTPException(status_code=502, detail=f"Ollama HTTP {e.response.status_code}: {body}") from e

    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Ollama request error: {e}") from e

    # Extract model response
    content = (
            data.get("message", {}).get("content")
            or data.get("response")
    )
    if content is None:
        raise HTTPException(status_code=502, detail="Ollama response missing message.content")

    return content