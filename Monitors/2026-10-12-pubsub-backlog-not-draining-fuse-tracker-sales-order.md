---
tags: [datadog-triage]
date: 2026-10-12
monitor: "Pub/Sub backlog not draining (any subscription)"
service: shopify-connector
business_id: PURDYFIGG
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1791827565357449"
opened_at: "2026-10-12T17:51:38Z"
resolved_at: "2026-10-12T17:56:00Z"
minutes_spent: 5
severity_assessed: P4
flapping: true
outcome: monitor_mistuned
escalated_to:
ticket:
session_id: 4fc06c6b-d424-4da8-b551-fb874e9c6e96
status: resolved
---
# "Not draining" fires on deepening PURDYFIGG reap bursts on the fuse-tracker sales_order sub, but every burst drains

## Fired
Monitor 323648858 (`change(avg(last_15m),last_1h)` of `num_undelivered_messages`, warn 75 / alert 200, Terraform-managed) warned on `fuse-tracker.prod.create_record_request.sales_order.v1.sub` at 17:51:38Z. It had cycled warn/alert since 17:24Z.

## Investigation
- Drains: backlog back to 0 within ~2 min of every burst (17:16, 17:21, 17:26, 17:31, 17:36, 17:46Z). Oldest unacked age 2s or less over 17:30-17:51Z, max 7s since 14:54Z. The 17:21Z burst (260), left open by the 17:21Z triage, was 0 by 17:23Z.
- Consumer HTTP health: push requests to `fuse-tracker-api-prod` all ack-class; Cloud Run 0 4xx / 0 5xx over 16:00-17:50Z, p95 0.9-2.9s, 3 instances. Acks equal sends per 5 min (1,035/1,035 at 17:30Z, 947/947 at 17:35Z). Sibling subs on the same topic stayed at 0-1 (dedupe, collector) over 17:35-17:51Z.
- What trips it: aligned 15-min average backlog 0.8 (16:30), 5.1 (16:45), 6.9 (17:00), 103.7 (17:15), 84.9 (17:30), 201 (17:45, partial bucket). Per-burst peak rose 6 (16:41) -> 52 (17:06) -> 260 (17:21) -> 378 -> 535 (17:46Z) while shopify-connector PURDYFIGG `Bulk reap completed` `published` fell 1,117 (16:40) -> 767 (17:45Z); one run every 5 min, 17 runs 16:30-17:50Z.
- Flapping: warn 17:24, alert 17:35 / warn 17:36, alert 17:50 / warn 17:51Z today; warn + recovered at 15:56 and 16:01Z on 10 Oct on this sub; collector sales_order sub 14:55Z on 11 Oct (`source:alert` events, 11 of 17 returned were read).
- Not established: why the per-burst peak rises while the source's published count falls; no tracker logs in Datadog (nothing under `fuse-tracker-api-prod` or any tracker service tag); whether the 17:51Z burst (337) drained (no points after 17:51Z at ~17:55Z).

## Outcome
No stuck consumer found; the alert text "isn't draining" does not match the data, the trend condition is tripping on deeper bursts. Recommended a drain-based condition (oldest unacked age or sustained non-zero backlog) in the `observability` Terraform. Nothing changed, no ticket filed. Amends the 17:21Z record (see Links): its open drain question is closed, and its "burst size" framing is refined.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1791827565357449
- Amended record: 2026-10-12-pubsub-backlog-fuse-tracker-sales-order-purdyfigg-reap.md
