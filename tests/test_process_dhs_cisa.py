"""Tests for scripts/data_collection/process_dhs_cisa.py"""

import process_dhs_cisa as dhs


def test_bod_yields_two_pairs_each(bod_entry):
    pairs = dhs.make_bod_pairs([bod_entry])
    assert len(pairs) == 2


def test_bod_pair_includes_id_and_title(bod_entry):
    pairs = dhs.make_bod_pairs([bod_entry])
    for p in pairs:
        assert bod_entry["id"] in p["completion"]
        assert bod_entry["title"] in p["completion"]


def test_bod_skipped_when_id_or_title_missing():
    bad = [{"id": "", "title": "x", "summary": "y", "action": "z"},
           {"id": "BOD 1", "title": "", "summary": "y", "action": "z"}]
    assert dhs.make_bod_pairs(bad) == []


def test_cert_alert_pairs_cover_all_categories():
    pairs = dhs.make_cert_alert_pairs()
    assert len(pairs) == len(dhs.CERT_CATEGORIES)
    for (_, label), pair in zip(dhs.CERT_CATEGORIES, pairs):
        assert label in pair["completion"]


def test_fallback_data_is_well_formed():
    """The hand-curated fallback list must include required fields."""
    for bod in dhs.BODS_FALLBACK:
        assert bod["id"]
        assert bod["title"]
        assert bod["summary"]
        assert bod["action"]


def test_bod_pairs_no_placeholder_strings(bod_entry):
    pairs = dhs.make_bod_pairs([bod_entry])
    for p in pairs:
        assert "Extract key" not in p["completion"]
        assert "based on chunk" not in p["completion"]
