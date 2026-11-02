---
tags: [datadog-triage]
date: 2026-10-22
monitor: "[FUSE][Snap Adapter] API latency threshold breached"
service: snap-adapter
business_id:
snap_instance: ilg001, ilg004
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792682546037229"
opened_at: "2026-10-22T15:21:08Z"
resolved_at: "2026-10-22T15:24:20Z"
minutes_spent: 3
severity_assessed: P4
flapping: true
outcome: vendor
escalated_to:
ticket:
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# Snap latency monitor 179927768 fired again for ilg001 (6.8s) and ilg004 (5.8s)

## Fired
The 20-minute average of `snap.poll.request.latency.avg` went over 5s for ilg001 (6797ms) and ilg004 (5809ms) at 15:21Z. Threads: ilg001 ts 1792682546.037229, ilg004 ts 1792682548.002709. This monitor has fired repeatedly all day.

## Investigation
Every check below covers 14:11Z (the previous triage) to now:
- **Latency:** in the 15:18Z bin, ilg001 averaged 13.5s (max 29.5s) and ilg004 averaged 8.5s (max 11.2s). The other hosts stayed under 1.35s, including ilg005.
- **Polls:** ilg001 had 262 successes and ilg004 had 581, with 0 failures on any host.
- **Snap errors:** none across snap_adapter, snap-polling-service and snap-queue-polling-service. That covers 5xx, 404, network timeouts, open circuits and EHOSTUNREACH.
- **snap_adapter errors:** there were 29.
  - 23 are the known PURDYFIGG LastName `schema_validation` precheck failures.
  - 6 are PURDYFIGG (ilg005) slot timeouts: 3 at 15:10–15:11Z and 3 at 15:20:51Z (#6577043, #6577045, #6577098). The later 3 were all created in Snap with a 204 by 15:21:54Z.
- **Replay holds:** the only new prod holds are the known PURDYFIGG #6506667 and #6575295.
- **Maintenance:** no window covers 15:21Z. Today's only one was DB4 at 08:30Z.

Not established: the cause on Snap's side.

## Outcome
Vendor, P4, unchanged since 14:11Z. Replies were posted in both threads. This monitor's repeated firings remain a tuning question.

## Links
- Slack thread (ilg001): https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792682546037229
- Slack thread (ilg004): https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792682548002709
