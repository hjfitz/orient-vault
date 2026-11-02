---
tags: [datadog-triage]
date: 2026-10-29
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: snap-adapter
business_id: SPORTLUX
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793257670492449"
opened_at: "2026-10-29T07:06:37Z"
severity_assessed: P3
flapping: true
outcome: real_minor
session_id: 7198be0e-f4de-4cae-8e32-ef4ac0c4cdb9
status: resolved
---
# 53 SPORTLUX sales-order creates hit snap_adapter slot_timeout

## Fired
More than 2 domain:fuse error logs in 2m at 07:06:37Z. Monitor 180072217; 7th firing in about 24h (see 2026-10-28 record).

## Investigation
- Monitor query on logs 06:00-07:30Z: 53 errors, all snap_adapter, SPORTLUX, sales_order, slot_timeout, transient:true, 07:06:26-07:07:09Z (38 in the 07:06 minute, 15 in 07:07). No other service errored; no errors 23:00-07:00Z.
- SPORTLUX "Entity created in SNAP" distinct sales_order recordIds per minute: 20 (07:06), 92 (07:07), 36 (07:08).
- Yesterday's 17:21Z burst: 57 in the peak minute (73 over three minutes), PURDYFIGG.

## Not established
Redelivery of the 53 failed records (left to the 334832256 triage); Snap latency and host for SPORTLUX (Fuse MCP 401, metrics not queried); slot cap vs Snap latency as cause.

## Outcome
Real minor, P3. Reply posted (broadcast).

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793257670492449
