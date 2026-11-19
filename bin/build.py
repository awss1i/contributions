#!/usr/bin/env python3
"""Write README.md and the repository pages in repos/ from data/.

    python3 bin/build.py

README.md lists every repository, most contributions first. A repository with PAGE_AT or more
contributions gets its own page at repos/<owner>/<name>.md, and the README links to it. Below that,
the README links each pull request directly.

Everything in repos/ is written by this script. Pages for repositories that no longer qualify are removed.
"""
import os
import sys
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
PAGES = os.path.join(ROOT, "repos")
PAGE_AT = 2
PROFILE = "https://github.com/awss1i"
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]


def read_entry(path):
    with open(path, encoding="utf-8") as f:
        _, front, _ = f.read().split("---\n", 2)
    meta = {}
    for line in front.strip().splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    return meta


def month_key(date):
    parts = date.split()
    if len(parts) == 2 and parts[0][:3].lower() in MONTHS:
        return int(parts[1]) * 12 + MONTHS.index(parts[0][:3].lower())
    return 0


def month_label(date):
    parts = date.split()
    if len(parts) == 2 and parts[0][:3].lower() in MONTHS:
        return "%s %s" % (parts[0][:3].capitalize(), parts[1])
    return date


def short_count(n):
    if n >= 1000:
        k = n / 1000
        return ("%.1fk" % k).replace(".0k", "k") if k < 10 else "%dk" % round(k)
    return str(n)


def cell(text):
    return text.replace("|", "\\|")


def load():
    with open(os.path.join(DATA, "stars.json"), encoding="utf-8") as f:
        stars = json.load(f)
    with open(os.path.join(DATA, "names.json"), encoding="utf-8") as f:
        names = json.load(f)
    folder = os.path.join(DATA, "entries")
    repos = {}
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".md"):
            continue
        e = read_entry(os.path.join(folder, name))
        url = "https://github.com/" + e["repo"]
        r = repos.setdefault(e["repo"], {
            "repo": e["repo"], "url": url, "name": names.get(e["repo"], e["repo"].split("/")[-1]),
            "stars": stars.get(e["repo"], 0), "entries": [],
        })
        pr = e["pr"]
        link = "%s/%s/%s" % (url, "pull" if pr.startswith("#") else "commit", pr.lstrip("#"))
        r["entries"].append({"label": pr, "url": link, "title": e.get("title", ""), "date": e.get("date", ""),
                             "number": int(pr[1:]) if pr.startswith("#") and pr[1:].isdigit() else 0})
    for r in repos.values():
        # Newest month first. Within a month, higher pull request numbers are newer.
        r["entries"].sort(key=lambda e: (-month_key(e["date"]), -e["number"]))
        r["latest"] = r["entries"][0]["date"]
        r["page"] = "repos/%s.md" % r["repo"] if len(r["entries"]) >= PAGE_AT else None
    # Most contributions first, then the more starred repository.
    return sorted(repos.values(), key=lambda r: (-len(r["entries"]), -r["stars"], r["name"].lower()))


def plural(n, one, many):
    return "%d %s" % (n, one if n == 1 else many)


def readme(repos):
    rows = []
    for r in repos:
        n = len(r["entries"])
        if r["page"]:
            work = "[%s](%s)" % (plural(n, "contribution", "contributions"), r["page"])
        else:
            work = " · ".join("[%s](%s)" % (e["label"], e["url"]) for e in r["entries"])
        rows.append("| [%s](%s) | %s | %s | %s |" % (cell(r["name"]), r["url"], short_count(r["stars"]), work, month_label(r["latest"])))
    total = sum(len(r["entries"]) for r in repos)
    return """<p align="center"><a href="%(profile)s">Awss</a> › Contributions [%(total)d]</p>

<div align="center">

| Repo | Stars | Contributions | Latest |
|---|---|---|---|
%(rows)s

</div>
""" % {"profile": PROFILE, "total": total, "rows": "\n".join(rows)}


def repo_page(r, total):
    depth = "../" * (r["page"].count("/"))
    rows = "\n".join("| [%s](%s) | %s | %s |" % (e["label"], e["url"], cell(e["title"]), month_label(e["date"]))
                     for e in r["entries"])
    return """<h1 align="center">%(name)s</h1>

<p align="center"><a href="%(profile)s">Awss</a> › <a href="%(up)sREADME.md">Contributions [%(total)d]</a> › %(name)s</p>

<p align="center"><a href="%(url)s">%(repo)s</a> · %(stars)s stars · %(count)s</p>

---

<div align="center">

| PR | Title | Merged |
|---|---|---|
%(rows)s

</div>
""" % {"profile": PROFILE, "total": total, "name": r["name"], "up": depth, "url": r["url"], "repo": r["repo"], "stars": short_count(r["stars"]),
       "count": plural(len(r["entries"]), "contribution", "contributions"), "rows": rows}


def write(rel, text):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    repos = load()
    write("README.md", readme(repos))
    wanted = set()
    for r in repos:
        if r["page"]:
            write(r["page"], repo_page(r, sum(len(x["entries"]) for x in repos)))
            wanted.add(os.path.join(ROOT, r["page"]))
    if os.path.isdir(PAGES):
        for folder, _, files in os.walk(PAGES, topdown=False):
            for name in files:
                path = os.path.join(folder, name)
                if path.endswith(".md") and path not in wanted:
                    os.remove(path)
                    print("removed", os.path.relpath(path, ROOT))
            if folder != PAGES and not os.listdir(folder):
                os.rmdir(folder)
    print("wrote README.md and %d repository pages" % len(wanted))
    return 0


if __name__ == "__main__":
    sys.exit(main())
