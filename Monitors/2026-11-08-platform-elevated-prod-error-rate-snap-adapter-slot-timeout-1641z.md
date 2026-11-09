---
tags: [datadog-triage]
date: 2026-11-08
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: snap-adapter
business_id: PURDYFIGG
snap_instance: ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794156166571339"
opened_at: "2026-11-08T16:41:37Z"
severity_assessed: P3
flapping: true
outcome: real_minor
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# Third firing today: 26 PURDYFIGG sales orders hit snap-adapter's 30s slot timeout in the 16:40 burst on slow Snap ilg005; all created on redelivery

## Fired
Monitor 180072217 (group total) went Alert at 16:41:37Z (event ts 1794156097); Slack post C099WKQTE8G 1794156166.571339 at 16:42:46Z, no replies when read. Monitor status read OK at the time of triage (monitor query run from 16:39:37Z to 16:41:38Z returned the lines below). Third firing today after 15:46:37Z and 16:21:37Z (monitor events, source:alert, 24h: 180072217 Triggered 15:46:37 / Recovered 15:48:37 / Triggered 16:21:37 / Recovered 16:23:37 / Triggered 16:41:37; 334832256 Triggered 15:46:36 / Recovered 16:01:36 / Triggered 16:21:36 / Recovered 16:36:36). 180072217 also fired twice on 7 Nov (16:51:37Z, 19:52:37Z). No 334832256 event after 16:36:36Z was read in the first 12 of 15 events returned (remaining 3 not read).

