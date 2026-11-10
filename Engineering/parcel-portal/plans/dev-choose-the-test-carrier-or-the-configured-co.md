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
- [x] 4. Docs: svc README, runbook, ui README, dev.tfvars and variable description (AC 2) — verify: read through — svc README, runbook, ui README, dev.tfvars comment and carrier_mode description read through; terraform fmt clean — done: ce2574b
> SUPERSEDED 2026-11-10 — dev can't be driven as an admin from this session (the bootstrap-admin secret is IAM-denied and the dev smoke's admin login is broken), so increment 5 was split: the drive ran locally against the real Selector sandbox, and the drive on dev became increment 6, gated on a login.
- [x] 5. Dev deploy, and the drive run locally against the real Selector sandbox: a stand-in customer still books TST; a switch with open shipments is refused; an unticked customer's check reaches Selector; Manifest guard on a sandbox-routed customer (AC 1-6) — verify: evidence in Verification — dev deploy healthy (migration 17, test carrier offered); local drive against the real Selector sandbox, evidence in Verification — done: 3ea96d9
- [ ] 6. Drive it on dev as an admin: untick a demo customer onto the sandbox account, Check connection from dev, switch refused with a booked shipment, then tick it back (AC 1,3,4) — verify: evidence in Verification
      gate: a dev GFS-admin login this session can use (put in ~/.secrets), or Harry runs the check
            [ ] confirmed

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-11-10 [inc 5] **Dev deploy of the branch (5898dc0):** svc-parcel-dev-00050 and ui-parcel-dev-00058 serving `dev-5898dc0`; svc log on dev "Migrations applied 16 → 17 (applied 1)" then "The test carrier is offered"; `/sign-in` 200. Every existing dev customer keeps the test carrier (column default true).
- 2026-11-10 [inc 5] **Local drive, branch svc with a local-only carrier key, against the real Selector sandbox** (Playwright, screenshots in `carrier-choice-screens/`): the seed customer on the test carrier dispatched PREVIEW-18 as TST2613752224 (log `Dispatch booked testCarrier=true`) and the order page showed "Orders here are booked with a stand-in carrier"; unticking it with that shipment booked was refused: "This customer has 1 booked shipment to void or manifest. Close them before switching carrier…" (singular wording fixed in 3ea96d9), and a reload still showed it ticked. A fresh demo customer unticked onto the sandbox account (TEST/TEST, HERMES, GB) saved (audit `testCarrier=false passwordWritten=true`), Check connection answered "The carrier accepted the account." (one read-only daily query), its Shipments page had no TEST notice and Manifest off with the sandbox reason; ticked back with nothing open it saved, and Check said "This customer books with the test carrier, so nothing was checked with Selector."
- 2026-11-10 [inc 3] **Card where the test carrier isn't offered** (local svc in selector mode): no checkbox and no notices; the password is required.
- 2026-11-10 [inc 1-2] **Tests:** routing for every carrier call and the password router (unit); the choice, password and switch rules (20 core tests); open-work count and its tenant scoping against Postgres; e2e: a test-carrier customer books TST with no Selector call while an own-account one books through the faked Selector, switch refused with 422 `carrier_switch_blocked` until the shipment is voided, `test_carrier_unavailable` where not offered, and prod's wiring ignores a row the migration marked true (booking, log and status). Mutation-checked: the log test fails on the raw column, and the prod-wiring tests fail if selector mode wires the router. `make check` and the full integration suite green under `-race`.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- The authenticated flow on dev itself (increment 6): unticking a dev customer, its check reaching the sandbox from dev's network, and the refusal. Proven locally against the real sandbox with the same code; dev needs an admin login this session can use.
- The switch guard's race with a dispatch already under way (accepted and documented: a check, not a lock).

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-11-10** — Self-review: the booking log's testCarrier is the carrier's own Test(conn), as GET /carrier's is, because migration 017 marks every older row true, prod's included. Kept DEFAULT true (not false + a dev backfill) so dev customers keep the stand-in with no data step; prod never reads or reports the raw column (status, check, GET connection and now the log all go through the wired carrier or the offered flag).

- **2026-11-10** — Self-review (4 lenses): the switch guard stays a check, not a lock. A dispatch that read the old choice just before a switch still books with it, and that shipment then needs an engineer (Selector can't void a TST consignment, and the guard won't switch back while it's booked). Closing it means locking the carrier_connection row in the G2 claim transaction; not worth touching G2 for a dev-only toggle with a sub-second window. Documented in the README and on the guard.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
- **Local svc has no carrier key**, so any save that stores a carrier password answers 503 ("No carrier key: carrier passwords can't be stored or read"). An own-account save can only be driven on dev (which has `svc-parcel-carrier-key`) or in the e2e harness (`WithCarrierKey`). (2026-11-10)
- **A shipment booked by one backend can't be closed through the other.** Selector refuses a TST consignment it never saw, and its day list doesn't show it, so void's fallback can't recover it; the stand-in "voids" a real Selector booking portal-side only, leaving it live in the sandbox. This is why the switch guard exists, and why a dispatch caught mid-switch needs an engineer. (2026-11-10)
- **The local preview database's second demo customer (`Demo 6 Nov 14:12:31 UTC`) was deleted on 9 Nov**, so acting for it 404s on `/me`: the stale acting-cookie error page, not a bug. Make a fresh demo customer for local checks. (2026-11-10)
