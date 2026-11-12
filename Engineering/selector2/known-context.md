---
tags: [waypoint, selector2]
title: selector2 — known context
verified: 2026-11-12
verified_sha: null
verified_paths: []
---
# selector2 — known context

What source can't tell you. Written from the programme record (`Bifrost/Selector2/Migration State.md` and `Overview.md`), the repo's `docs/` and `AGENTS.md`, and the code, with no interview: Harry was not asked. Anything that comes from neither is under `## Unknowns`. Programme progress and the full decision log live in the Migration State; this holds the durable context behind the code.

## History
- **Programme, 11 to 12 November 2026.** Harry proposed a TypeScript, multi-tenant replacement for Selector's label-getting on 11 November. The repo is `ilg-merak/selector2`, made from an initial README; Harry's go-ahead ("go ahead and build this e2e") cleared gate G1.
- **Built in about two days by agents.** The first wave was scaffold (A1) and infra (A2). On 12 November Harry switched the programme to `ship` mode: "as far as i'm concerned we're going to /ship this as there are no customers. happy to make mistakes, /orchestrate and do whatever. as long as there's the v2 look and the backward soap compat - i'm happy". Units then merged in parallel waves with a review panel per diff and no per-unit go-ahead. Of the 25 units, 18 had merged by `6442634` (snapshot 2026-11-12); D2, D4, D5, E2 and E3 are open.
- **Names.** Every app, directory, Cloud Run service and image is `selector2-api` or `selector2-ui`, never `svc` or `ui`. The scaffold copied Parcel Portal's `apps/svc`; Harry corrected it.

## Decisions Harry made
- **2026-11-11, stack and home:** a new `ilg-merak` repo with NestJS and SvelteKit together, Postgres on the platform `database/cloud-sql-iam` module, egress to the carrier-playground mocks. No Firebird events; CSV export from the UI instead.
- **2026-11-11, data model:** one multi-tenant database, "more like a replacement than like-for-like". Drizzle through a clean Postgres model.
- **2026-11-11, scope:** the twelve proxy carriers only, the five label operations over SOAP and REST v1, REST v2 after the shape is agreed.
- **2026-11-11, auth:** HTTP basic auth in front of the UI, API keys created and stored hashed in the database, a seeded `god` account that can create other accounts when logged in. The assumption that **account = tenant** is mine, and Harry can change it.
- **2026-11-11, public exposure:** both services are invokable by `allUsers`, with auth in the app, as the mocks are. This follows from basic auth in the UI and API keys that cannot present Google ID tokens.
- **2026-11-11, mocks stay public:** selector2 sends a Cloud Run ID token to each proxy's `service_uri`, but the mocks never require it (R4, standing).
- **2026-11-11, SvelteKit and Drizzle:** recorded as departures from the org contract (R1), decided by Harry and written in `AGENTS.md`.
- **2026-11-12, ship mode:** merge without a separate go-ahead per unit, dev only. Confluence publishing, Slack and anything prod-shaped still stop for Harry. For Terraform, the agent reads each PR's plan and proceeds only when it shows adds or updates in dev; a destroy, an IAM widening beyond what is agreed, or anything surprising stops.

## Decisions taken by assumption (Harry can reverse)
- **G4, repeated reference (2026-11-11):** selector2 returns the existing shipment for the same tenant and reference, with no second carrier call. Selector books a second shipment. This is a recorded deliberate difference from CSS.
- **G2, REST v2 shape (2026-11-12):** Harry only asked for "the v2 look", so the agent defined "terse" itself (`docs/rest-v2.md`): four calls under `/v2/shipments`, flat request, per-item results, idempotent create.
- **B4 dropped (2026-11-12):** CSS takes consignment and parcel numbers from the proxy for all 12 carriers, and no proxy needs a range registered. The `number_range` table stays in the schema, unused.
- **C2 scope widened:** it includes `ValidateShipment` (singular) and `DailyShipQuery`, because Parcel Portal's client calls both and "books with only its URL changed" was the done-when.

