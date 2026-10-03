# Prompt: Maintain and Complete the Sales Genie Agent Project

Use this prompt with a coding agent that has the current official Databricks skills installed.

---

Use the installed official Databricks skills, particularly:

- `databricks-core`
- `databricks-genie-agents`
- `databricks-data-discovery`
- `databricks-unity-catalog`
- `databricks-dbsql`
- `databricks-python-sdk`
- `databricks-dabs`
- `databricks-metric-views` when reusable governed KPIs are appropriate

Read the applicable skill instructions and references completely before implementation. Verify time-sensitive behavior against current official Databricks documentation. When an installed skill and current official documentation disagree, document the discrepancy and follow the newer authoritative official documentation unless the installed CLI/schema proves otherwise.

## Objective

Maintain and complete this production-quality, source-controlled Databricks Genie Agent project for sales-data analysis. Preserve the implemented design unless current official Databricks documentation or the installed CLI schema requires a change.

Use the current term **Genie Agent**. Mention **formerly Genie Space** only where an API, CLI command, bundle resource key, or compatibility explanation requires it.

## Current operating constraint

I do not currently have a Databricks workspace.

Therefore:

- Generate and validate everything locally.
- Do not authenticate to Databricks.
- Do not call a workspace API.
- Do not create, update, or delete workspace resources.
- Do not deploy the Genie Agent.
- Do not invent workspace IDs, warehouse IDs, Agent IDs, table names, columns, metric formulas, joins, permissions, profiling results, or API responses.
- Use clearly labelled placeholders.
- Separate local validation from workspace-dependent validation.
- Do not manually implement OAuth or token handling.
- Do not claim that a placeholder SQL query has been tested.
- Preserve any existing user changes in the repository.

## Implemented baseline and required flow

The repository already implements the local scaffold described in
[`docs/final-design-and-flow.md`](docs/final-design-and-flow.md). Do not recreate or replace it with
an unrelated structure. Extend it through this flow:

1. Authors update environment mappings, data contracts, semantic context, instructions, examples,
   and independent evaluations.
2. Local validation checks placeholders, approvals, source resolution, SQL safety, serialized IDs,
   sensitive-data rules, and dev/prod isolation without authenticating.
3. The deterministic builder creates
   `generated/<target>/sales_genie.geniespace.json` using serialized-space version 2.
4. The native DAB resource in `resources/sales_genie.genie_space.yml`, included by
   `databricks.yml`, deploys that artifact with `bundle.engine: direct`.
5. A development workspace run verifies sources, SQL, permissions, conversations, generated SQL,
   results, and the independent evaluation suite.
6. Production promotion requires approved definitions and examples, passed local and workspace
   gates, a protected-environment approval, and a pre-update export.
7. Post-deployment smoke tests and export provide evidence; rollback uses the reviewed pre-update
   backup through an explicitly approved restore or clone operation.

The native DAB path is primary. Keep SDK/API utilities for inspection, conversations, query-result
retrieval, export/import, smoke tests, and exceptional lifecycle operations. Do not make the legacy
SDK deployment utility the normal deployment path.

## Requirements and design gates

Before designing a deployable Agent, explicitly record:

1. Target audience and expected data/SQL fluency.
2. The Agent's narrowly defined business purpose.
3. At least 3–5 real business questions.
4. Known data sources or clearly labelled logical placeholders.
5. Business terminology, KPI definitions, fiscal/date rules, default filters, currency rules, and sensitive-data restrictions that still require confirmation.
6. Whether evaluation is intended for Chat mode, Agent mode, or both.

The supplied purpose and sample questions below satisfy the local scaffolding requirement, but physical mappings and business definitions remain unresolved until a workspace and domain owners are available.

Before using raw fact/dimension tables for reusable KPIs, perform a **Metric View decision gate**:

