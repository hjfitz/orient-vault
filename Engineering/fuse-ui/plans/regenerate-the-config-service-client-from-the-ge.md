---
ticket: none
title: regenerate the config-service client from the generated spec
service: fuse-ui
status: active
created: '2026-09-17'
updated: '2026-10-05'
repo: /home/hjf/code/fuse/fuse-ui
worktree: /home/hjf/code/fuse/fuse-ui/.claude/worktrees/openapi-generated-client
branch: hjf/openapi-generated-client
base: origin/main
base_sha: c9d1e408d
pr: null
tags:
- waypoint
- plan
impl_model: sonnet
impl_effort: high
---
# none — regenerate the config-service client from the generated spec

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
fuse-ui generates its config-service client from config-service's hand-written `openapi.yaml`, which is
being retired in favour of the NestJS-generated document at a dedicated URL. Repoint the codegen and
absorb the consequence: the two specs share no schema names, so the 51 `schemas['X']` aliases in
`config-service.type.ts` must be re-derived against a different decomposition. Proven when the app
builds and the customer and storefront pages still work against dev config-service — including the two
operations that had no response schema before.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [ ] 1. `gen-config-service-client` points at config-service's dedicated generated-spec URL.
- [ ] 2. `config-service.type.ts` still exports the same 51 named types, re-derived from the generated components.
- [ ] 3. `pnpm test`, `pnpm lint`, `pnpm typecheck` and `pnpm build` all pass.
- [ ] 4. The customer and storefront pages render correctly against dev config-service, including the two previously-untyped storefront operations.
- [ ] 5. `result.ts`'s hand-declared error shape is replaced by the generated Problem Details type.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `code/package.json` — the `gen-config-service-client` script
- `code/src/lib/gen/config-service.client.d.ts` — the committed generated artefact (~3.2k lines; generated, so exempt from the PR size target — say so in the PR)
- `code/src/lib/types/config-service.type.ts` — the 51 `schemas['X']` aliases, the bulk of the work
- `code/src/lib/utils/result.ts` (the error shape at L20-25) and `code/src/lib/api-client/api-client.ts` — the typing boundary
- `code/src/app/server-functions/**` — 14 files importing the client, 36 operations across 14 paths
- `code/src/const/use-case.const.ts` — a **total** `Record<UseCase, …>` requiring 10 display fields per member
- Producer plan, must be deployed to dev before increment 1 runs: [[generated-openapi-as-the-single-source-of-truth]]

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- The generated spec covers all 14 config-service paths this app calls — diffed the live generated document against this repo's app-code path literals, 2026-09-17.
- The two specs share **zero** schema names (96 hand-written vs 31 generated `*Dto`, nested types inlined), so aliases become indexed access into a DTO plus `Extract<…, { type: 'sftp' }>` for union members — established by comparing the two component-name sets, intersection empty.
- A collapsed (`content?: never`) response surfaces as a **hard TS error** at the ~7 property-access sites (`data?.data`, `error?.status`, `error && error.status`), because optional chaining narrows `undefined` away and leaves `never`. It stays **silent** in `respond(data, error)` pass-throughs, where `Result<never, …>` is assignable. Established by compiling a probe against a client generated from the live document. So typecheck is necessary and not sufficient.
- This repo has no `build:check`; `next build` is the only thing that catches some failures, so `pnpm build` belongs in the gate — from `waypoint.yaml` `commands.missing` and `operations.md`.
- Nothing here imports `@gfs-bifrost/types` directly, so the pin skew against config-service (`^8.4.0` vs `^10.1.0`) cannot affect codegen — verified by grep.
- The discriminated-union guardrail survives: the generated `ConnectorResponseDto.config` and `ConnectorMappingResponseDto.mapping.config` both emit `anyOf` with `const` discriminators, so narrowing on `config.type` / `config.configType` still works — checked against the live document.
- The `UseCase` enums agree today (13 members, both sides). After this, a new `ALL_USE_CASES` member flows in automatically and breaks `use-case.const.ts`'s total record until someone supplies a label, icon and colour — a known bug class in this estate. Accepted as forced awareness rather than designed around.

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

