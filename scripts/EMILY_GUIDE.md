# Emily's Infrastructure Guide

This is HOW. For WHO/WHAT, see `AGENTS.md`'s Emily section.

> **Python environment:** Always use `uv run python` (or activate `.venv` first).
> Never use bare `python3`, never `pip install`, never create a private venv.
> If an import fails, the interpreter is wrong — not the package. Fix: `cd ~/repos/nf1-swarm && uv run python <script>`.

## Repo structure (the parts you touch most)

```
nf1-swarm/
├── .github/workflows/        # ci.yml (push), daily-health.yml (cron/dispatch)
├── .github/ISSUE_TEMPLATE/   # .yml templates only, no stale .md
├── .github/CODEOWNERS        # lists every @gwaybio-only path
├── knowledge_graph/
│   ├── seeds/bootstrap.py    # runs schema → seeds → migrations, in order
│   ├── schema/*.cypher       # constraints, indexes
│   ├── seeds/*.cypher        # core NF1 biology seed data
│   ├── migrations/*.cypher   # numbered, idempotent schema changes
│   └── queries/               # reserve_claim_id.py + saved .cypher queries
├── literature/fetcher.py     # PaperFetcher, used by Dirk
├── literature/extractor.py   # claim extraction helpers
├── scripts/                  # YOUR scratch space — anything here is unprotected
├── scientific-governance/
│   ├── claim-validation-harness/  # PROTECTED — approval_checker.py, claim_validator.py,
│   │                               run_tests.sh, check_cypher.py
│   ├── scientific-claim-rules/    # PROTECTED — claim_contract.yaml, evidence_rubric.yaml,
│   │                               edge_constraints.yaml, node_schemas.yaml
│   ├── required-graph-assertions/ # test DATA other agents write rows into
│   └── approved-graph-snapshots/  # snapshot approvals
└── claims/schema.json         # PROTECTED — the data contract
```

## What you can push directly vs. what needs a PR

