#!/usr/bin/env python3
"""File one merged contribution into data/entries and record its repository's star count.

    python3 bin/add_entry.py --repo caddyserver/caddy --pr '#8152' \\
        --title 'Stat symlink targets by the decoded path in browse listings' \\
        --date 'oct 2026' --stars-num 79126

--pr is '#<number>' for a pull request, or a short SHA for a change that landed as a commit.
Refuses a contribution already filed unless --force is passed. Pushing the new file makes the
refresh workflow rewrite README.md and the repository pages.
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTRIES = os.path.join(ROOT, "data", "entries")
STARS = os.path.join(ROOT, "data", "stars.json")
NAMES = os.path.join(ROOT, "data", "names.json")
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]


def front(path):
    meta = {}
    with open(path, encoding="utf-8") as f:
        _, block, _ = f.read().split("---\n", 2)
    for line in block.strip().splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    return meta


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True, help="owner/name")
    ap.add_argument("--pr", required=True, help="'#<number>', or a short commit SHA")
    ap.add_argument("--title", required=True, help="the pull request's title as merged")
    ap.add_argument("--date", required=True, help="merge month, like 'oct 2026'")
    ap.add_argument("--stars-num", type=int, help="the repository's live star count")
    ap.add_argument("--name", help="the repository's display name, like 'Nautilus Trader', needed the first time a repository is filed")
    ap.add_argument("--force", action="store_true", help="overwrite a contribution already filed")
    a = ap.parse_args()

    if not re.fullmatch(r"[\w.-]+/[\w.-]+", a.repo):
        sys.exit("--repo must be owner/name")
    if not re.fullmatch(r"#\d+|[0-9a-f]{7,40}", a.pr):
        sys.exit("--pr must be '#<number>' or a commit SHA")
    parts = a.date.split()
    if len(parts) != 2 or parts[0][:3].lower() not in MONTHS or not parts[1].isdigit():
        sys.exit("--date must be a month and year, like 'oct 2026'")
    date = "%s %s" % (parts[0][:3].lower(), parts[1])

    for name in os.listdir(ENTRIES):
        if name.endswith(".md") and not a.force:
            meta = front(os.path.join(ENTRIES, name))
            if meta.get("repo", "").lower() == a.repo.lower() and meta.get("pr") == a.pr:
                sys.exit("%s %s is already filed in data/entries/%s, pass --force to overwrite it" % (a.repo, a.pr, name))

    path = os.path.join(ENTRIES, "%s-%s.md" % (a.repo.split("/")[1], a.pr.lstrip("#")))
    with open(path, "w", encoding="utf-8") as f:
        f.write("---\nrepo: %s\npr: %s\ntitle: %s\ndate: %s\n---\n" % (a.repo, a.pr, a.title.strip(), date))

    with open(NAMES, encoding="utf-8") as f:
        names = json.load(f)
    if a.name:
        names[a.repo] = a.name.strip()
        save_json(NAMES, names)
    elif a.repo not in names:
        print("warning: %s has no display name, so the pages will show %r. Pass --name to set one." % (a.repo, a.repo.split("/")[1]))
    if a.stars_num is not None:
        with open(STARS, encoding="utf-8") as f:
            stars = json.load(f)
        stars[a.repo] = a.stars_num
        save_json(STARS, dict(sorted(stars.items(), key=lambda kv: kv[0].lower())))
    print("filed %s %s as %s" % (a.repo, a.pr, os.path.relpath(path, ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
