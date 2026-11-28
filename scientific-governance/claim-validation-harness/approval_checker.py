#!/usr/bin/env python3
"""Approval checker — PROTECTED (human-owned).

Captures or checks the graph state against approval snapshots.

Usage:
    uv run python approval_checker.py --capture --output \
        scientific-governance/approved-graph-snapshots/snapshot_YYYYMMDD.json
    uv run python approval_checker.py --capture   # print JSON to stdout (does not touch any file)
    uv run python approval_checker.py --check
    uv run python approval_checker.py             # just run assertions

Prefer --output over shell redirection: `--capture > snapshot.json` truncates an existing
snapshot before the checker runs, so a failed capture would destroy it. --output writes a
temp file beside the target, validates it as JSON and only then atomically replaces the
target; on any failure the existing snapshot is left untouched.
"""
import argparse
import json
import os
import sys
import yaml
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
ASSERTIONS_PATH = REPO_ROOT / "scientific-governance" / "required-graph-assertions" / "graph_assertions" / "seed_state.yaml"
APPROVED_DIR = REPO_ROOT / "scientific-governance" / "approved-graph-snapshots"


def get_driver():
    try:
        from neo4j import GraphDatabase
        return GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", os.environ.get("NEO4J_PASSWORD", "nf1swarm")))
    except Exception as e:
        print(f"WARNING: Neo4j unavailable: {e}")
        return None


def run_assertions(driver):
    spec = yaml.safe_load(ASSERTIONS_PATH.read_text())
    results = {}
    with driver.session() as session:
        for a in spec["assertions"]:
            count = session.run(a["cypher"]).single()["n"]
            results[a["id"]] = {
                "description": a["description"],
                "count": count,
                "expected_min": a["expected_min"],
                "passed": count >= a["expected_min"],
            }
    return results


def write_snapshot_atomically(results: dict, target: Path) -> None:
    """Write results as JSON to target without ever leaving it truncated or invalid.

    The temp file lives in the same directory as the target so os.replace is a
    same-filesystem atomic rename (a cross-filesystem move would copy, and a failed
    copy could lose the existing snapshot).
    """
    import tempfile
    target.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(results, indent=2)
    json.loads(text)  # validate before anything is replaced
    fd, tmp = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, target)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path, metavar="PATH",
                        help="with --capture: atomically write the snapshot to PATH instead of stdout")
    args = parser.parse_args()
    if args.output and not args.capture:
        parser.error("--output requires --capture")

    driver = get_driver()
    if driver is None:
        if args.capture:
            # A skipped capture must never look like a successful one: callers redirect
            # stdout into a snapshot file, so say nothing on stdout and fail.
            print("ERROR: cannot capture a snapshot — Neo4j is not running.", file=sys.stderr)
            return 2
        print("Skipping approval checks (Neo4j not running).")
        return 0

    results = run_assertions(driver)
    driver.close()

    if args.capture:
        if args.output:
            write_snapshot_atomically(results, args.output)
            print(f"Snapshot written to {args.output}", file=sys.stderr)
        else:
            print(json.dumps(results, indent=2))
        return 0

    if args.check:
        snapshots = sorted(APPROVED_DIR.glob("snapshot_*.json"))
        if not snapshots:
            print("No snapshot found. Run --capture first.")
            return 1
        approved = json.loads(snapshots[-1].read_text())
        failed = 0
        for key, cur in results.items():
            if key not in approved:
                print(f"  NEW   {key} (needs human approval)")
                failed += 1
            elif not cur["passed"]:
                print(f"  FAIL  {key}: count={cur['count']} < min={cur['expected_min']}")
                failed += 1
            else:
                print(f"  PASS  {key}")
        return 1 if failed else 0

    failed = 0
    for key, r in results.items():
        status = "PASS" if r["passed"] else "FAIL"
        if not r["passed"]:
            failed += 1
        print(f"  {status}  {r['description']} (count={r['count']}, min={r['expected_min']})")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
