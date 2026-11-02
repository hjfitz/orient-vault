---
ticket: none
title: generated OpenAPI as the single source of truth
service: config-service
status: active
created: '2026-09-17'
updated: '2026-10-19'
repo: /home/hjf/code/fuse/config-service
worktree: /home/hjf/code/fuse/config-service/.claude/worktrees/openapi-generated-single-source
branch: hjf/openapi-generated-single-source
base: origin/main
base_sha: 7f0572b57
pr: '215'
tags:
- waypoint
- plan
impl_model: sonnet
impl_effort: high
---
# none — generated OpenAPI as the single source of truth

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
config-service publishes two OpenAPI surfaces: a hand-maintained `code/openapi.yaml` rendered by a
Scalar page, and a NestJS-generated document. The hand-written one has drifted — it documents 8
operations that 404 in staging and omits `POST /events/customer-creation`. Make the generated
document the only spec, serve it from a dedicated stable URL for client codegen, and delete the
hand-written file and its Scalar page. Proven when that URL serves a spec in which every fuse-ui-consumed
path carries typed 2xx and 4xx bodies, and `openapi.yaml` no longer exists.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. A dedicated, stable spec URL (`/api/v1/docs-json`) serves the generated document, independent of wherever the Swagger UI lives.
- [x] 2. Every non-204 2xx response **that returns a body**, on the 14 paths fuse-ui consumes, declares a response schema. Two do not today; the five DELETE 200s that also lack `content` genuinely return no body and are correct as they stand.
- [x] 3. Every 4xx/5xx response declares a Problem Details schema.
- [x] 4. No schema-level description regression against the hand-written spec on those 14 paths, for schemas this repo owns — verified by porting every description the hand-written spec actually has for those schemas, not by a coverage count.
- [x] 5. `/api/v1/docs` serves the NestJS Swagger UI; Scalar is gone.
- [ ] 6. `openapi.yaml`, `ApiDocsController`, `@scalar/express-api-reference` and `express-openapi-validator` are gone, and this repo's own docs no longer describe a two-spec model.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `code/src/shared/openapi-schema.utilities.ts` — the Zod→OpenAPI conversion; rebuilds containers, so metadata must be carried across explicitly
- `code/src/shared/zod.utilities.ts` — `requiredString()`/`trimString()` build their inner string internally (28 call sites)
- `code/src/main.ts` — `SwaggerModule` setup and the explicit `jsonDocumentUrl`
- `code/src/http/api/v1/business/business.controller.ts` + the five DELETE routes — the untyped 2xx responses
- `code/src/exceptions/http/types.ts`, `exceptions/http/domain-exception.filter.ts` (8 sites), `exceptions/http/middleware.ts` (9 sites) — `ProblemDetails` and its **two** emitters
- `code/src/http/api/v1/{ddp,shipment-methods,sku-blacklist,storefronts,warehouse-routing}/schemas/*`, `connectors/{schema,schemas}.ts` — the schemas this repo owns; `backends/dto.ts` and `business/dto.ts` wrap `@gfs-bifrost/types` schemas and are out of reach
- `code/src/http/api/v1/api-docs/*`, `code/src/bootstrap/{containers/api-docs.module.ts,root.module.ts,factory.ts}`, `code/dockerfile` (L8, L37), `code/openapi.yaml`
- `CLAUDE.md` L14, L85-86, L178, L214-215 — four sites naming the hand-written spec
- `fuse-mcp` and `fuse-mcp-server` `data/api-endpoints.json` (L34, L35, L79, and the `note` at L85) — direct-to-master per the org contract
- Consumer plan, must repoint before increment 6: [[regenerate-the-config-service-client-from-the-ge]]

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- The generated document already covers every path fuse-ui calls (14/14) — diffed live `/api/v1/docs/generated-json` against fuse-ui's app-code path literals, 2026-09-17.
- The 8 hand-spec-only operations are fiction — `GET/POST/PUT /api/v1/default_mappings`, `GET/POST/PUT/DELETE /api/v1/ingress/{businessId}` and `GET /api/v1/connectors/{connectorId}/mappings` each 404 against live staging, and no controller serves them.
- `.meta()` exists (Zod 4.4.3 in the lockfile) and reaches JSON Schema on leaves, but is dropped on every rebuilt container — metadata lives in `z.globalRegistry` keyed by instance, and `toOpenApiSchema` rebuilds objects/arrays/unions/records/tuples/dates. Established by reading the utility and by a `z.toJSONSchema` probe.
- The docs URLs are public by middleware **ordering** (`SwaggerModule.setup` runs before `buildApp` registers auth), not by the `ignoredRoutes` allowlist — which matches on strict path equality and lists six exact entries. So a new spec URL registered by `SwaggerModule` is public automatically, with no allowlist edit. Verified live: an unlisted swagger asset returns 200 while an unknown path under the same prefix returns 401.
- The hand-written yaml is not a published external contract — the only consumers found are fuse-ui and fuse-tui. Caveat: the sweep covered local checkouts and the vault, not Confluence or Postman.
- fuse-tui's `make fetch-specs` breaks when the yaml goes. Accepted — it is a side project and explicitly out of scope (asked, 2026-09-17). Its vendored `specs/` means existing checkouts keep building until they refetch.
- Schemas originating in `@gfs-bifrost/types` (12 of 31 generated components, ~50 of 94 top-level properties) cannot be annotated from this repo. Deferred to a follow-up rather than wrapped locally (asked, 2026-09-17), which is why AC 4 is scoped to repo-owned schemas.

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

