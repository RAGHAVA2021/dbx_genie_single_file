from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from string import Template
from typing import Any

import yaml

PLACEHOLDER_RE = re.compile(r"<[^<>]+>")
MAX_DATA_SOURCES = 50
DEV_CONFIG_PATH = Path("config/environments/dev.yml")
PROD_CONFIG_PATH = Path("config/environments/prod.yml")
TABLES_PATH = Path("config/data/tables.yml")
SEMANTICS_PATH = Path("config/data/semantics.yml")
INSTRUCTIONS_PATH = Path("config/instructions/general_instructions.md")
SAMPLE_QUESTIONS_PATH = Path("config/examples/sample_questions.yml")
SQL_EXPRESSIONS_PATH = Path("config/examples/sql_expressions.yml")
SQL_EXAMPLES_PATH = Path("config/examples/sql_examples.yml")
SQL_FUNCTIONS_PATH = Path("config/examples/sql_functions.yml")
EVALUATIONS_PATH = Path("evaluations/sales_questions.yml")
GENERATED_ROOT = Path("generated")


def load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return value


def load_table_contract(path: str | Path = TABLES_PATH) -> dict[str, dict[str, Any]]:
    """Return the logical source contract that owns the source list and FQN templates."""
    tables = load_yaml(path).get("tables")
    if not isinstance(tables, dict) or not tables:
        raise ValueError(f"{path} must define a non-empty tables mapping")
    return tables


def table_keys(path: str | Path = TABLES_PATH) -> tuple[str, ...]:
    return tuple(load_table_contract(path))


def required_table_keys(path: str | Path = TABLES_PATH) -> tuple[str, ...]:
    return tuple(key for key, spec in load_table_contract(path).items() if spec.get("required"))


def contains_placeholder(value: Any) -> bool:
    if isinstance(value, str):
        return bool(PLACEHOLDER_RE.search(value))
    if isinstance(value, dict):
        return any(contains_placeholder(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_placeholder(item) for item in value)
    return False


@dataclass(frozen=True)
class EnvironmentConfig:
    raw: dict[str, Any]
    path: Path

    @property
    def environment(self) -> str:
        return str(self.raw.get("environment", ""))

    @property
    def state_path(self) -> Path:
        return Path("state") / f"{self.environment}.yml"

    @property
    def agent_id(self) -> str | None:
        state = load_yaml(self.state_path) if self.state_path.exists() else {}
        return state.get("agent_id") or self.raw.get("agent", {}).get("agent_id")

    def table_fqns(self, contract_path: str | Path = TABLES_PATH) -> dict[str, str]:
        contract = load_table_contract(contract_path)
        configured = self.raw.get("tables", {})
        values = {
            "catalog_name": self.raw.get("catalog_name"),
            "schema_name": self.raw.get("schema_name"),
        }
        values.update(
            {f"{key}_table": configured.get(key) for key in contract if configured.get(key)}
        )
        return {
            key: Template(spec["fqn_template"]).safe_substitute(values)
            for key, spec in contract.items()
            if configured.get(key)
        }

    def data_source_fqns(
        self, contract_path: str | Path = TABLES_PATH
    ) -> dict[str, dict[str, str]]:
        """Return resolved sources grouped by serialized-space collection."""
        contract = load_table_contract(contract_path)
        resolved = self.table_fqns(contract_path)
        grouped: dict[str, dict[str, str]] = {"tables": {}, "metric_views": {}}
        for key, identifier in resolved.items():
            source_type = contract[key].get("source_type", "table")
            collection = "metric_views" if source_type == "metric_view" else "tables"
            grouped[collection][key] = identifier
        return grouped

    @property
    def generated_agent_path(self) -> Path:
        return GENERATED_ROOT / self.environment / "sales_genie.geniespace.json"


def load_environment(path: str | Path) -> EnvironmentConfig:
    path = Path(path)
    return EnvironmentConfig(load_yaml(path), path)
