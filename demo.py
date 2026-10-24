"""One-command demo: python demo.py"""
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
os.environ["ROUTER_STATE_DIR"] = tempfile.mkdtemp(prefix="router-demo-")
sys.path.insert(0, ROOT)
from router import core, hook  # noqa: E402

areas = core.load_areas()
for sid, prompt in [("demo", "Can I afford the spring trip?"),
                    ("demo", "and what is my rent again?"),
                    ("demo", "tell me a joke"),
                    ("demo", "log my workout")]:
    out = hook.run({"session_id": sid, "prompt": prompt}, areas)
    print('PROMPT: "%s"' % prompt)
    print("  injected:", ", ".join(n for n in core.classify(prompt, areas) if "# Area: %s" % n in out) or "nothing")
    for line in out.splitlines():
        if line.startswith("# "):
            print("   ", line)
    print()
print("$ python -m router replay tests/replay.jsonl", flush=True)
subprocess.run([sys.executable, "-m", "router", "replay", os.path.join(ROOT, "tests", "replay.jsonl")], cwd=ROOT)
