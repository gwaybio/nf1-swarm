# Approval Snapshots

Known-good knowledge graph states for approval testing.

## Rules

- Updated ONLY by humans (`@gwaybio`) after reviewing the diff
- The PR updating a snapshot must include the graph diff in the PR description
- CI enforces CODEOWNERS: snapshot updates require `@gwaybio` approval
- File format: `snapshot_YYYYMMDD.json`

## Workflow

```bash
# Capture current graph state
uv run python scientific-governance/claim-validation-harness/approval_checker.py \
  --capture --output scientific-governance/approved-graph-snapshots/snapshot_$(date +%Y%m%d).json

# Check current graph against latest snapshot
uv run python scientific-governance/claim-validation-harness/approval_checker.py --check
```

Use `--output`, not shell redirection. `--capture > snapshot.json` truncates an existing
snapshot before the checker even starts, so a failed capture would destroy it.
`--output` writes a temp file in the same directory as the snapshot, validates it as JSON,
and only then atomically replaces the target; if anything fails, the existing snapshot is
left untouched.

`--capture` exits non-zero (code 2) with an error on stderr when Neo4j is not running.
`--check` and the default mode still skip successfully in that case so CI without Neo4j
stays green.
