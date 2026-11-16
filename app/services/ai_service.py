"""خدمة الذكاء الاصطناعي: DeepSeek API الآن، ونموذج محلي لاحقاً."""

from __future__ import annotations

import json
from typing import AsyncGenerator, List, Optional

import httpx

from app.core.config import Settings
from app.schemas.chat import ChatMessage, ModelInfo


class AIService:
    """طبقة موحدة للتعامل مع مزود النموذج."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._client: Optional[httpx.AsyncClient] = None
        self._ready = False

    async def initialize(self) -> None:
        """تهيئة عميل HTTP غير متزامن."""
        self._client = httpx.AsyncClient(timeout=60.0)
        # الخدمة تعتبر جاهزة إذا كان هناك مفتاح API أو مسار نموذج محلي
        self._ready = bool(self.settings.deepseek_api_key or self.settings.local_model_path)

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
        self._client = None
        self._ready = False

    @property
    def ready(self) -> bool:
        return self._ready

    def available_models(self) -> List[ModelInfo]:
        models = [
            ModelInfo(
                id=self.settings.deepseek_model,
                provider="deepseek",
                available=bool(self.settings.deepseek_api_key),
                description="مزود افتراضي للـ MVP عبر DeepSeek API",
            )
        ]
        if self.settings.local_model_path:
            models.append(
                ModelInfo(
                    id="ryko-arabic-local",
                    provider="local",
                    available=True,
                    description=f"نموذج محلي/مدرب: {self.settings.local_model_path}",
                )
            )
        return models

    def _build_messages(
        self,
        message: str,
        history: Optional[List[ChatMessage]],
        context: List[str],
    ) -> List[dict]:
        """بناء رسائل المحادثة مع حقن سياق الذاكرة (RAG/context)."""
        messages: List[dict] = [
            {
                "role": "system",
                "content": (
                    "أنت Ryko-AI، مساعد برمجة وذكاء اصطناعي عربي. "
                    "أجب بدقة ووضوح، واستخدم السياق المقدم عند توفره."
                ),
            }
        ]
        if context:
            ctx_text = "\n".join(f"- {c}" for c in context[:3])
            messages.append(
                {
                    "role": "system",
                    "content": f"سياق مسترجع من الذاكرة:\n{ctx_text}",
                }
            )
        if history:
            for item in history:
                messages.append({"role": item.role, "content": item.content})
        messages.append({"role": "user", "content": message})
        return messages

    async def generate_reply(
        self,
        message: str,
        history: Optional[List[ChatMessage]] = None,
        context: Optional[List[str]] = None,
    ) -> tuple[str, str]:
        """توليد رد كامل (غير متدفق)."""
        context = context or []
        # الأولوية للنموذج المحلي عند توفره مستقبلاً (حاليا DeepSeek API)
        if self.settings.deepseek_api_key:
            reply = await self._call_deepseek(message, history, context, stream=False)
            return reply, self.settings.deepseek_model
        if self.settings.local_model_path:
            # نقطة دمج مستقبلية: استدعاء النموذج المحلي/المحول إلى GGUF
            return (
                "تم اكتشاف مسار نموذج محلي، لكن واجهة الاستدلال المحلي غير مفعلة في هذه النسخة. "
                "يرجى إعداد خادم استدلال محلي أو استخدام DeepSeek API مؤقتاً.",
                "ryko-arabic-local",
            )
        return (
            "الخدمة غير مهيأة: أضف DEEPSEEK_API_KEY في ملف .env أو وفر نموذجاً محلياً.",
            "unconfigured",
        )

    async def stream_reply(
        self,
        message: str,
        history: Optional[List[ChatMessage]] = None,
        context: Optional[List[str]] = None,
    ) -> AsyncGenerator[str, None]:
        """بث الرد على شكل SSE chunks."""
        context = context or []
        if self.settings.deepseek_api_key:
            async for chunk in self._stream_deepseek(message, history, context):
                yield chunk
            return
        # fallback غير متدفق كبث بسيط
        reply, _ = await self.generate_reply(message, history, context)
        yield reply

    async def _call_deepseek(
        self,
        message: str,
        history: Optional[List[ChatMessage]],
        context: List[str],
        stream: bool = False,
    ) -> str:
        assert self._client is not None
        url = f"{self.settings.deepseek_base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self.settings.deepseek_model,
            "messages": self._build_messages(message, history, context),
            "stream": stream,
        }
        headers = {
            "Authorization": f"Bearer {self.settings.deepseek_api_key}",
            "Content-Type": "application/json",
        }
        resp = await self._client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )

    async def _stream_deepseek(
        self,
        message: str,
        history: Optional[List[ChatMessage]],
        context: List[str],
    ) -> AsyncGenerator[str, None]:
        assert self._client is not None
        url = f"{self.settings.deepseek_base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self.settings.deepseek_model,
            "messages": self._build_messages(message, history, context),
            "stream": True,
        }
        headers = {
            "Authorization": f"Bearer {self.settings.deepseek_api_key}",
            "Content-Type": "application/json",
        }
        async with self._client.stream("POST", url, json=payload, headers=headers) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data_str = line[len("data:") :].strip()
                if data_str == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    delta = data.get("choices", [{}])[0].get("delta", {}).get("content")
                    if delta:
                        yield delta
                except Exception:
                    continue