## Investigation
- Error lines behind the firing: the monitor's own query (with its exclusions) over 16:39:37Z-16:41:38Z returns one service and one message: snap_adapter "Entity creation in SNAP failed", 26 lines, first 16:40:43.859Z, last 16:40:46.336Z. Unfiltered `@domain:fuse status:(error OR critical OR alert OR emergency) @environment:prod` from 16:30Z to 16:48Z: the same 26 snap_adapter lines and nothing from any other service (so none from shopify-connector, config-service, fuse-ui, tracking, dedupe or replay).
- Breakdown of those 26 (snap_adapter prod logs): all `failureMode:slot_timeout`, `errorMessage` "Timed out after 30000ms waiting for a concurrency slot", `transient:true`, `deliveryAttempt:1`, `businessId:PURDYFIGG`, `recordType:sales_order`, 26 distinct recordIds, revision snap-adapter-prod-00099-b4z. Same mechanism as the 15:45Z and 16:20Z firings.
- Recovery at recordId level: all 26 failed recordIds have exactly one later "Entity created in SNAP", 16:42:39.651Z to 16:43:04.708Z, 115.8 s to 139.9 s after each record's last failure. Across 15:00Z to now, 74 distinct PURDYFIGG sales_order recordIds failed (33 + 15 + 26) and all 74 have a later created log. The only recordId with a failure and no created log across all businesses and types since 15:00Z is DOCKBAY UK-913950 (replay-service holds it, see below).
- Duplicates: no recordId has more than one "Entity created in SNAP" in 16:40Z-16:44:30Z or in 16:44Z-now.
- Held: replay-list-failures (production, sales_order, createdAt 2026-11-08) total 1: DOCKBAY UK-913950, 15:02:45Z, `ShipAddress.City` over 30 chars, failurePoint create.wms_precheck (unrelated). PURDYFIGG's newest held failures are three goods_out_confirmation entries from 16:35:17Z ("Fulfillment order ... is CLOSED in Shopify"), a different flow and not sales_order creation.
- Burst: "Incoming record received" 16:40:09Z to 16:46Z, per deliveryAttempt: 108 attempt-1 between 16:40:09.029Z and 16:40:46.339Z (a 37 s window), then 30 attempt-2 (16:40:55Z to 16:42:02Z). 111 "Entity created in SNAP", 111 distinct recordIds, all PURDYFIGG, 16:41:51.208Z to 16:43:04.742Z; none were created before 16:41:51Z, so the burst's first creation came about 100 s after its first arrival. Slowest order in this burst was in Snap about 2 min 55 s after arriving (16:40:09 to 16:43:04, bounds from the log windows, not per-record).
- Cloud Run snap-adapter-prod (gcp.run.request_count, per minute): 503 = 26 at 16:41, 0 at all other minutes 16:30-16:44; 429 = 4 at 16:42, 0 at all other minutes 16:30-16:44 (earlier firings had 0 429s per the 16:21 record; cause of these 4 not established); 204 = 18 (16:42) + 82 (16:43) + 11 (16:44) = 111, matching the 111 created logs. instance_count avg 1.5 for every minute 16:30-16:44.
- Snap ilg005 (PURDYFIGG host https://ilg005liveapi.snapfulfil.net/api, get-snap-connection production): snap.request.latency.avg by snap_host, per-minute points from 16:40Z: 6687, 5681, 5219, 4689, 4854, 5114, 4598 ms; 4493 ms at 16:48. Earlier 10 s series shows 566-637 ms at 16:30:10-16:30:30 and 2.6-3.1 s for the 16:31 burst (74 created, 0 failed). snap.slot_queue_depth (max) on ilg005 per minute 16:40-16:46: 20, 24, 7.5, no data, 24, 24, 6.8.
- Direct read-only probe of ilg005 (curl GET /api/v2/snaplookups/RECSTATUS at 16:48:51Z, 5 calls 2 s apart, plus one snap MCP snap-lookup RECSTATUS): HTTP 200 on all 5 at 0.051-0.073 s; MCP lookup returned 6 rows.
- Next burst did not fail: 16:45Z burst = 90 attempt-1 + 28 attempt-2 incoming, 118 "Entity created in SNAP" (35 + 81 + 2, 16:46Z-16:48Z), 0 failed logs, no duplicates; ilg005 latency in that burst was 4.5-5.1 s. So latency around 5 s did not by itself produce slot_timeouts.
- Trend: slot_timeout failures by minute today: 15:45 = 18, 15:46 = 15 (33 total), 16:20 = 11, 16:21 = 4 (15 total), 16:40 = 26 (all in one minute). Gaps between firings 35 min then 20 min; sizes 33, 15, 26. Zero slot_timeout failures on 4 Nov, 5 Nov, 7 Nov; 6 Nov 6; 2 Nov 267; 3 Nov 4 (per the 16:21 record, not re-queried).
- Maintenance: grep of Maintenance/*.md for 2026-11-07 and 2026-11-08 returned no record. Not checked: #bifrost-general pin or SNAPDowntime mail.
- Deploys: all failure logs carry revision snap-adapter-prod-00099-b4z, the same as the earlier firings (change events not re-queried for this window).

## Outcome
real_minor, P3. Repeat of the 15:45Z and 16:20Z mechanism: a PURDYFIGG order burst met slow ilg005 and snap-adapter's own 30 s slot timeout. All 26 failed orders are in Snap about 2 min after failing; nothing held for sales_order creation from these; no duplicates. Third occurrence in 55 minutes (74 orders delayed in total) but the 16:45 burst created 118 orders with no failures, so the pattern is recurring rather than demonstrably worsening. Follow-up (not filed): monitor tuning and slot-cap / ack-deadline review, as flagged in the 16:21 record.

Not established: why ilg005 averages 4.5-6.7 s during bursts while idle probes take 0.05-0.07 s; whether that latency is caused by our own load or by Snap; the adapter slot cap and ack-deadline settings (not read); what the 4 Cloud Run 429s at 16:42Z were; why created recordIds (111) exceed attempt-1 incoming logs (108) by 3 and why 4 attempt-2 deliveries arrived beyond the 26 redeliveries of failures; per-record mapping of attempt-1 incoming lines to recordIds (those logs carry messageId, not recordId); whether 334832256 fired again after 16:36:36Z; whether any maintenance notice exists in #bifrost-general or mail; whether prior firings' threads received replies.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794156166571339
- Monitor: https://app.datadoghq.com/monitors/180072217
- Earlier records: [[2026-11-08-snap-adapter-entity-creation-failing-1621z]], [[2026-11-08-snap-adapter-entity-creation-failing]]
