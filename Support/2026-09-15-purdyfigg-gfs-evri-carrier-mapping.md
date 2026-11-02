---
tags: [support-triage]
date: 2026-09-15
business_id: PURDYFIGG
customer: "Purdy and Figg"
connector: shopify
reporter: "James Godsell"
channel: bifrost-general
thread_url: "https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1789485470935279"
opened_at: "2026-09-15T15:17:50Z"
outcome: unresolved
session_id: 535aa793-cf02-4d5b-9169-be8e3c2823f1
status: open
---
# Purdy and Figg confirmations still show "GFS_EVRI" instead of "EVRI" on the carrier name sent back to Shopify

## Reported
James Godsell reported that Purdy and Figg's carrier name is hardcoded to "GFS_EVRI" on ingest, and he was trying to strip the "GFS_" prefix on the way back out to Shopify so it displays as "EVRI." He'd configured a `substring(shipping.carrierId, 4, 100)` mapping rule but it wasn't taking effect, and asked for help. This was originally raised as part of the tracking-link concern split off from the 90-missing-orders thread the same week.

## Root cause
James's mapping configuration was confirmed correct on inspection — the issue wasn't a config problem. Harry Fitzgerald subsequently found that sending tracking/carrier details back to Shopify is handled by a separate code path from the general mapping settings customers configure, so the substring rule James applied had no effect on this particular field. This needed a genuine platform-side fix, not a config change.

## Fix / Resolution
No resolution reached yet as of the end of this reporting window (2026-09-17). A fix was written and put up for engineering review on 16 September, treated as a priority given the customer was actively chasing it, but James was still asking for an update as of 17 September 15:51 with no confirmation it had shipped.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1789485470935279
