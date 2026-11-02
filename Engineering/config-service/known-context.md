---
tags: [waypoint, config-service]
verified: '2026-08-24'
verified_paths: []
title: config-service — known context
---

# config-service — known context

`known-context.md` is exempt from staleness checks — this is interview/investigation
truth, not a claim about current source. Re-verify against code before trusting a
specific implementation detail below.

## Ownership and criticality (confirmed 2026-08-24)

Wider Fuse team owns this day-to-day — same shared-ownership pattern as the SNAP and
Shopify integration pairs, despite backing every customer's configuration.
**Confirmed blast radius if it's down**: not a fleet-wide outage. Downstream
services cache config (`@gfs-bifrost/remote-config`, Redis + in-process LRU) and
refresh asynchronously off `config_revision` events, so already-cached config keeps
serving existing traffic. What actually breaks: **any new config change**
(onboarding, connector edits, credential rotation) and **any cold cache-miss**
downstream. Don't overstate this service's outage risk to "everything stops" — but
don't understate it either: "no writes can land" is still a real operational
incident, just not a data-plane one.

## No audit trail — and why that specifically hurt once {#no-audit-trail}

`updatedBy` on every write is hardcoded `"admin"` — there is no session identity, so
this service cannot itself say *who* changed a piece of config or *when*, beyond the
Mongo `metadata.updatedAt` timestamp. This isn't a hypothetical gap: a production
incident (SAIRA order-intake outage, referenced in this vault's project memory) was
undiagnosable for two days because nothing recorded what changed on a connector.
That motivated **FUSE-980**, an audit-trail effort — but it lives entirely in
**fuse-ui**, not this repo: it snapshots this service's before/after API responses
around each write and stores the diff itself. As of last check it was 8 commits on a
branch, dev-deployed, **no PR opened yet** (snapshot 2026-08-24). If you're asked to add audit/history to
config-service itself, check whether FUSE-980 already covers the need before
designing a first-party mechanism — don't build a second, competing audit trail.

## Legacy `useCase` naming is a known, deliberate laggard {#legacy-usecase}

The org-wide rename to camelCase `recordType` (decided 2026-05-08) has not reached
this service. Connector mappings are still keyed by a `:useCase` path param and the
legacy `UseCase` type. **Do not** propagate `useCase`/`use_case` into new code here,
and don't rename the existing ones except in a PR explicitly scoped to that cutover
— this service is the known exception to the org rule, not an oversight to
quietly fix.

## The two-place footgun for connector-config fields

A new field on a connector's `config` (SFTP/Shopify/REST ingress) must be added in
**both** the `@gfs-bifrost/types` stored type **and** this service's ingress +
response Zod schemas (`http/api/v1/storefronts/schemas/connector.base.schema.ts`).
Zod strips unknown keys on the way out, so a field added only to the stored type is
silently dropped before `remote-config`'s `ConnectorBacklinkHandler` ever sees it.
Has bitten `outboundTagsEnabled` (FUSE-883) and `egressFiletype` for real. The
use-case *keys* themselves no longer need this treatment (derived from
`ALL_USE_CASES` since `@gfs-bifrost/types` 8.3.0) — don't reintroduce a
null-coalescing crutch when adding a new one; that pattern was deliberately retired.

## Two independent API-contract docs, not one {#two-openapi-consumers}

> SUPERSEDED 2026-09-24 — since config-service#215 the hand-written `openapi.yaml` is **no longer served** (Swagger UI and `/api/v1/docs-json` come from Nest, generated from the DTOs). The file is still in the repo and still hand-edited until fuse-ui's codegen moves. **fuse-ui's `gen-config-service-client` still points at `…/api/v1/docs/openapi.yaml`, which main no longer serves**, so repoint it before regenerating. Found on FUSE-1253 (config-service#226).
> Everything below is kept as the record of the two-spec period.

`code/openapi.yaml` (hand-written, served at `/api/v1/docs/openapi.yaml`) and
`/api/v1/docs/generated` (a separate NestJS/`nestjs-zod`-generated Swagger doc, built
live from the Zod schema attached to each `createOpenApiZodDto` DTO class) are **two
independent specs with two independent consumers** — a field can be correct on one and
silently missing from the other.

- `openapi.yaml` is what fuse-ui's `gen-config-service-client` fetches (confirmed by
  reading its script directly: `npx openapi-typescript
  https://config.fuse.freightops.dev/api/v1/docs/openapi.yaml ...`). It only reflects
  what's hand-edited into it — see the two-place footgun above; this is really a third
  place for a connector-level field (outside `config`).
- `/api/v1/docs/generated` reflects whatever `@gfs-bifrost/types` schema is composed
  into the relevant DTO — e.g. `GET /v1/business` is typed against
  `CustomerInformationResponseDTOSchema`, which composes `ConnectorRefDTOSchema`. This
  one updates for free when the types package does; no hand-edit needed, but it's
  gated on the service's own `@gfs-bifrost/types` pin actually being current.

**Business-index reads (`GET /v1/business`) have no response serializer** —
`GET :businessId` assigns `connectors: result.connectors ?? []` by reference off the
raw Mongo aggregation, with no `ZodSerializerInterceptor`/`ClassSerializerInterceptor`
in front of it. So a field added to `businessInformationProjection` reaches the real
JSON response regardless of whether the imported `ConnectorRefDTO` type declares it,
and with no TS excess-property error. This decouples the **runtime** response from the
`@gfs-bifrost/types` pin entirely — only the two documented specs above depend on it.
(Confirmed FUSE-1167: `confirmationsEnabled` reached the runtime response and
`openapi.yaml` before any types bump; it only reached `/api/v1/docs/generated` once
the pin moved to a version where `ConnectorRefDTOSchema` carried the field.)

