from sales_genie.config import load_yaml
from sales_genie.evaluation import validate_evaluations


def test_evaluation_dataset_is_complete():
    assert validate_evaluations("evaluations/sales_questions.yml") == []


def test_categories_and_no_numeric_answers():
    rows = load_yaml("evaluations/sales_questions.yml")["questions"]
    expected = {"basic_aggregations", "time_series", "product_analysis", "store_analysis",
                "returns_and_discounts", "comparisons", "ambiguous", "unsupported", "security_sensitive"}
    assert expected <= {row["category"] for row in rows}
    assert all("expected_numeric_answer" not in row for row in rows)
    assert all(row["evaluation_mode"] in {"chat", "agent", "both"} for row in rows)
    clarification_ids = {row["id"] for row in rows if row["clarification_required"]}
    assert clarification_ids == {"SALES-016", "SALES-017"}


def test_production_promotion_requires_approved_passed_evaluations():
    errors = validate_evaluations(
        "evaluations/sales_questions.yml", deployment=True, production=True
    )
    assert any("not approved" in error for error in errors)
    assert any("passed workspace evaluation" in error for error in errors)
