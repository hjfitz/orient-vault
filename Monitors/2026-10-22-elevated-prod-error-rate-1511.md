---
tags: [datadog-triage]
date: 2026-10-22
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: snap-adapter
business_id: PURDYFIGG
snap_instance: ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792681964176819"
opened_at: "2026-10-22T15:11:37Z"
resolved_at: "2026-10-22T15:14:57Z"
minutes_spent: 3
severity_assessed: P4
flapping: false
outcome: self_resolved
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# Prod error-rate monitor tripped by 3 PURDYFIGG snap-adapter slot timeouts, all recovered on retry

## Fired
Monitor 180072217 (more than 2 `domain:fuse` error logs in 2m, excluding snap_adapter `transient:false`) triggered at 15:11:37Z.

## Investigation
- The monitor's own query, run by service and minute from 14:00Z, returned only snap_adapter: 1 error at 15:10 and 2 at 15:11.
- All 3 were `Entity creation in SNAP failed`, `failureMode:slot_timeout`, `transient:true`, `deliveryAttempt:1`, for PURDYFIGG sales orders #6576722, #6576659 and #6576671. They were Shopify-sourced, site 0010 BRACKMILLS2, and the host is ilg005liveapi (DB5, BM2).
- On attempt 2, at 15:11:30–40Z, each logged `Entity already exists in SNAP` (precheck) and a 204. Snap `snap-get-shipment PURD302CB7E4D9F` returned the order (#6576671) at Stage 10, created at 15:10:42Z.
- snap-adapter create volume was 73 in 15:11Z, a Shopify wave. Waves also came at 15:00 and 15:05.
- Metrics, 5-min buckets from 14:55 to 15:20Z: `snap.slot_queue_depth` max was 22.5, and 16.5 around the burst. `snap.request.latency.max` was 2.7–5.4s. The latency metric has no host tag.
- Transient snap_adapter errors over 7 days: PURDYFIGG had 3 slot_timeouts today (all of these). The day before, 21 Oct, had circuit_open, slot_timeout and snap_api_error for PURDYFIGG and STUBBLE; 19 Oct was heavier.
- Maintenance: the 2026-10-19 record puts DB5 on 29 Oct at 10:00Z, so no window covered 15:11Z today.
- Monitor history over 24h: it fired at 08:34Z (recovered 08:56Z) and at 15:11Z. That is not flapping.
- Replay-service prod holds created since 15:00Z: 6, all PURDYFIGG sales_order, `create.wms_precheck`, `ShipContacts.LastName - Too big: <=30 characters`. They cover 2 records. #6506667 has 11 holds since 14:20Z and #6575295 has 8 since 14:35Z. These are `transient:false`, so the monitor excludes them and they did not trip it.
- Not established: per-host Snap latency, and why attempt 1 timed out after the shipment already existed in Snap.

## Outcome
Self-resolved, P4. Posted in the thread with @fuse-support pinged for the 2 held LastName-length orders, which are a separate data issue that needs fixing and a replay. No ticket.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792681964176819
- Reply: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792682097683469