**Never push directly** (open a branch, tag `@gwaybio`, no self-merge):
- `scientific-governance/claim-validation-harness/` — CODEOWNERS-enforced
- `scientific-governance/scientific-claim-rules/` — CODEOWNERS-enforced, Rey reviews, Gregory approves
- `claims/schema.json` — CODEOWNERS-enforced
- Also CODEOWNERS-protected (same rule, broader than AGENTS.md's Emily list):
  `AGENTS.md`, `DESIGN.md`, `METHODS.md`, `.github/CODEOWNERS`, `.hermes/`

**Direct push is fine:**
- `bootstrap.py`, seed/migration `.cypher` files, `literature/*.py`
- CI workflow files (`.github/workflows/*.yml`) — as long as you're adding
  steps or env vars, not touching protected logic they call out to
- `scripts/` — this whole directory is yours
- `pyproject.toml`, documentation, issue templates

**If you can't modify the protected file but still need the behavior**: write
a thin wrapper in `scripts/` that *imports* from the protected module (e.g.
`scripts/validate_accepted_claims.py` imports `load_specs`/`validate_file`
from `scientific-governance/claim-validation-harness/claim_validator.py` rather than duplicating or editing
it). Same validation logic, zero protected-file edits, no PR needed.

## Running the test harness locally

```bash
cd ~/repos/nf1-swarm
uv run bash scientific-governance/claim-validation-harness/run_tests.sh
```

**You must prefix with `uv run`** (or activate the venv first) — the script
itself calls bare `python3`, which won't have `neo4j`/`jsonschema`/`pyyaml`
installed unless you're inside the uv-managed venv.

**Known harness bug (do not fix without a PR — it's CODEOWNERS-protected):**
`run_tests.sh` uses `set -e` combined with `((PASS++))`. When `PASS` is still
`0`, the bash arithmetic expression `((0++))` evaluates to `0` ("false"),
which trips `set -e` and kills the script right after the *first* passing
step — even though that step genuinely passed. You'll see it stop after
"Claim validator ... PASSED" with no further output and exit code 1. This is
cosmetic for local runs; **CI is not affected** because `ci.yml` calls
`claim_validator.py` and `approval_checker.py` directly (`&&`-chained), never
through `run_tests.sh`. If you need a real local pass/fail signal, run the
two scripts individually:

```bash
uv run python scientific-governance/claim-validation-harness/claim_validator.py
uv run python scientific-governance/claim-validation-harness/approval_checker.py
```

## Local Neo4j for testing

```bash
sudo systemctl start neo4j      # community 5.26, APOC + GDS already installed
# bolt://localhost:7687, neo4j/<password from secrets>
uv run python knowledge_graph/seeds/bootstrap.py
```

Check APOC is actually loaded before debugging a `reserve_claim_id.py`
failure — it's a server plugin, not a pip package, so `pyproject.toml` can
never fix a missing-APOC error:
```bash
uv run python -c "
from neo4j import GraphDatabase
d = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', os.environ['NEO4J_PASSWORD']))
print(d.session().run('RETURN apoc.version() AS v').single()['v'])
"
```

## CI debugging

```bash
gh run list --repo gwaybio/nf1-swarm --limit 5
gh run watch <run_id> --repo gwaybio/nf1-swarm --exit-status
gh run view <run_id> --repo gwaybio/nf1-swarm --log | grep -i <step name or error>
```

- `ci.yml` triggers on push to `main`. `daily-health.yml` is cron + manual —
  trigger it on demand to verify a fix without waiting for the schedule:
  `gh workflow run daily-health.yml --repo gwaybio/nf1-swarm`
- Before trusting a multi-line `run: |` step you hand-edited, extract and
  run the *exact* parsed script locally:
  ```bash
  uv run python -c "
  import yaml
  doc = yaml.safe_load(open('.github/workflows/ci.yml'))
  for s in doc['jobs']['graph-health']['steps']:
      if s.get('name') == '<step name>':
          open('/tmp/step.sh','w').write(s['run'])
  "
  bash /tmp/step.sh
  ```
  This catches YAML-escaping bugs (e.g. wrong backslash count in an embedded
  `python -c "..."` string) before they cost you a CI round-trip.
- The CI Neo4j container both jobs spin up needs
  `-e NEO4J_PLUGINS='["apoc"]'` to auto-download APOC at startup — without it,
  anything using `apoc.lock.nodes()` (i.e. `reserve_claim_id.py`) fails only
  in CI, never locally (your dev Neo4j already has the plugin installed).

## Pitfalls specific to this shared-checkout swarm

- **Other agents' uncommitted work sits in the same working tree.** Before
  `git add`, always check `git status --short` and stage only the files you
  actually touched (`git add <specific paths>`, never `git add -A` or
  `git commit -a`). A naive full-tree commit will bundle in whatever Dirk,
  Kim, or Graude left staged/unstaged, including commits to protected paths
  you didn't intend to push.
- **Pre-commit hooks can stash-and-modify files on a failed commit attempt**
  (trailing-whitespace / end-of-file-fixer). After any failed `git commit`,
  re-run `git status --short` before your next attempt — the hook may have
  "restored" files with trivial whitespace fixes applied, which you'll now
  see as unstaged changes to files you never touched.
- **Verify end-to-end, not just "doesn't error."** For `reserve_claim_id.py`
  specifically: a green bootstrap step proves the Counter node seeded
  correctly, but proves nothing about whether `apoc.lock.nodes()` actually
  works, since `bootstrap.py` never calls `next_claim_id()`. Add an explicit
  verification step (see `ci.yml`'s "Verify reserve_claim_id (APOC)" step)
  rather than trusting an unrelated step's green checkmark.

## Backup / restore

```bash
bash scripts/backup_graph.sh                      # dumps to backups/, keeps last 7
bash scripts/restore_graph.sh backups/nf1_graph_<timestamp>.dump
```

Both require `sudo` to stop/start the Neo4j service — run interactively, not
from an unattended agent call that can't supply a password.

## GitHub commenting rules

- **No `@handle` syntax anywhere** — not in issue comments, PR bodies, PR titles,
  or review comments. It fires email notifications to real people. Refer to
  teammates by name: Gregory, Rey, Graude, Otto, Dirk, Stan, Kim, Emily.
- Comments are factual status records for Gregory to read. Keep them concise:
  what was done, what IDs were assigned, what failed and why.
- Use `message_agent` (Hermes) for all agent-to-agent coordination — GitHub is
  for humans to track the science, not for agents to talk to each other.
