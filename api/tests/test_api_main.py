from pathlib import Path
import os

from api import api_main as cfg
from api import llm_client
from api import helpers as helpers_mod


def test_app_and_project_dirs() -> None:
    # APP_DIR should be the api package directory
    assert isinstance(cfg.APP_DIR, Path)
    assert cfg.APP_DIR.name == "api"

    # PROJECT_ROOT is parent of api
    assert cfg.PROJECT_ROOT == cfg.APP_DIR.parent


def test_repos_dir_is_absolute_path() -> None:
    assert isinstance(cfg.REPOS_DIR, Path)
    assert cfg.REPOS_DIR.is_absolute()


def test_output_jsonl_location() -> None:
    expected = cfg.PROJECT_ROOT / "api" / "output.jsonl"
    assert cfg.OUTPUT_JSONL == expected


def test_model_default_respects_env() -> None:
    expected_model = os.getenv("MODEL_NAME", "mistral:latest")
    assert llm_client.MODEL_NAME == expected_model


def test_batch_size_default_respects_env() -> None:
    expected_batch = int(os.getenv("BATCH_SIZE", "4"))
    assert helpers_mod.BATCH_SIZE == expected_batch
