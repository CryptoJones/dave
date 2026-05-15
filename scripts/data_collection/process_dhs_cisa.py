#!/usr/bin/env python3
"""
DHS/CISA Binding Operational Directives & US-CERT Alerts Processor
Downloads and converts BODs and alerts to Dave training pairs.
Source: https://www.cisa.gov/
License: Public Domain
"""

import json
import os
import urllib.request
from pathlib import Path

OUTPUT_DIR = Path(os.environ.get("DAVE_DATA_DIR", "data")) / "processed" / "free_sources"

# CISA BODs are published as structured data
BODS_URL = "https://www.cisa.gov/sites/default/files/feeds/bod_directives.json"

# Hand-curated BOD data from public CISA website (fallback if feed unavailable)
BODS_FALLBACK = [
    {
        "id": "BOD 22-01",
        "title": "Reducing the Significant Risk of Known Exploited Vulnerabilities",
        "summary": (
            "CISA established the KEV catalog and requires federal agencies to remediate "
            "known exploited vulnerabilities within defined timeframes. Critical vulnerabilities "
            "must be remediated within 15 days; other KEV entries within 6 months."
        ),
        "action": (
            "Review the CISA KEV catalog regularly. Prioritize remediation of any vulnerabilities "
            "listed in the catalog. Establish a process to track KEV entries against your asset inventory."
        ),
    },
    {
        "id": "BOD 23-02",
        "title": "Mitigating the Risk from Internet-Exposed Management Interfaces",
        "summary": (
            "Networked management interfaces exposed to the public internet create undue risk. "
            "CISA directs agencies to remove these interfaces from internet exposure or implement "
            "Zero Trust Architecture controls."
        ),
        "action": (
            "Identify all internet-exposed management interfaces (RDP, SSH, Telnet, web management). "
            "Remove from public internet or place behind VPN/Zero Trust controls. "
            "Implement network-level access controls and multi-factor authentication."
        ),
    },
    {
        "id": "BOD 19-02",
        "title": "Vulnerability Remediation Requirements for Internet-Accessible Systems",
        "summary": (
            "Critical vulnerabilities on internet-accessible systems must be remediated within "
            "15 days of discovery. High vulnerabilities must be remediated within 30 days."
        ),
        "action": (
            "Establish a vulnerability management program with defined SLAs aligned to BOD 19-02. "
            "Critical findings: 15-day remediation window. High findings: 30-day remediation window. "
            "Track and report remediation status to leadership."
        ),
    },
    {
        "id": "BOD 20-01",
        "title": "Develop and Publish a Vulnerability Disclosure Policy",
        "summary": (
            "Organizations must establish a vulnerability disclosure policy (VDP) that describes "
            "how external researchers can report security vulnerabilities."
        ),
        "action": (
            "Publish a vulnerability disclosure policy at a well-known URL (e.g., /security.txt). "
            "Define scope, safe harbor provisions, and reporting channels. "
            "Establish a process to triage and respond to submitted reports."
        ),
    },
    {
        "id": "BOD 18-01",
        "title": "Enhance Email and Web Security",
        "summary": (
            "Requires implementation of DMARC, STARTTLS, and HTTPS across all agency domains "
            "and web services to protect email integrity and web communications."
        ),
        "action": (
            "Implement DMARC at enforcement (p=reject) on all domains. "
            "Enable STARTTLS on all mail servers. "
            "Deploy HTTPS on all web services with HSTS preloading. "
            "Disable SSLv2, SSLv3, TLS 1.0, and TLS 1.1."
        ),
    },
]

# US-CERT alert categories for training pair generation
CERT_CATEGORIES = [
    ("ransomware", "Ransomware Activity"),
    ("phishing", "Phishing Campaign"),
    ("credential-theft", "Credential Theft"),
    ("supply-chain", "Supply Chain Compromise"),
    ("zero-day", "Zero-Day Exploitation"),
    ("apt", "Advanced Persistent Threat Activity"),
]


def make_bod_pairs(bods: list[dict]) -> list[dict]:
    pairs = []
    for bod in bods:
        bid = bod.get("id", "")
        title = bod.get("title", "")
        summary = bod.get("summary", "")
        action = bod.get("action", "")

        if not (bid and title):
            continue

        pairs.append({
            "prompt": f"Write a remediation recommendation referencing {bid}.",
            "completion": (
                f"Remediation Recommendation — {bid}: {title}\n\n"
                f"Directive Summary:\n{summary}\n\n"
                f"Required Actions:\n{action}\n\n"
                f"Reference: CISA {bid} — {title}"
            ),
        })

        pairs.append({
            "prompt": f"What does {bid} require and how does it apply to this finding?",
            "completion": (
                f"{bid} ({title}) requires the following:\n\n"
                f"{action}\n\n"
                f"This directive applies to this finding because it establishes mandatory "
                f"remediation timelines and security baselines. Non-compliance with CISA BODs "
                f"represents regulatory risk in addition to technical risk."
            ),
        })

    return pairs


def make_cert_alert_pairs() -> list[dict]:
    pairs = []
    for slug, label in CERT_CATEGORIES:
        pairs.append({
            "prompt": f"Write an executive summary section for a {label} finding.",
            "completion": (
                f"Executive Summary — {label}\n\n"
                f"During this assessment, evidence of {label.lower()} activity was identified "
                f"within the environment. This finding represents a significant risk to "
                f"organizational operations, data integrity, and business continuity.\n\n"
                f"US-CERT and CISA have published guidance on {label.lower()} threats, "
                f"indicating this attack vector is actively exploited against organizations "
                f"of similar profile. Immediate remediation action is recommended.\n\n"
                f"The following sections detail the technical findings, business impact, "
                f"and prioritized remediation recommendations."
            ),
        })

    return pairs


def try_download_bods() -> list[dict] | None:
    print("Attempting to download CISA BOD feed...")
    try:
        with urllib.request.urlopen(BODS_URL, timeout=15) as r:
            data = json.loads(r.read().decode())
            if isinstance(data, list):
                return data
            return data.get("directives", None)
    except Exception as e:
        print(f"  BOD feed unavailable ({e}), using curated fallback data.")
        return None


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUTPUT_DIR / "dhs_cisa_training.jsonl"

    all_pairs = []

    bods = try_download_bods() or BODS_FALLBACK
    bod_pairs = make_bod_pairs(bods)
    all_pairs.extend(bod_pairs)
    print(f"BOD training pairs: {len(bod_pairs)}")

    cert_pairs = make_cert_alert_pairs()
    all_pairs.extend(cert_pairs)
    print(f"US-CERT alert pairs: {len(cert_pairs)}")

    with open(out_file, "w") as f:
        for pair in all_pairs:
            f.write(json.dumps(pair) + "\n")

    print(f"Total DHS/CISA training pairs: {len(all_pairs)}")
    print(f"Output: {out_file}")


if __name__ == "__main__":
    main()
