"""نقطة دخول تطبيق FastAPI مع تهيئة الخدمات عند بدء التشغيل."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.routes.agents import router as agents_router
from app.api.v1.routes.chat import router as chat_router
from app.core.config import get_settings
from app.services.ai_service import AIService
from app.services.memory import MemoryService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """تهيئة وإغلاق الخدمات (AI + Memory) ضمن دورة حياة التطبيق."""
    settings = get_settings()
    app.state.settings = settings

    memory_service = MemoryService(persist_path=settings.database_url)
    ai_service = AIService(settings=settings)

    await memory_service.initialize()
    await ai_service.initialize()

    app.state.memory_service = memory_service
    app.state.ai_service = ai_service

    try:
        yield
    finally:
        await ai_service.close()
        await memory_service.close()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
    app.include_router(chat_router, prefix=settings.api_prefix)
    app.include_router(agents_router, prefix=settings.api_prefix)
    return app


app = create_app()
