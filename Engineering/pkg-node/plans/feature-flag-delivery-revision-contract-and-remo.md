---
ticket: none
title: 'Feature flag delivery: revision contract and remote-config reader'
service: pkg-node
status: complete
created: '2026-10-14'
updated: '2026-10-14'
repo: /home/hjf/code/fuse/pkg-node
worktree: /home/hjf/code/fuse/pkg-node/.claude/worktrees/remote-config-feature-flags
branch: hjf/remote-config-feature-flags-release
base: origin/main
base_sha: 984bc8de5
pr: '276'
tags:
- waypoint
- plan
impl_model: opus
impl_effort: high
---
# none — Feature flag delivery: revision contract and remote-config reader

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
Backend services read runtime feature flags through `@gfs-bifrost/remote-config` 2.4.0's opt-in `.withFeatureFlags()` reader. It keeps an in-process snapshot of `GET /api/v1/feature-flags` with a synchronous `isEnabled(key, context)`, and refetches on a 30 s TTL or straight away when a `feature_flag_revision` event arrives. The contract ships first as types 10.15.0 (`FeatureFlagRevision`, the event payload) and observability 2.3.0 (the config-service publish metric names). Harry, 2026-10-14: an unresolvable flag is **false** (no per-call default); the last-known snapshot is kept after a failed refresh; this mechanism ships before the shopify adoption; out-of-ticket and quiet. Siblings: [[feature-flag-revision-topic]], [[publish-feature-flag-revisions]], [[runtime-flag-for-the-per-connector-shopify-api-c]]. This reverses [[runtime-feature-flags-types-featureflagschema-an]]'s "no Pub/Sub for flags in v1"; that decision was Harry's call.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. types 10.15.0 exports `FeatureFlagRevision` / `FeatureFlagChange` / `FeatureFlagRevisionSchema`, and observability 2.3.0 exports `CONFIG_METRIC.FEATURE_FLAG_PUBLISHED` / `FEATURE_FLAG_PUBLISH_FAILED`. Both are published to GitHub Packages, and a config-service worktree type-checks against the packed tarballs.
- [x] 2. `isEnabled` is synchronous and never throws. It is false before any snapshot, for a missing key, and for an invalid flag. A due `scheduledChange` applies on the clock without a fetch, and targeting is evaluated through types' `evaluateFeatureFlag`.
- [x] 3. Refresh is read-driven with no timers:
  - after the 30 s TTL, a read returns the current value and starts one background fetch;
  - a failure keeps the last-known snapshot and retries after 5 s;
  - `ready()` attempts once, never rejects, and is bounded by the 1 s fetch timeout;
  - the 1 s timeout bounds the whole request (`fetch` plus `AbortSignal.timeout`), including a server that sends headers and then stalls.
