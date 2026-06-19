"""
scripts/discover_tools.py

Weekly tool discovery. Creates a GitHub Issue with candidates for human review.

Sources:
  1. GitHub Search — new repos with neuroimaging-related topics, sorted by stars
  2. bioRxiv API  — recent neuroscience preprints mentioning GitHub repos

Required env vars:
  GITHUB_TOKEN  — PAT or GITHUB_TOKEN from Actions (issues: write)
  GITHUB_REPO   — "openmritools/openmritools.github.io"
"""

from __future__ import annotations

import os
import re
import sys
import time
import yaml
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO  = os.environ.get("GITHUB_REPO", "")

if not GITHUB_TOKEN:
    sys.exit("Error: GITHUB_TOKEN not set")
if not GITHUB_REPO:
    sys.exit("Error: GITHUB_REPO not set")

HEADERS = {
    "Authorization":        f"Bearer {GITHUB_TOKEN}",
    "Accept":               "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# GitHub topics to query
TOPICS = [
    "neuroimaging",
    "fmri",
    "brain-mri",
    "diffusion-mri",
    "tractography",
    "mri-analysis",
    "brain-imaging",
]

MIN_STARS_NEW         = 25   # new repos (created last 7 days)
MIN_STARS_ESTABLISHED = 50   # established repos (any age)

NOW    = datetime.now(timezone.utc)
SINCE  = NOW - timedelta(days=7)


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_known_repos() -> set[str]:
    known = set()
    for path in Path("_data/tools").glob("*.yml"):
        tools = yaml.safe_load(path.read_text()) or []
        if not isinstance(tools, list):
            continue
        for tool in tools:
            slug = tool.get("github")
            if slug:
                known.add(slug.lower())
    return known


def gh_get(url: str, params: dict | None = None) -> dict | None:
    for attempt in range(3):
        r = requests.get(url, headers=HEADERS, params=params, timeout=15)
        if r.status_code in (429, 403) and int(r.headers.get("X-RateLimit-Remaining", 1)) == 0:
            wait = max(int(r.headers.get("X-RateLimit-Reset", time.time() + 60)) - int(time.time()), 1) + 2
            print(f"    rate limited — waiting {wait}s", flush=True)
            time.sleep(wait)
            continue
        if r.status_code == 422:
            return None  # invalid search query, skip silently
        r.raise_for_status()
        return r.json()
    return None


# ── Source 1: GitHub Search ───────────────────────────────────────────────────

def _search_topic(topic: str, extra_query: str, min_stars: int, seen: set, known: set) -> list[dict]:
    data = gh_get(
        "https://api.github.com/search/repositories",
        params={
            "q":        f"topic:{topic} {extra_query} stars:>={min_stars}",
            "sort":     "stars",
            "order":    "desc",
            "per_page": 30,
        },
    )
    time.sleep(1.2)  # stay well within search rate limit (10 req/min)

    results = []
    for repo in (data or {}).get("items", []):
        slug = repo["full_name"]
        if slug.lower() in known or slug in seen:
            continue
        seen.add(slug)
        results.append({
            "slug":        slug,
            "url":         repo["html_url"],
            "stars":       repo["stargazers_count"],
            "description": (repo["description"] or "").strip(),
            "topics":      repo.get("topics", []),
            "matched_on":  topic,
        })
    return results


def search_github(known: set[str]) -> tuple[list[dict], list[dict]]:
    date_str = SINCE.strftime("%Y-%m-%d")
    seen     = set()
    new_hits  = []
    old_hits  = []

    for topic in TOPICS:
        print(f"  topic:{topic} ...", end=" ", flush=True)

        new = _search_topic(topic, f"created:>{date_str}", MIN_STARS_NEW, seen, known)
        est = _search_topic(topic, "",                      MIN_STARS_ESTABLISHED, seen, known)

        new_hits.extend(new)
        old_hits.extend(est)
        print(f"{len(new)} new  {len(est)} established")

    return (
        sorted(new_hits, key=lambda x: -x["stars"]),
        sorted(old_hits, key=lambda x: -x["stars"])[:20],  # top 20 established
    )


# ── Source 2: bioRxiv ─────────────────────────────────────────────────────────

GITHUB_RE = re.compile(
    r'https?://github\.com/([\w.-]+/[\w.-]+?)(?:\.git)?(?=[/\s"\'<>,;)\]]|$)'
)

def search_biorxiv(known: set[str]) -> list[dict]:
    start_str = SINCE.strftime("%Y-%m-%d")
    end_str   = NOW.strftime("%Y-%m-%d")
    url       = f"https://api.biorxiv.org/details/biorxiv/{start_str}/{end_str}/0/json"

    print(f"  fetching {start_str} → {end_str} ...", end=" ", flush=True)
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"failed ({e})")
        return []

    papers = r.json().get("collection", [])
    print(f"{len(papers)} papers")

    seen_slugs = set()
    candidates = []

    for paper in papers:
        text    = (paper.get("title", "") + " " + paper.get("abstract", ""))
        matches = GITHUB_RE.findall(text)

        for slug in matches:
            # Filter out obvious non-tool repos
            if any(x in slug.lower() for x in ["awesome-", "tutorial", "course", "workshop", "slides"]):
                continue
            if slug.lower() in known or slug in seen_slugs:
                continue
            seen_slugs.add(slug)

            doi = paper.get("doi", "")
            candidates.append({
                "slug":        slug,
                "paper_title": paper.get("title", "").strip(),
                "paper_url":   f"https://www.biorxiv.org/content/{doi}" if doi else "",
            })

    return candidates


