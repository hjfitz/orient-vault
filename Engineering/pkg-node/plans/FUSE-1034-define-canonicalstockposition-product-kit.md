---
ticket: FUSE-1034
title: Define CanonicalStockPosition (product | kit)
service: pkg-node
status: complete
created: '2026-09-17'
updated: '2026-10-05'
repo: /home/hjf/code/fuse/pkg-node
worktree: /home/hjf/code/fuse/pkg-node/.claude/worktrees/fuse-1034-canonical-stock-position
branch: hjf/fuse-1034-canonical-stock-position
base: origin/main
base_sha: 57b1a574b
pr: https://github.com/gfs-bifrost/pkg-node/pull/227
tags:
- waypoint
- plan
impl_model: sonnet
impl_effort: low
---
# FUSE-1034 — Define CanonicalStockPosition (product | kit)

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
Define `CanonicalStockPosition` — a discriminated union on `type: "product" | "kit"` — and its
matching `CanonicalStockPositionSchema` in `@gfs-bifrost/types`. This is the foundational v2
(canonical) shape a later "Get Stock API" (FUSE-792) will return; kits and regular stock are
distinct entities in Snap and must be surfaced as distinct canonical types, not one shape with
optional fields. Observable outcome: the type and schema are exported with a minor version bump,
`@gfs-bifrost/types` builds clean, and every in-workspace dependent package still builds against
it.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. `CanonicalStockPosition` and `CanonicalStockPositionSchema` are exported from
  `@gfs-bifrost/types`, with the package's version bumped 10.1.0 → 10.2.0 (minor).
> SUPERSEDED 2026-09-17 — three corrections, latest first: (3) the quantity/date fields below are
> flat, the real implementation nests them to match the fleet's namespaced-field convention —
> `product.quantities?: {onHand,allocated,orderOut,dueIn}`, `kit.dates?: {effective,closed}` (see
> the 2026-09-17 "Restructured" Decisions & deviations entry); (2) field names below are Snap's
> raw casing, the real implementation used camelCase before the quantities nesting; and (1)
> "nothing else" on the kit branch is no longer true — it also carries an optional
> `kit?: CanonicalKit` (bill of materials). See all three 2026-09-17 Decisions & deviations
> entries.
- [x] 2. `type` discriminates `"product"` vs `"kit"`: the `product` branch carries `quantities`
  (`onHand`/`allocated`/`orderOut`/`dueIn`); the `kit` branch carries `potentialKitQty` and a
  `kit?: CanonicalKit` bill of materials.
- [x] 3. `@gfs-bifrost/types` builds clean, and every in-workspace package depending on it
  (`rules-engine`, `pubsub`, `remote-config`) builds clean against the new export. (fapi cannot
  be exercised in this PR — see UNRESOLVED below.)

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `pkg/types/src/canonical/types/stock-position.types.ts` (new) — the canonical type.
- `pkg/types/src/canonical/schemas/stock-position.schema.ts` (new) — the Zod schema.
- `pkg/types/src/canonical/types/product.types.ts` (new) — `CanonicalProduct`, split out of
  `master-data.types.ts` so it's a first-class type both `CanonicalMasterData` and
  `CanonicalStockPosition` compose from, not a master-data-owned shape.
- `pkg/types/src/canonical/schemas/product.schema.ts` (new) — `CanonicalProductSchema`, same
  split on the schema side.
- `pkg/types/src/canonical/types/kit.types.ts` (new) — `CanonicalKit`/`CanonicalKitComponent`,
  a kit's bill of materials, grounded in Snap's real `snapKit` entity fields, including matching
  its mandatory-field shape (`unit` required on both, not optional — cross-checked 2026-09-17).
- `pkg/types/src/canonical/schemas/kit.schema.ts` (new) — `CanonicalKitSchema`/
  `CanonicalKitComponentSchema`.
- `pkg/types/src/canonical/types/master-data.types.ts`,
  `pkg/types/src/canonical/schemas/master-data.schema.ts` — now reference `CanonicalProduct`/
  `CanonicalProductSchema` instead of owning the inline product shape.
- `pkg/types/src/canonical/types/index.ts`, `pkg/types/src/canonical/schemas/index.ts` — barrel
  re-exports.
- `pkg/types/package.json` — version bump.
- `/home/hjf/code/CLAUDE.md` — Package Changelog entry for `@gfs-bifrost/types` (org contract,
  not this vault).
