from __future__ import annotations

import json
import os
from datetime import timedelta
from typing import Any


class GenieClient:
    """Thin wrapper over the official SDK Genie API using SDK-managed authentication."""

    def __init__(self, profile: str):
        try:
            from databricks.sdk import WorkspaceClient
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("Install the project dependencies before workspace operations") from exc
        # Unified-auth environment variables take precedence in CI (for example github-oidc).
        # Named profiles remain mandatory for interactive/local workspace operations.
        self.workspace = (
            WorkspaceClient()
            if os.environ.get("DATABRICKS_AUTH_TYPE")
            else WorkspaceClient(profile=profile)
        )

    @property
    def genie(self) -> Any:
        return self.workspace.genie

    def get_agent(self, agent_id: str, *, include_serialized: bool = True) -> dict[str, Any]:
        return self.genie.get_space(
            agent_id, include_serialized_space=include_serialized
        ).as_dict()

    def create_agent(self, body: dict[str, Any]) -> dict[str, Any]:
        return self.genie.create_space(
            warehouse_id=body["warehouse_id"],
            serialized_space=body["serialized_space"],
            title=body.get("title"),
            description=body.get("description"),
            parent_path=body.get("parent_path"),
        ).as_dict()

    def update_agent(
        self, agent_id: str, body: dict[str, Any], *, etag: str | None = None
    ) -> dict[str, Any]:
        # parent_path is immutable once an Agent exists, so it is never sent on update.
        return self.genie.update_space(
            agent_id,
            warehouse_id=body.get("warehouse_id"),
            serialized_space=body.get("serialized_space"),
            title=body.get("title"),
            description=body.get("description"),
            etag=etag,
        ).as_dict()

    def get_attachment_query_result(
        self,
        agent_id: str,
        conversation_id: str,
        message_id: str,
        attachment_id: str,
    ) -> dict[str, Any]:
        return self.genie.get_message_attachment_query_result(
            agent_id, conversation_id, message_id, attachment_id
        ).as_dict()

    def query(self, agent_id: str, question: str, timeout_seconds: int = 600) -> dict[str, Any]:
        return self.genie.start_conversation_and_wait(
            agent_id, question, timeout=timedelta(seconds=timeout_seconds)
        ).as_dict()

    def follow_up(
        self,
        agent_id: str,
        conversation_id: str,
        question: str,
        timeout_seconds: int = 600,
    ) -> dict[str, Any]:
        return self.genie.create_message_and_wait(
            agent_id, conversation_id, question, timeout=timedelta(seconds=timeout_seconds)
        ).as_dict()


def make_agent_body(config: Any, serialized_space: dict[str, Any]) -> dict[str, Any]:
    return {
        "warehouse_id": config.raw["warehouse_id"],
        "title": config.raw["agent"]["display_name"],
        "description": config.raw["agent"]["description"],
        "parent_path": config.raw["agent"]["parent_path"],
        "serialized_space": json.dumps(serialized_space, separators=(",", ":")),
    }
