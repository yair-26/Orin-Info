import unittest

from scripts.chat import chat


class ChatTests(unittest.TestCase):
    def test_five_turns_with_mock(self):
        out = []
        rc = chat(iter(["שלום\n", "מה מחיר חלב?\n", "תודה\n", "מה שעות הפתיחה?\n", "להתראות\n", "\n"]), out.append)
        self.assertEqual(rc, 0)
        self.assertEqual(len(out), 10)  # answer + stats line per turn
        self.assertIn("example.invalid", out[2])
        self.assertIn("לא ידועה", out[1])  # no prices configured yet

if __name__ == "__main__":
    unittest.main()
