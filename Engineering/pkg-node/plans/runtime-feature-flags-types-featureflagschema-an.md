---
ticket: none
title: 'Runtime feature flags: FeatureFlagSchema, scheduled changes and the evaluation
  rule (types 10.14.0)'
service: pkg-node
status: complete
created: '2026-10-14'
updated: '2026-10-14'
repo: /home/hjf/code/fuse/pkg-node
worktree: /home/hjf/code/fuse/pkg-node/.claude/worktrees/runtime-feature-flags
branch: hjf/runtime-feature-flags
base: origin/main
base_sha: bb1c21967
pr: '271'
tags:
- waypoint
- plan
impl_model: opus
impl_effort: high
---
# none — Runtime feature flags: FeatureFlagSchema, scheduled changes and the evaluation rule (types 10.14.0)

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
Runtime feature flags for Fuse, phase 1 of 2. This is workshop action L3, "change process and feature flags", from Jack Bailey's Integrations Path Forward workshop; there is no ticket yet.

> SUPERSEDED 2026-10-14. Harry made fuse-ui the first adopter. fuse-ui reads config-service's API directly, with no local cache, so the remote-config snapshot below moves to a follow-up ticket for the event and caching approach. The ticket is not yet filed.
> This plan now owns the types contract only:
> - `FeatureFlagSchema`, including `scheduledChange` (scheduling is in v1; customer targeting stays in the shape, but a later iteration uses it).
> - The one evaluation rule, `resolveFeatureFlag` / `evaluateFeatureFlag`, which config-service and fuse-ui share.
>
> The bulk-ingest sibling is superseded by fuse-ui's adopter increments in [[runtime-feature-flags-audited-flag-page]].

Today a flag is a `FEATURE_FLAG_*` env var in tfvars. Turning one on in prod takes a PR plus a prod deploy, and that deploy ships everything on `main`. This plan owns the shared contract:
- `FeatureFlagSchema` in `@gfs-bifrost/types`.
- A flag snapshot in `@gfs-bifrost/remote-config`. Any service can evaluate it in-process with `isEnabled(key, ctx, default)`. It never rejects, and it sees a flip within a fixed time limit with no deploy.

This plan is the anchor for the shared design. The sibling plans:
- [[runtime-feature-flags-feature-flags-store-and-ap]]: config-service serves the flags.
- [[runtime-feature-flags-audited-flag-page]]: fuse-ui flips them, with each flip audited.
- [[runtime-feature-flags-first-adopter-bulk-ingest-]]: phase 2, the first reader in prod.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. `@gfs-bifrost/types` 10.14.0 exports `FeatureFlagSchema`, `FeatureFlagTargetsSchema`, `FEATURE_FLAG_KEY_PATTERN` and `FeatureFlag`. `ConfigFragmentSchema` is unchanged.
> SUPERSEDED 2026-10-14. AC 2–5 below covered the remote-config snapshot, which has moved to the event and caching follow-up. Their checkboxes were removed so sign-off doesn't gate on moved work. AC 6–8 replace them.

- 2. `isEnabled(key, ctx, default)` never rejects. It resolves to the caller's default in each of these cases:
  - the snapshot can't be loaded on a cold instance (API error, a response slower than `fetchTimeoutMs`);
  - the key is unknown;
  - the flag failed to parse.

  After a failed refresh it keeps the last-known value.
