---
tags: [datadog-triage]
date: 2026-10-13
monitor: "Slack report (no monitor): Escentric UK Shopify orders not importing in dev"
service: shopify-connector
business_id: ESCENTRIC
snap_instance:
channel: bifrost-general
thread_url: "https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1791901241230329"
opened_at: "2026-10-13T14:20:41Z"
severity_assessed: P4
flapping: false
outcome: real_minor
escalated_to:
ticket: FUSE-1312
status: open
---
# Escentric UK (dev) Shopify orders not polled — store shared with ESCENTRICPL

## Fired
James Godsell reported that ESCENTRIC's Shopify UK Dev Store connector shows 2 orders in the retrieval-conditions test but they never reach Snap. ESCENTRICPL's connector works. Both connectors point at the same Shopify store (`escentric-sandbox`). This was a Slack report, not a monitor. The thread was answered on 10-13 ("one connector per store instance"), and Jack Bailey logged FUSE-1312.

## Investigation
- Dev config (list-customers): ESCENTRIC `conn_ecb5288d35e54091be1dbe142bfe0637` "Shopify UK Dev Store", active, `tag == UK`. ESCENTRICPL `conn_cdc9af61d7974285acca844e14e17657` "Shopify PL Dev Store", active, `tag == EU`. The conditions don't overlap.
- Root cause is already fixed in code. `ShopifyApiFactory` cached the API instance by shop, so the second connector on a store was never polled and the first was polled twice. shopify-connector#332 (env flag) and #335 (runtime flag `shopify-connector.api-cache-per-connector`) both merged to `main` at 2026-10-14 17:27Z (commits 7e8b0b8 and 59f919b).
- Dev runs `59f919b` (log `version` tag, 10-14 18:35Z).
- The UK connector (`@connectorId:conn_ecb5…`) was polled 2026-10-14 17:15:01Z–18:35:02Z and not since. Checked through 10-15 08:20Z.
- Since 10-14 18:00Z, `"Shopify order collection started"` in dev shows one connector at 338, six at 173, and one that stops at 18:35:01Z (8 polls). That is the double-poll / no-poll signature again.
- config-service dev `GET /api/v1/feature-flags`: `shopify-connector.api-cache-per-connector` is `enabled: false`, version 4, `updatedAt 2026-10-14T18:35:13.458Z`, `updatedBy: admin`. shopify-connector logged `Feature flag revision received` at 18:35:14Z. #335 says it left the flag on at 17:18:31Z.
- Collector's newest ESCENTRIC sales_order is S15129, created 2026-10-12 (SFTP-shaped). No Shopify UK order has landed since.
- UK retrieval `created_at` window changed from 24h to 12h on 2026-10-14 (customer config snapshot).
- Not established:
  - who switched the flag off at 18:35Z, and why (`updatedBy` is just `admin`);
  - whether UK's 17:15–18:35 polls found any orders (the `@orderCount` grouping returned no values);
  - FUSE-1312's content (the Jira tool wasn't permitted in this session).

## Outcome
Real defect, dev only, test customer: P4. The fix is merged but the runtime flag is off in dev, so UK is unpolled again. Owed: decide whether to re-enable the flag in dev, and tie FUSE-1312 to #332/#335 (prod has no flag, so one connector per store still holds there). Reply proposed to Harry, not posted.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1791901241230329
- PRs: https://github.com/gfs-bifrost/shopify-connector/pull/332, https://github.com/gfs-bifrost/shopify-connector/pull/335
- Ticket: FUSE-1312
