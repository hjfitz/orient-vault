---
ticket: FUSE-1167
title: confirmationsEnabled on ConnectorRefDTO
service: pkg-node
status: complete
created: '2026-09-16'
updated: '2026-09-17'
repo: /home/hjf/code/fuse/pkg-node
worktree: /home/hjf/code/fuse/pkg-node/.claude/worktrees/fuse-1167-connector-ref-confirmations
branch: hjf/fuse-1167-connector-ref-confirmations
base: origin/main
base_sha: cb22ca1e2
pr: '225'
tags:
- waypoint
- plan
impl_model: sonnet
impl_effort: low
---
# FUSE-1167 — confirmationsEnabled on ConnectorRefDTO

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
Add an optional `confirmationsEnabled?: boolean` to `ConnectorRefDTO` — the compact per-connector
shape the config-service business index (`GET /api/v1/business`) projects — so a typed consumer
reading that response off the package (notably FUSE-1063's confirmation gating) can see each
connector's confirmation-enablement without re-fetching the full connector. The field already
exists on the full `ConnectorDTO` and on the stored `ConnectorConfigService`; `ConnectorRefDTO` is
the one remaining ref shape that omits it. This is the `@gfs-bifrost/types` half of
[FUSE-1167](https://globalfreight.atlassian.net/browse/FUSE-1167) — see the paired config-service
plan `[[FUSE-1167-confirmationsenabled-on-business-index]]` for the wire/HTTP half. Observable
proof: `@gfs-bifrost/types@10.1.0` publishes with `confirmationsEnabled?` on both the
`ConnectorRefDTO` type and `ConnectorRefDTOSchema`, and a value carrying the field round-trips
through `ConnectorRefDTOSchema.parse`.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. `ConnectorRefDTO` (type) and `ConnectorRefDTOSchema` (Zod) both carry an optional `confirmationsEnabled?: boolean`; `ConnectorRefDTOSchema.parse({...validRef, confirmationsEnabled: true})` returns the field (not stripped).
- [x] 2. `@gfs-bifrost/types` publishes as **10.1.0** (additive minor) with a matching `#### 10.1.0` Package Changelog entry in the org contract file.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `pkg/types/src/config/types/connector.type.ts` — `ConnectorRefDTO` (~L103-108). JSDoc to copy from `ConnectorDTO.confirmationsEnabled` (~L121-122).
- `pkg/types/src/config/schemas/connector-dto.schema.ts` — `ConnectorRefDTOSchema` (~L89), declared `z.ZodType<ConnectorRefDTO> = z.object({...})`. `z.boolean().optional()` to copy from `ConnectorDTOSchema.confirmationsEnabled` (~L65).
- `pkg/types/package.json` — version 10.0.0 → 10.1.0.
- `/home/hjf/code/CLAUDE.md` — "Package Changelog → `@gfs-bifrost/types`" (org contract, not in this repo).
- **Downstream contract:** `ConnectorRefDTOSchema` is composed into `CustomerInformationResponseDTOSchema` (`business-information.schema.ts`, `connectors: z.array(ConnectorRefDTOSchema)`) — so the field flows onto the business-index response schema with no edit to `business-information.type.ts`/`.schema.ts`.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- Type↔schema lockstep is **forced, not optional** — `ConnectorRefDTOSchema` is declared `z.ZodType<ConnectorRefDTO>`, so a field on one without the other fails to compile — established by reading the schema declaration (factual-grounding review).
- The schema edit is the load-bearing half: `ConnectorRefDTOSchema` is a plain `z.object` (strips unknown keys), so a remote-config-style consumer parsing the business index would **strip** `confirmationsEnabled` if only the type carried it (the `outboundTagsEnabled`/FUSE-883 strip class) — established by review; the field must be on the schema, not just the type.
- Additive optional field → minor bump → 10.1.0; `origin/main` is 10.0.0 — established by reading `package.json`.
- The org Package Changelog on disk stops at `#### 9.5.0` (no 10.0.0 row); adding a `#### 10.1.0` block above the gap is consistent with the repo's documented "version-history gaps are a separate cleanup" habit — established by reading the changelog. Worth flagging the missing 10.0.0 row to whoever owns that file, but not this ticket's job.

## Increments
<!-- Each independently implementable AND verifiable. Cite the criteria it discharges as
     (AC n,n). Tick with `wp tick`, which stamps `— done: <sha>` from HEAD; never hand-write it.
     Prefer 3-7 — more usually means the ticket is too big, so say that rather than splitting
     hairs. -->

- [x] 1. Add `confirmationsEnabled?: boolean` to `ConnectorRefDTO` (type) and `ConnectorRefDTOSchema` (`z.boolean().optional()`), lockstep, copying the JSDoc and the schema line from the existing `ConnectorDTO`/`ConnectorDTOSchema` siblings in the same files (AC 1) — verify: `pnpm --filter @gfs-bifrost/types build` / `tsc --noEmit` green, the package's schema↔type parity test passes, and a unit assertion that `ConnectorRefDTOSchema.parse({connectorId, storefrontId, friendlyName, useCases: [], confirmationsEnabled: true}).confirmationsEnabled === true`. — build + 63 tests green; ConnectorRefDTOSchema.parse round-trip confirmed confirmationsEnabled not stripped — done: 70732e2
- [x] 2. Bump `pkg/types/package.json` 10.0.0 → 10.1.0 and add a `#### 10.1.0` entry under "Package Changelog → `@gfs-bifrost/types`" in `/home/hjf/code/CLAUDE.md` (AC 2) — verify: `git diff` shows the `version` line changed (publishing is **version-gated, not diff-gated** — a merged types change with no bump silently strands, so this check is not optional) and the changelog block is present. Publish gate on merge: makes 10.1.0 available on GitHub Packages for the typed consumer (FUSE-1063) and for config-service's eventual Renovate crossing — it does **not** gate the paired config-service PR (Structure B, see that plan). — version bumped 10.0.0->10.1.0 in git diff; changelog entry added to org CLAUDE.md (untracked file, not part of this repo's diff) — done: d638ff1

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-09-17 [inc 1] `pnpm run build` (`tsc`) exit 0; `pnpm test` 8 files/63 tests passed, including `confirmation-registry.spec.ts` unaffected; `node -e` round-trip confirmed `ConnectorRefDTOSchema.parse({...,confirmationsEnabled:true}).confirmationsEnabled === true` (not stripped).
- 2026-09-17 [inc 2] `git diff` confirmed `package.json` version line `10.0.0` → `10.1.0`; changelog entry added to `/home/hjf/code/CLAUDE.md`. Published to GitHub Packages; PR [gfs-bifrost/pkg-node#225](https://github.com/gfs-bifrost/pkg-node/pull/225) merged 2026-09-17.
- 2026-09-17 **Downstream consumer proof**: config-service's `CustomerInformationResponseDTOSchema.safeParse(...)` round-tripped `connectors[0].confirmationsEnabled: true` once bumped to real published `10.1.0` — confirms the schema composition (`connectors: z.array(ConnectorRefDTOSchema)`) works end to end, not just in isolation.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- (none) — both increments verified, published, and confirmed working through the downstream consumer (config-service).

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
