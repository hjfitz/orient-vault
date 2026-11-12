---
title: Selector2 — Migration State
programme: selector2
status: planning
owner: Harry
services:
- carrier-playground
created: '2026-11-11'
updated: '2026-11-12'
tags:
- bifrost
- merak
- migration-state
---
# Selector2 — Migration State

<!-- The single source of truth for PROGRESS. The Overview carries the narrative and the verdict;
     this doc is the live ledger a session reads to know what is done and what is next.
     `wp programme status/next/tick` read and write the `## Unit status` tables below, so keep the
     table shape intact. -->

## What this is
A TypeScript, multi-tenant, SaaS-style replacement for Selector's label-getting. It mirrors CSS's SOAP API and selector-rest-proxy's REST API (v1), adds a terser REST v2, and gets labels by calling the twelve mock carrier proxies in `ilg-merak/carrier-playground`. A SvelteKit UI lets people drive end-to-end mocking and export shipments to CSV. See [[Selector2/Overview|Overview]].

**Services:** a new `ilg-merak` repo (working name `selector2`, backend and frontend together) and `ilg-merak/carrier-playground` (the mocks).

**The invariants every unit holds:**
- **One multi-tenant database.** Every row carries `tenant_id`, every query filters on it, and the repository layer has no unscoped query method. A second dummy tenant's data stays invisible in every integration test.
- **Same contract, own internals.** The five label operations keep CSS's and selector-rest-proxy's wire contracts, so a caller changes its URL and nothing else. The data model and code are a clean replacement, not a port of Firebird or C#.
- **Self-contained.** No Firebird events, no upload to GFS, no billing. The only way data leaves is the UI's CSV export and the carrier calls.
- **All data is synthetic.** Never import a real site, customer, key or label.
- **Never log a request or response body, a label, an address, a key or a credential.** Log identifiers only.
- **OpenAPI first, and published.** Change the spec, then generate, then implement (`ilg-merak/agents` AGENTS.md).
- **Dev only.** There is no prod environment, as with the mocks.

## Unit status
Legend: ⬜ not started · 🟨 in progress · ✅ merged · ⛔ blocked · ⏸ deferred · ❌ dropped · 🔄 rescoped

### A — Foundations
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **A1** | ✅ | New repo: selector2-api (NestJS) + selector2-ui (SvelteKit) | | med | sonnet/medium | ilg-merak/selector2#1 | **Gated on G1.** `ilg-merak/selector2`, a pnpm monorepo: `apps/selector2-api` (NestJS, `src/` layers per the org contract, DI in `bootstrap/containers/`) and `apps/selector2-ui` (SvelteKit). Biome, Vitest, `mise.toml`, golden `node24-runtime` image, CI with `build:check`. `svc-template` is still an empty README, so the layout comes from the org AGENTS.md and `parcel-portal`. **Done when** both apps build in CI and deploy to dev as stubs. |
| **A2** | ✅ | Dev IaC: Cloud SQL (IAM), Cloud Run, SAs | A1 | med | sonnet/high | ilg-merak/selector2#2 | `database/cloud-sql-iam` (IAM-only logins, no passwords, connector, `size` preset); one Cloud Run service per app (`selector2-api-dev`, `selector2-ui-dev`); app and migrator service accounts. Drizzle migrations run as a job inside the apply, as in Parcel Portal A2. Mock proxy URLs and invoker needs come from A3's outputs. **Both services become publicly invokable (`allUsers`), like the mock proxies, because auth is in the app: basic auth on the UI, API keys on the API** (Harry, 2026-11-11; R7). It also provisions the god account's initial password as a Secret Manager secret that only the migrator can read. No account tables here: B1 and B2. **Plan shared and agreed before any apply** (global CLAUDE.md). **Done when** the svc connects to the database as its IAM user on dev. |
| **A3** | ✅ | carrier-playground: IAM path and outputs | | low | sonnet/medium | ilg-merak/carrier-playground#15 | **Lives in `ilg-merak/carrier-playground`.** Each `mock-*` project already outputs `service_name`, `service_uri` and `service_account_email`, and `mock-edge` outputs `urls`. Add an `invoker_members` input to each so selector2's service account can be granted `roles/run.invoker`, and one aggregate output of every proxy's URI. **Keep `allUsers`: the public names stay** (R4). Only add to `mock-edge`, never remove a name (scar tissue). **Done when** selector2's account can call a mock's `service_uri` with an ID token on dev, and the outputs read from selector2's Terragrunt. |

