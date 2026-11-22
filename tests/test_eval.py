import csv
import tempfile
import unittest
from pathlib import Path

from scripts.eval import is_correct, main, read_questions, run_eval, summarize

SAMPLE = Path(__file__).resolve().parent.parent / "scripts" / "sample_questions.csv"


class EvalTests(unittest.TestCase):
    def test_sample_runs_with_mock(self):
        res = run_eval(read_questions(SAMPLE))
        self.assertEqual(len(res), 5)
        s = summarize(res)
        self.assertEqual(s["questions"], 5)
        self.assertEqual(s["errors"], 0)
        self.assertIsNone(s["avg_cost"])  # pricing.yaml is empty on purpose: unknown, not 0
        self.assertEqual(sum(x["search_calls"] for x in res), 3)  # price, phone, hours questions

    def test_correctness_check(self):
        self.assertTrue(is_correct("התשובה היא  42 שקלים", "42"))
        self.assertFalse(is_correct("לא יודע", "42"))
        self.assertFalse(is_correct("כלום", ""))

    def test_mock_echo_counts_as_correct_when_answer_in_question(self):
        # Mock LLM echoes the question, so this verifies the matching path end to end.
        with tempfile.TemporaryDirectory() as d:
            src, out = Path(d) / "q.csv", Path(d) / "r.csv"
            src.write_text("question,type,correct_answer,source\nמה זה בננה?,knowledge,בננה,x\n"
                           "מה זה תפוח?,knowledge,אגס,x\n", encoding="utf-8")
            self.assertEqual(main([str(src), "--out", str(out)]), 0)
            with out.open(encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
            self.assertEqual([r["correct"] for r in rows], ["True", "False"])

    def test_missing_column_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.csv"
            p.write_text("question,type\nx,y\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                read_questions(p)


if __name__ == "__main__":
    unittest.main()
