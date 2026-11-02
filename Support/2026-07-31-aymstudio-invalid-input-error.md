---
tags: [support-triage]
date: 2026-07-31
business_id: AYMSTUDIO
customer: "AYM Studio"
connector: sftp
reporter: "Milosz"
channel: bifrost-general
thread_url: "https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1785493477682609"
opened_at: "2026-07-31T10:24:37Z"
resolved_at: "2026-08-06T14:27:46Z"
minutes_spent: 8883
outcome: defect
ticket: FUSE-1069
session_id: 535aa793-cf02-4d5b-9169-be8e3c2823f1
status: resolved
---
# AYM Studio PO rejected with an unreadable, repeating "invalid input" error

## Reported
Milosz reported an error for AYM Studio order PO-30726: the error just repeated "invalid input" over and over with no indication of which field or line was the problem, and the same was true in Datadog. He asked for help identifying the actual cause.

## Root cause
Two things. First, the real failure: every one of the 23 order lines was missing a line identifier, built from two columns in the client's file (`OrdRef2` and `iOrderLines_LineNumber`) that were empty on all rows across three resubmissions that day. Second — and the reason the error was unreadable — Fuse's UI builds its "Reason" text from the error message only, drops the field name, and truncates at 500 characters, so the same generic sentence repeated with no pointer to the actual field. That UI gap was tracked as FUSE-1069. Denis Tomolea escalated when the customer separately pushed back that those two fields were marked non-mandatory in the ILG Fuse SFTP guide.
Note: this thread has several long idle gaps (spanning days) between the initial diagnosis, the customer's pushback on mandatory fields, and the final config fix — the elapsed time is not continuous investigation.

## Fix / Resolution
Since the customer couldn't reliably provide those two fields, Harry Fitzgerald had them set up as Fuse-side defaults ("N/A") instead of relying on the customer's file — James Godsell mapped this for AYM Studio. The underlying UI error-message readability gap was tracked separately as FUSE-1069; a real Datadog query was also handed over (`service:sftp_connector @environment:prod @businessId:AYMSTUDIO "Validated records"`) so the real per-field failure detail can be checked directly going forward.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1785493477682609
- Ticket: https://globalfreight.atlassian.net/browse/FUSE-1069
