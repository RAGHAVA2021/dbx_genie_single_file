from copy import deepcopy

import pytest

from sales_genie.config import EnvironmentConfig, load_environment
from sales_genie.deploy import deploy
from sales_genie.validation import validate_environment, validate_pair


def test_unresolved_placeholders_block_live_deployment():
    cfg = load_environment("config/environments/prod.yml")
    assert any("unresolved placeholders" in error for error in validate_environment(cfg, deployment=True))


def test_prod_requires_explicit_approval_after_validation(monkeypatch):
    raw = deepcopy(load_environment("config/environments/prod.yml").raw)
    raw = _resolve(raw)
    cfg = EnvironmentConfig(raw, load_environment("config/environments/prod.yml").path)
    with pytest.raises(PermissionError, match="approve-prod"):
        deploy(cfg, dry_run=False, approved=False)


def _resolve(value):
    if isinstance(value, str):
        return value.replace("<", "resolved-").replace(">", "")
    if isinstance(value, dict):
        return {key: _resolve(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_resolve(item) for item in value]
    return value


def test_dev_prod_ids_cannot_match(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "state").mkdir()
    (tmp_path / "state/dev.yml").write_text("agent_id: same\n")
    (tmp_path / "state/prod.yml").write_text("agent_id: same\n")
    dev = EnvironmentConfig({"environment": "dev", "workspace_host": "dev"}, tmp_path / "dev.yml")
    prod = EnvironmentConfig({"environment": "prod", "workspace_host": "prod"}, tmp_path / "prod.yml")
    assert any("must not share" in error for error in validate_pair(dev, prod))


def test_dev_prod_sources_follow_catalog_only_promotion_contract():
    dev = load_environment("config/environments/dev.yml")
    prod = load_environment("config/environments/prod.yml")
    assert validate_pair(dev, prod) == []

    same_catalog = deepcopy(prod.raw)
    same_catalog["catalog_name"] = dev.raw["catalog_name"]
    errors = validate_pair(dev, EnvironmentConfig(same_catalog, prod.path))
    assert any("different catalogs" in error for error in errors)

    different_schema = deepcopy(prod.raw)
    different_schema["schema_name"] = "<different-schema-name>"
    errors = validate_pair(dev, EnvironmentConfig(different_schema, prod.path))
    assert any("same schema and object name" in error for error in errors)
