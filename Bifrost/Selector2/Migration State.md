---
title: Selector2 — Migration State
programme: selector2
status: planning
owner: Harry
services:
- carrier-playground
created: '2026-11-11'
updated: '2026-11-11'
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
| **A2** | ⬜ | Dev IaC: Cloud SQL (IAM), Cloud Run, SAs | A1 | med | sonnet/high | | `database/cloud-sql-iam` (IAM-only logins, no passwords, connector, `size` preset); one Cloud Run service per app (`selector2-api-dev`, `selector2-ui-dev`); app and migrator service accounts. Drizzle migrations run as a job inside the apply, as in Parcel Portal A2. Mock proxy URLs and invoker needs come from A3's outputs. Also grants `roles/run.invoker` (both services are IAM-only after A1: an unauthenticated call returns 403, and Harry's account has no invoker either), starting with selector2-ui's account on selector2-api; a human invoker is a tfvars value, left empty until Harry names a principal. **Plan shared and agreed before any apply** (global CLAUDE.md). **Done when** the svc connects to the database as its IAM user on dev. |
| **A3** | ✅ | carrier-playground: IAM path and outputs | | low | sonnet/medium | ilg-merak/carrier-playground#15 | **Lives in `ilg-merak/carrier-playground`.** Each `mock-*` project already outputs `service_name`, `service_uri` and `service_account_email`, and `mock-edge` outputs `urls`. Add an `invoker_members` input to each so selector2's service account can be granted `roles/run.invoker`, and one aggregate output of every proxy's URI. **Keep `allUsers`: the public names stay** (R4). Only add to `mock-edge`, never remove a name (scar tissue). **Done when** selector2's account can call a mock's `service_uri` with an ID token on dev, and the outputs read from selector2's Terragrunt. |

### B — Core domain
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **B1** | ⬜ | Drizzle schema, migrations, seed | A2 | high | opus/high | | **The clean Postgres model.** Tenant, API user, carrier account, service, route, number range, shipment, parcel, label, carrier call. Each rule in CSS maps to a table or column, and the mapping is written down for the Confluence differences page. Seeds two tenants of synthetic data. |
| **B2** | ⬜ | Tenancy and API-user auth | B1 | high | opus/high | | Hashed credentials per tenant. SOAP reads CSS's `AuthConnDetails`; REST reads `x-api-key`; both resolve to the same tenant API user. A tenant-scoped repository with no unscoped query. **AC:** tenant A never sees tenant B's rows, proven with two tenants. |
| **B3** | ⬜ | Validation chain | B1 | high | opus/high | | Service, options, address and postcode, and customs checks for the twelve proxy carriers only. CSS's validation is about 10k lines (`ValidateProcedures.cs`); reproduce what these carriers and the five operations use, and list what is left out (R5). Credit checks are out. |
| **B4** | ⬜ | Consignment numbering | B1 | med | sonnet/high | | Allocate from a tenant's number range, atomically. **Depends on G4** for what a repeated reference does. |
| **B5** | ⬜ | Carrier egress port, ID-token client, Royal Mail | B1, A3 | high | opus/high | | One port; an HTTP client that sends a Cloud Run ID token to each proxy's `service_uri`; a recorded call trace per shipment (identifiers and timings, never bodies). First adapter: Royal Mail. Proxy URLs come from config built from A3's outputs. |
| **B6** | ⬜ | Adapters: UPS, Coll8, FedEx | B5 | med | sonnet/high | | Each adapter follows its proxy's contract in carrier-playground, including quirks the mocks mirror on purpose. |
| **B7** | ⬜ | Adapters: DPD EU, Amazon (SFP and Logistics), BJS | B5 | med | sonnet/high | | Amazon Logistics refuses PDF labels, and DPD EU's validator probably rejects Selector's call (handover, 11 Nov). Decide how selector2 reproduces each. |
| **B8** | ⬜ | Adapters: InPost, OCS, Exelot, Veho | B5 | med | sonnet/high | | OCS and Exelot multiply GRAM weights by 1000. Veho has no production proxy, so its adapter follows the agreed contract. |
| **B9** | ⬜ | Shipment use-cases | B2, B3, B4, B5 | high | opus/high | | `ProcessShipment(s)`, `ValidateShipments`, `DeleteShipments`, `CommitShipGroup`, `CommitShipments`, one use-case each. Per-shipment results aggregate to 200, 207 or 400, as selector-rest-proxy does. Commit marks a shipment committed and goes no further (no upload). **Depends on G4.** |

