---
ticket: none
title: 'Dev: choose the test carrier or the configured connection per customer'
service: parcel-portal
status: active
created: '2026-11-10'
updated: '2026-11-10'
repo: ilg-merak/parcel-portal
worktree: /home/harry/code/merak/parcel-portal/.claude/worktrees/dev-carrier-choice
branch: hjf/dev-carrier-choice
base: origin/main
base_sha: c357296
pr: null
tags:
- waypoint
- plan
---
# SHIP-1110-dev-carrier-optin — Dev: choose the test carrier or the configured connection per customer

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
Harry, 10 Nov: "can we configure dev to opt in to the test selector or a configured one? Maybe a check box or something." Today one Terraform setting (`carrier_mode`) makes every dev customer book with the stand-in carrier. Instead, each customer chooses on its Carrier card. **Book with the test carrier** stays ticked by default, and unticked it books through the customer's configured Selector connection. Prod is untouched: the test carrier isn't offered there, so the choice is neither shown nor consulted. Run `/ship` SHIP-1110-dev-carrier-optin; prod is held at D1, so this ships to dev only.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [ ] 1. On dev, an admin can untick **Book with the test carrier** on a customer's Carrier card, after which that customer's dispatch, check, void, manifest, refresh and connection check go through its configured Selector connection. Ticked, or for a customer never changed, they use the stand-in as today.
- [ ] 2. Prod never routes to the stand-in. svc wires the plain Selector client when the test carrier isn't offered, a request to choose it there is refused, and the card doesn't offer it.
- [ ] 3. Switching a customer's carrier is refused while it has booked shipments or unresolved dispatch attempts, saying what to close first, so nothing booked by one backend is voided, reconciled or manifested by the other (G2).
- [ ] 4. A customer on its configured connection needs a stored password, as on prod. The password stays optional only while the test carrier is chosen.
- [ ] 5. Status follows the customer. GET /carrier's `test`, the TEST notices and Manifest availability reflect that customer's choice: the sandbox Manifest guard still applies to a Selector-routed customer on the shared sandbox (G4). The card reads the choice for the customer being edited, not the acting one.
- [ ] 6. Demo customers and the dev smoke keep working: demo customers are created on the test carrier.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- svc: migration 017 (`carrier_connection.test_carrier`), `queries/carrier_connection.sql` and a tenant-scoped open-work count, `models.CarrierConnection`, `selector.Connection.TestCarrier`, a router plus a password router in `adapters/fakecarrier`, `core/carriers` (SetConnection, Status, Check), the three places that build `selector.Connection`, `bootstrap.go` wiring, and dispatch logging (the `testCarrier` tag per booking).
- Contract (G3): `openapi.yaml` CarrierConnectionRequest/CarrierConnection `testCarrier`, CarrierStatus `testCarrierAvailable`, the switch-refused error; 5.9.0 → 5.10.0; `make gen`.
- UI: `svc.ts` types, the Carrier card (`settings/customers/[id]/carrier`), `TestCarrierNotice` copy, demo and overview copy.
- Docs: `apps/svc/README.md`, `docs/runbook.md`, `apps/ui/README.md`, `iac/env/dev.tfvars` and the `carrier_mode` variable description. No Terraform resource change.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- Every carrier call comes from an HTTP request with the tenant on ctx; no background job books (research workflow `wf_dca4d453-2a0`, read from source).
- No shipment or attempt records which backend booked it, hence the switch guard rather than per-shipment routing (same source). Recording the backend per shipment would allow switching freely; it isn't needed for a dev-only choice.
- The column defaults to the test carrier, so existing dev customers don't change. Prod rows also get the default, but prod never consults it (the router is only wired where the test carrier is offered).
- This machine has no Selector sandbox credentials. On dev, an opted-in customer can be shown reaching its configured endpoint, not booking there. The opted-in booking path is proved end to end locally against a stand-in Selector HTTP server.

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
- [x] 1. svc routing: migration 017, queries and models, `selector.Connection.TestCarrier`, `fakecarrier` router and password router, wiring only where the test carrier is offered, Status and Check per connection, `testCarrier` log tag per booking (AC 1,2,5,6) — verify: unit tests for routing; e2e: a stand-in customer books TST while an opted-in customer books through a stand-in Selector server; prod-mode wiring ignores the flag — router + password router unit tests; e2e: a test-carrier customer books TST with no Selector call while an own-account customer books through the faked Selector; plain-client wiring refuses the choice — done: e19a6a9
- [x] 2. svc choice rules and contract: SetConnection takes `testCarrier` (absent keeps the stored choice), refuses it where not offered, requires a password unless the test carrier is chosen, and refuses a switch with booked shipments or open attempts; openapi 5.10.0 with the new fields and errors; controllers (AC 2,3,4) — verify: core tests per rule; `make check` incl. contract-check and the tenancy tests — 19 core tests for the choice, password and switch rules; e2e 422 carrier_switch_blocked and test_carrier_unavailable; make check (fmt, vet, race, lint, gen-check) and contract-check 5.9.0->5.10.0 additive; full integration suite green — done: e19a6a9
- [x] 3. UI: the Carrier card's checkbox (offered only where svc says so, state from the customer-scoped connection), the password rule, the switch-refused message, per-customer notice copy (AC 1,4,5) — verify: lint, build:check, next build; local e2e of the card on and off — biome, tsc and next build green; local Playwright: offered → box ticked + TEST notice + password optional, unticked → account notice + password required, a tick-back save with nothing open succeeds; not offered → no box or notice, password required. A save storing a password 503s locally (no carrier key); covered on dev — done: c5e8675
- [ ] 4. Docs: svc README, runbook, ui README, dev.tfvars and variable description (AC 2) — verify: read through
- [ ] 5. Dev: deploy and drive it: a stand-in customer still books TST; unticking a customer reaches its Selector endpoint; a switch with open shipments is refused; Manifest guard on a sandbox-routed customer (AC 1-6) — verify: evidence in Verification

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
