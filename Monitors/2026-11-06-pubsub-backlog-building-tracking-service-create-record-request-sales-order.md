---
tags: [datadog-triage]
date: 2026-11-06
monitor: "[FUSE][Platform] Pub/Sub backlog building (any subscription)"
service: tracking-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793959464709189"
opened_at: "2026-11-06T10:03:10Z"
resolved_at: "2026-11-06T10:07:26Z"
minutes_spent: 6
severity_assessed: P4
flapping: false
outcome: self_resolved
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# Pub/Sub backlog Warn on tracking-service create_record_request sales_order: a ~2,400-request batch peaked at 214 undelivered for one 1-minute sample, back to 0 the next

## Fired
Monitor 302536090 (`max(last_15m):max:gcp.pubsub.subscription.num_undelivered_messages{project_id:bifrost-prod-global1} by {subscription_id} > 1000`, critical 1000, warning 200, P2, Terraform-managed, `getMonitor`) went Warn at 10:03:10Z for `subscription_id:tracking-service.prod.create_record_request.sales_order.v1.sub` (value 214) and, at the same second, for `dedupe_service.prod.create_record_request_sales_order.v1.sub` (value 385) (`listEvents`; Slack posts 10:04:24Z and 10:04:22Z).

## Investigation
- Why now: per-minute max of undelivered on the tracking sub, 09:30 to 10:03Z: 171 (09:41), 32 (09:51), 180 (09:56), 214 (10:01), 0 at 10:02, no point for 10:03 (metrics lag about 4 min). 214 is the first sample above the 200 Warn line; the 15m window keeps it in Warn until about 10:16Z. Daily peaks 31 Oct to 6 Nov: 5, 100, 51, 39, 67, 161, 214 (rollup max 86400), so 214 is the 7-day high and the peak has risen three days running. Oldest-unacked max over 24h is 24 s; it was 0 s in every per-minute sample 09:30 to 10:03Z.
- Throughput: `sent_message_count` and `ack_message_count` for the sub track each other per minute (e.g. 2,224 sent and 2,224 acked in the bin labelled 09:57). Pushes: only `ack_204` returned for 09:31 to 10:00Z (2,026 down to 3); a 24h query for non-204 pushes returned only response codes 500 and 429 (hourly buckets whose timestamps did not line up, so not used for timing; the 500s match the 09:11 and 09:16 Cloud Run 5xx below). No `expired_ack_deadlines_count`, `nack_requests` or `dead_letter_message_count` series.
- Batch size growing: tracking-service-api-prod 2xx in the batch minute, every 5 min: 2,030 (09:06), 2,026, 2,077, 2,114, 2,171, 2,237, 2,219, 2,307, 2,262, 2,336, 2,346, 2,418 (10:01) (`gcp.run.request_count` by class).
- tracking-service errors: log patterns for `service:tracking-service* @environment:prod status:(error OR warn)` since 09:00Z gave one pattern, `store failed; nacking for redelivery`, 536 lines, first 09:10:13Z, last 09:16:10Z. A `"store failed"` search from 09:18Z to 10:06Z returned 0 lines. `fuse.tracking.store.errors` had no non-zero point after 09:17Z. Cloud Run 5xx: 225 (09:11 bin), 308 (09:16), 3 (09:17), 0 in every bin 09:18 to 10:03Z. So this firing does not coincide with a new store failed burst.
- Cloud Run tracking-service-api-prod, 09:04 to 10:03Z: instances 2 to 3; CPU p99 max 0.21 (0.16 at 10:01); memory p99 max 0.35; `max_request_concurrencies.p99` max 59.95 (09:07 to 09:22) and 31.94 at 10:01; `pending_queue.pending_requests` max 8 at 10:01 (1 at 09:51; 0 elsewhere), the same minutes as the 214 and 32 peaks. p99 request latency read 8,679 ms repeated across 09:55 to 10:02 bins (the same value in several bins, treated as unreliable). Concurrency setting not read (Terraform for tracking-service not found in the local checkout).
- Dead-letter depth: `num_undelivered_messages` max 0 over 3h on all 20 `tracking-service.prod.*.dlt.sub` subscriptions, including `create_record_request.sales_order.v1.dlt.sub`.
- Held: `replay-list-failures` (production, newest first): newest 10 are all PURDYFIGG goods_out_confirmation at 09:30:41 to 09:30:42Z (Shopify fulfilment order CLOSED, confirmation.delivery_shopify). Nothing newer, no create-side record held, so no record Fuse could not submit to Snap.
- Sibling group: dedupe_service create_record_request_sales_order sub: 385 undelivered at 10:01 and 10:02, oldest unacked 0 s, no point at 10:03; dedupe-service-prod 2xx only (2,313 in the 10:01 bin), 5 instances flat 09:50 to 10:04, p99 latency 7,862 ms at 09:55 to 09:56 and 1,876 ms at 10:01. A dedupe-service prod deploy (commit 1eeac6f, 09:57:46Z) and an api-gateway deploy (09:58:11Z) were announced in the channel before the peaks.
- Flapping: no earlier firing found in the events API (`listEvents` capped at the latest 1,000 events, so 24h/8d history is not conclusive); metric history shows no day above 200 on this sub in the prior 6 days.
- Slack: #bifrost-notifications (C099WKQTE8G) parent 1793959464.709189 (tracking, 10:04:24Z) and 1793959462.757479 (dedupe, 10:04:22Z) have no replies (`slack_read_thread`). Since 09:48Z, 1793958530.149339 (dedupe not-draining Warn) has one reply; 1793958585.613749 is a Recovered post and ignored.
- Not Snap related; maintenance check and Step 2b not applicable.

## Not established
- Why the 10:01 batch peaked higher than earlier ones (214 vs 171 to 180); the minutes where Cloud Run pending requests were 1 and 8 line up with the peaks but cause is untested.
- Whether the 09:57 dedupe-service deploy influenced the dedupe peak of 385 (instances were flat at 5; no per-request test run).
- Cloud Run concurrency cap for tracking-service-api-prod, so headroom against the 59.95 p99 concurrency seen 09:07 to 09:22Z is unknown.
- Pub/Sub state after about 10:03Z (metric lag about 4 minutes).
- Why shopify-connector keeps republishing the same PURDYFIGG orders in growing 5-minute batches (see the dedupe record); not read here.
- Alert history older than the latest 1,000 events (events API cap).

## Outcome
Self-resolved, P4, no action. A 5-minute batch of about 2,400 requests pushed the tracking sub to 214 undelivered for one 1-minute sample, then 0; every push in the window was 204, nothing dead-lettered or held, no new store failed errors since 09:16:10Z. Not mistuned from this evidence, but the 7-day trend (daily peak 67, 161, 214) follows the growing batch size and is worth the shopify-connector / tracking-service owners' eye. No ticket filed here.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793959464709189
- Monitor: https://app.datadoghq.com/monitors/302536090
- Related: Monitors/2026-11-06-pubsub-backlog-not-draining-dedupe-create-record-request-sales-order.md, Monitors/2026-11-06-tracking-service-push-5xx-rate-high-0916.md, Monitors/2026-11-06-platform-elevated-prod-error-rate-tracking-service-store-0910.md
