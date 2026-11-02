---
tags: [datadog-triage]
date: 2026-10-22
monitor: "[FUSE][Snap Adapter] API latency threshold breached"
service: snap-adapter
business_id:
snap_instance: ilg004
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792691246078149"
opened_at: "2026-10-22T17:46:08Z"
resolved_at: "2026-10-22T17:48:51Z"
minutes_spent: 3
severity_assessed: P4
flapping: true
outcome: vendor
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# ilg004 Snap API latency >5s (repeat)

## Fired
Monitor 179927768 on `snap_host:https_//ilg004liveapi.snapfulfil.net/api`, avg latency 5012ms over 20m. Repeat of the 16:10Z triage (ilg004 slow on Snap's side since the planned DB4 update ended 08:54Z).

## Investigation
- `snap.poll.request.latency.avg` ilg004live since 15:30Z: 2-min buckets 1.7–8s since 16:10Z (16.5s peak around 16:00Z), no worsening.
- Poll metrics since 16:10Z: ilg004live 735 success, 0 failure.
- Snap service errors since 16:10Z (snap_adapter / snap-polling-service / snap-queue-polling-service, prod): only 31 snap_adapter `schema_validation` errors, all PURDYFIGG (LastName>30 retries). No 5xx/404/timeout/circuit errors. Last slot_timeout was 15:55Z.
- replay_service "Failure stored" since 15:00Z: PURDYFIGG only. No new holds for KAPPAHL, BABYMORI, SAMMCK, SAIRA or SPORTLUX.

## Outcome
P4 vendor, no change. Verdict posted in thread. No ticket.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792691246078149
