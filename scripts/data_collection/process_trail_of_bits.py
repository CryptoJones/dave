#!/usr/bin/env python3
"""
Extract findings from Trail of Bits public security reviews.
Source:  trailofbits/publications (CC-BY-SA 4.0)
Input:   $DAVE_DATA_DIR/raw_github/publications/reviews/*.pdf
Output:  $DAVE_DATA_DIR/processed/free_sources/trail_of_bits_training.jsonl

Each report contains numbered findings with consistent structure:

    N. <Title>

     Severity: <S>            Difficulty: <D>
     Type: <T>                Finding ID: TOB-XXX-N
     Target: <files>

    Description
    <body>

    Recommendations
    Short term, ...
    Long term, ...

We parse each finding, emit several prompt/completion pairs covering finding
narrative, description, recommendations, and classification. Smart-contract /
web3 findings are filtered out per project policy.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

DAVE_DATA_DIR = Path(os.environ.get("DAVE_DATA_DIR", str(Path.cwd() / "data")))
INPUT_DIR = DAVE_DATA_DIR / "raw_github" / "publications" / "reviews"
OUTPUT_DIR = DAVE_DATA_DIR / "processed" / "free_sources"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "trail_of_bits_training.jsonl"

ATTRIBUTION = (
    "Source material: Trail of Bits public security reviews "
    "(github.com/trailofbits/publications), licensed CC-BY-SA 4.0."
)

# Web3 / smart-contract terms — findings mentioning these are skipped so Dave
# stays general-purpose (the user does not want a blockchain-skewed model).
WEB3_TERMS = re.compile(
    r"\b(?:solidity|smart contract[s]?|erc-?20|erc-?721|erc-?1155|"
    r"reentran(?:cy|t)|evm\b|oracle manipulation|slippage|liquidity pool[s]?|"
    r"uniswap|aave|compound finance|defi\b|ethereum|blockchain[s]?|"
    r"on[- ]chain|off[- ]chain|gas refund|sandwich attack|"
    r"flash loan[s]?|tokenomics|mev\b|stablecoin[s]?|nft[s]?\b|"
    r"web3\b|wallet contract|proxy contract|multisig contract|"
    r"governance token|yield farm|amm\b|cosmwasm|cairo lang|vyper)",
    re.IGNORECASE,
)

# Invisible / format characters that older + newer ToB PDFs sometimes embed
# inside headers (zero-width spaces, bidi controls, BOM, soft hyphens).
# Stripping them lets a single regex handle every report format we've seen.
_INVISIBLES = re.compile(
    "["
    "​-‏"   # ZWSP, ZWNJ, ZWJ, LRM, RLM
    "‪-‮"   # LRE, RLE, PDF, LRO, RLO
    "⁠-⁤"   # WJ + invisible operators
    "⁦-⁩"   # LRI, RLI, FSI, PDI
    "﻿"          # BOM / zero-width no-break space
    "­"          # soft hyphen
    "]"
)

# Header of a finding section. Anchor on a line that begins with "N." and
# allow the title to wrap across multiple lines until the (optional) blank
# line before "Severity:". The Severity / Difficulty / Type / Finding-ID
# block almost never appears together outside the Detailed Findings chapter,
# so false positives are negligible.
FINDING_HEADER_RE = re.compile(
    r"^[ \t]*(\d{1,3})\.[ \t]+(.{4,400}?)\n\s*\n?"
    r"[ \t]*Severity:[ \t]*([^\n]+?)\s+Difficulty:[ \t]*([^\n]+?)\s*\n+"
    r"[ \t]*Type:[ \t]*([^\n]+?)\s+Finding ID:[ \t]*(TOB-[A-Z0-9-]+)\s*\n+"
    r"(?:[ \t]*Target:[ \t]*([^\n]+)\s*\n+)?",
    re.MULTILINE | re.DOTALL,
)

# Lines that mark the end of a finding body (page footers).
PAGE_FOOTER_RE = re.compile(
    r"^\s*Trail of Bits\s+\d+\s+.+(?:Security|Assessment|Review).*$\s*"
    r"^\s*CONFIDENTIAL.*$",
    re.MULTILINE,
)


def pdf_to_text(pdf_path: Path) -> str:
    try:
        out = subprocess.run(
            ["pdftotext", "-layout", str(pdf_path), "-"],
            capture_output=True, text=True, timeout=60, check=True,
        )
        text = out.stdout
        # pdftotext emits form-feed (\x0c) at page boundaries, which breaks
        # line-anchored regexes when a finding header lands at the top of a
        # new page. Strip them. Also strip invisible format chars that some
        # reports embed inside the Severity/Difficulty/Type/Target lines.
        text = text.replace("\x0c", "")
        text = _INVISIBLES.sub("", text)
        return text
    except subprocess.TimeoutExpired:
        return ""
    except subprocess.CalledProcessError:
        return ""


def clean_finding_body(text: str) -> str:
    text = PAGE_FOOTER_RE.sub("\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_description_recommendations(body: str) -> tuple[str, str]:
    """Find the 'Recommendations' header and split."""
    parts = re.split(r"\n\s*Recommendations\s*\n", body, maxsplit=1)
    description = parts[0]
    recommendations = parts[1] if len(parts) == 2 else ""

    # Strip leading "Description" header if present.
    description = re.sub(r"^\s*Description\s*\n+", "", description)

    return description.strip(), recommendations.strip()


def is_web3(*chunks: str) -> bool:
    return any(WEB3_TERMS.search(c or "") for c in chunks)


def extract_findings(text: str) -> list[dict]:
    """Parse all findings from one report's text."""
    findings = []
    matches = list(FINDING_HEADER_RE.finditer(text))
    for i, m in enumerate(matches):
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[body_start:body_end]
        body = clean_finding_body(body)

        # The Summary of Findings table lists findings without full bodies —
        # require enough body content to skip those stubs.
        if len(body) < 200:
            continue

        description, recommendations = split_description_recommendations(body)

        title = re.sub(r"\s+", " ", m.group(2)).strip().rstrip(".")
        findings.append({
            "number": m.group(1),
            "title": title,
            "severity": m.group(3).strip(),
            "difficulty": m.group(4).strip(),
            "type": m.group(5).strip(),
            "finding_id": m.group(6).strip(),
            "target": (m.group(7) or "").strip(),
            "description": description,
            "recommendations": recommendations,
        })
    return findings


