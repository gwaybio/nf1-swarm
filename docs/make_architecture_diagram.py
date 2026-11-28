
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
import numpy as np
from pathlib import Path

fig, ax = plt.subplots(figsize=(28, 20))
ax.set_xlim(0, 28)
ax.set_ylim(0, 20)
ax.axis("off")
fig.patch.set_facecolor("#0d1117")
ax.set_facecolor("#0d1117")

C = {
    "bg": "#0d1117", "panel": "#161b22", "border": "#30363d",
    "accent": "#58a6ff", "green": "#3fb950", "orange": "#f78166",
    "purple": "#bc8cff", "yellow": "#e3b341", "teal": "#39d353",
    "red": "#f85149", "gray": "#8b949e", "white": "#e6edf3",
    "dim": "#484f58",
    "dirk": "#1f6feb", "otto": "#388bfd", "archie": "#da3633",
    "stan": "#bf8700", "kim": "#238636", "rey": "#8957e5",
    "emily": "#db61a2", "milo": "#1b7c83", "graude": "#f78166",
}

MONO = "DejaVu Sans Mono"
SANS = "DejaVu Sans"

def box(ax, x, y, w, h, fc, ec, alpha=1.0, r=0.3, lw=1.8):
    b = FancyBboxPatch((x, y), w, h,
                       boxstyle=f"round,pad=0,rounding_size={r}",
                       fc=fc, ec=ec, lw=lw, alpha=alpha, zorder=3)
    ax.add_patch(b)

def txt(ax, x, y, s, color, size=9, weight="normal", ha="center", va="center",
        font=MONO, zorder=5, alpha=1.0):
    ax.text(x, y, s, color=color, fontsize=size, fontweight=weight,
            ha=ha, va=va, zorder=zorder, fontfamily=font, alpha=alpha)

def arr(ax, x1, y1, x2, y2, color, lw=1.5, alpha=0.75, rad=0.0):
    style = f"arc3,rad={rad}" if rad else "arc3,rad=0"
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color,
                                lw=lw, alpha=alpha,
                                connectionstyle=style,
                                mutation_scale=12),
                zorder=4)