### C — APIs
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **C1** | ⬜ | REST v1 (selector-rest-proxy parity) | B9 | med | sonnet/high | | OpenAPI first, published. Five operations, `application/problem+json`, 200/207/400, and the ZPLII 4x6 default print spec. **Done when** selector-rest-proxy's own contract tests pass against selector2 with only the URL and key changed. |
| **C2** | ⬜ | SOAP `ClientShipService` for the five operations | B9 | high | opus/high | | Wire-compatible with CSS: `AuthenticationDetails`, `ResponseDetails` and the status codes. Built against recorded real requests, taken from selector-adapter and Parcel Portal's Selector client. **Done when** Parcel Portal's Selector client books against selector2 dev with only its URL changed (R2). |
| **C3** | ⬜ | REST v2 (terser) | C1 | med | sonnet/high | | **Gated on G2.** |

### D — UI
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **D1** | ⬜ | SvelteKit shell and login | A1, B2 | med | sonnet/medium | | Session cookie, tenant-scoped. SvelteKit departs from the org contract's Next.js (R1). |
| **D2** | ⬜ | Shipment playground with call trace and label preview | D1, C1 | med | sonnet/high | | Compose a shipment, then validate, process, commit and delete it. Show each carrier call's trace and the label. |
| **D3** | ⬜ | Read-only admin | D1, B1 | low | sonnet/medium | | Tenants, API users (no secrets shown), carrier accounts, services, number ranges, and the mock proxies' URLs. |
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
- **R2 ★ SOAP wire compatibility** — CSS's ASMX namespaces, `AuthConnDetails`, status codes and refusals like `0066 Database updating` are easy to get subtly wrong. Mitigation: golden tests from recorded real requests, and C2's done-when check against Parcel Portal's client — open.
- **R3 Mocks mirror proxies, not Selector** — quirks the mocks copy on purpose (weights ×1000, no PDF for Amazon Logistics, DPD EU validator) will surface in the adapters — open.
- **R4 The IAM path is not enforced** — the mocks keep `allUsers`, so ID tokens are sent but never required. Making the mocks private would remove the public names, because the external LB can't attach ID tokens. A later unit if wanted — standing.
- **R5 Validation scope creep** — CSS validation is about 10k lines. Mitigation: B3 lists exactly what is reproduced and what is not — open.
- **R6 Platform module naming** — `cloud-sql-iam` and `cloud-sql` may be merged, with naming being agreed with SRE. Pin the module tag and re-check at A2 — standing.

## Decision log
- **2026-11-11** — **A1 shipped:** `ilg-merak/selector2#1` merged as `c2c35f3` with Harry's approval of the plan; deploy dev applied 2 added / 0 destroyed per app. The services are IAM-only, so health checks from outside need an invoker (A2). The PR's own `ci` and `Terraform plan (PR)` workflows did run on the branch even though `main` held only a README, so the new-repo "no runs on the first PR" gotcha in memory did not reproduce here (cause not established).
- **2026-11-11** — **Names:** every app, directory, Cloud Run service, image and log `service` tag carries the project name: `selector2-api` and `selector2-ui`. Never `svc`/`ui`, and no `sel2` suffix. Harry's correction after the scaffold copied Parcel Portal's `apps/svc` and `apps/ui` (memory `feedback-name-apps-and-services-with-project-name`).
- **2026-11-11** — **Build go-ahead:** Harry: "happy to go ahead and build this e2e". Read as clearing G1 (repo `ilg-merak/selector2` created, private) and G4 (idempotent on tenant + reference). G2 and G3 stay open; neither is needed until C3 and E2/E3. Merges and dev applies follow the dev-mock-infra rule in the carrier-playground handover; anything touching prod, or a Terraform plan with a destroy, still stops for Harry.
- **2026-11-11** — **Confluence:** a new MPK subsection covering similarities, differences, and an overview of the mock proxies and selector2. Pages are written with `plainly`. Nothing is published before G3.
- **2026-11-11** — **Planning model:** Harry chose to proceed on Sonnet rather than switch to Opus, although model routing sizes the design at opus/high. Units that need opus/high say so in `Tier`.
- **2026-11-11** — **UI v1:** shipment playground with call trace and label preview, CSV export and read-only admin. No admin CRUD.
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
