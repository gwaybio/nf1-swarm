#!/usr/bin/env bash
# Dump the Neo4j knowledge graph to a dated file.
# Run manually or add to cron: 0 2 * * * bash ~/repos/nf1-swarm/scripts/backup_graph.sh
set -euo pipefail

BACKUP_DIR="${HOME}/repos/nf1-swarm/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DUMP_FILE="${BACKUP_DIR}/nf1_graph_${DATE}.dump"

mkdir -p "$BACKUP_DIR"

echo "Stopping Neo4j for consistent dump..."
sudo systemctl stop neo4j

echo "Dumping to ${DUMP_FILE}..."
sudo neo4j-admin database dump neo4j --to-path="$BACKUP_DIR" --overwrite-destination=true
sudo mv "$BACKUP_DIR/neo4j.dump" "$DUMP_FILE"

echo "Restarting Neo4j..."
sudo systemctl start neo4j

# Keep only last 7 dumps
ls -t "$BACKUP_DIR"/*.dump | tail -n +8 | xargs rm -f 2>/dev/null || true

echo "Backup complete: $DUMP_FILE"
ls -lh "$BACKUP_DIR"/*.dump
