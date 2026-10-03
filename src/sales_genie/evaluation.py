from __future__ import annotations

from pathlib import Path

from .config import contains_placeholder, load_yaml

REQUIRED_EVALUATION_FIELDS = {
    "id", "category", "question", "required_tables", "expected_business_interpretation",
    "expected_sql_characteristics", "expected_result_characteristics", "clarification_required",
    "should_refuse", "business_owner_approval_status", "evaluation_mode",
}


def validate_evaluations(
    path: str | Path, *, deployment: bool = False, production: bool = False
) -> list[str]:
    raw = load_yaml(path)
    rows = raw.get("questions", [])
    errors: list[str] = []
    if len(rows) < 20:
        errors.append("evaluation dataset must contain at least 20 questions")
    ids = [row.get("id") for row in rows]
    if len(ids) != len(set(ids)):
        errors.append("evaluation question IDs must be unique")
    for index, row in enumerate(rows):
        missing = sorted(REQUIRED_EVALUATION_FIELDS - row.keys())
        if missing:
            errors.append(f"question {index} missing: {', '.join(missing)}")
        mode = row.get("evaluation_mode")
        if mode not in {"chat", "agent", "both"}:
            errors.append(f"question {index} has invalid evaluation_mode")
        if mode in {"chat", "both"} and not row.get("answer_sql"):
            errors.append(f"question {index} needs verified answer_sql for Chat mode")
        if mode in {"agent", "both"} and not (
            row.get("evaluation_note") or row.get("expected_result_characteristics")
        ):
            errors.append(f"question {index} needs Agent-mode grading guidance")
        if raw.get("include_in_agent") and row.get("business_owner_approval_status") != "approved":
            errors.append(f"question {index} cannot be promoted before business approval")
        if deployment and row.get("business_owner_approval_status") != "approved":
            errors.append(f"question {index} is not approved for workspace evaluation")
    if production:
        if raw.get("promotion_status") != "approved":
            errors.append("evaluation suite is not approved for production promotion")
        last_run = raw.get("last_workspace_run", {})
        if last_run.get("status") != "passed":
            errors.append("production promotion requires a passed workspace evaluation run")
        if not last_run.get("evidence") or contains_placeholder(last_run.get("evidence")):
            errors.append("production promotion requires evaluation evidence")
    return errors