### B — Core domain
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **B1** | ✅ | Drizzle schema, migrations, seed | A2 | high | opus/high | #3 | **The clean Postgres model.** Tenant, API user, carrier account, service, route, number range, shipment, parcel, label, carrier call. Each rule in CSS maps to a table or column, and the mapping is written down for the Confluence differences page. Seeds two tenants of synthetic data. |
| **B2** | ✅ | Accounts, API keys and auth | B1 | high | opus/high | #9 | **Account = tenant (assumed, Harry can change).** An account has a login (username and argon2id password hash), a role (`god` or `standard`) and any number of API keys. API keys are random, shown once, and stored hashed with a lookup prefix; they can be revoked. SOAP reads CSS's `AuthConnDetails`, REST reads `x-api-key`; both resolve to the account. HTTP basic credentials resolve to the same account for the admin routes. A `god` account sees every tenant; a `standard` one only its own rows. The repository layer has no unscoped query. **Seed:** the migration job creates the `god` account from the Secret Manager password A2 provisions (hash only in the DB, re-synced each run), and creates nothing else. Login attempts are rate-limited per account and per source. **AC:** tenant A never sees tenant B's rows, proven with two tenants; a revoked key stops working at once. |
| **B3** | ✅ | Validation chain | B1 | high | opus/high | #5 | Service, options, address and postcode, and customs checks for the twelve proxy carriers only. CSS's validation is about 10k lines (`ValidateProcedures.cs`); reproduce what these carriers and the five operations use, and list what is left out (R5). Credit checks are out. |
| **B4** | ❌ | Consignment numbering | B1 | med | sonnet/high | | Allocate from a tenant's number range, atomically. **Depends on G4** for what a repeated reference does. |
| **B5** | ✅ | Carrier egress port, ID-token client, Royal Mail | B1, A3 | high | opus/high | #4 | One port; an HTTP client that sends a Cloud Run ID token to each proxy's `service_uri`; a recorded call trace per shipment (identifiers and timings, never bodies). First adapter: Royal Mail. Proxy URLs come from config built from A3's outputs. |
| **B6** | ✅ | Adapters: UPS, Coll8, FedEx | B5 | med | sonnet/high | #6 | Each adapter follows its proxy's contract in carrier-playground, including quirks the mocks mirror on purpose. |
| **B7** | ✅ | Adapters: DPD EU, Amazon (SFP and Logistics), BJS | B5 | med | sonnet/high | #7 | Amazon Logistics refuses PDF labels, and DPD EU's validator probably rejects Selector's call (handover, 11 Nov). Decide how selector2 reproduces each. |
| **B8** | ✅ | Adapters: InPost, OCS, Exelot, Veho | B5 | med | sonnet/high | #8 | OCS and Exelot multiply GRAM weights by 1000. Veho has no production proxy, so its adapter follows the agreed contract. |
| **B9** | ⬜ | Shipment use-cases | B2, B3, B4, B5 | high | opus/high | | `ProcessShipment(s)`, `ValidateShipments`, `DeleteShipments`, `CommitShipGroup`, `CommitShipments`, one use-case each. Per-shipment results aggregate to 200, 207 or 400, as selector-rest-proxy does. Commit marks a shipment committed and goes no further (no upload). **Depends on G4.** |
| **B10** | ⬜ | Account and API-key use-cases | B2 | med | sonnet/high | | Create account, list accounts, create and revoke an API key, as use-cases behind the admin routes (basic auth, `god` may create accounts). Keys shown once, stored hashed. OpenAPI first. **AC:** a `standard` account cannot create accounts or see another tenant's keys. |

### C — APIs
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **C1** | ⬜ | REST v1 (selector-rest-proxy parity) | B9 | med | sonnet/high | | OpenAPI first, published. Five operations, `application/problem+json`, 200/207/400, and the ZPLII 4x6 default print spec. **Done when** selector-rest-proxy's own contract tests pass against selector2 with only the URL and key changed. |
| **C2** | ⬜ | SOAP `ClientShipService` for the five operations | B9 | high | opus/high | | Wire-compatible with CSS: `AuthenticationDetails`, `ResponseDetails` and the status codes. Built against recorded real requests, taken from selector-adapter and Parcel Portal's Selector client. **Done when** Parcel Portal's Selector client books against selector2 dev with only its URL changed (R2). |
| **C3** | ⬜ | REST v2 (terser) | C1 | med | sonnet/high | | **Gated on G2.** |

