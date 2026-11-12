"""المدقّق الأولي (بذرة G2): يطابق ادعاءات الوكيل مع أثر الأدوات في السجل."""
import json
from pathlib import Path

def audit(path="trace.jsonl"):
    tools_used, claims = set(), []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        ev = json.loads(line)
        if ev["type"] == "tool_result":
            tools_used.add(ev["tool"])
        elif ev["type"] == "claim":
            claims.append(ev)
    checked = [c for c in claims if c.get("tool")]
    unsupported = [c for c in checked if c["tool"] not in tools_used]
    phr = len(unsupported) / len(checked) if checked else 0.0
    return {"claims": len(checked), "unsupported": unsupported, "phr": phr}
