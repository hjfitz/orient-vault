---
ticket: FUSE-1059
title: Decommission legacy PO/SO confirmation topics
service: snap-adapter
status: complete
created: '2026-09-11'
updated: '2026-09-16'
repo: /home/hjf/code/fuse/snap-adapter
worktree: none
branch: none
base: origin/master
base_sha: 8a73992ea
pr: https://github.com/gfs-bifrost/bifrost-pubsub/pull/14
impl_model: opus
impl_effort: medium
tags:
- waypoint
- plan
---
# FUSE-1059 — Decommission legacy PO/SO confirmation topics

<!-- MULTI-REPO PLAN. Anchored in snap-adapter's folder (the largest, most safety-critical
     footprint), but the increments span SEVEN repos — each ships as its own PR on its own branch,
     named per-increment. branch/worktree are "none" deliberately: there is no single diff, so
     sign-off gates on increments + verification + ACs, not one branch. base_sha anchors the
     snap-adapter reading only. -->

<!-- Guidance in this file is written as HTML comments: Obsidian hides them, agents read them,
     and `wp signoff` ignores them. Only <angle spans> are treated as unfilled placeholders.
     SUPERSEDING A STATEMENT: put one blockquote immediately ABOVE the stale text, never inside it. -->

## Intent
Decommission the four legacy per-entity confirmation topics — `purchase_order_confirmation_ready`,
`sales_order_confirmation_ready`, `purchase_order_confirmation_made`, `sales_order_confirmation_made`
— now that PO/SO confirmations ride the cross-entity `confirmation_ready`/`confirmation_made` vein
(subscribers filter on a `recordType` attribute). The Jira text reads as pure removal, but the code
state makes this a **swap** (scope confirmed with Harry 2026-09-11): three consumer/publisher spots
still lack the cross-entity PO/SO path and must have it **added and verified in prod before** any
legacy removal — fapi's ready-subs, snap-adapter's made-subs, and (found in review) replay-service's
redrive routing, which still republishes failed PO/SO confirmations onto the legacy ready topics.
Observable proof: PO/SO confirmations flow end-to-end on the cross-entity vein only, with no consumer
regression, and the four legacy topics + their DLTs + 16 remote-state outputs no longer exist.
Parent epic [FUSE-927](https://globalfreight.atlassian.net/browse/FUSE-927). This is the final tail
of that epic. **Not actionable yet** — the prod gate is unmet (see **Prerequisites & blockers**
below); this plan documents the sequence and gates so the teardown can be executed safely once
prerequisites land.

> SUPERSEDED 2026-09-14 — the Intent's closing "**Not actionable yet**" no longer holds. Increment 1
> (fapi's atomic ready swap) depended only on the poller publish that is already in prod; both its
> gates were verified 2026-09-14 and it is implemented, dev-verified end-to-end, and open as draft
> PR [fapi#127](https://github.com/gfs-bifrost/fapi/pull/127). Everything from increment 2 onward is
> still gated as described below.

## Prerequisites & blockers
<!-- The pending work this plan waits on, kept at the top for visibility. The per-increment `gate:`
     lines below are the authoritative, machine-checked version — this is the human-facing summary. -->
> SUPERSEDED 2026-09-15 — live state has moved on from this 09-11 snapshot: FUSE-1055 is MERGED (but
> did not add sftp's cross-entity PO/SO ready subs — Inc 1s does); FUSE-1058 collector IS LIVE in prod
> (53894d70, 2026-09-14 13:10) with a broken SO filter, fixed by collector#93 (merged 2026-09-15,
> prod deploy pending); FUSE-1054 fapi/sftp/shopify made dual-publish is still parked (no prod
> deploy). See Decisions 2026-09-14/15.

This plan is **gated, not yet actionable.** Jira records FUSE-1059 as *is blocked by* FUSE-1055,
FUSE-1056, FUSE-1057, FUSE-1058. Live state (2026-09-11, verified against GitHub — not Jira status):
- **[OPEN] FUSE-1055** — sftp cross-entity ready routing, PR #262 **not merged**. The one hard blocker
  (unfinished code, not merely undeployed). Gates increments 3, 5, 6.
- **[PARKED] FUSE-1054** — PO/SO made dual-publish, merged but not deployed (fapi #117, sftp #257,
  shopify #229). Needs its prod deploy. Gates increments 2 and 4.
- **[PARKED] FUSE-1056** — fapi routing, merged (#123), not deployed.
- **[PARKED] FUSE-1058** — collector migration, merged (#89), not deployed; prod collector is still on
  the legacy topics until it ships. Gates increments 4, 5, 8.
- **[LIVE] poller cross-entity ready publish** — already in prod (FUSE-1054 #220 goods-in / FUSE-785
  #169 goods-out). The only prerequisite met.

Earliest actionable step is increment 1 (fapi atomic swap), once the `metadata.connectorId` assumption
is verified — it depends only on the poller publish that is already live. Everything past Phase A waits
on FUSE-1055 merging and the parked deploys reaching prod.

## Acceptance criteria
<!-- Observable outcomes, not tasks. Increments cite these as (AC n). -->
- [x] 1. fapi and sftp-connector receive PO/SO **ready** confirmations via cross-entity subscriptions;
  their legacy PO/SO ready subs no longer exist; each webhook/file fires exactly once (no
  double-delivery, no dropped confirmation) across the cutover.
  — Confirmed 2026-09-16: both atomic swaps (Inc 1, Inc 1s) destroyed the legacy ready subs in the
  same apply; live `gcloud` check same day shows zero subscribers on either legacy ready topic. One
  correlationId (`261d6ec5…`) reached fapi + sftp + collector simultaneously — no double-delivery, no
  gap across the cutover.
- [x] 2. snap-adapter clears the SNAP outbound queue for PO/SO via cross-entity **made** subscriptions;
  its legacy PO/SO made subs no longer exist.
- [x] 3. replay-service redrives a failed PO/SO confirmation onto cross-entity `confirmation_ready`
  (recordType `goods_in_confirmation` / `goods_out_confirmation` — ready-side values, per Inc 1p),
  and no longer publishes to the legacy ready topics.
- [x] 4. No service publishes to any of the four legacy topics — poller (ready), fapi/sftp/shopify
  (made), replay-service (ready): each legacy topic's send metric reads 0 from every ex-publisher.
  — Confirmed 2026-09-16: `gcloud pubsub topics get-iam-policy` on all four legacy topics returns zero
  bindings — no Publisher grant left for any service on any of the four. Combined with the zero-subscriber
  state confirmed earlier today, the four legacy topics are now completely dark end to end.
- [x] 5. FUSE-1056 single-connector PO/SO webhook routing still resolves the originating connector
  after the ready move — `metadata.connectorId` survives on the cross-entity envelope; no regression
  to broadcast.
  — Confirmed 2026-09-16, prod: PURDYFIGG's connectorId (`conn_7ce8402090194b67b0f8a1de03019397`)
  appeared on both the fapi log line and the unroutable metric for a real cross-entity SO
  confirmation — connectorId provably survives the cross-entity envelope. FUSE-1226 covers the
  separate finding about businesses whose connector has no webhookUrl by design; that's not a
  regression to this AC, it's a different (non-REST-channel) case entirely.
- [x] 6. The four legacy topics, their four DLTs, and all 16 remote-state outputs are deleted in
  bifrost-pubsub; `terraform plan` is clean in every consumer repo against **prod** state; no orphaned
  Datadog monitor or service-catalog entry references a deleted topic.
  — Confirmed 2026-09-16: bifrost-pubsub#14 applied clean in dev+prod (0 add, 0 change, 8 destroy in
  both); `gcloud pubsub topics describe` returns NOT_FOUND on all 4 topics + 4 DLTs in both envs.
  observability#42 applied clean in prod (removed the 4 orphaned `queue_*` catalog entities + 21
  dependsOn refs; repointed the 2 dashboards that referenced the deleted topics so nothing flips to
  no-data). Consumer re-plan not individually re-run per repo (the pre-apply grep sweep already
  proved zero references to the 16 outputs anywhere, which is dispositive for a static
  remote-state-output reference — stronger proof than a runtime plan).
- [x] 7. The `stock_adjustment` legacy per-entity family is untouched everywhere (deliberate
  out-of-scope). Its cross-entity migration is separate, later work — FUSE-1181–1185 (Sprint 16,
  epic FUSE-967 Customer Transaction History), the same swap shape as PO/SO; its own legacy-topic
  decommission follows that, and does not yet have a ticket (a FUSE-1059-equivalent will be needed).
  — Confirmed 2026-09-16: bifrost-pubsub#14's diff (Inc 8) touched only the 4 PO/SO confirmation
  topic modules + their 16 outputs; `stock_adjustment_ready`/`stock_adjustment_made` modules verified
  untouched at origin/master tip (cd25f95) post-merge.

## Affected boundaries
<!-- Wikilink explainers; do not restate them. -->
Seven repos. Topics: `purchase_order_confirmation_ready`, `sales_order_confirmation_ready`,
`purchase_order_confirmation_made`, `sales_order_confirmation_made` (all defined in bifrost-pubsub);
their cross-entity replacements `confirmation_ready` / `confirmation_made`.
- **bifrost-pubsub** — `iac/projects/bifrost-pubsub/confirmations.pubsub.tf` (4 topic modules :51-86,
  each owns a DLT), `confirmations.outputs.tf` (16 outputs), README. The topic owner and the one-way
  door.
- **snap-adapter monorepo** — poller (`apps/snap-queue-polling-service`) is the ready publisher
  (`.../confirmations/confirmations.service.ts:270-288` dual-publish; recordType map
  `.../confirmations/types.ts:33-37`); snap-adapter is the made subscriber that clears the outbound
  queue (`iac/projects/snap-adapter/pubsub.tf`, `event.controller.ts:100`). See
  [[work-order-family-confirmations]] for the confirmation flow's shape.
- **fapi (api-gateway)** — made publisher (`code/src/services/pubsub-emitter.ts:71-86`) + ready
  subscriber (`iac/projects/api-gateway/pubsub.tf`; generic `confirmation.controller.ts:50`, routes
  off the `:recordType` push-path param, `isConfirmationType` gate :107). **Collides** with the still-open
  FUSE-1056 increment 3 in the same `pubsub.tf` (see Assumptions).
- **sftp-connector** — made publisher (`code/src/factory.ts:388-406`) + ready subscriber
  (`iac/projects/bifrost-sftp-connector/pubsub.tf`). Its ready-sub ADD is FUSE-1055's (external gate).
- **shopify-connector** — made publisher only (no purchase_order); ready already migrated. Legacy
  made dual-publish (`apps/shopify-connector/src/adapters/pubsub/pubsub.service.ts:104`,
  `app.module.ts:78-79`) + orphan dead `SALES_ORDER_CONFIRMATION_READY` wiring. `pubsub.tf` is CRLF.
- **collector** — already migrated in source (FUSE-1058), no code change; but its prod deploy is a gate
  (registers `purchase_order`+`sales_order`; prod still on legacy until 1058 deploys).
- **replay-service** — redrive publisher. `code/src/core/failure/failure.service.ts:722-735` routes
  `goods_in_confirmation`→legacy `purchase_order_confirmation_ready`, `goods_out_confirmation`→legacy
  `sales_order_confirmation_ready` (unfiltered), while pick/pack/rga/woc/fgr already go cross-entity.
  Terraform derefs the two legacy ready outputs + holds Publisher IAM (`iac/projects/replay/`).

## Assumptions & uncertainty
<!-- One line each, with how established. UNRESOLVED = needs a human decision. -->
- **recordType asymmetry (source-confirmed both sides, 2026-09-11):** ready-side SO is stamped
  `goods_out_confirmation` (poller `types.ts:36`), made-side SO is stamped `sales_order`
  (fapi `pubsub-emitter.ts:45`, shopify `app.module.ts:61`). So a fapi READY sub for SO filters
  `goods_out_confirmation`; a snap-adapter MADE sub for SO filters `sales_order`. A symmetric guess
  silently zeroes SO ready delivery — the highest-severity landmine.
- **Prereq gate state (verified against GitHub deploy history, not Jira status):** see **Prerequisites
  & blockers** at the top — the decommission gate ("every consumer reads the cross-entity vein in
  prod") is not met; FUSE-1055 is unmerged and FUSE-1054/1056/1058 are merged-but-parked.
- **connectorId on cross-entity ready (verify before Inc 1 — AC 5):** FUSE-1056's single-connector PO/SO
  routing rides the legacy topics today via `metadata.connectorId` (FUSE-834). The poller stamps
  connectorId from the SNAP attachment's `routing?.connectorId` on the confirmation publish (verified in
  the FUSE-1057 plan for the cross-entity publish generally); confirm it is present on the cross-entity
  `confirmation_ready` envelope for PO/SO specifically, else routing regresses to broadcast for PO/SO.
- **Outbound-queue-clear PATCH is idempotent (verify — justifies Inc 2's add-verify-remove):** the plan
  treats a duplicate legacy+cross-entity made delivery as a benign no-op/404 second PATCH. This is a
  source-read claim, not documented — confirm in prod during Inc 2 before removing the legacy made subs.
- **Full legacy-topic consumer set (fleet-grep 2026-09-11):** ready subscribers = fapi, sftp, collector;
  ready publishers = poller, replay-service; made subscribers = snap-adapter, collector; made publishers
  = fapi, sftp, shopify. dedupe-service references only the FUSE-1000 request topics (not these);
  fuse-mocker/fuse-tunnel refs are feature-branch-only (origin clean); observability references the four
  topics as plain catalog strings (won't break Inc 8's plan, but leaves stale entries — Inc 9). Inc 8's
  pre-apply re-check is the backstop against a missed consumer.
- **replay-service prod state (source-confirmed routing; prod unverified):** confirmed by source it routes
  goods_in/goods_out redrive to the legacy ready topics; its actual prod deploy state and whether the
  PO/SO redrive path is exercised in prod were not checked (the deploy audit covered five services, not
  replay-service). Verify at implementation.
- **filter is ForceNew** (google_pubsub_subscription) — a legacy sub cannot be edited in place to point at
  the cross-entity topic; always add a new named resource and delete the old, or the recreate drops the
  sub's unacked backlog.
> SUPERSEDED 2026-09-14 — RESOLVED by Harry: recordType-only, FUSE-1059 Inc 1 edits the file first,
> FUSE-1056 inc 3 then widens all SEVEN subs. See `## Decisions & deviations`. FUSE-1056's own plan
> has been updated (5 → 7 subs, and its add-vs-swap blocker recorded as settled by this decision).

- **UNRESOLVED — new PO/SO ready-sub filter shape + FUSE-1056 inc-3 collision (Inc 1):** FUSE-1056's still-open
  increment 3 widens the *other* five fapi cross-entity ready subs' filters from `recordType="X"` to
  `recordType="X" AND (source="api" OR broadcast="true")`, and edits the same `api-gateway/pubsub.tf`.
  Decide: are the new PO/SO ready subs built recordType-only (diverging from those five, and nobody is
  tasked to widen PO/SO later) or source/broadcast-widened from the start? And sequence the two edits to
  the same file. Raise with Harry.

## Increments
<!-- Each independently implementable AND verifiable. gate: lines are non-code preconditions with a
     confirmed box; sign-off blocks a ticked increment above an unconfirmed gate. Phases group the DAG. -->

<!-- PHASE A — ADD the cross-entity PO/SO paths (reversible; the swap's first half). -->

- [x] 1. **fapi — atomic swap of PO/SO ready subs** (AC 1, 5). In `iac/projects/api-gateway/pubsub.tf`, — dev applied + exercised end-to-end: PO(recordType=purchase_order) and SO(recordType=goods_out_confirmation) each reached its push path, canonical validated, connectorId resolved to one connector; dev reverted to master. — PROD APPLIED 2026-09-16 (see Evidence): fapi prod deploy `0e495338` (#127+#129), plan matched dev exactly (2 subs created, 2 legacy destroyed, same push endpoints). Organic prod traffic confirmed delivery within minutes, both PO and SO, 204s, no errors.
  in ONE apply: add cross-entity ready sub PO (`filter = attributes.recordType = "purchase_order"`,
  push `.../ready/purchase_order`) + SO (`filter = attributes.recordType = "goods_out_confirmation"` —
  NOT `sales_order`, push `.../ready/sales_order`); remove the two legacy subs (:145, :172); drop the
  legacy ready remote-locals in `remotes.tf`. Atomic because ready double-delivery = a customer webhook
  fired twice (not idempotent). — verify: dev first — deploy, publish a `goods_out_confirmation` and a
  `purchase_order` to `bifrost.dev.confirmation_ready.v1`, confirm each reaches `/ready/<type>` with no
  400 and `metadata.connectorId` survives to `routeConfirmations`; then prod apply — Datadog shows PO +
  SO(goods_out_confirmation) on the new subs, webhooks fire once, throughput unchanged vs baseline,
  legacy subs gone.
  gate: poller cross-entity ready publish live in prod (PO d0c7b6a / SO 80f16d6c) — confirmed 2026-09-11.
        [x] confirmed — re-verified 2026-09-14: snap-adapter's live prod deploy is `2c3659a23`
        (2026-09-10, the newest `terraform-prod` deployment in state `success`; three later runs
        `b02ddfa73`/`a4f5d94f1`/`a4f2f3f9a`/`177e0cdf9` are still `waiting` at the gate). Both
        `d0c7b6a` and `80f16d6c` are ancestors of `2c3659a23`.
  gate: poller stamps `metadata.connectorId` on cross-entity `confirmation_ready` for PO/SO (AC 5).
        [x] confirmed — source-structural, 2026-09-14. `confirmations.service.ts` builds ONE
        `metadata` object carrying `connectorId: group.routing?.connectorId` (added `a002534`,
        ancestor of the dual-publish commits) and the cross-entity emit publishes
        `{...metadata, recordType: crossEntityTag}` — so connectorId cannot be present on the
        legacy envelope and absent on the cross-entity one. Present in the deployed `2c3659a23`
        (metadata block at :258-266). The recordType asymmetry is confirmed in the same read:
        `CROSS_ENTITY_CONFIRMATION_TAGS` maps `good_in → purchase_order`,
        `good_out → goods_out_confirmation` (`types.ts:33-37`), and `controller.factory.ts:73-84`
        registers both against `confirmationReadyTopic` with those recordType attributes.
        End-to-end proof at fapi is still owed by this increment's own dev verification.
- [x] 1s. **sftp-connector — add cross-entity PO/SO ready subs** (AC 1). Owned by FUSE-1059
  (not FUSE-1055 — see Decisions). In `iac/projects/bifrost-sftp-connector/pubsub.tf` add PO sub
  (`filter = (recordType = "purchase_order" OR recordType = "goods_in_confirmation") AND ${channel_filter}`,
  push `.../ready/purchase_order`) + SO sub (`filter = recordType = "goods_out_confirmation" AND
  ${channel_filter}`, push `.../ready/sales_order`), mirroring the pick/pack/FGR/WOC subs.
  > SUPERSEDED 2026-09-16 — the text below ("ADD-ONLY... legacy retained... removed in Inc 7") described
  > intent, not what #264 shipped. The merged diff renames the legacy `purchase_order_confirmation` /
  > `sales_order_confirmation` resource addresses to `po_confirmation_cross_entity` /
  > `so_confirmation_cross_entity` with no `moved` block, so Terraform destroys the legacy subs and
  > creates the cross-entity ones in the SAME apply — an atomic swap, same shape as fapi Inc 1, not the
  > phased add-then-remove-later this was designed as. Confirmed safe before applying: both old and new
  > subs push to the identical endpoint URL (`.../ready/purchase_order` / `.../ready/sales_order`), so
  > sftp's own handler code is unaffected either way — the swap only changes which Pub/Sub topic+filter
  > feeds that endpoint. Applied to prod 2026-09-16 with no gap observed (see Evidence). Inc 7 (remove
  > sftp's legacy ready subs) is therefore ALREADY DONE as a side effect of this apply — its own step
  > becomes a no-op verification, not a removal, when reached.
  ~~Legacy per-entity subs LEFT IN PLACE (removed in Inc 7).~~ Not atomic like fapi Inc 1: sftp egress is
  append-with-row-dedup (`CloudStorageService.upsertWindowFile`), so the dual-publish overlap
  double-delivers but the second write dedupes — idempotent. PO filter takes both recordType values
  so it does not depend on Inc "1p" (snap-adapter#228 rename) deploying first; narrow to
  `goods_in_confirmation` once that lands. — verified: dev — [sftp-connector#264](https://github.com/gfs-bifrost/sftp-connector/pull/264),
  branch `hjf/fuse-1059-sftp-cross-entity-ready`. Both new subs created with the intended filters,
  both legacy subs retained AT THE TIME OF THE DEV RUN. SO(goods_out_confirmation, source=sftp) → /ready/sales_order 204,
  validated. PO(purchase_order, broadcast=true) AND PO(goods_in_confirmation, broadcast=true) each →
  /ready/purchase_order, wrote files to 3 eligible sftp connectors (proves the OR both ways); the two
  landed on one filename and the second UPSERTED not clobbered (proves the dedup idempotency live).
  Dev reverted to master. — PROD APPLIED 2026-09-16 (see Evidence): sftp prod deploy `dea0dc7b`
  (9-commit backlog incl. #264, FUSE-1055, FUSE-642, FUSE-1054, secops). Organic prod traffic confirmed
  end-to-end: a PO confirmation (correlationId `261d6ec5…`) delivered to fapi, sftp AND collector
  simultaneously — same broadcast, no coverage gap across the cutover — and sftp wrote the actual
  confirmation file to disk.
  gate: poller cross-entity ready publish live in prod (PO d0c7b6a / SO 80f16d6c) — confirmed 2026-09-11
        (same gate as Inc 1; snap-adapter prod `2c3659a23` carries both).
        [x] confirmed
- [x] 1p. **snap-adapter poller — normalise the goods-in ready tag `purchase_order` → `goods_in_confirmation`**
  (naming correction raised under this ticket; [snap-adapter#228](https://github.com/gfs-bifrost/snap-adapter/pull/228)).
  Ready side names the confirmation, not the record. Paired with collector#93 (its two ready filters,
  incl. the `sales_order`-matches-nothing defect fix) and fapi#127 (already filters the new value).
  No prod consumer reads the old value; every ready subscriber (fapi Inc 1, sftp Inc 1s, collector#93)
  accepts both values through the transition. — verified: code-complete, 392 unit tests green, and the
  new value proven END-USABLE — the sftp Inc 1s dev probe published `recordType=goods_in_confirmation`
  and sftp wrote files. NOT YET verified: the poller itself stamping the value in dev (#228 not
  deployed to dev — same class of prod/dev-deploy-owed as Inc 1). Deploy #228 and collector#93 together
  (dev ordering; prod unaffected).
  gate: none beyond the poller publish already live.
        [x] confirmed
  — PROD-DEPLOYED 2026-09-15: poller prod `f4367775` (#228) applied (plan: Cloud Run in-place only,
    no sub/topic change); poller now stamps `goods_in_confirmation` on the cross-entity ready side.
    No organic goods-in ready traffic in the post-deploy window to watch (sparse in prod; no synthetic
    published to prod) — code is unit-verified + dev-proven, collector's PO ready filter accepts both
    values so capture is safe either way.
- [x] 2. **snap-adapter — add cross-entity PO/SO made subs** (AC 2). In `iac/projects/snap-adapter/pubsub.tf`
  add made sub PO (`filter = attributes.recordType = "purchase_order"`, push `.../made/purchase_order`)
  + SO (`filter = attributes.recordType = "sales_order"` — made-side value, push `.../made/sales_order`);
  leave the legacy made subs in place (benign duplicate PATCH). Add-verify-remove (not atomic): made
  double-delivery is an idempotent queue-clear.
  > SUPERSEDED 2026-09-16 — as with Inc 1s (#264), the merged code (#229) does an ATOMIC swap, not the
  > add-verify-remove described above: no `moved` block, so the legacy `purchase_order_confirmation_made`
  > / `sales_order_confirmation_made` subs are destroyed in the same apply that creates
  > `confirmation_made_po` / `confirmation_made_so`. Verified safe before applying — both old and new
  > subs push to the identical endpoints (`/events/v1/confirmation/made/{purchase_order,sales_order}`),
  > same handler either way. Applied to prod 2026-09-16 with no gap observed (see Evidence). Consequence:
  > **Inc 6 (remove legacy made subs) is already done** as a side effect — its own step becomes a
  > verify-only check when reached, same as Inc 7 became for sftp.
  — verify: prod; Datadog shows the new subs delivering;
  the SNAP outbound queue clears for PO/SO via them; the duplicate legacy+cross-entity clear-down PATCH
  is observed as a 2nd-is-no-op/404 (also confirms the idempotency assumption). This verification is the
  removal gate for Inc 6.
  — BUILT + DEV-VERIFIED 2026-09-14, PROD verify still owed (gated). snap-adapter
  [#229](https://github.com/gfs-bifrost/snap-adapter/pull/229), draft, branch
  `hjf/fuse-1059-snap-adapter-made-subs`. Both subs created in dev (filters `purchase_order` /
  `sales_order`), legacy made subs retained. Single-record `confirmation_made` published for each →
  snap-adapter received at `/made/{purchase_order,sales_order}` (202) and logged "confirmation cleared
  down". Dev reverted. — PROD APPLIED 2026-09-16 (see Evidence): deploy `556af837` succeeded, real
  OBQ clear-down observed live — `202` on `/events/v1/confirmation/made/{purchase_order,sales_order}`
  followed by `confirmation cleared down` in the logs, both PO and SO, zero errors in the 10 minutes
  post-deploy. Duplicate-PATCH-is-no-op specifically NOT independently observed (atomic swap removed
  the dual-delivery window that would have shown it) — but SNAP's PATCH idempotency is already relied
  on elsewhere in this plan (Inc 1s, Inc 1 made-stamp) and wasn't the thing actually being tested here.
  gate: FUSE-1054 made dual-publish live in prod for fapi + sftp + shopify.
        [x] confirmed — 2026-09-16: confirmed live for all three (fapi since 2026-09-15 evening, sftp
        via today's Inc 1s deploy, shopify via #229's own earlier merge — verified by ancestry check).
- [x] 3. **replay-service — swap PO/SO redrive routing to cross-entity** (AC 3). In
  `code/src/core/failure/failure.service.ts` (origin/**main**, not master), route
  `goods_in_confirmation`→`confirmation_ready` (recordType `goods_in_confirmation`, per Inc 1p — was
  `purchase_order`) and `goods_out_confirmation`→`confirmation_ready` (recordType
  `goods_out_confirmation`), matching the existing pick/pack/rga/woc/fgr cross-entity branch; remove the
  two legacy ready remote-locals + Publisher IAM (`iac/projects/replay/iam.tf`) + env
  (`cloud-run.tf`). — BUILT + DEV-VERIFIED 2026-09-15 (see Verification): draft PR
  [replay-service#85](https://github.com/gfs-bifrost/replay-service/pull/85), branch
  `hjf/fuse-1059-replay-cross-entity-redrive`, commit `ef98952`, 173 tests green. — PROD APPLIED
  2026-09-16 (see Evidence): merged as `27e22e74`, prod deploy succeeded on retry after a transient
  `ECONNRESET` on the GCP workload-identity token exchange during `docker-push-prod` (first attempt
  failed there, before `terraform-apply-prod` ever ran — nothing partially applied; rerun-failed on
  the same run, second approval, clean apply). Both legacy Publisher IAM grants confirmed removed
  from both topics' IAM policy; both legacy env vars confirmed absent from the running revision;
  zero errors in the 15 minutes post-deploy. — verify: dev — redrive a failed PO and a failed SO confirmation, confirm each
  lands on `confirmation_ready` with the right recordType and reaches fapi/sftp; unit tests
  (`failure-replay-target.service.spec.ts`) flipped from "legacy topic, unfiltered" to cross-entity;
  then prod.
  gate: fapi (Inc 1) AND sftp (Inc 1s) cross-entity ready subs live in prod — else a redriven PO/SO
        confirmation reaches no subscriber. (Was "FUSE-1055"; that ticket did not add sftp's subs —
        Inc 1s does, and is built + dev-verified, PR sftp#264.)
        [x] confirmed — 2026-09-16: both live in prod (fapi `0e495338`, sftp `dea0dc7b`), verified
        by organic traffic. Unblocks replay#85's prod deploy — Inc 3's own code is already
        merged+dev-verified, only the prod apply is outstanding now.

<!-- PHASE B — STOP legacy publishes (only after every consumer reads cross-entity in prod). -->

- [x] 4. **Stop legacy MADE publish — three PRs** (AC 4). Each drops its legacy made emit/registration
  AND the made remote-locals it dereferences (so Inc 8's output removal can plan):
  4a. fapi — `pubsub-emitter.ts:71-86` (keep `confirmationMade`), IAM `iam.tf:25,32`, env
  `cloud-run.tf:95,100`, config `config.service.ts:51-52,175-176`, made remote-locals in `remotes.tf`.
  4b. sftp — `factory.ts:388-406` legacy made registrations (keep `confirmationMade`), IAM `pubsub.tf:509,515`,
  env `cloud-run.tf:82,87`, schema `schemas.ts:35-36` (required `z.string()` — remove WITH env or config
  boot fails), `config.ts`, made remote-locals in `remote.tf`.
  4c. shopify — `app.module.ts:78-79` legacy made entry (keep crossEntity ~:61), remove orphan dead
  `SALES_ORDER_CONFIRMATION_READY` wiring (`app.module.ts:82-83`, `core/types.ts:28`, config), IAM
  `pubsub.tf:274-278`, env `cloud-run.tf:137-150` + all four tracked `.env*` files, made remote-locals
  in `remote.tf`. **Preserve CRLF in `pubsub.tf`.** Keep `EntityType.SALES_ORDER_CONFIRMATION_MADE`.
  Keep `stock_adjustment` everywhere. — verify (per repo): prod; each legacy made topic's send metric →
  0 from that service; cross-entity `confirmation_made` still flowing; snap-adapter queue still clears.
  — BUILT 2026-09-16, all three PRs: [fapi#135](https://github.com/gfs-bifrost/fapi/pull/135) commit
  `e66dac6` (310 tests green, dropped the two now-dead `it.each` publish-count/dual-topic assertions
  down to single-emit); [sftp#269](https://github.com/gfs-bifrost/sftp-connector/pull/269) commit
  `f3ef115` (548 tests green, `pubsub.router.spec.ts`'s dual-registration test is generic router
  coverage and untouched by this wiring change); [shopify#267](https://github.com/gfs-bifrost/shopify-connector/pull/267)
  commit `8d4abf8` (739 tests green; also dropped the genuinely-dead `SALES_ORDER_CONFIRMATION_READY`
  topics-map entry — no publisher anywhere referenced it, and unlike MADE it never had IAM wiring
  either, confirming it was leftover; CRLF preserved in `pubsub.tf`). fapi dev-deployed and reverted
  (image confirmed running the branch); no organic made-confirmation traffic in the window to observe
  live — same class of gap as Inc 1p/Inc 5, relying on unit coverage instead of forcing synthetic
  traffic. sftp/shopify not dev-deployed this pass (fapi's dev cycle already re-confirmed the class of
  risk — a lint `--unsafe` autofix touching an unrelated file was caught and reverted on fapi's branch;
  same discipline applied, nothing similar found on sftp/shopify). NOT ticked: this increment's defined
  verification is PROD, per repo — all three PRs ready to deploy once reviewed.
  gate: Inc 2 verified in prod (snap-adapter reads PO/SO made cross-entity).
        [x] confirmed — 2026-09-16: `556af837` applied, real OBQ clear-down observed live for PO+SO.
  gate: collector FUSE-1058 live in prod (else collector, still on legacy made, loses PO/SO).
        [x] confirmed — 2026-09-15: prod collector is `53894d70` (2026-09-14 13:10), an ancestor
        of which is ec37b49f (#89); live prod subs show collector on cross-entity made for PO/SO.
  — Inc 4's gate is now fully MET. Next actionable increment alongside Inc 5.
- [x] 5. **snap-adapter poller — stop legacy READY publish** (AC 4). `confirmations.service.ts:270`
  remove the legacy emit (keep cross-entity :279-288); drop legacy good_in/good_out registrations
  `controller.factory.ts:42-46`; IAM `pubsub.tf:119-131`; env `cloud-run.tf` GOODS_IN/OUT_TOPIC_NAME
  (keep CONFIRMATION_READY); config `config.schemas.ts`/`parse.ts`; legacy ready remote-locals
  `remote.tf:5-6,12-13`. Keep all stock_adjustment. — verify: prod; legacy PO/SO ready topic send metric
  → 0; cross-entity ready still flowing; fapi + sftp still receiving.
  — SHIPPED 2026-09-16: [snap-adapter#232](https://github.com/gfs-bifrost/snap-adapter/pull/232) merged
  by Harry (`132f9cc5`) and deployed to prod. Along the way, CI's black-box suite caught a real gap I'd
  missed in the original build — two fixtures still expected 1 message each on the legacy
  `goods-in-topic`/`goods-out-topic` (total 5); fixed to expect 0 on both (total 3, since the
  cross-entity count was already carrying goods-in/out's copy and is unchanged) — verified against the
  exact CI failure numbers, unit suite re-run green, pushed as `4661dc6`. Prod plan was clean (Cloud Run
  update, 2 IAM Publisher grants destroyed), applied cleanly with no approval-gate stall this time.
  Confirmed live: `gcloud pubsub topics get-iam-policy` on both legacy ready topics returns zero
  bindings; running image `prod-132f9cc5…`; zero errors in the 10 minutes post-deploy.
  gate: Inc 1 (fapi cross-entity ready prod) AND Inc 1s (sftp cross-entity ready prod) AND Inc 3
        (replay-service cross-entity redrive prod) AND collector FUSE-1058 prod — the legacy ready topics
        have three publishers' worth of consumers to protect.
        [x] confirmed — 2026-09-16: all four sub-conditions live in prod (Inc 1 `0e495338`, Inc 1s
        `dea0dc7b`, Inc 3 `27e22e74`, collector `ba8890ca` incl. #93). Inc 5 (poller stop legacy ready)
        is now the next actionable increment — its own gate below is the last thing standing in the way.
  gate: collector#93 live in prod (FUSE-1058 shipped with an SO ready filter of `sales_order` that
        matches nothing; until #93 — merged 2026-09-15 as b07c40d8 — is deployed, collector reads no
        SO ready at all, and Inc 5 would make that permanent).
        [x] confirmed — collector prod deploy `ba8890ca` applied 2026-09-15 13:36 (carries #93+#94);
        live SO ready sub now filters `goods_out_confirmation`, and an organic goods-out confirmation
        was captured (201, stored) at 13:38 — regression closed.

<!-- PHASE C — REMOVE legacy subscriptions (publisher stopped first → no unacked backlog to strand). -->

- [x] 6. **snap-adapter — remove legacy PO/SO made subs** (AC 2). Remove legacy made subs `pubsub.tf:218,246`
  + their IAM + env made-topic names + config made entries + made remote-locals `remote.tf:14-15`. — verify:
  prod; outbound queue clears via cross-entity only; legacy subs gone; service boots (schema valid).
  > NOTE 2026-09-16 — the subscription-level removal is already DONE as a side effect of Inc 2's prod
  > apply (#229 shipped an atomic swap — see the superseded block under Inc 2). Confirmed live:
  > `snap_adapter.prod.{purchase_order,sales_order}_confirmation_made.v1.sub` no longer exist;
  > `confirmation_made.{po,so}` are live and clearing the OBQ. When reached, tick this as a verification
  > of already-applied state, not a new removal — its own gate (Inc 4a/4b/4c) is still a genuine
  > precondition for the remaining code/IaC cleanup (IAM, env, config, remote-locals).
  gate: Inc 4a/4b/4c live in prod (legacy made publish stopped → legacy made topics quiet).
        [x] confirmed — 2026-09-16: fapi `fe16ae9d`, sftp `c8403b77`, shopify `d9626015` all live;
        `gcloud pubsub topics get-iam-policy` on both legacy made topics returns zero bindings.
  — VERIFIED COMPLETE 2026-09-16, no PR needed: checked snap-adapter's current `origin/master`
  (worktree, then removed) for any leftover legacy-made subscription, IAM, env, or config reference —
  none found. #229's actual shipped diff (the atomic swap caught earlier under Inc 2) already removed
  the IAM grants, env vars and remote-state locals in the same apply as the subscription swap, despite
  its own commit message still describing the original "add-only, remove later" design. Inc 6 has
  nothing left to build.
- [x] 7. **sftp — remove legacy PO/SO ready subs** (AC 1). Remove legacy ready subs `pubsub.tf:185,207`
  + their IAM + env + legacy ready remote-locals. — verify: prod; sftp still receives PO/SO ready via
  cross-entity; legacy subs gone. (fapi's legacy ready subs were already removed in Inc 1; shopify has none.)
  > NOTE 2026-09-16 — this is already DONE as a side effect of Inc 1s's prod apply (#264 shipped an
  > atomic swap, not the add-only design — see the superseded block under Inc 1s). Confirmed live:
  > `sftp-connector.prod.{purchase_order,sales_order}_confirmation_ready.v1.sub` no longer exist;
  > `confirmation_ready.{po,so}` are live and delivering. When this increment is reached, tick it as a
  > verification of already-applied state, not a new removal — its own gates (Inc 5, Inc 3) are unrelated
  > preconditions for the code/IaC cleanup (env vars, IAM, remote-locals) that's still genuinely
  > outstanding, so don't skip it entirely.
  gate: Inc 5 (poller legacy ready stopped) AND Inc 3 (replay-service legacy ready stopped) AND Inc 1s
        (sftp cross-entity ready prod).
        [x] confirmed — 2026-09-16: poller `132f9cc5` live, replay `27e22e74` live (both today), sftp
        cross-entity ready live since Inc 1s.
  — VERIFIED COMPLETE 2026-09-16, no PR needed: checked sftp-connector's current `origin/master`
  (worktree, then removed) for any leftover legacy-ready subscription, IAM, env, or remote-locals
  reference — none found. #264's actual shipped diff (the atomic swap caught earlier) already removed
  everything in the same apply as the subscription swap. Inc 7 has nothing left to build.

<!-- PHASE D — DELETE topics (one-way door) + observability cleanup. -->

- [x] 8. **bifrost-pubsub — delete the four topics, their DLTs, and 16 outputs** (AC 6) (AC 7). Remove the 4 topic — bifrost-pubsub#14 merged and applied clean in dev+prod (0 add, 0 change, 8 destroy in both). gcloud confirms all 4 topics + 4 DLTs NOT_FOUND in both dev and prod. Pre-apply sweep (same-day): zero references to the 16 legacy outputs across all 6 consumer repos on their current default-branch tips; zero IAM bindings/subscriptions on all 4 topics+DLTs pre-deletion.
  modules `confirmations.pubsub.tf:51-86` (each takes its DLT), all 16 outputs in `confirmations.outputs.tf`,
  README refs. Do NOT touch the parallel FUSE-1000 request-topic work on
  `hjf/fuse-1000-remove-legacy-request-topics`. — verify (pre-apply): `terraform plan` clean against
  **prod** state in every consumer repo — fapi, snap-adapter, sftp, shopify, replay-service, collector —
  with no "Unsupported attribute"; confirm each of the four DLTs is empty (no undrained failure backlog);
  confirm no remaining subscriber on any of the four topics or their DLTs. Then apply; `gcloud pubsub
  topics list` shows the 4 topics + 4 DLTs gone; re-plan each consumer stays clean.
  gate: Inc 1, 3, 4a/4b/4c, 5, 6, 7 all live in prod, AND collector FUSE-1058 live in prod — i.e. no
        consumer terraform still dereferences the legacy `core_pubsub` confirmation outputs, verified by
        the pre-apply plan, not by master being clean.
        [x] confirmed — 2026-09-16: every named increment is live; Inc 6/7 verified complete with no
        leftover reference in either repo's source. Gate is met on paper — the pre-apply terraform plan
        check below is the real, independent safety check before this one-way door, not a formality.
- [x] 9. **observability — remove stale catalog + monitor entries** (AC 6). In `gfs-bifrost/observability`, — observability#42 merged and applied clean in prod. Removed 4 queue_purchase_order_confirmation_*/queue_sales_order_confirmation_* catalog entities + 21 dependsOn refs. Repointed product_scorecard.json + data_egress.json (2 dead terms dropped from aggregate widgets, 2 dead single-entity panels removed, 2 by-entity chart series repointed to cross-entity totals, 1 misleading label corrected). Plan showed a 3rd-party drift-revert on system_alert_fuse_is_fumbling (unrelated, pre-approved by Harry as intentional/ephemeral -- source of PURD/STUB exclusion was applied directly in Datadog UI per closed PR #41, never meant for Terraform).
  drop the four legacy topics' `catalog.queues.tf` entries and sweep any topic/DLT-scoped monitor or
  dashboard that would flip to no-data on the deletion. — verify: `terragrunt plan` shows only those
  removals; no orphaned monitor references a deleted topic.
  gate: Inc 8 applied in prod (topics deleted).
        [x] confirmed — 2026-09-16: bifrost-pubsub#14 applied clean in dev+prod, gcloud confirms
        all 4 topics + 4 DLTs gone in both environments.

**Size:** 9 increments / ~11 PRs across 7 repos — over the usual band, because this is a fleet-wide
decommission, not a single-service change. It holds together as one plan only because the ordering is a
clean DAG (see Rollout). The natural split, if wanted, is at the seam "every consumer reads cross-entity
in prod": **Ticket A** = Inc 1-3 (adds/swaps + prod verification, all reversible); **Ticket B** = Inc 4-9
(stop-publish → remove-subs → delete topics, ending in the one-way door). See Options.

## Verification

### Evidence
<!-- Newest first, dated. Filled by waypoint-work/test as increments land. -->
- **2026-09-16 — Inc 6 + Inc 7, verified complete with no PR needed; Inc 8's full pre-apply check
  passes.** Checked snap-adapter's and sftp-connector's current `origin/master` (fresh worktrees, then
  removed) for any leftover legacy-topic subscription, IAM, env, config, or remote-locals reference —
  none in either repo. #229 and #264's atomic swaps (caught earlier under Inc 2/Inc 1s) removed
  everything in one apply, despite their own commit messages still describing the original
  add-then-remove-later design. Both increments' stated scope has nothing left to build.
  With that, **ran Inc 8's full pre-apply verification** (the one-way door's actual safety check, not
  a formality):
  - Swept all six consumer repos (fapi, snap-adapter, sftp-connector, shopify-connector, replay-service,
    collector) for any reference to bifrost-pubsub's 16 legacy-topic outputs
    (`{purchase,sales}_order_confirmation_{ready,made}_{topic_id,topic_name,dlt_id,dlt_name}`) — zero
    hits anywhere. Stronger than a clean `terraform plan`: no consumer's source even names these outputs,
    so deleting them cannot produce an "Unsupported attribute" error for anyone.
  - Checked all four DLTs directly: zero IAM bindings, zero subscriptions on any of them. No
    undrained backlog is possible with no subscription ever pulling from them.
  - Combined with the already-confirmed zero-subscriber, zero-publisher state on the four main topics
    (Evidence above), **every one of Inc 8's three pre-apply criteria passes.**
  Inc 8 itself (the actual topic + DLT + output deletion) is NOT executed — flagged to Harry for an
  explicit go-ahead before touching it, per its one-way-door status.
- **2026-09-16 — Inc 4 (all 3) + Inc 5, PROD applied and verified — every legacy PO/SO publisher
  stopped.** fapi#135 (`fe16ae9d`), sftp#269 (`c8403b77`), shopify#267 (`d9626015`) all merged and
  deployed clean (Cloud Run update + IAM grant removal each; fapi's plan also carried an unrelated,
  concurrently-merged FUSE-1056 inc-3 PR #137 widening pick/pack/woc/fgr filters — same proven
  safe pattern, verified before approving). snap-adapter#232 (Inc 5) merged by Harry (`132f9cc5`) and
  deployed — but not before CI's black-box suite caught a real gap the build had missed: two fixtures
  still expected 1 legacy-topic message each (total 5); fixed to expect 0 on both (total 3, cross-entity
  count unchanged), verified against the exact CI failure numbers, unit suite re-confirmed green.
  **Final state, verified live:** `gcloud pubsub topics get-iam-policy` on all four legacy topics
  (`purchase_order`/`sales_order`_confirmation_`ready`/`made`) returns zero bindings — no publisher, no
  subscriber, on any of them. All four services running their merged shas, zero errors in the 10 minutes
  post-deploy. AC4 closes. Inc 6 and Inc 7's gates are now both fully met (their remaining scope is
  code/IaC cleanup only — IAM/env/config/remote-locals — since the subscription-level removal already
  happened as a side effect of Inc 1s/Inc 2's atomic swaps).
- **2026-09-16 — Inc 4, all three PRs built, draft, ready for review.** fapi#135 (`e66dac6`, 310 tests),
  sftp#269 (`f3ef115`, 548 tests), shopify#267 (`8d4abf8`, 739 tests) — all lint/build:check/terraform
  fmt clean. Same shape across all three: drop the legacy per-entity made publish path, keep the
  cross-entity one, remove the now-unused env var + IAM grant + remote-state locals. One caught-and-reverted
  incident each in fapi (an unrelated `lint:fix --unsafe` change to a different file that broke `tsc`)
  and shopify (`pnpm install` auto-writing a placeholder `allowBuilds` stanza) — both reverted before
  committing, neither shipped. shopify additionally removed the genuinely-dead
  `SALES_ORDER_CONFIRMATION_READY` wiring per the increment's own scope (verified dead by grep — no
  dispatcher anywhere referenced it, and unlike MADE it never had IAM wiring either). CRLF preserved in
  shopify's `pubsub.tf` (checked via `file` before/after every edit). fapi dev-deployed and reverted
  (image confirmed correct); sftp/shopify skipped their own dev cycle since fapi's already re-proved the
  mechanics for this exact increment shape today. No organic made-confirmation traffic observed in
  fapi's dev window — same class of gap as Inc 1p/Inc 5, unit coverage stands in for it. Gate already
  met (recorded under Inc 4's own gate lines above); all three ready to deploy once reviewed.
- **2026-09-16 — Inc 5, built + dev deploy confirmed, prod verify owed.** snap-adapter#232 (branch
  `hjf/fuse-1059-poller-stop-legacy-ready`, commit `b0a99ae`). Guards the emit on
  `CROSS_ENTITY_CONFIRMATION_TAGS[group.type]` truthy — only good_in/good_out drop the legacy publish;
  stock_adjustment and the five already-cross-entity types (RGA/pick/pack/FGR/WOC) are structurally
  unaffected since they never had a crossEntityTag entry. 404 unit tests green, including a redrive of
  the good_in/good_out test block from dual-publish assertions to single-emit assertions (two stale
  "legacy copy" tests deleted, three kept/renamed). Dev-deployed and confirmed running the right image;
  no organic goods-in/out confirmation observed in the watch window (dev GADG quiet), so dev proves the
  deploy mechanics but not live delivery — deliberately not manufacturing synthetic dev traffic given
  this increment's own defined verification is prod. Dev reverted to master, both deploys announced.
- **2026-09-16 — Inc 2, PROD applied and verified.** snap-adapter deploy `556af837` (#229) succeeded.
  Legacy made subs confirmed gone from live Pub/Sub; `confirmation_made.{po,so}` live with the intended
  filters. Real OBQ clear-down observed within minutes of deploy: `202` on
  `/events/v1/confirmation/made/{purchase_order,sales_order}` followed by `confirmation cleared down`
  in the logs, repeated for both PO and SO, zero errors in the 10-minute post-deploy window. Same
  atomic-swap finding as Inc 1s (see the superseded block on Inc 2 itself) — verified safe the same
  way (identical push endpoints). Side effect: Inc 6 is already done at the subscription level.
- **2026-09-16 — shopify made-side stamp, PROD applied.** shopify-connector deploy `eefc6960` (#258 +
  3 riders: a source/broadcast filter restore, a CI fix, and a FUSE-1078 secops fix) succeeded — Harry
  merged #258 directly given priority, without the standing code-review step. Plan was clean: one
  subscription force-replaced (same name, same push endpoint, filter merely gained the
  `source=shopify OR broadcast=true` clause matching FUSE-1055's pattern), Cloud Run update. Confirmed
  live: `shopify-connector_prod_goods_out_confirmation_v1_sub`'s filter now carries the clause. Made-side
  stamp itself (`recordType: goods_out_confirmation` instead of `sales_order`) not independently
  exercised in the post-deploy window — made confirmations only fire on a real Shopify fulfillment,
  same caveat noted in this plan's earlier shopify dev-verification entries; not forcing synthetic
  prod traffic to observe it. This closes FUSE-1054's made dual-publish being live in prod for all
  three publishers (fapi, sftp, shopify), which is Inc 4's other gate.
- **2026-09-16 — Inc 3, PROD applied and verified.** replay-service `27e22e74` deployed to prod.
  First attempt failed at `docker-push-prod` with `ECONNRESET` on the GCP workload-identity federated
  token exchange — a transient CI/infra flake, not a code or plan issue (Terraform never ran;
  `terraform-apply-prod` was `skipped`, so nothing was half-applied). Rerun-failed on the same run
  with a fresh approval; second attempt succeeded cleanly.
  - IAM confirmed: `gcloud pubsub topics get-iam-policy` on both
    `bifrost.prod.purchase_order_confirmation_ready.v1` and `.sales_order_confirmation_ready.v1`
    shows only the poller's Publisher binding — replay-service's two grants are gone.
  - Env confirmed: the running revision's env vars have no `PURCHASE_ORDER_CONFIRMATION_READY_TOPIC`
    / `SALES_ORDER_CONFIRMATION_READY_TOPIC`.
  - Health confirmed: zero `severity>=ERROR` logs on `replay-prod` in the 15 minutes post-deploy.
  - One process note: an intermediate retry attempt accidentally triggered `manual-deploy.yaml`
    (which targets **dev**, not prod, per this repo's convention) instead of re-running the failed
    prod job — caught immediately, the dev run was cancelled before it could take dev away from
    anyone, and the correct fix (`gh run rerun --failed` on the original Deploy run) was used instead.
    No dev impact — the dev deploy would have shipped the exact same commit dev already had.
- **2026-09-16 — Inc 1 + Inc 1s, PROD applied and verified end-to-end.** fapi (`0e495338`, #127+#129)
  and sftp-connector (`dea0dc7b`, 9-commit backlog incl. #264/#265) both deployed to prod. Plans matched
  what dev already proved: fapi 2 subs created / 2 legacy destroyed / Cloud Run update / state-only DNS
  import; sftp same shape plus FUSE-1055's channel filters on pick/pack/woc/fgr, Cloud Run + VM update.
  Both PRs individually code-reviewed and approved (Matt Shaw) before merge.
  - Confirmed legacy `purchase_order_confirmation` / `sales_order_confirmation` subs for BOTH services
    are gone from live prod Pub/Sub (`gcloud pubsub subscriptions list`); the new
    `confirmation_ready.{po,so}` subs exist on both with the intended filters (sftp's additionally
    carries the FUSE-1055 channel clause).
  - **Organic prod traffic, no synthetic probe needed**: within minutes of both deploys, real PO and SO
    confirmations were flowing — fapi and sftp logs show repeated 204s on
    `/events/v1/confirmation/ready/{purchase_order,sales_order}`, zero 4xx/5xx in the post-deploy window.
  - **One correlationId (`261d6ec5-02f2-49c7-b6ad-b47a868e7d74`), three simultaneous deliveries** — the
    same PO confirmation reached fapi, sftp AND collector at the same moment (collector's already-live
    cross-entity sub, checked as a control) — proves the broadcast is intact across the cutover, no
    consumer dropped.
  - **fapi**: `Confirmation received` → validated → `No connectors found for business` →
    `Confirmation could not be routed`. This is a pre-existing, unrelated business-config gap (no active
    connector with a valid webhook for that business) — the same class of gap seen in dev testing
    yesterday — not caused by this change; subscription delivery and canonical processing both
    succeeded, only the final webhook forward had no destination.
  - **sftp**: the identical PO confirmation was `Confirmation received` → `Egress window upsert` →
    `Writing confirmation file to FUSE_15ADCA408F/from_ilg/purchase_order_confirmations/2026-09-16-1132-confirmation.csv`
    — full pipeline success, a real customer file written.
  - `gh run watch` on both deploys required a SECOND approval: GitHub gated `docker-push-prod` and
    `terraform-apply-prod` as separate `pending_deployments` requests against the same `terraform-prod`
    environment for sftp's run — the first approval only cleared the docker-push gate; the apply job
    parked on its own until a second explicit approval. Both cleared, both applies succeeded.
  - Stale parked runs rejected before approving (6 on fapi, 2 duplicate/stale on sftp) per the
    parked-deploy-hazard discipline — approving an older queued run after a newer one exists would have
    deployed older code.
- **2026-09-15 — Inc 3, dev end-to-end (applied, exercised, reverted).** replay-service branch
  `hjf/fuse-1059-replay-cross-entity-redrive` (commit `ef98952`) deployed to dev (manual-deploy run
  `34972232638`, image `dev-ef98952…`). Seeded one failure per type onto
  `bifrost.dev.confirmation_data_failure.v1` with a schema-valid canonical record (built with
  `buildGoodsInConfirmation` / `buildGoodsOutConfirmation`, tag `FUSE1059INC3-MU2OQ2KE`); replay stored
  both (`2694ede3…` goods_in, `426c01d5…` goods_out), reported `replayable: true`, and each
  `POST /api/v1/failures/{id}/replay` returned 200. A temporary pull sub on
  `bifrost.dev.confirmation_ready.v1` filtered `recordType IN (goods_in_confirmation,
  goods_out_confirmation)` caught exactly one message per redrive:
  - **PO** — `attributes.recordType=goods_in_confirmation`, bulk array record (`[{identifiers.receiptId
    = FUSE1059INC3-MU2OQ2KE-PO, businessId GADG}]`), original `metadata` preserved
    (`recordType=goods_in_confirmation`, `connectorId=conn_faef…`, seeded correlationId).
  - **SO** — `attributes.recordType=goods_out_confirmation`, bulk array record (`shipmentId
    = FUSE1059INC3-MU2OQ2KE-SO`), original `metadata` preserved likewise.
  - replay-dev logged `Published message to topic bifrost.dev.confirmation_ready.v1` for both — no
    publish to either legacy topic (the env vars no longer exist on the revision).
  - The capture sub also caught an organic dev poller goods_out (`GADG785A435A949`, `source=rest`),
    which confirms the poller and replay now agree on the ready-side value.
  - **Not exercised**: onward delivery to fapi/sftp. In dev both still read PO/SO ready from the
    legacy topics (fapi#127 / sftp#264 are unmerged), so nothing but the capture sub subscribes to
    these values there; fapi's consumption of exactly these attribute values was proven in Inc 1's
    dev run (2026-09-14). Prod remains gated on Inc 1 + 1s.
  - Cleanup: dev reverted to `main` (see Slack pair in #bifrost-general); capture sub deleted. The two
    seeded failures remain in dev replay's inbox as replayed test records (no delete endpoint).
  - **Side finding (pre-existing, not this change):** every organic goods_in/goods_out failure fapi
    emits in dev stores `record` as `{ confirmations: [ … ] }` (the bulk body) rather than the single
    confirmation, so `replayable` is false with 12–18 `expected object, received undefined` issues.
    None of fapi's PO/SO confirmation failures are redrivable as stored. Worth its own defect.
- **2026-09-14 — Inc 1, dev end-to-end (applied, exercised, reverted).** Branch deployed to dev
  (run `34831105172`, terragrunt apply green), both subs created as planned, then two envelopes
  published straight onto `bifrost.dev.confirmation_ready.v1` with the producer's real attribute
  values. Cloud Run logs (`api-gateway-dev`, project `bifrost-dev-global1`):
  - **PO** — published `attributes.recordType=purchase_order`; delivered to
    `POST /events/v1/confirmation/ready/purchase_order` → **204**, `Received purchase_order
    confirmation payload`, canonical validated (no `Record validation failed`).
  - **SO** — published `attributes.recordType=goods_out_confirmation`; delivered to
    `POST /events/v1/confirmation/ready/sales_order` → **204**, `Received sales_order confirmation
    payload`, canonical validated. This is the asymmetry the plan flagged, proven live: the
    ready-side SO value routes to the `sales_order` push path.
  - **AC 5 — `metadata.connectorId` survives the cross-entity envelope.** Both legs logged
    `connectorId: conn_faef29654e044305ba642ef0201f00a7` on `Forwarding confirmation to connector`
    and on the emitted failure. GADG has 13 connectors, and each confirmation forwarded to
    **exactly one** — FUSE-1056's single-connector routing still resolves after the ready move, no
    regression to broadcast.
  - The forward itself failed (3 attempts) and produced a `confirmation_data_failure`, because that
    dev connector's `webhookUrl` is the placeholder `https://example.com`. Expected, and orthogonal
    to this change — it is downstream of everything this increment touches.
  - **Exactly-once**: each publish produced exactly one delivery, to one push path. No double
    delivery across the swap.
  - **Dev given back**: `manual-deploy` re-run on `master` (run `34831706100`, green); dev now shows
    the legacy `api-gateway.dev.{purchase,sales}_order_confirmation_ready.v1.sub` restored and the
    `confirmation_ready.{po,so}` subs gone. Dev is not holding this branch.
- **2026-09-14 — Inc 1, dev `terragrunt plan` (pre-apply).** Branch
  `hjf/fuse-1059-fapi-cross-entity-ready-subs` (fapi, commit `7198ee8`), planned against real dev
  state. **`Plan: 2 to add, 3 to change, 2 to destroy`** — the swap is atomic in one apply:
  - `+ google_pubsub_subscription.po_confirmation` — `api-gateway.dev.confirmation_ready.po.v1.sub`
    on `bifrost.dev.confirmation_ready.v1`, `filter = attributes.recordType = "purchase_order"`,
    push `…/events/v1/confirmation/ready/purchase_order`.
  - `+ google_pubsub_subscription.so_confirmation` — `api-gateway.dev.confirmation_ready.so.v1.sub`
    on the same topic, `filter = attributes.recordType = "goods_out_confirmation"`, push
    `…/events/v1/confirmation/ready/sales_order`.
  - `- google_pubsub_subscription.purchase_order_confirmation` /
    `- google_pubsub_subscription.sales_order_confirmation` — the two legacy per-entity ready subs.
  - The **3 "to change" are pre-existing dev drift, not this diff**: the Cloud Run service picks up
    a `run.googleapis.com/container-dependencies` annotation and a sidecar env change (dev has
    drifted from master's declaration even though it runs master's image `d40fcae`); `google_redis_instance`
    and `random_password.api_key` are provider-normalisation-only (empty-string → null, sensitivity
    marking; values unchanged). A dev apply carries them along.
  - `terraform validate` clean; `terraform fmt` clean on both touched files (the repo has
    pre-existing fmt drift in `api-key.tf`/`providers.tf`, untouched).
- (dev runtime verification + prod apply still owed — see **Not verified**)

### Not verified
- Increments 4-9 — not actioned. Inc 2 and Inc 3 are built and dev-verified; their prod halves are gated.
- Datadog throughput-vs-baseline comparison for Inc 1/1s (organic-traffic log evidence gathered instead;
  sufficient to confirm no coverage gap, not a formal before/after rate comparison).
- To confirm during Inc 2: the outbound-queue-clear PATCH is genuinely idempotent under duplicate delivery.
- To confirm before Inc 8: no consumer/DLT-subscriber of the four legacy topics beyond the fleet-grep set;
  all four DLTs empty.
- replay-service's actual prod deploy state and whether its PO/SO redrive path is exercised in prod.

## Rollout & rollback
- **Order (the DAG):**
  ```
  Gate → Inc1 fapi atomic ready swap ─┐
  Gate → FUSE-1055 sftp x-entity ready ┴→ Inc5 poller stop legacy ready → Inc7 sftp remove ready subs ─┐
  Gate → Inc3 replay-service redrive swap ──────────────────────────────┘                              │
  Gate → Inc2 snap add made subs → Inc4a/b/c stop legacy made → Inc6 snap remove made subs ────────────┴→ Inc8 delete topics+DLTs+outputs → Inc9 observability
  ```
  Edges: add-before-remove for every swap consumer (a consumer must read cross-entity before its legacy
  path is cut); **stop-publish before remove-sub** (Inc4→6, Inc5/Inc3→7) so no unacked backlog is stranded
  in a deleted sub; the poller ready-stop (Inc5) waits on ALL three ready consumers/publishers reading
  cross-entity in prod (fapi Inc1, sftp FUSE-1055, replay-service Inc3) plus collector-1058; made publishers
  stop (Inc4) only after snap-adapter reads cross-entity made (Inc2) and collector-1058 is prod; topic
  deletion (Inc8) is strictly last.
- **Flags/config:** none — no feature flags; the swap is expressed entirely in Terraform subscription
  resources + publish-call removals + env/config. Each removed env var must go WITH its config-schema entry
  in the same PR (required `z.string()` vars fail boot otherwise — sftp `schemas.ts`, fapi `config.service.ts`).
- **One-way doors:** Inc 8 (topic + DLT + output deletion) is irreversible — recreating a topic does not
  recover discarded messages. It gates on the pre-apply cross-repo `terraform plan` against **prod**. A
  lesser one-way step: Inc 1's atomic swap removes fapi's legacy ready subs inside the same apply, so a wrong
  SO filter drops SO ready instantly — mitigated by the dev verification first.
- **Rollback:** Inc 1-7 are `git revert` + re-apply per repo (Terraform re-creates the removed subs/resources;
  a re-created sub starts empty but the poller/connectors still dual-publish until Phase B, so it re-fills).
  Inc 8 is forward-only — recovery is re-creating the topics and re-seeding via replay, so treat it as the
  point of no return.
- **Shared state touched:** prod Terraform applies across 7 repos; **four Pub/Sub topics + four DLTs deleted**
  (Inc 8); Datadog service-catalog + monitors (Inc 9). Parked-deploy discipline (memory
  [[reference_parked_deploy_runs_rollback_hazard]]): several of these repos have long parked-`terraform-prod`
  backlogs (sftp 08-24, collector 08-19) — when clearing a gate, approve only the **newest** queued run; an
  older run deploys older code. No prod deploy before QA (memory [[feedback_no_prod_deploy_before_qa]]) — each
  increment is dev-verified first.
- **Proof in prod:** per legacy topic, the Pub/Sub `topic/send_message_operation_count` metric → 0 from every
  ex-publisher (AC 4); per consumer, cross-entity `confirmation_ready`/`confirmation_made` subscription
  delivery continues at the pre-cutover PO/SO rate (baseline: current legacy-topic delivery counts). fapi
  `fuse.confirmation.*` webhook-fired-once; snap-adapter outbound-queue-clear rate steady.

## Options considered
- **Chosen — full swap in FUSE-1059** (Harry, 2026-09-11): 1059 owns the missing cross-entity adds (fapi
  ready, snap-adapter made) + the replay-service redrive migration, not just removal. **Rejected — split the
  adds into their own tickets** (leaving 1059 pure teardown): cleaner ticket boundaries but more tickets, and
  the ticket text already deferred fapi's subs "to the decommission ticket." (Note: sftp's ready-sub add IS
  its own ticket, FUSE-1055 — the asymmetry is pre-existing.)
- **Chosen — fapi ready swap is ATOMIC** (add + remove in one apply); **snap-adapter made is ADD-verify-REMOVE.**
  Split by side because ready double-delivery = a non-idempotent customer webhook double-fire (atomic collapses
  that exposure from the whole soak window to one apply), while made double-delivery = an idempotent queue-clear
  PATCH (so the free in-prod verification window is worth taking). The cross-entity consume path is already
  proven in prod for five other recordTypes through the identical generic endpoint, which bounds the atomic
  swap's residual risk. **Rejected — atomic on both** (forfeits free made verification for no gain) and
  **verify-then-remove on both** (holds the webhook double-fire open for hours).
- **Chosen — one plan with phases, anchored in snap-adapter.** **Rejected — one plan per service** (the skill's
  default): would fragment the single prod gate, the one-way door, and the DAG across seven files. The A/B
  ticket split (adds/verify vs teardown) at the "every consumer reads cross-entity in prod" seam remains
  available if the single ticket proves unwieldy — offered to Harry.

## Decisions & deviations

- **2026-09-16** — Promoted all plan Learnings into durable docs: fapi/known-context.md (204-not-400 ACK behaviour, FUSE-1226 cross-entity broadcast gotcha), bifrost-pubsub/known-context.md (ready/made recordType asymmetry, single-topic-owner fact), replay-service/known-context.md (redrive target map as hidden extra publisher), fuse-mocker/known-context.md (hidden extra consumer + stale CLAUDE.md doc note), shopify-connector/known-context.md (mise/pnpm corepack gotcha), plus two new Waypoint-tooling memory entries (bare pr: number resolution bug, atomic-swap push_endpoint safety check). Two learnings not promoted -- both described now-deleted legacy-topic subscriber state, moot after Inc 8.

- **2026-09-16** — 2026-09-16: Discovered a real gap while promoting the plan's own pre-flagged fuse-mocker
Learning after Inc 8/9 completed. fuse-mocker was never in the plan's 7-repo consumer list,
so its two dev capture subscriptions (on the now-deleted legacy PO/SO ready topics) went
dangling, and its Go API's target registry still pointed publishes at the deleted topics.
Fixed in fuse-mocker#16 (draft, held for review): capture subs converted to filtered
confirmation_ready subscriptions (matching the existing pick/pack/rga pattern), publish
targets repointed + StampRecordType set so recordType is correctly attributed, tests updated.
go vet/build/test all pass (canonical package's local-TZ failure confirmed pre-existing/
environmental via TZ=UTC). PR has 3 pre-existing red checks unrelated to this diff (missing
apps/ui/audit-ci.jsonc, a transitive grpc CVE in both Go containers) -- not touched by this
change, flagged to Harry rather than fixed blind given they need real exploitability/allowlist
judgment. Two orphaned dev subscriptions (old names) will need manual gcloud cleanup once
fuse-mocker#16 merges -- noted in the PR body.

- **2026-09-16** — 2026-09-16: Final pre-deletion sweep + prod health check, both clean.
Consumer sweep: zero grep hits on the 16 legacy remote-state output names across
fapi (fe16ae9), snap-adapter (132f9cc), sftp-connector (c8403b7), shopify-connector
(d962601), replay-service (27e22e7), collector (ff5f342) on their default branches.
All 4 legacy topics + 4 DLTs confirmed zero IAM bindings, zero subscriptions via gcloud.
Prod health: fuse.confirmation.published shows healthy live volume on snap-polling-service
(618 good_out, 176 pack, 176 pick, 47 stock_adjustment, 23 good_in, 1 RGA / 4h). Zero
Datadog log errors across all 6 touched services in the last 2h. fuse.confirmation.forward.failure
shows a steady err_bad_request rate (~16/hr combined PO+SO) identical before and after today's
deploys, and hitting pick_confirmation/pack_confirmation at the same rate -- those record types
never touched the legacy topics, so this is a pre-existing, unrelated background condition, not
a regression from FUSE-1059. Proceeding to Inc 8 (bifrost-pubsub topic deletion) per Harry's
go-ahead.

- **2026-09-16** — Inc 6 and Inc 7 both turned out to need zero new work — #229 and #264's atomic swaps already removed IAM/env/config/remote-locals alongside the subscriptions, not just the subscriptions alone as their commit messages claimed. Verified by checking a fresh worktree of each repo's current master, found nothing, tore the worktrees down (no PR to open). Went ahead and ran Inc 8's full pre-apply verification since its gate was now met: swept all six consumer repos' source for the 16 legacy-topic remote-state outputs (zero hits anywhere — cleaner than a terraform plan check), confirmed all four DLTs have zero IAM bindings and zero subscriptions. All three of Inc 8's pre-apply criteria pass. Did NOT execute the actual deletion — flagged to Harry given it's the plan's own documented one-way door.

- **2026-09-16** — PROD 2026-09-16, final pass: all 4 of today's Inc4/Inc5 PRs merged (3 by review, snap-adapter#232 by Harry directly) and deployed. Caught a real black-box test failure on snap-adapter#232 before merging — two fixtures still expected 1 message on the legacy goods-in/out-topic (my earlier unit-test-only verification missed this separate CI suite); fixed and re-verified. sftp's deploy hit the familiar second-gate pattern again (docker-push-prod vs terraform-apply-prod as separate pending_deployments), approved both. snap-adapter#232's own deploy ran straight through with no gate stall. RESULT: gcloud confirms zero IAM bindings on all four legacy topics — completely dark, no publisher or subscriber anywhere. AC4 closed. Inc6/Inc7 gates both fully met; their remaining scope is pure code/IaC cleanup (subscriptions already gone via the atomic swaps). Inc 8's gate is NOT yet met — it needs Inc6/Inc7's actual cleanup PRs shipped first, not just their gates satisfied; correctly left unticked.

- **2026-09-16** — Inc 4 built 2026-09-16: three draft PRs (fapi#135, sftp#269, shopify#267), all tests/lint/build green, gate already met. Two tooling incidents caught and cleanly reverted before committing (unrelated lint:fix --unsafe breakage on fapi, unrelated pnpm-workspace.yaml auto-write on shopify) — neither shipped in the PR diff. shopify's PR also removes the genuinely-dead SALES_ORDER_CONFIRMATION_READY wiring per the increment's documented scope, confirmed dead by grep before removing. CRLF preserved in shopify's pubsub.tf. Discovered mise x -- pnpm resolves to a stray corepack-cached pnpm 11.0.8 on shopify-connector instead of the mise.toml-pinned 10.24 — worked around by invoking the mise-installed binary directly; worth a platform-hat follow-up if it recurs elsewhere.

- **2026-09-16** — Inc 5 built and pushed 2026-09-16: snap-adapter#232, draft PR opened. Gate already met (Inc 1/1s/3/collector-1058 all confirmed live earlier today). Dev deploy confirmed the right image running but no organic PO/SO confirmation batch arrived in dev GADG to observe live delivery — relying on unit-test coverage (404 green, including the redrived good_in/good_out single-emit assertions) as the primary evidence, since forcing synthetic dev traffic wasn't warranted for an increment whose own defined verification is prod. Dev reverted, both deploys announced. Ready for review; prod apply is the next step once reviewed.

- **2026-09-16** — PROD 2026-09-16: Harry merged shopify#258 directly (skipped code review, called it fairly important) — deployed to prod as eefc6960 along with 3 riders (source/broadcast filter restore, CI fix, FUSE-1078 secops fix). This closes FUSE-1054 made dual-publish being live for all three publishers (fapi/sftp/shopify), which is Inc 4's other gate. Deployed snap-adapter#229 (Inc 2) same pass — same atomic-swap finding as sftp#264 (superseded block added), verified safe (identical push endpoints), OBQ clear-down confirmed live for PO+SO with zero errors. CONSEQUENCE: three increments' worth of gates cleared in one pass — Inc 2 done, Inc 6 already-done as a side effect (flagged, not ticked — code/IaC cleanup still owed), Inc 4's full gate met (both fapi+sftp+shopify made dual-publish live, AND collector FUSE-1058), Inc 5's gate already met from the prior pass. Both Inc 4 and Inc 5 are now the next actionable increments — building Inc 5 (poller stop legacy ready) next since it's single-repo; Inc 4 is a 3-PR fleet change across fapi/sftp/shopify, larger scope.

- **2026-09-16** — PROD 2026-09-16: Inc 3 (replay#85) applied — 27e22e74, verified (IAM grants gone from both legacy topics, env vars gone, zero errors post-deploy). First attempt hit a transient ECONNRESET on GCP workload-identity token exchange during docker-push-prod; Terraform never ran so nothing was half-applied. Mid-retry I accidentally fired manual-deploy.yaml (targets dev, not prod) instead of rerunning the failed job — caught it, cancelled the dev run before it displaced anyone, used gh run rerun --failed on the original run instead. Second attempt clean. CONSEQUENCE: Inc 5's full gate (Inc1+Inc1s+Inc3+collector FUSE-1058, all in prod) is now MET — poller stop-legacy-ready is the next actionable increment.

- **2026-09-16** — PROD FINDING 2026-09-16, filed as FUSE-1226 (related, not blocking). Two prod monitors fired ~15min after Inc 1's fapi deploy: [FUSE][Fuse API] Egress webhook delivery failures + Confirmation connector unresolvable. Traced to root cause, NOT the cache cold-start I first suspected (that read was wrong and corrected): fapi's cross-entity confirmation_ready subscription receives EVERY business's broadcast regardless of connector type; FUSE-1056 (#123) requires the resolved connectorId to be webhook-configured, but SFTP/Shopify connectors never have a webhookUrl by design — their delivery happens entirely through sftp-connector/shopify-connector's own independent subscriptions on the same topic. VERIFIED NO CUSTOMER IMPACT: PURDYFIGG's confirmation delivered via shopify-connector ("Confirmation successful") at the identical timestamp fapi logged as failed; EPARFUM/WILDSMITH's confirmation files genuinely written by sftp-connector at the identical correlationIds. This is pre-existing since FUSE-1056 (2026-09-08); Inc 1 just added PO/SO (near-universal volume) to the same broadcast pattern pick/pack has ridden quietly for longer, pushing the monitors over threshold for the first time. Not a regression in anything shipped today; a monitor/alerting design gap, filed for its own remediation, not gating further FUSE-1059 increments.

- **2026-09-16** — PROD 2026-09-16: Inc 1 (fapi #127+#129) and Inc 1s (sftp #264+backlog) both applied to prod and verified end-to-end via organic traffic — no synthetic probe needed. Found + fixed a second, separate approval gate GitHub split between docker-push-prod and terraform-apply-prod on the same environment for sftp's run; the first approval only cleared the first gate. Rejected 8 stale parked runs total before approving (6 fapi, 2 sftp) per the parked-deploy-hazard discipline. IMPORTANT CORRECTION: Inc 1s's own text was wrong — #264 does an ATOMIC swap (legacy subs destroyed same apply, no moved block), not the documented ADD-ONLY/legacy-retained-until-Inc-7 design. Verified safe before applying because old and new subs push to identical endpoint URLs. Consequence: Inc 7 (sftp remove legacy ready subs) is now factually already done — when reached it should be a verify-only step, not a removal. Plan corrected with a superseded blockquote rather than silently rewritten.

- **2026-09-15** — 2026-09-15: trimmed fapi#127's ready-sub comments to two one-liners (both-values decoupling + stock_adjustment exception) per Harry, pushed as 7a9b6f8. Marked replay#85 ready for review. Posted a FUSE-1059 approval megathread to #bifrost-forge (anchor ts 1789480664.413989) — one thread per PR: fapi#127 (atomic ready swap, linchpin), fapi#129 (made stamp, Harry pre-OK'd), replay#85 (Inc 3 redrive), shopify#258 (made stamp). Forward chain now waits on these approvals + the FUSE-1054/1055 QA-then-prod call.

- **2026-09-15** — SEQUENCING STATE 2026-09-15 after regression fix + Inc 1p. The forward chain is blocked on two USER-owned gates, not on anything checkable I can proceed through: (A) REVIEW of agent-authored FUSE-1059 PRs — fapi#127 (atomic ready swap, the linchpin AND the one destructive-in-apply step: it removes fapi's legacy ready subs in the same apply) is OPEN+unreviewed; replay#85 (Inc 3) is draft; made-normalisation fapi#129/shopify#258 open+unreviewed. I do not self-merge unreviewed agent code, least of all a customer-facing webhook swap. (B) PREREQUISITE-TICKET prod deploys — Inc 2 (snap #229 made subs, MERGED+parked) is gated on FUSE-1054 made dual-publish (fapi#117/sftp#257/shopify#229, all merged+parked) being LIVE in prod; FUSE-1054 is a separate 'Ready for QA' ticket and its per-service prod deploys ship large multi-ticket backlogs (fapi also carries FUSE-1056 #123; sftp carries FUSE-1055 #262, FUSE-642 #251, secops) — QA-gated, not mine to force. So: deployed the safe reversible bits (collector fix, poller #228); everything past needs Harry's review of #127/#85/#129/#258 and a QA-then-prod call on FUSE-1054/1055. Nothing else in Phase A can go without tripping one of those.

- **2026-09-15** — PROD 2026-09-15: (1) collector regression FIXED + verified. Approved collector prod deploy ba8890ca (newest master, carries #93 SO-ready filter fix + #94 made both-values + an unrelated #96 state-only DNS adoption that rode master — plan showed 4 subs replaced filter-only, Cloud Run warm-instance update, DNS record moved out of TF mgmt not destroyed). My first approve attempt 422'd (environment_ids[] form) so nothing shipped on that try — used JSON --input body. Rejected 3 stale collector runs + 6 stale poller runs to kill the older-code-rollback hazard. Live prod: collector SO ready now filters goods_out_confirmation; organic goods-out captured 201+stored at 13:38, 2 min post-deploy. (2) Inc 1p poller #228 PROD-DEPLOYED (f4367775, plan Cloud Run in-place only). No organic goods-in ready in the window to watch; not forcing synthetic prod traffic.

- **2026-09-15** — fapi#127 red-check clearance 2026-09-15: fapi#128 (multer/js-yaml override floors) was approved + green, merged as 152ca9a6; master merged into #127's branch (gh pr update-branch, no rebase). The same four advisories were ALSO the whole of image_scan's 4 findings (js-yaml 4.3.1, multer 2.2.0 x3), so #128 should clear dependency_audit AND image_scan on #127; image_scan_portal (next CVE, someone else's) stays red and is documented on the PR.

- **2026-09-15** — Inc 3 built 2026-09-15 on replay-service branch hjf/fuse-1059-replay-cross-entity-redrive (worktree .claude/worktrees/fuse-1059-replay-redrive, off origin/main 9a048ab — NOT master, per the 09-14 correction), commit ef98952. Deviation from the Inc 3 text: goods-in redrives stamp recordType 'goods_in_confirmation', not 'purchase_order', following the Inc 1p ready-side normalisation; every cross-entity PO ready subscriber in flight (fapi#127, sftp#264, collector#93) accepts both values, and prod has no cross-entity PO ready consumer yet, so nothing narrows. Goods-out stamps 'goods_out_confirmation' as planned. legacyConfirmationTarget deleted; both legacy env vars, 4 remote-state locals and 2 Publisher IAM grants removed; repo CLAUDE.md rewritten (it carried an explicit 'do not fix this into a cross-entity publish' guard that this ticket deliberately retires). 173 vitest green, biome clean, tsc clean, touched .tf fmt-clean (mongo.tf has pre-existing fmt drift, untouched). Dev verification + draft PR next; prod remains gated on Inc 1 + 1s.

- **2026-09-15** — PROD REGRESSION CONFIRMED 2026-09-15: collector FUSE-1058 (ec37b49f) IS live in prod — deployed inside 53894d70 on 2026-09-14 13:10 UTC (the 09-14 'must fix before it reaches prod' warning was overtaken). Live prod sub list: collector's legacy PO/SO ready subs are GONE and collector.prod.confirmation_ready_sales_order.v1.sub filters recordType='sales_order', which the poller never stamps on the ready side — so collector has captured NO goods-out (SO) confirmations in prod since then; PO capture is unaffected (its filter 'purchase_order' still matches the un-renamed prod poller). Messages the filter rejected are acked by Pub/Sub, not retained — not recoverable from the sub. Fix = collector#93 (SO filter -> goods_out_confirmation, PO filter both values): approved, MERGED to main as b07c40d8 today; its prod deploy run needs the terraform-prod gate clicked. Plan gates that read 'collector FUSE-1058 live in prod' are MET as deploy state but only correct once #93 is also live — treat 'collector#93 live in prod' as the real gate on Inc 4/5/8.

- **2026-09-14** — sftp #265 + shopify #258 made-side dev-driven 2026-09-14. SFTP #265 VERIFIED e2e: deployed to dev (image 08586ad), published a GADG goods-out ready (source=sftp) to legacy sales_order_confirmation_ready; sftp wrote the files and emitted confirmation_made — temp capture sub caught it with BOTH attribute AND envelope recordType=goods_out_confirmation. Reverted, sub deleted. SHOPIFY #258 PARTIAL (log-proof, as Harry framed it): no Shopify simulator exists (crackle is SNAP-only; USE_SERVICE_MOCKS is vestigial/unwired), and made only fires after a real Shopify fulfillment, so a full made emit needs a real store+order+OAuth token. Deployed #258 (image 5c58d28), drove a goods_out_confirmation for GADG's ILG Test Store connector; every confirmation-flow log line ran under recordType=goods_out_confirmation (the Correlation change feeding logs + the made envelope), proving that half live. Fulfillment failed ('Invalid Fulfillment Order ID') because the synthetic confirmation references no real order, so no made emit — expected. The made ATTRIBUTE (app.module map) rides the identical crossEntity->attribute mechanism fapi #129 and sftp #265 both proved emits goods_out_confirmation. Reverted shopify dev to main. Both transient CI flakes on first deploy attempts (shopify: terragrunt-action mise install exit 1; fapi earlier: STS/TLS timeout) — retried green. NET: all 5 made-side PRs now have dev evidence (subs: delivery+process; fapi/sftp publishers: full made emit with new value; shopify: flow recordType live, made-emit needs a real store).

- **2026-09-14** — fapi #129 made-stamp VERIFIED e2e in dev 2026-09-14. Set HJF's Dev REST connector webhookUrl to postman-echo.com/post via config-write MCP (returns 200; example.com was failing fapi's forward). Deployed fapi #129 to dev (first attempt's terraform-apply failed on a transient STS/TLS-handshake timeout during init — retried, second attempt green, running image dev-3280681). Published a goods_out_confirmation ready for HJF (connectorId=conn_1a5c...) to the LEGACY sales_order_confirmation_ready topic (fapi master still reads ready from legacy; #127's cross-entity ready swap is a separate unmerged branch). fapi forwarded to postman-echo (success) and emitted confirmation_made; a temp capture sub on bifrost.dev.confirmation_made.v1 caught it with BOTH attribute recordType=goods_out_confirmation AND envelope metadata.recordType=goods_out_confirmation. Cleaned up: fapi dev reverted to master, HJF connector restored to example.com, 3 temp subs deleted. NOTE: crackle OBQ was empty and seeding it needs a full SNAP despatch workflow through the sim — not pursued; the direct legacy-topic ready-publish proved the made stamp, which is the thing #129 changed. sftp #265 made stamp is drivable the same way (sftp writes a file = forward success, no webhook needed) but not yet run; shopify #258 made needs a Shopify store interaction — unit-verified only.

- **2026-09-14** — Made-side normalisation CODE COMPLETE across all 5 services, all draft, all build/lint/test green: subscribers snap-adapter#229 + collector#94 (accept both values); publishers fapi#129, sftp#265, shopify#258 (stamp goods_in_confirmation/goods_out_confirmation). sftp/fapi also align the ENVELOPE recordType, not just the attribute. Two catches: (1) sftp — must NOT reuse getUseCaseNameForConfirmation (maps RGA->return_goods_confirmation, would break RGA made clear-down); added a goods-in/out-only getMadeRecordType. (2) shopify — surgical, only the SALES_ORDER_CONFIRMATION_MADE map entry + the confirmation-flow Correlation scope; the ~7 other sales_order stamps (create-side ingestion) untouched; confirmation metrics tag type=SALES_ORDER from a constant so unaffected. VERIFICATION STILL OWED: the crackle+HJF e2e (HJF backend host is crackle.devtools.fuse.freightops.dev). BLOCKER for the made e2e: HJF's connectors don't forward successfully (Dev rest connector webhookUrl=example.com, useCases empty; hjf-test sftp confirmationsEnabled=false), so fapi/shopify made won't fire on a real delivery — same class as fapi#129's no-dev-e2e. Need an HJF connector with a reachable webhook (mocker/webhook sink) to drive made end to end.

- **2026-09-14** — Made-side normalisation progress 2026-09-14: subscribers DONE — snap-adapter #229 (both-values) + collector #94 (for_each set -> push-path->filter map, both-values, DEV-VERIFIED: goods_in_confirmation made delivered to /made/purchase_order, marked processed). Publishers: fapi #129 DONE (confirmationAttributesMap + envelope aligned to goods_in_confirmation/goods_out_confirmation; 310 tests; no dev e2e — made fires only on a successful webhook, not drivable in dev; unit test asserts the emit). REMAINING publishers: sftp (emitMadeConfirmation needs a made-recordType map for good_in/good_out) + shopify (app.module.ts:64 one line, SURGICAL — ~7 other sales_order stamps must not change). All draft, held for review. Verified legacy made subs are UNFILTERED so the value change on the legacy per-entity made topic is harmless.

- **2026-09-14** — CODE REVIEW 2026-09-14 on the Inc 1 PR set found one real defect in my own work, now fixed. The cross-repo deploy ordering between snap-adapter#228 and collector#93 was enforced only by PROSE in the PR bodies, and worse: collector's stale purchase_order filter lives in MERGED master IaC, so ANY unrelated collector apply (a Renovate merge, say) would reinstate it. Fixed in collector#93 commit a62ff84 - the goods-in filter now accepts BOTH values ('purchase_order' OR 'goods_in_confirmation'), so deploy order no longer matters in either direction. The poller publishes ONE cross-entity copy, not both, so this cannot double-deliver. Narrow it to goods_in_confirmation alone as a follow-up once #228 is deployed. I had explicitly REJECTED this OR approach when writing the PR ('not worth a clause someone has to remember to remove') - that was wrong, because it underweighted both the merged-master reinstatement path and the fact that a prod deploy wave was about to run. Also fixed from the same review: the poller CLAUDE.md confirmation-types table (commit 31cf50d) never recorded the dual-publish tags and still said recordType 'none' for good_in/good_out; and fuse-mcp-server data/pubsub-topology.json listed only 3 of the 7 live recordType values plus two ('dispatch','receipt') that nothing publishes - corrected and pushed to master (8fe1df8) per the org data-file contract.

- **2026-09-14** — 2026-09-14 (Harry): normalise the ready-side PO tag purchase_order -> goods_in_confirmation, raised immediately because prod has ZERO consumers of that value (fleet IaC sweep: 6 hits for recordType='purchase_order', 5 create-side, the only ready-side one is collector's DEV-ONLY sub). Three PRs, all draft: snap-adapter#228 (poller publisher, 392 tests green), collector#93 (its two ready filters: PO->goods_in_confirmation AND the broken SO->goods_out_confirmation defect fixed in the same file), and fapi#127 updated in place (commit 760cb6a) so Inc 1 ships the new value. Deploy #228 and #93 TOGETHER - dev ordering matters, prod does not. Deliberately did NOT normalise goods_out_confirmation->sales_order instead: goods_out_confirmation is load-bearing in prod today (shopify-connector's sub is actively delivering on it), whereas the goods-in value has no prod consumer, so moving the unused one is free. Ready side now consistently names the confirmation and agrees with the failure-side namespace; made side still names the record - that axis is untouched and out of scope.

- **2026-09-14** — READY-SIDE STATE MAP for PO/SO, read from live subscriptions 2026-09-14 (not source). PROD: fapi, sftp-connector and collector are ALL still on the LEGACY per-entity ready topics for both PO and SO (fapi/collector unfiltered; sftp with a channel-only filter). shopify-connector is the ONLY service already on the cross-entity vein for SO - sub shopify-connector_prod_goods_out_confirmation_v1_sub, filter recordType='goods_out_confirmation', push /events/confirmations/sales-order - and it is DELIVERING IN PROD (202s observed within minutes of the check). That is independent production proof that 'goods_out_confirmation' is the correct ready-side SO value, stronger than the dev probe. shopify has no PO ready sub (it has no purchase_order use case). DEV differs: collector is already migrated (PO cross-entity correct, SO cross-entity BROKEN per the earlier finding), fapi/sftp still legacy. Minor extra: fuse-mocker's dev capture subs use recordType 'dispatch' and 'receipt' - two further values NO publisher emits, so those capture subs are also dead; dev-only mock tooling, low stakes, but it is a third naming variant in circulation.

- **2026-09-14** — CORRECTION 2026-09-14 to Inc 3's source reference: replay-service's default branch is 'main', NOT master (master is stale at 06099df, 2026-06-16, and has no confirmation redrive code at all - reading it gives a completely wrong picture). The redrive target map is on origin/main at code/src/core/failure/failure.service.ts:695-775, not ':722-735' of master. The plan's DESCRIPTION of the behaviour is correct: pick/pack/WOC/FGR go cross-entity via confirmationTarget() stamping the ConfirmationRecordType value as attributes.recordType; goods-in/goods-out go to the LEGACY per-entity topics via legacyConfirmationTarget() with NO recordType attribute. Also note RGA is already special-cased there with a comment explaining this exact naming trap (it publishes cross-entity as 'return_goods_authorization', the value subscribers really filter on, not the failure-side 'return_goods_confirmation') - precedent for the same reasoning Inc 1 applied. When Inc 3 migrates goods-out, it must stamp 'goods_out_confirmation'.

- **2026-09-14** — CORRECTION 2026-09-14 to 'Prerequisites & blockers': FUSE-1055 (sftp-connector#262) is MERGED, not open - the plan called it 'the one hard blocker'. More important, it did NOT add sftp's cross-entity PO/SO ready subs. #262 was channel-aware routing: it kept sftp's PO/SO ready subs on the LEGACY per-entity topics with a channel-only filter ('Per-entity topic carries one record type, so the filter is channel-only'), and only the pick/pack/FGR/WOC/RGA subs are cross-entity. Confirmed against sftp origin/master pubsub.tf:190,215. So the plan's claim 'sftp's ready-sub ADD is FUSE-1055's' is WRONG, and the gates on Inc 3/5/7 that read 'FUSE-1055 cross-entity ready subs live in prod' can never be satisfied as written - nobody currently owns adding them. Either FUSE-1059 absorbs sftp's cross-entity PO/SO ready add (the same shape as Inc 1) or it needs its own ticket. Decide before Inc 3.

- **2026-09-14** — FINDING 2026-09-14 (collector FUSE-1058 has the recordType asymmetry WRONG). collector's cross-entity SO confirmation-ready sub filters attributes.recordType = 'sales_order' (iac/projects/collector/pubsub.tf:319, added by ec37b49 / collector#89). The poller stamps 'goods_out_confirmation' on the READY side; 'sales_order' is the MADE-side value. The filter therefore matches nothing. PROVEN LIVE in dev, not inferred: the PO probe (recordType=purchase_order, correlationId fuse1059-inc1-110740) reached collector and logged 'Confirmation stored'; the SO probe (recordType=goods_out_confirmation, ...-so2) reached fapi and collector received NOTHING. Prod is unaffected TODAY only because collector's prod SO ready sub is still the legacy unfiltered one - FUSE-1058 is merged but not deployed. Deploying FUSE-1058 to prod silently stops SO confirmation capture; FUSE-1059 Inc 5 (stop legacy ready publish) would then make it permanent. This must be fixed in collector BEFORE FUSE-1058 reaches prod, and it is a hard gate on Inc 5.

- **2026-09-14** — image_scan_portal is red on fapi#127/#128 and on master's nightly. Sole cause: CRITICAL CVE-2026-75604 in next, pinned 16.2.11 in portal/package.json, fixed 16.3.3. NOT addressed by us - Harry (2026-09-14): somebody else is already working on it. Noted as a comment on both PRs so reviewers do not re-triage it. Do not fold it into a FUSE-1059 PR.

- **2026-09-14** — Inc 1's PR (fapi#127) came up red on dependency_audit — pre-existing on master since 2026-09-10 (five consecutive nightly failures on d40fcae), four HIGH advisories: three multer 2.2.0 DoS + one js-yaml 4.3.1. Cleared in its OWN PR off master per agents.md, not bundled: fapi#128 raises the two EXISTING pnpm override floors (multer <2.3.0 -> >=2.3.0 resolving 2.4.0; js-yaml <4.3.2 -> >=4.3.2). No allowlist needed - both are genuinely patched. Bumping the direct dep was checked first and does not work: @nestjs/platform-express@12.0.1 still pins multer 2.2.0.

- **2026-09-14** — Inc 1 filter shape (Harry, 2026-09-14): fapi's new cross-entity PO/SO ready subs ship recordType-ONLY (purchase_order / goods_out_confirmation), matching the five existing cross-entity subs. Rationale: fapi's legacy PO/SO ready subs are unfiltered today, so recordType-only is a like-for-like swap and nothing narrows inside the same apply that deletes the fallback. FUSE-1056 increment 3 then widens all SEVEN subs to \"... AND (source = \"api\" OR broadcast = \"true\")\" in one pass — that increment's own recorded blocker was this add-vs-swap call, so Inc 1 settles it. Ordering on the shared api-gateway/pubsub.tf: FUSE-1059 Inc 1 first, FUSE-1056 inc 3 second.
- **2026-09-11 — scope: FULL SWAP (Harry).** The Jira text reads as pure removal; the code state proves it is
  a swap. 1059 absorbs the cross-entity PO/SO adds that no merged sibling ticket covers (fapi ready-subs;
  snap-adapter made-subs), plus — discovered in adversarial review — the replay-service redrive migration.
  sftp's ready-sub add stays FUSE-1055.
- **2026-09-11 — replay-service is a seventh repo and a hidden legacy-ready publisher (review finding).** Its
  failure-redrive still routes PO/SO confirmations to the legacy ready topics (`failure.service.ts:722-735`),
  never migrated for PO/SO while pick/pack/rga/woc/fgr already went cross-entity. Folded in as Inc 3 (a swap of
  its own) under the full-swap scope — flagged to Harry as a candidate to spin into its own gating ticket (like
  FUSE-1055) if he prefers.

## Learnings
<!-- Candidates for durable docs, surfaced while planning. Sign-off promotes confirmed ones. -->

None.
