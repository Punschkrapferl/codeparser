from pathlib import Path
from typing import Any, Dict, Generator

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from api.main import app
import api.routes_github as routes_github


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_jobs() -> Generator[None, Any, None]:
    # Ensure JOBS dict is clean before and after each test
    routes_github.JOBS.clear()
    yield
    routes_github.JOBS.clear()


# ------------------ /github/analyze ------------------


def test_github_analyze_missing_repo_url_returns_400(client: TestClient) -> None:
    # No query param, no JSON body -> 400
    resp = client.post("/github/analyze")
    assert resp.status_code == 400
    data = resp.json()
    assert data["detail"] == "repo_url required"


def test_github_analyze_query_param_happy_path(
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
) -> None:
    """
    Full pipeline test of /github/analyze with query parameters, but all heavy
    bits (git, go, LLM) are mocked.
    """

    # 1) Fake clone_or_update -> returns a repo path under tmp_path
    fake_repo_path = tmp_path / "repos" / "myrepo"
    fake_repo_path.mkdir(parents=True)
    monkeypatch.setattr(
        routes_github,
        "REPOS_DIR",
        tmp_path / "repos",
        )
    monkeypatch.setattr(
        routes_github,
        "clone_or_update",
        lambda url, dest: str(fake_repo_path),
    )

    # 2) Make parser_go dir under PROJECT_ROOT (monkeypatch PROJECT_ROOT)
    monkeypatch.setattr(routes_github, "PROJECT_ROOT", tmp_path)
    parser_dir = tmp_path / "parser_go"
    parser_dir.mkdir()
    go_file = parser_dir / "main.go"
    go_file.write_text("package main\nfunc main() {}", encoding="utf-8")

    # 3) Patch subprocess.run so no real go-toolchain is invoked
    with patch("api.routes_github.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)

        # 4) Fake OUTPUT_JSONL and contents
        fake_jsonl = tmp_path / "output.jsonl"
        fake_jsonl.write_bytes(
            b'[{"path":"a.py","language":"python","code":"print(1)"}]'
        )
        monkeypatch.setattr(routes_github, "OUTPUT_JSONL", fake_jsonl)

        # 5) Patch helpers used inside _run_github_pipeline
        monkeypatch.setattr(
            routes_github,
            "_parse_chunks_bytes",
            lambda raw, filename=None: [
                {"path": "a.py", "language": "python", "code": "print(1)"}
            ],
        )
        monkeypatch.setattr(
            routes_github,
            "_normalize_chunks",
            lambda chunks: chunks,
        )

        async def fake_analyze_parts(*_args, **_kwargs):
            return {"analysis": "OK", "batches": 1}

        monkeypatch.setattr(routes_github, "_analyze_parts", fake_analyze_parts)

        # 6) Call endpoint
        resp = client.post(
            "/github/analyze",
            params={
                "repo_url": "https://example.com/myrepo.git",
                "system_hint": "explain simply",
            },
        )

    assert resp.status_code == 200
    data: Dict[str, Any] = resp.json()

    # Check core fields from _run_github_pipeline
    assert data["analysis"] == "OK"
    assert data["batches"] == 1
    assert data["num_parts"] == 1
    assert data["repo_path"] == str(fake_repo_path)
    assert data["source_file"] == str(fake_jsonl)
    assert data["languages"] == ["python"]


@pytest.mark.asyncio
async def test_github_analyze_json_body_uses_body_repo_and_system_hint(
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Here we only test that JSON body fields are correctly forwarded into
    _run_github_pipeline (repo_url + system_hint).
    """
    mock_run = AsyncMock(return_value={"analysis": "X", "batches": 0})
    monkeypatch.setattr(routes_github, "_run_github_pipeline", mock_run)

    payload = {
        "repo_url": "https://example.com/body-repo.git",
        "system_hint": "from-body",
    }

    resp = client.post(
        "/github/analyze",
        json=payload,
    )
    assert resp.status_code == 200
    assert resp.json()["analysis"] == "X"

    # _run_github_pipeline should have been called with repo_url from body
    mock_run.assert_awaited_once()
    args, kwargs = mock_run.call_args
    assert args[0] == "https://example.com/body-repo.git"
    assert args[1] == "from-body"


# ------------------ /analyze-github-job (start + get) ------------------


def test_start_github_job_invalid_url_returns_400(client: TestClient) -> None:
    resp = client.post("/analyze-github-job", json={"repo_url": ""})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "repo_url invalid"


def test_start_github_job_creates_pending_job(
        client: TestClient,
) -> None:
    """
    We ensure that:
      - 200 OK
      - job_id returned
      - JOBS[job_id] is created
      - _github_job_worker is scheduled
    """
    with patch("api.routes_github._github_job_worker", new=AsyncMock()) as mock_worker:
        resp = client.post(
            "/analyze-github-job",
            json={"repo_url": "https://example.com/repo.git", "system_hint": "hint"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "job_id" in data
    job_id = data["job_id"]

    assert job_id in routes_github.JOBS
    job = routes_github.JOBS[job_id]
    # At this point job may still be "pending" or already changed by the worker,
    # but it must at least exist with the basic structure.
    assert job["job_id"] == job_id
    assert "status" in job
    assert "result" in job
    assert "error" in job

    # Worker should have been scheduled once with the correct args
    mock_worker.assert_awaited_once()
    args, kwargs = mock_worker.call_args
    assert args[0] == job_id
    assert args[1] == "https://example.com/repo.git"
    assert args[2] == "hint"


def test_get_github_job_status_404_for_unknown_job(client: TestClient) -> None:
    resp = client.get("/analyze-github-job/non-existent-id")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "job not found"


def test_get_github_job_status_returns_job(client: TestClient) -> None:
    job_id = "test-job"
    routes_github.JOBS[job_id] = {
        "job_id": job_id,
        "status": "done",
        "result": {"analysis": "OK"},
        "error": None,
    }

    resp = client.get(f"/analyze-github-job/{job_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"] == job_id
    assert data["status"] == "done"
    assert data["result"]["analysis"] == "OK"
    assert data["error"] is None
