---
ticket: none
title: 'Runtime feature flags: first adopter (bulk-ingest allowlist)'
service: shopify-connector
status: abandoned
created: '2026-10-14'
updated: '2026-10-14'
repo: /home/hjf/code/fuse/shopify-connector
worktree: not created — phase 2, adopter undecided
branch: not created — phase 2, adopter undecided
base: origin/main
base_sha: not stamped — set when the worktree is created
pr: null
tags:
- waypoint
- plan
impl_model: opus
impl_effort: high
reason: 'Harry, 2026-10-14: fuse-ui is the first adopter, and customer targeting is
  deferred to a later iteration. The bulk-ingest allowlist is per-business targeting,
  and it sits on the ingest path during peak. The adopter work is now fuse-ui inc
  4 and 5 in runtime-feature-flags-audited-flag-page. Revisit bulk-ingest once targeting
  ships.'
---
# none — Runtime feature flags: first adopter (bulk-ingest allowlist)

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
Phase 2 of runtime feature flags (workshop action L3, no ticket yet): the first service to read a runtime flag in prod.

The candidate is `shopify-connector.bulk-ingest`, which adds businesses to the Shopify bulk-ingest lane without a deploy. The env vars stay as a hard ceiling, so the flag can never remove PURDYFIGG from bulk.

This waits until after the Purdy & Figg sale (7–8 Nov) and the peak freeze lift, and the choice of adopter is still open. The mechanism plans are [[runtime-feature-flags-types-featureflagschema-an]], [[runtime-feature-flags-feature-flags-store-and-ap]] and [[runtime-feature-flags-audited-flag-page]].

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [ ] 1. If the dev flag is absent or invalid, or config-service is unreachable, the bulk lane behaves exactly as the env vars say: PURDYFIGG stays on bulk and `bulkExcludedCount: 1` continues. A `feature_flag.fallback` metric records the reason.
- [ ] 2. In dev, adding a business to the flag's `businessIds` moves it onto the bulk lane within 30 s plus one poll cycle, with no deploy and the Cloud Run revision unchanged. Removing it moves it back. The flag never takes PURDYFIGG off bulk.
- [ ] 3. Preview envs never run bulk ops, whatever the dev flag says.
- [ ] 4. In prod after rollout, `tick.connectors` stays at its pre-deploy value and `feature_flag.fallback` stays at 0 for 24 h.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- The gate itself:
  - `apps/shopify-connector/src/providers/connector/connector-config.provider.ts:97-120` (`getBulkEnabledBusinessIds`, `listBulkEnabled`) and the interface in `providers/connector/types.ts:74`;
  - its callers: `core/shopify/use-cases/shopify-sales-order.service.ts` (`preview` at :137-139, `collect` at :172-173), and `core/bulk/tick/bulk-ingest-tick.ts:61`, which reaches it through `listBulkEnabled`.
