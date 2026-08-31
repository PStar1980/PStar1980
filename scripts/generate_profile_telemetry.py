#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

GITHUB_API = "https://api.github.com"
GOLD = "#D4AF37"
GOLD_BRIGHT = "#F6D76B"
GOLD_SOFT = "#9D7F24"
TEXT = "#F2F2F2"
MUTED = "#9A927C"
DIM = "#5E5747"
BG = "#070707"
PANEL = "#0B0B0B"
BORDER = "#3B321A"
BAR_BG = "#1B1810"


def api_get(url: str):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "PStar1980-profile-telemetry",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.getenv("GH_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def list_public_repositories(username: str) -> list[dict]:
    repositories: list[dict] = []
    page = 1
    while True:
        query = urllib.parse.urlencode(
            {"per_page": 100, "page": page, "sort": "pushed", "direction": "desc"}
        )
        batch = api_get(f"{GITHUB_API}/users/{urllib.parse.quote(username)}/repos?{query}")
        repositories.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repositories


def aggregate_languages(repositories: list[dict]) -> dict[str, int]:
    totals: dict[str, int] = defaultdict(int)
    for repo in repositories:
        if repo.get("fork"):
            continue
        owner = urllib.parse.quote(repo["owner"]["login"])
        name = urllib.parse.quote(repo["name"])
        try:
            languages = api_get(f"{GITHUB_API}/repos/{owner}/{name}/languages")
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            print(
                f"warning: language telemetry unavailable for {repo['full_name']}: {exc}",
                file=sys.stderr,
            )
            continue
        for language, byte_count in languages.items():
            totals[language] += int(byte_count)
    return dict(totals)


def parse_github_time(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def compact_number(value: int) -> str:
    if value < 1_000:
        return str(value)
    if value < 1_000_000:
        return f"{value / 1_000:.1f}K".replace(".0K", "K")
    return f"{value / 1_000_000:.1f}M".replace(".0M", "M")


def svg_text(x, y, value, *, size=20, fill=TEXT, weight=500, anchor="start", cls=""):
    class_attr = f' class="{cls}"' if cls else ""
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
        f'font-weight="{weight}" text-anchor="{anchor}"{class_attr}>{esc(value)}</text>'
    )


def panel(x, y, width, height):
    return (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="14" '
        f'fill="{PANEL}" stroke="{BORDER}" stroke-width="1.3"/>'
    )


def metric_card(x, y, width, height, label, value, sublabel):
    return "\n".join(
        [
            panel(x, y, width, height),
            f'<line x1="{x}" y1="{y + 12}" x2="{x}" y2="{y + height - 12}" stroke="{GOLD}" stroke-width="4"/>',
            svg_text(x + 24, y + 34, label.upper(), size=15, fill=MUTED, weight=700, cls="mono"),
            svg_text(x + 24, y + 77, value, size=38, fill=TEXT, weight=750, cls="mono"),
            svg_text(x + 24, y + 101, sublabel.upper(), size=12, fill=DIM, weight=600, cls="mono"),
            f'<circle cx="{x + width - 25}" cy="{y + 25}" r="4" fill="{GOLD}" filter="url(#glow)">'
            '<animate attributeName="opacity" values="0.45;1;0.45" dur="2.4s" repeatCount="indefinite"/>'
            "</circle>",
            f'<line x1="{x + width - 100}" y1="{y + height - 14}" x2="{x + width - 24}" y2="{y + height - 14}" stroke="{GOLD_SOFT}" stroke-width="2" opacity=".5"/>',
        ]
    )


def svg_shell(width: int, height: int, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">
  <defs>
    <linearGradient id="goldLine" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#3A2E11"/>
      <stop offset="50%" stop-color="{GOLD}"/>
      <stop offset="100%" stop-color="#3A2E11"/>
    </linearGradient>
    <radialGradient id="halo" cx="78%" cy="5%" r="80%">
      <stop offset="0%" stop-color="#6A561A" stop-opacity=".22"/>
      <stop offset="55%" stop-color="#15110A" stop-opacity=".05"/>
      <stop offset="100%" stop-color="#000000" stop-opacity="0"/>
    </radialGradient>
    <filter id="glow" x="-300%" y="-300%" width="700%" height="700%">
      <feGaussianBlur stdDeviation="4" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <style>
      .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }}
      text {{ font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    </style>
  </defs>
  <rect width="100%" height="100%" rx="18" fill="{BG}"/>
  <rect width="100%" height="100%" rx="18" fill="url(#halo)"/>
  <rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="18" fill="none" stroke="{BORDER}" stroke-width="2"/>
  <line x1="38" y1="38" x2="{width - 38}" y2="38" stroke="url(#goldLine)" stroke-width="2" opacity=".72"/>
  <path d="M 845 -20 C 770 140, 860 250, 740 520" fill="none" stroke="{GOLD_SOFT}" stroke-width="1" opacity=".12"/>
  <path d="M 900 -30 C 820 130, 930 260, 800 540" fill="none" stroke="{GOLD_SOFT}" stroke-width="1" opacity=".08"/>
  {body}
</svg>
'''


def generate_profile_card(username: str, profile: dict, repositories: list[dict], languages: dict[str, int]) -> str:
    authored = [repo for repo in repositories if not repo.get("fork")]
    stars = sum(int(repo.get("stargazers_count", 0)) for repo in authored)
    forks = sum(int(repo.get("forks_count", 0)) for repo in authored)
    open_items = sum(int(repo.get("open_issues_count", 0)) for repo in authored)
    now = datetime.now(timezone.utc)
    active_cutoff = now - timedelta(days=90)
    active_90d = sum(
        1
        for repo in authored
        if (parse_github_time(repo.get("pushed_at")) or datetime.min.replace(tzinfo=timezone.utc)) >= active_cutoff
    )
    latest_push = max(
        (parse_github_time(repo.get("pushed_at")) for repo in authored if repo.get("pushed_at")),
        default=None,
    )
    top_language = max(languages, key=languages.get) if languages else "N/A"

    width, height = 1100, 520
    body = []
    body.append(f'<circle cx="56" cy="77" r="6" fill="{GOLD}" filter="url(#glow)"><animate attributeName="opacity" values=".4;1;.4" dur="2s" repeatCount="indefinite"/></circle>')
    body.append(svg_text(76, 84, "PROFILE ONLINE", size=24, fill=TEXT, weight=800, cls="mono"))
    body.append(svg_text(45, 111, f"@{username.upper()} // LIVE GITHUB ENGINEERING TELEMETRY", size=12, fill=MUTED, weight=700, cls="mono"))
    body.append(svg_text(width - 44, 84, "SYNCHRONIZED", size=12, fill=GOLD_BRIGHT, weight=800, anchor="end", cls="mono"))

    card_w, card_h = 485, 116
    body.append(metric_card(45, 142, card_w, card_h, "Public repositories", compact_number(len(repositories)), f"{active_90d} active in last 90 days"))
    body.append(metric_card(570, 142, card_w, card_h, "Followers", compact_number(int(profile.get("followers", 0))), f"{profile.get('following', 0)} following"))
    body.append(metric_card(45, 278, card_w, card_h, "Stars earned", compact_number(stars), "across authored public repos"))
    body.append(metric_card(570, 278, card_w, card_h, "Forks", compact_number(forks), f"{open_items} open repo items"))

    body.append(panel(45, 418, 1010, 69))
    body.append(svg_text(66, 442, "REPOSITORY SIGNAL", size=12, fill=TEXT, weight=800, cls="mono"))
    values = [
        ("ACTIVE 90D", str(active_90d)),
        ("LANGUAGES", str(len(languages))),
        ("TOP LANG", top_language.upper()),
        ("LATEST PUSH", latest_push.strftime("%Y-%m-%d") if latest_push else "N/A"),
        ("LAST SYNC", now.strftime("%Y-%m-%d")),
    ]
    xs = [68, 260, 440, 650, 850]
    for (label, value), x in zip(values, xs):
        body.append(svg_text(x, 463, label, size=10, fill=DIM, weight=700, cls="mono"))
        body.append(svg_text(x, 481, value, size=14, fill=GOLD_BRIGHT if label == "TOP LANG" else TEXT, weight=800, cls="mono"))

    body.append(svg_text(width - 47, height - 15, "GITHUB PROFILE INTELLIGENCE // LIVE DATA LAYER", size=9, fill=GOLD_SOFT, weight=700, anchor="end", cls="mono"))
    return svg_shell(width, height, "\n  ".join(body))


def generate_language_matrix(username: str, languages: dict[str, int]) -> str:
    sorted_languages = sorted(languages.items(), key=lambda item: item[1], reverse=True)[:6]
    total = sum(languages.values()) or 1
    width = 1100
    row_h = 54
    height = 165 + max(len(sorted_languages), 1) * row_h

    body = [
        svg_text(48, 82, "LANGUAGE MATRIX", size=28, fill=TEXT, weight=850, cls="mono"),
        svg_text(48, 107, f"@{username.upper()} // BYTE DISTRIBUTION // AUTHORED PUBLIC REPOSITORIES", size=11, fill=MUTED, weight=700, cls="mono"),
        svg_text(width - 48, 82, "SYSTEM ONLINE", size=10, fill=GOLD_BRIGHT, weight=800, anchor="end", cls="mono"),
    ]

    if not sorted_languages:
        body.append(svg_text(48, 160, "No language telemetry available.", size=16, fill=MUTED, cls="mono"))
        return svg_shell(width, 240, "\n  ".join(body))

    bar_x, bar_w = 315, 590
    shades = ["#F6D76B", "#D4AF37", "#B7952E", "#8F7525", "#6F5B20", "#57481C"]

    for index, (language, byte_count) in enumerate(sorted_languages, start=1):
        y = 150 + (index - 1) * row_h
        pct = byte_count / total * 100
        fill_w = max(4, bar_w * pct / 100)
        body.append(svg_text(52, y + 19, f"{index:02d}", size=11, fill=GOLD_SOFT, weight=800, cls="mono"))
        body.append(svg_text(94, y + 19, language.upper(), size=15, fill=TEXT, weight=800, cls="mono"))
        body.append(svg_text(94, y + 38, f"{compact_number(byte_count)} BYTES", size=9, fill=DIM, weight=600, cls="mono"))
        body.append(f'<rect x="{bar_x}" y="{y + 5}" width="{bar_w}" height="15" rx="7.5" fill="{BAR_BG}" stroke="{BORDER}" stroke-width=".8"/>')
        body.append(f'<rect x="{bar_x}" y="{y + 5}" width="{fill_w:.1f}" height="15" rx="7.5" fill="{shades[index - 1]}" filter="url(#glow)" opacity=".95"/>')
        body.append(svg_text(1025, y + 19, f"{pct:.1f}%", size=14, fill=GOLD_BRIGHT, weight=850, anchor="end", cls="mono"))
        if index < len(sorted_languages):
            body.append(f'<line x1="52" y1="{y + 49}" x2="1028" y2="{y + 49}" stroke="{BORDER}" stroke-width=".7" opacity=".65"/>')

    body.append(svg_text(width - 48, height - 18, f"{len(languages)} LANGUAGES DETECTED", size=9, fill=GOLD_SOFT, weight=700, anchor="end", cls="mono"))
    return svg_shell(width, height, "\n  ".join(body))


def main() -> None:
    username = os.getenv("PROFILE_USER") or os.getenv("GITHUB_REPOSITORY_OWNER") or "PStar1980"
    output_dir = Path(os.getenv("OUTPUT_DIR", "dist"))
    output_dir.mkdir(parents=True, exist_ok=True)

    profile = api_get(f"{GITHUB_API}/users/{urllib.parse.quote(username)}")
    repositories = list_public_repositories(username)
    languages = aggregate_languages(repositories)

    (output_dir / "profile-telemetry.svg").write_text(
        generate_profile_card(username, profile, repositories, languages),
        encoding="utf-8",
    )
    (output_dir / "language-matrix.svg").write_text(
        generate_language_matrix(username, languages),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "username": username,
                "publicRepositories": len(repositories),
                "followers": profile.get("followers", 0),
                "languages": len(languages),
                "output": [
                    str(output_dir / "profile-telemetry.svg"),
                    str(output_dir / "language-matrix.svg"),
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
