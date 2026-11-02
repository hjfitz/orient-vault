---
ticket: FUSE-1167
title: confirmationsEnabled on business index
service: config-service
status: complete
created: '2026-09-16'
updated: '2026-09-17'
repo: /home/hjf/code/fuse/config-service
worktree: /home/hjf/code/fuse/config-service/.claude/worktrees/fuse-1167-connector-confirmations-index
branch: hjf/fuse-1167-connector-confirmations-index
base: origin/main
base_sha: d329e7c9e
pr: '211'
tags:
- waypoint
- plan
impl_model: sonnet
impl_effort: medium
---
# FUSE-1167 — confirmationsEnabled on business index

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
Surface each connector's `confirmationsEnabled` flag on the config-service business index
(`GET /api/v1/business` and `GET /api/v1/business/{businessId}`), which currently projects
connectors as `{connectorId, storefrontId, friendlyName, useCases}` only. FUSE-1063 (confirmation
gating) needs this per-connector flag on that response to decide whether to push a confirmation
into Fuse; business-level enablement is being deprecated in favour of the connector-level flag.
This is the wire/HTTP half of [FUSE-1167](https://globalfreight.atlassian.net/browse/FUSE-1167);
the shared-type half is `[[FUSE-1167-confirmationsenabled-on-connectorrefdto]]` (pkg-node).

> SUPERSEDED 2026-09-17 — Structure A adopted instead once `@gfs-bifrost/types@10.1.0` published;
> see `## Decisions & deviations`. The text below describes the original Structure B call and is
> kept as the record of how it was first planned.

Chosen approach is **Structure B (decoupled)**: this PR adds the projection field + openapi declaration
with **no `@gfs-bifrost/types` pin bump** — see Assumptions for why that is sound and safe.
Observable proof: the business-index response returns `confirmationsEnabled` on each connector
matching its stored value, and the served `openapi.yaml` documents it.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. `GET /api/v1/business/{businessId}` (and the paged `GET /api/v1/business`) returns `confirmationsEnabled` on each entry in `connectors[]`, matching that connector's stored value.
- [x] 2. `GET /api/v1/storefronts/{id}/connectors` still returns its existing shape (unaffected).
- [x] 3. `code/openapi.yaml`'s `CustomerInformationResponseDTO` declares the `connectors[]` shape (incl. `confirmationsEnabled`) so the served contract documents what the runtime returns.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `code/src/core/business-information/constants.ts` — `businessInformationProjection`, `connectors.$map.in` block. This one projection feeds **both** the list (`@Get()`) and get-by-id (`@Get(:businessId)`) service paths, so a single edit covers both AC 1 endpoints.
- `code/openapi.yaml` — `CustomerInformationResponseDTO` (~L2354): declares only `businessId`+`friendlyName` today; needs the `connectors[]` (and `storefronts[]`) shape inlined. Reusable description string at ~L1637/L2864.
- `code/src/http/api/v1/business/__tests__/business.controller.integration.spec.ts` — inserted connector Mongo docs (~L198/L334) + expected `toEqual` connectors (~L242/L367).
- **Not touched (AC 2):** `findConnectorsWithStorefrontsPipeline` (`code/src/core/storefront/constants.ts`) — the separate projection behind `GET /storefronts/{id}/connectors`. Precedent for the bare projection reference is `storeFrontsWithConnectorsProjection` in the same `storefront/constants.ts` (FUSE-1122).
- Consumes (read-only) `ConnectorRefDTO` from `@gfs-bifrost/types` — pin unchanged at `^9.2.2`.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- **The field rides through untyped, so no types-pin bump is needed** — the business projection is a raw Mongo aggregation and the `GET :businessId` handler assigns `connectors: result.connectors ?? []` by reference (not a fresh literal), so the projected `confirmationsEnabled` reaches the JSON response and triggers no TS excess-property error under `^9.2.2`; there is no response serializer (`ZodSerializerInterceptor`/`ClassSerializerInterceptor`) to strip it — verified against `origin/main` by two independent reviews.
- **This is not the two-place ingress footgun.** `confirmationsEnabled` is an already-persisted, top-level connector *capability* flag (writable on POST/PATCH, backfilled by `migrate:confirmations-enabled`, already surfaced on `GET /storefronts/{id}`), not a new `config`-subobject ingress field entering the boundary — so the "add it to the ingress Zod schema or Zod strips it" hazard (CLAUDE.md) does not apply to this read-side projection. The live `HOTFIX(FUSE-809 revert)` `.extend({confirmations})` in `business/dto.ts` is that footgun on the *request* side and is unrelated here.
- **Structure A rejected** (bump `^9.2.2`→`^10.1.0` so config-service's own type carries the field): it forces config-service across the types 10.x major the team's automation hasn't adopted (open Renovate PR #203 only reaches `^9.5.0`) and adds a cross-repo publish gate, for a cosmetic honesty gain on a raw-aggregation passthrough. config-service self-heals onto the typed field whenever Renovate later crosses it to 10.x — no code change then. See `## Options`.
- `migrate:confirmations-enabled` already backfilled the flag onto existing connector docs, so the bare `$$connector.confirmationsEnabled` reference finds real data in prod (matches the FUSE-1122 precedent) — established from operations.md + the FUSE-1122 PR.
- The connectors `$lookup` joins on `foreignField: "businessId"`, so the integration fixture's inserted connector docs must keep `businessId` set (they already must, for the current `connectors[]` projection to return anything) — established from the projection + operations.md `migrate:connector-business-id` note.

## Increments
<!-- Each independently implementable AND verifiable. Cite the criteria it discharges as
     (AC n,n). Tick with `wp tick`, which stamps `— done: <sha>` from HEAD; never hand-write it.
     Prefer 3-7 — more usually means the ticket is too big, so say that rather than splitting
     hairs. -->

- [x] 1. Add `confirmationsEnabled: "$$connector.confirmationsEnabled"` to `businessInformationProjection`'s `connectors.$map.in` block, **and** add the field to the inserted connector docs and the expected `toEqual` connectors in `business.controller.integration.spec.ts` (both the list and single-business cases) — keeping `businessId` on the inserted docs. Leave the unit spec's typed connector literals untouched (adding the field there is an excess-property error against the `^9.2.2` `ConnectorRefDTO`). (AC 1,2) — verify: with the projection line reverted the integration test **fails** (field stripped from `resp.body`); with it applied it **passes** — the concrete AC 1 proof. Confirm the existing storefront-connectors integration tests stay green (AC 2, passive — no code touches that path). — failing-first proof: reverted line -> 2 tests fail exactly on the missing field; reapplied -> 31/31 pass. AC2 storefront-connectors tests unaffected (7/7 pass). build:check + build:check:tests both exit 0, no excess-property error — done: fb2ff79
- [x] 2. In `openapi.yaml`, inline the `connectors[]` array shape (`connectorId`, `storefrontId`, `friendlyName`, `useCases[]`, `confirmationsEnabled`) and the `storefronts[]` array shape (`storefrontId`, `friendlyName`) onto `CustomerInformationResponseDTO` — neither array exists in the spec today (FUSE-1064 added them to the runtime response but never to the spec) and there is no reusable `ConnectorRef` component to `$ref`, so they must be written out. Reuse the existing `confirmationsEnabled` description string. (AC 3) — verify: the served-spec / OpenAPI validation step passes (the repo's spec lint if one exists, else `npx @redocly/cli@latest lint code/openapi.yaml`), and fuse-ui's `gen-config-service-client` (or a manual read of the served `/api/v1/docs/openapi.yaml`) surfaces `connectors[].confirmationsEnabled`. Discharges no *runtime* AC — AC 1 is the JSON, this is the documented contract for downstream consumers. — redocly lint: identical 56 errors/68 warnings before and after (pre-existing security-defined/operationId noise, none in edited range); parsed YAML confirms connectors[].confirmationsEnabled present — done: 9edf9bf
- [x] 3. Full local gate then dev e2e — `pnpm run build:check` + `pnpm run build:check:tests` (both exit 0, no types bump so no cross-major resolution), `pnpm test`, `pnpm run test:integration`, `pnpm run lint:fix`; then deploy the branch to dev (`gh workflow run manual-deploy.yaml --ref hjf/fuse-1167-connector-confirmations-index`) and curl the real service. (AC 1, AC 2 end-to-end) — verify: `GET /api/v1/business/{businessId}` for a business whose connectors carry the flag returns `connectors[].confirmationsEnabled` matching the stored value (AC 1 e2e); `GET /api/v1/storefronts/{id}/connectors` returns its unchanged shape (AC 2 e2e). — local gate green (build:check/build:check:tests/619 unit/334 integration/lint); dev e2e via curl (Fuse MCP): AC1 confirmed with real mixed true/false data on GADG, AC2 confirmed storefronts/connectors endpoint unchanged — done: 9edf9bf

## Options
<!-- Alternatives the planning/review surfaced worth recording. -->
- **Projection: bare reference vs `$ifNull` default.** Chosen: bare `$$connector.confirmationsEnabled` (matches the FUSE-1122 `storeFrontsWithConnectorsProjection` precedent; emits the stored `true`/`false`, omits the key only for a doc predating the backfill — none in prod). Alternative `$ifNull: ["$$connector.confirmationsEnabled", false]` would always emit a boolean but diverges from precedent and could mislabel a genuinely-unset legacy connector as `false`. Reviewer's-choice; left as bare for consistency.
- **Structure A (types-pin bump to `^10.1.0`)** — see Assumptions. Kept in the back pocket for whenever the team crosses config-service onto types 10.x; at that point fold this field onto the unit-spec typed literals too.

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-09-17 [inc 3] **AC1 e2e (dev)**: `GET /api/v1/business` (via Fuse MCP `list-customers`) and `GET /api/v1/business/GADG` (via `config-read`) both return `connectors[].confirmationsEnabled` — verified against real mixed data, not a static default: GADG alone has both `true` (e.g. "Primary SFTP") and `false` (e.g. "Emerald Sea", "Primary API") connectors, matching their stored values exactly.
- 2026-09-17 [inc 3] **AC2 e2e (dev)**: `GET /api/v1/storefronts/sf_c18b98604b4242ec819aba8bbdf4b5f9/connectors` (GADG's storefront) returns its unchanged shape — `{_id, connectorId, friendlyName, metadata, businessId, status, type, useCases}`, no `confirmationsEnabled` — confirming `findConnectorsWithStorefrontsPipeline` is genuinely untouched.
- 2026-09-17 [inc 3] **Local gate**: `build:check` + `build:check:tests` both exit 0 (no excess-property error, no types-pin bump needed); `pnpm test` 29 files/619 tests passed; `pnpm run test:integration` 14 files/334 passed (15 skipped), matching the FUSE-1122 precedent's exact counts; `lint:fix` clean except one pre-existing `noExplicitAny` warning in `connectors.controller.ts:58` (documented in the FUSE-1122 PR, untouched by this change).
- 2026-09-17 [inc 3] Deployed to dev via `gh workflow run manual-deploy.yaml --ref hjf/fuse-1167-connector-confirmations-index` (run 35199062944, docker-push-dev + terraform-apply-dev both success); dev given back to `main` afterward.
- 2026-09-17 **Types bump to `^10.1.0` (Structure A adopted, see Decisions)**: `CustomerInformationResponseDTOSchema.safeParse(...)` round-tripped with `connectors[0].confirmationsEnabled: true` present in the parsed output — confirms the field now flows through the same Zod schema that drives `/api/v1/docs/generated` (the NestJS-generated Swagger doc), not just the hand-written `openapi.yaml`. Full local gate re-run against the real published 10.1.0: `build:check` + `build:check:tests` both exit 0, `pnpm test` 619/619 (incl. the unit spec's typed connector literals, now also carrying `confirmationsEnabled` with no excess-property error), `pnpm run test:integration` 334/334 (15 skipped), `lint:fix` clean (same pre-existing warning).

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- (none) — both AC1 and AC2 verified live against dev with real data; AC3 (openapi) verified statically in increment 2.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-09-17** — Adopted Structure A after all (bumped @gfs-bifrost/types ^9.2.2 -> ^10.1.0), superseding the plan's original Structure B call. Trigger: /api/v1/docs/generated (NestJS-generated Swagger, built from the same Zod schema that composes ConnectorRefDTOSchema) is consumed by some services -- unlike fuse-ui's client, which reads the hand-written openapi.yaml directly, those consumers need the field on the typed schema, not just the raw projection. Verified against the real published 10.1.0 (not just the earlier grep prediction): build:check, build:check:tests, 619/619 unit, 334/334 integration all clean -- the 10.0.0 major (FUSE-1164, customer-reference-required on canonical SO/RGA/WO) is confirmed inert for config-service. Unit spec's typed connector literals (business.controller.spec.ts) now also carry confirmationsEnabled, closing the one gap Structure B had left.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
- Promoted into `known-context.md` § [[known-context#two-openapi-consumers|Two independent API-contract docs, not one]] (the no-response-serializer fact, the openapi.yaml/generated-doc split, and the FUSE-1064 drift history). Still worth a follow-up: config-service's own `CLAUDE.md` "Connector-level fields have a third place" section describes only `openapi.yaml`, not `/api/v1/docs/generated` — flagged to the user, not fixed here (repo doc, no open PR to carry it).
