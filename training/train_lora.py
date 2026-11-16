"""تدريب LoRA لنموذج عربي أساسي (مثل Qwen2.5-Coder أو Gemma).

السكربت مصمم للتشغيل في بيئة تحتوي GPU وtorch/transformers/peft.
يدعم بيانات ChatML بصيغة JSONL ويخرج محولات LoRA.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

try:
    import torch
    from datasets import load_dataset
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        DataCollatorForLanguageModeling,
        Trainer,
        TrainingArguments,
    )
except Exception:  # pragma: no cover
    torch = None  # type: ignore
    load_dataset = None  # type: ignore


@dataclass
class TrainConfig:
    base_model: str
    data_path: str
    output_dir: str
    max_seq_len: int = 1024
    epochs: int = 1
    batch_size: int = 1
    grad_accum: int = 8
    lr: float = 2e-4
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    use_4bit: bool = True


def _format_messages(messages: List[Dict[str, str]]) -> str:
    """تحويل رسائل ChatML إلى نص تدريبي بسيط (fallback)."""
    parts = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        parts.append(f"<|{role}|>\n{content}")
    parts.append("<|assistant|>")
    return "\n".join(parts)


def _load_records(path: str):
    if load_dataset is None:
        raise RuntimeError("حزمة datasets غير متاحة")
    # تحميل JSONL كسجل train
    ds = load_dataset("json", data_files={"train": path})["train"]
    return ds


def main() -> None:
    parser = argparse.ArgumentParser(description="تدريب LoRA لنموذج Ryko العربي")
    parser.add_argument("--base-model", default="Qwen/Qwen2.5-Coder-7B-Instruct")
    parser.add_argument("--data-path", default="data/processed/train_chatml.jsonl")
    parser.add_argument("--output-dir", default="outputs/ryko-ar-lora")
    parser.add_argument("--max-seq-len", type=int, default=1024)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--grad-accum", type=int, default=8)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--no-4bit", action="store_true")
    args = parser.parse_args()

    if torch is None:
        raise RuntimeError("بيئة التدريب غير مكتملة: يلزم torch/transformers/peft/datasets")

    cfg = TrainConfig(
        base_model=args.base_model,
        data_path=args.data_path,
        output_dir=args.output_dir,
        max_seq_len=args.max_seq_len,
        epochs=args.epochs,
        batch_size=args.batch_size,
        grad_accum=args.grad_accum,
        lr=args.lr,
        use_4bit=not args.no_4bit,
    )

    tokenizer = AutoTokenizer.from_pretrained(cfg.base_model, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    quant_config = None
    if cfg.use_4bit:
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
        )

    model = AutoModelForCausalLM.from_pretrained(
        cfg.base_model,
        device_map="auto",
        quantization_config=quant_config,
    )
    if cfg.use_4bit:
        model = prepare_model_for_kbit_training(model)

    lora_config = LoraConfig(
        r=cfg.lora_r,
        lora_alpha=cfg.lora_alpha,
        lora_dropout=cfg.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    )
    model = get_peft_model(model, lora_config)

    ds = _load_records(cfg.data_path)

    def tokenize_fn(batch: Dict[str, Any]) -> Dict[str, Any]:
        texts = []
        for msgs in batch["messages"]:
            if hasattr(tokenizer, "apply_chat_template"):
                try:
                    texts.append(tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False))
                    continue
                except Exception:
                    pass
            texts.append(_format_messages(msgs))
        out = tokenizer(
            texts,
            truncation=True,
            max_length=cfg.max_seq_len,
            padding="max_length",
        )
        out["labels"] = out["input_ids"].copy()
        return out

    tokenized = ds.map(tokenize_fn, batched=True, remove_columns=ds.column_names)

    args_train = TrainingArguments(
        output_dir=cfg.output_dir,
        num_train_epochs=cfg.epochs,
        per_device_train_batch_size=cfg.batch_size,
        gradient_accumulation_steps=cfg.grad_accum,
        learning_rate=cfg.lr,
        fp16=torch.cuda.is_available(),
        logging_steps=10,
        save_steps=200,
        save_total_limit=2,
        report_to=[],
    )

    trainer = Trainer(
        model=model,
        args=args_train,
        train_dataset=tokenized,
        data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
    )
    trainer.train()
    trainer.save_model(cfg.output_dir)
    tokenizer.save_pretrained(cfg.output_dir)
    print(f"تم حفظ محولات LoRA في: {cfg.output_dir}")


if __name__ == "__main__":
    main()
