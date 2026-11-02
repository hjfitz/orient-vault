---
tags: [datadog-triage]
date: 2026-09-29
monitor: "[FUSE][Fuse API] Availability below target (request failure rate)"
service: fapi
business_id: DOCKBAY
channel: bifrost-notifications
thread_url: "https://gfs-engineering.slack.com/archives/C099WKQTE8G/p1790687929222909"
opened_at: "2026-09-29T13:17:45Z"
resolved_at: "2026-09-29T13:31:53Z"
minutes_spent: 14
severity_assessed: P3
flapping: true
outcome: monitor_mistuned
escalated_to:
ticket:
session_id: 6aef9a85-766f-4a6b-af49-a3d857baf2fb
status: resolved
---
# Fuse API availability monitor flapping on DOCKBAY 400 validation rejections

## Fired
Monitor 302685705 (`fuse.request.failure / fuse.request` on `service:api-gateway`, sum over 15m, above 5%) triggered at 13:17 UTC with a value of 42.857. Five failures were counted against about 12 requests.

## Investigation
- **Confirmed (Cloud Run request logs matched to `fuse.request.failure` count for count):** all 19 failures since 28 Sep were `400 Validation failed for one or more records` returned to DOCKBAY's integration (`python-httpx/0.28.1`, GCP egress IPs). There were 11 on `/api/v2/master-data` on 28 Sep and 8 on `/api/v2/sales-orders` on 29 Sep. `fuse.ingest.validation_errors` matches `fuse.request.rejected{httpstatus:400}` hour for hour. fapi served zero 5xx all week.
- **Confirmed:** DOCKBAY's first fapi call was 28 Sep (2 × 401 at 10:42, then master data, then sales orders on 29 Sep). It is a brand-new REST integration with about 5% of calls failing validation. DOCKBAY has no Customers vault folder yet.
- **Confirmed:** every trigger aligns with a burst of DOCKBAY 400s (28 Sep 17:23; 29 Sep 09:55, 10:43, 13:17).
- **Root cause of the flapping:** `logging.interceptor.ts` counts every non-acked 4xx as `fuse.request.failure`, and the availability monitor treats that as unavailability. `all-exceptions.filter.ts` explicitly classifies 4xx as caller fault (`request.rejected`, never `errors.*`), so the two disagree. Low volume (about 10–15 requests per 15 minutes) makes one bad batch exceed 5%.
- **Observability gap:** 4xx reasons are logged at `debug` (dropped in prod), so the field-level rejection reason and businessId never reach Datadog. The debug level was chosen to silence scanner 404s. Scanner 404s never reach the interceptor, so they don't feed the metric.
- **Retracted:** the earlier `@ilg-platform` 1.10.0 hypothesis was a timing coincidence.
- The PURDYFIGG `use_case_inactive` warns are unrelated background (steady ~5/hour, 204).

## Outcome
The monitor is mistuned: availability counts client 4xx. Recommended fixes, pending the human's decision:
1. In fapi, count only 5xx as `request.failure` and keep 4xx in `request.rejected`.
2. Log 400 validation rejections at info/warn with businessId and the error list, keeping 404 at debug.
3. Optionally add a separate per-business rejection-rate signal for integration health.

The correction was posted in the thread.

## Links
- Slack thread: https://gfs-engineering.slack.com/archives/C099WKQTE8G/p1790687929222909
