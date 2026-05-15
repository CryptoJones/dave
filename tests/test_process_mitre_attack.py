"""Tests for scripts/data_collection/process_mitre_attack.py"""

import process_mitre_attack as mitre


def test_single_technique_produces_one_pair(attack_bundle):
    pairs = mitre.make_pairs(attack_bundle)
    assert len(pairs) == 1


def test_revoked_techniques_are_skipped(attack_bundle):
    pairs = mitre.make_pairs(attack_bundle)
    blob = "".join(p["completion"] for p in pairs)
    assert "Revoked Technique" not in blob
    assert "T9999" not in blob


def test_pair_contains_technique_metadata(attack_bundle):
    pair = mitre.make_pairs(attack_bundle)[0]
    assert "T1053.005" in pair["completion"]
    assert "Scheduled Task" in pair["completion"]
    assert "Windows" in pair["completion"]


def test_pair_has_defensive_framing(attack_bundle):
    """Dave should never emit offensive content; output must read as detection guidance."""
    pair = mitre.make_pairs(attack_bundle)[0]
    completion = pair["completion"].lower()
    assert "defensive recommendations" in completion
    assert "detection rules" in completion
    # No offensive verbs in the framing
    assert "exploit this technique" not in completion
    assert "how to attack" not in completion


def test_pair_references_attack_navigator(attack_bundle):
    pair = mitre.make_pairs(attack_bundle)[0]
    assert "attack.mitre.org/techniques/T1053/005" in pair["completion"]


def test_description_truncation():
    long_desc = "A" * 700
    bundle = {
        "objects": [{
            "type": "attack-pattern",
            "name": "Test",
            "description": long_desc,
            "external_references": [{"source_name": "mitre-attack", "external_id": "T0001"}],
        }]
    }
    pair = mitre.make_pairs(bundle)[0]
    # Description is truncated to 500 chars + ellipsis
    assert "..." in pair["completion"]
    assert "A" * 700 not in pair["completion"]


def test_techniques_missing_id_are_skipped():
    bundle = {"objects": [{"type": "attack-pattern", "name": "NoId", "description": "x"}]}
    assert mitre.make_pairs(bundle) == []
