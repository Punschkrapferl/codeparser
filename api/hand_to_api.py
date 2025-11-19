import httpx, logging
from pathlib import Path

async def send_to_api(file_path: Path):
    url = "http://localhost:8000/analyze"
    async with httpx.AsyncClient(timeout=120) as client:
        try:
            with open(file_path, "rb") as f:
                files = {"file": (file_path.name, f)}
                resp = await client.post(url, files=files)
                resp.raise_for_status()  # synchronous method
                logging.info(f"API response: {resp.text}")
        except httpx.HTTPError as e:
            logging.error(f"API request failed: {e}")
