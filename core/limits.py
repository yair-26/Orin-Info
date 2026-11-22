"""Enforcement of config/limits.yaml. Exceeding a cap stops the call (T-03)."""
from __future__ import annotations

import time
from typing import Callable


class LimitExceeded(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason  # one of: call_seconds, tool_calls, search_calls_per_turn


class CallLimits:
    def __init__(self, cfg: dict, clock: Callable[[], float] = time.monotonic):
        self.max_call_seconds = cfg["max_call_seconds"]
        self.max_tool_calls = cfg["max_tool_calls_per_call"]
        self.max_search_per_turn = cfg["max_search_calls_per_turn"]
        self._clock = clock
        self._start = clock()
        self.tool_calls = 0
        self.search_this_turn = 0

    def elapsed(self) -> float:
        return self._clock() - self._start

    def start_turn(self) -> None:
        self.search_this_turn = 0
        if self._clock() - self._start > self.max_call_seconds:
            raise LimitExceeded("call_seconds")

    def register_tool_call(self, is_search: bool) -> None:
        self.tool_calls += 1
        if self.tool_calls > self.max_tool_calls:
            raise LimitExceeded("tool_calls")
        if is_search:
            self.search_this_turn += 1
            if self.search_this_turn > self.max_search_per_turn:
                raise LimitExceeded("search_calls_per_turn")
