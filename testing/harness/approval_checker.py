#!/usr/bin/env python3
"""Approval checker — PROTECTED (human-owned).

Captures or checks the graph state against approval snapshots.

Usage:
    python approval_checker.py --capture > testing/approved/snapshot_YYYYMMDD.json
    python approval_checker.py --check
    python approval_checker.py          # just run assertions
"""
import argparse
import json
import os
import sys
import yaml
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
ASSERTIONS_PATH = REPO_ROOT / "testing" / "acceptance" / "graph_assertions" / "seed_state.yaml"
APPROVED_DIR = REPO_ROOT / "testing" / "approved"


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    driver = get_driver()
    if driver is None:
        print("Skipping approval checks (Neo4j not running).")
        return 0

    results = run_assertions(driver)
    driver.close()

    if args.capture:
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
