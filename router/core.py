"""Route a prompt to the areas it touches. An area is one markdown file with frontmatter:

    ---
    keywords: [budget, rent, "can i afford"]
    needs: {fitness: ["Goals"]}      # sections to pull from other areas
    updated: 2026-10-01              # older than STALE_DAYS -> flagged
    ---
    ## Current values
    ...
"""
import datetime as dt
import json
import os
import re

AREAS_DIR = os.environ.get("ROUTER_AREAS", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "areas"))
STALE_DAYS = int(os.environ.get("ROUTER_STALE_DAYS", "45"))


def parse_area(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    if not m:
        return None
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            try:
                meta[k.strip()] = json.loads(v.strip())
            except ValueError:
                meta[k.strip()] = v.strip()
    meta["name"] = os.path.splitext(os.path.basename(path))[0]
    meta["body"] = m.group(2).strip()
    return meta


def load_areas(d=None):
    d = d or AREAS_DIR
    out = {}
    for f in sorted(os.listdir(d)):
        if f.endswith(".md"):
            a = parse_area(os.path.join(d, f))
            if a:
                out[a["name"]] = a
    return out


def section(body, title):
    m = re.search(r"^## %s\s*\n(.*?)(?=^## |\Z)" % re.escape(title), body, re.S | re.M)
    return m.group(0).strip() if m else ""


def classify(prompt, areas):
    p = prompt.lower()
    hits = []
    for name, a in areas.items():
        for kw in a.get("keywords", []):
            if re.search(r"(?<!\w)%s(?!\w)" % re.escape(kw.lower()), p):
                hits.append(name)
                break
    return hits


def is_stale(area, today=None):
    today = today or dt.date.today()
    try:
        return (today - dt.date.fromisoformat(str(area.get("updated")))).days > STALE_DAYS
    except ValueError:
        return True


def build_context(prompt, areas, already=(), today=None):
    """-> (text, areas_injected). Areas already injected this session are skipped."""
    names = [n for n in classify(prompt, areas) if n not in already]
    if not names:
        return "", []
    parts, done = [], []
    for n in names:
        a = areas[n]
        flag = "  [STALE: verify against the live source before quoting]" if is_stale(a, today) else ""
        parts.append("# Area: %s%s\n%s" % (n, flag, a["body"]))
        done.append(n)
        for other, titles in (a.get("needs") or {}).items():
            if other in areas and other not in names:
                for t in titles:
                    s = section(areas[other]["body"], t)
                    if s:
                        parts.append("# From %s\n%s" % (other, s))
    return "\n\n".join(parts), done
