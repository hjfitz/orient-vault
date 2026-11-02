---
tags: [support-triage]
date: 2026-09-14
business_id: STUBBLE
customer: "Stubble & Co"
connector: sftp
reporter: "Joseph Mashiloane"
channel: bifrost-general
thread_url: "https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1789380166163539"
opened_at: "2026-09-14T10:02:46Z"
resolved_at: "2026-09-14T10:12:13Z"
minutes_spent: 9
outcome: defect
session_id: 535aa793-cf02-4d5b-9169-be8e3c2823f1
status: resolved
---
# Stubble & Co stopped receiving dispatch confirmations and tracking alerts since the previous Friday

## Reported
Joseph Mashiloane reported that Stubble & Co had not received any dispatch confirmation or tracking information alerts since Friday, giving three example references (SC17408522, SC17408515, SC17408528). He'd checked Fuse Exception logs and Datadog and found nothing. Denis Tomolea flagged it might be related to a prior confirmations discussion.

## Root cause
Not the SFTP connector — the SNAP confirmation poller. A single shipment (`STUB72604F5184E`, closed 11 September) was variance-flagged with every line at zero quantity shipped, but SNAP still raised a DESPATCH record with a tracking number for it. That despatch had no matching stock record behind it, so Fuse's mapping threw an error trying to process it — and because the whole poll batch shares one promise, that single throw discarded every other confirmation in the same batch and nothing got marked processed. It then retried the same bad record every ~2 minutes indefinitely, blocking all 324 unprocessed DESPATCH entries queued behind it for Stubble specifically. This was the third occurrence of this exact failure shape (also seen 19 Aug and 27 Aug).

## Fix / Resolution
The example orders Joseph gave were confirmed already despatched correctly in SNAP with tracking — they were just stuck behind the blocking record, not lost. The fix handed over was to correct the one bad shipment (`STUB72604F5184E`) in the SNAP host UI, or clear that one outbound-queue entry, which would let the remaining 323 drain within one poll cycle. A recurring-ticket follow-up was flagged internally (one bad record blocking a whole client's confirmation lane, for the third time) but no ticket number was given in this thread.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1789380166163539
