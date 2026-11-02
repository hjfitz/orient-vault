---
tags: [support-triage]
date: 2026-09-15
business_id: ""
customer: "All live prod customers (reported via Saira Skin / Purdy and Figg examples)"
connector: unknown
reporter: "James Godsell"
channel: bifrost-general
thread_url: "https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1789459777776309"
opened_at: "2026-09-15T08:09:37Z"
resolved_at: "2026-09-15T15:00:29Z"
minutes_spent: 411
outcome: defect
session_id: 535aa793-cf02-4d5b-9169-be8e3c2823f1
status: resolved
---
# Transaction History in prod showed zero goods-out or goods-out confirmations for any customer

## Reported
James Godsell reported that every live customer in prod showed zero goods-out and goods-out-confirmation records in Transaction History for the last 30 days, despite this having worked for him a couple of weeks earlier when replaying failed Saira Skin goods-out orders. He'd flagged this once before, off the back of an earlier SNAP issue, and it still looked broken. There was some initial cross-talk about whether goods-out confirmations were implemented in Transaction History at all before the real scope of the report (goods-out itself, not just confirmations, missing for every customer) was pinned down.

## Root cause
A latent scaling bug, not a regression tied to any specific deploy. Transaction History's server functions called collector's legacy list routes, which query with no sort (effectively oldest-first) and only fetch the first 100 records per type. For high-volume record types like sales_order on busy customers (Saira Skin, Purdy and Figg), the first 100 records loaded were the oldest survivors — recent goods-out orders were never even loaded into the page, and any recency filter then showed zero rows. A separate, related gap meant many older records had no `lifecycle` field populated at all (lifecycle capture only went live in late July), which needed a one-off backfill.
Note: there's a multi-hour idle gap in this thread (roughly 10:01 to 14:49) while the fix was built and deployed — the elapsed time isn't continuous back-and-forth.

## Fix / Resolution
Fixed and verified live in prod on 15-16 September: collector's list routes were switched to a newest-first, database-paginated query, and a one-off backfill was run in prod to populate the missing `lifecycle` field on existing records. James confirmed dev was already populating correctly; prod initially lagged behind because the fix hadn't been deployed to prod yet, which was then completed the same day.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1789459777776309
