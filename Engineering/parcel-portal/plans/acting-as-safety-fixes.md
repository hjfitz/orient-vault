---
ticket: none
title: Acting-as safety fixes
service: parcel-portal
status: active
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
The 4 Nov audit of "acting as" found four bugs; this fixes them. **Stale tabs:** upload, manifest and export act for whichever customer the browser-wide cookie names at click time, not the one the page showed. **Stale cookie:** a cookie naming a deleted customer breaks every page. **Logout:** signing out while acting doesn't revoke the session in svc. **Audit:** logs often don't say which admin acted. Harry decided (4–5 Nov) that acting stays per browser, and (5 Nov) that every request a customer's page makes to act carries the customer the page showed, which svc refuses on a mismatch. That covers the five tenant-wide requests and every order, shipment and label action, so a stale tab always gets one plain message. The plan also restores the documented rule that `X-Acting-Tenant` applies to session routes only. Sibling plan: [[acting-as-clearer-settings]] (C20).

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [ ] 1. If the customer behind the page no longer matches the browser's acting customer, five requests are refused with 409 `tenant_changed` and act on nobody: upload, the upload's status poll, Manifest, Refresh status and the Export download. The page says plainly that the customer was switched in another tab.
- [ ] 2. A cookie naming a deleted or unknown customer gets 404 `acting_tenant_not_found` on session routes. The UI clears that cookie and lands on Orders' "Pick a customer" with a notice. No page shows Next's "Application error".
- [ ] 3. Any unexpected error inside the signed-in app shows an error page offering Try again, Back to GFS and Sign out. Sign-out reaches `/sign-in` even when svc fails.
- [ ] 4. `POST /auth/logout` with `X-Acting-Tenant` set revokes the session: the next request with that token gets 401.
- [ ] 5. Every log line of a signed-in request carries `actorId`, audit events and "Request completed" included. User-management events name their subject `targetUserId`.
- [ ] 6. Tenant-less admin-only routes ignore `X-Acting-Tenant` and log no acting event: `/admin/tenants`, `/admin/mapping/*`, `/admin/layouts/*` and `/admin/demo-customer`.
- [ ] 7. The same refusal covers every order, shipment and label action on a stale page, and each says what wasn't done ("nothing was dispatched"):
  - dispatch, cancel, pack and Check, in bulk;
  - edit, pack and dispatch one order;
  - void a shipment;
  - print or download labels.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- **Contract** (`apps/svc/openapi.yaml`), all additive:
  - `info.description`: `X-Acting-Tenant` applies to `session` operations only, and the new `X-Expected-Tenant` precondition is described;
  - codes `acting_tenant_not_found` (404) and `tenant_changed` (409);
  - a 409 `TenantChanged` response on the fifteen guarded operations, and a 404 on `getMe`:
    - AC 1's five: `uploadImportFile`, `listImportFiles`, `manifestShipments`, `refreshShipmentStatus` and `downloadShipmentExport`;
    - AC 7's ten: `dispatchOrders`, `cancelOrders`, `packOrders`, `validateOrders`, `editOrder`, `packOrder`, `dispatchOrder`, `voidShipment`, `getShipmentLabels` and `getParcelLabel`.
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
  - orders (`page.tsx`, `upload-panel.tsx`, `upload/route.ts`), shipments (`page.tsx`, `manifest-bar.tsx`, `actions.ts`), export (`page.tsx`, `export-picker.tsx`, `download/route.ts`);
  - for AC 7:
    - orders (`actions.ts`, `orders-table.tsx`) and the order page (`[id]/actions.ts`, `order-form.tsx`, `lines-panel.tsx`);
    - the shipment page (`[shipmentId]/void-panel.tsx`);
    - labels: `shipments/labels/route.ts`, `shipments/[shipmentId]/parcels/[parcelId]/label/route.ts`, `shipments/links.ts` and `shipments/print/page.tsx`;
    - printing: `printing/reasons.ts` and `printing/print-labels.ts`.
