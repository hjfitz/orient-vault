---
tags:
- waypoint
- snap-adapter
- decision
decided: '2026-11-05'
status: accepted
---
# SNAP resilience is shared through @gfs-bifrost/resilience, not the snap package or an in-repo package; a 429 trips the breaker

## Context
Before the Purdy & Figg peak (2026-11-06), an audit found the SNAP resilience primitives copied three ways.
- **Adapter:** a hand-rolled circuit breaker on which a 429 resets, plus a local `Semaphore` with an acquire timeout, a `TokenBucket` and a retry interceptor.
- **Poller:** its own cockatiel breaker on which a 429 trips, a retry interceptor, no concurrency cap, and no request timeout outside stock sync.
- **pkg-node:** `@gfs-bifrost/resilience` 0.1.0 (`PerHostCircuitBreaker`, `Semaphore` without a timeout, backoff). Its only consumer is `@gfs-bifrost/snap`, which re-exports it.

The two services also tag `snap_host` differently: the adapter uses the origin, and the poller appends `/api`.

## Options considered
- **Chosen: `@gfs-bifrost/resilience` (pkg-node).**
  - Release 0.2.0 additively: the adapter's timeout `Semaphore`, `TokenBucket`, and a per-host breaker state readout.
  - Both apps plug the primitives into their own `AxiosBuilder` through axios's `adapter` hook, so cockatiel's `execute()` wraps the real request. Interceptor-only gating is why the adapter hand-rolled its breaker.
  - The host key (origin, lowercased) and the transient rule (5xx, network error or 429) stay small and local to each app, pinned identical by tests.
- **Rejected: an in-repo package in snap-adapter.** The repo isn't a workspace (no root `package.json` or `pnpm-workspace.yaml`); FUSE-1006 already chose pkg-node over in-repo packages; and it would be a fourth copy that snap-mcp and shopify-connector couldn't use.
- **Deferred, the eventual target: both apps on `@gfs-bifrost/snap`** (Harry, 2026-11-05: "eventually"). Not part of the resilience step, because its response types are still largely unverified against live SNAP (about 28 entities never checked) and we haven't relied on hard response parsing in over a year of running.
  - Adopt it in layers: `client` helpers (endpoints, transient classification, write-envelope checks), then `http`, then `types`, one entity at a time as each is live-verified.
  - The poller still imports its SNAP schemas from `@gfs-bifrost/types`' old `snap/` copy. Moving it to `@gfs-bifrost/snap/types` is what unblocks deleting that copy, a breaking `types` major.
- **429 trips the breaker** in both services, matching `isTransientSnapStatus`: sustained SNAP throttling backs us off instead of resetting the failure count.

## Consequences
- One breaker and semaphore implementation across adapter, poller and snap-mcp. The poller gains a request timeout and a concurrency cap.
- Metric names must move in lockstep with the observability repo. Monitors 337501612 and 341185701 read `snap.circuit_opened` and `snap.circuit_breaker.state`, so emit the new names alongside the old, repoint, then drop the old.
- Accepted cost: a small amount of duplicated glue (axios wiring, host key, transient rule) per app.

## Confirmation
- A breaker opening on a 429-only throttle storm and starving a healthy backlog. Check `snap.circuit_opened` against 429 counts per host.
- Divergent behaviour between the two apps' glue despite the pinning tests.
