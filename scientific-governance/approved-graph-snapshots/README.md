# Approval Snapshots

Known-good knowledge graph states for approval testing.

## Rules

- Updated ONLY by humans (`@gwaybio`) after reviewing the diff
- The PR updating a snapshot must include the graph diff in the PR description
- CI enforces CODEOWNERS: snapshot updates require `@gwaybio` approval
- File format: `snapshot_YYYYMMDD.json`

## Workflow

Order matters. `--check` compares the live graph with the **latest approved snapshot**, so it
must run *before* a new snapshot is captured: once a new assertion has been captured into the
latest snapshot, `--check` reports it as `PASS` instead of `NEW` and the review signal is lost.

```bash
CHECKER=scientific-governance/claim-validation-harness/approval_checker.py
SNAPDIR=scientific-governance/approved-graph-snapshots

# 1. Check the live graph against the latest approved snapshot.
#    NEW lines = assertions not yet approved; FAIL lines = regressions.
uv run python $CHECKER --check

# 2. Capture a CANDIDATE outside the approved directory (never straight over an approved snapshot).
uv run python $CHECKER --capture --output "$TMPDIR/candidate.json"

# 3. Produce the diff a human reviews (--check does not produce a graph diff).
latest=$(ls $SNAPDIR/snapshot_*.json | sort | tail -1)
diff -u <(python3 -m json.tool --sort-keys "$latest") \
        <(python3 -m json.tool --sort-keys "$TMPDIR/candidate.json")

# 4. Only after review and approval, install it under today's name and commit it in a PR
#    whose description includes the diff from step 3.
cp "$TMPDIR/candidate.json" "$SNAPDIR/snapshot_$(date +%Y%m%d).json"
```

Use `--output`, not shell redirection. `--capture > snapshot.json` truncates an existing
snapshot before the checker even starts, so a failed capture would destroy it.
`--output` writes a temp file in the same directory as the snapshot, validates it as JSON,
and only then atomically replaces the target; if anything fails, the existing snapshot is
left untouched.

`--capture` exits non-zero (code 2) with an error on stderr when Neo4j is not running.
`--check` and the default mode still skip successfully in that case so CI without Neo4j
stays green.