- If questions centre on governed reusable measures such as revenue, margin, return rate, conversion, or targets, recommend an appropriate Unity Catalog Metric View first.
- Explain that Metric Views centralise dimensions, measures, joins, and aggregation semantics.
- Do not create a Metric View without explicit approval and the applicable Metric View skill.
- If raw tables are retained, document why raw-detail access is required or why the Metric View recommendation was declined.

## Business purpose

The Genie Agent must help authorised business users analyse sales data using natural-language questions, including:

- What were total sales yesterday?
- Show monthly sales trends.
- Compare current-year sales with the prior year.
- What are the top-selling products?
- Which stores have declining sales?
- What are sales quantity and sales amount by product, store, and date?
- What are gross sales, discounts, returns, and net sales?
- Which products have the highest number of transactions?
- Compare actual sales with target sales, if approved target data is available.

Do not assume these measures or columns exist. Treat every physical object, relationship, formula, sign convention, grain, date rule, and currency rule as an approval-required placeholder.

## Source selection and readiness

Follow current Databricks guidance:

- Start small and focused; aim for five or fewer tables, views, or Metric Views initially.
- Include only sources and columns needed for the approved questions.
- Check the current official source limit rather than relying on a hard-coded historical value.
- Prefer well-documented, simplified, pre-joined views or Metric Views when they reduce ambiguity and fan-out risk.
- Do not attach a Metric View and its underlying raw tables unless users genuinely need both governed aggregation and raw detail.
- Hide or exclude irrelevant ETL metadata, hashes, raw payloads, embeddings, secrets, tokens, sensitive free text, and other distracting fields.

Define a future readiness assessment for each core business question with High/Medium/Low confidence across:

- Semantic coverage
- Data quality and freshness
- Modelability and join evidence
- Genie context readiness

Do not present Low-confidence questions as supported.

## Required repository structure

Use this separation of responsibilities:

```text
sales_genie/
├── README.md
├── prompt.md
├── pyproject.toml
├── .gitignore
├── databricks.yml                         # Native DAB entry point when current schema supports genie_spaces
├── resources/
│   └── sales_genie.genie_space.yml       # Native bundle resource, if supported by current CLI/schema
├── config/
│   ├── environments/
│   │   ├── dev.yml
│   │   └── prod.yml
│   ├── data/
│   │   ├── README.md
│   │   ├── tables.yml
│   │   └── semantics.yml
│   ├── instructions/
│   │   ├── README.md
│   │   ├── general_instructions.md
│   │   └── text_instruction_justification.md
│   └── examples/
│       ├── README.md
│       ├── sample_questions.yml
│       ├── sql_expressions.yml
│       ├── sql_examples.yml
│       └── sql_functions.yml              # Optional references to approved UC functions
├── generated/                             # Generated per-environment .geniespace.json; ignored unless policy says otherwise
├── evaluations/
│   └── sales_questions.yml
├── docs/
│   ├── final-design-and-flow.md
│   ├── workspace-smoke-tests.md
│   ├── permissions.md
│   ├── readiness-and-decisions.md
│   └── deployment-and-rollback.md
├── src/
│   └── sales_genie/
│       ├── __init__.py
│       ├── agent_definition.py
│       ├── bundle.py
│       ├── cli.py
│       ├── client.py
│       ├── config.py
│       ├── conversation.py
│       ├── deploy.py
│       ├── evaluation.py
│       ├── export_import.py
│       └── validation.py
├── scripts/
├── tests/
└── .github/
    └── workflows/
        └── genie-agent-cicd.yml
```

Adjust the exact structure only when current official Databricks schemas or skills require it, and explain the change.

## Environment configuration

Support independent development and production configurations under `config/environments/`.

Each environment must provide placeholders for:

