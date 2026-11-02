---
title: "Poller Clear-Down — Overview"
status: done
verdict: go
owner: "Harry"
services: ["snap-queue-polling-service", "snap-adapter", "fapi", "sftp-connector", "shopify-connector", "replay-service", "fuse-ui", "observability"]
created: "2026-09-29"
updated: "2026-10-13"
tags: [bifrost, snap-queue-polling-service, confirmations]
---
# Poller Clear-Down — Overview

<!-- The narrative and the verdict. PROGRESS lives in the Migration State doc, not here — link it,
     never duplicate its ledger. This doc changes rarely; the state doc changes every session. -->

## Deliverables
- [[Poller Clear-Down/Migration State|Migration State]] — the live source of truth for progress
- `Findings/` — the 2026-09-29 feasibility study (14 read-only investigations; every gap claim was
  re-checked at source by an independent skeptic). Each report has an exit-path table per component —
  the A-group units work from those tables. Key ones: `poller-lifecycle.md`, `poller-deferral-semantics.md`,
  `fapi-egress.md`, `sftp-egress.md`, `shopify-egress.md`, `replay-service.md`, `snap-obq-semantics.md`.
- No Jira ticket/epic — Harry's choice (2026-09-29). PRs reference this programme by name and get an
  out-of-ticket `wp ledger` entry each.

## The change
snap-queue-polling-service today: fetch the row from SNAP's outbound queue (OBQ) + its data → publish the
canonical confirmation. The row stays on the OBQ until a delivery service publishes `confirmation_made`
and snap-adapter PATCHes it processed.

After this programme:
1. Fetch the confirmation from the OBQ and its data *(unchanged)*
2. Publish it to Pub/Sub as usual *(unchanged)*
3. **Clear the row from the OBQ** (`PATCH /v2/snapoutbound/{queueId}/processed`, the call snap-adapter
   makes today) once the publish is acknowledged — replacing snap-adapter's `confirmation_made` clear-down.

Each SNAP confirmation is announced once.

## Verdict
**Go.** The poller change is small. What makes it safe is elsewhere: today every downstream
non-delivery is silently rescued because the row is still on the OBQ and gets re-announced every ~10 min
(claim TTL). After step 3 that rescue is gone, so every downstream exit must end in a recorded terminal
outcome — delivered (`confirmation_made`) or a failure in replay-service that an operator can redrive.
The programme is those prerequisites plus the three steps.

## Why this needs a programme
Eight repos, and the flip is one-way per business: once a row is processed, SNAP's list route no longer
returns it (it is only readable by id). The feasibility study found the downstream services
acknowledge-and-log on most non-delivery paths, replay redrive reaches no connector for 6 of 8 types, and
the OBQ is shared with Jitterbit for split customers. None of that is visible from the poller.

## Strategy
- **Prerequisites first, in parallel, one repo each** (groups A, B): every fapi / sftp-connector /
  shopify-connector non-delivery publishes `confirmation_data_failure`; replay redrive carries routing and
  lets an operator edit it.
- **Poller code lands dark** (group C): the clear runs only for businesses on a poller env allow-list,
  default empty.
- **Cutover is per business** (D1): add a business to the allow-list once the gates are clear; revert by
  removing it (rows just go back to the old clear-on-made path).
- **Retire snap-adapter's clear-down last** (D2), once every confirmation-live business is allow-listed
  and broadcast has its own terminal outcome (G5). v1 clears **routed rows only**; broadcast rows stay on
  snap-adapter's clear-on-made path until then.

Out of scope: `stock_adjustment` (no failure sink anywhere; stays on today's `stock_adjustment_made`
path), receipt stores / ledgers, and anything the Confirmation Enrichment Pipeline programme owns.

## Next
A1, A2, A3, B1, B2 are unblocked and independent — drive them with `waypoint-programme`.
