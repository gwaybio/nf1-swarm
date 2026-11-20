"""
milo_dream.py — Nightly offline memory consolidation for the nf1-swarm.

Runs at 02:00 UTC via GitHub Actions cron (daily-dream.yml).
Four phases: merge → score → prune → rebuild.

Scoring function (Park et al. 2023, adapted):
    I(m, t) = α·R(m,t) + β·F(m) + γ·S(m)

    R = recency   (1.0 for today, decays by 0.1/day, floor 0.0)
    F = frequency (access/reference count, normalized 0–1)
    S = semantic relevance (NF1-core proximity: 1.0 for gene/protein/pathway
                            claims with evidence_strength>=4, else 0.3)

Entries scoring below PRUNE_THRESHOLD are logged to pruning_log.md.
Nothing is deleted without an audit trail entry.
"""
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SWARM_MEM = REPO_ROOT / "swarm_memory"
EPISODES_DIR = SWARM_MEM / "episodes"
REGISTRY_PATH = SWARM_MEM / "registry.md"
PRUNING_LOG = SWARM_MEM / "pruning_log.md"
ISSUES_DIGEST = SWARM_MEM / "issues_digest.md"
PIPELINE_STATE = SWARM_MEM / "pipeline_state.md"
PERFORMANCE_DIR = SWARM_MEM / "performance"
CLAIMS_ACCEPTED = REPO_ROOT / "claims" / "accepted"
CLAIMS_PENDING = REPO_ROOT / "claims" / "pending"
CLAIMS_REJECTED = REPO_ROOT / "claims" / "rejected"
PROCESSED_MD = REPO_ROOT / "literature" / "processed.md"
QUEUE_MD = REPO_ROOT / "literature" / "queue.md"

PRUNE_THRESHOLD = 0.25  # entries below this score are flagged (not deleted)
ALPHA, BETA, GAMMA = 0.3, 0.3, 0.4  # recency, frequency, semantic weights

AGENTS = ["graude", "dirk", "otto", "archie", "stan", "kim", "rey", "emily", "milo"]


# ── Scoring ───────────────────────────────────────────────────────────────────

def recency_score(mtime_epoch: float) -> float:
    """Linear decay: 1.0 today → 0.0 at 10 days old."""
    now = datetime.now(timezone.utc).timestamp()
    days_old = (now - mtime_epoch) / 86400
    return max(0.0, 1.0 - days_old * 0.1)


def frequency_score(path: Path, git_log: str) -> float:
    """Rough frequency: how many times is this file referenced in git log."""
    name = path.name
    count = git_log.count(name)
    return min(1.0, count / 10.0)  # normalize: 10+ refs = 1.0


def semantic_score(path: Path) -> float:
    """High relevance for core NF1 biology episodes and high-strength claims."""
    text = path.read_text(errors="replace").lower()
    core_terms = ["nf1", "neurofibromin", "ras/mapk", "evidence_strength: 5",
                  "evidence_strength: 4", "selumetinib", "encodes", "inhibits"]
    hits = sum(1 for t in core_terms if t in text)
    return min(1.0, hits / 3.0)


def importance_score(path: Path, git_log: str) -> float:
    mtime = path.stat().st_mtime
    r = recency_score(mtime)
    f = frequency_score(path, git_log)
    s = semantic_score(path)
    return ALPHA * r + BETA * f + GAMMA * s


# ── Git helpers ───────────────────────────────────────────────────────────────

def git_log_oneline() -> str:
    result = subprocess.run(
        ["git", "log", "--oneline", "--all"],
        cwd=REPO_ROOT, capture_output=True, text=True
    )
    return result.stdout


def git_log_for_agent(agent: str) -> list[str]:
    result = subprocess.run(
        ["git", "log", f"--author={agent}", "--oneline", "--all", "-20"],
        cwd=REPO_ROOT, capture_output=True, text=True
    )
    return result.stdout.strip().splitlines()


def count_claims(directory: Path) -> int:
    return len(list(directory.glob("*.json"))) if directory.exists() else 0


# ── Phase 1: Merge (deduplicate episodes) ─────────────────────────────────────

def phase_merge() -> int:
    """Remove exact-duplicate episode files (same content, different names)."""
    seen = {}
    removed = 0
    for f in sorted(EPISODES_DIR.glob("*.md")):
        content = f.read_text(errors="replace")
        if content in seen:
            print(f"  MERGE  duplicate: {f.name} == {seen[content]}")
            removed += 1
            # Log before action
            _log_pruning(f, 0.0, f"exact duplicate of {seen[content]}", "merged")
            f.unlink()
        else:
            seen[content] = f.name
    return removed


# ── Phase 2: Score ────────────────────────────────────────────────────────────

def phase_score(git_log: str) -> dict[Path, float]:
    scores = {}
    for f in sorted(EPISODES_DIR.glob("*.md")):
        scores[f] = importance_score(f, git_log)
        print(f"  SCORE  {f.name}: {scores[f]:.3f}")
    return scores


