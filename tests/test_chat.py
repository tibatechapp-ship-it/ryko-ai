"""اختبارات مسار الدردشة باستخدام خدمة AI وهمية."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


class FakeAIService:
    ready = True

    def available_models(self):
        return [{"id": "fake-model", "provider": "test", "available": True, "description": "fake"}]

    async def generate_reply(self, message, history=None, context=None):
        ctx = context or []
        suffix = f" | ctx={len(ctx)}"
        return f"echo:{message}{suffix}", "fake-model"

    async def stream_reply(self, message, history=None, context=None):
        for part in ["echo:", message]:
            yield part

    async def initialize(self):
        self.ready = True

    async def close(self):
        self.ready = False


class FakeMemoryService:
    ready = True

    def __init__(self):
        self.saved = []

    async def initialize(self):
        self.ready = True

    async def close(self):
        self.ready = False

    async def add_message(self, session_id, role, content):
        self.saved.append((session_id, role, content))

    async def get_relevant_context(self, session_id, query, n_results=3):
        return ["سياق تجريبي"]


@pytest.fixture()
def client():
    app = create_app()
    with TestClient(app) as c:
        # استبدال الخدمات الحقيقية بخدمات وهمية بعد بدء lifespan
        c.app.state.ai_service = FakeAIService()
        c.app.state.memory_service = FakeMemoryService()
        yield c


def test_chat_endpoint_returns_reply(client):
    resp = client.post(
        "/api/v1/chat",
        json={"message": "مرحبا", "session_id": "s1", "use_memory": True},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == "s1"
    assert data["reply"].startswith("echo:مرحبا")
    assert data["model"] == "fake-model"
    assert isinstance(data["context_used"], list)
