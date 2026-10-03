# Sales Genie Project Conversation Transcript

This document records the visible user–assistant conversation that produced and refined this
repository. Hidden system/developer instructions and raw tool logs are excluded. Earlier sections are
historical and intentionally preserve decisions that were later superseded; the latest sections and
the root `README.md` describe the current implementation.

> **Current-design notice:** Historical sections below mention four-to-six sources, dimensions,
> joins, and earlier deployment choices. Those statements are not current requirements. The present
> design permits exactly one logical `sales_fact` source—one denormalized table/view or one governed
> Metric View—and prohibits Genie join specifications. The root `README.md`, `prompt.md`, and Section
> 16 of this transcript are authoritative for the current design.

## 1. Initial project request

### User

Create a production-quality, source-controlled Databricks Genie Agent project for sales analysis using the installed official Databricks skills, especially Databricks Core, Genie Agents, Data Discovery, Unity Catalog, DBSQL, Python SDK, and DABs only where officially supported.

The user specified that no Databricks workspace was available. Everything had to be generated and tested locally without authentication, workspace API calls, resource creation, deployment, invented IDs, invented schemas, or fabricated API responses. The project needed separate dev/prod configuration, configurable tables and semantics, Genie instructions and examples, lifecycle scripts, tests, evaluation questions, CI/CD, least-privilege documentation, and explicit workspace-deferred checks.

### Assistant

Implemented a local source-controlled project with:

- Independent development and production configuration
- Unity Catalog table mappings and semantic placeholders
- Genie `serialized_space` version 2 generation
- SDK-authenticated lifecycle tooling for future use
- Separate ignored Agent state files
- Production approval, backup, placeholder, and separation guards
- A 21-question business evaluation dataset
- GitHub Actions validation and protected deployment templates
- Permission and workspace smoke-test documentation
- No unsupported native DAB Genie resource

Initial verification reported 15 passing tests, successful linting, configuration validation, dev/prod separation, dry-run payload generation, and no Databricks connection or deployment.

## 2. Mandatory and optional files

### User

What are all mandatory files and folders, and what are all optional?

### Assistant

Explained that the application package, environment configuration, semantics, instructions, evaluation dataset, and tests were mandatory for the implemented workflow. The `scripts/` wrappers, documentation, CI workflow, and human-readable table contract were optional at runtime but recommended.

Also explained that `state/`, `backups/`, and `exports/` are generated folders, while virtual environments, caches, build outputs, and package metadata must not be committed.

Confirmed that `databricks.yml` was not required because the project was not using a confirmed native Genie Agent bundle resource.

## 3. Data, instructions, and examples

### User

This folder contains files for Data, Instructions / General Instructions, and Examples so that Genie provides accurate responses.

### Assistant

Mapped the repository into three Genie context areas:

- Data: environment mappings and semantic definitions
- General instructions: ambiguity, safety, date, security, and response behaviour
- Examples: sample questions and evaluation cases

Identified a design gap: evaluation cases were not Genie SQL examples, and sample questions were still hard-coded in Python. Recommended separating data, instructions, examples, and evaluations.

## 4. Missing SQL examples

### User

Not able to see SQL examples.

### Assistant

Acknowledged that no visible `example_question_sqls` file existed and added a dedicated SQL examples configuration containing four read-only placeholder examples:

- Total sales yesterday
- Monthly sales trends
- Top-selling products
- Current year versus prior year

Connected these examples to the generated Genie payload under `instructions.example_question_sqls`.

Explained that every physical identifier remained a placeholder and that each query must be completed, tested against the target SQL warehouse, approved, and marked `approved` before deployment. Deployment validation was updated to reject unresolved or unapproved SQL examples.

Verification then reported 16 passing tests, successful linting and validation, and all four examples in the dry-run payload.

## 5. Folder redesign

### User

As you said above, redesign the folder structure by adhering to Databricks skills.

### Assistant

Redesigned configuration into:

