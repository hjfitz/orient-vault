---
ticket: none
title: Publish feature flag revisions
service: config-service
status: complete
created: '2026-10-14'
updated: '2026-10-14'
repo: /home/hjf/code/fuse/config-service
worktree: /home/hjf/code/fuse/config-service/.claude/worktrees/feature-flag-revision-publish
branch: hjf/feature-flag-revision-publish
base: origin/main
base_sha: 815b0e54e
pr: '243'
tags:
- waypoint
- plan
impl_model: sonnet
impl_effort: medium
---
# none — Publish feature flag revisions

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
After every successful flag create, update or delete, config-service publishes a `BifrostMessage<FeatureFlagRevision>` (`{key, change, version?}`) to `bifrost.{env}.feature_flag_revision.v1`, so remote-config readers refetch without waiting for their TTL. The publish is best-effort like G1 and never fails the HTTP write. It is bounded by a timeout and counted on its own metrics, `fuse.feature_flag.published` and `fuse.feature_flag.publish_failed`, not `REVISION_PUBLISH_FAILED`. Out-of-ticket, quiet (Harry, 2026-10-14). Siblings: [[feature-flag-revision-topic]], [[feature-flag-delivery-revision-contract-and-remo]], [[runtime-flag-for-the-per-connector-shopify-api-c]].

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. In dev, POST, PATCH and DELETE of `hjf.probe` each put exactly one message on the topic: created v1, updated v2, then deleted with no version. Each has `metadata.customer:"system"` and `source:"config-service"`. A 409 or a 400 publishes nothing. Read with a throwaway pull subscription.
- [x] 2. A failed or hung publish still returns the write's normal status within the timeout. It emits `publish_failed{operation}` and a `PublishFailed` log, and not `REVISION_PUBLISH_FAILED`.
- [x] 3. Customer-config routes and the `config_revision` publish are unchanged.
- [x] 4. In prod, the service runs with `FEATURE_FLAG_REVISION_TOPIC_NAME` set, and its SA has `roles/pubsub.publisher` on the prod topic.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- Code:
  - `code/src/core/pubsub/feature-flag.dispatcher.ts` (new, `FeatureFlagEventDispatcher.dispatchChange`, on `PubsubHandler`, with a timeout);
  - `core/pubsub/types.ts` interface;
  - `core/feature-flags/feature-flags.service.ts` (dispatch after the `FeatureFlagEvent.Changed` log in create, update and delete; delete logs inline, not via `logChange`);
  - `bootstrap/containers/feature-flags.module.ts` wiring;
  - `observability/events/feature-flag.type.ts` (`PublishFailed`);
  - `config/env.ts` (required `FEATURE_FLAG_REVISION_TOPIC_NAME`).
