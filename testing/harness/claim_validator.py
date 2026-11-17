#!/usr/bin/env python3
"""Claim validator — PROTECTED (human-owned, do not modify via agent PR).

Validates claims in claims/pending/ against:
  - claims/schema.json (JSON Schema)
  - testing/specs/claim_contract.yaml (claim type rules)
  - testing/specs/evidence_rubric.yaml (strength/type consistency)

Agents write claims; this validator checks them. The validator is not modifiable by agents.
"""
import json
import sys
from pathlib import Path

try:
    import jsonschema
    import yaml
except ImportError:
    print("ERROR: Run: pip install jsonschema pyyaml")
    sys.exit(1)

REPO_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = REPO_ROOT / "claims" / "schema.json"
CONTRACT_PATH = REPO_ROOT / "testing" / "specs" / "claim_contract.yaml"
RUBRIC_PATH = REPO_ROOT / "testing" / "specs" / "evidence_rubric.yaml"
PENDING_DIR = REPO_ROOT / "claims" / "pending"


def load_specs():
    schema = json.loads(SCHEMA_PATH.read_text())
    contract = yaml.safe_load(CONTRACT_PATH.read_text())
    rubric = yaml.safe_load(RUBRIC_PATH.read_text())
    return schema, contract, rubric


def validate_json_schema(claim, schema):
    errors = []
    validator = jsonschema.Draft7Validator(schema)
    for err in validator.iter_errors(claim):
        errors.append(f"Schema: {err.message}")
    return errors


def validate_claim_contract(claim, contract):
    errors = []
    claim_type = claim.get("claim_type")
    if claim_type not in contract["claim_types"]:
        return [f"Contract: unknown claim_type '{claim_type}'"]

    rules = contract["claim_types"][claim_type]
    strength = claim.get("evidence_strength", 0)
    min_strength = rules.get("min_evidence_strength", 1)
    if strength < min_strength:
        errors.append(f"Contract: evidence_strength {strength} below minimum {min_strength} for '{claim_type}'")

    evidence_type = claim.get("evidence_type")
    allowed = rules.get("allowed_evidence_types", [])
    if evidence_type and allowed and evidence_type not in allowed:
        errors.append(f"Contract: evidence_type '{evidence_type}' not allowed for '{claim_type}'. Allowed: {allowed}")

    return errors


def validate_rubric(claim, rubric):
    errors = []
    strength = claim.get("evidence_strength")
    evidence_type = claim.get("evidence_type")
    if strength is None or evidence_type is None:
        return errors
    for rule in rubric.get("consistency_rules", []):
        if rule["evidence_strength"] == strength:
            if evidence_type in rule.get("forbidden_evidence_types", []):
                errors.append(f"Rubric: '{evidence_type}' inconsistent with strength {strength}")
    return errors


def validate_file(path, schema, contract, rubric):
    try:
        claim = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return False, [f"JSON parse error: {e}"]
    errors = validate_json_schema(claim, schema)
    if not errors:
        errors += validate_claim_contract(claim, contract)
        errors += validate_rubric(claim, rubric)
    return len(errors) == 0, errors


def main():
    schema, contract, rubric = load_specs()
    pending = list(PENDING_DIR.glob("*.json"))
    if not pending:
        print("No pending claims to validate.")
        return 0
    passed = failed = 0
    for path in sorted(pending):
        ok, errors = validate_file(path, schema, contract, rubric)
        if ok:
            print(f"  PASS  {path.name}")
            passed += 1
        else:
            print(f"  FAIL  {path.name}")
            for e in errors:
                print(f"        {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
