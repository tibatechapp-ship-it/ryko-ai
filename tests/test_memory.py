"""اختبارات خدمة الذاكرة مع degrade آمن عند غياب chromadb."""

import pytest

from app.services.memory import MemoryService


@pytest.mark.asyncio
async def test_memory_service_initializes_safely(tmp_path):
    svc = MemoryService(persist_path=str(tmp_path / "chroma"))
    await svc.initialize()
    # قد تكون غير جاهزة إذا chromadb غير مثبتة في البيئة الحالية، وهذا مقبول
    assert isinstance(svc.ready, bool)
    # الواجهات يجب ألا ترمي أخطاء حتى لو غير جاهزة
    await svc.add_message("s1", "user", "مرحبا")
    ctx = await svc.get_relevant_context("s1", "مرحبا")
    assert isinstance(ctx, list)
    await svc.close()
