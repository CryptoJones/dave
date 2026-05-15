# Dave — Limitations

**Read this before deploying Dave in an operational context.** Dave is a writing
assistant. Treating it as more than that endangers clients and practitioners.

---

## 1. Dataset is small for a 70B model

The default training set is approximately **11,000 prompt/completion pairs**. That is
small for fine-tuning a 70B-parameter base. The QLoRA adapter learns *style and
structure* from these examples but does not gain new world-knowledge — Dave's factual
breadth still comes from the Llama-3.3-70B-Instruct base model. Expect Dave to
sometimes produce confident-sounding writing about technical specifics it doesn't
actually know. **Verify every technical claim against the underlying evidence and
authoritative documentation.**

## 2. Source composition shapes the output

The training set is weighted toward:

- **Trail of Bits public audits (~63%)** — strong on cryptographic, parsing,
  data-validation, access-control, and dependency-management findings. Audit-style
  voice (formal, hedged, lots of "the Snow library does not...").
- **CISA KEV catalog (~29%)** — strong on CVE write-ups with required-action and
  due-date language.
- **MITRE ATT&CK (~6%)** — defensive mappings; Dave will reach for ATT&CK technique
  IDs when describing detection coverage.
- **NIST + DHS BODs (~2%)** — risk-narrative phrasing and federal-compliance framing.

Dave will be **weakest** at: red-team narrative writing, social-engineering finding
write-ups, physical-pentest reporting, embedded/IoT-specific reporting, and OT/ICS
report style. None of those domains are well-represented in the public sources we
were able to use legally.

## 3. The web3 filter is heuristic, not perfect

Trail of Bits' corpus is mostly smart-contract work. We filter findings whose title,
description, type, or recommendations match a deny-list (`solidity`, `reentrancy`,
`evm`, `oracle manipulation`, etc.). Some web3-flavored vocabulary will still leak
through. If your engagements never touch blockchain, expect occasional out-of-place
references to "canisters," "ledger state," or similar audit-domain idioms.

## 4. No real client reports

We do not train on confidential or NDA-protected pentest reports. The
`juliocesarfort/public-pentesting-reports` collection, the most-cited mega-corpus of
real reports, is built from third-party reports without explicit redistribution
permission — using it would create real legal exposure for an Apache 2.0
redistributable adapter. As a result, Dave has **never seen a real client
deliverable** during training. Output will have audit-firm voice (from Trail of Bits)
or advisory voice (from KEV / NIST). Adapt to your firm's house style during review.

## 5. Books are noisy and off by default

The licensed-book processor (`process_books_nda_fixed.py`) extracts chunks near
report-relevant keywords. Most security books are *teaching material*, not example
reports — so the extraction tends to surface tool descriptions, technique
walk-throughs, and table-of-contents fragments rather than report-style prose.
Books are **disabled by default** (`DAVE_INCLUDE_BOOKS=0`). Enabling them increases
volume but reduces signal-to-noise. Use only if you've curated the input library.

## 6. Hallucination risk on specific technical claims

When asked to write about a CVE, control, or technique that wasn't in training, Dave
may confidently fabricate plausible-sounding details (CVSS vectors, due dates,
RFC references, NIST control IDs). **Every specific number, identifier, citation,
and command-line in Dave's output must be verified by a human reviewer.** Treat
Dave's output as a draft a junior consultant would produce — useful structure, but
the senior reviewer is responsible for accuracy.

## 7. Authorization-gate is a prompt convention, not a hard guarantee

Dave is conditioned via system prompt to require written authorization before
writing target-specific content. This is a soft guardrail. Sufficiently
adversarial prompting can route around it. **Do not rely on Dave's authorization
behavior as a compliance control.** Authorization is the practitioner's
responsibility, verified via signed statement of work — not an LLM safety property.

## 8. Jurisdiction and acceptable use

Dave is trained, conditioned, and licensed for **authorized US security assessments
only.** Non-US targets, unauthorized testing, and offensive use are out of scope.
See `USAGE_POLICY.md`.

## 9. License obligations propagate

Content materially derived from CC BY-SA 4.0 sources (Trail of Bits) carries
attribution and share-alike obligations. The adapter itself ships under Apache 2.0,
but downstream redistribution of *outputs that materially copy CC BY-SA training
content* should respect the upstream license. When in doubt, treat substantive
verbatim or near-verbatim output as needing attribution.

## 10. Performance is not yet validated

At time of writing, Dave's adapter has not been benchmarked against held-out real
reports or evaluated by working penetration testers for output quality. Expect rough
edges in the first deployment. File issues against the repo with specific
input/output pairs where Dave performs poorly — that feedback drives future data
curation and re-training.

---

**Summary:** Dave is useful for compressing the time between *"I have evidence"* and
*"I have a draft section to edit."* Dave is not useful as a black box that produces
client-ready deliverables. The practitioner remains responsible for accuracy,
ethics, authorization, and final quality.
