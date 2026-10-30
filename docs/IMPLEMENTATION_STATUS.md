# Insyvera implementation and verification status

Updated: 27 October 2026.

**Result:** a working, tested local application with the complete synthetic research/analytics/reporting journey. **Release state:** local implementation verified; full Docker infrastructure and real-model release gates remain unverified. No cloud deployment, remote Git push, or v1.0 release tag was performed.

## Verified evidence

| Check | Actual result |
|---|---|
| Python unit/API/security/resilience tests | **23 passed**, 20.13 seconds |
| Chromium browser acceptance | **2 passed**, 30.1 seconds |
| Synthetic evaluation suite | **5/5 cases passed** through the browser |
| React/TypeScript production build | Passed |
| Python Ruff lint | Passed |
| Compose configuration validation | Passed with generated local credentials |
| Frontend npm audit | 0 reported vulnerabilities |
| Git whitespace check | Passed |
| Local backup/restore | Hash-verified round-trip test passed |
| Cancellation/recovery | Active-node cancellation race, busy resume, checkpoint resume, and duplicate-run checks passed |
| Storage outage/deletion | Logical source removal and retryable object cleanup test passed |

Backend machine-readable results: [backend-results.xml](verification/backend-results.xml). Product screenshots are under [screenshots](screenshots/). The final browser run exercised actual API/React interactions and downloaded a real PDF; it did not use a fake API.

### Commands run

```powershell
.\.venv\Scripts\python.exe -m ruff check apps/api tests
.\.venv\Scripts\python.exe -m pytest -q --tb=short --junitxml=docs/verification/backend-results.xml
npm run build
npm run test:e2e
npm --prefix apps/web audit --json
docker compose config --quiet
git diff --check
```

The full browser suite used Chromium, the local API, and the actual Vite app. It created synthetic private accounts, imported all formats, ran the canonical investigation, opened source/cell views, generated charts, saved/edited/exported reports, ran evaluations, checked calculator behavior, and verified mobile overflow/navigation.

### Exact acceptance calculations

| Metric | Independently expected | Computed |
|---|---:|---:|
| Income | 84000 | 84000 |
| Expenses | 18000 | 18000 |
| Income minus recorded expenses | 66000 | 66000 |
| Reported income mismatch | 500 | 500 |
| Gift spending | 570 | 570 |
| Gift budget | 500 | 500 |
| Gift budget overrun | 70 | 70 |

Additional tests check decimal 0.1 + 0.2 = 0.3, merged cells, absent formula caches, duplicate/null profiles, safe filters/joins/correlation/trends, cleaning previews, all four chart types, exact analysis replay, exported document readability, source version diffs, collections, revoked access, and unsafe tool/upload rejection.

### Bounded local performance sample

40 retrieval requests, concurrency 4, seven synthetic sources, lexical retrieval:
- p50: 54.22 ms
- p95: 62.44 ms
- maximum: 76.54 ms

This is a small local sample. It does not establish production capacity, large-corpus latency, model-inference speed, or an SLA.

## Roadmap coverage

| Sprint | Implemented behavior | Verification boundary |
|---:|---|---|
| 0 | Repository, locked dependencies, developer commands, lint/build/tests, CI definitions, documentation | Local checks pass; remote CI has not run |
| 1 | FastAPI, SQLAlchemy, migrations, readiness, PostgreSQL/pgvector/Redis/MinIO Compose | Local runtime tested; real Compose services not started |
| 2 | Registration/login/logout, expiring sessions, workspaces, collections, audit and isolation | API and browser verified |
| 3 | All six format families, immutable originals/versions, previews, source locations, reprocess/delete | API and browser verified; object-store outage recovery tested locally |
| 4 | Structural chunks, embedding adapters, dimension/model metadata, reindex, pgvector/HNSW schema | Local chunking and mocked embedding contracts pass; real provider/index integration pending |
| 5 | BM25 fallback, PostgreSQL FTS + vector rank fusion, scoped filters and scores | Local retrieval verified; PostgreSQL execution pending |
| 6 | Cited extracts, optional model synthesis, missing-answer abstention, sources/history/SSE | Extractive mode verified; real model inference pending |
| 7 | Sheet/cell/formula/cache extraction, null/type/duplicate/anomaly profiles | Verified with demo and edge fixtures |
| 8 | Decimal calculations, aggregation/filter/join/statistics/trend/correlation, aligned tax reconciliation | Exact independent tests pass |
| 9 | Separate allowlisted operation process, clean environment, input/time bounds, provenance; optional sandbox image | Windows process execution tested; Linux resource/container boundary not executed here |
| 10 | Saved/replayable analyses, bar/line/histogram/scatter, underlying records and CSV/image export | API/browser verified; chart library lazy-loaded |
| 11 | LangGraph nodes, per-run durable checkpoints, cancellation, locks, resume and budgets | Checkpoint and Windows cancellation-race tests pass |
| 12 | Mixed-source investigation, comparison tables, scoped metrics, limited textual contradiction flags | Canonical synthetic investigation passes |
| 13 | Evidence statuses, unavailable-source checks, report editing/versions/exports | API/browser verified, including stale-edit rejection |
| 14 | Calculator, approved HTTPS retrieval, SSRF controls, source/model separation | Calculator/disabled-policy and URL validation tested; enabled real external fetch not exercised |
| 15 | Five labeled cases, separate metrics, history/configuration and custom experiments | Five-case local suite passes; broad real-model evaluation pending |
| 16 | Permission/upload/injection/operation/queue/lock controls, local backup/restore, traces/logs, bounded benchmark | Local tests pass; full infrastructure outages/restarts/restore and independent audit pending |
| 17 | Full packaging, startup/verify/backup scripts, README/API/security/architecture and screenshots | Packaging/config validated; clean full-stack release rehearsal pending |

