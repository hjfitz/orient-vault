---
title: "Tracking Service — Overview"
status: active
verdict: go, with the cutover held for sign-off
owner: "Harry Fitzgerald"
services: ["tracking-service", "fuse-ui", "observability"]
created: "2026-10-05"
updated: "2026-10-07"
tags: [bifrost]
---
# Tracking Service — Overview

> Backfilled 2026-10-07, three days after the work began. Progress lives in the Migration State doc;
> this one holds the why.

## Deliverables
- [[Bifrost/Tracking Service/Migration State|Migration State]] — the live source of truth for progress
- Repo: `gfs-bifrost/tracking-service` (renamed from `fuse-tracker`); plan `docs/productionisation.md`, runbook `docs/cutover.md`
- The order tracker page in fuse-ui: PRs #287, #289, #290, #291, #292
- Dashboard and monitors in the observability repo (unmerged; waits for the cutover)
- Live today: https://fuse.ilg.software/order-tracker (flagged), and the standalone UI at https://esm.fuse.ilg.software (prod) and https://esm.fuse.freightops.dev (dev)

## Verdict
**Go.** The service is already running in prod on its first-build stack and support are using the tracker
(the first feedback round came from Jack on day three). The remaining one-way door is the database
cutover, which waits for Harry's sign-off on the review pack (gate G1).

## Why this needs a programme
Fuse had no place that followed a shipment or a return end to end, including their confirmations; support
answered "where is order X" by walking logs and several UIs. What began as a skunkworks tracker became a
service the L2 support team works from, which meant productionising it (a new database kept forever, a
zero-loss cutover, observability, dead letters) while the page on top of it was still changing daily. The
cutover is a one-way door and the support work shipped around it, so the two had to be sequenced.

## Strategy
Three groups, built in this order:
- **A. The skunkworks build** (done): the Go API, returns, the MCP, the hidden fuse-ui page.
- **B. Productionisation**: a new `tracking-service` stack and Firestore database, then a cutover per
  environment (dev first). The new stack is in the repo and planned, but not applied. Ingest is held so the
  new subscriptions build a backlog, the old database is exported and imported, and message ids are the same
  on every subscription, so the backlog replays idempotently. fuse-ui's URL switches last, and the legacy
  stack is destroyed after a clean week.
- **C. The order tracker as an L2 work queue**: feedback-driven fixes and features that ship on the legacy
  stack in the meantime. Anything that needs a new index waits for the new database.

## Scar tissue
Identity is businessId + customer reference, and a record is counted once on its first failure; see the
Migration State for the rest.

## Next
**G1:** share the review pack with Harry (new-stack plans, legacy unchanged, observability plan, runbook).
Then **B2**, the dev cutover, driven by `waypoint-programme`. In parallel, **C6** (per-connector confirmation
status) waits on a ship decision and **C7** (the UX-review fixes) is approved and unstarted.
