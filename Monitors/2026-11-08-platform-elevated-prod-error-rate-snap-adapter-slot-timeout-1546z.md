---
tags: [datadog-triage]
date: 2026-11-08
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: snap-adapter
business_id: PURDYFIGG
snap_instance: ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794152865156769"
opened_at: "2026-11-08T15:46:37Z"
resolved_at: "2026-11-08T15:50:25Z"
minutes_spent: 4
severity_assessed: P3
flapping: false
outcome: real_minor
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# 33 snap_adapter slot_timeout error lines (PURDYFIGG) tripped the platform error-rate monitor, all orders created on redelivery

## Fired
Monitor 180072217 (log alert, count of `@domain:fuse status:error @environment:prod` minus four exclusions, last 2m, threshold > 2) went Alert at 15:46:37Z and Recovered at 15:48:37Z (monitor event 15:48:37Z). Same-second sibling: Snap Adapter entity-creation monitor 334832256 (triaged elsewhere).

## Investigation
- Per-service count with the monitor's own query, 15:40-15:50Z: snap_adapter 33, no other service. Per-minute count of all `@domain:fuse status:error @environment:prod` lines 15:30Z-15:49Z: snap_adapter 18 (15:45) and 15 (15:46), nothing else, nothing after 15:46:13Z.
- Grouped by service/message/businessId/failureMode/transient/correlationId: one group, snap_adapter, "Entity creation in SNAP failed", businessId PURDYFIGG, failureMode slot_timeout, errorMessage "Timed out after 30000ms waiting for a concurrency slot", transient true, correlationId 8b6d121e-8418-43f1-8f17-f60183a7b6a2, 33 lines, 15:45:40.6Z to 15:46:13.5Z, 33 distinct recordIds (#6694384 ... #6694570), deliveryAttempt 1. The 33 lines are why the monitor's `NOT(snap_adapter AND @transient:false)` exclusion did not drop them (transient is true).
- Shared cause with the Snap Adapter failures: yes, they are the same log lines. 334832256 counts distinct `@recordId` of `service:snap_adapter "Entity creation in SNAP failed"` over 15m (> 10); the same message gives 33 distinct recordIds in the window. 24h total of that message: 35 lines, 35 records.
- Same window, snap_adapter logs per minute: 94 "Incoming record received" at 15:45, 18 x 503 at 15:45 and 15 x 503 at 15:46 on POST /events/v1/record/create/sales_order (33 total), "Entity created in SNAP" 31 at 15:46 and 53 at 15:47.
- Outcome of the 33: per-recordId check over 15:40Z-now of "Entity creation in SNAP failed" vs "Entity created in SNAP": all 33 have exactly one failure and one creation, last creation at 15:47:39.664Z. No errors from any service after 15:46:13Z as of 15:49:29Z.
- Instance: get-snap-connection (production) PURDYFIGG host is ilg005liveapi.snapfulfil.net, lookup-snap-instance ilg005 = Snap DB 5, site 0010 Brackmills 2 (BM2); includeBusinesses returned businessCount 0 so other businesses on the instance not listed. Read-only snap-lookup RECSTATUS on that host at ~15:49Z returned 200 with data (response time not captured by the MCP).
- Metric snap.request.latency.avg (all hosts), 8 data points in 15:30-15:50Z: lowest 539 ms, highest 7824 ms (values 539, 4349, 3390, 3287, 2161, 7824, 6330, 4769); timestamps of the individual points not verified. snap.slot_queue_depth max per point 6 to 19.
- Maintenance: Maintenance/ records checked by grep for window fields; none has a window covering 2026-11-08 (latest windows 2026-11-05 10:00Z start, DB not DB5-related per filename; not read in full).
- 7-day history of "Entity creation in SNAP failed" slot_timeout: 2 Nov 230 PURDYFIGG, 21 SPORTLUX, 15 DOCKBAY, 1 ESCENTRIC; 3 Nov 4 PURDYFIGG; 6 Nov 6 DOCKBAY; 8 Nov 33 PURDYFIGG. Repeats on ilg005 hosts' businesses across days.
- Monitor firing history, 24h (monitor events): triggered 7 Nov 16:51Z, 7 Nov 19:52Z and 8 Nov 15:46Z, each recovered ~2m later. The 7 Nov firings are logged as separate causes (shopify), so not the same-cause flap.

## Outcome
Real but minor, self-recovered: a PURDYFIGG burst of sales orders hit snap-adapter's 30s concurrency-slot wait, 33 creates returned 503, Pub/Sub redelivered and all 33 were created by 15:47:39Z. Nothing held, no support action. This monitor firing and 334832256 share the same 33 log lines, so they are one cause.

Not established: why the slots were exhausted (burst size vs ilg005 latency vs the adapter's concurrency cap are not separable from what I read); timestamps of the latency datapoints; probe response time; that replay-service holds nothing for these (inferred from every record having a creation log, replay-service not queried); the other 15:44:49Z Pub/Sub warning's cause (other agent).

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794152865156769
- Monitor: https://app.datadoghq.com/monitors/180072217
- Sibling: [[2026-11-08-pubsub-ack-deadline-headroom-snap-adapter-sales-order-1543z]]
