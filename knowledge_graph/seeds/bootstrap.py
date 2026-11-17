#!/usr/bin/env python3
"""Bootstrap the NF1-Swarm Neo4j knowledge graph.

Runs schema constraints, indexes, and seed Cypher files in order.
Safe to re-run (all Cypher uses MERGE/IF NOT EXISTS).

Usage:
    python knowledge_graph/seeds/bootstrap.py [--uri bolt://localhost:7687] [--password nf1swarm]
"""
import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
SEEDS_DIR = REPO_ROOT / "knowledge_graph" / "seeds"
SCHEMA_DIR = REPO_ROOT / "knowledge_graph" / "schema"
MIGRATIONS_DIR = REPO_ROOT / "knowledge_graph" / "migrations"


def get_driver(uri, user, password):
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        return driver
    except ImportError:
        print("ERROR: Run: pip install neo4j")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Cannot connect to {uri}: {e}")
        sys.exit(1)


def run_cypher_file(session, path):
    print(f"  {path.name}...")
    cypher = path.read_text()
    # Split on semicolons, skip comments and blanks
    statements = [s.strip() for s in cypher.split(";")
                  if s.strip() and not s.strip().startswith("//")]
    for stmt in statements:
        if stmt:
            try:
                session.run(stmt)
            except Exception as e:
                print(f"    WARNING: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--uri", default="bolt://localhost:7687")
    parser.add_argument("--user", default="neo4j")
    parser.add_argument("--password", default="nf1swarm")
    args = parser.parse_args()

    driver = get_driver(args.uri, args.user, args.password)
    print(f"Connected to Neo4j at {args.uri}")

    with driver.session() as session:
        for f in sorted(SCHEMA_DIR.glob("*.cypher")):
            run_cypher_file(session, f)
        for f in sorted(SEEDS_DIR.glob("*.cypher")):
            run_cypher_file(session, f)
        for f in sorted(MIGRATIONS_DIR.glob("*.cypher")):
            run_cypher_file(session, f)

    driver.close()
    print("Bootstrap complete.")


if __name__ == "__main__":
    main()
