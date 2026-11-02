---
tags: [support-triage]
date: 2026-07-22
business_id: BYOMA
customer: "Byoma"
connector: sftp
reporter: "Joseph Mashiloane"
channel: bifrost-general
thread_url: "https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1784735321260139"
opened_at: "2026-07-22T15:48:41Z"
resolved_at: "2026-07-24T08:04:32Z"
minutes_spent: 2416
outcome: defect
session_id: 535aa793-cf02-4d5b-9169-be8e3c2823f1
status: resolved
---
# Byoma PO confirmation file showed one batch number against every product

## Reported
Joseph Mashiloane flagged that for PO POLP012920, SNAP showed different batch numbers assigned per product, but the confirmation file Fuse sent back to the client showed the same batch number against every product line — the two didn't line up. He asked whether this was expected or a data-generation issue, and provided the confirmation file and a screenshot from the client (Byoma, Poland, production).

## Root cause
Not spelled out in detail in the thread — Schuster Efigenio investigated after receiving the confirmation file and confirmed it was a genuine issue with how the confirmation file was generated (batch numbers weren't being carried through correctly from SNAP into the outbound file), not expected behaviour.
Note: there's an overnight idle gap in this thread while the fix was investigated and deployed — the ~40-hour elapsed time isn't continuous investigation.

## Fix / Resolution
Schuster deployed a fix to production on 24 July resolving the batch-number mismatch in the confirmation file generation.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1784735321260139
