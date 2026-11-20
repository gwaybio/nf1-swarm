#!/usr/bin/env python3
"""
Claim ID lifecycle management.

Three stages:
  1. Extraction — Dirk deposits a claim with a temporary 8-char hex pending_id.
                  No C#### is assigned yet; the counter does not advance.
  2. Acceptance — Rey calls accept_claim(). C#### is assigned atomically from
                  the Neo4j counter, file is moved to claims/accepted/C####.json.
  3. Rejection  — Rey calls reject_claim(). R#### is assigned atomically from a
                  separate Neo4j counter, file is moved to claims/rejected/R####.json.
                  R#### claims never consume C#### IDs.
  4. Resurrection — a resurrected R#### claim goes back to pending with a new
                    pending_id, then through the normal accept path. The new
                    accepted claim carries resurrected_from = "R####".

Usage (Dirk — extraction):
    from scripts.reserve_claim_id import generate_pending_id
    claim["pending_id"] = generate_pending_id()   # e.g. "a3f8c21b"
    # save to claims/pending/pending_a3f8c21b.json

Usage (Rey — acceptance):
    from scripts.reserve_claim_id import accept_claim
    with driver.session() as s:
        cid = accept_claim("a3f8c21b", s)   # returns "C0042"

Usage (Rey — rejection):
    from scripts.reserve_claim_id import reject_claim
    with driver.session() as s:
        rid = reject_claim("a3f8c21b", s, "structural",
                           "Predicate not in edge_constraints")
"""
from __future__ import annotations

import json
import secrets
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo4j import Session

REPO_ROOT    = Path(__file__).parent.parent
PENDING_DIR  = REPO_ROOT / "claims" / "pending"
ACCEPTED_DIR = REPO_ROOT / "claims" / "accepted"
REJECTED_DIR = REPO_ROOT / "claims" / "rejected"

_PENDING_PREFIX = "pending_"


# ── ID generators ─────────────────────────────────────────────────────────────

def generate_pending_id() -> str:
    """Return an 8-char lowercase hex string for a new pending claim."""
    return secrets.token_hex(4)


def pending_filename(pending_id: str) -> Path:
    return PENDING_DIR / f"{_PENDING_PREFIX}{pending_id}.json"


def _next_neo4j_counter(session: Session, counter_name: str, prefix: str) -> str:
    """Atomically increment a Neo4j counter and return the formatted ID."""
    result = session.run(
        """
        MATCH (c:Counter {name: $name})
        CALL apoc.lock.nodes([c])
        SET c.value = c.value + 1
        RETURN $prefix + right('0000' + toString(c.value), 4) AS id
        """,
        name=counter_name,
        prefix=prefix,
    )
    record = result.single()
    if record is None:
        raise RuntimeError(
            f"Counter '{counter_name}' not found in Neo4j. "
            "Run bootstrap.py to initialise the counters."
        )
    return record["id"]


# ── Claim lifecycle ───────────────────────────────────────────────────────────

def accept_claim(pending_id: str, session: Session) -> str:
    """
    Accept a pending claim.

    Assigns the next C#### ID (via Neo4j 'claim_id' counter), sets
    status='accepted', moves the file to claims/accepted/C####.json,
    and deletes the pending file.

    Returns the assigned C#### ID.
    """
    src = pending_filename(pending_id)
    if not src.exists():
        raise FileNotFoundError(f"Pending claim not found: {src}")

    claim = json.loads(src.read_text())
    cid = _next_neo4j_counter(session, "claim_id", "C")

    claim["claim_id"]  = cid
    claim["status"]    = "accepted"

    dest = ACCEPTED_DIR / f"{cid}.json"
    dest.write_text(json.dumps(claim, indent=2) + "\n")
    src.unlink()
    return cid


def reject_claim(
    pending_id: str,
    session: Session,
    rejection_class: str,
    rejection_reason: str = "",
) -> str:
    """
    Reject a pending claim.

    Assigns the next R#### ID (via Neo4j 'rejection_id' counter), sets
    status='rejected', moves the file to claims/rejected/R####.json,
    and deletes the pending file.

    Returns the assigned R#### ID.
    """
    if rejection_class not in ("structural", "biological"):
        raise ValueError(
            f"rejection_class must be 'structural' or 'biological', got {rejection_class!r}"
        )

    src = pending_filename(pending_id)
    if not src.exists():
        raise FileNotFoundError(f"Pending claim not found: {src}")

    claim = json.loads(src.read_text())
    rid = _next_neo4j_counter(session, "rejection_id", "R")

    claim["claim_id"]        = rid
    claim["status"]          = "rejected"
    claim["rejection_class"] = rejection_class
    if rejection_reason:
        claim["rejection_reason"] = rejection_reason

    dest = REJECTED_DIR / f"{rid}.json"
    dest.write_text(json.dumps(claim, indent=2) + "\n")
    src.unlink()
    return rid


def resurrect_claim(rejected_id: str) -> str:
    """
    Move a rejected R#### claim back to pending with a fresh pending_id.

    Sets resurrected_from = R####, clears claim_id, resets status to 'pending'.
    Returns the new pending_id. Rey calls accept_claim() on it after re-grounding.
    """
    src = REJECTED_DIR / f"{rejected_id}.json"
    if not src.exists():
        raise FileNotFoundError(f"Rejected claim not found: {src}")

    claim = json.loads(src.read_text())
    new_pending_id = generate_pending_id()

    claim["resurrected_from"] = rejected_id
    claim["claim_id"]         = None
    claim["status"]           = "pending"
    # Clear curation fields — Rey will fill them on re-acceptance
    for field in ("curated_by", "curation_date", "rejection_reason", "rejection_class"):
        claim[field] = None

    dest = pending_filename(new_pending_id)
    dest.write_text(json.dumps(claim, indent=2) + "\n")
    src.unlink()
    return new_pending_id
