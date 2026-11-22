"""Mock providers: no keys, no network. In the mock world, 'audio' is just UTF-8 text bytes."""
from __future__ import annotations

import uuid

from .base import (
    LLMProvider, LLMResult, SearchHit, SearchProvider, SearchResponse, STTProvider,
    STTResult, TelephonyProvider, ToolCall, TTSProvider, TTSResult,
)

# Words that make the mock LLM ask for a web search (price / phone / opening hours).
SEARCH_TRIGGERS = ("מחיר", "כמה עולה", "טלפון", "שעות פתיחה")


class MockSTT(STTProvider):
    def transcribe(self, audio: bytes) -> STTResult:
        return STTResult(text=audio.decode("utf-8"), confidence=1.0, latency_ms=1.0)


class MockTTS(TTSProvider):
    def synthesize(self, text: str) -> TTSResult:
        return TTSResult(audio=text.encode("utf-8"), chars=len(text), latency_ms=1.0)


class MockSearch(SearchProvider):
    def search(self, query: str) -> SearchResponse:
        hit = SearchHit(
            title="תוצאת דמה",
            snippet=f"מידע לדוגמה עבור: {query}",
            source="https://example.invalid/mock",
            date="2026-11-22",
        )
        return SearchResponse(hits=[hit], latency_ms=1.0)


class MockLLM(LLMProvider):
    """Deterministic: asks for a search once if the user's last message looks like a lookup."""

    def complete(self, messages: list[dict], tools: list[dict] | None = None) -> LLMResult:
        last = messages[-1]
        in_tokens = sum(len(m["content"].split()) for m in messages)
        if last["role"] == "tool":
            text = f"לפי {last['source']} ({last['date']}): {last['content']}"
            return LLMResult(text, in_tokens, len(text.split()), 1.0)
        if tools and any(t in last["content"] for t in SEARCH_TRIGGERS):
            call = ToolCall("search", {"query": last["content"]})
            return LLMResult("", in_tokens, 5, 1.0, tool_calls=[call])
        text = "תשובת דמה: " + last["content"]
        return LLMResult(text, in_tokens, len(text.split()), 1.0)


class MockTelephony(TelephonyProvider):
    def __init__(self, utterances: list[str] | None = None):
        self._queue = [u.encode("utf-8") for u in (utterances or [])]
        self.sent: list[bytes] = []
        self.hung_up = False

    def accept_call(self) -> str:
        return uuid.uuid4().hex[:12]

    def receive_audio(self) -> bytes | None:
        return self._queue.pop(0) if self._queue else None

    def send_audio(self, audio: bytes) -> None:
        self.sent.append(audio)

    def hangup(self) -> None:
        self.hung_up = True
