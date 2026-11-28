#!/usr/bin/env bash
# PROTECTED TEST HARNESS — human-owned, do not modify via agent PR
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

PASS=0; FAIL=0

run_step() {
    local name="$1"; shift
    echo "=== $name ==="
    if "$@"; then
        echo "  → PASSED"; PASS=$((PASS+1))
    else
        echo "  → FAILED"; FAIL=$((FAIL+1))
    fi
    echo ""
}

run_step "Claim validator"       python3 scientific-governance/claim-validation-harness/claim_validator.py
run_step "Graph assertions"      python3 scientific-governance/claim-validation-harness/approval_checker.py

echo "========================================"
echo "Results: $PASS passed, $FAIL failed"
echo "========================================"
[ "$FAIL" -eq 0 ]
