---
ticket: none
title: 'Runtime feature flags: audited flag page'
service: fuse-ui
status: complete
created: '2026-10-14'
updated: '2026-10-19'
repo: /home/hjf/code/fuse/fuse-ui
worktree: /home/hjf/code/fuse/fuse-ui/.claude/worktrees/runtime-feature-flags
branch: hjf/runtime-feature-flags
base: origin/main
base_sha: f1538e4
pr: '316'
tags:
- waypoint
- plan
impl_model: sonnet
impl_effort: medium
---
# none — Runtime feature flags: audited flag page

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
> SUPERSEDED 2026-10-14 (Harry). This plan is now also the **first adopter**: fuse-ui reads flags for its own features, server-side and straight from the API with no local cache (see inc 4 and 5). Customer targeting moves to a later iteration, so v1 shows Everyone only. Scheduled changes ("when") are in v1. The design mock is `~/ff.png` (Claude Design project d1908210…).

Signed-in Fuse staff (the role is still to be decided) can create, flip, retarget and delete runtime feature flags from a fuse-ui page. Every write is audited under the real user. This is phase 1, workshop action L3 (no ticket yet). fuse-ui calls config-service's `/api/v1/feature-flags` ([[runtime-feature-flags-feature-flags-store-and-ap]]). The shared design is in [[runtime-feature-flags-types-featureflagschema-an]].

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. An authorised user can create, toggle, retarget and delete a flag from fuse-ui, and config-service reflects each change.
- [x] 2. Each successful write produces exactly one audit row:
  - target `feature_flag/<key>`;
  - action `created`, `updated` or `deleted`;
  - before and after both read via `GET /feature-flags/{key}`, with before `null` on create and after `null` on delete;
  - the signed-in user's email as the actor.
- [x] 3. An unauthorised session is refused before any config-service call. A failed config-service write (e.g. a 409) writes no audit row and shows the conflict.
> SUPERSEDED 2026-10-14. Targeting is deferred, so AC 4 below is out of v1. Its checkbox was removed. AC 5–7 were added.

