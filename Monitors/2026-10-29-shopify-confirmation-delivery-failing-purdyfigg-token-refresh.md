---
tags: [datadog-triage]
date: 2026-10-29
monitor: "[FUSE][Egress] Shopify confirmation delivery failing (fulfilment / order-tag)"
service: shopify-connector
business_id: PURDYFIGG
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793261528412669"
opened_at: "2026-10-29T08:10:49Z"
resolved_at: "2026-10-29T08:14:00Z"
minutes_spent: 4
severity_assessed: P3
flapping: false
outcome: self_resolved
escalated_to:
ticket:
session_id: 7198be0e-f4de-4cae-8e32-ef4ac0c4cdb9
status: resolved
---
# 5 PURDYFIGG goods-out confirmations failed on a Shopify token refresh returning HTML, all delivered on the 3rd attempt

## Fired
Monitor 303425509 (`sum(last_15m)` of `fuse.confirmation.forward.failure` + `fuse.order.tags.update.failure`, prod, `> 5`, P3) went Warn at ~08:10:49Z (value 4), then Alert at 08:13:07Z (value 10).

## Investigation
- 10 "Confirmation dispatch failed" logs, all goods_out_confirmation, all PURDYFIGG (purdy-figg.myshopify.com), 08:10:11-08:11:18Z, one correlationId ec002b30-882a-4d77-99ce-16be7ec88e0b. 5 distinct recordIds (14613311816060, 14613386887548, 14613472870780, 14613531132284, 14613561082236), 2 failures each. No other business had a dispatch failure in 24h, and no error type other than fulfilment dispatch (no order-tag failure logs).
- Every failure is paired with a "Token refresh failed" log 9ms earlier; error text `Unexpected token '<', "<html>\r\n<h"... is not valid JSON` (SyntaxError), i.e. the token refresh response was an HTML page. No HTTP status is logged. One earlier "Token refresh failed" at 07:56:03Z.
- All 5 records then logged "Confirmation dispatched successfully" / "Record published to topic" at 08:11:25-29Z (third attempt, ~75s after the first). No shopify-connector error logs 08:11:30-08:13:52Z. PURDYFIGG: 7 further successful dispatches after 08:11:30Z. 3,402 PURDYFIGG successful dispatches in 24h; also ESCENTRICPL 23, ESCENTRIC 22, SAIRA 19.
- Monitor/OAuth monitor 314846184 still report Alert via the API at 08:13:52Z (15m window).

## Not established
- Why the refresh returned HTML (OAuth agent's scope).
- Whether replay-service holds failure records for these 5 (Fuse MCP 401). Logs show successful redelivery, so none should be needed.
- Other shops' tokens; only PURDYFIGG failed.

## Outcome
P3, self-resolved on the egress side: 5 orders, ~1-2 min delay, nothing held or dropped per logs. Refresh failure may recur until the OAuth work lands. No ticket. Draft reply returned, not posted.

## Links
- Slack thread (Warn parent): https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793261528412669
