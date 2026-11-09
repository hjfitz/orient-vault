---
title: "SNAP Resilience Normalisation — Overview"
status: active
verdict: go
owner: "Harry Fitzgerald"
services: ["pkg-node", "snap-adapter", "snap-queue-polling-service", "observability"]
created: "2026-11-05"
updated: "2026-11-05"
tags: [bifrost]
---
# SNAP Resilience Normalisation — Overview

## Deliverables
- [[SNAP Resilience Normalisation/Migration State|Migration State]], the live source of truth for progress.
- **Phase 1:** both SNAP services run their SNAP resilience on `@gfs-bifrost/resilience` 0.2.0, with one breaker-metric vocabulary that monitors read (groups A–D).
- **Phase 2 (deferred):** both services move onto `@gfs-bifrost/snap`, behind a strict/tolerant response-parsing breakglass env var (group E).
- Decision record: [[snap-adapter/decisions/2026-11-05-snap-resilience-is-shared-through-gfs-bifrost-resilience-not|SNAP resilience is shared through @gfs-bifrost/resilience]].

## Verdict
**Go, Phase 1 first.** No prod behaviour change ships until the Purdy & Figg peak has passed (gate G1). Phase 2 starts only once Phase 1's metrics have soaked.

## Why this needs a programme
- **Copies:** the SNAP circuit breaker, concurrency slot and rate limit exist as two divergent app copies plus a shared package that neither app uses.
- **Behaviour:** they disagree on 429, half-open and host keying.
- **Contract:** the breaker metrics are a contract that live monitors read.
- **Scope:** four services. Some steps change how prod behaves against a WMS that has melted down under load before (May 2026). Others can only be proved by a soak.

## Strategy
1. **Release the primitives.** Grow the package additively (0.2.0), then move each app onto it, the adapter and the poller independently. Wrap at axios's `adapter` hook so cockatiel's `execute()` sees the real network call.
2. **Behaviour changes ship separately**, each behind a config switch defaulting to today's behaviour: 429 trips, single-probe half-open, the poller cap.
3. **Metric renames are dual-emitted:** new names alongside old, new monitors, a parity soak, then the old names are deleted.
4. **Phase 2** lifts the transport into `@gfs-bifrost/snap/http` and migrates SNAP response types one entity at a time. A breakglass env var falls back to today's tolerant parsing.

## Scar tissue
See [[SNAP Resilience Normalisation/Migration State#Scar tissue|Migration State → Scar tissue]].

## Next
**N1** (pkg-node: port the timeout semaphore and token bucket into `@gfs-bifrost/resilience`), driven by `waypoint-programme`. **Q1** (poller request timeout) has no dependency and can run alongside it. Neither is prod-visible before G1.