### D — UI
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **D1** | ⬜ | SvelteKit shell and basic-auth gate | A1, B2 | med | sonnet/medium | | **The UI sits behind HTTP basic auth** (Harry, 2026-11-11): the server hook checks the credentials against the account store through selector2-api and challenges with `WWW-Authenticate` otherwise. Never log or echo credentials. Tenant-scoped after login. SvelteKit departs from the org contract's Next.js (R1). |
| **D2** | ⬜ | Shipment playground with call trace and label preview | D1, C1 | med | sonnet/high | | Compose a shipment, then validate, process, commit and delete it. Show each carrier call's trace and the label. |
| **D3** | ⬜ | Accounts and API keys admin | D1, B10 | med | sonnet/high | | **Create accounts when logged in** as `god` (Harry, 2026-11-11), list accounts, create and revoke API keys (the key is shown once). Tenants' contracts, services, number ranges and the mock proxies' URLs stay read-only. |
| **D4** | ⬜ | CSV export | D2 | low | sonnet/low | | Export a tenant's shipments and parcels to CSV. |
| **D5** | ⬜ | End-to-end mock scenarios | D2 | med | sonnet/high | | Preset shipments per carrier, including the magic values that trigger each mock's failures, and a run-all across the twelve with a result grid. |

### E — Docs
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **E1** | ⬜ | Onboard selector2 into Waypoint | B9 | low | sonnet/medium | | `waypoint-onboard`, then explainers once the contract is real. |
| **E2** | 🟨 | Confluence: mock carrier proxies overview | | low | sonnet/medium | | **Gated on G3.** Written with `plainly`. Sources: the carrier-playground handover and ledger. Can start now. |
| **E3** | ⬜ | Confluence: selector2 overview, similarities and differences | C2 | low | sonnet/medium | | **Gated on G3.** Written with `plainly`. Differences come from B1's mapping and the decision log. |

## Gates
- [x] **G1 — Repo name and creation go-ahead** — blocks A1. **Cleared 2026-11-11:** Harry said "go ahead and build this e2e" after `ilg-merak/selector2` was proposed. Created private, `main`, from an initial README.
- [ ] **G2 — REST v2 shape agreed** — blocks C3. "Terser" is not defined yet. Harry says what v2 drops or merges relative to v1.
- [ ] **G3 — Confluence parent page agreed** — blocks E2, E3. Harry names the parent under MPK; nothing is published before that.
- [x] **G4 — A repeated reference: mirror Selector or be idempotent** — blocks B4, B9. Selector books a second shipment (proved by the selector-adapter spike). **Cleared 2026-11-11 by assumption:** Harry said to build end to end after my recommendation was on the table, so selector2 returns the existing shipment for the same tenant and reference, recorded as a deliberate difference. Harry can reverse it.

