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
import os
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
LOCK_WAIT_SECONDS = 60   # max time a caller waits for a concurrent rebuild


# ── Schema ────────────────────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS papers (
    pmid           TEXT PRIMARY KEY,
    -- DOIs are case-insensitive; NOCASE makes lookups and UNIQUE case-insensitive
    -- while keeping the original case for display. NULL allowed (multiple NULLs ok).
    doi            TEXT UNIQUE COLLATE NOCASE,
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
        doi     = _clean_doi(doi_m.group(1)) if doi_m else None
        issue_m = re.search(r'issue #(\d+)', line)
        issue   = int(issue_m.group(1)) if issue_m else None
        papers.append({"pmid": pmid, "doi": doi, "status": status,
                       "issue_number": issue, "source_type": "primary"})
    return papers


def _clean_doi(raw: str | None) -> str | None:
    """Strip wrapping punctuation, keep balanced parentheses, validate, normalise."""
    if not raw:
        return None
    raw = raw.rstrip(",;")
    while raw.endswith(")") and raw.count("(") < raw.count(")"):
        raw = raw[:-1]
    return idutils.normalize_doi(raw) if idutils.is_doi(raw) else None


# Issue-form bodies render as "### PMID\n\n32187458\n\n### DOI\n\n10.x/y"
# (blank optional fields render as "_No response_").
_FORM_PMID = re.compile(r"^###[ \t]*PMID[ \t]*\n+[ \t]*(\d+)[ \t]*$", re.M)
_FORM_DOI  = re.compile(r"^###[ \t]*DOI[ \t]*\n+[ \t]*(10\.\S+)[ \t]*$", re.M)


def _fetch_paper_issues() -> list[dict]:
    """All issues labelled 'paper' (open + closed), fully paginated, PRs excluded.

    Uses the REST API with --paginate so there is no result cap to truncate at.
    Any failure raises: a partial import must never be published as complete.
    """
    try:
        raw = subprocess.check_output(
            ["gh", "api", "--paginate",
             "repos/gwaybio/nf1-swarm/issues?labels=paper&state=all&per_page=100",
             "--jq",
             ".[] | select(.pull_request | not) | {number, title, body, state}"],
            text=True, timeout=120,
        )
    except (subprocess.CalledProcessError, FileNotFoundError,
            subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"GitHub issues fetch failed: {exc}") from exc
    return [json.loads(line) for line in raw.splitlines() if line.strip()]


def _github_issues() -> list[dict]:
    """Paper issues -> rows. Identifiers come from the title (inline
    'PMID:123 DOI:10.x') or from the issue-form body ('### PMID' / '### DOI')."""
    papers = []
    for issue in _fetch_paper_issues():
        title = issue["title"]
        body = issue.get("body") or ""
        pmid_m = (re.search(r"PMID:(\d+)", title) or _FORM_PMID.search(body)
                  or re.search(r"PMID:(\d+)", body))
        doi_m = (re.search(r"DOI:(10\.\S+)", title) or _FORM_DOI.search(body)
                 or re.search(r"DOI:(10\.\S+)", body))
        if not pmid_m and not doi_m:
            continue
        pmid = idutils.normalize_pmid(pmid_m.group(1)) if pmid_m else None
        doi = _clean_doi(doi_m.group(1)) if doi_m else None
        status = "done" if issue["state"].lower() == "closed" else "in_progress"
        papers.append({"pmid": pmid, "doi": doi, "title": title,
                       "status": status, "issue_number": issue["number"],
                       "source_type": "primary"})
    return papers


# ── Build ─────────────────────────────────────────────────────────────────────

def build(db_path: Path = DB_PATH) -> None:
    """Ensure db_path is a complete, fresh database, or raise.

    Serialised with fcntl.flock on a persistent lock file. The kernel drops the
    lock when the owning process exits for any reason, so there is no stale-lock
    detection to get wrong, and the lock is held across the freshness check,
    the build, the atomic publish and temp-file cleanup. A caller that waited
    acquires the lock itself, re-checks freshness, and rebuilds if the previous
    builder failed; it never returns having merely seen an old DB.
    Diagnostics go to stderr so lookup.py keeps clean JSON on stdout.
    """
    import fcntl
    import time

    db_path.parent.mkdir(parents=True, exist_ok=True)
    lock = db_path.with_suffix(".rebuild.lock")   # persistent; never unlinked
    fd = os.open(lock, os.O_CREAT | os.O_RDWR, 0o644)
    try:
        deadline = time.monotonic() + LOCK_WAIT_SECONDS
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        f"Timed out after {LOCK_WAIT_SECONDS}s waiting for "
                        f"another rebuild (lock: {lock})") from None
                time.sleep(0.1)
        _build_locked(db_path)
    finally:
        os.close(fd)   # releases the flock


def _build_locked(db_path: Path) -> None:
    """Freshness re-check + build + atomic publish. Caller holds the lock."""
    tmp_path = db_path.with_suffix(".tmp")
    try:
        # Re-check freshness under the lock — another builder may have just
        # finished, making our rebuild redundant.
        if db_path.exists():
            try:
                con_check = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
                cached = con_check.execute(
                    "SELECT value FROM meta WHERE key='commit'"
                ).fetchone()
                con_check.close()
                if cached and cached[0] == _git_head():
                    return   # already fresh — another builder beat us
            except Exception:
                pass   # unreadable DB → rebuild anyway

        # Build into a temp file so readers always see a complete database.
        # os.rename is atomic on POSIX when src and dst are on the same filesystem.
        tmp_path.unlink(missing_ok=True)
        con = sqlite3.connect(tmp_path)
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
        # Atomic publish: rename tmp → db_path so readers never see a partial DB
        os.rename(tmp_path, db_path)
        # Diagnostics go to stderr — stdout stays clean JSON for callers
        print(f"Rebuilt {db_path} — {paper_count} papers, commit {_git_head()}",
              file=sys.stderr)
    finally:
        tmp_path.unlink(missing_ok=True)  # no-op if renamed; cleans up on failure


if __name__ == "__main__":
    build()
