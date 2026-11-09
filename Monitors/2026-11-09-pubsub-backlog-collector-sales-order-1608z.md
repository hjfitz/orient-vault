---
tags: [datadog-triage]
date: 2026-11-09
monitor: "[FUSE][Platform] Pub/Sub backlog building (any subscription)"
service: collector
business_id: PURDYFIGG
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794240569068789"
opened_at: "2026-11-09T16:08:10Z"
severity_assessed: P4
flapping: true
outcome: self_resolved
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# Backlog Warn on collector sales-order subscription: an 833-record PURDYFIGG burst peaked at 246 and drained within a minute

## Fired
Monitor 302536090 (priority 2, `max(last_15m)`, Warn 200, Critical 1,000) went Warn on `collector.prod.create_record_request_sales_order.v1.sub` at 16:08:10Z with value 246. Datadog's post is C099WKQTE8G 1794240569.068789 (16:09:29Z, no replies when read). Triggered in the same minutes as the snap_adapter slot_timeout alert thread (1794240464.998109), which carries a Bifrost Support Bot reply.

## Investigation
- Subscription: Fuse MCP lookup-topic create_record_request lists collector as a subscriber (recordType filtered). collector_service logs `POST /events/v1/record/request/sales_order - 201` and `Record stored` for the burst, so collector is the consumer.
- Backlog (max per minute, `get_datadog_metric`, read about 16:12Z): num_undelivered_messages 0 for 16:00-16:05, 246 at 16:06, 0 at 16:07; no point yet for 16:08 or later (metric lag). oldest_unacked_message_age 1 s at 16:06, 0 before and after. Last 3h: peaks 12, 55, 9, 24, 9, 121 (15:51), 246 (16:06), otherwise 0. ack_message_count 417 at 16:05 and 436 at 16:06.
- Source: shopify-connector logged "Record published to topic" 840 times for PURDYFIGG between 16:04:10Z and 16:06:09Z. collector stored 833 PURDYFIGG sales orders between 16:05:06.680Z and 16:05:12.432Z (one correlationId 09b835ac-4b7d-4c71-bb37-7af91fc2440b). dedupe_service logged 833 "Incoming record received" for that correlationId, "Record dropped" (warn) 717 times and "Record published to topic" 116 times (16:05:10-16:05:15Z). The thread 1794240464.998109 reports snap_adapter took in 90 then 33 records (123) at 16:05-16:06Z. 116 vs 123 not reconciled to the record.
- Cadence: collector_service log lines per minute spike at every 5-minute mark since 14:00Z (about 900-1,040 lines at 14:00-15:30Z; 1,657 at 15:35, 1,902 at 15:40, 2,187 at 15:45, 2,109 at 15:50, 1,965 at 15:55, 2,604 at 16:00, 2,562 at 16:05, 3,098 at 16:10). Log lines, not records. The backlog effect of the 16:10 burst was not yet visible in the metric. dedupe_service and tracking-service subscriptions read 0 undelivered through 16:08 (dedupe) and 15:31-16:07 (tracking); snap_adapter sub peaked at 36 at 16:07.
- Errors: collector_service has no status error or warn logs in the last 6h.
- Flapping: 71 events of this monitor in 7 days; collector Warns at 6 Nov 10:28, 20:53, 22:53; 7 Nov 12:18, 15:38, 16:33, 16:58, 17:28, 18:43; 9 Nov 16:08 (10 in 7 days). Earlier today's Warn was on the snap_adapter subscription (08:23Z). Same record-type subscriptions (dedupe, tracking) fired together on 6-7 Nov.
- Held (replay-service, production): no PURDYFIGG sales_order failure created 9 Nov. Newest unreplayed held items are unrelated: ESCENTRIC sales_order 15337 (ShipContacts.Phone over 20 characters, 15:03Z), AYMSTUDIO purchase_order PO-091126 (14:15Z), SAIRA sales_order #37929 (13:40Z), and PURDYFIGG goods_out_confirmation Shopify CLOSED fulfilment orders (13:25Z).
- Maintenance/: no record with a window covering 9 Nov (latest window_start 2026-11-05T10:00Z). #bifrost-general pin and ILG mail not checked. Step 2b (Snap host probes) not run: this alert is the collector subscription, not a Snap call failure.

## Outcome
self_resolved, P4. An 833-record PURDYFIGG sales-order burst arrived in about 6 seconds; collector stored all 833 and the backlog peaked at 246 for one minute with a 1 s oldest-unacked age, back to 0 the next minute. Nothing held for this flow. Collector has now Warned 10 times in 7 days, so the 200 threshold on instantaneous count is noisy for this subscription; whether to retune is for the team.

Not established: backlog and age for 16:08Z onward (including the 16:10 burst); whether the 16:10 burst peaks above 246; what triggers the 5-minute bursts and the rise in their size since 15:35Z; whether the 116 published by dedupe are the 123 snap_adapter received; when this monitor recovers; #bifrost-general pin and ILG mail.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794240569068789
- Monitor: https://app.datadoghq.com/monitors/302536090
- Related: [[2026-11-09-pubsub-backlog-snap-adapter-sales-order-0823z]]
