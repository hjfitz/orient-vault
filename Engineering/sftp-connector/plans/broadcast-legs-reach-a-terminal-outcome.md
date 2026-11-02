---
ticket: none
title: Broadcast legs reach a terminal outcome
service: sftp-connector
status: complete
created: '2026-10-01'
updated: '2026-10-05'
repo: /home/hjf/code/fuse/sftp-connector
worktree: /home/hjf/code/fuse/sftp-connector/.claude/worktrees/broadcast-terminal-outcome
branch: hjf/broadcast-terminal-outcome
base: origin/master
base_sha: c7ecb31c0
pr: '301'
tags:
- waypoint
- plan
programme: poller-clear-down
unit: E1
impl_model: opus
impl_effort: high
---
# none — Broadcast legs reach a terminal outcome

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
[[Poller Clear-Down/Migration State|Poller Clear-Down]] unit **E1**, sftp-connector leg (no ticket). Siblings:
[[fapi/plans/broadcast-legs-reach-a-terminal-outcome|fapi]],
[[shopify-connector/plans/broadcast-legs-reach-a-terminal-outcome|shopify-connector]],
[[config-service/plans/business-index-returns-connector-usecases|config-service]].
Once the poller clears rows after publish, a fan-out confirmation sftp acks without a `made` or a failure
is lost. Under G5 (Migration State, "Broadcast terminal outcome"), each SFTP connector that has the use
case and wasn't delivered gets its own failure (`source=sftp` + its `connectorId`), partial delivery
still emits `made`, and an unpublishable `made` is never acked.

## Acceptance criteria
- [x] 1. On a fan-out confirmation (`!routeToOrigin`: broadcast, or no `connectorId`), a connector with no use case for the type, or a business with no SFTP connector, records nothing.
- [x] 2. A connector that has the use case but isn't delivered — use case inactive, `hasConfig: false`, connector inactive (failed leg), no username, EDI not deliverable, mapping rules unfetchable, use-case lookup error, write/upload error, invalid EDI message — gets exactly one failure per record, body and envelope `connectorId` = that connector, `source=sftp`.
- [x] 3. With several connectors, one leg's write failure doesn't stop the others; `made` is emitted when ≥1 leg delivered, before leg failures are published.
- [x] 4. A fan-out `made` that can't be published rejects the push (500) and is not recorded as `write_failed`.
- [x] 5. A fan-out leg failure that can't be published rejects the push.
- [x] 6. When the business's connectors can't be read on fan-out, a retryable `dependency` failure (`source=sftp`, no `connectorId`, `metadata.connectorId` removed) is published and the push acks.
- [x] 7. Invalid records on fan-out are published as failures only when ≥1 connector takes the type.
- [x] 8. A replay redrive of a leg failure writes only that connector's file (dev e2e). Routed behaviour (#290) unchanged.

## Affected boundaries
- `code/src/confirmations/confirmation-egress.service.ts` — `process()` zero-target branch `:181-219`, write loop `:243-252`, EDI check `:253-255`, made `:257`, write catch `:271-297` (`mustRecord = routeToOrigin` `:295`), lookup catch `:160-163`, `publishConfirmationFailures` `:344`, `selectTargets` `:374-411` (username de-dup `:407`), `selectDynamicTargets` `:413-446`, `evaluateConnector` `:448-550` (gate order active `:455` → username `:464` → EDI `:474-481` → mapping `:483`, fold `:488` → `hasConfig` `:501` → rules `:515`), stale comment `:887-888`.
- `code/src/confirmations/to-confirmation-failure.ts` — reused; `toConfirmationLookupFailure` hard-codes `"GET connector"` (`:104`); write failures carry `retryable: false` (`:31`).
- `code/src/errors.ts` — status mapping (`ConfirmationFailureNotRecordedException` → generic 500 `:241`).
- `code/src/gcs/storage.service.ts` `upsertWindowFile` `:68-159` (duplicate-row drop `:100-120`); EDI `build-edi-files.ts` hashed name + create-only `createFile` (`:214-229`).
- Guardrails: [[sftp-connector/architecture|G2 shared window object]], G3 config-is-the-contract.
- `CLAUDE.md` "routed confirmation is always recorded"; `interfaces.md:58-62`, `operations.md:72-76`, `architecture.md:150`, `known-context.md:68-71` (validation gate) — updated with increments.

