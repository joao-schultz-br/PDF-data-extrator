from fastapi.testclient import TestClient

from app.main import app


def test_health_check() -> None:
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "pdf-data-extractor",
        "version": app.version,
    }


def test_preview_origin_can_upload():
    origin = "http://localhost:4173"
    with TestClient(app) as client:
        response = client.options(
            "/api/documents/extract",
            headers={"Origin": origin, "Access-Control-Request-Method": "POST"},
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
