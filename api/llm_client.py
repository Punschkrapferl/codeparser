import json
import logging
import os
from typing import Dict, Any

import httpx

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "mistral:latest")

logger = logging.getLogger(__name__)


async def call_llm(prompt: str) -> str:
    """
    DEV MODE: very fast stub for the LLM.

    - Does NOT call Ollama at all.
    - Returns a short synthetic "analysis" string immediately.
    - Lets you test the whole pipeline (clone -> parse -> normalize -> analyze_parts)
      and the Angular UI without waiting minutes for the model.
    """
    max_preview = 400
    preview = prompt[:max_preview].replace("\n", " ") + (
        "..." if len(prompt) > max_preview else ""
    )

    logger.info("DEV STUB LLM called, prompt length=%d", len(prompt))

    return (
        "DEV STUB ANALYSIS (no real LLM call)\n"
        "This response is generated instantly for fast testing.\n\n"
        f"- Model configured: {MODEL_NAME}\n"
        f"- Ollama host    : {OLLAMA_HOST}\n"
        f"- Prompt length  : {len(prompt)} characters\n"
        f"- Prompt preview : {preview}\n"
    )

# async def call_llm(prompt: str) -> str:
#     """
#     REAL MODE: Call the local Ollama chat API once with the given prompt.
#
#     On success:
#       - returns the model's text content.
#
#     On failure (network error, HTTP 5xx, JSON error, missing content):
#       - logs the error
#       - returns a descriptive error string instead of raising.
#     """
#     payload: Dict[str, Any] = {
#         "model": MODEL_NAME,
#         "messages": [{"role": "user", "content": prompt}],
#         "stream": False,
#         "options": {"num_ctx": 8192},
#     }
#
#     url = f"{OLLAMA_HOST}/api/chat"
#     logger.info("Calling LLM at %s with model=%s", url, MODEL_NAME)
#
#     # network / connection errors
#     try:
#         async with httpx.AsyncClient(timeout=300.0) as client:
#             resp = await client.post(url, json=payload)
#     except httpx.RequestError as e:
#         logger.error("Ollama request error: %s", e)
#         return f"[LLM request error] Could not reach Ollama at {OLLAMA_HOST}: {e}"
#
#     # HTTP status not 2xx
#     if resp.status_code // 100 != 2:
#         body = resp.text[:400] if resp.text else ""
#         logger.error(
#             "Ollama HTTP error %s. Response body (truncated): %s",
#             resp.status_code,
#             body,
#         )
#         return f"[LLM HTTP error {resp.status_code}] {body}"
#
#     # Parse JSON
#     try:
#         data = resp.json()
#         # handle mocks returning awaitable json()
#         if callable(getattr(data, "__await__", None)):
#             data = await data
#     except (json.JSONDecodeError, ValueError) as e:
#         logger.error("Ollama JSON decode error: %s | raw: %s", e, resp.text[:400])
#         return f"[LLM JSON error] Could not decode Ollama response: {e}"
#
#     # Extract model content
#     content = (
#             data.get("message", {}).get("content")
#             or data.get("response")
#     )
#
#     if not isinstance(content, str) or not content.strip():
#         logger.error("Ollama response missing/empty content. Raw: %r", data)
#         return "[LLM error] Response missing usable content from Ollama."
#
#     return content.strip()