# ── Icon renderer using matplotlib markers + text ────────────────────────────
def icon(ax, x, y, kind, size=320, color="#58a6ff"):
    """Draw a symbolic icon using shapes. kind in:
       db, brain, dna, lock, person, book, graph, gear, cloud, arrow_cycle,
       checklist, flask, discord, github
    """
    ms = size
    if kind == "db":          # cylinder stack
        for dy in [0, 0.18, 0.36]:
            e = mpatches.Ellipse((x, y+dy), 0.38, 0.14,
                                  fc=color, ec=color, alpha=0.85, zorder=6)
            ax.add_patch(e)
        r = mpatches.Rectangle((x-0.19, y), 0.38, 0.36,
                                 fc=color, ec="none", alpha=0.5, zorder=5)
        ax.add_patch(r)
    elif kind == "brain":     # two circles
        for dx in [-0.12, 0.12]:
            c = mpatches.Circle((x+dx, y), 0.17, fc=color, ec=color,
                                  alpha=0.8, zorder=6)
            ax.add_patch(c)
        ax.plot([x, x], [y-0.17, y+0.17], color=color, lw=2, alpha=0.6, zorder=6)
    elif kind == "dna":       # double helix (sine waves)
        t = np.linspace(0, 2*np.pi, 40)
        xs = x + 0.18*np.sin(t)
        ys = y - 0.3 + 0.6*(t/(2*np.pi))
        ax.plot(xs,  ys, color=color, lw=2.5, alpha=0.9, zorder=6)
        ax.plot(-xs+2*x, ys, color=color, lw=2.5, alpha=0.5, zorder=6)
    elif kind == "lock":      # padlock
        c = mpatches.Arc((x, y+0.15), 0.3, 0.3, angle=0,
                          theta1=0, theta2=180, color=color, lw=3, zorder=6)
        ax.add_patch(c)
        r = mpatches.FancyBboxPatch((x-0.17, y-0.15), 0.34, 0.3,
                                     boxstyle="round,pad=0.02",
                                     fc=color, ec=color, alpha=0.8, zorder=6)
        ax.add_patch(r)
    elif kind == "person":    # stick figure head+body
        c = mpatches.Circle((x, y+0.22), 0.13, fc=color, ec=color,
                              alpha=0.85, zorder=6)
        ax.add_patch(c)
        ax.plot([x, x], [y+0.09, y-0.15], color=color, lw=2.5, alpha=0.85, zorder=6)
        ax.plot([x-0.15, x+0.15], [y, y], color=color, lw=2.5, alpha=0.85, zorder=6)
        ax.plot([x, x-0.12], [y-0.15, y-0.35], color=color, lw=2.5, alpha=0.85, zorder=6)
        ax.plot([x, x+0.12], [y-0.15, y-0.35], color=color, lw=2.5, alpha=0.85, zorder=6)
    elif kind == "book":      # open book
        for dx, sign in [(-0.18, -1), (0.18, 1)]:
            r = mpatches.FancyBboxPatch((x+sign*0.02, y-0.2), 0.22, 0.4,
                                         boxstyle="round,pad=0.02",
                                         fc=color, ec=C["bg"], lw=1.5,
                                         alpha=0.75, zorder=6)
            ax.add_patch(r)
        ax.plot([x, x], [y-0.2, y+0.2], color=C["bg"], lw=2, zorder=7)
    elif kind == "graph":     # nodes + edges
        nodes = [(x-0.2, y+0.15), (x+0.2, y+0.15), (x, y-0.2), (x, y+0.35)]
        edges = [(0,1),(0,2),(1,2),(0,3),(1,3)]
        for i,j in edges:
            ax.plot([nodes[i][0], nodes[j][0]],
                    [nodes[i][1], nodes[j][1]],
                    color=color, lw=1.5, alpha=0.6, zorder=5)
        for nx, ny in nodes:
            c = mpatches.Circle((nx, ny), 0.07, fc=color, ec=C["bg"],
                                  lw=1, zorder=7)
            ax.add_patch(c)
    elif kind == "gear":      # simplified gear (circle + teeth)
        c = mpatches.Circle((x, y), 0.18, fc=color, ec=C["bg"],
                              lw=1.5, alpha=0.8, zorder=6)
        ax.add_patch(c)
        for angle in np.linspace(0, 2*np.pi, 8, endpoint=False):
            tx = x + 0.26*np.cos(angle)
            ty = y + 0.26*np.sin(angle)
            sq = mpatches.Circle((tx, ty), 0.07, fc=color, ec="none",
                                   alpha=0.8, zorder=6)
            ax.add_patch(sq)
        c2 = mpatches.Circle((x, y), 0.08, fc=C["panel"], ec="none", zorder=7)
        ax.add_patch(c2)
    elif kind == "arrow_cycle":   # circular arrows
        for start, end in [(30, 150), (210, 330)]:
            arc = mpatches.Arc((x, y), 0.42, 0.42,
                                theta1=start, theta2=end,
                                color=color, lw=3, zorder=6)
            ax.add_patch(arc)
        for angle in [150, 330]:
            rad = np.radians(angle)
            ax.annotate("", xy=(x+0.21*np.cos(rad), y+0.21*np.sin(rad)),
                        xytext=(x+0.21*np.cos(rad-0.3), y+0.21*np.sin(rad-0.3)),
                        arrowprops=dict(arrowstyle="-|>", color=color,
                                        lw=2, mutation_scale=10), zorder=7)
    elif kind == "flask":     # chemistry flask
        ax.plot([x-0.1, x+0.1], [y+0.3, y+0.3], color=color, lw=3, zorder=6)
        ax.plot([x-0.08, x-0.18, x+0.18, x+0.08],
                [y+0.1, y-0.25, y-0.25, y+0.1],
                color=color, lw=2.5, alpha=0.8, zorder=6)
        liquid = mpatches.Wedge((x, y-0.18), 0.18, 180, 360,
                                  fc=color, alpha=0.4, ec="none", zorder=5)
        ax.add_patch(liquid)
    elif kind == "checklist":
        for i, (checked, label) in enumerate([(True,"accept"),(True,"ground"),
                                               (False,"pending")]):
            yy = y + 0.2 - i*0.22
            sym = "+" if checked else "o"
            col = C["green"] if checked else C["yellow"]
            ax.text(x-0.2, yy, sym, color=col, fontsize=9,
                    ha="center", va="center", zorder=7, fontfamily=MONO)
            ax.text(x+0.0, yy, label, color=color, fontsize=6.5,
                    ha="left", va="center", zorder=7, fontfamily=MONO)
    elif kind == "discord":   # simplified D shape
        c = mpatches.Circle((x, y), 0.22, fc=color, ec="none",
                              alpha=0.85, zorder=6)
        ax.add_patch(c)
        txt(ax, x, y, "DC", C["bg"], size=9, weight="bold", zorder=8)
    elif kind == "github":
        c = mpatches.Circle((x, y), 0.22, fc=color, ec="none",
                              alpha=0.85, zorder=6)
        ax.add_patch(c)
        txt(ax, x, y, "GH", C["bg"], size=9, weight="bold", zorder=8)

