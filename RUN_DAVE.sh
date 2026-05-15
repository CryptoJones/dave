#!/bin/bash
# Dave one-shot pipeline: build data → train adapter.
#
# Everything runs on YOUR machine (or RunPod pod). No data leaves your control.
#
# Configurable paths (export before running):
#   DAVE_DATA_DIR       (default: ./data)
#   DAVE_OUTPUT_DIR     (default: ./dave_adapter)
#   DAVE_BOOKS_DIR      (only used if DAVE_INCLUDE_BOOKS=1)
#   DAVE_INCLUDE_BOOKS  (0/1, default 0 — opt-in for licensed-book pairs)
#   DAVE_EPOCHS         (default: 2)
#
# This script is idempotent: re-runs reuse cached downloads where possible.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

export DAVE_DATA_DIR="${DAVE_DATA_DIR:-$REPO_DIR/data}"
export DAVE_OUTPUT_DIR="${DAVE_OUTPUT_DIR:-$REPO_DIR/dave_adapter}"
export DAVE_INCLUDE_BOOKS="${DAVE_INCLUDE_BOOKS:-0}"

echo "=============================================="
echo "  Dave — End-to-End Training Pipeline"
echo "=============================================="
echo "  Data dir:     $DAVE_DATA_DIR"
echo "  Output dir:   $DAVE_OUTPUT_DIR"
echo "  Include books: $DAVE_INCLUDE_BOOKS"
echo "=============================================="
echo ""

# Step 1 — Environment
if ! python3 -c "import torch, transformers, peft, trl, bitsandbytes" 2>/dev/null; then
    echo "[1/3] Installing dependencies via setup_dave.sh ..."
    bash "$REPO_DIR/setup_dave.sh"
else
    echo "[1/3] Dependencies already installed."
fi
echo ""

# Step 2 — Build training data
echo "[2/3] Building training dataset ..."
bash "$REPO_DIR/build_training_data.sh"
echo ""

# Sanity-check: training file exists and contains data
TRAIN_FILE="$DAVE_DATA_DIR/shuffled_training.jsonl"
if [ ! -s "$TRAIN_FILE" ]; then
    echo "ERROR: training file is missing or empty: $TRAIN_FILE"
    exit 1
fi
echo "Training file ready: $(wc -l < "$TRAIN_FILE") pairs"
echo ""

# Step 3 — Train
echo "[3/3] Training Dave (QLoRA on Llama-3.3-70B-Instruct) ..."
echo "      This requires a CUDA GPU (A100 80GB recommended)."
python3 "$REPO_DIR/train_dave.py"
echo ""

echo "=============================================="
echo "  Training complete"
echo "=============================================="
ls -la "$DAVE_OUTPUT_DIR"
echo ""
echo "REMINDERS:"
echo "  • Dave outputs are DRAFT material. A qualified human reviewer must"
echo "    verify accuracy and authorization before any client delivery."
echo "  • Dave is for authorized US security assessment report writing only."
echo "  • Adapter contains derived knowledge from licensed/permissive sources."
echo "    Redistribution must respect each source's license (see README.md)."
