#!/usr/bin/env python3
"""Draws the profile as a code-editor window (assets/ide.svg) in the vova-builds.dev syntax palette.

Text is converted to outlines with Geist Mono (GitHub strips web fonts from READMEs).
Needs: pip install fonttools brotli   and the site repo for the font files (SITE_REPO, default ~/code/vova-builds).
Run:   python3 build/ide.py
"""
import os
import re
from html import escape
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

FONTS = Path(os.environ.get("SITE_REPO", Path.home() / "code/vova-builds")) / "node_modules/@fontsource-variable/geist-mono/files"
OUT = Path(__file__).resolve().parent.parent / "assets" / "ide.svg"

BG, PANEL, SURF, BORDER = "#090b0d", "#0d1013", "#101316", "#232a30"
FG, MUTED, FAINT = "#ededed", "#a1a1a1", "#808080"
CYAN, AMBER, VIOLET, PINK, GREEN = "#7fe3f0", "#f5b454", "#b48cff", "#ff7ab8", "#3ecf8e"

CODE = '''// cybersecurity student, Prague
const vova = {
  role: "Cybersecurity student · Junior DevSecOps",
  school: "SPŠE V Úžlabině",
  graduation: 2027,

  workingOn: [
    "Ansible server hardening",
    "Backups with a tested restore",
    "CI/CD with Trivy and gitleaks",
  ],

  homelab: ["Proxmox", "Ubuntu Server", "Docker"],
  experience: [
    "2× internship, České Radiokomunikace",
    "Co-founder of Syvia",
    "Hack The Box",
    "picoCTF",
  ],
  courses: ["Cisco CCNA (ITN, SRWE, ITE)", "NDG Linux"],
  openToWork: true,
};

export function contact() {
  return "vova.builds.sec@gmail.com";
}
'''

TOKEN = re.compile(
    r'(?P<comment>//.*$)|(?P<string>"[^"]*")|(?P<kw>\b(?:const|export|function|return)\b)|(?P<lit>\b(?:true|false)\b)'
    r'|(?P<num>\b\d+\b)|(?P<op>=)|(?P<punct>[{}\[\](),:;])|(?P<ws>\s+)|(?P<id>[A-Za-z_]\w*)|(?P<other>.)'
)
COLOR = {"comment": FAINT, "string": AMBER, "kw": CYAN, "lit": VIOLET, "num": VIOLET, "op": PINK, "punct": MUTED, "id": FG, "other": FG}

W, TAB_H, LH, FS, GUTTER, CODE_X, STATUS_H = 800, 40, 24, 14, 44, 64, 28


