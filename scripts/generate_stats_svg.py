#!/usr/bin/env python3
"""Generate a neofetch-style terminal info card as an SVG, dark + light variants.

Static fields (OS/Kernel/Host/Shell/Languages/Frameworks) are hardcoded below.
Repos/Stars/Followers are fetched live from the public GitHub API at generation
time. Run via GitHub Actions on a schedule to keep the numbers fresh; the two
output SVGs are committed to the `output` branch alongside the contribution
snake (see .github/workflows/snake.yml).
"""

import json
import os
import sys
import urllib.request

GITHUB_USER = os.environ.get("GITHUB_STATS_USER", "mengyuest")

STATIC_FIELDS = [
    ("OS", "Signal Temporal Logic"),
    ("Kernel", "Diffusion Policies x Flow Matching"),
    ("Host", "Apple Robotics (REALM Lab alum)"),
    ("Shell", "PyTorch"),
    ("Languages", "Python, C++, LaTeX"),
    ("Frameworks", "PyTorch, ROS, MuJoCo"),
]

PALETTES = {
    "dark": {
        "bg": "#0f1830",
        "border": "#2a3550",
        "prompt": "#e8e8e6",
        "label": "#7a88a8",
        "value": "#e8e8e6",
        "rule": "#2a3550",
    },
    "light": {
        "bg": "#f7f7f6",
        "border": "#d9dde3",
        "prompt": "#1b2a4a",
        "label": "#6b7280",
        "value": "#1b2a4a",
        "rule": "#d9dde3",
    },
}

WIDTH = 560
HEIGHT = 300
PAD_X = 32
LABEL_X = PAD_X
VALUE_X = 190
ROW_H = 24
FONT = "SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"


def fetch_live_stats(user):
    try:
        with urllib.request.urlopen(
            f"https://api.github.com/users/{user}", timeout=15
        ) as resp:
            profile = json.load(resp)
        followers = profile["followers"]
        repos = profile["public_repos"]

        stars = 0
        page = 1
        while True:
            req = urllib.request.Request(
                f"https://api.github.com/users/{user}/repos?per_page=100&page={page}"
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                batch = json.load(resp)
            if not batch:
                break
            stars += sum(r["stargazers_count"] for r in batch)
            if len(batch) < 100:
                break
            page += 1
        return {"repos": repos, "stars": stars, "followers": followers}
    except Exception as e:
        print(f"warning: live stats fetch failed ({e}); using fallback zeros", file=sys.stderr)
        return {"repos": 0, "stars": 0, "followers": 0}


def esc(s):
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def render_svg(palette_name, stats, papers=6):
    p = PALETTES[palette_name]
    rows = []
    y = 95
    for label, value in STATIC_FIELDS:
        rows.append(
            f'<text x="{LABEL_X}" y="{y}" font-family="{FONT}" font-size="13" fill="{p["label"]}">{esc(label)}:</text>'
            f'<text x="{VALUE_X}" y="{y}" font-family="{FONT}" font-size="13" fill="{p["value"]}">{esc(value)}</text>'
        )
        y += ROW_H

    y += ROW_H // 2
    stat_pairs = [
        (f"Repos: {stats['repos']}", f"Stars: {stats['stars']}"),
        (f"Followers: {stats['followers']}", f"Papers: {papers}"),
    ]
    for left, right in stat_pairs:
        rows.append(
            f'<text x="{LABEL_X}" y="{y}" font-family="{FONT}" font-size="13" fill="{p["value"]}">{esc(left)}</text>'
            f'<text x="{VALUE_X}" y="{y}" font-family="{FONT}" font-size="13" fill="{p["value"]}">{esc(right)}</text>'
        )
        y += ROW_H

    body_height = y + 20

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{body_height}" viewBox="0 0 {WIDTH} {body_height}">
  <rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{body_height - 1}" rx="16" fill="{p['bg']}" stroke="{p['border']}" stroke-width="1"/>
  <text x="{PAD_X}" y="42" font-family="{FONT}" font-size="16" font-weight="600" fill="{p['prompt']}">yue@apple-robotics</text>
  <line x1="{PAD_X}" y1="58" x2="{WIDTH - PAD_X}" y2="58" stroke="{p['rule']}" stroke-width="1"/>
  {''.join(rows)}
</svg>"""
    return svg


def main():
    user = GITHUB_USER
    stats = fetch_live_stats(user)
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out_dir, exist_ok=True)
    for name in ("dark", "light"):
        svg = render_svg(name, stats)
        path = os.path.join(out_dir, f"stats-{name}.svg")
        with open(path, "w") as f:
            f.write(svg)
        print(f"wrote {path}")
    print("stats:", stats)


if __name__ == "__main__":
    main()
