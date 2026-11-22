"""Provider interfaces. Every external service sits behind one of these (see CLAUDE.md)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class STTResult:
    text: str
    confidence: float
    latency_ms: float
    audio_seconds: float | None = None  # needed for per-minute STT pricing


@dataclass
class TTSResult:
    audio: bytes
    chars: int
    latency_ms: float


@dataclass
class ToolCall:
    name: str
    arguments: dict


@dataclass
class LLMResult:
    text: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    tool_calls: list[ToolCall] = field(default_factory=list)


@dataclass
class SearchHit:
    title: str
    snippet: str
    source: str  # URL or site name. Required: every factual answer needs a source.
    date: str | None  # ISO date of the page, if known


@dataclass
class SearchResponse:
    hits: list[SearchHit]
    latency_ms: float


class STTProvider(ABC):
    @abstractmethod
    def transcribe(self, audio: bytes) -> STTResult: ...


class TTSProvider(ABC):
    @abstractmethod
    def synthesize(self, text: str) -> TTSResult: ...


class LLMProvider(ABC):
    @abstractmethod
    def complete(self, messages: list[dict], tools: list[dict] | None = None) -> LLMResult: ...


class SearchProvider(ABC):
    @abstractmethod
    def search(self, query: str) -> SearchResponse: ...


class TelephonyProvider(ABC):
    """One call session. receive_audio returns None when the caller hung up."""

    @abstractmethod
    def accept_call(self) -> str: ...  # returns an opaque call_id (never a phone number)

    @abstractmethod
    def receive_audio(self) -> bytes | None: ...

    @abstractmethod
    def send_audio(self, audio: bytes) -> None: ...

    @abstractmethod
    def hangup(self) -> None: ...
