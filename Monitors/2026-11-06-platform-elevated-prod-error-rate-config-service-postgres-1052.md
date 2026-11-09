---
tags: [datadog-triage]
date: 2026-11-06
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: config-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793962423535819"
opened_at: "2026-11-06T10:52:37Z"
resolved_at: "2026-11-06T10:57:00Z"
minutes_spent: 5
severity_assessed: P4
flapping: true
outcome: real_minor
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# 10:52Z firing: config-service Postgres connection reset, one HTTP 500 to sftp-connector (retried, delivered)

## Fired
More than 2 error-level domain:fuse logs in 2m (monitor 180072217, alert post 10:53:43Z, parent ts 1793962423.535819, no replies). Shortened re-check, run as a read-only subagent (watcher posts the reply). Unlike the 23:29Z, 01:46Z and 08:23Z firings of this cause, one of the three lines was a caller-visible HTTP 500, so the check was widened.

## Investigation
- Matching errors since 10:40Z (analyze_datadog_logs, the monitor's exact query): exactly 3. config-service "Dependency connection failed | read ECONNRESET" (`dependency: postgres`) 10:51:58Z; config-service "Error unhandled" 10:52:04Z (cause ECONNRESET, syscall read, on the `connectors` select for `GET /api/v1/connectors/conn_9758e49936e64060b314b4cebc82c0ff`, statusCode 500); sftp_connector "Unable to make request to config service" 10:52:04Z (STUBBLE, flow confirmation, recordType sales_order, got 500 from config-service, correlationId 7222b822-4701-4f0d-922b-0b7fe2f106f4). Same revision as earlier firings (config-service-prod-00071-czr, version 6b73684).
- Matches the config-service Postgres pattern (23:29Z, 01:46Z, 08:23Z). Not tracking-service store failed, snap_adapter slot_timeout or 599, or replay-service 400.
- The 500 is the one new element. Cloud Run `gcp.run.request_count` for config-service-prod, 10:40Z to now: 244 2xx, 65 4xx, 1 5xx. Last 24h: 6 HTTP 500 (5 in the 12Z hour, which are the 12:09Z probe's five "Error unhandled" lines; 1 in the 10Z hour). So this is the first caller-visible 500 from the Postgres pattern.
- Outcome of the 500: sftp_connector logged "Retry attempted after transient failure" (warn) at 10:52:04Z, then "Confirmation file write started" 10:52:06Z, "Egress window upsert", "Confirmation processed", and `POST /events/v1/confirmation/ready/sales_order - 204` at 10:52:06Z, same correlationId. "Unable to make request to config service" appears once in 24h (sftp_connector only).
- Postgres gauge: `min:fuse.postgres.up` 10:45Z to now dipped (0, 0.8, 0.17, 0, 0, 0.8, 0.75, 0) and read 1 on the last 7 points (20s buckets). Cloud SQL `num_backends` max 2-3 in the window. `gcp.cloudsql.database.uptime` returned no data.
- Recurrence: config-service "Dependency connection failed" (dependency postgres) by version: 2 on 3 Nov 14:32Z (9627e7b), 2 on 5 Nov 12:54Z (5db1f87), 22 from 5 Nov 15:22Z to now (6b73684). So it predates the 6b73684 deploy (first seen 5 Nov 15:20Z). config-service error lines by hour: 5 Nov 20Z 3, 23Z 6; 6 Nov 01Z 3, 07Z 2, 08Z 3, 09Z 1, 10Z 4.
- Backlog: `max:gcp.pubsub.subscription.oldest_unacked_message_age{subscription_id:*prod*}` max per subscription 10:30Z to now: highest 8s (snap_adapter create_record_sales_order), then 5s (tracking-service, dedupe) and 4s, 3s; all others 0-1.
- Held records: replay-list-failures (production, createdAt 2026-11-06) total 43. Newest 10 are PURDYFIGG goods_out_confirmation created 10:50:39-10:50:41Z, reason "Fulfillment order ... is CLOSED in Shopify" (failurePoint confirmation.delivery_shopify, source shopify). Created before the first matching error (10:51:58Z), a Shopify-side reason, not in the monitor's matching set; not caused by this. Oldest of that type today is 07:06:38Z. replay-list-failures for STUBBLE: newest is 4 Nov 15:35Z (create.snap_api, Snap field validation), nothing new from this.
- Channel read (slack_read_channel from 10:38Z, then thread read): the only non-Recovered alert post since 10:38Z is this one (1793962423.535819, no reply). The 10:37:42Z and 10:37:43Z posts are before 10:38Z and both have replies.

## Not established
Why the Postgres connections are reset (Cloud SQL restart or maintenance, network, pool or idle-timeout config): no Cloud SQL logs or operations were readable and `cloudsql.database.uptime` had no data. Whether other config-service callers saw failures beyond the one Cloud Run 5xx (no other 5xx logged or counted). Why the 10:50Z PURDYFIGG Shopify "CLOSED" holds were created (not investigated; unrelated to this alert).

## Outcome
Real minor, P4, flapping. Same config-service Postgres connection-reset pattern as 23:29Z, 01:46Z and 08:23Z, now with one HTTP 500 (first from this pattern): sftp-connector retried within the same second and the STUBBLE confirmation processed at 10:52:06Z. `fuse.postgres.up` back to 1, no backlog beyond 8s, nothing new held by this. Earlier leads stand: log the dependency check at warn until repeated failure, look at Cloud SQL connectivity. No ticket filed here.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793962423535819
- Monitor: https://app.datadoghq.com/monitors/180072217
- Prior records: Monitors/2026-11-06-platform-elevated-prod-error-rate-config-service-postgres-0823.md, Monitors/2026-11-06-platform-elevated-prod-error-rate-config-service-postgres-0146.md, Monitors/2026-11-05-platform-elevated-prod-error-rate-config-service-postgres-2329.md
