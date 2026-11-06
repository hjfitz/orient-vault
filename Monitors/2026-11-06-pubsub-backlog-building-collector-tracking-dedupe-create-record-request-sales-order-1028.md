---
tags: [datadog-triage]
date: 2026-11-06
monitor: "[FUSE][Platform] Pub/Sub backlog building (any subscription)"
service: collector
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793960962947539"
opened_at: "2026-11-06T10:28:10Z"
severity_assessed: P4
flapping: false
outcome: self_resolved
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# Pub/Sub backlog building: collector, tracking-service and dedupe create_record_request sales_order subs all Warn at 10:28Z

## Fired
Monitor 302536090 (`max(last_15m)` of `gcp.pubsub.subscription.num_undelivered_messages` by `subscription_id`, warn 200, critical 1000) went Warn for three groups at 10:28:10Z. Alert thread parent ts in C099WKQTE8G: collector `1793960962.947539` (value 301), tracking-service `1793960964.882129` (301), dedupe `1793960966.783909` (329). No other group of this monitor went Warn/Alert between 10:20Z and 10:32Z (alert events for monitor 302536090 over the last 24h: 5 Warn and 2 Recovered, all on these three subscriptions; the earlier Warns were the tracking-service and dedupe groups at 10:03:10Z, Recovered 10:16 and 10:17Z). The sibling monitors 323648858 (not draining, 10:31:45-49Z, all three subs) and 302511458 (dedupe backlog, 10:29:47Z) also posted; they are separate monitors and not triaged here.

## Investigation
Pub/Sub metric lag is about 4 minutes: at 10:32:38Z the newest samples were 10:28Z for oldest-unacked and 10:27Z for undelivered.

Per group (undelivered peak, oldest-unacked peak, push responses, dead-letter, 09:30Z to 10:28Z):

| Group | Undelivered peak | Oldest-unacked peak | Push responses | Dead-letter |
|---|---|---|---|---|
| collector | 301 at 10:27 (190 at 10:02, 132 at 09:42) | 1s at 10:17; 0 at 10:28 | 27,492 ack_201, nothing else | no `dead_letter_message_count` series; no collector dlt subscription series found |
| tracking-service | 301 at 10:27 (214 at 10:01) | 0 at every sample | 27,492 ack_204, nothing else | 20 tracking `.dlt.sub` subs all max 0 over 3h; no `dead_letter_message_count` series |
| dedupe | 329 at 10:27 (385 at 10:01 and 10:02) | 6s at 10:27; 0 at 10:28 | 27,492 ack_204 plus 1 `unreachable_cant_contact_dns` at 09:46Z (outside both firings) | no `dead_letter_message_count` series; no dedupe dlt subscription series found |

Drain: undelivered read 0 in every minute 10:20-10:26 on all three and 301/301/329 at 10:27 (the 10:28 undelivered sample was not yet published). Oldest-unacked read 0 at 10:28 on all three, so the backlog had been consumed; not directly confirmed through the undelivered series.

Cause shared by all three: every sample above 100 on these subs lands in the minute of or the minute after a 5-minute batch minute (tracking above 100 at 09:41, 09:56, 10:01, 10:27 against batches at 09:41, 09:56, 10:01, 10:26; dedupe and collector the same pattern). Batch size per `sent_message_count` (the batch minute or minutes): collector 1760 at 09:01, 2162 at 10:01, 2286 at 10:16, 2297 at 10:21, 2284 at 10:26; tracking 2224 at 10:01, 2295 at 10:16, 2369 at 10:21, 2325 at 10:26; dedupe 2288 at 10:01, 2357 at 10:16, 2394 at 10:21, 2361 at 10:26. First batches above 500 per minute from 07:46Z (571-593); growth has flattened over the last three batches (10:16-10:26), within about 2%.

Batch content: dedupe-service logs 10:25-10:32Z: 4,831 "Incoming record received", 4,751 "Record dropped" (4,720 PURDYFIGG, 19 ESCENTRIC, 8 ESCENTRICPL, 4 SAIRA), 80 "Record published to topic". About 98% of received records are dropped.

