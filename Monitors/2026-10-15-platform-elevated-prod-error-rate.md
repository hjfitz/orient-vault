---
tags: [datadog-triage]
date: 2026-10-15
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: replay
business_id: DOCKBAY
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792055859280009"
opened_at: "2026-10-15T09:16:37Z"
resolved_at: "2026-10-15T09:21:00Z"
minutes_spent: 5
severity_assessed: P4
flapping: true
outcome: real_minor
escalated_to:
ticket:
session_id: 4fc06c6b-d424-4da8-b551-fb874e9c6e96
status: resolved
---
# Platform error-rate monitor tripped by 2 replay-service 500s on DOCKBAY goods_out_confirmation

## Fired
Monitor is `>2` matching `domain:fuse` error log lines in 2m (id 180072217, terraform-managed). It tripped at 09:16:37Z on 4 log lines. Not the cause from the 2026-10-14 record (PURDYFIGG Shopify fulfilment rejections).

## Investigation
- DDSQL per-minute count on the monitor filter, 08:30Z to ~09:19Z: only 2026-10-15T09:16Z, replay_service, DOCKBAY, 4 lines, plus 1 sftp_connector line at 09:05Z. The same count with the monitor exclusions removed is identical.
- The 4 lines are 2 pairs at 09:16:05Z: `POST /event/confirmation-made - 500` and `Error unhandled | error.message: Cannot set property name of  which has only a getter`, `recordType=goods_out_confirmation`, correlationIds `741ef06c-97ef-4c4e-af57-a4ed5f2e2387` and `dd3588df-cdd5-4f87-8061-3b54fd1c7154`. Requests came from Google IPs with an APIs-Google user agent, which fits a Pub/Sub push (not otherwise checked).
- The `Error unhandled` stack is a TypeError in `@ilg-platform/observability@1.10.0` `CredentialsRedactor.restoreErrorName_`, thrown while `RedactingLogger.error` was logging an error. The original exception text is therefore not in the logs.
- Same pair seen once before in 7d: 2026-10-08T13:06:07Z, DOCKBAY goods_out_confirmation, correlationId `2260241e-ece6-402c-99cd-47f4b49e4e19`, on older version `f8aa2da2`. The only other replay_service errors in 7d are 2 lines at 2026-10-11T10:33Z (`Failed to decode param '%C0'`).
- Current: no error lines after 09:16:05Z (checked to ~09:19Z); monitor state is OK.
- Us vs vendor: 0 error lines from shopify-connector, snap_adapter or snap-polling-service from 09:00Z to now. The 500s are replay-service's own responses.
- Deploys: replay_service version `43380ebd` first logged 2026-10-13T09:28Z; get_change_stories for replay_service 2026-10-14T21:00Z to 2026-10-15T10:30Z is empty. Not a deploy.
- tracking-service cutover (INGEST_HOLD 503s): service `tracking-service` has 126 info + 1 warn and 0 error lines in 24h, and 0 lines with a 5xx `@res.statusCode`. None of its lines are in the monitor's count.
- Other DOCKBAY activity 09:00Z to now is info-level only, apart from the 4 lines. The two correlationIds appear only in replay_service (7d search of the other services found none).
- Flapping: 55 alert events on this monitor in 7d (search_datadog_events).
- Replay failures list for DOCKBAY shows sales_order validation failures (City/LastName over 30 chars), not connected to these lines; not investigated further.
- Not established:
  - the original exception behind the 500 (masked by the redactor TypeError);
  - whether Pub/Sub redelivered the 2 messages (no further attempts logged by 09:19Z);
  - what the replay handler does with a `goods_out_confirmation` (Fuse MCP lists only pick/pack for this subscription);
  - whether the redactor TypeError causes the 500 or only co-occurs with it.

