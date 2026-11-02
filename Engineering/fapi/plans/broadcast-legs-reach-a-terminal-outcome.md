---
ticket: none
title: Broadcast legs reach a terminal outcome
service: fapi
status: complete
created: '2026-10-01'
updated: '2026-10-05'
repo: /home/hjf/code/fuse/fapi
worktree: /home/hjf/code/fuse/fapi/.claude/worktrees/broadcast-terminal-outcome
branch: hjf/broadcast-terminal-outcome
base: origin/master
base_sha: 92186ae62
pr: '162'
tags:
- waypoint
- plan
programme: poller-clear-down
unit: E1
impl_model: sonnet
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
[[Poller Clear-Down/Migration State|Poller Clear-Down]] unit **E1**, fapi leg (no ticket). Sibling plans:
[[sftp-connector/plans/broadcast-legs-reach-a-terminal-outcome|sftp-connector]],
[[shopify-connector/plans/broadcast-legs-reach-a-terminal-outcome|shopify-connector]],
[[config-service/plans/business-index-returns-connector-usecases|config-service]].
Once the poller clears rows after publish, a broadcast (or unnamed) confirmation fapi acks without a
`made` or a failure is lost. Under G5 (Migration State, "Broadcast terminal outcome"), fapi records one
`confirmation_data_failure` per REST connector that takes the type and wasn't delivered to, stamped
`source=rest` + that `connectorId`, and never acks a `made` it couldn't publish.

