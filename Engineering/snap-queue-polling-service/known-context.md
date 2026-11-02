---
tags: [waypoint, snap-queue-polling-service]
verified: '2026-08-24'
verified_paths: []
title: snap-queue-polling-service — known context
---

# snap-queue-polling-service — known context

`known-context.md` is exempt from staleness checks — this is interview/investigation
truth, not a claim about current source. Re-verify against code before trusting a
specific implementation detail below.

## Criticality

Confirmed mid/high: if this service goes down or falls badly behind, customers/3PLs
**miss** fulfilment confirmations (pick/pack/despatch/receipt/RGA/work-order) for as
long as it's down. It is, however, **self-healing, not data-losing** — SnapFulfil's
outbound queue just backs up and drains normally once the service recovers; nothing
is dropped by an outage itself (distinct from the INC-30 duplication failure mode,
which is a *double*-delivery bug, not a loss one).

## INC-30 — duplicate confirmations {#inc-30}

Because stage 2 (`/event/poll/confirmations`) fetches + converts + **publishes before
it acks**, a business with a large outbound-queue backlog can blow past a short ack
deadline. Pub/Sub then redelivers the same poll, the still-uncleared items get
re-fetched and **re-published** — duplicate confirmations (>1000 observed in the
original incident).

- **Mitigation shipped**: the customer-poll subscription's `ack_deadline_seconds` was
  raised to Pub/Sub's max (600s) so one invocation can usually complete and ack once.
  This reduces the frequency of redelivery; it does not make redelivery safe.
- **Durable fix ships too, as of this onboarding pass** {#idempotency}: despite the
  in-repo CLAUDE.md's note that this was "not in master," direct code inspection
  (2026-08-24, sha `8a73992`) confirms `ConfirmationsService.claimConfirmations()` +
  `CacheService.tryClaimConfirmation()` are live — each confirmation is claimed via
  `@gfs-bifrost/cache`'s `trySetIfNotExistsAsync` (`SET NX PX`) keyed on
  `identifiers.queueId` before publish. Outcomes: `"claimed"` → publish,
  `"duplicate"` → filtered out silently, `"unavailable"` (cache down) → **fails open**
  and still publishes (a live outage must not silently stop confirmations flowing).
  Treat the app's own CLAUDE.md idempotency section as **stale** until it's corrected
  in that repo.

## FUSE-1062 — work order queued at 29/39 is never cleared

`good_out`, `pick_confirmation` and `pack_confirmation` all exclude
`work_order_confirmation`'s underlying shipments from stages 29/39 (a work order is
only confirmed at fulfilment, stage 90) — so a work order sitting at 29 or 39 is left
unclaimed on the outbound queue indefinitely. Known and accepted as of the last
investigation touching this area; status of an active fix was not confirmed during
this onboarding pass — check FUSE-1062 directly before assuming either way.

## FUSE-1101 investigation residue — pick "QTY missing" left unexplained

During the FUSE-1101 pick/pack confirmation investigation (2026-08-20/21), three real
bugs were found and fixed (sftp-connector column-bucketing, a shared rules-engine
DSL Date gap, and pick confirmations never fetching Snap Stock Detail for
batch/expiry — mirrored from `PackConfirmationHandler`). A fourth reported symptom,
missing `QTY` on pick confirmations, was investigated directly in
`PickConfirmationHandler` and the DSL lookup path with **no code-level cause found** —
left as possibly SNAP test-data-specific (a genuinely-zero `QtyPicked` at test time)
rather than a real defect. If this resurfaces, don't assume the three merged fixes
cover it.

## SNAP confirmation emission is a stage+owner workflow rule, not something this
   service controls

SnapFulfil itself decides when a queue row appears, via configurable rules keyed on
stage + owner (e.g. "pick = Stage 29 AND Owner=<business>"). This service only reads
what SNAP already decided to queue — it cannot make SNAP emit a confirmation sooner,
and an empty poll is not evidence that nothing happened (the poll only runs every 2
min). On the shared dev SNAP tenant, **pick (29) is reliably reproducible via the
API**; **pack (39) and despatch (90) are not** — they appear to require a real pick
task / assigned StU, and StU/task write routes are 405 (read-only) over the API. Don't
attribute a queue row to your own test action by timing alone on a shared tenant —
match the `ShipmentId`/`ReceiptId` inside the row's `Key`.

## Ownership

No dedicated owner — the wider Fuse team maintains this alongside its sibling
`snap-adapter` (write side). Don't assume a single point of contact.

## Absorption from the archived repo

This app was absorbed into the `snap-adapter` monorepo (FUSE-952, PR #123,
2026-07-07) from a standalone `gfs-bifrost/snap-queue-polling-service` repo that is
now archived/read-only on GitHub. A separate local checkout of that archived repo
(`~/code/fuse/snap-queue-polling-service`) still fetches fine and looks alive — it
is not; a push to it fails outright. Always confirm you're in
`~/code/fuse/snap-adapter/apps/snap-queue-polling-service` before doing anything.

