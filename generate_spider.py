#!/usr/bin/env python3
"""Generate an animated SVG of a spider eating your GitHub contribution graph.

Reads GH_USER and GH_TOKEN from the environment, asks the GitHub GraphQL API
for the last year of contributions, and writes dist/spider.svg.
Standard library only, so there is nothing to pip install.
"""
import json
import os
import urllib.request

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays {
            contributionCount
            weekday
          }
        }
      }
    }
  }
}
"""

# Grid layout (in pixels)
CELL = 10
GAP = 3
PITCH = CELL + GAP
PAD = 20
ROWS = 7

# Colours
BG = "#0d1117"
EMPTY = "#161b22"
LEVELS = ["#7a3a5e", "#b24f84", "#e072a8", "#ffd6e8"]  # dim pink -> baby pink
SPIDER = "#ffd6e8"

# Timing
SECONDS_PER_CELL = 0.06
HOLD_FRACTION = 0.12  # share of each loop the spider rests after the last cell


def fetch_weeks(user, token):
    body = json.dumps({"query": QUERY, "variables": {"login": user}}).encode()
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": "bearer " + token,
            "Content-Type": "application/json",
            "User-Agent": "spider-contribution-graph",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if payload.get("errors"):
        raise RuntimeError("GitHub API error: " + json.dumps(payload["errors"]))
    if payload["data"]["user"] is None:
        raise RuntimeError("GitHub user not found: " + user)
    calendar = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    return calendar["weeks"]


def build_svg(weeks):
    cols = len(weeks)
    cell_count = cols * ROWS
    biggest = max(
        (d["contributionCount"] for w in weeks for d in w["contributionDays"]),
        default=0,
    )
    biggest = max(biggest, 1)

    width = cols * PITCH - GAP + 2 * PAD
    height = ROWS * PITCH - GAP + 2 * PAD

    # The spider walks column by column, down then up, so every step is
    # exactly one PITCH long. That makes its speed constant.
    def order_index(col, row):
        return col * ROWS + (row if col % 2 == 0 else ROWS - 1 - row)

    def center(col, row):
        return PAD + col * PITCH + CELL / 2, PAD + row * PITCH + CELL / 2

    points = []
    for col in range(cols):
        rows = range(ROWS) if col % 2 == 0 else range(ROWS - 1, -1, -1)
        for row in rows:
            x, y = center(col, row)
            points.append(f"{x:g} {y:g}")
    path = "M" + " L".join(points)

    travel_fraction = 1 - HOLD_FRACTION
    total_seconds = (cell_count - 1) * SECONDS_PER_CELL / travel_fraction
    dur = f"{total_seconds:.2f}s"

    cells = []
    for col, week in enumerate(weeks):
        for day in week["contributionDays"]:
            row = day["weekday"]
            count = day["contributionCount"]
            x = PAD + col * PITCH
            y = PAD + row * PITCH
            if count <= 0:
                cells.append(
                    f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{EMPTY}"/>'
                )
                continue
            level = min(3, (count * 4 - 1) // biggest)
            color = LEVELS[level]
            eaten_at = order_index(col, row) / (cell_count - 1) * travel_fraction
            eaten_at = max(eaten_at, 0.001)
            cells.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{color}">'
                f'<animate attributeName="fill" calcMode="discrete" '
                f'values="{color};{EMPTY}" keyTimes="0;{eaten_at:.4f}" '
                f'dur="{dur}" repeatCount="indefinite"/></rect>'
            )

    spider = (
        "<g>"
        f'<g transform="scale(0.7)" stroke="{SPIDER}" stroke-width="2" stroke-linecap="round" fill="none">'
        '<path d="M-4,-3 L-11,-9 M-5,-1 L-13,-3 M-5,2 L-13,5 M-4,4 L-10,11 '
        'M4,-3 L11,-9 M5,-1 L13,-3 M5,2 L13,5 M4,4 L10,11"/>'
        f'<ellipse cx="0" cy="1" rx="5" ry="6.5" fill="{SPIDER}" stroke="none"/>'
        f'<circle cx="0" cy="-7" r="3.5" fill="{SPIDER}" stroke="none"/>'
        "</g>"
        f'<animateMotion dur="{dur}" repeatCount="indefinite" calcMode="linear" '
        f'keyPoints="0;1;1" keyTimes="0;{travel_fraction:.2f};1" path="{path}"/>'
        "</g>"
    )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img">'
        "<title>A spider eating my GitHub contributions</title>"
        f'<rect width="{width}" height="{height}" rx="8" fill="{BG}"/>'
        + "".join(cells)
        + spider
        + "</svg>\n"
    )


def main():
    user = os.environ["GH_USER"]
    token = os.environ["GH_TOKEN"]
    weeks = fetch_weeks(user, token)
    svg = build_svg(weeks)
    os.makedirs("dist", exist_ok=True)
    with open("dist/spider.svg", "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote dist/spider.svg ({len(weeks)}
