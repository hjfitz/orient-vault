---
tags: [datadog-triage]
date: 2026-10-28
monitor: "Pub/Sub ack-deadline headroom eroding (standard subscriptions)"
service: snap-adapter
business_id: DOCKBAY
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793206698605749"
opened_at: "2026-10-28T16:56:39Z"
severity_assessed: P3
flapping: false
outcome: self_resolved
session_id: 7198be0e-f4de-4cae-8e32-ef4ac0c4cdb9
status: resolved
---
# Ack-deadline monitor Warn on snap_adapter create_record_master_data sub (157s)

## Fired
Monitor 323648859 (max oldest_unacked_message_age over 10m, critical >180s) warned on snap_adapter.prod.create_record_master_data.v1.sub, 157.0s (notification value), 16:58Z. Terraform-managed.

## Investigation
- snap_adapter prod master_data logs 16:45Z-now: activity only 16:50:00-16:52:49Z. 132 received, 127 "Entity created in SNAP", 127 x 204. Per-minute rows 71 / 133 / 194 / 189 (16:50-16:52Z).
- 5 slot_timeout (30000ms, transient:true) 16:51:17-25Z, each a 503 at the 30s mark; 5 deliveryAttempt:2 logs at 16:51Z. No other failure mode.
- No master_data logs after 16:52:49Z to ~17:03Z.
- Thread for this alert had no prior replies. Verdict posted in thread with broadcast.

## Not established
Ack deadline, redelivery due to deadline expiry, oldest-unacked/backlog timeline (every metric query timed out or 504ed), whether the 157s message was one of the 5 retried, Snap latency (Fuse MCP 401). The earlier sales_order firing (16:24Z, 118s) is not answered by this evidence.

## Outcome
Self-resolved, P3. Own bulk load meeting slot waits; nothing held. Earlier sales_order record stays unresolved.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793206698605749
- Earlier record: Monitors/2026-10-28-pubsub-ack-deadline-snap-adapter-sales-order.md
