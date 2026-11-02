---
tags: [datadog-triage]
date: 2026-10-29
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: shopify-connector
business_id: PURDYFIGG
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793261510096099"
opened_at: "2026-10-29T08:10:37Z"
severity_assessed: P3
flapping: true
outcome: real_minor
session_id: 7198be0e-f4de-4cae-8e32-ef4ac0c4cdb9
status: resolved
---
# 08:10Z firing was a shopify-connector PURDYFIGG token-refresh burst, not snap_adapter

## Fired
More than 2 domain:fuse error logs in 2m at 08:10:37Z. Second firing today (first: 07:06Z, SPORTLUX snap_adapter slot_timeout, see 2026-10-29-platform-elevated-prod-error-rate).

## Investigation
- Monitor's own query, 08:08-08:12Z: 21 errors, all shopify-connector, all PURDYFIGG, shop purdy-figg.myshopify.com: 20 goods_out_confirmation (flow confirmation) + 1 sales_order (flow create). All phase shopify_exchange, SyntaxError "Unexpected token '<', \"<html>...\" is not valid JSON" (a non-JSON, HTML body where JSON was expected; the 11 "Token refresh failed" logs each have a matching "Confirmation dispatch failed"/"Bulk tick failed").
- All 22 PURDYFIGG errors fall 08:10:08-08:11:18Z. None after 08:12Z; at 08:12:16-17Z PURDYFIGG logs show Shopify GraphQL responses received and "Confirmation dispatched successfully".
- snap_adapter: zero error logs 08:00-08:20Z (any @transient). All prod domain:fuse errors since 07:50Z: 23 (22 PURDYFIGG + 1 ESCENTRIC at <08:08Z).
- Shopify monitors 314846184 / 303425509 fired from the same burst; root cause left to their triage.

## Not established
Source of the HTML body (Shopify, an edge or proxy in between); whether the 10 failed confirmations and 1 failed create were redelivered; token refresh health overall.

## Outcome
Real minor, P3. Not snap_adapter slot_timeout.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793261510096099
