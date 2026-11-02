---
ticket: FUSE-1253
title: EDIFACT egress option on the SFTP connector form behind FEATURE_FLAG_EDI_EGRESS
service: fuse-ui
status: complete
created: '2026-09-24'
updated: '2026-10-09'
repo: /home/hjf/code/fuse/fuse-ui
worktree: /home/hjf/code/fuse/fuse-ui/.claude/worktrees/edi-egress
branch: hjf/fuse-1253-edi-egress
base: origin/main
base_sha: ae14bc540
pr: '275'
tags:
- waypoint
- plan
impl_model: sonnet
impl_effort: medium
programme: edi-support
unit: E5
---
# FUSE-1253 — EDIFACT egress option on the SFTP connector form behind FEATURE_FLAG_EDI_EGRESS

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
[FUSE-1253](https://globalfreight.atlassian.net/browse/FUSE-1253). The SFTP connector edit form's output-file-type dropdown gains **EDIFACT** (`egressFiletype: "edi"`). Choosing it shows the envelope fields (sender and receiver id plus qualifier, and a test indicator) and a warning listing which confirmation types have no EDIFACT message and won't be sent. It writes what [[persist-and-validate-ediegress-on-sftp-connector]] accepts, and [[edifact-confirmation-egress-desadv-recadv-behind]] reads it.

> SUPERSEDED 2026-10-09 — the flag is now wired into the iac and on in dev (`iac/env/dev.tfvars`, `0b593e1`); prod still sets nothing.
> The sentence below is kept as the state at merge.

The option is hidden behind `FEATURE_FLAG_EDI_EGRESS`, which is **set in no environment** (following the FUSE-1220 precedent). It is verified locally against dev data.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. With the flag off, the form, the display and the PATCH payload are unchanged: there is no EDIFACT option and no `ediEnvelope` key.
- [x] 2. With the flag on (locally, against dev), choosing EDIFACT and filling in the envelope saves `egressFiletype: "edi"` and `ediEnvelope`. The display then shows **EDIFACT** instead of falling back to CSV, the audit summary records the change, and pending changes flags it as a dangerous edit.
- [x] 3. With EDIFACT chosen, the form lists the confirmation types that won't be sent (currently returns only), plus a G3 warning that the connector's confirmation mapping must be rewritten for the EDIFACT messages.
- [x] 4. A non-EDI save on an EDI connector keeps `egressFiletype` and `ediEnvelope`, and resends `stockAdjustmentsEnabled`.
> SUPERSEDED 2026-10-09 — held for this PR's diff; `0b593e1` later wired `FEATURE_FLAG_EDI_EGRESS` into iac and on in dev, as planned under the rollout ticket.
- [x] 5. The flag isn't set in any iac.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `code/src/config.ts`, with a new `featureFlags.ediEgress` next to `mappingDictionaries` (`:106`, `:128`, `:232`).
- The prop is threaded through `connector/[connectorId]/page.tsx:30-36`, then `ConnectorLandingPage` (`connector-landing-page.tsx:122-128`), then `SftpConnectorConfig`.
- The form (`sftp-connector-config.tsx:43-67`, `:229-239`) and the display (`sftp-connector-display.tsx:166-175`), which maps anything that isn't jsonl to the "CSV" label and needs an `edi` case.
- `storefronts.action.ts:176-187`, which types `egressFiletype` as `'csv' | 'jsonl'`.
- `pending-changes.logic.ts` (`DANGEROUS_PATH_PREFIXES` `:4-8`, `SftpFormValues` `:15`, `sftpComparable` `:38`) and `audit-summary.logic.ts:33`.
- The create form (`create-sftp-ingress-form.tsx`, `new-connector.schema.ts`) hardcodes `csv`. It is left alone, since EDI is edit-only.
- The generated config-service client, regenerated from the **deployed dev** openapi (`code/package.json:15`).

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- **Flag convention: off unless "true", set nowhere, not in iac** (the FUSE-1220 precedent). Wiring it into iac is FUSE-1256's job, and that happens only after sftp-connector's prod flag is on.
- **Codegen reads the deployed dev openapi**, so the gate is config-service merged and deployed to dev from main. **Found 2026-09-24:** `gen-config-service-client` still points at `…/api/v1/docs/openapi.yaml`, which config-service main no longer serves (since #215 Nest generates the spec at `/api/v1/docs-json`). Increment 1 must repoint codegen first, or coordinate with the "regenerate client from generated spec" plan.
- **Where the covered/uncovered list lives:** the set of types with an EDIFACT message is a UI-side constant, everything except returns, until FUSE-1255 settles the returns message. No API exposes it today, and adding one is speculative.
- **Coordinate with the active fuse-ui "regenerate client from generated spec" plan.**
- **Decision: no starter DESADV/RECADV mapping template here.** The rule names depend on Charlotte Tilbury's required fields (FUSE-1255). Any future template must never overwrite an existing mapping (FUSE-1010).

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
- [x] 1. Add the plumbing (AC 1,5): — flag plumbing; flag-off payload has no ediEnvelope; 696 tests — done: 791c275
  - `featureFlags.ediEgress` threaded down as a prop;
  - the client regenerated;
  - `storefronts.action.ts` types;
  - `SftpFormValues` and `sftpComparable`, with `ediEnvelope` omitted from the payload unless the type is `edi`.

  Nothing becomes visible. (AC 1,5) — verify: a flag-off local run that captures the PATCH payload with no `ediEnvelope` key and an unchanged `egressFiletype`; flag-off screenshots identical to main; no iac diff.
      gate: config-service increment 1 merged and deployed to dev from main
            [x] confirmed — config-service#226 (`1aef7bc`) deployed dev + prod via Deploy on main, 2026-09-24
- [x] 2. Build the EDIFACT option, envelope fields, the uncovered-types list, the G3 warning, the display label, the pending-changes entry and the audit summary. (AC 2,3,4) — verify: locally with the flag on against dev (fuse-ui screenshot recipe), on the HJF test connector: save EDIFACT; GET shows both fields; the audit entry appears; a non-EDI save preserves them; the display reads EDIFACT; the warnings are shown. Take one screenshot per state and none that show secrets. — local vs dev: save/GET round trip 99→03, warnings, dangerous confirm, audit; screenshots on fuse-ui#275 — done: 791c275

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
- 2026-10-09 [sign-off] Re-checked the red `Terraform Apply / terragrunt`. Job 107679047096 (run 36012810065, `Preview Environment Deploy`, head `791c275`) reads `conclusion: cancelled`, completed 14:31:20Z, 27s after the merge; its logs have expired (HTTP 410). It is the PR preview env, not dev or prod. The merge commit's `Deploy` run 36013360461 has `terraform-apply-dev` and `terraform-apply-prod` both SUCCESS (checked via GraphQL statusCheckRollup on `ad6614e`). Later `Deploy` runs on `71ce17a` (37496773954, includes `0b593e1`) and `d6fc38c` (37636315138) also apply dev and prod green. Live `fuse-ui-app-dev` runs image `dev-759cb0e` with `FEATURE_FLAG_EDI_EGRESS=true`. `wp signoff` still prints BLOCKED because it counts the cancelled preview job on the PR head.
- 2026-10-05 [sign-off] The red `Terraform Apply / terragrunt` on fuse-ui#275 is the **PR preview-environment** apply (workflow `Preview Environment Deploy`, run 36012810065, job 107679047096), not a dev/prod apply. Its `Run Terragrunt` step concluded `cancelled` at 14:31:20Z, 27s after the merge (14:30:53Z); there is no error in the log, and `gh pr checks` shows a cancelled job as `fail`. `Preview Environment Destroy` (run 36013364074) then succeeded (Plan Destroy, Destroy, Verify Teardown, Clean Up State all pass), so the preview env was torn down cleanly and nothing is left to reapply. The real applies ran in `Deploy` run 36013360461 on `ad6614e`: `terraform-apply-dev` and `terraform-apply-prod` both success (14:34Z / 14:36Z). Prod `fuse-ui-app-prod` is now Ready on revision `00058-l4m`, image `prod-fdab993`, and `ad6614e` is an ancestor of `fdab993`. `FEATURE_FLAG_EDI_EGRESS` still has 0 hits under `iac/` on origin/main (AC 5).
- 2026-09-24 [merge+prod] fuse-ui#275 squash-merged as `ad6614e`; prod Deploy approved (plan: image `ae14bc5`→`ad6614e` + standing sidecar/scaling drift, no flag/env change), `fuse-ui-app-prod` Ready on `ad6614e`, no prod error logs in the 30 min after. Flag unset in every env → inert in prod.
- 2026-09-24 [AC 1-5] 696 tests (form-logic: flag-off no EDIFACT option/no `ediEnvelope` key, edi connector keeps edi with flag off, non-EDI save omits envelope + resends `stockAdjustmentsEnabled`); local vs dev HJF test connector with flag on: receiverId 03→99→03 saved and read back via GET, dangerous-change confirm, uncovered-types + mapping-rewrite warnings, audit entries; screenshots on fuse-ui#275; `grep EDI_EGRESS iac/` = 0 hits.
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
> SUPERSEDED 2026-10-09 — the flag is on in dev (live `fuse-ui-app-dev` env var `true`). Still unproven here: the deployed flag-on UI was not driven this session.
- The flag has not been switched on in any deployed environment (by design: it goes on only after sftp-connector can write EDIFACT, tracked on FUSE-1256). The deployed flag-on UI is therefore proven only locally against dev config-service, not on a deployed fuse-ui.

## Handback
<!-- Append-only, newest first. Written by `wp handback`, never by hand.
     Sign-off never clears this section — a refuted approach is exactly what a
     later session needs and what ## Learnings would have deleted. -->

### 2026-09-24 15:37
- **stopped:** Sign-off blocked only by the cancelled PR preview-env 'Terraform Apply' check on merged fuse-ui#275 (cancelled deliberately after merge; its destroy ran). Everything else passes. Harry to decide: accept and complete, or leave active until the flag-on rollout (FUSE-1256).
- **turn:** me

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-10-09** — Signed off with the PR's cancelled preview-env Terraform Apply check cleared as a non-gating artefact: merge-commit Deploy run applied dev and prod green, and dev now runs the flag on. The EDI-egress flag wiring in iac landed separately (0b593e1), after this PR.

- **2026-09-24** — Client regenerated from committed config-service openapi.yaml (post-#226), not the deployed dev URL. Flag-off: an edi-stored connector still shows EDIFACT as its current value (never hide a stored value). Blank-envelope form default qualifier ZZ is form-only.

- **2026-09-24 (Harry)** — Scope now covers every confirmation type except returns: FGR (Snap R10 receipt) to RECADV, and WOC component lines (Snap S10 shipment) to INVRPT with finished-good lines excluded to avoid double-booking. Returns stay out until one message is confirmed (the evidence is split between RECADV echoing the RMA and an INVRPT return adjustment), tracked in FUSE-1255. FGR/WOC are gated on a poller follow-up (line batch + work-order references); stock-adjustment INVRPT is gated on FUSE-1088.

- **2026-09-24 (Harry)** — INVARIANT: the EDI egress path is customer-agnostic, and Charlotte Tilbury is config, not code. No serializer, assembly step, dispatch table or UI rule may branch on, or hardcode, a customer or partner. Every partner-varying value (association code, BGM document code, NAD/RFF/QTY/DTM qualifiers, INV/STS codes, envelope IDs) is caller- or config-supplied, with an EANCOM D.96A default. CT's sample files are conformance tests driven by a CT config fixture. The type-to-message mapping follows EANCOM practice and Snap's resource model (S10 work-order shipment, R10 finished-goods receipt), not CT.

- **2026-09-24 (Harry)** — Scope widened from goods-out/goods-in to the five confirmation types Charlotte Tilbury's samples and Puig's guides both document: goods-in to RECADV 352, goods-out to DESADV loading 701, pack to DESADV pack 351, pick to OSTRPT 93E, stock adjustment to INVRPT 78. Returns, WOC and FGR stay unmapped (FUSE-1213 epic note, 24 Sep). Codes Charlotte Tilbury hasn't confirmed come from mapping config, not code.

- **2026-09-24 (Harry)** — Config shape switched from a separate ediEgress block to egressFiletype "edi" + an ediEnvelope block (Harry's call). A cross-repo grep showed only types, config-service, fuse-ui and sftp-connector read egressFiletype, and remote-config consumers only resolve their own connector type, so the enum-widening hazard is confined to sftp-connector and handled by ordering (sftp increment 1 in prod first). Types with no EDIFACT message write nothing and report why, and the UI warns which types they are; an edi connector never falls back to CSV.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
(none)

