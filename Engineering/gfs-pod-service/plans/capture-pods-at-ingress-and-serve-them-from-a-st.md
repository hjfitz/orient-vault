---
ticket: "none"
title: "Capture PODs at ingress and serve them from a store"
service: "gfs-pod-service"
status: draft
created: "2026-11-06"
updated: "2026-11-06"
repo: "unknown"
worktree: "unknown"
branch: "unknown"
base: "origin/master"
base_sha: "unknown"
pr:
tags: [waypoint, plan]
---
# none — Capture PODs at ingress and serve them from a store

<!-- Guidance in this file is written as HTML comments: Obsidian hides them, agents read them,
     and `wp signoff` ignores them. Only <angle spans> are treated as unfilled placeholders, so
     they mark the places a human or agent must actually type something. Leave the comments in
     place — deleting them costs the next reader the guidance and gains nothing at the gate.

     SUPERSEDING A STATEMENT. This file is edited by several sessions over days. When something
     here stops being true, do NOT strike it through, delete it, or bury a correction inside it.
     Put one blockquote immediately ABOVE the stale text and leave the text alone:

         > SUPERSEDED 2026-09-04 — the monitor now lives in `gfs-bifrost/observability`.
         > Everything below is kept as the record of how it was first built here.

     One marker, always above, never inside. `wp decide` writes the dated entry in
     `## Decisions & deviations` that explains why. -->

## Intent
<!-- What we are changing and why. Link the ticket. -->
Move POD capture to the ingress layer. Each carrier's connector or webhook fetches the POD and its images when a delivered event arrives, stores them in a central bucket and emits a pointer event (e.g. `pod.v1`). `gfs-pod-service` subscribes to that topic and becomes a read model, serving v2 from the store instead of calling the carrier live. The outcome: a POD is captured once per delivery, image links stay stable, and each carrier's API knowledge lives in one place instead of three (proxy, connector, POD module).

**Status: idea only.** The source is Harry (`user`), from the carrier-integrations research, and it came out of waypoint-ideate on 2026-11-06. The service belongs to the carriers team, which Harry doesn't own yet, so it isn't actionable until he does or that team agrees. No ticket.

Why (evidence, snapshot 2026-11-06):
- Carrier knowledge is spread by function rather than by carrier. UPS has a proxy, `connectors-ups` and a POD module with its own OAuth client; DHL Parcel UK has a connector, a POD module and `dhl-pod-images`. Amazon (via its proxy) and Evri (the `evri-auth-facade` token) already reuse their carrier's integration for POD. See [[architecture]] and [[known-context]].
- The live fetch depends on the carrier at request time. Image IDs go stale as the cache changes (G3). DHL is ~85% of POD requests in one shared process.

Considerations raised when the idea was formed (not decided):
- **Delivered detection:** connectors see raw carrier codes, but the mapping to GFS "delivered" happens downstream (response-publisher, tracking-mapper). Each connector or webhook needs its own POD-bearing-event rule.
- **Late images:** some carriers likely publish the image after the delivered event, so plan for retry with backoff, not one fetch.
- **Separate topic:** keep `pod.v1` apart from `raw_tracking.v1`, because timing and consumers differ and the tracking contract should stay stable. Payload: shipment IDs, carrier, parcel or consignment, signatory, time, GPS, object paths.
- **Personal data:** signatures and doorstep photos need retention, no public access, and serving through the API or signed URLs.
- **Migration:** move one carrier at a time, with the live fetch kept as a fallback for carriers not yet moved and for shipments delivered before cutover. v2 callers don't change.
- **Volume:** about 665k deliveries per 15 days against 21k on-request fetches today; small next to polling's 142M calls. Check each carrier's POD and image endpoint rate limits.
- **Odd ones out:** BJS is a scrape with SFTP tracking, so it has no connector to host the fetch. Royal Mail has no POD today, but its webhook may already carry a signatory (unconfirmed).

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [ ] <observable outcome>

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- <component / path / contract>

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- <assumption> — <how it was established: source read, ticket, asked>
- UNRESOLVED: <question that needs a human decision>

## Increments
<!-- Each independently implementable AND verifiable. Cite the criteria it discharges as
     (AC n,n). Tick with `wp tick`, which stamps `— done: <sha>` from HEAD; never hand-write it.
     Prefer 3-7 — more usually means the ticket is too big, so say that rather than splitting
     hairs.

     A PRECONDITION THAT IS NOT CODE goes on its own indented `gate:` line, with a confirmation
     box under it. Sign-off blocks on a ticked increment sitting above an unconfirmed gate, and
     `wp brief` shows unmet gates in its NEXT block — so "do not action this yet" stops being
     bold prose a fresh session can miss:

         - [ ] 6. Widen the subscription filter (AC 6) — verify: filter matches in dev
               gate: FUSE-1052 AND FUSE-1053 confirmed in prod
                     [ ] confirmed
-->

- [ ] 1. <increment> — verify: <how>
- [ ] 2. <increment> — verify: <how>

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- <YYYY-MM-DD> [inc <n>] <what was run, against what, and the observable result>

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- <what remains unproven, and what would prove it>

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