- 3. An evaluating instance sees a flip made in dev config-service within `ttlMs` (default 30 s) of the write, with no deploy.
- 4. A service built without `.withFeatureFlags()` makes no request to `/api/v1/feature-flags`. fapi and shopify-egress-service are unaffected by taking 2.4.0.
- 5. Adding, retiring or deleting a flag needs no types, remote-config or config-service release. The remote-config readme documents those steps as data-only.
- [x] 6. `FeatureFlag` carries `scheduledChange: { at, enabled } | null`. A flag scheduled to switch on at T evaluates off before T and on from T. `resolveFeatureFlag` folds a due change into `enabled` and clears it.
- [x] 7. `evaluateFeatureFlag(flag, now, context)` is the single rule: it resolves the schedule, then applies `targets`. It is exported from `@gfs-bifrost/types` for config-service and fuse-ui.
- [x] 8. remote-config is unchanged on this branch's net diff, and adding a flag needs no types or config-service release.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `pkg/types/src/config/schemas/feature-flag.schema.ts` (new), exported from `schemas/index.ts`. `config-fragment.schema.ts` is deliberately untouched: flags are not a `config_revision` fragment.
- `pkg/remote-config/src/feature-flags/` (new: evaluate, client, snapshot), plus `remote-config.ts` (builder), `index.ts`, `package.json` (2.4.0, peer `>=10.14.0`) and `readme.md`.
- `pkg-node/CLAUDE.md` package table: the types and remote-config rows. Its remote-config peer note says `>=6.1.0`, but the real floor is `>=10.13.0`.
- The org Package Changelog in `/home/hjf/code/CLAUDE.md`. That file isn't a git repo, so it's a checklist item with no sha.
- fuse-mcp `data/shared-packages.json` and `data/config-domain.json`, plus the `make parity-accept` baseline. These go straight to master.
- Consumer contract: config-service `GET /api/v1/feature-flags` returns `{ flags: FeatureFlag[] }` ([[runtime-feature-flags-feature-flags-store-and-ap]]).

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- **No Pub/Sub for flags in v1.**
  - A Pub/Sub push reaches one Cloud Run instance, so every other instance only sees a change when its own cache expires. The TTL is therefore the limit on propagation, whichever topic carries the event.
  - A TTL'd pull also serves services that don't use remote-config's cache (sftp-connector, snap-adapter, dedupe-service, wms-gateway), and it needs no subscription Terraform per adopter.
  - Source: wms-gateway `pubsub.tf:5-8`, remote-config `remote-config.ts:247-249`, cache `memory.cache.ts:23-26`; planning agent plus factual review.
- **The flag snapshot doesn't use remote-config's `CacheService` or Redis.**
  - The TTL there is builder-wide.
  - The Redis TTL is passed as ms (`PX`) but documented as seconds.
  - Consumers range from 604.8 s (fapi) to 7 days (shopify).
  - Source: `redis.cache.ts:259-267`, shopify `global.tfvars:27`, fapi `variables.tf:79-83`; factual review.
- **Refresh is lazy, during evaluation, not on a background timer.**
  - This works the same whatever a consumer's Cloud Run CPU setting is, and it adds no idle work.
  - shopify-connector runs with `cpu-throttling: false`, so a timer would work there. It was rejected for portability, not feasibility.
  - Source: factual review.
- **After a failed refresh the last-known value is kept forever.** Only a cold instance falls back to the code default. This matches config-service's documented blast radius, "cached config keeps serving". Source: history review, config-service known-context.
- **`owner` and `expiresAt` are required. `expiresAt` is informational only** and never changes evaluation. Source: default stated to Harry on 2026-10-14.
- **Evaluation rules:**
  - `enabled: false` → false.
  - `targets: null` → true.
  - Otherwise true when `businessId ∈ businessIds` OR `connectorId ∈ connectorIds`.
  - Empty arrays match nothing, and so does a missing ctx id.
  - `targets` is a strict object, so a flag carrying a targeting dimension the evaluator doesn't know fails to parse and evaluates to the caller's default.
  - Source: planning agent.
- **Defaults:** `ttlMs` 30 000, `fetchTimeoutMs` 1 000, backoff after a failed refresh 5 000. Each consumer can override them. Load is about instances / 30 s, so roughly 0.33 rps at shopify's maximum of 10 instances. Source: default taken; history review on load.
- **No Zod schema specs for the types change.** Evidence is `tsc`, dependent builds and the existing suite (standing preference). The strict-`targets` behaviour is proven where it is our own logic: the client skips an invalid item.
- **Version numbers are free today (2026-10-14):** types 10.13.0 → 10.14.0 and remote-config 2.3.0 → 2.4.0. The only open pkg-node PR is #201 (snap 0.4.0). Re-check before each merge. Source: factual review.
- **A types release opens a Renovate PR inside pkg-node** that raises remote-config's peer floor with no version bump (precedent: #267). Let that PR land, then bump remote-config to 2.4.0 on top of it. Source: pkg-node architecture, history review.
> SUPERSEDED 2026-10-14. The work went ahead out-of-ticket under L3. #271 was pushed as `hjf/runtime-feature-flags`.

