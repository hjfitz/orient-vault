---
tags: [support-triage]
date: 2026-09-16
business_id: CHAMPO
customer: "Champo"
connector: sftp
reporter: "Joseph Mashiloane"
channel: bifrost-general
thread_url: "https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1789578394863799"
opened_at: "2026-09-16T17:06:34Z"
resolved_at: "2026-09-17T08:41:14Z"
minutes_spent: 935
outcome: mundane
session_id: 535aa793-cf02-4d5b-9169-be8e3c2823f1
status: resolved
---
# Champo stock quantity in Shopify not matching SNAP

## Reported
Joseph Mashiloane asked which support workflow to use to raise an issue where Champo's stock update wasn't reflecting in Shopify — a specific SKU showed 960 in SNAP but 0 in Shopify — and said he couldn't find anywhere in Fuse to check SKU quantity updates for this customer.
Note: there's an overnight idle gap in this thread before the answer came back.

## Root cause
Not a Fuse issue. Champo does not have Stock Management configured to flow through Fuse at all — only Goods Out & Confirmations and Master Data are live for them in Fuse (with no Goods In traffic observed either). Champo's e-commerce/Shopify stock sync runs through Jitterbit, entirely outside Fuse, which is why nothing shows in Fuse for this.

## Fix / Resolution
No fix needed on Fuse's side. Jack Bailey pointed Joseph at checking the customer's connector/use-case configuration in Fuse as the general way to tell what is and isn't flowing through the platform. James Godsell separately confirmed Champo's ecom integration is set up on Jitterbit.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1789578394863799
