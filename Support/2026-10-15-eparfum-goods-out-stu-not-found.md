---
tags: [support-triage]
date: 2026-10-15
business_id: EPARFUM
customer: "Euro Parfums"
connector: sftp
reporter: "James Godsell"
channel: bifrost-general
thread_url: "https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1792052679629039"
opened_at: "2026-10-15T08:24:39Z"
outcome: escalated
session_id: b22bb70f-b566-483e-bb02-e1afac6c3ba1
status: open
---
# Euro Parfums goods-out "Consignment StU not found"

## Reported
James escalated that Euro Parfums goods-out confirmations are "failing" on "Consignment StU not found" and the customer has a list of confirmations that haven't come back.

## Root cause
The warning is non-fatal; EPARFUM goods-out files are being written to SFTP (latest 2026-10-15 08:28Z) and Snap's outbound queue is empty. The poller's StU read filters on `Consignment eq <shipment id>`, but for stock picked from pallets received earlier the StU's `Consignment` is the origin receipt consignment (EPAR23B52B65A6E -> BM2P083043), so it returns nothing and package weight goes out as 0 and H/W/D blank (verified in the 08:18Z egress file; line qty/batch/SSCC correct). `Ref eq <shipment>` returns both StUs. Fleet-wide (~55k warns in 3 days, ~1.6k EPARFUM). Not yet confirmed: what the customer's files actually contain, or which confirmations they consider missing.

## Fix / Resolution
Bot replied in-thread asking for example refs and what the customer sees. Defect not filed; awaiting go-ahead.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1792052679629039
