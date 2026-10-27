# Security model

This is a locally oriented portfolio application. It has concrete security controls and tests, but no independent security audit or enterprise certification.

## Implemented controls

- Passwords: PBKDF2-SHA256, independent random salts, 600,000 iterations. Session secrets are random and stored as SHA-256 hashes.
- Sessions: HttpOnly, SameSite=Strict, configurable Secure flag, server-side expiry and logout revocation.
- Membership/resource checks: workspace predicates on documents, versions, search, research, analyses, reports, approvals and experiments.
- Mutation origins: explicit allowlist, with same-origin proxying in the UI.
- Rate limiting: Redis in Compose; bounded in-memory limiter in single-process local mode.
- Upload limits: size, signatures, archive expansion, macro rejection, type and text checks. Originals are never executable application assets.
- Untrusted sources: treated as data. Models cannot register, approve or invoke arbitrary tools.
- Model output: rendered as text; no raw HTML insertion.
- Quantitative tools: allowlisted operations only; clean process environment, bounded stdin, isolated working directory, wall timeout and Linux resource limits.
- Web tool: disabled by default, exact URL approval, HTTPS-only, public address validation, DNS-pinned connection, byte limit, no automatic redirects.
- CSV export: formula-leading values are prefixed to reduce spreadsheet formula injection.
- Containers: non-root application users, no-new-privileges, dropped capabilities, no Docker socket, loopback-published endpoints.
- Logs: request paths/status/latency, not passwords, tokens, model keys or source passages.

## Threats and assumptions

| Boundary | Threat | Control / limitation |
|---|---|---|
| Upload parser | Malformed/bomb content | Bounded archives/cells/pages; patched pinned libraries; no universal antivirus guarantee |
| Cross-workspace retrieval | Tenant leakage | SQL/resource predicates and negative tests |
| Source/model content | Prompt injection | No model-driven permission or arbitrary-code interface |
| Numerical computation | Code/tool misuse | Reviewed operation DSL; general generated Python is unsupported |
| Network tool | SSRF / DNS rebinding | Public-IP validation and pinned TLS connection; redirects rejected |
| Reports | Unsupported edited statements | Version history and underlying run inspection; edits are not automatically reverified |
| Deletion | Stale evidence | Original/chunk removal and unavailable-source warnings |
| Worker failure | Duplicate/restarted work | Per-run locks, durable checkpoints, safe retry and explicit stale recovery |
| Local host | Compromised account | Host security remains the operator's responsibility |

The subprocess operation interface does not provide a kernel network jail. Network access is absent from the supported operations. Do not replace it with arbitrary Python without a separate security design.

## Before exposing beyond localhost

Use TLS and secure cookies; review allowed origins and reverse-proxy trust; rotate credentials; decide signup/invitation policy and access controls; test the Docker stack, backups/restores and the chosen real models; conduct a focused security review. These are release requirements, not claims that a Compose file alone establishes production readiness.

## Data retention

No hidden automatic retention deletion. Deleting a source removes original versions and searchable chunks; derived results and user-edited reports remain. Backups contain private records and must be protected. Runtime secrets are excluded from source control and source archives.

Report security issues privately to the repository maintainer. No contact address is invented here.
