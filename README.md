# nf1-swarm

An agentic AI swarm compiling the known history of NF1 (Neurofibromatosis type 1) biology and clinical outcomes into a structured, traversable knowledge graph.

## What this is

NF1 is a rare genetic disease (OMIM #162200) caused by loss-of-function mutations in the *NF1* gene encoding neurofibromin, a RAS-GTPase activating protein. It is one of the most common single-gene disorders affecting the nervous system (1:3000 births), with broad phenotypic expression spanning skin, nervous system, eyes, bones, vasculature, and cognition.

This repository is the working home of an AI agent swarm that reads primary literature, extracts structured claims, verifies them against raw data, curates them through PI-level review, and deposits them into a Neo4j knowledge graph. All work is auditable, versioned, and traceable to source.

## The team

| Agent | Role | Primary skills |
|-------|------|----------------|
| **Graude** | Orchestrator — assigns tasks, owns GitHub, tracks progress | github, llm-wiki |
| **Dirk** | Reads primary literature, extracts claims with evidence strength | arxiv, pdf, grounded-citations |
| **Archie** | Fact-checks claims, runs simulations, pulls raw data | python-debugpy, codebase-inspection, github |
| **Kim** | Builds and traverses the knowledge graph | python-debugpy, codebase-inspection, spike |
| **Rey** | PI/senior curator — final accept/reject decisions | systematic-debugging, requesting-code-review |

## Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start Neo4j (must be running on bolt://localhost:7687)
sudo systemctl start neo4j

# 3. Set Neo4j password (first run only)
# Default: neo4j/neo4j — change via http://localhost:7474

# 4. Bootstrap the knowledge graph
python knowledge_graph/seeds/bootstrap.py

# 5. Run the test suite
bash testing/harness/run_tests.sh
```

## Repository structure

```
nf1-swarm/
├── AGENTS.md                    # Agent roles, task protocol, communication
├── DESIGN.md                    # Architecture and design decisions
├── knowledge_graph/             # Neo4j schema, seeds, queries
├── claims/                      # Claim pipeline (pending → accepted)
├── literature/                  # Paper tracking
├── testing/                     # Agentic testing framework
├── agents/                      # Per-agent protocols
└── data/                        # External resource links
```

## Knowledge graph

Stored in Neo4j (bolt://localhost:7687). Schema spans 13 node types and 20 relationship types covering: genes, proteins, pathways, mutations, phenotypes, diseases, drugs, clinical trials, publications, claims, cell lines, animal models, and datasets.

## Testing philosophy

This project adopts two emerging principles for agentic codebases:

1. **Tests as data** (Vaccari, 2026): Acceptance tests live as tables and DSL files, not code. Agents write rows into test tables — they do not modify the test harness. The harness (`testing/harness/`) is human-owned and protected.

2. **Specification-first verification** (AlphaProof Code, DeepMind, 2026): Humans write the *specifications* (what correctness means: `testing/specs/`). Agents prove compliance. A claim that cannot pass the validator against the spec is rejected regardless of who wrote it.

See `testing/README.md` for full details.
