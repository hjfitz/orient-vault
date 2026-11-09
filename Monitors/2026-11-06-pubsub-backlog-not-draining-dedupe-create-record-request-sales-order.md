---
tags: [datadog-triage]
date: 2026-11-06
monitor: "[FUSE][Platform] Pub/Sub backlog not draining (any subscription)"
service: dedupe-service
business_id: PURDYFIGG
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793958530149339"
opened_at: "2026-11-06T09:47:38Z"
resolved_at: "2026-11-06T09:48:38Z"
minutes_spent: 1
severity_assessed: P4
flapping: false
outcome: self_resolved
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# Pub/Sub backlog Warn on dedupe_service create_record_request_sales_order: a 2,130-message batch peaked at 174 undelivered for 2 minutes, recovered after 1 minute

## Fired
Monitor 323648858 (`change(avg(last_15m),last_1h):avg:gcp.pubsub.subscription.num_undelivered_messages{project_id:bifrost-prod-global1} by {subscription_id} > 200`, warning 75 / critical 200, P3, Terraform-managed, `getMonitor`) went Warn for `subscription_id:dedupe_service.prod.create_record_request_sales_order.v1.sub` at 09:47:38Z and Recovered at 09:48:38Z (alert events, `listEvents`). The monitor message says "grown by more than 200" because it prints the critical threshold; the Warn line is 75. It fires on the 15-minute average now versus the same average an hour earlier, not on how long messages sit.

