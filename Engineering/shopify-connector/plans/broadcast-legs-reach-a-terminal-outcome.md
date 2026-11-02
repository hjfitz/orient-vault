---
ticket: none
title: Broadcast legs reach a terminal outcome
service: shopify-connector
status: complete
created: '2026-10-01'
updated: '2026-10-05'
repo: /home/hjf/code/fuse/shopify-connector
worktree: /home/hjf/code/fuse/shopify-connector/.claude/worktrees/broadcast-terminal-outcome
branch: hjf/broadcast-terminal-outcome
base: origin/main
base_sha: 80d1f4d03
pr: '303'
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
[[Poller Clear-Down/Migration State|Poller Clear-Down]] unit **E1**, shopify-connector leg (no ticket). Siblings:
[[fapi/plans/broadcast-legs-reach-a-terminal-outcome|fapi]],
[[sftp-connector/plans/broadcast-legs-reach-a-terminal-outcome|sftp-connector]],
[[config-service/plans/business-index-returns-connector-usecases|config-service]].
Once the poller clears rows after publish, a fan-out goods-out confirmation shopify-connector acks without
a `made` or a failure is lost. Under G5, each Shopify connector that has the goods-out confirmation use
case and could have fulfilled the order but didn't gets one failure (`source=shopify` + its
`connectorId`); an unpublishable `made` is never acked; an order that isn't this shop's stays benign.

