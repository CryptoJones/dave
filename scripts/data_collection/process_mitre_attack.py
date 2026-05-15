#!/usr/bin/env python3
"""
MITRE ATT&CK Processor — DEFENSIVE CONTEXT ONLY
Downloads ATT&CK Enterprise matrix and converts to Dave training pairs
focused on detection and hardening guidance, NOT offensive use.
Source: https://attack.mitre.org/
License: CC BY 4.0
"""

import json
import os
import urllib.request
from pathlib import Path

OUTPUT_DIR = Path(os.environ.get("DAVE_DATA_DIR", "data")) / "processed" / "free_sources"

ATTACK_URL = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"


def download_attack() -> dict:
    print("Downloading MITRE ATT&CK Enterprise matrix...")
    with urllib.request.urlopen(ATTACK_URL, timeout=60) as r:
        return json.loads(r.read().decode())


def make_pairs(bundle: dict) -> list[dict]:
    pairs = []
    objects = bundle.get("objects", [])

    techniques = [o for o in objects if o.get("type") == "attack-pattern" and not o.get("revoked")]

    for t in techniques:
        name = t.get("name", "")
        desc = t.get("description", "")
        tid = ""
        for ref in t.get("external_references", []):
            if ref.get("source_name") == "mitre-attack":
                tid = ref.get("external_id", "")
                break

        # Pull detection guidance if present
        detection = t.get("x_mitre_detection", "")
        platforms = ", ".join(t.get("x_mitre_platforms", []))
        permissions = ", ".join(t.get("x_mitre_permissions_required", []))

        if not (tid and name):
            continue

        # MITRE mapping pair — defensive framing only
        pairs.append({
            "prompt": (
                f"Map the following finding to MITRE ATT&CK and provide defensive guidance: "
                f"{name} ({tid})"
            ),
            "completion": (
                f"MITRE ATT&CK Mapping\n\n"
                f"Technique: {name}\n"
                f"ID: {tid}\n"
                f"Platforms: {platforms}\n"
                f"{'Permissions Required: ' + permissions + chr(10) if permissions else ''}"
                f"\nTechnique Overview:\n{desc[:500].strip()}{'...' if len(desc) > 500 else ''}\n\n"
                f"{'Detection Guidance:' + chr(10) + detection.strip() + chr(10) + chr(10) if detection else ''}"
                f"Defensive Recommendations:\n"
                f"- Review logs and alerts for indicators of {name} activity\n"
                f"- Implement detection rules aligned with {tid} in your SIEM\n"
                f"- Consult MITRE ATT&CK Navigator for related techniques and defensive coverage gaps\n"
                f"- Reference: https://attack.mitre.org/techniques/{tid.replace('.', '/')}/"
            ),
        })

    return pairs


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUTPUT_DIR / "mitre_attack_training.jsonl"

    bundle = download_attack()
    pairs = make_pairs(bundle)

    with open(out_file, "w") as f:
        for pair in pairs:
            f.write(json.dumps(pair) + "\n")

    print(f"ATT&CK techniques processed: {len(pairs)}")
    print(f"Output: {out_file}")


if __name__ == "__main__":
    main()
