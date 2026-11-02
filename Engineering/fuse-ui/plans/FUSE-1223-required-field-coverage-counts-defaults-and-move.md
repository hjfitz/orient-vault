---
ticket: FUSE-1223
title: Required-field coverage counts defaults and moves to use-case level
service: fuse-ui
status: complete
created: '2026-10-19'
updated: '2026-10-19'
repo: /home/hjf/code/fuse/fuse-ui
worktree: /home/hjf/code/fuse/fuse-ui/.claude/worktrees/fuse-1223-required-field-coverage
branch: hjf/fuse-1223-required-field-coverage
base: origin/main
base_sha: dd6eec753
pr: '340'
tags:
- waypoint
- plan
impl_model: sonnet
impl_effort: medium
---
# FUSE-1223 — Required-field coverage counts defaults and moves to use-case level

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

- **2026-10-19** — Learnings promoted at sign-off: the single coverage rule into `architecture.md` "Validity gates"; the constants, naming, check-shape and `shopifyOut` facts into `known-context.md`; the test and tooling gotchas into `operations.md`; the template explainer updated.

- **2026-10-19** — The shas on the ticked increments are branch commits, and each PR was squash-merged, so none is on `main`. Mapping: #336 = increments 1-2 (prod `1b3cbf0`), #337 = 3 (`29bc556`), #338 = 4-5 (`4978257`), #340 = 6 (`6f0d67f`).

