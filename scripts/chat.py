"""Hebrew text chat in the terminal with timing, tokens and cost per turn (T-06, mock-capable).

Run: python3 -m scripts.chat            (type a message, empty line or Ctrl-D to quit)
The LLM comes from config/providers.yaml. Only the mock exists so far; a real provider needs a
human decision (docs/STATUS.md) and a key in .env.
"""
from __future__ import annotations

import sys

from core.config import load_limits, load_pricing, load_providers
from core.conversation import TurnRecord, answer_turn
from core.costs import CostCalculator
from core.limits import CallLimits, LimitExceeded
from core.providers.registry import get_provider


def chat(lines, out=print) -> int:
    llm, search = get_provider("llm"), get_provider("search")
    costs = CostCalculator(load_pricing(), load_providers())
    limits, messages, n = CallLimits(load_limits()), [], 0
    for line in lines:
        if not line.strip():
            break
        n += 1
        t = TurnRecord(turn_id=n)
        messages.append({"role": "user", "content": line.strip()})
        try:
            limits.start_turn()
            text = answer_turn(messages, llm, search, limits, t)
        except LimitExceeded as e:
            out(f"[נעצר: חריגה מתקרה {e.reason}]")
            return 1
        messages.append({"role": "assistant", "content": text})
        c = costs.llm(t.input_tokens, t.output_tokens)
        out(text)
        out(f"  [{t.llm_ms + t.search_ms:.0f}ms | טוקנים {t.input_tokens}/{t.output_tokens} | "
            f"עלות {'לא ידועה' if c is None else f'{c:.5f}'}]")
    return 0


if __name__ == "__main__":
    sys.exit(chat(iter(lambda: sys.stdin.readline() if sys.stdin.readable() else "", None)))