- Test and CI env: `code/.env.test`, `code/.env.development`, `.github/workflows/integration-tests.yaml` (lines 18 and 76).
- IaC: `iac/projects/config-service/remote.tf` (`core_pubsub` output), `iam.tf` (`google_pubsub_topic_iam_member.cloudrun_feature_flag_revision_push`), `cloud-run.tf` env.
- Deps: types ^10.15.0, observability ^2.3.0, with `minimumReleaseAgeExclude` entries.
- Docs: CLAUDE.md (the publishing section, "flag writes publish nothing", the env table); `manual-deploy.yaml` gets `notify_on_*` (an opportunistic backfill per CLAUDE.md). fuse-mcp `pubsub-topology.json` and `config-domain.json`, straight to master with `make parity-accept`.
- Guardrails: G1 (best-effort publish; deletes don't reuse `-1`); G3 (no new exception type); the `$`-pipeline gotcha doesn't apply (no writes change).

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- **The publish is awaited, with a timeout.** config-service runs with `cpu-throttling=true`, so fire-and-forget could stall after the response, while an unbounded await on Pub/Sub's retry window could hold the write for minutes. A 3 s bound like audit's publisher: on timeout, count `publish_failed` and return. Source: factual and structure reviews.
- **Infra and code in one PR.** The topic env var is required at boot, and both land in the same terragrunt apply, so it's never required before it's set. Source: structure review.
- **No `version` attribute on any log.** Datadog treats `version` as the reserved service-version tag (#242). Use `flagVersion`. Source: history review.
- **Merging ships all of main.** Before approving prod, review `git log <prod>..<run>` and cancel only older parked runs. 35326288564 is stuck and harmless. A manual deploy of the branch applies dev Terraform, and a later manual deploy of #206 off main would drop the new IAM grant in dev. Source: history review.
- **Renovate #238 is redundant** (main is already on types ^10.14.0); close it. Source: factual review.
- **The RootModule controller specs need `.overrideProvider(FeatureFlagEventDispatcher)`**, or a real PubSub would try ADC in CI. Source: draft.
- **Gates:** the topic must exist in dev and prod first, because the prod plan reads `core_pubsub`; types 10.15.0 and observability 2.3.0 must be published.

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
                     [x] confirmed
-->

- [x] 1. **Publisher, infra and code (one PR, branch `hjf/feature-flag-revision-publish`).** (AC 1,2,3) — see Verification — done: de3e3c0
  - gate: `feature_flag_revision` topic applied in dev and prod ([[feature-flag-revision-topic]])
        [x] confirmed
  - gate: types 10.15.0 and observability 2.3.0 published ([[feature-flag-delivery-revision-contract-and-remo]] inc 1)
        [x] confirmed
  — verify:
  - dispatcher specs, one behaviour each: publishes the revision to the topic; emits `PUBLISHED` on success; a rejected publish resolves; emits `PUBLISH_FAILED` with `operation`; logs `PublishFailed`; a publish that never settles resolves after the timeout;
  - service integration: one dispatch per successful create; per update; per delete, with the exact payloads; none for a duplicate 409, a stale-version 409, a 404 or a 400;
  - controller: a PATCH still returns 200 when the dispatcher's publish rejects;
  - full unit and integration suites;
  - dev, after a manual deploy:
    - IAM policy and env describe;
    - a throwaway subscription created before writing, then POST, PATCH, a stale PATCH (409) and DELETE `hjf.probe`;
    - the pull returns exactly 3 messages;
    - `sum:fuse.feature_flag.published{service:config-service,environment:dev} by {operation}` reads 1/1/1, with no `publish_failed`;
    - delete the subscription.
- [x] 2. **Prod.** Merge, review `git log <prod>..<run>`, approve, and cancel older parked runs. (AC 4) — see Verification — done: de3e3c0
  — verify:
  - the live image is the merge sha;
  - `gcloud run services describe config-service-prod` env has the topic;
  - the prod topic IAM policy lists `config-service-prod@`;
  - `publish_failed{environment:prod}` is empty;
  - fuse-mcp data is pushed, and `lookup-topic feature_flag_revision` resolves on the hosted server.

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-14 [inc 2] (AC 4) **Prod.** #243 merged as de3e3c0. The prod range from 815b0e5 was #238 (Renovate deps) and #243.
  - The prod plan showed the image, a new `+ env` on the main container, the new `cloudrun_feature_flag_revision_push` publisher member, and the known `pubsub_invoker` flip-flop drift. No destroys.
  - Deploy 38597952541 approved; all jobs green. The older #238 run 38597362420 was cancelled; only the stuck 35326288564 remains.
  - `config-service-prod` is on `prod-de3e3c0`, with `FEATURE_FLAG_REVISION_TOPIC_NAME=bifrost.prod.feature_flag_revision.v1`, and the topic IAM lists `config-service-prod@` as publisher.
  - No prod write was made to probe it, because the dev probe covers the code path.
- 2026-10-14 [inc 1] (AC 1,2,3) **Dev, live.** Branch manual-deployed (run 38596855050, image `dev-e7ef138`); the env var and topic IAM are present.
  - With throwaway subscription `hjf-ff-probe` created before writing, I sent POST, PATCH, a stale PATCH (409) and DELETE `hjf.probe`. The subscription got exactly 3 messages: `{created, v1}`, `{updated, v2}`, `{deleted}` with no version, each with `metadata.customer:"system"` and `source:"config-service"` and no attributes.
  - Datadog `fuse.feature_flag.published{environment:dev} by {operation}` reads created 1, updated 1, deleted 1, with no `publish_failed`. The subscription was deleted afterwards.
  - Unit: 700/700, including 7 dispatcher specs. Integration: 420 passed / 15 skipped, including 8 dispatch cases. The 17 write-route specs run through an always-rejecting publisher and keep their normal statuses (AC 2,3).

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- **The prod publish on a real write.** It is proven in dev with the same code, and the first real prod flag write will show `fuse.feature_flag.published{environment:prod}`.

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
