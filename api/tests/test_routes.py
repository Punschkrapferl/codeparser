import io
from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# ------------------ simple routes ------------------


def test_health_route(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_root_route(client: TestClient) -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["message"] == "API is running"
    # allow version / extra keys, so we do not assert equality


# ------------------ /analyze (single file) ------------------


def test_analyze_simple_python_file(client: TestClient) -> None:
    """
    Upload a tiny python file and ensure /analyze returns the expected shape
    and uses the dev stub LLM.
    """
    code = b"def add(a, b):\n    return a + b\n"
    files = {
        "file": ("sample.py", io.BytesIO(code), "text/x-python"),
    }

    resp = client.post("/analyze", files=files)
    assert resp.status_code == 200

    data: Dict[str, Any] = resp.json()

    assert "analysis" in data
    assert "batches" in data
    assert "num_parts" in data
    assert "filename" in data
    assert "languages" in data

    assert data["filename"] == "sample.py"
    assert data["num_parts"] >= 1
    assert "python" in data["languages"]

    # Make sure the dev stub was used
    assert "DEV STUB ANALYSIS (no real LLM call)" in data["analysis"]


def test_analyze_empty_file_returns_no_parts(client: TestClient) -> None:
    """
    Upload an empty file: expect 0 parts, empty analysis, 0 batches.
    """
    files = {
        "file": ("empty.txt", io.BytesIO(b""), "text/plain"),
    }

    resp = client.post("/analyze", files=files)
    assert resp.status_code == 200
    data = resp.json()

    assert data["num_parts"] == 0
    assert data["batches"] == 0
    assert data["analysis"] == ""
    assert data["filename"] == "empty.txt"


# ------------------ /analyze-multi (folder / multi-file) ------------------


def test_analyze_multi_two_files(client: TestClient) -> None:
    """
    Upload two small files via /analyze-multi and ensure they are
    aggregated and sent through the dev stub LLM.
    """
    code1 = b"def a():\n    return 1\n"
    code2 = b"class B:\n    pass\n"

    files: List[tuple[str, tuple[str, io.BytesIO, str]]] = [
        ("files", ("a.py", io.BytesIO(code1), "text/x-python")),
        ("files", ("b.py", io.BytesIO(code2), "text/x-python")),
    ]

    resp = client.post("/analyze-multi", files=files)
    assert resp.status_code == 200

    data: Dict[str, Any] = resp.json()

    assert data["num_files"] == 2
    assert data["total_parts"] >= 2
    assert "python" in data["languages"]
    assert len(data["file_summaries"]) == 2
    assert "DEV STUB ANALYSIS (no real LLM call)" in data["analysis"]