## Intent
<!-- What we are changing and why. Link the ticket. -->
[FUSE-1223](https://globalfreight.atlassian.net/browse/FUSE-1223). A customer mapping whose required field is supplied by a default (the Academically Gifted ECOM Retail ID case) cannot be saved today: the editor's save gate counts rules only, so the first edit after load disables Save. Make "what supplies this required field?" one pure function over rules and defaults. It drives the save gate, a use-case-level coverage panel (gap blocks, conflict and check inform) and a required marker on Default rows. Proof: the AG-shaped mapping saves and `shipping.method` stays editable.

Paths below are relative to `code/src`. fuse-ui only; config-service and pkg-node need no change (see Assumptions).

## Acceptance criteria
- [x] 1. A required field with no rule but a default is satisfied, and the config saves.
- [x] 2. The per-table "Required Fields" button and red box are gone. Coverage shows once per use case, as one panel directly under the tab pills (the design's placement) on every tab, with wording that follows the active tab.
- [x] 3. The panel appears only when a required field has no source, or a field has a fixed rule plus a default that can never apply, or a column-fed required field also has a default. Otherwise it is absent.
- [x] 4. A gap (required, no source) blocks save. Conflicts and checks do not.
- [x] 5. Every panel row names the field, states the problem in plain language, and offers its action: Add mapping, Add default, Remove mapping, Remove default, or make fixed.
- [x] 6. Add mapping opens the rule dialog with the destination preselected. Add default opens the default dialog with the field pre-filled.
- [x] 7. Default rows show the required marker where the field is required.
- [x] 8. A config whose required fields are satisfied by defaults is accepted by every validator in the path (UI gate, `validateMappingConfig`, config-service).
- [x] 9. On a dev business shaped like Academically Gifted (Retail ID `identifiers.customerId` default `ECOM`, no rule), the mapping saves, and `shipping.method` can be edited and saved. Real AG is confirmed after the prod deploy, not by this plan.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `modules/translator-config-editor/stores/{simple,grouped}-config-editor/*-store.ts`: `calculateIsValid` is the save gate today (the simple one is a closure in the store factory, the grouped one is module-private). Mounted by `providers/*-provider.tsx` (G4: the first prop-sync effect clears `hasPendingChanges`; removing a dep is safe, adding a prop to it is not).
- `modules/translator-config-editor/components/require-field-validator.tsx` (the old check, three mounts), the two `*-translator-config-editor.tsx` (panel mounts above `<Tabs>`), the two `*-translator-defaults.tsx` and `default-value-editor-modal.tsx` (marker, `requiredKeys={[]}`), `translation-rule-modal.tsx` (prefill).
- `modules/translator-config-editor/logic/`: `dry-run-mapping.logic.ts` (`classifyFrom`, `requiredNotMapped`), `mapping-config-validity.logic.ts` (`unhandled`, `validateMappingConfig`, used by `app/server-functions/templates/templates.action.ts:68,154,320`, so template import acceptance changes), `expression-fields.logic.ts` (`fuseFieldsRead`).
- `app/server-functions/configuration.func.ts`: the hard-coded required-key lists (read-only here).
- Consumers of the editor: only `modules/customer-storefront/components/connector-mapping-editor.tsx` and `modules/template-library/components/template-mapping-editor.tsx` (the only setter of `defaultsSatisfyRequiredKeys`).
- Explainers whose claims this reverses: [[mapping-template-library]] (customer gate must map every required field) and the architecture.md "Mapping editor: two validity gates" bullet. Both are updated at sign-off.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- The failure is UI-only: the customer editor never sets `defaultsSatisfyRequiredKeys`, so every `updateConfig` recomputes `isValid=false` for a default-satisfied field and Save disables. No second gate on the customer save path (`updateConnectorMapping` goes straight to the PUT). — traced end to end by the grounding review.
- config-service has no required-field validation (POST/PUT `connector-mappings.controller.ts` → `StorefrontService.validateMappingConfig` checks dictionaries and `configType` only), and the required lists exist nowhere outside fuse-ui. AC 8 therefore needs no server change. The ticket's "Fuse sets it back" is not supported by source. — source read of config-service origin/main and pkg-node, both reviewers.
- Retail ID is `identifiers.customerId` (`app/server-functions/data/sales-order-keys.json`). The ticket's `customer.id` is the Shopify source column, which dev ACADEMIC maps to `identifiers.businessCustomerId`. — dev config read plus source.
- Runtime precedence: rule output wins and empties are dropped, so a default applies only when the rule yields nothing, on sftp-connector and shopify-connector inbound. A fixed literal can never fall back (conflict). — rules-engine `allocate-defaults.ts`/`apply-rules.ts`, both connectors' sales-order transformers.
- A rule whose `from` is an expression with no column reference (`upper('ECOM')`, the live AG workaround) is **fixed**, not a check. `classifyFrom` treats an unlexable `from` as fixed, so the coverage function must not report a conflict for it. — dev ACADEMIC mapping; `lex()` returns `[]` on error.
- Defaults count as a source on **inbound flows only** (`fileIn`, `shopifyIn`). Outbound flows keep today's rules-only check and today's side (`to`). A default on SFTP egress fills the canonical field but emits no column unless a rule reads it. `shopifyOut` holds the Fuse field in `from`, so the existing `to`-side check may already be wrong there. That predates this ticket and is out of scope, unverified, and a follow-up candidate. — decided as the conservative default; `labels.const.ts` orientation and the egress transformer read.
- "Check" covers a required field fed by a column or by an expression that reads at least one column. — decided; ticket wording ("mapped from a column") is the narrow case.
- Copy says **Fallback**, following the design page, which uses "Fallback Values" for the tab, table and every message. The UI says "Default Values" today and FUSE-955 (the wider reframe) has not landed. Increment 3 renames the visible strings in the translator-config-editor module only, not code identifiers, because one screen saying both would confuse the users. This plan's "default" means the UI's Fallback. — design screenshots (2026-10-19), source grep, 1:1 notes.
- Design (screenshots in `~/fuse-1223`, Goods Out mapping for Aurora): one amber banner sits **under the tab pills**, not above them, on both Mapping Rules and Fallback Values, with wording per tab (Rules: "A fallback can never apply ... open Fallback Values to remove it, or switch the rule back to a source column"; Fallback tab: "This fallback can never apply ... Remove it here, or switch the rule back to a source column"). A conflicting Fallback row also carries an amber "shadowed by fixed value" pill. The Fallback tab opens with two lines of copy: "Fallback values fill a field only when the source provides no value for it. To set a value that should always apply, enter it as a fixed value in the mapping rule instead." The banner is shown on every tab so a disabled Save is always explained (the design does not show Dictionaries or Test Mapping, so this is my default). The gap (red) and check (amber) states are not visible in the screenshots, only described in the page header text, which is what the plan follows for them. — screenshots.
- A `CHANGE_ME_<key>` placeholder rule still counts as a source, as today. Unchanged, not a decision.
- Folding the two gates reverses FUSE-1070's deliberate choice ("a customer mapping must map every required field"). The ticket asks for it. The PR must say so and re-derive why the gates differed. — FUSE-1070 plan and ledger, architecture.md.
- Existing behaviour the coverage function must keep, each with a spec: FGR/WOC and simple goods_in/goods_out/RGA/RGC/pick/pack have empty required lists. Grouped `calculateIsValid` throws on `master_data`, and the simple one returns false on an unknown use case. The SFTP `groupBy` requirement stays in the grouped gate. Header defaults do not satisfy a line requirement. — FUSE-1049/1050/1070 ledger entries, source.
- `isValid` is `undefined` on load today (the providers never seed it). Save itself is unaffected because it also needs pending changes, but "Save as Template" (`disabled={!isValid}`) stays disabled until the first edit, and the new panel would disagree with it on load. Deriving it from the coverage function at init fixes both. — grounding review of `SharedConfigEditorActions`.
> SUPERSEDED 2026-10-19 — the design page says Always send X "resolves it", so the next bullet's
> keep-the-default behaviour was replaced by the convert-and-delete behaviour below.
> Kept as the record of how it was first decided.

- DECIDED 2026-10-19 (Harry): **Always send X** on a check row rewrites the column rule's `from` to the fixed literal of the default's value and **keeps the default**. The row then reads as a conflict (amber, non-blocking) offering Remove default, so it takes two clicks to reach a single source. Chosen over converting and deleting the default in one step because the users are not expected to follow the Fixed-versus-Fallback model, and keeping the default is the safer result of a click. Supersedes the FUSE-955 open question.
- DECIDED 2026-10-19 (Harry): a literal placeholder default such as `TBA` counts as a source on the customer gate, like any default. No gap.
- DECIDED 2026-10-19 (Claude, at Harry's delegation after he'd said B and then "use your judgement"): **Always send X** replaces the column rule's `from` with the fixed literal of the fallback's value **and deletes the fallback**, so the panel clears, as the design page says ("Remove mapping or Always send ECOM resolves it"). It is one click to a single clear source, and Cancel restores both rows because nothing is saved before Save. Tradeoff accepted: one click rewrites two rows, where keeping the fallback (B, Harry's first pick) took two clicks and left an amber row. The PR description states this.
- DECIDED 2026-10-19 (Claude, same delegation): the per-table "Required Fields" button and its checklist popover go, per AC 2 and the design page's own header ("moves out of the mapping table"). The screenshots show them because the prototype renders today's behaviour behind the Fuse Tweaks toggle.

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

- [x] 1. Pure coverage module (AC 1,3,4 groundwork). Move `classifyFrom`/`columnRefs` from `dry-run-mapping.logic.ts` into `logic/rule-source.logic.ts`, treating an expression with zero column refs as fixed. Add `logic/required-field-coverage.logic.ts`: `computeCoverage({ required, rules, defaults, flow })` returns per-key `gap | conflict | check` plus `blocking`. Inbound flows count defaults, outbound flows are rules-only on `to`. Grouped header and lines are computed separately. — verify: new `required-field-coverage.logic.spec.ts` (each state; expression-read rule; `upper('ECOM')` is fixed; unlexable `from` is no conflict; header default does not satisfy a line requirement, mirroring `mapping-config-validity.logic.spec.ts`; empty required list; outbound unchanged), and the existing dry-run spec stays green as the only guard on the extraction. `pnpm test`, `pnpm typecheck`, `pnpm lint`. — logic + rule-source specs pass (179 in module), typecheck and lint clean — done: f8dfba5
- [x] 2. Save gate and consistency, the hotfix (AC 1,4,8,9 save half). Both stores derive `isValid` from `computeCoverage(...).blocking`, keep the SFTP `groupBy` requirement, the `master_data` throw and the simple store's unknown-use-case false, and seed `isValid` at provider init. Remove `defaultsSatisfyRequiredKeys` through the chain. `validateMappingConfig`/`unhandled` delegate to the same function. The old `RequiredFieldValidator` reads gaps from `computeCoverage` so the red box cannot contradict an enabled Save. — verify: specs on the extracted validity wrapper (default-only field valid; no source invalid; conflict valid; unknown use case; groupBy; Save-as-Template enabled on load), existing `mapping-config-validity.logic.spec.ts` green, and the template editor still accepts a default-satisfied field (no behaviour change there). Dev deploy via `verify` on dev business HJF: `sales_order` Shopify mapping with `identifiers.customerId` default `ECOM` and no rule, edit `shipping.method`, Save is enabled and the PUT returns 200. Capture the request and response. — store + validity specs, full suite 1178 green, typecheck and lint clean; dev check pending — done: bab8f46
- [x] 3. Fallback labels and required marker (AC 7). Rename the visible "Default Values" strings in the translator-config-editor module to "Fallback Values" (tabs, table titles, modal titles), add the two lines of explanatory copy at the top of the Fallback tab, pass the use case's required keys into the defaults tables and `DefaultValueEditorModal`, and drop the `requiredKeys={[]}` overrides and the "might be misleading" comment. Independent of 1 and 2. — verify: `.spec.tsx` asserting the required icon and tooltip on a required fallback row and not on an optional one, and the tab reads "Fallback Values" (mock the ESM-only `@ilg-platform/ui-toolkit/*` subpaths as the existing specs do); `grep` that no user-visible "Default Values" string is left in the module; one screenshot in the increment 5 deploy. — PR #337 merged and live in prod (29bc556); fallback-row spec, mutation-checked; screenshot on dev data — done: 5427df7
- [x] 4. Coverage panel (AC 2 part, 3,4,5 part). Add `components/required-field-coverage-panel.tsx`, derived from store `config` at render, returning `null` when clean. Red gap rows, amber conflict and check rows with plain-language text and the friendly field name, with the **Remove mapping** and **Remove default** actions via the existing reducers. Mounted directly under the tab pills in both `*-translator-config-editor.tsx`, on every tab, with message wording per active tab and an amber "shadowed by fixed value" pill on a conflicting Fallback row. The old validator stays until 5, so gap rows still have its Add button. — verify: panel `.spec.tsx` (absent when clean; one row per state; gap rows marked blocking; Remove actions change the store config and clear the row), then screenshots of gap, conflict, check and absent on one simple and one grouped use case. — PR #338 merged and live in prod (4978257); panel + Remove actions; specs, live walkthrough on dev data — done: 03b356d
- [x] 5. Add mapping and Add default with prefill, and delete the old check (AC 2,5,6). Add `initialTo?` to `TranslationRuleModal` and `initialKey?` to `DefaultValueEditorModal` (a prefill on an add, not `existingRule`; guard `handleTabChange`, which blanks the expression-side field). The panel calls `useDialog` and the existing store actions directly, with no new hook and no new prop on the provider effect (G4). Delete `require-field-validator.tsx` and its three mounts, keeping the `CHANGE_ME_` Rename badge. — verify: modal specs (destination preselected; Confirm adds a rule or default), panel spec (buttons open the right modal with the field), then one dev deploy walk-through on HJF: gap row, Add mapping, row clears, Save; and no per-table red box remains. — PR #338: Add mapping/Add fallback with prefill, old per-table check removed; live walkthrough — done: 03b356d
- [x] 6. **Always send X** (AC 5, 9 end to end). A check row's make-fixed action: replace the column rule's `from` with the quoted literal of the fallback's value and delete the fallback, so the panel clears, using `serializeArg` from `expression-builder/serialize-dsl.ts` (module-private today, so export it) so the quoting is not hand-rolled. — verify: store specs (after the action `classifyFrom` is fixed, the fallback is gone, and `computeCoverage` reports no entry for the field; a fallback value containing a quote is serialized correctly), `rule-reducers.spec.ts` if a reducer is added, and a dev run of the AG shape end to end: panel absent, Save works, `shipping.method` editable; re-add a column rule and the amber check row offers both actions, and Always send X clears the panel and the fallback row is gone. — PR #340 merged and live in prod (6f0d67f); seven store-asserting specs, serializer round-trip, live on dev data with the stored mapping read back — done: e109696

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-19 [inc 6] AC 5,9: local run against the real dev config-service on a temporary `sales_order` mapping where Retail ID was mapped from `customer.id` with an `ECOM` fallback. Buttons offered: Remove fallback, Remove mapping, Always send ECOM. Clicking Always send ECOM cleared the Retail ID note, left only the unrelated Currency conflict, and enabled Save; saving stored `{"from":"'ECOM'","to":"identifiers.customerId"}` with only `financial.currency=USD` left in the fallbacks (`config-read`). 100 suites / 1222 tests, typecheck, lint and build pass. Screenshots on `hjf/fuse-1223-always-send-evidence`.
- 2026-10-19 [inc 4,5] AC 2,3,4,5,6: same local setup. Rules and Fallback tabs showed both amber states with tab-specific wording and the shadowed pill; Remove mapping cleared the Retail ID note; deleting its fallback produced the red gap with "Save is blocked" and Save Config disabled; Add mapping and Add fallback opened with Retail ID preselected; confirming a prefilled mapping cleared the gap and re-enabled Save. No per-table Required Fields button remained. 100 suites / 1204 tests. Screenshots on `hjf/fuse-1223-coverage-panel-evidence`.
- 2026-10-19 [inc 3] AC 7: on the Fallback tab Retail ID (required) shows the marker while Currency and Ship Lane do not; the tab, titles and explanatory copy read Fallback. The spec fails with the old `requiredKeys={[]}` restored. 97 suites / 1181 tests. Screenshot on `hjf/fuse-1223-fallback-labels-evidence`.
- 2026-10-19 [all] Each slice was merged and promoted: #336 → prod `1b3cbf0`, #337 → `29bc556`, #338 → `4978257`, #340 → `6f0d67f`. Each prod plan was `0 to add, 1 to change, 0 to destroy` (image only plus the standing scaling/container-dependencies/sidecar-env drift, identical to the last applied plan), the range to prod's sha was only that PR, and `gcloud run services describe fuse-ui-app-prod` showed the new image tag after each apply.
- 2026-10-19 [inc 2] AC 1,4,9: the branch (bab8f46) ran locally on :3010 against the real dev config-service. A temporary `sales_order` mapping on HJF's `Dev` connector had `identifiers.customerId` supplied only by the default `ECOM` and no rule. The page loaded with the Header check green and "Save as Template" enabled (isValid seeded true). Editing the `shipping.method` rule enabled Save Config, the save's three server actions returned 200, and `config-read` showed the stored mapping with the new rule and the `ECOM` default intact. The mapping was deleted afterwards (204). Screenshots: `.pr-evidence/fuse-1223-01-default-only-on-load.png`, `fuse-1223-02-save-enabled-after-edit.png` on branch `hjf/fuse-1223-required-field-coverage-evidence`.
- 2026-10-19 [inc 1,2] `pnpm test` 96 suites / 1178 tests green, `pnpm typecheck` and `pnpm lint:fix` clean. The unchanged dry-run spec is the guard on the helper extraction.
- 2026-10-19 [inc 2] AC 8: config-service origin/main has no required-field validation (POST/PUT mapping → `validateMappingConfig` checks dictionaries and `configType` only), so the server already accepts such a config. The live save above is the proof.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- The branch was not deployed to the shared dev environment. The deploy was started and cancelled in the Docker build stage because the deployed UI cannot be driven without a login, and the local run against the real dev config-service covers the same behaviour. dev fuse-ui was never touched. The per-PR preview environment is the remaining deployed check.
- The saved HJF mapping used a rest connector rather than Shopify. The gate depends on the flow (`fileIn`/`shopifyIn` are both inbound), which the unit specs cover for both, but a Shopify connector was not driven.
- The real Academically Gifted mapping (AC 9) is now deployable but unconfirmed: it needs someone to open it in prod and save, which was not done.
- The grouped panel's actions were exercised on a `sales_order` header section only: the Lines section, an outbound mapping (Add fallback is hidden there), a Shopify connector, the Dictionaries and Test Mapping tabs, and the template editor mount were not driven in a browser.
- The prod rollout skipped the usual QA step at Harry's instruction ("send it to prod as you go"); the ticket has not been through QA.

## Rollout & rollback
<!-- Added on demand. Written at plan time; amend in place as it changes.
     `Shared state touched:` is the single home for the five classes git does not own — a dev
     deploy, a prod config write, a Datadog monitor, a CI var or secret, cross-repo IaC. Reverting
     the branch undoes none of them, so if they are not written here they are not written down. -->

- **Order:** 1 → 2 → 4 → 5, with 3 anywhere and 6 last (needs 4). Increments 1-2 ship alone as the fix. Increment 4 on its own leaves the old red box and the panel both showing, which is harmless, so 4 and 5 should merge close together. No cross-repo ordering: config-service and pkg-node are unchanged.
- **Flags/config:** none.
- **One-way doors:** none. It is UI validation with no data migration. Once promoted, the Save gate loosens for every customer mapping at once, and previously blocked configs become saveable.
- **Rollback:** per increment `git revert`.
- **Shared state touched:** dev fuse-ui, whose branch deploys overwrite master (redeploy master after verifying), and a write to a dev business's mapping in config-service during the increment 2 and 5 checks. Name the business (HJF), and restore the mapping afterwards.
- **Proof in prod:** the AG Retail ID mapping saves with the default ECOM and `shipping.method` is editable. There is no metric. Baseline is the failing save reported 14 Sep.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-10-19** — Increments 4 and 5 shipped as one PR (#338): the panel without its Add actions would have sat beside the old per-table button, so the old check was deleted in the same change. The `defaultsSatisfyRequiredKeys` deviation below stands.
- **2026-10-19** — The Fallback rename went beyond the editor module: `template-default-marks.tsx` told users to "Add one in the Default Values tab", so the template-library headings and the template validation messages were renamed too. Code identifiers and `lookup()`'s third-argument label "Default" were left alone.
- **2026-10-19** — Fixed `serializeArg` (the DSL string serializer) to escape backslashes while building Always send, because a value like `a\b` lost its backslash and one ending in `\` broke the quoting. It also affects the expression builder.
- **2026-10-19** — Shipped to prod slice by slice at Harry's instruction, skipping QA and peer review; each prod gate was approved after reading its plan and the commit range. No #bifrost-forge announcements, per his "just ship" preference.
- **2026-10-19** — Deviation from increment 2: `defaultsSatisfyRequiredKeys` is kept, not removed. Templates can cover outbound use cases, where a default must still satisfy a required field, while a customer outbound mapping stays rules-only (a default on SFTP egress emits no column). computeCoverage takes `defaultsSatisfy` for that case; inbound flows always count defaults, so the customer editor needs no flag.

- **2026-10-19** — A conflict (fixed rule plus a default) is reported for any field, not only required ones, matching AC 3 ('a field has two sources'). Gaps and checks stay required-only. Increment 1.
- 2026-10-19 — Always send X converts and deletes the fallback rather than keeping it. Harry first chose to keep it (B) before seeing the design page, then delegated the call once the page showed the action "resolves it". Detail under Assumptions.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
(none)