# ═══════════════════════════════════════════════════════════════════════════════
# TITLE BAR
# ═══════════════════════════════════════════════════════════════════════════════
box(ax, 0.2, 18.8, 27.6, 1.0, "#0a0f1a", C["accent"], r=0.4, lw=2)
icon(ax, 1.0, 19.3, "dna", color=C["green"])
txt(ax, 14, 19.38, "nf1-swarm  —  NF1 Knowledge Graph Pipeline", C["white"],
    size=16, weight="bold")
txt(ax, 14, 19.0, "Agentic framework  ·  Routing  ·  Engineering infrastructure  ·  Evidence-graded NF1 biology & clinical outcomes",
    C["gray"], size=9.5)
icon(ax, 27.0, 19.3, "graph", color=C["accent"])

# ═══════════════════════════════════════════════════════════════════════════════
# GRAUDE — ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════════
box(ax, 9.5, 16.5, 5.5, 2.0, "#1a0a00", C["graude"], r=0.4, lw=3)
icon(ax, 10.3, 17.5, "brain", color=C["graude"])
txt(ax, 12.25, 18.2, "GRAUDE  —  Orchestrator", C["graude"], size=12, weight="bold")
txt(ax, 12.25, 17.85, "Routes tasks  ·  Tracks state  ·  Makes decisions", C["white"], size=9)
txt(ax, 12.25, 17.55, "GitHub Issues = task board  ·  Hermes message_agent = coordination", C["gray"], size=8.5)

# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC GOAL
# ═══════════════════════════════════════════════════════════════════════════════
box(ax, 20.5, 16.5, 7.2, 2.0, "#0a1a0a", C["green"], r=0.4, lw=2.5)
icon(ax, 21.3, 17.5, "dna", color=C["green"])
txt(ax, 24.1, 18.2, "PUBLIC GOAL", C["green"], size=12, weight="bold")
txt(ax, 24.1, 17.85, "NF1 Knowledge Graph", C["white"], size=10, weight="bold")
txt(ax, 24.1, 17.5, "Evidence-graded claims: biology & clinical outcomes", C["gray"], size=8.5)
arr(ax, 15.0, 17.5, 20.5, 17.5, C["green"], lw=2)
txt(ax, 17.75, 17.75, "curates toward", C["gray"], size=8)

# ═══════════════════════════════════════════════════════════════════════════════
# HERMES MESSAGE LAYER
# ═══════════════════════════════════════════════════════════════════════════════
box(ax, 0.2, 15.5, 9.0, 0.8, "#0a0a1a", C["purple"], r=0.3, lw=1.8)
icon(ax, 0.75, 15.9, "arrow_cycle", color=C["purple"])
txt(ax, 5.1, 15.95, "Hermes  message_agent  —  all inter-agent coordination  (fire-and-forget DM)", C["purple"], size=8.5, weight="bold")
txt(ax, 5.1, 15.65, "GitHub Issues = human audit trail only  ·  no @tags  ·  agents message Graude on completion", C["dim"], size=8)

# ═══════════════════════════════════════════════════════════════════════════════
# FETA PIPELINE — left column
# ═══════════════════════════════════════════════════════════════════════════════
box(ax, 0.2, 1.0, 1.1, 14.3, "#0d1520", C["border"], r=0.3, lw=1, alpha=0.6)
txt(ax, 0.75, 8.15, "F E T A", C["accent"], size=9, weight="bold", alpha=0.7)
txt(ax, 0.75, 7.75, "P I P E", C["accent"], size=9, weight="bold", alpha=0.7)
txt(ax, 0.75, 7.35, "L I N E", C["accent"], size=9, weight="bold", alpha=0.7)

