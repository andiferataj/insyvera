# INSYVERA — Complete Development Roadmap

> **Agentic Research & Data Intelligence Platform**  
> **Tagline:** *From raw data to verified insight.*  
> **Project #3 · Portfolio-scale product · Version 1.0 plan**  
> **Status:** Roadmap / planned; features are not implemented merely because they appear here.

## 1. Product Vision and Scope

Insyvera is a locally runnable AI research and automated data analysis platform. Users upload documents and datasets, ask complex questions in natural language, and receive transparent, reproducible findings with source citations, calculation provenance, and explicit uncertainty.

It combines document intelligence, hybrid search, agentic research, deterministic and controlled Python data analysis, visualization, evidence verification, report generation, and systematic AI evaluations. It is **not** merely a “chat with PDFs” application.

**Target users:** researchers, developers, students, analysts, consultants, and small teams investigating mixed documents and datasets.

**Core promise:** *Upload your files, ask what you want to know, and receive an analysis you can inspect, reproduce, and verify.*

**Working product name:** Insyvera. Final commercial branding requires separate trademark, domain, and name availability verification.

### Six modules

1. **Insyvera Library:** upload, organize, preview, version, reprocess, and delete files; parse PDF, DOCX, XLSX, CSV, Markdown, and TXT with provenance.
2. **Insyvera Research:** question answering, source discovery, document comparisons, contradiction detection, multi-step investigations, and cited summaries.
3. **Insyvera Analytics:** profile and clean datasets, compute statistics, reconcile figures, identify anomalies, generate interactive charts, and save reproducible analyses.
4. **Insyvera Agents:** stateful research planning, retrieval, analysis, synthesis, verification, checkpoints, tool calls, and run monitoring.
5. **Insyvera Evidence:** trace claims to precise passages, PDF pages, worksheets/cells, and executed calculations; flag missing or unsupported evidence.
6. **Insyvera Lab:** evaluate retrieval, citation validity, numerical correctness, groundedness, abstention, model configurations, latency, and approximate cost.

### Three operating modes

- **Research Mode:** textual documents, evidence extraction, comparisons, requirements, and citations.
- **Data Analysis Mode:** structured spreadsheets/CSV, cleaning, calculations, statistics, and visualizations.
- **Deep Investigation Mode:** coordinated cross-document research plus calculations, verification, and reports.

The UI can recommend a mode, but a direct question should use a cheap, fast path rather than launching unnecessary agents.

## 2. Canonical Example: Three Uploaded Files

**Inputs (fictional, reproducible demonstration data):**

- `taxes_2026.xlsx` — income, expenses, categories, formulas, deductions.
- `tax_report_2026.pdf` — tax summary and reported figures.
- `christmas_gifts.xlsx` — purchases, recipients, prices, and budget.

**User asks:** “Compare my tax records, identify mismatches, analyze Christmas spending, and produce a report with recommendations.”

**Required behavior:**

1. Identify relevant files, tables, sheets, cell ranges, PDF pages, reporting periods, and currencies.
2. Extract and normalize numeric and textual data without changing source files.
3. Profile missing values, mixed types, formula results, units, and possible duplicates.
4. Calculate figures using executed Python or vetted deterministic functions—not invented LLM arithmetic.
5. Compare aligned income, expense, and other tax fields; report discrepancies without assuming which source is correct.
6. Analyze gift spending by recipient, category, date, and budget.
7. Generate meaningful charts and a discrepancy table.
8. Validate calculations and link findings to source cells/pages and analysis artifacts.
9. Produce a saved report with evidence, assumptions, limitations, and export options.
10. Abstain or ask for missing information if a claim cannot be supported. In particular, taxable income is not automatically available cash.

**Acceptance dataset:** deliberately include a known numerical discrepancy, a seeded contradiction, a missing-answer question, and a few data-cleaning edge cases to test the system end to end.

