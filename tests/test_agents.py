"""اختبارات نظام الوكلاء."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


class FakeAIService:
    ready = True

    def available_models(self):
        return [{"id": "fake-model", "provider": "test", "available": True, "description": "fake"}]

    async def generate_reply(self, message, history=None, context=None):
        return f"[fake-reply] {message[:120]}", "fake-model"

    async def stream_reply(self, message, history=None, context=None):
        yield "[fake-stream]"

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
        return []


@pytest.fixture()
def client():
    app = create_app()
    with TestClient(app) as c:
        c.app.state.ai_service = FakeAIService()
        c.app.state.memory_service = FakeMemoryService()
        yield c


def test_agent_execute_endpoint(client):
    resp = client.post(
        "/api/v1/agent/execute",
        json={"task": "اكتب دالة بايثون بسيطة تجمع رقمين", "session_id": "t1"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == "t1"
    assert "plan" in data
    assert "code_output" in data
    assert "review_output" in data
    assert "final_output" in data
    assert isinstance(data["steps"], list)
    assert len(data["steps"]) >= 3
