#!/usr/bin/env python3
"""Contribution heatmap in editor-panel style (palette of vova-builds.dev).

Usage: python3 build/activity.py <github-login> <out.svg>
Needs the `gh` CLI with a token in GH_TOKEN (present on GitHub Actions runners).
"""
import json
import math
import subprocess
import sys
from datetime import date

QUERY = """query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{
totalContributions weeks{contributionDays{date contributionCount}}}}}}"""

BG, PANEL, BORDER = "#090b0d", "#0d1013", "#232a30"
FG, MUTED, FAINT = "#ededed", "#a1a1a1", "#808080"
TINT, VIOLET, AMBER, GREEN = "#7fe3f0", "#b48cff", "#f5b454", "#3ecf8e"
LEVELS = ["#161a1e", "#3b3018", "#7a5c22", "#c28a38", AMBER]
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono',monospace"


def level(count, top):
    return 0 if count == 0 or top == 0 else math.ceil(count / top * 4)


def streaks(counts):
    """(current, longest) run of days with contributions; an empty last day (today) does not break the current run."""
    longest = run = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    tail = counts[:-1] if counts and counts[-1] == 0 else counts
    current = 0
    for c in reversed(tail):
        if not c:
            break
        current += 1
    return current, longest


def fetch(login):
    out = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={QUERY}", "-f", f"login={login}"],
        check=True, capture_output=True, text=True,
    ).stdout
    cal = json.loads(out)["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    return cal["totalContributions"], cal["weeks"]


def text(x, y, s, fill, size=12, anchor="start", weight="400"):
    return (f'<text x="{x:g}" y="{y:g}" fill="{fill}" font-size="{size}" font-weight="{weight}" '
            f'text-anchor="{anchor}" font-family="{MONO}">{s}</text>')


def render(total, weeks):
    days = [d["contributionCount"] for w in weeks for d in w["contributionDays"]]
    cur, best = streaks(days)
    top = max(days, default=0)
    cell, gap, x0, y0, width = 11, 3, 30, 128, 800
    height = y0 + 7 * (cell + gap) + 62
    p = [
        f'<rect x=".5" y=".5" width="{width-1}" height="{height-1}" rx="12" fill="{BG}" stroke="{BORDER}"/>',
        f'<path d="M1 12.5Q1 1 12.5 1H{width-1}.5Q{width-1} 1 {width-1} 12.5V36H1Z" fill="{PANEL}"/>',
        f'<path d="M0 36.5H{width}" stroke="{BORDER}"/>',
    ]
    x = 20
    for name in ("PROBLEMS", "OUTPUT", "TERMINAL", "GIT"):
        p.append(text(x, 23, name, FG if name == "GIT" else FAINT, 11, weight="500"))
        w = len(name) * 6.6
        if name == "GIT":
            p.append(f'<path d="M{x} 35H{x + w:.0f}" stroke="{TINT}" stroke-width="2"/>')
        x += w + 24
    p.append(text(24, 68, "$", TINT, 13) + text(40, 68, 'git log --since="1 year ago" --oneline | wc -l'.replace('"', "&quot;"), FG, 13))
    p.append(text(24, 90, str(total), VIOLET, 13, weight="500") + text(24 + 8 * len(str(total)) + 8, 90, "contributions in the last year", MUTED, 13))
    last_month = None
    for wi, w in enumerate(weeks):
        month = date.fromisoformat(w["contributionDays"][0]["date"]).strftime("%b")
        if month != last_month and wi < len(weeks) - 2:
            p.append(text(x0 + wi * (cell + gap), y0 - 8, month, FAINT, 10))
        last_month = month
        for di, d in enumerate(w["contributionDays"]):
            c = LEVELS[level(d["contributionCount"], top)]
            p.append(f'<rect x="{x0 + wi * (cell + gap)}" y="{y0 + di * (cell + gap)}" width="{cell}" height="{cell}" rx="2" fill="{c}">'
                     f'<title>{d["date"]}: {d["contributionCount"]}</title></rect>')
    ys = y0 + 7 * (cell + gap) + 30
    p.append(text(24, ys, "current streak", FAINT) + text(24 + 14 * 7.2 + 8, ys, f"{cur} d", GREEN, 12, weight="500"))
    p.append(text(250, ys, "longest streak", FAINT) + text(250 + 14 * 7.2 + 8, ys, f"{best} d", AMBER, 12, weight="500"))
    lx = width - 24 - 5 * 14 - 34
    p.append(text(lx - 6, ys, "less", FAINT, 10, "end"))
    p.extend(f'<rect x="{lx + i * 14}" y="{ys - 10}" width="11" height="11" rx="2" fill="{c}"/>' for i, c in enumerate(LEVELS))
    p.append(text(lx + 5 * 14 + 4, ys, "more", FAINT, 10))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="t">'
        f'<title id="t">Contribution activity: {total} in the last year, current streak {cur} days, longest {best} days</title>'
        + "".join(p) + "</svg>\n"
    )


if __name__ == "__main__":
    login, out = sys.argv[1], sys.argv[2]
    total, weeks = fetch(login)
    open(out, "w").write(render(total, weeks))
    print(f"{out}: {total} contributions")
