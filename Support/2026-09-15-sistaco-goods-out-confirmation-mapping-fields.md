---
tags: [support-triage]
date: 2026-09-15
business_id: SISTACO
customer: "Sistaco"
connector: shopify
reporter: "James Godsell"
channel: bifrost-general
thread_url: "https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1789482281008349"
opened_at: "2026-09-15T14:24:41Z"
resolved_at: "2026-09-16T08:49:12Z"
minutes_spent: 1105
outcome: defect
ticket: FXS-2
session_id: 535aa793-cf02-4d5b-9169-be8e3c2823f1
status: resolved
---
# Sistaco's Goods Out Confirmations mapping was missing selectable target fields that existing customers already had configured

## Reported
James Godsell reported that on the Shopify connector's "Goods Out Confirmations" use case in dev, three target ("To") fields visible and already configured for Purdy and Figg (`fulfillmentOrderId`, and the two `fulfillmentOrderLineItems[]` line fields) were missing from the field picker when he tried to set up the same mapping for Sistaco. He couldn't select or manually enter them, and a template application didn't produce them either.

## Root cause
A UI display bug: the three target fields had dropped out of the "To" field picker entirely, so they couldn't be selected for a new customer and showed as `[TO BE PROVIDED]` on customers where they were already configured (Purdy & Figg, Saira, etc.). Confirmed to be display-only — the fields were still present under the hood and confirmations for already-configured customers continued flowing to Shopify correctly throughout.

## Fix / Resolution
A hotfix was written, reviewed, and deployed to both dev and prod the same evening, restoring the fields to the "To" picker. James confirmed the next morning he was able to add them to Sistaco's Goods Out Confirmation template. Tracked via ticket FXS-2 (raised through the new `/support` workflow).

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1789482281008349
- Ticket: https://globalfreight.atlassian.net/browse/FXS-2
