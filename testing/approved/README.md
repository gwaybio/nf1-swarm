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
python testing/harness/approval_checker.py --capture > testing/approved/snapshot_$(date +%Y%m%d).json

# Check current graph against latest snapshot
python testing/harness/approval_checker.py --check
```
