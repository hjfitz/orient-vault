---
tags: [datadog-triage]
date: 2026-10-21
monitor: "[FUSE][Platform] Pub/Sub ack-deadline headroom eroding (standard subscriptions)"
service: snap-adapter
business_id: PURDYFIGG
snap_instance: ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792580868185169"
opened_at: "2026-10-21T11:06:39Z"
resolved_at: "2026-10-21T11:24:32Z"
minutes_spent: 18
severity_assessed: P3
flapping: true
outcome: vendor
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# snap_adapter sales_order sub unacked up to 290s while ilg005 answered creates slowly

## Fired
Monitor 323648859, group snap_adapter.prod.create_record_sales_order.v1.sub. Oldest unacked was 290s.

## Investigation
- Oldest-unacked went 290s, then 14s (11:07Z), then 256s (about 11:16Z). Undelivered peaked at 17 at 11:09Z.
- Each wave was PURDYFIGG creates hitting the 120s timeout twice, then a 503, then a redelivery acked as already-exists. Orders queued behind them got slot_timeout 503s.
- No dead letters on any prod subscription since 10:30Z. Deliveries peaked at 6 of 10.

## Outcome
Vendor-driven (Snap ilg005), so the consumer wasn't stuck. It will flap until Snap answers creates normally.

## Links
- Slack reply: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792581872858829
