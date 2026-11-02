---
title: "Delivery Backends — Overview"
status: planning
verdict: go
owner: "Harry"
services: ["pkg-node", "config-service", "dedupe-service", "selector-adapter", "snap-adapter", "fuse-mcp-server"]
created: "2026-10-27"
updated: "2026-10-27"
tags: [bifrost]
---
# Delivery Backends — Overview

<!-- The narrative and the verdict. PROGRESS lives in the Migration State doc, not here — link it,
     never duplicate its ledger. This doc changes rarely; the state doc changes every session. -->

## Deliverables
- [[Delivery Backends/Migration State|Migration State]], the live source of truth for progress.
- Decision record: [[config-service/decisions/2026-10-27-delivery-and-fulfilment-backends-share-one-backend-config-mo]].
- This programme follows on from the [[selector-adapter/plans/selector-adapter-dev-spike|selector-adapter dev spike]]. The spike proves Selector booking against a static, env-backed connection. This programme replaces that connection with real per-business config, and it supplies the routing the spike's live e2e (its Gate D) waits on.
- A new repo in the **ilg-merak** GitHub org holds the Merak delivery portal.

## Verdict
> SUPERSEDED 2026-10-27 — PM/EM have already decided: the split goes through a separate delivery portal. G2 is cleared, and prod waits only on the remaining gates.
**Go for dev.** Prod for anything that books in Selector waits on PM/EM's delivery-vs-fulfilment product call (G2). The config-service and deduper units are safe to take to prod earlier. Until a Selector backend exists they change nothing, because every old surface stays SNAP-only.

## Why this needs a programme
- **One shared model, two products.** A business lives once in config-service and appears in both portals. Fuse (fulfilment) adds only `SNAP` backends, and Merak (delivery) adds only `SELECTOR` backends.
- **The work spans 6 repos and two GitHub orgs.**
- **A single Selector row can break Snap for everyone.** The poller and snap-adapter validate whole pages of `/api/v1/backend` against a SNAP-only schema, so one Selector row fails Snap config for every business.
- **The cutover has a hard order.** If snap-adapter's subscription starts filtering on a `snap` tag before the deduper stamps it, Snap traffic stops.

## Strategy
1. **Contract first (A).** `@gfs-bifrost/types` gains a `SELECTOR` backend type alongside SNAP, additively.
> SUPERSEDED 2026-10-27 — no plural route: the existing routes take `?type=`, defaulting to SNAP (Harry, on config-service#248). See the Decision log.
2. **Make config-service's old surfaces SNAP-only (A2).** This is a no-op today, since every row is SNAP. It has to land before anything can store a Selector backend (A3). Selector backends are read and written only through a new plural `/business/{id}/backends` route.
2a. **The existing backend routes take a `?type=` query param that defaults to `SNAP` (A2).** Callers that send no type see exactly what they see today. A3 widens the accepted types to include `SELECTOR`; Selector readers and the portal use the same routes with `?type=SELECTOR`. With one backend per type per business, business plus type identifies a backend, so no plural route is needed.
3. **Routing (B).** The deduper stamps one boolean attribute per backend type the business has (`snap`, `selector`) on `create_record`, and each adapter's subscription filters on its own type. Broadcast across types is then one publish.
4. **Last cutover (B3):** snap-adapter's subscriptions switch to filter on `snap`, once prod stamping is proven.
5. **Merak portal (C).** An unstyled Next app built from ilg-merak `svc-template`'s `apps/ui`. It manages only `SELECTOR` backends.
6. **Several backends of one type (D) is deferred** until a business needs it.

## Scar tissue
- **The delivery/fulfilment split lives in the portals, never in config-service.** config-service stays type-agnostic.
> SUPERSEDED 2026-10-27 — the default is now a visible `?type=` param, and there is no plural route.
- **Old backend surfaces return SNAP only, permanently, until D1 retires them.** That covers the unfiltered list, the singular routes and `BACKEND_CONFIG` revision events. Readers outside the old surfaces opt in with `?type=` or the plural route.
- **A backend route called without `?type=` acts on SNAP backends only.** That covers the list, the per-business routes and `BACKEND_CONFIG` revision events, which stay SNAP-only. Readers of other types always pass `?type=`.
- **At most one backend per type per business until D2.**
- **Selector is never shown in fuse-ui.**

## Next
**A1, the types union.** Drive it with `waypoint-programme`.
