#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Aaron K. Clark
#
# Publish a trained Dave adapter to Hugging Face Hub + a GitHub Release.
#
# Prerequisites:
#   - DAVE_ADAPTER_DIR points at the adapter to publish (must contain
#     adapter_config.json + adapter_model.safetensors, or a
#     checkpoint-* subdir you've chosen).
#   - HF_TOKEN environment variable set to a token with WRITE access (the
#     read-only token used for training won't work). Generate at
#     https://huggingface.co/settings/tokens.
#   - `gh` CLI authenticated for the GitHub Release step (gh auth status).
#
# Usage:
#   ./scripts/publish_adapter.sh                       # both targets
#   ./scripts/publish_adapter.sh --hf-only             # skip GitHub Release
#   ./scripts/publish_adapter.sh --github-only         # skip HF upload
#   HF_REPO=user/model ./scripts/publish_adapter.sh    # override repo name
#   RELEASE_TAG=v0.2.0 ./scripts/publish_adapter.sh    # explicit GH tag
#
# Defaults:
#   HF_REPO=Ronin48LLC/Dave-Llama-3.3-70B-QLoRA
#   GH_REPO=CryptoJones/dave
#   DAVE_ADAPTER_DIR=./dave_adapter (or $DAVE_OUTPUT_DIR if set)
#   RELEASE_TAG=auto (v0.1.0 first run, then v0.1.N+1)

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ADAPTER_DIR="${DAVE_ADAPTER_DIR:-${DAVE_OUTPUT_DIR:-$REPO_DIR/dave_adapter}}"
TRAIN_LOG="${DAVE_TRAIN_LOG:-/workspace/train.log}"
HF_REPO="${HF_REPO:-Ronin48LLC/Dave-Llama-3.3-70B-QLoRA}"
GH_REPO="${GH_REPO:-CryptoJones/dave}"

HF_ONLY=0
GH_ONLY=0
for arg in "$@"; do
    case "$arg" in
        --hf-only)      HF_ONLY=1 ;;
        --github-only)  GH_ONLY=1 ;;
        --help|-h)
            sed -n '2,30p' "$0"
            exit 0 ;;
        *) echo "Unknown flag: $arg" >&2; exit 1 ;;
    esac
done

# ---------- preflight ----------

[[ -d "$ADAPTER_DIR" ]] || { echo "ERROR: adapter dir not found: $ADAPTER_DIR" >&2; exit 1; }
[[ -f "$ADAPTER_DIR/adapter_config.json" ]] || {
    echo "ERROR: $ADAPTER_DIR is missing adapter_config.json" >&2
    echo "       If you want to publish a specific checkpoint, set:" >&2
    echo "         DAVE_ADAPTER_DIR=$ADAPTER_DIR/checkpoint-N ./scripts/publish_adapter.sh" >&2
    exit 1
}

