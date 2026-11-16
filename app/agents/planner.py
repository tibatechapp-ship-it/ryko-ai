"""وكيل التخطيط: يحلل المهمة ويضع خطة عمل خطوة بخطوة."""

from __future__ import annotations

from app.agents.base import BaseAgent


class PlannerAgent(BaseAgent):
    name = "planner"
    role = "Planner Agent"
    system_prompt = (
        "أنت وكيل تخطيط في نظام Ryko-AI متعدد الوكلاء. "
        "مهمتك: تحليل المهمة المعقدة وتقسيمها إلى خطة عمل واضحة مرقمة (خطوة 1..ن). "
        "أعطِ مخرجات عملية: أهداف، خطوات تنفيذ، ملفات محتملة للتعديل/الإنشاء، ومخاطر مختصرة. "
        "لا تكتب كوداً كاملاً هنا؛ ركز على الخطة."
    )
