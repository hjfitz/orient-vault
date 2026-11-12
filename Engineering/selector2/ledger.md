---
tags: [waypoint, ledger]
---
# selector2 — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-11-12 — Add the scenarios page: preset shipments for the twelve mock carriers

Add the scenarios page: preset shipments for the twelve mock carriers

Unit D5. /scenarios books preset shipments against the twelve mock carrier proxies and compares the outcome with what each preset expects: 74 presets (12 happy, 62 failure presets using the mocks' magic values), run one or run all happy paths (3 at a time, at most 12 per click, one run per account, no new call after 150 s so the worst case stays inside Cloud Run's 300 s). The local synthetic seed now gives the Acme tenant a contract, service and route for every carrier, and Bramble's service codes are corrected to ones its mocks accept. Three-lens review panel, all verified findings fixed. Local end to end against the real mocks: 12 of 12 happy paths ok in the browser, 74 of 74 presets matched.

PR: ilg-merak/selector2#20

## 2026-11-12 — Add the shipment playground, shipment list and label preview, and the CSV export to the UI

Add the shipment playground, shipment list and label preview, and the CSV export to the UI

Units D2 and D4. The playground composes a v2 shipment and validates, processes, commits and deletes it through the basic-auth admin routes, showing item outcomes, the carrier call trace and the labels (PNG in an img, PDF in an unsandboxed iframe because Chromium's PDF viewer refuses a sandboxed frame, ZPL as server-read text). Shipment list with filters and detail; CSV export streamed through the UI server. A four-lens review panel found and the PR fixes: the PDF preview never rendering, a failed label read turning a successful booking into a 500, the compose form blanking after commit, a god's stale tab writing to another tenant (now 409), a UI timeout shorter than the API's worst carrier call, vacuous tests. Also fixes the synthetic seed's Royal Mail service code (RMT24, not the product code TPN24). Verified locally end to end against the public mocks in headless Chromium.

PR: ilg-merak/selector2#19

## 2026-11-12 — Add the basic-auth routes the UI uses: shipments, labels, carrier accounts, CSV export

Add the basic-auth routes the UI uses: shipments, labels, carrier accounts, CSV export

Unit B11 (added mid-run): /admin/shipments operations sharing the REST v2 functions, list and detail with the carrier call trace, label bytes, carrier accounts, CSV export with a cap, concurrency limit and injection-safe cells, tenantId on every route. Two-lens review fixed.

Ship: SELECTOR2-1112-ship. PR: ilg-merak/selector2#18

## 2026-11-12 — Add the accounts and API keys admin UI

Add the accounts and API keys admin UI

Unit D3: /accounts and /accounts/[id] over the admin routes; one-time key shown once with no-store, uncertain-create handling, guarded submit, accessible revoke confirmation. Review fixed.

Ship: SELECTOR2-1112-ship. PR: ilg-merak/selector2#17

## 2026-11-12 — Add the SOAP ClientShipService, wire-compatible with CSS

Add the SOAP ClientShipService, wire-compatible with CSS

Unit C2: SOAP 1.1 service for eight operations, 46 golden replies, XML safety budgets, Parcel Portal's own Selector client booked against a local selector2 with only the endpoint and credentials changed. Security review fixed.

Ship: SELECTOR2-1112-ship. PR: ilg-merak/selector2#16

## 2026-11-12 — Add REST v2, the terse API

Add REST v2, the terse API

Unit C3: /v2/shipments create, validate, delete, commit plus GET /v2/services over B9 use-cases; flat request, per-item results, idempotent create, envelope-only strict validation, response bodies validated against the spec. Two-lens review fixed.

Ship: SELECTOR2-1112-ship. PR: ilg-merak/selector2#15

## 2026-11-12 — Add REST v1 at parity with selector-rest-proxy

Add REST v1 at parity with selector-rest-proxy

Unit C1: five routes over B9 use-cases, Ajv-validated against rest-v1.yaml, proxy error shapes, ApiKeyGuard. Proxy smoke suite: 20 of 28 pass unchanged, the 6 failures assert Selector sandbox data, ported copy 26 of 26. Two-lens review fixed.

Ship: SELECTOR2-1112-ship. PR: ilg-merak/selector2#14

## 2026-11-12 — Add the shipment use-cases: process, validate, delete and commit

Add the shipment use-cases: process, validate, delete and commit

Unit B9: five label operations as use-cases with a typed batch result; idempotent reference claim, cancel hold (migration 0003), ambiguous-create handling, CSS mapping fixes, tenant-scoped writes tested directly. Three-lens review fixed.

Ship: SELECTOR2-1112-ship. PR: ilg-merak/selector2#13

## 2026-11-12 — Add the SvelteKit shell and the basic-auth gate

Add the SvelteKit shell and the basic-auth gate

Unit D1: basic-auth gate over GET /admin/me, success cache, per-visitor limiter, shell with CSP, god tenant picker, terraform_remote_state for the API URL. Two-lens review fixed. Follow-up: API trusts a verified UI-forwarded visitor address.

Ship: SELECTOR2-1112-ship. PR: ilg-merak/selector2#12

## 2026-11-12 — Add the account and API-key use-cases and the admin routes

Add the account and API-key use-cases and the admin routes

Unit B10: admin OpenAPI first, account and API-key use-cases, basic-auth guard over the B2 resolver, JSON-only POST (CSRF), trusted-proxy source address. Two-lens review fixed.

Ship: SELECTOR2-1112-ship. PR: ilg-merak/selector2#10

## 2026-11-12 — Add accounts, API keys, the principal resolver and the god account

Add accounts, API keys, the principal resolver and the god account

Unit B2: hashed revocable API keys, argon2id passwords, principal resolver (REST key, SOAP, basic), TenantScope with no unscoped query, throttling (migration 0002), god account synced by the migrate job from Secret Manager. Three-lens review fixed.

Ship: SELECTOR2-1112-ship. PR: ilg-merak/selector2#9

## 2026-11-12 — Add the InPost, OCS, Exelot and Veho carrier adapters

Add the InPost, OCS, Exelot and Veho carrier adapters

Unit B8: InPost, OCS, Exelot (create) and Veho (create, cancel, commit); BookingRequest.shipDate; all 12 proxy carriers now registered. Two-lens review fixed.

Ship: SELECTOR2-1112-ship. PR: ilg-merak/selector2#8

## 2026-11-12 — Add the DPD Europe, Amazon and BJS carrier adapters

Add the DPD Europe, Amazon and BJS carrier adapters

Unit B7: DPD EU (create), Amazon SFP (create, validate) and Logistics (create, validate, cancel), BJS (create, cancel). Two-lens review fixed.

Ship: SELECTOR2-1112-ship. PR: ilg-merak/selector2#7

## 2026-11-12 — Add the UPS, Coll8 and FedEx carrier adapters

Add the UPS, Coll8 and FedEx carrier adapters

Unit B6: UPS (two XML calls, partial-failure handle), Coll8 (cancel and end-of-day manifest), FedEx. Two-lens review fixed; fast-xml-parser 5.11.2 with DOCTYPE refusal.

Ship: SELECTOR2-1112-ship. PR: ilg-merak/selector2#6

## 2026-11-12 — Add the shipment request model and the validation chain

Add the shipment request model and the validation chain

Unit B3: canonical shipment request (CSS in camelCase), pure validation chain for the 12 proxy carriers with rule slugs, validation-scope doc. Three-lens review fixed.

Ship: SELECTOR2-1112-ship. PR: ilg-merak/selector2#5

## 2026-11-12 — Add the carrier egress port, ID-token client and Royal Mail adapter

Add the carrier egress port, ID-token client and Royal Mail adapter

Unit B5: carrier port with optional capabilities, Cloud Run ID-token HTTP client, carrier_call tracing, Royal Mail adapter. Three-lens review fixed. Finding: no number ranges for the 12 proxy carriers, so B4 dropped.

Ship: SELECTOR2-1112-ship. PR: ilg-merak/selector2#4

## 2026-11-12 — Add the multi-tenant domain schema, its Selector mapping and a synthetic seed

Add the multi-tenant domain schema, its Selector mapping and a synthetic seed

Unit B1: Drizzle schema (12 tables, composite tenant FKs), migration 0001, docs/data-model.md (CSS mapping), dev-only fail-closed synthetic seed, integration tests against Postgres 17. Review panel (data, seed/security, tests) findings fixed. Draft; merge waits on Harry.

PR: ilg-merak/selector2#3

## 2026-11-11 — Cloud SQL, migrations, readiness and public access

Cloud SQL, migrations, readiness and public access

Cloud SQL (cloud-sql-iam, Postgres 17, db-f1-micro, ZONAL, deletion protection on), IAM-only logins, a Cloud Run migrate job run inside the apply, readiness that checks the database, and allUsers invokers on selector2-api and selector2-ui (auth is in the app, later units). Dev apply: api 17 added / 1 changed / 0 destroyed, ui 1 / 1 / 0. Migrate job logged migrations applied and exited 0; api readiness returns 200 publicly. The god-password secret exists (Terraform state; read with gcloud secrets versions access) but no job reads it yet: the seeding unit adds the env. Open: no instance cap on the platform module (R8), readiness not probed by Cloud Run (R9).

PR: ilg-merak/selector2#2

## 2026-11-11 — Scaffold selector2-api and selector2-ui, IaC and CI

Scaffold selector2-api and selector2-ui, IaC and CI

New repo ilg-merak/selector2: NestJS selector2-api and SvelteKit selector2-ui in one pnpm workspace, Biome, Vitest, Terragrunt projects and four workflows. Merged to main; deploy dev applied 2 resources per app (Cloud Run service plus service account), 0 destroyed. Services are IAM-only (no allUsers), so an unauthenticated call returns 403 and no invoker is granted yet. Names carry the project name, never svc/ui.

PR: ilg-merak/selector2#1
