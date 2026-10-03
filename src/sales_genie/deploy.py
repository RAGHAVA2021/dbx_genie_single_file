from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from .agent_definition import build_serialized_space
from .bundle import validate_project
from .client import GenieClient, make_agent_body
from .config import EnvironmentConfig
from .validation import require_valid


def save_state(config: EnvironmentConfig, agent_id: str) -> None:
    config.state_path.parent.mkdir(parents=True, exist_ok=True)
    config.state_path.write_text(yaml.safe_dump({"environment": config.environment, "agent_id": agent_id}), encoding="utf-8")


def export_backup(
    client: GenieClient, config: EnvironmentConfig, response: dict[str, Any] | None = None
) -> Path:
    if not config.agent_id:
        raise ValueError("Cannot back up an Agent without an Agent ID")
    result = response or client.get_agent(config.agent_id, include_serialized=True)
    target = Path("backups") / f"{config.environment}-{config.agent_id}-{datetime.now(UTC):%Y%m%dT%H%M%SZ}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return target


def deploy(
    config: EnvironmentConfig, *, dry_run: bool, approved: bool = False, tests_passed: bool = False
) -> dict[str, Any]:
    if config.environment == "prod" and not (dry_run or approved):
        raise PermissionError("Production deployment requires --approve-prod")
    require_valid(validate_project(config, deployment=not dry_run))
    if config.environment == "prod" and not (dry_run or tests_passed):
        raise RuntimeError("Production deployment requires a successful local test run")
    serialized = build_serialized_space(config)
    body = make_agent_body(config, serialized)
    action = "update" if config.agent_id else "create"
    if dry_run:
        return {"dry_run": True, "action": action, "agent_id": config.agent_id, "body": body}
    client = GenieClient(config.raw["cli_profile"])
    backup = None
    if config.agent_id:
        current = client.get_agent(config.agent_id, include_serialized=True)
        backup = str(export_backup(client, config, current))
        result = client.update_agent(config.agent_id, body, etag=current.get("etag"))
    else:
        result = client.create_agent(body)
        agent_id = result.get("space_id") or result.get("id")
        if not agent_id:
            raise RuntimeError("Create response did not contain an Agent ID")
        save_state(config, agent_id)
    return {"action": action, "backup": backup, "result": result}
