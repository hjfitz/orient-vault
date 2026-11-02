---
ticket: none
title: '@gfs-bifrost/audit: AuditMessage envelope, Fuse kind registry and publisher'
service: pkg-node
status: complete
created: '2026-10-12'
updated: '2026-10-12'
repo: /home/hjf/code/fuse/pkg-node
worktree: /home/hjf/code/fuse/pkg-node/.claude/worktrees/audit-package
branch: hjf/audit-package
base: origin/main
base_sha: b38280ba9
pr: '268'
tags:
- waypoint
- plan
programme: Audit Service
unit: UC
impl_model: opus
impl_effort: medium
---
# none — @gfs-bifrost/audit: AuditMessage envelope, Fuse kind registry and publisher

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
This is unit UC of the [[Audit Service/Migration State|Audit Service]] programme. It is out-of-ticket work; the nearest epic is FUSE-980.

The change publishes a new standalone package, `@gfs-bifrost/audit` 0.1.0. It owns:
- the **`AuditMessage`** envelope, a standard of its own, distinct from `BifrostMessage` and usable outside the Bifrost suite;
- the per-system kind registry, starting with `fuse`;
- a publisher that never throws.

It is the single source of the audit contract. TS producers (fuse-ui, sftp-connector) import it. The Go audit-service generates its envelope from it, the way wms-gateway generates from `@gfs-bifrost/types`.

Proof that it worked:
- `npm view @gfs-bifrost/audit@0.1.0` resolves.
- `z.toJSONSchema` of the envelope yields a non-empty object schema that go-jsonschema can consume.
- The publisher returns `{ok:false}` on a timeout, a rejection or an invalid message, and never throws.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. `@gfs-bifrost/audit@0.1.0` is published to GitHub Packages from pkg-node `main`.
- [x] 2. The root export is an `AuditMessage` Zod schema and type. It has nothing Bifrost-specific in it: no `businessId`, `recordType` or `customer` field.
- [x] 3. `system` is required on every message, and per-system kind registries are exported separately from the envelope (`./fuse`).
- [x] 4. `z.toJSONSchema(AuditMessageSchema)` emits a single object schema (not a root union) with every required field present, so the Go codegen has something to generate.
- [x] 5. `createAuditPublisher` validates, publishes under a bounded timeout, and resolves `{ok:true,messageId}` or `{ok:false,reason}`. It never rejects, never logs the payload, and emits no telemetry.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- **New `pkg/audit/`:** `package.json`, `src/`, `biome.json`, `tsconfig.json`, `vitest.config.ts`. Modelled on `pkg/resilience` and `pkg/snap` (subpath exports with `typesVersions`).
- **Subpaths:**
  - `.` holds the `AuditMessage` envelope.
  - `./fuse` holds Fuse's kind registry.
  - `./publisher` holds `createAuditPublisher`.
> SUPERSEDED 2026-10-12: there is no `@google-cloud/pubsub` peer. The publisher takes a structurally-typed client, so `zod` is the only peer (see Decisions).
- **Dependencies:** a peer `zod` pinned to exactly `4.4.3`, like every other package. A peer `@google-cloud/pubsub ^5`, optional and needed only for `./publisher`. No `@gfs-bifrost/*` dependency at all.
- **CI and publishing:** new `.github/workflows/code-quality-audit.yaml`, copied from `code-quality-resilience.yaml`, keeping `node-run.yaml@hjf/node-run-pnpm-filter` deliberately. New `publish-audit` job in `publish-package.yaml` (`needs: prepare-cache`).
- **Docs:** the pkg-node `CLAUDE.md` package table and dependency graph; a Package Changelog entry in `/home/hjf/code/CLAUDE.md`; fuse-mcp `shared-packages.json` (at sign-off, with `make parity-accept`).
- **Consumers in later units:** audit-service `tools/auditschema` (UE.2), fuse-ui (UF.1), sftp-connector (UG).

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- **Proposed `AuditMessage` v1 fields.** This is a planning default; amend it at plan review.
  - `schemaVersion: 1`
  - `eventId`: a UUID minted by the producer, or a 24-hex legacy id. Accepting both lets the import reuse old ObjectIds.
  - `system`: a lowercase slug, e.g. `fuse`.
  - `tenantId?`: the scope inside the system; for Fuse, the `businessId`.
  - `occurredAt`: an ISO-8601 string.
  - `producer`: the emitting service.
  - `correlationId`: required.
  - `kind`, `action`, and `target{type,id}`: all open strings.
  - `actor{type: user|service|customer|system, id, ip?}`.
  - `details`: an object.
  - Source: the programme decisions on 2026-10-12 (G1, and storing by system), plus the history review (rename to `producer`, require `correlationId`).
- **The envelope is a plain `z.object`, not a union.** canonschema/go-jsonschema emits an empty file for a root union, so gen-check would pass vacuously. Source: the history review of wms-gateway.
- **Open strings for `kind`, `action` and `target.type`, not enums.** Widening a shared enum later breaks older consumers (types 10.4.0). Unknown kinds are still valid envelopes.
- **No JSON Schema artefacts in the package.** The Go side runs `z.toJSONSchema` on the Zod itself, as canonschema does. Source: the factual-grounding review.
- **The publisher emits no telemetry.** Each service emits `fuse.audit.publish_failed` from the result. Source: [[feedback_metrics_in_service_not_shared_package]].
- **No Zod schema tests.** Verification comes from `tsc`, the JSON Schema emit check and behaviour tests on the publisher. Source: [[feedback_no_zod_schema_tests]].
- **It doesn't wrap `PubSubRouter`.** The router wraps payloads in `BifrostMessage` and throws `PubSubPublishError`, whereas the audit publisher returns a result. `PublishOptions` passthrough exists there but doesn't help.

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

