# Data and semantic context

- `tables.yml` owns the logical source contract. It declares every source key, whether the source is
  a `table` or `metric_view`, whether it is required, and the `fqn_template` used to build the fully
  qualified name from environment values. Adding a source here is what makes it available to the
  environment files. Dev-to-prod promotion changes only the catalog; source type, schema, and object
  name must remain aligned.
- `semantics.yml` defines proposed columns, descriptions, synonyms, classifications, measures, grain, keys, and joins.

Prefer governed Metric Views for reusable KPIs when available. Do not invent joins or metric formulas; confirm them from Unity Catalog evidence and business-owner approval.
This repository can attach an existing Metric View to the Genie Agent; creating or changing that
Metric View requires the separate Metric View workflow and explicit approval.
