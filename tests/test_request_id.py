from fastapi.testclient import TestClient

from app.main import app


def test_request_id_propagates_header() -> None:
    client = TestClient(app)
    res = client.get("/health", headers={"x-request-id": "abc-123"})
    assert res.status_code == 200
    assert res.headers.get("x-request-id") == "abc-123"


def test_request_id_generated_when_missing() -> None:
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.headers.get("x-request-id")


