---
tags: [datadog-triage]
date: 2026-10-28
monitor: "Pub/Sub ack-deadline headroom eroding (standard subscriptions)"
service: snap-adapter
business_id: PURDYFIGG
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793208499493909"
opened_at: "2026-10-28T17:26:39Z"
resolved_at: "2026-10-28T17:33:00Z"
severity_assessed: P3
flapping: false
outcome: real_minor
session_id: 7198be0e-f4de-4cae-8e32-ef4ac0c4cdb9
status: resolved
---
# Ack-deadline monitor Warn on snap_adapter create_record_sales_order sub (150s), after PURDYFIGG slot_timeout burst

## Fired
Monitor 323648859 warned on snap_adapter.prod.create_record_sales_order.v1.sub, 150s (notification 17:28Z).

## Investigation
- Ack deadline 300s from snap-adapter iac (`snap_event_ack_deadline_seconds` default, pubsub.tf); live value not read back.
- Metric oldest_unacked_message_age 17:22-17:26: 43, 43, 127, 150, 0. num_undelivered at 17:24 was 92, at 17:25 18.
- Cloud Run 5xx 9/54/10 at 17:21-17:23 (the 73 slot_timeout logs) are nacks, retried after backoff (#6614284: attempt 1 503 at 17:21:01, attempt 2 at 17:21:55). Received logs: attempt 1 = 93+8, attempt 2 = 62, attempt 3 = 11, all done by 17:23:12.
- No "Incoming record received" at 17:23/17:24, then 78 at 17:25, all attempt 1; no error log 17:22:20-17:35. The 150s is a new batch waiting for first delivery, not retries.
- 'Already exists' logs 17:00-17:40: 14 at attempt 2, 3 at attempt 1. The 13 PURDYFIGG ones followed a 503 slot timeout inside the deadline, so not deadline-caused.
- 16:24Z firing (118s): only error in 16:05-16:35 was slot_timeout #6611181 (503 16:15:53, created 16:17:15). 118s consistent with that retry; not message-level confirmed. Earlier record updated.
- Snap latency alerts: ilg001 17:18:39Z, ilg003 17:21:40Z (from channel). Link to the 150s not established. Corrected in thread after first post overstated it.

## Not established
Why 'already exists' on the 13; why delivery paused 17:23-17:25; max handler duration vs 300s (push latency metric sparse, one weighted avg point 154s); expired_ack_deadlines_count returned no series; Snap host for PURDYFIGG (Fuse MCP 401); flapping history.

## Outcome
real_minor, P3. Backlog wait after a slot_timeout burst; nothing held, no deadline expiry observed.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793208499493909
- Earlier: Monitors/2026-10-28-pubsub-ack-deadline-snap-adapter-sales-order.md, ...-master-data.md
