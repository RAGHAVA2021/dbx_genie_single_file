import json
from copy import deepcopy

import pytest

from sales_genie.agent_definition import build_serialized_space
from sales_genie.config import load_environment
from sales_genie.export_import import remap_import_sources
from sales_genie.validation import ConfigurationError


def test_import_remaps_only_catalog_while_preserving_source_shape():
    dev_payload = build_serialized_space(load_environment("config/environments/dev.yml"))
    dev_payload["instructions"]["example_question_sqls"][0]["sql"].append(
        "SELECT 1 FROM `<dev-catalog-name>`.`<schema-name>`.`<sales-fact-table>`"
    )
    prod = load_environment("config/environments/prod.yml")

    remapped, replacements = remap_import_sources(dev_payload, prod)

    encoded = json.dumps(remapped)
    assert "<dev-catalog-name>." not in encoded
    assert "<prod-catalog-name>." in encoded
    assert "`<prod-catalog-name>`.`<schema-name>`.`<sales-fact-table>`" in encoded
    assert replacements
    assert all(
        source.split(".", 1)[1] == target.split(".", 1)[1]
        for source, target in replacements.items()
    )


def test_import_rejects_schema_or_object_drift():
    payload = build_serialized_space(load_environment("config/environments/dev.yml"))
    changed = deepcopy(payload)
    changed["data_sources"]["tables"][0]["identifier"] = (
        "<dev-catalog-name>.<different-schema>.<unexpected-object>"
    )

    with pytest.raises(ConfigurationError, match="not configured for the target"):
        remap_import_sources(changed, load_environment("config/environments/prod.yml"))


def test_import_rejects_table_metric_view_type_drift():
    payload = build_serialized_space(load_environment("config/environments/dev.yml"))
    changed = deepcopy(payload)
    source = changed["data_sources"]["tables"].pop(0)
    changed["data_sources"]["metric_views"] = [source]

    with pytest.raises(ConfigurationError, match="source type does not match"):
        remap_import_sources(changed, load_environment("config/environments/prod.yml"))
