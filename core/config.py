"""Config loading: YAML files under config/. Secrets come only from environment (.env)."""
from __future__ import annotations

import os
from pathlib import Path

import yaml

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def load_yaml(name: str, config_dir: Path | None = None) -> dict:
    path = (config_dir or CONFIG_DIR) / name
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_providers(config_dir: Path | None = None) -> dict:
    return load_yaml("providers.yaml", config_dir)


def load_limits(config_dir: Path | None = None) -> dict:
    return load_yaml("limits.yaml", config_dir)


def load_pricing(config_dir: Path | None = None) -> dict:
    return load_yaml("pricing.yaml", config_dir)


def env(name: str, default: str | None = None) -> str | None:
    """Read a secret/setting from the environment. Never hardcode values."""
    return os.environ.get(name, default)
