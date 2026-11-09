---
ticket: none
title: Exempt unqueried fields from Firestore indexing
service: tracking-service
status: active
created: '2026-11-06'
updated: '2026-11-06'
repo: /home/hjf/code/fuse/tracking-service
worktree: /home/hjf/code/fuse/tracking-service/.claude/worktrees/exempt-unqueried-firestore-fields
branch: hjf/exempt-unqueried-firestore-fields
base: origin/main
base_sha: b12d0a630
pr: '18'
tags:
- waypoint
- plan
impl_model: sonnet
impl_effort: medium
---
# none — Exempt unqueried fields from Firestore indexing

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
Out-of-ticket. Programme unit **D1** of [[Bifrost/Tracking Service/Migration State|Tracking Service]] group D: a cheap stopgap while persistence moves to MongoDB.

On 2026-11-06 at 09:10–09:16 UTC, 536 Firestore commits failed with `RESOURCE_EXHAUSTED` during PURDYFIGG's 5-minute reap bursts, which peaked at about 2,385 pushes a minute. Each of them then failed again as `InvalidArgument: The referenced transaction has expired`: the gapic Commit retry reuses the dead transaction id, and `RunTransaction` only retries `Aborted`. Pub/Sub redelivery healed it and nothing reached a DLT.

The leading hypothesis is an index write hotspot. Every copy rewrites indexed fields that nothing queries, starting with `lastSeenAt`, which only ever increases. This change exempts every such field from single-field indexing. Proof: bursts stop producing `RESOURCE_EXHAUSTED`.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [ ] 1. In both databases, these fields report no single-field indexes:
  - `shipments`: `lastSeenAt`, `totalDuplicates`, `stageTimes`, `confirmations`;
  - `returns`: `lastSeenAt`, `totalDuplicates`, `stageTimes`, `confirmation`, `linkedShipmentJson`.
  - Every existing query still serves: the composite indexes and the other fields' automatic indexes are untouched.
- [ ] 2. `firestore.indexes.json` and `firestore.tf` declare the same overrides (the `declared_field_overrides` precondition passes), and the emulator suite is green.
- [ ] 3. In prod, over at least 48 h of reap bursts, `gcp.firestore.api.request_count{database_id:tracking-service,response_code:resource_exhausted}` and Cloud Run 5xx are compared against the 2026-11-06 baseline, and the result is recorded against programme gate G3. It counts either way: if the throttling persists, the hypothesis is refuted, and that is also a result.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `apps/api/firestore.indexes.json` `fieldOverrides`, plus 9 `google_firestore_field` resources appended to the end of the `depends_on` chain in `iac/projects/tracking-service/firestore.tf`, plus `local.declared_field_overrides`.
- No Go code. No contract change: served fields are unchanged; only their indexing changes.
- `database-collections` in fuse-mcp describes collections, not index config, so it needs no change. Confirm at sign-off.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- **None of the 9 fields is filtered or ordered by any query, and none is in a composite index.**
  - Established 2026-11-06 by two independent source reads.
  - The queried fields are `businessId`, `status`, `failed`, `orphan`, `channel`, `searchKeys`, `attentionAt`, `actionNeeded`, `customerRefNorm`, `rgaNumberNorm`, `createdAt`, `updatedAt` and `day`.
  - `orderedQuery` sorts only on `updatedAt`/`createdAt`.
- **Which copies this covers.**
  - A reap copy (received, deduplicated, in_wms) moves `lastSeenAt`, `totalDuplicates` and unindexed `*Json` blobs, so this removes all of its index writes.
  - Confirmation re-announce copies also move `confirmations.*.lastDeliveredAt`, `.deliveryFailedAt` and `.queueIdKeyJson` (`reduce.go:112-127`), and `stageTimes.despatched` (`reduce.go:521-522`). All of those are covered too.
  - Not covered, because the fields are queried:
    - a create-failed copy can flip `failed`/`status`/`attentionAt` (`reduce.go:104,533-537`);
    - an out-of-order earlier copy can lower `updatedAt` (`dedupe.go:160,207`).
  - Established by the factual review, 2026-11-06.
- **Exempting a map field (`stageTimes`, `confirmations`, `confirmation`) exempts its subfields.** This is Firestore's documented inheritance, not checked on this database. Verify on dev with `gcloud firestore indexes fields describe` on one subfield.
- **Firestore applies an exemption by rewriting the index entries of existing docs.** So on populated `shipments`/`returns` each field operation takes longer than the ~6 min measured on the empty database at cutover. Unmeasured; dev times it first.
- **The hotspot is the cause of the 11-06 `RESOURCE_EXHAUSTED`.** UNPROVEN. Key Visualizer was not checked, and on 2026-10-29 a 4,497-push minute caused no throttling. AC 3 tests it.
- UNRESOLVED: the G3 threshold, i.e. what drop in `resource_exhausted` during bursts counts as "fixed". It needs agreeing with Harry before merge, or the soak can't decide anything.

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

- [x] 1. **Declare the 9 exemptions** (AC 1,2). Add them to `fieldOverrides` in `firestore.indexes.json` and as `google_firestore_field` resources with `index_config {}`, each `depends_on` the previous, appended after `events_errors_json`, plus `local.declared_field_overrides`. — verify: — gates green; dev plan via PR tf-plan — done: c52f644
  - `terraform fmt -check -recursive iac` passes;
  - `make fmt-check vet lint test-race test-emulator` passes;
  - `indexes_test.go` passes;
  - the dev `terragrunt plan` shows exactly 9 resources to add and nothing else.
