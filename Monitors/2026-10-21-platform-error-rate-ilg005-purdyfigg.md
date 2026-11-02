---
tags: [datadog-triage]
date: 2026-10-21
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: snap-adapter
business_id: PURDYFIGG
snap_instance: ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792580625070129"
opened_at: "2026-10-21T11:02:37Z"
resolved_at: "2026-10-21T11:05:36Z"
minutes_spent: 3
severity_assessed: P4
flapping: false
outcome: self_resolved
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# PURDYFIGG ilg005 create timeouts at 11:02Z tripped the platform error-rate monitor; they redelivered cleanly

## Fired
Monitor 180072217 (more than 2 `@domain:fuse` error logs in 2 minutes, excluding snap_adapter `transient:false`) alerted at 11:02:37Z, 90 seconds after the ilg001 latency Alert.

## Investigation
- All prod `status:error` logs from 10:58 to 11:04Z: 4 snap_adapter `SNAP request failed` (status 599) for PURDYFIGG #6570186, #6570190, #6570280 and #6570286 at 11:02:14–16Z. The other two were `transient:false` rejections, which the monitor excludes: PURDYFIGG #6565591 (Email MANDATORY) and DOCKBAY UK-909462 (City over 30 characters). None of the errors involves ilg001.
- PURDYFIGG is on ilg005 (get-snap-connection; site 0010 is BM2, instance 005).
- Correlation de9c6a3d: the 120000ms timeout led to `Retries exhausted` at 11:04:14–17Z. The circuit opened for ilg005, and snap-adapter returned 503 so Pub/Sub would redeliver. At 11:05:02–06Z all 4 got `Entity already exists in SNAP`, then 204. The original writes had landed, so nothing is held.
- ilg005 `snap.poll.request.latency.avg` peaked at 3.3–5.3s around 11:00–11:04Z and is now 166ms. Direct probe at 11:05Z: 4 `snaplookups` calls returned 200 in 0.40–0.62s.
- Not established: the cause of the ilg005 slowdown. ilg001 spiked to 26s and ilg002 to 1.4s at the same time.

## Outcome
Self-resolved vendor blip on ilg005, P4. Verdict posted in the thread without a ping. No ticket.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792580625070129
- Verdict: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792580736194369?thread_ts=1792580625.070129
