---
tags: [datadog-triage]
date: 2026-10-19
monitor: "[FUSE][Replay Service] 5xx rate high (console/ingest availability)"
service: replay-service
business_id: STUBBLE
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792437068351549"
opened_at: "2026-10-19T19:09:48Z"
severity_assessed: P4
flapping: false
outcome: self_resolved
escalated_to:
ticket:
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: open
---
# Replay-service 5xx rate tripped by a single 500 on low volume

## Fired
Warn at 19:09:48Z, metric value 2.857 (1 5xx in ~35 requests over 15m, threshold 5).

## Investigation
- gcp.run.request_count for replay-prod by response_code, 6h: one 500 (minute 19:06), 204s x42 at ~15:40-15:50Z with no 5xx.
- Logs: 19:06:06Z POST /event/confirmation-made 500, STUBBLE goods_out_confirmation, corr 34d56c1b, `Failed to soft-delete records from collection failures: read ECONNRESET`. Later STUBBLE confirmation-made calls returned 200 (19:06:39, 19:10:06).
- 7d 5xx total 3: 2 on 2026-10-15 ~09:16Z (confirmation-made, "Cannot set property name of  which has only a getter", version 43380ebd), 1 today. Not flapping.
- Deploy: version bb2a9981 to 66ca610c between 16:27Z and 16:44Z; no change_tracking events in 24h; instance count 1 throughout 16:13-19:09Z.
- Not the subagent deletes or INC-39: no 5xx in the delete window.

Not established: whether the failed message was redelivered and succeeded; what reset the DB connection (no Mongo-side check); the monitor's recovery time.

## Outcome
Transient DB connection reset on one Pub/Sub push; no action. Monitor is ratio-based on ~2 req/min so one 500 can exceed 5%; retune (minimum request count) is a candidate if it recurs. Status left open until the monitor is seen to recover.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792437068351549
