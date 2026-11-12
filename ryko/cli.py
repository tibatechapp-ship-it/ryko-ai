"""واجهة أوامر Ryko: python -m ryko.cli demo | verify | audit"""
import argparse, sys
from pathlib import Path
from . import __version__
from .recorder import Recorder, verify_chain
from .auditor import audit

def _require(path):
    if not Path(path).exists():
        print(f"✘ لا يوجد سجل في: {path} — شغّل demo أولاً")
        sys.exit(2)

def _print_verify(path):
    ok, msg = verify_chain(path)
    print(("✔ " if ok else "✘ ") + msg)
    return ok

def _print_audit(path):
    rep = audit(path)
    for c in rep["unsupported"]:
        print(f"✘ ادعاء غير مدعوم: «{c['text']}» — لا أثر لأداة {c['tool']} في السجل")
    supported = rep["claims"] - len(rep["unsupported"])
    print(f"✔ ادعاءات مدعومة: {supported}")
    print(f"PHR = {rep['phr']:.0%}  ({len(rep['unsupported'])} من {rep['claims']})")
    return rep

def cmd_demo(args):
    r = Recorder(args.path)
    r.log("run_start", task="تجربة Ryko", condition="C4")
    r.tool_result("web.search", {"q": "تصحيح الأخطاء الكمومية"},
                  {"hits": 3}, tokens=812, cost_usd=0.004)
    r.claim("بحثتُ ووجدتُ 3 نتائج", tool="web.search")   # ادعاء صادق
    r.claim("شغّلتُ الاختبارات ونجحت", tool="code.run")  # ادعاء كاذب مزروع
    r.log("run_end", status="done")
    _print_verify(args.path)
    _print_audit(args.path)
    return 0  # الكذبة مزروعة عمداً — العرض ناجح دائماً

def cmd_verify(args):
    _require(args.path)
    return 0 if _print_verify(args.path) else 1

def cmd_audit(args):
    _require(args.path)
    rep = _print_audit(args.path)
    return 1 if rep["unsupported"] else 0  # خروج 1 = فشل تدقيق

def main(argv=None):
    p = argparse.ArgumentParser(prog="ryko", description="Ryko AI — طبقة الثقة للوكلاء")
    p.add_argument("--version", action="version", version=f"ryko {__version__}")
    p.add_argument("-p", "--path", default="trace.jsonl", help="مسار السجل")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("demo", help="تشغيلة تجريبية تكشف كذبة مزروعة").set_defaults(fn=cmd_demo)
    sub.add_parser("verify", help="التحقق من سلامة سلسلة السجل").set_defaults(fn=cmd_verify)
    sub.add_parser("audit", help="تدقيق الادعاءات مقابل الأثر").set_defaults(fn=cmd_audit)
    args = p.parse_args(argv)
    sys.exit(args.fn(args))

if __name__ == "__main__":
    main()
