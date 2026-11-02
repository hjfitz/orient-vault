---
tags: [datadog-triage]
date: 2026-10-28
monitor: "[FUSE][Snap Adapter] Entity creation failing for many records"
service: snap-adapter
business_id: DOCKBAY
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793189209323259?thread_ts=1793189209.323259"
opened_at: "2026-10-28T12:06:36Z"
resolved_at: "2026-10-29T07:12:00Z"
minutes_spent: 18
severity_assessed: P3
flapping: true
outcome: real_minor
session_id: 7198be0e-f4de-4cae-8e32-ef4ac0c4cdb9
status: resolved
---
# Entity creation failing: DOCKBAY 12:05Z, 16:51Z, then a 62-record PURDYFIGG slot_timeout burst at 17:21Z (Alert); all recovered

## Fired
Monitor 334832256 (Warn) tripped at 12:06:36Z: more than 5 distinct recordIds with "Entity creation in SNAP failed" in 15m. No thread of its own existed in the channel; reply went on the same-time Platform error-rate alert thread.

## Investigation
- Failure logs, last 3h grouped by failureMode/business: DOCKBAY slot_timeout transient x6 (12:05:29-12:05:38Z); ESCENTRIC, PURDYFIGG, WILDSMITH non-transient earlier (09:47-10:59Z), outside the 15m window.
- Error text "Timed out after 30000ms waiting for a concurrency slot", HTTP 503 to Pub/Sub, deliveryAttempt 1.
- All 6 recordIds later logged "Entity created in SNAP" (12:05:41-12:05:56Z). Nothing held.
- `snap.poll.request.latency.avg` 6h: ilg001/003/004 about 4-13s, ilg002/005 0.1-1.2s. 7 days: ilg001/004 3-5s daily, ilg003 about 5.3s from 27 Oct. Latency monitor 179927768 is already in Alert and muted.
- slot_timeout daily counts over 7d: present 21, 22, 23, 26, 27, 28 Oct (PURDYFIGG, STUBBLE, DOCKBAY, SPORTLUX, ICONICL).
- No maintenance record covers 28 Oct.

## Outcome
Self-resolved, P4. Probably a knock-on of chronically slow Snap hosts (correlation only). Chronic slot_timeout recurrence may merit a ticket or a slot/latency review.

Not established: DOCKBAY's Snap host (Fuse MCP unreachable, no get-snap-connection), direct host probe, causal link between slow hosts and slot timeouts, Platform error-rate monitor cause.

## Refire 16:51Z (Warn, same monitor)
Monitor query: `cardinality(@recordId)` of "Entity creation in SNAP failed" on snap_adapter prod, last 15m (retries of one record count once). Window 16:36:36-16:51:36Z: 7 distinct records, DOCKBAY 5 slot_timeout (master_data, 16:51:17-25Z), PURDYFIGG #6612739 slot_timeout (16:46:03Z), ESCENTRIC #138864 schema_validation. Without ESCENTRIC retries still 6 > 5, so a genuine slot_timeout wave, not retry inflation.
- All 5 DOCKBAY and #6612739 later logged "Entity created in SNAP" (16:52:17-23Z, 16:46:59Z). No loss.
- Creates per minute at the time: PURDYFIGG 107 (16:46), DOCKBAY 22/34/71 (16:50-16:52). Correlation only.
- ESCENTRIC #138864: schema_validation "Unable to parse data", 32 failures 14:15-16:50Z every 5 min (shopify-connector republish), stored in replay-service, not created per logs. Held, needs data fix then replay.
- PURDYFIGG #6521935: 22 failures 13:55-15:45Z, none since, no "Entity created" log; creation not confirmed.
- Verdict unchanged: self_resolved P4, with ESCENTRIC held. Reply posted in the Platform error-rate thread (monitor has no thread of its own): https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793206478606219?thread_ts=1793206363.217339

Not established (refire): whether #6521935 was created or why retries stopped; cause of slot timeouts (Snap latency vs our concurrency cap); Snap lookup and host probe (Fuse MCP 401).

