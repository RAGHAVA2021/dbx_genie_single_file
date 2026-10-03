from pathlib import Path

import yaml

from sales_genie.agent_definition import build_serialized_space
from sales_genie.config import load_environment


def test_serialized_space_shape_and_sorting():
    payload = build_serialized_space(load_environment("config/environments/dev.yml"))
    assert payload["version"] == 2
    assert payload["data_sources"]["tables"] == sorted(
        payload["data_sources"]["tables"], key=lambda item: item["identifier"]
    )
    assert len(payload["data_sources"]["tables"]) == 4
    ids = [item["id"] for item in payload["config"]["sample_questions"]]
    assert ids == sorted(ids)
    assert all(len(value) == 32 for value in ids)
    examples = payload["instructions"]["example_question_sqls"]
    assert len(examples) == 5
    assert examples == sorted(examples, key=lambda item: item["id"])
    assert all(item["question"] and item["sql"] for item in examples)
    assert "benchmarks" not in payload
    sale_date = next(
        column
        for table in payload["data_sources"]["tables"]
        for column in table.get("column_configs", [])
        if column["column_name"] == "<sale-date-column>"
    )
    assert sale_date["enable_entity_matching"] is False
    assert all(table.get("description") for table in payload["data_sources"]["tables"])


def test_metric_view_sources_are_serialized_separately(tmp_path: Path):
    contract = yaml.safe_load(Path("config/data/tables.yml").read_text(encoding="utf-8"))
    contract["tables"]["sales_fact"]["source_type"] = "metric_view"
    contract_path = tmp_path / "tables.yml"
    contract_path.write_text(yaml.safe_dump(contract), encoding="utf-8")

    payload = build_serialized_space(
        load_environment("config/environments/dev.yml"), contract_path=contract_path
    )

    metric_views = payload["data_sources"]["metric_views"]
    assert [item["identifier"] for item in metric_views] == [
        "<dev-catalog-name>.<schema-name>.<sales-fact-table>"
    ]
    assert all(
        item["identifier"] != "<dev-catalog-name>.<schema-name>.<sales-fact-table>"
        for item in payload["data_sources"]["tables"]
    )


def test_sql_snippets_and_agent_benchmarks_are_serialized(tmp_path: Path):
    expressions = tmp_path / "expressions.yml"
    expressions.write_text(
        """measures:
  - name: total_amount
    display_name: Total amount
    alias: total_amount
    sql: SUM(sales_fact.`amount`)
    synonyms: [sales]
""",
        encoding="utf-8",
    )
    evaluations = tmp_path / "evaluations.yml"
    evaluations.write_text(
        """include_in_agent: true
questions:
  - id: TEST-001
    question: Explain the sales trend.
    evaluation_mode: agent
    expected_business_interpretation: Use approved sales.
    expected_sql_characteristics: Use a bounded date range.
    expected_result_characteristics: Cite evidence.
""",
        encoding="utf-8",
    )
    payload = build_serialized_space(
        load_environment("config/environments/dev.yml"),
        expressions_path=expressions,
        evaluations_path=evaluations,
    )
    measure = payload["instructions"]["sql_snippets"]["measures"][0]
    assert measure["sql"] == ["SUM(sales_fact.`amount`)"]
    benchmark = payload["benchmarks"]["questions"][0]
    assert benchmark["answer"] == [{"format": "SQL", "content": []}]
    assert benchmark["evaluation_note"]