## 3. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React, TypeScript, Vite | Web application |
| UI | Tailwind CSS, shadcn/ui | Design system |
| Backend | Python, FastAPI, Pydantic | API and request validation |
| Agent orchestration | LangGraph | Stateful workflows and checkpoints |
| Primary database | PostgreSQL | Application metadata and records |
| Vector retrieval | pgvector | Semantic similarity search |
| Keyword retrieval | PostgreSQL full-text search | Exact-term and hybrid search |
| ORM/migrations | SQLAlchemy, Alembic | Persistence and schema changes |
| Queue and jobs | Celery, Redis | Parsing, indexing, reports, evaluations |
| Files/artifacts | MinIO (S3-compatible) | Originals and generated outputs |
| Spreadsheet processing | pandas, NumPy, openpyxl | Tables, profiles, transformations |
| Statistics | SciPy, statsmodels | Quantitative analysis |
| Charting | Plotly | Interactive charts |
| Document parsing | PyMuPDF, python-docx, openpyxl | Text, page, table, and sheet extraction |
| Models | Ollama and configurable hosted providers | Language and embedding inference |
| Telemetry | OpenTelemetry | Application/agent traces and metrics |
| Backend testing | pytest | Unit/integration tests |
| Browser testing | Playwright | End-to-end verification |
| Deployment | Docker Compose | Reproducible local stack |
| CI | GitHub Actions | Automated quality gates |

**Version strategy:** At Sprint 0, select compatible stable versions, lock dependencies, record model IDs and embedding dimensions, and test reproducibility. Do not casually upgrade packages mid-sprint.

**Model strategy:** support a local Ollama mode without a paid API requirement (hardware dependent), plus an optional paid hosted-model configuration. The application itself should still boot without provider API keys.

## 4. Architectural Principles

Use a **modular monolith FastAPI backend with separate worker processes** to keep the system easy to develop locally while preserving domain boundaries. Avoid unnecessary microservices; distributed systems are already emphasized by other portfolio projects.

```text
React / TypeScript / Vite
      |
FastAPI (auth, workspaces, library, research, analytics, evidence, eval)
      |
      +-- Document ingestion workers ----> MinIO originals/artifacts
      +-- Hybrid retrieval -------------> PostgreSQL + pgvector/FTS
      +-- LangGraph research engine ----> LLM / embeddings (Ollama or provider)
      +-- Controlled analytics ---------> isolated analysis executor
      +-- Evaluation runner ------------> datasets and metrics
      +-- Redis + Celery ---------------> async jobs, retries, cancellation
      +-- OpenTelemetry ----------------> traces and observability
```

### Agent roles

| Role | Responsibility |
|---|---|
| Planner | Split complex objectives into bounded, explicit tasks |
| Retriever | Fetch only authorized files/passages/tables |
| Data Analyst | Select deterministic tools and request controlled calculations |
| Synthesizer | Merge supported findings into answers and reports |
| Verifier | Inspect numeric outputs, citation support, contradictions, missing evidence |
| Supervisor | Coordinate routing, limits, retries, approvals, checkpoints, and failures |

Agent roles can be LangGraph nodes, not six simultaneous chatbots. Use deterministic programmatic logic wherever appropriate. Expose workflow stages, tool outcomes, and supporting evidence, **not purported hidden model reasoning**.

### Retrieval and citation policy

1. Extract source text and tables with location metadata.
2. Chunk by structure while preserving document/version/page/sheet/range IDs.
3. Embed chunks with versioned model metadata.
4. Combine vector search, full-text search, metadata filters, and optional reranking.
5. Enforce workspace permissions **inside** retrieval queries.
6. Require citations to resolvable source locations, and validate their support.
7. Treat absent evidence as uncertainty or abstention—not as permission to fabricate.

### Safe analysis execution

- Prefer predefined, tested calculation functions first.
- Never execute model-generated arbitrary Python in the FastAPI process.
- For advanced requests, use isolated, non-privileged execution with input allowlists, explicit resource/time limits, restricted filesystem access, disabled network by default, and a minimal package environment.
- Capture input versions, program/tool versions, code or operation definitions, stdout/stderr, computed outputs, and provenance.
- Separate read-only analysis from external or state-changing tools; use explicit user approvals where needed.
- Maintain original uploads as immutable files; produce derived artifacts separately.
- Threat-model the execution boundary and test it; containers alone are not a complete security guarantee.

## 5. Repository Layout

