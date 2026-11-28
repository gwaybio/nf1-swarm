#!/usr/bin/env python3
"""Validate accepted claims against the same specs claim_validator.py uses.

This is a *separate* script (NOT in scientific-governance/claim-validation-harness/, which is
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

import importlib.util
import sys
from pathlib import Path

# scientific-governance/claim-validation-harness/ is a hyphenated directory and
# cannot be imported as a dotted Python package. Load the validator by file path.
_validator_path = Path(__file__).parent.parent / \
    "scientific-governance" / "claim-validation-harness" / "claim_validator.py"
_spec = importlib.util.spec_from_file_location("claim_validator", _validator_path)
assert _spec is not None and _spec.loader is not None, \
    f"Could not load claim_validator from {_validator_path}"
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]
load_specs = _mod.load_specs
validate_file = _mod.validate_file

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
            for w in errors:  # on success these are WARN: messages only (e.g. retired predicate)
                print(f"        {w}")
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
