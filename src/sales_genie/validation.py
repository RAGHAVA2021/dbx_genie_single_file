from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable

from .config import (
    MAX_DATA_SOURCES,
    EnvironmentConfig,
    contains_placeholder,
    load_table_contract,
    load_yaml,
    required_table_keys,
    table_keys,
)

FQN_RE = re.compile(r"^[^.\s]+\.[^.\s]+\.[^.\s]+$")
SECRET_PATTERNS = (
    re.compile(r"dapi[a-zA-Z0-9]{20,}"),
    re.compile(r"(?i)(token|password|client_secret)\s*[:=]\s*['\"]?(?!<)[^\s'\"]{8,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)
WRITE_SQL = re.compile(
    r"(?is)^\s*(?:CREATE|ALTER|DROP|INSERT|UPDATE|DELETE|MERGE|COPY|TRUNCATE|GRANT|REVOKE)\b"
)
READ_SQL = re.compile(r"(?is)^\s*(?:SELECT|WITH)\b")
ID_RE = re.compile(r"^[0-9a-f]{32}$")
SQL_COMMENT_RE = re.compile(r"(?s)/\*.*?\*/|--[^\n]*")
BARE_QUOTED_COLUMN_RE = re.compile(r"(?<![.\w])`[^`]+`")
AGGREGATION_RE = re.compile(r"(?i)\b(?:SUM|AVG|COUNT|MIN|MAX|MEASURE)\s*\(")
AGENT_PERMISSION_LEVELS = frozenset({"CAN_RUN", "CAN_EDIT", "CAN_MANAGE", "CAN_VIEW"})
PRINCIPAL_KEYS = ("group_name", "user_name", "service_principal_name")
CANONICAL_HEADINGS = (
    "## PURPOSE",
    "## DISAMBIGUATION",
    "## DATA QUALITY NOTES",
    "## CONSTRAINTS",
    "## Instructions you must follow when providing summaries",
)


class ConfigurationError(ValueError):
    pass


def validate_environment(config: EnvironmentConfig, *, deployment: bool = False) -> list[str]:
    errors: list[str] = []
    raw = config.raw
    required = (
        "environment", "workspace_host", "cli_profile", "warehouse_id", "catalog_name",
        "schema_name", "tables", "agent", "deployment_identity", "authorised_principals",
    )
    for field in required:
        if raw.get(field) in (None, "", [], {}):
            errors.append(f"missing required field: {field}")
    if raw.get("environment") not in {"dev", "prod"}:
        errors.append("environment must be dev or prod")
    if config.path.stem in {"dev", "prod"} and raw.get("environment") != config.path.stem:
        errors.append("configuration filename and environment do not match")
    for key in required_table_keys():
        if not raw.get("tables", {}).get(key):
            errors.append(f"missing required source: {key}")
    for key in sorted(set(raw.get("tables", {})) - set(table_keys())):
        errors.append(f"source is not declared in the logical source contract: {key}")
    contract = load_table_contract()
    for key, spec in contract.items():
        if spec.get("source_type", "table") not in {"table", "metric_view"}:
            errors.append(f"source {key} has invalid source_type; expected table or metric_view")
    fqns = list(config.table_fqns().values())
    if len(fqns) != len(set(fqns)):
        errors.append("duplicate fully qualified source definitions")
    for fqn in fqns:
        if not FQN_RE.fullmatch(fqn):
            errors.append(f"invalid fully qualified source name: {fqn}")
    if len(fqns) > MAX_DATA_SOURCES:
        errors.append(f"an Agent cannot contain more than {MAX_DATA_SOURCES} data sources")
    if deployment and contains_placeholder(raw):
        errors.append("unresolved placeholders are not allowed for deployment")
    if deployment and not raw.get("warehouse_id"):
        errors.append("warehouse_id is required for deployment")
    return errors


def validate_principals(principals: Any) -> list[str]:
    """Check authorised principals against the DAB resource-permission shape."""
    errors: list[str] = []
    if not isinstance(principals, list) or not principals:
        return ["authorised_principals must be a non-empty list of permission entries"]
    seen: list[tuple[str, str]] = []
    for index, entry in enumerate(principals):
        if not isinstance(entry, dict):
            errors.append(f"authorised principal {index} must be a mapping")
            continue
        if entry.get("level") not in AGENT_PERMISSION_LEVELS:
            errors.append(
                f"authorised principal {index} has an invalid level; "
                f"expected one of {', '.join(sorted(AGENT_PERMISSION_LEVELS))}"
            )
        named = [key for key in PRINCIPAL_KEYS if entry.get(key)]
        if len(named) != 1:
            errors.append(
                f"authorised principal {index} must name exactly one of "
                f"{', '.join(PRINCIPAL_KEYS)}"
            )
            continue
        if unknown := sorted(set(entry) - {"level", *PRINCIPAL_KEYS}):
            errors.append(
                f"authorised principal {index} has unsupported fields: {', '.join(unknown)}"
            )
        identity = (named[0], str(entry[named[0]]))
        if identity in seen:
            errors.append(f"authorised principal {index} is a duplicate of an earlier entry")
        seen.append(identity)
    return errors


def validate_semantics(path: str | Path, *, deployment: bool = False) -> list[str]:
    raw = load_yaml(path)
    errors: list[str] = []
    valid_relationships = {"many_to_one", "one_to_many", "one_to_one", "many_to_many"}
    columns = raw.get("columns", [])
    for index, column in enumerate(columns):
        required = {"table", "physical_column", "data_type", "description", "approval_status"}
        missing = sorted(key for key in required if not column.get(key))
        if missing:
            errors.append(f"column {index} missing: {', '.join(missing)}")
        if column.get("enable_entity_matching"):
            if str(column.get("data_type", "")).upper() not in {"STRING", "VARCHAR", "CHAR"}:
                errors.append(f"column {index} enables entity matching on a non-string type")
            if not column.get("enable_format_assistance"):
                errors.append(f"column {index} requires format assistance for entity matching")
            if column.get("protected_source"):
                errors.append(f"column {index} cannot use entity matching on a protected source")
        if deployment and column.get("approval_status") != "approved":
            errors.append(f"column {index} is not approved")
    for index, join in enumerate(raw.get("joins", [])):
        required = {
            "name", "left_table", "left_column", "right_table", "right_column",
            "relationship", "approval_status", "evidence",
        }
        missing = sorted(key for key in required if not join.get(key))
        if missing:
            errors.append(f"join {index} missing: {', '.join(missing)}")
        if join.get("relationship") not in valid_relationships:
            errors.append(f"join {index} has invalid relationship")
        if deployment and join.get("approval_status") != "approved":
            errors.append(f"join {index} is not approved")
    for index, measure in enumerate(raw.get("measures", [])):
        for field in ("aggregation_rule", "approval_status", "evidence"):
            if not measure.get(field):
                errors.append(f"measure {index} missing {field}")
        if deployment and measure.get("approval_status") != "approved":
            errors.append(f"measure {index} is not approved")
    decision = raw.get("metric_view_decision", {})
    if deployment and decision.get("approval_status") != "approved":
        errors.append("Metric View decision is not approved")
    if deployment and contains_placeholder(raw):
        errors.append("semantic configuration contains unresolved placeholders")
    return errors


def validate_sql_examples_file(path: str | Path, *, deployment: bool = False) -> list[str]:
    raw = load_yaml(path)
    errors: list[str] = []
    examples = raw.get("examples", [])
    if deployment and not examples:
        errors.append("at least one approved SQL example is required for deployment")
    names = [example.get("name") for example in examples]
    if len(names) != len(set(names)):
        errors.append("SQL example names must be unique")
    for index, example in enumerate(examples):
        for field in ("name", "question", "sql", "usage_guidance", "approval_status"):
            if not example.get(field):
                errors.append(f"SQL example {index} missing {field}")
        errors.extend(validate_sql_examples([example.get("sql", "")]))
        parameters = re.findall(r"(?<!:)\:([A-Za-z_][A-Za-z0-9_]*)", example.get("sql", ""))
        definitions = {item.get("name"): item for item in example.get("parameters", [])}
        for parameter in parameters:
            definition = definitions.get(parameter, {})
            missing = [
                key for key in ("type", "description", "default") if definition.get(key) in (None, "")
            ]
            if missing:
                errors.append(
                    f"SQL example {index} parameter {parameter} missing: {', '.join(missing)}"
                )
        if deployment and example.get("approval_status") != "approved":
            errors.append(f"SQL example {index} is not approved")
    if deployment and contains_placeholder(raw):
        errors.append("SQL examples contain unresolved placeholders")
    return errors


def validate_sql_expressions_file(path: str | Path, *, deployment: bool = False) -> list[str]:
    raw = load_yaml(path)
    errors: list[str] = []
    names: list[str] = []
    for kind in ("measures", "filters", "expressions"):
        for index, snippet in enumerate(raw.get(kind, [])):
            required = {
                "name", "display_name", "sql", "usage_guidance", "approval_status", "evidence"
            }
            if kind != "filters":
                required.add("alias")
            missing = sorted(key for key in required if not snippet.get(key))
            if missing:
                errors.append(f"{kind} snippet {index} missing: {', '.join(missing)}")
            names.append(str(snippet.get("name", "")))
            errors.extend(validate_sql_fragments([snippet.get("sql", "")]))
            sql = snippet.get("sql", "")
            if kind == "measures" and not AGGREGATION_RE.search(sql):
                errors.append(f"measure snippet {index} must contain an aggregation")
            if kind == "expressions" and AGGREGATION_RE.search(sql):
                errors.append(f"dimension snippet {index} must not contain an aggregation")
            if kind == "filters" and not re.search(
                r"(?i)(?:=|<>|!=|<=|>=|<|>|\bIN\b|\bLIKE\b|\bIS\b|\bBETWEEN\b)", sql
            ):
                errors.append(f"filter snippet {index} must be a Boolean condition")
            if deployment and snippet.get("approval_status") != "approved":
                errors.append(f"{kind} snippet {index} is not approved")
    if len(names) != len(set(names)):
        errors.append("SQL expression names must be unique across all snippet types")
    if deployment and contains_placeholder(raw):
        errors.append("SQL expressions contain unresolved placeholders")
    return errors


def validate_sql_functions_file(path: str | Path) -> list[str]:
    raw = load_yaml(path)
    if raw.get("functions"):
        return [
            "SQL functions cannot be emitted until the current workspace serialized schema "
            "has been exported and confirmed"
        ]
    return []


def validate_sample_questions(path: str | Path, *, deployment: bool = False) -> list[str]:
    raw = load_yaml(path)
    questions = raw.get("questions", [])
    errors: list[str] = []
    if not questions:
        errors.append("at least one sample question is required")
    if len(questions) != len(set(questions)):
        errors.append("sample questions must be unique")
    if not all(isinstance(question, str) and question.strip() for question in questions):
        errors.append("sample questions must be non-empty strings")
    if deployment and raw.get("approval_status") != "approved":
        errors.append("sample questions are not approved")
    if deployment and contains_placeholder(raw):
        errors.append("sample questions contain unresolved placeholders")
    return errors


def validate_sql_examples(sql_values: Iterable[str]) -> list[str]:
    errors = []
    for sql in sql_values:
        cleaned = SQL_COMMENT_RE.sub(" ", sql).strip()
        if not READ_SQL.search(cleaned):
            errors.append(f"SQL example must start with SELECT or WITH: {sql[:60]}")
        if WRITE_SQL.search(cleaned) or ";" in cleaned.rstrip().rstrip(";"):
            errors.append(f"unsafe SQL example: {sql[:60]}")
        if re.search(r"(?i)\bselect\s+\*", cleaned):
            errors.append(f"SELECT * is not allowed in examples: {sql[:60]}")
    return errors


def validate_sql_fragments(sql_values: Iterable[str]) -> list[str]:
    errors = []
    for sql in sql_values:
        cleaned = SQL_COMMENT_RE.sub(" ", sql).strip()
        if not cleaned:
            errors.append("SQL expression cannot be empty")
        if WRITE_SQL.search(cleaned) or ";" in cleaned.rstrip().rstrip(";"):
            errors.append(f"unsafe SQL expression: {sql[:60]}")
        if re.search(r"(?i)\bselect\s+\*", cleaned):
            errors.append(f"SELECT * is not allowed in SQL expressions: {sql[:60]}")
        if BARE_QUOTED_COLUMN_RE.search(cleaned):
            errors.append(f"SQL expression contains an unqualified quoted column: {sql[:60]}")
    return errors


def validate_instructions(path: str | Path) -> list[str]:
    text = Path(path).read_text(encoding="utf-8").strip()
    errors: list[str] = []
    if len(text) > 2_000:
        errors.append("general instructions must not exceed 2,000 characters")
    headings = [line for line in text.splitlines() if line.startswith("## ")]
    expected = [heading for heading in CANONICAL_HEADINGS if heading in headings]
    if headings != expected:
        errors.append("general instruction headings are missing, unknown, or out of canonical order")
    if re.search(r"(?im)^\s*(SELECT|WITH)\b", text):
        errors.append("SQL belongs in structured examples or expressions, not general instructions")
    return errors


def validate_serialized_space(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("version") != 2:
        errors.append("serialized_space version must be 2")
    data_sources = payload.get("data_sources", {})
    tables = data_sources.get("tables", [])
    metric_views = data_sources.get("metric_views", [])
    if len(tables) + len(metric_views) > MAX_DATA_SOURCES:
        errors.append(f"serialized_space exceeds the {MAX_DATA_SOURCES}-source limit")
    for collection_name, sources in (("tables", tables), ("metric_views", metric_views)):
        if sources != sorted(sources, key=lambda item: item.get("identifier", "")):
            errors.append(f"data_sources.{collection_name} must be sorted by identifier")
        for source in sources:
            columns = source.get("column_configs", [])
            if columns != sorted(columns, key=lambda item: item.get("column_name", "")):
                errors.append("column_configs must be sorted by column_name")

    question_ids: list[str] = []
    instruction_ids: list[str] = []
    id_arrays = [payload.get("config", {}).get("sample_questions", [])]
    id_arrays.append(payload.get("benchmarks", {}).get("questions", []))
    for values in id_arrays:
        ids = [str(item.get("id", "")) for item in values]
        question_ids.extend(ids)
        if ids != sorted(ids):
            errors.append("sample questions and benchmark arrays must be sorted by id")
    instructions = payload.get("instructions", {})
    if len(instructions.get("text_instructions", [])) > 1:
        errors.append("serialized_space supports at most one text instruction item")
    instruction_count = len(instructions.get("example_question_sqls", []))
    instruction_count += len(instructions.get("text_instructions", []))
    instruction_count += len(instructions.get("sql_functions", []))
    if instruction_count > 100:
        errors.append("serialized_space exceeds the 100-instruction limit")
    snippet_count = len(instructions.get("join_specs", []))
    snippet_count += sum(len(values) for values in instructions.get("sql_snippets", {}).values())
    if snippet_count > 200:
        errors.append("serialized_space exceeds the 200-knowledge-snippet limit")
    for key in ("text_instructions", "example_question_sqls", "join_specs"):
        values = instructions.get(key, [])
        ids = [str(item.get("id", "")) for item in values]
        instruction_ids.extend(ids)
        if ids != sorted(ids):
            errors.append(f"instructions.{key} must be sorted by id")
    for values in instructions.get("sql_snippets", {}).values():
        ids = [str(item.get("id", "")) for item in values]
        instruction_ids.extend(ids)
        if ids != sorted(ids):
            errors.append("SQL snippet arrays must be sorted by id")
    all_ids = question_ids + instruction_ids
    if any(not ID_RE.fullmatch(value) for value in all_ids):
        errors.append("all serialized IDs must be lowercase 32-character hexadecimal values")
    if len(question_ids) != len(set(question_ids)):
        errors.append("sample and benchmark question IDs must be unique")
    if len(instruction_ids) != len(set(instruction_ids)):
        errors.append("instruction IDs must be unique")
    import json

    encoded = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    if len(encoded.encode("utf-8")) > 3_500_000:
        errors.append("serialized_space exceeds 3.5 MB")
    def strings(value: Any):
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict):
            for nested in value.values():
                yield from strings(nested)
        elif isinstance(value, list):
            for nested in value:
                yield from strings(nested)

    if any(len(value) > 25_000 for value in strings(payload)):
        errors.append("serialized_space contains a string longer than 25,000 characters")
    return errors


def scan_secrets(root: str | Path) -> list[str]:
    findings: list[str] = []
    ignored = {".git", ".venv", ".pytest_cache", ".ruff_cache"}
    for path in Path(root).rglob("*"):
        if not path.is_file() or any(part in ignored for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if any(pattern.search(text) for pattern in SECRET_PATTERNS):
            findings.append(str(path))
    return findings


def validate_pair(dev: EnvironmentConfig, prod: EnvironmentConfig) -> list[str]:
    errors: list[str] = []
    if dev.environment != "dev" or prod.environment != "prod":
        errors.append("dev/prod configuration roles are invalid")
    if dev.agent_id and prod.agent_id and dev.agent_id == prod.agent_id:
        errors.append("development and production must not share an Agent ID")
    if not dev.raw.get("tables") or not prod.raw.get("tables"):
        return errors
    dev_sources = dev.table_fqns()
    prod_sources = prod.table_fqns()
    if set(dev_sources) != set(prod_sources):
        errors.append("development and production must configure the same logical sources")
    for key in sorted(set(dev_sources) & set(prod_sources)):
        dev_parts = dev_sources[key].split(".", 2)
        prod_parts = prod_sources[key].split(".", 2)
        if len(dev_parts) != 3 or len(prod_parts) != 3:
            continue
        if dev_parts[0] == prod_parts[0]:
            errors.append(f"development and production source {key} must use different catalogs")
        if dev_parts[1:] != prod_parts[1:]:
            errors.append(
                f"development and production source {key} must use the same schema and object name"
            )
    return errors


def require_valid(errors: list[str]) -> None:
    if errors:
        raise ConfigurationError("\n".join(f"- {error}" for error in errors))
