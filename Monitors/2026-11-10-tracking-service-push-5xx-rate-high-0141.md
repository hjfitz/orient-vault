---
tags: [datadog-triage]
date: 2026-11-10
monitor: "[FUSE][Tracking Service] Push 5xx rate high"
service: tracking-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794274888025569"
opened_at: "2026-11-10T01:41:04Z"
severity_assessed: P3
flapping: false
outcome: real_minor
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# Push 5xx rate high: 24 tracking-service pushes answered 500 in a 6 s Firestore store-write burst at 01:35Z; nothing since, aggregate shows all acked

## Fired
Composite 332917924 (`332917918 && 332917914`, Terraform-managed, priority 2) Triggered 01:41:04Z; Slack post 01:41:28Z, ts 1794274888.025569 in C099WKQTE8G, no replies when read at 01:46Z. Inputs: (Cloud Run 5xx on `tracking-service-api-prod` minus `fuse.tracking.push.held`) over 10 minutes, count > 5 and ratio > 5%. All three monitors read Alert at 01:46Z (search_datadog_monitors). Same event as the [FUSE][Platform] error-rate alert at 01:35Z (thread 1794274606.519949, triaged separately): `@domain:fuse status:error @environment:prod` 01:30Z on returns only tracking-service, 24 lines in the 01:35 minute.

