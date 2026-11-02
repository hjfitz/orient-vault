---
ticket: FUSE-1265
title: Route confirmation records that fail validation to the retry queue
service: sftp-connector
status: complete
created: '2026-09-24'
updated: '2026-09-24'
repo: /home/hjf/code/fuse/sftp-connector
worktree: /home/hjf/code/fuse/sftp-connector/.claude/worktrees/fuse-1265
branch: hjf/fuse-1265-confirmation-decode-drop
base: a7fcb1363c96a4290138d42be7b93c3ec68e13b0
base_sha: a7fcb1363
pr: '282'
tags:
- waypoint
- plan
programme: "edi-support"
unit: "R1"
---
# FUSE-1265 — Route confirmation records that fail validation to the retry queue

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
[FUSE-1265](https://gfsdeliver.atlassian.net/browse/FUSE-1265). `decodeAgainst` silently drops confirmation records that fail their canonical schema; when every record drops, egress still emits an empty `confirmation_made` and counts `result:delivered`. Instead, dropped records go to `confirmation_data_failure` (Retry Queue) with their validation issues, an all-dropped batch emits no made and writes no file, and `fuse.confirmation.forward` reports `result:zod_dropped`.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. A record failing canonical validation is published to `confirmation_data_failure` with the raw record and `type: validation` errors (field + problem).
- [x] 2. When every record is dropped: no file, no `confirmation_made`, no `delivered`.
- [x] 3. `fuse.confirmation.forward` counts `result:zod_dropped` (with `type` + `fileType`, per distinct target file type, like `delivered`).
- [x] 4. Mixed batch: valid records write/emit made/count delivered exactly as today; invalid ones go to failure. — unit-tested only (mixed batch not driven in dev)
- [x] 5. The "Record failed validation" log carries the dropped records' `orderRefs`.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `code/src/confirmations/confirmations.service.ts` (`decodeConfirmations` returns `{ valid, invalid }`)
- `code/src/confirmations/confirmation-egress.service.ts` (`process`)
- `code/src/confirmations/to-confirmation-failure.ts` (validation failure mapper)
- Contract: `confirmation_data_failure` bulk envelope — same shape as the write-failure path, new error `type: validation`. No topic/type/MCP data change.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- Failures are only published once at least one eligible target exists — a broadcast confirmation for a business sftp-connector doesn't serve must not land in the Retry Queue — source read (`selectTargets`, `logUnresolvableConnector`).
- Stock adjustments validate the whole bulk envelope at the controller (`BifrostBulkMessageSchema(CanonicalStockAdjustmentSchema)`), so one bad record rejects the batch (MessageDecodeFailed, 204) — structurally different, out of scope, reported — source read.

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

- [x] 1. Decode returns rejected records; egress publishes them as validation failures, counts zod_dropped, and skips write/made when none survive; log carries orderRefs (AC 1,2,3,4,5) — verify: unit tests + lint + build:check — 697 tests pass; lint 0; build:check 0 — done: c0678ba
- [x] 2. Dev e2e: invalid pick (no `lines[].role`) → failure in dev replay, no made, no file, zod_dropped metric; valid GADG goods-in unchanged (AC 1,2,3,4) — verify: logs, replay-list-failures, Datadog metric — dev: replay failure 5826767a, zod_dropped=1, no made/file; goods-in regression unchanged — done: c0678ba

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-09-24 [prod] Shipped with #282+#283 as `30871dc` (Harry: "ship 282 and 283"); prod plan image-only + standing sidecar drift; both gates approved; revision `sftp-connector-prod-cr-00097-gpl` Ready. 19:03–19:27Z on it: 6 STUBBLE sales-order validations 0 invalid, 2 confirmations written + processed, no warn/error.
- 2026-09-24 [inc 2] Dev @ 7807964 (rev sftp-connector-dev-cr-00795-t6l), 18:15Z. GADG pick with `lines[].role` removed (`mock-fuse1265-drop-1`, broadcast): "Record failed validation" orderRefs `[GADGPCK1265BAD]` → "Confirmation records that failed validation published" topic `bifrost.dev.confirmation_data_failure.v1` failedCount 1 → "Every confirmation record failed validation — no file written"; no `Confirmation processed`, no `confirmation/made` for the id in any service; no object under `FUSE_4E7E60F55B/from_ilg/pick_confirmation_confirmations/2026-09-24-18*`. Replay failure `5826767a-6976-4bf1-a658-529a5c443321` (pick_confirmation, GADG, recordId GADGPCK1265BAD, stage confirmation_ready, errors `validation` lines.0.role / lines.1.role, replayable false with matching blockingIssues). Datadog `sum:fuse.confirmation.forward{service:sftp_connector,environment:dev} by {result,type,filetype}` 18:14Z→: pick zod_dropped/jsonl = 1, no pick delivered.
- 2026-09-24 [inc 2] Same deploy: HJF invalid pick (`mock-fuse1265-drop-hjf-1`) — HJF's only connector is edi with the flag off → NoEligibleConnectors, forward skipped (no fileType) = 1, no replay failure (search HJFPCK1265BAD → 0). Confirms failures only publish once a target exists.
- 2026-09-24 [inc 2] Same deploy: valid GADG goods-in (`mock-fuse1265-regression-1`) unchanged — 3 files written (2 csv + 1 jsonl, e.g. `FUSE_D89734E435/from_ilg/purchase_order_confirmations/2026-09-24-1815-confirmation.csv` 286B), Confirmation processed, collector `POST /events/v1/confirmation/made/purchase_order 204`, forward delivered csv=1 jsonl=1.
- 2026-09-24 [inc 1] vitest 697/697, `pnpm run lint` 0, `pnpm run build:check` 0 at 7807964.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- Mixed valid+invalid batch only unit-tested, not driven in dev.
- SNAP re-announce: with no `confirmation_made` the poller re-announces the record (subject to its queueId claim TTL), so a persistently invalid record may publish a failure per re-announce — same property as the existing write-failure path; not measured.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-09-24** — Reused import/translators validateRecords + toValidationErrors rather than duplicating the per-issue mapping; failure errors are type:validation, record is the raw (unparsed) record so replay's blockingIssues can show it.

- **2026-09-24** — Stock adjustments not changed: the controller validates the whole bulk envelope (BifrostBulkMessageSchema(CanonicalStockAdjustmentSchema)), so one bad record rejects the batch as MessageDecodeFailed + 204 — no per-record drop, and stock_adjustment has no confirmation failure mapping. Structurally different; reported, not widened.

- **2026-09-24** — Mixed batch: valid records write, emit made (valid only) and count delivered exactly as before; invalid records go to confirmation_data_failure and count zod_dropped (per distinct target fileType, like delivered). Failures/zod_dropped only once an eligible target exists — no-target/unsupported-type paths unchanged.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
