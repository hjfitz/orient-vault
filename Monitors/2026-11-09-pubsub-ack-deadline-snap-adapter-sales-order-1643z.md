---
tags: [datadog-triage]
date: 2026-11-09
monitor: "[FUSE][Platform] Pub/Sub ack-deadline headroom eroding (standard subscriptions)"
service: snap-adapter
business_id: PURDYFIGG
snap_instance: ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794242691825099"
opened_at: "2026-11-09T16:43:39Z"
severity_assessed: P3
flapping: true
outcome: real_minor
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# snap_adapter create_record_sales_order sub: oldest unacked 199 s (first Alert today) after the 16:35Z PURDYFIGG wave

## Fired
Alert (above the 180 s critical line) on `max(last_10m)` of oldest_unacked_message_age for `snap_adapter.prod.create_record_sales_order.v1.sub`, event 16:43:39Z, value 199 s. Datadog events for this group today: Warn 08:23:39, Recovered 08:32:39, Warn 15:23:39, Recovered 15:33:39, Warn 16:13:39, Recovered 16:20:39, Warn 16:33:39, Alert 16:43:39, Recovered 16:50:39 (Slack post read at 16:51:50Z), Warn 17:08:39 (112 s). The 17:08 Warn is a separate episode with its own Slack post (ts 1794244205.553099), which had no thread replies when read at about 17:12Z.

## Investigation
- Per-minute metric stamps (oldest unacked s / undelivered): 16:36 21/67, 16:37 81/111, 16:38 141/91, 16:39 152/53, 16:40 199/36, then 0 at 16:41-16:45, 13/14 at 16:46, 14/14 at 16:47, 0 at 16:48-16:51. Stamps run behind the logs by a couple of minutes.
- snap_adapter logs 16:30-16:38Z, sales_order received by deliveryAttempt: 164 at 1, 104 at 2, 14 at 3, none above 3. Slot_timeout failures 16:30-16:37Z: 15+2+1 (16:30-31), 30 (16:35), 70 (16:36) = 118, all `transient:true`, `exhausted:false`. Cloud Run 5xx for the same minutes: 15, 3, 33, 67 (118). Instance count 3 (2 at 16:32).
- Window 16:38-16:50Z: 1 error log (a non-transient `snap_api_error`, the DOCKBAY purchase order PO573058 held in replay-service, created 16:38:45Z), 0 slot_timeouts, 0 Cloud Run 5xx or 429, 105 received (all attempt 1), instance count 3, breaker state 0 (closed) all minutes to 17:12.
- Failing orders 16:25-17:16Z: 104 distinct (102 PURDYFIGG, 2 STUBBLE). Snap ilg005 `shipments` read by CustomerRef: 104 found, 0 missing, 0 duplicates, all Status 00, PURDYFIGG DateCreated 16:30:53-16:38:35, STUBBLE 16:38:11-13. The 14 messages that reached attempt 3 are all PURDYFIGG and all in Snap. For #6700369 the log trail is received 16:35:06 / slot_timeout 16:35:48 / received 16:36:16 / slot_timeout 16:36:46 / received 16:37:17 / "Entity already exists in SNAP" 16:37:38 / 204; Snap shows it created 16:35:13.
- 16:40-17:15Z: 549 received = 549 "Entity created in SNAP", 0 error/warn. The 17:01 wave (111 received at 17:01, 25 at 17:02) saw 6 Cloud Run 429s in the 17:03 minute and 7 attempt-2 deliveries at 17:01:48-17:03:00, no app errors. Oldest-unacked stamp 112 s at 17:05 (the 17:08:39 Warn).
- Retry policy (live gcloud describe of the subscription and Cloud Run service revision snap-adapter-prod-00100-qk9, running version 8b2e5af, which is repo master head): ackDeadlineSeconds 300, maxDeliveryAttempts 35, retry backoff 10 s-600 s, SNAP_MAX_TRANSIENT_DELIVERY_ATTEMPTS 30, slot acquire timeout 30 s, 5 slots per instance, max 3 instances x 30 concurrency. Code: `apps/snap-adapter/src/http/controllers/event.controller.ts` sets `exhausted` when a transient failure reaches deliveryAttempt >= the limit and then publishes create_data_failure; `iac/projects/snap-adapter/variables.tf` default 30 ("about four hours of runway"); `iac/projects/snap-adapter/pubsub.tf` dead-letters at limit + 5. Worst case today is attempt 3, so 27 deliveries from the self-report.
- Snap ilg005 request latency (avg of snap.request.latency.avg, per minute): 8.5 s at 16:30, 9.6 s at 16:36 (max 14.6 s), 4.9 s 16:38, 4.2 s 16:40, 3.1-3.2 s 16:44-45, 1.5 s 16:50, 3.7-4.0 s 17:01-17:03, 1.5 s 17:10, 0.78 s 17:15. Slot queue depth peaked 24 (16:37), 22.5 (17:02). Timed read-only GETs of snaplookups/RECSTATUS at 17:14:54-17:15:27Z: 200 in 4.14, 0.08, 0.06, 0.07, 4.13, 0.09 s.
- Slot_timeout failures per day (7 days): 3 Nov 4 (PURDYFIGG), 6 Nov 6 (DOCKBAY), 8 Nov 74 (PURDYFIGG), 9 Nov 125 (PURDYFIGG 122, STUBBLE 2, ESCENTRIC 1). 5-minute counts today 3 (15:20), 4 (16:05), 18 (16:30), 100 (16:35), then 0 for 16:40-17:15 despite waves of 118-125 at 16:50-16:55 and 111 at 17:01.
- replay-service production, 2026-11-09, sales_order/purchase_order: 6 held, none PURDYFIGG or STUBBLE, none a slot_timeout (data rejections: ESCENTRIC 15337 and 15335, DOCKBAY UK-914263 and PO573058, AYMSTUDIO PO-091126, SAIRA #37929).
- Maintenance/: no record covers 2026-11-09 (latest window 2026-11-05).

## Outcome
Real but minor, P3. The 199 s peak is the 16:35 PURDYFIGG wave draining: first deliveries 16:35:06-16:35:14Z, last of the 104 orders created in Snap at 16:38:35Z. Everything created, nothing held, deepest delivery attempt 3 of a 30 attempt self-report budget. Not worsening since 16:38Z (0 slot_timeouts, 0 5xx), but ilg005 is still intermittently slow (two of six probes about 4.1 s) and the daily slot_timeout count has risen from 4-6 to 74 (8 Nov) and 125 (9 Nov). A ticket on the adapter's slot cap and burst intake, and on ilg005 latency with ILG, is warranted if the 5-minute waves keep coming.

Not established: which message was the 199 s one; how #6700369 got its Snap record at 16:35:13Z before its first delivery timed out at 16:35:48Z; which other businesses share ilg005 (lookup-snap-instance returned no business list; PURDYFIGG and STUBBLE confirmed via get-snap-connection); why ilg005 is slow and whether our slot cap or Snap holds the slots; per-message outcome of the 7 attempt-2 deliveries at 17:01-17:03 (matched by count only); Snap vendor mail and the #bifrost-general pin; 95 PURDYFIGG goods_out_confirmation failures held at about 16:50Z ("Fulfillment order ... is CLOSED in Shopify") are confirmation-side and were not investigated.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794242691825099
- Later Warn post (no thread yet): https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794244205553099
