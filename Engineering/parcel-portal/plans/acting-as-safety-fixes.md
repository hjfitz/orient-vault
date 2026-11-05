---
ticket: none
title: Acting-as safety fixes
service: parcel-portal
status: draft
created: '2026-11-05'
updated: '2026-11-05'
repo: ilg-merak/parcel-portal
worktree: /home/harry/code/merak/parcel-portal/.claude/worktrees/acting-safety
branch: hjf/acting-safety
base: origin/main
base_sha: a8e92471c4e7cbef6860dcd20ed572c8403242d8
pr: null
tags:
- waypoint
- plan
programme: Parcel Portal
unit: C19
impl_model: opus
impl_effort: high
---
# none — Acting-as safety fixes

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
The 4 Nov audit of "acting as" found four bugs; this fixes them. **Stale tabs:** upload, manifest and export act for whichever customer the browser-wide cookie names at click time, not the one the page showed. **Stale cookie:** a cookie naming a deleted customer breaks every page. **Logout:** signing out while acting doesn't revoke the session in svc. **Audit:** logs often don't say which admin acted. Harry decided (4–5 Nov) that acting stays per browser, so a request that acts on a whole customer carries the customer its page showed, and svc refuses it on a mismatch. The plan also restores the documented rule that `X-Acting-Tenant` applies to session routes only. Sibling plan: [[acting-as-clearer-settings]] (C20).

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [ ] 1. If the customer behind the page no longer matches the browser's acting customer, five requests are refused with 409 `tenant_changed` and act on nobody: upload, the upload's status poll, Manifest, Refresh status and the Export download. The page says plainly that the customer was switched in another tab.
- [ ] 2. A cookie naming a deleted or unknown customer gets 404 `acting_tenant_not_found` on session routes. The UI clears that cookie and lands on Orders' "Pick a customer" with a notice. No page shows Next's "Application error".
- [ ] 3. Any unexpected error inside the signed-in app shows an error page offering Try again, Back to GFS and Sign out. Sign-out reaches `/sign-in` even when svc fails.
- [ ] 4. `POST /auth/logout` with `X-Acting-Tenant` set revokes the session: the next request with that token gets 401.
- [ ] 5. Every log line of a signed-in request carries `actorId`, audit events and "Request completed" included. User-management events name their subject `targetUserId`.
- [ ] 6. Tenant-less admin-only routes ignore `X-Acting-Tenant` and log no acting event: `/admin/tenants`, `/admin/mapping/*`, `/admin/layouts/*` and `/admin/demo-customer`.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- **Contract** (`apps/svc/openapi.yaml`), all additive:
  - `info.description`: `X-Acting-Tenant` applies to `session` operations only, and the new `X-Expected-Tenant` precondition is described;
  - codes `acting_tenant_not_found` (404) and `tenant_changed` (409);
  - a 409 `TenantChanged` response on `uploadImportFile`, `listImportFiles`, `manifestShipments`, `refreshShipmentStatus` and `downloadShipmentExport`, and a 404 on `getMe`.
- **svc:**
  - `internal/http/middleware/authorize.go` (`Authorize`, `actingTenant`), `internal/exceptions`, `internal/http/respond`;
  - `internal/core/auth/logout.go`, `repositories/postgres/{queries/session.sql,sessions.go}`;
  - `internal/models/scope.go` (WithScope doc);
  - `internal/observability/{log.go,audit.go,catalog.go}` and a new `actor.go`;
  - `internal/http/middleware/middleware.go` (`Correlation`).
- **UI:**
  - `apps/ui/src/svc.ts` (`call`, `authed`, `getMe`, the upload pair, `manifestShipments`, `refreshShipmentStatus`, `downloadShipmentExport`), plus a new page-tenant module beside `zone.ts`;
  - `app/(app)/layout.tsx`, `app/(app)/actions.ts` (`signOutAction`);
  - new `app/error.tsx`, `app/(app)/error.tsx`, `app/(app)/acting/gone/route.ts`;
  - orders (`page.tsx`, `upload-panel.tsx`, `upload/route.ts`), shipments (`page.tsx`, `manifest-bar.tsx`, `actions.ts`), export (`page.tsx`, `export-picker.tsx`, `download/route.ts`).
