---
ticket: none
title: 'Per-account Selector services list: block, package code'
service: parcel-portal
status: active
created: '2026-11-10'
updated: '2026-11-10'
repo: /home/hjf/code/merak/parcel-portal
worktree: /home/hjf/code/merak/parcel-portal/.claude/worktrees/selector-services
branch: hjf/selector-service-allowlist
base: origin/main
base_sha: 79888873f
pr: null
tags:
- waypoint
- plan
programme: Parcel Portal
impl_model: sonnet
impl_effort: medium
---
# none — Per-account Selector services list: block, package code

<!-- Guidance in this file is written as HTML comments: Obsidian hides them, agents read them,
     and `wp signoff` ignores them. Only <angle spans> are treated as unfilled placeholders, so
     they mark the places a human or agent must actually type something. Leave the comments in
     place — deleting them costs the next reader the guidance and gains nothing at the gate.

     SUPERSEDING A STATEMENT. This file is edited by several sessions over days. When something
     here stops being true, do NOT strike it through, delete it, or bury a correction inside it.
     Put one blockquote immediately ABOVE the stale text and leave the text alone:

         > SUPERSEDED 2026-09-04 — the monitor now lives in `gfs-bifrost/observability`.
         > Everything below is kept as the record of how it was first built here.

     One marker, always above, never inside. `wp decide` writes the dated entry in
     `## Decisions & deviations` that explains why. -->

