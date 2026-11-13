---
title: "Native Dispatch — Overview"
status: planning
verdict: undecided
owner: "Harry"
services: ["parcel-portal"]
created: "2026-11-13"
updated: "2026-11-13"
tags: [bifrost]
---
# Native Dispatch — Overview

<!-- The narrative and the verdict. PROGRESS lives in the Migration State doc, not here — link it,
     never duplicate its ledger. This doc changes rarely; the state doc changes every session. -->

## Deliverables
- [[Native Dispatch/Migration State|Migration State]] — the live source of truth for progress
- [[Native Dispatch/Requirements|Requirements]] — the 13 Nov feedback as 17 numbered requirements, each traced to who asked and checked against the code
- History: the [[Parcel Portal/Overview|Parcel Portal Overview]] and its [[Parcel Portal/Migration State|Migration State]] (units A to D, and the held prod gate D1)
- Sources: Teams messages from Phil, Pete and Chris (13 Nov); Oliver Wilders' Slack DM (12 to 13 Nov); the 13 Nov team catch-up, recording `20261113-093409-e9a5`

## What it is
Native Dispatch is GFS's own dispatch portal for shippers whose warehouse system drops order CSVs. It was called Parcel Portal until the 13 Nov catch-up, where the new name was chosen because "it describes what it does". Staff import orders by CSV (SFTP or a browser upload), fix the bad rows, pack, dispatch and print through Selector, and export the day back to the customer's system. TCA (Yusen US, FedEx) is the first customer. The repo is `ilg-merak/parcel-portal`, and the service and system ids keep that name.

## Where it stands (13 Nov)
- TCA saw a demo on 12 Nov. Oliver reports the feedback was "additive", and estimates the process drops from about 40 clicks in Despatch Cloud to three.
- Prod is held at D1 in the Parcel Portal programme. Work and testing go on in dev.
- On dev, TCA's customer validates all six FedEx services on version-test. On 13 Nov Oliver asked to test-print against TCA's live endpoint, Harry agreed, and Oliver reports a label was generated.
- Per the catch-up, the next step is one proof against TCA's endpoint, then an account for TCA, who will start by dispatching one order at a time by hand. Oliver expects the proof to pass because nothing changes "beyond where it's pointing".

## Verdict
Undecided on prod, as in the Parcel Portal programme: that call waits on D1 and on G7 there (building outside Fuse, agreed with Oli Denton). Building and testing in dev goes on. The conditions that matter here are two: TCA's first manual order has to dispatch cleanly, and nothing about a live carrier account may be sent or committed without a person deciding it.

## Why this needs a programme
Feedback now arrives in batches from several people (Phil, Pete, Chris, Oliver), some of it overlapping or changing an earlier call (Phil first wanted contact details editable, then accepted read-only), and a live carrier account sits behind the dispatch path. Numbering each ask, tracing it to who said it and checking it against the code stops items being dropped or argued twice. Three of the 17 turned out different from how they were put: the preset-dimensions complaint is a real bug, "cancel label" mostly exists already, and Chris's legacy fields belong to Selector2.

## Strategy
One unit is one PR. Each goes through `review-panel`, then merges once CI is green. No agent approves a prod gate. Units are taken in waves:
- **Wave 1, what blocks TCA's first manual order:** T3 then T4 (weight 0 and the five templates, approved), I1 (the preset bug), T2 (ShipperId 0), L1 (void from the order page, so test labels on the live box can be cancelled), O1 (contact details).
- **Wave 2, the order page:** O3, O6, O2, O8, and I2.
- **Wave 3, larger changes:** O4 and O7.
- **Waiting on an answer:** I3 and O5 (G1), X1 (G2), T6 (G3), T7 (G4), L2 (G6), T11 (G7).

### Parallel plan (13 Nov, for the orchestrated run)
Five builder lanes, each its own worktree under `~/code/merak/parcel-portal/.claude/worktrees/`, each running its own throwaway Postgres on a lane-specific port and container name (never port 3000, never another lane's container, kill only exact PIDs). Builders commit locally, run the repo's gates, gather evidence and stop; the conductor pushes, opens the PR, runs `review-panel`, merges once CI is green, ticks the ledger and writes the `wp ledger` entry (`--programme "Native Dispatch"`).
- **Lane 1, chores:** T14 (Trivy renew, due before 16 Nov), then T13 (the rename, including the export's `salesChannel`), T9, T15. No contract or migration.
- **Lane 2, svc carrier:** T3 (Go only: the preset table only checks `weight <> ''`), then T2 (migration 020, `connection.go`, request XML test).
- **Lane 3, svc import:** I1 (no migration, no contract), then I2 (migration 021 and a contract bump, rebased after T2 merges).
- **Lane 4, UI order page:** O1, O8, O6, then L1, strictly in series, because they share `orders/[id]/order-form.tsx`.
- **Lane 5, svc order API:** the svc halves of O3 (a customer-readable services list) and O2 (total weight and the export).
- **Conductor, foreground:** T4 (the five templates, after T3 is on dev), T5, and dev checks through the debug MCP after each deploy.
- **Contract and migration order:** migrations 020 (T2) and 021 (I2) are reserved. Contract PRs merge one at a time, in the order T2, O3, I2, then O4. Each regenerates and takes the next minor `info.version` just before its merge.
- **Held back:** O3 and O2 UI halves, O4 and O7 (they need lanes 4 and 5 merged first), I3 and O5 (G1), L2 (G6), X1 (G2), T6 (G3), T7 (G4), T11 (G7), T12. T1 is human-led and T8 changes dev state.
- **No agent** calls CommitShipments, PrintManifest or ProcessCarrierDispatch, sends anything to TCA's live endpoint, or approves a prod gate.

## Scar tissue
Kept in the [[Native Dispatch/Migration State|Migration State]]: no commit or manifest calls by an agent, no prod gate approved, nothing sent to TCA's live endpoint without Harry, nothing about an order defaulted.

## Context from the catch-up (not units)
- TCA is testing Manhattan against the Selector server directly, and wants an API as MVP2, with a first test planned for 30 Nov. Phil leads that conversation. The API key UI stays hidden (S1; Harry, 13 Nov), and the API and keys stay up for that test.
- The team wants a named decision-maker on Yusen's side and an org chart, to raise at the in-person session on Monday 16 Nov at 11:00.
- The recording is auto-transcribed, so names and terms are approximate. "VT changes for native dispatch" is unclear and is in Q8.

## Next
Wave 1, starting with T3, the weight 0 change Harry approved. Driven by `waypoint-programme`. Phil's call (G1) and Oliver's answer on cancelling (G6) are the two people-dependencies worth chasing first.
