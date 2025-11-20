from fastapi.testclient import TestClient
from api.main import app

def test_app_starts_and_root_works():
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
