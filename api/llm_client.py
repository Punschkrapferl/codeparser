import logging
import os

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

# Real implementation kept commented out for now. When you switch to real mode,
# tests can be extended to patch httpx.AsyncClient and simulate responses.
#
# async def call_llm(prompt: str) -> str:
#     ...
