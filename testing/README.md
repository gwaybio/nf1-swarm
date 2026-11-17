# Testing Framework — nf1-swarm

This project adopts an agentic-aware testing philosophy drawing on two 2026 frameworks:

## Philosophy

### Problem: agents corrupt tests

When AI agents write both production code and test code, tests lose their protective value. An agent optimizing for a passing suite can silently weaken a test — the test becomes a liability masquerading as an asset.

### Solution 1: Tests as Data (Vaccari, 2026)

Move the contract between humans and agents into *data*, not code.

- `testing/specs/` — **TRUSTED**. Human-written YAML specifications. The formal contract.
- `testing/acceptance/` — **TEST DATA**. Agent-writable tables. Rows assert expected behavior.
- `testing/harness/` — **PROTECTED**. Human-owned Python. CODEOWNERS-enforced. Agents cannot modify.
- `testing/approved/` — **SNAPSHOTS**. Known-good graph states. Human approval required to update.

### Solution 2: Specification-first verification (AlphaProof Code, DeepMind, 2026)

Humans write the *specification* (what correctness means). Agents prove compliance.

Trusted computing base (TCB):
1. `testing/specs/claim_contract.yaml`
2. `testing/specs/evidence_rubric.yaml`
3. `testing/specs/edge_constraints.yaml`
4. `testing/specs/node_schemas.yaml`

Anything outside the TCB is untrusted and checked mechanically.

## For agents: how to contribute tests

1. **Adding a claim assertion**: Add a row to `testing/acceptance/claim_tables/pathway_claims.csv`. Do not modify the header or harness.
2. **Adding a graph assertion**: Add a YAML block to `testing/acceptance/graph_assertions/seed_state.yaml`. Do not modify the assertion schema.
3. **Never modify**: `testing/specs/`, `testing/harness/`, `testing/approved/`

## Running tests

```bash
bash testing/harness/run_tests.sh
```
