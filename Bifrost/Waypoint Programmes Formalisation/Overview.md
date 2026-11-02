---
title: "Waypoint Programmes Formalisation — Overview"
status: in-progress
verdict: go
owner: "Harry Fitzgerald"
services: ["waypoint-tooling", "orient"]
created: "2026-09-10"
updated: "2026-09-10"
tags: [bifrost]
---
# Waypoint Programmes Formalisation — Overview

## Deliverables
- [[Waypoint Programmes Formalisation/Migration State|Migration State]] — the live source of truth for progress
- **A** — `templates/programme.md` + `wp programme` (new/status/next/tick) + the plan↔unit link
- **B** — an orient `ProgrammeReader` detail view with a progress rollup
- **C** — a generic `waypoint-programme` skill, replacing the five bespoke ones incrementally

## Verdict
Go. The pattern is proven five times over by hand; formalising it removes ~80% duplicated skill prose,
makes the unit ledger machine-readable (`wp programme`), and gives programmes the first-class orient view
plans already have.

## Why this needs a programme
Five hand-rolled programme skills share one skeleton but drift; the ledger is readable only by each
skill's own prose; orient renders programmes as raw markdown. It touches core tooling (`wp.py`), the
skills, and orient at once — enough moving parts, and enough risk in migrating the two active programmes,
to sequence and gate rather than just do.

## Strategy
Build the data model + tooling first and prove the tolerant ledger parser against the real hand-authored
ledgers (Gate A); then the orient view (Gate B); then the generic skill, proven on the one complete
programme before any active one migrates (Gate C). A unit stays a ledger row, promotable to a plan.

## Scar tissue
The Overview carries no `programme:`/`-state` marker (only the State doc is the ledger); frontmatter
`{{token}}`s must be whole values; `wp programme tick` edits table cells by position. See the State doc.

## Next
Deliverable B — orient's `ProgrammeReader`. Driven by `waypoint-programme` once that exists (S1);
until then, by hand. Unit ledger and `wp programme status` are the source of truth for progress.
