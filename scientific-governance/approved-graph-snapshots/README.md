# Approval Snapshots

Known-good knowledge graph states for approval testing.

## Rules

- Updated ONLY by humans (`@gwaybio`) after reviewing the diff
- The PR updating a snapshot must include the graph diff in the PR description
- CI enforces CODEOWNERS: snapshot updates require `@gwaybio` approval
- File format: `snapshot_YYYYMMDD.json`

## Workflow

```bash
# Capture current graph state. Write to a temp file and replace the snapshot only
# if the capture succeeded and the output is valid JSON: a bare `> snapshot.json`
# truncates today's snapshot before the checker runs.
snap=scientific-governance/approved-graph-snapshots/snapshot_$(date +%Y%m%d).json
tmp=$(mktemp)
uv run python scientific-governance/claim-validation-harness/approval_checker.py --capture > "$tmp" \
  && uv run python -m json.tool "$tmp" > /dev/null \
  && mv "$tmp" "$snap" \
  || { rm -f "$tmp"; echo "capture failed; existing snapshot left untouched" >&2; }

# Check current graph against latest snapshot
uv run python scientific-governance/claim-validation-harness/approval_checker.py --check
```

`--capture` exits non-zero (code 2) with an error on stderr when Neo4j is not
running. `--check` and the default mode still skip successfully in that case so CI
without Neo4j stays green.
