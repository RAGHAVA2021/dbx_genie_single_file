# Sales Genie Agent

A source-controlled project for designing, validating, deploying, and evaluating a Databricks Genie Agent for sales analysis.

The repository currently operates in **local-only mode** because no Databricks workspace is available. It has not authenticated to Databricks, called a workspace API, created an Agent, or deployed any resource. All workspace identifiers and physical data definitions are placeholders.

## What a Genie Agent is

A Genie Agent is a curated natural-language interface over selected Unity Catalog data. It uses configured data sources, semantic context, examples, and instructions to generate Databricks SQL and return grounded answers through a SQL warehouse.

Some APIs and commands still use the compatibility term **Genie Space**. This project uses **Genie Agent** in user-facing documentation and retains API terminology only where required.

## Project goals

The Agent is intended to help authorised business users analyse total sales, trends, product and store performance, returns, discounts, transaction counts, and actual-versus-target results when approved target data exists.

The project does not assume that any measure, column, join, fiscal rule, target, or currency conversion exists. These remain configurable and require evidence and business approval.

The audience, scope, evaluation intent, confidence, and unresolved decisions are recorded in
[readiness-and-decisions.md](docs/readiness-and-decisions.md).

The complete architecture, mandatory versus optional inputs, and local-to-production operating flow
are documented in [final-design-and-flow.md](docs/final-design-and-flow.md).

## Repository structure

```text
sales_genie/
├── README.md
├── prompt.md
├── databricks.yml
├── pyproject.toml
├── resources/
│   └── sales_genie.genie_space.yml
├── config/
│   ├── environments/
│   │   ├── dev.yml
│   │   └── prod.yml
│   ├── data/
│   │   ├── tables.yml
│   │   └── semantics.yml
│   ├── instructions/
│   │   ├── general_instructions.md
│   │   └── text_instruction_justification.md
│   └── examples/
│       ├── sample_questions.yml
│       ├── sql_expressions.yml
│       ├── sql_examples.yml
│       └── sql_functions.yml
├── generated/                 # ignored per-environment .geniespace.json files
├── evaluations/
│   └── sales_questions.yml
├── docs/
│   ├── deployment-and-rollback.md
│   ├── final-design-and-flow.md
│   ├── permissions.md
│   ├── readiness-and-decisions.md
│   └── workspace-smoke-tests.md
├── src/sales_genie/
├── scripts/
├── tests/
└── .github/workflows/genie-agent-cicd.yml
```

### Configuration responsibilities

| Location | Purpose | Included in Agent payload |
|---|---|---|
| `config/environments/` | Dev/prod workspace, warehouse, catalog, schema, table, identity, and Agent settings | Resolves deployment metadata and source identifiers |
| `config/data/tables.yml` | Logical source contract: declares source keys, `source_type` (`table` or `metric_view`), required sources, and each `fqn_template` | Resolves typed, fully qualified source identifiers |
| `config/data/semantics.yml` | Columns, descriptions, synonyms, classifications, grain, measures, keys, and joins | Yes; column configuration and join specifications |
| `config/instructions/general_instructions.md` | Global ambiguity, safety, availability, and response rules | Yes; one `text_instructions` item |
| `config/instructions/text_instruction_justification.md` | Governance rationale and risk assessment for free-text instructions | No |
| `config/examples/sample_questions.yml` | User-visible starting questions | Yes; `config.sample_questions` |
| `config/examples/sql_expressions.yml` | Approved reusable measures, filters, and dimensions | Yes; `instructions.sql_snippets` when configured |
| `config/examples/sql_examples.yml` | Approved read-only question-to-SQL teaching examples | Yes; `instructions.example_question_sqls` |
| `config/examples/sql_functions.yml` | Optional approved UC functions; empty until the live serialized schema is confirmed | Not currently emitted |
| `evaluations/sales_questions.yml` | Independent business evaluation cases | Only when deliberately promoted with `include_in_agent: true` |
| `databricks.yml` and `resources/` | Native direct-engine DAB deployment definition | Deploys the generated Agent artifact and permissions |

The builder generates the Genie `serialized_space` version 2 object with stable 32-character IDs and API-required sorting. The deployed Agent remains a workspace object; local configuration expresses desired state but does not prove that the workspace object exists.

## Local installation