def make_pairs(f: dict) -> list[dict]:
    """Build prompt/completion pairs from one finding."""
    title = f["title"]
    sev = f["severity"]
    diff = f["difficulty"]
    typ = f["type"]
    desc = f["description"]
    recs = f["recommendations"]

    structured = (
        f"Finding: {title}\n"
        f"Severity: {sev}\n"
        f"Difficulty: {diff}\n"
        f"Type: {typ}\n\n"
        f"Description:\n{desc}"
    )
    if recs:
        structured += f"\n\nRecommendations:\n{recs}"
    structured += f"\n\n{ATTRIBUTION}"

    pairs = [
        {
            "prompt": f"Write a professional vulnerability finding titled \"{title}\" "
                      f"for inclusion in a security assessment report. "
                      f"Severity is {sev}; difficulty to exploit is {diff}; category is {typ}.",
            "completion": structured,
        },
        {
            "prompt": f"Describe the technical issue behind the finding: \"{title}\".",
            "completion": desc + f"\n\n{ATTRIBUTION}",
        },
    ]
    if recs:
        pairs.append({
            "prompt": f"Write the remediation recommendations for the finding: \"{title}\".",
            "completion": recs + f"\n\n{ATTRIBUTION}",
        })
    pairs.append({
        "prompt": f"Classify the following security finding and assign a severity and "
                  f"exploitation difficulty: \"{title}\". Context: {desc[:400]}",
        "completion": (
            f"Category: {typ}\nSeverity: {sev}\nDifficulty to exploit: {diff}\n\n"
            f"This finding is classified as {typ.lower()} because the underlying issue "
            f"concerns that domain. The {sev.lower()} severity and {diff.lower()} difficulty "
            f"are assigned based on impact and exploitability as described in the report.\n\n"
            f"{ATTRIBUTION}"
        ),
    })
    return pairs


def main() -> None:
    if not INPUT_DIR.exists():
        sys.exit(f"ERROR: {INPUT_DIR} not found. Clone trailofbits/publications first.")

    pdfs = sorted(INPUT_DIR.glob("*.pdf"))
    if not pdfs:
        sys.exit(f"ERROR: no PDFs in {INPUT_DIR}")

    print(f"Processing {len(pdfs)} Trail of Bits reports...")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Web3 filter: ON (smart-contract findings will be skipped)")
    print()

    total_findings = 0
    web3_skipped = 0
    pairs_written = 0
    reports_with_findings = 0
    reports_zero = 0
    errors = 0

    with OUTPUT_FILE.open("w", encoding="utf-8") as out:
        for i, pdf in enumerate(pdfs, 1):
            try:
                text = pdf_to_text(pdf)
                if not text:
                    continue
                findings = extract_findings(text)
                if not findings:
                    reports_zero += 1
                    continue
                reports_with_findings += 1

                for f in findings:
                    if is_web3(f["title"], f["description"],
                               f["recommendations"], f["type"]):
                        web3_skipped += 1
                        continue
                    total_findings += 1
                    for pair in make_pairs(f):
                        out.write(json.dumps(pair) + "\n")
                        pairs_written += 1
            except Exception as e:
                errors += 1
                if errors <= 3:
                    print(f"  error on {pdf.name}: {type(e).__name__}: {e}")
                continue

            if i % 25 == 0:
                print(f"  [{i}/{len(pdfs)}] kept {total_findings} findings, "
                      f"web3-skipped {web3_skipped}, pairs={pairs_written}")

    print()
    print(f"Reports processed:           {len(pdfs)}")
    print(f"Reports with findings:       {reports_with_findings}")
    print(f"Reports with zero findings:  {reports_zero}")
    print(f"Findings kept (post-web3):   {total_findings}")
    print(f"Findings web3-skipped:       {web3_skipped}")
    print(f"Training pairs written:      {pairs_written}")
    print(f"Errors:                      {errors}")
    print(f"Output file:                 {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
