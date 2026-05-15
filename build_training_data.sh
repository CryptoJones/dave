#!/bin/bash
# Build all Dave training data from scratch
# Run this once before training.
#
# Usage:
#   ./build_training_data.sh
#
# Overrides:
#   DAVE_BOOKS_DIR=/path/to/books ./build_training_data.sh
#   DAVE_DATA_DIR=/path/to/data   ./build_training_data.sh

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS="$REPO_DIR/scripts/data_collection"

export DAVE_DATA_DIR="${DAVE_DATA_DIR:-$REPO_DIR/data}"
export DAVE_BOOKS_DIR="${DAVE_BOOKS_DIR:-$REPO_DIR/books}"
export DAVE_OUTPUT_DIR="${DAVE_OUTPUT_DIR:-$REPO_DIR/dave_adapter}"

# Books are OFF by default. Set DAVE_INCLUDE_BOOKS=1 to include them.
# Rationale: the heuristic-extracted book pairs contain TOC/index noise and
# textbook prose rather than report-style content. Free sources (KEV/NIST/
# MITRE/DHS) are higher signal-to-noise. See README for the data-quality story.
DAVE_INCLUDE_BOOKS="${DAVE_INCLUDE_BOOKS:-0}"

BOOKS_OUT="$DAVE_DATA_DIR/processed/books/books_training.jsonl"
FREE_DIR="$DAVE_DATA_DIR/processed/free_sources"
COMBINED="$DAVE_DATA_DIR/combined_training.jsonl"
SHUFFLED="$DAVE_DATA_DIR/shuffled_training.jsonl"

echo "========================================"
echo "  Dave — Training Data Build"
echo "========================================"
echo "  Books dir:   $DAVE_BOOKS_DIR"
echo "  Data dir:    $DAVE_DATA_DIR"
echo "  Adapter out: $DAVE_OUTPUT_DIR"
echo "========================================"
echo ""

# Short-circuit: training data is committed to the repo so a fresh clone can
# train immediately. Skip the (slow, network-heavy) rebuild unless the user
# explicitly forces it or the file is missing/empty.
if [ -s "$SHUFFLED" ] && [ "${DAVE_FORCE_REBUILD:-0}" != "1" ]; then
    echo "Training file already present and non-empty:"
    echo "  $SHUFFLED ($(wc -l < "$SHUFFLED") pairs)"
    echo ""
    echo "Skipping data build. To force a full rebuild, run:"
    echo "  DAVE_FORCE_REBUILD=1 ./build_training_data.sh"
    exit 0
fi

mkdir -p "$DAVE_DATA_DIR/processed/books"
mkdir -p "$FREE_DIR"
mkdir -p "$DAVE_OUTPUT_DIR"

# Step 1: Licensed books (opt-in via DAVE_INCLUDE_BOOKS=1)
if [ "$DAVE_INCLUDE_BOOKS" = "1" ]; then
    if [ -f "$BOOKS_OUT" ]; then
        echo "[1/6] Books already processed — skipping. Delete $BOOKS_OUT to reprocess."
    else
        if [ ! -d "$DAVE_BOOKS_DIR" ]; then
            echo "ERROR: DAVE_BOOKS_DIR not found: $DAVE_BOOKS_DIR"
            echo "Set it before running: export DAVE_BOOKS_DIR=/path/to/your/books"
            exit 1
        fi
        echo "[1/6] Processing licensed books..."
        python3 "$SCRIPTS/process_books_nda_fixed.py" "$DAVE_BOOKS_DIR"
    fi
else
    echo "[1/6] Books skipped (set DAVE_INCLUDE_BOOKS=1 to include them)."
fi
echo ""

# Step 2: CISA KEV
echo "[2/6] Downloading and processing CISA KEV catalog..."
python3 "$SCRIPTS/process_cisa_kev.py"
echo ""

# Step 3: NIST publications
echo "[3/6] Downloading and processing NIST publications..."
python3 "$SCRIPTS/process_nist.py"
echo ""

# Step 4: DHS/CISA BODs and US-CERT alerts
echo "[4/6] Processing DHS/CISA directives and US-CERT alerts..."
python3 "$SCRIPTS/process_dhs_cisa.py"
echo ""

# Step 5: MITRE ATT&CK (defensive only)
echo "[5/6] Downloading and processing MITRE ATT&CK (defensive context only)..."
python3 "$SCRIPTS/process_mitre_attack.py"
echo ""

# Step 6: Trail of Bits public security reviews (CC-BY-SA 4.0)
TOB_DIR="$DAVE_DATA_DIR/raw_github/publications"
TOB_OUT="$FREE_DIR/trail_of_bits_training.jsonl"
echo "[6/6] Trail of Bits public security reviews..."
if [ ! -d "$TOB_DIR" ]; then
    echo "  Cloning trailofbits/publications (reviews/ only)..."
    mkdir -p "$DAVE_DATA_DIR/raw_github"
    git -C "$DAVE_DATA_DIR/raw_github" clone \
        --depth 1 --filter=blob:none --sparse \
        https://github.com/trailofbits/publications.git
    git -C "$TOB_DIR" sparse-checkout set reviews
fi
python3 "$SCRIPTS/process_trail_of_bits.py"
echo ""

# Combine and shuffle
echo "========================================"
echo "  Combining and shuffling..."
echo "========================================"
if [ "$DAVE_INCLUDE_BOOKS" = "1" ] && [ -f "$BOOKS_OUT" ]; then
    cat "$BOOKS_OUT" "$FREE_DIR"/*_training.jsonl > "$COMBINED"
else
    cat "$FREE_DIR"/*_training.jsonl > "$COMBINED"
fi
shuf "$COMBINED" > "$SHUFFLED"
rm "$COMBINED"

echo ""
echo "========================================"
echo "  Build Complete"
echo "========================================"
if [ "$DAVE_INCLUDE_BOOKS" = "1" ] && [ -f "$BOOKS_OUT" ]; then
    echo "  Books pairs:    $(wc -l < "$BOOKS_OUT")"
else
    echo "  Books pairs:    0 (skipped)"
fi
echo "  Free src pairs: $(cat "$FREE_DIR"/*_training.jsonl | wc -l)"
echo "  Total shuffled: $(wc -l < "$SHUFFLED")"
echo "  Output file:    $SHUFFLED"
echo "========================================"
echo ""
echo "Next step: python3 train_dave.py"
