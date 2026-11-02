---
ticket: none
title: Business index returns connector useCases
service: config-service
status: complete
created: '2026-10-01'
updated: '2026-10-05'
repo: /home/hjf/code/fuse/config-service
worktree: /home/hjf/code/fuse/config-service/.claude/worktrees/broadcast-terminal-outcome
branch: hjf/broadcast-terminal-outcome
base: origin/main
base_sha: d58dc5527
pr: '235'
tags:
- waypoint
- plan
programme: poller-clear-down
unit: E1
impl_model: sonnet
impl_effort: low
---
# none — Business index returns connector useCases

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
Part of [[Poller Clear-Down/Migration State|Poller Clear-Down]] unit **E1** (no ticket). `GET /api/v1/business`
returns each connector ref without `useCases`, because `businessInformationProjection` maps
`$$connector.useCases`, a field connector documents don't store. The poller needs it to tell "no
connector of this business takes this confirmation type" (C1's broadcast unroutable check). Derive it
the way the storefront projection already does, so the index matches its own contract.

## Acceptance criteria
- [x] 1. Every connector ref in `GET /api/v1/business` and `GET /api/v1/business/:businessId` carries `useCases`: the use cases whose key is set (non-null) on the connector document.
- [x] 2. A connector document with no use-case keys returns `useCases: []`, never an absent field.
- [x] 3. Prod `GET /api/v1/business` returns `useCases` for every connector after deploy (live read).

## Affected boundaries
- `code/src/core/business-information/constants.ts:50` — `businessInformationProjection`, used by `business-information.service.ts:141,238` (list + by-id).
- `code/src/core/storefront/constants.ts:28` — `useCasesProjection(fieldPrefix)`, reused, not changed (already used at `:76` for `$$connector.` and `list-all-connectors.ts:57`).
- Contract: `openapi.yaml:2466` already marks `useCases` required on these refs; `@gfs-bifrost/types` `ConnectorRefDTOSchema` (`useCases: z.array(UseCaseEnumSchema)`, required). No contract change, so no types bump and no Fuse MCP data-file change.
- Consumers of `GET /business`: snap-queue-polling-service (own local `BusinessIndexEntry`, reads only `confirmationsEnabled` today), fuse-ui, fuse MCP `list-customers`. Additive for all.

## Assumptions & uncertainty
- "Takes the type" = use-case key present on the connector document, the same meaning `useCasesProjection` gives the storefront and connector-list routes — source read; matches the G5 decision ("has a mapping").
- The field is absent in prod today for every connector — live `GET /api/v1/business?limit=100` on prod, 2026-10-01.
- The integration spec passes today only because its fixtures seed a stored `useCases` array (`business.controller.integration.spec.ts:203,341`) that real documents don't have — source read. The fixture must seed use-case keys instead, or the test proves nothing.
- Resolved 2026-10-01 (C1 owns it; this plan unchanged): this fix alone doesn't let C1 judge "nobody takes it" for REST. REST connectors carry no use-case keys (prod: all three `useCases: []`) yet fapi delivers every non-stock type to any REST connector with a `webhookUrl`. C1 needs a per-channel rule (REST = has webhook), and the index doesn't expose connector type or webhook presence. Settle C1's predicate before shipping this, in case the index needs more than `useCases`.
- No consumer validates this response against `CustomerInformationResponseDTOSchema` (only config-service's own `dto.ts`/fixture reference it) — repo-wide grep of default branches, 2026-10-01.

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

- [x] 1. Project `useCases` with `useCasesProjection("$$connector.")` in `businessInformationProjection`; rewrite the integration fixtures to seed use-case keys (e.g. `sales_order: {…}`, `goods_out_confirmation: null`) rather than a stored `useCases` array, and add one test per behaviour: keys set → listed, null key → omitted, no keys → `[]` (AC 1,2) — verify: `pnpm test` incl. the integration spec; `lint:fix`, `build:check`, `build:check:tests`. — dev e2e: useCases on every connector ref; fixture tests red on old projection, green on fix — done: 53b2c91
- [x] 2. Deploy to dev, then prod via merge (AC 3) — verify: dev then prod `GET /api/v1/business` via the fuse MCP `config-read` show `useCases` on every connector; PURDYFIGG's three connectors list differing sets. — done: 6f0b36b — done: 53b2c91

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-02 [inc 2] Prod release (AC 3): #235 merged `6f0b36b`. Deploy run 37026253565 was approved through `terraform-prod` after Harry agreed the plan (1 change, image; plus 1 add, `pubsub_invoker` IAM member from FUSE-1190/1191 and Renovate commits shipped alongside). Stale parked run 36980402181 (`a4c22f1`) was cancelled. `config-service-prod` runs `prod-6f0b36b`. Prod `GET /api/v1/business/PURDYFIGG` returns `useCases` on every connector, each a different set: Main SFTP `[master_data, sales_order, purchase_order]`, API `[]`, Live Shopify `[sales_order, goods_out_confirmation]`.
- 2026-10-01 [inc 1] Dev e2e (branch `53b2c91` via manual-deploy run 36877920145, reverted to main after): `GET /api/v1/business?limit=5` and `GET /api/v1/business/DAZZA` on dev return `useCases` on every connector ref, matching each connector's use-case keys — DAZZA Demo SFTP `[master_data, sales_order, goods_in_confirmation]`, harry test / Resty / Demo Rest `[]`, GADG Primary SFTP all 13. Discharges AC 1, 2 in dev.
- 2026-10-01 [inc 1] Integration spec (`business.controller.integration.spec.ts`, mongo 27018): the new fixture tests fail 4/33 against the `origin/main` projection and pass 33/33 with the fix. Full gate green: unit 693/693, integration 362 passed / 15 skipped, `lint:fix` clean on changed files, `build:check`, `build:check:tests`.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- (none)

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
