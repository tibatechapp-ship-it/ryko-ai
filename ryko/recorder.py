"""الصندوق الأسود: سجل أحداث متسلسل الهاش (Hash-Chain) — نواة G1."""
import hashlib, json, time
from pathlib import Path

ZERO = "0" * 64

def _hash(obj) -> str:
    return hashlib.sha256(
        json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()

class Recorder:
    def __init__(self, path="trace.jsonl"):
        self.path = Path(path)
        self.prev = ZERO
        if self.path.exists():
            lines = self.path.read_text(encoding="utf-8").strip().splitlines()
            if lines:
                self.prev = json.loads(lines[-1])["hash"]

    def log(self, event_type, **fields):
        ev = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "type": event_type, **fields, "prev": self.prev}
        ev["hash"] = _hash(ev)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
        self.prev = ev["hash"]
        return ev

    def tool_result(self, tool, args, result, tokens=0, cost_usd=0.0, permission="R0"):
        return self.log("tool_result", tool=tool, args=args, result=result,
                        result_hash=_hash(result), tokens=tokens,
                        cost_usd=cost_usd, permission=permission)

    def claim(self, text, tool=None):
        return self.log("claim", text=text, tool=tool)

def verify_chain(path="trace.jsonl"):
    """يتحقق أن السجل لم يُعبث به وأن حلقاته متصلة."""
    prev = ZERO
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines, 1):
        ev = json.loads(line)
        stored = ev.pop("hash")
        if ev.get("prev") != prev:
            return False, f"انقطاع السلسلة عند السطر {i}"
        if _hash(ev) != stored:
            return False, f"تلاعب مكتشف عند السطر {i}"
        prev = stored
    return True, f"السلسلة سليمة ({len(lines)} أحداث)"
