---
tags: [support-triage]
date: 2026-09-21
business_id: EPARFUM
customer: "Euro Parfums"
connector: sftp
reporter: "Joseph Mashiloane"
channel: bifrost-general
thread_url: "https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1789986209296039"
opened_at: "2026-09-21T10:23:29Z"
resolved_at: "2026-09-21T17:03:34Z"
minutes_spent: 400
outcome: defect
session_id: 559a2c9e-8afc-4610-aef8-2dc08be15252
status: resolved
---
# SNAP outage (2026-09-16) left 163 orders stuck across 5 customers, unretried for 5 days

## Reported
Joseph (support) reported two order refs missing from SNAP (ST508105, ST507227), with
screenshots from replay-service's failure UI showing "Snap rejected the record" with a raw
HTML 404 body. He asked what the error meant in plain terms so he could explain it to the
client. He later flagged a third order (WILDSMITH SO-28513, same signature) and asked how many
customers were affected in total, and whether there's a way to clear this class of error without
raising a ticket every time.

## Root cause
All affected orders' `wms_submission` create attempts (`PUT /v2/shipments` via snap-adapter)
landed during an unannounced SnapFulfil prod maintenance window on `ilg005liveapi.snapfulfil.net`,
2026-09-16 09:05–10:36 UTC — the same event already tracked as INC-36. Direct query of
replay-service (deduped by `recordId`, not raw failure-log-line count) gives the real scope:
**163 distinct records across 5 businesses** — PURDYFIGG 117, STUBBLE 28, WILDSMITH 10 (3 orders
+ 7 product updates), EPARFUM 7, LISAUK 1. All passed the replay-service strict-schema gate
cleanly (`blockingIssues: []`) — not a data/config issue. The underlying error is classified
`retryable: false` by snap-adapter (a raw 404 doesn't look like a transient error to it), so the
pipeline never auto-retried any of them — they sat untouched in the failure inbox for 5 days
until this thread surfaced them, except STUBBLE's 28, which had already been cleared by some
other means before this investigation (not established here).

An early internal estimate of "~1000 orders across 4-5 customers" was wrong — it came from
raw retry-attempt log-line counts (each stuck order generated repeated automatic retry-attempt
log entries during the 80-minute outage; deduping those down to distinct orders gives the real
163). This was walked back to Joseph directly once caught.

**Platform gap worth a ticket**: snap-adapter classifying a raw-404 "SNAP unreachable" error as
`retryable: false` means an outage of this kind leaves every affected order permanently stuck
with no automatic cleardown — a human has to notice and manually redrive. 5 days elapsed between
the outage and anyone noticing, and it took an explicit customer escalation to trigger the
noticing.

## Fix / Resolution
Verified a sample of the still-stuck failures were safe to redrive (root cause understood, no
blocking issues), then bulk-replayed all 133 still-stuck records (one per distinct `recordId`)
via replay-service (`replay-retry`, production, `confirm: true`) — 133/133 returned success
(republished into the pipeline; STUBBLE's 28 were already clear, so untouched). Replied to
Joseph in-thread: explained the outage in plain terms, corrected the ~1000 figure to the real
163-across-5-customers breakdown, answered his "can we clear the queue" question (yes, and it's
now been done), and confirmed nothing is left for him to chase from this outage.

Process note: this replay was done by engineering as a one-off; going forward this class of
"confirmed-safe-to-redrive" failure should be handed to support to action via the Replay button
in the failure UI themselves, not redriven by engineering (see
[[feedback_dev_vs_support_division_of_labor]]).

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1789986209296039
- Related: INC-36 (SnapFulfil ilg005 unannounced maintenance, 2026-09-16)
- Follow-up worth filing: snap-adapter's `retryable: false` classification for a raw-404 SNAP
  create failure means this class of outage never self-clears — no ticket filed yet.