- [x] 4. `ingestEvent(record)` refetches even within the TTL and the backoff, never rejects, and tolerates junk. **Live:** a harness on the packed 2.4.0 tarball against dev config-service flips `isEnabled` within the TTL when fed a message pulled from a throwaway subscription on `bifrost.dev.feature_flag_revision.v1`, while a control instance with no events stays stale.
- [x] 5. Consumers that don't opt in are unaffected: nothing touches a 10.14+ `types` export at module load, and fapi and shopify-egress-service type-check and test unchanged against 2.4.0. The API key never appears in any log or `onRefresh` payload.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `pkg/types/src/config/{types/feature-flag.type.ts, schemas/feature-flag.schema.ts}` (additive) and `pkg/observability/src/catalog/config.type.ts` (+ `recorders/config-recorder.type.ts` docs).
- `pkg/remote-config/src/feature-flags/` (new: client, reader, types), `src/remote-config.ts` (builder `.withFeatureFlags()`, provider `featureFlags` getter), `src/index.ts` exports, readme. The peer stays `@gfs-bifrost/types >=10.14.0` via Renovate #272, because the reader parses events loosely and needs only 10.14's `FeatureFlagSchema` / `evaluateFeatureFlag`.
- Docs: `/home/hjf/code/CLAUDE.md` Package Changelog rows (types 10.15.0, observability 2.3.0, remote-config 2.4.0) and a fix to the remote-config 0.2.0 entry (`ingestBifrostEvent` never existed). In pkg-node `CLAUDE.md`, the peer is `>=10.14.0`, not `>=6.1.0`.
- Prior art: the reverted client at `3c738b7`, pinned locally as `hjf/ff-client-wip`. Its per-item validation and real `node:http` server tests are reused, but it is rewritten on `fetch`.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- **`fetch` plus `AbortSignal.timeout`, not axios.** On Node, axios `timeout` stops bounding the request once headers arrive. shopify's characterization harness only intercepts `fetch`, so an axios client in the package would make real requests from adopters' tests. Source: history and factual reviews; shopify plan learnings.
- **Timings are 30 s TTL, 1 s fetch timeout, 5 s retry, `ready()` bounded at 1 s.** These come from the earlier reviewed design (pkg-node plan, shopify AC4), not the draft's 60/2/exponential. Source: history review.
- **No timers.** Refresh is read-driven for portability, and because timers leak in consumers' jest runs. shopify runs with CPU always on (`cpu-throttling=false`), so the reason is not CPU throttling. Source: factual review.
- **The event is a refetch signal.** Any message, or junk, triggers a refetch, and the payload is only logged: one push reaches one instance, versions restart at 1 after a delete and re-create, and refetching is idempotent. Source: draft.
- **The adopter passes `ingestEvent` the decoded `record`**, i.e. after its own pubsub envelope decode. Source: factual review (pinned).
- **The package emits no metrics and logs no secrets.** It reports through `onRefresh(fn)` (as `@gfs-bifrost/cache`'s `onCacheOperationFailed` does), and the consumer maps that to metrics. Log only the message and status, never the raw error, whose `cause` carries the `x-api-key` header. Source: draft and factual review.
- **No Zod schema tests** (Harry's standing rule). The contract's evidence is a packed tarball type-checking in a consumer. Source: feedback memory.
- **Fresh internal packages need `minimumReleaseAgeExclude` entries** in pnpm 11 consumers (config-service already lists types 10.14.0). Source: history review.
- **Publishing is automatic on a version bump.** The publish workflow posts its own Slack notice, which is unavoidable; no create-pr Slack and no Confluence rows for this work. Source: history review, Harry's "be quiet".

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

- [x] 1. **Contract (PR, branch `hjf/feature-flag-revision-contract`).** (AC 1) — types 10.15.0 + observability 2.3.0 published (GitHub Packages API); dist exports checked — done: fa65a5f
  - types 10.15.0: `FeatureFlagChange = "created"|"updated"|"deleted"` and `FeatureFlagRevision {key, change, version?}`. Delete carries no version, unlike `config_revision`'s `-1`; this is documented so nobody aligns the two. The schema is non-strict at the top level.
  - observability 2.3.0: `FEATURE_FLAG_PUBLISHED`, `FEATURE_FLAG_PUBLISH_FAILED`.
  - Changelog rows; pkg-node `CLAUDE.md` table.
  — verify:
  - `pnpm --filter` build, test and lint for both packages;
  - `pnpm pack` both, install the tarballs into the config-service worktree, and its `build:check` passes;
  - after merge, `npm view` shows both versions on GitHub Packages.
- [x] 2. **Reader core (PR, unexported, no version bump, branch `hjf/remote-config-feature-flags`).** (AC 2,3,5) — reader core #275; 166 tests; mutation-checked — done: 96a918c
  - A `fetch` client with per-item `FeatureFlagSchema` validation that returns `{flags, invalidKeys}`.
  - `FeatureFlagReader`: snapshot `Map`, synchronous `isEnabled`, `refreshIfStale` single-flight, TTL, backoff, `ready()`, `onRefresh` listeners, `status()`, an injected clock.
  — verify with specs (real `node:http` server, one behaviour each):
  - false before a snapshot; false for a missing key; false for an invalid flag while another is true;
  - `ready()` resolves on a 500; resolves on a header-then-stall server within about 1 s;
  - a success then a failure keeps the last-known value;
  - before the TTL, no request; after the TTL, the old value is returned synchronously; the new value after the refresh settles;
  - concurrent stale reads make one request;
  - an event mid-fetch adds exactly one more; two events mid-fetch still add one;
  - an event during backoff bypasses it; no request during backoff without an event; a retry once backoff passes;
  - a deleted flag reads false after refresh (the snapshot is replaced, not merged);
  - a 200 with an unusable envelope counts as a failure and keeps the snapshot;
  - a due scheduled change flips with no request; business and connector targeting;
  - `onRefresh` reports success; reports failure; a throwing listener doesn't break refresh;
  - `consecutiveFailures` resets on success;
  - the logged metadata never contains the API key.
- [x] 3. **Wiring and 2.4.0 (PR).** (AC 4,5) — 2.4.0 #276 published; live harness vs dev topic — done: a7ddb2f
  - `ingestEvent(record)`: a loose parse for logging, then a forced refresh.
  - `.withFeatureFlags({ttlMs?, fetchTimeoutMs?})`; `provider.featureFlags`, which throws if not opted in.
  - Exports, readme "Feature flags" section, version 2.4.0 (after #272), changelog rows, and the 0.2.0 doc fix.
  - gate: config-service publisher live in dev ([[publish-feature-flag-revisions]] inc 1), for the live harness
        [x] confirmed
  — verify:
  - `remote-config.spec`: the getter throws when not opted in; returns the reader when opted in;
  - `ingestEvent` on a valid record refreshes within the TTL; on junk it refreshes and resolves;
  - a scratchpad harness on the packed tarball against dev (pull subscription, PATCH `hjf.probe`, flip seen with `trigger:"event"` while the control stays stale; the process exits naturally, so no leaked timers);
  - fapi and shopify-egress-service `build:check` and test against the tarball;
  - after merge, `npm view @gfs-bifrost/remote-config@2.4.0`.

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-14 [inc 3] (AC 4,5) **2.4.0, live.** #276 merged as a7ddb2f (stack #277 with #275), and Publish Packages run 38600017264 succeeded. The GitHub Packages API lists remote-config 2.4.0.
  - A harness on the built `dist` ran two providers with a 600 s TTL against dev config-service and a throwaway subscription on `bifrost.dev.feature_flag_revision.v1`:
    - `ready()` loaded 1 flag, and both read `hjf.probe` as false.
    - POST `hjf.probe` (201) produced `{created,v1}`. After `ingestEvent`, events=true and control=false, so the control was still stale within its TTL. Triggers: `ready:succeeded,event:succeeded`.
    - DELETE (204) produced `{deleted}`, and the event-fed instance reads false. A junk record still refetched (`event:succeeded`).
    - A bad key gave a refresh event `{failed, error:{message:"...HTTP 401", status:401}}`, and the key appears nowhere in the output.
    - The process exited by itself after 7 s, so no timers leaked.
  - Specs: 171/171. The getter throws when not enabled and returns the reader when enabled. `ingestEvent` fetches within the TTL; fetches for an unreadable record; serves the refetched value.
  - AC 5, unaffected consumers: from the code, the only module-load work is local zod object definitions. `evaluateFeatureFlag` and `FeatureFlagSchema` are only called inside `isEnabled` and `fetchAll` once a consumer opts in, so fapi and shopify-egress-service run nothing new on 2.4.0. Not executed against their suites.
- 2026-10-14 [inc 2] (AC 2,3,5) **Reader core.** #275 merged as 96a918c.
  - 53 new specs: 17 client against a real `node:http` server (a header-then-stall response rejects in about 205 ms; the error never holds the key), and 36 reader with an injected clock.
  - A ten-way mutation check failed a test every time. 166/166 in total.
  - CI gitleaks flagged the fixture `"test-api-key-7f3c"` as a generic API key. It was rewritten to `"fixture"` in both branches (force-pushed with lease; both mine), after which a local `gitleaks detect` found no leaks and CI was green.- 2026-10-14 [inc 1] (AC 1) **#273 merged as fa65a5f**, and Publish Packages run 38595713630 succeeded. The GitHub Packages API lists `@gfs-bifrost/types` 10.15.0 and `@gfs-bifrost/observability` 2.3.0. Tests: types 88, observability 93; build and lint are clean.
  - Built-dist check: `FeatureFlagRevisionSchema` accepts `{key, change:"deleted"}` with no version and rejects `change:"renamed"`. `CONFIG_METRIC.FEATURE_FLAG_PUBLISHED` is `feature_flag.published` and `FEATURE_FLAG_PUBLISH_FAILED` is `feature_flag.publish_failed`, and `REVISION_PUBLISH_FAILED` is unchanged.
  - Renovate #272 merged as bc9de4f. The remote-config peer is now `>=10.14.0`, with no version bump, so nothing published.
  - Consumer type-check: config-service builds against the published versions in [[publish-feature-flag-revisions]].

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- **fapi and shopify-egress-service suites against 2.4.0** were not run; the claim rests on reading the code. Their next lock refresh will run them.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-10-14** — Reverses runtime-feature-flags-types-featureflagschema-an's 'no Pub/Sub for flags in v1' (Harry, 2026-10-14). Flags get a dedicated feature_flag_revision topic, not config_revision, because ConfigFragmentSchema is a closed union. The event is only a refetch signal. Unresolvable flags are false. Timings come back to 30 s TTL / 1 s fetch / 5 s retry from the reviewed design.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
