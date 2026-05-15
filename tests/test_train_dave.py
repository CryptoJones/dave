"""Tests for train_dave.py — the unit-testable helpers only.

The actual `main()` requires CUDA + a 70B base model, so it's not exercised here.
We cover the lightweight pure-function helpers and the data-quality guard.
"""

import json

import pytest


@pytest.fixture
def train_module(monkeypatch, tmp_path):
    """Import train_dave with environment that won't blow up at module load."""
    monkeypatch.setenv("DAVE_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("DAVE_OUTPUT_DIR", str(tmp_path / "out"))

    import sys
    for name in list(sys.modules):
        if name == "train_dave":
            del sys.modules[name]
    try:
        import train_dave
    except ImportError as e:
        pytest.skip(f"train_dave's heavy deps not installed: {e}")
    return train_dave


def test_format_example_returns_messages_structure(train_module):
    example = {"prompt": "Write a finding.", "completion": "Here is one."}
    out = train_module.format_example(example)
    assert "messages" in out
    msgs = out["messages"]
    assert len(msgs) == 3
    assert msgs[0]["role"] == "system"
    assert msgs[1]["role"] == "user"
    assert msgs[1]["content"] == "Write a finding."
    assert msgs[2]["role"] == "assistant"
    assert msgs[2]["content"] == "Here is one."


def test_system_prompt_mentions_authorization(train_module):
    """The system-prompt convention is one of Dave's soft guardrails."""
    assert "authoriz" in train_module.SYSTEM_PROMPT.lower()


def test_system_prompt_disclaims_offensive_content(train_module):
    assert "offensive" in train_module.SYSTEM_PROMPT.lower() or \
           "how-to" in train_module.SYSTEM_PROMPT.lower()


def test_placeholder_guard_passes_clean_file(train_module, tmp_path):
    f = tmp_path / "clean.jsonl"
    f.write_text(json.dumps({"prompt": "P", "completion": "C"}) + "\n")
    # Should not raise.
    train_module.check_for_placeholder_rows(f, sample=10)


def test_placeholder_guard_fails_on_dirty_file(train_module, tmp_path):
    f = tmp_path / "dirty.jsonl"
    dirty_completion = "Executive summary: [Write APA/(ISC)²-aligned summary based on chunk]"
    dirty_prompt = "Technical finding: [Extract key vulnerability/finding from context]"
    f.write_text(json.dumps({"prompt": dirty_prompt, "completion": dirty_completion}) + "\n")
    with pytest.raises(SystemExit) as excinfo:
        train_module.check_for_placeholder_rows(f, sample=10)
    assert "placeholder" in str(excinfo.value).lower()


def test_require_data_file_exits_when_missing(train_module, tmp_path, monkeypatch):
    monkeypatch.setattr(train_module, "TRAIN_FILE", tmp_path / "nope.jsonl")
    with pytest.raises(SystemExit):
        train_module.require_data_file()


def test_require_data_file_exits_on_empty(train_module, tmp_path, monkeypatch):
    empty = tmp_path / "empty.jsonl"
    empty.write_text("")
    monkeypatch.setattr(train_module, "TRAIN_FILE", empty)
    with pytest.raises(SystemExit):
        train_module.require_data_file()


def test_require_data_file_passes_on_real_file(train_module, tmp_path, monkeypatch):
    real = tmp_path / "real.jsonl"
    real.write_text(json.dumps({"prompt": "x", "completion": "y"}) + "\n")
    monkeypatch.setattr(train_module, "TRAIN_FILE", real)
    # Should not raise.
    train_module.require_data_file()
