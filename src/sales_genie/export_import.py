from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from .client import GenieClient, make_agent_body
from .config import EnvironmentConfig, contains_placeholder
from .deploy import save_state
from .validation import (
    ConfigurationError,
    require_valid,
    validate_environment,
    validate_serialized_space,
    validate_sql_examples,
    validate_sql_fragments,
)


def _replace_identifiers(value: Any, replacements: dict[str, str]) -> Any:
    """Replace complete three-part identifiers without rewriting arbitrary catalog text."""
    if isinstance(value, str):
        for source, target in replacements.items():
            value = value.replace(source, target)
        return value
    if isinstance(value, list):
        return [_replace_identifiers(item, replacements) for item in value]
    if isinstance(value, dict):
        return {key: _replace_identifiers(item, replacements) for key, item in value.items()}
    return value


def remap_import_sources(
    payload: dict[str, Any], config: EnvironmentConfig
) -> tuple[dict[str, Any], dict[str, str]]:
    """Enforce the catalog-only promotion contract and return a remapped copy."""
    expected_groups = config.data_source_fqns()
    expected_by_suffix: dict[tuple[str, str], tuple[str, str]] = {}
    for collection, sources in expected_groups.items():
        for logical_name, identifier in sources.items():
            parts = identifier.split(".", 2)
            if len(parts) != 3:
                raise ConfigurationError(f"invalid target source identifier: {identifier}")
            key = (parts[1], parts[2])
            if key in expected_by_suffix:
                raise ConfigurationError(
                    f"target sources are ambiguous for schema and object: {parts[1]}.{parts[2]}"
                )
            expected_by_suffix[key] = (collection, identifier)

    identifier_remap: dict[str, str] = {}
    imported_suffixes: set[tuple[str, str]] = set()
    source_catalogs: set[str] = set()
    for collection in ("tables", "metric_views"):
        for source in payload.get("data_sources", {}).get(collection, []):
            identifier = source.get("identifier", "")
            parts = identifier.split(".", 2)
            if len(parts) != 3:
                raise ConfigurationError(f"invalid imported source identifier: {identifier}")
            suffix = (parts[1], parts[2])
            expected = expected_by_suffix.get(suffix)
            if not expected:
                raise ConfigurationError(
                    f"imported source is not configured for the target: {identifier}"
                )
            expected_collection, target_identifier = expected
            if collection != expected_collection:
                raise ConfigurationError(
                    f"imported source type does not match target configuration: {identifier}"
                )
            imported_suffixes.add(suffix)
            source_catalogs.add(parts[0])
            identifier_remap[identifier] = target_identifier

    missing = sorted(set(expected_by_suffix) - imported_suffixes)
    if missing:
        formatted = ", ".join(f"{schema}.{name}" for schema, name in missing)
        raise ConfigurationError(f"import is missing configured target sources: {formatted}")
    if len(source_catalogs) > 1:
        raise ConfigurationError("imported sources must all come from one source catalog")
    replacements = dict(identifier_remap)
    for source, target in identifier_remap.items():
        quoted_source = ".".join(f"`{part}`" for part in source.split(".", 2))
        quoted_target = ".".join(f"`{part}`" for part in target.split(".", 2))
        replacements[quoted_source] = quoted_target
    return _replace_identifiers(deepcopy(payload), replacements), identifier_remap


def export_agent(config: EnvironmentConfig, output: Path, agent_id: str | None = None) -> Path:
    agent_id = agent_id or config.agent_id
    if not agent_id:
        raise ValueError("Agent ID is required for export")
    response = GenieClient(config.raw["cli_profile"]).get_agent(agent_id, include_serialized=True)
    raw = response.get("serialized_space")
    parsed = json.loads(raw) if isinstance(raw, str) else raw
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(parsed, indent=2), encoding="utf-8")
    return output


def import_agent(
    config: EnvironmentConfig,
    source: Path,
    *,
    dry_run: bool,
    approved: bool = False,
    tests_passed: bool = False,
) -> dict[str, Any]:
    require_valid(validate_environment(config, deployment=not dry_run))
    if config.environment == "prod" and not (dry_run or approved):
        raise PermissionError("Production import requires --approve-prod")
    if config.environment == "prod" and not (dry_run or tests_passed):
        raise RuntimeError("Production import requires a successful local test run")
    parsed = json.loads(source.read_text(encoding="utf-8"))
    parsed, source_remap = remap_import_sources(parsed, config)
    errors = validate_serialized_space(parsed)
    if not dry_run and contains_placeholder(parsed):
        errors.append("imported serialized_space contains unresolved placeholders")
    example_sql = [
        sql
        for example in parsed.get("instructions", {}).get("example_question_sqls", [])
        for sql in example.get("sql", [])
    ]
    snippet_sql = [
        sql
        for values in parsed.get("instructions", {}).get("sql_snippets", {}).values()
        for snippet in values
        for sql in snippet.get("sql", [])
    ]
    benchmark_sql = [
        sql
        for question in parsed.get("benchmarks", {}).get("questions", [])
        for answer in question.get("answer", [])
        for sql in answer.get("content", [])
    ]
    errors += validate_sql_examples(example_sql + benchmark_sql)
    errors += validate_sql_fragments(snippet_sql)
    require_valid(errors)
    body = make_agent_body(config, parsed)
    if dry_run:
        return {"dry_run": True, "source_remap": source_remap, "body": body}
    result = GenieClient(config.raw["cli_profile"]).create_agent(body)
    agent_id = result.get("space_id") or result.get("id")
    if not agent_id:
        raise RuntimeError("Import response did not contain an Agent ID")
    save_state(config, agent_id)
    return result
