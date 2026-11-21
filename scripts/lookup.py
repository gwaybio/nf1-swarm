#!/usr/bin/env python3
"""
Point-query CLI for the nf1-swarm SQLite lookup layer (data/swarm.db).

Agents call this to check paper status, claim existence, and contract
validity WITHOUT loading full JSON files into context. Output is compact
JSON — a few hundred bytes, never full claim text.

The DB is auto-rebuilt if missing or stale (commit hash mismatch).

Usage:
    uv run python scripts/lookup.py paper <pmid|doi>
    uv run python scripts/lookup.py claims <pmid>
    uv run python scripts/lookup.py exists <pmid> <text_fragment>
    uv run python scripts/lookup.py valid-combo <claim_type> <evidence_type>
    uv run python scripts/lookup.py cited-by <pmid>
    uv run python scripts/lookup.py rebuild          # force full rebuild
"""
from __future__ import annotations

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


def _rebuild() -> None:
    from scripts.rebuild_db import build
    build()


# ── Queries ───────────────────────────────────────────────────────────────────

def cmd_paper(args: list[str]) -> dict:
    """lookup.py paper <pmid|doi> — paper status, issue, claim count."""
    if not args:
        return {"error": "usage: lookup.py paper <pmid|doi>"}
    key = args[0]
    con = _ensure_db()
    if key.startswith("10."):
        row = con.execute(
            "SELECT * FROM papers WHERE doi=?", (key,)
        ).fetchone()
    else:
        row = con.execute(
            "SELECT * FROM papers WHERE pmid=?", (key,)
        ).fetchone()
    con.close()
    if not row:
        return {"found": False, "pmid": key}
    claim_ids = json.loads(row["claim_ids"]) if row["claim_ids"] else []
    return {
        "found":        True,
        "pmid":         row["pmid"],
        "doi":          row["doi"],
        "title":        row["title"],
        "year":         row["year"],
        "status":       row["status"],
        "issue_number": row["issue_number"],
        "source_type":  row["source_type"],
        "claim_count":  len(claim_ids),
        "claim_ids":    claim_ids,
    }


def cmd_claims(args: list[str]) -> dict:
    """lookup.py claims <pmid> — claim IDs and statuses for a paper."""
    if not args:
        return {"error": "usage: lookup.py claims <pmid>"}
    pmid = args[0]
    con = _ensure_db()
    rows = con.execute(
        """SELECT pending_id, claim_id, claim_type, subject_id, predicate,
                  object_id, status
           FROM claims WHERE source_pmid=?
           ORDER BY claim_id NULLS LAST, pending_id""",
        (pmid,)
    ).fetchall()
    con.close()
    return {
        "pmid":   pmid,
        "count":  len(rows),
        "claims": [
            {
                "id":        r["claim_id"] or r["pending_id"],
                "claim_type": r["claim_type"],
                "triple":    f"{r['subject_id']} {r['predicate']} {r['object_id']}",
                "status":    r["status"],
            }
            for r in rows
        ],
    }


def cmd_exists(args: list[str]) -> dict:
    """lookup.py exists <pmid> <text_fragment> — dedup check by PMID + text."""
    if len(args) < 2:
        return {"error": "usage: lookup.py exists <pmid> <text_fragment>"}
    pmid, fragment = args[0], " ".join(args[1:]).lower()
    con = _ensure_db()
    # Check by triple fragment (subject or predicate or object contains text)
    rows = con.execute(
        """SELECT claim_id, pending_id, status FROM claims
           WHERE source_pmid=?
             AND (lower(subject_id) LIKE ? OR lower(predicate) LIKE ?
                  OR lower(object_id) LIKE ?)""",
        (pmid, f"%{fragment}%", f"%{fragment}%", f"%{fragment}%"),
    ).fetchall()
    con.close()
    return {
        "pmid":     pmid,
        "fragment": fragment,
        "exists":   len(rows) > 0,
        "matches":  [
            {"id": r["claim_id"] or r["pending_id"], "status": r["status"]}
            for r in rows
        ],
    }


def cmd_valid_combo(args: list[str]) -> dict:
    """lookup.py valid-combo <claim_type> <evidence_type> — pre-flight check."""
    if len(args) < 2:
        return {"error": "usage: lookup.py valid-combo <claim_type> <evidence_type>"}
    claim_type, evidence_type = args[0], args[1]
    con = _ensure_db()
    row = con.execute(
        """SELECT min_strength, max_strength FROM contract_rules
           WHERE claim_type=? AND evidence_type=?""",
        (claim_type, evidence_type),
    ).fetchone()
    con.close()
    if not row:
        return {"valid": False, "claim_type": claim_type,
                "evidence_type": evidence_type,
                "reason": "combination not found in claim_contract.yaml"}
    return {"valid": True, "claim_type": claim_type,
            "evidence_type": evidence_type,
            "min_strength": row["min_strength"],
            "max_strength": row["max_strength"]}


def cmd_cited_by(args: list[str]) -> dict:
    """lookup.py cited-by <pmid> — which reviews cite this paper."""
    if not args:
        return {"error": "usage: lookup.py cited-by <pmid>"}
    pmid = args[0]
    con = _ensure_db()
    rows = con.execute(
        """SELECT cr.source_pmid, p.title, cr.review_count, cr.status
           FROM cited_references cr
           LEFT JOIN papers p ON p.pmid = cr.source_pmid
           WHERE cr.cited_pmid=?
           ORDER BY cr.review_count DESC""",
        (pmid,),
    ).fetchall()
    con.close()
    return {
        "cited_pmid": pmid,
        "cited_by": [
            {"review_pmid": r["source_pmid"], "title": r["title"],
             "review_count": r["review_count"], "status": r["status"]}
            for r in rows
        ],
    }


# ── Main ──────────────────────────────────────────────────────────────────────

COMMANDS = {
    "paper":       cmd_paper,
    "claims":      cmd_claims,
    "exists":      cmd_exists,
    "valid-combo": cmd_valid_combo,
    "cited-by":    cmd_cited_by,
}


def main() -> int:
    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0

    if argv[0] == "rebuild":
        _rebuild()
        return 0

    cmd = argv[0]
    if cmd not in COMMANDS:
        print(json.dumps({"error": f"unknown command {cmd!r}",
                          "available": list(COMMANDS)}))
        return 1

    result = COMMANDS[cmd](argv[1:])
    print(json.dumps(result, indent=2))
    return 1 if "error" in result else 0


if __name__ == "__main__":
    sys.exit(main())