```text
config/
├── environments/
│   ├── dev.yml
│   └── prod.yml
├── data/
│   ├── README.md
│   ├── tables.yml
│   └── semantics.yml
├── instructions/
│   ├── README.md
│   ├── general_instructions.md
│   └── text_instruction_justification.md
└── examples/
    ├── README.md
    ├── sample_questions.yml
    └── sql_examples.yml

evaluations/
└── sales_questions.yml
```

The separation was explained as:

- `environments/`: workspace and deployment mappings
- `data/`: structured source and semantic context
- `instructions/`: global behaviour that cannot be encoded structurally
- `examples/`: content deliberately taught to Genie
- `evaluations/`: independent test material kept separate to prevent benchmark leakage

Sample questions were removed from Python and externalised. All source paths, tests, workflow commands, and README references were updated. Deployment validation began requiring approved sample questions and SQL examples.

Verification reported 17 passing tests, successful linting and environment validation, plus a dry-run payload with four sources, five sample questions, four SQL examples, one text instruction, and three joins.

## 6. Redesigned files not visible in the IDE

### User

I am not seeing this redesign in my project folder `sales_genie`.

### Assistant

Verified that the redesigned files physically existed under:

```text
/home/raghava/projects/dbx_genie_prj/sales_genie/config
```

Explained that the open tabs referenced deleted old paths, indicating a stale IDE explorer. Mapped old paths to new paths and advised refreshing or reloading the IDE window.

### User

I am not able to see this redesign structure in the folder.

### Assistant

Verified the real filesystem path, Git worktree, directory metadata, and complete configuration listing. Confirmed the redesign existed on disk and advised:

1. Close stale tabs.
2. Refresh the file explorer.
3. Use **Developer: Reload Window** if necessary.
4. Confirm the workspace root is `/home/raghava/projects/dbx_genie_prj/sales_genie`.

## 7. README update

### User

Update the README document properly.

### Assistant

Rewrote the root README to document:

- Project status and local-only constraints
- Genie Agent purpose and terminology
- Redesigned folder structure
- Content included in the Agent payload versus governance and evaluation content
- Installation and local validation
- Semantic and SQL example approval
- Authentication and lifecycle commands
- Dev/prod separation
- State, export, backup, import, and rollback
- Evaluation, CI/CD, permissions, and promotion
- Deferred workspace smoke tests
- Python SDK and DAB design choices
- Assumptions requiring confirmation

Verification reported valid paths and commands, 17 passing tests, successful Ruff linting, and a clean diff check.

## 8. Whether `databricks.yml` is required

### User

Does this folder require a `databricks.yml` file?

### Assistant

Explained that `databricks.yml` is not required because the project uses standalone Python SDK commands:

```bash
sales-genie deploy-dev
sales-genie deploy-prod --approve-prod
```

Explained that `databricks.yml` becomes relevant only if supported bundle resources—such as a Job, pipeline, dashboard, or app—are added. Warned against inventing an unsupported `resources.genie_agents` block and recommended checking current support with:

```bash
databricks bundle schema
```

## 9. Deployment frequency

### User

One-time deployment only; an enhanced version may be deployed once every week.

### Assistant

Explained that neither one-time SDK deployment nor GitHub Actions scheduling requires `databricks.yml`. Recommended that any weekly process validate, test, evaluate, preview, and back up, but deploy only when an approved change exists.

### User

It is mostly a one-time deployment; later, bug fixes may be deployed only five or six times over six months.

### Assistant

Recommended keeping the existing on-demand release model instead of adding a recurring schedule or Databricks Job.

Recommended flow:

```text
Make configuration/code change
  → open pull request
  → run local validation and tests
  → deploy to development
  → run smoke tests and business evaluation
  → obtain production approval
  → back up production Agent
  → update production
  → run post-deployment smoke tests
```

Suggested versioning such as:

```text
v1.0.0  Initial production deployment
v1.0.1  SQL example correction
v1.0.2  Instruction or synonym fix
v1.1.0  New approved measure or data source
```

Concluded that deployment should remain manual, approved, versioned, tested, and backed up, with no DAB required.

## 10. Transcript request

### User

Provide the entire chat—our conversation—as an `.md` file.