## Intent
<!-- What we are changing and why. Link the ticket. -->
Origin: Oliver Wilders's DMs, 10 Nov (TCA's Selector account has six installed FedEx services, some must be installable but hidden; later a customer-routes call may fill the list) and Harry's "leave it open so it's extensible" and go-ahead. Each tenant gets a free-form list of Selector services `{serviceCode, label, enabled, packageCode?}`. `enabled=false` blocks a service installed on the account but not yet wanted. An empty list means no restriction, so every existing account behaves as today. When the list is non-empty, booking and "Check with carrier" refuse an order whose mapped service is blocked or unlisted before Selector is called, the shipping-methods editor offers only enabled services, and the row's `packageCode` goes out as `<PackageCode>` between `ServiceCode` and `Dropoff`.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [ ] 1. A tenant with no services rows books, checks and edits shipping methods exactly as before. Evidence: the existing request goldens and `shipping_methods_e2e_test.go` pass unchanged, plus a dispatch test with an empty list.
- [ ] 2. `GET`/`PUT /admin/tenants/{tenantId}/carrier-services` round-trips and is admin-only (a customer gets 403). `PUT` replaces the whole list in one transaction and `[]` clears it. A duplicate (case-insensitive) or blank code gets 400 `invalid_input`. A tenant with no connection gets 404.
- [ ] 3. Each tenant reads and writes only its own list, and saving the carrier connection never changes the list. Evidence: both extended tenancy tests, plus an e2e where an old-shape `PUT carrier-connection` leaves the services intact.
- [ ] 4. With a non-empty list, dispatch, batch dispatch and "Check with carrier" refuse an order whose service is blocked or unlisted with `order_not_dispatchable` naming the code, and make zero `ClaimDispatch`, `ProcessShipment` or `ValidateShipment` calls.
- [ ] 5. An enabled row's `packageCode` is sent as `<PackageCode>` after `<ServiceCode>`. With none set no element is sent, and every existing request golden stays byte-identical.
- [ ] 6. The test-carrier path is not gated, and a mapped service for a different carrier keeps today's carrier-mismatch message only.
- [ ] 7. With a non-empty list, saving shipping methods rejects a new or changed row naming a blocked or unlisted service for the account's carrier (400). Unchanged stale rows still save and reset to built-in is always allowed. `GET` reports each method's `serviceStatus` and offers only enabled services.
- [ ] 8. On dev, with a real admin login and "Book with the test carrier" unticked, an admin enters services on the carrier page, the shipping-methods editor restricts to them, and a blocked order is refused with its message. Evidence: screenshots.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- Contract: `apps/svc/openapi.yaml`, 5.10.0 → 5.11.0 (carrier-services CRUD) and → 5.12.0 (shipping-methods GET fields). Edit first, `make gen`; `public-openapi.yaml` untouched (admin-only). `serviceStatus` is declared `x-extensible-enum` so a later value isn't an oasdiff break.
- Store: migration `018_carrier_service.sql`, `queries/carrier_service.sql`, `internal/repositories/postgres/carrier_services.go` (modelled on `bench_printers.go`), `models.CarrierService` in `internal/models/dispatch.go`.
- Core: `internal/core/carriers/services.go` (use cases, validation, pure `Standing`), `internal/core/dispatch/prepare.go` (the one enforcement point for Dispatch, Batch and Check), `internal/core/imports/shipping_methods.go`.
- Adapter: `internal/adapters/selector/{types,wire,client}.go` (`Connection.PackageCode`, `carrierService.PackageCode`).
- HTTP and wiring: `internal/http/controllers/admin.go`, `internal/bootstrap/bootstrap.go` (~290–297).
- UI (hand-typed `apps/ui/src/svc.ts`): `settings/customers/{actions.ts,carrier-account.tsx,shipping-methods.tsx}`, `[id]/carrier/page.tsx`, `[id]/shipping-methods/page.tsx`, new `carrier-services.tsx`. The UI has no test setup, and AGENTS.md says to ask before adding one.
- Docs: `apps/svc/README.md` (endpoint table ~128, carrier-account paragraph ~196).
- Guardrails: G1 (every new query names `tenant_id`; both tenancy tests extended), G3, G4 (never Commit/PrintManifest/ProcessCarrierDispatch on the shared sandbox), G6 (`PackageCode` is never defaulted).

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- A new table, not jsonb on `carrier_connection` — a later routes sync upserts per row without racing admin edits, and uniqueness is a DB constraint. Settled by reading `bench_printers.go` and `import_mapping.shipping_methods` (migration 009).
- A separate endpoint, not a field on `CarrierConnectionRequest` — `PutCarrierConnection` rewrites the whole row, so an old UI would wipe the list. Source read.
- The gate sits in `prepare`, before `ClaimDispatch`, so no attempt row and no Selector call. It uses `Test(selector.Connection{TestCarrier: conn.TestCarrier})`, as bootstrap does, because `sel` isn't built until after the password read. Source read, both reviewers.
- The test carrier is not gated: the list describes a real Selector account and the fake accepts any code. Consistent with the carrier-choice plan, which says prod never consults `test_carrier` and prod rows hold `true` from migration 017. On dev the block shows only after unticking "Book with the test carrier".
- Errors are 400 `invalid_input` (`exceptions.InvalidInput`), not 422; a duplicate code from a concurrent PUT is also `InvalidInput`, as in `ReplaceBenchPrinters`. The 404 for GET and PUT comes from the use case calling `GetCarrierConnection` first, because an empty PUT never trips the FK.
- `PackageCode` goes between `ServiceCode` and `Dropoff`: Selector's `ClientShipClass.cs:7844` orders `routeMapCode, carrier, contractNo, serviceCode, packageCode, dropoff`. Selector requires it for FedEx (`ValidateProcedures.cs:1267`), it must exist in Selector's `ship_packages`, and Selector truncates it to 4 characters. Source read in `/home/hjf/code/selector`.
- An empty `PackageCode` is omitted, never defaulted to `YP` (G6). Selector fills an empty one from the department/contract route map, so omitting is not "none" on every account.
- Code matching is case-insensitive (`EqualFold`), matching the `upper(service_code)` unique index. The order's code is sent as stored.
- A carrier change leaves the list as it was; no server change, only a UI hint in 5a. Clearing it would touch `PutCarrierConnection`.
- On a restricted FedEx account every built-in FedEx mapping reads "unlisted" (they are `unconfirmedCarriers` guesses), so those orders are refused at dispatch and Check until the mapping is edited. Chosen deliberately: the refusal message names the code, and reset-to-built-in stays allowed on save. FedEx isn't bookable yet anyway (G6 / MKP-10).
- Non-goals: marking orders invalid at import, gating `PATCH /orders`, and showing customers why a service is blocked beyond the order message.
- UNRESOLVED: should a row be keyed by service code, or by Selector route (carrier + contract + service + route code)? Selector's `GetCustRoutes` returns `{routeCode, carrier, contractNo, serviceCode, routeDesc, packageCode, saturdayDeliv}`, and two routes can share a service with different package codes. Planned default: key by `serviceCode` now, and add `routeCode` later as an additive column when the sync exists.
- UNRESOLVED: which package codes are valid for TCA's FedEx account (`YP` was named for the sandbox login). Gates entering real rows, not the code. Ask Oliver Wilders.

## Increments
<!-- Each independently implementable AND verifiable. Cite the criteria it discharges as
     (AC n,n). Tick with `wp tick`, which stamps `— done: <sha>` from HEAD; never hand-write it.
     Prefer 3-7 — more usually means the ticket is too big, so say that rather than splitting
     hairs.

     A PRECONDITION THAT IS NOT CODE goes on its own indented `gate:` line, with a confirmation
     box under it. Sign-off blocks on a ticked increment sitting above an unconfirmed gate, and
     `wp brief` shows unmet gates in its NEXT block — so "do not action this yet" stops being
     bold prose a fresh session can miss:

         - [ ] 6. Widen the subscription filter (AC 6) — verify: filter matches in dev
               gate: FUSE-1052 AND FUSE-1053 confirmed in prod
                     [ ] confirmed
