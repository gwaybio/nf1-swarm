#!/usr/bin/env python3
"""
Rebuild data/swarm.db from the canonical sources in this repo.

Run after any `git pull` that changes claims/ or literature/ files.
Called automatically by lookup.py when the DB is missing or stale.

Usage:
    cd ~/repos/nf1-swarm && uv run python scripts/rebuild_db.py
"""
from __future__ import annotations

import json
import re
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DB_PATH   = REPO_ROOT / "data" / "swarm.db"

CLAIMS_DIRS = [
    REPO_ROOT / "claims" / "accepted",
    REPO_ROOT / "claims" / "pending",
    REPO_ROOT / "claims" / "rejected",
]
QUEUE_MD    = REPO_ROOT / "literature" / "queue.md"
CONTRACT    = REPO_ROOT / "testing" / "specs" / "claim_contract.yaml"
RUBRIC      = REPO_ROOT / "testing" / "specs" / "evidence_rubric.yaml"


# ── Schema ────────────────────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS papers (
    pmid            TEXT PRIMARY KEY,
    doi             TEXT,
    title           TEXT,
    year            INTEGER,
    journal         TEXT,
    status          TEXT DEFAULT 'queued',
    issue_number    INTEGER,
    source_type     TEXT DEFAULT 'primary',
    grounding_hints TEXT,  -- JSON blob for Otto's CURIEs
    claim_ids       TEXT,  -- JSON array of resulting claim IDs
    updated_at      TEXT
);

CREATE TABLE IF NOT EXISTS claims (
    pending_id  TEXT,
    claim_id    TEXT,
    claim_type  TEXT,
    subject_id  TEXT,
    predicate   TEXT,
    object_id   TEXT,
    source_pmid TEXT,
    status      TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_claims_pk
    ON claims(COALESCE(pending_id, claim_id));
CREATE INDEX IF NOT EXISTS idx_claims_triple
    ON claims(subject_id, predicate, object_id);
CREATE INDEX IF NOT EXISTS idx_claims_pmid
    ON claims(source_pmid);

CREATE TABLE IF NOT EXISTS cited_references (
    source_pmid TEXT,
    cited_pmid  TEXT,
    review_count INTEGER DEFAULT 1,
    status       TEXT DEFAULT 'queued',
    PRIMARY KEY (source_pmid, cited_pmid)
);

CREATE TABLE IF NOT EXISTS contract_rules (
    claim_type    TEXT,
    evidence_type TEXT,
    min_strength  INTEGER,
    max_strength  INTEGER DEFAULT 5,
    PRIMARY KEY (claim_type, evidence_type)
);
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT, text=True
        ).strip()
    except Exception:
        return "unknown"


def _load_claim_files() -> list[dict]:
    claims = []
    for d in CLAIMS_DIRS:
        for f in d.glob("*.json"):
            if f.stat().st_size < 50:
                continue
            try:
                claims.append(json.loads(f.read_text()))
            except json.JSONDecodeError:
                pass
    return claims


def _queue_md_papers() -> list[dict]:
    """Parse literature/queue.md for paper entries."""
    if not QUEUE_MD.exists():
        return []
    papers = []
    for line in QUEUE_MD.read_text().splitlines():
        m = re.search(r'\[(\w+)\].*PMID:(\d+)', line)
        if not m:
            continue
        status_raw, pmid = m.group(1).lower(), m.group(2)
        status = {"done": "done", "pending": "queued", "in_progress": "in_progress",
                  "skipped": "skipped"}.get(status_raw, "queued")
        doi_m = re.search(r'DOI:(\S+)\)', line)
        doi = doi_m.group(1).rstrip(")") if doi_m else None
        issue_m = re.search(r'issue #(\d+)', line)
        issue_num = int(issue_m.group(1)) if issue_m else None
        papers.append({"pmid": pmid, "doi": doi, "status": status,
                       "issue_number": issue_num, "source_type": "primary"})
    return papers


def _load_contract_rules() -> list[tuple]:
    """Extract (claim_type, evidence_type, min_strength) from contract YAML."""
    try:
        import yaml
    except ImportError:
        return []
    if not CONTRACT.exists():
        return []
    spec = yaml.safe_load(CONTRACT.read_text())
    rows = []
    for ctype, rules in spec.get("claim_types", {}).items():
        min_s = rules.get("min_evidence_strength", 1)
        for etype in rules.get("allowed_evidence_types", []):
            rows.append((ctype, etype, min_s, 5))
    return rows


# ── Build ─────────────────────────────────────────────────────────────────────

def build(db_path: Path = DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.unlink(missing_ok=True)

    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA)

    # --- meta ---
    con.execute("INSERT OR REPLACE INTO meta VALUES (?,?)", ("commit", _git_head()))
    con.execute("INSERT OR REPLACE INTO meta VALUES (?,?)",
                ("rebuilt_at", datetime.now(timezone.utc).isoformat()))

    # --- papers from queue.md ---
    for p in _queue_md_papers():
        con.execute("""
            INSERT OR IGNORE INTO papers
                (pmid, doi, status, issue_number, source_type, updated_at)
            VALUES (?,?,?,?,?,?)
        """, (p["pmid"], p.get("doi"), p["status"],
              p.get("issue_number"), p["source_type"],
              datetime.now(timezone.utc).isoformat()))

    # --- claims + backfill papers from claim files ---
    all_claims = _load_claim_files()
    paper_claim_ids: dict[str, list[str]] = {}

    for c in all_claims:
        pid  = c.get("pending_id")
        cid  = c.get("claim_id")
        pmid = c.get("source_pmid") or ""
        triple = c.get("semantic_triple") or {}

        con.execute("""
            INSERT OR IGNORE INTO claims
                (pending_id, claim_id, claim_type, subject_id, predicate,
                 object_id, source_pmid, status)
            VALUES (?,?,?,?,?,?,?,?)
        """, (pid, cid, c.get("claim_type"),
              triple.get("subject_id"), triple.get("predicate"),
              triple.get("object_id"), pmid, c.get("status", "pending")))

        # ensure paper row exists (may not be in queue.md yet)
        if pmid:
            con.execute("""
                INSERT OR IGNORE INTO papers (pmid, status, updated_at)
                VALUES (?,?,?)
            """, (pmid, "done", datetime.now(timezone.utc).isoformat()))

            if cid and c.get("status") == "accepted":
                paper_claim_ids.setdefault(pmid, []).append(cid)

    # --- backfill claim_ids JSON on papers ---
    for pmid, ids in paper_claim_ids.items():
        con.execute("UPDATE papers SET claim_ids=? WHERE pmid=?",
                    (json.dumps(sorted(ids)), pmid))

    # --- contract rules ---
    for row in _load_contract_rules():
        con.execute("""
            INSERT OR REPLACE INTO contract_rules
                (claim_type, evidence_type, min_strength, max_strength)
            VALUES (?,?,?,?)
        """, row)

    con.commit()
    con.close()

    claim_count = len(all_claims)
    paper_count = len(_queue_md_papers())
    print(f"Rebuilt {db_path} — {paper_count} papers, {claim_count} claims, "
          f"commit {_git_head()}")


if __name__ == "__main__":
    build()
