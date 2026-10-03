from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .agent_definition import build_serialized_space
from .config import (
    EVALUATIONS_PATH,
    INSTRUCTIONS_PATH,
    SAMPLE_QUESTIONS_PATH,
    SEMANTICS_PATH,
    SQL_EXAMPLES_PATH,
    SQL_EXPRESSIONS_PATH,
    SQL_FUNCTIONS_PATH,
    EnvironmentConfig,
    load_yaml,
)
from .evaluation import validate_evaluations
from .validation import (
    require_valid,
    validate_environment,
    validate_instructions,
    validate_principals,
    validate_sample_questions,
    validate_semantics,
    validate_serialized_space,
    validate_sql_examples_file,
    validate_sql_expressions_file,
    validate_sql_functions_file,
)


def validate_bundle_mapping(
    config: EnvironmentConfig, bundle_path: str | Path = "databricks.yml"
) -> list[str]:
    bundle = load_yaml(bundle_path)
    errors: list[str] = []
    if bundle.get("bundle", {}).get("engine") != "direct":
        errors.append("bundle.engine must be direct for resources.genie_spaces")
    target = bundle.get("targets", {}).get(config.environment)
    if not target:
        return errors + [f"bundle target is missing: {config.environment}"]
    expected = {
        "warehouse_id": config.raw.get("warehouse_id"),
        "agent_title": config.raw.get("agent", {}).get("display_name"),
        "agent_description": config.raw.get("agent", {}).get("description"),
        "parent_path": config.raw.get("agent", {}).get("parent_path"),
    }
    variables = target.get("variables", {})
    for key, value in expected.items():
        if variables.get(key) != value:
            errors.append(f"bundle target {config.environment} does not match config field {key}")
    if target.get("workspace", {}).get("host") != config.raw.get("workspace_host"):
        errors.append(f"bundle target {config.environment} workspace host does not match config")
    errors += validate_principals(config.raw.get("authorised_principals", []))
    if variables.get("agent_permissions") != config.raw.get("authorised_principals"):
        errors.append(
            f"bundle target {config.environment} agent_permissions do not match "
            "authorised_principals"
        )
    return errors


def validate_project(config: EnvironmentConfig, *, deployment: bool = False) -> list[str]:
    errors = validate_environment(config, deployment=deployment)
    errors += validate_semantics(SEMANTICS_PATH, deployment=deployment)
    errors += validate_sql_expressions_file(SQL_EXPRESSIONS_PATH, deployment=deployment)
    errors += validate_sql_examples_file(SQL_EXAMPLES_PATH, deployment=deployment)
    errors += validate_sql_functions_file(SQL_FUNCTIONS_PATH)
    errors += validate_sample_questions(SAMPLE_QUESTIONS_PATH, deployment=deployment)
    errors += validate_instructions(INSTRUCTIONS_PATH)
    errors += validate_evaluations(
        EVALUATIONS_PATH,
        deployment=deployment,
        production=deployment and config.environment == "prod",
    )
    errors += validate_bundle_mapping(config)
    semantics = load_yaml(SEMANTICS_PATH)
    configured_sources = set(config.table_fqns())
    referenced_sources = {column.get("table") for column in semantics.get("columns", [])}
    for join in semantics.get("joins", []):
        referenced_sources.update((join.get("left_table"), join.get("right_table")))
    for source in sorted(referenced_sources - configured_sources - {None}):
        errors.append(f"semantic configuration references an unconfigured source: {source}")
    if not errors:
        errors += validate_serialized_space(build_serialized_space(config))
    return errors


def write_bundle_artifact(
    config: EnvironmentConfig,
    *,
    output: str | Path | None = None,
    deployment: bool = False,
) -> dict[str, Any]:
    require_valid(validate_project(config, deployment=deployment))
    payload = build_serialized_space(config)
    target = Path(output) if output else config.generated_agent_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return {
        "environment": config.environment,
        "output": str(target),
        "data_sources": sum(len(values) for values in payload["data_sources"].values()),
        "tables": len(payload["data_sources"].get("tables", [])),
        "metric_views": len(payload["data_sources"].get("metric_views", [])),
        "examples": len(payload.get("instructions", {}).get("example_question_sqls", [])),
        "benchmarks": len(payload.get("benchmarks", {}).get("questions", [])),
    }
