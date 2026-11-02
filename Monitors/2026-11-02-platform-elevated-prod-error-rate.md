---
tags: [datadog-triage]
date: 2026-11-02
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: snap-adapter
business_id: DOCKBAY
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793630386889499"
opened_at: "2026-11-02T14:38:37Z"
severity_assessed: P3
flapping: true
outcome: real_minor
session_id: 7198be0e-f4de-4cae-8e32-ef4ac0c4cdb9
status: resolved
---
# 14:38Z firing: 7 DOCKBAY snap_adapter slot_timeouts as the REST stream resumed with a 110-order burst; 1 record held on a permanent create failure

## Fired
More than 2 domain:fuse error logs in 2m. Same failure mode as 29 Oct (snap_adapter slot_timeout), but a new business (DOCKBAY, sales_order) and much smaller (7 vs 53 / 126 / 22 / 51). Not a new service or failure mode.

## Investigation
- Monitor's own query, 14:25-14:50Z: 7 errors, all snap_adapter, DOCKBAY, sales_order, slot_timeout, transient:true, "Timed out after 30000ms waiting for a concurrency slot". 3 at 14:37, 4 at 14:38, none 14:39-15:10. No other service errored in that window.
- Trigger: DOCKBAY's REST stream (silent from 10:43Z per the earlier thread) resumed: rest_connector 110 x `POST /api/v2/sales-orders` 202 at 14:37Z, dedupe 111 incoming at 14:37Z, snap_adapter creates 28 at 14:37 and 80 at 14:38.
- Each timeout returned 503 to the dedupe-forwarded create (7 x 503). All 7 recordIds (UK-911963, 911965, 911968, 911971, 911975, 912049, 912065) logged "Entity created in SNAP" at 14:37-14:38Z after the failure.
- Accounting 14:36-15:10Z DOCKBAY snap_adapter: 110 create requests accepted (204), 108 distinct recordIds created, 1 already exists, 1 not created (UK-911960).
- UK-911960: "Entity creation in SNAP failed", "Unable to parse data", schema_validation, transient:false at 14:37:09Z (excluded from the monitor). Dedupe logged "Dedupe gate held on permanent failure" 14:37Z; failure stored in replay-service. The same failure mode hit WAIT12005-7-DISPATCH / PO573058 at 09:21Z. Not read: the Snap error detail.
- Snap latency (snap.poll.request.latency.avg, prod-wide, 1m): 2.4-12.1s per minute 14:26-14:36Z (12.1s at 14:33, 5.2s at 14:36). Data ends before the 14:37 burst.
- Flapping: monitor fired many times 28-29 Oct and again today.

## Not established
Whether Snap slowness or our own 30s slot cap drove the timeouts (Fuse MCP 401: no host resolution or probe; latency metric has no per-host tag and ends before the burst). Why DOCKBAY stopped at 10:43Z and resumed at 14:37Z. What field failed "Unable to parse data" on UK-911960 and PO573058, or whether PO573058 is still held.

## Outcome
Real minor, P3. The 7 timeouts self-healed on redelivery. One DOCKBAY order (UK-911960) is held after a permanent Snap create failure and needs its data fixed and replayed (support ping).

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793630386889499
