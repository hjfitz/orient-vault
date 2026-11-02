---
tags: [support-triage]
date: 2026-09-24
business_id: DOCKBAY
customer: "Dock and Bay"
connector: rest
reporter: "Thomas Dunn"
channel: bifrost-general
thread_url: "https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1790238566972459"
opened_at: "2026-09-24T08:29:26Z"
outcome: defect
ticket: FUSE-1238
session_id: ca4715c6-f753-4733-a266-f699d5807b53
status: open
---
# Dock and Bay dev SO confirmation (DOCKDAA304A94BA / UK-903081) never delivered

## Reported
Thomas Dunn was testing Dock and Bay SO confirmations in dev. He reported that the confirmation for `DOCKDAA304A94BA` / `UK-903081`, from about 16:14 BST on 23 Sep, was still on the SNAP outbound queue. Datadog under correlationId `c4837ecf` showed SNAP fetch failures.

## Root cause
There were two layers.

1. **Platform defect.** The sales order failed in SNAP and was redriven from the retry queue. snap-adapter's failure envelope had overwritten `metadata.source` ("rest") with "snap-adapter", and replay re-sent that value. snap-adapter then stored it as the order's routing source. The poller published the confirmation with a `source` that no delivery subscription accepts, so it was never delivered or cleared, and was re-published every ~12 minutes. The same bug had poisoned 157 prod routing docs: STUBBLE 28 despatches stuck since 17 Sep, EPARFUM 7, WILDSMITH 2, PURDYFIGG 4. The SNAP errors in the reporter's logs belonged to another business (FUSEDEV) sharing the poll-cycle correlationId, so they were a red herring.
2. **Customer config.** Once routed, the Fulfil.io sandbox (`dockandbay-sandbox.fulfil.io`, the Fulfil.io Testing connector) rejects every webhook with 401 "Invalid x-webhook-secret-key". The connector's webhook secret doesn't match what Fulfil expects. `DOCK34A2DEAEEB6` failed webhook delivery to the same connector repeatedly on 23 Sep, likely for the same reason (not re-checked).

## Fix / Resolution
- **The fix:** snap-adapter#253, replay-service#94 and shopify-connector#280 (FUSE-1238) were merged and deployed to prod on 24 Sep at about 10:25Z. They stop `metadata.source` being overwritten after ingress.
- **Data repair:** routing docs were repaired between 10:27Z and 10:43Z (3 in dev including DOCKBAY, 156 in prod). The prod backlog was delivered and cleared from SNAP by about 10:53Z, confirmed over an hour-long soak.
- **Still open for DOCKBAY:** the confirmation now reaches fapi, but Fulfil rejects it (401). We're waiting on Dock and Bay to confirm the Fulfil webhook secret. The thread was updated on 24 Sep with the likely causes; per Harry, the platform bug wasn't mentioned there.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1790238566972459
- Ticket: https://globalfreight.atlassian.net/browse/FUSE-1238
- PRs: gfs-bifrost/snap-adapter#253, gfs-bifrost/replay-service#94, gfs-bifrost/shopify-connector#280