- UNRESOLVED: a Jira ticket, or out-of-ticket under L3? Branches are `hjf/runtime-feature-flags` until this is answered, and can be renamed before the first push.
- **How scheduling works: the change lives on the flag, and readers evaluate it against the clock.**
  - config-service's GET serves the resolved state and writes nothing; a due change is folded into storage on the flag's next write.
  - It needs no scheduler job, and the flip happens at T even while config-service is down.
  - Source: Harry, 2026-10-14 ("yes to 1").
- UNRESOLVED: **which fields the v1 contract carries, given the design mock** (`~/ff.png`).
  - The design shows a display name, ticket, area, description, Read by, a caution note and flip notes, plus a Not ready → Ready lifecycle ("Engineering marks a flag ready").
  - It doesn't show `owner` or `expiresAt`.
  - Informational fields can be added later without risk, but that costs another types bump. Settle this before #271 merges.

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

- [x] 1. **types 10.14.0.** Adds `FeatureFlagSchema`: — types build+70 tests, dependents green, packed-consumer tsc clean — done: cd3500a
  - fields: `key`, `enabled`, `targets` (nullable), `owner`, `description?`, `expiresAt`, and the read-only `version`, `updatedAt` and `updatedBy?`;
  - dates follow the existing types convention;
  - `.meta()` descriptions go on each property.

  Also adds the strict `FeatureFlagTargetsSchema`, `FEATURE_FLAG_KEY_PATTERN` (`<service>.<name>`, at most 64 characters) and the `FeatureFlag` type, plus the types row in pkg-node CLAUDE.md. (AC 1)
  — verify:
  - `pnpm -r build` passes and the existing suite stays green;
  - the diff leaves `config-fragment.schema.ts` untouched;
  - after merge, `npm view @gfs-bifrost/types@10.14.0 version` returns 10.14.0.
> SUPERSEDED 2026-10-14. Reverted in 47638f7, so nothing reads flags through remote-config in v1. The pure rule moved to types (inc 5). The client returns with the event and caching follow-up, and its code stays reachable at 3c738b7.

- [x] 2. **remote-config: `evaluateFlag` and `FeatureFlagClient`.** — 10 evaluate + 8 client tests vs node:http; timeout mutation-checked — done: 3c738b7
  - `evaluateFlag(flag, ctx)` is a pure function.
  - `FeatureFlagClient` has its own axios instance with a timeout; the existing `ConfigApiClient` has none.
  - The client parses `{ flags }` item by item, skipping and logging invalid items.
  - No version bump. (AC 2)

  — verify:
  - a table-driven `evaluate.spec.ts` covering:
    - `enabled: false` gives false;
    - null targets give true;
    - a businessId match and a connectorId match;
    - empty arrays give false;
    - a missing ctx id gives false;
    - a past `expiresAt` doesn't change the result;
  - `feature-flag.client.spec.ts`:
    - an invalid item is skipped and the valid ones are returned;
    - a response slower than `fetchTimeoutMs` rejects within it.
> SUPERSEDED 2026-10-14. Inc 3 and inc 4 below moved to the event and caching follow-up ticket, together with their gates. Their checkboxes were removed so sign-off doesn't gate on moved work.

- 3. **remote-config: the `FeatureFlags` snapshot.** It handles TTL, a single shared refresh, a 5 s backoff after a failure and keeping the last-known value, and it takes an `onFallback(evt)` listener. `isEnabled` never rejects. (AC 2,3)
  — verify with vitest fake timers, one test each:
  - the default on a cold start when the API rejects;
  - the default when the API hangs;
  - the last-known value after a failed refresh;
  - the default for an unknown key;
  - N concurrent calls make one fetch;
  - a refetch after the TTL;
  - no refetch inside the backoff;
  - never rejects when the client throws synchronously;
  - `onFallback` receives a reason.
