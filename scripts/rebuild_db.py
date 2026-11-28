#!/usr/bin/env python3
"""
Rebuild data/swarm.db — papers-only bibliography index.

Sources (in order of precedence):
  1. Open/closed GitHub issues with label 'paper' (live status from tracker)
  2. literature/queue.md (local queue entries)

Neo4j is the claim store. This DB covers only paper-level status so agents
can answer "has this paper been read?" without scanning GitHub issues.

Run after any `git pull` that changes literature/ files, or on `git push`.
Called automatically by lookup.py when the DB is missing or stale.

Usage:
    cd ~/repos/nf1-swarm && uv run python scripts/rebuild_db.py
"""
from __future__ import annotations

import json
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import idutils

REPO_ROOT = Path(__file__).parent.parent
DB_PATH   = REPO_ROOT / "data" / "swarm.db"
QUEUE_MD  = REPO_ROOT / "literature" / "queue.md"


# ── Schema ────────────────────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS papers (
    pmid           TEXT PRIMARY KEY,
    doi            TEXT UNIQUE,  -- NULL ok; SQLite allows multiple NULLs in UNIQUE cols
    title          TEXT,
    year           INTEGER,
    journal        TEXT,
    status         TEXT DEFAULT 'queued'
                   CHECK(status IN ('queued','in_progress','done','skipped')),
    issue_number   INTEGER,
    source_type    TEXT DEFAULT 'primary'
                   CHECK(source_type IN ('primary','review','review_extraction')),
    processed_date TEXT
);

CREATE INDEX IF NOT EXISTS idx_papers_status ON papers(status);
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


def _queue_md_entries() -> list[dict]:
    """Parse literature/queue.md → list of paper dicts."""
    if not QUEUE_MD.exists():
        return []
    papers = []
    for line in QUEUE_MD.read_text().splitlines():
        # Lines: - `[DONE]` Title — PMID:2116237 (DOI:...) — issue #14
        m_status = re.search(r'\[(\w+)\]', line)
        if not m_status:
            continue
        status_raw = m_status.group(1).upper()
        status = {"DONE": "done", "PENDING": "queued",
                  "IN_PROGRESS": "in_progress", "SKIPPED": "skipped"
                  }.get(status_raw, "queued")
        m_pmid  = re.search(r'PMID:(\d+)', line)
        doi_m   = re.search(r'DOI:(10\.\S+)', line)
        if not m_pmid and not doi_m:  # require at least one identifier
            continue
        pmid    = idutils.normalize_pmid(m_pmid.group(1)) if m_pmid else None
        doi_raw = doi_m.group(1).rstrip(");,") if doi_m else None
        doi     = (idutils.normalize_doi(doi_raw)
                   if doi_raw and idutils.is_doi(doi_raw) else None)
        issue_m = re.search(r'issue #(\d+)', line)
        issue   = int(issue_m.group(1)) if issue_m else None
        papers.append({"pmid": pmid, "doi": doi, "status": status,
                       "issue_number": issue, "source_type": "primary"})
    return papers


def _github_issues() -> list[dict]:
    """Fetch paper issues from GitHub via gh CLI (open + closed)."""
    papers = []
    LIMIT = 500  # per-state; warn if we hit this
    for state in ("open", "closed"):
        try:
            raw = subprocess.check_output(
                ["gh", "issue", "list",
                 "--repo", "gwaybio/nf1-swarm",
                 "--label", "paper",
                 "--state", state,
                 "--limit", str(LIMIT),
                 "--json", "number,title,body,state"],
                text=True, timeout=30
            )
        except (subprocess.CalledProcessError, FileNotFoundError,
                subprocess.TimeoutExpired) as exc:
            # Hard fail — a partial index is worse than an empty one
            print(f"WARNING: gh issue list failed for state={state}: {exc}",
                  file=sys.stderr)
            raise RuntimeError(f"GitHub issues fetch failed: {exc}") from exc
        issues = json.loads(raw)
        if len(issues) >= LIMIT:
            print(f"WARNING: gh issue list returned {LIMIT} issues for state={state} "
                  f"— results may be truncated; raise LIMIT in rebuild_db.py",
                  file=sys.stderr)
        for issue in issues:
            num   = issue["number"]
            title = issue["title"]
            body  = issue.get("body") or ""
            # Try title first; fall back to scanning body for identifiers
            pmid_m = re.search(r'PMID:(\d+)', title) or re.search(r'PMID:(\d+)', body)
            doi_m  = re.search(r'DOI:(10\.\S+)', title) or re.search(r'DOI:(10\.\S+)', body)
            if not pmid_m and not doi_m:
                continue
            pmid = idutils.normalize_pmid(pmid_m.group(1)) if pmid_m else None
            doi_raw = doi_m.group(1).rstrip(");,") if doi_m else None
            # Validate DOI before normalising — idutils.is_doi prevents "pending" etc.
            doi = (idutils.normalize_doi(doi_raw)
                   if doi_raw and idutils.is_doi(doi_raw) else None)
            status = "done" if issue["state"] == "CLOSED" else "in_progress"
            papers.append({"pmid": pmid, "doi": doi, "title": title,
                           "status": status, "issue_number": num,
                           "source_type": "primary"})
    return papers


