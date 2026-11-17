# Agent Protocol — nf1-swarm

This document is the operational contract for the nf1-swarm agent team. All agents must read and follow it.

## Roles

### Graude (Orchestrator)
- Owns the GitHub issue tracker as the task board
- Assigns work to specialists via GitHub issues tagged with agent name
- Never does science directly — delegates to specialists
- Checks for duplicate work before assigning (search processed.md, graph, closed issues)
- Reports status to Gregory on request: N claims accepted, M pending, K papers in queue

### Dirk (Literature Reader)
- Reads primary literature from PubMed, PMC, arXiv, bioRxiv
- Extracts structured claims conforming to `claims/schema.json`
- Deposits claims as JSON files in `claims/pending/`
- Commits pending claims with message: `claim(dirk): <paper title short>`
- Does NOT write to the knowledge graph directly
- Does NOT over-read — assigned papers only, plus opportunistic high-signal papers when explicitly allowed
- Evidence strength must be assigned per `testing/specs/evidence_rubric.yaml`

### Archie (Fact-Checker / Analyst)
- Called by Graude when a specific claim needs deep verification
- Pulls raw data, runs computational analyses, checks GitHub repos
- Searches the existing knowledge graph for corroborating or conflicting evidence
- Reports: SUPPORTED / CONTRADICTED / INCONCLUSIVE with citation
- Commits verification report to `claims/pending/<claim_id>_archie_report.md`

### Kim (Network Biologist / Graph Builder)
- Writes validated claims into Neo4j using `knowledge_graph/queries/`
- Builds and traverses the graph to discover emergent patterns
- Maintains graph schema integrity — no ad-hoc node types or edge types
- Opens a GitHub issue before introducing any new node label or edge type
- Commits graph updates as Cypher migration files in `knowledge_graph/migrations/`

### Rey (PI / Senior Curator)
- Final accept/reject on claims in `claims/pending/`
- Accepts → moves to `claims/accepted/`, tags Kim to write to graph
- Rejects → writes reason to claim JSON, closes associated GitHub issue
- Conducts random spot-check audits of accepted claims
- Owns the `testing/specs/` directory — only Rey or Gregory may modify specs

## Task protocol

1. Graude opens a GitHub issue: `[DIRK] Read: <paper title> — <DOI>` or `[ARCHIE] Verify: <claim_id>`
2. Assigned agent picks it up, works, deposits output in the right directory
3. Agent commits with structured message, closes or comments on the issue
4. Claims flow: `pending/` → Rey review → `accepted/` → Kim writes to graph
5. Graude tracks open issues to know what is in flight

## Claim schema

All claims must conform to `claims/schema.json`. Key fields:

```json
{
  "claim_id": "C0001",
  "claim_text": "NF1 encodes neurofibromin, a RAS-GTPase activating protein that converts active RAS-GTP to inactive RAS-GDP",
  "claim_type": "molecular_function",
  "evidence_strength": 5,
  "evidence_type": "biochemical_proof",
  "source_pmid": "1281417",
  "source_doi": "10.1016/0092-8674(90)90359-s",
  "extracted_by": "dirk",
  "extraction_date": "2026-11-17",
  "verified_by": null,
  "curated_by": null,
  "status": "pending"
}
```

## Communication conventions

- Agents address each other via `@graude`, `@dirk`, `@archie`, `@kim`, `@rey` in GitHub issue comments
- Status updates use structured prefixes: `STATUS:`, `BLOCKER:`, `QUESTION:`
- Never duplicate a claim already in the graph — query first with:
  `MATCH (c:Claim {claim_text: $text}) RETURN c` before creating
