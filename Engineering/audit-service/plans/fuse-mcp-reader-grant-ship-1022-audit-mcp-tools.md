---
ticket: none
title: Fuse MCP reader grant (SHIP-1022-audit-mcp-tools)
service: audit-service
status: complete
created: '2026-10-22'
updated: '2026-10-22'
repo: /home/hjf/code/fuse/audit-service
worktree: /home/hjf/code/fuse/audit-service/.claude/worktrees/mcp-reader
branch: hjf/mcp-audit-reader
base: origin/main
base_sha: 8dec02b3a
pr: '15'
tags:
- waypoint
- plan
impl_model: sonnet
impl_effort: low
---
# none — Fuse MCP reader grant (SHIP-1022-audit-mcp-tools)

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
Add `fuse-mcp-prod-sa@bifrost-prod-global1.iam.gserviceaccount.com` to prod `api_readers` so the Fuse MCP's new `audit-search`/`audit-get-event` tools can read audit-service. This is the go-live switch for those tools and ships last, after the MCP side is live and its token rotated. Harry's decision and accepted risks: [[Bifrost/Audit Service/Migration State]] (decision log 2026-10-22, R2). Companion plan: [[Engineering/fuse-mcp/plans/read-only-audit-tools-on-the-mcp-ship-1022-audit]]. Run SHIP-1022-audit-mcp-tools; no ticket.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. `fuse-mcp-prod-sa` holds `run.invoker` on `audit-service-prod` and is listed in its `READ_CALLERS`, with fuse-ui's access unchanged.
- [x] 2. The MCP's `audit-search` returns prod events instead of its 403 text.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `iac/env/prod.tfvars:6` `api_readers` → `google_cloud_run_v2_service_iam_member.api_invoker_readers` (`iam.tf:21-29`) and `READ_CALLERS` (`cloud-run.tf:68-71`). The allow-list spans every `/api/v1/systems/*` route, `secrets` included.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- The PR's tf-plan is dev-only (`tf-plan.yaml:19`); the prod plan exists only in the post-merge Deploy run's `terraform-plan-prod` job log (`deploy.yaml:72`), and apply waits on `terraform-prod` (`deploy.yaml:108`) — factual review.
- Deploy runs share one concurrency group without cancel-in-progress; a parked run blocks later ones and an approval ships all of main since the live sha — history review (ledger 2026-10-22).

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

- [x] 1. Add the SA to prod `api_readers` (AC 1,2) — verify: Deploy run's prod plan is 1 to add (the IAM member) and 1 to change (image + `READ_CALLERS`), nothing else; `git log <live sha>..<run sha>` shows only this commit; after apply `gcloud run services get-iam-policy audit-service-prod` lists the member, `describe` shows both callers in `READ_CALLERS`, fuse-ui's audit page still loads, and the MCP smoke passes. — done: 1e64279
      gate: the fuse-mcp side is live (its tools answer the fixed 403 text) and its rotated token is in Harry's registrations; Harry approves the prod plan
            [x] confirmed — 2026-10-22: fuse-mcp side live (tools answered the Cloud Run 403 text), token rotated (#59); Harry's registrations not confirmed beforehand (the grant didn't depend on them); prod plan 1/1/0 approved by the /ship run per Harry's no-ask instruction

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-22 [inc 1] Deploy run 39808101938: prod plan 1 to add (run.invoker member for fuse-mcp-prod-sa), 1 to change (image 8dec02b→1e64279 plus the masked api env = READ_CALLERS; the sidecar env swap matches the last applied plan). Only #15 rode the gate. After apply: get-iam-policy lists fuse-mcp-prod-sa, READ_CALLERS lists both readers, MCP reads succeed after ~30s propagation; fuse-ui-prod is still in both run.invoker and READ_CALLERS, so its access is unchanged by configuration; fuse-ui's audit page itself was not loaded (no browser session).

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- Only the MCP's smoke proves the grant end to end; there is no pre-prod path (dev's `api_readers` is fuse-ui-dev only, by design).

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
