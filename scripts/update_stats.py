#!/usr/bin/env python3
"""Update the README.md swarm-progress stats block.

Reads live counts from the filesystem and rewrites the block between
<!-- STATS_START --> and <!-- STATS_END --> anchors in README.md.

Usage:
    cd ~/repos/nf1-swarm && uv run python scripts/update_stats.py
"""
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
README = REPO_ROOT / "README.md"
CLAIMS_ACCEPTED = REPO_ROOT / "claims" / "accepted"
CLAIMS_PENDING  = REPO_ROOT / "claims" / "pending"
PROCESSED_MD    = REPO_ROOT / "literature" / "processed.md"


def count_json(directory: Path) -> int:
    """Count *.json files, excluding .gitkeep."""
    return sum(1 for f in directory.glob("*.json"))


def count_processed_papers() -> int:
    """Count data rows in literature/processed.md (skip header + separator)."""
    if not PROCESSED_MD.exists():
        return 0
    rows = [
        ln for ln in PROCESSED_MD.read_text().splitlines()
        if ln.startswith("|") and not ln.startswith("| Paper") and not ln.startswith("|---")
    ]
    return len(rows)


def build_stats_block(accepted: int, pending: int, papers: int, updated: str) -> str:
    return (
        "<!-- STATS_START -->\n"
        "| 🧬 Accepted claims | ⏳ Pending | 📄 Papers processed | 🕐 Updated |\n"
        "|:-----------------:|:----------:|:-------------------:|:----------:|\n"
        f"| {accepted} | {pending} | {papers} | {updated} |\n"
        "<!-- STATS_END -->"
    )


def main() -> int:
    text = README.read_text()

    if "<!-- STATS_START -->" not in text or "<!-- STATS_END -->" not in text:
        print("ERROR: README.md is missing <!-- STATS_START --> / <!-- STATS_END --> anchors",
              file=sys.stderr)
        return 1

    accepted = count_json(CLAIMS_ACCEPTED)
    pending  = count_json(CLAIMS_PENDING)
    papers   = count_processed_papers()
    updated  = datetime.now(timezone.utc).strftime("%Y-%m-%d UTC")

    new_block = build_stats_block(accepted, pending, papers, updated)

    new_text = re.sub(
        r"<!-- STATS_START -->.*?<!-- STATS_END -->",
        new_block,
        text,
        flags=re.DOTALL,
    )

    if new_text == text:
        print("Stats unchanged — no commit needed.")
        return 0

    README.write_text(new_text)
    print(f"Updated: accepted={accepted} pending={pending} papers={papers} date={updated}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