- 4. **Builder and release.**
  - `.withFeatureFlags({ ttlMs?, fetchTimeoutMs? })` on `buildProvider()` exposes `provider.featureFlags`.
  - A standalone `.buildFeatureFlags()` needs only `withConfigApi`.
  - The readme gets an "add / retire / delete a flag" section.
  - Version 2.4.0, with peer `>=10.14.0`.
  - The remote-config row in pkg-node CLAUDE.md.

  (AC 3,4,5)

  — verify:
  - spec: without `withFeatureFlags`, `provider.featureFlags` is undefined and the HTTP mock records no `/feature-flags` call;
  - spec: `buildFeatureFlags()` builds with no cache or Redis config;
  - live: the built `dist`, pointed at dev config-service, evaluates `pkg-node.smoke-test` as true once it is created, as false within 30 s of a PATCH to false, and as the default after a delete;
  - after merge: `npm view @gfs-bifrost/remote-config@2.4.0 peerDependencies` shows `>=10.14.0`.

      gate (moved): config-service write routes live in dev ([[runtime-feature-flags-feature-flags-store-and-ap]] inc 4)
      gate (moved): Renovate's peer-floor PR for types 10.14.0 merged or closed

- [x] 5. **Scheduled changes and the evaluation rule, in types.** — 18 state tests, boundary mutation-checked, packed consumer, remote-config net-unchanged — done: d6f8a14
  - `FeatureFlagScheduledChangeSchema` is strict, and `FeatureFlag.scheduledChange` is required and nullable.
  - Adds the `FeatureFlagContext` type.
  - Adds the pure `resolveFeatureFlag(flag, now)` and `evaluateFeatureFlag(flag, now, context)` in `config/utilities`, with their spec.

  (AC 6,7,8)

  — verify:
  - the `feature-flag-state.spec.ts` truth table, covering schedule before, at and after T, plus targets;
  - a mutation check on the boundary comparison;
  - a packed-consumer check: JSON round trip, schedule flip, a strict schedule, and a schedule-only update;
  - dependents stay green;
  - the net diff against origin/main touches no `pkg/remote-config` file.

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-14 [post-merge] (AC 1) **Published.** #271 was squash-merged as 984bc8d. Publish Packages run 38559655041 succeeded, with Types / Publish green. `npm view @gfs-bifrost/types@10.14.0 version` returns `10.14.0` from GitHub Packages.
- 2026-10-14 [post-merge] **fuse-mcp updated.** `shared-packages.json` now has types 10.14.0 and its feature-flag surface. `make parity-accept` updated `ts-baseline.json`, `go test ./internal/...` has 0 failures, and it was pushed to fuse-mcp master as 5a97141.
- 2026-10-14 [inc 5] (AC 8) **remote-config untouched.** `git diff --stat origin/main -- pkg/remote-config` is empty after the 47638f7 revert. On the reverted tree, remote-config 113, rules-engine 145 and pubsub 29 are all green.
- 2026-10-14 [inc 5] (AC 6,7) **Packed `types@10.14.0` consumer** (strict TypeScript, nodenext). `tsc` is clean.
  - The `FeatureFlag` survives a JSON round trip, and `scheduledChange.at` comes back as a `Date`.
  - `evaluateFeatureFlag` is true at 12:00 for a switch-on scheduled at 07:00, and false at 06:59:59.
  - `resolveFeatureFlag` clears the schedule.
  - An extra key inside `scheduledChange` is rejected.
  - The derived update schema accepts a schedule-only patch.
  - A `@ts-expect-error` proves `scheduledChange` can't be left out.
- 2026-10-14 [inc 5] (AC 6,7) **`feature-flag-state.spec.ts`**, 18 tests:
  - resolve: an unscheduled flag is unchanged, a future change stays pending, a due change applies `enabled` and clears itself, and a change at exactly now counts as due;
  - evaluate: the 10 targeting cases, plus on after a scheduled switch-on, off before it, and off after a scheduled switch-off.

  Mutation check: changing `>` to `>=` makes "treats a change scheduled for exactly now as due" fail. The line was restored. types has 88 tests, all green.
