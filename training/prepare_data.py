"""تحضير وتنظيف بيانات التدريب العربية (CIDAR / Arabic-Coding-ChatML).

يقوم السكربت بتحميل مجموعات بيانات من HuggingFace (عند توفرها) أو قراءة ملفات محلية،
تنظيفها، وتحويلها لصيغة ChatML موحدة ثم حفظها كـ JSONL.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    from datasets import load_dataset
except Exception:  # pragma: no cover
    load_dataset = None  # type: ignore


SYSTEM_PROMPT = (
    "أنت Ryko-AI، نموذج مساعد عربي متخصص في البرمجة والتواصل التقني."
)


def _normalize_record(instruction: str, output: str, input_text: str = "") -> Optional[Dict[str, Any]]:
    """تحويل عينة إلى صيغة رسائل ChatML موحدة مع تنظيف بسيط."""
    instruction = (instruction or "").strip()
    output = (output or "").strip()
    input_text = (input_text or "").strip()
    if not instruction or not output:
        return None
    user_content = instruction if not input_text else f"{instruction}\n\n{input_text}"
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": output},
        ]
    }


def _from_hf_dataset(name: str, split: str, limit: Optional[int]) -> List[Dict[str, Any]]:
    if load_dataset is None:
        raise RuntimeError("حزمة datasets غير مثبتة. ثبّت المتطلبات أولاً.")
    ds = load_dataset(name, split=split)
    records: List[Dict[str, Any]] = []
    for row in ds:
        rec = _normalize_record(
            instruction=str(row.get("instruction") or row.get("prompt") or row.get("question") or ""),
            output=str(row.get("output") or row.get("response") or row.get("answer") or ""),
            input_text=str(row.get("input") or ""),
        )
        if rec:
            records.append(rec)
        if limit and len(records) >= limit:
            break
    return records


def _from_local_jsonl(path: Path, limit: Optional[int]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if "messages" in row and isinstance(row["messages"], list):
                records.append({"messages": row["messages"]})
            else:
                rec = _normalize_record(
                    instruction=str(row.get("instruction") or row.get("prompt") or ""),
                    output=str(row.get("output") or row.get("response") or ""),
                    input_text=str(row.get("input") or ""),
                )
                if rec:
                    records.append(rec)
            if limit and len(records) >= limit:
                break
    return records


def write_jsonl(records: Iterable[Dict[str, Any]], out_path: Path) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with out_path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="تحضير بيانات التدريب العربية لـ Ryko-AI")
    parser.add_argument("--dataset", default="arbml/CIDAR", help="اسم مجموعة البيانات على HuggingFace")
    parser.add_argument("--split", default="train", help="split المستخدم")
    parser.add_argument("--local-jsonl", default="", help="مسار ملف JSONL محلي بديل")
    parser.add_argument("--out", default="data/processed/train_chatml.jsonl", help="مسار ملف الإخراج")
    parser.add_argument("--limit", type=int, default=20000, help="الحد الأقصى للعينات")
    parser.add_argument("--shuffle", action="store_true", help="خلط العينات قبل الحفظ")
    args = parser.parse_args()

    if args.local_jsonl:
        records = _from_local_jsonl(Path(args.local_jsonl), args.limit)
    else:
        records = _from_hf_dataset(args.dataset, args.split, args.limit)

    if args.shuffle:
        random.shuffle(records)

    count = write_jsonl(records, Path(args.out))
    print(f"تم حفظ {count} عينة بصيغة ChatML في: {args.out}")


if __name__ == "__main__":
    main()
