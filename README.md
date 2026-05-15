# Dave — Documentation of Adversarial Vulnerability Evidence

> **Before deploying in an operational context, read [LIMITATIONS.md](LIMITATIONS.md).**

**An Open-Source Model Fine-Tuned for Security Assessment Report Writing**

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg?logo=apache)](https://opensource.org/licenses/Apache-2.0)
[![Codeberg](https://img.shields.io/badge/Codeberg-CryptoJones%2FDave-2185D0?logo=codeberg&logoColor=white)](https://codeberg.org/CryptoJones/Dave)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-v0.1.0--dev-orange)]()

> *"Hacking is not just a technical skill — it's a mindset. And the report is where that mindset
> becomes something that actually changes an organization."*
> — David Kennedy, TrustedSec

> *"The best penetration test in the world means nothing if the report doesn't communicate the risk."*

---

## Acknowledgments

Dave is named in the spirit of **David Kennedy** — founder of TrustedSec, creator of the Social
Engineer Toolkit (SET), co-author of *Metasploit: The Penetration Tester's Guide*, and one of the
most vocal advocates for mental health awareness in the security community.

Dave wrote the blog post. He talked about what this work does to people. He was right.

This model carries his name as a reminder that the people writing these reports are human beings —
and that the reports they write protect other human beings. Do the work with that in mind.

---

## Supporters

Dave is community-funded. Every contribution keeps this project free, open, and in the hands
of the practitioners who need it most.

| Donor | Amount | Note |
|---|---|---|
| Joe Sixpack (Anonymous) | N/A | Founding donor |
| CryptoJones (Aaron K. Clark) | $25 | |

*Want to support Dave? Reach out to the maintainers.*

---

## Overview

| Attribute | Value |
|---|---|
| **Full Name** | Documentation of Adversarial Vulnerability Evidence |
| **Named After** | David Kennedy, TrustedSec |
| **Role** | Security assessment report writing assistant |
| **Users** | Penetration testers, red teamers, security consultants |
| **Base Model** | `meta-llama/Llama-3.3-70B-Instruct` (fine-tuned) |
| **Alignment** | APA / (ISC)² / NIST / OWASP / DHS-CISA |
| **Jurisdiction** | United States authorized assessments only |
| **Project** | CryptoJones |

Dave is not a hacking tool. Dave writes about hacking — professionally, precisely, and in a way
that clients can actually act on. The exploitation is yours. The report is Dave's.

---

## Capabilities

Given a technical finding, evidence description, or raw assessment notes, Dave can:

1. **Finding Narratives** — Write professional vulnerability findings in APA/(ISC)²-aligned format:
   title, severity, CVSS score rationale, description, evidence, business impact, and remediation

2. **Executive Summaries** — Translate technical findings into C-suite language: what was found,
   what it means for the business, what needs to happen, and by when

3. **Remediation Guidance** — Write actionable, prioritized remediation recommendations using
   NIST, CISA, and vendor guidance as references

4. **Methodology Sections** — Document assessment scope, approach, tools used, and testing phases
   in language that survives legal review and client questions

5. **Risk Narratives** — Build risk assessment sections using CVSS, NIST SP 800-30, and
   business-impact language that quantifies risk without overstating it

6. **Evidence Documentation** — Write proof-of-concept descriptions and evidence sections
   that are technically accurate without being a how-to guide

7. **CISA KEV Integration** — Reference the Known Exploited Vulnerabilities catalog when
   applicable findings align with KEV entries, with required action and due dates

8. **MITRE ATT&CK Mapping** — Map findings to ATT&CK techniques in defensive context —
   for detection and hardening guidance, not offense

---

## ⚠ Authorization Requirement

Dave is trained to ask one question before writing anything:

> *Do you have explicit, written authorization to conduct this assessment against this target?*

Dave will not write a finding for an unauthorized test. It will not help you frame an
unauthorized intrusion as a security assessment. Every output Dave generates should be traceable
to a signed statement of work, rules of engagement, or written authorization letter.

This is not a technical limitation. It is a professional obligation.

---

## Architecture

- **Base Model:** [Meta Llama 3.3 70B Instruct](https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct)
- **Fine-tuning Method:** QLoRA (4-bit quantization with Low-Rank Adaptation)
- **Context Window:** 128K tokens (native)
- **Quantization:** NF4 double quantization via bitsandbytes
- **Origin:** Meta Platforms, Inc. (United States)

---

## Project Structure

```
Dave/
├── LICENSE
├── README.md
├── LIMITATIONS.md                          # Read before operational deployment
├── TRAINING.md                             # Operator's guide for training runs
├── MODEL_CARD.md                           # Model card uploaded to HF Hub
├── USAGE_POLICY.md
├── RUN_DAVE.sh                             # One-shot wrapper: build data → train
├── setup_dave.sh                           # Environment / dependency install
├── build_training_data.sh                  # Re-runnable data pipeline (idempotent)
├── train_dave.py                           # QLoRA training entry point
├── data/
│   ├── processed/
│   │   ├── books/                          # Opt-in licensed-book pairs (NDA-safe)
│   │   └── free_sources/                   # KEV / NIST / MITRE / DHS / Trail of Bits
│   ├── raw_github/                         # Cloned public sources (gitignored)
│   └── shuffled_training.jsonl             # Final training file (~11k pairs)
└── scripts/
    ├── publish_adapter.sh                  # Upload trained adapter to HF Hub + GitHub Release
    └── data_collection/
        ├── process_cisa_kev.py             # CISA KEV catalog → JSONL
        ├── process_nist.py                 # NIST SP 800-30/53, NISTIR 8286
        ├── process_dhs_cisa.py             # CISA Binding Operational Directives
        ├── process_mitre_attack.py         # MITRE ATT&CK (defensive context)
        ├── process_trail_of_bits.py        # Trail of Bits public audits (CC-BY-SA)
        └── process_books_nda_fixed.py      # NDA-safe book processor (opt-in)
```

---

## Training Data Sources

| Source | Description | License |
|---|---|---|
| Trail of Bits public security reviews | ~1,800 real findings with severity, description, recommendations | CC BY-SA 4.0 |
| CISA KEV Catalog | Known Exploited Vulnerabilities with required actions and due dates | Public Domain |
| NIST SP 800-30 Rev. 1 | Risk assessment guidance | Public Domain |
| NIST SP 800-53 Rev. 5 | Security and privacy controls | Public Domain |
| NISTIR 8286 | Cybersecurity risk integration | Public Domain |
| DHS Binding Operational Directives | Federal cybersecurity directives | Public Domain |
| US-CERT Alerts | Vulnerability and threat alerts | Public Domain |
| MITRE ATT&CK® | Defensive context mappings only | CC BY 4.0 |
| Licensed Security Books *(opt-in)* | PDF/EPUB/MOBI extracted via NDA-safe processor — disabled by default; enable with `DAVE_INCLUDE_BOOKS=1` | NDA-compliant (your own licensed copies) |

### Attribution (CC BY-SA 4.0 content)

Training pairs derived from `trailofbits/publications` (and any other CC BY-SA source
added later) carry an attribution line in every completion. Downstream uses of the
fine-tuned adapter inherit the share-alike obligation under CC BY-SA 4.0 for content
materially derived from those sources. The Apache 2.0 license on Dave's own code and
configuration is unaffected.

### Web3 / Smart-Contract Filter

Trail of Bits' public corpus is web3-heavy. `process_trail_of_bits.py` skips any
finding whose title, description, or type matches a pattern from a configurable
deny-list (Solidity, reentrancy, EVM, oracle manipulation, ERC-20/721/1155, DeFi,
flash loans, MEV, blockchain, on/off-chain, etc.). This keeps Dave focused on
general-purpose security writing rather than smart-contract auditing. Toggle or
extend `WEB3_TERMS` in that script if your engagements include web3 work.

### NDA-Compliant Book Processing (opt-in)

`process_books_nda_fixed.py` extracts reporting-relevant sections from your own
licensed security books. It never logs filenames, paths, or content details — the
output is anonymous training pairs.

**Books are disabled by default.** The heuristic extraction yields a mix of useful
prose and table-of-contents / index noise (books are written for humans, not as
report exemplars). Enable only if you have curated your library and accept the
quality trade-off:

```bash
export DAVE_INCLUDE_BOOKS=1
export DAVE_BOOKS_DIR=/path/to/your/books
./build_training_data.sh
```

---

## Quick Start

```bash
# 1. One-time environment setup (installs PyTorch, transformers, peft, trl, bitsandbytes, ...)
chmod +x setup_dave.sh build_training_data.sh RUN_DAVE.sh
./setup_dave.sh

# 2. Choose where data and the trained adapter live
export DAVE_DATA_DIR=$(pwd)/data
export DAVE_OUTPUT_DIR=$(pwd)/dave_adapter

# 3. (Usually skip) Build the training dataset
#    The committed `data/shuffled_training.jsonl` (~11k pairs from free sources)
#    is already ready to train on. `build_training_data.sh` short-circuits if
#    that file is present, so you can run it harmlessly. Force a full rebuild
#    only if you want to refresh from upstream:
#      DAVE_FORCE_REBUILD=1 ./build_training_data.sh
#    To include your own licensed books, set DAVE_INCLUDE_BOOKS=1 and
#    DAVE_BOOKS_DIR=/path/to/your/books, then force a rebuild.
./build_training_data.sh

# 4. Train Dave (target: single A100 80GB on RunPod)
python3 train_dave.py

# 5. Verify
ls -la "$DAVE_OUTPUT_DIR"     # expect adapter_config.json + adapter_model.safetensors
```

**Compute target:** single NVIDIA A100 80GB (RunPod). The training script uses 4-bit
NF4 quantization with LoRA (r=16, α=32) on all attention and MLP projections, paged
8-bit AdamW, and bf16 compute — Llama-3.3-70B fits in 80GB with room for activations.

**Resulting dataset (default config, no books):** ~11k prompt/completion pairs from
Trail of Bits audits, CISA KEV, NIST, MITRE ATT&CK, and DHS BODs. See the next section
for source breakdown.

---

## Training Dave

For everything about launching a training run, reading the live metrics,
deciding when to stop, picking the right checkpoint, and recovering from
common failure modes (underfit / overfit / instability), see
[TRAINING.md](TRAINING.md). It's the operator's guide for whoever is sitting
in the RunPod shell during a fine-tune.

## Where to find Dave

After training, the LoRA adapter is published to two places:

- **Hugging Face Hub** (primary, canonical): https://huggingface.co/CryptoJones/Dave-Llama-3.3-70B-QLoRA
  Use this for `PeftModel.from_pretrained()` loading. See [MODEL_CARD.md](MODEL_CARD.md)
  for the full model card.
- **GitHub Release** (mirror archive): the latest tag at
  https://github.com/CryptoJones/dave/releases contains a tarball of the
  adapter as an attachment.

Run `./scripts/publish_adapter.sh` after training to push to both. See
[TRAINING.md](TRAINING.md) step 6 for prerequisites.

---

## Testing

```bash
pip install pytest
python3 -m pytest tests/
```

The suite covers the pure-function helpers in every data processor and in
`train_dave.py`'s data-quality guard. Tests that depend on `torch` /
`transformers` are auto-skipped when those deps aren't installed (so the suite
runs cleanly on a dev box and the same tests light up on the training pod).

See `tests/README.md` for the test inventory and conventions.

---

## Disclaimer

Dave is a writing assistant for authorized security professionals. It is **NOT**:

- A tool for unauthorized access, exploitation, or attack
- A replacement for professional judgment, peer review, or legal counsel
- Authorized for use against targets without explicit written permission
- Suitable for use outside United States jurisdiction

All outputs must be reviewed by a qualified security professional before delivery to a client.
Dave is an assistant, not an author. The practitioner is responsible for the accuracy,
completeness, and ethics of every report that bears their name.

This software is provided "AS IS" without warranty of any kind.

---

## Usage Policy

See [USAGE_POLICY.md](USAGE_POLICY.md) for the full acceptable use policy, including
permitted uses, prohibited uses, and enforcement.

**TL;DR:** Authorized US security assessments only. Written permission required. No malware.
No non-US targets. No unauthorized access.

---

## Contributing

Contributions from working penetration testers, red teamers, and security consultants are
especially welcome. If you write reports for a living and have opinions about how Dave should
write them — open an issue or a pull request.

---

## License

**Apache License 2.0** — Copyright 2026 Aaron K. Clark. See [LICENSE](LICENSE).

**Base Model Weights:** Meta Llama 3.3 Community License. Fine-tuned adapter weights and all
original Dave contributions remain Apache 2.0.

Proudly Made in Nebraska. Go Big Red! 🌽 https://xkcd.com/1654/
