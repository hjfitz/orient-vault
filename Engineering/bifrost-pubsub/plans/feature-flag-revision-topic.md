---
ticket: none
title: Feature flag revision topic
service: bifrost-pubsub
status: complete
created: '2026-10-14'
updated: '2026-10-14'
repo: /home/hjf/code/fuse/bifrost-pubsub
worktree: /home/hjf/code/fuse/bifrost-pubsub/.claude/worktrees/feature-flag-revision-topic
branch: hjf/feature-flag-revision-topic
base: origin/master
base_sha: c23d5c343
pr: '17'
tags:
- waypoint
- plan
impl_model: sonnet
impl_effort: low
---
# none — Feature flag revision topic

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
Add `bifrost.{env}.feature_flag_revision.v1` (plus its automatic `.dlt`) next to `config_revision`, with outputs mirroring `config_revision_topic_*`. config-service publishes a refetch signal on it after every flag write, and remote-config readers consume it. This is phase 2 of runtime feature flags (workshop action L3, out-of-ticket and quiet). Done when the topic and its DLT exist in dev and prod and the remote-state outputs resolve. Siblings: [[publish-feature-flag-revisions]], [[feature-flag-delivery-revision-contract-and-remo]], [[runtime-flag-for-the-per-connector-shopify-api-c]].

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. `bifrost.dev.feature_flag_revision.v1` and `.v1.dlt` exist in `bifrost-dev-global1`, and the same pair exists in `bifrost-prod-global1`.
- [x] 2. The outputs `feature_flag_revision_topic_name` / `_id` / `_dlt_name` / `_dlt_id` are readable through `core_pubsub` remote state in both envs, because config-service's prod plan depends on them.
- [x] 3. The dev and prod plans are add-only (`2 to add, 0 to change, 0 to destroy`).

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `iac/projects/bifrost-pubsub/config.pubsub.tf` (module `feature_flag_revision`) and `config.outputs.tf`. A README row in the Configuration table.
- The consumer of these outputs is config-service `iac/projects/config-service/remote.tf`. Publisher IAM lives in the publisher's repo, not here.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- **Both `terraform-dev` and `terraform-prod` are gated** (`required_reviewers`). `tf-plan-pr` plans dev only, so read the prod plan from the Deploy run's log before approving. Source: factual and history reviews; memory bifrost-pubsub-deploy-gates.
- **An older parked run approved late would destroy the topic.** Approve only the run whose head sha is this merge, and cancel only older runs. Source: history review.
- **The `bifrost` domain, not a new one.** Flags belong to the Bifrost config plane; audit has its own domain because it's used outside Bifrost. Source: draft.
- **Harry's instruction:** do it all autonomously and get to prod. The Terraform plan is reviewed by the agent as add-only and quoted in the report, and the usual plan-share pause is waived for this run.

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

- [x] 1. **Topic and outputs.** Add the module, the four outputs and the README row. Open a PR, check the `tf-plan-pr` comment, merge, and approve dev then prod after reading each plan. (AC 1,2,3) — applied dev+prod; 4 topics described — done: eaf32b1
  — verify:
  - the PR plan comment and the Deploy run's dev and prod plan logs each say `Plan: 2 to add, 0 to change, 0 to destroy`;
  - `gcloud pubsub topics describe bifrost.{dev,prod}.feature_flag_revision.v1` (and `.dlt`) in each project;
  - no older parked Deploy run is left approvable.

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-14 [inc 1] (AC 1,2,3) **#17 merged as eaf32b1.**
  - The PR plan comment (dev), and the Deploy run 38595302193 dev and prod plan logs, each read `Plan: 2 to add, 0 to change, 0 to destroy`: `google_pubsub_topic.default` and `.dlt`, plus the 4 outputs.
  - Approved `terraform-prod`, then `terraform-dev`, and all 4 jobs succeeded.
  - `gcloud pubsub topics describe` resolves `bifrost.{dev,prod}.feature_flag_revision.v1` and `.v1.dlt` in `bifrost-{dev,prod}-global1`.
  - No other Deploy run was parked. The prior run c23d5c3 had completed.
  - AC 2, the remote-state outputs, is also proven by config-service's plan reading `core_pubsub` (see [[publish-feature-flag-revisions]]).

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- (none). AC 2 is read by config-service's own plan.

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
(none — the PR-flow correction went into memory `project_bifrost_pubsub_deploy_gates`)
