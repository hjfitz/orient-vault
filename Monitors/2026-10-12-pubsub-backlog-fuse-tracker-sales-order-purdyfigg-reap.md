---
tags: [datadog-triage]
date: 2026-10-12
monitor: "Pub/Sub backlog building (any subscription)"
service: shopify-connector
business_id: PURDYFIGG
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1791825738591779"
opened_at: "2026-10-12T17:21:10Z"
resolved_at: "2026-10-12T17:25:00Z"
minutes_spent: 4
severity_assessed: P4
flapping: true
outcome: monitor_mistuned
escalated_to:
ticket:
session_id: 4fc06c6b-d424-4da8-b551-fb874e9c6e96
status: resolved
---
# Backlog warn on fuse-tracker sales_order sub is the PURDYFIGG 5-minute bulk-reap burst, drained by the consumer

## Fired
Monitor 302536090 (warn 200 / crit 1000, `max(last_15m)`) warned on `fuse-tracker.prod.create_record_request.sales_order.v1.sub` with a value of 260 at 17:21Z.

## Investigation
- Backlog on that sub over 11:24-17:21Z peaked at 140 (17:16Z) and 260 (17:21Z) and was 0 between bursts. Oldest unacked age maxed at 7s over the same window (`num_undelivered_messages`, `oldest_unacked_message_age`).
- Acks track sends: 1,052 acked vs 1,053 sent in the 17:16Z minute.
- Source: shopify-connector `Bulk reap completed` for PURDYFIGG logged `published` 1,047 / 1,049 / 1,042 at 17:10, 17:15, 17:20Z. The `bifrost.prod.create_record_request.v1` topic saw 1,022 and 1,018 publishes at 17:11 and 17:15Z. 288 reap runs per day on 9, 10, 11 Oct, ~1,000+ orders each. dedupe-service and collector subs on the same topic show the same bursts.
- Flapping: monitor fired/recovered on this sub on 10 Oct (15:26-16:12Z), 11 Oct (14:56-15:07Z) and now, and on collector's sales_order sub on 11 Oct (14:51-15:06Z). The 2026-09-29 record saw the same pattern.
- Threshold source: `monitors.tf` in `observability` (origin/main), warn 200 / crit 1000.
- Not established: whether the 17:21Z burst fully drained (no metric points after 17:21Z at 17:23Z); fuse-tracker service logs (no tracker-named service returned logs, service tag not identified).

## Update 17:56Z (from the "not draining" monitor 323648858 firing on the same sub)
- The open question is closed: the 17:21Z burst (260) was 0 by 17:23Z, and every burst through 17:46Z drained to 0 within ~2 min, oldest unacked age 2s or less over 17:30-17:51Z. Push deliveries to `fuse-tracker-api-prod` were all ack-class with 0 4xx / 0 5xx over 16:00-17:50Z.
- Refined: the backlog peak is not simply the burst size. Reap runs published ~1,000-1,100 each, but backlog peaks were 6 (16:41Z) rising to 535 (17:46Z) while `published` fell 1,117 -> 767. So the "warns on burst size" framing above is imprecise. Why the peaks deepen is not established.
- Not established still: no tracker logs in Datadog (nothing under `fuse-tracker-api-prod`).
- Full record: 2026-10-12-pubsub-backlog-not-draining-fuse-tracker-sales-order.md

## Outcome
No consumer problem found; the monitor warns on burst peak depth, not on a stuck consumer (corrected 17:56Z, was "burst size"). Recommended a sustained-window or age-based condition in the `observability` Terraform. Nothing changed, no ticket filed.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1791825738591779
- Earlier record: 2026-09-29-pubsub-ack-headroom-backlog-shopify-egress-burst.md
