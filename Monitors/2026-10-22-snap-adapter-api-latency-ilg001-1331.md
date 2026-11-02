---
tags: [datadog-triage]
date: 2026-10-22
monitor: "[FUSE][Snap Adapter] API latency threshold breached"
service: snap-adapter
business_id:
snap_instance: ilg001
channel: bifrost-notifications
thread_url: "https://gfs-engineering.slack.com/archives/C099WKQTE8G/p1792675942511459"
opened_at: "2026-10-22T13:31:08Z"
resolved_at: "2026-10-22T13:32:58Z"
minutes_spent: 2
severity_assessed: P4
flapping: true
outcome: vendor
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# ilg001 latency monitor repeat (5.03s avg vs 5s), nothing failing

## Fired
Monitor 179927768, group snap_host ilg001liveapi, 20-min avg `snap.poll.request.latency.avg` 5032ms > 5000ms at 13:31:08Z. One further firing folded in. Repeat of the 12:41Z triage.

## Investigation
- Latency `snap.poll.request.latency.avg{snap_host:*ilg001*}` 12:30Z–now: 20s points 3.0–11.5s.
- Since 12:41Z: `snap.poll.request.success` = 785, `snap.poll.request.failure` = no data (0).
- Logs (snap_adapter / snap-polling-service / snap-queue-polling-service, @environment:prod) since 12:41Z: 0 errors; only warn pattern "Consignment StU not found" (531), steady over prior 24h (4.6k+), not a new signal.
- replay-list-failures production, createdAt 2026-10-22: DOCKBAY 0, MANUCURIST 0.
- Not established: why ilg001 has been slow since 19 Oct.

## Outcome
P4 vendor, no action. Monitor still needs a retune (chronic flapper).

## Links
- Slack thread: https://gfs-engineering.slack.com/archives/C099WKQTE8G/p1792675942511459
