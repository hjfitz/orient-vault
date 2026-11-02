---
tags: [support-triage]
date: 2026-07-28
business_id: SPORTLUX
customer: "SportLux (Dickies)"
connector: sftp
reporter: "Joseph Mashiloane"
channel: bifrost-general
thread_url: "https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1785230473239729"
opened_at: "2026-07-28T09:21:13Z"
outcome: unresolved
session_id: 535aa793-cf02-4d5b-9169-be8e3c2823f1
status: open
---
# SportLux/Dickies reported not receiving "OC" (shipment) confirmations for a list of dispatched orders

## Reported
Joseph Mashiloane reported that SportLux/Dickies had not received "OC" confirmations (clarified as shipment/dispatch confirmation status) back for a list of orders, and asked for them to be checked and resent. He confirmed the orders had actually been dispatched in SNAP.

## Root cause
Harry Fitzgerald traced the SFTP write directly: the confirmation file for the example order was confirmed written by Fuse's SFTP connector at the expected time, and the file (and almost every other confirmation sent to this customer over the prior two months) was subsequently gone from the bucket with no cleanup job on Fuse's side that could have removed it — pointing to the client's own SFTP client fetching and deleting files after download, i.e. delivery had succeeded on Fuse's end. However, the conversation then became confused: Joseph asked whether files moved to the client's own "Archive" folder meant confirmations had been generated, and Harry's answer that "confirmation files are not moved by fuse" left Joseph unclear on why the client's order status still hadn't updated. The thread ends on that confusion, unresolved.

## Fix / Resolution
No resolution reached — the delivery-succeeded finding was given, but Joseph's follow-up question about why the client's own order status wasn't updating was never actually answered before the thread went quiet. James Godsell's message on 08-05 ("I think this is related to what I have commented in the chat earlier today at 12:30") appears to reference a separate but related SFTP outbound-use-case issue (see the 2026-08-05 BYOMA/fleet record) rather than resolving this thread directly.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1785230473239729