**Waypoint tooling caveat**: `wp.py locate`/`verify`/`stale` resolve a service by
matching `~/code/fuse/<service-name>` literally — for this service that resolves to
the dead archived checkout, not the monorepo where the real source and commit history
live. Don't trust a bare `wp verify snap-queue-polling-service <doc>` or `wp stale` run
here — it will silently anchor against/diff the wrong (dead) repo and never surface
real drift. The docs in this folder were hand-anchored with the correct sha/paths from
`~/code/fuse/snap-adapter` instead; re-anchor by hand the same way rather than trusting
the CLI's automatic repo resolution for this one service.

## Unknowns

- Whether FUSE-1062 (work order stuck at 29/39) has an active fix in flight, or is
  accepted as permanent behaviour.
- Whether the FUSE-1101 pick QTY-missing symptom is real or purely a test-data
  artifact — never conclusively resolved.
- No documented SLA/on-call rotation for this service specifically was found or
  confirmed — treat "wider Fuse team" as the operative answer, not a formal
  escalation path.

## Confirmation eligibility gating — a prior attempt already failed here (FUSE-1063, promoted 2026-09-17)

- **This is the second attempt at connector-level confirmation gating, not the first.**
  FUSE-808 tried to remove the business-level `confirmations` gate on the assumption
  that connectors would decide their own eligibility, but had to be reverted — the
  per-connector toggle it assumed didn't exist yet, so every mapped connector kept
  getting confirmation files regardless of intent (the `HOTFIX(FUSE-808 revert)`
  markers this predates removed). FUSE-1063 only retired the business-level gate once
  the real per-connector toggle existed *and* could be backfilled across every
  business — confirmed with the ticket owner this was a premature removal the first
  time, not a discovered blocker, so it's safe now. If a future change proposes
  removing the connector-level `confirmationsEnabled` gate or loosening its
  fail-closed default, check whether the backfill precondition that made *this*
  attempt safe still holds before assuming it will.
- **`confirmationsEnabled` absent reads as `false`, deliberately** — the opposite of
  this codebase's usual "absent means enabled" convention. Established from FUSE-1122's
  own PR text describing seeding `false` as a landmine "the moment [SFTP/Shopify] start
  honouring it," which only makes sense under fail-closed semantics. A production
  backfill (config-service's `migrate:confirmations-enabled` /
  `migrate:confirmations-enabled-sftp-shopify`) was required before this could ship,
  precisely because of this default.
- **Scope is deliberately narrow: the boolean toggle only.** Use-case/mapping
  eligibility (does the connector have the relevant `CONNECTOR_MAPPING` configured)
  stays enforced downstream, at each connector service (sftp-connector,
  shopify-connector, fapi) — verified none of the three duplicate a
  `confirmationsEnabled` check of their own. Don't assume this service's gate makes
  those downstream checks redundant; they're a different, still-necessary concern.

## Confirmation routing store (FUSE-1078, promoted 2026-09-14)

- **A confirmation handler cannot abort the poll.** `QueueLane.drainForClient` wraps
  every `mapOwnedEntries` in a per-consumer `.catch()` (logs "Unable to map
  confirmations", bumps `snap.poll.failure{businessId}`, returns `[]` for that handler
  this cycle — nothing claimed or published, siblings on the lane unaffected). Any
  "throw to abort the poll" reasoning in a handler is wrong; the catch is the safety net
  and must stay. Because `poll.failure` can't tell a SNAP outage from a Firestore one
  (only the log line carries `confirmationType`), the routing store read emits a
  dedicated `snap.routing_lookup.error{lane}` before it rethrows.
- **Reader-error vs miss is load-bearing.** `claimConfirmations` runs at *announce*
  time, so throwing in `mapConfirmation` (a reader error) is safe redelivery — nothing
  is claimed or published, it retries next cycle. Only a genuine *miss* falls back to
  the SNAP attachment, then to the unchanged manual-origin (broadcast) path. Never let a
  reader error silently degrade to a miss/broadcast.
- **Pick, pack and WOC fetch the shipment's `SHH` attachment only for routing.** `fetchShipmentAttachments(["SHH"])` feeds nothing but `extractRouting`, the pre-store fallback. That is one SNAP call per mapped record, there only for orders created before the Firestore write. Goods-out fetches `SHL` + `SHH` for the same reason, and goods-in reads its receipt's `REH` only for routing too. All of these can go when the attachment read is retired. RGA's `REH` read also carries the `RET_TRACK` return-tracking attachment, so retiring the routing read there only drops the `extractRouting` call, not the fetch. Checked against master `7c436f9`, 2026-10-05.
- **`good_in` store hits can't be manufactured in dev** — receiving is a SNAP-UI
  workflow, so a post-store PO must be physically received before `type:good_in` shows a
  store hit. Fallback reads on real PO-era receipts are the available live proof of the
  receipt-lane path; the despatch-lane types (pick/pack/good_out) hit far more readily.
