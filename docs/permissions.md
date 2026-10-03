# Least-privilege permissions

## Deployment identity

Use service principals according to the approved workspace topology. Development and production may
share an identity when explicitly approved, but retain separate protected deployment environments,
Agent permissions, state, and audit evidence. GitHub Actions should authenticate with Databricks
workload identity federation (`github-oidc`), not a stored PAT or client secret.

Grant only what the bundle needs:

- Permission to create and manage the Genie Agent in the configured parent workspace folder.
- `CAN USE` on the selected SQL warehouse.
- `USE CATALOG` and `USE SCHEMA` for the configured source namespace.
- `SELECT` on only the approved tables, views, or Metric Views.
- `EXECUTE` on only the approved Unity Catalog SQL functions, if functions are later configured.

## Agent users and editors

Each environment's `authorised_principals` list is the single source of truth for Agent access. Every
entry names exactly one `group_name`, `user_name`, or `service_principal_name` and one level, and the
list is applied through the Genie Agent resource's own `permissions` field — the per-resource form
Databricks documents for bundle resources. Validation rejects an unknown level, an entry naming no or
several principals, a duplicated principal, and any drift between the environment file and the
bundle target.

- Grant `CAN_RUN` to the business groups that consume the Agent. Prefer groups over named users.
- Grant `CAN_EDIT` only to curators who review sources, examples, benchmarks, and generated SQL.
- Keep `CAN_MANAGE` with the deployment identity and designated owners.

Unity Catalog grants, row filters, column masks, dynamic views, and curated views are the security
boundary. General instructions and excluded columns improve context but are not access controls.
Before enabling entity matching, verify that the source has no row filter or column mask and is not a
view over protected data.