- [x] 1. **Scaffold and envelope.** Add `pkg/audit` at 0.1.0 with the root `AuditMessageSchema`/`AuditMessage` and `code-quality-audit.yaml`. Add **no** publish job yet, so nothing publishes on merge. (AC 2,4) — verify: — build/lint pass; JSON Schema is a single object with the 11 required fields — done: d921775
      - `pnpm --filter @gfs-bifrost/audit run build lint test` pass.
      - A test asserts that `z.toJSONSchema(AuditMessageSchema)` has `type: "object"` and lists `eventId`, `system`, `occurredAt`, `producer`, `correlationId`, `kind`, `action`, `target`, `actor` and `details` as required.
      - The CI code-quality check is green on the PR.
- [x] 2. **Fuse kind registry (`./fuse`).** Add `details` schemas for `config_change` (before/after/changedPaths, friendlyName), `user_change`, `credential_access` (`viewed`, `copied`, `link_created`, `rotated`), `sftp_user` and `legacy`, plus a `parseFuseDetails(kind, details)` lookup. Kinds without a registry entry stay valid. (AC 3) — verify: — tsc + lint pass; every kind emits JSON Schema; npm pack lists dist/fuse/* — done: 55e0090
      - `tsc` passes, and `npm pack --dry-run` lists `dist/fuse/*`.
      - Each registered kind emits a JSON Schema.
      - A fixture copied from each real fuse-ui call site parses through the lookup. These are the five eras E1–E5 from the programme Scar tissue.
- [x] 3. **Publisher subpath, then publish.** Add `createAuditPublisher({topicName, producer, timeoutMs})`: validate, set the attributes `auditKind`/`producer`/`system`/`schemaVersion`, publish under a bounded gax timeout with no unbounded retry, and resolve a result. Add the `publish-audit` job, the Package Changelog entry and the pkg-node `CLAUDE.md` row. (AC 1,5) — verify: — 14 tests pass (success/attributes/invalid/timeout/throw); a real PubSub type-checks against AuditPubSubClient; npm view pending merge — done: cae328c
      - Mocked-topic tests show success returns `{ok:true}`; a timeout, a rejection and an invalid message each return `{ok:false}` with nothing published; a thrown client error never escapes.
      - After merge, the `publish-audit` run is green and `npm view @gfs-bifrost/audit@0.1.0 --registry https://npm.pkg.github.com` resolves.
      - gate: Harry approves the merge (publishing is effectively one-way; a published version can't be reused)
            [ ] confirmed

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-12 [AC 1] The merge of pkg-node#268 (`bad70b0`) triggered Publish Packages run 38227308644. `Audit / Publish` succeeded, and `npm view @gfs-bifrost/audit@0.1.0 version --registry https://npm.pkg.github.com` returns `0.1.0`.
- 2026-10-12 [AC 2,3,4] The `audit-message.spec.ts` checks pass: the root `z.toJSONSchema(AuditMessageSchema)` is `type: object` and requires exactly the 11 envelope fields, with `tenantId` optional. `system` is required, and the Fuse registry and union live only under `./fuse`. `npm pack --dry-run` lists `dist/fuse/*` and `dist/publisher/*`.
- 2026-10-12 [AC 3] A scratch `tsc` check against `FuseAuditMessageInput` passes. It is assignable to the publisher's `AuditMessageInput`, and `kind` narrows `details`. `privateKey` in `sftp_user` and `system: "other"` are both compile errors (`@ts-expect-error` honoured). Removing the `legacy` arm produces 1 TS error, which shows the exhaustiveness guard bites.
- 2026-10-12 [AC 5] The `audit-publisher.spec.ts` checks pass (5): ok + messageId; the stamped body + `auditKind`/`producer`/`system`/`schemaVersion` attributes; `invalid` with no publish; `timeout` (fake timers); `publish_failed` resolved, not rejected. A real `PubSub` from `@google-cloud/pubsub` type-checks against `AuditPubSubClient`.
- 2026-10-12 PR CI: all 28 checks pass (per-package tests and lint, plus secops).

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- That the audit-service Go codegen consumes this JSON Schema cleanly. Proven in UE.2 (`make gen-check`).
- That `FuseAuditMessage` fits fuse-ui's real call sites. Proven by fuse-ui's typecheck when it adopts the package in UF.1.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-10-12** — Added FuseAuditMessage (discriminated union on kind, ./fuse) at Harry's request: producers-only typed surface; the envelope stays open so new kinds never break readers or the Go codegen.

- **2026-10-12** — Publisher takes a structurally-typed AuditPubSubClient instead of peer-depending on @google-cloud/pubsub ^5 as planned: a real PubSub satisfies it (checked with tsc against pkg/pubsub's installed client), and the package keeps zod as its only peer.

- **2026-10-12** — Increment 2 dropped the planned 'real call-site fixtures parse' tests: they would assert Zod validates as Zod does, which Harry has ruled out (feedback_no_zod_schema_tests). Tests cover only the lookup's own branching and the JSON Schema emit the Go codegen relies on; call-site fit is proven by fuse-ui's typecheck in UF.1.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