### Assistant

Created this transcript at:

```text
docs/conversation-transcript.md
```

The transcript includes the visible user–assistant conversation and excludes hidden instructions and raw tool logs.

## 11. Native bundle and current-reference redesign

### User

Requested a final production-quality design aligned with the current Databricks reference sites.

### Assistant

Rechecked the installed CLI and official documentation, then adopted native Declarative Automation
Bundles as the primary deployment mechanism because current CLI schema supports
`resources.genie_spaces` with `bundle.engine: direct`. The Python SDK utilities remained for
inspection, conversations, export/import, smoke testing, and an explicitly legacy lifecycle path.

The repository was expanded to include deterministic serialized-space v2 generation, typed bundle
targets, SQL expressions, five teaching examples, benchmark promotion controls, stricter validation,
and manual protected dev/prod workflows.

## 12. Full script and reference audit

### User

Asked to verify the entire implementation against the reference sites and then requested an
explanation of the three highest-severity findings.

### Assistant

Confirmed that tests and lint passed but identified three design gaps:

1. Metric Views could not be represented separately from tables.
2. Cross-environment imports could retain development catalog references.
3. Environment comparison did not enforce the intended promotion topology.

The audit also confirmed that the official current limit is 50 sources and that the native direct
bundle resource matches the installed Databricks CLI 1.17.0 schema.

## 13. Catalog-only promotion topology

### User

Clarified that development and production use different catalog names while schema names, table
names, and Metric View names remain the same.

### Assistant

Refined the environment contract accordingly: source type, schema, and object name must remain
aligned, while only the catalog component changes. Hosts, profiles, warehouses, and identities may
be shared when that is the explicitly approved workspace topology. Agent IDs, bundle targets, state,
generated artifacts, approvals, and permissions remain environment-specific.

## 14. High-priority fixes

### User

Requested implementation of the fixes.

### Assistant

Implemented:

- `source_type: table | metric_view` in the logical source contract.
- Separate `data_sources.tables` and `data_sources.metric_views` serialization.
- Source descriptions in the generated payload.
- Catalog-only import validation and remapping across complete identifiers and embedded SQL,
  including fully backtick-quoted identifiers.
- Rejection of unknown, missing, schema-drifted, object-drifted, or type-drifted imported sources.
- Dev/prod comparison enforcing different catalogs with matching logical sources, schemas, and object
  names.
- Updated unit coverage and design documentation.

Verification completed with 40 passing tests, successful Ruff linting, successful dev/prod local
validation, successful environment comparison, and a production import dry run that remapped all
development source identifiers to the production catalog. No workspace API call or deployment was
performed.

## 15. Markdown documentation audit

### User

Asked whether every Markdown file was current and then requested updates.

### Assistant

Audited all Markdown files and aligned the living documentation with typed sources, the catalog-only
promotion contract, DAB Agent-ID resolution, safe import behavior, Metric View boundaries, workspace
smoke-test terminology, and the approved shared-infrastructure option. This transcript was extended
without rewriting its historical sections.

## 16. Single-source redesign and validation hardening

### User

Requested that the copied project use a single source before changing its Git remote, then requested
a bug review, fixes, and complete documentation alignment.

### Assistant

Converted the current design to exactly one logical source named `sales_fact`. The configured object
is either one denormalized table/view or one governed Metric View containing the product, store, date,
customer, target, and measure columns needed by supported questions. Removed separate dimension and
target source mappings, removed SQL joins, and prohibited authored or serialized join specifications.

Hardened validation so the source contract and serialized payload require exactly one source,
unresolved `${...}` template variables fail resolution, and `join_specs` are rejected. Corrected the
aligned current/prior-year SQL example, metadata examples, evaluation wording, tests, and all living
documentation. The Git remote now points to `RAGHAVA2021/dbx_genie_single_file`.

Local verification completed with 43 passing tests, successful Ruff linting, syntax parsing,
development and production configuration validation, environment comparison, and generated dev/prod
payloads containing one source and zero join specifications. No Databricks workspace operation or
deployment was performed.