# ── Phase 3: Prune ────────────────────────────────────────────────────────────

def phase_prune(scores: dict[Path, float]) -> int:
    flagged = 0
    for path, score in scores.items():
        if score < PRUNE_THRESHOLD:
            print(f"  FLAG   {path.name} (score={score:.3f} < {PRUNE_THRESHOLD})")
            _log_pruning(path, score, "below importance threshold", "flagged-for-review")
            flagged += 1
    return flagged


def _log_pruning(path: Path, score: float, reason: str, action: str):
    now = datetime.now(timezone.utc).isoformat()
    entry = f"\n{now} | {path.name} | score={score:.3f} | {reason} | {action}"
    with open(PRUNING_LOG, "a") as f:
        f.write(entry)


# ── Phase 4: Rebuild registry ─────────────────────────────────────────────────

def phase_rebuild():
    """Rewrite registry.md with current per-agent status from git + claims."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    pending = count_claims(CLAIMS_PENDING)
    accepted = count_claims(CLAIMS_ACCEPTED)

    lines = [f"# Swarm Agent Registry\n",
             f"Maintained by Milo. Last dream: {now}\n",
             f"Graph: {accepted} accepted claims, {pending} pending.\n",
             "---\n"]

    for agent in AGENTS:
        recent = git_log_for_agent(agent)
        last_task = recent[0] if recent else "(none yet)"
        log_path = Path(f"/home/gway/.hermes/profiles/{agent}/logs/agent.log")
        health = _check_latency_health(log_path)
        lines.append(f"## @{agent}\n")
        lines.append(f"Last commit: {last_task}\n")
        lines.append(f"Context health: {health}\n\n")

    REGISTRY_PATH.write_text("".join(lines))
    print(f"  REBUILD  registry.md updated ({len(AGENTS)} agents)")


def _check_latency_health(log_path: Path) -> str:
    """Return OK / WARN / IDLE based on recent latency in agent log.
    Falls back to commit recency when no log exists (most agents).
    """
    if log_path.exists():
        try:
            lines = log_path.read_text(errors="replace").splitlines()
            latencies = []
            for line in lines[-200:]:
                if "latency=" in line:
                    try:
                        lat = float(line.split("latency=")[1].split("s")[0])
                        latencies.append(lat)
                    except (ValueError, IndexError):
                        pass
            if latencies:
                avg = sum(latencies) / len(latencies)
                recent_avg = sum(latencies[-5:]) / min(5, len(latencies))
                if recent_avg > avg * 2:
                    return f"WARN (recent avg {recent_avg:.1f}s vs baseline {avg:.1f}s)"
                return f"OK (avg {avg:.1f}s)"
        except Exception:
            pass
    # Fallback: use git commit recency as activity proxy
    return _health_from_commit_recency(log_path.parent.name.rstrip("s"))


def _health_from_commit_recency(agent: str) -> str:
    """Infer health from how recently an agent committed."""
    result = subprocess.run(
        ["git", "log", f"--author={agent}", "--format=%cd", "--date=iso-strict", "-1"],
        cwd=REPO_ROOT, capture_output=True, text=True
    )
    date_str = result.stdout.strip()
    if not date_str:
        return "idle (no commits yet)"
    try:
        from datetime import datetime, timezone
        last = datetime.fromisoformat(date_str)
        days_ago = (datetime.now(timezone.utc) - last).days
        if days_ago == 0:
            return "active (committed today)"
        elif days_ago <= 2:
            return f"OK (committed {days_ago}d ago)"
        elif days_ago <= 7:
            return f"quiet ({days_ago}d since last commit)"
        else:
            return f"IDLE ({days_ago}d since last commit)"
    except Exception:
        return "UNKNOWN"


# ── Phase 5: Compact agent briefings ─────────────────────────────────────────

def _gh_open_issues() -> list[dict]:
    """Fetch open GitHub issues via gh CLI. Returns list of dicts."""
    result = subprocess.run(
        ["gh", "issue", "list", "--state", "open",
         "--json", "number,title,labels,createdAt", "--limit", "100"],
        cwd=REPO_ROOT, capture_output=True, text=True
    )
    if result.returncode != 0:
        return []
    try:
        return json.loads(result.stdout)
    except Exception:
        return []


def _age_days(iso_str: str) -> int:
    try:
        created = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - created).days
    except Exception:
        return 0


def phase_briefings():
    """Generate compact, token-efficient briefing artifacts for agents.

    Writes:
      swarm_memory/issues_digest.md   — compact open-issues table (~10 tokens/row)
      swarm_memory/pipeline_state.md  — claim pipeline snapshot
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    issues = _gh_open_issues()

    # ── issues_digest.md ──────────────────────────────────────────────────────
    # Graude reads this instead of raw gh issue list JSON (saves 50-200 tokens/issue).
    # Format: #N  ASSIGNEE  AGE  short title
    lines = [
        "# Open Issues Digest\n",
        f"Generated by Milo at {now}. Load this file, not raw gh issue list.\n\n",
        f"{'#':>4}  {'agent':8}  {'age':>5}  title\n",
        f"{'----':>4}  {'--------':8}  {'-----':>5}  -----\n",
    ]
    for iss in sorted(issues, key=lambda x: x["number"]):
        labels = {lb["name"] for lb in iss.get("labels", [])}
        # Determine assigned agent from labels
        agent_labels = {"dirk", "otto", "archie", "stan", "kim", "rey", "emily", "milo"}
        assigned = next((lb for lb in agent_labels if lb in labels), "graude")
        age = _age_days(iss.get("createdAt", ""))
        # Truncate title to 70 chars — the key fix that prevents token bloat
        title = iss["title"][:70]
        lines.append(f"#{iss['number']:>4}  {assigned:8}  {age:>4}d  {title}\n")

    if not issues:
        lines.append("(no open issues)\n")
    ISSUES_DIGEST.write_text("".join(lines))

    # ── pipeline_state.md ────────────────────────────────────────────────────
    # Answers "what is the swarm working on right now" in under 100 tokens.
    pending = count_claims(CLAIMS_PENDING)
    accepted = count_claims(CLAIMS_ACCEPTED)
    rejected = count_claims(CLAIMS_REJECTED) if CLAIMS_REJECTED.exists() else 0
    total = pending + accepted + rejected

    # Papers: count by label
    paper_issues = [i for i in issues if any(lb["name"] == "paper" for lb in i.get("labels", []))]
    blocked = sum(1 for i in paper_issues if "PAYWALLED" in i["title"].upper() or "BLOCKED" in i["title"].upper())

    # Literature queue
    papers_processed = 0
    if PROCESSED_MD.exists():
        content = PROCESSED_MD.read_text(errors="replace")
        # Count non-header, non-empty rows in the table
        papers_processed = sum(1 for ln in content.splitlines()
                               if ln.strip().startswith("|") and "---" not in ln
                               and "Paper" not in ln and ln.strip() != "|")

    p_lines = [
        "# Pipeline State\n",
        f"Generated by Milo at {now}\n\n",
        "## Claim counts\n",
        f"  pending:  {pending}\n",
        f"  accepted: {accepted}\n",
        f"  rejected: {rejected}\n",
        f"  total:    {total}\n\n",
        "## Literature queue\n",
        f"  papers processed: {papers_processed}\n",
        f"  papers queued (open issues): {len(paper_issues)}\n",
        f"  blocked (paywalled): {blocked}\n\n",
        "## Open issues by agent\n",
    ]
    by_agent: dict[str, int] = {}
    for iss in issues:
        labels = {lb["name"] for lb in iss.get("labels", [])}
        agent_labels = {"dirk", "otto", "archie", "stan", "kim", "rey", "emily", "milo"}
        assigned = next((lb for lb in agent_labels if lb in labels), "graude")
        by_agent[assigned] = by_agent.get(assigned, 0) + 1
    for agent, count in sorted(by_agent.items()):
        p_lines.append(f"  {agent}: {count} open\n")

    PIPELINE_STATE.write_text("".join(p_lines))
    print(f"  BRIEF  issues_digest.md ({len(issues)} issues) + pipeline_state.md written")


