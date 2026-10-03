# Deployment and rollback

Deployments are manual and infrequent. There is no recurring schedule.

## Development

1. Replace placeholders and obtain the recorded business and technical approvals.
2. Run `ruff check .`, `pytest`, both environment validations, and the dev/prod separation check.
3. Generate the dev artifact with `sales-genie generate-bundle --config config/environments/dev.yml --deployment`.
4. Run `databricks bundle validate --strict --target dev --profile <dev-profile>`.
5. Review the bundle plan and deploy with `databricks bundle deploy --target dev --profile <dev-profile>`.
6. Resolve the deployed resource ID from `databricks bundle summary`, then run smoke tests and the approved benchmark suite.

## Production

1. Promote the exact reviewed source revision and use the protected production environment.
2. Run `sales-genie compare-dev-prod`. The source type, schema, and object name must match development;
   only the catalog component changes for production.
3. Generate and strictly validate the production target using only production mappings and the
   approved workspace identity.
4. Export the current production Agent before changing it and retain the parsed JSON as an artifact.
5. Deploy the bundle only after explicit approval.
6. Run smoke tests and business evaluation. Retain the resulting export and evidence.

## Rollback

1. Identify the last known-good Git revision and its production export.
2. Review the diff, warehouse, single-source mapping, parent path, permissions, and Agent ID.
3. Regenerate the production `.geniespace.json` from that revision.
4. Run local tests and `databricks bundle validate --strict --target prod`.
5. Redeploy the previous bundle revision through the protected production environment.
6. Repeat smoke tests and business evaluation. Do not use `bundle destroy` as rollback.

For emergency cloning from an export, use `import-agent --dry-run` first. Import requires the same
source type, schema, and object name as the target, remaps the complete identifier and embedded SQL to
the target catalog, and rejects a missing, additional, or mismatched source. It creates a new Agent; it does not
silently overwrite the bundle-managed production Agent.
