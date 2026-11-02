---
ticket: FUSE-1238
title: CanonicalWorkOrder identifiers.carrierId (types 10.12.0)
service: pkg-node
status: active
created: '2026-10-09'
updated: '2026-10-19'
repo: /home/hjf/code/fuse/pkg-node
worktree: /home/hjf/code/fuse/pkg-node/.claude/worktrees/fuse-1238-wo-carrier
branch: hjf/fuse-1238-work-order-carrier-id
base: origin/main
base_sha: 316ddd362
pr: '265'
tags:
- waypoint
- plan
---
# FUSE-1238 — CanonicalWorkOrder identifiers.carrierId (types 10.12.0)

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
Add optional `identifiers.carrierId` to `CanonicalWorkOrder` so a connector mapping default (Tom Dunn's `OWN` on GADG work-order ingest) survives the Zod parse in sftp-connector and snap-adapter and reaches the Snap S10 shipment's `CarrierId`. Attached to the Distraction Duty ticket FUSE-1238. Proof is downstream: a GADG work order ingested with the default shows `CarrierId: OWN` in Snap. See [[FUSE-1238-gadg-work-order-csv-confirmations-woc-and-fgr-ma]] (sftp-connector) for the config half.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. `@gfs-bifrost/types@10.12.0` is published with `identifiers.carrierId?: string` on the work-order type and schema
- [x] 2. The Package Changelog (org contract) and the Fuse MCP canonical-types data describe the new field
- [ ] 3. Consumers (snap-adapter, sftp-connector, fuse-ui) take the version and a GADG work order with the default reaches Snap with `CarrierId` set (proven in their plans)

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `pkg/types/src/canonical/{schemas/work-order.schema.ts,types/work-order.types.ts}`: one optional field, schema and type in lockstep, no `.default()`.
- Canonical type surface, so the Fuse MCP `data/canonical-types.json` (done, with `make parity-accept`) and the Package Changelog in `/home/hjf/code/CLAUDE.md` (the org contract, outside any repo).
- Fan-out: sftp-connector and snap-adapter `safeParse` against the schema (strip on old pins); fapi `POST /api/v2/work-orders` and collector strip until they bump, not covered.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- 10.11.0 is held by open PR #262 (StockSyncFailure), so this takes 10.12.0 — checked with `gh pr view 262` and origin/main (10.10.0) on 2026-10-09. If #262 merges later it publishes 10.11.0 after 10.12.0; consumers use carets so nothing breaks, but `latest` will point at 10.11.0 until the next publish.
- `identifiers.carrierId` rather than `shipping.carrier.id` — Harry's call, mirrors `CanonicalSalesOrder`.
> SUPERSEDED 2026-10-19 — refuted for S10 creates: GADG dev Snap stored NETCOURIER when sent OWN. See Evidence.
- Snap accepts non-lookup carrier values on a shipment (2024 GADG shipment carries `DHL`, CARRIER lookup holds only `NETCOURIER`); OpenAPI `maxLength: 1` on the header is a spec error — queried live 2026-10-09. A write of `OWN` is not yet proven; the downstream dev check does that.

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

- [x] 1. Add `carrierId` to the work-order schema and type, bump `pkg/types` to 10.12.0 (AC 1) — verify: `pnpm build`, 70 tests and `lint:fix` pass in `pkg/types`; PR checks green — done: 921a54a
- [x] 2. Merge so the Publish workflow publishes (AC 1) — verify: `gh api /orgs/gfs-bifrost/packages/npm/types/versions` lists 10.12.0 — done: 921a54a
- [x] 3. Package Changelog row in the org contract and Fuse MCP `canonical-types.json` + parity baseline pushed to master (AC 2) — verify: `go test ./internal/...` passes; `fuse://canonical-types` shows `carrierId` after the MCP deploy — done: 921a54a

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-19 **Real SnapFulfil substitutes the carrier.** GADG's dev mapping carries the default `identifiers.carrierId = OWN`. Its work order `WO-20261016-AP005` (correlation `776af3a6-cc2d-45ca-95ee-55a5a402d068`, created 2026-10-16 11:03Z by snap-adapter-dev-00537, which includes the fix) reached snap-adapter with `carrierId: "OWN"`, per dedupe-service's forwarded canonical. Real GADG dev Snap accepted the create, and S10 `GADGDFD78D24007` reads **`CarrierId: "NETCOURIER"`**. That is the only value in GADG dev Snap's CARRIER lookup. Fuse delivers the value; Snap swaps in its own. Making `OWN` land is Snap-side config (the CARRIER lookup), not Fuse code.
- 2026-10-09 [inc 1,2] PR gfs-bifrost/pkg-node#265 (squash-merged): Lint, Tests, dependency audit, gitleaks and Semgrep green; Publish Packages run 37907929945 succeeded; `gh api /orgs/gfs-bifrost/packages/npm/types/versions` lists 10.12.0 first.
- 2026-10-09 [inc 3] fuse-mcp commit 0245812 pushed to master: `data/canonical-types.json` work-order identifiers now ends `…prime, carrierId`; `make parity-accept` diff limited to the canonical-types text; `go test ./internal/...` all ok. Package Changelog 10.12.0 row added to `/home/hjf/code/CLAUDE.md`.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- That `OWN` is accepted on a Snap write, and the whole carrier chain on dev/prod: proven in the snap-adapter and sftp-connector plans and the parent's dev check.
- fuse://canonical-types after the MCP Deploy workflow finishes was not read back.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-10-19** — AC 3 stays open on a Snap-side finding. Fuse carries the carrier end to end: HJF simulator S10 HJFD4AC7656638E holds OWN, and both consumer plans are complete. But real GADG dev Snap stored NETCOURIER for a GADG work order sent with OWN (see Evidence). The assumption 'Snap accepts non-lookup carrier values' is refuted for S10 creates. AC 3 needs OWN added to GADG's CARRIER lookup in SnapFulfil (dev, then prod), or a different carrier value; that's a WMS/ops decision for Harry.

- **2026-10-19** — Sign-off check 2026-10-19: AC 1 re-verified (types versions list 10.12.0) and AC 2 (fuse-mcp origin/master canonical-types carries carrierId; Package Changelog row present). AC 3 unmet: consumer PRs sftp-connector#304 and snap-adapter#286 merged 2026-10-09, but neither consumer plan has run its dev end-to-end check (each has its AC 3 / inc 3 open).

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
