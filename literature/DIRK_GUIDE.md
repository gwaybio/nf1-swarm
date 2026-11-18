# Dirk's Literature Guide

## Fetching papers

```python
from literature.fetcher import PaperFetcher

f = PaperFetcher()

# Search
pmids = f.search("NF1 neurofibromatosis plexiform MEK inhibitor", max_results=10)

# Fetch a paper (auto-attempts PMC full text)
paper = f.fetch("32187458")
print(paper.title)
print(paper.has_full_text, paper.full_text_source)

# Fetch by DOI
paper = f.fetch_by_doi("10.1056/NEJMoa1912735")

# Fetch a preprint
paper = f.fetch_by_doi("10.1101/2026.01.15.628000")
```

## Full-text availability

| Source | Access | Method |
|--------|--------|--------|
| PubMed Central (PMC) | Free for OA papers | Auto via `fetch()` |
| bioRxiv / arXiv | Always free | Auto via `fetch_by_doi()` |
| Paywalled journals | Abstract only | `paper.abstract` |

When full text is unavailable (`paper.full_text_source == "unavailable"`):
1. Use abstract + methods section from abstract
2. Note in claim JSON: `"notes": "Full text unavailable, extracted from abstract"`
3. Assign evidence_strength conservatively (max 3 from abstract alone)
4. Flag the PMID in `literature/queue.md` with `[PAYWALL]`

## Claim extraction workflow

1. Read `paper.full_text` (or `paper.abstract` if that's all available)
2. Extract claims — each is a **single falsifiable statement**
3. Reserve a claim ID: `uv run python -c "from knowledge_graph.queries.reserve_claim_id import next_claim_id; from neo4j import GraphDatabase; d = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j','nf1swarm')); print(next_claim_id(d.session()))"`
4. Write JSON to `claims/pending/C<id>.json` matching `claims/schema.json`
5. Run validator: `uv run python testing/harness/claim_validator.py`
6. Commit and reference the GitHub issue

## What counts as a claim

**Yes:**
- "Selumetinib reduces plexiform neurofibroma volume by ≥20% in pediatric NF1 patients" (clinical_outcome, strength 4)
- "NF1-deficient Schwann cells show elevated RAS-GTP levels compared to controls" (molecular_function, strength 3)

**No:**
- "NF1 is an interesting disease" (not falsifiable)
- "Selumetinib may help some patients" (too vague)
- "See Figure 3" (not standalone)

## Evidence strength quick guide

| Strength | Assign when |
|----------|-------------|
| 5 | Consensus — this is in every textbook |
| 4 | Phase 3 RCT, replicated across labs |
| 3 | Phase 2, validated animal model |
| 2 | Phase 1, single study, in vitro only |
| 1 | Expert opinion, hypothesis, your inference |

When in doubt, go lower. Rey will upgrade if warranted.

## GitHub commenting rules

- **No `@handle` syntax anywhere** — not in issue comments, PR bodies, PR titles,
  or review comments. It fires email notifications to real people. Refer to
  teammates by name: Gregory, Rey, Graude, Otto, Dirk, Stan, Kim, Emily.
- Comments are factual status records for Gregory to read. Keep them concise:
  what was done, what IDs were assigned, what failed and why.
- Use `message_agent` (Hermes) for all agent-to-agent coordination — GitHub is
  for humans to track the science, not for agents to talk to each other.
