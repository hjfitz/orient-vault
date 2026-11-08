---
tags: [datadog-triage]
date: 2026-11-08
monitor: "[FUSE][Snap Adapter] Entity creation failing for many records"
service: snap-adapter
business_id: PURDYFIGG
snap_instance: ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794152865156769"
opened_at: "2026-11-08T15:46:36Z"
severity_assessed: P3
flapping: false
outcome: real_minor
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# 33 PURDYFIGG sales orders hit snap-adapter's 30s slot timeout during a burst on slow Snap ilg005; all created on redelivery

## Fired
Monitor 334832256 (P2, group total) went to Alert at 15:46:36Z: more than 10 distinct `@recordId` with "Entity creation in SNAP failed" in 15m (query from the monitor definition). The monitor has no Slack thread of its own; the nearest thread is the same-minute Platform error-rate alert (C099WKQTE8G 1794152865.156769, 15:47:45Z).

## Investigation
- Failures (snap_adapter prod logs, 15:44-15:51Z): 33 "Entity creation in SNAP failed", 33 distinct recordIds, all PURDYFIGG, all `sales_order`, all `failureMode:slot_timeout`, `errorMessage` "Timed out after 30000ms waiting for a concurrency slot", `transient:true`, `deliveryAttempt:1`, `exhausted:false`. First 15:45:40.600Z, last 15:46:13.514Z. 33 x "POST /events/v1/record/create/sales_order - 503". One connectorId (conn_7ce8402090194b67b0f8a1de03019397), one correlationId. No other failure mode in the window.
- Counts since 15:44:00Z: 245 "Incoming record received" lines, 212 "Entity created in SNAP", 33 failed. Zero status:error snap_adapter logs after 15:47:30Z.
- Recovery: all 33 failed recordIds have a later "Entity created in SNAP", 15:47:19.680Z to 15:47:39.664Z (checked by recordId, 0 missing). Pub/Sub redelivered the 503s.
- Held: replay-list-failures (production, PURDYFIGG, 2026-11-08) returned total 0. The only replay entry for today is DOCKBAY UK-913950, `ShipAddress.City` over 30 chars, create.wms_precheck, 15:02:45Z, unrelated to this burst.
- Snap: PURDYFIGG host is ilg005 (get-snap-connection, production; lookup-snap-instance: DB5, site 0010 Brackmills 2). snap.request.latency.avg for ilg005 was 689 ms at 15:30, 2.2-4.3 s 15:25-15:40, then 7.8 s (max 9.0 s) at 15:45, 6.3 s at 15:46, 4.8 s at 15:47. snap.slot_queue_depth 19 at 15:45 and 15:46, 6 at 15:47. Direct read-only probe (GET /v2/snaplookups/RECSTATUS, 15:50Z, 5 calls, 2 s apart): HTTP 200 x5, 0.06 s on 3 and 4.10 s on 2. snap-get-outbound-queue (top 1) returned HTTP data (latest row created 15:48:52).
- Snap-side status: no Snap error response was returned; snap.request.failure had no data points in 15:25-15:51Z, and no snap_api_error / circuit_open failure modes occurred.
- Changes: all snap_adapter logs in the last 6h carry version 4393a8838af6, revision snap-adapter-prod-00099-b4z; no change_tracking/deploy events for snap_adapter in 6h. Instance starts at 11:02Z and 15:35Z were scale-ups of that same revision. No maintenance record in ~/Documents/obsidian/Maintenance/ covers 2026-11-08.
- Same-day context: monitor 323648859 (Pub/Sub ack headroom, Warn 15:43:39Z) recovered 15:50:46Z; monitor 180072217 fired 15:47:45Z (same log lines count there). 179927768 (Snap polling latency) status Warn.
- History: slot_timeout failures on 2 Nov 267, 3 Nov 4, 6 Nov 6, 8 Nov 33 (snap_adapter logs, 7d, other days 0). Monitor alert events: 12 in 7 days (latest before today 2 Nov, three Triggered/Recovered pairs 15:02-17:16Z that day).

## Outcome
real_minor, P3: a PURDYFIGG order burst met slow ilg005 and snap-adapter's own 30s slot timeout; 33 orders were delayed about 1.5-2 min and all are in Snap, nothing held. Not shown: how much of it was burst size versus Snap latency versus the slot cap. Not established below.

Not established: adapter slot cap and ack deadline settings (not read); split of cause between burst size, ilg005 latency and slot cap; why ilg005 intermittently takes about 4.1 s; which other businesses share ilg005 (lookup returned businessCount 0); whether the monitor should exclude transient slot_timeout (judgement, not tested).

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794152865156769
- Monitor: https://app.datadoghq.com/monitors/334832256