agents = [
    # (y,    color,       icon_kind, name,    role_line,                   lines)
    (13.0, C["dirk"],   "book",    "DIRK",   "Stage 1 — Literature Reader",
     ["Reads PMC full text & local PDFs", "Extracts falsifiable claims",
      "Deposits pending_<hex>.json", "Catalogues cited primary papers"]),
    (10.5, C["otto"],   "graph",   "OTTO",   "Stage 2 — Ontology Grounder",
     ["CURIEs via RTX-KG2 TRAPI", "Fills semantic_triple & bel_notation",
      "Populates related_nodes", "Checks lookup.py before grounding"]),
    ( 8.0, C["archie"], "flask",   "ARCHIE", "Stage 3 — Fact-Checker",
     ["Deep-dives on disputed claims", "Archival cross-check",
      "Flags contradictions for Gregory"]),
    ( 5.5, C["stan"],   "checklist","STAN",  "Stage 4 — Statistician",
     ["confidence_score via PET-PEESE", "RoBMA-PSMA when N>=3",
      "Publication bias flags", "independence_flags on claims"]),
    ( 3.0, C["rey"],    "person",  "REY",    "Stage 5 — PI Curator",
     ["accept_claim() -> C#### assigned", "reject_claim() -> R####.json",
      "expert_opinion for consensus stmts", "Policy: primary literature only"]),
    ( 1.0, C["kim"],    "db",      "KIM",    "Stage 6 — Graph Builder",
     ["Writes accepted claims to Neo4j", "Cypher migrations 001+",
      "Validates graph assertions"]),
]

for (y, color, ik, name, role, lines) in agents:
    box(ax, 1.4, y, 6.5, 2.2, C["panel"], color, r=0.3, lw=2)
    icon(ax, 2.2, y+1.1, ik, color=color)
    txt(ax, 2.75, y+1.9, f"@{name.lower()}", color, size=10, weight="bold", ha="left")
    txt(ax, 2.75, y+1.55, role, C["white"], size=8.5, ha="left")
    for i, line in enumerate(lines):
        txt(ax, 2.75, y+1.18-i*0.28, f"• {line}", C["gray"], size=7.8, ha="left")

# Pipeline flow arrows
for y_from, y_to in [(13.0, 10.5+2.2), (10.5, 8.0+2.2),
                      (8.0, 5.5+2.2), (5.5, 3.0+2.2), (3.0, 1.0+2.2)]:
    arr(ax, 4.65, y_from, 4.65, y_to, C["accent"], lw=2)

# ═══════════════════════════════════════════════════════════════════════════════
# CLAIMS LIFECYCLE — center column
# ═══════════════════════════════════════════════════════════════════════════════
box(ax, 8.2, 1.0, 5.8, 14.3, "#0d0d1a", C["border"], r=0.3, lw=1, alpha=0.4)
txt(ax, 11.1, 15.1, "CLAIMS LIFECYCLE", C["accent"], size=11, weight="bold")

states = [
    (12.8, C["dirk"],   "pending_<hex>.json",        "Dirk deposits · no C#### yet"),
    (10.6, C["otto"],   "grounded (pending)",         "Otto fills CURIEs · triple set"),
    ( 8.2, C["rey"],    "C####.json  accepted",       "Rey accepts · moved to accepted/"),
    ( 6.5, C["red"],    "R####.json  rejected",       "Rey rejects · preserved + traceable"),
    ( 4.4, C["kim"],    "Neo4j node",                 "Kim writes Cypher migration"),
    ( 2.4, C["stan"],   "confidence_score",           "Stan scores · bias checked"),
    ( 1.0, C["green"],  "KNOWLEDGE GRAPH",            "Queryable NF1 evidence store"),
]

for (y, color, title, desc) in states:
    box(ax, 8.4, y, 5.4, 1.5, C["panel"], color, r=0.25, lw=2)
    txt(ax, 11.1, y+1.15, title, color, size=9, weight="bold")
    txt(ax, 11.1, y+0.65, desc, C["gray"], size=8.5)
    # small icon
    if color == C["dirk"]:    icon(ax, 8.9,  y+0.75, "book",    color=color)
    elif color == C["otto"]:  icon(ax, 8.9,  y+0.75, "graph",   color=color)
    elif color == C["kim"]:   icon(ax, 8.9,  y+0.75, "db",      color=color)
    elif color == C["stan"]:  icon(ax, 8.9,  y+0.75, "checklist", color=color)
    elif color == C["green"]: icon(ax, 8.9,  y+0.75, "dna",     color=color)

