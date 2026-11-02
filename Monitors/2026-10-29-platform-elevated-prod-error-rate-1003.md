---
tags: [datadog-triage]
date: 2026-10-29
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: snap-polling-service
business_id:
snap_instance: ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793268284132689"
opened_at: "2026-10-29T10:04:44Z"
severity_assessed: P4
flapping: true
outcome: vendor
session_id: 7198be0e-f4de-4cae-8e32-ef4ac0c4cdb9
status: open
---
# 10:03Z firing: ilg005 (DB5) 404s during the planned Snap DB5 update, 9 sales-order creates held in replay

## Fired
More than 2 domain:fuse error logs in 2m at about 10:04Z. Third firing today (07:06Z SPORTLUX snap_adapter slot_timeout, 08:10Z PURDYFIGG shopify-connector token refresh). New failure mode: Snap HTTP 404 from ilg005.

## Investigation
- Monitor's own query, 09:50-10:20Z: 51 errors, per minute 10:03 = 4, 10:04 = 42, 10:05 = 5. 42 snap-polling-service (6 each for ABBOTT, EPARFUM, ESCENTRIC, PHLUR, PURDYFIGG, STUBBLE, WILDSMITH; GET /v2/snapoutbound STOCK_MOVE, 404) and 9 snap_adapter sales_order creates (WILDSMITH 4, PURDYFIGG 4, ESCENTRIC 1).
- Every one targets https://ilg005liveapi.snapfulfil.net/api; the response is an IIS "HTTP Error 404 ... Not Found" page (Server: Microsoft-HTTPAPI/2.0).
- Maintenance/2026-10-19-snap-version-update-and-patch.md: DB5 (BM2) window starts 2026-10-29T10:00Z, est 60 min, "integrations off", no end time stated. ilg005 = DB5.
- Last "Entity created in SNAP" for these businesses 10:00:17Z; none after 10:00:17Z at 10:06Z.
- 9 creates (SO-29414..29417, #138943, #6615561/65/66, #6615456): snap_adapter "Entity creation in SNAP failed" (snap_api_error, transient:false), replay_service "Failure stored" x9, dedupe release 204, no later success log at 10:06Z. The transient:false ones are excluded from the monitor; the counted snap_adapter lines are the "SNAP request failed" pair.

## Not established
Whether ilg005 has recovered (errors stopped at 10:05Z but that may only be lower call volume, no success seen yet); whether the 9 held records are replayed or resent after the window; instance/business list via lookup-snap-instance (Fuse MCP 401).

## Outcome
Vendor, P4, planned maintenance. Escalate only if ilg005 still 404s past about 11:15Z. Replay the 9 held creates after the window.

## Update 10:08Z: [FUSE][Snap Adapter] Entity creation failing for many records (334832256) Warn
- Monitor: cardinality(@recordId) of "Entity creation in SNAP failed" over 15m, Warn >5, Alert >10. No Slack post of its own found in the channel at 10:06Z (latest message 10:06:34); the 07:06Z-era alerts for it also had no thread.
- Distinct failed recordIds in the 15m window at 10:08Z: 14 (listLogs, service:snap_adapter). That is already above the Alert threshold of 10, so expect Alert on the next evaluation. All 14 are sales_order, snap_api_error, transient:false, and every one has a baseUrl of ilg005liveapi and a 404 IIS page.
  - WILDSMITH 4, PURDYFIGG 4, ESCENTRIC 1 (the 9 from the earlier triage) plus 5 new STUBBLE at 10:06:08-09: SC17418701, 702, 703, 704, 706.
- replay-service "Failure stored" exists for all 14 (STUBBLE 5 at 10:06:08-09). Nothing lost.
- ilg005 still 404: snap-polling-service logged 404s to ilg005liveapi at 10:08:04Z for ABBOTT, EPARFUM, ESCENTRIC, PHLUR, PURDYFIGG, STUBBLE, WILDSMITH (18 each since 10:04:04Z, 63 total in 10 min). No success logged against ilg005 since. Down about 5 min as of 10:08Z (first 404 10:03:17Z), 8 min into the 60 min window.
- No other host: every snap_adapter and snap-polling-service error in 15-30m targets ilg005 (14 and 63). The separate ilg001 latency monitor (179927768) was firing all morning, a different signal.
- No "Entity created in SNAP" for any of the 14 records; the newest created log of any business was DOCKBAY 10:02:34Z.

### Not established (update)
- Which businesses have all traffic on ilg005: Fuse MCP 401, so no lookup-snap-instance or list-customers. The 7 polled businesses are on ilg005 for polling, but other hosts' health cannot be shown from logs (success calls carry no snapHost).
- Direct probe of ilg005 (snap MCP needs get-snap-connection, also Fuse MCP).
- Whether the replay of the 14 has happened (none can succeed before ilg005 is back).

## Update 10:13Z: [FUSE][Platform] create_data_failure spike (302536087) Warn, same cause
- Monitor: `sum(last_15m):sum:gcp.pubsub.topic.send_request_count{topic_id:bifrost.prod.create_data_failure.v1}.as_count() > 20`, P2, Terraform-managed. Warn at 10:12Z with value 13 (message shows a warn threshold of 5; alert is >20). It counts publish requests, not records. Metric per minute from 10:04Z: 1,0,5,5,0,0,2.
- Alert's own thread: C099WKQTE8G ts 1793268746.040589 (10:12:26Z, no replies when read).
- What is on the topic: replay-service "Failure stored" since 10:00Z = 24 entries, all recordType sales_order, covering 19 distinct records. snap_adapter "Entity creation in SNAP failed" since 10:00Z = 24 logs, all snap_api_error, statusCode 404, transient:false. The two counts match (no other failure type, no schema/validation failure in this window). The only other replay entries today are PURDYFIGG goods_out_confirmation at 08:20 and 09:43Z (earlier, unrelated).
- 19 distinct held: WILDSMITH 4, PURDYFIGG 6 (the 4 plus #6615571, #6615574), STUBBLE 5, PHLUR 3 (SO399422, SO399425, SO399428, new at 10:08:54Z), ESCENTRIC 1. Five of them (ESCENTRIC #138943, PURDYFIGG #6615456/561/565/566) were stored a second time at about 10:10Z, so the 24 is 19 + 5 retries.
- New distinct records per minute: 10:03 4, 10:05 5, 10:06 5, 10:08 3, 10:10 2 (PURDYFIGG, PHLUR counted once each). Still growing at 10:13Z.
- ilg005 still 404 at 10:12:04Z: snap-polling-service 42 errors per 2 min, every window since 10:04Z (ABBOTT sample baseURL ilg005liveapi, GET /v2/snapoutbound, status 404). No success logged since. Down about 9 min at 10:12Z.
- Only successful Snap create of any business since 10:00:30Z is DOCKBAY 13, last 10:02:34Z; none since (other hosts' traffic cannot be told apart from quiet).
- Support need: replay the held sales_orders after ilg005 returns; the retries add duplicate stored entries per record.

### Not established (update 2)
- Why 5 records were re-stored at 10:10Z (retry source not traced).
- Whether metric send_request_count (13) maps one to one to records (24 stored; publishes may be batched).
- Whether DOCKBAY and other businesses are on other hosts and healthy.
- Direct probe of ilg005; replay has not happened.

## Update 10:30Z: create_data_failure Alert (23 at 10:22Z, re-Triggered 10:26Z), ilg005 recovered, 20 records still held
- Alert events (302536087): Warn 10:11, Triggered 10:21:07, Warn 10:22:07, Triggered 10:26:07. Slack alert ts 1793269343.022849 has no replies.
- Failed creates since 10:00Z (snap_adapter "Entity creation in SNAP failed", 45m window): 56 logs, all statusCode 404, all recordType sales_order. Distinct records 33 = replay-service "Failure stored" distinct 33 (PURDYFIGG 12, STUBBLE 11, WILDSMITH 6, PHLUR 3, ESCENTRIC 1). Nothing lost. No schema_validation or other failure type; no other businesses. Last failure 10:20:21Z (STUBBLE).
- ilg005 recovery: last snap-polling 404 at 10:22:04Z (42 per 2 min every window 10:04-10:22). From 10:24:15Z the polling runs carry no errors; 0 domain:fuse error logs in the 7m to 10:29Z. First successful creates 10:25:08Z. 404s lasted about 19 min (first 10:03:17Z), inside the 60 min estimate.
- Created in Snap 10:25Z onward: PURDYFIGG 12 of 12 held (#6615456...#6615593) and ESCENTRIC #138943 (resends via dedupe, 158 request/sales_order 204s 10:25:05-08Z). Still no success log for STUBBLE 11, WILDSMITH 6, PHLUR 3 (20 records) as of 10:29Z; their last event is the failure.
- The 5 PURDYFIGG/ESCENTRIC re-stores seen earlier were repeated attempts (PURDYFIGG #6615456 stored at 10:05, 10:10, 10:15, 10:20); STUBBLE retried 6 records at 10:20.
- New and unrelated: snap-polling-service warn "Stock movement dropped - could not determine adjustment direction", ESCENTRIC, 4 per run from 10:24:15Z (first seen in this 14m window; earlier history not checked).
- Verdict: vendor, P4. Planned DB5 maintenance, recovered before the 60 min estimate ended. Replay/resend of the 20 outstanding records is the open item.

### Not established (update 3)
- Whether STUBBLE, WILDSMITH and PHLUR resend on their own (their feeds were not traced).
- Whether replay-service still lists the 13 recovered records as held (clear-down not checked).
- Whether the Warn about stock movement direction predates the maintenance.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793268284132689
- create_data_failure alert thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793268746040589
