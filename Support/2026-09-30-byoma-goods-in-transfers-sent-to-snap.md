---
tags: [support-triage]
date: 2026-09-30
business_id: BYOMA
customer: "Byoma"
connector: sftp
reporter: "James Godsell"
channel: bifrost-general
thread_url: "https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1790768173603349?thread_ts=1789999974.819089&cid=C098LD5PS95"
opened_at: "2026-09-30T11:36:13Z"
resolved_at: "2026-09-30T12:00:00Z"
minutes_spent: 24
outcome: config-issue
session_id: e8017a60-9ced-4075-8946-6deeee593aa9
status: resolved
---
# Send Byoma transfers TRF04208, TRF04257, TRF04280 through to Snap

## Reported
James asked for three Byoma goods-in transfers (failing on "Invalid Consignment / Invalid Receipt") to be sent through to Snap.

## Root cause
Snap rejects the receipt create when `consignmentId` is `AUTO`. Blanking it worked (as on TRF04291 on 09-29). A plain retry failed again. Hypothesis: the Byoma mapping default sends `AUTO`; not verified in the mapping.

## Fix / Resolution
Edited `consignmentId` to blank on the newest failure record for each transfer, retried, and confirmed "Entity created in SNAP" (BYOMF1CD6232ACC, BYOM6B039328307, BYOMD5E228F042C). Nine similar Byoma transfers are still held. A mapping defect is not yet filed.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1790768173603349?thread_ts=1789999974.819089&cid=C098LD5PS95
