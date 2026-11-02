---
tags: [datadog-triage]
date: 2026-09-29
monitor: "[FUSE][Fuse API] Request latency p95 high"
service: fapi
business_id: DOCKBAY
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790697364246269"
opened_at: "2026-09-29T15:55:01Z"
resolved_at: "2026-09-29T15:58:49Z"
minutes_spent: 4
severity_assessed: P4
flapping: true
outcome: monitor_mistuned
escalated_to:
ticket:
session_id: 47540e1e-47b2-4ca6-8a6c-1867e78d6dd5
status: resolved
---
# Fuse API p95 latency warn, alongside the availability monitor flapping again

## Fired
Monitor 302685721 (p95 of `fuse.request.latency.95percentile` on `service:api-gateway`) went to Warn at 15:55 UTC with a value of 1091ms. The availability monitor 302685705 also triggered at 15:51 and recovered at 15:52, with 1 failure against about 12 requests (8.3%).

## Investigation
- **Confirmed:** fapi carries about 1–3 req/min, so any ratio or percentile over 15 minutes rests on a handful of requests. Peak p95 bin was 3.0s around 15:40Z, coinciding with DOCKBAY's go-live bulk load (about 90 sales orders in a minute, 205 master-data records). Max p95 for the DOCKBAY connector's master_data was 6.1s.
- **Confirmed:** the latest `fuse.request.failure` count moves with `fuse.request.rejected{httpstatus:400}` and `fuse.ingest.validation_errors` in the same bin, consistent with the earlier triage (`2026-09-29-fuse-api-availability-below-target`), which matched failures to DOCKBAY 400 validation rejections count-for-count. 4xx reasons are logged at debug, so the rejection reason itself was not readable.
- **Confirmed, separate issue:** two DOCKBAY records failed in Snap after fapi accepted them (`snap_adapter`, `schema_validation`, `transient: false`). At 15:36:41Z sales_order UK-904657 had `ShipAddress.0.Line1` over 50 chars. At 15:50:21Z master_data SKU `POS-DIS-SM-FULL-TOWLB-KID-EN-24` (31 chars) exceeded the 30-char `SKUId` limit. These keep the go-live D9 monitor red. My first Slack draft wrongly attributed the availability alert to them; the message was edited to correct that.
- **Hypothesis (unverified):** the slow requests are DOCKBAY master-data batch POSTs (large payloads). Request sizes were not checked.
- Both monitors are Terraform-managed (`managed-by:terraform`, `observability` repo). Nothing was changed.
- Unrelated background: 64 PURDYFIGG `stock_adjustment` `use_case_inactive` confirmation warns in 3h.

## Outcome
Monitor mistuned, not a platform fault. The recommended fix from the earlier triage stands: count only 5xx as `request.failure` in fapi, and log 400 rejections with businessId. The verdict was posted in the thread with broadcast. Owed: DOCKBAY needs telling about the two Snap-rejected records and their 400s. No ticket filed. On 2026-09-30 the availability retune shipped as observability#54: the alert is now a composite (ratio >5% AND at least 3 failed requests in 15m), live as monitor 326574293. The latency p95 monitor and the fapi 5xx-only counting are still open.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790697364246269
- Earlier same-day triage: [[2026-09-29-fuse-api-availability-below-target]], [[2026-09-29-fuse-api-availability-low-volume]]