- `workspace_host`
- Explicit Databricks CLI profile
- `warehouse_id`
- `catalog_name`
- `schema_name`
- Required sales fact, product, store, and date sources
- Optional customer and sales-target sources
- Genie Agent display name and description
- Parent workspace path
- Environment-specific Agent ID or bundle resource identity after deployment
- Deployment identity or service principal
- `authorised_principals`: a list of Agent access grants, each naming exactly one `group_name`,
  `user_name`, or `service_principal_name` plus its permission level. Any number of principals is
  supported; the list must match the bundle target's `agent_permissions`.

Use placeholders such as `<dev-workspace-url>`, `<prod-workspace-url>`, and `<dev-warehouse-id>`. Do not hard-code secrets, tokens, actual URLs, email addresses, or object IDs.

Store dev and prod Agent IDs, bundle target state, generated artifacts, and local state separately.
Promotion changes only the catalog component of source identifiers; schema names, object names, and
source types remain the same. Workspace hosts, warehouses, profiles, and identities may be shared
when that is the explicitly approved topology.

## Structured data and semantic configuration

`config/data/tables.yml` must define the logical source contract, declare each source's `source_type`
as `table` or `metric_view`, and construct fully qualified Unity Catalog identifiers from environment
values. The Genie project may attach an existing Metric View but must not create one without the
separate Metric View workflow and explicit approval.

`config/data/semantics.yml` must support:

- Business and physical names
- Data types
- Precise descriptions
- Synonyms
- Grain
- Primary/business and foreign keys
- Join relationships and cardinality
- Allowed filters
- Time dimensions
- Measures and aggregation rules
- Currency and unit of measure
- Sensitive-data classification
- Non-sensitive example values
- Approval status and evidence/source for each business definition
- Selective format assistance and entity-matching settings
- Excluded/hidden columns

Potential measures may include gross sales, discounts, returns, net sales, quantity, transaction count, and average transaction value, but all must be marked as examples pending business approval.

Prefer structured context in this order:

1. Agent description
2. Metric View semantics, when applicable
3. Focused source selection
4. Table and column descriptions
5. Synonyms and display names
6. Selective format assistance and entity matching
7. Hidden/excluded fields
8. Verified join specifications
9. SQL expressions for measures, filters, and fields
10. Representative example SQL
11. Approved Unity Catalog SQL functions for suitable complex/non-additive logic
12. Minimal global text instructions
13. Sample questions and independent benchmarks

## Prompt matching and sensitive data

- Enable entity matching only for stable string dimensions users are likely to name, such as product category, status, department, state, or country codes.
- Do not enable it broadly on IDs, hashes, free text, latitude/longitude, or numeric measures.
- Require format assistance when entity matching requires it.
- Do not enable entity matching on tables protected by row filters or column masks.
- Disable it for views that reference protected tables and for dynamic views unless current official documentation explicitly establishes a safe supported pattern.
- Treat Unity Catalog grants, row filters, masks, and curated views as the security boundary; text instructions are not access control.

## SQL expressions and example SQL

Create `config/examples/sql_expressions.yml` for reusable:

- Measures
- Filters
- Fields/dimensions
- Synonyms
- Usage instructions
- Approval state

Use SQL expressions for business concepts that can be encoded structurally. Do not bury metric formulas, filters, joins, or table-selection logic in general text instructions.

Create `config/examples/sql_examples.yml` containing representative, read-only Databricks SQL query shapes. Use the most typical natural-language phrasing as each example title/question and include concise usage guidance.

Requirements:

- Use only `SELECT` or `WITH` for query examples; use `SHOW`, `DESCRIBE`, `EXPLAIN`, and `information_schema` only for validation/profiling utilities.
- Never include mutating SQL.
- Fully qualify every column reference with its table or alias, including inside subqueries.
- Do not use `SELECT *` in examples or benchmarks.
- Avoid fan-out and respect source grain.
- Apply explicit date filters.
- Use safe division and explicit null handling where applicable.
- Do not duplicate formulas already governed by a Metric View.
- Parameterized examples must define the parameter type, description, allowed meaning, and a real validated default before deployment.
- Choose examples for distinct, high-value query shapes and known failure modes; quality and coverage matter more than a fixed quota. The current scaffold contains five reviewable examples, but every locally generated placeholder example must remain untested/pending and must block deployment until verified.
- Every example requires business and technical approval.

