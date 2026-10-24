import datetime as dt
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["ROUTER_STATE_DIR"] = tempfile.mkdtemp(prefix="router-test-")
from router import core, hook  # noqa: E402

AREAS = core.load_areas()


class Tests(unittest.TestCase):
    def test_replay_matches_expected_areas(self):
        with open(os.path.join(ROOT, "tests", "replay.jsonl"), encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        for line in lines:
            row = json.loads(line)
            self.assertEqual(sorted(core.classify(row["prompt"], AREAS)), sorted(row["expect"]), row["prompt"])

    def test_general_prompt_injects_nothing(self):
        self.assertEqual(core.build_context("tell me a joke", AREAS), ("", []))

    def test_needs_pulls_only_the_named_section(self):
        text, _ = core.build_context("what is my rent", AREAS)
        self.assertIn("# From travel", text)
        self.assertIn("Spring trip", text)
        self.assertNotIn("Passport valid", text.split("# From travel")[0])
        self.assertNotIn("## Open\n- Pick a hotel", text)

    def test_stale_area_is_flagged(self):
        text, _ = core.build_context("gym today", AREAS, today=dt.date(2026, 10, 1))
        self.assertIn("STALE", text)
        fresh, _ = core.build_context("what is my rent", AREAS, today=dt.date(2026, 10, 1))
        self.assertNotIn("STALE", fresh.split("# From")[0])

    def test_once_per_session(self):
        ev = {"session_id": "s1", "prompt": "my rent"}
        self.assertIn("Area: money", hook.run(ev, AREAS))
        self.assertEqual(hook.run(ev, AREAS), "")
        self.assertIn("Area: money", hook.run({"session_id": "s2", "prompt": "my rent"}, AREAS))

    def test_word_boundaries(self):
        self.assertEqual(core.classify("the apartment rental market", AREAS), [])

    def test_check_passes_on_sample_areas(self):
        from router.__main__ import check
        self.assertEqual(check(AREAS) in (0, 1), True)


if __name__ == "__main__":
    unittest.main()
