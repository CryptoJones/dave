#!/bin/bash
# Dave Setup Script - Run ONCE to prepare environment
# YOU execute this on YOUR machine - no data leaves your control

set -euo pipefail

# --- Configurable paths ---
DAVE_DATA_DIR="${DAVE_DATA_DIR:-$(pwd)/data}"
DAVE_OUTPUT_DIR="${DAVE_OUTPUT_DIR:-/home/akclark/Source/adapters/dave}"

echo "=== Dave Environment Setup ==="
echo "Data directory:   $DAVE_DATA_DIR"
echo "Adapter output:   $DAVE_OUTPUT_DIR"
echo ""
echo "Override with environment variables before running:"
echo "  export DAVE_DATA_DIR=/path/to/data"
echo "  export DAVE_OUTPUT_DIR=/path/to/adapters/dave"
echo ""

# Check if running as root (not recommended)
if [ "$EUID" -eq 0 ]; then
    echo "WARNING: Running as root is not recommended for ML work."
    echo "Continue? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check Python version
python_version=$(python3 --version | awk '{print $2}')
echo "Python version: $python_version"

# Check CUDA availability
if python3 -c "import torch; print(torch.cuda.is_available())" 2>/dev/null | grep -q True; then
    gpu_count=$(python3 -c "import torch; print(torch.cuda.device_count())")
    gpu_name=$(python3 -c "import torch; print(torch.cuda.get_device_name(0))")
    vram_gb=$(python3 -c "import torch; print(torch.cuda.get_device_properties(0).total_memory / 1024**3)" | cut -d'.' -f1)
    echo "GPU: $gpu_name ($gpu_count x)"
    echo "VRAM: ${vram_gb}GB"
    if [ "$vram_gb" -lt 24 ]; then
        echo "WARNING: Less than 24GB VRAM detected. Dave requires 40GB+ for 70B training."
        echo "Consider using RunPod (A100 80GB) for training."
        echo "Continue? (y/N)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    echo "WARNING: No CUDA-capable GPU detected. Training will be extremely slow on CPU."
    echo "Continue? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create required directories
echo ""
echo "Creating directories..."
mkdir -p "${DAVE_DATA_DIR}/processed/books"
mkdir -p "${DAVE_DATA_DIR}/processed/free_sources"
mkdir -p "${DAVE_OUTPUT_DIR}"

# Install dependencies
echo ""
echo "Installing required packages..."
pip install --quiet torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install --quiet "transformers>=4.45" "peft>=0.13" "accelerate>=1.0" "datasets>=3.0" "bitsandbytes>=0.44" "trl>=0.12" wandb scipy

# Verify installation
echo ""
echo "Verifying installations..."
python3 -c "import torch; print('PyTorch:', torch.__version__)"
python3 -c "import transformers; print('Transformers:', transformers.__version__)"
python3 -c "import peft; print('PEFT:', peft.__version__)"

echo ""
echo "=== Setup Complete ==="
echo "Next steps:"
echo "1. Process your licensed books:"
echo "   python3 scripts/data_collection/process_books_nda_fixed.py /path/to/your/books"
echo "2. Run training:"
echo "   DAVE_DATA_DIR=${DAVE_DATA_DIR} DAVE_OUTPUT_DIR=${DAVE_OUTPUT_DIR} python3 train_dave.py"
echo "3. Adapter will be saved to: ${DAVE_OUTPUT_DIR}"
echo ""
echo "REMINDER: Dave is ONLY for authorized US security assessment report writing."
