#!/usr/bin/env python3
"""Render the SVG cards for the d-aldana profile README.

Usage:
    python scripts/build.py            # render everything (fetches live data if GITHUB_TOKEN is set)
    python scripts/build.py --sample   # render with sample data, no network

Only the standard library is used, so the GitHub Action needs no installs.
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path

USER = os.environ.get("GH_USER", "d-aldana")
NAME = "Dustin Aldana"
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"

BG = "#0b1020"
PANEL_STROKE = "#1e293b"
INK = "#e2e8f0"
MUTED = "#64748b"
DIM = "#334155"


def x(s):
    return escape(str(s), quote=True)


def pct(t, total):
    return f"{max(0.0, min(100.0, t / total * 100)):.3f}%"


# --------------------------------------------------------------------------
# 1. The agent pipeline (hero animation)
# --------------------------------------------------------------------------
STAGES = [
    ("≡", "Ticket", "Jira intake", "#94a3b8",
     "PROJ-142 picked up · parsing acceptance criteria"),
    ("◇", "Architect", "planning agent", "#a78bfa",
     "architect › plan drafted: 3 files, 1 migration, API contract"),
    ("</>", "Coder", "coding agent", "#60a5fa",
     "coder › implementation + tests written · 14 passed"),
    ("◉", "Reviewer", "review agent", "#fbbf24",
     "reviewer › 2 suggestions applied · no blocking issues"),
    ("✎", "Human", "final review", "#f472b6",
     "human › diff reviewed · approved"),
    ("✓", "Merged", "pull request", "#34d399",
     "PR #142 merged into main ✓"),
]


def render_pipeline():
    W, H = 900, 330
    T = 13.0                       # loop length (s)
    STEP, HOLD = 2.0, 1.5          # time per stop, time spent holding at a stop
    END = 12.4                     # when the card starts fading out
    x0, x1, track_y, card_y = 80, 820, 168, 108
    n = len(STAGES)
    xs = [x0 + i * (x1 - x0) / (n - 1) for i in range(n)]
    arrive = [i * STEP for i in range(n)]
    span = x1 - x0

    css = [f"""
    .t{{font-family:{SANS}}} .m{{font-family:{MONO}}}
    .card{{animation:move {T}s infinite}}
    .bar{{stroke-dasharray:{span};animation:fill {T}s infinite}}
    .lit,.ring,.msg{{opacity:0}}
    .ring{{transform-box:fill-box;transform-origin:center}}
    """]

    # card position keyframes: arrive at stop i, hold, slide to next
    move, fill = [], []
    for i, a in enumerate(arrive):
        for t in (a, min(a + HOLD, END)):
            move.append(f"{pct(t, T)}{{transform:translate({xs[i]:.1f}px,{card_y}px);opacity:1}}")
            fill.append(f"{pct(t, T)}{{stroke-dashoffset:{span - (xs[i] - x0):.1f}}}")
    move.insert(0, f"0%{{transform:translate({xs[0]:.1f}px,{card_y}px);opacity:0}}")
    move[1] = f"{pct(0.3, T)}{{transform:translate({xs[0]:.1f}px,{card_y}px);opacity:1}}"
    move.append(f"100%{{transform:translate({xs[-1]:.1f}px,{card_y - 14}px);opacity:0}}")
    fill.append(f"100%{{stroke-dashoffset:0}}")
    css.append("@keyframes move{" + "".join(move) + "}")
    css.append("@keyframes fill{" + "".join(fill) + "}")
    css.append(".card,.bar{animation-timing-function:cubic-bezier(.65,0,.35,1)}")

    for i, a in enumerate(arrive):
        lit = (f"0%{{opacity:0}}{pct(max(a - .01, 0), T)}{{opacity:0}}"
               f"{pct(a + .25, T)}{{opacity:1}}{pct(END, T)}{{opacity:1}}100%{{opacity:0}}")
        ring = (f"0%{{opacity:0;transform:scale(1)}}{pct(max(a - .01, 0), T)}{{opacity:0;transform:scale(1)}}"
                f"{pct(a, T)}{{opacity:.9;transform:scale(1)}}{pct(a + 1.1, T)}{{opacity:0;transform:scale(1.9)}}"
                f"100%{{opacity:0;transform:scale(1.9)}}")
        stop = arrive[i + 1] if i + 1 < n else END
        msg = (f"0%{{opacity:0}}{pct(max(a - .01, 0), T)}{{opacity:0}}{pct(a + .2, T)}{{opacity:1}}"
               f"{pct(stop - .15, T)}{{opacity:1}}{pct(stop, T)}{{opacity:0}}100%{{opacity:0}}")
        css.append(f"@keyframes lit{i}{{{lit}}}@keyframes ring{i}{{{ring}}}@keyframes msg{i}{{{msg}}}")
        css.append(f".lit{i}{{animation:lit{i} {T}s infinite}}.ring{i}{{animation:ring{i} {T}s infinite}}"
                   f".msg{i}{{animation:msg{i} {T}s infinite}}")

    css.append("@media (prefers-reduced-motion:reduce){.card,.bar,.lit,.ring,.msg{animation:none}"
               ".lit,.msg5{opacity:1}.bar{stroke-dashoffset:0}.card{opacity:0}}")

    stops = [f'<stop offset="{i / (n - 1):.2f}" stop-color="{s[3]}"/>' for i, s in enumerate(STAGES)]
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'role="img" aria-label="Animated diagram: a Jira ticket moves through architect, coding and review '
           f'agents, then human review, and lands as a merged pull request.">',
           f"<style>{''.join(css)}</style>",
           f'<defs><linearGradient id="g" x1="{x0}" x2="{x1}" gradientUnits="userSpaceOnUse">{"".join(stops)}'
           f'</linearGradient></defs>',
           f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="{BG}" stroke="{PANEL_STROKE}"/>',
           f'<text class="t" x="32" y="44" fill="{INK}" font-size="16" font-weight="600">Ticket → pull request, '
           f'handled by agents</text>',
           f'<text class="m" x="{W - 32}" y="44" fill="{MUTED}" font-size="12" text-anchor="end">'
           f'multi-agent workflow · claude</text>',
           f'<line x1="{x0}" y1="{track_y}" x2="{x1}" y2="{track_y}" stroke="{PANEL_STROKE}" stroke-width="3" '
           f'stroke-linecap="round"/>',
           f'<line class="bar" x1="{x0}" y1="{track_y}" x2="{x1}" y2="{track_y}" stroke="url(#g)" '
           f'stroke-width="3" stroke-linecap="round"/>']

    for i, (glyph, name, sub, color, _) in enumerate(STAGES):
        cx = xs[i]
        gsize = 15 if len(glyph) > 1 else 19
        out += [
            f'<circle class="ring ring{i}" cx="{cx:.1f}" cy="{track_y}" r="26" fill="none" stroke="{color}" '
            f'stroke-width="2"/>',
            f'<circle cx="{cx:.1f}" cy="{track_y}" r="26" fill="#0f172a" stroke="{DIM}" stroke-width="2"/>',
            f'<circle class="lit lit{i}" cx="{cx:.1f}" cy="{track_y}" r="26" fill="{color}" fill-opacity=".14" '
            f'stroke="{color}" stroke-width="2"/>',
            f'<text class="m" x="{cx:.1f}" y="{track_y + gsize * .36:.1f}" fill="{color}" font-size="{gsize}" '
            f'font-weight="700" text-anchor="middle">{x(glyph)}</text>',
            f'<text class="t" x="{cx:.1f}" y="{track_y + 50}" fill="{INK}" font-size="13" font-weight="600" '
            f'text-anchor="middle">{x(name)}</text>',
            f'<text class="m" x="{cx:.1f}" y="{track_y + 67}" fill="{MUTED}" font-size="11" '
            f'text-anchor="middle">{x(sub)}</text>',
        ]

    # the travelling ticket card
    out += [
        '<g class="card">',
        f'<line x1="0" y1="17" x2="0" y2="{track_y - card_y - 27}" stroke="{DIM}" stroke-width="1.5" '
        f'stroke-dasharray="2 3"/>',
        f'<rect x="-42" y="-17" width="84" height="34" rx="8" fill="#111a33" stroke="#475569"/>',
        f'<circle cx="-31" cy="0" r="3.5" fill="#34d399"/>',
        f'<text class="m" x="7" y="4.5" fill="{INK}" font-size="12" font-weight="600" '
        f'text-anchor="middle">PROJ-142</text>',
        '</g>',
    ]

    # status console
    out.append(f'<rect x="32" y="{H - 62}" width="{W - 64}" height="36" rx="8" fill="#0f172a" '
               f'stroke="{PANEL_STROKE}"/>')
    for i, (*_, color, msg) in enumerate(STAGES):
        out.append(f'<text class="m msg msg{i}" x="50" y="{H - 39}" font-size="12.5" fill="{INK}">'
                   f'<tspan fill="{color}">● </tspan>{x(msg)}</text>')
    out.append("</svg>")
    return "\n".join(out)


# --------------------------------------------------------------------------
# 2. Stack card
# --------------------------------------------------------------------------
STACK = [
    ("frontend", [("TypeScript", "#3178c6"), ("JavaScript", "#f7df1e"), ("React", "#61dafb"),
                  ("React Native", "#61dafb")]),
    ("backend", [("Python", "#ffd43b"), ("Django", "#44b78b")]),
    ("ai / agents", [("Claude", "#d97757"), ("Agentic workflows", "#a78bfa"),
                     ("Multi-agent orchestration", "#a78bfa"), ("LLM tooling", "#5eead4"),
                     ("Prompt engineering", "#5eead4")]),
]


def render_stack():
    W, row_h, top, left = 900, 42, 70, 160
    rows = []  # wrap chips that would overflow the card
    for label, chips in STACK:
        cur, cx = [], left
        for name, color in chips:
            w = len(name) * 7.4 + 38
            if cur and cx + w > W - 32:
                rows.append((label, cur)); label, cur, cx = "", [], left
            cur.append((name, color, cx, w)); cx += w + 10
        rows.append((label, cur))
    H = top + row_h * len(rows) + 20
    css = (f".t{{font-family:{SANS}}}.m{{font-family:{MONO}}}"
           ".chip{opacity:0;animation:in .5s ease-out forwards}"
           "@keyframes in{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}"
           "@media (prefers-reduced-motion:reduce){.chip{animation:none;opacity:1}}")
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
           f'aria-label="Tech stack: {x(", ".join(c for _, cs in STACK for c, _ in cs))}">',
           f"<style>{css}</style>",
           f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="{BG}" stroke="{PANEL_STROKE}"/>',
           f'<text class="t" x="32" y="44" fill="{INK}" font-size="16" font-weight="600">What I work with</text>']
    k = 0
    for r, (label, chips) in enumerate(rows):
        y = top + r * row_h
        if label:
            out.append(f'<text class="m" x="32" y="{y + 20}" fill="{MUTED}" font-size="12">{x(label)}</text>')
        for name, color, cx, w in chips:
            out.append(
                f'<g class="chip" style="animation-delay:{.15 + k * .08:.2f}s">'
                f'<rect x="{cx}" y="{y}" width="{w:.0f}" height="30" rx="15" fill="#0f172a" stroke="{PANEL_STROKE}"/>'
                f'<circle cx="{cx + 16}" cy="{y + 15}" r="4" fill="{color}"/>'
                f'<text class="t" x="{cx + 28}" y="{y + 19.5}" fill="{INK}" font-size="13">{x(name)}</text></g>')
            k += 1
    out.append("</svg>")
    return "\n".join(out)


# --------------------------------------------------------------------------
# 3. Terminal card (refreshed daily by the Action)
# --------------------------------------------------------------------------
QUERY = """
query($login:String!, $from:DateTime!, $to:DateTime!) {
  user(login:$login) {
    contributionsCollection(from:$from, to:$to) {
      totalCommitContributions
      totalPullRequestContributions
      commitContributionsByRepository(maxRepositories:25) {
        repository { name primaryLanguage { name } }
        contributions { totalCount }
      }
    }
    repositories(first:5, orderBy:{field:PUSHED_AT, direction:DESC}, ownerAffiliations:OWNER, privacy:PUBLIC) {
      nodes { name description }
    }
  }
}"""


def fetch_stats():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return None
    now = datetime.now(timezone.utc)
    body = json.dumps({"query": QUERY, "variables": {
        "login": USER, "from": (now - timedelta(days=7)).isoformat(), "to": now.isoformat()}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": USER})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        raise RuntimeError(data["errors"])
    u = data["data"]["user"]
    cc = u["contributionsCollection"]
    langs = {}
    for item in cc["commitContributionsByRepository"]:
        lang = (item["repository"]["primaryLanguage"] or {}).get("name")
        if lang:
            langs[lang] = langs.get(lang, 0) + item["contributions"]["totalCount"]
    repos = [n["name"] for n in u["repositories"]["nodes"] if n["name"].lower() != USER.lower()]
    return {
        "commits": cc["totalCommitContributions"],
        "prs": cc["totalPullRequestContributions"],
        "repos": len(cc["commitContributionsByRepository"]),
        "lang": max(langs, key=langs.get) if langs else None,
        "latest": repos[0] if repos else None,
        "date": now.strftime("%b %d, %Y"),
    }


SAMPLE = {"commits": 23, "prs": 3, "repos": 4, "lang": "TypeScript", "latest": "agent-pipeline",
          "date": datetime.now(timezone.utc).strftime("%b %d, %Y")}


def render_terminal(s):
    W, H = 900, 262
    CH = 8.43  # approx. advance width of a 14px monospace glyph
    if s["commits"]:
        week = (f'{s["commits"]} commits · {s["prs"]} PRs · {s["repos"]} repo{"s" if s["repos"] != 1 else ""}'
                + (f' · mostly {s["lang"]}' if s["lang"] else ""))
    else:
        week = "quiet week on GitHub · probably deep in a design doc"
    latest = f'latest push → {s["latest"]}' if s["latest"] else "latest push → (nothing public yet)"

    lines = [  # (kind, text, start_time)
        ("cmd", "whoami", 0.4),
        ("out", f"{NAME} · software developer · I build agents that ship code", 1.3),
        ("cmd", "./this_week --summary", 2.0),
        ("out", week, 3.5),
        ("out", latest, 3.8),
    ]
    css = (f".m{{font-family:{MONO}}}.o{{opacity:0;animation:show .01s forwards}}"
           "@keyframes show{to{opacity:1}}"
           ".cur{opacity:0;animation:show .01s 4.3s forwards,blink 1.1s 4.3s steps(1) infinite}"
           "@keyframes blink{0%{opacity:1}50%{opacity:0}}"
           "@media (prefers-reduced-motion:reduce){.o,.cur{animation:none;opacity:1}}")
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
           f'aria-label="{x(NAME)}. This week: {x(week)}. {x(latest)}.">',
           f"<style>{css}</style>", "<defs>"]
    for i, (kind, text, t0) in enumerate(lines):
        if kind == "cmd":
            n = len(text)
            vals = ";".join(f"{k * CH:.1f}" for k in range(n + 1)) + ";2000"
            out.append(f'<clipPath id="c{i}"><rect x="52" y="0" height="{H}" width="0">'
                       f'<animate attributeName="width" values="{vals}" begin="{t0}s" dur="{n * .07 + .07:.2f}s" '
                       f'calcMode="discrete" fill="freeze"/></rect></clipPath>')
    out.append("</defs>")
    out += [f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="{BG}" stroke="{PANEL_STROKE}"/>',
            f'<line x1="0" y1="40" x2="{W}" y2="40" stroke="{PANEL_STROKE}"/>',
            '<circle cx="26" cy="20" r="6" fill="#f87171"/><circle cx="46" cy="20" r="6" fill="#fbbf24"/>'
            '<circle cx="66" cy="20" r="6" fill="#34d399"/>',
            f'<text class="m" x="{W / 2}" y="25" fill="{MUTED}" font-size="12" text-anchor="middle">'
            f'{x(USER)}@github: ~</text>']
    y = 78
    for i, (kind, text, t0) in enumerate(lines):
        if kind == "cmd":
            if i:
                y += 12
            out.append(f'<text class="m o" style="animation-delay:{max(t0 - .3, 0):.2f}s" x="32" y="{y}" '
                       f'font-size="14" fill="#34d399">$</text>')
            out.append(f'<text class="m" clip-path="url(#c{i})" x="52" y="{y}" font-size="14" fill="{INK}">'
                       f'{x(text)}</text>')
        else:
            out.append(f'<text class="m o" style="animation-delay:{t0:.2f}s" x="32" y="{y}" font-size="14" '
                       f'fill="#94a3b8">{x(text)}</text>')
        y += 26
    y += 12
    out.append(f'<g class="cur"><text class="m" x="32" y="{y}" font-size="14" fill="#34d399">$</text>'
               f'<rect x="52" y="{y - 13}" width="9" height="17" fill="{INK}"/></g>')
    out.append(f'<text class="m" x="{W - 24}" y="{H - 16}" fill="{DIM}" font-size="11" text-anchor="end">'
               f'auto-updated {x(s["date"])} · github actions</text>')
    out.append("</svg>")
    return "\n".join(out)


def main():
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / "pipeline.svg").write_text(render_pipeline(), encoding="utf-8")
    (ASSETS / "stack.svg").write_text(render_stack(), encoding="utf-8")
    stats = None
    if "--sample" not in sys.argv:
        try:
            stats = fetch_stats()
        except Exception as e:  # keep the last good card rather than breaking the README
            print(f"stats fetch failed: {e}", file=sys.stderr)
            if (ASSETS / "terminal.svg").exists():
                return
    (ASSETS / "terminal.svg").write_text(render_terminal(stats or SAMPLE), encoding="utf-8")
    print("rendered:", ", ".join(p.name for p in sorted(ASSETS.glob("*.svg"))))


if __name__ == "__main__":
    main()
