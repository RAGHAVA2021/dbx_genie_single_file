from pathlib import Path

import pytest

from sales_genie.config import (
    contains_placeholder,
    load_environment,
    load_yaml,
    required_table_keys,
    table_keys,
)


def test_yaml_files_parse():
    for path in Path("config").rglob("*.yml"):
        assert isinstance(load_yaml(path), dict)


def test_fully_qualified_names():
    cfg = load_environment("config/environments/dev.yml")
    assert cfg.table_fqns()["sales_fact"] == "<dev-catalog-name>.<schema-name>.<sales-fact-table>"


def test_only_single_sales_source_is_resolved():
    cfg = load_environment("config/environments/dev.yml")
    assert tuple(cfg.table_fqns()) == ("sales_fact",)


def test_placeholders_are_detected():
    assert contains_placeholder(load_yaml("config/environments/dev.yml"))


def test_source_list_comes_from_the_logical_contract():
    contract = load_yaml("config/data/tables.yml")["tables"]
    assert tuple(contract) == ("sales_fact",)
    assert table_keys() == tuple(contract)
    assert required_table_keys() == tuple(k for k, v in contract.items() if v.get("required"))


def test_fqn_template_drives_source_resolution(tmp_path):
    contract = tmp_path / "tables.yml"
    contract.write_text(
        'tables:\n'
        '  sales_fact:\n'
        '    required: true\n'
        '    fqn_template: "${catalog_name}.curated_${schema_name}.${sales_fact_table}"\n',
        encoding="utf-8",
    )
    cfg = load_environment("config/environments/dev.yml")
    assert cfg.table_fqns(contract) == {
        "sales_fact": "<dev-catalog-name>.curated_<schema-name>.<sales-fact-table>"
    }


def test_unresolved_fqn_template_variable_is_rejected(tmp_path):
    contract = tmp_path / "tables.yml"
    contract.write_text(
        'tables:\n'
        '  sales_fact:\n'
        '    required: true\n'
        '    fqn_template: "${catalog_name}.${schema_name}.${misspelled_table}"\n',
        encoding="utf-8",
    )
    cfg = load_environment("config/environments/dev.yml")
    with pytest.raises(ValueError, match="unresolved template variable"):
        cfg.table_fqns(contract)
