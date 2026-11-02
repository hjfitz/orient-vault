---
ticket: FUSE-1254
title: Adopt types 10.x and reject records without a customer reference
service: sftp-connector
status: complete
created: '2026-09-24'
updated: '2026-09-24'
repo: /home/hjf/code/fuse/sftp-connector
worktree: /home/hjf/code/fuse/sftp-connector/.claude/worktrees/fuse-1254
branch: hjf/fuse-1254-types-10
base: c0678bac2465f651970d2a584b8d6af87a6ef451
base_sha: c0678bac2
pr: '283'
tags:
- waypoint
- plan
programme: "edi-support"
unit: "R2"
---
# FUSE-1254 — Adopt types 10.x and reject records without a customer reference

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
[FUSE-1254](https://gfsdeliver.atlassian.net/browse/FUSE-1254). Move sftp-connector from `@gfs-bifrost/types` `^9.5.0` to `^10.4.0`, where the customer reference is required on sales orders (`order.customerRef`), work orders (`workOrder.customerRef`) and returns (`identifiers.businessRgaNumber`). A record whose mapping supplies no reference must fail canonical validation at ingest and route to `error/` like any other validation failure — never padded with `""`, which since FUSE-1166 collides in dedupe (the failure mode that closed sftp-connector#268). At the same time, retire the FUSE-1253 local mirrors of the SFTP EDI config shapes in favour of the shared 10.4.0 ones, keeping the lenient envelope read.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. sftp-connector builds and tests against types 10.4.0 (tsc, lint, vitest green).
- [x] 2. A sales order / work order / return with no customer reference is rejected as a validation failure naming the missing path; no placeholder is invented anywhere.
- [x] 3. Every active prod SFTP connector with a sales-order (and work-order / RGA) ingress mapping is re-audited as mapping the reference.
- [x] 4. Dev ingest for each active dev SFTP customer processes as before (with-ref ingests, no-ref routes to `error/`, EDI inbound still ingests, confirmation egress still writes).
- [x] 5. The local EDI config mirrors are replaced by the shared shapes; a malformed or blank-party `ediEnvelope` still reads as absent and never stops ingest.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `code/src/factories/canonical/{sales-order,work-order,return-goods-authorization}.factory.ts` — skeleton types without the reference
- `code/src/import/translators/*` — validation sites (unchanged code, new behaviour via the schema)
- `code/src/config/{schema,types}.ts`, `config.api.ts`, `confirmations/confirmation-egress.service.ts`, `confirmations/edi/build-edi-files.ts`, `types/confirmations/operations.ts` — EDI mirrors
- `tests/` black-box: minimum sales-order fixture + golden md5
- Contract: `create_record_request` (records now always carry a real reference); dedupe keys on it

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- A blank reference column does not produce `""`: the rules engine drops empty values, so the field is absent and validation fails — established by unit test (sales-order spec, blank `customer_ref`) and consistent with the existing work-order "missing customer_id" test. This is stronger than the ticket expected ("present but blank still produces an empty string"); a rule/default that yields a non-empty constant still passes, and `""` only survives if a default sets it.
- RGA confirmations are also validated against `CanonicalReturnGoodsAuthorizationSchema` on egress; the producer (snap-queue-polling-service, on types ^10.4.0) sets `businessRgaNumber: receipt.SupplierRef ?? receipt.ReceiptId` — source read, snap-adapter origin/HEAD.
- Only the three canonical schemas tightened between 9.5.0 and 10.4.0 (diff of the published dist); confirmation schemas otherwise unchanged apart from additive exports.

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

- [x] 1. Bump types to ^10.4.0; factories return skeleton types without the reference; test fixtures carry one; rejection tests for all three translators; black-box minimum fixture gets `AccountID`/`OrdRef1` and a recomputed golden (AC 1,2) — verify: tsc/lint/vitest; probe reproduces old golden then new — tsc/lint 0; vitest 679/679; probe reproduced old golden 1d7eaccf then new cc1815a1 — done: 30871dc
- [x] 2. Replace the local EDI mirrors with shared `EgressFiletype` / `SFTPEdiEnvelope` / `SFTPIngressSchema`, keeping envelope leniency via a preprocess wrapper (AC 1,5) — verify: connector-handler specs incl. blank-party envelope (mutation-checked) — blank-party envelope test mutation-checked — done: 30871dc
- [x] 3. Prod audit of SFTP ingress mappings for the reference path (AC 3) — verify: table from config-service prod, auth stripped — 26/26 prod SFTP SO map OrdRef1; no WO/RGA mappings — done: 30871dc
- [x] 4. Dev deploy + ingest checks (AC 4) — verify: logs/GCS routing per check, revision sha — a-d verified on dev-cr-00797; reverted to master — done: 30871dc

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-09-24 [prod] Shipped with #282+#283 as `30871dc` (Harry: "ship 282 and 283"); prod plan image-only + standing sidecar drift; both gates approved; revision `sftp-connector-prod-cr-00097-gpl` Ready. 19:03–19:27Z on it: 6 STUBBLE sales-order validations 0 invalid, 2 confirmations written + processed, no warn/error.
- 2026-09-24 [inc 4] Dev branch image `91371aa` (revision `sftp-connector-dev-cr-00797-wtd`; plan = image + standing sidecar env drift, 0/1/0). Drops at 18:24:53Z:
  - (a) with-ref sales orders re-dropped from each business's last dev SO: GADG `FUSE_4E7E60F55B` csv, EPARFUM `FUSE_BF827F7E3E`, SAMMCK `FUSE_747B622494` → `Records validated` 1/0 → emitted. dedupe dropped GADG/EPARFUM as duplicates of the originals (keyed on the real ref); SAMMCK passed dedupe and failed in SNAP → `error/`, same as its original. GADG RGA jsonl → 1/0, emitted, dedupe duplicate.
  - (b) GADG SO with `OrdRef1` blanked → `Records validated` 0/1, warn `Records failed CSV validation` sampleError `order.customerRef: Invalid input: expected string, received undefined` → `Validation failures published` → `File routed` destination `error`. Nothing reached create_record_request/dedupe.
  - (c) HJF `FUSE_4366B07EED` INSDES `.edi` → 1/0, emitted (dedupe duplicate of the original).
  - (d) GADG goods-in (`mock-fuse1254-regression`, `recordType=purchase_order`, `broadcast=true`) → `FUSE_167F5C016A` + `FUSE_D89734E435` CSV and `FUSE_4E7E60F55B` JSONL `purchase_order_confirmations/2026-09-24-1825-confirmation.*` at 18:25:17Z.
  - Only warns on the revision: the expected (b) pair and one `File routing deferred to an in-flight claim`. Test copies left in `to_ilg/` by dedupe holds were removed. Dev reverted to master `a7fcb13` (`sftp-connector-dev-cr-00798-jds`).
- 2026-09-24 [inc 3] Prod audit (config-service prod, storefront mapping endpoints only, no connector GETs): 31 connectors / 29 businesses. 26 SFTP `sales_order` mappings, all active, all map `order.customerRef` from `OrdRef1` (+2 Shopify connectors mapping `name`). 0 `work_order` and 0 `return_goods_authorization` mappings in prod. ACADEMIC, BFA (SFTP) and PURDYFIGG API have no ingress mapping of the three. Nothing MISSING.
- 2026-09-24 [inc 1,2] Local: tsc 0, lint 0, vitest 39 files / 679 tests. Probe over the black-box CSVs with the real translator + customerx config reproduced old golden `1d7eaccf` exactly (9.5.0 schema), then new `cc1815a1` for the minimum fixture with AccountID/OrdRef1.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- Black-box docker suite not run locally (other sessions' containers occupy the shared names/ports); CI runs it on the PR.
- DAZZA's empty-rule-set staging connector was not exercised (expected to reject).
- A mapping that sets `order.customerRef` via a `""` default would still pass; none exists in prod (audit), and the non-empty rule is the types follow-up.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-09-24** — Black-box 'Sales Order - Minimum provided fields' fixture gains AccountID+OrdRef1 rather than being left to publish nothing: the harness does not fail on a count shortfall, so the case would pass vacuously. OrdRef1 alone isn't enough: mapping identifiers.id replaces the factory identifiers block (shallow assign), so businessId must be mapped too.

- **2026-09-24** — EDI envelope leniency kept as a thin preprocess around the shared SFTPIngressSchema: an envelope that fails SFTPEdiEnvelopeSchema, or has a blank party, is dropped before the parse. The shared schema is strict and has no min(1); the old local mirror had both, so the blank-party refine preserves behaviour (a blank UNB party would be written unvalidated by @gfs-bifrost/edi).

- **2026-09-24** — Factories return skeleton types (Omit the reference) instead of emitting a placeholder: the reference can only come from the mapping, so an unmapped record fails validation at ingest. Rejected: "" placeholders (#268; dedupe collision), DeepPartial (loses the rest of the skeleton's typing).

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
