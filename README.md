# Kaika Goals

A leadership workspace for accountable goals, inherited workstreams, terminal deliverables and evidence-based decisions. Summary, Goal Hierarchy and Hygiene share the same goal records and calculations.

**Status: connected internal workshop preview.** The leader switcher simulates identity. This application binds to loopback and is not suitable for public hosting or an organization-wide rollout without authentication and tenant authorization.

## Run a synthetic demo

Requires Python 3.12+ (verified on 3.14), Node 22.12+ (verified on 26), and npm.

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.lock
npm ci
npm run build
.venv/bin/python server.py --fixtures --port 8787
```

Open http://127.0.0.1:8787. Fixture edits persist locally in the ignored `.demo-state.json`. The generated `dist/Kaika-Connected-Preview.html` needs the local server for data operations. Opening it directly provides a link back to the running app.

## Connect an existing private workshop

Copy `connection.example.json` to `.workshop-config.json`, then configure the existing Edge endpoint and its restricted, expiring capability locally. Never use a publishable key as the capability. Never commit this file. The application does not provision cloud access automatically.

```sh
.venv/bin/python server.py --connected-workshop --port 8787
```

The existing private database stays authoritative. There is no fallback to synthetic storage when a cloud request fails. `database/` contains schema and adapter references, not an automatic production migration or a dump. Imported workforce records, identity mappings and tenant-specific activation scripts are intentionally excluded.

## Stack and project map

- Python / FastAPI / Uvicorn: local HTTP boundary, origin/Host validation, private credential handling, gzip and timing headers.
- HTTPX: pooled server-to-server TLS connections to the Supabase Edge adapter.
- PostgreSQL and private Supabase Storage: records, revision-checked commits, idempotency and evidence.
- TypeScript / Vite: typed, built network boundary. The established screen renderers are still JavaScript; this is an incremental migration, not a completed React rewrite.
- `fixture_server.py`, `goal_contract.py`, `outcome_metrics.py`, `leadership_domain.py`, `support_domain.py`: shared domain rules.
- `hygiene_actions.js`, `hygiene_ui.js`: personalized responsibilities, plan checks and history.
- `summary_ui.js`, `summary_history.js`, `plans_map.js`: summary, snapshots and hierarchy.

## Verify

```sh
npm run check
.venv/bin/python -m unittest test_api test_cloud_repository test_support test_personalization test_strategy_workshop test_editable_demo test_success_basis test_outcomes test_leadership test_scenarios
```

The CI template in `docs/ci-verify.yml` uses synthetic data only. To activate it, place it at `.github/workflows/verify.yml` using a GitHub connection with workflow permission. It is not active yet. See [architecture](docs/ARCHITECTURE.md), [verification](docs/VERIFICATION.md) and [product scope](docs/PRODUCT-SCOPE.md). Private meeting transcripts and detailed stakeholder documents remain outside this public repository.

## Goal Charter

Approved goals open the Charter; unfinished goals open setup. See [behavior and connected verification](docs/GOAL-CHARTER.md).

## Goal registration

Five-step setup supports initiated and inherited goals, reasoned pushback, metric-only/delivery/combined contracts and deliverable-linked resources. See [workflow and verification](docs/GOAL-REGISTRATION.md).

## Source provenance

The small Oslo kommune OKR helper in `vendor/` is derived from `oslokommune/okr-tracker` revision `06d87896644280771549c8c1c9212c11ea1f665f`. Its MIT notice and attribution are retained. Perdoo informed product patterns only; its code and assets were not copied. Third-party licenses do not grant a license to all original application code.