-->

Seven PRs, stacked in this order: 1a → 1b → 2+3 → 4a → 4b → 5a → 5b. 5a depends only on 1b. 4a stacks on 3 because it uses `carriers.Standing`. Sizes are hand-written lines, generated code excluded.

- [x] 1. **Store (~350 lines).** Migration 018 `carrier_service(tenant_id uuid PK-part REFERENCES carrier_connection(tenant_id), position int, service_code text, label text, enabled bool NOT NULL, package_code text NULL, updated_at, updated_by)`, PK `(tenant_id, position)`, unique index on `(tenant_id, upper(service_code))`, CHECKs for trimmed/non-empty/length. Queries, `carrier_services.go` (delete + insert in `pgx.BeginFunc`), `models.CarrierService`. No openapi bump. (AC 2,3) — verify: `make gen`, `make check`, `make test-integration` with one-behaviour store tests (reads only its own tenant; replacing A leaves B; empty clears; case-insensitive duplicate refused; replace with a missing connection fails the FK); both tenancy tests extended (`TestEveryScopedMethodRefusesAContextWithoutATenant`, `TestEveryTenantDataQueryNamesTheTenant`); a migration up/down check, or drop the rollback claim. — done: b1df3bc
      gate: `origin/main` re-checked for a competing migration 018 and contract version at PR time
            [x] confirmed — 2026-11-10 15:30Z: origin/main at 7988887, latest migration 017, only Dependabot PRs open
