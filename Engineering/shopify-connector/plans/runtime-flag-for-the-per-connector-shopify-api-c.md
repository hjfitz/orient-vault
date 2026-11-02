---
ticket: none
title: Runtime flag for the per-connector Shopify API cache
service: shopify-connector
status: complete
created: '2026-10-14'
updated: '2026-10-14'
repo: /home/hjf/code/fuse/shopify-connector
worktree: /home/hjf/code/fuse/shopify-connector/.claude/worktrees/runtime-flag-cache-per-connector
branch: hjf/shopify-runtime-flag-cache-per-connector
base: origin/main
base_sha: 9bf307b24
pr: '335'
tags:
- waypoint
- plan
impl_model: sonnet
impl_effort: high
---
# none — Runtime flag for the per-connector Shopify API cache

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
> SUPERSEDED 2026-10-14 (Harry). Three changes:
> - **No env-var fallback.** An unresolvable flag (no snapshot, key missing or invalid) is **false**, and #332's `SHOPIFY_API_CACHE_PER_CONNECTOR` is replaced, not kept as a default.
> - **The reader is not local.** It lives in `@gfs-bifrost/remote-config`, and config-service pushes flag-change events on a dedicated topic with its own publish-failure metric.
> - **The mechanism ships first** (types, bifrost-pubsub, config-service, remote-config). This plan becomes the **adopter** step afterwards, and its increments are rewritten once those plans exist.
>
> The text below is kept as the record of the local-reader draft.

shopify-connector reads the runtime flag `shopify-connector.api-cache-per-connector` from config-service, so #332's per-connector `ShopifyStoreApi` cache (which lets two connectors share one Shopify store) can be switched on in prod without a deploy. `SHOPIFY_API_CACHE_PER_CONNECTOR` stays as the code default whenever the flag is absent, invalid or unreachable, the same contract as fuse-ui's `isFeatureEnabled`. Done when, in dev, creating and flipping the flag changes the cache key with no redeploy, and with config-service unreachable the behaviour equals the env var and a fallback metric fires.

**Quiet work.** Out-of-ticket under workshop action L3: no Slack, no Jira (FUSE-1313 is untouched), no product changelog. Harry, 2026-10-14: "we need to be quiet about this, as we said it would take a few weeks". Mechanism plans: [[runtime-feature-flags-types-featureflagschema-an]], [[runtime-feature-flags-feature-flags-store-and-ap]], [[runtime-feature-flags-audited-flag-page]].

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. **Flag absent → env behaviour.** With no flag in dev, the factory keys as the env var says, and `fuse.feature_flag.fallback{reason:unknown_key}` is emitted.
- [x] 2. **A flip applies without a deploy.** In dev, with the Cloud Run revision unchanged, setting the flag `enabled:false` makes the two `escentric-sandbox.myshopify.com` connectors (ESCENTRIC UK `conn_ecb5…`, ESCENTRICPL) collapse onto one instance: one `connectorId` appears twice in `Shopify order collection started` and the other not at all, with `fuse.api.factory.cache.miss{keymode:shop}`. Setting it `true` gives both connectors, with `keymode:connector`.
- [x] 3. **config-service unreachable never fails a request.** Before any snapshot exists, the reader answers with the env default (`reason:unavailable`). After a failed refresh it keeps the last good snapshot. A refresh never rejects, so the poll's throw-for-redelivery semantics are unchanged.
- [x] 4. **A cold instance doesn't serve its first request on the default.** Boot waits for one refresh, capped at 1 s, and `fuse.feature_flag.refresh{outcome:succeeded}` is emitted at instance start in dev.
- [x] 5. **The predicate applies on every route that builds a store API**, not only the poll. A confirmation for ESCENTRICPL (via `mock-send`) emits `fuse.api.factory.cache.*` with the expected `keymode`.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- **New, local to the app:** `apps/shopify-connector/src/adapters/config/`
  - `feature-flag-api.client.ts`: global `fetch` with `AbortSignal.timeout(1000)`;
  - `feature-flag.reader.ts`;
  - `constants.ts`;
  - additions to `token.ts` / `types.ts` / `__fixture__/`;
  - registration in `RemoteConfigModule.forRoot()` (`@Global`, already the config-service boundary). No new directory or module.