# flow arrows
for (y_from, y_to) in [(12.8, 10.6+1.5),(10.6, 8.2+1.5),(8.2, 4.4+1.5),
                        (4.4, 2.4+1.5),(2.4, 1.0+1.5)]:
    arr(ax, 11.1, y_from, 11.1, y_to, C["accent"], lw=1.8)

# accept / reject split — rejected routes right to avoid crossing accepted→Neo4j path
arr(ax, 11.1, 10.6, 11.1, 8.2+1.5, C["green"], lw=1.5)   # accepted: straight down
arr(ax, 11.1, 10.6, 14.5, 10.6,    C["red"],   lw=1.5)   # rejected: right then down
arr(ax, 14.5, 10.6, 14.5, 6.5+1.5, C["red"],   lw=1.5)
txt(ax, 10.1, 9.5,  "accept", C["green"], size=8)
txt(ax, 12.5, 11.1, "reject", C["red"],   size=8)

# resurrection arc
ax.annotate("", xy=(8.4, 12.8+0.75), xytext=(8.4, 6.5+0.75),
            arrowprops=dict(arrowstyle="-|>", color=C["purple"], lw=1.5,
                            alpha=0.7, connectionstyle="arc3,rad=0.5",
                            mutation_scale=12), zorder=4)
txt(ax, 7.5, 9.8, "resurrect\nR->pending", C["purple"], size=7.5)

# ═══════════════════════════════════════════════════════════════════════════════
# INFRASTRUCTURE — right column
# ═══════════════════════════════════════════════════════════════════════════════
box(ax, 14.3, 1.0, 13.5, 14.3, "#0d0d0d", C["border"], r=0.3, lw=1, alpha=0.4)
txt(ax, 21.05, 15.1, "INFRASTRUCTURE & MEMORY", C["accent"], size=11, weight="bold")

# Emily
box(ax, 14.5, 12.5, 6.0, 2.5, C["panel"], C["emily"], r=0.3, lw=2)
icon(ax, 15.3, 13.75, "gear", color=C["emily"])
txt(ax, 15.9, 14.75, "@emily  —  Software Engineer", C["emily"], size=10, weight="bold", ha="left")
txt(ax, 15.9, 14.35, "CI/CD · GitHub Actions · Discord webhooks", C["white"], size=8.5, ha="left")
txt(ax, 15.9, 14.0,  "SQLite lookup layer · PDF text cleaner", C["gray"], size=8, ha="left")
txt(ax, 15.9, 13.65, "Citation resolver · source_quote schema", C["gray"], size=8, ha="left")
txt(ax, 15.9, 13.3,  "Neo4j health · concurrency fix (PR #61)", C["dim"], size=7.5, ha="left")

# Milo
box(ax, 20.8, 12.5, 6.8, 2.5, C["panel"], C["milo"], r=0.3, lw=2)
icon(ax, 21.5, 13.75, "arrow_cycle", color=C["milo"])
txt(ax, 22.1, 14.75, "@milo  —  Memory & Context", C["milo"], size=10, weight="bold", ha="left")
txt(ax, 22.1, 14.35, "Nightly dream: merge · score · prune · rebuild", C["white"], size=8.5, ha="left")
txt(ax, 22.1, 14.0,  "graude_briefing.md — session-start anchor", C["gray"], size=8, ha="left")
txt(ax, 22.1, 13.65, "issues_digest.md · pipeline_state.md", C["gray"], size=8, ha="left")
txt(ax, 22.1, 13.3,  "Nightly reconcile of swarm.db", C["dim"], size=7.5, ha="left")

# Neo4j
box(ax, 14.5, 9.8, 6.0, 2.4, C["panel"], C["accent"], r=0.3, lw=2)
icon(ax, 15.3, 11.0, "db", color=C["accent"])
txt(ax, 15.9, 11.95, "Neo4j  —  bolt://localhost:7687", C["accent"], size=10, weight="bold", ha="left")
txt(ax, 15.9, 11.55, "28+ accepted claims in graph", C["white"], size=8.5, ha="left")
txt(ax, 15.9, 11.2,  "Cypher migrations 001+", C["gray"], size=8, ha="left")
txt(ax, 15.9, 10.85, "Graph assertions in CI (graph-health job)", C["gray"], size=8, ha="left")
txt(ax, 15.9, 10.5,  "APOC plugin · Counter nodes for IDs", C["dim"], size=7.5, ha="left")

