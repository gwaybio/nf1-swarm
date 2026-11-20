#!/usr/bin/env python3
"""Update the README.md swarm-progress stats block and regenerate claims/provenance.csv.

Sources of truth:
  - Accepted/pending claim counts: filesystem (claims/accepted/*.json, claims/pending/*.json)
  - Papers processed: unique source_pmid / source_doi values across ALL claim files
    (ground truth — derived from the claims themselves, not from queue.md)
  - Provenance: claims/provenance.csv maps each paper to the claims it generated

Usage:
    cd ~/repos/nf1-swarm && uv run python scripts/update_stats.py
"""
import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT       = Path(__file__).parent.parent
README          = REPO_ROOT / "README.md"
CLAIMS_ACCEPTED = REPO_ROOT / "claims" / "accepted"
CLAIMS_PENDING  = REPO_ROOT / "claims" / "pending"
PROVENANCE_CSV  = REPO_ROOT / "claims" / "provenance.csv"


def load_all_claims() -> list[dict]:
    """Load every claim JSON from accepted/ and pending/."""
    claims = []
    for directory in (CLAIMS_ACCEPTED, CLAIMS_PENDING):
        for f in sorted(directory.glob("*.json")):
            try:
                claims.append(json.loads(f.read_text()))
            except json.JSONDecodeError:
                pass
    return claims


def count_json(directory: Path) -> int:
    return sum(1 for _ in directory.glob("*.json"))


def build_provenance(claims: list[dict]) -> list[tuple[str, str, str]]:
    """Return rows for ACCEPTED claims only: (source_pmid, source_doi, claim_id)."""
    rows = [
        (
            c.get("source_pmid") or "",
            c.get("source_doi") or "",
            c.get("claim_id", ""),
        )
        for c in claims
        if c.get("status") == "accepted"
    ]
    return sorted(rows, key=lambda r: (r[0] or r[1], r[2]))


def unique_papers(provenance: list[tuple]) -> int:
    """Count distinct papers by PMID (preferred) or DOI."""
    seen: set[str] = set()
    for pmid, doi, *_ in provenance:
        seen.add(pmid if pmid else doi)
    return len(seen)


def write_provenance(rows: list[tuple]) -> None:
    with open(PROVENANCE_CSV, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(["source_pmid", "source_doi", "claim_id"])
        writer.writerows(rows)


def build_stats_block(accepted: int, pending: int, papers: int, updated: str) -> str:
    return (
        "<!-- STATS_START -->\n"
        "| 🧬 Accepted claims | ⏳ Pending claims | 📄 Papers processed | 🕐 Updated |\n"
        "|:-----------------:|:-----------------:|:-------------------:|:----------:|\n"
        f"| {accepted} | {pending} | {papers} | {updated} |\n"
        "<!-- STATS_END -->"
    )


def main() -> int:
    text = README.read_text()
    if "<!-- STATS_START -->" not in text or "<!-- STATS_END -->" not in text:
        print("ERROR: README.md missing <!-- STATS_START --> / <!-- STATS_END --> anchors",
              file=sys.stderr)
        return 1

    claims     = load_all_claims()
    provenance = build_provenance(claims)
    write_provenance(provenance)

    accepted = count_json(CLAIMS_ACCEPTED)
    pending  = count_json(CLAIMS_PENDING)
    papers   = unique_papers(provenance)
    updated  = datetime.now(timezone.utc).strftime("%Y-%m-%d UTC")

    new_block = build_stats_block(accepted, pending, papers, updated)
    new_text  = re.sub(
        r"<!-- STATS_START -->.*?<!-- STATS_END -->",
        new_block,
        text,
        flags=re.DOTALL,
    )

    README.write_text(new_text)
    print(f"README: accepted={accepted} pending={pending} papers={papers} date={updated}")
    print(f"Provenance: {len(provenance)} rows → {PROVENANCE_CSV}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
