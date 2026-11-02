---
tags: [datadog-triage]
date: 2026-10-21
monitor: "[FUSE][Snap Adapter] API latency threshold breached"
service: snap-queue-polling-service
business_id:
snap_instance: ilg001
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792583004030049"
opened_at: "2026-10-21T11:42:08Z"
resolved_at: "2026-10-21T11:45:22Z"
minutes_spent: 3
severity_assessed: P3
flapping: true
outcome: vendor
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# ilg001 latency Warn (3.84s 20m avg) is lag from pre-outage slowness; host now 500s in ms

## Fired
Monitor 179927768, group snap_host ilg001liveapi, Warn, 20m avg 3839.952ms (4 folded firings).

## Investigation
- `snap.poll.request.latency.avg` ilg001, 5m buckets: 11:30 6210ms, 11:35 18ms, 11:40 33ms.
- snap-polling-service "Outbound queue fetch failed" HTTP 500 on ilg001: 6 @11:36, 2 @11:38, 2 @11:40, 1 @11:42Z (ilg005 similar: 7/2/2/1).
- Direct snaplookups probe on ilg001 (DOCKBAY) at 11:45Z: 500.
- No ilg001 creates held in replay-service since 11:35Z.

## Outcome
Vendor (Snap ilg001 HTTP 500 outage). Latency number is averaging artefact. Confirmations delayed, not lost.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792583004030049
- Verdict: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792583122552699