- **Factory:** `src/adapters/shopify/api/api.factory.ts` (#332's `cacheByConnector` boolean becomes a per-call predicate, and the hit/miss metrics gain a `key_mode` tag), wired in `src/modules/shopify/shopify.module.ts`.
- **Observability:** new `src/providers/observability/catalog/feature-flag-metric.type.ts` and `feature-flag-event.type.ts`, re-exported from `catalog/index.ts`. Metrics emit as `fuse.<name>`, and Datadog lowercases tag keys.
- **Contract read:** config-service `GET {CONFIG_API_BASE_URL}/feature-flags`. `CONFIG_API_BASE_URL` already ends in `/api/v1`, and the existing `CONFIG_API_KEY` works. Evaluated with types' `evaluateFeatureFlag(flag, now, {businessId, connectorId})`. No new env var or IaC.
- **Docs:** CLAUDE.md's #332 paragraph, plus the stale metric lines at 501–504 (the `shopify_connector.*` prefix, the `METRIC` map), and `.env.example`.
- **fuse-mcp:** `service-dependencies.json` (shopify-connector → config-service purpose text) and `config-domain.json` `featureFlags` readers.
- **Guardrails:** G2 holds; `DEFAULT_TTL` (30 s) and `GRAPHQL_REQUEST_RETRIES` are untouched. G3 holds because the reader never throws. G5: CI red is cleared in its own PR off main, which #334 did on 2026-10-14.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- **A local reader rather than remote-config.**
  - remote-config 2.3.0's `ConfigApiClient` has no timeout and no flags method, and its `get` is private. Reusing it would mean a pkg-node release, which is the general FUSE-1313 work: slower and more visible.
  - This is a deliberate stopgap. FUSE-1313 later lifts the reader into remote-config and this one is deleted.
  - Source: factual review; Harry's "be quiet" instruction.
- **`fetch`, not axios.** On Node, axios `timeout` stops bounding the request once headers arrive, while `AbortSignal.timeout` bounds the whole thing. The characterization harness's undici `MockAgent` with `disableNetConnect` blocks `fetch`, so the reader falls back to the default there without a fourth harness override (`harness.ts:30`: "three overrides, deliberately no more"). Source: factual and history reviews.
- **After a failed refresh, keep the last good snapshot and retry after 5 s.** A config-service blip must not flip prod back to the shop-only key. This was already decided in FUSE-1313's technical notes and the pkg-node plan, so it isn't re-asked. Source: history review.
- **Boot waits for one refresh, capped at 1 s, and never throws.** With `minScale=0`, a new instance would otherwise serve its first confirmation or poll on the env default, and in prod that is the buggy shop-only key. This replaces the draft's pre-poll refresh in `collect()`, which also avoided a new core→adapters import (the open PORTS ADR in the rearchitecture programme). Source: structure review.
- **Warm-instance flip latency is up to about 2 polls (~10 min).** A read past the 30 s TTL returns the current answer and refreshes in the background, and polls are 5 min apart. That's acceptable for a planned rollout; it's documented, not fixed. Source: draft and structure review.
- **On a flip, old-key cache entries are orphaned.** The keys `uri` and `uri:connectorId` never collide, so old entries stay until the 100-entry LRU capacity or an instance restart pushes them out, and `api.factory.cache.size` stays inflated until then. There's no real "burst of misses": with a 30 s factory TTL against 5-min polls, nearly every poll misses already (Migration State R3). Source: factual and history reviews.
- **Preview envs read dev config-service, and their subscriptions sit on the shared dev topics.** A dev flip therefore changes live previews' confirmation, tag and stock paths. Flip briefly and say so. Source: draft.
- **No prod business shares a store today** (SAIRA and PURDYFIGG each have one; Escentric has no prod Shopify connector). The prod flag can ship off and be turned on when a shared-store tenant goes live. Source: history review against live config.
- **Dev doesn't have #332 yet.** Dev runs main `9bf307b2`, where the env var is absent and parses as false, so the "off" state is only visible after this branch is deployed. Source: history review.
- **ESCENTRICPL in dev also has a "Gadgets Test" Shopify connector** (no mappings), so count logs by `@connectorId`, not by business. Source: history review.
- **Stacking:** PR A branches off main and doesn't touch #332. PR B stacks on #332 (another session's branch): it only ever merges into it, and never rebases or force-pushes. Renovate #333 (types 10.14.0) merges first, then main is merged up. Source: structure review.
- UNRESOLVED (default taken): it ships to prod with the flag off, before or after the 1 Nov freeze? Default: the code goes in dark (no prod flag; env false, so behaviour is unchanged), and the prod flip waits for a shared-store tenant and Harry's call.

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