## The customer-credential encryption key lives in `core-infra`, not here

Found while onboarding `core-infra` (2026-08-24): the KMS crypto key and
Secret Manager secrets backing config-service's customer-credential
encryption (`config_service_aes_key`, `config_service_api_key`,
`customer_credential_aes_key`) are provisioned in `gfs-bifrost/core-infra`'s
`crypto.tf`, not anywhere in this repo. This isn't visible from
config-service's own code or IaC — anyone touching credential encryption
on either side needs to know the real key material's home is the other
repo. See `core-infra`'s own Waypoint docs (`architecture.md`) for the
full picture of what's provisioned there.

## Doc/tooling drift already known and flagged in-repo

- `README.md` describes a pre-NestJS, plain-Express layout that no longer exists —
  trust `CLAUDE.md` and the code.
- The Fuse MCP catalog (`services.json`) currently lists config-service as
  publishing `customer_creation` events — it doesn't; it's the *subscriber* (see
  [[architecture]]). Also lists a stale Express/Node-22 tech stack.
- CI (`code-quality.yaml`/`integration-tests.yaml`) pins node 22 / pnpm 11.0.8-or-
  `latest`, while the actual runtime is node 24 / pnpm 10 — a real drift, not just a
  stale comment, and `latest` risks a known tarball-mismatch failure against
  `@gfs-bifrost` GitHub Packages.
- `iac/projects/root.hcl`'s `remote_state` block has no `location` — has caused a
  real Terragrunt failure elsewhere in the fleet against the prod bucket
  (`Missing required GCS remote state configuration location`).

## Stale local checkout, with uncommitted work — leave it alone

Verified 2026-08-24: `~/code/fuse/config-service` was on branch `pr-183` with
**uncommitted local modifications** (several spec/service files) and ~45 days
behind `origin/main`. This may be someone's in-progress work — it was left
untouched; all current-state claims in this doc set were read from `origin/main` via
`git show`/`git log`, not the working tree. **Waypoint tooling implication**: this
folder's docs were anchored by hand to `origin/main`'s sha (`18d8c7a`), not the local
checkout's HEAD — a bare `wp verify config-service <doc>` here would stamp the local
checkout's actual (older, dirty) HEAD instead. Don't trust `wp verify`/`wp stale` for
this service until the checkout is confirmed current or a fresh worktree is used.

## The business index derives connector `useCases` (fixed 2026-10-01) {#business-index-usecases}

Until config-service#235 (prod 2026-10-02, `6f0b36b`), `GET /api/v1/business` never returned connector
`useCases` in prod. `businessInformationProjection` read a `useCases` field that connector documents don't
store, and the integration spec masked it by seeding that field into its fixtures. Use-case membership is
derived from the per-use-case keys (`useCasesProjection("$$connector.")`, the same helper the storefront
and connector-list routes use). REST connectors carry no use-case keys, so `useCases: []` is normal for
them: REST "takes a type" by having a webhook.

## Generated OpenAPI document — traps (checked 2026-10-05) {#generated-openapi-traps}

The served contract is the Nest-generated document (`/api/v1/docs-json`), built from the DTOs
since config-service#215. Found while building it:

- **A `.meta()` on the root of a DTO schema does nothing visible.** `nestjs-zod` copies root
  metadata onto every property as an `x-nestjs_zod-parent-metadata` extension and leaves the
  component itself undescribed. Annotate properties and nested objects instead. Pinned by
  `shared/__tests__/openapi-document.spec.ts`.
- **Two DTO classes share a name.** `connectors/dto.ts` and `storefronts/dto.ts` both export
  `ConnectorResponseDto` and `PagedConnectorsResponseDto`. Swagger keys `components.schemas` by
  class name, so one silently wins. Harmless while both wrap `ConnectorDTOSchema`; if one ever
  diverges, the document will show one schema for both and nothing will fail.
- **Tests run with `code/` as the working directory, the same as the app.** A test that writes
  or deletes a bare relative path can hit a real committed file. One briefly deleted
  `code/openapi.yaml`. Use explicit fixture paths, never `process.cwd()`.
- **Two Express majors are installed.** `package.json` pins `express@^4.22.2` (body-parser,
  auth middleware); `@nestjs/platform-express` brings its own `express@5.2.1` for the server.
  They treat `res.sendFile(absolutePath)` differently: 4 accepts it, 5 returns 404. Use
  `res.sendFile(name, { root })`, which works on both. No `src` code calls `sendFile` today.
- **No hand-edit escape hatch once fuse-ui is repointed.** A field fuse-ui needs will then have to
  reach the generated document: publish `@gfs-bifrost/types`, bump the pin here, deploy, then
  regenerate in fuse-ui. FUSE-1167 relied on hand-patching the yaml because `GET /v1/business` has
  no response serializer. Until fuse-ui moves, see the SUPERSEDED note in
  [[#two-openapi-consumers]]: the yaml URL returns 401, so fuse-ui cannot regenerate at all.

## Unknowns

- Whether FUSE-980's audit trail (fuse-ui side) has since opened a PR or landed —
  check current state rather than trusting the snapshot above.
- Who is actually working in the local checkout's uncommitted changes (`pr-183`) —
  not investigated as part of this onboarding pass; don't assume it's abandoned.
