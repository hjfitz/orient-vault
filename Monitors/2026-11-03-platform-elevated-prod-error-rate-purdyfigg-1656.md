---
tags: [datadog-triage]
date: 2026-11-03
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: snap-adapter
business_id: PURDYFIGG
snap_instance: ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793725064374449"
opened_at: "2026-11-03T16:56:37Z"
severity_assessed: P4
flapping: true
outcome: real_minor
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# 16:56Z firing: 4 PURDYFIGG snap_adapter slot_timeouts in a 1289-order Shopify reap; all 4 orders created in Snap within 43s

## Fired
More than 2 domain:fuse error logs in 2m. Same failure mode as the 2 Nov waves (snap_adapter `slot_timeout`, `transient:true`). No customer record held.

## Investigation
- Monitor query, 16:40Z to now: 4 matches, all snap_adapter, PURDYFIGG, sales_order, "Timed out after 30000ms waiting for a concurrency slot", failureMode slot_timeout, transient true, deliveryAttempt 1, exhausted false, 16:56:09-16:56:13Z. One correlationId, 67f110e1-184f-41cc-a640-0a085663a198.
- Trigger: shopify-connector "Bulk reap completed" at 16:55:14Z, published 1289 of total 1289, same correlationId 67f110e1. The two earlier reaps were 1164 (16:45Z) and 1182 (16:50Z). snap_adapter PURDYFIGG create_record sales_order POSTs per minute: 16:50 24, 16:51 5, 16:55 1, 16:56 115, 16:57 1.
- Per-recordId join for the four failed records (#6650847, #6650877, #6650886, #6650869): each got a 503 at attempt 1, then 16:56:41Z #6650869 "Entity already exists in SNAP" (attempt 2), 16:56:49Z #6650877 created, 16:56:52Z #6650847 and #6650886 created. 4 of 4 landed, longest first failure to success 42.6s. After 16:56:30Z the only PURDYFIGG snap_adapter create/fail logs are creates (94 at 16:56). No failures after 16:56:13Z in the queries run at about 17:00Z.
- ilg005: PURDYFIGG's prod host is https://ilg005liveapi.snapfulfil.net (Fuse MCP get-snap-connection); lookup-snap-instance puts ilg005 at Snap DB 5, site 0010 Brackmills 2.
- Per-business (snap_adapter errors, last 24h): slot-timeout 62 logs for PURDYFIGG (2 correlationIds), no other business. ESCENTRIC, DOCKBAY, SAIRA and STUBBLE errors that day are other messages ("Unable to parse data", "Snap rejected the creation of an entity"), not slot timeouts.
- Hourly slot-timeout errors, 7 days (snap_adapter, any business): PURDYFIGG 27 Oct 12+4, 28 Oct 2+73, 29 Oct 197, 30 Oct 6+9, 2 Nov 172+58, 3 Nov 4; SPORTLUX (28, 29, 30 Oct, 2 Nov), DOCKBAY (28 and 30 Oct, 2 Nov) and ICONICL (30 Oct) also had slot timeouts.
- ilg005 Snap request latency (snap.request.latency.95percentile, snap_host ilg005, 3-min buckets): 1.8-2.4s at 16:51-16:57Z, 2.2-3.3s at 16:30-16:48Z; hourly max of p95 9.0s in the 16:00Z hour vs 1.3-3.2s from 23:00Z to 06:00Z; 2 Nov 16:00Z hour 37.3s and 17:00Z hour 24.0s. snap.slot_queue_depth hourly max on ilg005 was 24 in the 15:00Z and 16:00Z hours today, and 24 in 3 of the hours on 2 Nov.
- Direct probe at about 16:59Z, 5 read-only GETs of /v2/snaplookups/RECSTATUS on ilg005 with PURDYFIGG's credentials: HTTP 200 each, 62-85 ms total. After the burst, so it says the host is up, not what it did at 16:56Z.
- Maintenance: the 3 Nov API update window was 10:00-10:30Z (Maintenance/2026-11-02-snap-api-update.md), ended 6h26m before this firing. Not a cover for this.
- Flapping: 19 alert/recovery events for monitor 180072217 in 48h (search_datadog_events). Of the monitor query's matches in 48h, 271 are snap_adapter slot timeouts; the rest by service are shopify-connector 6, config-service 3, sftp_connector 3, rest_connector 1. Monitor is tagged managed-by:terraform (observability repo).

## Not established
Whether Snap's own slowness or our 30s slot cap drove the four timeouts: the Snap latency is host-level p95 only, there is no per-request timing for the 16:56Z POSTs and no spans for snap_adapter (zero spans in the last 30m), and the probe ran after the burst. The adapter's slot cap value was not read. Whether other businesses share ilg005 (lookup-snap-instance returned businessCount 0 for every instance, so it could not list them). Which hosts SPORTLUX, DOCKBAY and ICONICL's slot timeouts were on. The sales order subscription oldest-unacked age (metric query returned no data).

## Outcome
Real minor, P4, self-healed on redelivery. 4 of 4 records created, nothing held, no support ping. Recurring slot_timeout during Shopify bulk reaps (PURDYFIGG, SPORTLUX, DOCKBAY, ICONICL) is a tuning/capacity lead; the monitor counts transient:true slot timeouts that redeliver cleanly. Not ticketed here.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793725064374449
- Monitor: https://app.datadoghq.com/monitors/180072217
