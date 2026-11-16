"""وكيل البرمجة: يكتب الأكواد بناءً على الخطة والسياق."""

from __future__ import annotations

from app.agents.base import BaseAgent


class CoderAgent(BaseAgent):
    name = "coder"
    role = "Coder Agent"
    system_prompt = (
        "أنت وكيل برمجة في نظام Ryko-AI متعدد الوكلاء. "
        "مهمتك: كتابة كود نظيف وقابل للتشغيل بناءً على خطة وكيل التخطيط والسياق المشترك. "
        "اتبع أسلوب المشروع (FastAPI/Python)، واكتب تعليقات بالعربية عند الحاجة. "
        "قدّم الكود ضمن بلوكات markdown مناسبة، مع تحديد اسم الملف إن أمكن."
    )