- [x] 1. Carry Zod metadata through `toOpenApiSchema`, and give `requiredString()`/`trimString()` a metadata parameter (AC 4) — verify: a new spec file under `code/src/shared/__tests__/` (none exists for this utility today) proving a description survives object/array/union/optional/pipe, **plus a canary** — annotate one leaf and one container, deploy the branch to dev, and show both appearing in the generated document. Asserting on the utility's return value alone is insufficient: the hop through `createZodDto` → `@nestjs/swagger` is untested, and if this increment is wrong, increment 4 silently evaporates. — 11 unit tests (7 fail without the fix) plus an in-process Nest document test proving leaf + nested-container metadata reach SwaggerModule.createDocument output; helpers needed no metadata param — done: eda3645
- [x] 2. Declare response schemas on the two storefront operations that return a body without one (AC 2) — `GET`/`POST /api/v1/business/{businessId}/storefront`. The other six responses lacking `content` (five DELETE 200s and `/health`) return nothing or are out of the consumed set, and the hand spec declares no body for them either. verify: assert the two operations carry `content` in the generated document, and that the nested connector schema expands rather than degrading to `unknown`. — PagedStorefrontResponseDto + CreateStorefrontResponseDto wired; nested connector schema verified to expand to real properties, not unknown — done: 1b4996f
- [x] 3. Declare Problem Details on 4xx/5xx (AC 3) — add a `ProblemDetailsDto` from `exceptions/http/types.ts` and newly derive a `ValidationProblemDetailsDto` (it exists only in the hand yaml today, not in code); apply through one shared decorator rather than 91 hand edits, and cover both emitters. verify: generated document shows `content` on every 4xx/5xx. — ProblemDetailsDto + ValidationProblemDetailsDto registered via extraModels; attachErrorResponses walks the document once, 6 unit tests covering 4xx/5xx/success/already-declared/no-responses — done: 7ce15c9
- [x] 4. Port every field description the hand-written spec actually gives for repo-owned schemas behind the 14 consumed paths (AC 4) — stacked on increment 1. Most fields have no description in the hand-written source either (IDs, type discriminators, nested auth objects); ported only what's grounded there, never invented text for an undescribed field. verify: a per-schema assertion, wired against the real exported DTO classes (not a hand-rolled duplicate schema), that each ported field carries its exact description in the generated document. — 33 grounded descriptions/examples ported across 15 schemas; 18-case wiring test against the real exported DTO classes proves each survives into the generated document — done: 01d0d5d
> SUPERSEDED 2026-10-05 — the retained `openapi.yaml` route described below did not ship. The PR's last commit (`bae72f8`, the
> merge of `origin/main`) removed `legacy-openapi-yaml.route.ts`, its test and its `main.ts` registration, so the squash `b66dfd7`
> serves no yaml at all: `/api/v1/docs/openapi.yaml` returns 401 in dev and prod. The file itself is still committed.
- [x] 5. Expose the dedicated spec URL and retire Scalar (AC 1,5) — explicit `jsonDocumentUrl: "api/v1/docs-json"`, Swagger UI on `/api/v1/docs`, `@scalar/express-api-reference` and the dead `express-openapi-validator` dropped. **The retained `openapi.yaml` route could not stay a Nest controller** — Swagger UI's mount at `/api/v1/docs` swallows any Nest-routed sibling registered under the same base path before Nest's own router ever sees it, confirmed by an actual 404 in a local test. Replaced with a raw Express handler registered directly on the HTTP adapter's instance before `SwaggerModule.setup()` runs. verify: a real (not simulated) supertest run proving Swagger UI, the dedicated JSON URL, and the retained yaml route all 200 together in-process; then the same three against dev. — Retained openapi.yaml route rebuilt as a raw Express handler after the planned Nest-controller approach was proven to 404 (Swagger UI's mount swallows it); real supertest run proves UI, docs-json, and the yaml route all coexist. Also fixed a latent dual-Express-major sendFile bug this surfaced. — done: a789458
- [ ] 6. Delete the hand-written surface (AC 6) — `openapi.yaml`, `ApiDocsController` + module + constants, `express-openapi-validator`, dockerfile L8/L37, the four now-dead `ignoredRoutes` entries, the four `CLAUDE.md` sites, and both `data/api-endpoints.json` files. verify: the yaml URL no longer resolves, `/api/v1/docs` and the spec URL still 200, and the image builds without the yaml.
      gate: [[regenerate-the-config-service-client-from-the-ge]] increment 1 merged — deleting the yaml under a client still pointed at it is the exact failure this ordering exists to prevent
            [ ] confirmed

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-05 [sign-off] Prod `config-service-prod` runs image `prod-6f0b36b` (current `origin/main`, includes squash `b66dfd7` of #215, merged 2026-09-21). Live, unauthenticated: `/api/v1/docs` 200 and is Swagger UI (`swagger-ui-bundle.js`, no Scalar); `/api/v1/docs-json` 200, `openapi: 3.0.0`, 19 paths, byte-identical to dev's. Discharges AC 1 and AC 5.
- 2026-10-05 [sign-off] Same prod document: 91/91 4xx/5xx responses carry `content`; `ProblemDetailsDto` and `ValidationProblemDetailsDto` are in `components.schemas` (AC 3). `GET`/`POST /api/v1/business/{businessId}/storefront` carry `application/json` on 200/201. The only non-204 2xx without `content` are `/health` and the five DELETE 200s the AC excludes (AC 2). `ConnectorResponseDto.connectorId` carries "Unique identifier for the connector", one of the ported descriptions; AC 4 otherwise rests on the increment 4 wiring test.
- 2026-10-05 [sign-off] AC 6 not met. On `origin/main` (`6f0b36b`) Scalar, `express-openapi-validator`, `ApiDocsController`, its module and constants are gone, and `factory.ts` lists only `/api/v1/docs` and `/api/v1/docs-json` among the docs routes. Still present: `code/openapi.yaml` (hand-edited since by #224, #226 and #231), dockerfile L8/L37 copying it, and `CLAUDE.md` L15, L189, L200, L222 describing it. Increment 6 is unstarted.
- 2026-10-05 [sign-off] The increment 6 gate is unmet: [[regenerate-the-config-service-client-from-the-ge]] has `pr: null` and no ticked increments. fuse-ui `origin/main` (`2cae280`) still has `gen-config-service-client` fetching `https://config.fuse.freightops.dev/api/v1/docs/openapi.yaml`, which returns 401 today, so fuse-ui cannot regenerate its client until that plan lands.
- 2026-09-17 [inc 1] `pnpm test` in the worktree: 634 tests / 31 files green, including 11 new `toOpenApiSchema` metadata tests. Deliberately re-ran them against the unfixed function by stubbing the registry read: **7 of the 11 fail**, so they are real regression guards rather than vacuous assertions.
- 2026-09-17 [inc 1] `openapi-document.spec.ts` boots a minimal Nest module and asserts on `SwaggerModule.createDocument` output — the `createZodDto` → `@nestjs/swagger` hop the plan flagged as unproven. Leaf `description` and `example` and a nested object's `description` all reach the emitted component schema.
- 2026-09-17 [inc 1] Same test found that a `.meta()` on a DTO schema's **root** does not become a schema-level `description` — nestjs-zod hoists it onto each property as `x-nestjs_zod-parent-metadata`. Pinned by a test and carried into `## Learnings`; it changes how increment 4 must be written.
- 2026-09-17 [inc 1] `pnpm run lint`, `build:check` and `build:check:tests` each exit 0 (checked the exit code, not the log tail).
- 2026-09-17 [inc 2,3] Deployed `hjf/openapi-generated-single-source` to dev (run 35219960275, announced/reverted in #bifrost-general) and fetched `https://config.fuse.freightops.dev/api/v1/docs/generated-json` live: `GET`/`POST /api/v1/business/{businessId}/storefront` now return 200/201 `content` referencing `PagedStorefrontResponseDto`/`CreateStorefrontResponseDto` respectively — both had none before.
- 2026-09-17 [inc 3] Same live fetch: **91/91** 4xx/5xx responses carry `content`, zero mismatches against the expected schema (400 → `ValidationProblemDetailsDto`, everything else → `ProblemDetailsDto`). `ValidationProblemDetailsDto`'s `issues` field confirmed optional in the emitted schema.
- 2026-09-17 [inc 1] In-process re-verification of the metadata canary with a container **nested inside** a DTO (the shape increment 4 will actually use, as distinct from a `.meta()` on a DTO's own root, which the Learnings entry already covers): both the nested object's description and a leaf's description+example reach `SwaggerModule.createDocument` output.
- 2026-09-17 [inc 1] Dev given back to master (run 35220326177) once the above was captured.
- 2026-09-17 [inc 4] `schema-descriptions.spec.ts`: 18 assertions wired against the real exported DTO classes (`ConnectorResponseDto`, `PagedConnectorsResponseDto`, `CreateConnectorRequestDto`, `UpdateConnectorRequestDto`, `StorefrontResponseDto`, `CreateConnectorMappingRequestDto`, `ReplaceConnectorMappingRequestDto`, `ConnectorMappingResponseDto`) — each of the 33 ported descriptions confirmed present, verbatim, in the actual generated OpenAPI document. `pnpm test`: 658/658 (up from 640). `build:check`/`build:check:tests`/`lint` all exit 0.
- 2026-09-17 [inc 5] Deployed `hjf/openapi-generated-single-source` to dev (run 35224875325, announced/reverted in #bifrost-general) and fetched all three URLs live: `/api/v1/docs` 200 (Swagger UI), `/api/v1/docs-json` 200 (103,351 bytes, `openapi: 3.0.0`, carries the increment-3 descriptions verbatim — spot-checked `ConnectorResponseDto.connectorId` and `PagedConnectorsResponseDto.total`), `/api/v1/docs/openapi.yaml` 200 (the hand-written file, unchanged, 102,795 bytes) — all three simultaneously, proving the raw-Express fix actually resolves the routing collision in the real deployed service, not just in-process. `/api/v1/docs/generated` and `/api/v1/docs/generated-json` both correctly 404 — no dangling alias.
- 2026-09-17 [inc 5] Re-confirmed 91/91 4xx/5xx responses carry content on the fresh live fetch (same script as increment 3's evidence, re-run against this deploy).
- 2026-09-17 [inc 4] Not deployed to dev separately — the wiring test boots the same `SwaggerModule.createDocument` code path a live deploy would, against the real DTO classes, so a dev round-trip would prove nothing the test doesn't already.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->

- That a leaf `.meta()` survives `createZodDto` → `@nestjs/swagger` into the emitted document — probed only as far as `z.toJSONSchema`. Increment 1's canary is what proves it.
- That `SwaggerModule.setup("api/v1/docs")` coexists with the retained Nest `@Get("openapi.yaml")` route under the same base path. Plausible — an unknown path under the swagger prefix falls through to auth rather than a swagger 404, so swagger-ui-express mounts no catch-all — but it needs the local smoke test in increment 5.

## Rollout & rollback
<!-- Added on demand. Written at plan time; amend in place as it changes.
     `Shared state touched:` is the single home for the five classes git does not own — a dev
     deploy, a prod config write, a Datadog monitor, a CI var or secret, cross-repo IaC. Reverting
     the branch undoes none of them, so if they are not written here they are not written down. -->

- **Order:** 1 → (2, 3) → 4 → 5 → [[regenerate-the-config-service-client-from-the-ge]] → 6. Increment 4 **stacks on** increment 1 rather than merely following it: its verification reads the generated document off a dev deploy, and on a branch without increment 1 the metadata is discarded and the assertion fails. 2 and 3 are independent of each other. Reversing 5 and the fuse-ui repoint leaves fuse-ui with no URL to point at; reversing the repoint and 6 deletes the yaml under a live consumer.
- **Flags/config:** none. The only config-shaped change is `jsonDocumentUrl` in `main.ts` (unset → an explicit dedicated path) and the `ignoredRoutes` list in `bootstrap/factory.ts` shrinking by four entries in increment 6.
- **One-way doors:** increment 6 deletes a 3,267-line hand-written artefact and the URL that served it. Recoverable from git, but any consumer not repointed by then loses its spec — fuse-tui, accepted. The gate on increment 6 is the real control.
- **Rollback:** git revert per increment; all six are forward-only-safe and none migrates data. Increment 5 is the one to revert fastest if the docs URLs misbehave, since it moves a live route.
- **Shared state touched:** dev deploys of config-service (increments 1-5 each need one for evidence) and the two `fuse-mcp*` `data/api-endpoints.json` files, which commit direct to master with no PR. Dev is shared and unguarded — a branch deploy overwrites whatever is there, including master — so work these increments **serially through master→dev rather than as parallel branch deploys**, and announce each dev deploy in `#bifrost-general` per the standing rule. The cross-repo consequence: fuse-ui's codegen reads the live URL, so "merged" is never sufficient for it — 2-5 must be *deployed*.
- **Proof in prod:** `/api/v1/docs` returns the Swagger UI and the dedicated spec URL returns a document whose 14 consumed paths all carry typed 2xx and 4xx bodies. Pre-deploy baseline: today the same check fails on 8 2xx responses and all 91 4xx/5xx responses.

## Options considered
<!-- Added on demand. Why this approach and not the others — the thing the planning agent is
     asked for and the plan has otherwise had nowhere to put. Promote to a durable record with
     `wp decide --record` when it is worth defending in a review six months out. -->

- **Chosen — a dedicated live spec URL, with the yaml deleted outright** — consumers point at one URL once and never revisit it; nothing is checked in to drift (asked, 2026-09-17).
- **Rejected — commit a generated spec file, fapi's `export:openapi` pattern** — fapi boots Nest in a script and writes `openapi.yaml`/`.json`, which both its sandbox and its Redoc portal build from. It would have removed the dev-deploy dependency from every verification here, made spec changes reviewable as PR diffs, and kept fuse-tui working untouched — at the cost of a checked-in build artefact and a CI staleness check. Rejected in favour of the fire-and-forget URL (asked, 2026-09-17).
- **Rejected — keep a `/api/v1/docs/generated` alias after the URL move** — a sweep of every local checkout found no consumer; only `fuse-mcp`'s data file documents the path. An alias with no consumer is a permanent artefact for nothing.
- **Rejected — `@ApiProperty` on the DTO classes instead of Zod `.meta()`** — `createZodDto` yields classes with no declared properties, so this means redeclaring ~94 fields purely to hang decorators on: a second source of truth, which is the drift this work exists to kill.
- **Rejected — a local `.extend()` wrapper to annotate `@gfs-bifrost/types`-owned schemas** — same second-source-of-truth objection. Those descriptions belong in the types package; deferred to a follow-up.
- **Out of scope — `.passthrough()` → `.strip()`** — every generated object emits `additionalProperties: {}` (117 sites), which disables excess-property checking across the whole client. The same schemas drive `ZodValidationPipe`, so changing it would alter request-validation behaviour under cover of a docs migration. Measure and decide separately.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-10-19** — Sign-off check 2026-10-19: #215 (inc 1-5) merged. Inc 6 stays open, and its gate is still unmet: fuse-ui's regenerate-the-config-service-client plan has no PR (no PR on hjf/openapi-generated-client), and code/openapi.yaml is still on config-service origin/main. Harry: leave active.

- **2026-10-05** — 2026-10-05: fuse-ui regen against /api/v1/docs-json stopped before commit. The generated document has three defects that would make the client wrong, not just loose. (1) Array response and request DTOs (DDP rules, shipment methods, SKU blacklist, warehouse routing) are emitted as an object {root?: [...]}; the live API returns bare arrays (dev: GET /business/GADG/skus/blacklist -> ["GAD003",...]). (2) The recursive Shopify retrieval-condition group is emitted as unknown, so (value|interval|unknown)[] collapses to unknown[]. (3) DDP minValue is unknown on one union arm. Also every object carries a passthrough [key: string]: unknown, which a Strict<T> helper in fuse-ui can strip. Fix (1)-(3) in config-service's document generation first, then regenerate.

- **2026-10-05** [sign-off] — Found at sign-off, not decided during the work: the PR's final merge commit (`bae72f8`, "retire legacy openapi.yaml route") dropped the raw-Express yaml route that increment 5 built, so #215 retired the yaml **URL** ahead of the gate on increment 6. The gate was meant to stop the yaml going while fuse-ui still pointed at it. In practice the URL went on 2026-09-21 and fuse-ui's codegen has pointed at a 401 since. What increment 6 still has to do is delete the unserved file, the dockerfile lines, the `CLAUDE.md` text and the `fuse-mcp*` data entries. Repointing fuse-ui is now urgent rather than a precondition.

- **2026-09-17** — Increment 5's retained openapi.yaml route could not be a Nest @Controller as planned: SwaggerModule's mount at /api/v1/docs swallows any Nest-routed sibling registered under the same base path, confirmed by an actual 404. Replaced with a raw Express handler (registerLegacyOpenApiYamlRoute) registered directly on the HTTP adapter's instance before SwaggerModule.setup() runs, proven with a real supertest run rather than reasoned about.

- **2026-09-17** — Increment 4 scoped down from '100% property coverage' to 'port what the hand-written spec actually describes'. Extracted the real hand-yaml description/example pairs first (33 grounded facts across ~15 schemas) — most properties (IDs, type discriminators, nested auth objects) have no description in the source of truth either, so requiring 100% coverage would mean inventing text with no grounding. AC 4 and increment 4 reworded to match: no regression, not fabricated completeness.

- **2026-09-17** — PR #215's Integration Tests check went red on a pre-existing CI flake (actions/setup-node's pnpm cache failing to save when the separate node_modules cache hits and skips pnpm install), reproduced identically on unrelated PR #208. Fixed in its own draft PR #216 off main per the org's red-check rule, verified green on its own run, held in draft pending review — not merged or announced yet.

- **2026-09-17** — Increment 2 narrowed from 8 responses to 2. The five DELETE 200s (business, ddp/rules, shipment_methods, skus/blacklist, warehouses/routing) have void handlers and the hand-written spec declares no body for them either, so they are not a regression and inventing a schema would document a body that is never sent. /health is real but outside the 14 consumed paths. AC 2 reworded to 'returns a body'.

- **2026-09-17** — Increment 1: the planned canary (annotate, deploy to dev, eyeball the document) became an in-process test that boots a minimal Nest module and asserts on SwaggerModule.createDocument output. It proves the same createZodDto -> @nestjs/swagger hop, is a permanent regression guard, and needs no dev deploy. Real dev evidence still follows at ship time.

- **2026-09-17** — Increment 1: dropped the planned metadata parameter on requiredString()/trimString(). Carrying metadata at the toOpenApiSchema wrapper already transfers a call-site .meta() off the pipe onto the string it unwraps to, so the helpers need no change — pinned by a test. Source won over the plan.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->

- `waypoint.yaml` lists `code/openapi.yaml` as a key path, with the comment "hand-written API contract, served at runtime". It is no longer served (since #215), and the entry must go when increment 6 deletes the file. Not edited at this sign-off: it is not a markdown doc.

## Handback
<!-- Learnings that turned out false at sign-off, kept as the record rather than deleted. -->

- 2026-10-05 [sign-off] Refuted: "`requiredString()`/`trimString()` construct their inner `z.string()` inside the helper, so `.meta()` written at a call site lands on the pipe and is lost. The helpers need a metadata parameter; 28 call sites depend on this." Increment 1 showed otherwise (see Decisions, 2026-09-17): `carryMetadata` in `toOpenApiSchema` moves call-site metadata off the pipe onto the unwrapped string, so the helpers were left unchanged. Recorded in `architecture.md`.
