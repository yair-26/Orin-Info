"""Question-set evaluation (T-08).

Usage: python3 -m scripts.eval QUESTIONS.csv [--llm NAME ...] [--out RESULTS.csv]
CSV columns: question,type,correct_answer,source. The real 50 questions come from humans
(docs/STATUS.md, 'requires a person'); scripts/sample_questions.csv is infrastructure test data only.
Correctness here is a crude automatic check (normalized substring of correct_answer in the answer);
treat it as a first filter, a person should review failures and borderline cases.
"""
from __future__ import annotations

import argparse
import csv
import statistics
import sys

from core.config import load_limits, load_pricing, load_providers
from core.conversation import TurnRecord, answer_turn
from core.costs import CostCalculator
from core.limits import CallLimits, LimitExceeded
from core.providers.registry import get_provider


def _norm(s: str) -> str:
    return " ".join(s.lower().split())


def is_correct(answer: str, correct: str) -> bool:
    return bool(correct.strip()) and _norm(correct) in _norm(answer)


def read_questions(path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    for need in ("question", "type", "correct_answer", "source"):
        if rows and need not in rows[0]:
            raise ValueError(f"questions CSV is missing column: {need}")
    return rows


def run_eval(rows: list[dict], llm_name: str | None = None) -> list[dict]:
    llm = get_provider("llm", name=llm_name)
    search = get_provider("search")
    names = {**load_providers(), "llm": llm_name or load_providers()["llm"]}
    costs = CostCalculator(load_pricing(), names)
    out = []
    for r in rows:
        limits = CallLimits(load_limits())
        t = TurnRecord(turn_id=1)
        limits.start_turn()
        error = None
        try:
            answer = answer_turn([{"role": "user", "content": r["question"]}], llm, search, limits, t)
        except LimitExceeded as e:
            answer, error = "", f"limit_exceeded:{e.reason}"
        cost_parts = {"llm": costs.llm(t.input_tokens, t.output_tokens), "search": costs.search(t.search_calls)}
        known = None if None in cost_parts.values() else sum(cost_parts.values())
        out.append({"question": r["question"], "type": r["type"], "llm": llm_name or names["llm"],
                    "answer": answer, "correct": is_correct(answer, r["correct_answer"]),
                    "latency_ms": t.llm_ms + t.search_ms, "words": len(answer.split()),
                    "search_calls": t.search_calls, "cost": known, "error": error})
    return out


def summarize(results: list[dict]) -> dict:
    n = len(results)
    costs = [x["cost"] for x in results]
    return {"questions": n,
            "accuracy": sum(x["correct"] for x in results) / n if n else None,
            "avg_latency_ms": statistics.mean(x["latency_ms"] for x in results) if n else None,
            "avg_words": statistics.mean(x["words"] for x in results) if n else None,
            "avg_cost": None if not n or None in costs else statistics.mean(costs),
            "errors": sum(1 for x in results if x["error"])}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("questions")
    ap.add_argument("--llm", action="append", help="LLM provider name; repeat to compare several")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    rows = read_questions(a.questions)
    all_results = []
    for name in a.llm or [None]:
        res = run_eval(rows, name)
        all_results += res
        s = summarize(res)
        fmt = lambda v: "לא ידוע" if v is None else f"{v:.3f}"
        print(f"[{res[0]['llm'] if res else name}] שאלות={s['questions']} נכונות={fmt(s['accuracy'])} "
              f"השהיה={fmt(s['avg_latency_ms'])}ms מילים={fmt(s['avg_words'])} עלות={fmt(s['avg_cost'])} שגיאות={s['errors']}")
    if a.out and all_results:
        with open(a.out, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(all_results[0]))
            w.writeheader()
            w.writerows(all_results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
