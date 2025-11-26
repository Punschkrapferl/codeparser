import logging
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent

REPOS_DIR = Path(os.getenv("REPOS_DIR", APP_DIR / "repos")).resolve()
OUTPUT_JSONL = PROJECT_ROOT / "api" / "output.jsonl"
