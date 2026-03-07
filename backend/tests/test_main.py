from fastapi.testclient import TestClient

from main import app, create_app


def test_create_app_metadata() -> None:
    created_app = create_app()
    assert created_app.title == "stockVis API"
    assert created_app.version == "0.1.0"


def test_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
