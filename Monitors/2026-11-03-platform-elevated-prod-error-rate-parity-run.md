---
tags: [datadog-triage]
date: 2026-11-03
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: config-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793714991814999"
opened_at: "2026-11-03T14:08:37Z"
severity_assessed: P4
flapping: true
outcome: real_minor
session_id: 7198be0e-f4de-4cae-8e32-ef4ac0c4cdb9
status: resolved
---
# 6 errors in 33s at 14:08Z, all from one synthetic run (correlationId parity-8cc48e-p-*) against prod config-service and its consumers

## Fired
More than 2 domain:fuse error logs in 2m. New pattern: not snap_adapter slot_timeout and not a customer flow.

## Investigation
- Monitor query (@domain:fuse status:error @environment:prod minus exclusions), 13:30-14:45Z per minute: only 14:08 has errors, 6 (config-service 1, sftp_connector 3, shopify-connector 1, rest_connector 1). Nothing 13:30-14:07 or 14:09-14:45. No businessId, failureMode or recordType on any of them.
- All 6 carry correlationId parity-8cc48e-p-NN. Across all statuses that prefix has 160 logs in config-service, rest_connector, sftp_connector, snap_adapter, shopify-connector, 14:07:59-14:08:33Z (6 error, 13 warn, rest info). Warns are "Entity not found" 7 and "Conflict detected" 6, config-service. A scripted run, not customer traffic.
- Errors: config-service 14:08:00 "Error unhandled" on POST /storefronts/sf_3e4f.../connectors/conn_e21e.../credentials/cycle, error TooManyRequestsException retryAfter 300, logged statusCode 500. rest_connector and shopify-connector 14:08:33 "Config API request failed" 404 on GET /connectors/conn_e21e... in the config-revision backlink refresh (connector no longer exists). sftp_connector (72984d4, the S3 cut deploy) x3 "Unsupported fragment type: Possible unknown fragment type", 14:08:01, :02, :32.
- config-service prod deploys 13:06, 13:40, 13:57, 14:04Z (9627e7b, revision config-service-prod-00067) by Harry; the run started 3.5 min after the last.
- "Unsupported fragment type" in sftp_connector prod: 3 in the last 24h, all in this burst, so first occurrence in 24h. Fragment type not in the log.
- snap_adapter: one error 14:03:16 ("Entity creation in SNAP failed", outside the monitor window, no attributes), none 14:04-14:45. No snap_adapter error in the 2m that tripped.
- Sizes: 6 vs 101 (2 Nov 16:35Z), 126 PURDYFIGG (29 Oct), 53 SPORTLUX.

## Not established
Who or what ran the parity-8cc48e run (inferred from the prefix and the deploy timing only). Whether it wrote or deleted any real config in prod. Which fragment type sftp_connector rejected and whether a real revision event would hit the same error. Whether config-service returning 500 for a TooManyRequestsException is a defect. snap_adapter create_record_sales_order oldest-unacked peak (metric query returned no data).

## Outcome
Real minor, P4. Self-contained 33s burst, no customer record, no held record. Follow-ups are leads, not ticketed.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793714991814999