Keep teaching examples separate from evaluation questions to avoid benchmark leakage.

## General instructions

Use `config/instructions/general_instructions.md` only for global behavior that structured surfaces cannot express.

Use these headings in this order, omitting empty sections:

```markdown
## PURPOSE
## DISAMBIGUATION
## DATA QUALITY NOTES
## CONSTRAINTS
## Instructions you must follow when providing summaries
```

Requirements:

- Keep the total concise and below the current documented guidance.
- Use clear, specific instructions rather than vague rules.
- Put clarification instructions near the end of the general instructions so Genie prioritises them.
- State the exact clarification question for important ambiguous prompts.
- Ensure instructions do not conflict with metadata, SQL expressions, examples, or Metric View definitions.
- Put summary-only behavior under the exact summary heading.
- Do not place SQL in general instructions.

Create `text_instruction_justification.md` with:

- Exact instruction text or reference
- Why structured surfaces are insufficient
- Intended global behavior
- Possible overreach/regression risk
- Review and validation method

## Genie serialized definition

Generate a deterministic `serialized_space` version 2 definition using the current official schema.

Support, where confirmed:

- Sample questions
- Tables and Metric Views
- Table/column descriptions
- Column synonyms
- Format assistance and entity matching
- Hidden columns
- Join specifications
- SQL expressions/snippets
- Example question SQL with usage guidance
- Approved SQL functions
- Text instructions
- Benchmarks, if intentionally promoted into the Agent

Enforce current schema rules, including required lowercase 32-character hexadecimal IDs, array field shapes, uniqueness, deterministic ordering, maximum sizes, and source limits. Do not assume that historical limits remain current; verify them.

## Bundle and deployment design

Current official documentation, verified on 2026-10-03, documents native Declarative Automation Bundle support for Genie Agents through `resources.genie_spaces`, added in Databricks CLI 1.3.0 and requiring the **direct deployment engine**.

Therefore:

- Check the installed/current CLI version and `databricks bundle schema` before finalising implementation.
- If native `genie_spaces` is supported, use it as the primary source-controlled deployment mechanism.
- Configure `bundle.engine: direct`.
- Prefer `file_path` pointing to a generated `.geniespace.json` file instead of embedding a large escaped JSON string when practical.
- Parameterise warehouse, source mappings, parent path, names, and permissions per dev/prod target.
- Declare Agent access on the resource's own `permissions` field, which is the per-resource form
  Databricks documents for bundle resources. Do not move it to the top-level `permissions` mapping:
  that mapping's supported resource types are not enumerated, the documentation warns that resource
  permission levels "cannot necessarily be applied" through it, and `genie_spaces` support cannot be
  verified without a workspace. Supply the whole list from a per-target `type: complex` variable so
  several principals stay in one place per environment.
- Run `databricks bundle validate --strict --target <target>` only after a workspace/profile is available; do not run it under the current no-workspace constraint if it would authenticate.
- Retain Python SDK/API utilities only for lifecycle operations, conversation tests, export/inspection, or other capabilities not cleanly covered by the bundle resource.
- If the installed CLI/schema does not support native `genie_spaces`, document that exact evidence and fall back to SDK-authenticated management APIs without inventing a bundle resource.

The deployment is infrequent: one initial deployment followed by approximately five or six approved fixes over six months. Use manual, on-demand deployments rather than a recurring schedule.

## Deployment behavior

Development:

- Read `config/environments/dev.yml`.
- Validate and generate the dev `.geniespace.json` artifact.
- Support dry run.
- Create or update idempotently where supported.
- Keep dev state separate from production.
- Run workspace smoke tests and business evaluations after deployment.

Production:

