"""Simulated call loop: telephony -> STT -> LLM (+search tool) -> TTS -> telephony.

Privacy: records and log lines have no phone number and no conversation text, only ids,
timings, counts, costs and status (see CLAUDE.md and docs/api-contracts.md).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

from .costs import CostCalculator, total_or_none
from .limits import CallLimits, LimitExceeded
from .turnlog import TurnLog

SEARCH_TOOL = {"name": "search", "description": "Web search", "parameters": {"query": "string"}}
COMPONENTS = ("stt", "llm", "tts", "search", "telephony")


@dataclass
class TurnRecord:
    turn_id: int
    stt_ms: float = 0.0
    llm_ms: float = 0.0
    tts_ms: float = 0.0
    search_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    tts_chars: int = 0
    search_calls: int = 0
    audio_seconds: float | None = None
    classification: str = "chat"  # chat | lookup (draft values, see decisions.md)
    cost: dict = field(default_factory=dict)  # component -> float | None (None = unknown)
    error: str | None = None


@dataclass
class CallRecord:
    call_id: str
    status: str  # completed | limit_exceeded:<reason>
    turns: list[TurnRecord] = field(default_factory=list)
    duration_seconds: float = 0.0
    cost_breakdown: dict = field(default_factory=dict)
    total_cost: float | None = None


def answer_turn(messages: list[dict], llm, search, limits: CallLimits, t: TurnRecord) -> str:
    """LLM loop for one user message, running search tool calls. Updates t, returns answer text."""
    while True:
        res = llm.complete(messages, tools=[SEARCH_TOOL])
        t.llm_ms += res.latency_ms
        t.input_tokens += res.input_tokens
        t.output_tokens += res.output_tokens
        if not res.tool_calls:
            return res.text
        for call in res.tool_calls:
            limits.register_tool_call(is_search=call.name == "search")
            found = search.search(call.arguments["query"])
            t.search_calls += 1
            t.search_ms += found.latency_ms
            t.classification = "lookup"
            hit = found.hits[0]
            messages.append({"role": "tool", "content": hit.snippet,
                             "source": hit.source, "date": hit.date})


def _now() -> datetime:
    return datetime.now(timezone.utc)


def run_call(telephony, stt, llm, tts, search, limits: CallLimits,
             costs: CostCalculator | None = None, log: TurnLog | None = None,
             wall_clock=_now) -> CallRecord:
    started = wall_clock()
    call_id = telephony.accept_call()
    record = CallRecord(call_id=call_id, status="completed")
    messages: list[dict] = []
    turn_id = 0
    try:
        while (audio := telephony.receive_audio()) is not None:
            turn_id += 1
            limits.start_turn()
            heard = stt.transcribe(audio)
            messages.append({"role": "user", "content": heard.text})
            t = TurnRecord(turn_id, stt_ms=heard.latency_ms, audio_seconds=heard.audio_seconds)
            text = answer_turn(messages, llm, search, limits, t)
            messages.append({"role": "assistant", "content": text})
            spoken = tts.synthesize(text)
            t.tts_ms, t.tts_chars = spoken.latency_ms, spoken.chars
            telephony.send_audio(spoken.audio)
            if costs:
                t.cost = {"stt": costs.stt(t.audio_seconds), "llm": costs.llm(t.input_tokens, t.output_tokens),
                          "tts": costs.tts(t.tts_chars), "search": costs.search(t.search_calls)}
            record.turns.append(t)
            if log:
                log.write({"type": "turn", "call_id": call_id, **asdict(t)})
    except LimitExceeded as e:
        record.status = f"limit_exceeded:{e.reason}"
    finally:
        telephony.hangup()
    record.duration_seconds = limits.elapsed()
    if costs:
        parts = {c: total_or_none({"t": x.cost.get(c) for x in record.turns}) if record.turns else 0.0
                 for c in ("stt", "llm", "tts", "search")}
        parts["telephony"] = costs.telephony(record.duration_seconds)
        record.cost_breakdown = parts
        record.total_cost = total_or_none(parts)
    if log:
        log.write({"type": "call", "call_id": call_id, "started_at": started.isoformat(),
                   "ended_at": wall_clock().isoformat(), "status": record.status,
                   "duration_seconds": record.duration_seconds,
                   "cost_breakdown": record.cost_breakdown, "total_cost": record.total_cost})
    return record