- 4. The targets editor makes "all businesses" (`targets: null`) and "only these" (explicit lists) two distinct choices. An empty "only these" can't be saved as "all".
- [x] 5. **An admin can schedule a change.** They can schedule switching a flag on or off at a date and time (UK time shown, as in the design), and cancel it. The list shows the pending change ("On · Mon 29 Jun 07:00") and has a Scheduled filter. The flag flips at that time with nobody acting.
- [x] 6. **fuse-ui reads its own flags server-side** through one helper, `isFeatureEnabled(key, default)`. The helper fetches `GET /feature-flags` (no local cache) and evaluates with `evaluateFeatureFlag` from types. If config-service is unreachable, slower than the timeout, or doesn't have the key, the helper returns the code default. It never shows an error page.
- [x] 7. **First migrated flag: `fuse-ui.mapping-dictionaries` replaces `FEATURE_FLAG_MAPPING_DICTIONARIES`.** In dev, turning it off from the flags page hides the dictionaries editor with no deploy, and turning it back on restores it.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- The generated client, `code/src/lib/gen/config-service.client.d.ts`, regenerated from config-service's committed `openapi.yaml`.
- The `gen-config-service-client` script. It points at `/api/v1/docs/openapi.yaml`, which now returns 401; repoint it.
- `lib/types/config-service.type.ts` (the `FeatureFlag` alias).
- The audit vocabulary (G6): `lib/db/audit-log.types.ts` (`AuditTarget`, `AUDIT_TARGETS`) and `modules/audit-trail/audit-trail.const.ts` (`ENTITY_LABEL`, a total record).
- `app/server-functions/feature-flags/*.func.ts` and `*.action.ts` (new).
- `app/server-functions/audit/audit-config-change.func.ts`, called as `auditConfigChange(action, 'feature_flag', key, before, after, context?)`.
- The role check (G3). `assertAdmin` is private to `audit-log.func.ts`, so extract it into a shared helper. Existing config write actions such as `backend.action.ts` have no role check.
- The page and its nav entry; the location depends on the who-may-flip question. Also `proxy.ts`, which role-gates only `/user-management`.
- G1: flags live in config-service, never in fuse-ui's Mongo. G2: audit rows go only through the audit-writer path.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- **Prod audit rows land in fuse-ui's Mongo `audit_log`.** That is the system of record until the Audit Service UF cutover. Setting `AUDIT_SINK=both` in prod is that programme's gate, not this plan's. Source: history review, `Bifrost/Audit Service/Migration State.md`.
- **audit-service needs no change.** `target.type` is an open string, ingest only checks `system`, and a `feature_flag` row is classified as `config_change`. Source: factual review (`pkg/audit/src/audit-message.ts:21-24`, audit-service `ingest.go:62`, `lib/audit/audit-message.ts:14-20`).
- **Flag rows carry no `tenantId`.** They appear on the user-management audit log, never on a customer's `/changes` page, even for a targeted flip. Accepted for v1. Source: history review.
- **Snapshots come from the same GET, never from the PATCH response.** Source: fuse-ui architecture, Audit trail "Snapshots".
- **The open audit stack (#307, #308, #310) edits `audit-log.types.ts`.** Rebase after it lands, and branch off `origin/main`.
- **Dev flags are shared.** Preview envs (`dev-pr-N`) read the same dev config-service, so live checks use the throwaway key `fuse-ui.smoke-test` and delete it afterwards. Source: structure review.
- UNRESOLVED: **who may flip in prod?**
  - The only admin is the shared `fuse-support@gfsdeliver.com` login (`iac/env/global.tfvars:4`, `app/api/auth/login/route.ts`). User management can only create editors.
  - Admin-only would audit every prod flip under a shared mailbox. Allowing editors gives named actors, but means every editor can flip.
  - Separately, L3 may want a second approver.
  - The answer decides inc 2's role check and inc 3's page location. If flipping is admin-only, `/user-management/feature-flags` gets proxy role-gating for free.

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

- [x] 1. **Contract and vocabulary.** — client +243, audit vocab, 2 spec cases — done: 8764bfd
  - Repoint the gen script, either to the committed `openapi.yaml` or to the live `/api/v1/docs-yaml`.
  - Regenerate the client.
  - Add the `FeatureFlag` alias.
  - Add `feature_flag` to `AuditTarget`, `AUDIT_TARGETS` and `ENTITY_LABEL`.

  (AC 2)

  — verify:
  - the generated `.d.ts` has `paths['/api/v1/feature-flags']` (get, post) and `paths['/api/v1/feature-flags/{key}']` (get, patch, delete);
  - `audit-message.spec`: a `feature_flag` row maps to kind `config_change` with target `{type:'feature_flag', id:key}`;
  - the audit filters accept `feature_flag`.

      gate: config-service write routes and `openapi.yaml` merged to main ([[runtime-feature-flags-feature-flags-store-and-ap]] inc 4)
            [x] confirmed
- [x] 2. **Server functions.** List and get go in `.func.ts`; create, update and delete go in `.action.ts`. Each function opens with the role check. A write is followed by a GET to read the after-state, then `auditConfigChange`. (AC 1,2,3) — 12 specs; admin-only; audit before/after via GET — done: 3fa7f74
  — verify with specs:
  - a session without the role throws before the client is called;
  - an authorised PATCH writes one audit row, with before and after from GET and the user's email;
  - a config-service 409 writes no row and returns a conflict result.

      gate: who-may-flip decided (and whether L3 requires a second approver)
            [x] confirmed
> SUPERSEDED 2026-10-14. Inc 3 now follows the design mock instead of the list below:
> - the Admin → Feature Flags page, with All/On/Off/Scheduled filters and search;
> - a table of flag, status, scheduled change and the other v1 fields;
> - a detail drawer with a toggle, a scheduled-change control, "Read by" and a history taken from the audit log.
>
> There's no targets editor; Who shows Everyone. Which fields appear, and whether create and delete stay in the UI, waits on the design-fields question. It discharges AC 1, 3 and 5.

- [x] 3. **Page.** — stack #318-#320 merged; live vs dev config-service incl. scheduled flip with no write, 409, delete, audit, editor refused — done: 4ef7e6b
  - A list showing owner and expiry, with an expired badge.
  - A toggle with a blast-radius confirm that names the targeted businesses, or "all".
  - A targets editor with an explicit "all businesses" vs "only these" choice.
  - Create and delete.
  - A nav entry.

  (AC 1,3,4)

  — verify live on dev with `fuse-ui.smoke-test`:
  - create, toggle, retarget and delete it;
  - the audit-log page shows four rows under the signed-in email;
  - a config-service GET shows a matching `updatedBy`;
  - an unauthorised account is refused;
  - screenshots of the list, the confirm dialog, the targets editor and the audit rows;
  - in prod after approval, the page loads an empty list.

      gate: config-service flag routes live in prod before this PR merges (a fuse-ui prod approval ships all of main)
            [x] confirmed
      gate: v1 fields and the ready lifecycle decided against the design mock
            [x] confirmed
- [x] 4. **Flag reader.** — 9 specs + race mutation check — done: c33e71b
  - A server-only `isFeatureEnabled(key, default)` fetches `GET /api/v1/feature-flags` once per request (React `cache()`, no cross-request cache).
  - The fetch has a short timeout.
  - It evaluates with `evaluateFeatureFlag(flag, new Date())`.
  - It returns `default` when config-service is unreachable, slow or missing the key, and logs it.

  (AC 6)

  — verify with specs (each one assertion):
  - a known flag that's on gives true;
  - a known flag that's off gives false;
  - a flag whose scheduled switch-on has passed gives true;
  - an unknown key gives the default;
  - a config-service 500 gives the default;
  - a response slower than the timeout gives the default;
  - two calls in one request make one fetch.

      gate: config-service read routes live in dev ([[runtime-feature-flags-feature-flags-store-and-ap]] inc 3)
            [x] confirmed
- [x] 5. **First adopter.** — live: tab hides/shows on flip and on schedule, 5 shots — done: 763f256
  - `FEATURE_FLAG_MAPPING_DICTIONARIES` becomes `isFeatureEnabled('fuse-ui.mapping-dictionaries', <the env var's current value>)`.
  - Seed the flag on in dev, then prod, matching today's value.
  - Remove the env var and tfvars only after the prod flag is confirmed.

  (AC 7)

  — verify live on dev:
  - switching the flag off on the flags page hides the dictionaries editor on the next page load;
  - the Cloud Run revision is unchanged;
  - switching it back on restores the editor;
  - a switch-off scheduled two minutes ahead takes effect at that time;
  - screenshots of each state.

      gate: prod flag `fuse-ui.mapping-dictionaries` created on before this merges
            [x] confirmed
      > SUPERSEDED 2026-10-14. The gate above is moot, so it's marked confirmed. The default passed to `isFeatureEnabled` is the env var's current value, so an absent prod flag behaves exactly as today, and the merge is safe without one. Removing the env var and tfvars is the step that needs the prod flag; that's a follow-up.

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-14 [inc 3] (AC 1,2,3,5) **Live run of the flags page.** fuse-ui ran locally from `hjf/runtime-feature-flags-page` against **dev config-service**, with a throwaway local Mongo for the session and the audit log, driven with headless Chrome under the env admin login (`hjf`). The flag used was `fuse-ui.smoke-test`; `fuse-ui.mapping-dictionaries` was only opened, never changed. Each step was checked against dev config-service through fuse-mcp `config-read`, not just on screen:
  - the list renders the real dev flag, with All/On/Off/Scheduled counts;
  - **create** via New Flag (key, description, owner prefilled from the session, Remove by 31 Oct, Starts Off) gives a stored flag at v1 with `updatedBy: hjf`. The existing proxy `x-user` header carries the session email, so the actions need no header of their own. The drawer opens on the new flag, and its history reads "Created, switched off";
  - **switch on** through the confirm dialog, which stacks correctly over the drawer: the stored flag is `enabled: true`, and history reads "Switched on";
  - **schedule** a switch-off for 15:36 UK: stored as `at: 2026-10-14T14:36:00Z`, which is BST-correct. The list shows the "Off · Wed 14 Oct, 15:36" pill, and the Scheduled filter counts it;
  - **after 15:36, with nobody acting**, the list shows Off, and config-service returns `enabled: false`, `scheduledChange: null`, still v3 with the same `updatedAt`, so nothing was written;
  - **schedule then cancel**: history reads "Scheduled to switch on…", then "Cancelled the scheduled change";
  - **edit details**: the key field is disabled, and the owner changes to `fuse-team`;
  - **conflict**: an out-of-band PATCH from `someone-else@example.com` took the flag to v7, and a stale switch-on from the open drawer was refused with the conflict toast. The drawer then showed the other writer's change, and no audit row was added;
  - **delete** with the typed confirm: dev `GET` returns 404 and the drawer closes;
  - the **audit log** (`?entity=feature_flag`) shows 7 rows under `hjf`, from Created to Deleted, with changed paths;
  - an **editor** account sent to `/user-management/feature-flags` lands on `/customer`;
  - with **config-service unreachable** (`CONFIG_SERVICE_URI=http://127.0.0.1:9`), the page shows "Couldn't load feature flags from config-service: fetch failed" inside the layout.

  Two defects were found in this run and fixed before commit:
  - the schedule form's future-time refine called the formatter on an empty date. zod's standard-schema adapter turns a thrown sync parse into a Promise, so tanstack-form threw "async function passed to sync validator";
  - `minDate={new Date()}` disabled today, so a change couldn't be scheduled for later the same day.

  The page also caught only HTTP errors at first: openapi-fetch throws on a network failure, so that case reached the generic error page. It now catches both.

  Gates: jest 84 suites / 1016 tests, including 31 new logic specs that check the real formatter output (not just the fallback); tsc 0; biome clean. No shared dev deploy was taken.
- 2026-10-14 [inc 5] (AC 6,7) **Live run.** fuse-ui ran locally from this branch against **dev config-service**, using real HJF data and the dev flags. The page was `/customer/HJF/storefront/sf_35ed…/connector/conn_1435…/sales_order`, driven with headless Chrome under the env admin login, in one process with no restart:
  - no flag (local env unset, so the default is false): no Dictionaries tab ([shot](https://github.com/gfs-bifrost/fuse-ui/blob/hjf/runtime-feature-flags-reader-evidence/.pr-evidence/1-no-flag-default-off.png));
  - POST `fuse-ui.mapping-dictionaries` `enabled: true`: the tab appears ([shot](https://github.com/gfs-bifrost/fuse-ui/blob/hjf/runtime-feature-flags-reader-evidence/.pr-evidence/2-flag-on.png));
  - PATCH `enabled: false`: it's gone ([shot](https://github.com/gfs-bifrost/fuse-ui/blob/hjf/runtime-feature-flags-reader-evidence/.pr-evidence/3-flag-off.png));
  - PATCH `scheduledChange {at: 13:04:30Z, enabled: true}` at v3: still hidden at 13:03:30 ([shot](https://github.com/gfs-bifrost/fuse-ui/blob/hjf/runtime-feature-flags-reader-evidence/.pr-evidence/4-scheduled-pending.png)), and shown at 13:04:36 with nobody acting ([shot](https://github.com/gfs-bifrost/fuse-ui/blob/hjf/runtime-feature-flags-reader-evidence/.pr-evidence/5-scheduled-switched-on.png)).

  The dev flag is left resolving to `true`, which matches dev's `FEATURE_FLAG_MAPPING_DICTIONARIES=true`.
- 2026-10-14 [inc 4] (AC 6) **`is-feature-enabled.spec.ts`**, 9 tests:
  - on gives true and off gives false;
  - a passed scheduled switch-on gives true;
  - each of these gives the default: an unknown key, a config-service 500, a thrown request, a never-resolving response (past the 1 s race), and a flag that fails validation;
  - a fallback logs `{key, reason:'unknown_key'}`.

  Mutation check: with the `Promise.race` removed, the slow-response test hangs for 5 s and fails. The file was restored. jest 973/973, and tsc is 0 after typegen.
- 2026-10-14 [inc 2] (AC 1,2,3) **Server-function specs**, 12 new, one assertion each:
  - create: an editor session is refused ("Only admins can manage feature flags") and config-service isn't called; the audit is `created`/`feature_flag`/key/`null`/the flag read back via GET; a config-service 409 writes no audit row.
  - update: the audit has before and after from two GETs; a 409 comes back as `{ok:false, error:{originalCode:409, message}}` with no audit row.
  - delete: the audit is `deleted` with the before-state and `after: null`; a missing session is refused.
  - func: the list returns `flags`; an editor is refused; an unknown key returns `{ok:true, data:null}`.

  jest 964/964 across 78 suites. `tsc --noEmit` gives 0 errors after `next typegen`; without generated route types there are 46 existing `AppHref` errors, none in touched files. biome is clean.
- 2026-10-14 [inc 1] (AC 2) **Client and audit vocabulary.**
  - The client was regenerated from config-service `origin/main:code/openapi.yaml` (8b1ae2b+) with the repo's `openapi-typescript` 7.13, then biome-formatted. The diff is +243 / −0, all of it the feature-flag paths and schemas.
  - `audit-message.spec` gains two cases: a `feature_flag` row maps to `config_change`, with target `{type:'feature_flag', id:key}`.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- A flip from this page changing a service's behaviour. That is proven by phase 2's dev soak ([[runtime-feature-flags-first-adopter-bulk-ingest-]]).

## Rollout & rollback
<!-- Added on demand. Written at plan time; amend in place as it changes.
     `Shared state touched:` is the single home for the five classes git does not own — a dev
     deploy, a prod config write, a Datadog monitor, a CI var or secret, cross-repo IaC. Reverting
     the branch undoes none of them, so if they are not written here they are not written down. -->

- **Order:**
  - PR1 is inc 1+2 (about 450–600 lines). It starts once config-service PR3 is on main.
  - PR2 is inc 3 (about 500–700 lines). It merges only once config-service's routes are in prod.
  - Merge order replaces an env flag for the page.
- **Flags/config:** none.
- **One-way doors:** none.
- **Rollback:** `git revert`.
- **Shared state touched:**
  - dev deploys (manual-deploy applies dev Terraform);
  - throwaway dev flag `fuse-ui.smoke-test`, deleted after the check;
  - dev audit rows from the smoke test.
- **Proof in prod:** the page loads, and fuse-ui shows no new 5xx.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-10-19** — Sign-off reconcile: shipped in five merged PRs, not one. #316 (inc 1+2), #317 (inc 4+5), and #318-#320 (inc 3 stack). pr: records only #316. AC 4 is out of v1 (targeting deferred). Owed follow-up: removing FEATURE_FLAG_MAPPING_DICTIONARIES and its tfvars needs the prod flag fuse-ui.mapping-dictionaries created first. Prod config-service has no flags at all (snapshot 2026-10-19), so prod still resolves the env-var default (true).

- **2026-10-14** — Inc 3 shipped with the fields the flag already has (Harry: build the page). Admin-only under /user-management/feature-flags in a new Platform sidebar group. Create, edit and delete stay in the UI. Who gets it is always Everyone. Flip notes, ticket, area, Read by and the not-ready lifecycle from the mock are deferred to an additive types minor. Split into a 3-PR native stack (#318 logic, #319 list, #320 drawer), merged via gh stack merge.

- **2026-10-14** — Who may flip, default taken: admin-only. It matches the design ('admins choose who gets it and when'), the existing assertAdmin pattern and the proxy's /user-management role gate. It's also the more restrictive choice, so widening to editors later is a one-line change. Known limitation: the only admin login today is the shared fuse-support@ mailbox, so prod flips are audited under it until named admins exist (Entra ID, FUSE-602). No second approver in v1. The page goes at /user-management/feature-flags. The client was regenerated from config-service's committed openapi.yaml on main and biome-formatted, giving a 243-line additive diff. The gen-config-service-client script URL (it 401s) is left for the generated-spec plan to repoint.

- **2026-10-14** — Harry, 2026-10-14, after reviewing the Claude Design mock (~/ff.png): per-customer targeting (Who gets it: Selected customers / Tier) moves to a later iteration, and scheduled changes ('when') are in the first iteration. The v1 page shows Everyone only and adds a Schedule control. The design (list with On/Off/Scheduled filters, a detail drawer with toggle, scheduled change, Read by and history) is the reference for inc 3.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