Python 3.11 or later is required.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
```

No Databricks credentials are needed for local validation or dry runs.

## Local validation

```bash
sales-genie validate-config --config config/environments/dev.yml
sales-genie validate-config --config config/environments/prod.yml
sales-genie compare-dev-prod
sales-genie generate-bundle --config config/environments/dev.yml
pytest
ruff check .
```

Local validation permits intentionally retained placeholders. Deployment validation is stricter and
rejects unresolved placeholders, unapproved examples, missing warehouse configuration, invalid joins,
unsafe SQL, environment mixing, and shared dev/prod Agent IDs. `compare-dev-prod` additionally enforces
the catalog-only promotion contract.

Preview generated requests without constructing an SDK client or making a network call:

```bash
sales-genie deploy-dev --dry-run
sales-genie deploy-prod --dry-run
```

The preferred native-bundle preview is:

```bash
sales-genie generate-bundle --config config/environments/dev.yml
```

This writes `generated/dev/sales_genie.geniespace.json` locally. Generated files are ignored
because the catalog, environment metadata, and approval state differ by target even though schema
and object names remain aligned.

## Preparing real configuration

Complete these steps only after a Databricks workspace and approved data sources are available.

### 1. Configure environments

Update the development and production files independently with:

- Workspace host and explicit CLI profile
- SQL warehouse ID
- Catalog, schema, and physical table, view, or Metric View names
- Agent display name, description, and parent workspace path
- Deployment identity, and one `authorised_principals` entry per principal granted access

Each `authorised_principals` entry names a single `group_name`, `user_name`, or
`service_principal_name` plus its level, and must match the target's `agent_permissions` in
[databricks.yml](databricks.yml). Any number of principals is supported.

Promotion changes only the catalog component of each source identifier. Schema names, object names,
and source types must match between development and production. Agent IDs, state files, generated
artifacts, and bundle target state remain environment-specific; hosts, warehouses, profiles, and
identities may be shared when that is the approved workspace topology.

### 2. Confirm data and semantics

Use Unity Catalog metadata and bounded read-only profiling to confirm table and column existence, types, source grain, keys, join cardinality, date rules, measure formulas, aggregations, currency handling, and sensitive-data classifications.

Update [semantics.yml](config/data/semantics.yml) only with supported definitions. Reusable business KPIs should preferably be governed upstream, such as through a suitable Unity Catalog Metric View, rather than repeatedly derived in Genie instructions.

Before deployment, complete `metric_view_decision` in `semantics.yml`. For this KPI-heavy sales
domain, a governed Metric View is the recommended default. Retaining raw fact/dimension sources
requires an approved rationale, verified grain and joins, and a documented need for raw-detail access.

### 3. Approve Genie examples

Review [sample_questions.yml](config/examples/sample_questions.yml), then set its `approval_status` to `approved`.

For every entry in [sql_examples.yml](config/examples/sql_examples.yml):

1. Replace all `<...>` placeholders.
2. Confirm every source is configured for the Agent.
3. Keep every column reference qualified with its source alias.
4. Execute or `EXPLAIN` the query against the intended SQL warehouse.
5. Confirm it is read-only and produces the intended result shape.
6. Obtain business and technical approval.
7. Change `approval_status` to `approved`.

Example SQL teaches reusable query shapes. It must not contain fabricated numeric answers or unverified business formulas.
When a configured source is a Metric View, its examples must follow the applicable `MEASURE()` query
rules and must not re-derive governed measures.

Add approved reusable business terms to
[sql_expressions.yml](config/examples/sql_expressions.yml), not to general instructions. Measures
must aggregate, filters must be Boolean conditions, dimensions must be row-level expressions, and
all column references must be qualified. Keep `sql_functions.yml` empty until a live Agent export
confirms the current API field shape; approved functions also require UC `EXECUTE` permission.

### 4. Review general instructions

[general_instructions.md](config/instructions/general_instructions.md) contains global behaviour only. Table selection, column meaning, joins, metric definitions, and SQL patterns belong in structured configuration.

The rationale and regression risks are documented in [text_instruction_justification.md](config/instructions/text_instruction_justification.md).

## Authentication when a workspace is available

Install a current unified Databricks CLI and configure explicit named profiles using an official
OAuth, workload-identity, or service-principal flow. Profiles and identities follow the approved
workspace topology; the catalog-only source mapping and environment-specific Agent state are always
validated independently.

Interactive operations construct `WorkspaceClient(profile=...)`. CI uses Databricks GitHub OIDC
workload identity through unified-auth environment variables. The CLI and SDK own authentication and
token refresh; this project does not manually create or handle OAuth tokens.

## Agent lifecycle commands

Native DAB deployment is the primary path. Generate the environment-specific artifact first, then
validate strictly and deploy manually. Bundle validation is intentionally deferred until credentials
and a real workspace exist.

### Development

```bash
sales-genie generate-bundle --config config/environments/dev.yml --deployment
databricks bundle validate --strict --target dev --profile <dev-profile>
databricks bundle deploy --target dev --profile <dev-profile>
databricks bundle summary --target dev --profile <dev-profile>

# Copy resources.genie_spaces.sales_genie.id from the summary.
sales-genie get-agent --config config/environments/dev.yml --agent-id <dev-agent-id>
sales-genie query-agent \
  --config config/environments/dev.yml \
  --agent-id <dev-agent-id> \
  --question 'What were total sales yesterday?'
