#!/usr/bin/env bash
# Restore Neo4j from a dump file.
# Usage: bash scripts/restore_graph.sh backups/nf1_graph_20261117_120000.dump
set -euo pipefail

DUMP_FILE="${1:?Usage: restore_graph.sh <dump_file>}"

echo "Stopping Neo4j..."
sudo systemctl stop neo4j

echo "Restoring from ${DUMP_FILE}..."
sudo neo4j-admin database load neo4j --from-path="$(dirname "$DUMP_FILE")" \
  --overwrite-destination=true

echo "Restarting Neo4j..."
sudo systemctl start neo4j && sleep 5

echo "Restore complete. Verify with:"
echo "  cd ~/repos/nf1-swarm && uv run python scientific-governance/claim-validation-scripts/approval_checker.py"
