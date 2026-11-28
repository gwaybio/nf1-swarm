# Testing Framework — nf1-swarm

This project adopts an agentic-aware testing philosophy drawing on two 2026 frameworks:

## Philosophy

### Problem: agents corrupt tests

When AI agents write both production code and test code, tests lose their protective value. An agent optimizing for a passing suite can silently weaken a test — the test becomes a liability masquerading as an asset.

### Solution 1: Tests as Data (Vaccari, 2026)

Move the contract between humans and agents into *data*, not code.

- `scientific-governance/scientific-claim-rules/` — **TRUSTED**. Human-written YAML specifications. The formal contract.
- `scientific-governance/required-graph-assertions/` — **TEST DATA**. Agent-writable tables. Rows assert expected behavior.
- `scientific-governance/claim-validation-scripts/` — **PROTECTED**. Human-owned Python. CODEOWNERS-enforced. Agents cannot modify.
- `scientific-governance/approved-graph-snapshots/` — **SNAPSHOTS**. Known-good graph states. Human approval required to update.

### Solution 2: Specification-first verification (AlphaProof Code, DeepMind, 2026)

Humans write the *specification* (what correctness means). Agents prove compliance.

Trusted computing base (TCB):
1. `scientific-governance/scientific-claim-rules/claim_contract.yaml`
2. `scientific-governance/scientific-claim-rules/evidence_rubric.yaml`
3. `scientific-governance/scientific-claim-rules/edge_constraints.yaml`
4. `scientific-governance/scientific-claim-rules/node_schemas.yaml`

Anything outside the TCB is untrusted and checked mechanically.

## For agents: how to contribute tests

1. **Adding a claim assertion**: Add a row to `scientific-governance/required-graph-assertions/claim_tables/pathway_claims.csv`. Do not modify the header or harness.
2. **Adding a graph assertion**: Add a YAML block to `scientific-governance/required-graph-assertions/graph_assertions/seed_state.yaml`. Do not modify the assertion schema.
3. **Never modify**: `scientific-governance/scientific-claim-rules/`, `scientific-governance/claim-validation-scripts/`, `scientific-governance/approved-graph-snapshots/`

## Running tests

```bash
uv run bash scientific-governance/claim-validation-scripts/run_tests.sh
```