# ── Build ─────────────────────────────────────────────────────────────────────

def build(db_path: Path = DB_PATH) -> None:
    """
    Rebuild the database atomically, serialised by a lock file.

    Diagnostic output goes to stderr so automated callers (lookup.py)
    don't see it on stdout.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    lock = db_path.with_suffix(".rebuild.lock")

    import os

    def _lock_is_stale(p: Path) -> bool:
        try:
            pid = int(p.read_text().strip())
            os.kill(pid, 0)
            return False
        except (ValueError, FileNotFoundError, ProcessLookupError):
            return True
        except PermissionError:
            return False

    acquired = False
    try:
        with open(lock, 'x') as _f:   # O_CREAT|O_EXCL — atomic on POSIX
            _f.write(str(os.getpid()))
        acquired = True
    except FileExistsError:
        if _lock_is_stale(lock):
            lock.unlink(missing_ok=True)
            try:
                with open(lock, 'x') as _f:
                    _f.write(str(os.getpid()))
                acquired = True
            except FileExistsError:
                pass

    if not acquired:
        import time; time.sleep(0.5)
        return

    try:
        db_path.unlink(missing_ok=True)
        con = sqlite3.connect(db_path)
        con.executescript(SCHEMA)

        now = datetime.now(timezone.utc).isoformat()
        con.execute("INSERT OR REPLACE INTO meta VALUES (?,?)", ("commit", _git_head()))
        con.execute("INSERT OR REPLACE INTO meta VALUES (?,?)", ("rebuilt_at", now))

        # queue.md first (lower precedence — IGNORE on conflict)
        for p in _queue_md_entries():
            pmid, doi = p.get("pmid"), p.get("doi")
            if pmid:
                con.execute("""
                    INSERT OR IGNORE INTO papers
                        (pmid, doi, status, issue_number, source_type, processed_date)
                    VALUES (?,?,?,?,?,?)
                """, (pmid, doi, p["status"], p.get("issue_number"),
                      p["source_type"], now))
            elif doi:
                con.execute("""
                    INSERT OR IGNORE INTO papers
                        (doi, status, issue_number, source_type, processed_date)
                    VALUES (?,?,?,?,?)
                """, (doi, p["status"], p.get("issue_number"),
                      p["source_type"], now))

        # GitHub issues (higher precedence — upsert status and issue_number)
        for p in _github_issues():
            if not p.get("pmid") and not p.get("doi"):
                continue
            if p.get("pmid"):
                con.execute("""
                    INSERT INTO papers
                        (pmid, doi, title, status, issue_number, source_type, processed_date)
                    VALUES (?,?,?,?,?,?,?)
                    ON CONFLICT(pmid) DO UPDATE SET
                        doi          = COALESCE(excluded.doi, doi),
                        title        = COALESCE(excluded.title, title),
                        status       = excluded.status,
                        issue_number = excluded.issue_number
                """, (p["pmid"], p.get("doi"), p.get("title"),
                      p["status"], p["issue_number"], p["source_type"], now))
            else:
                con.execute("""
                    INSERT INTO papers
                        (doi, title, status, issue_number, source_type, processed_date)
                    VALUES (?,?,?,?,?,?)
                    ON CONFLICT(doi) DO UPDATE SET
                        title        = COALESCE(excluded.title, title),
                        status       = excluded.status,
                        issue_number = excluded.issue_number
                """, (p["doi"], p.get("title"),
                      p["status"], p["issue_number"], p["source_type"], now))

        con.commit()
        paper_count = con.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
        con.close()
        # Diagnostics go to stderr — stdout stays clean JSON for callers
        print(f"Rebuilt {db_path} — {paper_count} papers, commit {_git_head()}",
              file=sys.stderr)
    finally:
        lock.unlink(missing_ok=True)


if __name__ == "__main__":
    build()