sales-genie run-smoke-tests --config config/environments/dev.yml --agent-id <dev-agent-id>
sales-genie export-agent \
  --config config/environments/dev.yml \
  --agent-id <dev-agent-id> \
  --output exports/dev-agent.json
```

### Production

```bash
sales-genie generate-bundle --config config/environments/prod.yml --deployment
databricks bundle validate --strict --target prod --profile <prod-profile>
# Run only after protected-environment/manual approval.
databricks bundle deploy --target prod --profile <prod-profile>
databricks bundle summary --target prod --profile <prod-profile>
# Copy resources.genie_spaces.sales_genie.id from the summary.
sales-genie run-smoke-tests --config config/environments/prod.yml --agent-id <prod-agent-id>
sales-genie export-agent \
  --config config/environments/prod.yml \
  --agent-id <prod-agent-id> \
  --output exports/prod-agent.json
```

A live production deployment rejects unresolved configuration and pending approvals, requires the
catalog-only source mapping contract, and uses a separately protected target, Agent identity, state,
permissions, and generated artifact. Workspace infrastructure may be shared by policy.
The CI workflow runs tests, exports the existing Agent when present, validates with `--strict`, deploys,
smoke-tests, and stores the backup and resulting export as artifacts.

## State, export, import, and rollback

The legacy SDK deployment utility stores environment-specific Agent IDs in ignored files:

```text
state/dev.yml
state/prod.yml
```

Native DAB deployment does not populate these files. After a bundle deployment, resolve the Agent ID
with `databricks bundle summary` and pass it explicitly to inspection, query, smoke-test, and export
commands.

Generated exports and backups are also ignored:

```text
exports/*.json
backups/*.json
```

Exports store parsed, reviewable `serialized_space` JSON. Import verifies that source types, schemas,
and object names match the target and remaps complete identifiers from the source catalog to the
target catalog. It creates a new Agent rather than silently overwriting an existing one:

```bash
sales-genie import-agent \
  --config config/environments/prod.yml \
  --input exports/dev-agent.json \
  --dry-run
```

For rollback, review the pre-update backup, validate its environment mappings, and restore it only through an explicitly approved update or clone process.

## Business evaluation

[sales_questions.yml](evaluations/sales_questions.yml) contains 21 cases covering aggregations, time series, product and store analysis, returns and discounts, comparisons, ambiguity, unsupported requests, and security-sensitive requests.

Each case records required sources, expected interpretation, SQL/result characteristics, clarification/refusal behaviour, and approval status. It deliberately contains no fabricated expected numeric answers. Business owners must approve the evaluation expectations and review actual development results before promotion.

The file also records `evaluation_mode`, benchmark promotion intent, and the latest workspace-run
evidence. Deterministic questions can move to Chat mode only after their `answer_sql` has been tested.
Production generation is blocked until the suite is approved and a passed workspace evaluation with
evidence is recorded.

## CI/CD

The GitHub Actions template provides:

1. Pull-request linting, validation, tests, environment-separation checks, and secret detection without connecting to Databricks.
2. Manual development deployment through a protected `dev` environment.
3. Manual production deployment through a separately protected `prod` environment with approval,
   topology-approved credentials, backup, smoke tests, and export artifacts.

The workflow pins both the `databricks/setup-cli` action and the Databricks CLI release it installs
to the version this repository's bundle schema was verified against, so a CLI release cannot silently
change deployment behaviour. Only the two deployment jobs are granted `id-token: write`; pull-request
validation never receives a token because it never authenticates.

Authentication steps remain placeholders until the workspace and organisational authentication standard are known.

## Least-privilege permissions

The future deployment identity needs only permission to create objects in the configured parent folder, manage/export the specific Genie Agent, and read metadata required for validation.

The applicable runtime identity or querying user needs:

- `CAN USE` on the selected SQL warehouse
- `USE CATALOG` on the approved catalog
- `USE SCHEMA` on the approved schema
- `SELECT` on only the approved tables, curated views, or Metric Views
- Permission to use the Genie Agent

Do not grant entire-catalog access when table- or view-level access is sufficient. Protect sensitive data with Unity Catalog views, row filters, column masks, and grants. Prompt instructions are not a security boundary.

## Workspace smoke tests

The future acceptance sequence is documented in [workspace-smoke-tests.md](docs/workspace-smoke-tests.md). It covers authentication, warehouse and source checks, required columns, permissions, Agent lifecycle operations, conversations, generated SQL, final responses, failures, timeouts, evaluation, export, and restoration.

The following cannot be completed locally:

- Workspace authentication and profile verification
- Warehouse, catalog, schema, table/view/Metric View, and column checks
- Data types, freshness, grain, key quality, and join fan-out
- Unity Catalog privileges and sensitive-data controls
- Agent creation, update, export, import, and permissions
- Conversation execution, generated SQL, results, and timeouts
- Business correctness of returned answers

## Python SDK and DAB design choice

The primary deployment mechanism is the native `resources.genie_spaces` DAB resource in
[databricks.yml](databricks.yml), using `bundle.engine: direct` and a generated version 2
`.geniespace.json` file. Local CLI 1.17.0 confirms this resource and its `file_path`, permissions,
title, description, parent path, and warehouse fields.

The official Python SDK remains for read-only inspection, conversations and follow-ups, attachment
query-result retrieval, export/import, smoke tests, and an explicitly legacy API deployment utility.
It uses Databricks unified authentication and never handles tokens directly. DAB deployment is the
documented default for normal development and production promotion.

## Verified Databricks references

The following sources were rechecked on **2026-10-03**. Current Databricks product documentation and
the schema returned by the installed CLI take precedence if an example in a GitHub skill or repository
becomes stale.

### Official Databricks documentation

| Reference | What it was used to verify |
|---|---|
| [Databricks documentation index](https://docs.databricks.com/llms.txt) | Official documentation discovery and current product terminology. |
| [Curate an effective Genie Agent](https://docs.databricks.com/aws/en/genie-agents/best-practices) | Focused scope, aim for five or fewer sources, current 50-source limit, metadata, SQL expressions, examples, and minimal text instructions. |
| [Tune Genie Agent quality](https://docs.databricks.com/aws/en/genie-agents/tune-quality) | SQL expressions, example queries, trusted SQL functions, prompt matching, entity-matching restrictions, and instruction/snippet limits. |
| [Use the Genie Agents API](https://docs.databricks.com/aws/en/genie-agents/conversation-api) | Conversation lifecycle, polling, messages, attachments, query results, and version 2 serialized definitions. |
| [Test and monitor a Genie Agent](https://docs.databricks.com/aws/en/genie-agents/monitor) | Chat and Agent benchmark modes, evaluation notes, independent conversations, and alternate question phrasings. |
| [Declarative Automation Bundle resources](https://docs.databricks.com/aws/en/dev-tools/bundles/resources) | Native `resources.genie_spaces`, direct deployment engine, `.geniespace.json` `file_path`, warehouse, parent path, and permissions. |
| [GitHub Actions workload identity federation](https://docs.databricks.com/aws/en/dev-tools/auth/provider-github) | Secretless `github-oidc` authentication using `DATABRICKS_HOST` and `DATABRICKS_CLIENT_ID`. |
| [Unified authentication environment variables](https://docs.databricks.com/aws/en/dev-tools/auth/env-vars) | Supported Databricks authentication types and environment-variable names used by the CLI and SDK. |

### Databricks-owned GitHub repositories

| Repository or file | What it was used to verify |
|---|---|
| [databricks/databricks-agent-skills](https://github.com/databricks/databricks-agent-skills) | Installed official skill source and Databricks workflow guidance. |
| [Create Genie Agent skill reference](https://github.com/databricks/databricks-agent-skills/blob/main/skills/databricks-genie-agents/references/create-genie-agent.md) | Structured-context priority, qualified SQL, column configuration, join/snippet shapes, review gates, and local-versus-workspace validation boundaries. |
| [databricks/cli](https://github.com/databricks/cli) | Unified CLI project used for bundle schema inspection and Genie/DAB command support. |
| [databricks/setup-cli](https://github.com/databricks/setup-cli) | Official GitHub Action used by the deployment workflow to install the Databricks CLI. |
| [databricks/bundle-examples](https://github.com/databricks/bundle-examples) | Official bundle layout and deployment examples used as a secondary DAB reference. |

### Local CLI verification

- Installed CLI: `Databricks CLI v1.17.0`.
- `databricks bundle schema -o json` confirmed `resources.genie_spaces` with `file_path`,
  `serialized_space`, `warehouse_id`, `title`, `description`, `parent_path`, and `permissions`.
- The schema confirms that the direct deployment engine is supported and is the correct engine for
  this native Genie resource.
- No workspace profile, workspace API, bundle validation, or deployment was invoked while performing
  these local checks.

## Assumptions requiring confirmation

- The approved raw-table source set or replacement governed Metric View exists in both environments.
- Customer and target sources are optional.
- Grain, keys, joins, calendars, measures, return/discount rules, cancellation rules, currency handling, and classifications are not yet approved.
- A focused Agent with four to six sources is appropriate. Current official guidance recommends starting with five or fewer sources and documents a 50-source limit; recheck the current limit before deployment.
- Production approval will be enforced through both the protected GitHub environment and the CLI guard.
- SDK and Genie API shapes will be revalidated against current official documentation before the first deployment.
