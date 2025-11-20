import logging
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)


async def send_to_api(file_path: Path) -> None:
    """
    Send a local file to the FastAPI backend /analyze endpoint.

    - file_path: path to a JSONL (or compatible) file that the backend expects.

    Logs the backend response on success.
    Logs an error if the HTTP request fails.
    """
    url = "http://localhost:8000/analyze"

    async with httpx.AsyncClient(timeout=120) as client:
        try:
            with file_path.open("rb") as f:
                files = {"file": (file_path.name, f)}
                resp = await client.post(url, files=files)
                # This is synchronous, so plain call is fine
                resp.raise_for_status()
                logger.info("API response: %s", resp.text)
        except httpx.HTTPError as e:
            logger.error("API request failed: %s", e)
