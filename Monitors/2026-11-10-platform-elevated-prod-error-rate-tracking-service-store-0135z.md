---
tags: [datadog-triage]
date: 2026-11-10
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: tracking-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794274606519949"
opened_at: "2026-11-10T01:35:37Z"
severity_assessed: P4
flapping: true
outcome: real_minor
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# Error-rate monitor tripped by 24 tracking-service Firestore store failures in a 6 s burst at 01:35Z, all retried by Pub/Sub; not Snap

## Fired
Monitor 180072217 (more than 2 error-level `domain:fuse` log lines in 2 minutes, Terraform-managed), Triggered 01:35:37Z, Slack post 01:36:46Z (parent ts 1794274606.519949, no replies when read). The Datadog event stream shows it Recovered at 01:37:37Z. Not the Snap slot_timeout cause of 9 Nov.

## Investigation
- Monitor query run via analyze_datadog_logs 01:25-01:45Z, grouped by minute/service/businessId/failureMode/transient/exhausted: 24 matches, all tracking-service, all in the 01:35 minute (01:35:02.501Z to 01:35:08.009Z), message "store failed; nacking for redelivery", recordType sales_order, topic create_record_request, 24 distinct event ids, error text "InvalidArgument: The referenced transaction has expired or is no longer valid". No businessId, failureMode, transient or exhausted attributes on these lines. Nothing else matched.
- Same filter with no monitor exclusions, error/warn/critical, 01:25-01:50Z: no snap_adapter lines, no snap-polling 401s, no shopify-connector errors. Warn-only, unrelated to the trip: dedupe_service "Record dropped" 631, snap-polling-service "Consignment StU not found" 385 and "Stock movement dropped" 70, config-service "Entity not found" 29, shopify-connector "DDP rules unavailable" 29 / "more than one fulfillment order" 13, snap-polling "Withholding confirmation" 7 (01:25-01:40Z). No error-level Fuse prod log after 01:35:09Z up to about 01:41Z.
- Cloud Run `gcp.run.request_count{service_name:tracking-service-api-prod}`: 5xx 3 (01:35 bin) + 21 (01:36 bin) = 24, 4xx 0; 5xx was 0 in every bin 01:20-01:34.
- Pub/Sub `tracking-service.prod.create_record_request.sales_order.v1.sub` push_request_count: 24 `unreachable_5xx_error_500`; ack_204 195 + 3 = 198 in the 01:36/01:37 bins. dedupe_service "Incoming record received" in the 01:35 minute: PURDYFIGG 188, SAIRA 6, ESCENTRIC 2, ESCENTRICPL 2 = 198. The 01:30 wave: 210 incoming, 204 + 6 = 210 acked, no 5xx. So the 198 records of the 01:35 wave all show an ack alongside the 24 initial 500s; this is an aggregate, not per-event proof.
- `num_undelivered_messages` max over `tracking-service.prod.*`: 0 at 01:33-01:35, 2 at 01:36 and 01:37 (later bins not yet available). `tracking-service.prod.*.dlt.sub` max 0 through 01:37.
- Firestore `gcp.firestore.api.request_count{api_method:commit}` (project bifrost-prod-global1): `resource_exhausted` 4 (01:35 bin) and 44 (01:36 bin); `invalid_argument` 4 and 44, the same counts; `aborted` 0; 0 of both in every bin 01:25-01:34. Same pairing earlier: 4 and 4 in the 00:21 bin, with 2 matching error lines at 00:20:09Z. `fuse.tracking.store.errors` reads 8 at 01:35 against 24 log lines (not reconciled, as in the 6 Nov record).
- Waypoint tracking-service known-context (verified 2026-10-15, entry dated 2026-11-06, not re-verified against source): Firestore index-write RESOURCE_EXHAUSTED surfaced as "transaction has expired" because the Commit retry reuses the dead transaction id; fixed by #18 (exempt unqueried fields from indexing), "0 in 48 h". The commit codes above are consistent with that mechanism. The "0 in 48 h" claim is not what the logs show now: tracking-service error logs since 2026-11-06T14:33Z by day: 6 Nov 7 (Aborted contention), 7 Nov 4 Aborted + 2 "transaction has expired", 8 Nov 1 Aborted + 1 Unavailable, 9 Nov 1 Unavailable, 10 Nov 26 "transaction has expired" (2 at 00:20Z, 24 at 01:35Z). Pre-fix bursts for scale: 536 (09h) and 486 (11h) error lines on 6 Nov.
- Deploys: GitHub deployments API for gfs-bifrost/tracking-service, terraform-prod: a97baca success 2026-11-06T17:58:17Z (the version tag on the error lines); e967e19 created 2026-11-09T11:09:44Z, latest status `waiting`. No deploy status change near 01:35Z.
- Flapping: events API (source:alert, monitor 180072217, 9 Nov 01:00Z to 10 Nov 01:45Z) shows 7 Triggered/Recovered pairs: 15:21:37, 16:06:37, 16:31:37, 16:36:37, 18:31:37, 20:01:37 (recovered 20:20:37) on 9 Nov, and 01:35:37 (recovered 01:37:37) on 10 Nov. The 9 Nov ones were the Snap ilg005 slot_timeout waves (existing records); this one is a different cause.
- Snap (read-only, because the alert was raised alongside last night's ilg005 trouble; the matched logs are not Snap): `snap.request.latency.avg` for ilg005 in 10-minute bins 00:00-01:40Z 469-928 ms, max `snap.request.latency.max` 2,328 ms (01:00 bin); `snap.poll.request.latency.avg` 60-233 ms on ilg001-005. snap_adapter logged no circuit/breaker/slot line 20:20Z to 01:45Z. `snap.slot_wait.count` returned no series. Two cheap reads against ilg005 with the PURDYFIGG connection (a SHIPSTATUS snap-lookup and a one-row shipments search) returned success; response time is not measurable through the MCP. Snap latency monitor 179927768 reads OK, muted_until_ts 1794306393 = 2026-11-10T10:26:33Z.
- Snap failures in the period: snap_adapter error/warn since 19:00Z 9 Nov: 20:00 hour only transient (slot_timeout, circuit_open, snap_api_error, all `exhausted:false`, PURDYFIGG/STUBBLE/PHLUR); then two non-transient lines, DOCKBAY schema_validation 22:02:56Z and PHLUR snap_api_error 23:52:01Z; none from 00:00Z. No "Entity already exists in SNAP" line after 21:15:13Z. No order in this alert failed transiently in snap_adapter, so the missing-attachment check had nothing to run on.
- Maintenance/: newest record 2026-11-04 (emergency patch 5 Nov 10:00Z); none covers 9-10 Nov. #bifrost-general (C098LD5PS95) since about 11:00Z 9 Nov: only the Support Bot attachment-backfill post at 22:20Z, no ILG notice. #snap-wms (C0CCB86QTR9): newest message 8 Nov 16:55Z.
- replay-service (production): createdAt 2026-11-10 total 0. createdAt 2026-11-09 sales_order: 5 (DOCKBAY UK-914467 22:02:57Z and UK-914263, ESCENTRIC 15337 and 15335, SAIRA #37929; all data validation at wms_precheck / snap_api). PHLUR purchase_order TO004859 held from 23:52:02Z ("No Product Found on 4 lines"). No mention of UK-914467 or TO004859 in Monitors/, Support/, Tasks/ or public Slack search. Unrelated to this alert.
- Jira (FUSE, text ~ tracking-service + Firestore/transaction expired/RESOURCE_EXHAUSTED): no matching defect found.

## Not established
- Why Firestore returned RESOURCE_EXHAUSTED on commit for database `tracking-service` at 00:20Z and 01:35Z (limit, hot document or index-write throttling): the metric gives the codes, not the cause. No Firestore quota or key-visualizer data was read.
- Which businesses/orders the 24 nacked events belong to: the lines carry only an event id and no tool maps an event id to a customer ref. The wave was 188 PURDYFIGG of 198 records, but that does not say which records failed.
- Per-event completion: tracking-service writes no success log; completion rests on the aggregate (198 acks for 198 records, 0 on the dead-letter subscriptions to 01:37Z, no repeat error line to about 01:41Z). Pub/Sub and Firestore state after about 01:38Z was not yet available.
- Why 2 RESOURCE_EXHAUSTED commits per failed event on average (48 vs 24 lines), and the `store.errors` 8 vs 24 gap.
- That the 6 Nov mechanism in Waypoint is the cause now (not re-verified against source).
- Whether the ILG mailbox holds a notice (Outlook not read). Pinned post in #bifrost-general not read (no pin tool). Whether ilg005 shares businesses with others: lookup-snap-instance returned businessCount 0 for ilg005 although get-snap-connection puts PURDYFIGG there. 7-day ilg005 history not queried (Snap step not triggered by the matched logs).
- Attachments for the 5 shipments left unchanged last night were not re-read.

## Outcome
Real minor, P4, not escalated. tracking-service answered 500 to 24 Pub/Sub pushes in 6 s when Firestore commits failed (RESOURCE_EXHAUSTED then INVALID_ARGUMENT, 48 each over 01:35-01:36Z), the monitor correctly counted 24 error lines, and Pub/Sub redelivery appears to have completed (198 acks for 198 records, nothing dead-lettered, nothing held in replay for 10 Nov). No Snap involvement; nothing here was not submitted to Snap. Recurs after the 6 Nov index-exemption fix: largest burst since (24 vs at most 7), 26 "transaction has expired" lines in 100 minutes. A tracking-service defect ticket is warranted (none exists); not filed here, needs a go-ahead via create-defect. Draft reply returned to the watcher, which posts it.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794274606519949
- Monitor: https://app.datadoghq.com/monitors/180072217
- Related: Monitors/2026-11-06-tracking-service-push-5xx-rate-high-1126.md, Monitors/2026-11-07-platform-elevated-prod-error-rate-shopify-duplicate-attempt-tracking-contention-1651.md, Engineering/tracking-service/known-context.md