- [x] 2. **Apply to dev and time it** (AC 1). Merge, which applies dev and then parks the prod apply behind `terraform-prod`. Don't push to `main` while the Deploy run is in flight. — verify: — dev 9/9 exempt, 56 min; API 200s — done: c52f644
  - `gcloud firestore indexes fields describe` reports the 9 fields, plus one map subfield, as exempt on the dev database;
  - the wall-clock time per field operation is recorded;
  - dev `/api/v1` list, search, attention and stats calls still answer.
      gate: Harry agrees the prod Terraform plan (plan-then-proceed) and the G3 threshold
            [x] confirmed
- [ ] 3. **Apply to prod and soak** (AC 1,3). Approve `terraform-prod`. The run stays open for roughly 9 × the dev per-field time. — verify:
  - `gcloud ... describe` on the prod database;
  - 48 h of burst minutes: `resource_exhausted` count, Cloud Run 5xx and commit latency, against 09:10–09:16 on 2026-11-06;
  - the result is written to G3 in the Migration State.
  - Use GCP-side metrics, not `fuse.tracking.*`, which undercounts.

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
- 2026-11-06 [inc 3] **Prod applied and verified; G3 soak started 15:40:40Z.** Deploy run 42226342798 `terraform-apply-prod` (job 127949952620) ran 14:34:18–15:40:40Z, **66 min for 9 field ops (~7.4 min each on prod's 89k shipments)**, `Apply complete! Resources: 9 added, 1 changed, 0 destroyed.` `gcloud firestore indexes fields describe … --database=tracking-service --project=bifrost-prod-global1` at 15:41Z: all 9 fields report 0 indexes (`shipments` `lastSeenAt`, `totalDuplicates`, `stageTimes`, `confirmations`; `returns` `lastSeenAt`, `totalDuplicates`, `stageTimes`, `confirmation`, `linkedShipmentJson`); the map subfield `shipments.stageTimes.despatched` inherits from `stageTimes` (0); control `shipments.updatedAt` keeps its 3. `tracking-service-api-prod` serves `prod-44734ac…`. Prod API with an ID token at 15:41Z: `/health`, `/api/v1/shipments?limit=1`, `?lane=action`, `/api/v1/returns?limit=1`, `/api/v1/stats`, `/api/v1/stats/businesses` all 200 (`/stats/businesses` took 9.0 s). (AC 1, prod)
- 2026-11-06 [inc 3] **Pre-soak baseline, prod** (`sum:gcp.firestore.api.request_count{database_id:tracking-service,response_code:resource_exhausted,project_id:bifrost-prod-global1}`, per minute, 2026-11-05 00:00Z → 15:25Z 11-06): 1,026 in total today. 09:11–09:17Z = 536 (the incident), **11:20–11:22Z = 486** (a second burst, before D1 reached any database), 00:51/00:56Z = 4; none 11:23Z → 15:25Z. The soak compares burst minutes from 15:40:40Z against these. (AC 3, baseline)
- 2026-11-06 [inc 2] **Dev applied and verified.** Deploy run 42226342798 (merge `44734ac`, PR #18); `terraform-apply-dev` ran 13:34:24–14:30:45Z, **56 min for 9 field ops (~6.3 min each on the populated dev database)**. `gcloud firestore indexes fields describe` on `bifrost-dev-global1/tracking-service`: all 9 fields report 0 indexes; the map subfield `shipments.stageTimes.despatched` inherits from `stageTimes` (ancestorField `.../shipments/fields/stageTimes`, 0 indexes), so the map-inheritance assumption holds; control `shipments.updatedAt` keeps its 3. Dev API with an ID token: `/health`, `/api/v1/shipments?limit=1`, `?lane=action`, `?search=HJF`, `/api/v1/returns?limit=1`, `/api/v1/stats`, `/api/v1/stats/businesses` all 200. (AC 1, dev)
- 2026-11-06 [inc 2] **Prod plan checked before approval** (`terraform-plan-prod` job 127949642667): `Plan: 9 to add, 1 to change, 0 to destroy`, the same 9 `google_firestore_field` adds plus the routine Cloud Run image (`prod-b12d0a6…` → `prod-44734ac…`) and masked Datadog env bump. Harry agreed the plan and the G3 bar (zero `resource_exhausted` commits in reap-burst minutes over 48 h, `gcp.firestore.api.request_count{database_id:tracking-service}`) on 2026-11-06 ("yes, ship it"); `terraform-prod` approved 14:3xZ.
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->


### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
> SUPERSEDED 2026-11-06 — AC 1 is verified in prod (Evidence, inc 3). Only AC 3 remains.

- AC 1 in prod and AC 3 (the 48 h soak) — pending the prod apply and two days of bursts.
- AC 3: the 48 h soak runs 2026-11-06T15:40:40Z → no earlier than 2026-11-08T15:41Z. Read it then against the baseline above; tick inc 3 only after.

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
- **The 2026-11-06 burst errors are `RESOURCE_EXHAUSTED` underneath.** The surfaced `InvalidArgument: transaction has expired` comes from the gapic Commit retry (`firestore/apiv1` v1.25.0 retries Commit on ResourceExhausted/Unavailable, reusing the transaction id). `RunTransaction` retries only `Aborted`. Every throttled commit therefore shows up as 1 RE plus 1 IA in `gcp.firestore.api.request_count`. This is the first store-error incident on the new stack.
- **Copy-redelivery protection is capped.** `CountedIDs` keeps 64 ids per record (`dedupe.go:22`), which is about 1.5–2 h of PURDYFIGG resends. Older redelivered copies count again.
- **Prod Firestore has point-in-time recovery disabled** (`firestore.tf:9`). There is no backup of the `tracking-service` database.
- **`api-emulator` is one of the 8 required checks on `main`.**

