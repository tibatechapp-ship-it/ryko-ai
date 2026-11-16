"""اختبارات نقاط الصحة والنماذج."""

from fastapi.testclient import TestClient

from app.main import create_app


def get_client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_health_endpoint():
    with get_client() as client:
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "app" in data
        assert "version" in data
        assert "model_ready" in data
        assert "memory_ready" in data


def test_models_endpoint():
    with get_client() as client:
        resp = client.get("/api/v1/models")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert "id" in data[0]
