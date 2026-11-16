"""مسارات الدردشة والبث والنماذج والصحة."""

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from app.core.config import Settings, get_settings
from app.schemas.chat import ChatRequest, ChatResponse, HealthResponse, ModelInfo

router = APIRouter(tags=["chat"])


def verify_api_key(
    x_api_key: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    """تحقق بسيط عبر API Key (يمكن استبداله/تعزيزه بـ JWT)."""
    if settings.api_key and x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="مفتاح API غير صالح")


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    request: Request,
    _: None = Depends(verify_api_key),
):
    """استقبال رسالة وإرجاع رد كامل مع استخدام الذاكرة."""
    ai_service = request.app.state.ai_service
    memory_service = request.app.state.memory_service

    context = []
    if payload.use_memory:
        context = await memory_service.get_relevant_context(payload.session_id, payload.message)
        await memory_service.add_message(payload.session_id, "user", payload.message)

    reply, model = await ai_service.generate_reply(
        message=payload.message,
        history=payload.history,
        context=context,
    )

    if payload.use_memory:
        await memory_service.add_message(payload.session_id, "assistant", reply)

    return ChatResponse(session_id=payload.session_id, reply=reply, model=model, context_used=context)


@router.post("/stream")
async def stream_chat(
    payload: ChatRequest,
    request: Request,
    _: None = Depends(verify_api_key),
):
    """بث الرد مباشرة عبر Server-Sent Events (SSE)."""
    ai_service = request.app.state.ai_service
    memory_service = request.app.state.memory_service

    context = []
    if payload.use_memory:
        context = await memory_service.get_relevant_context(payload.session_id, payload.message)
        await memory_service.add_message(payload.session_id, "user", payload.message)

    async def event_generator():
        parts: list[str] = []
        try:
            async for chunk in ai_service.stream_reply(
                message=payload.message,
                history=payload.history,
                context=context,
            ):
                parts.append(chunk)
                yield {"event": "message", "data": chunk}
            full_reply = "".join(parts)
            if payload.use_memory and full_reply.strip():
                await memory_service.add_message(payload.session_id, "assistant", full_reply)
            yield {"event": "done", "data": "[DONE]"}
        except Exception as e:
            yield {"event": "error", "data": str(e)}

    return EventSourceResponse(event_generator())


@router.get("/models", response_model=list[ModelInfo])
async def list_models(request: Request, _: None = Depends(verify_api_key)):
    """عرض النماذج المتاحة."""
    return request.app.state.ai_service.available_models()


@router.get("/health", response_model=HealthResponse)
async def health(request: Request):
    """فحص جاهزية الخادم والخدمات."""
    settings: Settings = request.app.state.settings
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        version=settings.app_version,
        model_ready=bool(request.app.state.ai_service.ready),
        memory_ready=bool(request.app.state.memory_service.ready),
    )
