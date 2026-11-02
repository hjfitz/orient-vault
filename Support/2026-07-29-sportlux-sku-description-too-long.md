---
tags: [support-triage]
date: 2026-07-29
business_id: SPORTLUX
customer: "SportLux (Dickies)"
connector: sftp
reporter: "Joseph Mashiloane"
channel: bifrost-general
thread_url: "https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1785340767005789"
opened_at: "2026-07-29T15:59:27Z"
resolved_at: "2026-07-29T17:23:13Z"
minutes_spent: 84
outcome: defect
session_id: 535aa793-cf02-4d5b-9169-be8e3c2823f1
status: resolved
---
# SportLux alerted on "too big" SKU error even though the SKUs were under the character limit

## Reported
Joseph Mashiloane flagged an alert for two SportLux SKUs with the error "Too big: expected string to have <=30 characters," even though both SKU IDs were well under 30 characters. He asked why the error was being raised against fields that looked fine.

## Root cause
The error was correctly identifying an oversized field, but misleadingly attributed to the SKU — the field actually over the 30-character SNAP limit was the product description (33 characters on both flagged products), not the SKU. Fuse's platform sends product descriptions straight through to SNAP without shortening them, so any description over 30 characters is rejected outright. The error surfaces against the SKU only because that's how the failed record is identified in the logs. This affected 139 SportLux products at the time, all retrying and failing every 5-10 minutes.

## Fix / Resolution
Harry Fitzgerald explained the real cause and handed over a reusable Datadog query (`service:snap_adapter "SNAP entity creation failed" @customer:SPORTLUX @failureMode:schema_validation`) so Joseph could self-serve checking status going forward. The underlying defect (descriptions not truncated/validated before being sent to SNAP) was flagged to be raised internally to work out the right fix — no confirmation in this thread that the platform-side fix was actually shipped.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1785340767005789
