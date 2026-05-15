# Dave — Inference Examples

Minimal, self-contained snippets for loading and running the Dave QLoRA
adapter on top of Llama-3.3-70B-Instruct.

## `infer.py`

Single-finding generator. Loads the adapter from Hugging Face Hub (or a
local path), prompts Dave for one finding writeup, and prints it to stdout.

```bash
# Default: pulls the published adapter, generates a Stored XSS finding
python3 examples/infer.py

# Local adapter path + custom finding
python3 examples/infer.py \
    --adapter ./dave_adapter \
    --title "Authentication bypass in admin login" \
    --severity High \
    --difficulty Medium \
    --type "Access Controls"

# All options
python3 examples/infer.py --help
```

Requirements: a CUDA GPU with at least **42 GB VRAM** (A100 80GB, H100 80GB,
RTX PRO 6000 96GB, A6000 with offload), plus `transformers`, `peft`,
`bitsandbytes`, and `accelerate` installed.

Output goes to stdout; a closing reminder reinforces that Dave's writeup is
**draft material for a human reviewer to verify**.
