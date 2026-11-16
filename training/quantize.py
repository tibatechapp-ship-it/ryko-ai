"""تحويل النموذج المدرب إلى صيغة GGUF (للتشغيل عبر llama.cpp).

يتطلب توفر أدوات llama.cpp (convert_hf_to_gguf.py و/أو llama-quantize).
السكربت يوفر واجهة موحدة لتنفيذ خطوات الدمج والتحويل والتكميم.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def run(cmd: list[str]) -> None:
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="تحويل نموذج Ryko إلى GGUF")
    parser.add_argument("--hf-model-dir", required=True, help="مسار النموذج بصيغة HuggingFace (أو مدمج مع LoRA)")
    parser.add_argument("--outfile", default="outputs/ryko-ar.gguf", help="ملف GGUF الناتج")
    parser.add_argument("--llama-cpp-dir", default="./llama.cpp", help="مسار مستودع llama.cpp")
    parser.add_argument("--quant-type", default="Q4_K_M", help="نوع التكميم (مثل Q4_K_M)")
    parser.add_argument("--skip-quantize", action="store_true", help="تخطي خطوة التكميم إن كان الملف بالفعل GGUF f16")
    args = parser.parse_args()

    llama_dir = Path(args.llama_cpp_dir)
    convert_script = llama_dir / "convert_hf_to_gguf.py"
    quant_bin = llama_dir / "build" / "bin" / "llama-quantize"

    out_path = Path(args.outfile)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not convert_script.exists():
        raise SystemExit(
            f"لم يتم العثور على {convert_script}. استنسخ llama.cpp وحدد --llama-cpp-dir بشكل صحيح."
        )

    f16_path = out_path.with_suffix(".f16.gguf")
    run(["python3", str(convert_script), args.hf_model_dir, "--outfile", str(f16_path)])

    if args.skip_quantize:
        print(f"تم إنشاء GGUF (f16): {f16_path}")
        return

    if not quant_bin.exists():
        print(f"تحذير: لم يتم العثور على {quant_bin}، سيتم الإبقاء على ملف f16 فقط: {f16_path}")
        return

    run([str(quant_bin), str(f16_path), str(out_path), args.quant_type])
    print(f"تم إنشاء GGUF المكمم: {out_path}")


if __name__ == "__main__":
    main()