- [x] 2. **Contract and CRUD (~450 lines).** openapi 5.11.0: `GET`/`PUT /admin/tenants/{tenantId}/carrier-services` (`adminSession`), `CarrierService` and `CarrierServicesRequest` (`additionalProperties: false`, `maxItems`, `maxLength`), `$ref: responses/InvalidInput` for 400, 404 for no connection. Use cases in `core/carriers/services.go` (Get/Set, validation, 404 via `GetCarrierConnection`), thin controller methods, bootstrap wiring, README rows. (AC 2,3) — verify: `make gen`, `make check`, `make contract-check BASE_REF=origin/main` (additive), a bootstrap e2e modelled on `shipping_methods_e2e_test.go` (PUT/GET round trip; customer 403; old-shape `PUT carrier-connection` leaves services intact; no connection 404). — done: f9a5ffd
- [x] 3. **PackageCode and enforcement (~650 lines, at the PR size limit).** Adapter: `Connection.PackageCode`, `carrierService.PackageCode` `xml:"PackageCode,omitempty"` between `ServiceCode` and `Dropoff`, passed at `client.go:301`. Core: `carriers.Standing(list, code)` (available | blocked | unlisted | unrestricted, `EqualFold`); `preparer` gets a required services reader (update `Deps`, `CheckDeps`, `dispatch_test.go`, `check_test.go`, `fakeValidator`, `bootstrap.go`); `CheckDeps.Carrier` gains `Test`. In `prepare`, before the password read and the `len(problems)>0` return: skip when `Test(selector.Connection{TestCarrier: conn.TestCarrier})` is true, the list is empty, the service code is empty, or the carrier differs; otherwise append "the service FGHD (FedEx Home Delivery) is blocked for this account" or "… isn't one of this account's services" and reuse `OutcomeNotDispatchable`. Set `sel.PackageCode` from the matched row once `sel` is built. If this overflows, split the adapter out as its own PR merged first. (AC 1,4,5,6) — verify: `go test ./internal/adapters/selector` (new hand-built golden with `PackageCode` right after `ServiceCode`, noted as not recorded; `TestValidateShipmentSendsTheRequestTheSandboxAccepted` and the other goldens byte-identical); `go test ./internal/core/dispatch` with the existing stubs (blocked → `order_not_dispatchable` naming the code; unlisted → different wording; blocked → zero `ClaimDispatch` and `ProcessShipment`; Check blocked → `OK:false` and zero `ValidateShipment`; empty list as before; enabled row with `packageCode` reaches the stub's `selector.Connection`; without it none; test-carrier with a blocked service still books; different carrier keeps the mismatch message only); unit tests for `Standing`. — done: 194b5f6
      gate: Oliver Wilders (or the sandbox, via a read-only `ValidateShipment`, never Commit/PrintManifest/ProcessCarrierDispatch) confirms the `PackageCode` position before merge; Harry confirms the test carrier stays ungated
            [ ] confirmed
- [x] 4. **Shipping-methods save enforcement (~300 lines, no contract change).** `Set` and `setOnOwnLayout` diff the submitted rows against the stored list (`shippingMethodsOf(m, found).Methods`, or `methodsOf(dictionaries)` on an own layout) and reject only new or changed rows for the account's carrier whose service is blocked or unlisted, with `exceptions.InvalidInput("service FGR is blocked for this account")`. Unchanged stale rows pass; an empty list resets to built-in and is always allowed. `NewSetShippingMethods` and `NewGetShippingMethods` gain the readers via a functional option, so the call sites in `shipping_methods_test.go` (lines ~106, 115, 193, 249, 258) keep compiling. (AC 7) — verify: `go test ./internal/core/imports` and the bootstrap e2e (new row to a blocked service → 400; unchanged stale row passes; empty list no restriction; no connection no restriction; reset to built-in allowed). — done: 3a3a736
- [x] 5. **Shipping-methods GET fields (~280 lines).** openapi 5.12.0: `restricted: bool`, `services: [{serviceCode, label}]` (enabled, for the account's carrier), per-method `serviceStatus` as `x-extensible-enum` available | blocked | unlisted (omitted when unrestricted or when the method's carrier differs). `toShippingMethods` maps them. (AC 7) — verify: `make gen`, `make check`, `make contract-check`, e2e: a stale mapping reads `blocked`; an unrestricted tenant gets no new fields. — done: aa4cd0d
- [x] 6. **Account services card (~380 lines).** `svc.ts` types and `getCarrierServices`/`setCarrierServices` (tolerate 404 and `null`); `setCarrierServicesAction` in `actions.ts`; a second `GCard`, "Account services", on `[id]/carrier/page.tsx` beside the existing `CarrierAccountForm` (`carrier-account.tsx`), with rows `[code | label | enabled | package code]`, add and remove, Save; disabled with a hint until a connection exists; an empty list reads "no restriction"; a hint when the account's carrier changed under a stale list; README carrier-services rows. (AC 2,8) — verify: `pnpm run lint`, `pnpm run build:check`, `pnpm run build` (no UI test setup exists), then a local svc drive with screenshots. — done: dc6dc63
      gate: svc with 1b and the contract at 5.11.0 deployed to dev first, so the UI never meets an svc without the route
            [ ] confirmed
- [ ] 7. **Shipping-methods editor (~300 lines).** When `restricted`, the service code is a select of `services` plus the current value, flagged "blocked / not on this account" if stale; otherwise free text. A Save error shows the svc message. README shipping-methods rows. (AC 7,8) — verify: `pnpm run lint`, `pnpm run build:check`, `pnpm run build`; a manual drive against a svc without the route and then with it, screenshotting both pages; then the dev drive for AC 8 with a real dev admin login and "Book with the test carrier" unticked.
      gate: dev drive done with the real admin login, not `CARRIER_MODE=fake` alone
            [ ] confirmed

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- <YYYY-MM-DD> [inc <n>] <what was run, against what, and the observable result>

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- <what remains unproven, and what would prove it>

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-11-10** — Deviations in 1–2: package_code and label are NOT NULL DEFAULT '' (not NULL) to keep sqlc types plain; the list body is {items:[…]} like bench printers, not {services:[…]}; a duplicate code in any case is 400 invalid_input at both store and use-case level; the up/down migration check is dropped (the repo has no down migrations), so the only rollback claim is that an older image ignores the table.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
- Selector requires `PackageCode` for FedEx (`ValidateProcedures.cs:1267`); it must exist in Selector's `ship_packages` (`CarrierFedEx.cs:866`) and is truncated to 4 characters. Selector fills an empty one from the department/contract route map, so omitting it is not "none" on every account.
- The Selector `CarrierService` wire order is `routeMapCode, carrier, contractNo, serviceCode, packageCode, dropoff` (`ClientShipClass.cs:7844`). The selector-adapter plan still lists it as unverified.
- Selector's "customer routes" call is `GetCustRoutes`, returning `{routeCode, carrier, contractNo, serviceCode, routeDesc, packageCode, saturdayDeliv}`. It is the later source for the services list.
- `exceptions.InvalidInput` is HTTP 400 `invalid_input` at runtime, even where the shipping-methods spec prose says 422. Use `$ref: responses/InvalidInput`.
- On a restricted FedEx account, every built-in FedEx shipping-method guess reads "unlisted" until real services are entered.
