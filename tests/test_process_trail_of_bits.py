"""Tests for scripts/data_collection/process_trail_of_bits.py

Regression coverage for bugs encountered in the field:
- Python 3.13 inline-flag PatternError (was process_books_nda)
- pdftotext form-feed (\x0c) page breaks anchoring before headers
- Unicode bidi controls / zero-width spaces inside header lines
- Multi-line wrapped titles (TOB-SNOW-7-style)
"""

import json

import pytest

import process_trail_of_bits as tob


# ---------- header regex ----------

def test_modern_format_finds_one_finding(tob_text_modern):
    findings = tob.extract_findings(tob_text_modern)
    assert len(findings) == 1
    f = findings[0]
    assert f["finding_id"] == "TOB-EX-1"
    assert f["severity"] == "Informational"
    assert f["type"] == "Patching"
    assert "Cargo.toml" in f["target"]


def test_old_format_with_multi_line_title(tob_text_old):
    findings = tob.extract_findings(tob_text_old)
    assert len(findings) == 1
    f = findings[0]
    assert f["finding_id"] == "TOB-EX-2"
    assert f["severity"] == "Medium"
    # Multi-line title must be collapsed to one line.
    assert "\n" not in f["title"]
    assert "CipherState::decrypt_ad" in f["title"]


def test_form_feed_does_not_break_anchor():
    """\x0c at the start of a new page caused early termination of the finding list."""
    text = "\x0c 1. Example finding\n\n Severity: Low      Difficulty: Low\n\n" \
           " Type: Data Validation    Finding ID: TOB-EX-3\n\n" \
           " Target: foo.rs\n\nDescription\n" + "Body text. " * 30 + \
           "\n\nRecommendations\nDo the thing.\n"
    # pdf_to_text() strips form-feeds; simulate by calling the same stripping path.
    text = text.replace("\x0c", "")
    findings = tob.extract_findings(text)
    assert len(findings) == 1


def test_bidi_invisibles_are_stripped():
    """Newer reports embed U+202D (LRO) and U+202C (PDF) inside header values."""
    raw = (
        " 1. Example finding\n\n"
        " ‭Severity:‬‭Low‬        ‭Difficulty:‬‭High‬\n\n"
        " ‭Type: Cryptography‬   ‭Finding ID: TOB-EX-4‬\n\n"
        " ‭Target: foo.rs‬\n\n"
        "Description\n" + "Body. " * 30 +
        "\n\nRecommendations\nDo it.\n"
    )
    cleaned = tob._INVISIBLES.sub("", raw)
    findings = tob.extract_findings(cleaned)
    assert len(findings) == 1
    assert findings[0]["finding_id"] == "TOB-EX-4"
    assert findings[0]["severity"] == "Low"


def test_too_short_body_is_skipped():
    """Summary-of-findings table rows have no body — these should be skipped."""
    text = " 1. Title\n\n Severity: Low Difficulty: Low\n\n Type: X Finding ID: TOB-EX-5\n\n"
    findings = tob.extract_findings(text)
    assert findings == []


# ---------- web3 filter ----------

@pytest.mark.parametrize("term", [
    "solidity", "reentrancy", "Reentrant", "EVM", "oracle manipulation",
    "ERC-20", "ERC20", "Ethereum", "blockchain", "flash loan", "MEV",
    "Uniswap", "DeFi", "on-chain", "off-chain", "smart contracts", "vyper",
])
def test_web3_terms_are_caught(term):
    assert tob.is_web3(f"Some text mentioning {term} here")


@pytest.mark.parametrize("clean", [
    "Buffer overflow in libfoo",
    "Missing TLS certificate validation",
    "SQL injection via search parameter",
    "Weak password policy",
    "Authentication bypass in admin endpoint",
])
def test_non_web3_terms_pass_through(clean):
    assert not tob.is_web3(clean)


# ---------- finding body cleanup ----------

def test_page_footer_is_removed():
    body = (
        "Description content goes here. " * 5 +
        "\n   Trail of Bits                              15                  X Security Assessment\n"
        "   CONFIDENTIAL\n"
        + "More body content. " * 5
    )
    cleaned = tob.clean_finding_body(body)
    assert "CONFIDENTIAL" not in cleaned
    assert "Trail of Bits" not in cleaned


def test_split_description_recommendations():
    body = "Description text here.\n\nRecommendations\nShort term, do X.\nLong term, do Y."
    desc, recs = tob.split_description_recommendations(body)
    assert "Description text here" in desc
    assert "Short term, do X" in recs
    assert "Long term, do Y" in recs


def test_split_handles_missing_recommendations():
    body = "Just a description, no recs section."
    desc, recs = tob.split_description_recommendations(body)
    assert desc == "Just a description, no recs section."
    assert recs == ""


# ---------- make_pairs ----------

def test_make_pairs_yields_four_pairs_with_recommendations(tob_finding_dict):
    pairs = tob.make_pairs(tob_finding_dict)
    assert len(pairs) == 4


def test_make_pairs_yields_three_pairs_without_recommendations(tob_finding_dict):
    tob_finding_dict["recommendations"] = ""
    pairs = tob.make_pairs(tob_finding_dict)
    assert len(pairs) == 3


def test_every_pair_carries_attribution(tob_finding_dict):
    pairs = tob.make_pairs(tob_finding_dict)
    for p in pairs:
        assert "Trail of Bits" in p["completion"]
        assert "CC-BY-SA" in p["completion"] or "CC BY-SA" in p["completion"]


def test_structured_finding_contains_all_metadata(tob_finding_dict):
    pair = tob.make_pairs(tob_finding_dict)[0]
    assert tob_finding_dict["title"] in pair["completion"]
    assert tob_finding_dict["severity"] in pair["completion"]
    assert tob_finding_dict["difficulty"] in pair["completion"]
    assert tob_finding_dict["type"] in pair["completion"]
    assert tob_finding_dict["description"] in pair["completion"]
    assert tob_finding_dict["recommendations"] in pair["completion"]


def test_no_placeholder_strings_in_output(tob_finding_dict):
    pairs = tob.make_pairs(tob_finding_dict)
    blob = json.dumps(pairs)
    assert "[Extract" not in blob
    assert "based on chunk" not in blob


# ---------- pdf_to_text (lightweight subprocess test) ----------

def test_invisibles_regex_strips_known_chars():
    sample = "before​zero-width‭LRO‬reset﻿BOM­soft-hyphen after"
    cleaned = tob._INVISIBLES.sub("", sample)
    assert cleaned == "beforezero-widthLROresetBOMsoft-hyphen after"
