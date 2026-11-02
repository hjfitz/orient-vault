---
tags: [support-triage]
date: 2026-09-14
business_id: PURDYFIGG
customer: "Purdy and Figg"
connector: shopify
reporter: "Joseph Mashiloane"
channel: bifrost-general
thread_url: "https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1789407023150359"
opened_at: "2026-09-14T17:30:23Z"
resolved_at: "2026-09-16T15:50:16Z"
minutes_spent: 2780
outcome: config-issue
session_id: 535aa793-cf02-4d5b-9169-be8e3c2823f1
status: resolved
---
# Purdy and Figg reported more than 90 orders that never imported to SNAP

## Reported
Joseph Mashiloane reported that more than 90 orders for Purdy and Figg (list attached) had not imported into SNAP. The customer was frustrated and reluctant to place further orders until resolved, and separately raised two related but distinct concerns in the same complaint: orders whose addresses needed manual correction on their side, and a missing tracking link on fulfilled orders.

## Root cause
The missing-orders part was confirmed as a genuine Fuse-side config gap: the affected orders never made their way into Fuse at all, caused by config on the integration that caused them to be missed (the retrieval condition Fuse's Shopify connector polls against). The address-correction issue was client-side (Purdy and Figg's own Shopify app that amends addresses for SNAP compliance) and not something Fuse handles. The tracking-link concern was split off into a separate, still-open thread about the `GFS_EVRI` carrier code (see the 2026-09-15 record).

## Fix / Resolution
Because the orders never reached Fuse, they couldn't be replayed from Fuse's side — they needed to come through again. Rather than asking the customer to manually resubmit, James Godsell added an `updated_at` retrieval condition to Purdy and Figg's Shopify connector, so that when the customer updates the affected orders in Shopify (which they need to do to fix the addresses anyway), Fuse's polling will pick them up and import them automatically.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1789407023150359
