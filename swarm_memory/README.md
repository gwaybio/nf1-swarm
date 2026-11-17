# Swarm Memory Store

Managed by Milo. This directory is the shared episodic and operational memory
for the nf1-swarm. It is git-tracked — the commit history of this directory
is itself episodic memory about memory management.

## Structure

| Path | Purpose | Writer | Readers |
|------|---------|--------|---------|
| `registry.md` | DACS ≤200-token status per agent | Milo | Graude, all agents |
| `pruning_log.md` | Audit trail of all pruning decisions | Milo | Graude, Gregory |
| `episodes/` | Completed work-phase summaries | Milo | All agents |
| `performance/claim_quality.json` | Claim acceptance trends | Milo | Graude, Rey |
| `performance/agent_latency.json` | Per-agent API latency baselines | Milo | Graude, Emily |

## Retrieval

Any agent can query this store by messaging @milo:
- "What has Dirk processed?" → episodes/ + git log
- "What is the current confidence_score for C0001?" → claims/accepted/C0001.json
- "What is Dirk's context state?" → registry.md

## Dreaming schedule

Nightly at 02:00 UTC. Script: `swarm_memory/milo_dream.py`
Phases: merge → score → prune → rebuild index
