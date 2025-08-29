import json
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    assert data.get("status") == "ok"


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    assert "message" in data
