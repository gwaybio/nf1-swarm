#!/usr/bin/env python3
"""
Bibliography lookup CLI — data/swarm.db (papers only).

Agents call this to check paper status before opening a new reading issue,
without loading GitHub issues or large markdown files into context.
Output is compact JSON — a few hundred bytes.

The DB is auto-rebuilt if missing or stale (commit hash mismatch).
Claim data lives in Neo4j, not here.

Usage:
    uv run python scripts/lookup.py --pmid 32187457
    uv run python scripts/lookup.py --doi 10.1056/NEJMoa1912735
    uv run python scripts/lookup.py --status queued
    uv run python scripts/lookup.py --rebuild
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DB_PATH   = REPO_ROOT / "data" / "swarm.db"


# ── DB management ─────────────────────────────────────────────────────────────

def _git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT, text=True
        ).strip()
    except Exception:
        return "unknown"


def _db_is_fresh(con: sqlite3.Connection) -> bool:
    try:
        row = con.execute("SELECT value FROM meta WHERE key='commit'").fetchone()
        return row is not None and row[0] == _git_head()
    except sqlite3.OperationalError:
        return False


def _rebuild() -> None:
    import sys as _sys
    _sys.path.insert(0, str(REPO_ROOT))
    from scripts.rebuild_db import build  # noqa: PLC0415
    build()


def _ensure_db() -> sqlite3.Connection:
    if not DB_PATH.exists():
        _rebuild()
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    if not _db_is_fresh(con):
        con.close()
        _rebuild()
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
    return con


# ── Queries ───────────────────────────────────────────────────────────────────

def _row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "found":        True,
        "pmid":         row["pmid"],
        "doi":          row["doi"],
        "title":        row["title"],
        "year":         row["year"],
        "journal":      row["journal"],
        "status":       row["status"],
        "issue_number": row["issue_number"],
        "source_type":  row["source_type"],
    }


def lookup_pmid(pmid: str) -> dict:
    con = _ensure_db()
    row = con.execute("SELECT * FROM papers WHERE pmid=?", (pmid,)).fetchone()
    con.close()
    return _row_to_dict(row) if row else {"found": False, "pmid": pmid}


def lookup_doi(doi: str) -> dict:
    con = _ensure_db()
    row = con.execute("SELECT * FROM papers WHERE doi=?", (doi,)).fetchone()
    con.close()
    return _row_to_dict(row) if row else {"found": False, "doi": doi}


def lookup_status(status: str) -> dict:
    valid = ("queued", "in_progress", "done", "skipped")
    if status not in valid:
        return {"error": f"status must be one of {valid}"}
    con = _ensure_db()
    rows = con.execute(
        "SELECT pmid, doi, title, year, issue_number FROM papers WHERE status=? ORDER BY pmid",
        (status,)
    ).fetchall()
    con.close()
    return {
        "status": status,
        "count":  len(rows),
        "papers": [{"pmid": r["pmid"], "doi": r["doi"], "title": r["title"],
                    "year": r["year"], "issue_number": r["issue_number"]}
                   for r in rows],
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--pmid",    metavar="PMID",   help="Look up by PubMed ID")
    group.add_argument("--doi",     metavar="DOI",    help="Look up by DOI")
    group.add_argument("--status",  metavar="STATUS",
                       help="List papers by status (queued|in_progress|done|skipped)")
    group.add_argument("--rebuild", action="store_true",
                       help="Force a full DB rebuild from GitHub issues + queue.md")

    args = p.parse_args()

    if args.rebuild:
        _rebuild()
        return 0

    if args.pmid:
        result = lookup_pmid(args.pmid)
    elif args.doi:
        result = lookup_doi(args.doi)
    else:
        result = lookup_status(args.status)

    print(json.dumps(result, indent=2))
    return 1 if "error" in result else 0


if __name__ == "__main__":
    sys.exit(main())
