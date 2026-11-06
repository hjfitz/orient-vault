---
tags: [datadog-triage]
date: 2026-11-06
monitor: "[FUSE][Platform] Pub/Sub backlog building (any subscription)"
service: tracking-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793964267215019"
opened_at: "2026-11-06T11:23:10Z"
resolved_at: "2026-11-06T11:27:30Z"
minutes_spent: 4
severity_assessed: P3
flapping: true
outcome: real_minor
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# Pub/Sub backlog Warn on tracking-service create_record_request sales_order: a 486-line "store failed" burst (466 push 500s) at 11:20Z, third recurrence today and growing

## Fired
Monitor 302536090 (critical 1000, warning 200, `max(last_15m)`, P2) is Warn for `subscription_id:tracking-service.prod.create_record_request.sales_order.v1.sub`, value 355 (`search_datadog_monitors` status Warn; Slack post 11:24:27Z, ts 1793964267.215019, no replies by `slack_read_thread`; trigger time 11:23:10Z as supplied by the watcher, the events API returned 0 events for the monitor so it was not independently read). A shortened re-check was started; it left the known pattern (5xx, errors), so this is the full investigation.

## Alert posts in the family since 11:15Z
`slack_read_channel` C099WKQTE8G oldest 11:15Z returned three posts: snap-adapter deploy 11:16:43Z (not an alert), `[FUSE][Platform] Elevated production error rate` 11:21:44Z (monitor 180072217, outside the three-monitor family, ts 1793964104.264289, no reply), and this one. No post for 323648858 or 302511458 since 11:15Z. So one family alert, unreplied.

## Investigation
- Group peak and drain: per-minute max undelivered on the sub 11:18 to 11:22Z: 0, 0, 0, 0, 355 (11:22). Oldest-unacked max: 0, 0, 0, 0, 11 s (11:22), 0 (11:23). The undelivered series ends at 11:22Z (metrics lag about 4 min), so the undelivered count after 11:22 is not read. 24h hourly peaks of oldest-unacked: 24 s (09:00Z hour), 5 s (10:00Z hour), 11 s (11:00Z hour); of undelivered: 180, 573, 355 for the same hours.
- Different from the 10:xx pattern: push responses on this sub per minute: ack_204 62 (11:20), 1,400 (11:21), 141 (11:22), 1 (11:23); `unreachable_5xx_error_500` 417 (11:21), 49 (11:22), 0 (11:23). 466 in total; no 5xx on this sub in the 10:30 to 11:20 buckets. Other tracking subs 5xx in the 11:20 five-minute bucket: create_acknowledge.sales_order 12, create_record.sales_order 8; goods_out_confirmation subs only ack.
- Errors: tracking-service error/warn log patterns 11:00Z to now: one pattern, `store failed; nacking for redelivery`, 486 lines, 11:20:12Z to 11:21:03Z. By topic (analyze_datadog_logs): create_record_request 466 lines / 355 distinct event ids (11:20:12 to 11:20:48), create_record 8 / 7, create_acknowledge 12 / 10. All recordType sales_order. Error text on the three sampled lines: `rpc error: code = InvalidArgument desc = The referenced transaction has expired or is no longer valid.` By second: peak 98 at 11:20:13Z, tail of 1 to 3 per second to 11:20:48Z, single lines at 11:20:59 and 11:21:03. Attempts per event id: 268 events once, 94 twice, 10 three times. Dead-letter after 5 attempts (`lookup-service` operationalNotes), so none reached the limit within the logged attempts.
- Same signature as 00:55Z and 09:10Z (version b12d0a630c68596cd08de1afb501b91b9f43ed45, revision tracking-service-api-prod-00014-khz, same error text, sampled rows). Lines per burst: 4 (00:55Z), 225 (09:10Z), 486 (11:20Z) per the earlier records and this query. Same version on all three, so no new tracking-service deploy between them. `fuse.tracking.store.errors` reads 214 (11:20) and 1 (11:21) against 486 log lines; not reconciled.
- Ended: no tracking-service error line after 11:21:03Z (analyze_datadog_logs 11:21:04Z to now: 0 rows of any status); `store.errors` 0 for 11:22 to 11:26; Cloud Run tracking-service-api-prod 5xx: 485 (11:21), 1 (11:22), 0 (11:23 to 11:24, 11:25 and 11:26 not yet in the series); `fuse.tracking.events.ingested` 884 in the 11:20 minute (the burst) and 726 in the 11:25 minute with no store errors.
- Cloud Run saturation: instances 2 to 3 11:10 to 11:24; pending requests 0 in every bin 11:10 to 11:22; CPU p99 max 0.15 (11:22); memory p99 max 0.27; request concurrency p99 54.85 (11:21) and 59.95 (11:22), against 54.85 to 54.95 at the 11:12, 11:16, 11:17 batch minutes that had no errors. So not CPU, memory or queue saturation, and concurrency does not separate the burst from clean batches. Concurrency cap not read.
- Batch size: push ack_204 per 5 min on this sub 10:30 to 11:15Z: 2,398, 2,337, 2,253, 2,178, 2,115, 2,052, 1,956, 1,884, 1,815, 1,721 (falling); dedupe-service "Incoming record received" sales_order per 5 min 10:50 to 11:25Z: 2,115, 2,052, 1,960, 1,880, 1,815, 1,721, 1,604, 1,476 (the 11:25 bin may be partial). So the batch is falling, not growing.
- Duplicates: dedupe "Record dropped" / incoming per 5 min: 2,089/2,115, 2,004/2,052, 1,926/1,960, 1,826/1,880, 1,778/1,815, 1,706/1,721, 1,569/1,604, 1,457/1,476 (97.8% to 99.1%). Still about 98% duplicates.
- Sibling subs: collector `create_record_request_sales_order` and dedupe_service `create_record_request_sales_order` undelivered 0 at 11:18 to 11:22Z, so the Warn is the tracking sub only; those consumers are not affected.
- Dead-letter depth: `num_undelivered_messages` max 0 over 11:18 to 11:22Z on all `tracking-service.prod.*.dlt.sub` (metrics lag about 4 min).
- Held: `replay-list-failures` (production) newest overall: 10 PURDYFIGG goods_out_confirmation at 10:50:39 to 10:50:41Z (Shopify fulfilment order CLOSED, confirmation.delivery_shopify); newest sales_order failure 2026-11-05T17:20:05Z (WILDSMITH, wms_precheck). Nothing new, nothing Fuse could not submit to Snap. Not Snap related; maintenance check and Step 2b not applicable.
- Flapping: this sub also went Warn at 10:03Z today (earlier record) and recovered at 10:48:30Z (channel post 1793962110.724479).
- Resolved service: `lookup-service tracking-service` (Go, Firestore, Cloud Run, push subs; 500 only on a store error).

