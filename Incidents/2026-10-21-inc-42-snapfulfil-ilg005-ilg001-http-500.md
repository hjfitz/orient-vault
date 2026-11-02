---
tags: [incident]
reference: INC-42
date: 2026-10-21
service: snap-adapter
business_id:
severity: P1
is_us: false
declared_by: agent
declared_at: "2026-10-21T11:49:58Z"
resolved_at: "2026-10-21T18:09:07Z"
minutes_to_resolve: 379
incident_url: "https://app.incident.io/gfsdeliver-eng/incidents/01M5F4QXDC80YW1B177YAEM8Y0"
slack_channel_url: "https://gfsdeliver-eng.slack.com/archives/C0CASJJEVKM"
follow_up_count: 8
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# SnapFulfil ilg005 + ilg001 returning HTTP 500: orders not reaching the warehouse

## Impact
- **Outage:** SnapFulfil hosts ilg005 and ilg001 returned HTTP 500 to every request from 12:35 to 12:51 BST, and again from 13:30 to 13:35.
- **Earlier the same day:** ilg001 returned IIS 404s at 09:46–10:06 BST, after a planned Snap change from 08:00 to 08:30.
- **Customers:** ilg005 serves PURDYFIGG, STUBBLE, EPARFUM, WILDSMITH, BYOMA, SPORTLUX, SAIRA, PHLUR, KAPPAHL, BABYMORI and SAMMCK. ilg001 serves DOCKBAY and MANUCURIST.
- **Orders:** couldn't be created in Snap. About 40 were delayed and created on their own.
- **Replays:** 7 DOCKBAY orders needed a manual replay, done at 19:08 BST, about 9 hours late. 4 more held orders were already in Snap.
- **Confirmations:** delayed about 16 minutes and 5 minutes during the two outages.
- **Data loss:** none, and nothing was dead-lettered.

## Root cause
- **Vendor-side.** SnapFulfil applied a fix at 16:00 BST. No RCA has arrived yet.
- **ilg001 is still slow:** about 2–3s, since 19 Oct.
- **Our amplifiers:**
  - An IIS 404 was classed as non-transient, so the DOCKBAY orders were held instead of retried.
  - snap-adapter's per-host request slots were starved by PURDYFIGG creates hanging past 120s.

## Resolution
- Snap recovered on its own at 12:51 and 13:35, and its 16:00 fix went through cleanly.
- The 7 DOCKBAY orders were replayed and confirmed in Snap.
- **Process change:** a Snap outage is now declared as an incident straight away.

## Follow-ups
- Get Snap's RCA and a fix for ilg001's slowness (via ILG's ticket).
- Fix the data-error holds at source:
  - PURDYFIGG #6565591
  - STUBBLE SCPR3410
  - DOCKBAY UK-909420, UK-909462 and UK-909511
  - WILDSMITH SO-29273
- snap-adapter: treat IIS/HTML error pages as transient.
- Entity-creation monitor 334832256: count only non-transient failures before publishing it.
- A single host-level "Snap host failing" signal grouping the knock-on monitors.
- Replay safety: check Snap for each order before replaying it.
- Review snap-adapter's per-host slot model and its 120s timeout.
- Poller: log the queue id when it publishes a confirmation.

## Links
- Incident: https://app.incident.io/gfsdeliver-eng/incidents/01M5F4QXDC80YW1B177YAEM8Y0
- Slack channel: https://gfsdeliver-eng.slack.com/archives/C0CASJJEVKM
- Postmortem (complete; closed 2026-10-21T18:22:04Z): https://globalfreight.atlassian.net/wiki/spaces/Bifrost/pages/337674242
