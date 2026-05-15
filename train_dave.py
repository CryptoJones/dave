#!/usr/bin/env python3
"""
Dave — QLoRA fine-tune of Llama-3.3-70B-Instruct for security assessment report writing.

Reads:  $DAVE_DATA_DIR/shuffled_training.jsonl  (one {"prompt","completion"} JSON per line)
Writes: $DAVE_OUTPUT_DIR/                       (LoRA adapter only — base weights unchanged)

Target hardware: single A100 80GB (RunPod). See setup_dave.sh for dependency install.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import torch
from datasets import load_dataset
from peft import LoraConfig, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)
from trl import SFTConfig, SFTTrainer


BASE_MODEL = os.environ.get("DAVE_BASE_MODEL", "meta-llama/Llama-3.3-70B-Instruct")
DATA_DIR = Path(os.environ.get("DAVE_DATA_DIR", str(Path(__file__).parent / "data")))
OUTPUT_DIR = Path(os.environ.get("DAVE_OUTPUT_DIR", "/home/akclark/Source/adapters/dave"))
TRAIN_FILE = DATA_DIR / "shuffled_training.jsonl"

SYSTEM_PROMPT = (
    "You are Dave — a writing assistant for authorized US security assessments. "
    "You write professional, APA/(ISC)²-aligned finding narratives, executive summaries, "
    "remediation guidance, methodology sections, risk narratives, and evidence documentation. "
    "You never produce offensive how-to content. You require written authorization for any "
    "specific target before writing target-specific content. Outputs are draft material for a "
    "qualified security professional to review."
)


def require_data_file() -> None:
    if not TRAIN_FILE.exists():
        sys.exit(
            f"ERROR: training file not found: {TRAIN_FILE}\n"
            f"Run ./build_training_data.sh first (or set DAVE_DATA_DIR)."
        )
    if TRAIN_FILE.stat().st_size == 0:
        sys.exit(f"ERROR: training file is empty: {TRAIN_FILE}")


def check_for_placeholder_rows(path: Path, sample: int = 200) -> None:
    """Fail loudly if the training set still contains the old unfilled-template rows."""
    bad_markers = (
        "Extract key vulnerability/finding from context",
        "Write APA/(ISC)²-aligned summary based on chunk",
    )
    seen = 0
    bad = 0
    with path.open() as f:
        for line in f:
            seen += 1
            if any(m in line for m in bad_markers):
                bad += 1
            if seen >= sample:
                break
    if bad:
        sys.exit(
            f"ERROR: detected {bad}/{seen} sampled rows containing unfilled placeholder "
            f"templates. Refusing to train — rebuild data first."
        )


def format_example(example: dict) -> dict:
    """Render one prompt/completion pair using the tokenizer's chat template at train time."""
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": example["prompt"]},
            {"role": "assistant", "content": example["completion"]},
        ]
    }


def main() -> None:
    require_data_file()
    check_for_placeholder_rows(TRAIN_FILE)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not torch.cuda.is_available():
        sys.exit("ERROR: CUDA not available. Dave needs an A100 80GB (or equivalent).")

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        attn_implementation="sdpa",
    )
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    model.config.use_cache = False

    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
    )

    raw = load_dataset("json", data_files=str(TRAIN_FILE), split="train")
    splits = raw.train_test_split(test_size=0.01, seed=42)
    train_ds = splits["train"].map(format_example, remove_columns=splits["train"].column_names)
    eval_ds = splits["test"].map(format_example, remove_columns=splits["test"].column_names)

    report_to = ["wandb"] if os.environ.get("WANDB_API_KEY") else []

    sft_config = SFTConfig(
        output_dir=str(OUTPUT_DIR),
        num_train_epochs=int(os.environ.get("DAVE_EPOCHS", "2")),
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=16,
        gradient_checkpointing=True,
        learning_rate=2e-4,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        weight_decay=0.0,
        bf16=True,
        max_length=2048,
        packing=False,
        logging_steps=20,
        eval_strategy="steps",
        eval_steps=200,
        save_strategy="steps",
        save_steps=200,
        save_total_limit=3,
        optim="paged_adamw_8bit",
        report_to=report_to,
    )

    trainer = SFTTrainer(
        model=model,
        args=sft_config,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        peft_config=lora_config,
        processing_class=tokenizer,
    )

    trainer.train()
    trainer.save_model(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))
    print(f"\nAdapter saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
