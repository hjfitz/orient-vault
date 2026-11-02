---
tags: [datadog-triage]
date: 2026-10-20
monitor: "[FUSE][Platform] create_data_failure spike"
service: snap-adapter
business_id: PURDYFIGG
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792498642951699"
opened_at: "2026-10-20T12:16:07Z"
resolved_at: "2026-10-20T12:19:57Z"
minutes_spent: 4
severity_assessed: P4
flapping: false
outcome: real_minor
escalated_to:
ticket:
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# create_data_failure warn: two PURDYFIGG orders rejected on every reap (Email MANDATORY)

## Fired
Monitor 302536087 went to Warn at 12:16Z: the sum over 15 minutes was 6, against a warn threshold of 5 and an alert threshold of 20. It is a follow-on to the 11:37Z trigger (25), which recovered at 11:49Z (5).

## Investigation
- **Metric:** `gcp.pubsub.topic.send_request_count{topic_id:bifrost.prod.create_data_failure.v1}` at 1-minute resolution, 11:32–12:05Z. It shows 3 and 22 at 11:32–11:33, then 2 roughly every 4–5 minutes.
- **Logs:** snap_adapter `Entity creation in SNAP failed` from 11:45Z to now returns 14 lines.
  - All 14 are PURDYFIGG, and all are records `#6565591` and `#6531052`. The exclusion query returns 0.
  - They come in pairs under 7 correlationIds about 5 minutes apart, which is the Shopify reap cadence.
- **Reason:** `fieldErrors` gives `CONTACT_UPDATE Email MANDATORY` with an empty value, on lines SGC834M64Y and SGC832ZYC9. `errors[].retryable` is false.
- **History:** these two records have 35 rejections since 2026-10-18. The first was at 11:31:55Z today.
- **Not established:** whether the two orders are an INC-40 knock-on. The first rejection followed the ingest resume, but the cause is missing data. Replay-service holdings were not checked.

## Outcome
Real but minor, P4. The failures are a data rejection that recurs on every reap and will keep the monitor at warn until the orders have a contact email. @fuse-support was pinged to fix the email and replay. No ticket was filed, and no replays or releases were done.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792498642951699
- Earlier trigger thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792496249354999
