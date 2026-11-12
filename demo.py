"""أول تشغيلة: وكيل يحكي قصة… وRyko يكشف الكذبة. شغّل: python demo.py"""
from ryko.recorder import Recorder, verify_chain
from ryko.auditor import audit

r = Recorder("trace.jsonl")
r.log("run_start", task="تجربة Ryko الأولى", condition="C4")
r.tool_result("web.search", {"q": "تصحيح الأخطاء الكمومية"},
              {"hits": 3}, tokens=812, cost_usd=0.004)
r.claim("بحثتُ ووجدتُ 3 نتائج", tool="web.search")      # ادعاء صادق
r.claim("شغّلتُ الاختبارات ونجحت", tool="code.run")     # ادعاء كاذب مزروع
r.log("run_end", status="done")

ok, msg = verify_chain("trace.jsonl")
print(("✔ " if ok else "✘ ") + msg)

report = audit("trace.jsonl")
for c in report["unsupported"]:
    print(f"✘ ادعاء غير مدعوم: «{c['text']}» — لا أثر لأداة {c['tool']} في السجل")
supported = report["claims"] - len(report["unsupported"])
print(f"✔ ادعاءات مدعومة: {supported}")
print(f"PHR = {report['phr']:.0%}  ({len(report['unsupported'])} من {report['claims']})")
