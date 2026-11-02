---
ticket: FUSE-1070
title: template library storage, browse and CRUD
service: fuse-ui
status: complete
created: '2026-09-02'
updated: '2026-09-11'
repo: /home/hjf/code/fuse/fuse-ui
worktree: /home/hjf/code/fuse/fuse-ui/.claude/worktrees/fuse-1070-template-library
branch: hjf/fuse-1070-08-preset-tba-marking
base: origin/main
base_sha: 1875a2060
pr: '227'
tags:
- waypoint
- plan
---
# FUSE-1070 — template library storage, browse and CRUD

## Intent

Build the foundation of the Mapping Template Library ([FUSE-1070](https://globalfreight.atlassian.net/browse/FUSE-1070), epic FUSE-1004) entirely inside fuse-ui: a third collection in its own Mongo, a Templates area in the main nav, browse + search, collection detail, and full management CRUD. FUSE-1071 was closed *Won't do* and folded in, which is why CRUD sits here. A collection is scoped to one connector type and holds a template per use case; templates store a `MappingConfig` verbatim plus a sidecar marking each default **pre-set** or **to-be-advised**, replacing today's literal `'TBA'` string. Copy-on-apply means nothing downstream ever reads a template, so no config-service change.

## Acceptance criteria

- [x] Templates area reachable from the main nav by any logged-in user
- [x] Library lists collections with name, description, connector type, covered use cases, creator and last updated, and is searchable
- [x] Opening a collection shows each use-case template's mapping rules and its pre-set and to-be-advised values
- [x] A collection and its use-case templates can be created, edited and deleted entirely in the UI
- [x] Every default value on a template is marked pre-set or to-be-advised
- [x] Invalid or incomplete template content is rejected at save with a clear message
- [x] Deleting a template or collection leaves every customer it was applied to unchanged
- [x] Two collections can exist for the same connector type

## Affected boundaries

- **fuse-ui's own Mongo** gains a third collection (`template_collections`), alongside `users` and `audit_log`. `architecture.md` currently says *"Never add a Fuse platform collection to this app's Mongo"* — this is a **sanctioned exception**, authorised on FUSE-1004 (templates live entirely in fuse-ui; copy-on-apply is what stops them becoming a second source of truth for config). `architecture.md` needs that wording at sign-off. No IaC change: `iac/projects/fuse-ui/mongo.tf:73` grants `readWrite` database-wide.
- **`code/src/lib/db/`** — new `template-collections.collection.ts` + client-safe `template-collections.types.ts`. The split is load-bearing: a **value** import of a `.collection.ts` from a client component pulls the Mongo driver into the browser bundle. `import type` is erased and safe; `pnpm typecheck` does not catch the value case, only `next build` does.
- **`code/src/app/server-functions/templates/`** — `.func.ts` reads (unguarded; the page guards) / `.action.ts` writes (`getSession()` guard, hand-built `{ok:false,error:{message}}` for local failures, not `respond`).
- **`code/src/modules/translator-config-editor/`** — decoupled from customer/storefront so a template can mount it. Four seams, not three (see increment 1).
- **`code/src/lib/db/audit-log.types.ts` + `code/src/modules/audit-trail/audit-trail.const.ts`** — two new `AuditTarget` members (`template_collection`, `template`). `ENTITY_LABEL` is a total `Record<AuditTarget, string>`, so neither compiles without an entry in both files.
- **No config-service boundary is crossed.** `DefaultMappingDTO` / `default_mappings` stays dead — confirmed unused here and confirmed removed server-side in config-service's `interfaces.md`.
- No explainers exist for fuse-ui yet (`explainers/` is empty, `ledger.md` has no entries), so nothing to wikilink. This work should produce the first of both.

## Assumptions & uncertainty

- **Store the generated-client `MappingConfig` verbatim** — it is what `CreateConnectorMappingRequest.config` takes, so FUSE-1073's apply is a straight copy. Established: read `src/lib/gen/config-service.client.d.ts:3067`. fuse-ui deliberately types mapping config from the generated client, not the package (FUSE-954 #162 dropped the `& { columnOrder }` intersections after client regen).
- **Validate with the package's published schemas, not hand-rolled ones.** `LinedMappingConfigSchema` / `SimpleMappingConfigSchema` exist in `@gfs-bifrost/types` (`dist/config/schemas/connector-mapping-fragment.schema`), carry both `configType` and `columnOrder`, and the package already composes them as `z.discriminatedUnion("configType", …)`. Established: two reviewers independently read the installed package. The draft's opposite claim came from reading `mapping.schema` — a different (DEFAULT_MAPPING/DTO) family. Hand-composing a structural schema would violate CLAUDE.md's *Shared Types* rule.
- **A to-be-advised default keeps its placeholder value; the mark is a sidecar.** Not because the package forces it — `DefaultConnectorSchema` is a plain `z.string()` with no min length, and `DefaultSchema` is module-private and governs a different family — but because **fuse-ui's own** `defaultValueSchema` requires non-empty and caps strings at 100 chars, and because an absent value would render invisibly in the reused editor. Corroborated by the FUSE-1004 breakdown: *"literal `'TBA'` strings become to-be-advised values"* — a marked value, not an absence.
- **`resolveMappingConfigType` returns a shape for all 39 (connectorType × useCase) pairs and never throws.** The existing switch throws for 9 shopify use cases, but that is about *default content*, not config shape; a blank template still needs a shape. Decided here, stated for the record.
- **Collection names are not unique** — globally or per connector type. The AC only requires multiple collections per connector type. No unique index.
- **Editing a use-case template bumps the parent collection's `lastUpdated`/`lastUpdatedBy`** — AC2 renders "last updated" in the list, so without this the column is wrong after every template edit.
- **`templates` keys are `Partial<Record<UseCase, …>>`, never required-but-nullable**, derived from `allUseCases`. This is the `ConnectorDTOSchema` scar (CLAUDE.md, types 8.3.0) one layer up. Note the mechanism differs: there it was runtime Zod rejecting stored documents; here, with no Zod on the Mongo read, it fails at compile time on literals and fixtures.
- **The worktree has no `node_modules` and pins `@gfs-bifrost/types` `^8.4.0`**, while the main checkout has 7.6.0 installed. Install inside the worktree; do not read package surface from the main checkout.
- **The ticket stays whole — eight increments, eight PRs.** Realistic total is ~3000–3700 changed lines against the 500–700 target. Decided 2026-09-02: do not split management CRUD back out. The obligation this creates is **consistency** — every increment ships as its own PR at roughly the target size, stacked, rather than the stack drifting into two oversized ones near the end.
- **"Invalid" = not every required canonical model field is handled.** Required fields come from `groupedTranslatorRequiredKeys` (`getMappingConfiguration()`), applied per section for a lined config (header keys against header, line keys against lines). **"Handled" means the key is present as a rule or as a default — a to-be-advised default handles its field.** That is what reconciles the gate with FUSE-1074: a hardcoded template's literal `'TBA'` becomes a marked default, the key is present, and the template validates. A field with neither a rule nor a default is what fails. Note the grouped `calculateIsValid` currently *throws* on `master_data` and FGR/WOC have deliberately empty required lists (left that way after FUSE-1049/1050 to avoid false enforcement) — both behaviours carry forward unchanged into `validateMappingConfig`.
- **Audit is in scope, not deferred.** Decided 2026-09-02, reversing the FUSE-1004 deferral — it is a key part of the feature now. Both collection-level and template-level writes are audited via `logAuditEvent`. Two new `AuditTarget` members rather than one: `template_collection` (targetId = collection id) and `template` (targetId = `${collectionId}:${useCase}`), so the audit-trail filter can separate "someone renamed a collection" from "someone changed a mapping template". Each needs an `ENTITY_LABEL` entry. The Templates-area audit *viewer* stays out of scope; rows surface in the existing audit trail.
- **`columnOrder` is kept, scoped exactly as the editor scopes it** — SFTP, confirmation use cases, lined configs. It rides inside `MappingConfig` verbatim, so nothing special is needed to store it; the constraint is not to offer it where the editor cannot round-trip it. The stores hold `*TranslatorConfig` (no `columnOrder`) and re-stamp `configType` on save, so a `columnOrder` on a stored `SimpleMappingConfig` is **silently dropped** — `emptyMappingConfig` must not seed it on the simple arm.
- **Scar tissue this inherits, for the later tickets:** sftp-connector's ledger records that DRSAMS/DRSAMSPL carry a different `columnOrder` to the other twelve, and that *"template-stamping would have silently reordered two customers' CSVs with nothing to catch it"*. Since `feature_flag_use_dynamic_confirmation_mapping` went true in prod, a connector's `columnOrder` determines the real CSV header a customer receives. **FUSE-1073/1074 must not stamp `columnOrder` over a hand-authored order**, and FUSE-1074 was blocked on the unmerged `hjf/fuse-ui-goods-out-column-order-template` (#212) landing first, or the wrong goods-out order would have frozen into "ILG Standard".

> SUPERSEDED 2026-09-11 — #212 merged 2026-09-07 and FUSE-1074 shipped on top of it (a separate 4-PR stack, #231 among them: "import the ILG Standard templates and retire the code-managed ones"), found while signing off this plan. Neither FUSE-1073 nor FUSE-1074 went through a Waypoint plan.

## Increments

Two tracks that converge at 6. Track A (1, 2) and track B (3, 4, 5) are independent.

- [x] 1. **Decouple the mapping editor from customer/storefront** (behaviour-preserving, no new surface). Four seams: stores take injected `save(config)`/`remove()` so `updateConnectorMapping`/`deleteConnectorMapping` leave the store files (the storefront caller inherits stamping `mapping.friendlyName`); `SharedConfigEditorActions` takes `onDeleted()` instead of `useParams`+`router.replace`; `TranslatorConfigEditor` takes a `saveSlotId` defaulting to `PortalIds.StorefrontHeaderSaveSlot`; and — the seam the draft missed — `connectorConfig: ConnectorConfig` narrows to `{ useCase }` plus an explicit `editorKey` prop, since a template has no storefrontId/connectorId/status and would otherwise force fabricated ids through ~7 files. **First, not fifth**: it is the only increment touching live customer-facing code, so it lands on main against a small diff rather than behind a stack. — verify: existing `stores/*/__test__/*.spec.ts` unchanged and green (`pnpm test`), `pnpm build`; UI regression on `/customer/{id}/storefront/{sid}/connector/{cid}/{useCase}` — edit a rule, Save Config persists, Delete returns to the connector page. — done: 27e3bd2 (merge commit; rebased 2026-09-03, see sign-off note below)
- [x] 2. **Shared mapping-config vocabulary.** `resolveMappingConfigType(connectorType, useCase)`, `emptyMappingConfig(configType)` (asymmetric on `columnOrder` per the constraint above), and a **new** template-side `validateMappingConfig(config, {useCase, connectorType, requiredKeys})` = the package's `LinedMappingConfigSchema`/`SimpleMappingConfigSchema` **plus** the required-field rule. **The two existing `calculateIsValid` copies are deliberately left alone.** They are different rules, not one duplicated (grouped applies the sftp `groupBy` gate and throws on `master_data`; simple returns false on an unknown use case), and — decisively — both check **rules only, never defaults**. Template validity counts a default as handling its field, so unifying them would quietly loosen the customer-side editor's Save gate, which is outside this ticket. — verify: `mapping-config-validity.logic.spec.ts` carrying (a) a parity assertion against `getDefaultMappingConfig(u, false, t).configType` for the 30 of 39 pairs that don't throw, and (b) an explicit truth table pinning at minimum sftp `stock_adjustment`→simple, sftp `master_data`→simple, rest `purchase_order`→simple, sftp `purchase_order`→lines, shopify `master_data`→simple. The parity test is scaffolding that dies with FUSE-1074; the truth table is the spec that survives. `pnpm test` + `pnpm build`. — done: 9313969 (merge commit; rebased 2026-09-03)
- [x] 3. **Data model + collection module (reads only).** `TemplateCollectionDocument` = `{_id, name, description, connectorType, createdBy, created, lastUpdated, lastUpdatedBy, templates: Partial<Record<UseCase, {config: MappingConfig; defaultMarks: DefaultMarks; updated: Date}>>}`; `DefaultMarks` mirrors the `defaults` shape (`{header, lines}` lined / flat simple — the same key can appear in both). Runtime `MARKS` array lives in `.types.ts`, not the collection file. Indexes `{connectorType:1}`, `{lastUpdated:-1}`, no unique index; registered in `instrumentation.ts`. Write helpers land with their callers, not here. — verify: `toTemplateCollectionSummary` spec (`pnpm test`), `pnpm build`. — done: 02dccc0 (merge commit; rebased 2026-09-03)
- [x] 4. **Nav entry + `/templates` library page.** `AppSearchInput` + `AppDataTable` modelled on `customers-list` (note: it does *not* use `filterObjectArray`), URL-synced filter via `window.history.replaceState`. — verify: `pnpm build` proves the `AppHref` typed route resolves; UI check as a non-admin — Templates sits next to Customers and the page renders its empty state. (The "a real row lists and search filters it" check belongs to 5, where a row can be created through the UI.) — done: b3ccbc7 (merge commit; rebased 2026-09-03)
- [x] 5. **Collection CRUD (metadata only), audited.** Create/update/delete in `templates.action.ts` with the session guard and `revalidatePath('/templates','page')`; modals reuse `AppForm`/`AppSelectField`/`AppDangerDelete`. Each write calls `logAuditEvent(action, 'template_collection', collectionId, details)`; the two new `AuditTarget` members and their `ENTITY_LABEL` entries land here. No zod schema unit test — schema shape is evidenced by `tsc`/build. — verify: UI check creating **two** sftp collections (this is the only place AC8 is asserted), rename reflected in the list, delete removes the row and leaves a customer connector untouched (AC7's collection half ships here, not later); all three actions appear in the existing audit trail under a Template Collection entity filter. — done: 85e5b90 (merge commit; rebased 2026-09-03)
- [x] 6. **Collection detail shell.** `/templates/[collectionId]` + `layout.tsx` + `TemplateCollectionHeader` hosting the save-slot portal div, listing covered use cases with rule counts from `Object.keys(templates)`, plus an explicit empty state — which after 5 is the only reachable state. Pre-set/TBA rendering deliberately deferred to 8, where the data exists. — verify: opens an increment-5 collection and renders the empty state; covered-use-case view-model spec (`pnpm test`). — done: 0cafafc (merge commit; rebased 2026-09-03)
- [x] 7. **Use-case template editor: mount, add, save/load, delete — audited.** Mounts `TranslatorConfigEditor` on `/templates/[collectionId]/[useCase]` via the increment-1 seams; add-use-case flow uses `getUseCaseOptionsForConnector(collection.connectorType)` + `emptyMappingConfig(resolveMappingConfigType(...))`; `config` round-trips; `deleteUseCaseTemplate` `$unset`s the key; both writes bump the collection's `lastUpdated`/`lastUpdatedBy` and call `logAuditEvent(action, 'template', \`${collectionId}:${useCase}\`, details)`. Column ordering is offered only where the editor already offers it — SFTP, confirmation use cases, lined configs. — verify: create a template, add rules, save, reopen and see them; delete it and watch the collection detail's covered list shrink; the list page's Last Updated moves on a template edit; both actions land in the audit trail under a Template entity filter. — done: 104e3f0 (merge commit; rebased 2026-09-03)
- [x] 8. **Pre-set / to-be-advised marking + save-time rejection.** A template-flavoured Defaults panel adds a Mark column per default key; `saveUseCaseTemplate` runs `validateMappingConfig` plus a marks-completeness check (marks cover exactly the config's default keys) server-side and returns `{ok:false,error:{message}}`; `unwrap` → `AppSaveCancelActions` → `dialog.alert` is the "clear message" channel. **Invalid = a required canonical field handled by neither a rule nor a default**, per section for a lined config; a to-be-advised default handles its field. Collection detail gains the pre-set/TBA split pulled forward from 6. — verify: `default-marks.logic.spec.ts` (marks follow add/remove/rename of a default; completeness invariant) and a validity spec asserting that a required field carrying only a to-be-advised default **passes** while one with neither rule nor default **fails** — that pair is what proves FUSE-1074's import isn't blocked. Then a UI check: mark a default TBA, save, reopen and see it; delete the rule and the default for a required field and save → the dialog names the missing field and the collection detail is unchanged. — done: 127049a (merge commit; rebased 2026-09-03)

## Verification

**Increments 1-4 — 2026-09-02.** Local gates on every commit: `pnpm lint` exit 0, `pnpm build` exit 0, full suite green (333 → 390 tests, 32 → 36 suites).

**Browser regression, increments 1 and 4.** Run locally against real dev config-service reads with a throwaway Mongo and a seeded local admin, because the dev deploy needs a login not held here and because Delete would otherwise destroy a real customer's mapping. Driven on **HJF / `hjf test`** — Harry's own sandbox connector, which had **no use cases configured**, so the whole exercise creates and removes its own subject and leaves the business exactly as found.

| Check | Result |
|---|---|
| Templates link renders in main nav for a logged-in user | pass — `Templates → /templates` present |
| `/templates` renders its empty state | pass — "No template collections yet" |
| Create a mapping (`purchase_order`, ILG standard template, lined) | pass — redirects into the editor |
| Editor mounts through the new `ConnectorMappingEditor` wrapper | pass — Grouping/Header/Line tables, 12 rules, required-field ticks green |
| Save/Delete actions portal into the storefront header via `saveSlotId` | pass — Save Config, Discard Changes, Delete all render in the header bar |
| Edit a rule (remove `metadata.notes`) | pass — 12 → 11 rows, unsaved |
| **Save Config persists through the injected `save`** | pass — "Config saved successfully"; after a full reload, 11 rows and `metadata.notes` gone |
| **Delete redirects via the injected `onRemoved`** | pass — lands on the connector page, back to "have not configured any inbound use cases" |
| Sandbox left as found | pass — config-service shows `hjf test` with no `useCases` |

Screenshots: `scratchpad/shots/0{1..12}-*.png` (local only — to be attached to the PRs on an evidence branch).

**Dev environment:** taken for `hjf/fuse-1070-01-decouple-mapping-editor` (run 33664132976, succeeded), then **reverted to `main`** (run 33665310118). Both announced in `#bifrost-general`. The dev deploy ended up unused — verification ran locally — so it was given straight back.

**Increments 5-8 — 2026-09-02.** Same local environment. Driven on a REST collection with `master_data` — a simple config whose two required fields (`product.identifiers.skuId`, `product.information.description`) make the save gate observable.

| Check | AC | Result |
|---|---|---|
| Create a collection through the UI | 4 | pass |
| **Two SFTP collections coexist** | 8 | pass — no unique constraint fires |
| Search filters the library | 2 | pass — matched on name, connector label, friendly use-case name and raw key |
| Rename reflected in the list | 4 | pass |
| Collection detail empty state | 3 | pass |
| Add a use case → **persists nothing**, opens a blank editor | 6 | pass |
| Blank template → **Save disabled** | 6 | pass |
| One of two required fields via a default → **Save still disabled** | 6 | pass |
| **Two of two via defaults, zero rules → Save enabled** | 6 | pass — the whole point of `defaultsSatisfyRequiredKeys` |
| Save persists | 4 | pass — document shape confirmed directly in Mongo |
| Marks panel lists both defaults | 5 | pass |
| Toggle one to to-be-advised, Save Marks | 5 | pass — `defaultMarks` shows one of each, values retained |
| Collection detail shows the split | 3 | pass — "1 pre-set" / "1 to be advised" |
| Delete template → redirect, collection empty again | 4 | pass |
| Delete collection → gone from library | 4, 7 | pass — dialog states applied customers are unaffected |
| Audit trail | — | pass — Created/Updated/Deleted under **Template Collection** and **Template**, composite `{id}:{useCase}` target rendered |

Stored document after the round-trip, as the machine-checkable pairing for the screenshots:

```json
"master_data": {
  "config": { "configType": "simple", "rules": [],
    "defaults": [ {"key":"product.identifiers.skuId","value":"TBA"},
                  {"key":"product.information.description","value":"TBA"} ] },
  "defaultMarks": { "product.identifiers.skuId": "to_be_advised",
                    "product.information.description": "preset" }
}
```

**Two defects found by driving the UI**, both of which passed every unit test in the stack — see *Decisions & deviations*.

**Real CI, per branch — 2026-09-02.** `code-quality` (lint → test → build) **green on all eight branches**. Seven had to be dispatched by hand: both `code-quality.yaml` and `secops.yaml` scope `pull_request` to `branches: [main, master]`, so a PR based on another feature branch runs **no CI at all** and shows zero checks. That is a pre-existing repo-wide gap, not specific to this stack — the retry-queue stack (#191-197) shipped under it too. Left unfixed deliberately: the one-line trigger change alters CI behaviour for every PR in the repo and is a call for Harry, not a side effect of this ticket.

**Dependency audit — 2026-09-03.** `#228` merged to `main`, and the whole stack was then **rebased onto it** and force-pushed (`--force-with-lease`, all eight tips re-verified against their remotes first; no conflicts, since #228 only touched `package.json` and the lockfile). `#220` is now **all checks green**.

Worth recording, because it cost a wasted cycle: **re-running a failed `pull_request` check does not pick up a fix that landed on the base branch since.** GitHub replays the original merge commit, so the audit failed identically on re-run. The branch has to actually contain the fix — rebase or merge, not re-run.

**Confluence:** the nine changelog rows (eight stack PRs + the dependency fix) were added to the [Fuse UI changelog](https://globalfreight.atlassian.net/wiki/spaces/Bifrost/pages/152305665) on 2026-09-03, once the stack was ready for review.

**Merge — 2026-09-03/04.** All nine PRs (#220–228) merged to `main`, review APPROVED, checks green, zero unresolved threads on every one — verified directly against GitHub at sign-off (2026-09-11), not assumed from this doc.

## Decisions & deviations

- **2026-09-02 — progress.** Increments 1-3 implemented and committed, each on its own stacked branch, each passing `pnpm lint` (exit 0), `pnpm test` and `pnpm build` locally: 1 = `9191905` (`hjf/fuse-1070-01-decouple-mapping-editor`), 2 = `1fcb0fb` (`hjf/fuse-1070-02-mapping-config-vocabulary`), 3 = `041a0f6` (`hjf/fuse-1070-03-template-collections-model`). Boxes stay unticked until the dev-deploy verification each increment names is actually run — local gates are not the named verification.
- **2026-09-02 — verification cadence.** Dev deploys happen at four checkpoints rather than once per increment: after 1 (the refactor, the only change to live customer-facing code, verified alone so a regression is attributable), after 4 (nav + library page), after 5 (CRUD), and at the stack tip. Deploying every increment separately buys nothing for a stack that merges in order.

- **2026-09-02** — Increment ordering inverted from the draft: the editor decoupling moves from fifth to first. It is the only increment touching live customer-facing code, it merges on its own merit as a behaviour-preserving refactor, and it shares two store files with the vocabulary increment, so keeping them adjacent avoids a gratuitous rebase collision three PRs deep.
- **2026-09-02** — Draft claim "the package schemas cannot validate a stored template" **overridden**: it read `mapping.schema` (the DEFAULT_MAPPING/DTO family) instead of `connector-mapping-fragment.schema`. Two reviewers independently confirmed the published `LinedMappingConfigSchema`/`SimpleMappingConfigSchema` carry `configType` and `columnOrder`. Validation uses them.
- **2026-09-02** — Audit writes go through `logAuditEvent` (`server-functions/audit/log-audit-event.func.ts`), which resolves its own session and is fire-and-forget — not `addAuditLog(session.email, …)`, which is the collection-level primitive at `lib/db/audit-log.collection.ts:47`. Recorded design decision: future audited actions call the generic function rather than growing a bespoke wrapper.
- **2026-09-02** — Increment 1 shipped with three departures from the plan, all found in source. (a) `saveSlotId` is a **required** prop with no storefront default — a default would have left the shared module naming a storefront-owned element id, which is the coupling the increment exists to remove. (b) `TranslatorConfigEditor` branches on `config.configType` instead of `isGroupedTranslatorConfig()`, and the two now-unreachable `configType` throw-guards in the concrete editors are gone. (c) The customer-side wiring lives in a new `modules/customer-storefront/components/connector-mapping-editor.tsx` client wrapper, which also inherits stamping `mapping.friendlyName` — the plan named that responsibility but not its home.
- **2026-09-02** — The work ships as **eight stacked branches** (`hjf/fuse-1070-<nn>-<slug>`), each its own PR off its predecessor, rather than the single `hjf/fuse-1070-mapping-template-library` branch the frontmatter names. The frontmatter branch is repointed to the stack tip at sign-off so `wp signoff` can reconcile every `done:` sha.
- **2026-09-02 — two defects caught by driving the UI, neither visible to any test in the stack.** (a) The editor's own Save gate counted **rules only**, so a required field covered by a to-be-advised default would have left Save permanently disabled — exactly the case the feature exists for. Fixed with a `defaultsSatisfyRequiredKeys` flag on both stores, set for a template and unset for a customer mapping, so the customer-side gate is untouched by construction. (b) Increment 7's add-use-case flow **persisted a blank template**, which increment 8's gate then rejected — adding a use case would have failed outright. Adding no longer persists; the editor opens on a blank config and the first passing save is what puts it in the library, which is also what AC6 asks for. Both folded into increment 8, since 8 is what introduced the gate.
- **2026-09-02 — a third defect, layout.** The root `<main>` is `display: flex` (a row), so `/templates` pages returning a header plus content rendered them **side by side**, content pushed ~40% across the viewport. Every other top-level area supplies its own container via a layout; `app/templates/layout.tsx` does the same. Folded into increment 4 (which introduced the route) and the stack rebased, so each PR is independently correct rather than four of them shipping a broken page.
- **2026-09-02 — final shape:** eight stacked draft PRs, #220 → #227, plus **#228** off `main` clearing a pre-existing red dependency audit (`main`'s own nightly went red the same day). Screenshots live on the throwaway branch `hjf/fuse-1070-evidence`, to be deleted once the stack merges.
- **2026-09-02** — Four scope questions answered by Harry, all four closing an UNRESOLVED: (1) **keep FUSE-1070 whole** at eight PRs rather than splitting management CRUD back out, on condition the increments stay consistently sized; (2) **"invalid" = not every required canonical model field is handled**, where a to-be-advised default counts as handling — this is what keeps the gate compatible with FUSE-1074's `'TBA'`-laden import, and it is worth a test rather than a comment; (3) **auditing is not deferred** — reversing the FUSE-1004 deferral, since it is now a key part of the feature; (4) **`columnOrder` is kept for SFTP templates**, scoped exactly as the editor already scopes it (SFTP + confirmation + lined), which is why `emptyMappingConfig` stays asymmetric on the simple arm.
- **2026-09-11 — sign-off reconciliation.** `wp signoff` reported all eight `done:` shas as unreachable and 23 uncommitted paths in `/home/hjf/code/fuse/fuse-ui` — both false positives, not real gaps. The recorded worktree (`fuse-1070-template-library`) had already been removed (normal post-merge cleanup, per the *Worktrees* rule in `~/code/CLAUDE.md`), so `wp signoff` fell back to the **main checkout**, which sits on an unrelated branch (`hjf/fuse-1000-secops-02-migrate-fuse-ui`) carrying separately-parked FUSE-980 work — its state has nothing to do with this ticket and was left untouched, per the worktree rule. The `done:` shas themselves were the **pre-rebase** local commits (see the 2026-09-03 dependency-audit entry above: the whole stack was rebased onto `#228` and force-pushed), so they were never going to be ancestors of any post-rebase branch. Verified instead directly against GitHub: all nine PR merge-commit shas (`27e3bd2`, `9313969`, `02dccc0`, `b3ccbc7`, `85e5b90`, `0cafafc`, `104e3f0`, `127049a`, plus `#228`'s `32bcb91`) are real ancestors of `origin/main` (`git merge-base --is-ancestor`), and all nine PRs are `MERGED`/`APPROVED`/zero-unresolved-threads via `gh pr view`. Increment `done:` stamps above were updated to the merge-commit shas so a future `wp signoff` reconciles cleanly.

## Learnings
