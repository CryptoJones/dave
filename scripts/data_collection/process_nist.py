#!/usr/bin/env python3
"""
NIST Publications Processor
Downloads and converts NIST SP 800-30, SP 800-53, and NISTIR 8286 to Dave training pairs.
Sources: https://csrc.nist.gov/
License: Public Domain
"""

import json
import os
import urllib.request
from pathlib import Path

OUTPUT_DIR = Path(os.environ.get("DAVE_DATA_DIR", "data")) / "processed" / "free_sources"

# NIST publications available as JSON via their API
NIST_SOURCES = [
    {
        "id": "SP 800-30 Rev. 1",
        "title": "Guide for Conducting Risk Assessments",
        "url": "https://csrc.nist.gov/publications/detail/sp/800-30/rev-1/final",
        "context": "risk assessment methodology",
    },
    {
        "id": "SP 800-53 Rev. 5",
        "title": "Security and Privacy Controls for Information Systems and Organizations",
        "url": "https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final",
        "context": "security controls",
    },
    {
        "id": "NISTIR 8286",
        "title": "Integrating Cybersecurity and Enterprise Risk Management",
        "url": "https://csrc.nist.gov/publications/detail/nistir/8286/final",
        "context": "enterprise risk integration",
    },
]

# NIST SP 800-53 controls data (machine-readable)
SP80053_URL = "https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json"

# NIST SP 800-30 risk factors (hand-curated from public document)
RISK_LEVELS = [
    ("Very High", "10", "Catastrophic adverse effects on organizational operations, assets, or individuals."),
    ("High", "8-9", "Severe adverse effects on organizational operations, assets, or individuals."),
    ("Moderate", "5-7", "Significant adverse effects on organizational operations, assets, or individuals."),
    ("Low", "2-4", "Limited adverse effects on organizational operations, assets, or individuals."),
    ("Very Low", "1", "Negligible adverse effects on organizational operations, assets, or individuals."),
]

LIKELIHOOD_LEVELS = [
    ("Very High", "The threat event is almost certain to occur."),
    ("High", "The threat event is highly likely to occur."),
    ("Moderate", "The threat event is somewhat likely to occur."),
    ("Low", "The threat event is unlikely to occur."),
    ("Very Low", "The threat event is highly unlikely to occur."),
]


def make_risk_assessment_pairs() -> list[dict]:
    pairs = []

    # Risk level narrative pairs
    for level, score, desc in RISK_LEVELS:
        pairs.append({
            "prompt": f"Write a risk narrative for a {level} risk finding.",
            "completion": (
                f"Risk Level: {level} (Score: {score}/10)\n\n"
                f"Risk Assessment (per NIST SP 800-30 Rev. 1):\n"
                f"{desc}\n\n"
                f"This risk level requires {'immediate' if level in ('Very High', 'High') else 'planned'} "
                f"remediation action. "
                f"{'Senior leadership notification and expedited remediation are required.' if level == 'Very High' else ''}"
                f"{'Remediation should be prioritized and tracked at the management level.' if level == 'High' else ''}"
                f"{'Remediation should be included in the next planned maintenance cycle.' if level == 'Moderate' else ''}"
                f"{'Remediation may be addressed through routine security operations.' if level in ('Low', 'Very Low') else ''}"
            ),
        })

    # Likelihood pairs
    for level, desc in LIKELIHOOD_LEVELS:
        pairs.append({
            "prompt": f"How do I describe {level} likelihood in a risk assessment per NIST SP 800-30?",
            "completion": (
                f"Likelihood of Occurrence: {level}\n\n"
                f"Per NIST SP 800-30 Rev. 1: {desc}\n\n"
                f"When assessing likelihood, consider: threat source capability and intent, "
                f"vulnerability severity, and existing security controls. Document your "
                f"rationale for the likelihood determination in the finding narrative."
            ),
        })

    # Risk assessment methodology pairs
    pairs.append({
        "prompt": "Describe the NIST SP 800-30 risk assessment methodology for a penetration test report.",
        "completion": (
            "Risk Assessment Methodology (NIST SP 800-30 Rev. 1)\n\n"
            "This assessment follows the NIST SP 800-30 Rev. 1 framework for risk assessment, "
            "which evaluates risk as a function of:\n\n"
            "1. Threat Source Characteristics — The intent and capability of the threat actor "
            "to exploit the identified vulnerability.\n\n"
            "2. Vulnerability Severity — The degree to which the vulnerability can be exploited "
            "given current security controls.\n\n"
            "3. Impact — The magnitude of harm that would result from successful exploitation, "
            "assessed across organizational operations, assets, and individuals.\n\n"
            "4. Likelihood — The probability that the threat event will occur, considering "
            "existing controls and observed threat activity.\n\n"
            "Risk is rated on a five-point scale: Very High, High, Moderate, Low, and Very Low. "
            "Each finding includes a risk score, likelihood determination, impact assessment, "
            "and prioritized remediation guidance."
        ),
    })

    return pairs


def make_control_pairs(catalog: dict) -> list[dict]:
    pairs = []
    groups = catalog.get("catalog", {}).get("groups", [])

    for group in groups:
        family = group.get("title", "")
        for control in group.get("controls", []):
            control_id = control.get("id", "").upper()
            title = control.get("title", "")
            parts = control.get("parts", [])

            # Extract statement text
            statement = ""
            for part in parts:
                if part.get("name") == "statement":
                    for prose in part.get("parts", []):
                        statement += prose.get("prose", "") + " "

            if not (control_id and title and statement.strip()):
                continue

            pairs.append({
                "prompt": (
                    f"Write a remediation recommendation referencing NIST SP 800-53 {control_id}."
                ),
                "completion": (
                    f"Remediation Recommendation — {control_id}: {title}\n\n"
                    f"Control Family: {family}\n\n"
                    f"Per NIST SP 800-53 Rev. 5, {control_id} ({title}) requires: "
                    f"{statement.strip()}\n\n"
                    f"Implementation guidance: Review current configurations against the "
                    f"{control_id} control requirements and remediate any gaps. Document "
                    f"implementation evidence for audit purposes."
                ),
            })

    return pairs


def download_sp80053_catalog() -> dict | None:
    print("Downloading NIST SP 800-53 Rev. 5 catalog...")
    try:
        with urllib.request.urlopen(SP80053_URL, timeout=30) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"  Warning: Could not download SP 800-53 catalog: {e}")
        print("  Skipping control-level pairs, using risk assessment pairs only.")
        return None


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUTPUT_DIR / "nist_training.jsonl"

    all_pairs = []

    # SP 800-30 risk assessment pairs (hand-curated, no download needed)
    risk_pairs = make_risk_assessment_pairs()
    all_pairs.extend(risk_pairs)
    print(f"SP 800-30 risk assessment pairs: {len(risk_pairs)}")

    # SP 800-53 control pairs (from machine-readable catalog)
    catalog = download_sp80053_catalog()
    if catalog:
        control_pairs = make_control_pairs(catalog)
        all_pairs.extend(control_pairs)
        print(f"SP 800-53 control pairs: {len(control_pairs)}")

    with open(out_file, "w") as f:
        for pair in all_pairs:
            f.write(json.dumps(pair) + "\n")

    print(f"Total NIST training pairs: {len(all_pairs)}")
    print(f"Output: {out_file}")


if __name__ == "__main__":
    main()
