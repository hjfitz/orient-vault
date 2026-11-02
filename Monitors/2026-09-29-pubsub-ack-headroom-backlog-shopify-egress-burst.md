---
tags: [datadog-triage]
date: 2026-09-29
monitor: "Pub/Sub ack-deadline headroom + backlog + Shopify egress burst"
service: snap-adapter
business_id: DOCKBAY
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790697437104329"
opened_at: "2026-09-29T15:55:01Z"
resolved_at: "2026-09-29T15:59:49Z"
minutes_spent: 5
severity_assessed: P4
flapping: true
outcome: real_minor
escalated_to:
ticket:
session_id: 1d69c80f-4740-4a73-9c91-307d597bd013
status: resolved
---
# Burst of monitors at ~15:55Z traced to DOCKBAY go-live load, PURDYFIGG reap batches and an unmuted stuck Shopify confirmation

## Fired
Five monitors in about two minutes: Pub/Sub ack-headroom on snap_adapter `create_record_master_data` (54s) and `confirmation_made.so` (32s), collector `create_record_request_sales_order` backlog (238 > 200), Shopify egress delivery failing, and fapi p95 latency.

## Investigation
- Confirmed: fapi accepted 204 DOCKBAY master-data records at ~15:51Z. The snap_adapter master_data unacked age peaked at 54s for two minutes, then returned to 0.
- Confirmed: collector sales_order backlog spikes every ~5 min, one minute after each PURDYFIGG bulk-reap step. The 238 datapoint was the latest at the time and had not been seen to drain.
- Confirmed: 10 `Confirmation dispatch failed` errors, all PURDYFIGG goods_out_confirmation, one every ~12 min from 14:08Z. This is the stuck confirmation flagged at 12:43 BST. The monitor mute expired 15:49Z and it re-fired 15:56Z.
- Hypothesis: snap_adapter briefly saturated by the master-data batch; 238 is the same PURDYFIGG pattern at larger size. Shopify failure reason and the stuck order were not identified (error line carries no message detail).

## Outcome
No outage. Ack-headroom and backlog monitors trip on short batches at low volume and need a sustained-duration condition (Terraform, `observability` repo; not changed). Owed: identify the stuck PURDYFIGG outbound-queue item; tell DOCKBAY about two Snap-rejected records.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790697437104329
