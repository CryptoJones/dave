"""
Shared pytest fixtures for the Dave test suite.

Most tests target the pure-function helpers in scripts/data_collection/*.py.
We add that directory to sys.path so tests can import each processor as a
top-level module without packaging the scripts.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts" / "data_collection"

# Make the processors importable as flat modules.
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# Also make the repo root importable (for train_dave).
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# ---------- KEV ----------

import pytest


@pytest.fixture
def kev_entry() -> dict:
    """One representative entry from the CISA KEV feed."""
    return {
        "cveID": "CVE-2024-9999",
        "vendorProject": "ExampleCorp",
        "product": "WidgetServer",
        "vulnerabilityName": "ExampleCorp WidgetServer Auth Bypass",
        "shortDescription": "An unauthenticated attacker can bypass login.",
        "requiredAction": "Apply vendor patch immediately.",
        "dueDate": "2024-12-31",
    }


@pytest.fixture
def kev_incomplete_entry() -> dict:
    """Missing requiredAction — make_pairs should skip this one."""
    return {
        "cveID": "CVE-2024-0001",
        "vendorProject": "ExampleCorp",
        "product": "WidgetServer",
        "shortDescription": "An issue.",
        "requiredAction": "",
        "dueDate": "2024-12-31",
    }


# ---------- BOD ----------

@pytest.fixture
def bod_entry() -> dict:
    return {
        "id": "BOD 22-01",
        "title": "Reducing the Significant Risk of Known Exploited Vulnerabilities",
        "summary": "Federal agencies must remediate KEV entries on a schedule.",
        "action": "Track KEV against asset inventory and remediate per schedule.",
    }


# ---------- MITRE ATT&CK ----------

@pytest.fixture
def attack_bundle() -> dict:
    """A minimal STIX-like bundle with one technique."""
    return {
        "objects": [
            {
                "type": "attack-pattern",
                "name": "Scheduled Task",
                "description": "Adversaries may abuse the Windows Task Scheduler.",
                "external_references": [
                    {"source_name": "mitre-attack", "external_id": "T1053.005"},
                ],
                "x_mitre_platforms": ["Windows"],
                "x_mitre_permissions_required": ["User", "Administrator"],
                "x_mitre_detection": "Monitor scheduled task creation.",
            },
            {
                # Revoked entries should be skipped.
                "type": "attack-pattern",
                "name": "Revoked Technique",
                "description": "Should not appear in output.",
                "revoked": True,
                "external_references": [
                    {"source_name": "mitre-attack", "external_id": "T9999"},
                ],
            },
        ]
    }


# ---------- NIST SP 800-53 catalog ----------

@pytest.fixture
def sp80053_catalog() -> dict:
    """A trimmed SP 800-53 catalog with one control."""
    return {
        "catalog": {
            "groups": [
                {
                    "title": "Access Control",
                    "controls": [
                        {
                            "id": "ac-2",
                            "title": "Account Management",
                            "parts": [
                                {
                                    "name": "statement",
                                    "parts": [
                                        {"prose": "Define and document the types of accounts."},
                                        {"prose": "Assign account managers."},
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ]
        }
    }


# ---------- Trail of Bits ----------

# Synthetic excerpt that matches the modern Trail of Bits finding format.
TOB_FINDING_TEXT_NEW = """\
Detailed Findings

 1. Sodiumoxide dependency is deprecated and unmaintained

 Severity: Informational                         Difficulty: Not Applicable


 Type: Patching                                  Finding ID: TOB-EX-1


 Target: Cargo.toml


Description
The library uses the deprecated sodiumoxide crate, which is flagged unmaintained
in the RustSec advisory database.


Recommendations
Short term, deprecate the sodiumoxide backend or warn users that it is
unmaintained.

Long term, use cargo audit during release to catch known deprecations.


   Trail of Bits                              15                  Example Security Assessment
   CONFIDENTIAL
"""

# Older format: no blank line between title and Severity:, plus a multi-line title.
TOB_FINDING_TEXT_OLD = """\
1. CipherState::decrypt_ad increments nonce even after authentication
failure
Severity: Medium                                Difficulty: Low
Type: Cryptography                              Finding ID: TOB-EX-2
Target: src/cipherstate.rs

Description
The decrypt_ad function increments the nonce before verifying the AEAD tag,
allowing an attacker to permanently desynchronize an encrypted channel.

Recommendations
Short term, only increment the nonce after successful tag verification.

Long term, add fuzzing for adversarial AEAD inputs.

   Trail of Bits                              30                  Example Security Assessment
   CONFIDENTIAL
"""


@pytest.fixture
def tob_text_modern() -> str:
    return TOB_FINDING_TEXT_NEW


@pytest.fixture
def tob_text_old() -> str:
    return TOB_FINDING_TEXT_OLD


@pytest.fixture
def tob_finding_dict() -> dict:
    """A pre-parsed finding dict matching what extract_findings returns."""
    return {
        "number": "1",
        "title": "Example finding for unit tests",
        "severity": "Medium",
        "difficulty": "Low",
        "type": "Data Validation",
        "finding_id": "TOB-EX-1",
        "target": "src/example.rs",
        "description": "The example library does not validate input length.",
        "recommendations": "Short term, validate input length. Long term, fuzz the parser.",
    }
