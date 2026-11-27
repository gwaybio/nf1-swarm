# nf1-swarm — Agent Context

This file is auto-loaded by Hermes agents when working in this directory.

## Repo
- Path: `~/repos/nf1-swarm`
- GitHub: `https://github.com/gwaybio/nf1-swarm`
- Branch: `main` (direct push, no PRs)

## Knowledge graph
- Neo4j Community 5.26 with APOC + GDS
- URI: `bolt://localhost:7687`
- Credentials: `neo4j` / `nf1swarm`
- **Never hardcode the password in scripts.** Read it from the environment:
  ```python
  import os
  password = os.environ.get("NEO4J_PASSWORD", "nf1swarm")
  ```
- **Local setup:** add `export NEO4J_PASSWORD=nf1swarm` to `~/.bashrc` or `~/.zshrc`
  so the env var is always set. This keeps local and CI (GitHub secret) in sync.
- **If auth fails:** do NOT retry in a loop — you will trigger a lockout.
  Stop immediately and message Graude.
- Bootstrap: `uv run python knowledge_graph/seeds/bootstrap.py`
- Test: `uv run python scientific-governance/claim-validation-harness/approval_checker.py`

## Team
| Agent | Profile | Role |
|-------|---------|------|
| Graude | `graude` | Orchestrator — owns GitHub issues, assigns tasks |
| Dirk | `dirk` | Reads primary literature, extracts claims (FETA Stage 1) |
| Otto | `otto` | Ontology grounding — CURIEs, RTX-KG2, BEL notation (FETA Stage 2) |
| Archie | `archie` | Verifies claims, runs analyses |
| Stan | `stan` | Statistics — publication bias, confidence scoring |
| Kim | `kim` | Builds and queries the knowledge graph |
| Rey | `rey` | PI/curator — final accept/reject |
| Emily | `emily` | Software engineer — infrastructure, CI, bootstrap, tooling |
| Milo | `milo` | Memory & context manager — episodic store, dreaming, DACS registry, retrieval chatbot |

## Claim ID assignment

Claim IDs are assigned in two stages — never manually:

**Stage 1 — Extraction (Dirk):** generate a temporary 8-char hex `pending_id`:
```python
from scripts.reserve_claim_id import generate_pending_id
claim["pending_id"] = generate_pending_id()   # e.g. "a3f8c21b"
# save to claims/pending/pending_a3f8c21b.json
```

**Stage 2 — Acceptance/Rejection (Rey):** permanent IDs are assigned atomically:
```python
from scripts.reserve_claim_id import accept_claim, reject_claim
# inside a Neo4j session:
cid = accept_claim("a3f8c21b", session)    # returns "C0042", moves to accepted/
rid = reject_claim("a3f8c21b", session, "structural", "reason")  # returns "R0001", moves to rejected/
```

`C####` IDs only advance on acceptance — never on extraction or rejection.
`R####` IDs are a separate counter for rejected claims.

## Task flow
1. Graude opens GitHub issue `[DIRK] Read: <title> — <DOI>`
2. Dirk reads paper → deposits `claims/pending/pending_<hex>.json` (using `generate_pending_id()` from `scripts.reserve_claim_id`)
3. Dirk runs `uv run python scientific-governance/claim-validation-scripts/claim_validator.py` before committing
4. Dirk commits: `claim(dirk): <short title>`
5. Rey reviews pending/ → accepts (moves to accepted/) or rejects (adds reason)
6. Kim writes accepted claims to Neo4j using `write_neo4j_cypher` MCP tool
7. Graude tracks progress via open GitHub issues

## Protocols
- Full team protocol: `AGENTS.md`
- Architecture: `DESIGN.md`
- Testing philosophy: `scientific-governance/README.md`
- Literature queue: `literature/queue.md`