> SUPERSEDED 2026-10-14. The increments below replace the local-reader draft. That draft had three increments, now gone from this file: a local `FeatureFlagReader` in `adapters/config` (PR A, off main), the factory predicate (PR B, on #332) and a dark prod rollout. They were dropped when Harry moved the reader into remote-config; see Decisions & deviations, 2026-10-14. The mechanism is already live: topic [[feature-flag-revision-topic]], publisher [[publish-feature-flag-revisions]], reader [[feature-flag-delivery-revision-contract-and-remo]] (remote-config 2.4.0).

- [x] 1. **Adopt the reader (one PR, stacked on #332, with Renovate #333 and main merged in).** (AC 1,2,3,4,5) — see Verification — done: 59f919ba
  - **Deps:** connector `@gfs-bifrost/remote-config` 2.4.0, types 10.15.0, plus release-age excludes.
  - **Reader wiring** in `RemoteConfigModule`:
    - `.withFeatureFlags()`, and `await provider.featureFlags.ready()` in the factory (bounded at 1 s, never throws);
    - `onRefresh` feeds a local `feature_flag.refresh{trigger,outcome}` metric and a `Feature flag refresh failed` warn log (message and status only; no top-level `version`).
  - **Route:** `POST /events/feature-flags/revision`, behind `ApiKeyGuard`/OIDC with `ConfigRevisionExceptionFilter`. It always answers 202, decodes with `pubsubService.ingestEvent`, and calls `featureFlags.ingestEvent(record)`.
  - **IaC:**
    - `remote.tf` local `feature_flag_revision_topic_id`;
    - a push subscription `{project}.{env}.feature_flag_revision.v1.sub` in `pubsub.tf` (CRLF; OIDC `cloudrun_sa`, 20 s ack, no DLT).
  - **Factory:** `ShopifyApiFactory` takes `cacheByConnector: (config) => boolean`, wired to `featureFlags.isEnabled("shopify-connector.api-cache-per-connector", {businessId, connectorId})`. A `key_mode` tag goes on the hit and miss metrics.
  - **Clean-up:** #332's `SHOPIFY_API_CACHE_PER_CONNECTOR` is removed (schema, `.env.example`, tfvars, `cloud-run.tf`, `variables.tf`). An unresolvable flag is false, which is prod's behaviour today.
  - Docs: CLAUDE.md.

  — verify:
  - specs:
    - factory: a predicate flip switches the key with no new factory; the `key_mode` tag;
    - the route acks 202 and calls `ingestEvent` with the decoded record;
    - the route acks 202 on an undecodable push;
    - the module calls `ready()`;
    - an `onRefresh` failure emits the metric and log.
  - full suite, `build:check`, lint.
  - dev, after a manual deploy of this branch, with polls forced by `gcloud scheduler jobs run`:
    - no flag: one Escentric connector polled twice and the other not at all (`keymode:shop`);
    - POST the flag `enabled:true`: the push lands as `feature_flag.refresh{trigger:event}` within seconds, and the next poll has both `@connectorId`s (`keymode:connector`);
    - PATCH `enabled:false` collapses them again;
    - DELETE leaves them collapsed (unresolvable means false);
    - a `mock-send` confirmation for ESCENTRICPL emits the expected `keymode`.
  - Give dev back afterwards.
- [x] 2. **Prod (merge #332 and this one as one stack, then approve).** (AC 1) — see Verification — done: 59f919ba
  - Prod gets no flag, so the cache stays per shop, exactly as today.
  - Review the range `git log <prod>..<run>`: #331 (FUSE-1268, Done) and #334 ride along. Approve the connector gate only; egress's parked FUSE-1209 run is not ours.
  - fuse-mcp: shopify-connector as a subscriber of `feature_flag_revision`, the new route in `api-endpoints.json`, and the `service-dependencies.json` purpose.
  — verify:
  - the prod image is the merge sha;
  - `fuse.feature_flag.refresh{service:shopify-connector,environment:prod} by {outcome}` reads `succeeded` at boot;
  - the subscription exists in prod;
  - `api.factory.cache.miss{keymode:shop}` continues.

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-14 [inc 2] (AC 1) **Prod.** Stack #336 (#332 + #335) merged as 59f919b.
  - Prod range from e9aef9e: #331 (FUSE-1268, Done), #334, #333, #332, #335.
  - The prod plan was the image, `+ google_pubsub_subscription.feature_flag_revision`, and `sales_order_create_acknowledge` **replaced**. The replacement is FUSE-1268's filter change; at worst a missed `ILG_RECEIVED` tag in the seconds-long gap.
  - Deploy 38606864989 approved and green; the older run 38543846965 was cancelled.
  - `shopify-connector-prod-cr` is on `prod-59f919b`.
  - The subscription `shopify-connector.prod.feature_flag_revision.v1.sub` pushes to `/events/feature-flags/revision`. The `create_acknowledge` subscription has the FUSE-1268 filter.
  - `fuse.feature_flag.refresh{environment:prod}`: `ready:succeeded` 1, `stale:succeeded` 3, no failures.
  - `api.factory.cache.miss{environment:prod}` on the new build is all `key_mode:shop` (poll, confirmation, bulk_tick), so there's no prod flag and behaviour is unchanged.
  - Prod warn patterns after the deploy ("DDP rules unavailable", "more than one fulfillment order") match the 15:00–17:20 baseline.
  - fuse-mcp 22e93d2 adds shopify-connector as the `feature_flag_revision` subscriber and the purpose of the config-service dependency.
- 2026-10-14 [inc 1] (AC 1,2,3,4,5) **Dev, live.** Branch manual-deployed (run 38604078219, image `dev-976c6bd`). The new subscription pushes to `/events/feature-flags/revision`, and the service has no `SHOPIFY_API_CACHE_PER_CONNECTOR` env var.
  - No flag, poll at 17:13:15: PL `conn_cdc9…` collected twice, UK `conn_ecb5…` not at all, so unresolvable means false (AC 1).
  - POST the flag `enabled:true` at 17:14:51. `Feature flag revision received` at 17:14:54. Polls at 17:15:01 and 17:15:09 collected **both UK and PL**, with no deploy (AC 2).
  - PATCH `enabled:false` at 17:16:45, received the same second; the 17:17:01 poll was back to PL twice. Then PATCH `enabled:true` (v3), left on in dev.
  - `fuse.feature_flag.refresh{environment:dev}`: `ready`, `stale` and `event` all succeeded (AC 4). On escentric-sandbox, `api.factory.cache.miss` reads `key_mode:shop` before the flag and `key_mode:connector` after.
  - A broadcast `goods_out_confirmation` mock for ESCENTRICPL (with `broadcast: true`, because the subscription filters on `source=shopify OR broadcast`) gave `cache.miss{operation:confirmation, key_mode:connector}` (AC 5).
  - Specs 792/792. The characterization harness failed 5 tests until its config fake gained a `featureFlags` stub (false), because the factory predicate threw and the token probe never ran.
  - `build:check` and lint clean (only the pre-existing biome schema-version note).
  - #332's dev check is discharged by the same run.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- **The 5-minute config-service outage path (AC 3)** wasn't exercised live; it rests on remote-config's reader specs and the dev harness 401 run. The unresolvable-means-false path is proven live.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-10-14** — Harry: no env-var fallback, so an unresolvable flag is false. The reader moves into @gfs-bifrost/remote-config, with config-service publishing flag-change events on their own topic and metric. That mechanism ships before the shopify adoption. The local-reader draft is superseded; this plan is now the adopter step.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
(none: promoted 2026-10-14 to known-context#secops-nightly and to the architecture.md Shopify API resilience and Build sections)
