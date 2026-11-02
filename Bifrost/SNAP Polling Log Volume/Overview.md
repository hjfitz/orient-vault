---
title: "SNAP Polling Log Volume — Overview"
status: planning
verdict: undecided
owner: ""
services: ["snap-queue-polling-service"]
created: "2026-09-22"
updated: "2026-09-22"
tags: [bifrost]
---
# SNAP Polling Log Volume — Overview

<!-- The narrative and the verdict. PROGRESS lives in the Migration State doc, not here — link it,
     never duplicate its ledger. This doc changes rarely; the state doc changes every session. -->

## Deliverables
<!-- The live state doc, any external artifacts (a plan-of-record, an architecture review, a test
     plan), and the named tranches/deliverables if the work splits into separately-shippable phases. -->
- [[SNAP Polling Log Volume/Migration State|Migration State]] — the live source of truth for progress
- Baseline measurement: 395,752 logs/day on `service:snap-polling-service` (prod), 2026-09-22 —
  87% (345,517) from one un-deduplicated warn, the rest split across a duplicated raw-error log
  pair (12,431/day), info-level poll chatter (22,167/day), and 8,850/day debug logs that shouldn't
  reach prod at all.

## Verdict
Undecided — nothing has shipped yet. Target: cut daily volume by an order of magnitude, from
~396k/day toward the tens-of-thousands, while keeping (or improving) the operational visibility
the removed log lines currently provide. A1 alone removes ~87% of current volume; B/C close the
remainder and add the monitoring this service never had.

## Why this needs a programme
Nine units span three different failure classes (one un-deduplicated warn dominating volume, a
duplicated/oversized error-log pair, and assorted lower-volume discipline gaps) with real
sequencing between them — B2 depends on A1/A2 landing first, C2 depends on A1's metric and C1's
monitor both existing. It's also a measurable before/after (a log-volume number), which a ledger
tracks better than a pile of independent one-off PRs with no shared baseline. Sits alongside
[[Confirmation Enrichment Pipeline/Overview|Confirmation Enrichment Pipeline]] in the same repo
and service, but is a distinct concern (logging/observability discipline, not the confirmation
mapper's structure) — deliberately kept as its own programme rather than folded into that one.

## Strategy
Group A first — the two units (A1, A2) that account for the overwhelming majority of volume and
byte-cost, landed independently since neither depends on the other. A3 follows, touching the same
failure path as A2. Group B cleans up what's left once A's shape is settled (B2 explicitly needs
A1/A2 merged to know what "remaining" means). Group C adds the monitor and dashboard tab last,
once there's a metric (A1) worth watching. No cutover/flag — each unit is an independent,
behaviour-preserving-except-for-logging change, mergeable and shippable on its own.

## Scar tissue
- The StU-not-found warn (A1's target) was deliberately added by FUSE-1009/#196 to replace
  silent-zeroing with visibility. Removing the log line is not a reversion to silence — see R1 in
  the Migration State and don't let A1 ship as a pure deletion.
- Root-causing *why* SNAP never returns a StU for the ~4,207 stuck consignments is explicitly out
  of scope here (discarded during ideation) — this programme treats the condition's observability,
  not its underlying cause.

## Next
**A1** and **A2** are both unblocked — either can start first; recommend A1 given it's 87% of the
volume. Drive with `waypoint-programme` (`wp programme status "SNAP Polling Log Volume"` /
`wp programme next`), promoting a unit's existing draft stub with `wp plan new
snap-queue-polling-service --programme snap-polling-log-volume --unit A1` (etc.) rather than
starting blank — every unit already has ideation context in `plans/`.
