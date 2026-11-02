---
ticket: none
title: 'SHIP-1019-retry-queue-failure-point: show where each failure happened'
service: replay-service
status: complete
created: '2026-10-19'
updated: '2026-10-19'
repo: /home/hjf/code/fuse/replay-service
worktree: /home/hjf/code/fuse/replay-service/.claude/worktrees/reattribution-run
branch: hjf/groups-filter-parity
base: origin/main
base_sha: bb2a99814
pr: '121'
tags:
- waypoint
- plan
---
# SHIP-1019 — Retry Queue: show where each failure happened

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
Out-of-ticket, shipped autonomously via `/ship` (ID `SHIP-1019-retry-queue-failure-point`). An ILG operator looking at the Retry Queue needs to answer "did this die on the SFTP side or at Snap?" without opening the record. Replay derives a stable `failurePoint` key for every failure at read time, from fields that never change after ingest, and returns it on list and detail so the UI can show, filter and group by it. Failures whose record carries no businessId (whole-file SFTP failures, every Shopify ingest failure) currently land under `businessId: ""` and appear in no customer's queue; they are attributed to the envelope's customer instead. The fuse-ui side shipped as gfs-bifrost/fuse-ui#341 (claimed filter on group counts) and #343 (Where It Failed column, filter and grouping). There is no separate fuse-ui plan.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
1. [ ] `GET /failures/groups` honours every list filter (`createdAt`, `reason`, `connectorId`, `transaction`, `assigned`, `resolved` as well as the four it took), so a group's count equals the rows the list returns for it.
2. [ ] Every row from `GET /failures` and `GET /failures/:id` carries a non-empty `failurePoint` from a fixed enum, plus `stage` and `source` on the summary.
3. [ ] `GET /failures?failurePoint=<key>` (repeatable) narrows the list, and `GET /failures/groups?groupBy=failurePoint` buckets by it, agreeing with each other.
4. [ ] A failure whose record yields no businessId is stored under its envelope `metadata.customer`; a record that carries one keeps it (routed sales orders legitimately differ from the connector's business).
5. [ ] Existing prod rows with `businessId: ""` have a reviewed, reversible path to re-attribution (survey → plan file → apply only listed ids), and the survey's grouped output has been reviewed by Harry before any apply.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `code/src/core/failure/` — new `derive-failure-point.ts` + `failure-point-expression.ts` (hand-mirrored pair, same pattern as `derive-reason.ts` / `reason-expression.ts`); `failure.service.ts` (`buildQuery`, `getFailureGroups`, `extractBusinessId`).
- `code/src/repositories/collection.ts` — `count` / `groupByExpression` gain an opt-in `includeDeleted` (for `resolved=true` parity).
- `code/src/http/controllers/failures.controller.ts` + `http/dtos/failure.dto.ts` — admin API contract (additive fields, filter, groupBy value). fuse-ui regenerates its client from dev's `/api-json`.
- `code/scripts/` — the re-attribution script.
- Fuse MCP `api-endpoints.json` (new query params) — sign-off check.
- Must NOT change: redrive routing (G3, reads `failure.source` as a channel), clear-down keys (G4), store-as-received (G2).

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- fuse-ui is ILG-internal, so labels may name Snap — fuse-ui known-context (2026-08-24), design.md.
- Rows with no `stage` on an inbound type are snap-adapter WMS rejections from the legacy `release_*` ingest, removed 2026-07-02 (d99d272, FUSE-733) — history review + memory `reference_deduper_release_not_failure`.
- `source` keeps its mixed meaning (connectors stamp their channel; snap-adapter, the poller and shopify-egress stamp their service name) pending the approved-but-unscheduled channel-on-envelope work — `project_channel_connectorid_traceability` (2026-07-11); classifier normalises `sftp-connector` → `sftp`.
- Confirmation rows are classified by source, not stage: fapi stamps `confirmation_made` for a delivery failure while shopify/sftp stamp `confirmation_ready` — source read across producers.
- Attribution is record-first with `metadata.customer` fallback, matching tracking-service (`events.go:129-134`), so fuse-ui's order-tracker links into replay stay consistent — history review.
- Sibling businesses may NOT cross-send PO/MD/WO (Harry, 2026-10-19). Polluted record businessIds are fixed at sftp ingest under a separate defect, not here.
- snap-adapter `schema_validation` covers both the canonical re-check and the Snap-shaped pre-check (both `shared/zod.ts`), so `create.wms_precheck` is worded "stopped by Fuse before Snap"; an exhausted Snap 5xx is indistinguishable from a 4xx rejection until the snap-adapter retryable defect lands, so `create.snap_api` is worded "Snap returned an error".

## Failure-point mapping
First match wins. Side = `create` for `sales_order`/`purchase_order`/`master_data`/`work_order`, else `confirmation`.

| Condition | Key |
|---|---|
| create, no stage | `create.wms_legacy` |
| confirmation, no stage | `confirmation.not_recorded` |
| confirmation, any error `rule` = `no_originating_connector` | `confirmation.broadcast_notice` |
| confirmation, source `snap-queue-polling-service` | `confirmation.wms_read` |
| confirmation, source `snap-adapter` | `confirmation.wms_clear` |
| confirmation, source `shopify` / `shopify-egress-service` | `confirmation.delivery_shopify` |
| confirmation, source `sftp` / `sftp-connector` | `confirmation.delivery_sftp` |
| confirmation, source `rest` | `confirmation.delivery_rest` |
| create, stage `ingest`, sftp, first error `field` = `file` | `create.sftp_file` |
| create, stage `ingest`, sftp | `create.sftp_row` |
| create, stage `ingest`, shopify | `create.shopify_ingest` |
| create, stage `wms_submission`, first error `type` = `validation` | `create.wms_precheck` |
| create, stage `wms_submission`, first error `dependency` = `snap-credentials` | `create.snap_credentials` |
| create, stage `wms_submission`, first error `operation` = `lookup_nmfc` | `create.snap_product_lookup` |
| create, stage `wms_submission`, first error `dependency` = `snap` | `create.snap_api` |
| create, stage `wms_submission` (anything else) | `create.snap_adapter_internal` |
| anything else | `<side>.unclassified` |

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

- [x] 1. `/groups` takes every list filter, incl. `resolved` via opt-in `includeDeleted` on `count`/`groupByExpression` — own PR off main, pre-existing bug (AC 1) — verify: integration spec per newly-honoured filter (group count == list total); dev: `/groups?groupBy=reason&assigned=true` total equals `/failures?assigned=true` total for HJF — dev GADG assigned 2/2, resolved 8/8; prod 66ca610 — done: 9d4e550
- [x] 2. `failurePoint` derived on list + detail, with `stage`/`source` on the summary; filter + `groupBy=failurePoint`; OpenAPI enum; CLAUDE.md corrections (bulk-envelope claim, `/groups` filters, `source` wording) (AC 2,3) — verify: unit cases written per producer from the §1 inventory (expected key from what the producer emits, not from the table); integration parity spec TS vs Mongo expression over real Mongo; dev: induce one failure per reachable place (DAZZA SFTP bad row + unreadable file, mock-send invalid SO for wms_precheck, simulator fault for snap_api, poller partial order) and read each key back — dev 605k classified (2 synthetic unclassified); prod groups == filter — done: c2db77d
      gate: dev replay running this branch's sha before reading results
            [x] confirmed — dev ran d82c68e then 6c75d01 (checked image tag) before results were read
- [x] 3. `extractBusinessId` falls back to `metadata.customer` when the record yields `""` (AC 4) — verify: e2e create-failure (no-record whole-file, raw-Shopify-shaped record → customer; record with businessId → kept), confirmation-failure (record kept; empty → customer); dev: DAZZA unreadable file lands under DAZZA, not `""` — dev DAZZA whole-file failure filed under DAZZA — done: e664645
- [x] 4. Re-attribution script: `survey` (read-only, groups `businessId: ""` rows by useCase/source/customer), `plan` (writes ids to a file), `apply --plan` (sets `businessId` = `metadata.customer` only where still `""`, stamps `attribution: { previousBusinessId: "", at, by }`, refuses rows already stamped), `revert --plan` (AC 5) — verify: integration spec on mongodb-memory-server for survey/plan/apply/idempotence/revert; dev survey + apply + revert round-trip — 14 spec tests; dev plan/apply/revert round-trip — done: 66ca610
- [x] 5. Prod re-attribution — operation, no PR (AC 5) — 540/540 applied in prod; plan archived for revert — done: 66ca610
      gate: increment 3 live in prod; Harry has reviewed the prod survey output and approved the apply (prod data mutation is outside /ship's authority)
            [x] confirmed — Harry approved all 540 in conversation, 2026-10-19

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-19 [inc 5] Prod re-attribution. Re-ran the prod survey after #122 went live: 540 rows, identical to the approved survey. `apply` returned `{planned:540, changed:540}`, and a second survey showed 0 rows left with no business. The prod API shows `8df184f8` under SAIRA (`create.shopify_ingest`), and SAIRA's queue holds its 270 Shopify ingest failures. The plan file is archived at `plans/artifacts/ship-1019-prod-reattribution-plan.json`, so `revert --plan` can undo exactly this run.
- 2026-10-19 [inc 4] Integration spec, 14 tests (survey, plan record-first exclusion, apply customer/dismissed/race guards, malformed plan refused, idempotent, revert exact). The CLI was smoke-tested end to end on a throwaway Mongo (2 applied, then 2 reverted). The prod survey is still owed (gate).
- 2026-10-19 [inc 3] Dev (`replay:dev-6c75d01`), DAZZA SFTP harness. An unmappable file → a whole-file failure with no record, stored as `175e197c` with `businessId: DAZZA` and `failurePoint: create.sftp_file` (on `main` it would have been `""`). The harness was reverted (connector inactive, file removed).
- 2026-10-19 [inc 2] Dev, all 605,184 failures grouped by `failurePoint` in 4.9 s. Only 2 were `create.unclassified`, both synthetic test rows (`test-harness`, `fuse-832-e2e-test`).
  - Per business (HJF, DAZZA, PURDYFIGG), each group count equalled the `?failurePoint=` list total.
  - An unknown key returned 400.
  - Every row on a 100-row page carried `failurePoint`.
  - The client generated from dev `/api-json` was byte-identical to the local build's.
- 2026-10-19 [inc 2] fuse-ui#343, run locally against dev replay. Screenshots (PURDYFIGG grouped by place; HJF Failed at SFTP and detail) are on the `hjf/groups-filter-parity-evidence` branch.
- 2026-10-19 [inc 1] Dev (`replay:dev-d82c68e`), GADG. `assigned=true` list 2 / groups 2; `resolved=true` 8 / 8; `replayed=true` 31 / 31. HJF matched for six filters. On fuse-ui (#341), GADG In Progress grouped gave 2 groups of 1.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->
- 2026-10-19 — Increment 2 was verified differently from the plan. The plan was to induce one failure per place. Instead every one of dev's 605,184 real failures was grouped (their origin is the real producers), plus one induced failure (DAZZA SFTP, whole file). The real-data check covers more producer paths than staging one failure each would, and only 2 synthetic rows came out unclassified.
- 2026-10-19 — The replay stack merged atomically (`gh stack merge`, `66ca610`). Prod gate approved after the plan review showed only the image tag and standing drift. Four stale parked Deploy runs, ancestors of the approved sha, were cancelled. fuse-ui merged after replay#121 was live in prod (checked: prod `?failurePoint=create.bogus` returns 400), because an older replay ignores the filter.
- 2026-10-19 — fuse-ui's `create.snap_adapter_internal` stays in the Fuse zone, labelled "Fuse's Snap step didn't finish (outage or Fuse error)". It is snap-adapter's catch-all and holds failures that never reached Snap (13 prod `invalid_deterministic_id`). FUSE-1319 moves outages to `create.snap_api` at the producer.
- 2026-10-19 — Scope cut from the first draft after three reviews: sftp-connector unresolvable-file handling, the SFTP cross-business Snap write, snap-adapter's non-retryable exhausted 5xx, shopify's raw-payload failure record, and dismissing the 39k broadcast-notice + 77 PURDYFIGG wrapper rows each became their own defect/ticket (Harry approved filing). pkg-node doc/catalogue changes and `upstream` deprecation dropped (no AC needs them). `source` semantics left as-is (option c).
- 2026-10-19 — Hand-mirrored TS function + Mongo expression with a parity spec, not a rule-table compiler: follows the existing `reason` pattern, avoids a new abstraction (agents.md stop condition).
- 2026-10-19 — Re-attribution as a survey→plan→apply script, not an admin endpoint: fleet precedent (FUSE-1078 backfill, routing-doc repair) and no new bulk-mutation surface on a public service behind a shared key.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