## Constraints
- **Dev only, synthetic only.** There is no prod environment and no prod tfvars. Never import a real site, customer, key or label.
- **The mocks mirror proxies, not Selector** (R3). Quirks they copy on purpose (weights multiplied by 1000 for OCS and Exelot, no PDF for Amazon Logistics, DPD EU's validator) show up in the adapters.
- **Selector's `FEDEX` and `INPOST` mean a proxy in CSS but the carrier's own API in Client4.** selector2 mirrors CSS, so both go through the proxies.
- **Never remove a name from carrier-playground's `mock-edge`.** The platform load-balancer module deletes a backend and certificate before detaching them. Only add or update.

## Fragility
- **The stale limit.** A `booking` claim older than the limit is taken to have crashed and may be re-booked. If it is shorter than the longest carrier call, a slow live booking can be booked twice. Config derives it (at least 5 minutes) and refuses a lower override.
- **Commit marks first, then tells the carrier.** A crash between the two leaves a shipment committed locally that Royal Mail, Coll8 or Veho never manifested, and nothing retries it.
- **An ambiguous create keeps its reference.** After a timeout or 5xx the carrier may hold the booking; the caller must check or cancel before resending after the stale limit.
- **`X-Forwarded-For` hop count.** The api and ui trust the last entry only (`TRUSTED_PROXY_HOPS = 1`, `XFF_DEPTH=1`). A load balancer or IAP in front makes it 2. Too far left bypasses the throttle; too far right locks everyone into one bucket.
- **The ui shares one source address.** The api sees every ui call from the ui's own address, so a visitor guessing an account's password 10 times through the ui can make its owner's next ui sign-in a 429. The ui limits per visitor first, but the fix (the api trusting a verified ui-forwarded visitor address) is left for a decision and is not in the code at `6442634`.
- **The ui's 60-second sign-in cache** delays revocation by up to a minute per instance.
- **Pre-auth XML parsing.** The SOAP body is parsed before authentication. A 4 MiB body once blocked the event loop for about 1.6 s; the limit is now 1 MiB with tag-count and depth budgets. Keep any new parse budget-bound.

## Surprises
- **The god password is unreadable by humans.** Only the migrator service account can read `selector2-god-password`, and Harry's own account is denied. A sign-in check as `god` therefore needs someone who holds the password. The only route is impersonating the migrator or reading the pinned version through it (see [[operations]]).
- **SOAP `AuthConnDetails` is not a header.** Older notes and the first README and `iam.tf` comment said it was. It is a C# parameter name; the wire carries the body element `AuthenticationDetails` (superseded 2026-11-12, `docs/soap.md`).
- **SOAP carries an API key in the password field.** Parcel Portal and selector-adapter send whatever `Username`/`Password` their Selector connection holds, so pointing one at selector2 means setting those to an account username and an API key.
- **Four SOAP operations have no recorded sample.** ProcessShipments, ValidateShipments and CommitShipGroup have none, and CommitShipments has none from the real server. Their goldens are built from the C# source and the 2022 WSDL, so they prove the source reading, not the real server. `CommitShipGroup` drops all failure detail, and validation errors use code `0003`, not the documented `0200`.
- **The proxy smoke suite passes 20 of 28 unchanged.** The 6 failures assert Selector sandbox data (HERMES, YODEL, `ShipmentID` 0, Selector's echo); the ported copy in the repo passes 26 of 26.
- **A new repo's first PR did run its workflows** even though `main` held only a README, so the "no runs until the workflow is on the default branch" gotcha did not reproduce here. The cause was not established.
- **A local `terragrunt plan` with a developer account gets 403** on the Terraform state object; only the CI runner account reads it.

## Risks (snapshot 2026-11-12)
- **R1, org-contract departures:** SvelteKit instead of Next.js (owned by Darren Rielly) and Drizzle instead of no-ORM. Recorded in `AGENTS.md`. Darren has not been told.
- **R2, SOAP wire compatibility:** mitigated by 46 goldens and the Parcel Portal client run, but the four unrecorded operations remain unproven against the real server.
- **R4, the IAM path is not enforced:** ID tokens are sent and never required. Making the mocks private would remove their public names.
- **R5, validation scope creep:** `docs/validation-scope.md` lists what is reproduced and what is left out. Credit checks are out.
- **R6, platform module naming:** `cloud-sql-iam` and `cloud-sql` may be merged, with naming being agreed with SRE.
- **R7, public endpoints with a login:** mitigated by a random god password, argon2id, per-account and per-source throttling, constant-time comparison and hashed keys. Dev only.
- **R8, no instance cap:** the platform `compute/cloud-run` module has no `max_instance_count`, so a public service can exhaust the 25-connection database. The real fix is in `ilg-platform/terraform-modules`.
- **R9, readiness is invisible to Cloud Run:** only `/health/liveness` is probed. A startup probe on readiness needs checking against the module.

## Open gates (snapshot 2026-11-12)
- **G3, Confluence parent page:** Harry has not named a parent under MPK, so nothing is published. E2 (mock proxies page, drafted in the vault) and E3 (selector2 overview and differences) wait on it. This is why the run does not publish docs.

## Unknowns
- **Does selector2 belong to the Selector system in Waypoint?** `Systems/selector/` exists in the vault, and selector2 replaces part of it, but no record says it is a member, so `waypoint.yaml` has no `system:`.
- **Has Darren Rielly been told about SvelteKit and Drizzle?** The programme record says no (R1, open). Nothing says who tells him or when.
- **What does "the v2 look" mean to Harry beyond the shape the agent defined?** G2 was cleared by assumption, and Harry has not confirmed `docs/rest-v2.md`.
- **Is account = tenant what Harry wants?** It was assumed on 2026-11-11 and has not been confirmed.
- **Will selector2 ever get a prod environment or real customers?** The record says "dev only, no cutover" and nothing about a trigger to change that.
- **Who owns selector2 after the programme?** `owner: bifrost` in `waypoint.yaml` is inferred from the vault folder; no record names an owner.
- **Is the API to trust a ui-forwarded visitor address?** The ui doc says the fix is "left for a decision", and no record shows one.
- **Which person can read `selector2-god-password` today?** Only the migrator service account can. `db_migrator_impersonators` is empty (snapshot 2026-11-12), so no human is known to be able to.
- **Why did the new repo's first PR run its workflows?** Not established.
- **Does the deployed service match `6442634`?** Not checked: the deploy-dev run for the last merges was not read.