- 2026-10-14 [inc 2] (AC 2) **Mutation check on the timeout test.** Deleting the `timeout: options.fetchTimeoutMs` line from the axios instance makes "rejects … once fetchTimeoutMs passes without a response" hang for 5 s and fail, so the test really proves the timeout. The file was restored afterwards.
- 2026-10-14 [inc 2] (AC 2) **`FeatureFlagClient` against a real `node:http` server**, 8 tests, each asserting one behaviour:
  - the served flags come back parsed;
  - the request path is `/api/v1/feature-flags`;
  - `x-api-key` is sent;
  - an item whose `targets` has a typo is skipped while valid ones are kept;
  - the skipped keys are logged as `{count:1,total:2,keys:[…]}`;
  - a non-list body rejects with `ConfigApiException`, and so does a 500;
  - with no response at all, it rejects within `fetchTimeoutMs` (50 ms).
- 2026-10-14 [inc 2] (AC 2) **`evaluateFlag` truth table**, 10 tests:
  - `enabled: false` gives false, even when targeted;
  - null targets give true, with or without a context;
  - a listed business gives true, an unlisted one false;
  - a listed connector gives true;
  - the business and connector targets are OR'd;
  - empty `businessIds` gives false;
  - targeted with no context gives false;
  - a past `expiresAt` gives true.

  The full remote-config suite passes, 131 tests.
- 2026-10-14 [inc 1] (AC 1) **Packed-consumer check.** The `@gfs-bifrost/types@10.14.0` tarball was installed into a scratch consumer (zod 4.4.3, TypeScript 5.9.2, strict, nodenext).
  - The consumer derived config-service-style schemas: create (`omit` the read-only fields) and update (`omit` key, then `partial`, then `extend` with `expectedVersion`).
  - `tsc --noEmit` is clean.
  - `z.infer<typeof FeatureFlagSchema>` accepts a `FeatureFlag`.
  - A `@ts-expect-error` confirms `targets` can't be left out.
- 2026-10-14 [inc 1] (AC 1) **Smoke test against the built `dist`.**
  - Accepted: `targets: null`, and `targets.businessIds`.
  - Rejected: `targets.businessId` ("Unrecognized key"), `targets: {}`, the key `Foo_bar`, a 65-character key, and `expiresAt: "not-a-date"`.
  - All four exports are present.
  - `config-fragment.schema.ts` has no diff against origin/main.
- 2026-10-14 [inc 1] **Build and tests.** types: `tsc`, 70 tests and biome all clean. Dependents rebuilt and tested against the workspace types: rules-engine 145, pubsub 29 and remote-config 113, all green.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- A flip reaching a real service in prod. That is phase 2 ([[runtime-feature-flags-first-adopter-bulk-ingest-]]).
- inc 1: the publish itself. `npm view @gfs-bifrost/types@10.14.0 version` can only be checked after merge.
- inc 2: the client against real config-service. The route doesn't exist until config-service inc 4. The live check is inc 4's, behind its gate.

## Rollout & rollback
<!-- Added on demand. Written at plan time; amend in place as it changes.
     `Shared state touched:` is the single home for the five classes git does not own — a dev
     deploy, a prod config write, a Datadog monitor, a CI var or secret, cross-repo IaC. Reverting
     the branch undoes none of them, so if they are not written here they are not written down. -->

> SUPERSEDED 2026-10-14. The plan is now a single PR, #271, covering types only (inc 1 and inc 5, with inc 2 reverted). Merging it publishes types 10.14.0. remote-config is no longer released here, so the Renovate peer-floor race no longer applies to this plan. The post-merge checklist below still applies; drop remote-config from it.

- **Order:**
  - PR1 is inc 1+2 (about 400 lines). Merging it publishes types 10.14.0, which unblocks config-service inc 2.
  - PR2 is inc 3 (about 600 lines).
  - PR3 is inc 4 (about 300 lines). It merges only after config-service's write routes are in dev and Renovate's peer-floor PR has landed.