# Auto-pick RELEASE_TAG: bump patch from latest existing tag, or default v0.1.0.
if [[ -z "${RELEASE_TAG:-}" ]]; then
    if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
        LAST_TAG=$(gh release list --repo "$GH_REPO" --limit 1 --json tagName --jq '.[0].tagName' 2>/dev/null || echo "")
        if [[ "$LAST_TAG" =~ ^v([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
            RELEASE_TAG="v${BASH_REMATCH[1]}.${BASH_REMATCH[2]}.$((BASH_REMATCH[3]+1))"
        else
            RELEASE_TAG="v0.1.0"
        fi
    else
        RELEASE_TAG="v0.1.0"
    fi
fi

echo "=== Publish Dave adapter ==="
echo "  Source:         $ADAPTER_DIR"
[[ "$GH_ONLY" -eq 0 ]] && echo "  HF Hub target:  https://huggingface.co/$HF_REPO"
[[ "$HF_ONLY" -eq 0 ]] && echo "  GitHub Release: https://github.com/$GH_REPO/releases/tag/$RELEASE_TAG"
echo ""

# ---------- Hugging Face Hub upload (via Python HfApi — CLI-version-independent) ----------

if [[ "$GH_ONLY" -eq 0 ]]; then
    [[ -n "${HF_TOKEN:-}" ]] || { echo "ERROR: HF_TOKEN is unset. Need a write-permission token." >&2; exit 1; }

    # Make sure huggingface_hub is installed. The library is the canonical
    # entry point; we avoid the CLI here because `huggingface-cli` (0.x)
    # and `hf` (1.x) take subtly different arguments and the upgrade has
    # caused publish-time surprises in the past.
    python3 -c "import huggingface_hub" 2>/dev/null || {
        echo "Installing huggingface_hub..."
        pip install --quiet huggingface_hub --break-system-packages 2>/dev/null \
            || pip install --quiet huggingface_hub
    }

    echo "--- Hugging Face Hub upload ---"

    # Stage the model card and inject training metrics from train.log.
    cp "$REPO_DIR/MODEL_CARD.md" "$ADAPTER_DIR/README.md"
    if [[ -f "$TRAIN_LOG" ]]; then
        echo "  parsing eval metrics from $TRAIN_LOG"
        python3 "$REPO_DIR/scripts/inject_eval_metrics.py" \
            --log "$TRAIN_LOG" \
            --card "$ADAPTER_DIR/README.md" \
        || echo "  (metric injection skipped — see error above; placeholders remain in card)"
    else
        echo "  no training log at $TRAIN_LOG — leaving metric placeholders in the card."
        echo "  Set DAVE_TRAIN_LOG=/path/to/log to wire them up."
    fi

    HF_REPO="$HF_REPO" ADAPTER_DIR="$ADAPTER_DIR" HF_TOKEN="$HF_TOKEN" python3 - <<'PY'
import os
from huggingface_hub import HfApi
api = HfApi(token=os.environ["HF_TOKEN"])
repo = os.environ["HF_REPO"]

# create_repo with exist_ok=True is idempotent.
api.create_repo(repo_id=repo, repo_type="model", private=False, exist_ok=True)

api.upload_folder(
    folder_path=os.environ["ADAPTER_DIR"],
    repo_id=repo,
    repo_type="model",
    commit_message="Publish Dave QLoRA adapter for Llama-3.3-70B",
)
print(f"  ✓ folder uploaded to https://huggingface.co/{repo}")
PY

    echo ""
fi

# ---------- GitHub Release ----------

if [[ "$HF_ONLY" -eq 0 ]]; then
    command -v gh >/dev/null 2>&1 || { echo "ERROR: gh CLI not installed." >&2; exit 1; }
    gh auth status >/dev/null 2>&1 || { echo "ERROR: gh not authenticated. Run: gh auth login" >&2; exit 1; }

    echo "--- GitHub Release ($RELEASE_TAG) ---"
    TARBALL="/tmp/dave-adapter-${RELEASE_TAG}.tar.gz"
    tar -czf "$TARBALL" -C "$(dirname "$ADAPTER_DIR")" "$(basename "$ADAPTER_DIR")"
    echo "  packed $(du -h "$TARBALL" | cut -f1) → $TARBALL"

    RELEASE_NOTES=$(cat <<EOF
Dave QLoRA adapter — $RELEASE_TAG.

Trained on ~11k prompt/completion pairs (Trail of Bits + KEV + NIST + MITRE +
DHS BODs) on a single A100 SXM 80GB.

**Primary distribution:** [Hugging Face Hub — $HF_REPO](https://huggingface.co/$HF_REPO)

This GitHub Release is a mirror archive. Prefer the HF Hub copy for
\`PeftModel.from_pretrained()\` integration.

See [README.md](https://github.com/$GH_REPO/blob/main/README.md),
[TRAINING.md](https://github.com/$GH_REPO/blob/main/TRAINING.md), and
[LIMITATIONS.md](https://github.com/$GH_REPO/blob/main/LIMITATIONS.md) for
full context.
EOF
    )

    gh release create "$RELEASE_TAG" "$TARBALL" \
        --repo "$GH_REPO" \
        --title "Dave $RELEASE_TAG" \
        --notes "$RELEASE_NOTES" 2>/dev/null || {
        echo "  release $RELEASE_TAG exists — uploading asset to it (clobber)"
        gh release upload "$RELEASE_TAG" "$TARBALL" --repo "$GH_REPO" --clobber
    }

    rm -f "$TARBALL"
    echo "  ✓ Released at https://github.com/$GH_REPO/releases/tag/$RELEASE_TAG"
fi

# ---------- closing reminders ----------

cat <<EOF

==========================================================
  Publish complete.
==========================================================

NEXT STEPS — don't skip these:

  1. ROTATE THE HF TOKEN
     The token currently in HF_TOKEN was used during this session and may
     have been pasted into shells / chat / logs. Rotate it now:
        https://huggingface.co/settings/tokens
     Delete the old token; create a new one with write access if you
     expect to publish again.

  2. TEAR DOWN THE POD
     If you ran this from a RunPod pod, destroy it now — you've already
     copied the artifacts to durable storage. Pods bill hourly.
        runpodctl pod list
        runpodctl pod remove <pod-id>

  3. VERIFY THE PUBLISHED MODEL
     Open the HF page and confirm the card rendered:
EOF
[[ "$GH_ONLY" -eq 0 ]] && echo "        https://huggingface.co/$HF_REPO"
[[ "$HF_ONLY" -eq 0 ]] && echo "        https://github.com/$GH_REPO/releases/tag/$RELEASE_TAG"
echo "=========================================================="
