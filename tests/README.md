# Dave Test Suite

```bash
pip install pytest
python3 -m pytest tests/                  # full run
python3 -m pytest tests/ -v -rs           # verbose, show skip reasons
python3 -m pytest tests/ -k web3          # filter by keyword
python3 -m pytest tests/ -m "not slow"    # exclude slow / subprocess tests
```

## Inventory

| File | Module under test | Coverage |
|---|---|---|
| `test_process_cisa_kev.py` | `process_cisa_kev` | `make_pairs` shape, metadata presence, skip-incomplete behavior |
| `test_process_dhs_cisa.py` | `process_dhs_cisa` | `make_bod_pairs`, `make_cert_alert_pairs`, fallback data validity |
| `test_process_mitre_attack.py` | `process_mitre_attack` | technique extraction, revoked-skip, defensive framing, description truncation |
| `test_process_nist.py` | `process_nist` | risk-level / likelihood coverage, control-pair extraction with statement prose |
| `test_process_trail_of_bits.py` | `process_trail_of_bits` | header regex (modern + old format + multi-line title), bidi/page-break stripping, web3 filter, attribution propagation |
| `test_process_books_nda_fixed.py` | `process_books_nda_fixed` | Py 3.13 regex compilation regression, chunk classification, real-content pair generation (not placeholders) |
| `test_train_dave.py` | `train_dave` | chat-template formatting, placeholder-row guard, data-file existence checks |

## Conventions

- **No network.** All processors that download upstream data are tested via
  hand-built input dicts in `conftest.py`. The `download_*()` functions are
  intentionally not exercised.
- **No subprocess.** `process_trail_of_bits.pdf_to_text` shells out to
  `pdftotext`; tests target the post-extraction pure functions instead.
- **Auto-skip for heavy deps.** Tests that need `torch`/`transformers` are
  guarded with a `pytest.skip` in their fixture so the dev-box suite passes.
- **Regression tests are labelled.** When a test exists to prevent a specific
  bug from coming back, its docstring names the bug. Don't delete those.

## Adding tests for a new processor

1. Drop a sample input fixture into `tests/conftest.py`.
2. Create `tests/test_process_<name>.py`.
3. Mirror the pattern: at least one shape test, one content test, one
   skip-on-incomplete test, and one "no placeholder strings" test.