```text
insyvera/
├── apps/
│   ├── web/
│   │   ├── src/
│   │   │   ├── app/
│   │   │   ├── components/
│   │   │   ├── features/{auth,library,research,analytics,evidence,agents,evaluations}/
│   │   │   ├── hooks/
│   │   │   └── lib/
│   │   └── tests/
│   ├── api/
│   │   └── app/
│   │       ├── api/
│   │       ├── core/
│   │       ├── db/
│   │       ├── models/
│   │       ├── schemas/
│   │       └── modules/{identity,workspaces,documents,retrieval,research,analytics,evidence,evaluations}/
│   ├── worker/
│   └── sandbox/
├── packages/
│   ├── contracts/
│   ├── agents/
│   ├── ingestion/
│   ├── retrieval/
│   ├── analytics/
│   └── evaluation/
├── tests/{unit,integration,e2e,security,benchmarks}/
├── datasets/{demo,evaluation}/
├── infrastructure/{docker,observability,scripts}/
├── docs/{architecture,decisions,sprints}/
│   └── IMPLEMENTATION_STATUS.md
├── .github/workflows/
├── docker-compose.yml
├── .env.example
├── README.md
└── Makefile
```

The directory layout is a target, not a requirement to generate empty abstractions on day one. Introduce modules when they have real functionality.

### Key database tables

| Domain | Tables |
|---|---|
| Accounts | `users`, `sessions`, `workspace_members` |
| Workspaces | `workspaces`, `collections`, `workspace_settings` |
| Documents | `documents`, `document_versions`, `document_pages`, `document_chunks` |
| Structured data | `datasets`, `dataset_columns`, `dataset_profiles` |
| Search | `chunk_embeddings`, `index_jobs` |
| Research | `research_runs`, `research_tasks`, `agent_steps` |
| Analysis | `analysis_runs`, `execution_artifacts`, `analysis_results` |
| Evidence | `claims`, `evidence_links`, `verification_results` |
| Reports | `reports`, `report_versions`, `exports` |
| Evaluation | `evaluation_datasets`, `test_cases`, `evaluation_runs`, `evaluation_scores` |
| Security | `audit_events`, `api_credentials`, `access_grants` |

Design for UTC timestamps, workspace ownership, file versioning, permission-scoped results, retention and deletion, reproducible model configurations, and idempotent jobs.

## 6. Full Sprint Plan (0–17)

**Planning estimate:** 20–30 weeks of focused part-time implementation, with variability from AI model performance, document parsing edge cases, and security work. A sprint is only finished when its exit criteria pass.

### Phase I — Foundation (Sprints 0–3)

#### Sprint 0 — Environment, Specification & GitHub (2–4 days)

**Build steps:**
1. Verify Python, Node, npm, Docker Desktop, Docker Compose, Git, and WSL2.
2. Create repository and root folder layout; initialize Git and `.gitignore`.
3. Pin Python/JS dependencies and add lockfiles.
4. Define MVP workflows, supported file constraints, initial schema, API conventions, and architecture decision records (ADRs).
5. Add linting, formatting, type checks, pre-commit hooks, initial tests, and CI.
6. Create `docs/IMPLEMENTATION_STATUS.md`, a file-fixture policy, and a README.

**Done when:** Fresh clone restores dependencies and initial lint/build/test checks succeed.  
**Suggested commit:** `chore: initialize insyvera monorepo`

#### Sprint 1 — FastAPI, Database & Docker Foundation (1 week)

**Build steps:**
1. Create FastAPI server with dependency injection, settings and health endpoints.
2. Configure PostgreSQL with pgvector, Redis and MinIO in Docker Compose.
3. Set up SQLAlchemy, Alembic migrations and seed/fixture infrastructure.
4. Add validation, centralized error responses, structured logging and OpenAPI docs.
5. Write real infrastructure integration tests and readiness checks.

**Done when:** API, database, queue and storage start and pass health checks.  
**Suggested commit:** `feat: implement backend foundation`

#### Sprint 2 — Accounts, Workspaces & Access Control (1 week)

**Build steps:**
1. Implement sign-up, sign-in, secure sessions, expiry and logout.
2. Create workspaces, memberships, collections and workspace settings.
3. Enforce ownership and resource-level permissions at API/database query boundaries.
4. Build React auth pages, navigation and workspace switcher.
5. Add audit events and test cross-workspace isolation.

**Done when:** Two users can use private workspaces without accessing each other's files or results.  
**Suggested commit:** `feat: add authentication and workspaces`

#### Sprint 3 — Uploads & Document Ingestion (2 weeks)

**Build steps:**
1. Add PDF, DOCX, XLSX, CSV, Markdown and TXT uploads with size/type/content checks.
2. Store immutable originals in MinIO with metadata, hashes and versions.
3. Parse document text, PDF pages, tables, worksheet names and spreadsheet cell locations.
4. Add asynchronous Celery ingestion jobs with status, retries, deduplication and failure messages.
5. Create file browsing, upload progress, preview and deletion/reprocessing UI.
6. Test malformed files, extraction failures and safe deletion.

