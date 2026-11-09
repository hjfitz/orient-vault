---
tags: [datadog-triage]
date: 2026-11-09
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: snap-adapter
business_id: PURDYFIGG
snap_instance: ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794240464998109"
opened_at: "2026-11-09T16:06:37Z"
resolved_at: "2026-11-09T16:07:48Z"
minutes_spent: 1
severity_assessed: P4
flapping: true
outcome: self_resolved
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# Platform error-rate monitor fired on four snap_adapter slot_timeout 503s for PURDYFIGG; all four orders created by 16:07:48Z

## Fired
Monitor 180072217 (more than 2 matching error logs in 2m) went Triggered at 16:06:37Z, log window 16:04:37Z-16:06:37Z. A monitor read at about 16:09Z still showed Alert; no Recovered event had been seen yet.

## Investigation
- Window query (the monitor's own query, raw read): exactly 4 logs, all `snap_adapter` "Entity creation in SNAP failed", `failureMode: slot_timeout`, `errorMessage: Timed out after 30000ms waiting for a concurrency slot`, `transient: true`, `exhausted: false`, `deliveryAttempt: 1`, PURDYFIGG sales orders from Shopify. 16:06:11 #6702832, 16:06:11 #6702904, 16:06:12 #6702814, 16:06:20 #6702933. Each was answered 503. All four carry site 0010 / BRACKMILLS2; get-snap-connection puts PURDYFIGG on `ilg005liveapi` (instance 005, DB5, Brackmills 2). No other service matched in the window.
- Per-recordId trace to 16:08Z: #6702933 "Entity already exists in SNAP" + 204 at 16:07:15 (deliveryAttempt 2); #6702904 "Entity created in SNAP" + 204 at 16:07:40; #6702814 created + 204 at 16:07:45; #6702832 created + 204 at 16:07:48. None left failed.
- snap_adapter per-minute counts: "Incoming record received" 105 at 16:00, 18 at 16:02, 90 at 16:05, 33 at 16:06, 2 at 16:07. "Entity created in SNAP" 105 at 16:00, 18 at 16:02, 1 at 16:03, none at 16:04 or 16:05, 47 at 16:06, 73 at 16:07. So a 90-record intake at 16:05 saw no creates until 16:06.
- `snap.poll.request.latency.avg` by `snap_host`, 2-minute points: ilg005 263 ms (16:04), 166 ms (16:06), 137 ms (16:08). Polling latency was not elevated when the slots timed out. Earlier, 15:50-15:56, all five hosts sat at about 4.1-4.2 s (ilg005 3.77-4.13 s) and were back to 70-380 ms by 15:58; this matches the latency monitor going Warn.
- Direct probes of ilg005 (read of snaplookups/RECSTATUS with PURDYFIGG's connection, 16:08Z): six reads, all HTTP 200, 0.060-0.121 s.
- Latency monitor 179927768: status Warn, `muted_until_ts` 1794306393 (about 2026-11-10T10:26Z).
- Flapping: Triggered at 2026-11-08 15:46:37, 16:21:37, 16:41:37 and 2026-11-09 15:21:37, 16:06:37 (5 in about 31h; 4 read from alert events, the fifth is this one). snap_adapter slot_timeout count since 2026-11-08 14:00Z: PURDYFIGG 80, ESCENTRIC 1.
- The monitor query's matches since 14:00Z today: snap_adapter 7 (3 at 15:20-15:21, 4 now), config-service 3 (the 15:37-15:39 Postgres ping errors, not in this window).
- Only non-transient snap_adapter error since 15:00Z: ESCENTRIC #15337 at 15:03:00Z, `schema_validation`, "Unable to parse data"; excluded from this monitor, not part of this alert.
- Maintenance: no file in `Maintenance/` names a window on 2026-11-09.

Not established:
- Whether our own concurrency cap or slow Snap create calls held the slots. There is no per-call create duration or in-flight telemetry, and polling latency (reads) was normal.
- Whether a Snap vendor notice exists (ILG mail and the #bifrost-general pin not checked).
- Why every host plateaued at about 4.1-4.2 s at 15:50-15:56.
- Whether the other records received at 16:05-16:07 were all created; only the four failed ones were traced.
- When the monitor recovers; not observed.

## Outcome
Self-resolved, P4. Four transient slot_timeout 503s for PURDYFIGG on ilg005; all four orders created by 16:07:48Z. Monitor is a repeat flapper on this cause (5 firings in about 31h). A retune or a look at the adapter's slot cap and intake bursts is worth a ticket if it keeps repeating.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794240464998109
- Monitor: https://app.datadoghq.com/monitors/180072217
