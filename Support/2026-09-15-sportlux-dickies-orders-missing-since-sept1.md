---
tags: [support-triage]
date: 2026-09-15
business_id: SPORTLUX
customer: "SportLux (Dickies)"
connector: sftp
reporter: "Denis Tomolea"
channel: bifrost-general
thread_url: "https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1789463516044109"
opened_at: "2026-09-15T09:11:56Z"
outcome: escalated
session_id: 535aa793-cf02-4d5b-9169-be8e3c2823f1
status: open
---
# Dickies (SportLux) reported a large batch of orders missing since 1 September

## Reported
Denis Tomolea reported that Dickies (SportLux) had a large number of orders missing since 1 September, with the customer supplying a list of references. He'd spot-checked several in Datadog and found nothing, and nothing in the Retry Queue or Transaction History either. The customer escalated internally as they grew unhappy with the delay in a response.

Note: this thread ran from 15 to 17 September with several multi-hour and overnight idle gaps — the elapsed time is not continuous investigation.

## Root cause
Genuinely disputed and, as of the end of this reporting window, not settled. Of 49 orders investigated: 3 hit a platform bug that had since been fixed; the remaining 46 never reached Fuse at all. Harry Fitzgerald's first diagnosis ("we've found the missing orders") was later retracted as incorrect — Fuse never actually had them. A follow-up theory was that some order files landed in the wrong SFTP folder (the outbound/confirmations folder rather than inbound) and were picked up and deleted by the customer's own SFTP client, mistaking them for genuine confirmations — but the customer's own investigation directly disputed this, stating they've consistently uploaded to the correct folder since day one, and that files have been observed moving inconsistently into Archive/Error folders on the same day, in the same format, without any changes on their end. Fuse's side confirmed all files are where expected in its database, so the discrepancy remains unresolved.

## Fix / Resolution
No resolution reached. The 3 orders affected by the known platform bug were redriven into SNAP. For the other 46, the customer is being asked for a corrected resend or full order details, but the disagreement over root cause (file misplacement vs. inconsistent server-side archiving) is unresolved and a joint call between ILG and the customer is being arranged to get to the bottom of it — flagged as being escalated to director level on the customer's side. A related process issue also surfaced in this thread: James Godsell accessed the customer's production SFTP directly to cross-check file locations, which Harry Fitzgerald asked him not to do going forward (citing the prior agreement to keep investigations to the UI/Datadog and the need to cycle credentials given the direct access).

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1789463516044109
