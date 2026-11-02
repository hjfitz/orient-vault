---
tags: [datadog-triage]
date: 2026-11-02
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: snap-adapter
business_id: PURDYFIGG
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793636268775249"
opened_at: "2026-11-02T16:16:37Z"
severity_assessed: P3
flapping: true
outcome: real_minor
session_id: 7198be0e-f4de-4cae-8e32-ef4ac0c4cdb9
status: resolved
---
# 16:16Z firing: 32 PURDYFIGG snap_adapter slot_timeouts during an 85-order Shopify burst; all 85 orders created

## Fired
More than 2 domain:fuse error logs in 2m. Same failure mode as 14:38Z and 29 Oct (snap_adapter slot_timeout, transient:true). Not a new service or failure mode; PURDYFIGG sales_order was the 29 Oct 16:10Z business (126 errors), so 32 is smaller.

## Investigation
- Monitor query (@domain:fuse status:error @environment:prod), 16:05-16:35Z, per minute: 16:15 = 24, 16:16 = 8, nothing else. All snap_adapter, PURDYFIGG, sales_order, slot_timeout, transient:true. No other service, business or failure mode. No further errors since (checked to now).
- Trigger: shopify-connector bulk reap at 16:15Z published 631 sales orders (one correlationId 6b19b60f); dedupe dropped 546 and passed 85 (16:15). 5 min earlier a 548-order reap passed 75 (16:10) with no errors.
- snap_adapter PURDYFIGG per minute: 16:15 24 x 503 + 24 failed; 16:16 74 x 204, 8 x 503, 73 created, 1 already exists; 16:17 11 created.
- Per-recordId (85 distinct, 16:14-16:40Z): 32 failed once, then 31 "Entity created in SNAP" and 1 "Entity already exists" (#6643647). 53 never failed. 84 created + 1 existing = 85; none held. 85 create acks reached shopify-connector (74 at 16:16, 11 at 16:17).
- Snap latency (snap.poll.request.latency.avg, prod-wide, 2m rollup, 15:56-16:30Z): 4.6-6.8s, no per-host tag; ilg004/ilg003 latency monitors were already Alert at 16:03/16:11Z.
- Size: 32 vs 7 (14:38Z), 126 PURDYFIGG (29 Oct), 53 SPORTLUX, 51 DB5. slot_timeouts today: SPORTLUX 21 (08Z), DOCKBAY 7 (14Z) + 8 (15Z), PURDYFIGG 32 (16Z).

## Update (16:56Z, firing at 16:51:37Z, third wave)
- Monitor query per minute, 16:40-17:30Z: 16:50 = 34 (PURDYFIGG 33, ESCENTRIC 1), 16:51 = 6 (PURDYFIGG). Nothing before or after (checked to ~16:55Z). All snap_adapter, sales_order, slot_timeout, transient:true, deliveryAttempt 1. 40 errors, 40 distinct records, one failure each.
- Size vs earlier waves: 32 (16:15), 101 errors/49 records (16:35), 40/40 (16:50). Not monotonically growing.
- Per-recordId join (first error after 16:49Z vs first "Entity created"/"already exists"): 40 of 40 created, longest first-error-to-created 84.5s, last created 16:52:11Z. Nothing pending. The only deliveryAttempt >= 2 log 16:48-17:10Z is one ESCENTRIC "already exists" (attempt 2); no attempt >= 4.
- snap_adapter create_record_sales_order sub oldest_unacked 1-min: 16:50 0, 16:51 0, 16:52 54, 16:53 103s (peak so far; points after 16:53 not yet reported). Well under 248s peak and 300s deadline (Terraform default, not read back).
- shopify-connector PURDYFIGG "Bulk reap completed" total per 5 min: 478, 548, 631, 705, 777, 836, 893, 968, 1042, 1117 (16:05-16:50Z). Still rising (+75 last step).
- ilg005 snap.slot_queue_depth still 24 (16:50, 16:52).
- Verdict unchanged: real_minor, P3. Waves recur at about 16:15, 16:35, 16:50 with the reaps; each self-heals on redelivery.

## Not established
Final oldest-unacked peak after 16:53Z (metric lag). Whether Snap slowness or our own 30s slot cap drove the timeouts: Fuse MCP is down (401), so no host resolution or direct probe; latency metric has no host tag. Per-error timeout message text was not read this run.

## Outcome
Real minor, P3, self-healed on redelivery. Nothing held, no support ping. Recurring slot_timeout on bulk bursts (SPORTLUX, DOCKBAY, PURDYFIGG all today) is a tuning/capacity lead, not ticketed here.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793636268775249
