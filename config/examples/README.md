# Genie teaching examples

This directory contains context provided to Genie, not evaluation ground truth.

- `sample_questions.yml` controls starting questions shown to users.
- `sql_expressions.yml` controls structured measures, filters, and dimensions (`sql_snippets`).
- `sql_examples.yml` controls `instructions.example_question_sqls` and teaches reusable, read-only query shapes.
- `sql_functions.yml` records optional approved UC functions. It stays empty until the current live
  serialized schema is confirmed.

Keep benchmark/evaluation questions under `evaluations/` so test material is not accidentally taught to the Agent. SQL examples must use configured sources, qualify every column reference, remain read-only, be tested in the target workspace, and receive business and technical approval before deployment.
Examples that query Metric Views must use the applicable `MEASURE()` patterns and must not duplicate
governed measure formulas.

Do not derive SQL expressions automatically from proposed measures in `semantics.yml`. A snippet is
emitted only after its exact SQL, evidence, and approvals are recorded here.
