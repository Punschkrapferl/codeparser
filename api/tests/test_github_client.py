import subprocess
import pytest
from fastapi import HTTPException
from typing import cast
from unittest.mock import patch, MagicMock

from api.github_client import clone_or_update

# --- Fixtures ---
@pytest.fixture
def tmp_repo_dir(tmp_path):
    return tmp_path / "repos"

# --- Tests ---
def test_clone_or_update_invalid_url(tmp_repo_dir):
    with pytest.raises(HTTPException) as exc:
        clone_or_update("", tmp_repo_dir)
    http_exc = cast(HTTPException, exc.value)
    assert http_exc.status_code == 400
    assert "repo_url invalid" in getattr(http_exc, "detail", "")

def test_clone_or_update_existing_git_repo(tmp_repo_dir):
    repo_path = tmp_repo_dir / "existing_repo"
    repo_path.mkdir(parents=True)
    (repo_path / ".git").mkdir()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        path = clone_or_update("https://example.com/existing_repo.git", tmp_repo_dir)
        assert path == str(repo_path)
        assert mock_run.call_count == 2  # fetch + reset

def test_clone_or_update_new_repo(tmp_repo_dir):
    repo_url = "https://example.com/newrepo.git"

    # Mock subprocess.run for git clone
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        path = clone_or_update(repo_url, tmp_repo_dir)
        # Check that the returned path is inside tmp_repo_dir
        assert path.startswith(str(tmp_repo_dir))
        # Only one call for git clone
        assert mock_run.call_count == 1


def test_clone_or_update_subprocess_error(tmp_repo_dir):
    repo_url = "https://example.com/errorrepo.git"

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd="git clone", output="", stderr="simulated error"
        )
        with pytest.raises(HTTPException) as exc:
            clone_or_update(repo_url, tmp_repo_dir)
        http_exc = cast(HTTPException, exc.value)
        assert http_exc.status_code == 500
        assert "git error: simulated error" in getattr(http_exc, "detail", "")

def test_clone_or_update_file_not_found_error(tmp_repo_dir):
    repo_url = "https://example.com/errorrepo.git"

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError("git not found")
        with pytest.raises(HTTPException) as exc:
            clone_or_update(repo_url, tmp_repo_dir)
        http_exc = cast(HTTPException, exc.value)
        assert http_exc.status_code == 500
        assert "git not found on PATH" in getattr(http_exc, "detail", "")