## Not established
- Whether the 355 nacked create_record_request events were all stored on redelivery: no success log exists to search for an event id (one id searched, 0 hits), and the undelivered series ends at 11:22Z. Oldest-unacked 0 at 11:23Z, no error line since 11:21:03Z and no 5xx at 11:23Z point to completion but do not prove it.
- Why the store write failed: the error text is the whole evidence (a transaction reported expired or no longer valid). Ingest volume in the 11:20 minute (884) is below the 11:05 minute (958) with no errors, so volume alone does not explain it. No Firestore-side logs or metrics were read.
- Why the bursts are growing (4, 225, 486 lines) and why they hit at 09:10Z and 11:20Z but not in other batches.
- Cloud Run concurrency setting for tracking-service-api-prod.
- Undelivered, DLT and Cloud Run 5xx after about 11:23Z (metric lag about 4 min); Slack/Datadog trigger time 11:23:10Z not independently read.
- Whether the monitor 180072217 post (11:21:44Z) has been answered elsewhere; this thread read showed no reply.

## Outcome
Real minor, P3, no escalation. A burst of tracking-service store-write errors over about 50 s returned 466 push 500s; 355 distinct sales_order events were nacked and redelivered, none dead-lettered in the window, nothing held, collector and dedupe unaffected. The error stopped at 11:21:03Z. This is the third burst today on the same version with growing volume, so tracking-service owners should look at the Firestore store write; a defect ticket is warranted but not filed here. The monitor is not mistuned: it fired on a real 355 peak. DRAFT_REPLY returned to the watcher for posting.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793964267215019
- Monitor: https://app.datadoghq.com/monitors/302536090
- Related: Monitors/2026-11-06-platform-elevated-prod-error-rate-tracking-service-store-0910.md, Monitors/2026-11-06-platform-elevated-prod-error-rate-tracking-service-store-0055.md, Monitors/2026-11-06-pubsub-backlog-building-tracking-service-create-record-request-sales-order.md
