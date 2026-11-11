---
tags: [datadog-triage]
date: 2026-11-11
monitor: "[FUSE][Tracking Service] Push 5xx rate high (332917924; inputs 332917918 ratio, 332917914 count)"
service: tracking-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794411150406009"
opened_at: "2026-11-11T15:32:04Z"
severity_assessed: P4
flapping: true
outcome: monitor_mistuned
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# Push 5xx composite fired twice during the planned prod ingest hold; every 5xx is a deliberate 503 hold refusal, the "minus push.held" subtraction fails on series timing

## Fired
Composite 332917924 (`332917918 && 332917914`, Terraform-managed, priority 2) Triggered 15:32:04Z, Slack post 15:32:30Z (ts 1794411150.406009, no replies at 15:37Z). Later events (search_datadog_events, source:alert): Warn 15:33:04Z (post 1794411209.397629), Recovered 15:34:04Z, Triggered again 15:36:04Z (post 1794411388.468739), Recovered 15:37:04Z (post 1794411445.192769). Inputs: count 332917914 Alert 15:30:54Z, Recovered 15:32:54Z; ratio 332917918 Alert 15:30:58Z, Recovered 15:32:58Z. All three read OK at about 15:37:20Z. 12 composite events in 7 days, 5 of them since 15:32Z today.

