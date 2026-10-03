# Agent readiness and required decisions

## Audience and purpose

- Intended audience: authorised sales managers and analysts with business-domain fluency; SQL knowledge is not required.
- Purpose: answer focused descriptive sales questions about approved measures, trends, products, stores, returns, discounts, transaction counts, and targets when approved target columns exist in the single source.
- Out of scope: forecasting, competitor explanations, unrestricted row-level customer data, and any column or KPI that has not been approved.

## Core questions

1. What were total sales yesterday?
2. Show monthly sales trends.
3. Compare current-year sales with the prior year.
4. What are the top-selling products?
5. Which stores have declining sales?

The broader independent evaluation set is in `evaluations/sales_questions.yml`.

## Single logical source options

- Raw-table option: one denormalized sales table containing every approved measure and dimension;
  customer and sales-target attributes remain optional columns.
- Governed option: one focused Metric View that supplies the approved measures and dimensions can
  replace the raw table. This repository can attach that existing Metric View but does not
  create or deploy it.
- Physical catalog, schema, table/view/Metric View, column, warehouse, and Agent identifiers remain
  unresolved.

## Decisions required before deployment

- Approve a governed Metric View, or explicitly approve raw-table access with a raw-detail rationale.
- Confirm source grain, freshness, keys, and duplicate-row behavior.
- Approve sales, gross sales, discounts, returns, net sales, quantity, transaction count, and average transaction value definitions.
- Confirm calendar versus fiscal rules, default filters, cancellation handling, currency conversion, and units.
- Confirm sensitive-data classifications, row filters, column masks, dynamic views, and entity-matching eligibility.
- Test every example and deterministic benchmark SQL using bounded read-only execution or `EXPLAIN`.
- Approve the sample questions, SQL expressions, SQL examples, benchmark expectations, and permissions.

## Evaluation intent

Both Chat and Agent mode are planned. Current evaluation entries are Agent-mode-only because no
ground-truth SQL has been verified. Promote deterministic questions to `chat` or `both` only after
adding tested `answer_sql`. Agent benchmarks use grading notes and an empty SQL answer as required by
the serialized API shape.

## Current readiness

All core questions are **Low confidence** until physical mappings and business definitions are
verified. The local project supports the required structured surfaces and validation, but does not
claim data, semantic, security, or answer correctness without a workspace and domain-owner review.