**Done when:** Every supported demo format imports, previews, and retains source location information.  
**Suggested commit:** `feat: implement document ingestion pipeline`

### Phase II — Knowledge Intelligence (Sprints 4–6)

#### Sprint 4 — Chunking, Embeddings & Indexing (1–2 weeks)

**Build steps:**
1. Implement structure-aware chunking and source-location metadata.
2. Integrate a configurable embedding provider.
3. Create pgvector schema and indexes with model/version/dimension metadata.
4. Add background indexing, progress, retries and reindexing flows.
5. Remove stale indexes when document versions are deleted.
6. Add benchmark fixtures for known relevant passages.

**Done when:** Semantic search works and repeat indexing creates no duplicated active chunks.  
**Suggested commit:** `feat: add semantic document indexing`

#### Sprint 5 — Hybrid Search & Source Explorer (1–2 weeks)

**Build steps:**
1. Implement PostgreSQL full-text and pgvector search.
2. Merge rankings using weighted rank fusion; add optional reranker.
3. Filter by workspace, collection, file version, type, and metadata.
4. Build search UI with snippets, score explanations and source navigation.
5. Enforce permissions in every search path.
6. Measure retrieval recall against a small labeled dataset.

**Done when:** Known queries retrieve their expected passages at an agreed benchmark threshold.  
**Suggested commit:** `feat: implement hybrid knowledge retrieval`

#### Sprint 6 — Cited Question Answering (1–2 weeks)

**Build steps:**
1. Implement retrieval-grounded Q&A and streamed responses.
2. Store structured source references rather than fabricated citation numbers.
3. Build PDF-page navigation and worksheet/cell reference views.
4. Require abstention for insufficient evidence.
5. Add conversation history, source scoping and reference validation.
6. Test missing-answer questions, bad citations and permission bypass attempts.

**Done when:** Users can ask questions, open supporting evidence and get appropriately limited answers.  
**Suggested commit:** `feat: implement verifiable research answers`

### Phase III — Automated Data Science (Sprints 7–10)

#### Sprint 7 — Spreadsheet Intelligence & Data Profiling (1–2 weeks)

**Build steps:**
1. Extract tables, sheets, cell ranges, formulas and cached values.
2. Detect column types, dates, currencies, categories, nulls and duplicates.
3. Profile numeric distributions and suspicious values.
4. Expose cleaning assumptions and preview transformations.
5. Build dataset preview and data-quality UI.
6. Test merged cells, ambiguous headers, blank/formula cells, mixed units and missing cached results.

**Done when:** Tax and gift spreadsheets profile accurately and preserve provenance.  
**Suggested commit:** `feat: add structured data profiling`

#### Sprint 8 — Deterministic Analytics Engine (2 weeks)

**Build steps:**
1. Implement tested pandas/NumPy functions for filtering, joins, grouping and aggregation.
2. Add descriptive statistics, trend comparisons and transparent anomaly flags.
3. Implement reconciliation across structured spreadsheet and PDF table data.
4. Record input IDs, transformations, calculation definitions and outputs.
5. Add expected-answer fixtures and independent numerical tests.
6. Build comparison and discrepancy result views.

**Done when:** Tax totals, differences and gift spending match independently calculated expected values.  
**Suggested commit:** `feat: add reproducible analytics engine`

#### Sprint 9 — Safe Python Execution (2 weeks)

**Build steps:**
1. Design a restricted analysis-operation interface; keep most requests deterministic.
2. Implement isolated execution workers for advanced supported analysis code.
3. Set process/user permissions, resource limits, input allowlists, timeout and cancellation.
4. Disable network by default and keep user uploads read-only.
5. Record code/operation hashes, dependencies, logs and generated artifacts.
6. Test attempted filesystem/network access, resource exhaustion and tool misuse.

**Done when:** Authorized analyses reproduce correct results and prohibited actions fail safely.  
**Suggested commit:** `feat: introduce isolated analysis execution`

#### Sprint 10 — Charts, Dashboards & Saved Analyses (1–2 weeks)

**Build steps:**
1. Generate Plotly charts and validated summary statistics from computed data.
2. Implement tables, time-series, distributions, categories and comparisons.
3. Enable drill-down from chart summaries to underlying records.
4. Save analysis runs with parameters, assumptions and provenance.
5. Export datasets/charts (CSV/PNG where supported) and analysis summaries.
6. Test statistical and chart-data consistency.