## Refire 17:21Z (Alert, threshold >10 distinct records / 15m)
Replied in the Platform error-rate thread, broadcast: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793208303126059?thread_ts=1793208164.798889
- Window 17:06-17:24Z: PURDYFIGG sales_order slot_timeout, 62 distinct recordIds, 73 logs, 17:20:50-17:22:13Z. Only other failure: ESCENTRIC #138864 schema_validation at 17:10:03Z. No snap_api_error, no other business or mode.
- All 62 recovered: 49 "Entity created in SNAP", 13 "Entity already exists in SNAP" on deliveryAttempt 2 (17:21:55-17:22:46Z). 0 pending.
- Creates at volume: 100 (17:16), 54 (17:22), 32 (17:23) per minute (snap_adapter, all businesses).
- Snap latency (snap.poll.request.latency.avg): ilg001 8.5s, ilg003 9.4s, ilg004 8.7-10.8s at 17:22-17:24Z; all hosts under 2.1s at 17:14Z. ilg002/005 0.3-4.9s.
- ESCENTRIC #138864 held in replay-service, no create log; no attempts seen after 17:10:03Z.
- Verdict real_minor, P3; flapping monitor (needs retune to exclude transient slot_timeout that redeliver).

Not established (refire): PURDYFIGG's Snap host (Fuse MCP 401); Snap latency vs our slot cap as cause; why the 13 already existed; why ESCENTRIC attempts stopped; Pub/Sub backlog.

## Refire 2026-10-29 07:06Z (Alert, >10 distinct records / 15m)
Replied in the Platform error-rate thread, broadcast: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793257761604059?thread_ts=1793257670.492449 (monitor has no thread of its own).
- Window 06:51-07:07Z: 53 distinct recordIds, all SPORTLUX sales_order slot_timeout (transient), 07:06:26-07:07:09Z. No snap_api_error, no other business, mode or Fuse service.
- 53/53 later "Entity created in SNAP" (checked 07:08:51Z), 0 pending, no "already exists". Oldest unacked 0s on all prod snap_adapter create_record subs except sales_order 8s in one 2-min bucket.
- Creates (all businesses): 20, 92, 36 per minute at 07:06-07:08Z; 1-4 per minute before. Same shape as 17:21Z yesterday, slightly smaller (53 vs 62, 92 vs 100/min).
- Latency 10-min means 06:00-07:10Z: ilg001 2.8-7.3s, ilg003 2.8-7.1s, ilg004 3.2-6.0s, ilg002/005 0.2-0.6s.
- SPORTLUX slot_timeout by day: 26 Oct 2, 27 Oct 27, 28 Oct 15, 29 Oct 53.
- ESCENTRIC #138864 and PURDYFIGG #6521935: no snap_adapter logs since 17:00Z.
- Verdict real_minor, P3, flapping monitor.

Not established (refire): SPORTLUX's Snap host (Fuse MCP 401); whether slow hosts or our slot cap cause the timeouts; whether the two held orders were ever created.

