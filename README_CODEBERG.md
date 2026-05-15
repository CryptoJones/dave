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
| Ronin 48, LLC | N/A | Founding donor |

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
| **Suite** | Ronin 48 |

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
├── USAGE_POLICY.md
├── RUN_DAVE.sh                         # Step-by-step execution guide
├── setup_dave.sh                       # Environment setup
├── data/
│   ├── processed/
│   │   ├── books/                      # NDA-compliant book training pairs
│   │   └── free_sources/               # CISA KEV, NIST, MITRE, etc.
│   └── combined_training.jsonl         # Final shuffled training data
├── scripts/
│   └── data_collection/
│       ├── process_books_nda.py        # NDA-safe book processor
│       └── process_books_nda_fixed.py  # Production version with full classification
├── src/
└── docs/
```

---

## Training Data Sources

| Source | Description | License |
|---|---|---|
| Licensed Security Books | PDF/EPUB/MOBI — findings, remediation, methodology sections | NDA-compliant (your own licensed copies) |
| CISA KEV Catalog | Known Exploited Vulnerabilities with required actions and due dates | Public Domain |
| NIST SP 800-30 Rev. 1 | Risk assessment guidance | Public Domain |
| NIST SP 800-53 Rev. 5 | Security and privacy controls | Public Domain |
| NISTIR 8286 | Cybersecurity risk integration | Public Domain |
| DHS Binding Operational Directives | Federal cybersecurity directives | Public Domain |
| US-CERT Alerts | Vulnerability and threat alerts | Public Domain |
| MITRE ATT&CK® | Defensive context mappings only | CC BY 4.0 |

### NDA-Compliant Book Processing

Dave's `process_books_nda_fixed.py` extracts reporting-relevant sections from your licensed security
books without logging filenames, paths, or content details. Your NDA stays intact. The output is
anonymous training pairs — the model learns your books' writing style without anyone else ever
seeing what books you own.

Run it against your own licensed collection:

```bash
python3 scripts/data_collection/process_books_nda_fixed.py /path/to/your/books
```

---

## Quick Start

```bash
# Step 1: Prepare environment
chmod +x setup_dave.sh RUN_DAVE.sh
./setup_dave.sh

# Step 2: Process your licensed books
python3 scripts/data_collection/process_books_nda_fixed.py /path/to/your/books

# Step 3: Process free resources (see RUN_DAVE.sh for full list and commands)
# CISA KEV, NIST publications, MITRE ATT&CK (defensive only)

# Step 4: Combine and shuffle
cat data/processed/books/books_training.jsonl \
    data/processed/free_sources/*_training.jsonl \
    > data/combined_training.jsonl
shuf data/combined_training.jsonl > data/shuffled_training.jsonl

# Step 5: Train
python3 train_dave.py

# Step 6: Verify
ls -la dave_model/
```

Requires: 24GB+ VRAM (A100 recommended), Python 3.10+, CUDA 11.8+

---

## The Ronin 48 Suite

Dave handles the report. The rest of the suite handles everything else.

| Model | Domain | Purpose |
|---|---|---|
| **Dave** | Security Assessment | Penetration test report writing, findings, remediations, executive summaries |
| **[SELMA](https://codeberg.org/Ronin48/SELMA)** | Law Enforcement | Criminal statute identification, charge elements, constitutional flags |
| **[ABBY](https://codeberg.org/Ronin48/ABBY)** | Digital Forensics | Forensic methodology, evidence standards, chain of custody |
| **[ATTICUS](https://codeberg.org/Ronin48/ATTICUS)** | Defense | Defense strategy, constitutional analysis, evidentiary weaknesses |
| **[BRUNO](https://codeberg.org/Ronin48/BRUNO)** | Fire Service | Fireground tactics, incident command, hazmat, extrication |
| **[BONES](https://codeberg.org/Ronin48/BONES)** | EMS | Patient assessment, treatment protocols, triage, transport |

---

## Disclaimer

Dave is a writing assistant for authorized security professionals. It is **NOT**:

- A tool for unauthorized access, exploitation, or attack
- A replacement for professional judgment, peer review, or legal counsel
- Authorized for use against targets without explicit written permission
- Suitable for use outside United States jurisdiction

All outputs must be reviewed by a qualified security professional before delivery to a client.
Dave is an assistant, not a author. The practitioner is responsible for the accuracy,
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

**Base Model Weights:** Meta Llama 3.1 Community License. Fine-tuned adapter weights and all
original Dave contributions remain Apache 2.0.

---

Proudly Made in Nebraska. Go Big Red! 🌽
