---
tags: [datadog-triage]
date: 2026-10-13
monitor: "[FUSE][SFTP Connector] File routing move failed (file may be stuck unrouted)"
service: sftp-connector
business_id: STUBBLE
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1791884178890329"
opened_at: "2026-10-13T09:35:15Z"
resolved_at: "2026-10-13T09:37:22Z"
minutes_spent: 2
severity_assessed: P4
flapping: false
outcome: self_resolved
escalated_to:
ticket:
session_id: 4fc06c6b-d424-4da8-b551-fb874e9c6e96
status: resolved
---
# STUBBLE sales-order file hit a transient GCS 503 while being archived; redelivery archived it

## Fired
Monitor 307579275 (`fuse.file_routing.move.failure` > 0 over 10m, prod) fired with value 1, `trigger:acknowledge`. It was not the LISAUK file from the 09:30Z canonical-validation alert; that file routed fine.

## Investigation
- Metric `sum:fuse.file_routing.move.failure{service:sftp_connector,environment:prod}` over 14d: a single point, 1 at 09:35Z today. Not flapping.
- Paired log is `File routing failed` (the monitor message's `"Failed to route file"` search returns 0 hits). It names `FUSE_E5A356978A/to_ilg/create_sales_order/261013103450267SO.csv` (STUBBLE, correlationId `9bab3e37-46dc-442e-9baa-a858919ca2a0`), destination `.../archive/261013103450267SO.csv`, trigger `acknowledge`.
- Underlying error at 09:35:09Z: copy to archive succeeded (archive object created 09:35:04Z), then `file#delete` of the source returned GCS `503 backendError`. Only one `Failed to move object in cloud storage` in 7d of sftp_connector prod logs.
- Redeliveries: 09:35:47Z and 09:36:38Z logged `File routing deferred to an in-flight claim` (500, redeliver). The failed attempt leaves the claim held; `PENDING_CLAIM_TTL_MS` = 120_000 at deployed sha `28c514e` (read from `code/src/core/file-routing/constants.ts` at that sha). 09:37:22Z redelivery logged `File routed`, POST create_acknowledge 204.
- GCS read at 09:37:42Z (`gcloud storage ls`, read-only): source object absent, `archive/261013103450267SO.csv` present (created 09:37:22Z), no `error/` copy.
- No re-ingest: the only `Incoming record received` for the file is 09:34:57Z; the later `Incoming file event` lines at 09:35:04Z and 09:37:22Z are the archive writes.
- LISAUK `UK Concealer  WAVE 2.csv` (correlationId `8890c6b4-e6c4-4aa6-a9d5-cfd5b5d70c9e`): `File routed` at 09:29:35Z, object in `FUSE_84B6F5A152/to_ilg/create_sales_order/error/`. Unrelated to this alert.
- Monitor is Terraform-managed (`managed-by:terraform` tag); no change was made to it.
- No Customers/STUBBLE folder in the vault; cause is infra (GCS), not customer-specific.

Not established: whether Google had a wider Cloud Storage incident at 09:35Z; why the move failed only once in 7d (no GCS status source checked).

## Outcome
Self-resolved. No file stuck. Nothing moved or resent by this triage. Minor tuning note for the monitor owner: its message points at a log search string (`"Failed to route file"`) that matches nothing; the actual line is `File routing failed`.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1791884178890329
- Monitor: https://app.datadoghq.com/monitors/307579275
