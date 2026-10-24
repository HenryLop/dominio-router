"""python -m router check            validate every area file
python -m router replay FILE.jsonl  re-run past prompts, compare with expected areas
python -m router route "text"       show what a prompt would inject
"""
import json
import sys

from router import core


def check(areas):
    bad = 0
    for n, a in areas.items():
        probs = []
        if not a.get("keywords"):
            probs.append("no keywords")
        if core.is_stale(a):
            probs.append("stale (updated %s)" % a.get("updated"))
        for other, titles in (a.get("needs") or {}).items():
            if other not in areas:
                probs.append("needs unknown area %s" % other)
            else:
                probs += ["needs missing section '%s' in %s" % (t, other) for t in titles if not core.section(areas[other]["body"], t)]
        print("%-10s %s" % (n, "; ".join(probs) or "ok"))
        bad += bool(probs)
    return 1 if bad else 0


def replay(path, areas):
    fails = 0
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    for line in lines:
        if not line.strip():
            continue
        row = json.loads(line)
        got = core.classify(row["prompt"], areas)
        ok = sorted(got) == sorted(row["expect"])
        fails += not ok
        print("%s  %-45s expect=%s got=%s" % ("ok  " if ok else "FAIL", row["prompt"][:45], row["expect"], got))
    print("%d failure(s)" % fails)
    return 1 if fails else 0


def main():
    areas = core.load_areas()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "check":
        return check(areas)
    if cmd == "replay":
        return replay(sys.argv[2], areas)
    if cmd == "route":
        text, done = core.build_context(" ".join(sys.argv[2:]), areas)
        print(text or "(nothing injected)")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