## Outcome
Real but minor: replay-service, one business, 2 deliveries, single burst, recovered. P4, no incident, no ticket. Recurrence of the 2026-10-08 signature is worth a look by the replay-service owners, not ticketed here. Reply posted in thread with broadcast.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792055859280009
- Monitor: https://app.datadoghq.com/monitors/180072217
- Earlier record: [[2026-10-14-platform-elevated-prod-error-rate]]

## Update 2026-10-15T09:25Z: Replay Service 5xx rate monitor (id 303413088) tripped by the same two 500s

Priority-2 monitor `[FUSE][Replay Service] 5xx rate high (console/ingest availability)`, first triggered 09:19:48Z. Same cause as above; severity P4, outcome real_minor.

- Query: `sum(last_15m)` of `gcp.run.request_count{service_name:replay-prod,response_code_class:5xx}` over all `replay-prod` requests, alert above 5% (terraform-managed, tags `managed-by:terraform`, priority 2). No minimum-volume guard.
- Value 10.526% = 2 5xx / 19 requests (get_datadog_metric, 5-minute buckets 09:05 to 09:20Z: 12 + 3 + 4 requests, 2 5xx).
- The 2 5xx are the DOCKBAY `goods_out_confirmation` `POST /event/confirmation-made` 500s at 09:16:05Z already recorded above (same correlationIds `741ef06c-...`, `dd3588df-...`). DDSQL on 3h of replay_service request logs: `confirmation-made` 200 for PURDYFIGG 276, EPARFUM 69, SAIRA 24, DOCKBAY 19, WILDSMITH 10, STUBBLE 7; 500 only DOCKBAY 2. `/api/v1/failures` 7 and `/api/v1/failures/stats` 12, all 200.
- Not unavailable: 5xx metric 0 in the two minutes after the burst (data to 09:19Z); no 5xx log lines after 09:16:05Z; last logged request 09:19:36Z was a 200; DOCKBAY `confirmation-made` returned 200 at 09:16:44Z and 09:16:48Z. `gcp.run.request_latencies.p99` under 100ms in every 5-minute bucket from 08:30Z except 08:40Z (933ms).
- 7d: metric shows 3 5xx (1 on 2026-10-08 13:00Z hour, 2 now). Monitor events in 7d: Warn 2026-10-08T13:09:48Z, Recovered 13:22:48Z, Triggered 2026-10-15T09:19:48Z. Not a flapper (the 55 events on the Platform monitor are a different monitor).
- Us vs dependency: replay-service's own 500s; version `43380ebd` live since 2026-10-13.
- Monitor still Alert at 09:22Z; by its query it clears when the 09:16 5xx leaves the 15m window (about 09:31Z).
- Not established: original exception behind the 500 (masked by the logger TypeError); whether the TypeError causes the 500 or co-occurs; whether Pub/Sub redelivered the 2 messages (their correlationIds appear only in the 09:16:05Z lines).
- Worth a look by the owners (not ticketed here): the low-volume rate threshold means any single failing pair re-pages at P2.
- Reply posted in the monitor's thread with broadcast: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792056052243039
- Monitor: https://app.datadoghq.com/monitors/303413088

## Update 2026-10-15T15:38Z: third firing, SPORTLUX snap_adapter schema_validation (P4, real_minor)

Third firing of monitor 180072217 in ~28h (the 30h events search shows exactly three Triggered: 2026-10-14T11:25:37Z, 2026-10-15T09:16:37Z, 2026-10-15T15:34:37Z). Thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792078539734709. Severity P4, no incident, no ticket. Recovered event 15:35:37Z; monitor state OK at ~15:37:40Z.