## Refire 2026-10-29 16:11Z (Alert, P2 monitor, >10 distinct records / 15m)
No thread of its own; reply goes in the Platform error-rate thread / by the watcher. Triaged 16:15Z.
- Window 15:56-16:12Z: 79 distinct recordIds, all PURDYFIGG sales_order. 78 slot_timeout (transient, 126 logs, 16:10:41-16:12:33Z, "Timed out after 30000ms waiting for a concurrency slot"), 1 schema_validation (#6617071, "Unable to parse data", non-transient, 5 attempts 15:55-16:10Z every 5 min). No other business, mode or record type; no snap_api_error; no error/warn from replay/dedupe/other services in the window.
- 78/78 recovered: 55 "Entity created in SNAP", 23 "Entity already exists in SNAP", checked 16:13Z; 0 pending. Last failure log 16:12:33Z, none in 16:12:40Z-16:15Z.
- #6617071 held: "Failure stored" x5 in replay-service, no created log. Not in the earlier held list; needs data fix then replay.
- Load: PURDYFIGG Shopify batch f83c3c8f at 16:05-16:06Z carried 583 distinct records (about 490 already existed: 216+366 "already exists" logs, 98 created); batch a7db09a1 at 16:10Z had ~107 records and produced the timeouts (0 creates 16:10, 1 at 16:11, then 34+22 at 16:12, 48 at 16:13). All snap_adapter creates per minute 15:50-16:13Z: 80, 74, 88, 94 (16:05), 8 (16:06).
- Pub/Sub: oldest unacked on prod create_record_sales_order peaked 30s (4 buckets 28-30s) 15:57-16:08Z, 8s at 16:08Z; 0 on other prod subs. No backlog.
- Snap host latency (5-min avg, 15:30-16:10Z, s): ilg001/003/004 live 4.5-13.8 (the usual plateau); ilg002 live 0.2-0.5 until 16:05 then 1.0, 4.2 (16:10 partial); ilg005 live 0.3-0.5 until 16:05 then 0.9, 8.1 (16:10 partial). snap.poll.request equals .success on every live host, every minute 15:55-16:14Z. snap.slot_queue_depth ilg005live 22-24 at 15:55-16:12Z, 19.2 then 4.5 at 16:13-16:14Z.
- Maintenance: Maintenance/ records cover DB5 10:00Z (recovered 10:22Z) and a firewall window 08:00-09:00Z. Nothing covers 16:00Z.
- Verdict real_minor, P3. Third slot_timeout wave in 2 days (28 Oct 17:21Z 62 PURDYFIGG, 29 Oct 07:06Z 53 SPORTLUX, now 78 PURDYFIGG), all fully recovered. Flapping monitor.

Not established (refire 16:11Z): PURDYFIGG's current Snap host (ilg005 from the 10:03Z record, Fuse MCP 401 now); whether the ilg002/ilg005 latency rise at 16:10Z is cause or effect of our load; why 490 of the 16:05Z batch already existed; cause of #6617071 parse failure; ESCENTRIC #138864 / PURDYFIGG #6521935 not re-checked.

## Refire 2026-11-02 14:38Z (Warn, P2 monitor, >5 distinct records / 15m)
No thread of its own; the same-time Platform error-rate alert thread is C099WKQTE8G 1793630386.889499. Triaged 14:41Z. Verdict real_minor, P3, one record held.
- Window 14:23-14:39Z: 8 distinct recordIds, all DOCKBAY sales_order, 14:37:09-14:38:16Z. 7 slot_timeout (transient, deliveryAttempt 1: UK-911965, -911971, -912065, -911963, -911968, -911975, -912049) and 1 schema_validation (UK-911960). No snap_api_error, no 5xx/ECONN/ETIMEDOUT in snap_adapter 14:00-14:41Z, no other business or service with error logs in the window (snap_adapter 8 only).
- All 7 slot_timeout records later "Entity created in SNAP" (14:38:20-14:38:41Z, checked 14:40Z), 0 pending.
- Held: UK-911960 (shipment CS67250, businessSalesOrderId SO465857): schema_validation, transient false, fieldErrors `ShipAddress.0.City` "Too big: expected string to have <=30 characters". replay-service "Failure stored" 14:37:10Z, dedupe "Dedupe gate held on permanent failure"; no created log through 14:40:44Z. Needs the City fixed at the source and replay.
- Load: DOCKBAY's REST sales-order stream, silent since 10:43Z (see 2026-11-02-new-orders-stopped-dockbay), resumed: rest_connector "Incoming record received" 24 in the 14:25Z 5-min bucket and 110 in 14:35Z (140 since 10:30Z). snap_adapter DOCKBAY "Entity created in SNAP" 109 in 14:30-14:41Z (133 distinct since 14:00Z). Creates per minute, all businesses: 28 (14:37), 80 (14:38), 2 (14:40). snap.slot_queue_depth 12-23 at 14:29-14:38Z, 0 at 14:38-14:40Z.
- Snap host latency (snap.poll.request.latency.avg, ms): ilg001live 2.3-12.7s with 20.9s at 14:36Z; ilg003live 2.0-13.9s with 23.4-26.8s at 14:36-14:37Z; ilg004live 2.1-16.8s; ilg002live 0.1-1.5s; ilg005live 0.1-2.3s. Same plateau as earlier days. Oldest unacked on all prod snap_adapter create_record subs 0 every 3 min 14:00-14:36Z (one dev sub 19s at 14:27Z).
- Maintenance: no Maintenance/ record for 2 Nov (latest 28 Oct firewall); no snap maintenance hit in #bifrost-general after 30 Oct.
- Flapping monitor; fourth slot_timeout wave in the series, smaller (7 vs 53-78).

Not established (refire 14:38Z): DOCKBAY's Snap host (Fuse MCP 401; warehouse SPACE site 0001 only); whether slow Snap hosts or our slot cap cause the timeouts; the actual City value on UK-911960 (redacted in logs); previously held 29 Oct records not re-checked.

## Refire 2026-11-02 16:16Z (Alert, P2 monitor, >10 distinct records / 15m)
Triaged 16:21Z. Thread: the same-time Platform error-rate alert, C099WKQTE8G 1793636268.775249 (monitor has no thread of its own); another agent had already replied there at 16:20Z. Verdict real_minor, P3, one record held.
- Window 16:01:36-16:16:37Z: 33 distinct recordIds, 33 logs, all deliveryAttempt 1, all sales_order. 32 PURDYFIGG slot_timeout (transient:true, 24 at 16:15Z and 8 at 16:16Z, one correlationId 6b19b60f), 1 DOCKBAY schema_validation (UK-912082, 16:02:26Z). No other mode or business; no snap_api_error and no 5xx/ECONN/ETIMEDOUT in snap_adapter 15:30-16:19Z; no failure after 16:17Z.
- 31/32 PURDYFIGG "Entity created in SNAP" and 1 "Entity already exists", checked 16:19Z. 0 pending. Creates per minute (all businesses): 58 (16:05), 76 (16:10), 73 (16:16), 11 (16:17).
- Load: shopify-connector PURDYFIGG "Bulk reap completed" every 5 min, `total`/`published` 67-77 until 15:30Z then 125 (15:35), 174, 229, 303, 358, 422, 478, 548, 631 (16:15Z); errored 0, skipped 0. Failures hit the 16:15Z reap, 0 failed at the 16:10Z reap (76 creates).
- UK-912082 (DOCKBAY): schema_validation, transient false, fieldErrors `ShipAddress.0.City` "Too big: expected string to have <=30 characters". replay-service "Failure stored" and dedupe "Dedupe gate held on permanent failure" 16:02:27Z; no created log through 16:20Z. Same error as UK-911960 (14:37Z). Needs City fixed at source then replay.
- Older held records (ESCENTRIC 15309, UK-911960, PO573058, #138864, #6521935, #6617071): no "Entity created/already exists" log since 29 Oct for any of them.
- Snap latency 5-min avg 15:30-16:15Z (s): ilg001 3.5-12.5 (8.3 last), ilg003 2.7-10.8 (10.8 last), ilg004 3.0-8.3 (7.7 last), ilg002 0.1-2.0, ilg005 0.2-1.8. slot_queue_depth ilg005 0.5-18 (14.4 last bucket). Oldest unacked on prod snap_adapter create_record_sales_order 0-12.4s, 0 on every other sub. Latency monitor 179927768 in Alert (muted).
- Maintenance: no Maintenance/ record for 2 Nov; no snap maintenance post found in #bifrost-general since 30 Oct (search).
- Monitor 334832256: 8 alert events today (Warn/Alert/Recovered); Warn 15:02:36Z, Alert 16:16:36Z.

Not established (refire 16:16Z): PURDYFIGG/DOCKBAY Snap host and any direct probe (Fuse MCP 401); whether Snap slowness or our 30s slot cap drives timeouts; why the reap total rose from 77 to 631 since 15:30Z; the City value on UK-912082 (redacted); whether the other held records were fixed outside snap_adapter logs.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793189209323259?thread_ts=1793189209.323259
