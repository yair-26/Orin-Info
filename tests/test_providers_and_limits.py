import tempfile
import unittest
from pathlib import Path

from core.config import load_limits
from core.conversation import run_call
from core.limits import CallLimits
from core.providers.mock import MockLLM, MockSearch, MockSTT, MockTelephony, MockTTS
from core.providers.registry import get_provider

LIMITS = {"max_call_seconds": 300, "max_tool_calls_per_call": 5, "max_search_calls_per_turn": 2}


def build(utterances, limits):
    tel = MockTelephony(utterances)
    return tel, run_call(tel, MockSTT(), MockLLM(), MockTTS(), MockSearch(), limits)


class RegistryTests(unittest.TestCase):
    def test_default_config_gives_mocks(self):
        for kind in ("stt", "tts", "llm", "search", "telephony"):
            self.assertIsNotNone(get_provider(kind))

    def test_swap_by_config_only(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "providers.yaml").write_text("llm: nonexistent\n", encoding="utf-8")
            with self.assertRaises(ValueError) as cm:
                get_provider("llm", config_dir=Path(d))
            self.assertIn("not implemented", str(cm.exception))


class ConversationTests(unittest.TestCase):
    def test_five_turn_call_with_and_without_search(self):
        tel, rec = build(["שלום", "מה מחיר חלב?", "תודה", "מה שעות פתיחה של הדואר?", "להתראות"],
                         CallLimits(LIMITS))
        self.assertEqual(rec.status, "completed")
        self.assertEqual(len(rec.turns), 5)
        self.assertEqual([t.search_calls for t in rec.turns], [0, 1, 0, 1, 0])
        self.assertEqual(len(tel.sent), 5)
        self.assertTrue(tel.hung_up)

    def test_answer_with_search_includes_source_and_date(self):
        tel, _ = build(["מה מחיר חלב?"], CallLimits(LIMITS))
        spoken = tel.sent[0].decode("utf-8")
        self.assertIn("example.invalid", spoken)
        self.assertIn("2026-11-22", spoken)

    def test_record_has_no_conversation_text(self):
        _, rec = build(["סיסמה סודית"], CallLimits(LIMITS))
        self.assertNotIn("סודית", repr(rec))


class LimitTests(unittest.TestCase):
    def test_call_seconds_cap_stops_call(self):
        now = [0.0]
        limits = CallLimits(LIMITS, clock=lambda: now[0])
        tel = MockTelephony(["אחת", "שתיים", "שלוש"])
        orig = tel.receive_audio

        def advancing():
            a = orig()
            now[0] += 200  # each turn "takes" 200s
            return a

        tel.receive_audio = advancing
        rec = run_call(tel, MockSTT(), MockLLM(), MockTTS(), MockSearch(), limits)
        self.assertEqual(rec.status, "limit_exceeded:call_seconds")
        self.assertLess(len(rec.turns), 3)
        self.assertTrue(tel.hung_up)

    def test_tool_calls_cap_stops_call(self):
        cfg = dict(LIMITS, max_tool_calls_per_call=2)
        _, rec = build(["מחיר א", "מחיר ב", "מחיר ג"], CallLimits(cfg))
        self.assertEqual(rec.status, "limit_exceeded:tool_calls")
        self.assertEqual(len(rec.turns), 2)

    def test_search_per_turn_cap_stops_call(self):
        cfg = dict(LIMITS, max_search_calls_per_turn=0)
        _, rec = build(["מחיר חלב"], CallLimits(cfg))
        self.assertEqual(rec.status, "limit_exceeded:search_calls_per_turn")

    def test_real_limits_yaml_loads(self):
        cfg = load_limits()
        for key in LIMITS:
            self.assertIn(key, cfg)


if __name__ == "__main__":
    unittest.main()
