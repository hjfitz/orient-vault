---
tags: [datadog-triage]
date: 2026-10-09
monitor: "[FUSE][Egress] Shopify confirmation delivery failing (fulfilment / order-tag)"
service: shopify-connector
business_id: SAIRA
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1791450652797589"
opened_at: "2026-10-08T09:10:52Z"
resolved_at: "2026-10-09T09:45:00Z"
minutes_spent: 12
severity_assessed: P3
flapping: true
outcome: real_minor
escalated_to:
ticket:
session_id: 0a6fab47-9201-4b91-aea7-e306bf321ad2
status: open
---
# Shopify confirmation delivery warn: three SAIRA orders looping on missing fulfillment ID

## Fired
Monitor 303425509 (warn 1, crit 5, sum over 15m) has been in Warn continuously. The thread parent is the 10-08 10:10 BST "downtime ended" re-notify (value 5.0). 100+ alert events in 2 days.

## Investigation
- Confirmed: every failure is SAIRA `Confirmation dispatch failed: Unable to confirm order: Line item has no fulfillment ID` (shopify-connector prod `1d71e08`, shop `fb1ba1.myshopify.com`). No vendor/5xx errors.
- Confirmed: exactly three orders loop, one attempt per ~12 min poll: `14509447840119` (SAIR35998F912D9), `14508669436279` (SAIRA470EC2D5DC), `14509885391223` (SAIRCA3819D2EA9). First failures 2026-10-05 13:18-14:12Z, ~460 attempts each, still failing 10-09 09:42Z. All stage-90 despatches dated 10-02/03, so about four days unfulfilled in Shopify.
- Confirmed: flat ~15 failures/hr (metric `fuse.confirmation.forward.failure`), only businessid `saira`; order-tag failure metric is empty. Four other SAIRA orders failed 7-8 times on 10-05 (last 12:48-12:58Z) and then stopped. Corrected later: they did not succeed. They have the same SNAP-only extra line, no success dispatch is logged and replay holds their failures (attempts=0).
- Hypothesis, not verified per order: the missing-fulfillment-ID gap (line's Shopify ref never written at create time), tracked as FUSE-1118 (Backlog). The throw is swallowed by `Promise.allSettled` and never reaches `confirmation_data_failure`.
- No Customers/SAIRA folder exists, so no customer context was read.

## Outcome
P3, real-but-minor, one customer, three orders, stable. Verdict posted in-thread with broadcast. No monitor change.

Follow-up 2026-10-09 (repair-shopify-confirmation): classified as NOT repairable. Each routing doc lacked exactly one price-0 line (MC1 x3 / HFO10 x1 / MC1 x3) that SNAP held but the collector (one version per order) never carried, so no Shopify fulfilment id exists. On Harry's go-ahead the three queue records (SIOB000925, SIOB000937, SIOB000951) were marked processed; queue verified empty, nothing written to the routing store. Update posted in-thread as the support bot. The three orders remain unfulfilled in Shopify. Owed: someone to fulfil them by hand if wanted, add the SNAP-only-line mechanism to FUSE-1118, and retune the warn threshold in `observability` (Terraform-managed, needs plan-then-proceed).

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1791450652797589
- Earlier same-monitor triage: [[2026-10-02-shopify-confirmation-delivery-failing-purdyfigg]]
- Ticket: FUSE-1118 (existing, not commented)