**Done when:** Gift spending queries produce accurate interactive charts and saved analysis artifacts.  
**Suggested commit:** `feat: add analysis dashboards and charting`

### Phase IV — Agentic Research (Sprints 11–14)

#### Sprint 11 — LangGraph Orchestrator (2 weeks)

**Build steps:**
1. Define typed graph state for tasks, evidence, tool outputs, and budgets.
2. Implement Planner, Retriever, Data Analyst, Synthesizer, Verifier and Supervisor nodes.
3. Implement checkpoints, retry boundaries, cancellation and resume.
4. Route simple questions through a fast Q&A path.
5. Enforce maximum tool calls, tokens/compute, step count and runtime.
6. Test graph state recovery, timeouts, repeat execution and errors.

**Done when:** A research run can be interrupted and resumed without blindly repeating completed side effects.  
**Suggested commit:** `feat: implement agentic research orchestration`

#### Sprint 12 — Multi-File Investigation & Contradictions (2 weeks)

**Build steps:**
1. Support source selection across documents and datasets.
2. Extract comparison criteria and structured claims.
3. Build evidence and contradiction matrices.
4. Distinguish genuine conflicts from different scope, time, units or definitions.
5. Combine verified calculation artifacts with textual evidence.
6. Build the agent execution timeline and seed conflicting-document fixtures.

**Done when:** The tax/PDF/gifts question produces sourced discrepancies, correct calculations and justified conclusions.  
**Suggested commit:** `feat: add multi-source research intelligence`

#### Sprint 13 — Evidence Verification & Report Studio (1–2 weeks)

**Build steps:**
1. Represent material claims and supporting source IDs/calculation outputs.
2. Check citation existence, match and support; flag unsupported claims.
3. Build customizable report sections for financial analyses and research comparisons.
4. Implement save, edit, version, preview and export workflows.
5. Show assumptions, limitations, contradictory findings and unresolved questions.
6. Test deleted sources, invalid citations and unsupported claims.

**Done when:** A saved report contains traceable citations, reproducible calculations and appropriately flagged uncertainties.  
**Suggested commit:** `feat: add verification and report generation`

#### Sprint 14 — Permissioned Research Tools & Human Approval (1–2 weeks)

**Build steps:**
1. Register allowed tools with schemas and access policies.
2. Add optional authorized external web retrieval with timestamps and citations.
3. Implement safe calculator, table inspection and file-version comparison tools.
4. Require approvals for external retrieval where appropriate and for state-changing actions.
5. Audit tool calls, inputs, outputs, errors and approval state.
6. Test document/web prompt injection and untrusted tool-output handling.

**Done when:** Agents remain within permissions and cannot execute instructions embedded in untrusted source content.  
**Suggested commit:** `feat: add controlled research tools`

### Phase V — Evaluation, Hardening & Release (Sprints 15–17)

#### Sprint 15 — AI Evaluation Laboratory (2 weeks)

**Build steps:**
1. Create labeled Q&A, retrieval, citation, numerical and contradiction test datasets.
2. Implement retrieval recall and ranking metrics.
3. Score citation validity/support, arithmetic correctness, abstention and answer quality separately.
4. Record latency, model IDs, configuration versions and approximate inference cost.
5. Compare experiment runs for models, chunking, prompts and retrieval strategies.
6. Build evaluation history and regression dashboards.

**Done when:** Evaluation suites can run repeatably and reveal regressions instead of relying on chatbot impressions.  
**Suggested commit:** `feat: implement AI evaluation lab`

#### Sprint 16 — Security, Resilience & Performance (2 weeks)

**Build steps:**
1. Threat-model uploads, document access, prompt injection, generated analysis and secrets.
2. Test malicious files, oversized input, permission leaks and sandbox escape attempts.
3. Load-test concurrent ingestion and research workloads.
4. Test worker restarts, duplicate jobs, queue outages, cancelled work and model failures.
5. Verify data backup/restore, deletion and retention behavior.
6. Add OpenTelemetry traces, metrics and useful troubleshooting; resolve critical blockers.

**Done when:** Security/resilience tests pass and measurable load assumptions are documented, with no open critical findings.  
**Suggested commit:** `test: harden insyvera for release`

#### Sprint 17 — Local Release & Portfolio Packaging (1–2 weeks)

