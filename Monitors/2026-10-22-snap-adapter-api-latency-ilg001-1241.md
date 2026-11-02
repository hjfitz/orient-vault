---
tags: [datadog-triage]
date: 2026-10-22
monitor: "[FUSE][Snap Adapter] API latency threshold breached"
service: snap-adapter
business_id:
snap_instance: ilg001
channel: bifrost-notifications
thread_url: "https://gfs-engineering.slack.com/archives/C099WKQTE8G/p1792672947841919"
opened_at: "2026-10-22T12:41:08Z"
resolved_at: "2026-10-22T12:43:25Z"
minutes_spent: 2
severity_assessed: P4
flapping: true
outcome: vendor
escalated_to:
ticket:
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# ilg001 Snap poll latency Alert (repeat of 11:47Z)

## Fired
Monitor 179927768 Alert for snap_host ilg001liveapi: avg snap.poll.request.latency.avg 5767ms over 20m (> 5000ms). 2 further firings folded in.

## Investigation
- Latency 10-min avgs since 11:30Z: 3.6–7.6s (same band as earlier warns).
- snap.poll.request.success{ilg001} since 11:47Z = 436; failure = none.
- Prod status:error logs (snap_adapter / snap-polling-service / snap-queue-polling-service) since 11:47Z: 0. ilg001 timeout/5xx/404/circuit logs: 0.
- Prod replay holds created 2026-10-22: DOCKBAY 0, MANUCURIST 0.

## Outcome
P4 vendor, chronic ilg001 slowness; nothing failing or held, no action.

## Links
- Slack thread: https://gfs-engineering.slack.com/archives/C099WKQTE8G/p1792672947841919
