"""Tests for scripts/data_collection/process_books_nda_fixed.py

Includes a regression test for the Python-3.13 inline-regex-flag PatternError
that previously caused every book to fail silently during processing.
"""

import sys

import pytest


# This module's top-level reads sys.argv[1], so we have to set it up before
# import. We do that lazily via a fixture/helper.

@pytest.fixture
def books_module(tmp_path, monkeypatch):
    """Import process_books_nda_fixed with a benign argv so its module-level
    sys.argv[1] check does not call sys.exit(1)."""
    fake_books_dir = tmp_path / "books"
    fake_books_dir.mkdir()
    monkeypatch.setattr(sys, "argv", ["process_books_nda_fixed.py", str(fake_books_dir)])
    monkeypatch.setenv("DAVE_DATA_DIR", str(tmp_path / "data"))

    # Force a clean import so module-level code runs against our fakes.
    for name in list(sys.modules):
        if name.startswith("process_books_nda_fixed"):
            del sys.modules[name]
    import process_books_nda_fixed as books
    return books


# ---------- regex regression: Py 3.13+ inline flags ----------

def test_reporting_pattern_compiles(books_module):
    """The original module used `(?i)foo|(?i)bar` patterns that raise
    re.PatternError under Python 3.13. The fix uses a single re.IGNORECASE
    flag. This test guards against regression."""
    assert books_module.is_reporting_section("This text mentions a vulnerability.")
    assert books_module.is_reporting_section("Section on FINDINGS and remediation.")
    assert not books_module.is_reporting_section("Nothing relevant here.")


def test_reporting_pattern_is_case_insensitive(books_module):
    assert books_module.is_reporting_section("VULNERABILITY")
    assert books_module.is_reporting_section("Vulnerability")
    assert books_module.is_reporting_section("vulnerability")


# ---------- chunk cleaning ----------

def test_clean_chunk_collapses_whitespace(books_module):
    out = books_module.clean_chunk("foo   bar\n\nbaz")
    assert out == "foo bar baz"


def test_clean_chunk_strips_leading_trailing_page_numbers(books_module):
    out = books_module.clean_chunk("42 The body of the paragraph 43")
    assert out == "The body of the paragraph"


# ---------- classify_chunk ----------

@pytest.mark.parametrize("text,expected", [
    ("This is a critical CVE finding with high CVSS", "finding"),
    ("To remediate, apply the patch and rotate keys", "remediation"),
    ("Our methodology follows a phased approach", "methodology"),
    ("Executive summary: business impact is severe", "executive_summary"),
    ("Proof of concept screenshots and log output", "evidence"),
    ("Risk rating: high impact and high likelihood", "risk_assessment"),
    ("Some random other text about widgets", "general_reporting"),
])
def test_classify_chunk_categories(books_module, text, expected):
    assert books_module.classify_chunk(text) == expected


# ---------- generate_training_pair ----------

def test_short_chunk_returns_none(books_module):
    assert books_module.generate_training_pair("too short") is None


def test_generated_pair_has_real_content(books_module):
    """Regression: the original `process_books_nda.py` returned literal placeholder
    strings ('[Extract key vulnerability/finding from context]'). Fixed version
    must put the actual chunk into the completion."""
    chunk = ("This vulnerability allows an unauthenticated remote attacker to "
             "execute arbitrary code via a malformed packet on the management "
             "interface. The recommended remediation is to apply vendor patches.")
    pair = books_module.generate_training_pair(chunk)
    assert pair is not None
    # The completion must contain the actual chunk text, not a placeholder.
    assert "vulnerability" in pair["completion"]
    assert "[Extract" not in pair["completion"]
    assert "based on chunk" not in pair["completion"]
    # The prompt must be one of the curated templates, not the placeholder text.
    assert "Technical finding: [" not in pair["prompt"]


def test_generated_pair_uses_known_prompt_template(books_module):
    chunk = "We remediated the issue by applying a patch and rotating tokens. " * 3
    pair = books_module.generate_training_pair(chunk)
    assert pair is not None
    cat = books_module.classify_chunk(books_module.clean_chunk(chunk))
    assert pair["prompt"] in books_module._PROMPT_TEMPLATES[cat]


def test_pair_selection_is_deterministic(books_module):
    chunk = "An identified vulnerability allows privilege escalation. " * 3
    a = books_module.generate_training_pair(chunk)
    b = books_module.generate_training_pair(chunk)
    assert a == b
