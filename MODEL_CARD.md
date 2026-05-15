---
license: apache-2.0
base_model: meta-llama/Llama-3.3-70B-Instruct
base_model_relation: adapter
library_name: peft
pipeline_tag: text-generation
language:
- en
tags:
- security
- penetration-testing
- security-assessment
- report-writing
- vulnerability
- mitre-attack
- nist
- llama
- llama-3
- llama-3.3
- qlora
- lora
- adapter
- peft
inference: false
---

# Dave — Security Assessment Report Writing Assistant

> *"Hacking is not just a technical skill — it's a mindset. And the report is
> where that mindset becomes something that actually changes an organization."*
> — David Kennedy, TrustedSec

**Dave** is a QLoRA adapter for `meta-llama/Llama-3.3-70B-Instruct`,
fine-tuned to draft **professional security assessment report content** —
finding narratives, executive summaries, remediation recommendations,
methodology sections, risk narratives, and MITRE ATT&CK mappings — in
APA / (ISC)²-aligned format suitable for **authorized US security assessments**.

Dave is **not** a hacking tool. Dave writes *about* hacking — professionally,
precisely, and in a way that clients can act on. The exploitation is yours.
The report is Dave's.

---

## TL;DR

```python
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

base = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.3-70B-Instruct",
    quantization_config=BitsAndBytesConfig(
        load_in_4bit=True, bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16),
    device_map="auto", torch_dtype=torch.bfloat16,
)
model = PeftModel.from_pretrained(base, "Ronin48LLC/Dave-Llama-3.3-70B-QLoRA")
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.3-70B-Instruct")
```