## Investigation
- Per-minute `num_undelivered_messages` (max), 4h to 09:51Z: non-zero only at 08:10 (2), 08:22 (67), 09:41 (174), 09:42 (174); 0 at every point 09:43 to 09:47 (latest point, metrics lag about 4 min). `oldest_unacked_message_age` (max) non-zero at 08:22 (1s), 09:41 (1s), 09:42 (1s); never above 1s in 4h. Trend: not growing, each batch is absorbed within 1 to 2 minutes.
- Cadence: `sent_message_count` shows a batch every 5 minutes (09:11 1,920, 09:16 1,948, 09:21 1,996, 09:26 2,020, 09:31 2,098, 09:36 2,083, 09:41 2,130, 09:46 2,164), with `ack_message_count` the same per minute. Throughput matched inflow: ack 2,078 at the 09:41 label, 54 and 48 either side.
- Push responses to the subscription, 3h: 36,956 `ack_204` and 1 `unreachable_cant_contact_dns` (at 09:46). `dead_letter_message_count`, `expired_ack_deadlines_count`, `nack_requests` and `mod_ack_deadline_message_count` returned no series. No dedupe_service subscription had a dead-letter series; the 14 dedupe_service subscriptions all peaked 0 over 3h except this one (69.6 in a 5-min avg). Project-wide `dead_letter_message_count` by subscription returned nothing for 3h.
- Why the monitor tripped: not reproduced. A rolling reconstruction from the 1-min average series gives change(avg15, 1h) = 23.2 at 09:42 to 09:47, below Warn 75, yet the monitor evaluated above 75 at 09:47:38Z and at or below 75 at 09:48:38Z (alert event bodies).
- dedupe-service-prod (Cloud Run), 3h: 40,606 requests all 2xx class (no 4xx/5xx classes returned); instances 5 (max) and flat 09:36 to 09:49; `container.cpu.utilizations.p99` max 0.66 (07:21), 0.19 at 09:41; memory p99 max 0.37; `pending_queue.pending_requests` max 0; `request_latencies.p99` 754 ms at 09:41, 705 ms at 09:46, max 10,464 ms at 09:00 (backlog 0 then); `max_request_concurrencies.p99` 41.95 during the 09:41 batch (the service concurrency setting was not read). Pub/Sub `push_request_latencies.avg` 0.42 to 0.50 s (reported in microseconds) at 09:41 to 09:42.
- Logs: `service:dedupe_service @environment:prod`, 3h: info 88,121, warn 40,380, debug 57, zero error. The only warn pattern in the last hour is "Record dropped" (1 pattern, ~24k), with `reason:duplicate` on all 24,026.
- Inflow: last hour dedupe logged 24,661 "Incoming record received", 24,656 of them sales_order, 24,499 of them PURDYFIGG; "Record dropped" (all reason duplicate) was 24,026, sales_order 24,022, PURDYFIGG 23,955. So about 97% of sales_order records arriving in the last hour were dropped as duplicates. Per 5-minute "Incoming record received" sales_order: 6 at 03:55, 24 at 06:55, 190 at 07:25, 756 at 07:55, 1,816 at 08:55, 1,960 at 09:10, 2,080 at 09:25, 2,178 at 09:40 (every third bin sampled).
- Publisher: shopify-connector logged 2,181 "Record published to topic" for PURDYFIGG between 09:40:05Z and 09:42:09Z, which matches the 09:41 batch.
- Downstream: snap_adapter 3h logs: 5 error ("SNAP request failed", PURDYFIGG sales_order #6662650 / #6662660 / #6662675 / #6662677 / #6662693, 07:25 to 07:26Z, none since), 5 warn. `snap_adapter.prod.create_record_sales_order.v1.sub` peaked at 65 undelivered (08:02) and 28 s oldest unacked (08:27); nothing at 09:41. Other subs peaked at 09:41 to 09:42 with the same batch: tracking-service create_record_request sales_order 171 undelivered, collector create_record_request sales_order 132; all oldest-unacked values 24s or less.
- Held records: `replay-list-failures` (production), sales_order newest is 2026-11-05T17:20:05Z (WILDSMITH, ShipContacts.Phone too long, create.wms_precheck); nothing newer for sales_order. Newest overall is PURDYFIGG goods_out_confirmation at 2026-11-06T09:30:42Z (Shopify fulfilment order CLOSED, confirmation delivery), which is not a record Fuse failed to submit to Snap.
- Flapping: alert events 2026-10-29 to 2026-11-06: this group Warn 10-29 16:40:38Z (recovered 16:41:38Z) and now (recovered after 1 minute); snap_adapter create_record_sales_order fired 10-29 17:06 to 17:19Z. No other firing in the last 20 minutes (events at 09:47:38Z and 09:48:38Z only).
- Slack, #bifrost-notifications (C099WKQTE8G): parent ts 1793958530.149339 (Warn, 09:48:50Z), no replies. Recovery message 1793958585.613749 (09:49:45Z) is separate. Threads since 09:16Z with no reply (`slack_read_thread`): 1793956605.043959 (09:16:45Z, Elevated production error rate, monitor 180072217), 1793956647.214049 (09:17:27Z, tracking-service push 5xx Triggered), 1793957304.415799 (09:28:24Z, tracking-service push 5xx Recovered). 1793958585.613749 shows no reply count in the channel read. 1793956303.668759 (2 replies) and 1793956586.698649 (1 reply) are answered.
- Maintenance / Snap: dedupe_service makes no Snap call and no Snap timeouts were involved, so Step 2b and the maintenance check were not run.

## Not established
- Why the monitor evaluated above 75 at 09:47:38Z when the stored 1-min series gives 23.2 (partial or late data at evaluation time is a lead, not tested).
- Why shopify-connector publishes the same PURDYFIGG sales orders every 5 minutes in growing batches (about 2,200 per batch, 97% duplicates, rising since about 07:10Z); the shopify-connector poll/retrieval logic was not read. Whether it relates to the tracking-service 500 bursts at 09:10Z and 09:15Z (those were mostly create_record_request sales_order) is a lead only.
- Whether the one `unreachable_cant_contact_dns` push at 09:46Z was later acked (per-message state not queryable here); the backlog read 0 at 09:47Z but metrics lag about 4 minutes.
- The dedupe Cloud Run concurrency cap, so headroom against the 42 p99 concurrency seen at 09:41 is unknown.
- Whether the 5 snap_adapter errors at 07:25 to 07:26Z ended with the orders created (no later log or held failure was checked per order).
- State after about 09:49Z (metric lag).

## Outcome
Self-resolved, P4, no action. A roughly 2,100-message batch from shopify-connector raised the backlog to 174 for two one-minute samples with a 1 s oldest-unacked age, then it was 0; dedupe_service returned only 2xx, logged no errors, nothing dead-lettered or held. The monitor is not shown to be mistuned from this evidence (it fired twice in 8 days for this group, one minute each). Worth passing to the shopify-connector owner: PURDYFIGG sales orders are being re-published every 5 minutes and 97% are dropped as duplicates. No ticket filed here.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793958530149339
- Monitor: https://app.datadoghq.com/monitors/323648858
- Related: Monitors/2026-11-06-tracking-service-push-5xx-rate-high-0916.md, Monitors/2026-11-04-pubsub-backlog-snap-adapter-create-record-master-data.md
