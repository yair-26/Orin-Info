"""Cost calculation from config/pricing.yaml (T-05).

A missing/null price gives cost None ("unknown"), never 0. Prices are never invented.
Currency/unit is whatever pricing.yaml uses (document it there when filling real prices).
"""
from __future__ import annotations


def _num(x):
    return x if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def _mul(amount, price, divisor):
    if amount is None or _num(price) is None:
        return None
    return amount / divisor * price


class CostCalculator:
    def __init__(self, pricing: dict | None, names: dict[str, str]):
        """names: component -> pricing key, e.g. {"llm": "openai/gpt-x", "stt": "vendor"}."""
        self.pricing = pricing or {}
        self.names = names

    def _entry(self, kind: str) -> dict:
        return (self.pricing.get(kind) or {}).get(self.names.get(kind)) or {}

    def stt(self, audio_seconds):
        return _mul(audio_seconds, self._entry("stt").get("per_minute"), 60)

    def llm(self, input_tokens: int, output_tokens: int):
        e = self._entry("llm")
        a = _mul(input_tokens, e.get("input_per_1m_tokens"), 1_000_000)
        b = _mul(output_tokens, e.get("output_per_1m_tokens"), 1_000_000)
        return None if a is None or b is None else a + b

    def tts(self, chars: int):
        return _mul(chars, self._entry("tts").get("per_1k_chars"), 1000)

    def search(self, calls: int):
        return _mul(calls, self._entry("search").get("per_call"), 1)

    def telephony(self, call_seconds):
        return _mul(call_seconds, self._entry("telephony").get("per_minute"), 60)


def total_or_none(parts: dict) -> float | None:
    """Sum of components; None if any component is unknown (so unknown is never shown as 0)."""
    values = list(parts.values())
    return None if any(v is None for v in values) else sum(values)
