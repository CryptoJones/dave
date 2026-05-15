#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Aaron K. Clark
"""
Parse a Dave training log, extract the metrics the model card asks for, and
substitute them into the staged HF Hub README (MODEL_CARD copy).

Invoked by scripts/publish_adapter.sh. Usable standalone for testing:

    python3 scripts/inject_eval_metrics.py --log /workspace/train.log \\
        --card /workspace/dave_adapter/README.md
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

METRIC_LINE_RE = re.compile(r"^\s*(\{.*\})\s*$")


def parse_metric_line(line: str) -> dict | None:
    m = METRIC_LINE_RE.match(line)
    if not m:
        return None
    try:
        obj = ast.literal_eval(m.group(1))
        if isinstance(obj, dict):
            return obj
    except (ValueError, SyntaxError):
        pass
    return None


def collect_metrics(log_path: Path) -> tuple[dict[str, str], list[tuple[int, float]]]:
    """Return (final_training_dict, [(step, eval_loss), ...])."""
    last_train: dict[str, str] = {}
    evals: list[tuple[int, float]] = []
    running_step = 0

    with log_path.open(errors="replace") as f:
        for raw in f:
            # The log file contains tqdm \r-overwritten progress bars; split
            # those out and parse each segment.
            for piece in raw.split("\r"):
                d = parse_metric_line(piece)
                if not d:
                    continue
                if "eval_loss" in d:
                    step = int(d.get("step") or running_step)
                    try:
                        evals.append((step, float(d["eval_loss"])))
                    except (TypeError, ValueError):
                        pass
                elif "loss" in d and "grad_norm" in d:
                    last_train = {k: str(v) for k, v in d.items()}
                    running_step += 1
    return last_train, evals


def format_pct(value) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "—"


def format_float(value, digits: int = 3) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "—"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--log", required=True, type=Path)
    p.add_argument("--card", required=True, type=Path)
    args = p.parse_args()

    if not args.log.exists():
        sys.exit(f"log not found: {args.log}")
    if not args.card.exists():
        sys.exit(f"card not found: {args.card}")

    last_train, evals = collect_metrics(args.log)
    if not last_train and not evals:
        sys.exit("no parseable metric lines found in log — leaving card untouched")

    best_step, best_eval = (None, None)
    if evals:
        best_step, best_eval = min(evals, key=lambda se: se[1])

    final_loss = format_float(last_train.get("loss"))
    final_acc = format_pct(last_train.get("mean_token_accuracy"))
    best_eval_str = format_float(best_eval) if best_eval is not None else "—"
    best_step_str = str(best_step) if best_step is not None else "—"

    card_text = args.card.read_text()

    card_text = re.sub(
        r"\*\*Best checkpoint \(lowest eval loss\):\*\* _populated post-training_",
        f"**Best checkpoint (lowest eval loss):** step **{best_step_str}**, "
        f"eval_loss **{best_eval_str}**",
        card_text,
    )

    replacements = {
        "| Final training loss | _populated post-training_ |":
            f"| Final training loss | {final_loss} |",
        "| Best eval loss | _populated post-training_ |":
            f"| Best eval loss | {best_eval_str} |",
        "| Best eval loss step | _populated post-training_ |":
            f"| Best eval loss step | {best_step_str} |",
        "| Final mean token accuracy | _populated post-training_ |":
            f"| Final mean token accuracy | {final_acc} |",
    }
    for old, new in replacements.items():
        card_text = card_text.replace(old, new)

    args.card.write_text(card_text)
    print(f"  injected metrics: final_loss={final_loss}, "
          f"best_eval={best_eval_str} (step {best_step_str}), "
          f"token_acc={final_acc}")


if __name__ == "__main__":
    main()
