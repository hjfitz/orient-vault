---
tags: [datadog-triage]
date: 2026-10-20
monitor: "[FUSE][Platform] Pub/Sub oldest unacked message age (bifrost.prod.snap_poll_customer.v1.sub) - Recovered"
service: snap-polling-service
business_id: 
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792487847974509"
opened_at: "2026-10-20T09:16:13Z"
resolved_at: "2026-10-20T09:30:00Z"
minutes_spent: 14
severity_assessed: P3
flapping: false
outcome: self_resolved
escalated_to:
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# [FUSE][Platform] Pub/Sub oldest unacked message age (bifrost.prod.snap_poll_customer.v1.sub) - Recovered

## Fired
Recovery notification: last 10 m <= 300 s.

## Investigation
- Oldest unacked climbed from ~06:10Z to peak ~9,290 s (~08:40-08:50Z), drained to 0 by ~09:10Z (10-min max series).

Not established: what held the poll during the outage; whether the drain triggered the 09:15Z re-announce burst.

## Outcome
Recovered; part of INC-40. Linked to INC-40 (https://gfsdeliver-eng.slack.com/archives/C0CAEGABJBF). Read-only; nothing restarted or replayed.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792487847974509
- Incident: https://gfsdeliver-eng.slack.com/archives/C0CAEGABJBF
