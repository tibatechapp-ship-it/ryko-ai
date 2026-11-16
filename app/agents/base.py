"""الكلاس الأساسي للوكلاء: BaseAgent.

يتولى BaseAgent:
- الاتصال بخدمة الذكاء الاصطناعي (AIService)
- الوصول لطبقة الذاكرة (MemoryService) عند الحاجة
- بناء الرسائل مع System Prompt خاص بكل وكيل
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.schemas.chat import ChatMessage
from app.services.ai_service import AIService
from app.services.memory import MemoryService


class BaseAgent:
    """قاعدة مشتركة لكل الوكلاء."""

    name: str = "base"
    role: str = "Base Agent"
    system_prompt: str = "أنت وكيل مساعد."

    def __init__(self, ai_service: AIService, memory_service: Optional[MemoryService] = None):
        self.ai_service = ai_service
        self.memory_service = memory_service

    def _build_messages(
        self,
        task: str,
        shared_context: Optional[Dict[str, Any]] = None,
        history: Optional[List[ChatMessage]] = None,
        memory_context: Optional[List[str]] = None,
    ) -> List[dict]:
        """بناء رسائل الوكيل مع System Prompt والتعليمات."""
        messages: List[dict] = [{"role": "system", "content": self.system_prompt}]

        if memory_context:
            ctx_text = "\n".join(f"- {c}" for c in memory_context[:5])
            messages.append({"role": "system", "content": f"سياق من الذاكرة:\n{ctx_text}"})

        if shared_context:
            # إضافة ملخص السياق المشترك بشكل منظم
            summary_lines = []
            for k, v in shared_context.items():
                if v is None:
                    continue
                text = str(v)
                if len(text) > 4000:
                    text = text[:4000] + "\n...(مقتطع)"
                summary_lines.append(f"## {k}\n{text}")
            if summary_lines:
                messages.append(
                    {
                        "role": "system",
                        "content": "سياق مشترك بين الوكلاء:\n" + "\n\n".join(summary_lines),
                    }
                )

        if history:
            for item in history:
                messages.append({"role": item.role, "content": item.content})

        messages.append({"role": "user", "content": task})
        return messages

    async def _call_llm(self, messages: List[dict]) -> str:
        """استدعاء النموذج عبر AIService (بدون مسار /generate مباشر، نستخدم build + call)."""
        # نستخدم المسار الداخلي عبر generate_reply عبر صياغة رسالة واحدة + حقن history
        # لتفادي تكرار منطق prompt. هنا نمرر آخر user كرسالة وأي ما قبلها كـ history نصية.
        if not messages:
            return ""
        # فصل system+shared من history ومن الرسالة الأخيرة
        system_parts: List[str] = []
        hist: List[ChatMessage] = []
        last_user = ""
        for m in messages:
            if m["role"] == "system":
                system_parts.append(m["content"])
            elif m["role"] == "user":
                last_user = m["content"]
            elif m["role"] == "assistant":
                hist.append(ChatMessage(role="assistant", content=m["content"]))

        # ندمج system في أول system افتراضي عبر تمرير context فارغ ونحقن في generate عبر history ليس مثالياً،
        # لذلك نستخدم طريقة مباشرة: نطلب من ai_service.generate_reply مع context = system_parts (عدا الأولى)
        context_extra = system_parts[1:] if len(system_parts) > 1 else []
        # لكن AIService يضيف system أساسي خاص به؛ هنا نفضل أن يكون لدينا تحكم. كحل عملي نستخدم generate_reply.
        reply, _ = await self.ai_service.generate_reply(
            message=last_user or "نفّذ المطلوب.",
            history=hist,
            context=context_extra,
        )
        return reply

    async def run(
        self,
        task: str,
        shared_context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """تشغيل الوكيل على مهمة معينة وإرجاع النص الناتج."""
        memory_ctx: List[str] = []
        if session_id and self.memory_service and getattr(self.memory_service, "ready", False):
            try:
                memory_ctx = await self.memory_service.get_relevant_context(session_id, task)
            except Exception:
                memory_ctx = []

        messages = self._build_messages(
            task=task,
            shared_context=shared_context,
            history=None,
            memory_context=memory_ctx,
        )
        return await self._call_llm(messages)
