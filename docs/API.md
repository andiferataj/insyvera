# API guide

Interactive OpenAPI: http://127.0.0.1:8100/docs

All workspace routes require the HttpOnly session cookie and an authorized membership. Resource lookups are workspace-scoped. Unavailable or foreign resources return 404. Mutation requests enforce configured origins; use same-origin requests in the web app.

## Accounts and workspaces

| Method | Route | Purpose |
|---|---|---|
| POST | /api/auth/register | Create account and private workspace |
| POST | /api/auth/login | Create expiring session |
| POST | /api/auth/logout | Revoke current session |
| GET | /api/me | Current account |
| GET/POST | /api/workspaces | List/create workspaces |
| PATCH | /api/workspaces/{w} | Rename workspace |
| GET/POST | /api/workspaces/{w}/collections | Organize sources |

Registration/login JSON: `{"email":"researcher@example.test","password":"a-long-password","name":"Researcher"}`.

## Sources

| Method | Workspace-relative route | Purpose |
|---|---|---|
| GET/POST | /documents | List / multipart upload (`file`) |
| GET/PATCH/DELETE | /documents/{id} | Preview / collection assignment / delete |
| POST | /documents/{id}/versions | Multipart immutable new version |
| GET | /documents/{id}/compare?before={version}&after={version} | Extracted-content diff |
| GET | /versions/{id}/content | Authorized original bytes |
| POST | /versions/{id}/reprocess | Rebuild parser/index outputs |
| GET | /datasets | Structured tables and profiles |
| GET | /search?q=... | Permission-scoped retrieval |
| GET | /sources/{chunk_id} | Resolve cited source |
| POST | /demo | Idempotently load synthetic fixtures |

Search supports collection_id, document_id, version_id and limit. Keyword/semantic scores and actual strategy are returned. Uploads are limited to 20 MB; HTTP request bodies to 21 MB. Chunked mutation bodies require Content-Length.

## Research

```json
{
  "question": "Compare tax figures and gift spending",
  "mode": "investigation",
  "document_ids": null,
  "provider": "extractive"
}
```

POST `/runs` queues a run; GET `/runs/{id}` returns status, public stage outputs, claims, verification, source references and calculations. GET `/runs/{id}/events` streams SSE status/results. POST `/runs/{id}/cancel` and `/resume` control the graph. Modes: research, analysis, investigation.

## Analyses

POST `/analyses`:

```json
{
  "version_id": "source-version-uuid",
  "table_index": 0,
  "operation": "aggregate",
  "column": "Amount",
  "group_by": "Recipient"
}
```

Supported operations: aggregate, statistics, filter, join, correlation, trend, clean. Filtering accepts a bounded rule with eq/ne/gt/lt/not_null. Joins use right_version_id, right_table_index and key. Correlation/trend use second_column. Clean options include trim_strings, drop_duplicates, fill_missing and numeric_columns.

GET `/analyses`, GET `/analyses/{id}/export` and POST `/analyses/{id}/replay` inspect, export and reproduce saved operations.

POST `/charts`: version_id, table_index, kind (bar/line/histogram/scatter), x, y and optional bins. Chart artifacts retain their underlying records and source version.

## Reports and experiments

GET/POST `/reports`; PATCH `/reports/{id}` requires expected_version and saves a new version. GET `/reports/{id}/export?format=md|pdf|docx&version=N`.

GET/POST `/evaluations` runs or lists benchmarks. Custom cases support retrieval, numeric, citation, abstention and contradiction. Provider/model configuration is recorded per experiment.

GET `/audit` returns the authorized workspace audit trail.

## Tools

POST `/calculator` accepts expression; only bounded numeric +, -, *, / and parentheses are accepted.

POST `/approvals` accepts a public HTTPS URL only when external retrieval is enabled. GET `/approvals` lists exact pending URLs. POST `/approvals/{id}/approve` or `/deny` records the user's decision. Approval cannot be granted by source/model text.

## Error conventions

401: sign in. 404: absent or unauthorized resource. 409: state/version conflict. 411: unsupported chunked mutation. 413: request size. 422: invalid values/unsupported operations. 429: rate limit. 503: readiness dependency failure.

Do not build integrations around error-message text; use status codes and structured JSON detail.