# ── Performance update ────────────────────────────────────────────────────────

def update_performance():
    """Update claim_quality.json with current counts."""
    path = PERFORMANCE_DIR / "claim_quality.json"
    try:
        data = json.loads(path.read_text())
    except Exception:
        data = {}

    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    data["total_claims_pending"] = count_claims(CLAIMS_PENDING)
    data["total_claims_accepted"] = count_claims(CLAIMS_ACCEPTED)

    # Track history
    history = data.get("acceptance_rate_history", [])
    total = data["total_claims_accepted"] + data["total_claims_pending"]
    rate = data["total_claims_accepted"] / total if total > 0 else None
    history.append({"date": data["last_updated"], "rate": rate,
                    "accepted": data["total_claims_accepted"]})
    data["acceptance_rate_history"] = history[-90:]  # keep 90 days

    path.write_text(json.dumps(data, indent=2))
    print(f"  PERF   claim_quality.json updated ({data['total_claims_accepted']} accepted)")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"\n=== Milo dreaming — {datetime.now(timezone.utc).isoformat()} ===\n")
    EPISODES_DIR.mkdir(parents=True, exist_ok=True)

    git_log = git_log_oneline()

    print("Phase 1: Merge")
    merged = phase_merge()

    print("\nPhase 2: Score")
    scores = phase_score(git_log)

    print("\nPhase 3: Prune")
    flagged = phase_prune(scores)

    print("\nPhase 4: Rebuild")
    phase_rebuild()

    print("\nPhase 5: Briefings")
    phase_briefings()

    print("\nPerformance update")
    update_performance()

    print(f"\n=== Dream complete: {merged} merged, {flagged} flagged for review ===\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