- **Post-merge checklist** (lines without a sha):
  - [x] org Package Changelog row for types 10.14.0 (remote-config 2.4.0 is no longer part of this plan);
  - [x] fuse-mcp `shared-packages.json` plus `make parity-accept`, pushed to master (5a97141). `config-domain.json` waits for config-service's routes (its plan, inc 5).
- **Flags/config:** none in this repo.
- **One-way doors:**
  - A published version can't be unpublished.
  - The `FeatureFlag` shape becomes a contract with config-service and every evaluator. Adding a targeting dimension later is a types plus remote-config minor that every evaluating consumer must take before any flag uses it.
- **Rollback:**
  - Before publish: `git revert`.
  - After publish: forward-only. Consumers opt in by bumping, so nothing reaches a service until it upgrades.
- **Shared state touched:**
  - GitHub Packages publishes;
  - a throwaway dev flag `pkg-node.smoke-test` in dev config-service, deleted after the check;
  - the fuse-mcp data commit on master.
- **Proof in prod:** none from this repo. The first prod reader is phase 2.

## Options considered
<!-- Added on demand. Why this approach and not the others — the thing the planning agent is
     asked for and the plan has otherwise had nowhere to put. Promote to a durable record with
     `wp decide --record` when it is worth defending in a review six months out. -->

- **Chosen (scheduling): the change lives on the flag, and readers evaluate it against the clock.** There's no infrastructure to run, the flip is exact on every reader, and it works while config-service is down. config-service's GET projects the resolved state, so API readers see the truth.
- **Rejected (scheduling): a Cloud Scheduler job that has config-service apply due changes.** Stored state would always be current, but it needs a job plus Terraform, and flips land up to a minute plus the TTL late.

> SUPERSEDED 2026-10-14. The snapshot options below now feed the event and caching follow-up ticket. v1's only reader, fuse-ui, calls the API directly.

- **Chosen: a TTL'd in-process snapshot pulled from config-service.** Its limit on propagation holds whether or not anything is published, it works for every consumer, and it needs no Terraform.
- **Rejected: a `FEATURE_FLAG` fragment on `config_revision`** (the design first agreed in conversation on 2026-10-14):
  - It doesn't bound staleness across instances.
  - Every flip would reach 7 subscribers and fire parse-failure logs and metrics in at least 4 of them until each upgrades types.
  - It changes the closed `ConfigFragmentSchema` union.
  - Once published it can't be withdrawn.
- **Deferred: a dedicated `feature_flag_revision` topic carrying an invalidate signal.** A push still reaches only one instance, and it adds Terraform per adopter. It is the upgrade path if a limit under `ttlMs` is ever needed.
- **Rejected: flags in `CacheService` or Redis.** The TTL is builder-wide, the ms/seconds units are mismatched, and two cache layers add up their staleness.
- **Rejected: a server-side `/evaluate` endpoint.** It puts config-service on the hot path of every flag check.
- **Rejected: auto-revert on `expiresAt`.** Behaviour would change because of a date.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-10-14** — Merged #271 without the design mock's display fields (name, ticket, area, read-by, ready lifecycle). They're informational, and the top level is non-strict, so they can come as an additive types minor when the fuse-ui page needs them. Asking a third time would only have held the contract. Harry: 'merge the pull requests as we go'.

- **2026-10-14** — Harry, 2026-10-14, after reviewing the Claude Design mock (~/ff.png): per-customer targeting (Who gets it: Selected customers / Tier) moves to a later iteration, and scheduled changes ('when') are in the first iteration. The contract must carry the schedule before types 10.14.0 publishes, so #271 is held until the schedule shape is agreed.

- **2026-10-14** — inc 1: no .meta() descriptions on FeatureFlagSchema properties, contrary to the plan text. Nothing in @gfs-bifrost/types uses .meta() today, so it would be a new pattern for one schema. The cost is that config-service's generated OpenAPI shows these fields without descriptions. Revisit fleet-wide if the generated spec needs them.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
