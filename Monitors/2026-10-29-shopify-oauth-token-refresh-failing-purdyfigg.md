---
tags: [datadog-triage]
date: 2026-10-29
monitor: "[FUSE][Shopify Connector] OAuth token refresh failing sustained (prod)"
service: shopify-connector
business_id: PURDYFIGG
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793261508521399"
opened_at: "2026-10-29T08:10:24Z"
resolved_at: "2026-10-29T08:13:00Z"
minutes_spent: 3
severity_assessed: P4
flapping: false
outcome: self_resolved
escalated_to:
ticket:
session_id: 7198be0e-f4de-4cae-8e32-ef4ac0c4cdb9
status: resolved
---
# PURDYFIGG Shopify token refresh returned HTML for ~70s, self-recovered

## Fired
Monitor 314846184 (`sum(last_1h):sum:fuse.token.refresh.failed{environment:prod} by {shop} >= 3`, P2) alerted for shop purdy-figg.myshopify.com. The query counts failed refreshes only; it has no success offset despite the message text.

## Investigation
- Logs "Token refresh failed": 12 for purdy-figg between 08:10:08Z and 08:11:18Z (one more at 10-28 15:35:08Z); all `phase:shopify_exchange`, `reason:other`, errorMessage "Unexpected token '<', "<html>..." is not valid JSON", i.e. the token exchange got an HTML body, not JSON. 5 goods_out_confirmation records (each retried twice) hit it.
- Last good dispatch before: 08:08:15Z. All 5 records then logged "Confirmation dispatched successfully" at 08:11:24-28Z. 0 refresh failures and 0 dispatch failures after 08:11:30Z (checked 08:12:52Z); 7 successful dispatches since.
- Same signature, same recovery on 10-28: purdy-figg failure 15:35:08Z, dispatching again 15:36:12Z.
- Other shops, 7d: ESCENTRIC 1 (07:56:03Z today, identical HTML error, order collection continued at 08:00-08:10Z), SAIRA 1 (10-28 15:26:02Z, same error).
- shopifystatus.com summary at ~08:13Z: indicator none, no incidents, no degraded components.
- Running version 8266733 (commit 10-27 13:40Z); no deploy inside the window established.

## Outcome
Transient, self-resolved, no held or lost orders. Monitor trips on 2 retries of one short blip per record; retune (success offset, or count distinct records/longer window) is a candidate but no ticket filed.
Not established: what HTML Shopify returned (HTTP status not logged), why the stale-token lock path ("Stale token lock released") fired, whether a prod deploy occurred recently (deployments API returned none).

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793261508521399
