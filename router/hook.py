"""UserPromptSubmit hook: python router/hook.py   (event JSON on stdin)

Prints the matching areas as additional context, once per session per area.
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from router import core  # noqa: E402


def seen_file(session):
    d = os.environ.get("ROUTER_STATE_DIR") or tempfile.gettempdir()
    return os.path.join(d, "router-seen-%s.json" % "".join(c for c in session if c.isalnum() or c in "-_"))


def _load(p):
    with open(p) as fh:
        return json.load(fh)


def _dump(p, v):
    with open(p, "w") as fh:
        json.dump(v, fh)


def run(event, areas=None):
    areas = areas or core.load_areas()
    sf = seen_file(event.get("session_id") or "default")
    try:
        seen = _load(sf)
    except (OSError, ValueError):
        seen = []
    text, done = core.build_context(event.get("prompt") or "", areas, seen)
    if done:
        _dump(sf, seen + done)
    return text


if __name__ == "__main__":
    try:
        ev = json.load(sys.stdin)
    except ValueError:
        sys.exit(0)
    out = run(ev)
    if out:
        print(out)
