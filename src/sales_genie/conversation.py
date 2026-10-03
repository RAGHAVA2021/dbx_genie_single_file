from __future__ import annotations

from .client import GenieClient
from .config import EnvironmentConfig


def ask(config: EnvironmentConfig, question: str, timeout_seconds: int = 600) -> dict:
    if not config.agent_id:
        raise ValueError("Agent ID is required for queries")
    return GenieClient(config.raw["cli_profile"]).query(config.agent_id, question, timeout_seconds)
