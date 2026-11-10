---
tags: [datadog-triage]
date: 2026-11-10
monitor: "[FUSE][Dedupe Service] Silent publish drop (handled minus outcomes)"
service: dedupe-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794299508627269"
opened_at: "2026-11-10T08:30:36Z"
severity_assessed: P4
flapping: true
outcome: monitor_mistuned
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# Dedupe "silent publish drop" Warn at 08:30Z: nothing lost silently, 3 orders held in replay-service for support

## Fired
Monitor 302511456 (P2, managed-by:terraform, `sum(last_1h)` handled minus outcomes; warn >20, critical >50, evaluation_delay 300 s, require_full_window false, notify_no_data false; getMonitor). Warn event 08:30:36Z, Recovered event 08:35:36Z (search events API); getMonitor reads OK at 08:39Z. Alert post ts 1794299508.627269, no replies when read (08:4xZ). Value that tripped it, same formula over 07:25:36-08:25:36Z (queryScalarData sum): handled 859 minus (fresh 67 + duplicate 769) = +23; blacklisted, event.invalid, record.invalid and dropped_config_unavailable returned no series. My arithmetic, not the monitor's own evaluated value.

## Investigation
- Per-minute series, 8 h (queryTimeseriesData, 00:33-08:32Z): handled 4,945 vs outcomes 5,151. Rolling-1h net ran from -169 (01:33Z) to +23 (08:25Z), 0 from 03:33 to 06:03Z. By recordtype in 5-minute buckets 07:00-08:35Z the gap is all sales_order (net per bucket -1,-3,0,-1,-8,+4,+12,0,-1,-1,-1,+6,-6,+8,-1,-3,+6,-2); master_data reconciles exactly (46 = 46).
- 7-day hourly baseline: handled 275,198 vs outcomes 283,015 (outcomes exceed handled by 2.8%); 5 of 168 hours above +20 (4 Nov 18-19Z, 7 Nov 17-19Z); 84 hours below -20. Event history 30 d: 41 alert events, fired on 30 Oct, 1, 2, 4, 6, 7 Nov. Earlier records: Monitors/2026-11-07-dedupe-silent-publish-drop-*.md.
- Counters vs logs in the monitor window 07:25:36-08:25:36Z: logs incoming 3,794 = dropped 3,543 + published 251 (aggregateLogs), handled metric 859 (23%), fresh 67 vs 251 published, duplicate 769 vs 3,543 dropped.
- Per record (listLogs, key businessId|recordId|correlationId), dedupe_service 07:00:00Z to 08:36:06Z: 5,475 incoming logs = 5,474 distinct push receipts (5,474 `POST .../record/request` 204 logs) + 1 release-path receipt; 5,062 dropped (all @reason duplicate) + 412 published = 5,474; 0 receipts without an outcome, 0 outcomes without a receipt, 0 with two outcomes. The one key with two incoming logs is PURDYFIGG #6704623 (see below). Drop reasons since 07:00Z: duplicate 5,062 only. Logs for other drop paths (missing_business_id, sku_blacklist_unavailable, invalid_record_format, MessageDecodeFailed) since 00:00Z: 0. Warn/error in dedupe_service other than "Record dropped" 07:00-08:40Z: 0. "Dedupe gate held" 07:25:36-08:25:36Z: 0.
- Code (create-request.service.ts, identical at deployed sha 1eeac6f): handled increments first; fresh only after the publish; "Record published to topic" is logged before the publish call, so the log alone does not prove a publish. Proof is downstream below.
- Downstream per record (listLogs 06:55Z to 08:37Z): dedupe published 422 (422 distinct keys) = snap_adapter "Entity created in SNAP" 421 + "Entity creation in SNAP failed" 1; published without a snap_adapter outcome 0, outcome without a publish 0; publish to outcome lag p50 8.1 s, p95 18.2 s, max 24 s. Pub/Sub prod subscriptions (07:00-08:41Z): push_request_count only `ack` for dedupe create_record_request_sales_order (5,427) and snap_adapter create_record_sales_order (410); max oldest unacked 19 s and 14 s; max undelivered 2 and 14.
- Snap read-only samples (ilg005): PURDYFIGG #6707063 = PURD89109656A11 (DateCreated 07:00:09Z, published 07:00:07Z); #6707626 = PURD975C3353371 (08:25:11Z, published 08:25:09Z); STUBBLE SC17420746 = STUB39FAA45B9D5 (07:05:25Z); EPARFUM DC127893703 = EPAR3E0B8070AAF (07:21:19Z). Five duplicate-dropped records (#6688577, #6688804, #6688423, #6689040, #6688845): published 08:10:06Z, snap_adapter created 08:10:14Z, then dropped as duplicate 5 times (08:15-08:35Z).
- Upstream: shopify-connector create-side publishes vs PURDYFIGG dedupe receipts 07:00-08:36Z: 5,377 sales_order keys match; 1 PURDYFIGG receipt (PO-U-00002332, 08:35:06Z) has no shopify-connector publish; the 627 unmatched shopify-connector publishes in the wider run were all topic confirmation_made.
- Instances: 11 "Server listening" logs since 06:00Z (06:10 x4, 06:40 x2, 07:05 x3, 07:25 x2 incl. 07:25:19/07:25:21Z), no dedupe SIGTERM log; gcp.run.container.instance_count active 1 (03:00-06:00Z), 3.8 (06:10), 4 (07:10), 5 from 07:40Z, idle 0, never zero. Positive buckets at 08:00, 08:10 and 08:25Z came with no instance start after 07:25:21Z.
- Deploys/changes: Datadog change stories and change_tracking events for dedupe, snap_adapter, shopify-connector in 30 h: 0. GitHub deployments: dedupe-service last 2026-11-05T16:37Z (1eeac6f, same version in logs), snap-adapter 2026-11-09T10:48Z (8b2e5af), shopify-connector 2026-11-06T09:37Z.
- Held, not lost (replay-list-failures production, createdAt 2026-11-10, create-side types): 3 entries, all attempts 0. PURDYFIGG #6704623: published 07:15:05.503Z, snap_adapter "Entity creation in SNAP failed" 07:15:05.916Z, replay failure 76395c6e-8e07-46a1-a865-e8db7dcc56a3 (failurePoint create.wms_precheck, "ShipAddress.Name - Too big: expected string to have <=50 characters", replayable true, no blocking issues); the canonical ship-to name is 56 characters; not in Snap (snap-search-shipments by SalesOrder, BizSalesOrder, CustomerRef: 0 rows); dedupe ledger row 6af2c479ca971b8c38ea6591 holds it, dedupeCount 16, resends dropped as duplicate every 5 min to 08:35Z. Release path logged "Dedupe gate held on permanent failure" 07:15:07Z (this is the second incoming log). STUBBLE SC17420739: failed 05:36:24Z, create.snap_api, "Line1 - MANDATORY" (before the monitor window). SAIRA #37953: failed 08:40:03Z (after the window), create.wms_precheck, "ShipAddress.City - Too big: expected string to have <=30 characters".
- Maintenance/: no record has a window on 9 or 10 Nov (grep); newest is 2026-11-04. No Snap outage here, step 2b not run.

