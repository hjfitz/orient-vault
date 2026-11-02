---
tags: [support-triage]
date: 2026-07-17
business_id: STUBBLE
customer: "Stubble & Co"
connector: sftp
reporter: "Joseph Mashiloane"
channel: bifrost-general
thread_url: "https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1784301289078439"
opened_at: "2026-07-17T15:14:49Z"
resolved_at: "2026-07-24T11:56:53Z"
minutes_spent: 9882
outcome: defect
ticket: FUSE-1067
session_id: 535aa793-cf02-4d5b-9169-be8e3c2823f1
status: resolved
---
# Stubble & Co order SC17388002 imported into SNAP with a different customer's details

## Reported
Joseph Mashiloane reported that order SC17388002 (for customer Julien Blanc) had been imported into SNAP carrying James Marti's name, address and shipping method instead — the details of a different order, SC17388128, which itself never appeared in SNAP at all. He asked for the import logs to be reviewed and the cause investigated.

## Root cause
A shipment-ID collision inside SNAP: Fuse received SC17388002 correctly (with Julien Blanc's real details) at 10:47 on 1 July, but a colliding SNAP shipment ID meant the record created in SNAP a second later carried James Marti's order data instead. SC17388128 never reached Fuse's pipeline under that reference at all. The underlying collision was already fixed on the platform side on 3 July (SNAP shipment IDs are now generated deterministically), before this thread was even raised.
Note: there's a long idle gap in this thread — Fuse's logs at the time didn't retain data far enough back to investigate immediately, so the real diagnosis only came through days later via the longer-lived internal record store, and the root-cause summary landed two days after that. The elapsed time reflects that wait, not continuous investigation.

## Fix / Resolution
Both affected orders were resubmitted with a `-1` suffix (SC17388128-1 on 3 Jul, SC17388002-1 on 17 Jul) and both shipped correctly with the right customer details — confirmed by Joseph. The investigation was tracked as FUSE-1067, and the underlying ID-collision issue was already resolved by the deterministic-ID fix that shipped 3 July.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1784301289078439
- Ticket: https://globalfreight.atlassian.net/browse/FUSE-1067
