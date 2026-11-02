---
tags:
- waypoint
- config-service
- decision
decided: '2026-10-27'
status: accepted
---
# Delivery and fulfilment backends share one BACKEND_CONFIG model; each portal owns its backend types

## Context
<!-- What forced a choice. -->
Selector (delivery) needs per-business config. The same business has to show in both Fuse (the fulfilment portal) and Merak (the delivery portal). Harry, 2026-10-27: a business lives once in config-service, Fuse adds only Snap backends, and Merak adds only Selector backends (or Selector's replacement later). The deduper tags each order with the business's configured backends, and a business may later need several backends so that one order is broadcast to all of them.

Today, on `origin/main`:
- A business has exactly one backend. `BackendConfigService.fetchBackendConfigForBusiness` does a `findOne` by `businessId`, and the routes are the singular `/business/{id}/backend`.
- `type` is `z.literal("SNAP")` in `@gfs-bifrost/types` (`backend-fragment.schema.ts`).
- The poller (`snap-adapter/apps/snap-queue-polling-service/.../fuse-config.api.ts`) and snap-adapter (`adapters/config/config.api.ts`) fetch all backends from `/api/v1/backend`. They validate each whole page against the SNAP-only schema, so one non-Snap row fails every business's Snap config.

## Options considered
<!-- Chosen first, then each rejected one, each with its because. -->
- **Chosen: one `BACKEND_CONFIG` model, discriminated on `type` (`SNAP | SELECTOR`), stored per business as a collection addressed by the existing `backendId`.**
  - config-service stays type-agnostic: which portal may create which type is the portal's rule. That keeps the delivery/fulfilment classification out of the shared config model.
  - Multiple backends are built in, not retrofitted.
- **Rejected: a Selector-only config resource beside `BACKEND_CONFIG`.** This was the spike plan's original line. A third backend type would need yet another resource, and broadcast across types would need the deduper to know about every resource.
- **Rejected: the portal inside the selector-adapter repo.** Merak is its own product and GitHub org. The ilg-merak `svc-template` already ships an `apps/ui` Next scaffold with dev/prod deploy workflows (svc-template#1, open as of 2026-10-27).

## Consequences
<!-- Good, and the cost accepted. -->
> SUPERSEDED 2026-10-27 — the SNAP default is a visible `?type=` query param on the existing routes, not a hidden filter (Harry, on config-service#248). The list and revision-event points below still hold.
- **The old surfaces stay SNAP-only, so no existing consumer has to upgrade before the first Selector backend exists:**
  - an unfiltered `GET /api/v1/backend` returns only SNAP backends; `?type=` opts in to other types;
  - the singular `/business/{id}/backend` routes return the business's SNAP backend;
  - `BACKEND_CONFIG` revision events are published for SNAP backends only. Otherwise remote-config subscribers would fail to parse an unknown type and redeliver forever, the same hazard as types 10.4.0's `edi`.
> SUPERSEDED 2026-10-27 — there is no plural route. With at most one backend per type per business, business plus type identifies a backend, so Selector readers call the existing routes with `?type=SELECTOR` (A3 widens the accepted types). `backendId` addressing waits until a business has two backends of one type.
- **Selector readers** (the deduper, selector-adapter, the Merak portal) use a new plural `/business/{id}/backends` route through a cached lookup.
- **Routing.** On `create_record`, the deduper stamps one boolean attribute for each backend type the business has (`snap`, `selector`). Each adapter's subscription filters on its own type, so broadcast across types takes one publish. A failed lookup nacks and never forwards untagged.
- **Multiple backends of the same type** are resolved inside that type's adapter, with idempotency claims keyed per (order, `backendId`), so a partly failed fan-out retries only the backends that missed.
- **Cost: at most one backend per type per business** until every consumer of the singular routes and the SNAP-only list (fuse-ui, wms-gateway, snap-adapter, the poller, fuse-mcp `get-snap-connection`) has moved to the plural route. config-service enforces this limit.
- **Not covered by the per-type tags:** choosing between backends of the same type for each order (as opposed to broadcasting to all of them). If that's ever needed, it's adapter logic or a later per-`backendId` tag.
- **Confirmations aren't backend-aware.** They carry `businessId`, not `backendId`, so two Snap backends confirming the same order would duplicate downstream. That's out of scope until a business really has two Snap backends.
- **Ordering hazard:** snap-adapter's `create_record` subscriptions switch to filtering on `snap="true"` only after the deduper is stamping `snap` in prod. Otherwise Snap traffic stops.

## Confirmation
<!-- The signal in prod that would show this was wrong. -->
- After the first Selector backend is saved: a poller or snap-adapter config parse failure on `/api/v1/backend`, or a remote-config nack loop on `config_revision`. Either means a SNAP-only default leaked a Selector row.
- An order for a business with a Snap backend that never reaches snap-adapter after the subscription swap. That means the deduper isn't stamping `snap`.
