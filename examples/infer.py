#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Aaron K. Clark
"""
Minimal inference example for the Dave QLoRA adapter.

Loads `meta-llama/Llama-3.3-70B-Instruct` in 4-bit NF4 + the Dave adapter,
then generates a single-finding writeup from a user-supplied title and
severity. Useful as a smoke test after training or after pulling the
published adapter from Hugging Face Hub.

Usage:
    python3 examples/infer.py
    python3 examples/infer.py --adapter ./dave_adapter --severity High \\
        --title "Authentication bypass in admin login"

Requirements:
    pip install transformers peft bitsandbytes accelerate
    A CUDA GPU with ≥42 GB VRAM (A100 80GB, H100 80GB, RTX PRO 6000 96GB,
    or A6000 with offload).
"""

from __future__ import annotations

import argparse
import sys
from textwrap import dedent

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

BASE_MODEL = "meta-llama/Llama-3.3-70B-Instruct"
DEFAULT_ADAPTER = "Ronin48LLC/Dave-Llama-3.3-70B-QLoRA"

DAVE_SYSTEM = (
    "You are Dave — a writing assistant for authorized US security assessments. "
    "You write professional, APA/(ISC)²-aligned finding narratives, executive "
    "summaries, remediation guidance, methodology sections, risk narratives, and "
    "evidence documentation. You never produce offensive how-to content. You "
    "require written authorization for any specific target before writing "
    "target-specific content. Outputs are draft material for a qualified "
    "security professional to review."
)


def load(adapter: str):
    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )
    print(f"[loader] base model:    {BASE_MODEL}", file=sys.stderr)
    print(f"[loader] adapter:       {adapter}", file=sys.stderr)

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    base = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb,
        device_map="auto",
        torch_dtype=torch.bfloat16,
    )
    model = PeftModel.from_pretrained(base, adapter)
    model.eval()
    return tokenizer, model


def generate_finding(tokenizer, model, title: str, severity: str,
                     difficulty: str, finding_type: str,
                     max_new_tokens: int, temperature: float, top_p: float) -> str:
    user_msg = dedent(f"""\
        Write a professional vulnerability finding titled "{title}" for inclusion
        in a security assessment report. Severity is {severity}; difficulty to
        exploit is {difficulty}; category is {finding_type}.""")

    messages = [
        {"role": "system", "content": DAVE_SYSTEM},
        {"role": "user", "content": user_msg},
    ]
    inputs = tokenizer.apply_chat_template(
        messages, return_tensors="pt", add_generation_prompt=True
    ).to(model.device)

    with torch.inference_mode():
        out = model.generate(
            inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=temperature,
            top_p=top_p,
            repetition_penalty=1.05,
        )
    return tokenizer.decode(out[0][inputs.shape[1]:], skip_special_tokens=True)


def main() -> None:
    p = argparse.ArgumentParser(description="Run a single inference against the Dave adapter.")
    p.add_argument("--adapter", default=DEFAULT_ADAPTER,
                   help="HF Hub repo id or local path to the adapter directory.")
    p.add_argument("--title", default="Stored XSS in admin search interface")
    p.add_argument("--severity", default="Medium",
                   choices=["Informational", "Low", "Medium", "High", "Critical"])
    p.add_argument("--difficulty", default="Low",
                   choices=["Undetermined", "Low", "Medium", "High"])
    p.add_argument("--type", dest="finding_type", default="Data Validation",
                   help="Vulnerability category (e.g. Data Validation, Cryptography, Access Controls).")
    p.add_argument("--max-new-tokens", type=int, default=512)
    p.add_argument("--temperature", type=float, default=0.6)
    p.add_argument("--top-p", type=float, default=0.9)
    args = p.parse_args()

    if not torch.cuda.is_available():
        sys.exit("ERROR: CUDA not available. Dave needs a 4-bit-capable GPU "
                 "with at least 42 GB VRAM.")

    tokenizer, model = load(args.adapter)
    output = generate_finding(
        tokenizer, model,
        title=args.title,
        severity=args.severity,
        difficulty=args.difficulty,
        finding_type=args.finding_type,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        top_p=args.top_p,
    )

    print("=" * 72)
    print(f"Dave wrote: {args.title}  (Severity={args.severity})")
    print("=" * 72)
    print(output)
    print("=" * 72)
    print("REMINDER: This is draft material. Verify every technical claim, "
          "CVSS rating, and reference before delivering to a client.")


if __name__ == "__main__":
    main()
