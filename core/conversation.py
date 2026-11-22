"""Simulated call loop: telephony -> STT -> LLM (+search tool) -> TTS -> telephony.

Privacy: the returned record has no phone number and no conversation text, only ids,
timings, counts and status (see CLAUDE.md and docs/api-contracts.md).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .limits import CallLimits, LimitExceeded

SEARCH_TOOL = {"name": "search", "description": "Web search", "parameters": {"query": "string"}}


@dataclass
class TurnRecord:
    turn_id: int
    stt_ms: float
    llm_ms: float
    tts_ms: float
    search_ms: float
    input_tokens: int
    output_tokens: int
    tts_chars: int
    search_calls: int
    error: str | None = None


@dataclass
class CallRecord:
    call_id: str
    status: str  # completed | limit_exceeded:<reason>
    turns: list[TurnRecord] = field(default_factory=list)


def run_call(telephony, stt, llm, tts, search, limits: CallLimits) -> CallRecord:
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
            t = TurnRecord(turn_id, heard.latency_ms, 0, 0, 0, 0, 0, 0, 0)
            while True:
                res = llm.complete(messages, tools=[SEARCH_TOOL])
                t.llm_ms += res.latency_ms
                t.input_tokens += res.input_tokens
                t.output_tokens += res.output_tokens
                if not res.tool_calls:
                    break
                for call in res.tool_calls:
                    limits.register_tool_call(is_search=call.name == "search")
                    found = search.search(call.arguments["query"])
                    t.search_calls += 1
                    t.search_ms += found.latency_ms
                    hit = found.hits[0]
                    messages.append({"role": "tool", "content": hit.snippet,
                                     "source": hit.source, "date": hit.date})
            messages.append({"role": "assistant", "content": res.text})
            spoken = tts.synthesize(res.text)
            t.tts_ms, t.tts_chars = spoken.latency_ms, spoken.chars
            telephony.send_audio(spoken.audio)
            record.turns.append(t)
    except LimitExceeded as e:
        record.status = f"limit_exceeded:{e.reason}"
    finally:
        telephony.hangup()
    return record
