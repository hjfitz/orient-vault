---
tags: [datadog-triage]
date: 2026-10-20
monitor: "Pub/Sub ack-deadline headroom eroding (standard subscriptions)"
service: shopify-connector
business_id:
channel: bifrost-notifications
thread_url: "https://gfs-engineering.slack.com/archives/C099WKQTE8G/p1792476785450199"
opened_at: "2026-10-20T06:11:39Z"
severity_assessed: P2
flapping: false
outcome: escalated
escalated_to:
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: open
---
# shopify-connector prod poll-trigger subscriptions stuck, instances only emitting startup logs

## Fired
Monitor 323648859 group subscription_id:shopify-connector_prod_bulk_poll_trigger_v1_internal_sub, 198s oldest unacked at 06:11:39Z.

## Investigation
- Metric oldest_unacked_message_age on the sub: 0 to 06:07, then 17/78/138/198s to 06:11; 1 undelivered. push_request_count: deadline_exceeded 3,3,5 and remote_server_5xx 2, no acks.
- shopify-connector_prod_poll_trigger_v1_internal_sub also unacked (73s at 06:10, 06:11).
- Logs (service:shopify-connector @environment:prod): normal activity until 06:02:27Z; from 06:03 only startup lines, 5-10/min from 06:08 to 06:13; no 5-minute poll warnings at 06:05/06:10. Same sha 0fefcb4. Cloud Run request_count 0 for 06:06-06:10; instance_count 1 then 2 at 06:08.
- Other prod shopify-connector subs read 0 unacked age 05:55-06:11.
- Flapping: no earlier firing for this subscription in 7 days (events search on monitor id); earlier firings were snap_adapter (INC-39) and sftp-connector.

## Outcome
Ack posted in thread; escalated to caller as P2 candidate (ongoing, our service, all prod Shopify polling). No deploy event found (change_tracking search, 18h).

Not established: why instances restart or stall (no error or platform logs found), whether Shopify was slow, whether poll gap loses data, recovery.

## Links
- Slack thread: https://gfs-engineering.slack.com/archives/C099WKQTE8G/p1792476785450199
