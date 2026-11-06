---
tags: [datadog-triage]
date: 2026-11-06
monitor: "[FUSE][Tracking Service] Push 5xx rate high"
service: tracking-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793956586698649"
opened_at: "2026-11-06T09:16:04Z"
severity_assessed: P3
flapping: true
outcome: real_minor
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# Push 5xx rate high: 536 push 500s in two 5-minute-cadence bursts (09:10Z and 09:15Z), same transaction-expired store error, nothing since 09:16Z

## Fired
Composite 332917924 (`332917918 && 332917914`): Warn 09:16:04Z, Alert 09:17:04Z. Ratio input: (Cloud Run 5xx minus `fuse.tracking.push.held`) / all requests to tracking-service-api-prod over 10m > 5%. Count input: the same numerator > 5 in 10m. Both are on `gcp.run.request_count{service_name:tracking-service-api-prod}`, so the monitor counts every request to the service, not only the push route. Terraform-managed (`managed-by:terraform`).

## Investigation
- What the 5xx are: `gcp.run.request_count` for tracking-service-api-prod, 08:50Z on, by response code: 225 x HTTP 500 in the bin labelled 09:11 (0 in every other bin up to it), and 5xx class 308 in the 09:16 bin plus 3 in 09:17 (re-read at 09:21Z). That is 536 5xx in total, equal to the 536 tracking-service `store failed; nacking for redelivery` error logs since 09:00Z (analyze_datadog_logs: 536 lines, 451 distinct event ids, all 536 carry `The referenced transaction has expired or is no longer valid`). Cloud Run bins sit about a minute after the log times.
- Endpoint and caller: per the Fuse MCP (`lookup-endpoints tracking-service`), `POST /events/v1/{topic}/{recordType}` is the Pub/Sub push route, invoked only by the tracking-service-push-prod SA, and answers 500 on a store error. No request-level log or span for the 5xx exists in Datadog (search_datadog_logs and search_datadog_spans, 5xx, since 09:00Z: 0), so the route per request is from the doc, the 1:1 count match above is from data.
- Totals: the 2xx class (204) was 2,026 in the 09:11 bin and 2,077 in the 09:16 bin, so about 10% of requests in the first batch and about 13% in the second were 500 (computed from those bins). Over the 10m at 09:16:04Z it was about 5.0% (225 of 4,496), right at the 5% line.
- Cadence: Cloud Run 2xx shows a push batch of 1.9k to 2.1k requests every 5 minutes (08:51, 08:56, 09:01, 09:06, 09:11, 09:16 bins). The 09:05 batch had no errors. The 09:10 and 09:15 batches did. The 09:20 batch (`fuse.tracking.events.ingested` 732, `fuse.tracking.store.errors` 0 in 09:20 and 09:21, no tracking-service error log 09:17 to 09:21:32Z) did not.
- 09:10 burst: 225 lines, 09:10:13 to 09:10:48Z, 191 distinct events (see the 0910 record). 09:15 burst: 311 lines (308 in the 09:15 minute, 3 in 09:16) from 09:15:12Z to 09:16:10Z; by topic: create_record_request sales_order 287, create_record sales_order 11, create_acknowledge sales_order 11, confirmation_ready goods_out 1, confirmation_made goods_out 1. Same version b12d0a6, revision tracking-service-api-prod-00014-khz.
- Same cause as 09:10Z: yes by error text and service. The earlier 09:14 reply's "no 5xx found" only covered bins to 09:09, so it missed the 225 (sibling follow-up posted the correction at 09:19Z).
- Retries: per event id, failures logged since 09:00Z: 1 x 377, 2 x 64, 3 x 9, 4 x 1 events; none logged five times.
- Backlog and DLT: `num_undelivered_messages` on tracking-service.prod DLT subs 0 in every bin 09:08 to 09:17; main prod subs max 41 undelivered, oldest unacked 24s in the 09:12, 09:13, 09:17 and 09:18 bins; `dead_letter_message_count` returned no series. Metrics lag about 4 minutes, so the 09:15 burst is only partly covered.
- Hold mode: `fuse.tracking.push.held` returned no series (08:55 to 09:21Z), so nothing is excluded by the monitor's hold-mode subtraction.
- Held records: replay-list-failures (production, all record types, newest first): newest is 2026-11-06T07:06:40Z (PURDYFIGG goods_out_confirmation, Shopify fulfilment order closed), nothing since. No record Fuse could not submit to Snap is held from this.
- Deploy: version b12d0a6 first logged 2026-11-05T15:17:52Z; the previous version 389adbc logged from 2026-10-30T09:33Z. `store failed` errors by day (14d): 12 on 24 Oct, 50 on 26 Oct, 231 on 1 Nov (older version), 540 on 6 Nov. So the errors predate the current revision.
- Flapping: the composite or its inputs fired on 20 Oct (09:21Z record), 29 Oct 09:13Z (ratio input), 1 Nov 01:01Z (composite, recovered 01:08Z), 6 Nov 00:59Z (inputs, recovered 01:06:58Z) and now 09:16Z. Two episodes in the last 10 hours.
- Slack: parent ts 1793956586.698649 in C099WKQTE8G, no replies before this triage. 09:11:43Z alert (180072217) is a separate thread with one reply (09:14:39Z) about the same burst.

## Not established
That any individual nacked event was applied after redelivery (prod tracking-service writes no success log; the 09:10 events are covered by the sibling check, the 09:15 events were not checked per event); Pub/Sub state and DLT depth after about 09:17Z (metric lag), including after the 09:15 burst fully settles; the DLT max-delivery-attempts setting (the doc says 5); why the transactions expire and why only two of the last six batches failed (the 09:10 batch was 1,960 shopify-connector sales orders per the sibling check; volume alone does not explain it, since the 09:05 batch of 889 and the 09:20 batch of 732 were clean); when the monitor recovers (still Alert at 09:17:04Z, the 10m window rolls off about 09:26Z).

## Outcome
Real minor, P3. The 5xx are tracking-service answering HTTP 500 to Pub/Sub pushes when the Firestore store write fails with an expired transaction (`store failed; nacking for redelivery`), so Pub/Sub redelivers. Two bursts (09:10Z with 225 and 09:15Z with 311), same error as 00:55Z, none at 09:20Z. No DLT depth, backlog peaked at 41 messages and 24s, nothing held in replay-service since 07:06Z. Not escalated and not ticketed here. For tracking-service owners: the errors repeat in the 5-minute push batches and have been present since 24 Oct, look at transaction duration on the store write and how a batch is split. The monitor is correct, not mistuned: it fired on real 500s.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793956586698649
- Monitor: https://app.datadoghq.com/monitors/332917924
- Prior records: Monitors/2026-11-06-platform-elevated-prod-error-rate-tracking-service-store-0910.md, Monitors/2026-11-06-platform-elevated-prod-error-rate-tracking-service-store-0055.md, Monitors/2026-10-20-tracking-push-5xx-rate.md
