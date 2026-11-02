---
tags: [support-triage]
date: 2026-09-10
business_id: PURDYFIGG
customer: "Purdy and Figg"
connector: shopify
reporter: "Joseph Mashiloane"
channel: bifrost-general
thread_url: "https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1789049129870709"
opened_at: "2026-09-10T14:05:29Z"
resolved_at: "2026-09-11T14:46:13Z"
minutes_spent: 1481
outcome: defect
ticket: FUSE-1147
session_id: 535aa793-cf02-4d5b-9169-be8e3c2823f1
status: resolved
---
# Purdy and Figg order PURDCE5A8C4CBBC showed duplicated kit lines in SNAP

## Reported
Joseph Mashiloane was trying to trace order PURDCE5A8C4CBBC (Ref #6330760) for Purdy and Figg, which showed duplicated lines in SNAP against a kit product. He wanted to confirm whether the duplication came from the client's original file or was a SNAP-side issue, but got stuck following the standard SOP because the order had no correlation ID visible in Fuse and came through Shopify rather than SFTP.

## Root cause
The order Fuse received from Shopify had exactly one line, one unit of the kit product — no duplication. The duplication happened afterwards, on Fuse's side: the order was resubmitted to SNAP several times during a retry loop, and each retry caused SNAP to append another copy of the kit's component lines instead of replacing the existing ones. This was a known, already-fixed platform bug (tracked as FUSE-1147, a slot-timeout re-PUT loop causing kit line duplication) by the time this thread was raised.

## Fix / Resolution
Harry Fitzgerald pointed Joseph at the correct correlation ID and search pattern for Shopify-sourced orders going forward. The specific affected shipment needed manual handling because SNAP shipments are cancelled rather than deleted, so a straight replay onto the same shipment ID didn't take effect at first; a working redrive approach was found and verified end-to-end (tested on order #6330758), and the customer's operations team handled clearing the remaining affected orders directly in SNAP.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1789049129870709
- Ticket: https://globalfreight.atlassian.net/browse/FUSE-1147