# SQLite
box(ax, 20.8, 9.8, 6.8, 2.4, C["panel"], C["yellow"], r=0.3, lw=2)
icon(ax, 21.5, 11.0, "db", color=C["yellow"])
txt(ax, 22.1, 11.95, "SQLite  —  data/swarm.db  [planned]", C["yellow"], size=10, weight="bold", ha="left")
txt(ax, 22.1, 11.55, "papers(pmid,doi,title,status,issue#)", C["white"], size=8.5, ha="left")
txt(ax, 22.1, 11.2,  "claims(pending_id,claim_id,triple,status)", C["gray"], size=8, ha="left")
txt(ax, 22.1, 10.85, "Triple index for semantic dedup", C["gray"], size=8, ha="left")
txt(ax, 22.1, 10.5,  "scripts/lookup.py CLI  —  JSON output", C["dim"], size=7.5, ha="left")

# GitHub
box(ax, 14.5, 7.1, 6.0, 2.4, C["panel"], C["white"], r=0.3, lw=2)
icon(ax, 15.3, 8.3, "github", color=C["white"])
txt(ax, 15.9, 9.25, "GitHub  —  gwaybio/nf1-swarm", C["white"], size=10, weight="bold", ha="left")
txt(ax, 15.9, 8.85, "Issues = task board (paper-queue, claims)", C["white"], size=8.5, ha="left")
txt(ax, 15.9, 8.5,  "PRs: fast-path (Emily) + TCB (Gregory)", C["gray"], size=8, ha="left")
txt(ax, 15.9, 8.15, "CODEOWNERS: scientific-governance/ claim rules, harness, snapshots", C["gray"], size=8, ha="left")
txt(ax, 15.9, 7.8,  "CodeRabbit reviews all PRs", C["dim"], size=7.5, ha="left")

# Discord
box(ax, 20.8, 7.1, 6.8, 2.4, C["panel"], C["purple"], r=0.3, lw=2)
icon(ax, 21.5, 8.3, "discord", color=C["purple"])
txt(ax, 22.1, 9.25, "Discord  —  nf1-swarm server", C["purple"], size=10, weight="bold", ha="left")
txt(ax, 22.1, 8.85, "Graude bot live  ·  gateway running", C["white"], size=8.5, ha="left")
txt(ax, 22.1, 8.5,  "CI failure + dream failure -> webhook", C["gray"], size=8, ha="left")
txt(ax, 22.1, 8.15, "PR-opened events -> notification", C["gray"], size=8, ha="left")
txt(ax, 22.1, 7.8,  "Gregory DMs Graude directly", C["dim"], size=7.5, ha="left")

# TCB governance
box(ax, 14.5, 4.5, 6.0, 2.3, "#1a0a1a", C["purple"], r=0.3, lw=2)
icon(ax, 15.3, 5.65, "lock", color=C["purple"])
txt(ax, 15.9, 6.55, "TCB  —  Gregory-gated", C["purple"], size=10, weight="bold", ha="left")
txt(ax, 15.9, 6.15, "scientific-governance/ rules  ·  harness", C["white"], size=8.5, ha="left")
txt(ax, 15.9, 5.8,  "approved snapshots  ·  .github/CODEOWNERS", C["gray"], size=8, ha="left")
txt(ax, 15.9, 5.45, "claim_contract.yaml  ·  approval_checker.py", C["gray"], size=8, ha="left")
txt(ax, 15.9, 5.1,  "PRs require Gregory merge — never self-merge", C["dim"], size=7.5, ha="left")

# Agent souls
box(ax, 20.8, 4.5, 6.8, 2.3, "#0a1a0a", C["green"], r=0.3, lw=2)
icon(ax, 21.5, 5.65, "person", color=C["green"])
txt(ax, 22.1, 6.55, "Agent Souls  (9 agents)", C["green"], size=10, weight="bold", ha="left")
txt(ax, 22.1, 6.15, "SOUL.md · profile.yaml · gitconfig", C["white"], size=8.5, ha="left")
txt(ax, 22.1, 5.8,  ".hermes/profiles/<agent>/", C["gray"], size=8, ha="left")
txt(ax, 22.1, 5.45, "Co-authored-by: Gregory Way in every commit", C["gray"], size=8, ha="left")
txt(ax, 22.1, 5.1,  "Graude Dirk Otto Archie Stan Kim Rey Emily Milo", C["dim"], size=7.5, ha="left")