- Per-minute DDSQL on the monitor filter, 14:30Z to now: only snap_adapter, 14:35Z 1 line (PURDYFIGG `cancelled_in_wms`, unrelated) and 15:32 to 15:36Z 5 lines (1, 1, 2, 0, 1 per minute). Nothing else from any service.
- The 5 lines: `Entity creation in SNAP failed`, SPORTLUX, `sales_order` recordId `S-SO-032432`, connector `conn_bad08a939d7a4d38a98dad51935bef44`, `failureMode: schema_validation`, `errorMessage: Unable to parse data`, `fieldErrors`: `ShipAddress.0.Line1`, `Too big: expected string to have <=50 characters`, value logged as empty. Timestamps 15:32:58, 15:33:21, 15:34:13, 15:34:42, 15:36:19Z; five correlationIds (`fd181736-a820-4f7a-86cd-e0c897e3febf`, `fdb73ded-663b-4fd6-ab74-ffdbcb1211ef`, `9d29e123-d9b7-4da8-9b88-f89a5a36124a`, `bdfb0798-b7bd-46be-8f91-bb4bd6224f7f`, `d0e5d8ff-3af8-459c-ab45-24224bf70b7c`), `deliveryAttempt: 1` each, so five separate messages, not Pub/Sub redelivery of one.
- Source: sftp-connector `File download started` for `FUSE_DD2AF79592/to_ilg/create_sales_order/ILG_SO_Export 2_1510.csv` at 15:32:57, 15:33:20, 15:34:13, 15:34:41, 15:36:18Z. `Records to send resolved` recordCount 12 on each pickup (first pickup lists S-SO-032430 ... S-SO-032630, including 032432). First pickup: 11 `Entity created in SNAP` (all fd181736), 1 failure; later pickups logged no creations. replay_service `Failure stored` 5 (one per pickup).
- SPORTLUX 48h file pickups for this user: ILG_SO_Export 1_1410.csv twice (2026-10-14T15:31:08Z and 15:31:30Z, 37 records, 37 dedupe_service warns), 1_1510.csv once (10:48Z, 32 records), then the 5 above. So a repeat pickup of a SPORTLUX file also happened on 2026-10-14, with no errors.
- SPORTLUX error-level lines in 7d: only these 5. Warn lines in 7d: snap-polling 165, dedupe 37, sftp-connector 22 (not examined).
- Current: no `status:error` from any prod domain:fuse service after 15:36:19Z (checked to ~15:37:40Z); no SPORTLUX-tagged or `FUSE_DD2AF79592` log lines after 15:36:30Z.
- Deploys: get_change_stories for snap-adapter 2026-10-14T15:00Z to 2026-10-15T15:40Z empty. Version `fa3f47a5` revision `snap-adapter-prod-00089-2nw` (when it first appeared was not checked).
- tracking-service: 753 info, 1 warn (2026-10-14T19:40Z), 0 error in 24h, last log 15:14:50Z. No contribution.
- All prod domain:fuse error lines with no monitor exclusions, 30h by service/hour: snap_adapter 1+1+1+1+5, shopify-connector 6 (2026-10-14T11Z), fuse-ui 1+1, sftp_connector 1, replay_service 4. 7d snap_adapter history shows other businesses' recurring schema_validation / snap_api_error runs (SAIRA, PURDYFIGG, DOCKBAY, etc.), none overlapping this window except SPORTLUX.
- Us vs vendor: errors are snap-adapter's own validation (`schema_validation`, `Unable to parse data`); no Snap timeout or 5xx error line in the window (step 2b not run, no timeout signature).

What the three firings share: only the monitor itself (`>2` error lines in 2m, no volume floor). Different service, business and error each time (shopify-connector PURDYFIGG Shopify rejections; replay_service DOCKBAY 500s with a logger TypeError; snap_adapter SPORTLUX address-length validation). Not a common cause on the evidence gathered.

Not established:
- why the SPORTLUX file was picked up 5 times (customer re-upload vs connector re-read; the same happened twice on 2026-10-14);
- the actual `ShipAddress.0.Line1` value (logged empty);
- whether SPORTLUX has been told, and whether the other 11 orders are intact in Snap (only the `Entity created in SNAP` log lines were seen);
- why later pickups did not re-create the other 11 records (dedupe not queried).

Nothing retried, resent or changed (read-only). Reply posted in thread with broadcast: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792078711604449
