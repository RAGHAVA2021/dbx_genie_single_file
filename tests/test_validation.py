from copy import deepcopy

from sales_genie.agent_definition import build_serialized_space
from sales_genie.config import EnvironmentConfig, load_environment
from sales_genie.validation import (
    validate_environment,
    validate_instructions,
    validate_sample_questions,
    validate_semantics,
    validate_serialized_space,
    validate_sql_examples,
    validate_sql_examples_file,
    validate_sql_expressions_file,
)


def changed(**updates):
    base = deepcopy(load_environment("config/environments/dev.yml").raw)
    for key, value in updates.items():
        base[key] = value
    return EnvironmentConfig(base, load_environment("config/environments/dev.yml").path)


def test_required_fields_and_missing_warehouse():
    errors = validate_environment(changed(warehouse_id=None), deployment=True)
    assert any("warehouse_id" in error for error in errors)


def test_sources_outside_the_logical_contract_are_rejected():
    tables = deepcopy(load_environment("config/environments/dev.yml").raw["tables"])
    tables["bogus_source"] = "<bogus-table>"
    errors = validate_environment(changed(tables=tables))
    assert any("not declared in the logical source contract" in error for error in errors)


def test_deployment_requires_at_least_one_sql_example(tmp_path):
    empty = tmp_path / "sql_examples.yml"
    empty.write_text("examples: []\n", encoding="utf-8")
    assert not validate_sql_examples_file(empty)
    assert any(
        "at least one approved SQL example" in error
        for error in validate_sql_examples_file(empty, deployment=True)
    )


def test_duplicate_tables():
    cfg = changed()
    cfg.raw["tables"]["product_dimension"] = cfg.raw["tables"]["sales_fact"]
    assert "duplicate fully qualified source definitions" in validate_environment(cfg)


def test_environment_mixing():
    assert any("filename" in error for error in validate_environment(changed(environment="prod")))


def test_semantics_are_structurally_valid():
    assert validate_semantics("config/data/semantics.yml") == []


def test_unsafe_sql_is_rejected():
    assert validate_sql_examples(["DELETE FROM x", "SELECT * FROM x"])
    assert validate_sql_examples(["SELECT COUNT(*) FROM x"]) == []
    assert validate_sql_examples(["-- misleading comment\nDELETE FROM x"])
    assert validate_sql_examples(["SELECT 1; DELETE FROM x"])


def test_sql_examples_are_safe_but_not_deployment_ready():
    assert validate_sql_examples_file("config/examples/sql_examples.yml") == []
    errors = validate_sql_examples_file("config/examples/sql_examples.yml", deployment=True)
    assert any("unresolved placeholders" in error for error in errors)
    assert any("not approved" in error for error in errors)


def test_sample_questions_are_external_and_require_approval():
    path = "config/examples/sample_questions.yml"
    assert validate_sample_questions(path) == []
    assert "sample questions are not approved" in validate_sample_questions(path, deployment=True)


def test_structured_context_and_serialized_space_are_valid():
    assert validate_sql_expressions_file("config/examples/sql_expressions.yml") == []
    assert validate_instructions("config/instructions/general_instructions.md") == []
    payload = build_serialized_space(load_environment("config/environments/dev.yml"))
    assert validate_serialized_space(payload) == []


def test_entity_matching_requires_string_and_format_assistance(tmp_path):
    path = tmp_path / "semantics.yml"
    path.write_text(
        """columns:
  - table: sales_fact
    physical_column: product_id
    data_type: BIGINT
    description: Product identifier
    approval_status: approved
    enable_entity_matching: true
    enable_format_assistance: false
joins: []
measures: []
""",
        encoding="utf-8",
    )
    errors = validate_semantics(path)
    assert any("non-string" in error for error in errors)
    assert any("requires format assistance" in error for error in errors)
