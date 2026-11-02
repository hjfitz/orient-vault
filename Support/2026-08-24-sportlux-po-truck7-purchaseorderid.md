---
tags: [support-triage]
date: 2026-08-24
business_id: SPORTLUX
customer: "SportLux (Dickies)"
connector: sftp
reporter: "Joseph Mashiloane"
channel: bifrost-general
thread_url: "https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1787572933189509"
opened_at: "2026-08-24T12:02:13Z"
resolved_at: "2026-08-28T08:13:30Z"
minutes_spent: 5531
outcome: config-issue
session_id: 535aa793-cf02-4d5b-9169-be8e3c2823f1
status: resolved
---
# SportLux/Dickies PO "Truck-7 2108" failed to import with an unclear validation error

## Reported
Joseph Mashiloane asked why PO "Truck-7 2108" hadn't imported for SportLux/Dickies. After being pointed at Datadog, he found the file had failed validation on `purchaseOrderId` with the message "Invalid input: expected string, received undefined" — but couldn't tell what was actually wrong, since the client's file used the same template they always had, and the field involved (`OrdRef2`) was documented in SNAP as non-mandatory.

## Root cause
A recent platform change had switched Fuse from a hardcoded mapping (which defaulted `purchaseOrderId` to `"AUTO"`) to the customer's live configured mapping, which had no such default. Fuse treats `purchaseOrderId` as a required field; SportLux/Dickies' PO template mapped it from `OrdRef2`, which was empty on this file, so the record failed. The client's own PO template genuinely leaves `OrdRef2` blank in normal use — it's `OrdRef1` that's reliably the main PO reference on their CSVs.

## Fix / Resolution
As an immediate unblock, the `purchaseOrderId` mapping was changed from `OrdRef2` to `OrdRef1` for this customer (and Byoma, who had the same mapping). James Godsell confirmed this was corrected for Dickies on 27-28 August. The broader design question — whether `purchaseOrderId` should still be a required field, and whether it should default to `OrdRef1` for future customers — was left for a later sprint rather than resolved in this thread; no ticket number was given for that follow-up.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1787572933189509
