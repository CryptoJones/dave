# Dave — Documentation of Adversarial Vulnerability Evidence

<!--
This file is the model card uploaded to Hugging Face Hub alongside the
adapter weights. It is rendered on the model page at
https://huggingface.co/CryptoJones/Dave-Llama-3.3-70B-QLoRA (or whichever
repo you publish to). Sections below follow the HF model-card structure.
-->

---
license: apache-2.0
base_model: meta-llama/Llama-3.3-70B-Instruct
tags:
- security
- penetration-testing
- report-writing
- llama
- qlora
- adapter
- peft
library_name: peft
pipeline_tag: text-generation
language:
- en
---

# Dave — Security Assessment Report Writing Assistant

**Dave** is a LoRA adapter for `meta-llama/Llama-3.3-70B-Instruct`,
fine-tuned to write **professional security assessment report content** —
finding narratives, executive summaries, remediation recommendations,
methodology sections, risk narratives, and MITRE ATT&CK mappings — in
APA/(ISC)²-aligned format suitable for authorized US security assessments.

Dave is **not** a hacking tool. Dave writes *about* hacking — professionally,
precisely, and in a way that clients can act on. The exploitation is yours.
The report is Dave's.

Named in honor of [David Kennedy](https://www.trustedsec.com/), founder of
TrustedSec — who has spoken openly about the mental health toll of security
work, and the role thoughtful reporting plays in protecting both clients and
practitioners.

---

## Model Details

- **Base Model:** [`meta-llama/Llama-3.3-70B-Instruct`](https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct)
- **Adapter type:** QLoRA (4-bit NF4 quantization + LoRA, rank 16, alpha 32)
- **Target modules:** `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`
- **Training method:** Supervised fine-tuning via [TRL](https://github.com/huggingface/trl) `SFTTrainer`
- **Context window:** 128K (inherited from base; training used 1024-token packed sequences)
- **License (adapter):** Apache 2.0
- **License (base weights):** Meta Llama 3.3 Community License
- **Trained by:** [CryptoJones](https://codeberg.org/CryptoJones) (Aaron K. Clark)

---

## Training Data

Approximately 11,000 prompt/completion pairs from public sources, weighted
toward real audit-style report content:

| Source | Pairs | Share | License |
|---|---:|---:|---|
| Trail of Bits public security reviews (web3-filtered) | 6,980 | 63% | CC BY-SA 4.0 |
| CISA Known Exploited Vulnerabilities (KEV) catalog | 3,182 | 29% | Public Domain |
| MITRE ATT&CK® (defensive context only) | 709 | 6% | CC BY 4.0 |
| NIST SP 800-30 / 800-53 / NISTIR 8286 | 187 | 2% | Public Domain |
| DHS / CISA Binding Operational Directives | 16 | <1% | Public Domain |

Smart-contract-specific findings from Trail of Bits' corpus were filtered
out so Dave stays general-purpose rather than blockchain-focused.

Training data composition and source attribution are detailed in the project
repo: https://codeberg.org/CryptoJones/Dave/src/branch/master/data/processed/free_sources/NOTICE.md

---

## Intended Use

**Permitted:**

- Drafting professional report content for **authorized** US security assessments
- Writing finding narratives, executive summaries, remediation guidance
- Mapping findings to MITRE ATT&CK techniques (defensive context)
- Composing risk narratives using NIST SP 800-30 framing

**Not intended for:**

- Unauthorized security testing of any system
- Producing offensive how-to content, exploit code, or malware
- Targets outside US jurisdiction
- Use as a substitute for a qualified human reviewer

All outputs must be reviewed by a qualified security professional before
delivery to a client.

See the [USAGE_POLICY](https://codeberg.org/CryptoJones/Dave/src/branch/master/USAGE_POLICY.md)
for the full acceptable-use terms.

---

## Limitations

See [LIMITATIONS.md](https://codeberg.org/CryptoJones/Dave/src/branch/master/LIMITATIONS.md)
in the project repo for the full discussion. Key points:

- **Small dataset** (~11k pairs) — Dave learned style and structure, not
  new world knowledge. Verify every technical specific.
- **Source composition bias** — strongest at audit-style and CVE-style
  writeups; weakest at red-team narrative, social-engineering, OT/ICS,
  physical-pentest reporting.
- **No real client reports in training** — third-party report corpora were
  excluded on licensing grounds. Expect audit-firm voice or advisory voice
  rather than firm-house style. Adapt during review.
- **Hallucination risk** — every CVSS vector, identifier, citation, and
  command-line in Dave's output must be human-verified.
- **Authorization gate is a prompt convention, not a hard guarantee.**

---

## How to Use

### Loading the adapter (transformers + peft)

```python
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

bnb = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
)

base = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.3-70B-Instruct",
    quantization_config=bnb,
    device_map="auto",
    torch_dtype=torch.bfloat16,
)

model = PeftModel.from_pretrained(base, "CryptoJones/Dave-Llama-3.3-70B-QLoRA")
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.3-70B-Instruct")
```

### Inference

Dave was trained with this system prompt, baked into every sample:

> *"You are Dave — a writing assistant for authorized US security
> assessments. You write professional, APA/(ISC)²-aligned finding
> narratives, executive summaries, remediation guidance, methodology
> sections, risk narratives, and evidence documentation. You never produce
> offensive how-to content. You require written authorization for any
> specific target before writing target-specific content. Outputs are draft
> material for a qualified security professional to review."*

Use the same system prompt at inference for best behavior.

```python
messages = [
    {"role": "system", "content": "<system prompt above>"},
    {"role": "user", "content": "Write a professional vulnerability finding "
                                  "titled \"Stored XSS in admin search\" with "
                                  "Severity Medium."},
]
inputs = tokenizer.apply_chat_template(messages, return_tensors="pt", add_generation_prompt=True).to(model.device)
out = model.generate(inputs, max_new_tokens=512, do_sample=True, temperature=0.7)
print(tokenizer.decode(out[0][inputs.shape[1]:], skip_special_tokens=True))
```

---

## Training Procedure

- Hardware: single NVIDIA A100 SXM4 80GB on [RunPod](https://www.runpod.io/)
- Wall-clock: ~3-4 hours
- Image: `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404`
- Frameworks: `transformers`, `peft`, `trl`, `bitsandbytes`, `accelerate`

Hyperparameters (full table in
[TRAINING.md](https://codeberg.org/CryptoJones/Dave/src/branch/master/TRAINING.md)):

| Parameter | Value |
|---|---|
| Epochs | 1 |
| Effective batch size | 16 (per-device 1 × grad accum 16) |
| Learning rate | 2e-4 cosine, 3% warmup |
| Max sequence length | 1024 (packing enabled) |
| LoRA r / alpha / dropout | 16 / 32 / 0.05 |
| Optimizer | paged AdamW 8-bit |
| Precision | bf16 compute, NF4 weight quant |

---

## Citation

```bibtex
@misc{dave-llama-3.3-70b-qlora,
  author = {Clark, Aaron K. (CryptoJones)},
  title  = {Dave — A QLoRA Adapter for Security Assessment Report Writing},
  year   = {2026},
  url    = {https://codeberg.org/CryptoJones/Dave},
}
```

---

## License Compatibility

This adapter is released under **Apache 2.0**. The base model weights are
governed by the **Llama 3.3 Community License** — by downloading the base
model you agree to those terms (free for most uses; review the license for
specifics).

Training data derived from Trail of Bits' CC BY-SA 4.0 corpus carries an
attribution string in every training sample. Downstream redistribution of
outputs that substantively reproduce training content should respect the
upstream license.

---

## Acknowledgments

- [David Kennedy](https://www.linkedin.com/in/davidkennedy4/) — for the blog
  post, the work, and the name.
- [Trail of Bits](https://www.trail-of-bits.com/) — for publishing their
  security review corpus under CC BY-SA 4.0.
- Meta AI — for releasing Llama-3.3-70B-Instruct as an open-weight model.

Proudly Made in Nebraska. Go Big Red! 🌽 https://xkcd.com/1654/