- `fuse-mcp-server/data/canonical-types.json` — a new canonical type should be reflected there
  per the org's own MCP-maintenance contract; **cross-repo, explicitly not part of this PR's
  diff** — flag as a follow-up when this ships.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- The `kit` branch does not mirror the raw per-record quantity fields Snap's own
  `SnapStockTotalKit` entity also carries (`Qty`/`QtyAllocated`/etc.) — a kit's real
  availability is `potentialKitQty` (derived), not raw kit-record bookkeeping. It does carry an
  optional `kit?: CanonicalKit` (2026-09-17, per Harry: "export more kit data") — the bill of
  materials, grounded in Snap's real `snapKit` entity fields
  (`ProductKitId`/`Unit`/`ComponentSKUID`/`Qty`/`ComponentSKUUnit`/`DateEffective`/`DateClosed`/
  `MaintInd`) and modelled after `CanonicalWorkOrderLine`'s COMPONENT-role convention, though
  distinct from it: a work order line describes one instance of building a kit, `CanonicalKit`
  describes the kit's recipe itself.
- Product attributes are represented by `CanonicalProduct`/`CanonicalProductSchema` — a
  first-class canonical concept split out into its own `product.types.ts`/`product.schema.ts`
  (2026-09-17, per Harry's review) that both `CanonicalMasterData` and `CanonicalStockPosition`
  compose from — rather than a new bespoke field list or a dynamic custom-fields bag. Established
  by grepping the whole `canonical/` directory for an existing custom-fields convention (none
  exists) and finding the extracted product shape already canonicalizes every `SnapProduct`
  field the ticket could plausibly mean.
- Only the four Snap quantity fields the ticket names verbatim (`Qty`/`QtyAllocated`/
  `QtyOrderOut`/`QtyDueIn`) are included on the product branch, not the full `SnapStockTotal` set
  (`QtyAssigned`/`QtyOrderIn`/`QtyDueOut`/`StockLevelIndicator`/`DateLastMoved`) — established by
  the ticket naming exactly these four, twice, in both its technical description and AC2; read as
  a deliberate curation for this v2 canonical (vs. v1 lift-and-shift) shape, not an oversight.
  Additive, non-breaking to widen later once a real consumer needs more.
- UNRESOLVED: AC3 as literally worded ("a consuming build (fapi) type-checks against the new
  export") is not achievable inside this PR. fapi's `code/package.json` pins
  `"@gfs-bifrost/types": "^9.5.0"` (confirmed, and its lockfile resolves exactly `9.5.0`).
  `@gfs-bifrost/types` went through a breaking `10.0.0` bump (FUSE-1164, "require customer
  reference on SO, RGA, and WO") that fapi has never absorbed — a caret range never resolves
  across a major boundary, so bumping to `10.2.0` here changes nothing fapi's own install
  resolves, regardless of this PR's diff. Getting fapi onto `@gfs-bifrost/types@^10.x` is separate
  work in the `fapi` repo, itself blocked on fapi absorbing the unrelated FUSE-1164 breaking
  change first. This plan instead proves the new export type-checks against every in-workspace
  `pkg-node` consumer this PR can actually reach (Increment 3). Needs a call from Harry: accept
  this narrower reading of AC3 for this ticket, or open a tracked follow-up ticket for fapi's
  `types` major-version adoption and reference it here.

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

- [x] 1. **Add the `CanonicalStockPosition` type** (AC 2). New file — tsc --noEmit clean; discriminated-narrowing check confirmed both directions (kit hides Qty, product hides potentialKitQty) via a scratch @ts-expect-error test — done: fd05a62
  `pkg/types/src/canonical/types/stock-position.types.ts`: `CanonicalStockPositionProduct`
  (`type: "product"`, optional `Qty`/`QtyAllocated`/`QtyOrderOut`/`QtyDueIn`, optional
  `product?: CanonicalMasterData["product"]`), `CanonicalStockPositionKit` (`type: "kit"`,
  optional `potentialKitQty`), and the union `export type CanonicalStockPosition =
  CanonicalStockPositionProduct | CanonicalStockPositionKit`. Wire into
  `pkg/types/src/canonical/types/index.ts`'s `export *` barrel. — verify:
  `pnpm --filter @gfs-bifrost/types exec tsc --noEmit` passes; a scratch discriminated-narrowing
  check compiles clean (narrowing on `type === "kit"` exposes `potentialKitQty` and rejects the
  Qty fields, and vice versa for `"product"`).

- [x] 2. **Add `CanonicalStockPositionSchema`** (AC 1,2). New file — pnpm --filter @gfs-bifrost/types run build clean; lint:fix clean; 63/63 existing tests still pass (no regression from the master-data.schema.ts extraction) — done: b218669
  `pkg/types/src/canonical/schemas/stock-position.schema.ts`: a `z.discriminatedUnion("type",
  [...])` mirroring `ingest-capture.schema.ts`'s pattern, typed
  `z.ZodType<CanonicalStockPosition>` per the `stock-adjustment.schema.ts`/`master-data.schema.ts`
  convention. Requires a small, additive change to
  `pkg/types/src/canonical/schemas/master-data.schema.ts`: extract its existing inline
  `product: z.object({...})` into its own named, exported `CanonicalMasterDataProductSchema`
  const, referenced both by the existing `CanonicalMasterDataSchema` (unchanged behaviour) and by
  the new stock-position schema. This extraction is necessary, not stylistic:
  `CanonicalMasterDataSchema.shape.product` does **not** type-check as originally planned —
  confirmed by a direct `tsc` compile — because `CanonicalMasterDataSchema` is exported typed as
  `z.ZodType<CanonicalMasterData>`, and `.shape` isn't part of `ZodType`'s surface, only the
  concrete `ZodObject`'s, so it's inaccessible once that widening annotation is applied. Wire the
  new schema into `pkg/types/src/canonical/schemas/index.ts`'s barrel. — verify:
  `pnpm --filter @gfs-bifrost/types run build` (tsc) succeeds — no unit test, per the ticket's own
  instruction ("tests the library, not our code"); same evidence standard as
  `stock-adjustment.schema.ts`/`master-data.schema.ts`, neither of which has a spec file either.

- [x] 3. **Version bump, changelog, and dependent-build verification** (AC 1,3). Bump — types@10.2.0 build clean; rules-engine/pubsub/remote-config all build clean against it; 10.2.0 confirmed unpublished (latest on GitHub Packages is 10.1.0) so the publish workflow will fire on merge — done: 41b95da
  `pkg/types/package.json` 10.1.0 → 10.2.0 (minor — additive export only, nothing existing
  changes shape). Add a `10.2.0` entry to `/home/hjf/code/CLAUDE.md`'s Package Changelog →
  `@gfs-bifrost/types` section, directly after the existing `10.1.0` entry (that changelog is
  current through 10.1.0/FUSE-1167 already, including a self-noted gap for the intervening
  10.0.0/FUSE-1164 major — this increment is not catching up a stale doc, just appending the next
  real entry). — verify: `pnpm --filter @gfs-bifrost/types run build` succeeds;
  `pnpm --filter rules-engine --filter pubsub --filter remote-config run build` (every
  in-workspace package depending on `types`) all exit 0, proving the new export type-checks
  against every consumer this PR can actually reach; confirm `10.2.0` isn't already published so
  the publish workflow fires on merge.

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-09-17 [inc 3] `pnpm --filter @gfs-bifrost/types run build` → clean (tsc, version 10.2.0).
  `pnpm --filter @gfs-bifrost/rules-engine|@gfs-bifrost/pubsub|@gfs-bifrost/remote-config run
  build` → all three clean against the new export (AC3, scoped to in-workspace consumers).
  `npm view @gfs-bifrost/types versions` → latest published is `10.1.0`, confirming `10.2.0`
  isn't already published and the publish workflow will fire on merge (AC1).
- 2026-09-17 [inc 2] `pnpm --filter @gfs-bifrost/types run build` and `run lint:fix` both clean;
  `pnpm --filter @gfs-bifrost/types run test` → 63/63 existing tests still pass, confirming the
  `master-data.schema.ts` extraction (`CanonicalMasterDataProductSchema`) didn't regress
  `CanonicalMasterDataSchema`'s existing behaviour.
- 2026-09-17 [inc 1] `pnpm --filter @gfs-bifrost/types exec tsc --noEmit` → clean. A scratch
  discriminated-narrowing file confirmed both directions compile-error correctly: on the `kit`
  branch, accessing `Qty` is a real `tsc` error (`Property 'Qty' does not exist on type
  'CanonicalStockPositionKit'`); on the `product` branch, accessing `potentialKitQty` errors the
  same way — proving AC2's discrimination is real, not just declared.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- AC3 against the real fapi build — fapi is pinned below the major this bump ships in; see the
  UNRESOLVED entry above. Would be proven by a separate fapi-repo PR bumping
  `@gfs-bifrost/types` to `^10.x` once fapi has absorbed the FUSE-1164 breaking change.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-09-17** — Added per-field JSDoc to CanonicalStockPosition/CanonicalKit/CanonicalProduct (+ CanonicalKitComponent) per Harry's DX ask — every field documents what it represents, visible on hover, instead of requiring a trip to the Snap wire types or this PR to understand a field.

- **2026-09-17** — Restructured CanonicalStockPosition and CanonicalKit to match sibling canonical types' namespaced-field convention: StockPositionProduct's flat qty/qtyAllocated/qtyOrderOut/qtyDueIn now nest under quantities:{onHand,allocated,orderOut,dueIn}; CanonicalKit's dateEffective/dateClosed now nest under dates:{effective,closed} — mirrors CanonicalStockAdjustment.quantities/.dates exactly, prefix dropped inside the namespace. User caught the flat shape didn't match the fleet's flavour; confirmed by direct precedent check before restructuring.

- **2026-09-17** — Harry asked to cross-check optionality against Snap's real mandatory fields. Re-read all four Snap wire types fresh: SnapKit.Unit/ComponentSKUUnit are both mandatory (no ?), but CanonicalKit.unit/CanonicalKitComponent.unit had been left optional -- fixed to required on both type and schema (Zod min(1)). Everything else already matched: SnapStockTotal's Qty/QtyAllocated/QtyOrderOut/QtyDueIn are all optional (matches CanonicalStockPositionProduct), SnapProduct's SKUId/BizId/Description are the only mandatory fields (matches CanonicalProduct.identifiers.skuId/.businessId/.information.description already being required, not optional), and SnapStockTotalKit.PotentialKitQty is optional (matches potentialKitQty?). Re-verified: tsc/narrowing/build/lint/test (63/63)/dependent-builds all clean.

- **2026-09-17** — Scope expansion per Harry: export more kit data than potentialKitQty alone. Added CanonicalKit
(+ CanonicalKitSchema) in new kit.types.ts/kit.schema.ts -- the kit's bill of materials (kitId,
unit, components: CanonicalKitComponent[] with skuId/qty/unit each, dateEffective, dateClosed,
maintenanceIndicator), grounded directly in Snap's real snapKit entity fields
(ProductKitId/Unit/ComponentSKUID/Qty/ComponentSKUUnit/DateEffective/DateClosed/MaintInd -- one
row per component in Snap, collapsed here into one kit with a components array). Distinct from
CanonicalWorkOrderLine's COMPONENT/FINISHED_GOOD role lines (an instance of building a kit) --
this is the kit's recipe/definition itself. CanonicalStockPositionKit gains an optional
`kit?: CanonicalKit` field alongside the existing potentialKitQty, mirroring how
CanonicalStockPositionProduct carries `product?: CanonicalProduct` alongside its Qty fields --
keeps both branches structurally symmetric. Re-verified: tsc clean, discriminated-narrowing
check (extended to cover kit.components access + kit invisible on the product branch) still
passes, build/lint/test (63/63) all clean, all three in-workspace dependents still build clean.

- **2026-09-17** — Amended after Harry's review of PR #227, two real catches: (1) CanonicalStockPositionProduct's
Qty/QtyAllocated/QtyOrderOut/QtyDueIn were left in Snap's raw PascalCase (copied verbatim from
the ticket text, which itself just names the real Snap wire fields) instead of this codebase's
camelCase canonical convention -- inconsistent even within the same type against
potentialKitQty. Renamed to qty/qtyAllocated/qtyOrderOut/qtyDueIn. (2) The product-attributes
reuse (Increment 2) extracted CanonicalMasterDataProductSchema as a master-data-owned export --
better to make "product" a first-class canonical concept both CanonicalMasterData and
CanonicalStockPosition compose from equally. Split into new pkg/types/src/canonical/types/
product.types.ts (CanonicalProduct) + .../schemas/product.schema.ts (CanonicalProductSchema);
master-data.types.ts/master-data.schema.ts now just reference them instead of owning the shape.
Re-verified: tsc clean, discriminated-narrowing check still passes with the new field names,
build/lint/test (63/63) all clean, and all three in-workspace dependents (rules-engine, pubsub,
remote-config) still build clean.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->

## Handback
- 2026-10-05 [sign-off] Promoted the `z.ZodType<T>`-hides-`.shape` learning to
  `architecture.md` → Gotchas. Re-checked on `origin/main`: it applies to nearly every canonical
  schema, not just `stock-adjustment.schema.ts`.
- 2026-10-05 [sign-off] Not promoted: "`architecture.md`/`overview.md` are flagged STALE but
  haven't drifted; re-anchor them at sign-off". That described the docs on 2026-09-17, not the
  service, and it has since been handled. Both docs are now anchored at `3d79938`, after this PR,
  and `architecture.md`'s packages table already lists product/kit/stock-position. On 2026-10-05,
  `wp stale pkg-node` shows them 2 and 1 commits behind, from later unrelated PRs (#260, #261).
- 2026-10-05 [sign-off] Still owed outside this plan: `CanonicalStockPosition` is not in
  fuse-mcp `data/canonical-types.json` on `master` (checked through the GitHub API today).
  Affected boundaries named this as a follow-up.
