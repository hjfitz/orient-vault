---
tags: [datadog-triage]
date: 2026-10-19
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: snap-adapter
business_id: STUBBLE
snap_instance: ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792418679092359"
opened_at: "2026-10-19T14:03:37Z"
severity_assessed: P3
flapping: false
outcome: real_minor
ticket:
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: open
---
# STUBBLE master data rejected: NMFC codes missing in Snap

## Fired
Monitor 180072217 (>2 matching error logs in 2m, prod) triggered 14:03:37Z.

## Investigation
- analyze_datadog_logs over the monitor query, 13:50-14:15Z: 8 errors, all service snap_adapter. Hourly count last 24h: 1 (06:00), 1 (12:00), 8 (14:00). Zero matching errors from 14:04Z.
- search_datadog_logs: all 8 are STUBBLE master_data, failureMode nmfc_missing, "No NMFC code found in SNAP", one correlationId 389d8116-5751-4302-981c-c03f71e97dad, 14:03:00.0-14:03:00.3Z, deliveryAttempt 1, exhausted false. NMFC items sent: 401699, 830249, 830140 (SP.* hardshell spare-part SKUs).
- snap-search nmfcCodes on STUBBLE's host (ilg005 live), filter `Item eq` the three codes: empty result.
- replay-list-failures STUBBLE master_data (production): 8 held failures created 14:03:00-14:03:01Z, attempts 0.
- 7-day snap_adapter error profile: STUBBLE nmfc_missing 8 (this burst), EPARFUM nmfc_missing 2; all deliveryAttempt 1.
- Monitor events (3d): triggered 16 Oct 15:25Z, 17 Oct 14:03Z (recovered 14:09Z), 19 Oct 14:03Z. Not chronic flapping.
- Only Snap-side check run was the NMFC table read; no Snap latency/timeout evidence involved so Step 2b not applicable.

## Outcome
Real, minor, one customer: 8 SKUs await NMFC codes in Snap (or corrected codes in the customer file) and a replay. Reply posted in thread.

Not established: who owns the fix (customer file vs missing Snap NMFC rows); whether the 16/17 Oct firings share this cause.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792418679092359
