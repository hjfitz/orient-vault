---
tags: [datadog-triage]
date: 2026-11-06
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: tracking-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793926605353019"
opened_at: "2026-11-06T00:55:37Z"
resolved_at: "2026-11-06T01:01:00Z"
minutes_spent: 6
severity_assessed: P4
flapping: true
outcome: real_minor
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# 00:55Z firing: 4 tracking-service "store failed; nacking for redelivery" errors (transaction expired); not the config-service Postgres check

## Fired
More than 2 error-level domain:fuse logs in 2m. A fourth distinct cause for this monitor in 4 days. The 23:29Z lead (config-service Postgres dependency check) is not what fired.

## Investigation
- Monitor query run as written (00:20Z onwards, grouped by service and message, analyze_datadog_logs): 4 matches, all tracking-service `store failed; nacking for redelivery`, version b12d0a6, revision tracking-service-api-prod-00014-khz, recordType sales_order, topic create_record_request. Timestamps 00:50:03Z, 00:55:03Z, 00:55:07Z x2 (00:55:07 pair tripped the 2m window with the 00:55:03 one). Error on each: `rpc error: code = InvalidArgument desc = The referenced transaction has expired or is no longer valid.` for four distinct event ids (20350869244099672, 20350748780097922, 22441567977174752, 22447670587720915). No businessId on the logs.
- All prod error-level logs (not just domain:fuse) from 00:30Z: the same 4 only, no other service. 0 error-level domain:fuse logs after 00:57Z at query time (about 01:00Z).
- Postgres lead: 0 "Dependency connection failed" logs (any service) since 23:30Z. min fuse.postgres.up for config-service = 1 in all 18 five-minute bins 23:30Z to 00:59Z; fuse.postgres.latency.max 36 to 254ms. 0 config-service 5xx logs since 23:30Z.
- Recurrence: tracking-service logged 235 `store failed` errors in 7d. 231 were on the previous version 389adbc inside 30 Oct to 4 Nov (one bucket, exact hours not resolved), 4 are today on b12d0a6. 0 error-level tracking-service logs between 4 Nov 00:00Z and 6 Nov 00:00Z. Metric fuse.tracking.store.errors: 54 on 1 Nov, 3 today (metric counts differ slightly from log counts). Metric fuse.tracking.events.ingested: 33 and 42 in the 00:50 and 00:55 bins, 40k to 71k per day, so 4 errors is a tiny fraction.
- Impact: Pub/Sub oldest_unacked_message_age for tracking-service.prod.create_record_request.sales_order* was 0s in all 18 bins 23:30Z to 00:59Z, so no backlog built up. Per Fuse MCP, tracking-service answers 500 on a store error so Pub/Sub redelivers, dead-lettering after 5 attempts; the 4 event ids were not found in any log after the nack (searched from 23:00Z), so whether they were redelivered and stored is not established. tracking-service is a read-model of shipment status (fuse-ui tracker), not the order pipeline.
- Held records: replay-list-failures (production) createdAt 2026-11-06: 0. Newest held failure overall is 21:40Z on 5 Nov (PURDYFIGG goods_out_confirmation, Shopify CLOSED fulfilment orders), already known; no sales_order/purchase_order/master_data failure created since. No record held that Fuse could not submit to Snap.
- Flapping: monitor has fired 8 times since 2 Nov 16:36Z (7 per the 23:29Z record, plus this one), several distinct causes.

## Not established
Why the transactions expired (contention, slow commit, Firestore-side event); no Firestore or GCP events/logs were readable. Whether the 4 nacked events were redelivered and stored, or reached the dead-letter subscription (dead_letter_message_count returned no data; the .dlt.sub was not read). Whether the 4 Nov-30 Oct burst of 231 shared this cause beyond the identical message. Cloud SQL logs/events for the config-service Postgres lead were not read; the check is healthy now, so not pursued.

## Outcome
Real minor, P4. Four transient store-write errors on tracking-service's sales_order create path; no backlog, no held records, no 5xx on config-service, no other service erroring. The monitor counts the error-level log line, so 3 in 2m trips it. Not ticketed; if it recurs, tracking-service owners should look at transaction duration on the store write.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793926605353019
- Monitor: https://app.datadoghq.com/monitors/180072217
- Prior: Monitors/2026-11-05-platform-elevated-prod-error-rate-config-service-postgres-2329.md
