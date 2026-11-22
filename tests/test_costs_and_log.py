import tempfile
import unittest
from pathlib import Path

from core.conversation import run_call
from core.costs import CostCalculator
from core.limits import CallLimits
from core.providers.mock import MockLLM, MockSearch, MockSTT, MockTelephony, MockTTS
from core.turnlog import TurnLog, read_log

LIMITS = {"max_call_seconds": 300, "max_tool_calls_per_call": 5, "max_search_calls_per_turn": 2}
NAMES = {k: "mock" for k in ("stt", "llm", "tts", "search", "telephony")}
# FICTIONAL TEST PRICES. Not real vendor prices. Never copy into config/pricing.yaml.
FAKE = {
    "stt": {"mock": {"per_minute": 6.0}},
    "llm": {"mock": {"input_per_1m_tokens": 1_000_000.0, "output_per_1m_tokens": 2_000_000.0}},
    "tts": {"mock": {"per_1k_chars": 10.0}},
    "search": {"mock": {"per_call": 0.5}},
    "telephony": {"mock": {"per_minute": 60.0}},
}


def call(pricing, utterances, log=None):
    tel = MockTelephony(utterances)
    return run_call(tel, MockSTT(), MockLLM(), MockTTS(), MockSearch(), CallLimits(LIMITS),
                    costs=CostCalculator(pricing, NAMES), log=log)


class CostTests(unittest.TestCase):
    def test_formulas_with_fake_prices(self):
        c = CostCalculator(FAKE, NAMES)
        self.assertAlmostEqual(c.stt(30), 3.0)            # 0.5 min * 6
        self.assertAlmostEqual(c.llm(2, 1), 4.0)          # 2*1 + 1*2
        self.assertAlmostEqual(c.tts(500), 5.0)
        self.assertAlmostEqual(c.search(3), 1.5)
        self.assertAlmostEqual(c.telephony(30), 30.0)

    def test_missing_prices_are_unknown_not_zero(self):
        for pricing in (None, {}, {"stt": {"mock": {"per_minute": None}}}):
            c = CostCalculator(pricing, NAMES)
            self.assertIsNone(c.stt(30))
            self.assertIsNone(c.llm(10, 10))
            self.assertIsNone(c.tts(100))

    def test_call_total_unknown_when_any_price_missing(self):
        partial = {k: v for k, v in FAKE.items() if k != "tts"}
        rec = call(partial, ["שלום"])
        self.assertIsNone(rec.cost_breakdown["tts"])
        self.assertIsNone(rec.total_cost)

    def test_call_total_known_with_full_prices(self):
        rec = call(FAKE, ["שלום", "מה מחיר חלב?"])
        self.assertIsNotNone(rec.total_cost)
        self.assertAlmostEqual(rec.total_cost, sum(rec.cost_breakdown.values()))
        self.assertAlmostEqual(rec.cost_breakdown["search"], 0.5)  # one search in two turns


class LogTests(unittest.TestCase):
    def test_log_lines_and_privacy(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "calls.jsonl"
            call(FAKE, ["סיסמה סודית", "מה מחיר חלב?"], log=TurnLog(path))
            lines = read_log(path)
            self.assertEqual([x["type"] for x in lines], ["turn", "turn", "call"])
            self.assertEqual(lines[1]["classification"], "lookup")
            self.assertEqual(lines[0]["classification"], "chat")
            self.assertEqual(lines[2]["status"], "completed")
            raw = path.read_text(encoding="utf-8")
            self.assertNotIn("סודית", raw)
            self.assertNotIn("חלב", raw)


if __name__ == "__main__":
    unittest.main()
