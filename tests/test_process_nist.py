"""Tests for scripts/data_collection/process_nist.py"""

import process_nist as nist


def test_risk_pairs_cover_all_levels():
    pairs = nist.make_risk_assessment_pairs()
    completions = "\n".join(p["completion"] for p in pairs)
    for level, _, _ in nist.RISK_LEVELS:
        assert level in completions


def test_likelihood_pairs_cover_all_levels():
    pairs = nist.make_risk_assessment_pairs()
    completions = "\n".join(p["completion"] for p in pairs)
    for level, _ in nist.LIKELIHOOD_LEVELS:
        assert level in completions


def test_methodology_pair_present():
    pairs = nist.make_risk_assessment_pairs()
    assert any("Risk Assessment Methodology" in p["completion"] for p in pairs)


def test_methodology_references_nist_800_30():
    pairs = nist.make_risk_assessment_pairs()
    blob = "\n".join(p["completion"] for p in pairs)
    assert "NIST SP 800-30" in blob


def test_control_pair_emits_uppercase_id(sp80053_catalog):
    pairs = nist.make_control_pairs(sp80053_catalog)
    assert len(pairs) == 1
    # Catalog has lowercase id 'ac-2'; output should normalize to AC-2.
    assert "AC-2" in pairs[0]["completion"]


def test_control_pair_includes_statement_text(sp80053_catalog):
    pairs = nist.make_control_pairs(sp80053_catalog)
    assert "Define and document the types of accounts" in pairs[0]["completion"]
    assert "Assign account managers" in pairs[0]["completion"]


def test_control_pair_includes_family(sp80053_catalog):
    pair = nist.make_control_pairs(sp80053_catalog)[0]
    assert "Access Control" in pair["completion"]


def test_control_missing_statement_skipped():
    catalog = {"catalog": {"groups": [{"title": "x", "controls": [
        {"id": "no-stmt", "title": "T", "parts": []}
    ]}]}}
    assert nist.make_control_pairs(catalog) == []
