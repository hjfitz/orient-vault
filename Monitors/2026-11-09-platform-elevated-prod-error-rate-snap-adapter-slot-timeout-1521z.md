---
tags: [datadog-triage]
date: 2026-11-09
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: snap-adapter
business_id: PURDYFIGG
snap_instance: ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794237766838229"
opened_at: "2026-11-09T15:22:46Z"
severity_assessed: P4
flapping: true
outcome: self_resolved
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# Platform error-rate monitor fired on three snap_adapter slot_timeout 503s; all three orders created within about 80 s

## Fired
Monitor 180072217 (more than 2 matching error logs in 2m) went Triggered at 15:21:37Z (Slack post 15:22:46Z), log window 15:19:37Z-15:21:37Z. The Datadog Recovered event is 15:23:37Z. The monitor was OK when read at about 15:41Z.

## Investigation
- Window query (monitor query, DDSQL group-by): exactly 3 logs, all `snap_adapter` "Entity creation in SNAP failed". Raw read: `failureMode: slot_timeout`, `errorMessage: Timed out after 30000ms waiting for a concurrency slot`, `transient: true`, `exhausted: false`, `deliveryAttempt: 1`, sales_order from Shopify. At 15:20:41 ESCENTRIC #140430, at 15:20:58 PURDYFIGG #6701233, at 15:21:06 PURDYFIGG #6701244. All three carry site 0010 / warehouse BRACKMILLS2, and get-snap-connection puts both businesses on `ilg005liveapi` (instance 005, DB5, site 0010 Brackmills 2).
- Per-recordId log trace: each of the three has a later "Entity created in SNAP" plus a 204 (15:21:49, 15:22:15, 15:22:18). Nothing from these three is left failed.
- snap_adapter pattern view 15:18:30-15:21:10: 24 "Incoming record received" between 15:19:13 and 15:20:53 against 2 "Entity created in SNAP" (15:19:17 and 15:20:47), then 12 creates in the 15:21 minute and 12 in the 15:22 minute.
- Other matching errors 14:30Z to now: no further snap_adapter matches. 3 config-service "Postgres ping took longer than 2000ms" errors (15:37:34, 15:37:41, 15:39:23) also match the monitor query; separate cause, not investigated.
- ilg005 `snap.poll.request.latency.avg` (polling service, per host, 2-minute points): 6524/6553 ms at 15:20, 6087 ms at 15:21, 1688/1158 ms at 15:22, then 130-220 ms to 15:40. Other hosts at 15:20 were 4062-4169 ms (ilg001-004), and every host shows a 4.1-4.2 s plateau at various times, so the plateau is not ilg005-specific and is unexplained. ilg005 also exceeded the plateau earlier: 6159 ms at 14:36, 7103/7486 ms at 14:54, up to 7718 ms at 15:02-15:03.
- Direct probes of ilg005 (read of snaplookups/RECSTATUS with PURDYFIGG's connection, 15:43-15:46Z): 0.06-0.25 s x6, 1.09 s x1, 4.15 s and 4.11 s on the first two. Host currently mostly fast, intermittently slow.
- Flapping: Datadog alert events show Triggered at 2026-11-08 15:46:37, 16:21:37, 16:41:37 and 2026-11-09 15:21:37 (4 in 30h). No firing earlier on 11-09 within the events read. snap_adapter slot_timeout counts by hour, 48h: PURDYFIGG 33 (11-08 15:00 hour) and 41 (16:00 hour), then PURDYFIGG 2 and ESCENTRIC 1 (11-09 15:00 hour).
- Maintenance: no file in `Maintenance/` names a window on 2026-11-09 (latest windows 11-03 10:00-10:30Z and 11-05 10:00Z).
- Latency monitor 179927768 status OK, muted_until 1794306393 (about 2026-11-10T10:26Z).
- Separate from this alert: replay-service holds two ESCENTRIC sales_order failures today (15335 at 11:08Z, ShipAddress.City over 30 chars; 15337 at 15:03Z, ShipContacts.Phone over 20 chars), both `create.wms_precheck`, `transient: false`, so excluded from this monitor.

Not established:
- Whether Snap slowness or our own concurrency use filled the adapter's slots. ilg005 latency was elevated at the same time, but there is no adapter in-flight or per-call duration telemetry and no APM spans for adapter calls to Snap.
- Why every host shows a 4.1-4.2 s plateau in the polling latency metric.
- Whether a Snap vendor notice exists (ILG mail to SNAPDowntime@ilguk.com and the #bifrost-general pin were not checked).
- Whether all 24 records received in 15:19-15:21 were created; only the three failed ones were traced.
- Chronicity beyond 48h. lookup-snap-instance returned businessCount 0 for ilg005 although two businesses resolve to that host.
- The Pub/Sub ack-deadline alert at 15:25 (another agent triages it).

## Outcome
Self-resolved, P4. Three transient slot_timeout 503s on ilg005 sales order creates; all three orders were created within 80 s. Monitor is a repeat flapper on this cause (4 firings in 30h).

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794237766838229
- Monitor: https://app.datadoghq.com/monitors/180072217