Consumer errors: collector_service logs 09:40Z to 10:32Z had 0 error/warn lines (51,490 info lines since 10:00Z; "Incoming record received" 4,930 vs "Record stored" 4,831 for 10:25-10:32Z). dedupe_service warn lines are all "Record dropped" (16,370 warn since 10:00Z). tracking-service: 0 error/warn lines, Cloud Run 5xx series 0 over 09:55-10:28Z. The `fuse.tracking.store.errors` metric returned no series (name or tag not confirmed, so not relied on).

Cloud Run (09:55-10:28Z):

| Service | Instances | CPU p99 max | Memory p99 max | Max-concurrency p99 | Request latency p99 | Pending-queue max |
|---|---|---|---|---|---|---|
| collector-prod | 8-9 | 0.27 | 0.34 | 84.95 at 10:12, 84.85 at 10:27 | up to 1,417 ms | 0 |
| dedupe-service-prod | 5 | 0.53 at 09:58 | 0.38 | 41.98 at 10:27 | 7,862 ms at 10:26 | 32 at 10:01, 0 at 10:25-10:27 |
| tracking-service-api-prod | 2-3 | 0.24 | 0.31 | 39.94 | 7,173 ms at 10:26-10:27 | 8 at 10:01, 0 at 10:25-10:27 |

Collector Cloud Run request counts: 17,137 2xx and 6 4xx (09:43, 10:17, 10:20 x2, 10:21, 10:24, 10:27); no log line carried an `@http.status_code` 4xx, so their source is not established.

7-day daily max undelivered: collector 5, 57, 71, 82, 7, 171, 301 (Oct 31 to Nov 6); tracking 5, 100, 51, 39, 67, 161, 301; dedupe 5, 81, 15, 16, 13, 41, 385. Today's values are the 7-day highs on all three.

Held records: `replay-list-failures` (production, sales_order) newest entry is 2026-11-05T17:20Z (snap-adapter, WILDSMITH); nothing newer for sales_order. Newest overall is 2026-11-06T09:30:42Z, PURDYFIGG goods_out_confirmation, Shopify fulfilment order CLOSED (not a Snap submission). Nothing is held from this firing's window.

Alert threads for this monitor since 10:04Z: the 10:04:22Z dedupe thread (`1793959462.757479`) and 10:04:24Z tracking thread (`1793959464.709189`) each have one Bifrost Support Bot reply. The three 10:29Z threads had no replies at 10:32Z (collector `1793960962.947539`, tracking `1793960964.882129`, dedupe `1793960966.783909`).

## Outcome
Self-resolved, P4. A 5-minute batch of about 2,300 messages per subscription (about 98% of what dedupe receives is dropped, almost all PURDYFIGG; the publisher was not checked in this triage) briefly lifts each of the three subscriptions above the 200 Warn line at a 1-minute sample; consumers ack everything, nothing errors, nothing is dead-lettered or held. Recurring (second Warn cycle in 25 minutes) and peaks are rising; by its `max(last_15m)` definition each group holds Warn for 15 minutes after its last sample above 200.

Not established: why shopify-connector keeps republishing the same PURDYFIGG orders in growing batches; why some batches (10:11-10:21) did not cross 100 at the 1-minute sample while others did; the Cloud Run concurrency cap for collector (p99 concurrency 84.95, no pending requests); the source of the 6 collector 4xx responses; whether the 10:31Z and later batches drain (metrics lag about 4 minutes); undelivered at 10:28Z.

## Links
- Slack threads: collector https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793960962947539, tracking-service https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793960964882129, dedupe https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793960966783909
- Monitor: https://app.datadoghq.com/monitors/302536090
- Earlier records: Monitors/2026-11-06-pubsub-backlog-building-tracking-service-create-record-request-sales-order.md, Monitors/2026-11-06-pubsub-backlog-not-draining-dedupe-create-record-request-sales-order.md