# Reading queue policy
box(ax, 14.5, 1.8, 6.0, 2.4, "#1a1a0a", C["yellow"], r=0.3, lw=2)
icon(ax, 15.3, 3.0, "book", color=C["yellow"])
txt(ax, 15.9, 3.95, "Reading Queue Policy", C["yellow"], size=10, weight="bold", ha="left")
txt(ax, 15.9, 3.55, "Reviews -> catalogue cited papers only", C["white"], size=8.5, ha="left")
txt(ax, 15.9, 3.2,  "No claims from reviews (Rey: primary-only)", C["gray"], size=8, ha="left")
txt(ax, 15.9, 2.85, "Otto CURIEs -> grounding_hints in queue", C["gray"], size=8, ha="left")
txt(ax, 15.9, 2.5,  "Consensus stmts -> expert_opinion (primary)", C["dim"], size=7.5, ha="left")
txt(ax, 15.9, 2.15, "lookup.py dedup before opening paper issue", C["dim"], size=7.5, ha="left")
txt(ax, 15.9, 1.85, "source_type=review_extraction in swarm.db", C["dim"], size=7.5, ha="left")

# Swarm memory
box(ax, 20.8, 1.8, 6.8, 2.4, "#0d1a1a", C["teal"], r=0.3, lw=2)
icon(ax, 21.5, 3.0, "arrow_cycle", color=C["teal"])
txt(ax, 22.1, 3.95, "Swarm Memory", C["teal"], size=10, weight="bold", ha="left")
txt(ax, 22.1, 3.55, "swarm_memory/episodes/  ·  registry.md", C["white"], size=8.5, ha="left")
txt(ax, 22.1, 3.2,  "pruning_log.md  ·  performance/", C["gray"], size=8, ha="left")
txt(ax, 22.1, 2.85, "Scoring: I = alpha*R + beta*F + gamma*S", C["gray"], size=8, ha="left")
txt(ax, 22.1, 2.5,  "Git log = primary episodic memory store", C["dim"], size=7.5, ha="left")
txt(ax, 22.1, 2.15, "Milo dreams nightly at 02:00 UTC", C["dim"], size=7.5, ha="left")

# separator line between infra halves
ax.plot([20.75, 20.75], [1.2, 15.2], color=C["border"], lw=1, alpha=0.5, zorder=3)

# ── Graude routing arrows to pipeline ────────────────────────────────────────
for y_target in [14.1, 11.6, 9.1, 6.6, 4.1, 2.1]:
    arr(ax, 9.5, 17.0, 7.9, y_target, C["graude"], lw=1.0, alpha=0.3)

# Graude routing to Emily/Milo
arr(ax, 14.5, 17.5, 17.5, 15.0, C["emily"], lw=1.0, alpha=0.35)
arr(ax, 14.5, 17.2, 24.0, 15.0, C["milo"],  lw=1.0, alpha=0.35)

# Pipeline -> Neo4j
arr(ax, 7.9, 1.6, 15.5, 9.8, C["kim"], lw=1.5, alpha=0.5)

# SQLite lookup (Dirk checks before depositing)
arr(ax, 8.2, 13.9, 20.8, 11.0, C["yellow"], lw=1.2, alpha=0.4, rad=-0.2)
txt(ax, 15.5, 13.2, "lookup.py check", C["yellow"], size=7.5, alpha=0.7)

# Neo4j -> Knowledge Graph (goal)
arr(ax, 20.5, 11.0, 23.0, 16.5, C["green"], lw=1.8, alpha=0.6)

plt.tight_layout(pad=0.3)
import argparse as _ap, sys as _sys
_p = _ap.ArgumentParser(add_help=False)
_p.add_argument("--output", default=None)
_args, _ = _p.parse_known_args()
if _args.output:
    outpath = _args.output
else:
    outpath = str(Path(__file__).parent / "nf1_swarm_diagram.png")
Path(outpath).parent.mkdir(parents=True, exist_ok=True)
plt.savefig(outpath, dpi=150, bbox_inches="tight",
            facecolor=fig.get_facecolor())
plt.close()
print(outpath)
