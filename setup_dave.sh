#!/bin/bash
# Dave Setup Script - Run ONCE to prepare environment
# YOU execute this on YOUR machine - no data leaves your control

set -euo pipefail

# --- Configurable paths ---
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DAVE_DATA_DIR="${DAVE_DATA_DIR:-$REPO_DIR/data}"
DAVE_OUTPUT_DIR="${DAVE_OUTPUT_DIR:-$REPO_DIR/dave_adapter}"

echo "=== Dave Environment Setup ==="
echo "Data directory:   $DAVE_DATA_DIR"
echo "Adapter output:   $DAVE_OUTPUT_DIR"
echo ""
echo "Override with environment variables before running:"
echo "  export DAVE_DATA_DIR=/path/to/data"
echo "  export DAVE_OUTPUT_DIR=/path/to/adapters/dave"
echo ""

# Check if running as root (typical inside RunPod containers — skip the prompt
# in non-interactive shells; surface a warning otherwise).
if [ "$EUID" -eq 0 ] && [ -t 0 ]; then
    echo "WARNING: Running as root is not recommended on shared workstations."
    echo "Continue? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check Python version
python_version=$(python3 --version | awk '{print $2}')
echo "Python version: $python_version"

# Check CUDA availability (informational; we don't block install).
if python3 -c "import torch; print(torch.cuda.is_available())" 2>/dev/null | grep -q True; then
    gpu_name=$(python3 -c "import torch; print(torch.cuda.get_device_name(0))" 2>/dev/null)
    vram_gb=$(python3 -c "import torch; print(int(torch.cuda.get_device_properties(0).total_memory / 1024**3))" 2>/dev/null)
    echo "GPU detected: $gpu_name (${vram_gb}GB)"
    if [ "${vram_gb:-0}" -lt 40 ]; then
        echo "NOTE: Less than 40GB VRAM detected — train_dave.py targets a 70B base"
        echo "      and will not fit comfortably below 40GB. Consider RunPod A100 80GB."
    fi
else
    echo "NOTE: No CUDA-capable GPU detected. Training requires a GPU; this is fine"
    echo "      if you're only installing for tests or dev work."
fi

# Create required directories
echo ""
echo "Creating directories..."
mkdir -p "${DAVE_DATA_DIR}/processed/books"
mkdir -p "${DAVE_DATA_DIR}/processed/free_sources"
mkdir -p "${DAVE_OUTPUT_DIR}"

# Pick the right pip flag set:
#   - Add --break-system-packages on Ubuntu 24.04+ (PEP 668) when running outside a venv.
#   - Skip torch install if torch is already importable (RunPod images ship it).
PIP_FLAGS=("--quiet")
if pip install --help 2>/dev/null | grep -q -- '--break-system-packages'; then
    if [ -z "${VIRTUAL_ENV:-}" ]; then
        PIP_FLAGS+=("--break-system-packages")
    fi
fi

echo ""
echo "Installing required packages..."
if ! python3 -c "import torch" 2>/dev/null; then
    echo "  torch not present — installing CPU/CUDA build from default PyPI..."
    pip install "${PIP_FLAGS[@]}" torch torchvision torchaudio
else
    echo "  torch already installed — skipping (let the image's CUDA build win)."
fi

pip install "${PIP_FLAGS[@]}" \
    "transformers>=4.45" "peft>=0.13" "accelerate>=1.0" \
    "datasets>=3.0" "bitsandbytes>=0.44" "trl>=0.12" \
    hf_transfer wandb scipy pytest

# Verify installation
echo ""
echo "Verifying installations..."
python3 -c "import torch; print('PyTorch:', torch.__version__, '(CUDA available:', torch.cuda.is_available(), ')')"
python3 -c "import transformers; print('Transformers:', transformers.__version__)"
python3 -c "import peft; print('PEFT:', peft.__version__)"
python3 -c "import trl; print('TRL:', trl.__version__)"
python3 -c "import bitsandbytes; print('bitsandbytes:', bitsandbytes.__version__)"

echo ""
echo "=== Setup Complete ==="
echo "Next steps:"
echo "  ./build_training_data.sh   # short-circuits if data is already committed"
echo "  python3 train_dave.py      # full training run"
echo ""
echo "Or run the wrapper:"
echo "  ./RUN_DAVE.sh"
echo ""
echo "REMINDER: Dave is ONLY for authorized US security assessment report writing."
