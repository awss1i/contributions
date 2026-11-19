#!/usr/bin/env python3
"""Refresh data/stars.json from GitHub for every repository in data/entries.

    python3 bin/refresh_stars.py

Uses GITHUB_TOKEN when it's set. If a lookup fails, the repository keeps its existing count,
so a network error never blanks a number.
"""
import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STARS = os.path.join(ROOT, "data", "stars.json")
ENTRIES = os.path.join(ROOT, "data", "entries")


def repos():
    found = set()
    for name in os.listdir(ENTRIES):
        if not name.endswith(".md"):
            continue
        with open(os.path.join(ENTRIES, name), encoding="utf-8") as f:
            for line in f:
                if line.startswith("repo:"):
                    found.add(line.split(":", 1)[1].strip())
                    break
    return sorted(found, key=str.lower)


def fetch(repo, token):
    req = urllib.request.Request("https://api.github.com/repos/" + repo,
                                 headers={"Accept": "application/vnd.github+json", "User-Agent": "contributions-refresh"})
    if token:
        req.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(req, timeout=20) as res:
        return json.load(res)["stargazers_count"]


def main():
    with open(STARS, encoding="utf-8") as f:
        stars = json.load(f)
    token = os.environ.get("GITHUB_TOKEN", "")
    changed = failed = 0
    for repo in repos():
        try:
            n = fetch(repo, token)
        except Exception as e:
            failed += 1
            print("%s: kept %s (%s)" % (repo, stars.get(repo, 0), e))
            continue
        if stars.get(repo) != n:
            print("%s: %s -> %s" % (repo, stars.get(repo, 0), n))
            stars[repo] = n
            changed += 1
    with open(STARS, "w", encoding="utf-8") as f:
        json.dump(dict(sorted(stars.items(), key=lambda kv: kv[0].lower())), f, indent=2)
        f.write("\n")
    print("%d repositories changed, %d lookups failed" % (changed, failed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
