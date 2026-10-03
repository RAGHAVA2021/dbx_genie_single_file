from __future__ import annotations

import hashlib
from pathlib import Path
from string import Template
from typing import Any

from .config import (
    EVALUATIONS_PATH,
    INSTRUCTIONS_PATH,
    SAMPLE_QUESTIONS_PATH,
    SEMANTICS_PATH,
    SQL_EXAMPLES_PATH,
    SQL_EXPRESSIONS_PATH,
    TABLES_PATH,
    EnvironmentConfig,
    load_table_contract,
    load_yaml,
)


def stable_id(namespace: str, value: str) -> str:
    """Return the stable lowercase 32-hex ID required by serialized_space v2."""
    return hashlib.md5(f"{namespace}:{value}".encode(), usedforsecurity=False).hexdigest()


def _substitute(value: str, fqns: dict[str, str]) -> str:
    return Template(value).safe_substitute(fqns).strip()


def _column_config(column: dict[str, Any]) -> dict[str, Any]:
    item: dict[str, Any] = {
        "column_name": column["physical_column"],
        "description": [column["description"]],
        "synonyms": column.get("synonyms", []),
        "exclude": bool(column.get("exclude"))
        or column.get("sensitive_classification") in {"restricted", "secret"},
    }
    for key in (
        "enable_format_assistance",
        "enable_entity_matching",
        "get_example_values",
        "build_value_dictionary",
    ):
        if key in column:
            item[key] = bool(column[key])
    return item


def _sql_snippets(path: str | Path, fqns: dict[str, str]) -> dict[str, list[dict[str, Any]]]:
    raw = load_yaml(path)
    result: dict[str, list[dict[str, Any]]] = {}
    for kind in ("measures", "filters", "expressions"):
        values: list[dict[str, Any]] = []
        for snippet in raw.get(kind, []):
            name = snippet["name"]
            item: dict[str, Any] = {
                "id": stable_id(f"sql-snippet-{kind}", name),
                "display_name": snippet["display_name"],
                "sql": [_substitute(snippet["sql"], fqns)],
            }
            if kind != "filters":
                item["alias"] = snippet["alias"]
            if snippet.get("synonyms"):
                item["synonyms"] = snippet["synonyms"]
            values.append(item)
        if values:
            result[kind] = sorted(values, key=lambda value: value["id"])
    return result


def _benchmarks(path: str | Path, fqns: dict[str, str]) -> list[dict[str, Any]]:
    raw = load_yaml(path)
    if not raw.get("include_in_agent", False):
        return []
    values = []
    for row in raw.get("questions", []):
        answer_sql = row.get("answer_sql")
        content = [_substitute(answer_sql, fqns)] if answer_sql else []
        item: dict[str, Any] = {
            "id": stable_id("benchmark", row["id"]),
            "question": [row["question"]],
            "answer": [{"format": "SQL", "content": content}],
        }
        note = row.get("evaluation_note")
        if not note and row.get("evaluation_mode") in {"agent", "both"}:
            note = " ".join(
                (
                    row["expected_business_interpretation"],
                    row["expected_sql_characteristics"],
                    row["expected_result_characteristics"],
                )
            )
        if note:
            item["evaluation_note"] = [note]
        values.append(item)
    return sorted(values, key=lambda value: value["id"])


def build_serialized_space(
    config: EnvironmentConfig,
    semantics_path: str | Path = SEMANTICS_PATH,
    instructions_path: str | Path = INSTRUCTIONS_PATH,
    examples_path: str | Path = SQL_EXAMPLES_PATH,
    sample_questions_path: str | Path = SAMPLE_QUESTIONS_PATH,
    expressions_path: str | Path = SQL_EXPRESSIONS_PATH,
    evaluations_path: str | Path = EVALUATIONS_PATH,
    contract_path: str | Path = TABLES_PATH,
) -> dict[str, Any]:
    semantics = load_yaml(semantics_path)
    examples = load_yaml(examples_path)
    sample_questions = load_yaml(sample_questions_path)
    source_contract = load_table_contract(contract_path)
    fqns = config.table_fqns(contract_path)
    source_groups = config.data_source_fqns(contract_path)

    columns_by_table: dict[str, list[dict[str, Any]]] = {}
    for column in semantics.get("columns", []):
        columns_by_table.setdefault(column["table"], []).append(_column_config(column))

    data_sources: dict[str, list[dict[str, Any]]] = {}
    for collection, sources in source_groups.items():
        values = []
        for key, identifier in sources.items():
            item: dict[str, Any] = {"identifier": identifier}
            purpose = source_contract[key].get("purpose")
            if purpose:
                item["description"] = [purpose]
            if columns_by_table.get(key):
                item["column_configs"] = sorted(
                    columns_by_table[key], key=lambda value: value["column_name"]
                )
            values.append(item)
        if values:
            data_sources[collection] = sorted(values, key=lambda value: value["identifier"])

    questions = sample_questions.get("questions", [])
    text = Path(instructions_path).read_text(encoding="utf-8").strip()
    payload: dict[str, Any] = {
        "version": 2,
        "config": {
            "sample_questions": sorted(
                (
                    {"id": stable_id("sample", question), "question": [question]}
                    for question in questions
                ),
                key=lambda value: value["id"],
            )
        },
        "data_sources": data_sources,
        "instructions": {
            "text_instructions": [
                {"id": stable_id("instruction", text), "content": [text]}
            ]
        },
    }

    example_sqls = []
    for example in examples.get("examples", []):
        example_sqls.append(
            {
                "id": stable_id("example-sql", example["name"]),
                "question": [example["question"]],
                "sql": [_substitute(example["sql"], fqns)],
                "usage_guidance": [example["usage_guidance"]],
            }
        )
    if example_sqls:
        payload["instructions"]["example_question_sqls"] = sorted(
            example_sqls, key=lambda value: value["id"]
        )

    joins = []
    relation_tags = {
        "many_to_one": "--rt=FROM_RELATIONSHIP_TYPE_MANY_TO_ONE--",
        "one_to_many": "--rt=FROM_RELATIONSHIP_TYPE_ONE_TO_MANY--",
        "one_to_one": "--rt=FROM_RELATIONSHIP_TYPE_ONE_TO_ONE--",
        "many_to_many": "--rt=FROM_RELATIONSHIP_TYPE_MANY_TO_MANY--",
    }
    for join in semantics.get("joins", []):
        left_key, right_key = join["left_table"], join["right_table"]
        condition = (
            f"`{left_key}`.`{join['left_column']}` = "
            f"`{right_key}`.`{join['right_column']}`"
        )
        joins.append(
            {
                "id": stable_id("join", join["name"]),
                "left": {"identifier": fqns[left_key], "alias": left_key},
                "right": {"identifier": fqns[right_key], "alias": right_key},
                "sql": [condition, relation_tags[join["relationship"]]],
            }
        )
    if joins:
        payload["instructions"]["join_specs"] = sorted(
            joins, key=lambda value: value["id"]
        )

    snippets = _sql_snippets(expressions_path, fqns)
    if snippets:
        payload["instructions"]["sql_snippets"] = snippets

    benchmarks = _benchmarks(evaluations_path, fqns)
    if benchmarks:
        payload["benchmarks"] = {"questions": benchmarks}
    return payload
