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
#
# Defaults:
#   HF_REPO=CryptoJones/Dave-Llama-3.3-70B-QLoRA
#   GH_REPO=CryptoJones/dave
#   DAVE_ADAPTER_DIR=./dave_adapter (or $DAVE_OUTPUT_DIR if set)

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ADAPTER_DIR="${DAVE_ADAPTER_DIR:-${DAVE_OUTPUT_DIR:-$REPO_DIR/dave_adapter}}"
HF_REPO="${HF_REPO:-Ronin48LLC/Dave-Llama-3.3-70B-QLoRA}"
GH_REPO="${GH_REPO:-CryptoJones/dave}"
RELEASE_TAG="${RELEASE_TAG:-v0.1.0}"

HF_ONLY=0
GH_ONLY=0
for arg in "$@"; do
    case "$arg" in
        --hf-only)      HF_ONLY=1 ;;
        --github-only)  GH_ONLY=1 ;;
        --help|-h)
            sed -n '2,28p' "$0"
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

echo "=== Publish Dave adapter ==="
echo "  Source:         $ADAPTER_DIR"
[[ "$GH_ONLY" -eq 0 ]] && echo "  HF Hub target:  https://huggingface.co/$HF_REPO"
[[ "$HF_ONLY" -eq 0 ]] && echo "  GitHub Release: https://github.com/$GH_REPO/releases/tag/$RELEASE_TAG"
echo ""

# ---------- Hugging Face Hub upload ----------

if [[ "$GH_ONLY" -eq 0 ]]; then
    [[ -n "${HF_TOKEN:-}" ]] || { echo "ERROR: HF_TOKEN is unset. Need a write-permission token." >&2; exit 1; }
    if ! command -v hf >/dev/null 2>&1 && ! command -v huggingface-cli >/dev/null 2>&1; then
        echo "Installing huggingface_hub CLI..."
        pip install --quiet huggingface_hub --break-system-packages 2>/dev/null || pip install --quiet huggingface_hub
    fi
    HF_CLI=$(command -v hf || command -v huggingface-cli)

    echo "--- Hugging Face Hub upload ---"
    # Create the repo if it doesn't exist (idempotent — yields friendly error if it does).
    $HF_CLI repo create "$HF_REPO" --type model --yes 2>&1 | grep -v "already created" || true

    # Stage the model card so the HF page renders correctly.
    cp "$REPO_DIR/MODEL_CARD.md" "$ADAPTER_DIR/README.md"

    $HF_CLI upload "$HF_REPO" "$ADAPTER_DIR" . \
        --repo-type model \
        --commit-message "Initial Dave QLoRA adapter for Llama-3.3-70B"

    echo "✓ Uploaded to https://huggingface.co/$HF_REPO"
    echo ""
fi

# ---------- GitHub Release ----------

if [[ "$HF_ONLY" -eq 0 ]]; then
    command -v gh >/dev/null 2>&1 || { echo "ERROR: gh CLI not installed." >&2; exit 1; }
    gh auth status >/dev/null 2>&1 || { echo "ERROR: gh not authenticated. Run: gh auth login" >&2; exit 1; }

    echo "--- GitHub Release ---"
    # Pack the adapter into a single tarball for the release attachment.
    TARBALL="/tmp/dave-adapter-${RELEASE_TAG}.tar.gz"
    tar -czf "$TARBALL" -C "$(dirname "$ADAPTER_DIR")" "$(basename "$ADAPTER_DIR")"
    echo "  packed $(du -h "$TARBALL" | cut -f1) → $TARBALL"

    RELEASE_NOTES=$(cat <<EOF
Dave QLoRA adapter — initial release.

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
        --title "Dave $RELEASE_TAG — Initial adapter release" \
        --notes "$RELEASE_NOTES" || {
        # If the release already exists, upload the asset to it instead.
        echo "  release $RELEASE_TAG exists — uploading asset to it"
        gh release upload "$RELEASE_TAG" "$TARBALL" --repo "$GH_REPO" --clobber
    }

    rm -f "$TARBALL"
    echo "✓ Released at https://github.com/$GH_REPO/releases/tag/$RELEASE_TAG"
fi

echo ""
echo "Done."
