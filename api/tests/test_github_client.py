import subprocess
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from api.github_client import clone_or_update


@pytest.fixture
def tmp_repo_dir(tmp_path: Path) -> Path:
    # Base directory where clone_or_update will create repos
    return tmp_path / "repos"


def test_clone_or_update_invalid_url(tmp_repo_dir: Path) -> None:
    with pytest.raises(HTTPException) as exc:
        clone_or_update("", tmp_repo_dir)

    http_exc = cast(HTTPException, exc.value)
    assert http_exc.status_code == 400
    assert "repo_url invalid" in str(http_exc.detail)


def test_clone_or_update_existing_git_repo(tmp_repo_dir: Path) -> None:
    # Simulate existing repo with .git folder
    repo_path = tmp_repo_dir / "existing_repo"
    (repo_path / ".git").mkdir(parents=True)

    # Patch subprocess.run inside api.github_client
    with patch("api.github_client.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)

        path = clone_or_update("https://example.com/existing_repo.git", tmp_repo_dir)

        assert path == str(repo_path)
        # Two calls: fetch + reset
        assert mock_run.call_count == 2

        # Optional: verify commands
        fetch_call = mock_run.call_args_list[0]
        reset_call = mock_run.call_args_list[1]
        assert "fetch" in fetch_call.args[0]
        assert "reset" in reset_call.args[0]


def test_clone_or_update_new_repo(tmp_repo_dir: Path) -> None:
    repo_url = "https://example.com/newrepo.git"

    # No .git folder => should perform a clone
    with patch("api.github_client.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)

        path = clone_or_update(repo_url, tmp_repo_dir)

        # Returned path should be under tmp_repo_dir
        assert path.startswith(str(tmp_repo_dir))
        # Only one call (git clone)
        assert mock_run.call_count == 1

        clone_args = mock_run.call_args.args[0]
        assert clone_args[0] == "git"
        assert "clone" in clone_args


def test_clone_or_update_subprocess_error(tmp_repo_dir: Path) -> None:
    repo_url = "https://example.com/errorrepo.git"

    with patch("api.github_client.subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd="git clone",
            output="",
            stderr="simulated error",
        )

        with pytest.raises(HTTPException) as exc:
            clone_or_update(repo_url, tmp_repo_dir)

        http_exc = cast(HTTPException, exc.value)
        assert http_exc.status_code == 500
        assert "git error: simulated error" in str(http_exc.detail)


def test_clone_or_update_file_not_found_error(tmp_repo_dir: Path) -> None:
    repo_url = "https://example.com/errorrepo.git"

    with patch("api.github_client.subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError("git not found")

        with pytest.raises(HTTPException) as exc:
            clone_or_update(repo_url, tmp_repo_dir)

        http_exc = cast(HTTPException, exc.value)
        assert http_exc.status_code == 500
        assert "git not found on PATH" in str(http_exc.detail)
