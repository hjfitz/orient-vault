---
tags: [datadog-triage]
date: 2026-10-22
monitor: "[FUSE][Snap Adapter] API latency threshold breached"
service: snap-adapter
business_id:
snap_instance: ilg001, ilg004
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792710144953989"
opened_at: "2026-10-22T23:01:08Z"
resolved_at: "2026-10-22T23:05:00Z"
minutes_spent: 4
severity_assessed: P4
flapping: true
outcome: vendor
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# ilg001 + ilg004 Snap API latency >5s (repeat, midnight BST)

## Fired
Monitor 179927768 at 23:01Z on ilg004 (new post) and ilg001 (no new post; replied in the 19:02 BST ilg001 thread https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792692146672599). The alert time was 22 Oct 23:01Z, not after midnight UTC.

## Investigation
- Latency since 17:04Z: ilg001 1.3-19.6s, ilg004 1.6-13.5s (2-min avgs); ilg002/003/005 140-310ms. 22:40Z 20-min bucket 13.0s (ilg001), 9.3s (ilg004).
- Polls since 17:04Z: ilg001 1074 ok, ilg004 2684 ok, 0 failures.
- No timeout/5xx/404/circuit lines for ilg001/ilg004 since 20:03Z. One snap_adapter error in 3h: DOCKBAY `schema_validation`, `ShipAddress.0.City` >30 chars, sales_order UK-909735 (CS62539), held 21:02:39Z. Other 8 DOCKBAY orders in the redrive created fine. @fuse-support pinged.
- Holds in 4h: PURDYFIGG 35, DOCKBAY 1.
- No Maintenance/ record covers 22-23 Oct.

## Outcome
Vendor P4 for latency, no action. DOCKBAY hold is a data fix + replay for support.
Not established: DOCKBAY host mapping (fuse MCP auth rejected).

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792710144953989
