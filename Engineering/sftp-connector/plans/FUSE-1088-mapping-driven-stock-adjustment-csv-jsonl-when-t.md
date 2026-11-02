---
ticket: FUSE-1088
title: Mapping-driven stock adjustment CSV/JSONL when the connector's mapping has
  rules
service: sftp-connector
status: complete
created: '2026-09-29'
updated: '2026-10-05'
repo: /home/hjf/code/fuse/sftp-connector
worktree: /home/hjf/code/fuse/sftp-connector/.claude/worktrees/fuse-1088-mapped
branch: hjf/fuse-1088-stock-adjustment-mapped-files
base: origin/master
base_sha: f6a15e32d
pr: '288'
tags:
- waypoint
- plan
programme: edi-support
unit: D3
---
# FUSE-1088 — Mapping-driven stock adjustment CSV/JSONL when the connector's mapping has rules

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
[FUSE-1088](https://gfsdeliver.atlassian.net/browse/FUSE-1088), last part: make the stock adjustment movement reference (Jitterbit's `EntityID`) and batch (`BatchID`, from-batch else to-batch) mappable for any customer's csv/jsonl stock adjustment file. When a connector's `stock_adjustment` mapping has at least one rule, its csv/jsonl file comes from those rules through `transformConfirmations` (defaults, dictionaries, csv `columnOrder`). A mapping with no rules keeps the fixed 15-column transformer output byte for byte. Types 10.8.0 carries `identifiers.movementRef`, `from/to.batchId`, `from/to.expiry`; the poller populates them in prod since 2026-09-29.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. A csv/jsonl connector whose stock_adjustment mapping has rules gets a file with exactly the mapped columns, including `EntityID` ← `identifiers.movementRef` and `BatchID` ← `if(from.batchId, from.batchId, to.batchId)`.
- [x] 2. A mapping with no rules produces a file byte-identical to master's fixed output (csv and jsonl).
- [x] 3. csv `columnOrder`, dictionaries and defaults are honoured on the mapped path.
- [x] 4. The EDI (INVRPT) stock adjustment path is unchanged.
- [x] 5. If the mapping rules can't be fetched, the connector is skipped with `no_mapping_rules` (confirmation-egress precedent); `stock_adjustment_made` is still emitted whenever a file is written.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `code/src/confirmations/stock-adjustment.service.ts` (target selection + serialisation)
- `code/src/core/confirmation-transformer.ts` (reused: `transformConfirmations`, `rowsToCsv`, `rowsToJsonl`; unchanged)
- Contract: customers' stock adjustment csv/jsonl file shape, now per-connector config when the mapping has rules

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- No active prod SFTP connector has a stock_adjustment mapping at all, so no prod file changes on deploy — prod audit 2026-09-29 (see Evidence).
- The mapped path honours `useDynamicConfirmationMapping` like confirmation egress; off → fixed output without fetching rules — design decision, flag is true in dev and prod.
- UNRESOLVED: the fuse-ui SFTP standard template seeds stock_adjustment with 15 rules that mirror the fixed column names but not its order or `TrnDate` format. A connector built from the template now gets mapped output (ISO `TrnDate` with ms/Z, rule-order columns, jsonl values as strings) instead of the fixed file. Update the template (`TrnDate` ← `substr(dates.closed, 0, 19)` + `columnOrder`), or accept? Raised with Harry.

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

- [x] 1. Mapped csv/jsonl stock adjustment output when the mapping has rules; fixed output otherwise; unfetchable rules skip with `no_mapping_rules` (AC 1,2,3,4,5) — verify: unit tests + goldens — 752 tests green incl. csv/jsonl goldens on the no-rules path — done: 9eddde7
- [x] 2. Dev e2e: rules connector gets mapped columns, no-rules connector byte-identical to master, made event emitted (AC 1,2,5) — verify: dev deploy + published batch + file diff — dev e2e: mapped csv on rules connector, no-rules csv byte-identical to master — done: 9eddde7

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-05 [sign-off] Re-read on `origin/master` (`648ee6e`), which includes squash `9eddde7`. `stock-adjustment.service.spec.ts` pins each AC:
  - AC 3: "orders the csv columns by the mapping's columnOrder", "maps through the mapping's dictionaries" and "fills a mapped column from the mapping's defaults".
  - AC 5: "records no_mapping_rules as the unroutable reason" for a csv connector whose rules can't be fetched.
  - AC 2: the no-rules path is pinned by the unchanged `stock-adjustment.{csv,jsonl}` goldens, plus the dev `cmp` above.
  - AC 4: #288 removed no spec line. Its only EDI-related source change widens the `StockAdjustmentTarget` union (`{ fileType } | EdiTarget` → `FileTarget | EdiTarget`). The EDI suite (envelope missing, dynamic mapping off, rules unfetchable, invalid INVRPT, edi + csv sharing a business) is intact. The FUSE-1253 plan has the dev INVRPT evidence.
  - AC 1 and AC 5's made event are proven live in dev (2026-09-29 bullet).
  - Guardrails: none breached. G2: the mapped path writes the same hourly window object through the same `upsertCsv`/`upsertJsonl` calls. G3: the prod audit found no prod SFTP connector with a `stock_adjustment` mapping, so no customer's file shape changed on deploy. The fuse-ui template gap is tracked as FUSE-1279.
- 2026-09-30 [prod] sftp-connector#288 squash `9eddde7` (with #289 trivyignore `ffcc499`), prod plan image-only + standing sidecar drift; both gates approved; revision `sftp-connector-prod-cr-00101-fj6` Ready. No prod connector has a stock_adjustment mapping, so prod output is unchanged. Template gap tracked as FUSE-1279.
- 2026-09-29 [inc 2] Dev e2e on `a886433` (revision `sftp-connector-dev-cr-00809-bkc`; plan 0/1/0, image only). Published 3 `CanonicalStockAdjustment` 10.8.0 records (SHOL both-batch, SADJ no-batch, SREC to-batch-only; fake SKUs, schema-validated) to `bifrost.dev.stock_adjustment_ready.v1` with gcloud, one hour-bucket per round.
  - Rules connector (GADG "Custom CSV", `FUSE_D89734E435`, dev mapping temporarily set to 6 rules + `columnOrder`): `EntityID,TrnDate,AccountID,ProductID,BatchID,Qty` / `0002_SHOL_SHOL1088001_L1088A,2026-09-29T13:05:00,GADG,FUSE1088-TEST-A,B1088-FROM,6` / `0002_SADJ_…,,2` / `0002_SREC_SREC1088003_L1088C,…,B1088-TO9,5`. Log `Stock adjustment file write started mapped:true`.
  - Same connector with its real no-rules mapping: csv byte-identical to master `f6a15e3`'s output for the same batch (`cmp` clean, sha256 `d811d8af54d6a90b…` both). Log `mapped:false`.
  - `stock_adjustment_made` emitted each round: collector logged `Stock adjustment confirmed` ×3 per correlationId.
  - Dev mapping restored exactly (PUT can't drop `columnOrder` because config-service's pipeline `$set` merges sub-objects, so DELETE + POST of the original `{simple, rules: [], defaults: []}`; re-read confirms). Dev returned to master (`00810-r6h`, `f6a15e3`).
  - Side finding: GADG "Primary SFTP" (`FUSE_4E7E60F55B`, jsonl) carries the fuse-ui template's 15 rules, so on the branch it switched from the fixed file to mapped output: `TrnDate` `2026-09-29T13:05:00.000Z` vs `2026-09-29T13:05:00`, rule-order keys, `"Moves_Qty":"6"` vs `6`, empty keys present. See UNRESOLVED.
- 2026-09-29 [inc 1] 752 unit tests green, biome lint exit 0, `tsc --noEmit` clean. Goldens `stock-adjustment.{csv,jsonl}` unchanged, now exercised through the no-rules mapping path.
- 2026-09-29 [gate] Prod audit, read-only via config-service `GET /connectors?type=sftp` (projection has no `config`) + per-use-case mapping GETs:

  | Prod SFTP connectors | with a `stock_adjustment` key | active + ≥1 rule |
  |---|---|---|
  | 28 (all active) | 0 | 0 |

  The spot-checked mapping GETs return 404 (PURDYFIGG, STUBBLE, KAPPAHL, SPORTLUX). Prod logs agree: PURDYFIGG stock adjustments evaluate `present:false`, so no prod SFTP stock adjustment file is written today. Gate clear. `egressFiletype` wasn't read, because it lives only on the auth-bearing connector GET, and with zero mappings it doesn't matter.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- Dev jsonl on a rules connector with EntityID/BatchID: only the template-rules jsonl was exercised live. The EntityID/BatchID jsonl shape is covered by unit tests.
- `no_mapping_rules` skip: unit-tested only.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-09-29** — Unfetchable mapping rules skip the csv/jsonl connector with no_mapping_rules rather than falling back to fixed output: matches confirmation egress and the EDI stock adjustment path, and a customer who configured rules never gets a file in the wrong shape. Mapped path also respects useDynamicConfirmationMapping (off = fixed, no fetch).

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
