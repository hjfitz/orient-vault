---
tags: [datadog-triage]
date: 2026-09-22
monitor: "[FUSE][Platform] Pub/Sub ack-deadline headroom eroding (standard subscriptions)"
service: platform (snap-adapter / shopify-connector / sftp-connector / collector via create_acknowledge)
business_id:
channel: bifrost-notifications
thread_url: ""
opened_at: "2026-09-21T15:19:44Z"
severity_assessed: P4
flapping: true
outcome: monitor_mistuned
ticket:
session_id: 4dbd2b8d-0a68-4ad4-a7be-3178039a189b
status: resolved
resolved_at: "2026-09-22T08:26:52Z"
minutes_spent: 22
---
# Pub/Sub ack-deadline headroom monitor flapping on normal jitter

## Fired
Harry noticed repeated Slack noise about a "pubsub backlog for sales order acks" — not a specific
thread, just a recurring impression from #bifrost-notifications. Traced to monitor id `323648859`,
which Harry himself created 2026-09-21, alerting when
`max(last_10m):max:gcp.pubsub.subscription.oldest_unacked_message_age{...} by {subscription_id} > 15`
(seconds), scoped to all standard prod subscriptions except a deny-list of six known long-ack-deadline
(600s) subs.

## Investigation
- Confirmed the topic in question is `create_acknowledge` (publisher: snap-adapter; subscribers:
  shopify-connector, sftp-connector, collector) via Fuse MCP `lookup-topic`.
- Event history shows the monitor has fired and auto-resolved 16 times in <24h across three
  subscriptions (`sftp-connector.prod.create_acknowledge.v1.sub` plus two adjacent ones), each at
  ages of 11–30s, self-clearing within ~8 minutes each time — consistent with normal processing
  jitter, not a stuck consumer.
- Checked the two volume-based backlog monitors (`num_undelivered_messages`) that actually track
  queue depth: both status OK, never triggered.
- No error logs on any of the three subscriptions in the last 15 minutes at time of check.
- No dedicated Slack thread exists for this — the "backlog" impression came from repeated raw
  monitor-fire notifications in #bifrost-notifications, not one discussed thread.

## Outcome
No real backlog. The monitor's 15s threshold left almost no headroom above the subscriptions'
~20s real ack deadline for ordinary jitter. Fixed at the source: raised `critical`/`warning` to
60s/30s in the `observability` repo's Terraform (`pub_sub_ack_deadline_headroom_eroding` in
`monitors.tf`) rather than patching the live monitor directly, since it's `managed-by:terraform`
and a direct API edit would just drift on the next apply. Plan showed exactly the one resource
changing (0 to add, 1 to change, 0 to destroy); PR gfs-bifrost/observability#45 merged, CI applied
it behind the `terraform-prod` gate, and the live monitor was confirmed back to `OK` with the new
60/30 thresholds post-apply.

## Links
- Slack thread: none — raised directly by Harry, not from a monitor-alert thread
- Monitor: id 323648859
- PR: https://github.com/gfs-bifrost/observability/pull/45
