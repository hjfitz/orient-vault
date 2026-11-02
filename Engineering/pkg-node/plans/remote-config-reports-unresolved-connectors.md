---
ticket: none
title: remote-config reports unresolved connectors
service: pkg-node
status: complete
created: '2026-10-02'
updated: '2026-10-05'
repo: /home/hjf/code/fuse/pkg-node
worktree: /home/hjf/code/fuse/pkg-node/.claude/worktrees/remote-config-unresolved
branch: hjf/remote-config-unresolved-connectors
base: origin/main
base_sha: 386ffa712
pr: '261'
tags:
- waypoint
- plan
programme: poller-clear-down
unit: E8
impl_model: opus
impl_effort: high
---
# none — remote-config reports unresolved connectors

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
Part of [[Poller Clear-Down/Migration State|Poller Clear-Down]] unit **E8** (no ticket; Harry, 2026-10-02: autonomous, no code review). remote-config's business-level connector resolve drops any connector whose GET or schema validation fails, and never indexes it, so a fan-out consumer silently delivers to the rest. Release `@gfs-bifrost/remote-config` 2.3.0 with `resolveWithUnresolved`, which returns `{connectors, unresolved}`, and index failed ids so they keep being reported.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. `resolveWithUnresolved(businessId, type?)` lists each connectorId whose fetch or validation failed in `unresolved`, beside the connectors that resolved.
- [x] 2. A failed connector is added to the business index, so a later cached read reports it as unresolved again.
- [x] 3. `resolve()` is unchanged for callers: it still returns only resolved connectors.
- [x] 4. 2.3.0 is published to GitHub Packages.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `pkg/remote-config/src/handlers/backlinks/connector.handler.ts`: `resolve`, `fetchConnectorsForBusiness`, and `addToBusinessIndex` (reused). The storefront path is untouched.
- `pkg/remote-config/src/index.ts` exports `ConnectorResolution`.
- Consumers: fapi (`^2.2.0`) and shopify-connector (pinned `2.2.0`, in shopify-connector and shopify-egress-service). Their plans are separate.
- No Fuse MCP data file. `shared-packages.json` lists versions, so that gets updated after publish.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- `handler(ConfigFragmentType.CONNECTOR)` is typed as the concrete `ConnectorBacklinkHandler`, so consumers get the new method with no cast (`remote-config.ts:54`). Established by source read.
- A failed connector never reached the business index before this change, because only `cacheConnectorWithIndices` writes it and that only runs on success. Established by source read.
- Cost: while a connector keeps failing, every business-level resolve for that business refetches from the config API. Accepted, because it is an error state the consumers will now record.

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

- [x] 1. `resolveWithUnresolved`, plus indexing of failed ids. 6 tests: a failed fetch is listed unresolved; resolved connectors come back beside it; nothing unresolved when all fetch; the failed id is added to the index; it shows as unresolved again on a cached read; `resolve()` returns only resolved connectors (AC 1, 2, 3). Verify: package suite, lint, build. — done: 5b532c9
- [x] 2. Merge #261 and confirm the publish (AC 4). Verify: the `Publish Packages` run is green and `npm view @gfs-bifrost/remote-config@2.3.0` resolves on GitHub Packages. — done: 6776d65

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-02 [inc 2] #261 merged; `Publish Packages` run 37029239553 succeeded (job `Remote Config / Publish`); GitHub Packages now lists `2.3.0` as the latest `@gfs-bifrost/remote-config` version (AC 4).
- 2026-10-02 [inc 1] `pnpm --filter @gfs-bifrost/remote-config`: `pretest`, then vitest 6 files / 113 tests, all passing, including the 6 new tests in `connector-backlink.handler.spec.ts`. `biome check` exit 0, `tsc` build clean.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- Behaviour against a live config-service with a connector the schema rejects. Proven downstream by the consumer plans' dev e2e.

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
