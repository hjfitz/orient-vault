---
ticket: FUSE-1253
title: Accept egressFiletype edi and ediEnvelope on SFTP connectors
service: config-service
status: complete
created: '2026-09-24'
updated: '2026-09-24'
repo: /home/hjf/code/fuse/config-service
worktree: /home/hjf/code/fuse/config-service/.claude/worktrees/edi-egress
branch: hjf/fuse-1253-edi-egress
base: origin/main
base_sha: 687493f7b
pr: '226'
tags:
- waypoint
- plan
impl_model: sonnet
impl_effort: medium
programme: "edi-support"
unit: "E4"
---
# FUSE-1253 — Accept egressFiletype edi and ediEnvelope on SFTP connectors

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
[FUSE-1253](https://globalfreight.atlassian.net/browse/FUSE-1253). config-service accepts `egressFiletype: "edi"` on SFTP connectors, along with an `ediEnvelope` block that is required when the type is `edi`. It validates and persists both, returns them on GET, and never resets them on an unrelated PATCH. The shape comes from [[edi-0-5-0-interchange-envelope-types-ediegress-o]]. This work is the precondition for verifying [[edifact-confirmation-egress-desadv-recadv-behind]] in dev and for [[edifact-egress-option-on-the-sftp-connector-form]].

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. A PATCH with `egressFiletype: "edi"` and a full `ediEnvelope`, followed by a GET, returns both unchanged.
- [x] 2. A PATCH without either field (e.g. `{type, isActive}`) leaves both intact. A partial `ediEnvelope` PATCH keeps the fields it didn't send.
- [x] 3. Validation runs on the **merged** document and returns 400 in each of these cases:
  - `edi` with no envelope;
  - a missing, empty or longer-than-35-character sender or receiver id;
  - a qualifier outside `14`/`91`/`ZZ`.
- [x] 4. `openapi.yaml` documents `edi` and `ediEnvelope` on both `SFTPIngress` and `UpdateSFTPIngress`, and the fuse-mcp `config-domain.json` describes them.
- [x] 5. `csv`/`jsonl` connectors read and write exactly as before.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `connector.base.schema.ts:117-139` (SFTPIngress), `connector.update.schema.ts:11-20` (UpdateSFTPIngress), the response schema, and `connector.create.types.ts`: each has its own `egressFiletype` enum, and all of them need `edi`.
- `connector.update.types.ts:9-16`, which also lacks `egressFiletype`.
- `openapi.yaml`: `UpdateSFTPIngress` (~`:1683`, `additionalProperties: false`) and `SFTPIngress` (~`:1846`).
- `storefront.service.ts:692` `mergePartialUpdate`.
- `code/scripts/backfill-egress-filetype.ts` is a historical FUSE-671 backfill. Leave it alone; just check it doesn't assume a closed set.
- `fuse-mcp-server/data/config-domain.json`, which goes straight to master.
- Explainers: [[known-context]], covering the base/update/response/openapi footgun.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- **Merging this deploys prod, and prod then accepts `edi`.** So sftp-connector plan increment 1 (which tolerates `edi` on ingest) must already be in prod. Otherwise saving `edi` breaks that connector's ingest.
- **`mergePartialUpdate` is a lodash `mergeWith` deep merge.** It can't unset a key and it replaces arrays, so `ediEnvelope` can be changed but never removed. A connector switched back to `csv` keeps its inert envelope. Established by source read.
- **The PATCH body is validated with defaults applied before the merge, and those defaults are persisted.** `stockAdjustmentsEnabled` already defaults to false this way. So `ediEnvelope` gets **no `.default()`**, and fuse-ui must keep resending `stockAdjustmentsEnabled`, which is an existing trap.
- **There is no OpenAPI request validator.** `additionalProperties: false` only affects the docs and fuse-ui codegen.
- **Decision: the "simple configType can't be EDI" rule lives in sftp-connector at runtime.** A save-time check here can't see a mapping edited later.
- **Coordinate with the active "generated OpenAPI as single source of truth" plan** (PR #215, part 1/2). Check its status at implementation.

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
- [x] 1. Add `edi` to every `egressFiletype` enum here, plus `ediEnvelope` on the base, update and response schemas, the DTO types and both openapi entries, with post-merge validation and no defaults. (AC 1,2,3,4,5) — verify: specs for each 400 case and for preservation; after the dev deploy from main, a PATCH/GET round trip on the HJF test connector, a `PATCH {type,isActive}` that preserves both fields, a partial-envelope PATCH, malformed values that return 400, and a dev SFTP ingest on the `edi` connector that still processes. — done: 1c76c28
      gate: types minor published (pkg-node increment 7) AND sftp-connector increment 1 in prod
            [x] confirmed
      gate: fapi AND shopify-connector deployed to prod on @gfs-bifrost/types >=10.4.0. remote-config's connector backlink refresh is not type-filtered, so an older consumer throws on an `edi` SFTP connector's revision event, and fapi's config-event handler awaits it, which means a 500, nack and endless redelivery
            [x] confirmed
- [x] 2. Update the fuse-mcp `config-domain.json` SFTP connector entry with `edi`, `ediEnvelope` and its validation rules, as a scoped commit to master. (AC 4) — verify: `lookup-config sftp` on the hosted MCP returns it after the deploy. — done: 1c76c28

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-09-24 [inc 2] fuse-mcp `data/config-domain.json` updated with `edi` + `ediEnvelope` rules, the validation behaviour and the remote-config consumer requirement. Pushed to fuse-mcp master as `25ee525`.
- 2026-09-24 [inc 1] Dev, config-service `1aef7bc` (same as prod), HJF test connector `conn_1435ca939ecb4c65b728fb0888aae7eb`:
  - PATCH `egressFiletype: edi` with no envelope → 400 `ediEnvelope is required when egressFiletype is 'edi'`.
  - PATCH with qualifier `BAD` → 400 `expected one of "14"|"91"|"ZZ"`.
  - Full envelope → 200, stored.
  - Partial PATCH `{ediEnvelope:{receiverId}}` → 200: the other envelope fields are kept, and the omitted `egressFiletype` stays `edi`.
- 2026-09-24 [inc 1] Downstream in dev:
  - fapi (`api-gateway-dev`) and shopify-connector both refreshed the `edi` connector's two revision events with `202` (no 5xx, no validation errors), so there's no redelivery loop.
  - sftp-connector (`91cfc5c`) still ingested HJF INSDES `edi-conn-145850.edi` → archived.
  - A HJF receipt confirmation logged `Connector egresses EDIFACT, which this deployment does not write — no file written`.
- 2026-09-24 [inc 1] Unit 688/688, integration 360 pass / 15 skip; build:check and build:check:tests clean (config-service#226).

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- (none) — the fuse-ui form round-trip is the fuse-ui plan's.

## Rollout & rollback
<!-- Added on demand. Written at plan time; amend in place as it changes.
     `Shared state touched:` is the single home for the five classes git does not own — a dev
     deploy, a prod config write, a Datadog monitor, a CI var or secret, cross-repo IaC. Reverting
     the branch undoes none of them, so if they are not written here they are not written down. -->
- **Order:** the types minor is published, sftp-connector increment 1 is in prod, **and fapi + shopify-connector are on types >=10.4.0 in prod** (see the increment 1 gate), then this service merges (which deploys prod), then fuse-ui ([[edifact-egress-option-on-the-sftp-connector-form]]). fuse-ui regenerates its client from **dev deployed from main**, not from a branch deploy.
- **Flags/config:** none here. Until sftp's flag is on, an `edi` connector writes nothing and reports why.
- **One-way doors:** none. A stored `ediEnvelope` can't be removed through the API, only left unused.
- **Rollback:** git revert. Before reverting, set any connector already on `edi` back to `csv`, because the old schema rejects `edi` on PATCH.
- **Shared state touched:** a dev deploy; dev config writes on the HJF test connector; a push to fuse-mcp master (which redeploys the hosted MCP).
- **Proof in prod:** n/a until FUSE-1256.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-09-24** — Source vs plan: the response schema and update schema reuse the types enum (only connector.base.schema.ts had its own); openapi.yaml is no longer served since #215 (Nest generates the spec) but is still hand-edited until fuse-ui codegen moves; an ediEnvelope, when present, is validated even on csv connectors (deliberate tightening). Implemented in config-service#226; dev verification waits for fapi#147/shopify-connector#282 in dev.

- **2026-09-24 (Harry)** — INVARIANT: the EDI egress path is customer-agnostic, and Charlotte Tilbury is config, not code. No serializer, assembly step, dispatch table or UI rule may branch on, or hardcode, a customer or partner. Every partner-varying value (association code, BGM document code, NAD/RFF/QTY/DTM qualifiers, INV/STS codes, envelope IDs) is caller- or config-supplied, with an EANCOM D.96A default. CT's sample files are conformance tests driven by a CT config fixture. The type-to-message mapping follows EANCOM practice and Snap's resource model (S10 work-order shipment, R10 finished-goods receipt), not CT.

- **2026-09-24 (Harry)** — Config shape switched from a separate ediEgress block to egressFiletype "edi" + an ediEnvelope block (Harry's call). A cross-repo grep showed only types, config-service, fuse-ui and sftp-connector read egressFiletype, and remote-config consumers only resolve their own connector type, so the enum-widening hazard is confined to sftp-connector and handled by ordering (sftp increment 1 in prod first). Types with no EDIFACT message write nothing and report why, and the UI warns which types they are; an edi connector never falls back to CSV.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
(none)

