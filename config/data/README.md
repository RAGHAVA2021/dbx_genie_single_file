# Data and semantic context

- `tables.yml` owns the logical source contract. It must declare exactly one source key, whether that
  source is a `table` or `metric_view`, whether it is required, and the `fqn_template` used to build
  the fully qualified name from environment values. Dev-to-prod promotion changes only the catalog;
  source type, schema, and object name must remain aligned.
- `semantics.yml` defines proposed columns, descriptions, synonyms, classifications, measures, and grain for the single source. `joins` must remain empty.

Prefer a governed Metric View for reusable KPIs when available. The configured object must expose every approved dimension and measure needed by the Agent. Do not invent metric formulas; confirm them from Unity Catalog evidence and business-owner approval.
This repository can attach an existing Metric View to the Genie Agent; creating or changing that
Metric View requires the separate Metric View workflow and explicit approval.
