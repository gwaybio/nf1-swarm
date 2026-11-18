# Stan's Statistics Guide

## When to run confidence scoring

Run scoring on an accepted claim once `supporting_dois` (in the claim JSON)
has **N ≥ 3** independent entries. Below that threshold, report honestly:
"insufficient replication" — do not force a confidence_score out of 1-2
sources. N<3 claims keep `confidence_score: null`.

```python
import json
from pathlib import Path

claim = json.loads(Path("claims/accepted/C0042.json").read_text())
dois = claim.get("supporting_dois", [])
if len(dois) < 3:
    print("insufficient replication — do not score")
else:
    # proceed to PET-PEESE / RoBMA-PSMA
    ...
```

## Reading `supporting_dois`

`supporting_dois` grows over time as Dirk/Otto/Archie find more papers backing
the same claim. Each entry is a DOI or PMID string. Pull each paper's effect
size and sample size (via `literature/fetcher.py` if you need full text) to
build the meta-analytic input set.

```python
from literature.fetcher import PaperFetcher
f = PaperFetcher()
papers = [f.fetch_by_doi(d) if d.startswith("10.") else f.fetch(d) for d in dois]
```

## PET-PEESE / RoBMA-PSMA threshold logic

- **PET-PEESE** (precision-effect test / precision-effect estimate with
  standard error): use when you have ≥5 studies with reported standard
  errors — regress effect size on SE (PET) and SE² (PEESE) to estimate the
  publication-bias-corrected effect at SE→0.
- **RoBMA-PSMA** (robust Bayesian meta-analysis — publication-selection
  and multi-model averaging): use when study count is 3-4 (too few for a
  reliable PET-PEESE regression) or when effect sizes are heterogeneous
  across evidence_type (e.g. mixing RCT with preclinical_in_vivo).
- Either way, output a `confidence_score` in **[0.0, 1.0]** — this is
  publication-bias-ADJUSTED, not the same thing as `evidence_strength`
  (which is Dirk's/Rey's domain per source quality, 1-5 integer scale).
  Never touch `evidence_strength`.

## `independence_flags` criteria

Before trusting N≥3 as real replication, check whether the supporting
sources are actually independent. Flag (don't silently discard) when:

- **Same lab** — overlapping author lists across papers (check `first_author`
  field via Publication nodes or claim `notes`)
- **Same dataset** — e.g. two papers both reanalyzing the same GEO series or
  the same clinical trial's secondary endpoints
- **Same first author** — a self-replication is weaker evidence than an
  independent one
- **Same institution** — weaker signal than cross-institution replication

Write each concern as a short string into `independence_flags`:
```json
"independence_flags": ["same lab as C0031 (Smith et al.)", "reanalyzes GSE98765 used in C0028"]
```
A flagged claim isn't automatically wrong — it just means the N≥3 threshold
is softer than it looks. Lower your confidence_score accordingly rather than
rejecting outright; rejection is Rey's call.

## Reporting to Rey

Report to Rey **only** when `confidence_score` diverges significantly from
`evidence_strength` (e.g. evidence_strength=4 but confidence_score<0.4 after
bias correction, or vice versa) — that divergence is the signal Rey needs to
re-review. Routine scoring that confirms the existing strength doesn't need
escalation; just write the score and move on.

## Updating the claim JSON

```python
claim["confidence_score"] = 0.62
claim["independence_flags"] = ["same lab as C0031"]
Path("claims/accepted/C0042.json").write_text(json.dumps(claim, indent=2))
```

Commit: `fix(stan): score C<id> confidence (N=<n> supporting DOIs)` — or use
whatever commit convention Graude has set for your agent identity; the
important part is the message states what claim and why.

## Common pitfalls

1. **Don't conflate `evidence_strength` and `confidence_score`.** Strength is
   a 1-5 integer set by Dirk/Rey describing study design quality. Confidence
   is a 0.0-1.0 float you compute from accumulated, bias-corrected evidence.
   They can legitimately disagree.
2. **Re-score, don't just add, as new DOIs arrive.** A claim that had
   confidence_score=0.55 at N=3 might drop once a 6th study with a null
   result lands — publication bias correction is sensitive to the full set,
   not just new additions.
3. **`claims/schema.json` and `testing/specs/` are not yours to edit.** If the
   rubric or schema seems wrong for scoring purposes, flag it to Graude —
   don't work around it by stuffing scores into `notes`.

## GitHub commenting rules

- **No `@handle` syntax anywhere** — not in issue comments, PR bodies, PR titles,
  or review comments. It fires email notifications to real people. Refer to
  teammates by name: Gregory, Rey, Graude, Otto, Dirk, Stan, Kim, Emily.
- Comments are factual status records for Gregory to read. Keep them concise:
  what was done, what IDs were assigned, what failed and why.
- Use `message_agent` (Hermes) for all agent-to-agent coordination — GitHub is
  for humans to track the science, not for agents to talk to each other.
