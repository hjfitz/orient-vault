---
tags: [snap-maintenance]
date: 2026-11-02
subject: "Snap API Update - Planned Maintenance Tomorrow at 10:00 AM"
what: "Snap API update to improve order ingest performance ahead of peak"
impact: degraded
scope: "API, order ingest, all databases"
window_start: "2026-11-03T10:00:00Z"
window_end: "2026-11-03T10:30:00Z"
est_duration_min: 30
sender: "Ryan Ellis (ILG IT)"
message_id: "<CWLP265MB6737AEE0654DD0E80B577169A86A2@CWLP265MB6737.GBRP265.PROD.OUTLOOK.COM>"
slack_url: "https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1793693844443569"
slack_ts: "1793693844.443569"
notified_at: "2026-11-02T15:04:47Z"
posted_at: "2026-11-03T08:17:34Z"
session_id: 3550ca00-e900-415b-af5b-66d3b61d57f6
---
# Snap maintenance: API update, Tue 3 Nov

**BLUF: Snap API update, all databases, Tue 03 Nov 10:00–10:30 GMT. No downtime expected; order ingest disabled. No action required.**

- **WHAT:** Snap API update to improve order ingest performance ahead of peak
- **WHERE:** API · all databases
- **IMPACT:** System stays available. Order ingest disabled for all customers, suspended from 09:30 GMT. Up to 1 h for queued orders to flow after.
- **FUSE:** Order-ingest and Snap alerts in #bifrost-notifications from 09:30 GMT: likely this. Persisting after 11:30 GMT: investigate.
- **ACTION:** None.
- **NOTICE:** 18h 55m. First email reached the mailbox 2 Nov 15:04 GMT.
- **SOURCE:** Ryan Ellis (ILG IT) → SNAP Downtime, 02 Nov

The email gives a 30 min expected duration, so `window_end` is start plus 30 min. Package suspension starts 09:30. Ingest can take up to 1 h more to catch up.
