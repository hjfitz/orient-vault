---
tags: [waypoint, dedupe-service]
title: dedupe-service — known context
---
# dedupe-service — known context

What source cannot tell you. Established by interview 2026-08-24 unless marked otherwise.

## Intentional boundaries

The service exists as a **deliberate single choke point** — every ingress path inherits one
gate, and connectors know nothing about dedupe. Treat as intentional: don't move gating
upstream into a connector, don't let anything else publish `create_record`.

## Fragility

**Ack-first is an accident, not a design.** `postRequest` sends `204` before any processing
begins, so the outcome never reaches Pub/Sub: work lost after the ack is lost silently, and
there are no dead-letter topics to catch it. This was never a considered trade-off — nobody
revisited it — and it is the one thing that actually bites people working here. Worth a ticket
in its own right. Do not "document it as intent"; it isn't.

Notably *not* a live pain point despite looking like one: a changed resend forwarding and
upserting over an in-flight WMS shipment. The semantics allow it; in practice it doesn't bite.

## Contractual surfaces

`/api/v1/record/...` has **two live consumers** — fuse-ui's Dedupe Summary and the Fuse MCP
dedupe tools. Its response shapes are effectively frozen: changing them needs coordinated
updates in both. It carries no real versioning.

**Releases are support self-serve.** TSE/support clear held records themselves through fuse-ui;
engineering is involved only when the UI can't do it. That makes the admin API an operational
surface, not an engineering convenience — availability and response-shape stability matter more
than they would for an internal-only endpoint.

## What surprises people

`master_data` is all-or-nothing for the SKU blacklist. It's a single product with no lines, so
the blacklist either drops the record entirely or leaves it untouched — there is nothing to
strip. Every other record type has lines and gets partial stripping.

## Documentation drift — verify before trusting

- `README.md` is badly stale: describes Firestore (it's MongoDB) and a purchase-order-only
  service (there are five record types). Trust nothing in it.
- `CLAUDE.md` is the real reference but has drifted twice, both found 2026-08-24 by reading
  source: it says **"four record types"** (there are five — `work_order` was added later) and
  says the record admin API is **unauthenticated** with auth as a follow-up (`apiKeyMiddleware`
  is applied in `app.ts`).
- `iac/.../pubsub.tf` still declares three legacy `*_request_subscription_name` locals that
  nothing references — dead since the cross-entity `create_record_request` cutover.

## In-flight work

The **Express → NestJS migration is actively in progress**, tracked in Obsidian
(`Bifrost/Dedupe NestJS Migration/`) and driven by the `dedupe-nest-migration` skill rather
than a Jira ticket. No `@nestjs` dependency exists yet — what has landed is the safety net: the
in-process HTTP harness, infrastructure seams, and the characterization suite. **Do not undo or
casually refactor those**, and coordinate through the migration skill before changing structure.

## Unknowns

- Is there an owner or a target date for fixing the ack-first silent-drop path, or is it
  currently just known-and-accepted?
- Does any consumer depend on `/events/v1` remaining alongside `/events/v2`, or can v1 be
  retired once release-from-failure covers everything?
