"""أدوات مساعدة للوكلاء (تنفيذ آمن محدود، قراءة/كتابة ملفات ضمن جذر المشروع)."""

from __future__ import annotations

import ast
import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple


PROJECT_ROOT = Path(__file__).resolve().parents[2]  # مجلد ryko-ai


def safe_project_path(rel_path: str) -> Path:
    """تقييد المسارات داخل جذر المشروع لمنع الوصول لملفات حساسة خارجياً."""
    rel_path = rel_path.lstrip("/\\")
    p = (PROJECT_ROOT / rel_path).resolve()
    try:
        p.relative_to(PROJECT_ROOT.resolve())
    except ValueError as exc:
        raise PermissionError("الوصول خارج مجلد المشروع غير مسموح.") from exc
    return p


def read_file(rel_path: str, max_chars: int = 20000) -> str:
    """قراءة ملف نصي من داخل المشروع."""
    p = safe_project_path(rel_path)
    if not p.exists() or not p.is_file():
        return f"[خطأ] الملف غير موجود: {rel_path}"
    content = p.read_text(encoding="utf-8", errors="replace")
    if len(content) > max_chars:
        return content[:max_chars] + "\n...[مقطوع]"
    return content


def write_file(rel_path: str, content: str) -> str:
    """كتابة/إنشاء ملف داخل المشروع (مع إنشاء المجلدات عند الحاجة)."""
    p = safe_project_path(rel_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"[تم] كتابة الملف: {rel_path}"


def run_python_sandbox(code: str, timeout_sec: int = 10) -> Tuple[bool, str]:
    """تنفيذ كود بايثون في عملية منفصلة (Sandbox بسيط عبر subprocess).

    ملاحظة: هذا ليس Sandbox أمنياً كاملاً، لكنه يمنع الوصول المباشر لكائنات التطبيق
    ويشغل العملية في subprocess مع مهلة زمنية.
    """
    # فحص أساسي لمنع استيرادات خطيرة شائعة
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, f"خطأ صياغة: {e}"

    forbidden = {"os", "subprocess", "socket", "shutil", "pathlib"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in forbidden:
                    return False, f"استيراد محظور لأسباب أمنية: {root}"
        if isinstance(node, ast.ImportFrom):
            if node.module:
                root = node.module.split(".")[0]
                if root in forbidden:
                    return False, f"استيراد محظور لأسباب أمنية: {root}"

    try:
        proc = subprocess.run(
            ["python", "-c", code],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        out = (proc.stdout or "") + (("\n[stderr]\n" + proc.stderr) if proc.stderr else "")
        if proc.returncode != 0:
            return False, out.strip() or f"انتهى الكود برمز خروج {proc.returncode}"
        return True, out.strip()
    except subprocess.TimeoutExpired:
        return False, f"انتهت المهلة ({timeout_sec} ثانية)."
    except Exception as e:
        return False, f"فشل التنفيذ: {e}"
