from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from .bundle import validate_project, write_bundle_artifact
from .client import GenieClient
from .config import (
    DEV_CONFIG_PATH,
    PROD_CONFIG_PATH,
    SEMANTICS_PATH,
    load_environment,
    load_yaml,
)
from .conversation import ask
from .deploy import deploy
from .export_import import export_agent, import_agent
from .validation import (
    require_valid,
    scan_secrets,
    validate_pair,
    validate_sql_examples,
)


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="sales-genie")
    commands = root.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate-config")
    validate.add_argument("--config", default=str(DEV_CONFIG_PATH))
    validate.add_argument("--deployment", action="store_true")
    generate = commands.add_parser("generate-bundle")
    generate.add_argument("--config", required=True)
    generate.add_argument("--output")
    generate.add_argument("--deployment", action="store_true")
    for name in ("deploy-dev", "deploy-prod"):
        item = commands.add_parser(name)
        item.add_argument("--config")
        item.add_argument("--dry-run", action="store_true")
        item.add_argument("--approve-prod", action="store_true")
    for name in ("get-agent", "export-agent", "query-agent", "run-smoke-tests"):
        item = commands.add_parser(name)
        item.add_argument("--config", required=True)
        item.add_argument("--agent-id")
        if name == "export-agent":
            item.add_argument("--output", required=True)
        if name == "query-agent":
            item.add_argument("--question", required=True)
    follow_up = commands.add_parser("query-follow-up")
    follow_up.add_argument("--config", required=True)
    follow_up.add_argument("--agent-id")
    follow_up.add_argument("--conversation-id", required=True)
    follow_up.add_argument("--question", required=True)
    result = commands.add_parser("get-query-result")
    result.add_argument("--config", required=True)
    result.add_argument("--agent-id")
    result.add_argument("--conversation-id", required=True)
    result.add_argument("--message-id", required=True)
    result.add_argument("--attachment-id", required=True)
    imp = commands.add_parser("import-agent")
    imp.add_argument("--config", required=True)
    imp.add_argument("--input", required=True)
    imp.add_argument("--dry-run", action="store_true")
    imp.add_argument("--approve-prod", action="store_true")
    commands.add_parser("compare-dev-prod")
    return root


def smoke(config, agent_id: str | None = None):
    require_valid(validate_project(config, deployment=True))
    agent_id = agent_id or config.agent_id
    if not agent_id:
        raise ValueError("Agent ID is required; pass --agent-id or record it in environment state")
    client = GenieClient(config.raw["cli_profile"])
    warehouse = client.workspace.warehouses.get(id=config.raw["warehouse_id"])
    tables = [client.workspace.tables.get(full_name=fqn) for fqn in config.table_fqns().values()]
    expected_columns: dict[str, set[str]] = {}
    for column in load_yaml(SEMANTICS_PATH).get("columns", []):
        expected_columns.setdefault(column["table"], set()).add(column["physical_column"])
    for logical_name, table in zip(config.table_fqns(), tables, strict=True):
        actual = {column.name for column in (table.columns or [])}
        missing = expected_columns.get(logical_name, set()) - actual
        if missing:
            raise RuntimeError(f"{logical_name} is missing required columns: {sorted(missing)}")
    agent = client.get_agent(agent_id)
    conversation = client.query(
        agent_id, "What were total sales yesterday?", timeout_seconds=600
    )
    if conversation.get("status") != "COMPLETED":
        raise RuntimeError(f"smoke conversation ended with {conversation.get('status')}")
    generated_sql = [
        attachment.get("query", {}).get("query", "")
        for attachment in conversation.get("attachments", [])
        if attachment.get("query", {}).get("query")
    ]
    require_valid(validate_sql_examples(generated_sql))
    return {
        "authentication": "ok", "warehouse": warehouse.as_dict(),
        "tables": [table.as_dict() for table in tables], "agent": agent,
        "conversation": {
            "status": conversation.get("status"),
            "conversation_id": conversation.get("conversation_id"),
            "message_id": conversation.get("id") or conversation.get("message_id"),
            "attachment_count": len(conversation.get("attachments", [])),
            "generated_sql": generated_sql,
        },
    }


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "validate-config":
        cfg = load_environment(args.config)
        errors = validate_project(cfg, deployment=args.deployment)
        errors += [f"possible secret in {path}" for path in scan_secrets(".")]
        require_valid(errors)
        print("Local configuration validation passed.")
        return 0
    if args.command == "generate-bundle":
        cfg = load_environment(args.config)
        result = write_bundle_artifact(
            cfg, output=args.output, deployment=args.deployment
        )
        print(json.dumps(result, indent=2))
        return 0
    if args.command in {"deploy-dev", "deploy-prod"}:
        expected = args.command.removeprefix("deploy-")
        default_path = DEV_CONFIG_PATH if expected == "dev" else PROD_CONFIG_PATH
        cfg = load_environment(args.config or default_path)
        if cfg.environment != expected:
            raise ValueError(f"{args.command} cannot use a {cfg.environment} configuration")
        tests_passed = False
        if expected == "prod" and not args.dry_run:
            subprocess.run([sys.executable, "-m", "pytest", "-q"], check=True)
            tests_passed = True
        print(json.dumps(deploy(
            cfg, dry_run=args.dry_run, approved=args.approve_prod, tests_passed=tests_passed
        ), indent=2))
        return 0
    if args.command == "compare-dev-prod":
        require_valid(validate_pair(load_environment(DEV_CONFIG_PATH), load_environment(PROD_CONFIG_PATH)))
        print("Development and production separation checks passed.")
        return 0
    cfg = load_environment(args.config)
    if args.command == "get-agent":
        agent_id = args.agent_id or cfg.agent_id
        if not agent_id:
            raise ValueError("Agent ID is required")
        result = GenieClient(cfg.raw["cli_profile"]).get_agent(agent_id)
    elif args.command == "export-agent":
        result = {"output": str(export_agent(cfg, Path(args.output), args.agent_id))}
    elif args.command == "import-agent":
        tests_passed = False
        if cfg.environment == "prod" and not args.dry_run:
            subprocess.run([sys.executable, "-m", "pytest", "-q"], check=True)
            tests_passed = True
        result = import_agent(
            cfg,
            Path(args.input),
            dry_run=args.dry_run,
            approved=args.approve_prod,
            tests_passed=tests_passed,
        )
    elif args.command == "query-agent":
        if args.agent_id:
            result = GenieClient(cfg.raw["cli_profile"]).query(args.agent_id, args.question)
        else:
            result = ask(cfg, args.question)
    elif args.command == "query-follow-up":
        agent_id = args.agent_id or cfg.agent_id
        if not agent_id:
            raise ValueError("Agent ID is required")
        result = GenieClient(cfg.raw["cli_profile"]).follow_up(
            agent_id, args.conversation_id, args.question
        )
    elif args.command == "get-query-result":
        agent_id = args.agent_id or cfg.agent_id
        if not agent_id:
            raise ValueError("Agent ID is required")
        result = GenieClient(cfg.raw["cli_profile"]).get_attachment_query_result(
            agent_id,
            args.conversation_id,
            args.message_id,
            args.attachment_id,
        )
    else:
        result = smoke(cfg, args.agent_id)
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
