---
ticket: none
title: Record connectors remote-config couldn't resolve
service: fapi
status: complete
created: '2026-10-02'
updated: '2026-10-05'
repo: /home/hjf/code/fuse/fapi
worktree: /home/hjf/code/fuse/fapi/.claude/worktrees/e8-unresolved-legs
branch: hjf/e8-unresolved-connector-legs
base: origin/master
base_sha: 35b2e891d
pr: '166'
tags:
- waypoint
- plan
programme: poller-clear-down
unit: E8
impl_model: opus
impl_effort: high
---
# none — Record connectors remote-config couldn't resolve

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
Part of [[Poller Clear-Down/Migration State|Poller Clear-Down]] unit **E8** (no ticket; Harry 2026-10-02: autonomous, no code review). On remote-config 2.3.0's `resolveWithUnresolved`, a fan-out records one retryable failure per REST connector remote-config couldn't load, so the connector is no longer silently missed. A routed confirmation whose connector couldn't be loaded becomes retryable too. Depends on [[remote-config-reports-unresolved-connectors]] (pkg-node).

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. On a fan-out, each unresolved REST connector gets a failure with its `connectorId` on the body and the envelope. The failure is a `dependency` on `config_service`, `code: fapi.connector_unresolved`, `retryable: true`.
- [x] 2. Resolved connectors beside an unresolved one are still delivered, and `made` is still published when one delivers.
- [x] 3. A routed confirmation whose `connectorId` is unresolved records that retryable failure and attempts no delivery.
- [x] 4. Normal fan-out and routed delivery are unchanged, in dev and in prod.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `code/src/adapters/config/config-api.adapter.ts` gains `getConnectorResolutionByBusinessId`.
- `code/src/services/connector-registry.service.ts` gains `getResolutionByBusinessId`.
- `code/src/services/confirmation.service.ts`: `routeConfirmations` (routed) and `fanOutConfirmations`.
- Dependency: `@gfs-bifrost/remote-config` `^2.3.0`.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- An unresolved REST connector's webhook state is unknown, so it's always recorded: failure is preferred over silent loss. A design decision.
- No unresolved connector exists in any environment's logs over 14 days, so the live path is unit-proven only. Established with a Datadog search.

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

- [x] 1. Resolution through the adapter and registry; unresolved fan-out legs; retryable routed failure. 13 tests (AC 1, 2, 3). Verify: suite, lint, `build:check`, then a dev smoke. — done: 66c7a4d
- [x] 2. Merge, then a prod release behind `terraform-prod` with the plan shared (AC 4). Verify: `api-gateway-prod` on the merge sha; no new errors. — done: 66c7a4d
      gate: prod Terraform plan shared with Harry before approval
            [x] confirmed

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-05 [inc 2] Prod release (AC 4). Rechecked 3 days after merge: main still at the merge sha, prod unchanged, plan still 1 in-place change; Harry agreed it 2026-10-02. Approved `terraform-prod`. Now api-gateway-prod on prod-66c7a4d (Deploy 37033568929 + Developer Portal 37033569045), Ready. No prod `status:error` logs since 08:05Z.
- 2026-10-02 [inc 1] Dev smoke on branch `d54128a` (manual deploy 37030166717, announced; reverted to master by 37032470560): a routed HJF pick (correlationId `40143359…`) went through the new resolution path, was delivered to `conn_1a5c…` (failing), had its failure recorded against that connector, and was acked. Full suite 420/420, lint exit 0, `build:check` clean. Merged as fapi#166 `66c7a4d`.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- An actually unresolved connector, live. No case exists to drive it; unit tests cover it.

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
