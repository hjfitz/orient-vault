---
tags: [datadog-triage]
date: 2026-10-20
monitor: "[FUSE][Platform] Pub/Sub ack-deadline headroom eroding (tracking-service...confirmation_data_failure.goods_out_confirmation.v1.sub)"
service: tracking-service
business_id: 
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792488183400329"
opened_at: "2026-10-20T09:21:39Z"
resolved_at: "2026-10-20T09:30:00Z"
minutes_spent: 9
severity_assessed: P4
flapping: false
outcome: self_resolved
escalated_to:
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# [FUSE][Platform] Pub/Sub ack-deadline headroom eroding (tracking-service...confirmation_data_failure.goods_out_confirmation.v1.sub)

## Fired
Oldest unacked 183 s on the tracking-service goods_out failure sub.

## Investigation
- tracking-service store = Firestore `tracking-service` db, location europe-west2 (gcloud firestore databases describe); no Redis/Mongo (Fuse MCP lookup-service).
- 572 publishes on bifrost.prod.confirmation_data_failure.v1 in one 4m bucket (vs 0-48); replay-service stored 572 goods_out_confirmation failures 09:15:34-09:16:14Z: PURDYFIGG 502 (314 distinct records, reason "Fulfillment order ... is CLOSED in Shopify"; 596 such failures today), STUBBLE 52 (sftp 412 write failures, per 306134015 thread), SAIRA 18.
- tracking-service: 945 "store failed; nacking for redelivery" 09:15:49-09:18:27Z, all confirmation_data_failure/goods_out_confirmation, all Firestore Aborted (cross-transaction contention); 215 on daily insights doc `_all__2026-10-20`.
- Push responses on the goods_out sub: 884 remote_server_5xx, 61 deadline_exceeded, 55 unreachable. Backlog peaked 376, drained to 0 by ~09:22Z. DLT holds 8 (from ~09:23Z), 4 events visible in logs with 5 failures.
- No tracking-service errors after 09:18:27Z.

Not established: whether the failures duplicate already-delivered confirmations; what re-sent them at 09:15; which 8 message ids are in the DLT.

## Outcome
Same cause as tracking push 5xx; drained. Linked to INC-40 (https://gfsdeliver-eng.slack.com/archives/C0CAEGABJBF). Read-only; nothing restarted or replayed.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792488183400329
- Incident: https://gfsdeliver-eng.slack.com/archives/C0CAEGABJBF