**Build steps:**
1. Prepare full application Docker Compose profiles and image builds.
2. Implement bootstrap, database migration, seed, health, reset and backup scripts.
3. Document Ollama model acquisition, optional provider configuration and hardware tradeoffs.
4. Validate clean-clone startup on Windows/WSL2 with fresh volumes.
5. Create user/developer docs, diagrams, example API calls, demo video and portfolio README.
6. Re-run the entire acceptance suite and tag `v1.0` only after verification.

**Done when:** A new reviewer can follow the README and run the complete demo locally.  
**Suggested commit:** `release: prepare insyvera v1.0`

## 7. Major Milestones

| Milestone | After sprint | User-visible capability |
|---|---:|---|
| **A — Document Intelligence** | 6 | Upload, search, ask source-grounded questions, open citations |
| **B — Automated Data Analysis** | 10 | Profile spreadsheets, reconcile values, calculate and chart |
| **C — Agentic Investigation** | 14 | Combine documents and computations in multi-step, controlled research |
| **D — Measured AI Quality** | 15 | Run benchmarks and compare research/model configurations |
| **E — Verified Local Release** | 17 | Clean local deployment, end-to-end demo, testing and docs |

## 8. Windows Local Development

### Prerequisite checks

Run in PowerShell:

```powershell
python --version
py -0p
node --version
npm --version
git --version
docker --version
docker compose version
wsl --status
```

Create the repository only if the directory does not already contain project work:

```powershell
cd C:\Users\PC\Projects
New-Item -ItemType Directory -Path insyvera -Force
cd insyvera
git init
git branch -M main
```

Do not overwrite or modify the existing Nexus or Velqora projects.

### Running modes

- **Development:** Run PostgreSQL/pgvector, Redis and MinIO with Compose; use Python/React hot reload; Ollama local or a configured hosted provider.
- **Full stack:** Compose brings up UI, API, worker(s), database, message queue, storage, and optional inference profile.

**Proposed development endpoint defaults (configurable):**

| Service | URL / host |
|---|---|
| React | `http://localhost:5173` |
| FastAPI | `http://localhost:8000` |
| OpenAPI docs | `http://localhost:8000/docs` |
| PostgreSQL | `localhost:5432` |
| Redis | `localhost:6379` |
| MinIO console | `http://localhost:9001` |
| Ollama optional | `http://localhost:11434` |

These are **planned**, not currently running. Avoid host-port collisions with Nexus and Velqora through Compose networks and configurable port mappings. Bind management endpoints locally and supply non-default local credentials via an untracked `.env` based on `.env.example`.

## 9. Testing Strategy and Release Gates

| Test suite | What it verifies |
|---|---|
| Unit | Parsers, transformations, statistics, rules and policy functions |
| Integration | PostgreSQL, pgvector, Redis, MinIO, Celery and migrations |
| API | Validation, errors, auth, permissions, streaming and status codes |
| E2E | Upload, search, research, charts, citations, reports and export |
| Agent | Routing, step budgets, state, checkpoints, retries and cancellation |
| Evidence | Resolvable citations and claim support |
| Numerical | Values match independently defined expected answers |
| Security | Tenant/workspace isolation, untrusted content, sandbox boundaries |
| Evaluation | Retrieval quality, citation correctness, abstention, model comparisons |
| Resilience | Duplicated jobs, outages, worker crashes and recovery |
| Performance | Ingestion time, queue delay, retrieval latency, analysis throughput |

Each sprint's status document records which tests actually ran, commands used, output summaries, unresolved defects, and whether its exit conditions passed. **Implemented**, **tested**, and **release-verified** are distinct statuses.

## 10. Complete v1.0 Acceptance Checklist

- [ ] A clean clone starts using documented setup steps.
- [ ] Users can create accounts, sign in and maintain private workspaces.
- [ ] PDF, DOCX, CSV, XLSX, Markdown and TXT upload and parse.
- [ ] Originals, versions, sheet/cell references and PDF page references are retained.
- [ ] Document search is hybrid and permission-scoped.
- [ ] Q&A returns navigable, accurate source citations.
- [ ] Missing or unsupported evidence causes abstention/qualification.
- [ ] Data profiling identifies missing values, types and potential anomalies.
- [ ] Spreadsheet/PDF figures can be reconciled with exact numeric calculations.
- [ ] Analyses are reproducible and retain input/tool/code provenance.
- [ ] Generated-code execution, where supported, is isolated and limited.
- [ ] Charts are interactive and based on validated data artifacts.
- [ ] LangGraph research can be cancelled and resumed safely.
- [ ] Multi-file investigations include coherent evidence comparisons.
- [ ] Reports can be saved, versioned, reviewed and exported.
- [ ] Agent tool permissions and approval gates are enforced.
- [ ] Evaluation benchmarks run consistently and produce separate quality metrics.
- [ ] Security, resilience, unit, integration and E2E tests pass.
- [ ] The README includes architecture, setup, troubleshooting, limitations and a guided demo.

