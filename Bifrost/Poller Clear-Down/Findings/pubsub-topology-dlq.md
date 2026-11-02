# pubsub-topology-dlq — Pub/Sub topology and durability for the confirmation chain

Date 2026-09-29. Read-only. Label: pubsub-topology-dlq.

## Refs read (sha)
- bifrost-pubsub@cd25f95 (origin/master): iac/modules/topic/main.tf, iac/projects/bifrost-pubsub/{confirmations,errors}.pubsub.tf
- snap-adapter@3c1578b (origin/master): iac/projects/snap-adapter/pubsub.tf, iac/projects/snap-queue-polling-service/{pubsub,schedule}.tf, apps/snap-queue-polling-service/src/{adapters/pubsub/pubsub.router.ts, core/snap/confirmations/{confirmations.service,queue-lane,confirmation-failure}.ts, core/polling/polling.service.ts, core/cache/cache.service.ts, http/controllers/event.controller.ts, bootstrap/factory/controller.factory.ts, config/config.schemas.ts}, apps/snap-adapter/src/http/controllers/event.controller.ts (handleConfirmationMade)
- collector@f19ce57: iac/projects/collector/pubsub.tf, code/src/exceptions/all-exceptions.filter.ts
- fapi@f4bd648: iac/projects/api-gateway/pubsub.tf, code/src/services/{confirmation.service,pubsub-emitter}.ts, code/src/http/controllers/confirmation.controller.ts
- sftp-connector@f6a15e3: iac/projects/bifrost-sftp-connector/pubsub.tf, code/src/confirmations/{confirmation-egress.service,stock-adjustment.service,to-confirmation-failure}.ts
- shopify-connector@835c061 (origin/main): iac/shopify-connector/projects/bifrost-shopify-connector/pubsub.tf, apps/shopify-connector/src/{app.module.ts, core/confirmations/*, http/controllers/confirmation-events.controller.ts, http/filters/confirmation-processing.filter.ts, adapters/pubsub/pubsub.service.ts}
- replay-service@d75997f (origin/main): iac/projects/replay/pubsub.tf, code/src/http/controllers/event.controller.ts
- pkg-node@4d62ab9 (origin/main): pkg/pubsub/src/router.ts, pkg/types connector.type.ts
- observability@81d508f (origin/main): iac/projects/bifrost-observability/monitors*.tf
- LIVE GCP (read-only gcloud, 2026-09-29): `gcloud pubsub subscriptions list` and `topics list` for bifrost-prod-global1 (101 subs, 47 topics) and bifrost-dev-global1 (113 subs). Saved as scratchpad/efc/subs-*.json, topics-*.json.
- Live Datadog (read-only): pubsub metrics 14-30d, replay monitors, drop metric names.
- Fuse MCP lookup-topic "confirmation". Waypoint vault: Engineering/replay-service/{known-context,operations}.md, snap-adapter/known-context.md, bifrost-pubsub/{architecture,known-context}.md (verified 2026-08-24).

## 1. Headline findings

1. **Every DLT in the fleet has zero subscriptions** (prod and dev, verified live: all 22 prod `.dlt` topics have no attached subscription; no topic has message_retention set). A dead-lettered message is permanently gone. Nothing pulls, alerts on, or redrives any DLT.
2. **No confirmation_ready, confirmation_made (except replay), or stock_adjustment_ready/made subscription has a dead_letter_policy.** The only confirmation-chain subscriptions with a DLP are replay's three (confirmation_data_failure x2, confirmation_made), all pointing at replay-owned `replay.<env>.*.dlt` topics with max_delivery_attempts=5 and 30s..600s backoff. So on the delivery hops the failure mode is not "dead-letter" but "retry (immediately, no backoff on fapi/sftp/shopify) until the 7-day subscription retention expires, then silently vanish".
3. **All subscriptions are push, no ordering keys, no exactly-once, default 7d retention (604800s), expiration ttl="" (never expire).** Prod and dev are identical for the confirmation chain except dev has 10 `fuse-mocker.dev.*.capture.sub` extra subscribers that mask "no matching subscriber" black holes in dev.
4. **The poller publish is durable once it resolves** (`await topic.publishMessage`, gax retries up to 600s total; no batching/ordering; one Pub/Sub message per business x type x connector x source group carrying an array). The poller marks nothing processed itself except items it drops. The ordering hazard is claim-before-publish (Redis SET NX, 10 min TTL) and, under the proposal, when to PATCH processed.
5. **The terminal-recording layer (replay) is itself lossy and its alerting is partly dead**: (a) DLT monitor covers only `replay.*.create_data_failure.v1.sub`, not the two confirmation_data_failure subs or confirmation_made; (b) both "dropped forever" monitors query `replay_service.event.create_failure_dropped`, a metric name that no longer exists (code emits `fuse.failure.dropped`; live: one monitor status "No Data", the other "OK" via default_zero); 32 replay drops in the last 30d (all sales_order create side) raised no alert; (c) replay ack-and-drops on Zod/decode failure, and a bulk message with one bad record drops the whole batch.
6. **Most delivery consumers ack without recording a terminal outcome** on non-delivery paths (unroutable, disabled, unmapped, any exception on shopify). Those are exactly the paths where today's recovery is "row stays on the OBQ and re-announces after claim TTL".
7. **Stock adjustments have no failure topic at all.** sftp-connector states it in code; fapi/shopify have no failure publish for stock_adjustment.

## 2. Per-topic durability table (prod == dev unless noted)

Topic naming: `bifrost.<env>.<topic>.v1`; module creates a same-named `.dlt` topic per topic (bifrost-pubsub@cd25f95:iac/modules/topic/main.tf:1-18) but topic has no message_retention_duration and no schema.

| Topic | Publishers | Subscribers (sub name, filter, ack s, retry, DLP) | Consumer DLT? | Alert |
|---|---|---|---|---|
| confirmation_ready | poller (snap-adapter/apps/snap-queue-polling-service), replay (redrive) | see 2a | none have DLP | age>300s on `*confirmation*` subs (monitors.tf:36); age>600s any sub; backlog>1000; ack-headroom>60s (excludes snap_poll_customer etc.) |
| confirmation_made | fapi, sftp-connector, shopify-connector | snap-adapter x7 (rga, po, so, pick, pack, fgr, woc; ack 300 in prod; retry 10s..600s except woc none; DLP none), collector x4 (woc, fgr, po/goods_in, so/goods_out; ack 20; retry none; DLP none), replay (pick OR pack; ack 20; retry 30..600; DLP 5 -> replay.<env>.confirmation_made.v1.dlt) | replay DLT unconsumed, unmonitored | generic age/backlog only |
| confirmation_data_failure | fapi, sftp-connector, snap-adapter (clear-down), poller (manual-origin informational), shopify-connector (unroutable) | replay `.v1.sub` (pick/pack/woc/fgr) and `.goods.v1.sub` (goods_in/goods_out/return_goods_confirmation): ack 20, retry 30..600, DLP 5 -> replay.<env>.confirmation_data_failure.v1.dlt; collector x5 (woc, fgr, goods_in, goods_out, stock_adjustment; each `AND NOT source=snap-adapter`): ack 20, no retry, no DLP | replay DLT unconsumed, unmonitored | generic age; nothing on DLT |
| stock_adjustment_ready (legacy per-entity topic, still live) | poller | fapi (ack 60), sftp (ack 20), shopify (ack 600), collector (ack 20, retry 10..600); no filters, no DLP | none | age>600s any; shopify sub num_undelivered>200 monitor |
| stock_adjustment_made | fapi, sftp, shopify | snap-adapter (ack 300, retry 10..600, no DLP), collector | none | generic |
| snap_poll_customer (poller self-trigger) | poller | poller `/event/poll/confirmations` ack 600, no retry, no DLP | n/a | excluded from ack-headroom monitor; covered by generic |
| create_record / create_data_failure etc. | out of scope | snap-adapter create_record subs DO have DLP -> bifrost.<env>.create_record.v1.dlt (no consumer; Waypoint snap-adapter known-context calls this out) | none | none |

### 2a. confirmation_ready subscriptions (live prod, identical IaC)
All: push, retention 604800s, no ordering, exp ttl "", `retainAcked` off.

| Consumer | recordType filter | source/broadcast filter | ack s | retry_policy | DLP |
|---|---|---|---|---|---|
| fapi (api-gateway.prod.confirmation_ready.{po,so,pick,pack,woc,fgr}) | per type | `source="rest" OR broadcast="true"` | 60 | none | none |
| fapi rga | return_goods_authorization | none | 60 | none | none |
| sftp-connector {po,so,pick,pack,woc,fgr} | per type | `source="sftp" OR broadcast="true"` | 20 | none | none |
| sftp-connector rga | return_goods_authorization | none | 20 | none | none |
| shopify-connector goods_out | goods_out_confirmation | `source="shopify" OR broadcast="true"` | 20 | none | none |
| collector {po/goods_in, so/goods_out, pick, pack, woc, fgr} | per type | none | 20 | 10s..600s (pick, pack, po, so); none on woc, fgr | none |
| collector rga | **does not exist** | | | | |

Evidence: gcloud live listing (scratchpad/efc/subs-bifrost-prod-global1.json); IaC api-gateway/pubsub.tf, bifrost-sftp-connector/pubsub.tf:13 (`channel_filter`), shopify pubsub.tf, collector pubsub.tf:294-460.

### 2b. Coverage matrix (which subscriber can receive which (recordType, source))
Poller stamps `source` = connector type resolved from routing provenance (`connector.config.type` = rest|sftp|shopify, pkg-node connector.type.ts ConnectorType) and `broadcast=true` when customer opts in or there is no origin (confirmations.service.ts:252-269).

- pick/pack/woc/fgr/goods_in/goods_out with source=rest -> fapi + collector. source=sftp -> sftp + collector. source=shopify -> **only goods_out has a shopify sub**; pick/pack/woc/fgr/goods_in with source=shopify (non-broadcast) reach **only collector** (no delivery consumer). Reachability not verified in prod (see open questions), but the config allows it and ROUTING_AWARE_TYPES includes pick/pack/woc/fgr (confirmation-failure.ts:31-39).
- RGA -> fapi + sftp (both, no source filter); **no collector subscription** so RGA confirmations are not persisted by collector at all.
- Any other source value (none exists today) -> collector only.
- Business with no connector at all: no origin -> broadcast=true -> every consumer receives; fapi reports unroutable via metric only (confirmation.service.ts:96-107, 288-306), sftp logs and returns.
- Dev: fuse-mocker capture subs (no source filter, per recordType incl. rga and stock_adjustment) mask all of the above in dev.

## 3. Publish semantics as used by the poller
- `PubsubRouter.emit` -> `publishToTopicNamed` -> `this.pubsub.topic(name)` (fresh Topic each call, no batching options) -> `await topic.publishMessage({data, attributes})` returns messageId only after server ack (snap-queue-polling-service/src/adapters/pubsub/pubsub.router.ts:127-146). `@google-cloud/pubsub` 5.3.0 (installed): Publish retry codes include CANCELLED/UNKNOWN/DEADLINE_EXCEEDED/RESOURCE_EXHAUSTED/ABORTED/INTERNAL/UNAVAILABLE, total_timeout 600s (build/src/v1/publisher_client_config.json). No orderingKey anywhere; no subscription has enableMessageOrdering (live: 0/101 prod).
- Failure publisher for manual-origin uses `@gfs-bifrost/pubsub` `PubSubRouter.publishToTopic`, wraps errors in PubSubPublishError (pkg-node router.ts:96-113); poller does not catch it.
- A publish error propagates out of `announceConfirmations` -> `handleConfirmationPoll` -> `next(err)` -> HTTP 500 -> the poll push message redelivers (poll sub: ack 600, no retry_policy, no DLP, 7d retention; snap-queue-polling-service/pubsub.tf) and the whole chunk is re-fetched.
- **Claim precedes publish** (`claimConfirmations` then `emit`, confirmations.service.ts:287-334; SET NX, `REDIS_CONFIRMATION_CLAIM_TTL_MS` default 600000, config.schemas.ts:64). After a publish failure the claimed items are skipped for up to 10 min (`dropClaimed`, queue-lane.ts:116-146) and are only re-emitted after the claim lapses, because the row stays on the OBQ. Claim fails OPEN when Redis is unavailable (cache.service.ts:132-135) so concurrent/redelivered polls can double-publish.
- Group loop is sequential and non-atomic: groups published before the failing group are already out; groups after it are not.
- Payload granularity: one message per (business, type, connectorId, source) group with `record: publishable[]` (confirmations.service.ts:297-321; canonical-confirmation.handler.base.ts:63-73). `$top=1000` per lane drain. Pub/Sub max message 10 MB; a group approaching that fails publish with a non-retryable error and would re-fail every poll.
- Withheld groups (connector not enabled for confirmations, connector unresolvable) return null before claim/publish and rely on the row staying on the OBQ (confirmations.service.ts:185-229; monitor text "Withheld items stay on the Snap outbound queue and re-drain automatically" monitors.snap-adapter.tf:211).

## 4. Who consumes each DLT and who alerts (decisive section)

| DLT topic (prod) | Fed by | Subscription on DLT | Monitor |
|---|---|---|---|
| bifrost.prod.confirmation_ready.v1.dlt | nothing (no sub uses it) | none | n/a |
| bifrost.prod.confirmation_made.v1.dlt | nothing | none | n/a |
| bifrost.prod.confirmation_data_failure.v1.dlt | nothing | none | n/a |
| bifrost.prod.stock_adjustment_ready/made.v1.dlt | nothing | none | n/a |
| replay.prod.confirmation_data_failure.v1.dlt | replay `.v1.sub` and `.goods.v1.sub` after 5 failed attempts | **none** | **none** (monitor regex `replay.*.create_data_failure.v1.sub`) |
| replay.prod.confirmation_made.v1.dlt | replay confirmation_made sub | **none** | **none** |
| replay.prod.create_data_failure.v1.dlt | replay create sub | none | yes (dead_letter_message_count > 0; 303413085 live OK) |
| bifrost.prod.create_record.v1.dlt | snap-adapter create_record subs | none | none |
| bifrost.prod.config_revision.v1.dlt | config consumers | none | yes |

Live check: `gcloud pubsub subscriptions list` shows 0 subscriptions whose topic is any of the 22 prod `.dlt` topics. Datadog `gcp.pubsub.subscription.dead_letter_message_count` prod, 30d: no data (nothing dead-lettered on confirmation subs); only dev `create_record_master_data` (39). `oldest_unacked_message_age` on all `*confirmation*` prod subs, 14d max: 24s. So Pub/Sub-level delivery has been healthy; the loss risk is ack-without-outcome, not Pub/Sub failure.

Replay dead-letter window: min backoff 30s, max 600s, max_delivery_attempts 5 -> roughly 30+60+120+240s of replay/Mongo unavailability (~7-8 min) is enough to dead-letter a failure record. The generic 300s oldest-unacked monitor (replay.*) would fire during that window, but the eventual DLT landing is unmonitored.

## 5. Exit paths / acked-and-lost places (per hop)

| # | Hop | Exit | Behaviour today | Recorded where | Depends on OBQ row | If row already processed |
|---|---|---|---|---|---|---|
| 1 | poller publish | publishMessage rejects | 500, poll redelivers (no DLP) | poller logs; poll sub backlog | yes (re-fetch) | only safe if PATCH processed strictly after publish ack |
| 2 | poller publish | message >10MB / permanent error | poll fails every cycle | logs | yes | confirmations stuck or lost depending on order |
| 3 | poller | claim ok, publish fails | items skipped 10 min then re-emitted | none | yes | lost if already processed |
| 4 | poller | withheld (connector disabled/unresolvable) | not published, row stays | metric snap.confirmation.withheld_*; monitor on unresolvable | **yes (documented feature)** | lost silently |
| 5 | poller | mapping/validation failure for a lane batch | caught, [] returned, row stays (queue-lane.ts:96-109) | log+metric POLL_FAILURE | yes | lost silently |
| 6 | poller | claim Redis down | fail-open double publish | metric CLAIM_FAIL_OPEN | n/a | duplicates |
| 7 | poll trigger | invalid backendConfigs payload | 202 ack, dropped (event.controller.ts:152-158) | log | rows stay | chunk skipped one cycle |
| 8 | confirmation_ready, no matching subscription (recordType/source black hole, e.g. source=shopify pick/pack; RGA at collector) | Pub/Sub drops for that subscriber set | none | none | yes | lost for delivery; collector may still hold (not RGA) |
| 9 | confirmation_ready, consumer persistent 4xx/5xx (schema-invalid batch) | immediate redelivery loop up to 7d, then silent expiry (no DLP, no retry_policy on fapi/sftp/shopify) | age>300s monitor only | yes | expired = lost |
| 10 | fapi | no candidate connectors / not deliverable | metric + log, 204 ack (confirmation.service.ts:96-107; controller "always acknowledged (204)") | metric fuse.confirmation.unroutable | yes | lost |
| 11 | fapi | webhook fails 3x | failure published to confirmation_data_failure then ack | replay (pick/pack/woc/fgr/goods/return) | no (recorded) | recorded |
| 12 | fapi | failure publish itself fails | caught, logged (confirmation.service.ts:412-425) | log only | yes | lost |
| 13 | fapi | ack deadline 60s < worst case 3x30s webhook + backoff (~93s) x targets | redelivery during processing, duplicate webhooks | none | n/a | duplicates undetected |
| 14 | sftp | unsupported type / no eligible connectors / origin unresolved / mapping missing | log, return, ack (confirmation-egress.service.ts:140-180) | log only | yes | lost |
| 15 | sftp | write failure | failure published to confirmation_data_failure, ack | replay/collector | no | recorded |
| 16 | sftp | failure publish fails | caught, logged (confirmation-egress.service.ts:295-302) | log | yes | lost |
| 17 | sftp | stock adjustment: no targets, or invalid EDI | return with no made and no failure; code comment: "SNAP re-announces ... stock adjustments have no failure topic" (stock-adjustment.service.ts:~90-140) | log/metric | **yes (explicit)** | lost |
| 18 | shopify | any exception in goods_out or stock adjustment handler | ConfirmationProcessingExceptionFilter replies 202 (ack), log+metric only (confirmation-processing.filter.ts) | log+metric | yes | lost |
| 19 | shopify | unresolvable connector | publishUnroutable -> confirmation_data_failure; publish error swallowed (confirmation.failure-publisher.ts) | replay | partly | lost if publish fails |
| 20 | shopify | batch of up to 1000 confirmations processed sequentially, ack 20s | redelivery mid-flight, partial duplicates | none | n/a | duplicates undetected |
| 21 | collector | schema-invalid/decode error | 204 ack, dropped, metric fuse.collector.record_dropped (all-exceptions.filter.ts:41-92) | metric + monitor "Silent drop ... 204s" | n/a | collector record lost |
| 22 | replay | ValidationError/DecodeError on confirmation-failure | ack and drop (event.controller.ts:262-282); whole bulk message dropped if any one record fails (toStore built before save) | metric fuse.failure.dropped; **monitors on dead metric name** | n/a | failure record lost, no alert |
| 23 | replay | DB error x5 | DLT (no consumer, no monitor for confirmation subs) | none | n/a | failure record lost |
| 24 | snap-adapter made | 202 before work; crash before PATCH; decode failure returns after ack; failure-publish error logged | event.controller.ts:162-215 | metric messagesFailed | yes (re-announce) | moot if made-sub retired |
| 25 | snap-adapter made after early consume | PATCH processed on an already-processed row (SNAP behaviour unknown) -> ClearFailed -> failure published source=snap-adapter | replay subs have no `NOT source=snap-adapter` filter (collector does) | replay stores false failure -> operator redrive re-delivers to customer | n/a | duplicates/false failures |
| 26 | stock_adjustment | any delivery failure | no failure topic; collector sub on `confirmation_data_failure recordType=stock_adjustment` has no publisher; replay does not subscribe | none | yes | lost |

## 6. Message retention vs legitimate backoff
- Every delivery sub uses default 7d retention. Legitimate delays today are short: connectors ack immediately even on failure (fapi 204, sftp ack, shopify 202), so nothing is ever legitimately held in a backoff on confirmation_ready. The 7d window matters only for outages/poison; expiry is silent.
- The deferral feature ("disabled connector = deferred, enabling releases backlog") lives entirely on the OBQ, not in Pub/Sub. Pub/Sub retention (7d) is far shorter than a plausible enable-later window, so it cannot substitute.
- Claim TTL 10 min < subscription retention, so re-announcement cadence is the claim TTL, not Pub/Sub.

## 7. Drift noted
- Fuse MCP `confirmation_ready`/`confirmation_made` descriptions say collector subscribes to "the full set (pick, pack, rga, ...)" and "every type" on made. Live: no RGA ready sub; made subs only woc, fgr, po/goods_in, so/goods_out.
- Vault replay-service known-context/operations (verified 2026-08-24) implies all three replay DLTs are monitored; IaC and live monitors cover only create_data_failure.

## 8. Open questions
1. Does source=shopify pick/pack/woc/fgr/goods_in actually occur in prod (i.e. do pick/pack for shopify-origin orders get stamped source=shopify, and are those OBQ rows perpetually uncleared)? Needs a log query on poller announce vs made.
2. What does SNAP return for `PATCH /v2/snapoutbound/{id}/processed` on an already-processed row (404, 400, 200)? Determines gap 25.
3. Is collector deliberately excluded from RGA confirmation_ready, or is it a miss?
4. Pub/Sub default retry for push subs with no retry_policy (immediate vs slow-start) not verified empirically.
5. fapi/sftp behaviour on schema-invalid confirmation batches (nack vs ack) not fully traced; fapi throws via ingestBulkEvent in the controller (likely 4xx nack).
6. Is 10MB message size reachable given $top=1000 and goods-out line volumes? Not measured.
