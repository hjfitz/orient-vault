---
tags: [datadog-triage]
date: 2026-10-20
monitor: "[FUSE][Platform] Ingress stalled — no records entering the pipeline"
service: dedupe-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792483326214659"
opened_at: "2026-10-20T08:00:41Z"
severity_assessed: P2
flapping: false
outcome: escalated
escalated_to: INC-40
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: open
---
# Ingress stalled: Shopify (INC-40) and SFTP both silent since about 06:00Z

## Fired
`sum(last_2h):sum:fuse.dedupe.event.handled{environment:prod} < 1` (monitor 302536181) went to Alert at 08:00:41Z with a value of 0.1. Its last non-zero data was in the 06:00-06:10Z bucket (12).

## Investigation
- **Topic:** `bifrost.prod.create_record_request.v1` send_request_count was 29/31/22/23/24/31 per 30 min from 03:00Z, then 8 in the 06:00 bucket, then nothing. Every dedupe subscription's backlog is 0, so dedupe has nothing to process. It is not failing.
- **Mongo warnings:** dedupe-service logs "Dependency degraded" (`dependency: mongo`) about every 20s from 06:04:10Z. These sit alongside "Dependency connected" lines.
- **Per-channel baseline:** from dedupe "Incoming record received" by `@metadata.source`, for 06:00-08:00Z on each of the previous six days in the log window (13, 14, 16-19 Oct):
  - shopify: 398-1283 a day; today 11.
  - sftp: 6-102 a day; today 0.
  - rest: 1-7 a day; today 1.
- **Shopify:** last record about 06:02Z. Covered by INC-40.
- **SFTP:**
  - The last customer ingress file (`File download started`) was at 05:51:20Z. Yesterday had 7 files at 06Z and 14 at 07Z. Every day last week had at least 6 in 06:00-08:00Z.
  - Users seen yesterday 05-09Z: FUSE_E5A356978A (34 files), FUSE_C062E5C41B (10), FUSE_C232BE3BCC (3), FUSE_59DC37CB09 (1).
  - The sftp-connector Cloud Run service is healthy. It still handles confirmations and writes FUSE_E5A356978A confirmation CSVs every 2 min.
  - The SFTP VM `sftp-connector-prod-sftp` is in zone europe-west2-b. Its GCE uptime and network metrics stop at about 06:05Z, and CPU at about 06:15Z. They were continuous for the previous 7 days.
- **REST (`api-gateway-prod` = rest_connector):**
  - It is up: Nest started and the server was listening at 07:02Z. It runs LRU-only after "Cache service initialization failed" at 06:08:49Z.
  - Last ingest request was 06:02Z.
  - Yesterday's ingest in the same window was 5 requests (3 sales-orders, 2 master-data).
  - 5xx: 11 today, mostly 504s since 07:00Z, against 1 in the previous 7 days.
  - A 404 burst of 380 at 07:40-08:00Z also shows on other public services (developer-portal, ilg-secure-notes, fuse-mcp-go), so it looks like external crawling (not verified).
- **INC-40 room (C0CAEGABJBF):** mentions sftp only as a "zone-c (sftp)" Redis that is healthy. The SFTP VM is not covered.

### Not established
- Whether customers can actually connect to the SFTP server. There are no sshd or `sftp_login` logs in Datadog for the VM. The VM's state was not checked in GCP.
- Which REST path is returning 504.

## Outcome
Escalated (ESCALATE returned to caller; incident-response not invoked per caller override). Acknowledgement posted in the thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792483575048749

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792483326214659
- Incident: https://gfsdeliver-eng.slack.com/archives/C0CAEGABJBF
