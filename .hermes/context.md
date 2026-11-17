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
- Bootstrap: `uv run python knowledge_graph/seeds/bootstrap.py`
- Test: `uv run python testing/harness/approval_checker.py`

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

## Claim ID assignment
**Never manually assign claim IDs.** Use the atomic counter:
```python
from knowledge_graph.queries.reserve_claim_id import next_claim_id
# inside a Neo4j session:
cid = next_claim_id(session)   # returns e.g. "C0042"
```

## Task flow
1. Graude opens GitHub issue `[DIRK] Read: <title> — <DOI>`
2. Dirk reads paper → deposits `claims/pending/C<id>.json`
3. Dirk runs `uv run python testing/harness/claim_validator.py` before committing
4. Dirk commits: `claim(dirk): <short title>`
5. Rey reviews pending/ → accepts (moves to accepted/) or rejects (adds reason)
6. Kim writes accepted claims to Neo4j using `write_neo4j_cypher` MCP tool
7. Graude tracks progress via open GitHub issues

## Protocols
- Full team protocol: `AGENTS.md`
- Architecture: `DESIGN.md`
- Testing philosophy: `testing/README.md`
- Literature queue: `literature/queue.md`
