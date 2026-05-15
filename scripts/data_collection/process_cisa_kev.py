#!/usr/bin/env python3
"""
CISA Known Exploited Vulnerabilities (KEV) Catalog Processor
Downloads and converts KEV data to Dave training pairs.
Source: https://www.cisa.gov/known-exploited-vulnerabilities-catalog
License: Public Domain
"""

import json
import os
import urllib.request
from pathlib import Path

KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
OUTPUT_DIR = Path(os.environ.get("DAVE_DATA_DIR", "data")) / "processed" / "free_sources"


def download_kev() -> dict:
    print("Downloading CISA KEV catalog...")
    with urllib.request.urlopen(KEV_URL) as r:
        return json.loads(r.read().decode())


def make_pairs(data: dict) -> list[dict]:
    pairs = []
    for v in data.get("vulnerabilities", []):
        cve = v.get("cveID", "")
        vendor = v.get("vendorProject", "")
        product = v.get("product", "")
        desc = v.get("shortDescription", "")
        action = v.get("requiredAction", "")
        due = v.get("dueDate", "")
        name = v.get("vulnerabilityName", "")

        if not (cve and action and desc):
            continue

        # Finding narrative pair
        pairs.append({
            "prompt": (
                f"Write a professional vulnerability finding for {cve} affecting "
                f"{vendor} {product}."
            ),
            "completion": (
                f"Vulnerability: {name}\n\n"
                f"CVE: {cve}\n"
                f"Affected Product: {vendor} {product}\n\n"
                f"Description: {desc}\n\n"
                f"CISA KEV Status: This vulnerability is listed in the CISA Known Exploited "
                f"Vulnerabilities catalog, indicating active exploitation in the wild.\n\n"
                f"Required Action: {action}\n\n"
                f"Due Date: {due}"
            ),
        })

        # Remediation pair
        if action:
            pairs.append({
                "prompt": (
                    f"What is the recommended remediation for {cve} in {vendor} {product}?"
                ),
                "completion": (
                    f"Per CISA KEV directive, the required action for {cve} ({name}) is: "
                    f"{action} This action must be completed by {due}. "
                    f"Organizations should treat KEV-listed vulnerabilities as highest priority "
                    f"given confirmed active exploitation."
                ),
            })

    return pairs


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUTPUT_DIR / "kev_training.jsonl"

    data = download_kev()
    pairs = make_pairs(data)

    with open(out_file, "w") as f:
        for pair in pairs:
            f.write(json.dumps(pair) + "\n")

    print(f"KEV entries processed: {len(data.get('vulnerabilities', []))}")
    print(f"Training pairs generated: {len(pairs)}")
    print(f"Output: {out_file}")


if __name__ == "__main__":
    main()