## Intentional boundaries

- Arbitrary generated Python is unsupported. The implemented analysis interface accepts reviewed operations, as recommended by the roadmap's deterministic-first policy.
- No OCR service or universal Excel formula recalculation.
- Automatic dataset selection/reconciliation uses bounded, disclosed conventions. It is not an unrestricted autonomous analyst for arbitrary schemas.
- Textual contradictions are potential conflicts, not authoritative resolutions.
- Citation existence and exact quote checks do not prove semantic entailment.
- Model usage costs are marked not metered rather than fabricated.
- Stored/editable report prose is not silently re-certified after user edits.
- Deletion removes authorized metadata immediately. Original bytes are purged through durable cleanup records; failed cleanup can be retried, and Compose's periodic worker retries it.
- Windows operation limits differ from Linux resource controls; an ordinary subprocess is not a hostile-code jail.

## Remaining release gates

Docker Desktop's Linux engine was unavailable in this session. Compose parsing succeeded, but the API/database/worker/storage containers could not be run. The following remain **unverified**, not silently marked complete:

1. Actual PostgreSQL pgvector/HNSW/FTS, MinIO and Redis/Celery integration.
2. Clean Docker image builds/startup on fresh volumes and a clean clone.
3. Real Ollama or hosted-model inference and embedding smoke tests.
4. Linux executor/container resource and network-isolation checks.
5. Infrastructure backup/restore and crash/outage rehearsal.
6. External tool retrieval with the feature explicitly enabled.
7. Cloud deployment, HTTPS/domain configuration and production access policy, to be done together.

See [operations](OPERATIONS.md) for concrete commands and the deployment-day checklist. Do not tag v1.0 or claim a fully production-verified release until those gates pass.

## GitHub Actions repair — 30 October 2026

The first uploaded run passed the backend job but failed web startup and infrastructure image retrieval.

- Windows Playwright startup now uses `infrastructure/scripts/python.cjs`, which launches the absolute virtual-environment Python executable with `shell: false`. Both Playwright and `npm run test:api` use this launcher. CI refuses to reuse pre-existing web/API servers, so it exercises startup on each run.
- MinIO no longer pulls the unavailable `minio/minio` image. Compose builds the server from official source commit `07c3a429bfed433e49018cb0f78a52145d4bedeb`, corresponding to the same previously selected release. A MinIO readiness check gates API startup. Infrastructure CI allows 30 minutes for the initial source build.
- The dependency installer paths in the Windows workflow remain PowerShell commands; the reported failure was in Playwright's separate command-shell startup.

The source-build change still needs execution in a working Docker environment. It does not, by itself, establish a passing infrastructure job. Push these changes and inspect the new GitHub Actions run; re-running the old commit does not include the repair.

Repair checks completed locally: both launcher regression tests passed, including invocation from another working directory and exit-code propagation; a Windows `cmd.exe` launch with a script path containing spaces passed; the production web build, JavaScript syntax checks and `docker compose config --quiet` passed. The new launcher checks also run before the web build in CI. Full backend/browser rerun attempts stalled in the restricted local execution environment and were interrupted; they are not recorded as new passes. Docker's engine was unavailable, so source-image build and full infrastructure verification remain pending.

### Celery readiness follow-up — 30 October 2026

The next user-provided CI log reached the Celery check after the database/vector/FTS, object-storage and Redis checks, then failed the single five-second worker ping. The worker previously had no Compose healthcheck, allowing `--wait` to finish with a running but not-yet-ready worker container. That readiness gap is corrected; whether the reported worker was only starting or had a runtime failure still requires its service logs.

- Workers now have unique `insyvera@hostname` names and a targeted Celery-pong healthcheck. Compose waits for worker health.
- The infrastructure verifier uses bounded readiness retries, then requires a real queued health task to return its unique nonce through the result backend. Non-responses and wrong replies still fail the check; a scheduler ping cannot substitute for a worker response.
- CI bounds the infrastructure verification step and includes container states in failure diagnostics.
- **Eight readiness/task regression tests passed locally (6.82 seconds)**, covering delayed startup, transient broker errors, readiness deadlines, rejecting scheduler/error replies, targeting the current container, rejecting other-worker replies, and the health task payload. The eighth test starts a real Celery worker using the in-memory broker, requires its pong, and sends a health task through its consumer/result backend. Ruff, Compose configuration and worker-healthcheck wiring checks passed. This local worker test does not substitute for Redis/Docker integration.

The local Docker engine remains unavailable. The new worker healthcheck and broker-to-worker task round trip are implemented but await verification in the next GitHub Actions run. This is not a claimed live infrastructure pass.