## Risks
- **R1 ★ Org-contract departures** — SvelteKit (the contract says Next.js, owned by Darren Rielly) and Drizzle (the contract's tooling tier names Go tools and says no ORM by default). Mitigation: record the reason in the repo's AGENTS.md and README, and tell Darren before D1 — open.
> SUPERSEDED 2026-11-12 — `AuthConnDetails` is a C# parameter name in CSS, not a SOAP header. On the wire the credentials are the body element `AuthenticationDetails` inside each request, and the WSDL declares no `soap:header` (evidence: `c2-soap-contract-evidence.md`, `CommonProcedures.cs:25`).
- **R2 ★ SOAP wire compatibility** — CSS's ASMX namespaces, `AuthConnDetails`, status codes and refusals like `0066 Database updating` are easy to get subtly wrong. Mitigation: golden tests from recorded real requests, and C2's done-when check against Parcel Portal's client — open.
- **R3 Mocks mirror proxies, not Selector** — quirks the mocks copy on purpose (weights ×1000, no PDF for Amazon Logistics, DPD EU validator) will surface in the adapters — open.
- **R4 The IAM path is not enforced** — the mocks keep `allUsers`, so ID tokens are sent but never required. Making the mocks private would remove the public names, because the external LB can't attach ID tokens. A later unit if wanted — standing.
- **R5 Validation scope creep** — CSS validation is about 10k lines. Mitigation: B3 lists exactly what is reproduced and what is not — open.
- **R6 Platform module naming** — `cloud-sql-iam` and `cloud-sql` may be merged, with naming being agreed with SRE. Pin the module tag and re-check at A2 — standing.
- **R7 ★ Public endpoints with a login** — the UI and API are reachable from the internet with app-level auth, and the seeded `god` account can create accounts. Mitigations: a random password from Secret Manager (no default credential anywhere), argon2id hashes, per-account and per-source rate limiting on every credential check, constant-time comparison, API keys hashed with a lookup prefix, nothing credential-bearing in logs. Dev only, synthetic data — open.
- **R8 No instance cap, small database** — the platform `compute/cloud-run` module exposes no `max_instance_count`, so a public service can scale out until the 25-connection `db-f1-micro` is exhausted, after which readiness returns 503 and the migrator cannot connect. Mitigations in A2: pool of 2 per instance, single-flight readiness pings, no database access on unauthenticated routes beyond readiness. Real fix: add `max_instance_count` to the platform module (ilg-platform/terraform-modules) — open.
- **R9 Readiness is invisible to Cloud Run** — Cloud Run probes only `/health/liveness`, so a service that never reaches its database logs `databaseNotReady` and carries on. Exiting after the wait would not fail a deploy visibly (the instance is already ready). The fix is a startup probe on `/health/readiness`, which needs checking against what the platform module allows — open.

## Decision log
- **2026-11-12** — **Ship mode (Harry):** "go ahead. as far as i'm concerned we're going to /ship this as there are no customers. happy to make mistakes, /orchestrate and do whatever. as long as there's the v2 look and the backward soap compat - i'm happy". Merged B1 (`#3`, `49f175e`). The programme now runs under the `ship` skill: agents build in worktrees, a review panel checks each diff, then non-draft PR and merge without a separate go-ahead per unit, dev only, orchestrated in parallel waves. **Kept:** dev only; no secrets or emails; Confluence publishing, Slack and anything prod-shaped still stop for Harry (G3 stays open, so E2 and E3 are not part of this run). **Terraform:** I read each PR's plan myself and proceed when it shows only adds or updates in dev; a destroy, an IAM widening beyond what is already agreed, or anything surprising stops for Harry. **G2 cleared by assumption:** Harry only asked for a "v2 look", so I define REST v2 as the terse shape (decided at C3, recorded here). **B4 deferred**, because CSS takes numbers from the proxy; B5 reports whether Royal Mail needs range registration. **C2 scope:** includes `ValidateShipment` (singular) and `DailyShipQuery`, so Parcel Portal's client books with only its URL changed.
- **2026-11-12** — **B1 built and in draft review (`ilg-merak/selector2#3`):** 12 tables with composite `(id, tenant_id)` foreign keys, labels as `bytea`, mapping in `docs/data-model.md`, fail-closed dev seed (loopback only; separate from the migrate job). A three-lens panel ran over 5,200 lines (past the 1,500 guard on purpose, mostly tests) and every verified finding is fixed. Design calls: a repeated reference returns the live shipment through one `INSERT … ON CONFLICT DO UPDATE … RETURNING`; a committed shipment keeps its reference; stale `booking` rows are swept to `failed` by B9 (index only here). **B4 finding, recommendation only:** CSS takes consignment and parcel numbers from the proxy for all 12 proxy carriers, so `number_range` may be unneeded; whether the Royal Mail mock takes ranges is a B5 question. Harry decides whether B4 is dropped. Node floor raised to 24.7.0 (`argon2Sync`).
- **2026-11-12** — **C2 evidence gathered (read-only agent, spot-checked):** primary evidence exists for ProcessShipment, ValidateShipment, DeleteShipments and DailyShipQuery. `ProcessShipments`, `ValidateShipments` and `CommitShipGroup` have no recorded sample, and `CommitShipments` has none from the real server, so those four are built from the C# source and the 2022 WSDL snapshot. Parcel Portal also calls `ValidateShipment` (singular) and `DailyShipQuery`, so C2's done-when needs both although neither is among the five operations: scope decision for Harry. `CommitShipGroup` drops all failure detail, and validation errors use code `0003`, not the documented `0200`. The selector2 README (line ~183) and `iam.tf` comment repeat the wrong header claim and need correcting in the next unit that touches them.
- **2026-11-11** — **A2 review (4-lens panel, +1,870 lines incl. 883 of tests, so it ran past the skill's 1,500-line guard on purpose):** verified findings are being fixed on `ilg-merak/selector2#2`: ping timeout covers the open, single-flight readiness, pool 2 and query timeouts, migration lock handling, migration job exit-code tests, and the secret grant ordering. The god-password env binding is dropped from the migrate job until the seeding unit reads it; the secret and the migrator-only accessor stay. Not taken: exiting non-zero after the 120 s wait (R9).
- **2026-11-11** — **Public exposure:** basic auth on the UI means selector2-ui is publicly invokable (`allUsers`), and API-key callers cannot present Google ID tokens, so selector2-api is too. Both authenticate in the app, as the mock proxies do. A2's plan shows the bindings for Harry to agree before anything applies.
- **2026-11-11** — **UI auth and accounts (Harry):** "happy to put basic auth in front of the ui - and have a means of creating and storing api keys in a db. happy to start off with a god account that we seed the db with and have the option to create other accounts when logged in." Assumed: **account = tenant**, with a login, a role (`god` or `standard`) and API keys. Changes B2 and D1 and D3 and adds B10.
- **2026-11-11** — **A1 shipped:** `ilg-merak/selector2#1` merged as `c2c35f3` with Harry's approval of the plan; deploy dev applied 2 added / 0 destroyed per app. The services are IAM-only, so health checks from outside need an invoker (A2). The PR's own `ci` and `Terraform plan (PR)` workflows did run on the branch even though `main` held only a README, so the new-repo "no runs on the first PR" gotcha in memory did not reproduce here (cause not established).
- **2026-11-11** — **Names:** every app, directory, Cloud Run service, image and log `service` tag carries the project name: `selector2-api` and `selector2-ui`. Never `svc`/`ui`, and no `sel2` suffix. Harry's correction after the scaffold copied Parcel Portal's `apps/svc` and `apps/ui` (memory `feedback-name-apps-and-services-with-project-name`).
- **2026-11-11** — **Build go-ahead:** Harry: "happy to go ahead and build this e2e". Read as clearing G1 (repo `ilg-merak/selector2` created, private) and G4 (idempotent on tenant + reference). G2 and G3 stay open; neither is needed until C3 and E2/E3. Merges and dev applies follow the dev-mock-infra rule in the carrier-playground handover; anything touching prod, or a Terraform plan with a destroy, still stops for Harry.
- **2026-11-11** — **Confluence:** a new MPK subsection covering similarities, differences, and an overview of the mock proxies and selector2. Pages are written with `plainly`. Nothing is published before G3.
- **2026-11-11** — **Planning model:** Harry chose to proceed on Sonnet rather than switch to Opus, although model routing sizes the design at opus/high. Units that need opus/high say so in `Tier`.
> SUPERSEDED 2026-11-11 — UI v1 now includes account and API-key management behind basic auth (see the 2026-11-11 "UI auth and accounts" entry). Contracts, services and ranges stay read-only.
- **2026-11-11** — **UI v1:** shipment playground with call trace and label preview, CSV export and read-only admin. No admin CRUD.
> SUPERSEDED 2026-11-11 — refined: API keys are created and stored hashed in the database, and basic-auth accounts exist too (see "UI auth and accounts").
- **2026-11-11** — **Caller auth:** own API users per tenant, stored hashed. No ApiKy.
- **2026-11-11** — **Carrier paths:** the twelve proxy carriers only. No template-drawn labels and no direct-API carriers.
- **2026-11-11** — **Operations:** the five label operations over SOAP and REST v1; REST v2 follows after G2.
- **2026-11-11** — **Data model:** one multi-tenant, SaaS-style database. A clean Postgres model through Drizzle, "more like a replacement than like-for-like" (Harry). Supersedes my Firebird-shaped recommendation.
- **2026-11-11** — **Mock access:** the mocks stay public. selector2 calls each `service_uri` with an ID token, and carrier-playground exposes the invoker grants and outputs (A3).
- **2026-11-11** — **Stack and home:** a new `ilg-merak` repo holding NestJS and SvelteKit together; Postgres on the platform `database/cloud-sql-iam` module; egress to the carrier-playground mocks. Firebird events are out of scope, with CSV export through the UI instead.

## Scar tissue
- **Never remove a name from `mock-edge`.** The platform load-balancer module deletes a backend and cert before detaching them. Only add or update (carrier-playground handover, 11 Nov).
- **Every row carries `tenant_id`, and the repository has no unscoped query** — the same invariant Parcel Portal holds, and the one that keeps one deployment safe for many tenants.
- **Never log bodies, labels, keys or credentials.** CSS's `AuthConnDetails` header carries a password, and replies carry PII and labels.
- **Selector's `FEDEX` and `INPOST` mean a proxy in CSS but the carrier's own API in Client4.** selector2 mirrors CSS, so both go through the proxies.