def num(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def half(v):
    return num(v + 0.5)  # crisp 1px lines


font = instancer.instantiateVariableFont(TTFont(FONTS / "geist-mono-latin-wght-normal.woff2"), {"wght": 400}, inplace=False)
ext = instancer.instantiateVariableFont(TTFont(FONTS / "geist-mono-latin-ext-wght-normal.woff2"), {"wght": 400}, inplace=False)
FACES = [(f.getGlyphSet(), f.getBestCmap(), f["head"].unitsPerEm, f["hmtx"]) for f in (font, ext)]


def outline(x, y, s, size):
    out, cx = [], x
    for ch in s:
        gs, cmap, upem, hmtx = next(f for f in FACES if ord(ch) in f[1])
        name, sc = cmap[ord(ch)], size / upem
        pen = SVGPathPen(gs, ntos=num)
        gs[name].draw(TransformPen(pen, (sc, 0, 0, -sc, cx, y)))
        out.append(pen.getCommands())
        cx += hmtx[name][0] * sc
    return "".join(out), cx


def draw(x, y, s, fill, size=FS):
    d, end = outline(x, y, s, size)
    return (f'<path d="{d}" fill="{fill}"/>' if d else ""), end


def build():
    lines = CODE.rstrip("\n").split("\n")
    n = len(lines) + 1  # one empty last line holds the caret
    height = TAB_H + 16 + n * LH + 12 + STATUS_H
    cw = outline(0, 0, "0", FS)[1]
    cur_y = TAB_H + 16 + (n - 1) * LH
    sy = height - STATUS_H
    p = [
        f'<rect x=".5" y=".5" width="{W-1}" height="{height-1}" rx="12" fill="{BG}" stroke="{BORDER}"/>',
        f'<path d="M1 12.5Q1 1 12.5 1H{W-1}Q{W-1} 1 {W-1} 12.5V{TAB_H}H1Z" fill="{PANEL}"/>',
        f'<path d="M0 {half(TAB_H)}H{W}" stroke="{BORDER}"/>',
        f'<path d="M1 {TAB_H}V12.5Q1 1 12.5 1H152V{TAB_H}Z" fill="{BG}"/>',  # active tab
        f'<path d="M12 2H141" stroke="{CYAN}" stroke-width="2"/>',
    ]
    for label, x, fill in (("vova.ts", 24, FG), ("skills.json", 168, FAINT), ("contact.md", 296, FAINT)):
        p.append(draw(x, 25, label, fill, 12)[0])
    p.append(f'<path d="M152.5 8V32M280.5 8V32M404.5 8V32" stroke="{BORDER}"/>')
    p.append(f'<rect x="1" y="{cur_y - 17}" width="{W-2}" height="{LH}" fill="{SURF}"/>')  # current-line band
    for i, raw in enumerate(lines):
        base = TAB_H + 16 + i * LH + 3
        p.append(draw(GUTTER - cw * len(str(i + 1)), base, str(i + 1), FAINT, 12)[0])
        indent = len(raw) - len(raw.lstrip(" "))
        for lvl in range(2, indent + 1, 2):  # indent guides
            gx = CODE_X + (lvl - 2) * cw + 1
            p.append(f'<path d="M{half(gx)} {base - 15}V{base + 5}" stroke="{BORDER}"/>')
        x, after_function = CODE_X, False
        for m in TOKEN.finditer(raw):
            kind, tok = m.lastgroup, m.group()
            if kind == "ws":
                x += cw * len(tok)
                continue
            svg, x = draw(x, cur_y * 0 + base, tok, GREEN if (kind == "id" and after_function) else COLOR[kind])
            p.append(svg)
            after_function = kind == "kw" and tok == "function"
    p.append(draw(GUTTER - cw * len(str(n)), cur_y + 3, str(n), MUTED, 12)[0])
    p.append(f'<rect class="caret" x="{CODE_X}" y="{cur_y - 14}" width="2" height="18" fill="{AMBER}"/>')
    p.append(f'<path d="M1 {sy}H{W-1}V{height-12.5}Q{W-1} {height-1} {W-12.5} {height-1}H12.5Q1 {height-1} 1 {height-12.5}Z" fill="{PANEL}"/>')
    p.append(f'<path d="M0 {half(sy)}H{W}" stroke="{BORDER}"/>')
    p.append(f'<circle cx="24" cy="{sy + 14}" r="4" fill="{GREEN}"/>')
    p.append(draw(36, sy + 18, "open to work", MUTED, 12)[0])
    p.append(draw(152, sy + 18, "main", FAINT, 12)[0])
    for label, right in ((f"Ln {n}, Col 1", W - 24), ("UTF-8", W - 160), ("TypeScript", W - 232)):
        p.append(draw(right - outline(0, 0, label, 12)[1], sy + 18, label, FAINT, 12)[0])
    css = "@keyframes blink{50%{opacity:0}}.caret{animation:blink 1.1s steps(1) infinite}@media (prefers-reduced-motion:reduce){.caret{animation:none}}"
    desc = "vova.ts: " + " ".join(l.strip() for l in lines if l.strip())
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" viewBox="0 0 {W} {height}" role="img" aria-labelledby="t d">'
        f'<title id="t">vova.ts in a code editor</title><desc id="d">{escape(desc)}</desc><style>{css}</style>' + "".join(p) + "</svg>\n"
    )


if __name__ == "__main__":
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(build())
    print(f"{OUT} {OUT.stat().st_size // 1024} KB")