## Acceptance criteria
- [x] 1. A fan-out `made` that can't be published requires redelivery (500); a redelivery that finds the order FULFILLED re-emits `made` on fan-out as well as routed.
- [x] 2. A business with no Shopify connector, or a connector without a goods-out confirmation mapping, records nothing (today's `no_connectors` volume — ~8k/7d prod — unchanged).
- [x] 3. A connector whose goods-out use case is inactive, whose mapping can't be read, or that fails to hydrate gets one failure per record against its `connectorId`; one bad connector no longer fails the whole business lookup.
- [x] 4. A Shopify error, short-ship with nothing fulfillable, closed/on-hold FO, or missing line fulfillment id on an order found in that shop is a failure on that shop's connector.
- [x] 5. An FO not found / FO id missing is benign when the origin is another channel or connector, or another shop delivered; a failure when the origin is this connector (manual origin: benign).
- [x] 6. When the business's connectors can't be read on fan-out, a retryable failure (`source=shopify`, no `connectorId`, `metadata.connectorId` removed) is published and the push acks.
- [x] 7. Every fan-out failure carries an explicit body `connectorId` and envelope `metadata.connectorId` = that leg (replay otherwise falls back to the origin's id → `source_mismatch`). Routed (#294) unchanged.

## Affected boundaries
Paths under `apps/shopify-connector/src/`.
- `http/controllers/confirmation-events.controller.ts` — broadcast attr `:134-136`, routing `:158`, `publishMade` `:175-194` (raw rethrow for non-routed `:186-188`).
- `http/filters/confirmation-processing.filter.ts:41-44` — 500 only on `ConfirmationRedeliveryRequiredException`, else ack.
- `core/shopify/use-cases/shopify-sales-order.service.ts` — `processConfirmations` `:139-319` (eligibility `:171-176`, `routed && alreadyFulfilled` `:287`, broadcast skips dropped `:244-250`, errors logged `:264-284`, `recordNonDelivery` early exit `:327`), `selectTargets` `:348-350`, `classifyUnroutable` `:397-408`.
- `providers/connector/connector-config.provider.ts` — `getByBusinessId` `Promise.all` `:30`, mapping fetched only when active `:115-120`, status dropped `:127`; `adapters/config/config-api.adaptor.ts:68-88` (every error → `undefined`).
- `core/confirmations/confirmation.failure-publisher.ts:39-77` (reused), `core/confirmations/sales-order-confirmation.handler.ts` (FO states `:117-181`, `:419`), `core/shopify/types.ts:8-11` (`ConfirmationRouting` gains `source`).
- Mapping state via remote-config's cached `ConnectorMappingHandler` (status passes through; `ConfigApiException` with axios `cause` and `endpoint`) — never raw per-confirmation HTTP to config-service (FUSE-952 precedent; 30s LRU is do-not-change).
> SUPERSEDED 2026-10-02 — `apps/shopify-egress-service` is Matt Shaw's **FUSE-658 stock-sync** service (FUSE-1196/1197 done, FUSE-1198 consuming `recordType=stock_sync`), not a move of goods-out confirmations. Its long-term intent (FUSE-1196) is to own all confirmation delivery, but no ticket moves goods-out there; today it resolves one connector by id, with no fan-out. E1 lands in shopify-connector; if goods-out is ever moved, port the fan-out, per-connector mapping state and origin rule with it.
- **In flight elsewhere:** FUSE-1197/1198 moving egress into `apps/shopify-egress-service` (scaffold + token/config resolution merged; `confirmation_ready` still pushes to shopify-connector, `pubsub.tf:323`). Whatever lands here gets ported there — coordinate with its owner before inc 2. Open PR #296 touches root `CLAUDE.md` `:383-412`.

## Assumptions & uncertainty
- "Takes the type" = has a goods-out confirmation mapping, plus "the order can be in this shop": a shop can't fulfil another channel's order, so not-found is only a failure when this connector is the origin — G5's principle "a leg fails iff that connector could have delivered".
- `metadata.source` and `attributes.source` both carry the origin channel (poller `confirmations.service.ts:301-302`); with `broadcastConfirmations`, broadcast=true **and** source/connectorId are set, so the origin rule can read them. Prod has 2 Shopify connectors (SAIRA, PURDYFIGG), one per business, so the "another shop" branch doesn't occur today.
- Behaviour change: a connector whose goods-out use case is inactive is fulfilled today; after inc 3 it isn't and records a failure (R7). Check both prod connectors' mapping status before inc 3.
- Redelivery of a partly fulfilled FO can double-fulfil (`fulfillmentCreate` has no idempotency key) or be rejected (PURDYFIGG's untraced "Invalid fulfillment order line item quantity requested" is a candidate). #294 already accepted this for routed; fan-out inherits it — named in the PR.
- Short-ship is a failure, matching A3's routed decision (FUSE-785's "not a failure" was reversed there); redrive will hit `nothing_to_fulfil` again. Consistency default, not re-asked.
- `confirmationsEnabled` is not read here (dropped 09-23); a leg failure redrives to that connector even if it's opted out (E2 deferred).
- Increment 4 adds per-connector mapping lookups against a 20s ack deadline; request duration is unmeasured — measure in Datadog before shipping.
- Resolved 2026-10-01 (accepted, R8; fix deferred to E6): collector permanently `failed` on a leg failure even when another leg delivered (shared with fapi/sftp plans).
- Resolved 2026-10-01: an inactive **connector** with a goods-out mapping is a failed leg (R7 widened).
- Resolved 2026-10-01: manual-origin (no source, no connectorId), FO not found, is **benign** — a manual SNAP order can't be in a shop and a redrive can't help. The poller's `no_originating_connector` record does **not** cover it (informational, not redrivable: its `source` isn't a channel). It's the main live fan-out case in prod.

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

- [x] 1. A fan-out made is never lost: `publishMade` always throws `ConfirmationRedeliveryRequiredException` (drop the `routed` parameter); remove `routed &&` at service `:287` (AC 1) — verify: specs "requires redelivery when a broadcast's made cannot be published", "re-emits made for a broadcast whose order is already fulfilled", "counts a broadcast delivered when one shop is already fulfilled and another fulfils now". — done: 8857c91
      gate: E5 retry budget merged in shopify-connector
            [x] confirmed — E5 merged 2026-10-02 (stack rebuilt on the default branch)
- [x] 2. Per-connector goods-out state on the confirmation path only: provider method hydrating each connector independently (`allSettled`), looking up the mapping via remote-config regardless of ingress status, returning `absent` (mapping 404 on the mapping endpoint — check `exception.endpoint`, a connector 404 is not "absent") / `found` + status / `unavailable`; existing callers untouched (AC 3) — verify: specs "reports a mapping 404 as absent", "reports a connector 404 as unavailable, not absent", "looks up the goods-out mapping of an inactive connector", "carries the mapping status", "reports a connector that can't be hydrated without failing the business". — done: cfffa9e
      gate: egress-move owner (FUSE-1197/1198) agrees where this lands
            [x] confirmed — 2026-10-02: no goods-out move is ticketed; Harry agreed E1 lands in shopify-connector
- [x] 3. Config-state legs on fan-out: split `processConfirmations` into routed (untouched) and fan-out; no connector / mapping absent → benign; use case inactive, connector inactive (failed leg), mapping unavailable, hydration failed → one failure each via `ConfirmationFailurePublisher` with leg `connectorId` on body and envelope; business lookup fails → retryable failure, no `connectorId`, ack (AC 2,3,6,7) — verify: specs "records nothing for a business with no Shopify connector", "records nothing for a connector without a goods-out mapping", "records use_case_inactive against the connector", "records a failure when a connector's mapping can't be read", "publishes a retryable failure with no connector when connectors can't be read"; prod read of both connectors' goods-out mapping status first. — done: 3f73f3c
- [x] 4. Delivery-outcome legs on fan-out with the origin rule: pass `attributes.source` into `ConfirmationRouting`; Shopify error / short-ship / closed / missing line id → failure on that shop; not-found / missing FO id → origin rule (AC 4,5); first settle what Shopify returns for `gid://shopify/FulfillmentOrder/SO-123` on a dev store (null → `not_found` covers it; GraphQL error → reject non-numeric FO tails as `invalid_fulfillment_order_id` before calling Shopify, fan-out path only) — verify: specs "records a Shopify error against the shop's connector", "records a short-ship as a failure on that connector", "records nothing when another channel's order isn't in the shop", "records a not-found on the origin connector", "records nothing for a not-found when another shop delivered", "publishes made and a failure when one shop delivers and another fails"; #294 specs pass unchanged; dev e2e: `gcloud pubsub topics publish bifrost.dev.confirmation_ready.v1 --attribute=recordType=goods_out_confirmation,broadcast=true[,source=…]` — (a) `source=sftp` + SFTP connectorId, `customer.order=SO-TEST-1` → nothing; (b) `source=shopify`, dev connector, missing numeric FO → one failure, redrive arrives routed; (c) dev connector mapping set inactive → `use_case_inactive` failure (revert after); (d) business with no Shopify connector → nothing. — done: 3327514

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-02 [release] Prod: #302 → #301 → #303 merged atomically as a native stack (`e1ad1bb`). Deploy run 37026333017 was approved through `terraform-prod` after Harry agreed the plan (1 in-place change; only the three PRs between prod `92b81ec` and head). `shopify-connector-prod-cr` runs `prod-e1ad1bb`, Ready. The only error near cutover (PURDYFIGG `Confirmation dispatch failed`, 15:26:05Z) was on the old revision `92b81ec`, the known missing-fulfillment-id case.
- 2026-10-02 [inc 3-4] AC 3,4,5,7 — Dev e2e (`0b8afce`, same E1 code; dev reverted to main), `source=shopify` with no connectorId (shopify-connector only): ACADEMIC `customer.order SO-E1-ACADEMIC` → FO-id guard fired for both shops, no Shopify call, one `invalid_fulfillment_order_id` failure per shop (body + envelope `connectorId` = leg, `source: shopify`, replayable); UWDG inactive connector → one `connector_inactive` failure.
- 2026-10-02 [inc 4] Dev probe: routed goods-out `SO-PROBE-123` to ACADEMIC's dev store → Shopify `GraphqlQueryError "Invalid id"` (recorded as a retryable outage before the guard).
- 2026-10-02 [inc 3] Prod read: SAIRA and PURDYFIGG goods-out mappings both `active` — the inactive-use-case rule changes no prod delivery.
- 2026-10-02 [inc 1-4] Unit: 819 / 836 / 855 tests on shopify-connector#302 / #301 / #303; `build:check`, lint clean.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- The made-publish failure path (AC 1) is unit-test only.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-10-02** — Inc 4 dev probe settled (routed goods-out, customer.order SO-PROBE-123, ACADEMIC dev store, correlationId e1-fo-probe-1790931393): Shopify answers BasicOrderQuery with GraphqlQueryError 'Invalid id: gid://shopify/FulfillmentOrder/SO-PROBE-123', not null, which today is recorded as a retryable dependency failure. So inc 4 includes the guard: on fan-out, a non-numeric FO-id tail is invalid_fulfillment_order_id before any Shopify call, then the origin rule applies. The routed path is unchanged.

- **2026-10-02** — Inc 2's egress-move gate cleared (Harry): the egress service is FUSE-658 stock sync (Matt Shaw), not a goods-out move; nothing collides. E1 lands in shopify-connector stacked on #300; the PR notes what to port if goods-out ever moves to the egress service.

- **2026-10-02** — Stacked on E5 (`hjf/confirmation-retry-budget`, under review) with the default branch merged in, rather than waiting for E5 to merge: E5 touches the same confirmation code, and stacking turns the 'E5 merged' gates into merge order. The PR targets the E5 branch; gates are confirmed once E5 merges.
- 2026-10-01 — Out of this plan: E5 retry budget (`dead_letter_policy` block + app `deliveryAttempt` cap + `retry_policy` on `pubsub.tf:315-340`), its own PR with dev and prod plans shared before apply; note the subscription change in the Shopify Connector Rearchitecture Migration State so its contract-golden test doesn't read it as drift. `repair-shopify-confirmation` skill update (its backfill-and-wait approach stops working once C2 clears rows) is a follow-up.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
