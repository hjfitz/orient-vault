---
tags: [datadog-triage]
date: 2026-10-22
monitor: "[FUSE][Snap Adapter] API latency threshold breached"
service: snap-adapter
business_id:
snap_instance: ilg001
channel: bifrost-notifications
thread_url: "https://gfs-engineering.slack.com/archives/C099WKQTE8G/p1792669704443169"
opened_at: "2026-10-22T11:47:08Z"
resolved_at: "2026-10-22T11:49:28Z"
minutes_spent: 2
severity_assessed: P4
flapping: true
outcome: vendor
escalated_to:
ticket:
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# ilg001 Snap poll latency warn (repeat of 10:52Z)

## Fired
Monitor 179927768 Warn for snap_host ilg001liveapi: avg snap.poll.request.latency 4881ms over 20m (> 2000ms warn). Fourth latency warn today on ilg001/ilg004.

## Investigation
- Prod error logs (snap_adapter / snap-polling-service / snap-queue-polling-service) since 10:52Z: only 2 "Entity creation in SNAP failed" for PURDYFIGG ("Unable to parse data", 10:55Z, 11:00Z), a data rejection, not ilg001 latency. No 5xx/404/timeouts/circuit open matching ilg001.
- snap.poll.request.success{ilg001} since 10:52Z = 207; failure = none.
- Prod replay holds created 2026-10-22: DOCKBAY 0, MANUCURIST 0.
- Maintenance: no window covers ilg001 at 11:47Z (DB1 window was 21 Oct; today's 08:30Z window was DB4).

## Outcome
P4 vendor, repeat of the 10:52Z triage. Nothing held, no action. Not established: PURDYFIGG's Snap host.

## Links
- Slack thread: https://gfs-engineering.slack.com/archives/C099WKQTE8G/p1792669704443169
