---
tags: [support-triage]
date: 2026-07-16
business_id: STUBBLE
customer: "Stubble & Co"
connector: sftp
reporter: "Joseph Mashiloane"
channel: bifrost-general
thread_url: "https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1784197962933979"
opened_at: "2026-07-16T10:32:42Z"
outcome: unresolved
session_id: 535aa793-cf02-4d5b-9169-be8e3c2823f1
status: open
---
# STUBBLE order alerted as failing 7 days after it had already shipped

## Reported
Joseph Mashiloane flagged an alert for order SC17379195-1 (record type sales_order, a 400 error) for a shipment that had already gone through SNAP cleanly on the 7th with a dispatch confirmation sent. He asked how an error could surface a full week after the order had shipped without issue.

## Root cause
Harry Humby's working theory was that the order had been re-uploaded (a duplicate resubmission), which should be caught by dedupe-service. Investigating further, he found dedupe-service clears its hold ("gate") once a record is released — by design — so a re-send landing after that release isn't re-caught as a duplicate. That's a plausible mechanism for the 7-day-later alert, but it wasn't confirmed against this specific order.

## Fix / Resolution
No resolution reached — Harry Humby raised an open design question to the team ("should there be a longer-lived or 'already-completed' duplicate guard for re-sends that land after release?") but never closed the loop back with Joseph on this specific alert.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1784197962933979
