---
tags: [datadog-triage]
date: 2026-11-06
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: tracking-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793956303668759"
opened_at: "2026-11-06T09:10:37Z"
severity_assessed: P3
flapping: true
outcome: real_minor
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# 09:10Z firing: 225 tracking-service "store failed; nacking for redelivery" errors in 35s (same shape as 00:55Z, about 56x the volume)

## Fired
More than 2 error-level domain:fuse logs in 2m (monitor 180072217, alert post 09:11:43Z). Shortened re-check of known patterns, run as a read-only subagent (watcher posts the reply).

## Investigation
- Matching errors from 09:00Z (analyze_datadog_logs, the monitor's query minus the PURDYFIGG exclusion): tracking-service `store failed; nacking for redelivery` x225, config-service `Dependency connection failed` x1. Nothing else.
- tracking-service errors by second: 09:10:13Z to 09:10:20Z (190 lines, peak 76 at 09:10:18Z), a tail of 1 to 9 per second 09:10:26Z to 09:10:34Z, then single lines at 09:10:42Z, :43, :44, :48. 0 tracking-service error or warn logs from 09:11Z to about 09:14Z.
- Same shape as 00:55Z: version b12d0a6, revision tracking-service-api-prod-00014-khz, recordType sales_order, topic create_record_request, error `rpc error: code = InvalidArgument desc = The referenced transaction has expired or is no longer valid.` (search_datadog_logs, 3 sample rows). 191 distinct error strings (each carries an event id) across the 225 lines, so 34 lines repeat an event id.
- Context metrics: `fuse.tracking.events.ingested` 1155 in the 09:10 minute (587, 0, 14, 33, 8, 889, 148, 0, 4, 0 in the 09:00 to 09:09 minutes), `fuse.tracking.store.errors` 151 in the 09:10 minute, 0 in 09:11 and 09:12.
- Config-service lead: 1 "Dependency connection failed" line since 09:00Z (the 08:23Z pattern, not what tripped this).
- 5xx: logs with http.status_code / status_code / statusCode / response.status / error.status 500-599 prod since 09:00Z: 1 line, service ccp-sync-worker (not tracking-service, not domain:fuse-examined). Cloud Run `gcp.run.request_count` for tracking-service-api-prod, 5xx class: 0 in every bin 09:00 to 09:09; the 09:10 bin was not yet in the series when read, so that minute is not covered by this metric.
- Backlog: `max:gcp.pubsub.subscription.oldest_unacked_message_age` over all `*prod*` subscriptions 09:00Z onward, max 17s (the subscription holding it was not identified; 80 of 152 rows read were all 0). tracking-service.prod.create_record_request.sales_order.v1.sub: 0 in every bin 09:05 to 09:08; for the 08:50 to about 09:11 window max age 0 and max undelivered 0 on every tracking-service subscription except tracking-service.prod.create_record.sales_order.v1.sub (1 message, 1s) and tracking-service.prod.create_acknowledge.sales_order.v1.sub (2 undelivered, age 0). Dead-letter sub tracking-service.prod.create_record_request.sales_order.v1.dlt.sub undelivered 0 in the bins read.
- Held records: replay-list-failures (production) createdAt 2026-11-06 total 21, newest five all PURDYFIGG goods_out_confirmation created 07:06:40Z (same as the 08:23Z record); for sales_order, purchase_order, master_data the newest held failure is 2026-11-05T17:20:05Z (WILDSMITH, snap-adapter wms_precheck). Nothing new from this alert, nothing held that Fuse could not submit to Snap since.
- Channel read (slack_read_channel from 08:23Z): alert posts are 08:24:43Z (1793953483.806379, 1 reply at 08:26:30Z) and 09:11:43Z (1793956303.668759, no replies). No other unreplied thread since 08:23Z.

## Not established
Whether the nacked events were redelivered and stored (a nacked event id was searched in tracking-service logs from 09:00Z and found only in the error line; 34 repeat lines show some were redelivered and failed again; the end state of the 191 events was not read). Why the transactions expired (no Firestore or GCP logs readable); the coincident ingest spike (1155 events in the minute) is a lead, not a finding, since 889 in the 09:05 minute produced no errors. Dead-letter depth during the 09:10 minute (metric bins read ended at 09:07, and the broader window query showed 0 but is coarser). Cloud Run 5xx for the 09:10 minute. Which subscription held the 17s age.

## Outcome
Real minor, P3. Same tracking-service store-write error as 00:55Z (4 lines then), 191 distinct events this time, over in about 35s, nothing since 09:11Z. No backlog, no dead-letter depth seen, no held record from it, no 5xx found. The monitor counts the error-level line, so any burst of 3 trips it. Not ticketed here; the volume increase over 00:55Z (and 231 lines on 30 Oct to 4 Nov per the 00:55Z record) strengthens the earlier lead for tracking-service owners: look at transaction duration on the store write and how a burst is batched.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793956303668759
- Monitor: https://app.datadoghq.com/monitors/180072217
- Prior records: Monitors/2026-11-06-platform-elevated-prod-error-rate-tracking-service-store-0055.md, Monitors/2026-11-06-platform-elevated-prod-error-rate-config-service-postgres-0823.md
