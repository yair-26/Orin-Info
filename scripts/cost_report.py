"""Cost report from a JSONL turn log (T-07).  Usage: python3 -m scripts.cost_report LOG.jsonl"""
from __future__ import annotations

import statistics
import sys

from core.reporting import COST_KEYS, split_log, summary
from core.turnlog import read_log


def _fmt(x, nd=4):
    return "לא ידועה" if x is None else f"{x:.{nd}f}"


def format_report(lines: list[dict]) -> str:
    calls, _ = split_log(lines)
    s = summary(lines)
    known = [c["total_cost"] for c in calls if c["total_cost"] is not None]
    out = [
        f"שיחות: {s['calls_count']}   דקות: {s['total_minutes']:.2f}",
        f"שיחות עם עלות לא ידועה: {s['calls_count'] - len(known)}",
        f"עלות כוללת: {_fmt(s['total_cost'])}",
        f"עלות לדקה (ממוצע): {_fmt(s['avg_cost_per_minute'])}",
        f"עלות לשיחה, ממוצע: {_fmt(statistics.mean(known) if known else None)} | חציון: {_fmt(s['median_cost_per_call'])}",
        "לפי רכיב:",
    ]
    out += [f"  {k}: {_fmt(s['cost_by_component'][k])}" for k in COST_KEYS]
    out.append("שאלות עם חיפוש מול בלי (לפי תור, בלי טלפוניה):")
    for name, g in s["search_vs_no_search"].items():
        lat = "אין נתונים" if g["avg_latency_ms"] is None else f"{g['avg_latency_ms']:.0f}ms"
        out.append(f"  {name}: השהיה ממוצעת {lat} | עלות ממוצעת {_fmt(g['avg_cost'])}")
    return "\n".join(out)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python3 -m scripts.cost_report LOG.jsonl")
    print(format_report(read_log(sys.argv[1])))
