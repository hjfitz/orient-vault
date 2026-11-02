---
tags: [datadog-triage]
date: 2026-09-30
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: snap-adapter
business_id: SPORTLUX
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790757044810509"
opened_at: "2026-09-30T08:29:37Z"
severity_assessed: P3
flapping: true
outcome: monitor_mistuned
ticket:
session_id: e8017a60-9ced-4075-8946-6deeee593aa9
status: open
---
# Elevated error rate: SPORTLUX SNAP date rejections on top of a PURDYFIGG standing set

## Fired
Monitor 180072217 (>2 domain:fuse error logs in 2m) fired ~33 times in 24h; the 08:29 trigger came from SPORTLUX sales_orders.

## Investigation
- Confirmed: 7 SPORTLUX sftp sales_orders rejected by SNAP (400 validation) since 08:28 UTC; DateDueOut/DateShipment sent as `46295-01-01` (looks like an Excel serial read as a year).
- Confirmed: PURDYFIGG snap-adapter creation failures and shopify-connector "Line item has no fulfillment ID" account for most of the flapping volume.
- Hypothesis: SPORTLUX mapping passes an Excel serial date through unconverted. Not verified.

## Outcome
Verdict posted in-thread: real-but-minor, monitor chronically noisy. Owed: SPORTLUX date defect (create-defect) and retune to exclude the PURDYFIGG standing set (Terraform, observability repo).

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790757044810509