See [Inference](#inference) below for the system prompt and generation snippet.

| | |
|---|---|
| **Adapter size** | ~250 MB (LoRA r=16 over all attention + MLP projections) |
| **Min VRAM (4-bit + adapter)** | ~42 GB |
| **Min VRAM (bf16 base + adapter)** | ~140 GB |
| **Trained on** | 11,074 prompt/completion pairs from Trail of Bits, CISA KEV, MITRE ATT&CK, NIST, DHS BODs |
| **License** | Apache 2.0 (adapter) + Llama 3.3 Community License (base) |
| **Source repos** | [github.com/CryptoJones/dave](https://github.com/CryptoJones/dave) · [codeberg.org/CryptoJones/Dave](https://codeberg.org/CryptoJones/Dave) |

---

## Source Code

Dave's training pipeline, data processors, and test suite are fully open
source. The repository is hosted in two places — pick the platform you
prefer; they stay in sync on every push.

- **GitHub:** https://github.com/CryptoJones/dave
- **Codeberg:** https://codeberg.org/CryptoJones/Dave

Both mirrors carry identical contents: training script, data pipeline,
pytest suite, model card, training operator's guide, and the publish
workflow that produces this Hugging Face release.

---

## Files in this Repository

| File | Purpose |
|---|---|
| `adapter_config.json` | PEFT config (target modules, rank, alpha, base model reference). |
| `adapter_model.safetensors` | LoRA adapter weights. |
| `tokenizer_config.json`, `tokenizer.json`, `special_tokens_map.json` | Tokenizer files mirrored from the Llama 3.3 base, included for convenience. |
| `README.md` | This model card. |

Optional `checkpoint-*/` subdirectories may exist when multiple checkpoints
were uploaded; each is a self-contained adapter. The top-level adapter is
the recommended one (best eval loss).

---

## Model Details

- **Adapter type:** QLoRA (4-bit NF4 quantization on the base + LoRA, rank 16, alpha 32)
- **Target modules:** `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`
- **Base model:** [`meta-llama/Llama-3.3-70B-Instruct`](https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct) — 70B parameters, 128K context, Llama 3.3 Community License
- **Training method:** Supervised fine-tuning via [TRL](https://github.com/huggingface/trl) `SFTTrainer` with sample packing
- **Training context length:** 1024 tokens (packed from prompt/completion pairs)
- **Inference context:** 128K (inherited from base — no architectural changes)
- **Maintainer:** Aaron K. Clark — [GitHub](https://github.com/CryptoJones) · [Codeberg](https://codeberg.org/CryptoJones) · Ronin 48, LLC

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

**Smart-contract / web3 findings were filtered out** from the Trail of Bits
corpus so Dave stays general-purpose rather than blockchain-focused. The
filter pattern is documented in `scripts/data_collection/process_trail_of_bits.py`
([Codeberg](https://codeberg.org/CryptoJones/Dave/src/branch/master/scripts/data_collection/process_trail_of_bits.py) · [GitHub](https://github.com/CryptoJones/dave/blob/master/scripts/data_collection/process_trail_of_bits.py)).

Full data attribution and source documentation lives in
`data/processed/free_sources/NOTICE.md`
([Codeberg](https://codeberg.org/CryptoJones/Dave/src/branch/master/data/processed/free_sources/NOTICE.md) · [GitHub](https://github.com/CryptoJones/dave/blob/master/data/processed/free_sources/NOTICE.md)).

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
delivery to a client. See `USAGE_POLICY.md`
([Codeberg](https://codeberg.org/CryptoJones/Dave/src/branch/master/USAGE_POLICY.md) · [GitHub](https://github.com/CryptoJones/dave/blob/master/USAGE_POLICY.md))
for the full acceptable-use terms.

---

## How to Use

### System Prompt

Dave was trained with the following system prompt baked into every sample.
**Use the same one at inference time for best behavior:**

```text
You are Dave — a writing assistant for authorized US security assessments.
You write professional, APA/(ISC)²-aligned finding narratives, executive
summaries, remediation guidance, methodology sections, risk narratives, and
evidence documentation. You never produce offensive how-to content. You
require written authorization for any specific target before writing
target-specific content. Outputs are draft material for a qualified security
professional to review.
```

### Inference

```python
DAVE_SYSTEM = (
    "You are Dave — a writing assistant for authorized US security assessments. "
    "You write professional, APA/(ISC)²-aligned finding narratives, executive "
    "summaries, remediation guidance, methodology sections, risk narratives, and "
    "evidence documentation. You never produce offensive how-to content. You "
    "require written authorization for any specific target before writing "
    "target-specific content. Outputs are draft material for a qualified "
    "security professional to review."
)

messages = [
    {"role": "system", "content": DAVE_SYSTEM},
    {"role": "user", "content":
        "Write a professional vulnerability finding titled "
        "\"Stored XSS in admin search\" with Severity Medium, "
        "Difficulty Low, Type Data Validation."},
]
inputs = tokenizer.apply_chat_template(
    messages, return_tensors="pt", add_generation_prompt=True
).to(model.device)

out = model.generate(
    inputs,
    max_new_tokens=512,
    do_sample=True,
    temperature=0.6,
    top_p=0.9,
    repetition_penalty=1.05,
)
print(tokenizer.decode(out[0][inputs.shape[1]:], skip_special_tokens=True))
```

### Recommended generation parameters

| Parameter | Value | Why |
|---|---:|---|
| `temperature` | 0.6 | Balanced — coherent but not robotic for report prose. |
| `top_p` | 0.9 | Nucleus sampling; prevents long-tail vocabulary drift. |
| `max_new_tokens` | 512–1024 | Most finding writeups land in 200–600 tokens. |
| `repetition_penalty` | 1.05 | Reduces stock-phrase echoing without distorting style. |

---

## Sample Outputs

> *The following are **illustrative of the target format** Dave was trained
> to produce. Use them to calibrate prompting and post-processing. Specific
> phrasing from a trained Dave will vary.*

### Example: Finding narrative

**Prompt:** *Write a professional vulnerability finding titled "Stored XSS in
admin search" with Severity Medium, Difficulty Low, Type Data Validation.*

**Expected shape of completion:**

```
Finding: Stored XSS in admin search
Severity: Medium
Difficulty: Low
Type: Data Validation

Description:
The administrative search interface stores user-supplied input without
output encoding. An authenticated attacker with the ability to create
records in the searched dataset can inject HTML or JavaScript that
executes in another administrator's browser session when the malicious
record appears in search results...

Recommendations:
Short term, apply context-appropriate output encoding to all
administrator-rendered fields (HTML body, attributes, JavaScript).
Long term, deploy a Content Security Policy that blocks inline scripts,
and migrate administrator interfaces to a framework with automatic
context-aware escaping (React, Vue, or equivalent).
```

### Example: Remediation guidance

**Prompt:** *Write the remediation recommendations for the finding: "Missing
TLS certificate validation in updater client".*

**Expected shape of completion:**

```
Short term, enable TLS certificate verification in the updater HTTP
client and pin the trust anchor to the vendor-issued root CA used by
the update infrastructure. Reject any update payload served over a
connection that fails certificate validation.

Long term, sign update payloads with an offline-protected signing key
and verify the signature in the updater regardless of the transport
layer's integrity. This provides defense-in-depth against TLS-level
compromise and aligns with NIST SP 800-218 SP-1 (Secure Distribution).
```

---

## Evaluation

The training run holds out 1% of the dataset as an eval split and reports
`eval_loss` every 100 steps. Numbers from the publication run will be
inserted here by `scripts/publish_adapter.sh` when it uploads.

**Best checkpoint (lowest eval loss):** _populated post-training_

| Metric | Value |
|---|---:|
| Final training loss | _populated post-training_ |
| Best eval loss | _populated post-training_ |
| Best eval loss step | _populated post-training_ |
| Final mean token accuracy | _populated post-training_ |

No external benchmark scores are claimed — Dave is a style/structure adapter
on a narrow domain, not a general-capability uplift. Treat any apparent
gains on reasoning benchmarks as accidents of style transfer, not as
intended capability gains.

---

## Training Procedure

| | |
|---|---|
| **Hardware** | Single NVIDIA A100 SXM4 80GB ([RunPod](https://www.runpod.io/)) |
| **Image** | `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404` |
| **Wall-clock** | ~3-4 hours |
| **Frameworks** | `transformers`, `peft`, `trl`, `bitsandbytes`, `accelerate` |

### Hyperparameters

| Parameter | Value |
|---|---|
| `num_train_epochs` | 1 |
| Effective batch size | 16 (`per_device_train_batch_size=1` × `gradient_accumulation_steps=16`) |
| `learning_rate` | 2e-4, cosine schedule, 3% warmup |
| `max_length` | 1024 (with `packing=True`) |
| LoRA `r` / `alpha` / `dropout` | 16 / 32 / 0.05 |
| Optimizer | `paged_adamw_8bit` |
| Precision | bf16 compute, NF4 (double-quant) weight quantization |
| Loss masking | Default (full sequence — packed) |

Full operator guide (live metric interpretation, when to stop, picking the
best checkpoint, failure-mode recovery) in `TRAINING.md`
([Codeberg](https://codeberg.org/CryptoJones/Dave/src/branch/master/TRAINING.md) · [GitHub](https://github.com/CryptoJones/dave/blob/master/TRAINING.md)).

---

## System Requirements

To **load and run** Dave you need either:

- **GPU**, 4-bit NF4 base: ≥ **42 GB VRAM**
  *(A100 80GB, H100 80GB, RTX PRO 6000 96GB, A6000 + offload, etc.)*
- **GPU**, bf16 base: ≥ **140 GB VRAM** (multi-GPU only — e.g. 2× A100 80GB)
- **CPU + RAM** (not recommended): ≥ 150 GB RAM, expect seconds-per-token throughput

To **fine-tune further** on top of Dave you need at least the same as
training: A100 80GB (or equivalent) and the QLoRA stack.

---

## Limitations

The full discussion lives in `LIMITATIONS.md`
([Codeberg](https://codeberg.org/CryptoJones/Dave/src/branch/master/LIMITATIONS.md) · [GitHub](https://github.com/CryptoJones/dave/blob/master/LIMITATIONS.md)).
Highlights:

- **Small dataset** (~11k pairs) — Dave learned style and structure, not new
  world knowledge. Verify every technical specific.
- **Source composition bias** — strongest at audit-style and CVE-style
  writeups; weakest at red-team narrative, social-engineering, OT/ICS, or
  physical-pentest reporting.
- **No real client reports in training** — third-party report corpora were
  excluded on licensing grounds. Expect audit-firm or advisory voice rather
  than your firm's house style. Adapt during review.
- **Hallucination risk** — every CVSS vector, identifier, citation, and
  command-line in Dave's output must be human-verified.
- **The authorization-gate is a prompt convention, not a hard guarantee.**
  Sufficiently adversarial prompting can route around it.

---

## License & Attribution

| Layer | License | Notes |
|---|---|---|
| **This adapter (weights + config)** | **Apache 2.0** | Free to use, modify, redistribute. |
| **Llama 3.3 base weights** | **Llama 3.3 Community License** | You agree to the license when downloading the base from Meta / HF. |
| **Trail of Bits training content** | **CC BY-SA 4.0** | Attribution embedded in every relevant training sample; SA obligation propagates to substantive verbatim reproduction in outputs. |
| **CISA KEV / NIST / DHS sources** | **U.S. Government Public Domain** | No restrictions. |
| **MITRE ATT&CK®** | **CC BY 4.0** | Attribution in every relevant output. |

---

## Citation

```bibtex
@misc{clark2026dave,
  author       = {Clark, Aaron K.},
  title        = {Dave: A QLoRA Adapter for Security Assessment Report Writing},
  year         = {2026},
  howpublished = {Hugging Face},
  url          = {https://huggingface.co/Ronin48LLC/Dave-Llama-3.3-70B-QLoRA},
  note         = {Adapter for meta-llama/Llama-3.3-70B-Instruct, Apache 2.0}
}
```

---

## Acknowledgments

- **[David Kennedy](https://www.trustedsec.com/)** — founder of TrustedSec
  and longtime advocate for mental-health awareness in the security
  community. The "Dave" name and project ethos honor his work.
- **[Trail of Bits](https://www.trail-of-bits.com/)** — for publishing their
  security review corpus under CC BY-SA 4.0, which makes adapters like this
  possible without compromising on licensing hygiene.
- **Meta AI** — for releasing Llama-3.3-70B-Instruct as an open-weight model.
- **CISA, NIST, MITRE** — for public-domain and CC-licensed reference material.
- The wider open-source ML stack — `transformers`, `peft`, `trl`,
  `bitsandbytes`, `accelerate` — without which this would still be a
  multi-million-dollar project.

Proudly Made in Nebraska. Go Big Red! 🌽 https://xkcd.com/1654/