- Read only `config/environments/prod.yml`.
- Require explicit confirmation and a protected CI environment approval.
- Refuse unresolved placeholders, pending approvals, unsafe SQL, failed tests, failed evaluations, or environment mixing.
- Export/back up the existing production Agent before update.
- Use production mappings, identity, warehouse, and permissions.
- Run post-deployment smoke tests.
- Provide a tested rollback procedure.

Use manual semantic versioning, for example:

- `v1.0.0`: initial deployment
- `v1.0.1`: instruction, synonym, or SQL correction
- `v1.1.0`: approved source, measure, or capability addition

## API and authentication

Prefer current supported SDK methods. If a high-level method is unavailable, use the official REST path through `WorkspaceClient.api_client.do` so authentication remains SDK-managed.

Every Genie operation this project needs is already a typed `WorkspaceClient.genie` method, so none
of them may be hand-built as a REST path. Use `get_space`, `create_space`, `update_space`, and the
`start_conversation_and_wait` / `create_message_and_wait` helpers rather than reimplementing polling
and backoff. `parent_path` is immutable and is never sent on update. Pin `databricks-sdk` at or above
the release that provides Genie space create/update plus `etag` on `GenieSpace`, so optimistic
concurrency on update is available.

Support:

- Create/get/update where not delegated to DAB
- Export/import
- Conversation creation and follow-up
- Polling terminal states
- Generated SQL and attachment inspection
- Timeouts and errors
- Agent-mode streaming only where the current API and required preview are available

Never manually construct OAuth flows or persist access tokens.

## Evaluations and benchmarks

Create at least 20 independent sales evaluation questions across:

- Basic aggregations
- Time series
- Product analysis
- Store analysis
- Returns and discounts
- Comparisons
- Ambiguous questions
- Unsupported questions
- Security-sensitive requests

Each item must include:

- ID
- Category
- Natural-language question
- Required sources
- Expected business interpretation
- Expected SQL characteristics
- Expected result characteristics
- Clarification requirement
- Refusal expectation
- Business-owner approval status
- Intended Chat/Agent evaluation mode
- Optional evaluation note for Agent-mode judging

Do not fabricate numeric expected answers.

For workspace benchmarks:

- Use verified SQL answers for deterministic Chat-mode questions.
- Use evaluation notes for Agent-mode synthesis.
- Test realistic alternate phrasings; current official guidance recommends two to four phrasings for common questions.
- Keep benchmark result sets bounded and deterministic; use `ORDER BY` when ordering matters.
- Review generated SQL and results manually before promoting a question into the benchmark set.

## Local tests

Create automated tests for:

- YAML/JSON syntax
- Required fields
- Placeholder detection
- Environment-specific source resolution through each source's `fqn_template`
- Rejection of any environment source absent from the logical source contract
- Duplicate sources
- Dev/prod isolation
- Catalog-only promotion: source types, schemas, and object names match while catalogs differ
- Import remapping of complete identifiers and embedded SQL, with rejection of source-shape drift
- Agent ID separation
- Warehouse configuration
- Join completeness and valid cardinality
- Measures missing aggregation or approval
- SQL expression validity
- Unsafe SQL and `SELECT *`
- Unqualified SQL columns where detectable
- Duplicate/invalid serialized IDs and sorting
- Example and sample-question approval gates, including at least one example before deployment
- Authorised-principal shape: valid level, exactly one principal per entry, no duplicates, and no
  drift between the environment file and the bundle target
- Conflicts across semantics, examples, and text instructions
- Sensitive-data and entity-matching restrictions
- Hard-coded secrets or credentials
- Bundle generation and target mapping without authentication
- Production confirmation, test, backup, and rollback guards
- Evaluation dataset coverage

## Future workspace validation

Document but do not execute checks for:

