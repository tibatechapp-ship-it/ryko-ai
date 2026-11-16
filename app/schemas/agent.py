"""نماذج طلب/استجابة نظام الوكلاء."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentExecuteRequest(BaseModel):
    """طلب تنفيذ مهمة عبر الوكلاء."""

    task: str = Field(..., min_length=1, description="المهمة المعقدة التي يوزعها المنسق")
    session_id: str = Field(default="default", min_length=1, description="معرف الجلسة للذاكرة")


class AgentExecuteResponse(BaseModel):
    """استجابة تنفيذ الوكلاء."""

    session_id: str
    plan: str
    code_output: str
    review_output: str
    final_output: str
    steps: List[Dict[str, Any]] = Field(default_factory=list)
