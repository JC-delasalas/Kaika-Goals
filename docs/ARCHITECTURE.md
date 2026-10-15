# Architecture and operating contract

## Decision

Use a modular application with a Python FastAPI API and a TypeScript/Vite frontend boundary. Keep the tested domain rules during incremental UI migration. A wholesale frontend or backend rewrite would introduce more regression risk than this workshop warrants. Rust, Go, microservices and a server-rendered framework do not solve the observed duplicate database round trips.

The shipped client still has concatenated JavaScript renderers and overrides. TypeScript currently covers the transport only. Migrate one shared screen/data contract at a time; do not describe this as a fully typed frontend.

```text
Browser (no cloud credentials)
  -> loopback FastAPI: Host / Origin / nonce checks
     -> pooled HTTPX -> restricted Supabase Edge capability
        -> private PostgreSQL workshop store
        -> private evidence bucket
     -> shared Python validation and scoped projections
  <- committed result plus current actor-scoped projection
```

## Request lifecycle

`GET /api/bootstrap` provides a per-process nonce and connection mode. `POST /api/command` with `action=session` loads the roster and selected leader state in one cloud read. If a remembered persona is inactive, the server selects the configured active default. `state` always reloads committed source records and derives the current reporting scope. No shared scoped-response cache is used.

Writes carry a mutation UUID. Idempotency lookup and source load run concurrently. The server verifies the actor, scope, command and approval authority, computes row deltas, and submits a revision compare-and-swap transaction. A conflict is returned rather than overwriting another writer. The browser retains the mutation ID after uncertain failure and never announces success before a confirmed response. Successful mutations return `_state`, avoiding a second full load. Replayed commits reload before returning state. A future per-goal transaction model should replace the workspace-wide revision for concurrent production writers.

No global request lock serializes reads. Each request has its own domain instance and snapshot. HTTPX pools connections. A bounded eight-worker executor performs independent idempotency lookups. Gzip compresses large JSON and HTML; Server-Timing reports server duration without logging records.

## Evidence

Owner-authorized uploads are limited to 20 MiB and validated by type/content in the Edge adapter. The private bucket is `kaika-deliverable-evidence`. Objects are immutable and content-hashed. The server checks visible evidence before downloading. An upload has zero acceptance credit. Only the configured independent reviewer can accept a checkpoint against evidence. Storage and metadata are separate operations: retry uses stable identifiers; a future orphan-reconciliation job is still needed. Automated malware scanning is not connected.

## Data model

- Workspace: revision, scenario clock and private capability.
- Workforce: read-only imported people and reporting relationships, import provenance, active status. Goals never modify the HR source.
- Goal: one accountable parent and stable identity; relative objective/workstream presentation.
- Version: owner, approver, period, success contract, lifecycle and immutable approved baseline.
- Deliverable -> checkpoints -> evidence -> acceptance decisions.
- Measures -> append-only readings; separate operational KPIs and observations.
- Monthly allocations, approvals, check-ins, questions/replies/resolutions, decisions, follow-ups, support requests, private views and saved review snapshots.

The current workshop uses JSON payload rows with generated indexed columns in a private schema. It is not the final normalized multi-tenant model. The gateway presently loads the whole workshop before creating a scoped response. That is acceptable only as a measured workshop implementation, not evidence of 1,000 concurrent leaders' capacity.

## Latency contract

Target usable cold workspace <=3 seconds at p95; no ordinary read or confirmed small mutation above 4 seconds in the release acceptance sample. Measure from user action to usable rendered state, not spinner appearance. Record request, data parse, render and total separately.

Current transport warns at 3.5 seconds; ordinary requests have a 12-second client recovery deadline and remote operations have 3-second phase timeouts. These are failure-handling bounds, not guarantees of a successful result within four seconds. Multi-step mutations and network outages can exceed the target. Upload/download deadlines are larger because file transfer depends on size and bandwidth. Do not silently turn uncertain saves into failures or successes.

Before the 100-person pilot: scoped SQL projections and pagination, actor/tenant auth, query plans and indexes, cursor-based roster search, per-goal concurrency, immutable actual event times separate from scenario dates, workload-based p50/p95/p99 measurements and complete-process accessibility checks. Before 1,000+ leaders: representative concurrent read/write tests, tenant-scoped authorization and cache keys, background export/AI jobs, pool saturation metrics, backup and recovery rehearsal.

## Local operations

Keep the capability file local with owner-only permissions. If DNS fails, restore network/DNS; do not disable TLS verification, hardcode an IP or expose database credentials to the browser. If a capability expires, renew it through the existing authorized private setup. Supabase MCP authentication is a separate developer connection and does not determine application save behavior.

Restarting the server rotates the local nonce; the client reacquires it once after the specific validation failure. A generic 403 is never retried as a permission bypass. Back up before migrations. Never run SQL reference files blindly against an existing project. The no-login switcher must not be exposed on a public interface.

References: [FastAPI](https://fastapi.tiangolo.com/), [Vite](https://vite.dev/guide/), [TypeScript](https://www.typescriptlang.org/docs/), [HTTPX clients](https://www.python-httpx.org/advanced/clients/), [Supabase API security](https://supabase.com/docs/guides/api/securing-your-api).
