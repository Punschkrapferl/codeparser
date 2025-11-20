import logging
import os
from pathlib import Path

# ------------ config ------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent

REPOS_DIR = Path(os.getenv("REPOS_DIR", APP_DIR / "repos")).resolve()
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "mistral:latest")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "4"))

OUTPUT_JSONL = PROJECT_ROOT / "api" / "output.jsonl"
