---
tags: [datadog-triage]
date: 2026-10-12
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: snap-adapter
business_id: PURDYFIGG
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1791817359746069"
opened_at: "2026-10-12T15:01:37Z"
severity_assessed: P3
flapping: true
outcome: real_minor
ticket:
session_id: 92cde6e7-cd20-485a-a571-f3794eb6ada4
status: open
---
# Platform error-rate monitor: snap-adapter slot_timeout burst on top of a chronic PURDYFIGG retry loop

## Fired
More than 2 prod error logs tagged `domain:fuse` in 2 minutes. Monitor 180072217 had 19 alert events in the previous 24h (about 10 trigger/recover cycles), and 6 more firings were folded into this one.

## Investigation
- Confirmed: every matched error is `snap_adapter` (127 in 3h), nearly all PURDYFIGG. A vendor outage was not seen.
- This firing (15:00-15:01Z): 77 transient `slot_timeout` errors ("Timed out after 30000ms waiting for a concurrency slot", 503 so Pub/Sub retries) during a PURDYFIGG Shopify sales_order bulk wave. In the same window 249 entities were created and 75 already existed. Errors stopped at 15:01:19Z.
- Flapping baseline: PURDYFIGG #6519006 `schema_validation` (`ShipAddress.0.Name` over 50 chars), non-transient, retried every 5 min, which sits just under the threshold. Ops already know about it from the #bifrost-general write-up.
- A separate P2 `snap.entity_not_created` monitor fired at the same time on 4 one-off `snap_api_error` rejections (PURDYFIGG, DOCKBAY, EPARFUM, BYOMA).
- Hypothesis, unverified: the Snap concurrency cap (3 instances x 5) was saturated by the burst. Snap latency was not checked.

## Outcome
Real but minor, self-resolved. A verdict was posted in-thread with a broadcast. No ticket filed. Owed: ops fix the ship-to name on #6519006, and optionally retune the monitor (Terraform-managed, `observability` repo) to exclude known non-transient PURDYFIGG schema_validation failures.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1791817359746069
- Monitor: https://app.datadoghq.com/monitors/180072217