## Assumptions & uncertainty
- "Takes the type" = the connector has the use case (`getConnectorUseCaseMapping` returns non-null); `null` folds into `use_case_inactive` today (`:488`), so classification must split it — source read.
- Redelivery is mostly file-idempotent: window path from `metadata.timestamp` (per minute) and `upsertWindowFile` drops existing rows; EDI names are hashed and create-only. **Exception, the normal case:** customers fetch-and-delete, so a redelivery after collection recreates the window file → duplicate rows. Accepted (duplicates over loss), stated in the PR.
- Nacking contradicts the code comment `:277-279` and `interfaces.md:60` ("never nack a write failure"); superseded here for `made`/failure-publish only — write failures still record and ack.
- Business-lookup failure → retryable failure not nack, per the 2026-09-30 Decision log; must strip envelope `metadata.connectorId` or replay redrives to the origin connector (`confirmation-redrive-routing.ts:41`).
- `hasConfig: false`, EDI-not-deliverable (incl. `FEATURE_FLAG_EDI` off) and RGA on an EDI connector are failed legs: G5 counts misconfiguration as failure, and routed (#290) already records them. Default taken; say so in the PR.
- Username de-dup (`:407`): if two connectors share a username, the failure carries the surviving target's `connectorId`.
- Resolved 2026-10-01 (accepted, R8; fix deferred to E6): collector marks a broadcast `failed` permanently on any leg failure even if another leg delivered — same question as the fapi plan.
- Resolved 2026-10-01: an inactive **connector** that has the use case is a failed leg (R7 widened). (R7 covered inactive mapping only.)

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

- [x] 1. Fan-out `made` out of the write try block; an unpublishable fan-out made throws a new unmapped `ConfirmationMadeNotRecordedException` (generic 500); routed keeps recording `write_failed` (AC 4) — verify: specs "rejects with a non-acked error when a broadcast made cannot be published", "does not record a broadcast made-publish failure as a write failure", "still records a routed made-publish failure as a write failure"; controller spec asserts 500. — done: 40be016 — done: b4b92b1
      gate: window-overwrite fix (upsertWindowFile download-after-getMetadata) and E5 retry budget merged in sftp-connector
            [x] confirmed — #297 (A5) in prod 2026-10-02; E5 merged 2026-10-02
- [x] 2. Classify every connector on fan-out: look the use-case mapping up first (passed into `evaluateConnector`, no second fetch); `null` → benign (metric reason `use_case_not_configured`); lookup error → failed leg; otherwise existing gates → failed leg with existing reason; return `failedLegs` in `TargetSelection`; routed order unchanged (AC 1) — verify: specs "consults the use-case mapping before the active gate on fan-out", "counts a connector with no use case as use_case_not_configured", "counts an inactive connector with the use case as a failed leg" (rewrite spec:1218, which is a fan-out test, not routed). — done: b9cda8d — done: 86980e7 — done: 2058760
- [x] 3. Publish failed legs when nothing was delivered: per leg, `publishConfirmationFailures(..., {...metadata, connectorId: leg}, ..., true)` with body `connectorId` = leg; invalid records published only when ≥1 connector takes the type (AC 1,2,5,7) — verify: specs "publishes one failure per connector that takes the type but is inactive", "stamps the leg connectorId on body and envelope", "stamps source sftp", "publishes nothing when no connector has the use case", "rejects when a leg failure cannot be published" (replace spec:1858). — done: 9f68f94 — done: 0deb132 — done: e2a5e54
      gate: E5 merged in sftp-connector
            [x] confirmed — E5 merged 2026-10-02 (stack rebuilt on the default branch)
- [x] 4. Partial delivery: per-target catch in the write loop, invalid EDI per target, made for valid records when ≥1 leg delivered, then failed legs published (`mustRecord` true); `FORWARD_FAILURE` per leg (AC 2,3) — verify: specs "still writes the remaining connectors after one write fails", "emits made when one of two connectors is written", "publishes a failure for only the connector whose write failed", "publishes a failure for the EDI connector whose message is invalid, not the CSV one", "emits no made when every leg fails". — done: d6a91dc — done: 4596287 — done: d2fc0f3
- [x] 5. Fan-out connector-lookup failure (any error from `tryGetConfig`): retryable lookup failure, no `connectorId`, envelope `metadata.connectorId` removed, ack; docs and `:887-888` comment updated for 1–5 (AC 6,8) — verify: spec "publishes a retryable failure with no connector when connectors cannot be read on fan-out" (replace spec:1842); dev e2e: branch deploy, `gcloud pubsub topics publish bifrost.dev.confirmation_ready.v1 --attribute=recordType=goods_in_confirmation,broadcast=true` for DAZZA (record from `mock-generate`); add `goods_in_confirmation` to inactive "harry test" (`conn_54ec5a…`) first. Expect one file under `gs://sftp-connector-dev-storage/FUSE_A718C9465E/from_ilg/purchase_order_confirmations/`, one made, exactly one `source=sftp` failure on `conn_54ec5a…` (ignore fapi/shopify failures for the same broadcast); redrive it → routed to harry test only; republish → `droppedDuplicateRows > 0`. Revert: delete the temporary mapping, PATCH harry test back to inactive re-sending `stockAdjustmentsEnabled`. — done: e8750b6 — done: 01f78ea — done: fd8baab

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-02 [release] Prod: #300 → #301 merged atomically as a native stack (`648ee6e`). Deploy run 37026303433 passed both `terraform-prod` gates after Harry agreed the plan (1 in-place change; only #300/#301 between prod `5275304` and head). `sftp-connector-prod-cr` runs `prod-648ee6e`, Ready. No new prod errors on `sftp_connector` after cutover.
- 2026-10-02 [inc 2-5] AC 1,2,3,8 — Dev e2e (`d1b27f0`; dev reverted to master): GADG pick published `source=sftp` only → Primary SFTP written + processed; ILG Test Account and AlexP-Test (inactive, have pick) → one `connector_inactive` failure each with own `connectorId`, `source: sftp`; 4 connectors without pick → nothing. Redrive of `conn_94adbd…`'s failure → routed to that connector only, re-recorded; fapi/shopify untouched.
- 2026-10-02 [inc 1-5] Unit: 818 tests on sftp-connector#300 (inc 1), 853 on #301 (incs 2-5 + invalid-record fix `d1b27f0`); `build:check`, lint clean. Branches rebuilt as E5 tip + E1 commits; E1 files byte-identical to the verified branch.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- The made-publish failure path (AC 4) is unit-test only.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-10-02** — Black-box CI went red on #300: the harness (tests/init.ts) never created test.confirmation_made_topic, so every black-box made had always failed silently; inc 1 made that a 500. Fixed in #300 (b55f3c3) by creating the made and confirmation_data_failure topics; #301 rebased on it. Both green.

- **2026-10-02** — Split into two stacked PRs on E5 (#299): #300 inc 1 (made-nack), #301 incs 2-5 plus d1b27f0 (invalid records on a fan-out name no connector, so a redrive stays on sftp's fan-out instead of routing to a possibly non-SFTP origin). Branches rebuilt by cherry-pick onto E5's tip so the PR diffs carry no master merge. Kept: a gate-failed connector sharing a delivered username still records a leg.

- **2026-10-02** — Stacked on E5 (`hjf/confirmation-retry-budget`, under review) with the default branch merged in, rather than waiting for E5 to merge: E5 touches the same confirmation code, and stacking turns the 'E5 merged' gates into merge order. The PR targets the E5 branch; gates are confirmed once E5 merges.
- 2026-10-01 — Out of this plan, each its own PR off master (proposed ledger rows): (a) A2 gaps — `config.api.ts` `handleAxiosError_` resolves 4xx so `getConnectorUseCaseMapping` returns `null` (reads as "not configured"), and a routed 4xx on `getBusinessConnectors` is a `ValidationException` acked 204; the routed lookup catch (`:160`) only sees `ConfigApiException`. Both precede inc 2, since "null = benign" makes a 4xx a silent loss. Watch `stock-adjustment.service.ts`, which has no try/catch. (b) the `upsertWindowFile` overwrite fix A2 promised. (c) RGA subscription channel filter (`pubsub.tf:222-226`), create-before-destroy, before A2's prod approval. (d) E5 retry budget.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
