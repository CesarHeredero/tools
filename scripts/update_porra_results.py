#!/usr/bin/env python3
"""
Fetch World Cup 2026 results from ESPN public API and update html/porra/results.json.
Run daily via GitHub Actions cron or manually.
"""

import json
import os
import sys
import urllib.request
from datetime import datetime, date, timedelta, timezone

# All 72 group stage fixtures — indices match PRED_FALLBACK in porra/index.html
FIXTURES = [
    (0,  "Mexico",                "South Africa"),
    (1,  "Korea Republic",        "Czech Republic"),
    (2,  "Czech Republic",        "South Africa"),
    (3,  "Mexico",                "Korea Republic"),
    (4,  "Czech Republic",        "Mexico"),
    (5,  "South Africa",          "Korea Republic"),
    (6,  "Canada",                "Bosnia and Herzegovina"),
    (7,  "Qatar",                 "Switzerland"),
    (8,  "Switzerland",           "Bosnia and Herzegovina"),
    (9,  "Canada",                "Qatar"),
    (10, "Switzerland",           "Canada"),
    (11, "Bosnia and Herzegovina","Qatar"),
    (12, "Haiti",                 "Scotland"),
    (13, "Brazil",                "Morocco"),
    (14, "Brazil",                "Haiti"),
    (15, "Scotland",              "Morocco"),
    (16, "Scotland",              "Brazil"),
    (17, "Morocco",               "Haiti"),
    (18, "United States",         "Paraguay"),
    (19, "Australia",             "Turkey"),
    (20, "United States",         "Australia"),
    (21, "Turkey",                "Paraguay"),
    (22, "Turkey",                "United States"),
    (23, "Paraguay",              "Australia"),
    (24, "Ivory Coast",           "Ecuador"),
    (25, "Germany",               "Curaçao"),
    (26, "Germany",               "Ivory Coast"),
    (27, "Ecuador",               "Curaçao"),
    (28, "Curaçao",               "Ivory Coast"),
    (29, "Ecuador",               "Germany"),
    (30, "Netherlands",           "Japan"),
    (31, "Sweden",                "Tunisia"),
    (32, "Netherlands",           "Sweden"),
    (33, "Tunisia",               "Japan"),
    (34, "Japan",                 "Sweden"),
    (35, "Tunisia",               "Netherlands"),
    (36, "Iran",                  "New Zealand"),
    (37, "Belgium",               "Egypt"),
    (38, "Belgium",               "Iran"),
    (39, "New Zealand",           "Egypt"),
    (40, "Egypt",                 "Iran"),
    (41, "New Zealand",           "Belgium"),
    (42, "Saudi Arabia",          "Uruguay"),
    (43, "Spain",                 "Cape Verde"),
    (44, "Uruguay",               "Cape Verde"),
    (45, "Spain",                 "Saudi Arabia"),
    (46, "Cape Verde",            "Saudi Arabia"),
    (47, "Uruguay",               "Spain"),
    (48, "France",                "Senegal"),
    (49, "Iraq",                  "Norway"),
    (50, "Norway",                "Senegal"),
    (51, "France",                "Iraq"),
    (52, "Norway",                "France"),
    (53, "Senegal",               "Iraq"),
    (54, "Argentina",             "Algeria"),
    (55, "Austria",               "Jordan"),
    (56, "Argentina",             "Austria"),
    (57, "Jordan",                "Algeria"),
    (58, "Algeria",               "Austria"),
    (59, "Jordan",                "Argentina"),
    (60, "Portugal",              "DR Congo"),
    (61, "Uzbekistan",            "Colombia"),
    (62, "Portugal",              "Uzbekistan"),
    (63, "Colombia",              "DR Congo"),
    (64, "Colombia",              "Portugal"),
    (65, "DR Congo",              "Uzbekistan"),
    (66, "Ghana",                 "Panama"),
    (67, "England",               "Croatia"),
    (68, "England",               "Ghana"),
    (69, "Panama",                "Croatia"),
    (70, "Panama",                "England"),
    (71, "Croatia",               "Ghana"),
]

# ESPN displayName → our fixture name
ESPN_MAP = {
    "South Korea":          "Korea Republic",
    "Czechia":              "Czech Republic",
    "Türkiye":              "Turkey",
    "Turkiye":              "Turkey",
    "Bosnia-Herz.":         "Bosnia and Herzegovina",
    "Bosnia & Herzegovina": "Bosnia and Herzegovina",
    "Bosnia-Herzegovina":   "Bosnia and Herzegovina",
    "Côte d'Ivoire":        "Ivory Coast",
    "Cote d'Ivoire":        "Ivory Coast",
    "Congo DR":             "DR Congo",
    "DRC":                  "DR Congo",
    "Cabo Verde":           "Cape Verde",
    "USA":                  "United States",
    "Curacao":              "Curaçao",
}

def norm(name):
    return ESPN_MAP.get(name, name)

# frozenset({home, away}) -> (idx, fixture_home, fixture_away)
LOOKUP = {frozenset([h, a]): (i, h, a) for i, h, a in FIXTURES}


def fetch_day(d):
    url = (
        "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"
        f"?dates={d.strftime('%Y%m%d')}&limit=20"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  fetch {d}: {e}", file=sys.stderr)
        return None


def main():
    groups = {}
    today = date.today()

    d = date(2026, 6, 11)
    while d <= today:
        data = fetch_day(d)
        if data:
            for event in data.get("events", []):
                if not event.get("status", {}).get("type", {}).get("completed"):
                    continue
                comp = (event.get("competitions") or [{}])[0]
                scores = {}
                for c in comp.get("competitors", []):
                    team = norm(c.get("team", {}).get("displayName", ""))
                    score = int(c.get("score") or 0)
                    scores[c.get("homeAway", "")] = (team, score)

                home_team, home_score = scores.get("home", ("", 0))
                away_team, away_score = scores.get("away", ("", 0))
                key = frozenset([home_team, away_team])

                if key in LOOKUP:
                    i, fh, fa = LOOKUP[key]
                    if home_team == fh:
                        groups[str(i)] = [home_score, away_score]
                    else:
                        groups[str(i)] = [away_score, home_score]
                else:
                    print(f"  unmatched: '{home_team}' vs '{away_team}'", file=sys.stderr)
        d += timedelta(days=1)

    if not groups:
        print("No results fetched — keeping existing file unchanged", file=sys.stderr)
        sys.exit(0)

    result = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "groups": {k: groups[k] for k in sorted(groups, key=int)},
        "reached": {"r32": [], "r16": [], "qf": [], "sf": [], "final": []},
        "champion": None,
        "individuals": {"scorer": None, "mvp": None, "young": None},
    }

    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=None)
    args, _ = p.parse_known_args()

    if args.out:
        out = args.out
    else:
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        out = os.path.join(repo_root, "html", "porra", "results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)

    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Written {len(groups)} results → {out}")
    for k in sorted(groups, key=int):
        fh = next((h for i, h, a in FIXTURES if str(i) == k), "?")
        fa = next((a for i, h, a in FIXTURES if str(i) == k), "?")
        v = groups[k]
        print(f"  [{k}] {fh} {v[0]}-{v[1]} {fa}")


if __name__ == "__main__":
    main()