## Acceptance criteria
- [x] 1. A fan-out confirmation (broadcast, or no `metadata.connectorId`) to a business with no REST connector, or whose REST connectors have no `webhookUrl`, records nothing (unroutable metric/log as today).
- [x] 2. Each REST connector that takes the type and isn't delivered to — misconfigured (bad URI / missing secret), webhook non-2xx/timeout, inactive (failed leg) — gets exactly one failure per record with body `connectorId` = that connector, envelope `metadata.connectorId` = that connector, `source=rest`.
- [x] 3. Healthy connectors beside a failed leg are still delivered; `made` is published once per record when ≥1 connector delivered, before any leg-failure error is raised.
- [x] 4. A `made` that can't be published (routed or fan-out) rejects the push (500), never acks.
- [x] 5. A failure that can't be published on a fan-out push rejects the push after every leg was attempted.
- [x] 6. When the business's connectors can't be read on a fan-out push, a retryable `dependency` failure with `source=rest`, no `connectorId`, and `metadata.connectorId` removed is published and the push acks.
- [x] 7. A replay redrive of a leg failure reaches only that connector (dev e2e).
- [x] 8. Routed behaviour (fapi#155) is unchanged except AC 4; `stock_adjustment` untouched.

## Affected boundaries
- `code/src/services/confirmation.service.ts` — `routeConfirmations` (`:78-79` routed/recordFailures; `:86-89` lookup catch), candidate chain `:111-123`, `selectTargets` `:197-209`, `deliverConfirmation` (`:259` per-connector made), `isDeliverable` `:292-310`, `classifyUnroutable` `:342-361`, `tryEmitConfirmationMade` `:385-392`, `publishConfirmationFailure` `:520-571` (reused; `source: "rest"` at `:540`, rethrow on `mustRecord` `:567-569`).
- `code/src/http/controllers/confirmation.controller.ts` — `:126-127` broadcast attr; API description `:81` ("always acknowledged").
- `code/src/services/pubsub-emitter.ts` — made metadata `:204-212`; failure source `:277,285`.
- `CLAUDE.md` egress sections `:297-305`, `:352-354`.
- Contract: `confirmation_data_failure` envelope as consumed by replay-service (`resolveConfirmationRedriveRouting`: `routing` override → body `connectorId` → `metadata.connectorId`; source = channel; never broadcast). Collector also consumes it (R8, E6).

## Assumptions & uncertainty
- A REST connector "takes" every non-stock type when it has a `webhookUrl`; REST connectors carry no use-case keys (prod: PURDYFIGG, DOCKBAY, PHLUR all `useCases: []`, every key null) — live config read 2026-10-01; fapi only gates stock_adjustment per type (`:187-195`). Gating on use-case status would stop all REST delivery, so it isn't done.
- Fan-out = `!routed` (broadcast, or no `connectorId`) — matches `selectTargets`; replay redrives a no-`connectorId` failure unnamed, so it must take this path.
- Business-lookup failure publishes a retryable failure rather than nacking — follows the 2026-09-30 Decision log (no DLP → no `deliveryAttempt` budget). The redrive arrives `source=rest`, unnamed, so it fans out to this business's REST connectors only.
- `@google-cloud/pubsub` 4.11.0 already retries publish (600s total timeout, longer than the 60s push deadline), so no in-process retry; a stuck publish is redelivered by deadline either way — source read (`publisher_client_config.json`).
- One dead webhook takes ~93s (3 × 30s + 1s + 2s) against `ack_deadline_seconds = 60`; legs are sequential — redeliveries of slow broadcasts happen today. Not fixed here (E5).
- Redelivery re-POSTs every REST webhook (no idempotency key); accepted as duplicates-over-loss (R2).
- Resolved 2026-10-01 (accepted, R8; fix deferred to E6): collector treats `failed` as terminal and above `processed`, so a leg failure on a broadcast another connector delivered marks it permanently failed (Findings/collector.md). Needs Harry: change collector, or mark leg failures so collector can tell.
- Resolved 2026-10-01: an **inactive** REST connector with a webhook is a failed leg (R7 widened). G5/R7 covered inactive *mapping*; connector inactive wasn't decided. Prod impact today: none (all 3 active).

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

- [x] 1. `made` once per push, and never acked when unpublishable: move the made publish out of `deliverConfirmation` to after the leg loop (guarded by any success; stock_adjustment keeps its own path); a publish error rejects for routed and fan-out; `MadeEmitted`/`MadeEmitFailed` carry the delivered connector ids (AC 3,4) — verify: specs "emits confirmation_made once when several connectors deliver", "emits made when only some deliver", "rejects when confirmation_made cannot be published" (flip spec:1051); grep `gfs-bifrost/observability` for monitors on the made log/metric tags. — done: dd7dc56 — done: 6d9ba93
      gate: E5 (confirmation_ready retry budget) merged in fapi
            [x] confirmed — E5 merged 2026-10-02 (stack rebuilt on the default branch)
- [x] 2. Classify each REST connector on fan-out and record config-state legs: no `webhookUrl` → benign; `configurationProblem` → `business_rule`/`misconfigured`; inactive → `business_rule`/`connector_inactive` failed leg; publish via `publishConfirmationFailure({mustRecord: true, connectorId: leg})` with envelope `metadata.connectorId` = leg; routed keeps the existing chain (AC 1,2,8) — verify: specs "records nothing when the business has no REST connector", "records nothing for a connector with no webhook", "records a misconfigured connector against its own connectorId", "stamps source rest and the leg's connectorId on body and envelope". — done: a47ba3a — done: 72fd886
- [x] 3. Record webhook delivery failures on fan-out legs: every leg attempted, failure-publish errors collected and the first thrown after `made` (AC 2,3,5) — verify: specs "records a failure for each connector whose webhook fails", "still delivers to healthy connectors beside a failed leg", "attempts every connector before rejecting on an unpublishable failure" (flip spec:1230). — done: 0d75c79 — done: 619f3b6
      gate: E5 merged in fapi
            [x] confirmed — E5 merged 2026-10-02 (stack rebuilt on the default branch)
- [x] 4. Fan-out connector lookup failure: in the `:86-89` catch, publish a retryable `dependency` failure (`source=rest`, no `connectorId`, `metadata.connectorId` removed), ack; update CLAUDE.md `:297-305`, `:352-354` and the controller description `:81` for 1–4 (AC 6) — verify: spec "publishes a retryable failure with no connector when connectors cannot be read" (rewrite spec:548); then dev e2e (AC 7): branch deploy, `gcloud pubsub topics publish bifrost.dev.confirmation_ready.v1 --attribute=recordType=pick_confirmation,broadcast=true` for GADG with one webhook pointed at a 500 catcher (config write — confirm first, revert after); expect one made per record, one failure per failing leg (`replay-list-failures`, Datadog `service:rest_connector @correlationId:<id>`), `replay-retry` reaches that connector only. — done: f2c13e3 — done: 8b76e7d

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-02 [release] Prod: #161 → #162 merged atomically as a native stack (`35b2e89`). Deploy runs 37026284718 and 37026284563 (Developer Portal) were approved through `terraform-prod` after Harry agreed the plans (1 in-place change each; only #161/#162 between prod `4e9287e` and head). `api-gateway-prod` runs `prod-35b2e89`, Ready. No new prod errors on `rest_connector` after cutover.
- 2026-10-02 [inc 2-4] AC 2,6,7 — Dev e2e (branch `36dc4e3`, same E1 code as #162; dev reverted to master): pick for HJF published `source=rest` only → fapi tried HJF's one REST connector `conn_1a5c…` (webhook example.com), failed ×3, recorded one failure (`source: rest`, body + envelope `connectorId` = leg, `redriveRouting {rest, conn_1a5c…}`, replayable), acked 204, no made. `replay-retry` → routed to `conn_1a5c…` only; sftp/shopify received nothing.
- 2026-10-02 [inc 1-4] Unit: 365 tests on fapi#161 (inc 1), 394 on fapi#162 (incs 2-4); `build:check`, lint clean. Branches rebuilt as E5 tip + E1 commits (no master merge); E1 files byte-identical to the dev-verified branch.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- The made-publish failure path (AC 4) is unit-test only; Pub/Sub can't be made to fail on demand in dev.
- Made on partial success, and the inactive/misconfigured legs, are unit-verified only: no safe dev business has such REST connectors (GADG avoided: active "Fulfil.io Testing" connector).

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-10-02** — Stacked on E5 (`hjf/confirmation-retry-budget`, under review) with the default branch merged in, rather than waiting for E5 to merge: E5 touches the same confirmation code, and stacking turns the 'E5 merged' gates into merge order. The PR targets the E5 branch; gates are confirmed once E5 merges.
- 2026-10-01 — Out of this plan, each its own PR (proposed ledger rows): the RGA subscription filter (`iac/projects/api-gateway/pubsub.tf:241` is recordType-only, so every RGA routed to another channel records a false failure since fapi#155 — must land before A1's prod approval; create-before-destroy, the filter is ForceNew); the retry budget for nack paths (E5: `dead_letter_policy` block + app `deliveryAttempt` cap + `retry_policy`, per the retry-budget convention); `ack_deadline_seconds` vs the 93s webhook budget (needs the Cloud Run 300s request timeout considered).
- 2026-10-01 — Routed `made` publish failure now rejects too (AC 4). The brief said "routed as fapi#155 left it", but log-and-ack on a routed made is a loss once C2 clears rows; the invariant decides it.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
