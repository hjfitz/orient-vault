---
tags: [datadog-triage]
date: 2026-11-06
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: dedupe-service
business_id: PURDYFIGG
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793988409139299"
opened_at: "2026-11-06T18:05:37Z"
resolved_at: "2026-11-06T18:11:00Z"
minutes_spent: 5
severity_assessed: P4
flapping: true
outcome: self_resolved
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# 18:05Z firing: dedupe-service "Dependency connection failed" (config-api, status 599) x3 on PURDYFIGG duplicates, retried and dropped, nothing lost

## Fired
More than 2 error-level domain:fuse logs in 2m (monitor 180072217, alert post 18:06:49Z, parent ts 1793988409.139299, no replies). Shortened re-check run as a read-only subagent (watcher posts the reply). The trigger was not one of the previously recorded patterns, so the check was widened.

## Investigation
- Matching errors in the last 45m (analyze_datadog_logs, the monitor's exact query): 4. dedupe_service "Dependency connection failed" x3 at 18:05:20.577-.612Z (PURDYFIGG, `dependency: config-api`, error status 599 on request and response, flow create, recordType sales_order, records #6672166, #6672190, #6672394, one correlationId 70565c3c-6f82-4f33-b901-8bbfbacb101e); config-service "Dependency connection failed | Postgres ping took longer than 2000ms" x1 at 18:07:37Z (after the trigger, so not what tripped it). Unfiltered prod domain:fuse errors in the same 45m add one snap_adapter "Entity creation in SNAP failed" (DOCKBAY UK-913330, 18:03:53Z, transient:false, which the monitor excludes).
- The 3 dedupe lines are not Postgres ECONNRESET, tracking-service store failed, snap_adapter slot_timeout/599 or replay-service 400. The config-service line at 18:07 does match the config-service Postgres ping pattern.
- Outcome of the 3 records: each logged "Retry attempted after transient failure" (warn) at 18:05:20Z, then "Record dropped" and `POST /events/v1/record/request/sales_order - 204`. Each had already been "Record published to topic" earlier (#6672166 15:45:12Z, #6672190 15:10:15Z, #6672394 15:15:14Z), so these were duplicate drops of the shopify-connector republish batch. That batch (the correlationId above) logged 2584 "Incoming record received", 2584 204s, 55 published, 2529 dropped. Nothing lost, nothing held.
- Timing: config-service logged "App build started" x3 at 18:05:18Z, "Dependency connected" 18:05:19Z, "Server listening" 18:05:20Z, GET /health 200 at 18:05:21Z (instance starts per hour in 12h: 07Z 1, 11Z 1, 18Z 3). config-service has logged one version (6b73684) since 06:11Z, so no deploy. The 599s came at 18:05:20Z inside that start window. Only a temporal coincidence; no mechanism was confirmed. The two earlier dedupe config-api failures (6 Nov 16:25Z, 17:00Z; also 5 Nov 21:45Z) had no config-service instance start in their hour, so cold starts do not explain all of them.
- Impact checks: Cloud Run `gcp.run.request_count` 5xx by service, last 30m: 0 for config-service-prod, developer-portal-prod, ilg-secure-notes-prod-cr, sftp-connector-prod-cr, tracking-service-api-prod. Logs with `@http.status_code:[500 TO 599]` (domain:fuse, prod) in the last 30m: none. config-service error lines per minute over 3h: one (18:07Z).
- Pub/Sub: oldest unacked age, top 5 subscriptions by max over the last 30m: shopify-connector create_acknowledge_sales_order 29s, sftp-connector create_acknowledge 26s, snap_adapter create_record_sales_order 12s, shopify-connector bulk_ingest_order_reap 6s, tracking-service create_acknowledge sales_order 1s. No backlog (metrics lag about 4 min).
- Held records: `replay-list-failures` (production, createdAt 2026-11-06) has no new PURDYFIGG sales_order failure; newest is DOCKBAY sales_order UK-913330 at 18:03:53Z, ShipAddress.City over 30 characters, failurePoint create.wms_precheck (not caused by this firing; 8 of the 10 newest DOCKBAY failures are this City error, from 3 Nov to 18:03Z today, with 12:03Z and 14:03Z also today). PURDYFIGG goods_out_confirmation "Fulfillment order ... is CLOSED in Shopify" failures held 17:14-17:50Z are earlier than the trigger and not examined.
- Unreplied alert thread: the 16:02:43Z firing of this monitor (parent ts 1793980963.415549) has no replies. Matching errors in 15:58-16:06Z were tracking-service "store failed; nacking for redelivery" x7 (the known Firestore pattern).

## Not established
- Why dedupe-service got status 599 from config-service at 18:05:20Z (cold start coincidence only). Why the 16:25Z and 17:00Z failures occurred.
- Whether the config-service Postgres ping at 18:07:37Z relates to the 18:05 failures.
- DOCKBAY UK-913330 follow-up, and whether support already knows of the DOCKBAY City limit failures.

## Outcome
P4 self_resolved. Three config-api calls failed on duplicate PURDYFIGG records, were retried, and the records were dropped as already published. No 5xx, no backlog, no new held record caused by this.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793988409139299