- Authentication and selected profile
- CLI and bundle schema version
- Warehouse existence, type/state, and `CAN USE`
- Catalog, schema, table, view, and Metric View existence
- Required columns and types
- Unity Catalog comments and constraints
- Data grain, freshness, quality, key uniqueness, and join fan-out
- Approved metric definitions and Metric View semantics
- Grants, row filters, masks, dynamic views, and sensitive columns
- Entity matching eligibility
- Example SQL execution or `EXPLAIN`
- Bundle validation and deployment
- Agent create/update and permissions
- Chat conversation execution and follow-ups
- Agent-mode behavior where available
- Generated SQL, sources, results, timeouts, and errors
- Benchmark and business-user acceptance
- Backup and rollback restoration

## CI/CD

Create a GitHub Actions template with:

1. Pull-request validation that remains fully local and never authenticates.
2. Manual dev deployment through a protected `dev` environment.
3. Manual prod deployment through a separately protected `prod` environment with required approval.

Do not add a weekly or recurring deployment schedule. This Agent is deployed once initially and then only for approved bug fixes or enhancements.

Use workload identities or service principals that match the approved workspace topology, with
separate protected deployment environments and least privilege. Never include credentials in source
control.

Grant `id-token: write` only to the jobs that deploy; pull-request validation never authenticates and
must not be able to mint a token. Pin every action to a release tag rather than a moving ref, and pin
the Databricks CLI version the `setup-cli` action installs — its `version` input defaults to the
latest release, so an unpinned workflow silently changes CLI behaviour between runs. Pin tool
versions and lint rule selection so a dependency release cannot change what local validation means.

## Permissions

Document least privilege for:

- Bundle/deployment identity
- Agent manager/editor
- Runtime or querying identity, depending on current execution semantics
- SQL warehouse
- Catalog and schema usage
- `SELECT` on approved tables/views only
- `EXECUTE` on approved Unity Catalog functions
- End-user `CAN RUN` or current equivalent

Express Agent access as one `authorised_principals` entry per principal, supporting groups, users,
and service principals. Prefer groups over named users. Keep the environment file and the bundle
target as the single agreed source of truth and fail validation on any drift between them.

Do not automatically grant access to entire catalogs when table- or view-level access is sufficient.

## README requirements

Document:

- What a Genie Agent is
- Local configuration versus the deployed workspace object
- Repository structure and responsibility of each configuration area
- Structured-context priority
- Dev/prod separation
- Placeholder replacement and approval process
- Metric View decision
- Installation and local checks
- Authentication after a workspace becomes available
- DAB/native resource decision and CLI requirements
- Dry run, development deployment, evaluation, promotion, production deployment, export, backup, and rollback
- Permissions
- Deferred workspace checks
- Known assumptions and business confirmations

## Completion criteria

After implementation:

- Run every possible local validation and unit test.
- Do not authenticate or contact Databricks.
- Do not deploy.
- Scan for inconsistent names and stale paths.
- Scan for hard-coded secrets.
- Confirm intentional placeholders remain and live deployment rejects them.
- Confirm dev/prod isolation and production approval.
- Confirm teaching examples and evaluations remain separate.
- Show the final file tree.
- Summarise test results.
- List workspace-deferred validations.
- List assumptions and required business decisions.
- List any discrepancies found between installed skills, the CLI schema, and current official documentation.

## Authoritative references to verify

- Databricks agent skill design reference: https://github.com/databricks/databricks-agent-skills/blob/main/skills/databricks-genie-agents/references/create-genie-agent.md
- Curate an effective Genie Agent: https://docs.databricks.com/aws/en/genie-agents/best-practices
- Tune Genie Agent quality: https://docs.databricks.com/aws/en/genie-agents/tune-quality
- Genie Agents API and `serialized_space`: https://docs.databricks.com/aws/en/genie-agents/conversation-api
- Test and monitor a Genie Agent: https://docs.databricks.com/aws/en/genie-agents/monitor
- Declarative Automation Bundle resources, including `genie_space`: https://docs.databricks.com/aws/en/dev-tools/bundles/resources

---

End of prompt.
