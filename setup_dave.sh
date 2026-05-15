#!/bin/bash
# Dave Setup Script - Run ONCE to prepare environment
# YOU execute this on YOUR machine - no data leaves your control

set -euo pipefail

echo "=== Dave Environment Setup ==="
echo "This script prepares your environment to train Dave."
echo "YOU must process your licensed books FIRST using process_books_nda.py"
echo "Before running this script, ensure:"
echo "  1. Your licensed books are in a directory (e.g., /home/akclark/books/)"
echo "  2. You have run: python3 scripts/data_collection/process_books_nda.py /path/to/your/books"
echo "  3. You have processed US-government resources and combined all JSONL into shuffled_training.jsonl"
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
        echo "WARNING: Less than 24GB VRAM detected. Training may be slow or fail."
        echo "Consider reducing batch_size in train_dafe.py or using 8-bit quantization."
    fi
else
    echo "WARNING: No CUDA-capable GPU detected. Training will be extremely slow on CPU."
    echo "Continue? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check required directories
if [ ! -d "/home/akclark/Dave_repo/data/processed" ]; then
    echo "Creating data directories..."
    mkdir -p /home/akclark/Dave_repo/data/processed/books
    mkdir -p /home/akclark/Dave_repo/data/processed/free_sources
fi

# Install dependencies
echo ""
echo "Installing required packages..."
pip install --quiet torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install --quiet transformers peft accelerate datasets bitsandbytes wandb scipy

# Verify installation
echo ""
echo "Verifying installations..."
python3 -c "import torch; print('PyTorch:', torch.__version__)"
python3 -c "import transformers; print('Transformers:', transformers.__version__)"
python3 -c "import peft; print('PEFT:', peft.__version__)"

echo ""
echo "=== Setup Complete ==="
echo "Next steps:"
echo "1. Ensure your shuffled_training.jsonl is in /home/akclark/Dave_repo/data/"
echo "2. Run: python3 train_dave.py"
echo "3. Monitor training - it may take several hours"
echo "4. After training, your adapter will be in /home/akclark/Dave_repo/dave_model/"
echo ""
echo "REMINDER: Dave is ONLY for authorized US security assessment report writing."
echo "Never use it without explicit written permission for specific targets/techniques."
echo ""
