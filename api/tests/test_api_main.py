from fastapi.testclient import TestClient
from api.api_main import app, _parse_chunks_bytes, _normalize_chunks

client = TestClient(app)

# --- Test helper functions ---
def test_parse_chunks_bytes_empty():
    raw = b""
    chunks = _parse_chunks_bytes(raw)
    assert chunks == []

def test_normalize_chunks_basic():
    chunks = [
        {"path": "a.py", "language": "python", "code": "print('hi')"},
        {"Path": "b.java", "Language": "java", "Code": "class A {}"}
    ]
    norm = _normalize_chunks(chunks)
    assert len(norm) == 2
    assert norm[0]["language"] == "python"
    assert norm[1]["language"] == "java"

# --- Test FastAPI route ---
def test_health_route():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}

# Example: simulate file upload
def test_analyze_code_route(tmp_path):
    test_file = tmp_path / "test.jsonl"
    test_file.write_text('[{"path":"a.py","language":"python","code":"print(1)"}]')

    with open(test_file, "rb") as f:
        resp = client.post("/analyze", files={"file": ("test.jsonl", f)})

    assert resp.status_code == 200
    data = resp.json()
    assert "analysis" in data
    assert "batches" in data
