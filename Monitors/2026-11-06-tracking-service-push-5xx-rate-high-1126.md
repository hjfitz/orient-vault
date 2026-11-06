---
tags: [datadog-triage]
date: 2026-11-06
monitor: "[FUSE][Tracking Service] Push 5xx rate high"
service: tracking-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793964387268909"
opened_at: "2026-11-06T11:26:04Z"
severity_assessed: P3
flapping: true
outcome: real_minor
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# Push 5xx rate high: 486 push 500s from one 51s tracking-service store-write burst at 11:20Z, Firestore commit RESOURCE_EXHAUSTED in the same minutes, nothing since 11:21:03Z

## Fired
Composite 332917924 (`332917918 && 332917914`, Terraform-managed), Triggered 11:26:04Z (Slack post 11:26:27Z, ts 1793964387.268909, no replies when read). Inputs: (Cloud Run 5xx minus `fuse.tracking.push.held`) over all requests to tracking-service-api-prod in 10m, above 5% and above 5. All three monitors read Alert at about 11:30Z (search_datadog_monitors). Same monitor fired 09:16Z/09:17Z (threads 1793956586.698649, 1793956647.214049, recovered 09:28:04Z per the events API).

## Investigation
- 5xx count and minutes: `gcp.run.request_count{service_name:tracking-service-api-prod}` by response_code_class, 1-minute bins: 5xx 485 in the 11:21 bin and 1 in the 11:22 bin (all response_code 500), 0 in every other bin 10:50 to 11:24 (series ends 11:24). Bins sit one minute after log times. Total 486.
- Error: analyze_datadog_logs (service:tracking-service @environment:prod status:error, 11:10Z on): 486 lines, all `store failed; nacking for redelivery`, 486 of 486 with `rpc error: code = InvalidArgument desc = The referenced transaction has expired or is no longer valid.`, 11:20:12.487Z to 11:21:03.038Z (485 in the 11:20 minute, 1 in 11:21). By topic: create_record_request 466 lines, create_acknowledge 12, create_record 8, all recordType sales_order. 372 distinct event ids.
- Same version/revision as 09:10Z: every one of the 486 lines is version b12d0a630c68596cd08de1afb501b91b9f43ed45, revision tracking-service-api-prod-00014-khz (group by version, revision_name, topic). Same error text as the 09:10 and 09:15 bursts per the earlier records.
- Firestore side (new, `gcp.firestore.api.request_count{project_id:bifrost-prod-global1}` by response_code, api_method, database_id): all `commit` on database_id `tracking-service`. Per database_id series, resource_exhausted 39 (11:20), 426 (11:21), 21 (11:22) = 486, and invalid_argument 51, 413, 22 = 486, equal to the 486 error lines; both are 0 in every other bin from 11:00 to 11:25. Over 00:51Z to 11:26Z the same two codes are non-zero only at 00:5x (8 summed over both series, so 4 per series, matching the 4 lines then), 09:10 to 09:17 (1,072 summed, 536 per series, matching 225 + 311) and 11:20 to 11:22. The series carries each count twice (database_id N/A and tracking-service), so unaggregated sums are 2x. Firestore document write_count at 11:21 was 1,440, not above earlier batch minutes (1,526 at 11:01, 1,861 at 11:06, 1,714 at 11:11, 1,274 at 11:16).
- Today's bursts: 4 (00:55Z), 225 (09:10Z), 311 (09:15Z), 486 (11:20Z): growing, each one coinciding with the Firestore commit codes above. This one was a single 51s burst (09:10 to 09:16 was two).
- 5xx share: 485 of 2,123 requests (22.8%) in the 11:21 bin; 486 of 3,944 (12.3%) over the 11:16 to 11:24 bins (2xx 3,458 + 5xx 486; the 11:25 and later bins were not in the series). Monitor threshold 5% and 5 requests. For 09:16Z the earlier record has about 5.0% (225 of 4,496), so this is a larger share.
- Ongoing: no tracking-service log of any status from 11:21:04Z to about 11:29Z (analyze_datadog_logs, 0 rows); Cloud Run 5xx 0 in the 11:23 and 11:24 bins; the next push wave (dedupe_service "Incoming record received" 1,476 in the 11:25 to 11:29 minutes, `fuse.tracking.events.ingested` 726 in the 11:25 minute and 176 at 11:26) produced no error line and `fuse.tracking.store.errors` 0 for 11:22 to 11:27. The composite is still Alert only because the 10m window still holds the burst.
- Redelivery: attempts per event id (distinct event ids, failed lines): 268 events once, 94 twice, 10 three times, none four or more (dead-letter at 5 per the service doc, not re-read). No failure line after 11:21:03Z.
- Acked vs published, aggregate: tracking `create_record_request.sales_order.v1.sub` push responses ack_204 62 (11:20), 1,400 (11:21), 141 (11:22), 1 (11:23) = 1,604; unreachable_5xx_error_500 417 (11:21) + 49 (11:22) = 466 (equals the 466 create_record_request error lines); `ack_message_count` 62 + 1,434 + 108 = 1,604 for 11:20 to 11:22. dedupe_service "Incoming record received" for the same wave: 1,600 (11:20 minute) + 3 + 1 = 1,604. Earlier clean wave, topic published vs sub acked 11:11 to 11:16: 3,536 vs 3,536. The topic publish metric (`send_message_operation_count`) had not reached 11:20 when read (series ends 11:18), so the dedupe count is the proxy for published.
- Dead letters: `num_undelivered_messages` max 0 on every `tracking-service.prod.*.dlt.sub` for 11:18 to 11:22 (series ends 11:22); `dead_letter_message_count` returned no series.
- Held records: replay-list-failures (production): newest overall 5 PURDYFIGG goods_out_confirmation at 10:50:40 to 10:50:41Z (Shopify fulfilment order CLOSED, confirmation.delivery_shopify), none newer; useCase sales_order createdAt 2026-11-06: total 0. `fuse.tracking.push.held`: no series, so nothing is subtracted. Nothing Fuse could not submit to Snap; no Snap link, so maintenance check and Step 2b not applicable.
- Sample of affected orders: not possible. The error lines carry only an event id. tracking-lookup-refs (production, PURDYFIGG) with the 10 events that failed three times (all 10 chosen as the highest-retry set) returned found:false for all 10, and tracking-get-shipment by id for one of them returned no shipment, so event ids are not customer refs and I could not map them to orders. Sample size 0. A search of one event id across all prod logs 11:00Z on returned 0 lines.
- What changed around 11:20Z: GitHub deployments API for gfs-bifrost/tracking-service: latest 2026-11-05T15:10:41Z (b12d0a6, terraform-prod), previous 2026-10-19; nothing since. Cloud Run `instance_count` for tracking-service-api-prod: only revision 00014-khz, 2 to 3 instances 10:30 to 11:24, same 3-instance peak at each 5-minute wave as clean waves. Datadog get_change_stories (tracking-service, prod, 5 Nov 12:00Z to 6 Nov 11:30Z): none. Batch size did not grow: dedupe incoming per wave 1,815 (11:10), 1,720 (11:15), 1,604 (11:20), 1,476 (11:25). Only deploy post in the channel since 11:15Z is snap-adapter at 11:16:43Z (dda54bf), a different service; any link is not established. No Cloud Run or Firestore incident event was read (no tool for GCP status).
- Slack: parent 1793964387.268909 in C099WKQTE8G, no replies. The same burst was already answered in the backlog thread 1793964267.215019 (bot reply, P3, no Firestore detail).
- Monitor history: composite fired 09:16Z Warn, 09:17Z Alert, recovered 09:28:04Z, Triggered 11:26:04Z (search_datadog_events source:alert, 4 events today); earlier records show 00:59Z, 1 Nov, 29 Oct, 20 Oct. Chronic and recurring.

