# Training Data Sources and Licenses

The JSONL files in this directory contain prompt/completion pairs derived from
multiple public sources. Each file's content is governed by the license of its
upstream source, **not** the Apache 2.0 license that covers Dave's code.

| File | Source | License | Notes |
|---|---|---|---|
| `kev_training.jsonl` | CISA Known Exploited Vulnerabilities catalog | Public Domain (US Government work) | https://www.cisa.gov/known-exploited-vulnerabilities-catalog |
| `nist_training.jsonl` | NIST SP 800-30 Rev. 1, SP 800-53 Rev. 5, NISTIR 8286 | Public Domain (US Government work) | https://csrc.nist.gov/ |
| `dhs_cisa_training.jsonl` | CISA Binding Operational Directives, US-CERT alerts | Public Domain (US Government work) | https://www.cisa.gov/binding-operational-directives |
| `mitre_attack_training.jsonl` | MITRE ATT&CK® (defensive context only) | CC BY 4.0 | https://attack.mitre.org/ — attribution included in each completion |
| `trail_of_bits_training.jsonl` | Trail of Bits public security reviews | **CC BY-SA 4.0** | https://github.com/trailofbits/publications — attribution included in each completion; **share-alike obligation applies to downstream redistribution** |

## What "share-alike" means here

The Trail of Bits content is licensed CC BY-SA 4.0. Redistribution of `trail_of_bits_training.jsonl`
itself, or of a combined file (like `shuffled_training.jsonl`) that contains a substantial portion
of CC BY-SA content, must:

1. Carry attribution to Trail of Bits (already embedded in every completion).
2. Be licensed CC BY-SA 4.0 (or a compatible later version) for the CC BY-SA-derived
   portions.

Apache 2.0 governs Dave's training scripts, configuration, and the fine-tuned adapter weights
themselves. Whether and how those obligations propagate to the *outputs* of a model fine-tuned
on CC BY-SA data is unsettled in current jurisprudence. The conservative interpretation: if
Dave produces text that is substantively a verbatim or near-verbatim reproduction of training
content, treat the output as carrying the upstream license; otherwise, treat it as Dave's own
generation.

## Regenerating these files

Every file here is reproducible. From the repo root:

```bash
./build_training_data.sh
```

That re-downloads CISA KEV, NIST publications, MITRE ATT&CK, and DHS BODs from their
authoritative sources, and re-clones `trailofbits/publications` for the Trail of Bits step.
Outputs will overwrite the files in this directory.
