"""نقاط وصول نظام الوكلاء: تنفيذ كامل وبث الخطوات."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from app.core.config import Settings, get_settings
from app.schemas.agent import AgentExecuteRequest, AgentExecuteResponse
from app.agents.orchestrator import Orchestrator


router = APIRouter(tags=["agents"])


def verify_api_key(
    x_api_key: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    """تحقق بسيط عبر API Key."""
    if settings.api_key and x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="مفتاح API غير صالح")


def _build_orchestrator(request: Request) -> Orchestrator:
    ai_service = request.app.state.ai_service
    memory_service = request.app.state.memory_service
    return Orchestrator(ai_service=ai_service, memory_service=memory_service)


@router.post("/agent/execute", response_model=AgentExecuteResponse)
async def agent_execute(
    payload: AgentExecuteRequest,
    request: Request,
    _: None = Depends(verify_api_key),
):
    """تنفيذ مهمة معقدة عبر الوكلاء وإرجاع النتيجة النهائية."""
    orchestrator = _build_orchestrator(request)
    result = await orchestrator.execute(task=payload.task, session_id=payload.session_id)
    return AgentExecuteResponse(
        session_id=payload.session_id,
        plan=result.plan,
        code_output=result.code_output,
        review_output=result.review_output,
        final_output=result.final_output,
        steps=result.steps,
    )


@router.post("/agent/stream")
async def agent_stream(
    payload: AgentExecuteRequest,
    request: Request,
    _: None = Depends(verify_api_key),
):
    """بث خطوات الوكلاء مباشرة عبر SSE."""
    orchestrator = _build_orchestrator(request)

    async def event_generator():
        try:
            async for ev in orchestrator.stream_execute(task=payload.task, session_id=payload.session_id):
                event_name = ev.get("event", "message")
                data = ev.get("data", "")
                yield {"event": event_name, "data": str(data)}
        except Exception as e:
            yield {"event": "error", "data": str(e)}

    return EventSourceResponse(event_generator())