- `adapters/config/remote-config.module.ts`, and the env schema in `config.schema.ts:30-38`.
- `iac/shopify-connector/env/feature-branch.tfvars`, the preview isolation.
- Cross-repo: an observability `feature_flag.fallback` monitor, and fuse-mcp `service-dependencies.json`.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- **The flag can only add, never remove.** The gate is `TICK_ENABLED && (envAllowlist ∪ flag.businessIds)`.
  - Taking PURDYFIGG off bulk sends it to the metered poll, which tops out at about 1,700 orders/h.
  - The projected peak hour is about 4,360–9,900 orders.
  - The poll has no watermark, so a backlog older than the 3 h window is lost with nothing to show for it.
  - Source: history review (`Bifrost/Purdy & Figg Testing/Overview.md`, `Tasks/2026-10-09-peak-day-snap-load-test.md`, shopify known-context #r1-permanent-order-loss).
- **Nothing detects a business on the wrong lane.**
  - There is no ingest-window monitor.
  - A bulk op that finishes with `objectCount:0` emits no metric.
  - Workshop action S18 (hourly ingest monitoring) is the dependency.
  - Source: history review.
- **Previews must stay off bulk.** Preview envs read dev config-service. A dev flag would override `feature-branch.tfvars`'s empty allowlist, and a `targets: null` flag would turn bulk on for every business. Keep `bulk_ingest_tick_enabled = false` there as the hard ceiling. Source: history review.
- **The tick assumes one bulk connector per shop** (shopify-connector#332). A runtime allowlist skips the deploy-time review of that assumption. Escentric already has two connectors on one store. Source: history review.
- **The debug log can't be prod evidence.** `PollEvent.BulkConnectorsExcluded` is a debug event, which works in dev (`log_level = debug`) but is invisible in prod (`info`). Prod proof is `tick.connectors`. Source: factual and structure reviews.
- **The version bump redeploys all three apps.** shopify pins `@gfs-bifrost/*` exactly, and the 2.4.0 bump changes the root lockfile, so all three shopify apps redeploy. Source: structure review.
- **Lanes can stay split during a config-service outage.** Warm instances keep the last-known value, while cold ones (scale-out during a sale) use env. Once the flag differs from env, lanes stay split for the length of the outage. Source: history review.
- **Check for duplicate PRs before opening.** Re-check `gh pr list` first: bulk-area work has been duplicated twice, and "bulk-tick smoothing" is owed before peak. Source: history review.
- UNRESOLVED: is this the right first adopter? An adopter off the ingest path would be lower risk.
- UNRESOLVED: when a business switches lanes mid-window, what happens? Duplicates are held by dedupe. Misses would be a watermark gap.

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

- [ ] 1. **Wiring.**
  - Bump to remote-config 2.4.0 and types 10.14.0, through Renovate or in-branch.
  - Expose `FeatureFlags` from `RemoteConfigModule` (`ttlMs` 30 000, `fetchTimeoutMs` 1 000).
  - Wire `onFallback` to a catalogued `feature_flag.fallback{key,reason}` metric.

  (AC 1)

  — verify:
  - a module spec: `FeatureFlags` resolves;
  - a fallback spec: the metric is emitted with a reason tag.

      gate: `@gfs-bifrost/remote-config@2.4.0` published
            [ ] confirmed
- [ ] 2. **Add-only gate.**
  - The bulk set becomes `envAllowlist ∪ flag.businessIds`, behind `TICK_ENABLED`, through `listBulkEnabled`, `preview()` and `collect()`.
  - Set `bulk_ingest_tick_enabled = false` in `feature-branch.tfvars`.

  (AC 1,2,3)

  — verify:
  - provider specs:
    - flag absent → env set;
    - flag `[X]` → env ∪ {X};
    - flag `enabled: false` → env set (never empty);
    - `TICK_ENABLED` false → nobody, whatever the flag says;
    - API down → env set.
  - a dev soak with a throwaway business:
    - adding it changes the `BulkConnectorsExcluded` count, and the tick lists it within 30 s plus one poll;
    - removing it reverts both;
    - deleting the flag gives env behaviour plus the fallback metric.
  - open the PR as a draft marked "do not merge until phase-2 gates".

      gate: adopter confirmed
            [ ] confirmed
      gate: phase 1 live in dev (config-service routes, fuse-ui page) and the dev flag created through dev fuse-ui
            [ ] confirmed
- [ ] 3. **Prod.**
  - Create the prod flag matching env, with no additions.
  - Merge, and approve only after `git log prod..sha`.
  - Add the observability `feature_flag.fallback` monitor (cross-repo).
  - Update fuse-mcp `service-dependencies.json`.

  (AC 4)

  — verify: `tick.connectors` unchanged and fallback 0 over 24 h.

      gate: Purdy & Figg sale complete and peak freeze lifted
            [ ] confirmed
      gate: S18 hourly ingest monitoring live
            [ ] confirmed
      gate: phase 1 in prod (config-service routes and fuse-ui page)
            [ ] confirmed

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- (planning only — nothing run yet)

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-10-14** — Harry, 2026-10-14, after reviewing the Claude Design mock (~/ff.png): per-customer targeting (Who gets it: Selected customers / Tier) moves to a later iteration, and scheduled changes ('when') are in the first iteration. The bulk-ingest allowlist is per-business targeting, so it no longer fits the first iteration. The design is framed around fuse-ui features (FUSE-1263, FUSE-1264 and others), which makes fuse-ui the likelier first adopter. Pending Harry's confirmation.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
- **The ledger's 500 claim belongs to fapi, not here.** The 2026-09-24 ledger entry (#282) says shopify's config-event handler "500s and redelivers". Source contradicts it: `ConfigRevisionExceptionFilter` catches every `Error` and returns 202. The claim is true for fapi only.
- **The 30 s TTL in known-context isn't the config cache.** known-context's "config LRU's 30s TTL" is actually the `ShopifyStoreApi` per-shop LRU. remote-config's LRU defaults to 60 s.
- **Correction 19 in Migration State is stale.** It says the prod bulk tick is off, but it has been on since 08-28 (prod tfvars `true` / `PURDYFIGG`).
