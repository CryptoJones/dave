"""Tests for scripts/data_collection/process_cisa_kev.py"""

import json

import process_cisa_kev as kev


def test_complete_entry_yields_two_pairs(kev_entry):
    pairs = kev.make_pairs({"vulnerabilities": [kev_entry]})
    assert len(pairs) == 2


def test_incomplete_entry_is_skipped(kev_incomplete_entry):
    pairs = kev.make_pairs({"vulnerabilities": [kev_incomplete_entry]})
    assert pairs == []


def test_pair_contains_finding_metadata(kev_entry):
    pairs = kev.make_pairs({"vulnerabilities": [kev_entry]})
    finding = pairs[0]
    assert "CVE-2024-9999" in finding["completion"]
    assert "ExampleCorp" in finding["completion"]
    assert "WidgetServer" in finding["completion"]
    assert "Apply vendor patch immediately." in finding["completion"]
    assert "2024-12-31" in finding["completion"]


def test_pair_contains_kev_status_phrase(kev_entry):
    finding = kev.make_pairs({"vulnerabilities": [kev_entry]})[0]
    assert "Known Exploited Vulnerabilities catalog" in finding["completion"]


def test_remediation_pair_references_kev(kev_entry):
    remediation = kev.make_pairs({"vulnerabilities": [kev_entry]})[1]
    assert "CISA KEV" in remediation["completion"]
    assert "active exploitation" in remediation["completion"]


def test_no_placeholder_strings(kev_entry):
    pairs = kev.make_pairs({"vulnerabilities": [kev_entry]})
    blob = json.dumps(pairs)
    assert "Extract key vulnerability" not in blob
    assert "[Write APA" not in blob


def test_empty_input_returns_empty_list():
    assert kev.make_pairs({"vulnerabilities": []}) == []
    assert kev.make_pairs({}) == []
