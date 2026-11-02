---
tags: [datadog-triage]
date: 2026-10-12
monitor: "[FUSE][Shopify Connector] Confirmation lines skipped — prod"
service: shopify-connector
business_id: SAIRA
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1791818159613719"
opened_at: "2026-10-12T15:14:56Z"
resolved_at: "2026-10-12T15:18:00Z"
minutes_spent: 3
severity_assessed: P4
flapping: false
outcome: real_minor
escalated_to:
ticket:
session_id: 92cde6e7-cd20-485a-a571-f3794eb6ada4
status: resolved
---
# SAIRA: 12 despatched lines with no Shopify reference skipped in one burst

## Fired
Warn on `fuse.confirmations.lines_skipped` (sum last 1h, group businessid:saira) = 12. The monitor warns at >= 1; the critical threshold in the query is 1,000,000.

## Investigation
- Logs `service:shopify-connector @environment:prod "Lines with no Shopify reference skipped"`: 9 warn logs, 15:14:07-15:14:15Z, all SAIRA, `skippedCount` sums to 12 (matches the metric). DDSQL hourly count over 7d returns only the 15:00Z hour.
- Metric over 24h: one data point (15:00Z, 12), SAIRA only.
- Monitor events (3d): 1 alert event. Monitor created 2026-10-12 14:08Z. Not flapping.
- Same window, SAIRA: 9 `Confirmation processed` and 9 `Confirmation dispatched successfully` (log patterns).
- Skipped SKUs HFO10, NCO10, MC1, 1-2 of 3-6 lines per order. Snap (ilg004, SAIRA) shipments SAIR2286ED85FF6 and SAIRCA3819D2EA9: skipped line is the last line, Price 0, Discount/TaxRate explicitly 0, later-created Snap line id than the other lines. Consistent with a warehouse-added item.
- Is it us or vendor: no errors involved, no vendor failure.

Not established: whether the skipped SKUs are on the matching Shopify orders (Shopify not readable); whether skips occurred before today (monitor created today, log line first-ship date unchecked).

## Outcome
Real but minor, monitor working as designed. Verdict posted in thread. Ops to spot-check the 9 orders against Shopify. No ticket, no monitor change.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1791818159613719
- Monitor: https://app.datadoghq.com/monitors/331502396
