"""Pick a provider per component from config/providers.yaml. Swapping = editing config only."""
from __future__ import annotations

from pathlib import Path

from core.config import load_providers

from .mock import MockLLM, MockSearch, MockSTT, MockTelephony, MockTTS

# Real providers get registered here when implemented (T-06, T-13, T-14...).
REGISTRY: dict[str, dict[str, type]] = {
    "stt": {"mock": MockSTT},
    "tts": {"mock": MockTTS},
    "llm": {"mock": MockLLM},
    "search": {"mock": MockSearch},
    "telephony": {"mock": MockTelephony},
}


def get_provider(kind: str, config_dir: Path | None = None, name: str | None = None, **kwargs):
    if kind not in REGISTRY:
        raise ValueError(f"unknown provider kind: {kind}")
    name = name or load_providers(config_dir).get(kind)
    if name is None:
        raise ValueError(f"providers.yaml has no entry for '{kind}'")
    impls = REGISTRY[kind]
    if name not in impls:
        raise ValueError(
            f"provider '{name}' for '{kind}' is not implemented yet (available: {sorted(impls)})"
        )
    return impls[name](**kwargs)
