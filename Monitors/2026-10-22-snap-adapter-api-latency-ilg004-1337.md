---
tags: [datadog-triage]
date: 2026-10-22
monitor: "[FUSE][Snap Adapter] API latency threshold breached"
service: snap-adapter
business_id:
snap_instance: ilg004
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792676302672239"
opened_at: "2026-10-22T13:37:08Z"
resolved_at: "2026-10-22T13:39:32Z"
minutes_spent: 2
severity_assessed: P4
flapping: true
outcome: vendor
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# ilg004 Snap API latency >5s (repeat after DB4 planned update)

## Fired
snap.poll.request.latency.avg on ilg004 averaged 5284ms over 20m (threshold 5000). This is a repeat of the 11:05, 11:37 and 12:09 firings.

## Investigation
- Latency for ilg004, 11:30–13:38Z: binned averages of 2.4–5.5s, rising to 6.2s (peak 12.6s) in the 13:31Z bin.
- Polls on ilg004 since 12:09Z: 675 succeeded, 0 failed (snap.poll.request.success/failure).
- Logs for snap_adapter, snap-polling-service and snap-queue-polling-service, @environment:prod, since 12:09Z: no ilg004 5xx, 404, timeout or circuit-open errors. The only error was a PURDYFIGG PO-U-00002210 data rejection (SKU CP3580 not found).
- Prod replay holds created today: none for KAPPAHL, BABYMORI, SAMMCK, SAIRA or SPORTLUX after 10:03Z. SPORTLUX's newest is still 08:41:43Z (58 total).

## Outcome
P4 vendor. ilg004 is still slow after Snap's DB4 update, with no errors and no holds. No action taken. If it persists tomorrow, raise it with Snap.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792676302672239