## Outcome
No record verified lost: every receipt in the window has a drop or publish, every publish has a snap_adapter outcome, nothing held in dedupe by the monitor's counters. The +23 comes from counters that undercount the logs about 4x and net both signs between buckets. Monitor_mistuned, P4, flapping. Separately 3 create-side orders sit in the replay failure inbox (data too long or missing at Snap pre-check) awaiting support. Nothing replayed, released or changed. Draft reply returned to the watcher, not posted by this run.

## Not established
Why the counters undercount the logs and why buckets net both signs (code read only, not tested). The monitor's own evaluated value at 08:30:36Z. Whether support already knows about the 3 held orders (no #fuse-support read). Whether STUBBLE SC17420739 was handled after 05:36Z (still listed, attempts 0, at about 08:45Z). Snap-side presence of the other 418 published orders (log evidence only). Why #6704623 first reached Fuse at 07:15Z when created 2026-11-09T16:39Z. Whether replay-retry clears the dedupe gate for #6704623.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794299508627269
- Monitor: https://app.datadoghq.com/monitors/302511456
- Earlier records: Monitors/2026-11-07-dedupe-silent-publish-drop-warn-2020z.md, Monitors/2026-11-07-dedupe-silent-publish-drop-triggered-1905z.md, Monitors/2026-09-23-dedupe-silent-publish-drop-handled-minus-outcomes.md