## Investigation
- **Definition** (get monitor): count input `sum(last_10m): default_zero(sum:gcp.run.request_count{service_name:tracking-service-api-prod,response_code_class:5xx}.as_count()) - default_zero(sum:fuse.tracking.push.held{service:tracking-service,environment:prod}.as_count()) > 5`; ratio input is that difference over `default_zero(sum:gcp.run.request_count{service_name:tracking-service-api-prod}.as_count()) * 100 > 5` (warning 2). `requireFullWindow: false`, no evaluation delay in options. The API does not return the values evaluated at 15:30:54Z, so those are not read.
- **Per-minute, held vs Cloud Run 5xx** (settled data, queried 15:36Z). The GCP series is stamped one minute after the same refusals. Held[M] / GCP 5xx[M+1] / Cloud Logging 503s in minute M: 15:18 47/47/49, 15:19 31/30/29, 15:20 276/288/280, 15:21 178/169/176, 15:22 114/113/114, 15:23 80/78/79, 15:24 90/92/90, 15:25 59/62/60, 15:26 65/59/64, 15:27 42/44/41, 15:28 55/57/57, 15:29 45/43/44, 15:30 53/53/53, 15:31 48/48/48, 15:32 44/43/44, 15:33 44/46/44. Totals: held 15:18-15:32 = 1,227 against GCP 5xx 15:19-15:33 = 1,226; Cloud Logging 503s 15:18-15:33 = 1,272 against held 15:18-15:33 = 1,271.
- **GCP series lag.** Last Cloud Run 5xx point available: 15:29 when read at 15:32:30Z and again at 15:34:59Z, 15:34 when read at 15:36:18Z (lag 2-6 min). `push.held` had points to the current minute each time. Total requests 15:19-15:34 are 5xx plus 2 (15:23, 15:25), the two GETs below.
- **Replay of the formula on settled data** (10 one-minute buckets ending at stamp E; my reconstruction, not Datadog's evaluated values): E=15:29 5xx 992 - held 1,004 = -12; E=15:30 1,005 - 781 = +224 (22.2%); 15:31 +119 (15.4%); 15:32 +68 (10.4%); 15:33 +34 (5.9%). The first positive window is the one where the 15:20 held spike (276) has left the held side while its 288 echo (stamped 15:21) is still on the Cloud Run side; both inputs first alerted at 15:30:54/58Z. The 15:32:54Z recovery and the 15:36:04Z re-trigger are not explained by this replay (recovery would need the lagged, incomplete 5xx data), see Not established.
- **Every 5xx is a 503.** gcloud logging read, Cloud Run request logs for tracking-service-api-prod revision 00021-c28 from 15:16:30Z: 1,287 requests to 15:34:15Z, of which POST 503: /events/v1/confirmation_made/goods_out_confirmation 303, create_record_request/sales_order 287, create_record/sales_order 244, create_acknowledge/sales_order 242, confirmation_ready/goods_out_confirmation 209; GET /api/v1/businesses 200 x2. At 15:37:22Z: 1,425 requests, 1,423 POST 503, 2 GET 200, 0 other 5xx. `gcp.run.request_count` 5xx by response_code and revision since 15:16:30Z: 503 only, revision 00021-c28 (1,272 at read time). `fuse.tracking.push.held` since 15:16:30Z by topic: create_record_request 300, confirmation_made 317, create_acknowledge 256, create_record 258, confirmation_ready 221, the same five paths.
- **Logs.** Cloud Logging, same revision since 15:16:30Z: severity>=WARNING excluding the request log = 0; all 1,435 severity>=WARNING entries are request logs with status 503. Log names present: requests 1,438, stdout 26, system 2, audit system_event 2. Datadog `service:tracking-service @environment:prod` since 15:16Z at 15:33Z: 22 lines, all info (ingest held 16, shutdown draining 3, request handled 2, api listening 1). The refusal log is rate-limited to about one line a minute, so log counts do not count refusals. The two "request handled" lines are GET /api/v1/businesses 200 (15:22:46Z, 15:24:20Z).
- **Store.** `fuse.tracking.store.errors` prod: no series since 15:16:30Z. `fuse.tracking.events.ingested` prod: 30, 82, 34 at 15:14-15:16, no points after. `gcp.firestore.api.request_count` (project bifrost-prod-global1) since 15:16:30Z, by api_method: commit ok 99,936 / aborted 0, begintransaction ok 99,844, batchgetdocuments ok 99,958, runquery ok 200,506, runaggregationquery ok 144, no other code. Only non-ok points 15:10-15:33: aborted 2 at 15:11 and 2 at 15:16 (before the first refusal at 15:18:07Z). Commit volume rose to 2,844-15,312 a minute from 15:18, when the import started (15:17:58Z); not from ingest, since nothing was ingested. Attribution to the import was not checked.
- **Mongo import** (process 3655641, started 15:17:58Z, still running; redacted log tail, no connection string read): 59,000 shipments read, 59,000 written, 0 skipped, 0 live, 0 failed, 53/s at 15:36:42Z; "kept: 65 shipment and 0 return scope-days of duplicates"; no warn/error line in 119 log lines. From Firestore bifrost-prod-global1/tracking-service to MongoDB database tracking-service-prod.
- **Hold state since 15:26Z.** Cloud Run service latestCreated = serving = tracking-service-api-prod-00021-c28 at 100%, created 15:16:30Z, `INGEST_HOLD=true`, `STORE=firestore` (env read filtered to those two names); no newer revision. PR #41 (hjf/mongo-cut-prod-flip): open, draft, CLEAN, updatedAt 14:36:26Z; newest workflow runs in the repo are its 14:35:56Z checks. Refusals still arriving at 15:37:22Z.
- **Retention.** The five held tracking push subscriptions (create_record_request.sales_order, create_record.sales_order, create_acknowledge.sales_order, confirmation_made.goods_out_confirmation, confirmation_ready.goods_out_confirmation, `.v1.sub`) all have messageRetentionDuration 604800s and no dead-letter policy, so refused messages stay queued.
- **Related alert, not triaged here:** [FUSE][Platform] Pub/Sub backlog not draining on tracking-service.prod.create_record_request.sales_order.v1.sub, Slack post 15:31:52Z (ts 1794411112.327389).
- **Prior firings of this composite:** 6 Nov and 10 Nov 01:41Z were real Firestore store-write failures (see Monitors/2026-11-10-tracking-service-push-5xx-rate-high-0141.md); the monitor's "only answers 5xx when a store write fails" text does not hold during a hold.

## Not established
- The values Datadog evaluated for the inputs at 15:30:54Z, 15:32:54Z and 15:36:04Z, and why it recovered at 15:32:54Z and re-triggered at 15:36:04Z (my replay on settled data stays positive through the 15:33 window). Incomplete, lagging GCP data at evaluation time is a lead, not tested.
- Per-request proof that each 503 is a hold refusal: the match is aggregate (1,272 against 1,271 over 15:18-15:33, same five paths).
- Whether any tracker events were lost: only retention and the absence of a dead-letter policy were checked; no messages were pulled and no backlog or oldest-unacked values read after 15:26Z.
- Import end time and parity result (not read). 114,340 shipments is from the earlier session, not re-queried; at 53/s that is roughly 15:54Z (estimate).
- Whether the commit volume since 15:18Z is the import's read transactions.
- Per-business split of the held messages (the metric has no business tag).
- Who set the hold timing beyond the earlier record (Harry confirmed in-channel at 15:19Z, per the task brief).

## Outcome
P4, monitor_mistuned. No non-hold 5xx, no application warn/error, no store errors, Firestore all ok, import 0 failed, hold unchanged and refused messages retained. The composite subtracts a custom metric that is current and aligned to the app minute from a GCP metric stamped one minute later and 2-6 minutes behind, so any rate change inside a 10-minute window leaves a residual and the monitor can trigger, then recover, during a planned hold. Expect more flaps until the release. Suggested retune (not applied, read-only run): align the series (or compare only complete GCP minutes), or exclude 503 / mute while `ingest_hold` is on. The monitor text should also stop saying it only answers 5xx on a store write failure. Re-assess if a non-503 5xx or an app error line appears, or the hold outlasts the import.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794411150406009
- Warn post: .../p1794411209397629; second trigger: .../p1794411388468739; recovery: .../p1794411445192769
- Monitor: https://app.datadoghq.com/monitors/332917924 (inputs /332917918, /332917914)
- Hold record: Monitors/2026-11-11-tracking-service-hold-mode-on-prod-1518z.md
- Release PR: https://github.com/gfs-bifrost/tracking-service/pull/41
