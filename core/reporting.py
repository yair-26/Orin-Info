"""Aggregations over the JSONL log, shaped like docs/api-contracts.md (draft v0.1).

Used by scripts/cost_report.py, scripts/make_mock_data.py and later by the API (T-16).
Unknown costs stay None: any aggregate that includes an unknown part is None, never a partial sum.
"""
from __future__ import annotations

import statistics

from .costs import total_or_none

LATENCY_KEYS = ("stt", "llm", "tts", "search")
COST_KEYS = ("stt", "llm", "tts", "search", "telephony")


def split_log(lines: list[dict]) -> tuple[list[dict], dict[str, list[dict]]]:
    calls = [x for x in lines if x["type"] == "call"]
    turns: dict[str, list[dict]] = {}
    for x in lines:
        if x["type"] == "turn":
            turns.setdefault(x["call_id"], []).append(x)
    return calls, turns


def turn_latency_ms(t: dict) -> float:
    return sum(t[f"{k}_ms"] for k in LATENCY_KEYS)


def turn_cost(t: dict):
    return total_or_none(t["cost"]) if t.get("cost") else None


def _avg(values: list):
    return None if not values or any(v is None for v in values) else sum(values) / len(values)


def _sum(values: list):
    return None if any(v is None for v in values) else sum(values)


def call_list(lines, status=None, from_=None, to=None, limit=50, offset=0) -> list[dict]:
    calls, turns = split_log(lines)
    out = []
    for c in calls:
        if status and c["status"] != status:
            continue
        if from_ and c["started_at"] < from_:
            continue
        if to and c["started_at"] > to:
            continue
        out.append({"call_id": c["call_id"], "started_at": c["started_at"],
                    "duration_seconds": c["duration_seconds"], "status": c["status"],
                    "total_cost": c["total_cost"], "turns_count": len(turns.get(c["call_id"], []))})
    return out[offset: offset + limit]


def call_detail(lines, call_id: str) -> dict | None:
    calls, turns = split_log(lines)
    c = next((x for x in calls if x["call_id"] == call_id), None)
    if c is None:
        return None
    return {
        "call_id": c["call_id"], "started_at": c["started_at"], "ended_at": c["ended_at"],
        "duration_seconds": c["duration_seconds"], "status": c["status"],
        "total_cost": c["total_cost"], "cost_breakdown": c["cost_breakdown"],
        "turns": [{"turn_id": t["turn_id"],
                   "latency_ms_by_component": {k: t[f"{k}_ms"] for k in LATENCY_KEYS},
                   "classification": t["classification"], "had_search": t["search_calls"] > 0,
                   "error": t["error"]} for t in turns.get(call_id, [])],
    }


def summary(lines, from_=None, to=None) -> dict:
    calls, turns = split_log(lines)
    calls = [c for c in calls if (not from_ or c["started_at"] >= from_) and (not to or c["started_at"] <= to)]
    all_turns = [t for c in calls for t in turns.get(c["call_id"], [])]
    totals = [c["total_cost"] for c in calls]
    minutes = sum(c["duration_seconds"] for c in calls) / 60
    total_cost = _sum(totals) if calls else None

    def group(has_search: bool) -> dict:
        ts = [t for t in all_turns if (t["search_calls"] > 0) == has_search]
        return {"avg_latency_ms": statistics.mean(map(turn_latency_ms, ts)) if ts else None,
                "avg_cost": _avg([turn_cost(t) for t in ts])}

    return {
        "calls_count": len(calls),
        "total_minutes": minutes,
        "total_cost": total_cost,
        "avg_cost_per_minute": total_cost / minutes if total_cost is not None and minutes > 0 else None,
        "median_cost_per_call": statistics.median(totals) if calls and None not in totals else None,
        "cost_by_component": {k: _sum([c["cost_breakdown"].get(k) for c in calls]) if calls else None
                              for k in COST_KEYS},
        # Contract text is ambiguous here; interpreted as one entry per group (see decisions.md D-008).
        "search_vs_no_search": {"search": group(True), "no_search": group(False)},
    }