- **Must keep working:** `e2e/smoke.spec.ts` (#91) relies on the following, so none may change:
  - the cookie name `pp_acting_tenant`;
  - the testids `upload-input` and `upload-result` and the text "imported with problems";
  - create-demo-customer redirecting to `/orders`;
  - delete-customer landing on `/settings/customers`.
- **Docs:** `apps/svc/README.md` (Tenant scoping, Logging), `apps/ui/README.md` (Orders upload bullet, which has been stale since #65), `docs/runbook.md` (who-did-it query; the `customer_deleted` upload note becomes API-only). After merge, the Waypoint `architecture.md` needs a refresh (see Learnings).

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- **Harry, 5 Nov: guard every customer-facing write, not only the five** (AC 7).
  - Without the guard, an order or shipment action in a stale tab already fails safely: rule G1 scopes every query to the request's tenant, so it gets 404. The guard turns that 404 into the same plain message.
  - Check (`validateOrders`) books nothing, but it is an action button and calls Selector for the page's orders, so it's guarded.
  - Label printing and downloads are reads, but they're guarded because printing is an action.
  - Requests that only render a page aren't guarded (`/me`, `/carrier`, the lists and details): a reload shows the acted-for customer anyway.
- **Stale-cookie landing:** Orders' pick-a-customer, the state #65 made the landing for an admin acting for no one.
- **The rename to `targetUserId` costs nothing now.**
  - No Datadog dashboard or live monitor reads parcel-portal log fields. The repo's monitors are off and key only on message, `@route`, `@httpStatus`, `@importStatus` and `@attemptState`; dashboards and monitors were searched on 5 Nov.
  - There are no users before D1 (Harry, 3 Nov).
- **`X-Expected-Tenant` is optional:** it's a precondition only when sent, so svc needs no per-route change beyond the documented 409. The UI sends it on all fifteen guarded requests; making it required (428) can be added later.
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

**PR 1 (svc):** increments 1–4. **PR 2 (UI):** increment 5, off main, can ship first. **PR 3 (UI):** increments 6–7, verified once PR 1 is on dev. **PR 4 (UI):** increment 8, stacked on PR 3.

That's eight increments, one over the guide's seven. Harry's 5 Nov answer added the order, shipment and label actions. They touch a separate set of pages and need their own verification, so they're kept out of increment 7.

- [x] 1. svc: `X-Acting-Tenant` is read only on non-admin session routes; tenant-less admin-only routes scope to the admin's own tenant and log no acting event. A deleted or unknown acting tenant returns `ErrActingTenantNotFound`, which maps to 404 `acting_tenant_not_found`. Add header-taking variants of the e2e helpers (`do`, `send`, `act`, `get`), and parameterise the unit `actingRequest` by scopes and a chi `tenantId`. Update the README's Tenant scoping (AC 2,6) — verify: — unit: admin-only route keeps own scope, logs no acting, ignores a deleted tenant; unknown and deleted acting tenants give code acting_tenant_not_found. e2e: deleted customer in the header, /admin/tenants, /admin/mapping/fields, /admin/layouts/dc-layout 200; /me 404 acting_tenant_not_found — done: b174e2e
  - unit (`authorize_test.go`): an admin-only route with an unknown header gives own scope and no "Admin acting" line; a stale acting tenant gives code `acting_tenant_not_found` (asserted on `ErrorBody.Code`, not just the status);
  - e2e (`tenants_delete_e2e_test.go`), with the deleted tenant in the header: `GET /admin/tenants`, `/admin/mapping/fields` and `/admin/layouts/dc-layout` return 200, and `GET /me` returns 404 `acting_tenant_not_found`.
- [x] 2. svc: logout revokes in the session's own tenant: `WithScope(ctx, principal.Tenant)` in `LogoutUseCase`. `RevokeSession` becomes `:execrows` with `revoked_at = COALESCE(revoked_at, @revoked_at)`, and 0 rows is NotFound. The `WithScope` doc lists every caller: auth middleware, sign-in, slug import, apikey, demo, logout (AC 4) — verify: — unit: logout while acting revokes in the principal's own tenant. integration: another tenant's session is NotFound and stays live; a second revoke is fine. e2e TestSigningOutWhileActingEndsTheSession: /me 401 after; fails without the fix (200) — done: c522da7
  - unit: a fake revoker sees the principal's tenant while the scope is another;
  - integration: `TestSessionsCantRevokeAnotherTenantsSession` expects NotFound and a live session;
  - e2e `TestSigningOutWhileActingEndsTheSession` (in `e2e_test.go`): `/me` returns 401 afterwards. This test fails on main today.
- [x] 3. svc: actor on every line. A new `observability/actor.go` gives `TrackActor`/`SetActor`, backed by an atomic slot. `correlationHandler` stamps `actorId`, `Correlation` calls `TrackActor`, and `Authorize` calls `SetActor` straight after `Authenticate`. User* audit events rename `userId` to `targetUserId`. Update the README's Logging section and add a runbook `@actorId:` query (AC 5) — verify: — unit: tracked slot stamps actorId, also on a line logged with the pre-auth context; none without a user or a slot; Correlation→Logger→Authorize chain puts actorId on Request completed. e2e (table, x-request-id per event): user create/disable/enable/update/password, slug set, tenant delete/restore, upload while acting — each event line and its Request completed carry the admin's actorId; targetUserId names the changed user; /auth/login has none — done: 65041a2
  - unit: chain Correlation → Logger(`NewLogger`) → Authorize, and "Request completed" carries actorId;
  - e2e (`acting_e2e_test.go`), table-driven with one `t.Run` per event: create, disable, enable, update and set the password of a user, set a slug, delete and restore a tenant, and an upload while acting;
  - each audit line and its "Request completed" (matched by correlationId) carry the admin's actorId, and `/auth/login` carries none.
- [x] 4. svc: an `X-Expected-Tenant` precondition, checked in `Authorize` after the scope is resolved. A mismatch is 409 `tenant_changed`, plus a warn event `Tenant changed refused`; a malformed value is 400. Add the 409 `TenantChanged` response to the fifteen guarded operations, and the README Tenant scoping paragraph (AC 1,7) — verify: — unit: matching expected tenant passes; a mismatch is 409 tenant_changed and logged; a non-uuid is 400; a customer naming another tenant 409; an admin route matching its path tenant passes. e2e (admin acting for globex, page showing acme): all 15 guarded requests 409 tenant_changed; after them acme's order and shipment, the bucket and the fake carrier (bookings, deletes, commits, validations) are unchanged, and this test fails with the guard disabled; acting for acme and expecting acme, all 15 get past the guard — done: b798978
  - unit: a match passes, a mismatch gives code `tenant_changed`, a malformed value gives 400, and a customer naming another tenant gets 409;
  - e2e with an admin acting for globex while expecting acme:
    - upload returns 409 and no new object lands in the bucket;
    - the upload poll and refresh-status return 409;
    - manifest returns 409, the fake carrier records no commit, and the shipment stays booked;
    - the export CSV returns 409 with no body;
    - a table over AC 7's ten: each returns 409 with a mismatched header and changes nothing (the order's or shipment's status and version are as before, and the fake carrier records no call); with a matching header each succeeds;
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
- [ ] 8. UI: order, shipment and label actions carry the page's customer.
  - These send `X-Expected-Tenant` from the page's customer, through increment 7's page-tenant helper:
    - the Orders list's bulk dispatch, cancel, pack and Check;
    - the order page's edit, edit lines, pack and dispatch;
    - the shipment page's void;
    - printing: `labelsUrl` and the print page's frame and download links add `expect=`, which the two label routes turn into the header.
  - Each says what wasn't done: "You switched customer in another tab, so nothing was dispatched / cancelled / packed / checked / saved / voided / printed. Reload to see who you're acting for."
  - On a 409, a WebUSB print falls back with a new reason, `customer_changed`, not `labels_unavailable`. The print-to-screen page says the same.
  - (AC 7) — verify, with `acting.spec.ts` against dev:
    - tab A opens D1's Orders, one of its orders and one of its shipments, then tab B switches to D2;
    - in tab A each action is refused with its wording: bulk dispatch, cancel, pack and Check; edit, pack and dispatch one order; void; print and download labels;
    - neither D1 nor D2 changes, and no label is printed;
    - after a reload, tab A acts for D2.
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
- 2026-11-05 — Harry: guard every customer-facing write, not only the five tenant-wide requests (his answer to this plan's UNRESOLVED, "Every customer-facing write"). This adds AC 7 and increment 8. svc's check is unchanged, because it already applies to any request that sends `X-Expected-Tenant`; only the contract's 409s and the e2e table grow.
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
