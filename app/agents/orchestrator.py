"""المنسق (Orchestrator): يدير دورة حياة المهمة بين الوكلاء."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Dict, List, Optional

from app.agents.coder import CoderAgent
from app.agents.planner import PlannerAgent
from app.agents.reviewer import ReviewerAgent
from app.services.ai_service import AIService
from app.services.memory import MemoryService


@dataclass
class AgentStepEvent:
    step: str
    message: str
    status: str = "running"  # running|done|error


@dataclass
class OrchestratorResult:
    plan: str
    code_output: str
    review_output: str
    final_output: str
    steps: List[Dict[str, Any]] = field(default_factory=list)


class Orchestrator:
    """يدير التنفيذ المتسلسل: تخطيط -> برمجة -> مراجعة."""

    def __init__(self, ai_service: AIService, memory_service: Optional[MemoryService] = None):
        self.ai_service = ai_service
        self.memory_service = memory_service
        self.planner = PlannerAgent(ai_service=ai_service, memory_service=memory_service)
        self.coder = CoderAgent(ai_service=ai_service, memory_service=memory_service)
        self.reviewer = ReviewerAgent(ai_service=ai_service, memory_service=memory_service)

    async def execute(self, task: str, session_id: str = "default") -> OrchestratorResult:
        """تنفيذ المهمة كاملة وإرجاع النتيجة النهائية."""
        steps_log: List[Dict[str, Any]] = []
        shared: Dict[str, Any] = {"original_task": task}

        # 1) تخطيط
        plan = await self.planner.run(task=task, shared_context=shared, session_id=session_id)
        shared["plan"] = plan
        steps_log.append({"agent": "planner", "status": "done"})

        # 2) برمجة (مع مراعاة السياق من الذاكرة داخل الوكلاء)
        coder_task = (
            "نفّذ المهمة التالية بناءً على الخطة المعطاة في السياق المشترك.\n\n"
            f"المهمة الأصلية:\n{task}"
        )
        code_output = await self.coder.run(task=coder_task, shared_context=shared, session_id=session_id)
        shared["code_output"] = code_output
        steps_log.append({"agent": "coder", "status": "done"})

        # 3) مراجعة
        reviewer_task = (
            "راجع المخرجات البرمجية في السياق المشترك (خطة + كود). "
            "أعطِ قائمة ملاحظات ثم النسخة النهائية المقترحة إن وُجدت تحسينات مهمة."
        )
        review_output = await self.reviewer.run(
            task=reviewer_task, shared_context=shared, session_id=session_id
        )
        shared["review_output"] = review_output
        steps_log.append({"agent": "reviewer", "status": "done"})

        final_output = (
            "## الخطة\n"
            f"{plan}\n\n"
            "## مخرجات البرمجة\n"
            f"{code_output}\n\n"
            "## المراجعة والنسخة النهائية\n"
            f"{review_output}"
        )

        # حفظ ملخص في الذاكرة إن توفرت
        if self.memory_service and getattr(self.memory_service, "ready", False):
            try:
                await self.memory_service.add_message(
                    session_id, "assistant", f"[agents] نتيجة تنفيذ: {final_output[:4000]}"
                )
            except Exception:
                pass

        return OrchestratorResult(
            plan=plan,
            code_output=code_output,
            review_output=review_output,
            final_output=final_output,
            steps=steps_log,
        )

    async def stream_execute(self, task: str, session_id: str = "default") -> AsyncGenerator[Dict[str, Any], None]:
        """بث خطوات الوكلاء حياً (أحداث نصية)."""
        shared: Dict[str, Any] = {"original_task": task}

        yield {"event": "step", "data": "جاري التخطيط..."}
        plan = await self.planner.run(task=task, shared_context=shared, session_id=session_id)
        shared["plan"] = plan
        yield {"event": "step_done", "data": "انتهى التخطيط."}
        yield {"event": "plan", "data": plan}

        yield {"event": "step", "data": "جاري كتابة الكود..."}
        coder_task = "نفّذ المهمة بناءً على الخطة في السياق المشترك.\n\n" + task
        code_output = await self.coder.run(task=coder_task, shared_context=shared, session_id=session_id)
        shared["code_output"] = code_output
        yield {"event": "step_done", "data": "انتهى البرمجة."}
        yield {"event": "code", "data": code_output}

        yield {"event": "step", "data": "جاري المراجعة..."}
        reviewer_task = "راجع الخطة والكود في السياق المشترك وأعطِ ملاحظات ثم النتيجة النهائية."
        review_output = await self.reviewer.run(
            task=reviewer_task, shared_context=shared, session_id=session_id
        )
        yield {"event": "step_done", "data": "انتهت المراجعة."}
        yield {"event": "review", "data": review_output}

        final_output = (
            "## الخطة\n"
            f"{plan}\n\n"
            "## مخرجات البرمجة\n"
            f"{code_output}\n\n"
            "## المراجعة والنسخة النهائية\n"
            f"{review_output}"
        )
        yield {"event": "final", "data": final_output}
        yield {"event": "done", "data": "[DONE]"}