- [ ] 1. Repoint, regenerate, and make it compile (AC 1,2,3) — re-derive the 51 aliases against the generated components and fix the ~7 sites that hard-error. This must land atomically: the app does not compile between the repoint and the re-derivation, so it cannot be split into separately shippable halves. verify: `pnpm test && pnpm lint && pnpm typecheck && pnpm build` green, **plus** an explicit audit that no 2xx or 4xx on the 14 consumed paths resolved to `content?: never` — the pass-through call sites compile clean even when the type has collapsed.
      gate: [[generated-openapi-as-the-single-source-of-truth]] increments 2-5 deployed to dev — codegen reads a live URL, so merged is not enough, and dev is shared and unguarded, so confirm the deployed sha before regenerating
            [ ] confirmed
- [ ] 2. Adopt the now-real types (AC 4,5) — replace `result.ts`'s hand-declared `{ type; status; detail }` with the generated Problem Details type, and take the real response types on the two storefront operations. Separable from increment 1 because the app already compiles by then. verify: run against dev config-service and screenshot the customer and storefront pages (the fuse-ui screenshot evidence recipe applies — local Mongo plus dev config).

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- <!-- filled by waypoint-work / waypoint-test as each increment lands -->

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- The exact size of the alias re-derivation. 51 aliases are known; how many need `Extract<>` versus plain indexed access is only knowable once the client is regenerated. If increment 1 overruns the PR size target on hand-written lines (the generated `.d.ts` does not count), split it by alias group and say so in `## Decisions & deviations`.
- Whether any consumer relies on a field the hand spec declared and the generated one does not. The path-level diff is clean; a field-level diff across the 14 paths is the check, and increment 1's `content?: never` audit is the cheapest form of it.

## Rollout & rollback
<!-- Added on demand. Written at plan time; amend in place as it changes.
     `Shared state touched:` is the single home for the five classes git does not own — a dev
     deploy, a prod config write, a Datadog monitor, a CI var or secret, cross-repo IaC. Reverting
     the branch undoes none of them, so if they are not written here they are not written down. -->

- **Order:** blocked by [[generated-openapi-as-the-single-source-of-truth]] increments 2-5 being **deployed to dev**, not merely merged. Increment 1 here must merge **before** that plan's increment 6 deletes the yaml — otherwise the client is regenerated from a URL that no longer exists. Both directions are stated in both plans deliberately, so neither can be worked to completion out of sequence.
- **Flags/config:** none. The only change of this shape is the codegen URL in `package.json`.
- **One-way doors:** none here. The producer side owns the only irreversible step.
- **Rollback:** git revert. Increment 1 is a single atomic commit by construction, so reverting restores the previous client and aliases together.
- **Shared state touched:** none written by this plan, but it **reads** shared dev state — config-service's dev deployment. Dev is unguarded and a branch deploy overwrites whatever is there, so confirm which sha dev is running immediately before regenerating; regenerating against someone else's branch produces a wrong client silently, with nothing failing.
- **Proof in prod:** the customer and storefront pages render, and the two previously-untyped storefront operations return typed data rather than `unknown`. Pre-deploy baseline: those two operations currently have no response schema at all.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-10-05** — 2026-10-05: fuse-ui regen against /api/v1/docs-json stopped before commit. The generated document has three defects that would make the client wrong, not just loose. (1) Array response and request DTOs (DDP rules, shipment methods, SKU blacklist, warehouse routing) are emitted as an object {root?: [...]}; the live API returns bare arrays (dev: GET /business/GADG/skus/blacklist -> ["GAD003",...]). (2) The recursive Shopify retrieval-condition group is emitted as unknown, so (value|interval|unknown)[] collapses to unknown[]. (3) DDP minValue is unknown on one union arm. Also every object carries a passthrough [key: string]: unknown, which a Strict<T> helper in fuse-ui can strip. Fix (1)-(3) in config-service's document generation first, then regenerate.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->

- The two specs share zero schema names, so the alias layer in `config-service.type.ts` is the real cost of this migration — not the codegen repoint. Any future spec-source change should be sized on that file, not on `package.json`.
- `content?: never` does not fail silently everywhere: property access on the resulting `never` is a hard TS error, but `respond(data, error)` pass-throughs compile clean. The loud half is a useful canary; the quiet half is why typecheck alone is not a sufficient gate.
- This repo already generated two of its three clients (collector, replay) from NestJS Swagger JSON, so openapi-typescript against a Nest document was proven here before this work started.

