import copy
import json
from pathlib import Path

import yaml

from sales_genie.bundle import validate_bundle_mapping, write_bundle_artifact
from sales_genie.config import EnvironmentConfig, load_environment, load_yaml
from sales_genie.validation import validate_principals


def test_native_genie_bundle_uses_direct_engine_and_target_mappings():
    bundle = load_yaml("databricks.yml")
    assert bundle["bundle"]["engine"] == "direct"
    assert "resources/*.yml" in bundle["include"]
    resource = load_yaml("resources/sales_genie.genie_space.yml")
    assert "genie_spaces" in resource["resources"]
    assert resource["resources"]["genie_spaces"]["sales_genie"]["file_path"].endswith(
        ".geniespace.json"
    )
    assert validate_bundle_mapping(load_environment("config/environments/dev.yml")) == []
    assert validate_bundle_mapping(load_environment("config/environments/prod.yml")) == []


def test_agent_permissions_are_declared_on_the_resource():
    resource = load_yaml("resources/sales_genie.genie_space.yml")
    agent = resource["resources"]["genie_spaces"]["sales_genie"]
    assert agent["permissions"] == "${var.agent_permissions}"
    assert load_yaml("databricks.yml")["variables"]["agent_permissions"]["type"] == "complex"


def test_multiple_principals_of_mixed_types_are_supported(tmp_path: Path):
    many = [
        {"level": "CAN_RUN", "group_name": "<dev-authorised-group>"},
        {"level": "CAN_RUN", "service_principal_name": "<dev-reporting-sp>"},
        {"level": "CAN_EDIT", "user_name": "<dev-steward>"},
    ]
    assert validate_principals(many) == []
    base = load_environment("config/environments/dev.yml")
    raw = copy.deepcopy(base.raw)
    raw["authorised_principals"] = many
    config = EnvironmentConfig(raw, base.path)

    assert any("agent_permissions do not match" in e for e in validate_bundle_mapping(config))

    bundle = load_yaml("databricks.yml")
    bundle["targets"]["dev"]["variables"]["agent_permissions"] = many
    path = tmp_path / "databricks.yml"
    path.write_text(yaml.safe_dump(bundle), encoding="utf-8")
    assert validate_bundle_mapping(config, path) == []


def test_malformed_principals_are_rejected():
    assert validate_principals([])
    bad_level = [{"level": "CAN_SING", "group_name": "g"}]
    assert any("invalid level" in e for e in validate_principals(bad_level))
    assert any("exactly one" in e for e in validate_principals([{"level": "CAN_RUN"}]))
    assert any(
        "duplicate" in e
        for e in validate_principals(
            [{"level": "CAN_RUN", "group_name": "g"}, {"level": "CAN_EDIT", "group_name": "g"}]
        )
    )


def test_bundle_artifact_generation_is_local_and_deterministic(tmp_path: Path):
    output = tmp_path / "sales_genie.geniespace.json"
    config = load_environment("config/environments/dev.yml")
    first = write_bundle_artifact(config, output=output)
    original = output.read_text(encoding="utf-8")
    second = write_bundle_artifact(config, output=output)
    assert first == second
    assert output.read_text(encoding="utf-8") == original
    assert json.loads(original)["version"] == 2
