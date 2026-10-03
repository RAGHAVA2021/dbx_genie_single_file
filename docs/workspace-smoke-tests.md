# Workspace smoke-test design

These checks are intentionally deferred until a real workspace and approved mappings exist. Run them separately in dev and prod with that environment's profile and identity.

1. Instantiate `WorkspaceClient(profile=...)` and call a benign identity or warehouse read to prove SDK-managed authentication. Report authentication failures without printing credentials.
2. Fetch the configured SQL warehouse. Require that it exists, is an allowed type/state, and that the deployment/runtime identity has `CAN USE`; decide whether starting a stopped warehouse is authorised before doing so.
3. Fetch the one configured fully qualified table, view, or Metric View through Unity Catalog. Confirm
   its source type, catalog, schema, and object name without normalising names.
4. Compare physical columns and data types with approved `semantics.yml`. Fail for missing required columns, incompatible types, unresolved placeholders, zero/multiple sources, or any join specification.
5. Use grants/permission APIs or `SHOW GRANTS` to confirm `USE CATALOG`, `USE SCHEMA`, and `SELECT` at the narrowest approved scope. Confirm sensitive columns are protected by curated views, masks, or row filters; prompts alone do not count.
6. Profile bounded, read-only samples to confirm grain, key uniqueness, duplicate-row behaviour, null behaviour, and currency/date coverage. Use only `SELECT`, `WITH`, `SHOW`, `DESCRIBE`, `EXPLAIN`, or `information_schema` and apply limits/date filters.
7. For a missing Agent ID, create the dev Agent only after approval. For an existing ID, export a backup, fetch the Agent, and update it idempotently. In prod, require protected-environment approval and `--approve-prod`.
8. Start a conversation with an approved smoke question, capture conversation/message IDs, and poll through intermediate states until `COMPLETED`, `FAILED`, `CANCELLED`, or timeout.
9. On completion, record generated SQL, the cited source, text response, and query-result status. Assert
   the SQL is read-only, uses only the configured object, has explicit date filters, respects approved
   grain/measures and Metric View `MEASURE()` rules, and does not select sensitive columns.
10. Confirm final response retrieval and useful handling for ambiguity, unavailable columns/measures, permission errors, warehouse errors, failed SQL, cancellation, and timeout. Do not log row-level sensitive results.
11. Execute the approved evaluation set. Business reviewers assess interpretation and result characteristics; no fabricated numeric golden answers are permitted.
12. Export parsed `serialized_space`, test restoration in dev, retain evidence/artifacts, and record the exact Agent ID and environment without copying IDs across environments.

The included `run-smoke-tests` command implements warehouse/source lookup, required-column checks,
one conversation with exponential-backoff polling, terminal-status validation, and read-only generated
SQL checks. Grant inspection, bounded grain/duplicate-row profiling, query-result correctness, sensitive-data
controls, and full benchmark scoring remain workspace acceptance steps rather than automated local
claims.