- **Must keep working:** `e2e/smoke.spec.ts` (#91) relies on the following, so none may change:
  - the cookie name `pp_acting_tenant`;
  - the testids `upload-input` and `upload-result` and the text "imported with problems";
  - create-demo-customer redirecting to `/orders`;
  - delete-customer landing on `/settings/customers`.
- **Docs:** `apps/svc/README.md` (Tenant scoping, Logging), `apps/ui/README.md` (Orders upload bullet, which has been stale since #65), `docs/runbook.md` (who-did-it query; the `customer_deleted` upload note becomes API-only). After merge, the Waypoint `architecture.md` needs a refresh (see Learnings).

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- **UNRESOLVED (recommendation, needs Harry's yes):** guard only the five tenant-wide requests in AC 1.
  - Requests addressed by an order or shipment id (dispatch, cancel, pack, edit, void, print) can't reach another customer's data: rule G1 scopes every query to the request's tenant, so a stale tab gets 404.
  - Guarding them too means passing the page's customer through every action.
- **Stale-cookie landing:** Orders' pick-a-customer, the state #65 made the landing for an admin acting for no one.
- **The rename to `targetUserId` costs nothing now.**
  - No Datadog dashboard or live monitor reads parcel-portal log fields. The repo's monitors are off and key only on message, `@route`, `@httpStatus`, `@importStatus` and `@attemptState`; dashboards and monitors were searched on 5 Nov.
  - There are no users before D1 (Harry, 3 Nov).
- **`X-Expected-Tenant` is optional:** it's a precondition only when sent. The UI sends it on all five requests; making it required (428) can be added later.
- **The logout bug can't be hit through the portal UI:** `svc.ts` sends no acting header on `/auth/*`. It's fixed for direct svc clients and to keep the rule robust.
- **Out of scope:**
  - a path `{tenantId}` that doesn't exist returns 200 `[]` on list reads (follow-up);
  - a customer's settings dates showing in the acting zone, which is in [[acting-as-clearer-settings]].
- **Contract version:** #96 (export settings, 5.6.0) and its stack take 5.6–5.8. Whichever PR merges second renumbers `info.version` and reruns `make gen` and `make contract-check`.
- **Next 16:** dependabot #95 bumps Next 15 → 16, and its build fails. Land the UI PRs before it, or re-verify the error pages afterwards.
- **UI can't be checked on rc-hjf:** there's no `read:packages` and no browser here. UI evidence comes from an opt-in Playwright spec, `e2e/acting.spec.ts`, run against dev from `dev-smoke.yaml` by hand. Its sign-in needs the smoke login fixed (gate on increments 6–7).

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

**PR 1 (svc):** increments 1–4. **PR 2 (UI):** increment 5, off main, can ship first. **PR 3 (UI):** increments 6–7, verified once PR 1 is on dev.

- [ ] 1. svc: `X-Acting-Tenant` is read only on non-admin session routes; tenant-less admin-only routes scope to the admin's own tenant and log no acting event. A deleted or unknown acting tenant returns `ErrActingTenantNotFound`, which maps to 404 `acting_tenant_not_found`. Add header-taking variants of the e2e helpers (`do`, `send`, `act`, `get`), and parameterise the unit `actingRequest` by scopes and a chi `tenantId`. Update the README's Tenant scoping (AC 2,6) — verify:
  - unit (`authorize_test.go`): an admin-only route with an unknown header gives own scope and no "Admin acting" line; a stale acting tenant gives code `acting_tenant_not_found` (asserted on `ErrorBody.Code`, not just the status);
  - e2e (`tenants_delete_e2e_test.go`), with the deleted tenant in the header: `GET /admin/tenants`, `/admin/mapping/fields` and `/admin/layouts/dc-layout` return 200, and `GET /me` returns 404 `acting_tenant_not_found`.
- [ ] 2. svc: logout revokes in the session's own tenant: `WithScope(ctx, principal.Tenant)` in `LogoutUseCase`. `RevokeSession` becomes `:execrows` with `revoked_at = COALESCE(revoked_at, @revoked_at)`, and 0 rows is NotFound. The `WithScope` doc lists every caller: auth middleware, sign-in, slug import, apikey, demo, logout (AC 4) — verify:
  - unit: a fake revoker sees the principal's tenant while the scope is another;
  - integration: `TestSessionsCantRevokeAnotherTenantsSession` expects NotFound and a live session;
  - e2e `TestSigningOutWhileActingEndsTheSession` (in `e2e_test.go`): `/me` returns 401 afterwards. This test fails on main today.
- [ ] 3. svc: actor on every line. A new `observability/actor.go` gives `TrackActor`/`SetActor`, backed by an atomic slot. `correlationHandler` stamps `actorId`, `Correlation` calls `TrackActor`, and `Authorize` calls `SetActor` straight after `Authenticate`. User* audit events rename `userId` to `targetUserId`. Update the README's Logging section and add a runbook `@actorId:` query (AC 5) — verify:
  - unit: chain Correlation → Logger(`NewLogger`) → Authorize, and "Request completed" carries actorId;
  - e2e (`acting_e2e_test.go`), table-driven with one `t.Run` per event: create, disable, enable, update and set the password of a user, set a slug, delete and restore a tenant, and an upload while acting;
  - each audit line and its "Request completed" (matched by correlationId) carry the admin's actorId, and `/auth/login` carries none.
- [ ] 4. svc: an `X-Expected-Tenant` precondition, checked in `Authorize` after the scope is resolved. A mismatch is 409 `tenant_changed`, plus a warn event `Tenant changed refused`; a malformed value is 400. Add the 409 `TenantChanged` response to the five operations, and the README Tenant scoping paragraph (AC 1) — verify:
  - unit: a match passes, a mismatch gives code `tenant_changed`, a malformed value gives 400, and a customer naming another tenant gets 409;
  - e2e with an admin acting for globex while expecting acme:
    - upload returns 409 and no new object lands in the bucket;
    - the upload poll and refresh-status return 409;
    - manifest returns 409, the fake carrier records no commit, and the shipment stays booked;
    - the export CSV returns 409 with no body;
    - each request with a matching header succeeds.
- [ ] 5. UI: error pages. A shared panel for `app/error.tsx` (errors in `(app)/layout.tsx`) and `app/(app)/error.tsx` (page errors), with the digest as a reference, Try again, Back to GFS (`actAsAction(null)` then a hard navigation) and Sign out. `signOutAction` retries `signOut` once after 1 s, then logs and still clears both cookies; `redirect()` stays outside every try (AC 3) — verify:
  - biome, `build:check` and `build`, in CI;
  - on today's dev, a branch deploy where DevTools sets `pp_acting_tenant` to a random UUID shows the panel instead of "Application error", and both Sign out and Back to GFS work;
  - capture a screenshot through `acting.spec.ts` when its gate is open.
- [ ] 6. UI: a stale acting cookie cleans itself up.
  - `authed()` and `getMe` throw `ActingTenantGoneError` on 404 `acting_tenant_not_found`. The layout, the pages' existing session-expiry branches, the upload and export routes and the shipments actions all redirect to `/acting/gone`, with each redirect outside the try.
  - `acting/gone/route.ts` re-checks with `getMe` and clears the cookie only if svc confirms it is stale, then sends a 303 to `/orders?notice=customer-gone`.
  - The notice shows on Orders and on PickCustomer.
  - Update the UI README (AC 2) — verify, with `acting.spec.ts` against dev (opt-in, run by hand):
    - act for demo D1, delete D1 through the API from a second context, then:
      - navigating lands on Orders with the notice and "GFS (no customer)";
      - Download CSV and Manifest in the stale tab also land there;
    - `/acting/gone` while acting for a live customer keeps the cookie.
      gate: the smoke login signs in (DEV_SMOKE_ADMIN_EMAIL/PASSWORD fixed) and PR 1 is on dev
            [ ] confirmed
- [ ] 7. UI: stale tabs.
  - A page-tenant helper lives in its own module, as `zone.ts` does, using a React-`cache`d tenant list shared with the layout.
  - Orders, Shipments and Export pass the page's customer down to the five requests, which send `X-Expected-Tenant`. The upload route checks it before streaming the body, and the export link uses `expect=`, never `tenant=`.
  - Wording:
    - for upload, manifest, refresh and download: "You switched customer in another tab, so nothing was … Reload to see who you're acting for.";
    - for the poll: "Uploaded for {X}; reload to see its import".
  - Drop the upload pair's admin branch, which has been dead since #65. Update the UI README upload bullet (AC 1) — verify, with `acting.spec.ts` against dev:
    - set up demo customers D1 and D2, each with the sample uploaded and one order dispatched;
    - tab A acts for D1 while tab B switches to D2;
    - in tab A, upload, Manifest, Refresh status and Download are each refused;
    - D2 gains no file, no manifest and no download;
    - switching in tab B while tab A's import is polling shows the poll's wording;
    - after reloading, tab A works for D2;
    - screenshot each refusal for the PR, delete D1 and D2, and `dev-smoke` stays green.
      gate: the smoke login signs in and PR 1 is on dev
            [ ] confirmed

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- <YYYY-MM-DD> [inc <n>] <what was run, against what, and the observable result>

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- <what remains unproven, and what would prove it>

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->
- 2026-11-05 — Harry: acting stays per browser (the cookie), not per tab or in the URL. A request that acts on a whole customer carries the page's customer and is refused on a mismatch ("let's plan your two earlier prs", on my recommendation of 4 Nov).
- 2026-11-05 — Plan-time choices from review:
  - the stale-tab check lives in svc as a precondition header, not only in the UI, so svc e2e can prove it and new routes can't forget it;
  - 409 follows the `order_changed` precedent;
  - `actorId` is stamped by the log handler from a per-request slot, the `correlationId` pattern, rather than threaded through observer signatures;
  - the path-tenant existence check is deferred so it can't hold up the parts that must ship.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
- **The code drifted from #65's intent.** `X-Acting-Tenant` scopes every route without `{tenantId}`, admin-only ones included, though #65 and the contract say session routes only. This is the cause of the stale-cookie 404s on `/admin/tenants`. It's a candidate for known-context and an architecture guardrail.
- **Waypoint `architecture.md`/`operations.md` are stale.** They're anchored at 696cbd4 (29 Oct), before acting-as (#65), soft delete (#88) and the customer API, and neither mentions the acting header. Refresh them after this merges, with the guardrail "X-Acting-Tenant scopes session routes only; a tenant-wide act carries X-Expected-Tenant".
- **The ledger's #82 entry is wrong.** It says UploadPanel's `tenantId`/`tenantName` "still choose the admin upload route"; #65 had already removed their only caller.
- **UI work can't be verified on rc-hjf** (no `read:packages`, no browser). The repeatable route is a Playwright spec under `e2e/`, run against dev from `dev-smoke.yaml`.
