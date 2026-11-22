"""Generate FICTITIOUS sample log + dashboard mock data (T-09).

Run: python3 -m scripts.make_mock_data
All numbers are synthetic (seeded random) and all prices below are fictional test prices,
not vendor prices. Output must match docs/api-contracts.md; regenerate on any contract change.
"""
from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.costs import CostCalculator, total_or_none
from core.reporting import call_detail, call_list, summary

OUT = Path(__file__).resolve().parent.parent / "admin" / "mock-data"
NAMES = {k: "fictional" for k in ("stt", "llm", "tts", "search", "telephony")}
FICTIONAL_PRICES = {
    "stt": {"fictional": {"per_minute": 0.010}},
    "llm": {"fictional": {"input_per_1m_tokens": 1.0, "output_per_1m_tokens": 4.0}},
    "tts": {"fictional": {"per_1k_chars": 0.020}},
    "search": {"fictional": {"per_call": 0.005}},
    "telephony": {"fictional": {"per_minute": 0.008}},
}


def generate_log(n_calls: int = 12, seed: int = 7) -> list[dict]:
    rnd = random.Random(seed)
    costs = CostCalculator(FICTIONAL_PRICES, NAMES)
    base = datetime(2026, 11, 20, 8, 0, tzinfo=timezone.utc)
    lines: list[dict] = []
    for i in range(n_calls):
        call_id = f"mock{i + 1:04d}"
        start = base + timedelta(hours=7 * i)
        limit_call = i == 5  # one call that hit the duration cap
        turns, elapsed = [], 0.0
        for turn_id in range(1, rnd.randint(3, 8) + 1):
            searched = rnd.random() < 0.35
            t = {"type": "turn", "call_id": call_id, "turn_id": turn_id,
                 "stt_ms": rnd.uniform(250, 600), "llm_ms": rnd.uniform(600, 1500),
                 "tts_ms": rnd.uniform(200, 500), "search_ms": rnd.uniform(800, 2500) if searched else 0.0,
                 "input_tokens": rnd.randint(200, 900), "output_tokens": rnd.randint(40, 160),
                 "search_calls": 1 if searched else 0, "audio_seconds": rnd.uniform(2, 8),
                 "classification": "lookup" if searched else "chat", "error": None}
            t["tts_chars"] = t["output_tokens"] * 5
            t["cost"] = {"stt": costs.stt(t["audio_seconds"]), "llm": costs.llm(t["input_tokens"], t["output_tokens"]),
                         "tts": costs.tts(t["tts_chars"]), "search": costs.search(t["search_calls"])}
            for k in ("stt_ms", "llm_ms", "tts_ms", "search_ms"):
                t[k] = round(t[k])
            for k in ("audio_seconds",):
                t[k] = round(t[k], 2)
            elapsed += (t["stt_ms"] + t["llm_ms"] + t["tts_ms"] + t["search_ms"]) / 1000 + rnd.uniform(4, 9)
            turns.append(t)
        duration = 301.0 if limit_call else round(elapsed, 1)
        breakdown = {c: sum(t["cost"][c] for t in turns) for c in ("stt", "llm", "tts", "search")}
        breakdown["telephony"] = costs.telephony(duration)
        lines += turns
        lines.append({"type": "call", "call_id": call_id, "started_at": start.isoformat(),
                      "ended_at": (start + timedelta(seconds=duration)).isoformat(),
                      "status": "limit_exceeded:call_seconds" if limit_call else "completed",
                      "duration_seconds": duration, "cost_breakdown": breakdown,
                      "total_cost": total_or_none(breakdown)})
    return lines


def write_all(out: Path = OUT) -> None:
    lines = generate_log()
    (out / "calls").mkdir(parents=True, exist_ok=True)
    (out / "sample_log.jsonl").write_text(
        "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in lines), encoding="utf-8")

    def dump(path: Path, obj) -> None:
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    listing = call_list(lines, limit=1000)
    dump(out / "calls.json", listing)
    dump(out / "summary.json", summary(lines))
    for c in listing:
        dump(out / "calls" / f"{c['call_id']}.json", call_detail(lines, c["call_id"]))
    (out / "README.md").write_text(
        "# mock-data\n\nנתוני דמה פיקטיביים (נוצרו ב-`python3 -m scripts.make_mock_data`, זרע קבוע). "
        "המחירים והמספרים בדויים ואינם מחירי ספק. מתאימים ל-docs/api-contracts.md גרסה 0.1.\n\n"
        "- `calls.json` = GET /calls\n- `calls/<call_id>.json` = GET /calls/{call_id}\n"
        "- `summary.json` = GET /summary\n- `sample_log.jsonl` = לוג תורות לדוגמה (קלט ל-`scripts.cost_report`)\n",
        encoding="utf-8")


if __name__ == "__main__":
    write_all()
    print(f"wrote mock data to {OUT}")
