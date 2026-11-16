"""نماذج الدردشة والبث."""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """رسالة واحدة في سجل المحادثة."""

    role: Literal["system", "user", "assistant"] = Field(..., description="دور المرسل")
    content: str = Field(..., min_length=1, description="نص الرسالة")


class ChatRequest(BaseModel):
    """طلب دردشة عادي."""

    message: str = Field(..., min_length=1, description="رسالة المستخدم الحالية")
    session_id: str = Field(default="default", min_length=1, description="معرف الجلسة للذاكرة")
    history: Optional[List[ChatMessage]] = Field(
        default=None, description="سجل محادثة اختياري يرسل من العميل"
    )
    stream: bool = Field(default=False, description="تفعيل البث عند الحاجة")
    use_memory: bool = Field(default=True, description="استخدام الذاكرة السياقية")


class ChatResponse(BaseModel):
    """استجابة دردشة غير متدفقة."""

    session_id: str
    reply: str
    model: str
    context_used: List[str] = Field(default_factory=list)


class ModelInfo(BaseModel):
    """معلومات نموذج متاح."""

    id: str
    provider: str
    available: bool
    description: str = ""


class HealthResponse(BaseModel):
    """حالة جاهزية الخادم."""

    status: str
    app: str
    version: str
    model_ready: bool
    memory_ready: bool
