#!/usr/bin/env python3
"""Validate accepted claims against the same specs claim_validator.py uses.

This is a *separate* script (NOT in testing/harness/, which is
CODEOWNERS-protected) because claim_validator.py hardcodes PENDING_DIR
and is human-owned. Rather than modifying the protected harness, this
script reuses its validation logic via import and points it at
claims/accepted/ instead.

Why accepted claims need validation too: a tightened schema or spec
change could invalidate claims that were accepted under older rules.
claim_validator.py only ever checks claims/pending/, so drift in
claims/accepted/ would go unnoticed without this.

Usage:
    uv run python scripts/validate_accepted_claims.py
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from testing.harness.claim_validator import load_specs, validate_file  # noqa: E402

ACCEPTED_DIR = REPO_ROOT / "claims" / "accepted"


def main():
    schema, contract, rubric, edge_constraints = load_specs()
    accepted = list(ACCEPTED_DIR.glob("*.json"))
    if not accepted:
        print("No accepted claims to validate.")
        return 0

    passed = failed = 0
    failing_files = []
    for path in sorted(accepted):
        ok, errors = validate_file(path, schema, contract, rubric, edge_constraints)
        if ok:
            print(f"  PASS  {path.name}")
            passed += 1
        else:
            print(f"  FAIL  {path.name}")
            for e in errors:
                print(f"        {e}")
            failed += 1
            failing_files.append(path.name)

    print(f"\n{passed} passed, {failed} failed")
    if failing_files:
        print(f"Failing files: {', '.join(failing_files)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