### Final demonstration script

1. Start Insyvera locally from the documented Compose setup.
2. Create a user and workspace.
3. Upload synthetic `taxes_2026.xlsx`, `tax_report_2026.pdf`, and `christmas_gifts.xlsx`.
4. Request a tax reconciliation and gift-spending analysis.
5. Inspect numeric discrepancy tables and interactive charts.
6. Click through to a relevant PDF page and XLSX sheet/cell.
7. Inspect calculation inputs, transformations and outputs.
8. Review the multi-agent run stages, tool calls and failure behavior.
9. Generate, save, version and export a cited report.
10. Re-run research with another model/retrieval configuration.
11. Review the differences in Insyvera Lab.
12. Ask a deliberately unanswerable question and confirm appropriate abstention.

## 11. Per-Sprint Working Method

1. **Understand:** Explain the sprint goal, architecture and core concepts.
2. **Implement:** Supply complete files with exact paths—not disconnected snippets.
3. **Run:** Give Windows PowerShell commands and start the affected services locally.
4. **Test:** Execute relevant automated tests and independently check results.
5. **Fix:** Resolve failures before marking the sprint complete.
6. **Review:** Explain important functions, schema changes and design decisions.
7. **Document:** Update `docs/IMPLEMENTATION_STATUS.md` and any ADRs.
8. **Commit:** Push a meaningful tested commit to GitHub.

Maintain a changelog of design decisions, known issues, test evidence, and work left for the next sprint. Commit verified increments rather than a monolithic untested project dump.

## 12. Explicit Non-Goals and Limitations

- Not automatic tax filing, financial advice, or legal compliance certification.
- Not unrestricted web browsing, shell execution, or changes to uploaded originals.
- Not universal perfect parsing of every PDF, scan, formula, or proprietary file format.
- Scanned documents may need optional OCR and clear extraction-confidence warnings.
- Spreadsheet formulas may lack cached results; openpyxl does **not** itself recalculate arbitrary Excel workbooks. Handle missing formula values explicitly or add a compatible calculation/recalculation path.
- Citation verification improves auditability but does not mathematically guarantee truth.
- Docker alone does not guarantee secure execution of untrusted AI-generated code.
- Local model accuracy and performance vary with the selected model and computer hardware.
- Do not claim zero hallucinations, universal correctness, or enterprise-scale throughput without measured evidence.

## 13. GitHub and Portfolio Deliverables

The completed repository should include:

- Source code for frontend, API, workers and sandbox execution layer.
- Professional README with setup, screenshots and demo workflow.
- Architecture, data flow, trust boundary and LangGraph diagrams.
- API and database documentation.
- Versioned synthetic demo/evaluation datasets.
- Automated tests, evaluation reports and benchmark methodology.
- Security assumptions, limitations, threat model and safe analysis policy.
- Health checks, reset/seed/backup scripts and troubleshooting guidance.
- Screenshots or recording of full research and analysis flow.

**CV description (use only once verified):**

> **Insyvera — Agentic Research & Data Intelligence Platform**  
> *Python · LangGraph · FastAPI · PostgreSQL/pgvector · React · Docker*  
> Developed an AI-powered platform for multi-document research, automated quantitative analysis, verifiable citations, and reproducible reporting, incorporating stateful agent orchestration, hybrid retrieval, isolated Python execution, and systematic evaluation pipelines.

## 14. Immediate Next Step

**Begin Sprint 0.** Verify prerequisites on Windows; pin compatible versions; scaffold React, FastAPI, workers, Docker infrastructure and documentation; establish passing baseline builds and tests. Then progress sprint by sprint, keeping the three-file demonstration as the guiding end-to-end objective.

**Definition of fully functional:** the final acceptance script can be completed on a fresh local setup and the release test gates pass—not merely that files exist or a dashboard opens.