# ── Issue creation ────────────────────────────────────────────────────────────

def _repo_table(hits: list[dict]) -> list[str]:
    lines = [
        "| Repo | Stars | Matched topic | Description |",
        "|---|---|---|---|",
    ]
    for r in hits:
        desc = r["description"][:79] + "…" if len(r["description"]) > 79 else r["description"]
        lines.append(f"| [{r['slug']}]({r['url']}) | {r['stars']} | `{r['matched_on']}` | {desc} |")
    return lines


def create_issue(new_hits: list[dict], est_hits: list[dict], biorxiv_hits: list[dict]) -> str:
    week  = NOW.strftime("%Y-%m-%d")
    total = len(new_hits) + len(est_hits) + len(biorxiv_hits)

    lines = [f"## Tool candidates — week of {week}", ""]

    if total == 0:
        lines.append("No new candidates found this week.")
    else:
        lines.append(f"{total} candidate(s) for review. Add to `_data/tools/` if relevant, then close this issue.")
        lines.append("")

    if new_hits:
        lines += [f"### GitHub — {len(new_hits)} new repos this week (≥{MIN_STARS_NEW} stars)", ""]
        lines += _repo_table(new_hits)
        lines.append("")

    if est_hits:
        lines += [f"### GitHub — {len(est_hits)} established repos not yet listed (≥{MIN_STARS_ESTABLISHED} stars)", ""]
        lines += _repo_table(est_hits)
        lines.append("")

    if biorxiv_hits:
        lines += [
            f"### bioRxiv — {len(biorxiv_hits)} preprints mentioning GitHub repos",
            "",
            "| Paper | Repo |",
            "|---|---|",
        ]
        for r in biorxiv_hits:
            title = r["paper_title"][:70] + "…" if len(r["paper_title"]) > 70 else r["paper_title"]
            paper = f"[{title}]({r['paper_url']})" if r["paper_url"] else title
            lines.append(f"| {paper} | [github.com/{r['slug']}](https://github.com/{r['slug']}) |")
        lines.append("")

    lines += [
        "---",
        "*Auto-generated by `scripts/discover_tools.py` — human review required before adding anything.*",
    ]

    resp = requests.post(
        f"https://api.github.com/repos/{GITHUB_REPO}/issues",
        headers=HEADERS,
        json={
            "title":  f"Tool candidates — week of {week}",
            "body":   "\n".join(lines),
            "labels": ["candidates"],
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["html_url"]


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"Loading known repos...")
    known = load_known_repos()
    print(f"  {len(known)} tools already in directory\n")

    print("Searching GitHub...")
    new_hits, est_hits = search_github(known)
    print(f"  → {len(new_hits)} new this week, {len(est_hits)} established not yet listed\n")

    print("Searching bioRxiv...")
    biorxiv_hits = search_biorxiv(known)
    print(f"  → {len(biorxiv_hits)} papers with GitHub links\n")

    print("Creating issue...")
    url = create_issue(new_hits, est_hits, biorxiv_hits)
    print(f"  → {url}")


if __name__ == "__main__":
    main()