## Not established
- Why Firestore returned RESOURCE_EXHAUSTED on `commit` for database `tracking-service` (limit, hot-document contention, or something else): the metric shows the codes, not the reason. No Firestore quota or database-level data was read.
- Why these particular waves (00:55, 09:10, 09:15, 11:20) fail and others do not, and why the bursts grow. Batch size and write volume do not separate them.
- Whether each nacked event was finally stored: prod tracking-service writes no success log, and event ids could not be mapped to orders (sample size 0). The aggregate (1,604 acked = 1,604 in the wave via dedupe, no failure line after 11:21:03Z, nothing held) points to completion but is not per-event proof.
- Dead-letter depth and Pub/Sub state after about 11:22 to 11:23Z, Cloud Run 5xx after the 11:24 bin (metrics lag about 4 to 5 minutes); `store.errors` reads 215 (214 + 1) against 486 lines, not reconciled; when the monitor recovers.
- Whether the snap-adapter deploy at 11:16:43Z has any connection.

## Outcome
Real minor, P3, not escalated. tracking-service answered HTTP 500 to 486 Pub/Sub pushes in 51s when store writes failed, coinciding exactly with 486 Firestore commit RESOURCE_EXHAUSTED responses on its database. Same error, version and revision as 09:10Z; larger (486 vs 225 + 311). All messages in the wave were acked, nothing dead-lettered or held, no error since 11:21:03Z. The monitor is correct, not mistuned. A defect ticket for tracking-service owners is warranted (Firestore commit RESOURCE_EXHAUSTED on four waves today, growing) but was not filed here; it needs a go-ahead via create-defect. Draft reply returned to the watcher, which posts it.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793964387268909
- Monitor: https://app.datadoghq.com/monitors/332917924
- Related: Monitors/2026-11-06-tracking-service-push-5xx-rate-high-0916.md, Monitors/2026-11-06-pubsub-backlog-building-tracking-service-store-failed-1123.md, Monitors/2026-11-06-platform-elevated-prod-error-rate-tracking-service-store-0910.md
