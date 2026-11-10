---
ticket: "none"
title: "Per-account Selector services list: block, package code"
service: "parcel-portal"
status: draft
created: "2026-11-10"
updated: "2026-11-10"
repo: "/home/hjf/code/merak/parcel-portal"
worktree: "/home/hjf/code/merak/parcel-portal/.claude/worktrees/selector-services"
branch: "hjf/selector-service-allowlist"
base: "origin/main"
base_sha: "79888873f"
pr:
tags: [waypoint, plan]
programme: "Parcel Portal"
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
- <assumption> — <how it was established: source read, ticket, asked>
- UNRESOLVED: <question that needs a human decision>

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

- [ ] 1. <increment> — verify: <how>
- [ ] 2. <increment> — verify: <how>

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

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
