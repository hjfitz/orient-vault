---
tags: [datadog-triage]
date: 2026-11-09
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: snap-adapter
business_id: PURDYFIGG
snap_instance: ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794249167766929"
opened_at: "2026-11-09T18:31:37Z"
severity_assessed: P3
flapping: true
outcome: real_minor
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# Elevated production error rate: 4 slot_timeout 503s (4 PURDYFIGG orders) on Snap ilg005

## Fired
Monitor 180072217 matched 4 logs in 18:29:37Z-18:31:37Z (2 in the 18:30 minute, 2 in 18:31; timestamps 18:30:56Z to 18:31:09Z). All were snap_adapter "Entity creation in SNAP failed", businessId PURDYFIGG, failureMode `slot_timeout`, `transient:true`, `exhausted:false`, deliveryAttempt 1, errorMessage "Timed out after 30000ms waiting for a concurrency slot". Nothing else matched.

## Investigation
- Monitor query, DDSQL over 18:29-18:32Z grouped by service/businessId/failureMode/transient/exhausted/deliveryAttempt: one group, snap_adapter / PURDYFIGG / slot_timeout / true / false / 1, count 4. Four distinct refs: #6705385, #6705387, #6705398, #6705452.
- snap_adapter error logs 17:00Z to about 18:36Z: only these 4 (zero between 17:00 and 18:29Z). Today's slot_timeout totals by business (UTC day): PURDYFIGG 126, STUBBLE 2, ESCENTRIC 1. Max deliveryAttempt on any slot_timeout today is 2 (the 16:00 hour); no `exhausted:true` anywhere today.
- Per-record logs for the 4 refs: each has one "Entity creation in SNAP failed", one 503 on POST /events/v1/record/create/sales_order, then "Entity created in SNAP" and a 204.
- Read-only Snap ilg005 shipments search by CustomerRef for the 4 refs: 4 shipments, one each, Status 00, DateCreated 18:31:16 (#6705398), 18:31:19 (#6705452), 18:31:53 (#6705385), 18:32:05 (#6705387).
- replay-service, PURDYFIGG sales_order failures: newest held is 6 Nov 19:55Z; none from today and none for these refs. Separate held, non-transient Snap submission failures today (not part of this alert): ESCENTRIC 15335 and 15337 (field too long), DOCKBAY UK-914263 and PO573058 (16:38:45Z). Non-transient errors also logged today for SAIRA and AYMSTUDIO (snap_api_error), not examined.
- ilg005 (Snap DB 5, site 0010 Brackmills 2): snap.request.latency.avg per minute 3.3 s (18:30), 4.7, 4.9, 4.4, 5.0 (18:34), 3.5, 3.9 s; max 8.5 s at 18:30. Slot queue depth peaked at 24 in the 18:30 bucket, 0 by 18:34. Compare 16:36 wave: avg up to 11.0 s, max 14.6 s, 94 matches. Hourly Snap latency avg today: 4.0 s (08Z), 3.0-4.8 s 09Z-16Z, 3.6 s at 17Z and 18Z; 2.2-2.6 s the evening before.
- Cloud Run snap-adapter-prod: 5xx buckets total 4 (1 and 3, timestamps offset a few minutes from the logs); no 429 series after 17:03Z. Active instances (5 min max): 3 from about 15:35 to 17:20Z, 1 in every bucket 17:35-18:25Z, 3 in the 18:30Z bucket. p99 max concurrency per instance 31.98 in 3-instance periods.
- Backlog: oldest unacked on snap_adapter.prod.create_record_sales_order.v1.sub was 0 until 18:33, 7 s then 67 s, with 30 undelivered at the 18:34 point. Orders still arriving at 18:35Z (Entity created logs at 18:34 and 18:35).
- Timed read-only probes of ilg005 from this host at 18:34Z: 5 x GET snaplookups/RECSTATUS all 200 in 0.15-0.37 s; 3 x GET shipments top 1 all 200 in 0.27-0.47 s. The earlier 17:15Z thread reported intermittent 4 s responses, so one fast set is not proof the host is healthy.
- Maintenance vault: no record dated 9 or 10 Nov and none naming DB5 for today; latest is the 5 Nov emergency patch.
- Slack thread had no replies and no Recovered post when read. This monitor has triggered 4 times earlier today in the channel (15:22Z, 16:06Z, 16:31Z, 16:36Z per earlier replies); this is the 5th.
- slot_timeout per day over 7 d: 4 (3 Nov), 6 (6 Nov, DOCKBAY), 74 (8 Nov), 129 (9 Nov, all businesses).

## Outcome
real_minor, P3. 4 orders failed once with a transient slot timeout, were redelivered and are in Snap. Nothing held, nothing exhausted. This wave is much smaller than 16:36Z, but the monitor keeps flapping and the daily count is rising. A ticket on the adapter slot cap, burst intake and ilg005 latency remains warranted.

Not established: whether our slot cap or Snap's create latency held the slots; why ilg005 is slow; why the 4 timed out when instances were 1 versus 3 earlier (instance timing within the 18:30 bucket is not resolved); other businesses on ilg005; slot_wait metric (no series returned); #bifrost-general pin and ILG mail were not read; when this monitor recovers; the final state of the wave still arriving at 18:35Z.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794249167766929