## Investigation
- What tripped it: `gcp.run.request_count{service_name:tracking-service-api-prod}` 5xx 3 (01:35 bin) + 21 (01:36 bin) = 24; 4xx 0; 5xx 0 in every other bin 00:57-01:34 except 2 in the 00:20 5-minute bin. By my sum of per-minute bins 01:31-01:40: 2xx 401 (199 at 01:31, 21, 181) plus 24 5xx = 425, so 5.6%, count 24 against > 5. The monitor's own evaluated value was not read. `fuse.tracking.push.held` returned no series in the last 3 h, so nothing was subtracted (no hold).
- Why it fired at 01:41 rather than 01:36: not established (Cloud Run metric lag, about 4-5 min, is a lead).
- What the 5xx are: Pub/Sub push responses (`gcp.pubsub.subscription.push_request_count`, non-ack across all of project bifrost-prod-global1 since 01:15Z): 24 `remote_server_5xx` on `tracking-service.prod.create_record_request.sales_order.v1.sub`, no other subscription (so not dedupe or collector). One further earlier 5xx in that series does not match any Cloud Run 5xx bin (unreconciled).
- Error logs: analyze_datadog_logs `service:tracking-service project_id:bifrost-prod-global1 status:error`, per minute for 3 h: 00:20 (2) and 01:35 (24), nothing else. The 24: 01:35:02.501Z to 01:35:08.009Z, all "store failed; nacking for redelivery", topic create_record_request, recordType sales_order, error `InvalidArgument: The referenced transaction has expired or is no longer valid`, version a97baca, revision tracking-service-api-prod-00016-tcd. No error line from 01:35:09Z to about 01:46Z.
- Dependency: `gcp.firestore.api.request_count{database_id:tracking-service}` per minute: `resource_exhausted` 2 (01:35) + 22 (01:36) = 24 and `invalid_argument` 2 + 22 = 24, `aborted` 0, 0 of both 01:20-01:34. So the 24 failing pushes line up with 24 Firestore RESOURCE_EXHAUSTED responses, surfacing as "transaction has expired", the same shape as the 6 Nov bursts. Firestore, not Mongo: tracking-service logs carry version a97baca; GitHub deployments (terraform-prod) for gfs-bifrost/tracking-service: a97baca success 2026-11-06T17:58:17Z, e967e19 created 2026-11-09T11:09:44Z with latest status `waiting` (never applied); main has Mongo store commits (#26-#32, 9 Nov) that are not deployed. `gcp.run.container.instance_count` by revision over 24 h shows only revision 00016-tcd.
- Deploys / config in the last 24 h: none. get_change_stories (tracking-service, 9 Nov 01:00Z to 10 Nov 01:45Z) returned no stories; GitHub deployments above; one Cloud Run revision for 24 h.
- Baseline, 7 days hourly (default_zero series from 3 Nov): Cloud Run 5xx total 1,068; 4 (6 Nov 00h), 536 (6 Nov 09h), 486 (6 Nov 11h), 7 (6 Nov 16h), 2 (7 Nov 00h), 3 and 1 (7 Nov 16h, 17h), 1 and 1 (8 Nov 18h, 19h), 1 (9 Nov 11h), 2 (10 Nov 00h), 24 (10 Nov 01h). Firestore `resource_exhausted`: 4, 536, 486 on 6 Nov, then 2 (7 Nov 00h), 2 (10 Nov 00h) and 24 (10 Nov 01h); 0 in every other hour. tracking-service error logs by day: 6 Nov 1,026 "transaction has expired" + 7 aborted; 7 Nov 2 + 4 aborted; 8 Nov 1 aborted + 1 unavailable; 9 Nov 1 unavailable; 10 Nov 26 "transaction has expired" (2 at 00:20Z, 24 at 01:35Z). So this is the largest since the 6 Nov index-exemption fix (#18, in prod 15:40Z on 6 Nov), but about 1/20 of the 6 Nov bursts.
- Monitor history (search_datadog_events source:alert, 7 d): Warn 6 Nov 09:16Z, Triggered 09:17Z and 11:26Z, then this one 10 Nov 01:41Z; nothing 7-9 Nov. Recurring, not flapping in the last 24 h.
- Concentration: the 01:35 wave of the `create_record_request` sales_order stream was 198 records by dedupe_service "Incoming record received": PURDYFIGG 188, SAIRA 6, ESCENTRIC 2, ESCENTRICPL 2 (the 01:30 wave 210, the 01:40 wave 184). Failed pushes cannot be attributed to a business: the error lines carry only an event id.
- Retry and loss, aggregate: that subscription's acks for the wave were 195 + 3 = 198 (push_request_count, ack), equal to the 198 incoming records; the 01:30 wave acked 204 + 6 = 210 against 210. `oldest_unacked_message_age` max 0 s on that subscription 01:28-01:43Z, `num_undelivered_messages` max 0 on it and on its `.dlt.sub` through about 01:37Z (later bins not yet available). No tracking-service error line after 01:35:08Z including during the 01:40 wave (184 records published), and the tracker wrote a PURDYFIGG record at 01:45:13Z (tracking-search-shipments, production). This is not per-event proof.
- Customer impact: tracking-get-stats (production) 10 Nov: received 85, in_wms 85, failed 0, delivery_failed 0 so far today; tracking-list-attention (production) oldest rows are 6-7 Oct orders (WMS rejections, overdue despatch, confirmation_failed), unrelated to 10 Nov (attention 14,599 total, 11,950 action lane). Nothing in this alert held or dropped on the evidence read; tracking events for the 24 failed pushes were delayed at most until redelivery, duration not measured.
- Still firing: yes at 01:46Z (composite and both inputs Alert, search_datadog_monitors). Trend: 5xx bins 01:37-01:39 are 0, later Cloud Run bins not yet available (metric lag), no error logs since 01:35:08Z; the 10-minute window should clear as the 01:35-01:36 bins age out, not yet observed.
- Maintenance/: newest records are 2026-11-04 (snap emergency patch, snap test DBs); none covers 9-10 Nov, and none concerns tracking-service or Firestore. #bifrost-general (C098LD5PS95) 9 Nov 07:46Z to now: only the 22:20Z ilg005 attachment backfill post and the go-lives update; no overnight work announced.
- Waypoint: `wp stale tracking-service` shows overview, operations and architecture behind source (20, 8 and 18 commits since 9f01957, all the Mongo store work); known-context is exempt. Read known-context (11-06 entry: Firestore RESOURCE_EXHAUSTED surfacing as "transaction has expired", #18 exempted 9 unqueried fields, "0 in 48 h") and Handovers/2026-11-06-tracking-service-mongo.md (handover closed 9 Nov, Mongo not yet cut over). "0 in 48 h" does not hold now: resource_exhausted 2 on 7 Nov 00h, 2 and 24 on 10 Nov.

## Not established
- Why Firestore returned RESOURCE_EXHAUSTED (quota, hot document, index-write throttling): the metric gives the codes, not the cause; no Firestore quota or Key Visualizer data read. The 6 Nov mechanism matches the error shape but is not confirmed as the cause now.
- Per-event completion of the 24 nacked events, and which business owned them (event ids map to no ref).
- Cloud Run 5xx after about 01:40Z (metric lag); when the monitor recovers.
- The one earlier non-ack push on the sales_order subscription with no matching Cloud Run 5xx; `fuse.tracking.store.errors` 8 at 01:35 against 24 log lines.
- Whether a Jira defect exists (not searched here). Firestore or GCP status page not checked.

## Outcome
Real minor, P3, not escalated. tracking-service answered HTTP 500 to 24 Pub/Sub pushes in 6 s when Firestore commits on its database were rejected RESOURCE_EXHAUSTED, the monitor correctly counted them (24, about 5.6%). Nothing dead-lettered or held on the evidence read, wave acks equal wave records, no error since 01:35:08Z. Recurrence after the 6 Nov fix is why this is P3 rather than P4: a tracking-service defect ticket is warranted (Firestore throttling recurring, 2 + 2 + 24 since the fix), not filed here, needs a go-ahead via create-defect. The Mongo move (programme D5-D11) is the planned structural fix and is not deployed. Draft reply returned to the watcher, which posts it.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794274888025569
- Monitor: https://app.datadoghq.com/monitors/332917924
- Related: Monitors/2026-11-10-platform-elevated-prod-error-rate-tracking-service-store-0135z.md, Monitors/2026-11-06-tracking-service-push-5xx-rate-high-1126.md, Monitors/2026-11-06-tracking-service-push-5xx-rate-high-0916.md, Engineering/tracking-service/known-context.md
