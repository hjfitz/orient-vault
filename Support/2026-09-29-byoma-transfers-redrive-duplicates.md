---
tags: [support-triage]
date: 2026-09-29
business_id: BYOMA
customer: "Byoma"
connector: sftp
reporter: "James Godsell"
channel: bifrost-general
thread_url: "https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1789999974819089"
opened_at: "2026-09-29T13:25:42Z"
outcome: config-issue
session_id: 94674c18-3c85-400b-9df7-5a4839a38269
status: open
---
# Byoma held transfers: redrive after the AUTO consignmentId fix re-failed, and most already exist in Snap

## Reported
Follow-up on the 2026-09-21 thread. James removed the `AUTO` consignmentId default from Byoma's Goods In mapping, then replayed the held transfers from the Retry Queue on 09-29. They failed again, and afterwards he saw them as not failed in Fuse but not in Snap. Harry asked for the held messages to be redriven.

## Root cause
The mapping fix was right but does not reach records already held. The held records were stored with `identifiers.consignmentId: "AUTO"`, and a replay republishes the stored canonical unchanged, so James's 14:07 replay of the 13 transfers (TRF04206 to TRF04291) reproduced the same Snap rejection and left 13 fresh held copies. The old copies showed replay "success", which only means republished, not accepted by Snap.

Separately, Snap already holds warehouse-raised `POLP…` receipts for 9 of the 13 transfers, matched on SupplierRef (8 already received, TRF04206 open and unreceived). TRF04208, 04257 and 04280 have none. So the Poland warehouse appears to raise these receipts by hand regardless of what Fuse sends. Redriving the held records would therefore duplicate receipts for stock already in.

## Fix / Resolution
Partial, with one self-inflicted side effect. Edited the stored TRF04291 record (dropped consignmentId) and retried it. Snap accepted it and created receipt BYOM1DE849A334D, which duplicates the already-received POLP015489. That retry was done before checking Snap for existing receipts. The other 12 were not touched.

Replied in-thread as Bifrost Support Bot (Harry approved the draft): the mapping change is good, most transfers already exist, BYOM1DE849A334D should be cancelled by the warehouse, and asked whether TRF04208, 04257 and 04280 should be sent through Fuse. Still open, waiting on James/the warehouse. If the three do need sending, edit and retry only those.

Still to decide: the 13 old and 13 fresh held copies remain in the retry queue and inflate the count; nothing was deleted.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1789999974819089
- Reply: https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1790697514760489
- Earlier triage: [[2026-09-21-byoma-transfers-invalid-consignment]]
