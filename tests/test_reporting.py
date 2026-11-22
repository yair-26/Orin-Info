import json
import tempfile
import unittest
from pathlib import Path

from core.reporting import call_detail, call_list, summary
from scripts.cost_report import format_report
from scripts.make_mock_data import OUT, generate_log, write_all

CALL_LIST_KEYS = {"call_id", "started_at", "duration_seconds", "status", "total_cost", "turns_count"}
DETAIL_KEYS = {"call_id", "started_at", "ended_at", "duration_seconds", "status", "total_cost",
               "cost_breakdown", "turns"}
TURN_KEYS = {"turn_id", "latency_ms_by_component", "classification", "had_search", "error"}
SUMMARY_KEYS = {"calls_count", "total_minutes", "total_cost", "avg_cost_per_minute",
                "median_cost_per_call", "cost_by_component", "search_vs_no_search"}
FORBIDDEN = ("phone", "transcript", "content", "text")


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.lines = generate_log()

    def test_shapes_match_contract(self):
        rows = call_list(self.lines, limit=100)
        self.assertEqual(len(rows), 12)
        self.assertEqual(set(rows[0]), CALL_LIST_KEYS)
        d = call_detail(self.lines, rows[0]["call_id"])
        self.assertEqual(set(d), DETAIL_KEYS)
        self.assertEqual(set(d["cost_breakdown"]), {"stt", "llm", "tts", "search", "telephony"})
        self.assertEqual(set(d["turns"][0]), TURN_KEYS)
        self.assertEqual(set(summary(self.lines)), SUMMARY_KEYS)
        self.assertIsNone(call_detail(self.lines, "nope"))

    def test_no_phone_or_content_keys_anywhere(self):
        blob = json.dumps([call_list(self.lines), summary(self.lines)]).lower()
        for word in FORBIDDEN:
            self.assertNotIn(f'"{word}', blob)

    def test_filters(self):
        self.assertEqual(len(call_list(self.lines, status="limit_exceeded:call_seconds")), 1)
        self.assertEqual(len(call_list(self.lines, limit=3, offset=2)), 3)

    def test_unknown_cost_propagates_not_zero(self):
        lines = generate_log()
        for x in lines:
            if x["type"] == "call" and x["call_id"] == "mock0001":
                x["cost_breakdown"]["tts"] = None
                x["total_cost"] = None
        s = summary(lines)
        self.assertIsNone(s["total_cost"])
        self.assertIsNone(s["median_cost_per_call"])
        self.assertIsNone(s["cost_by_component"]["tts"])
        self.assertIsNotNone(s["cost_by_component"]["stt"])
        self.assertIn("לא ידועה", format_report(lines))

    def test_report_runs(self):
        self.assertIn("עלות לדקה", format_report(self.lines))


class MockDataInSyncTests(unittest.TestCase):
    def test_committed_mock_data_matches_generator(self):
        with tempfile.TemporaryDirectory() as d:
            write_all(Path(d))
            for name in ("calls.json", "summary.json", "sample_log.jsonl", "calls/mock0001.json"):
                self.assertEqual((Path(d) / name).read_text(encoding="utf-8"),
                                 (OUT / name).read_text(encoding="utf-8"), name)

    def test_committed_mock_data_uses_lf_only(self):
        # Committed data must be byte-stable across Windows, WSL and CI (see .gitattributes).
        for path in (OUT / "sample_log.jsonl", OUT / "calls.json", OUT / "summary.json",
                     OUT / "calls" / "mock0001.json"):
            self.assertNotIn(b"\r\n", path.read_bytes(), path.name)

    def test_generator_output_uses_lf_only(self):
        with tempfile.TemporaryDirectory() as d:
            write_all(Path(d))
            for path in Path(d).rglob("*"):
                if path.is_file():
                    self.assertNotIn(b"\r\n", path.read_bytes(), path.name)


if __name__ == "__main__":
    unittest.main()
