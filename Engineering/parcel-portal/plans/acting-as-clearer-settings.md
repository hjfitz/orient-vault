---
ticket: "none"
title: "Acting-as: clearer Settings"
service: "parcel-portal"
status: draft
created: "2026-11-05"
updated: "2026-11-05"
repo: "ilg-merak/parcel-portal"
worktree: "/home/harry/code/merak/parcel-portal/.claude/worktrees/acting-settings"
branch: "hjf/acting-settings"
base: "origin/main"
base_sha: "a8e92471c4e7cbef6860dcd20ed572c8403242d8"
pr:
tags: [waypoint, plan]
programme: "Parcel Portal"
unit: "C20"
---
# none — Acting-as: clearer Settings

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
Harry found "acting as" confusing in Settings. Customer screens (Orders, Shipments, Export, Printing) follow the browser-wide acting customer. Customer settings pages follow the URL's customer. The header and banner always show the acting one, so a page titled Y can sit under "Acting as X". This makes every page say plainly whose data and settings it shows, and stops moving between customers from leaving a dead page or a wrong bench. It follows [[acting-as-safety-fixes]] (C19) and reuses its "page's customer" mechanism.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [ ] 1. While acting as X, Settings opens X's own settings. The Customers list is one click away, marks X, and offers "Act as" on every other live customer.
- [ ] 2. On customer Y's settings while acting for anyone else (or no one), a notice reads "These are Y's settings. Orders, Shipments and Export are acting for X" (or "for no customer"), with an "Act as Y" button. Nothing switches on its own.
- [ ] 3. Settings → Printing names the customer whose benches it shows. An admin acting for no one is asked to pick a customer, not told to "Ask GFS".
- [ ] 4. A browser remembers its bench per customer: switching from X to Y never applies X's bench to Y or reports X's bench as missing. A print whose page customer no longer matches is refused with its own reason, not printed against the wrong customer's benches.
- [ ] 5. Dates on customer Y's settings and in the Customers list show in Y's own time zone.
- [ ] 6. An order, file or shipment page that isn't the acting customer's sends an admin back to that list with a notice, instead of a bare 404 or a dead alert.
- [ ] 7. The Export page and the downloaded file name the customer, and the page copy no longer assumes Yusen.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- **Contract** (`apps/svc/openapi.yaml`), additive, one minor bump in the first slice that touches it:
  - `Tenant.timezone` on the tenant list;
  - `ShipmentExportSummary.customer`;
  - the export Content-Disposition description.
- **svc:**
  - `repositories/postgres/queries/{tenant.sql,export.sql}` and their stores;
  - `models/{identity.go,export.go}`;
  - `core/tenants/{list.go,folder.go}` (`PlainName` pulled out of `FolderName`);
  - `core/exports` (`FileName`);
  - `http/controllers/{exports.go,auth.go}`.
- **UI:**
  - `src/{svc.ts,zone.ts}`, plus a new `customers.ts` (a cached `tenantList`, and `actingCustomer`);
  - `app/(app)/{layout.tsx,pick-customer.tsx}`, plus new `act-as-button.tsx` and `gone.tsx`;
  - settings: `page.tsx`, `customers/page.tsx`, `customers/[id]/{layout,overview/page,carrier/page,access/page}.tsx`, `printing/page.tsx`;
  - `src/printing/{this-bench.tsx,print-labels.ts,actions.ts,reasons.ts}`;
  - the export page and the order, file and shipment detail pages.
- **Package:** `packages/label-print` `src/pairing.ts` + `index.ts`, 0.1.0 → **0.2.0**, with a CHANGELOG entry and README "Storage".
- **Docs:**
  - `apps/ui/README.md`: Settings bullet, Dates, and the `?tenant=` paths marked legacy;
  - `apps/svc/README.md` Day-end export;
  - `docs/printing.md` steps 1–2, which are stale: benches now live on the customer's tab.
- **Must keep working:** `e2e/smoke.spec.ts`.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- **Plan A lands first.** Step 0 re-reads its diff for four things: the e2e acting helpers, the `info.version` base, any change to `actAsAction`, and the page-customer mechanism. The print path reuses `X-Expected-Tenant` from Plan A increment 4.
- **Time zone can now be set and seen.** #96 (export settings, 5 Nov) adds a customer Export tab that sets it. So AC 5 can be checked on dev by giving a demo customer a far-off zone, e.g. Asia/Tokyo; no SQL is needed.
- **Export file name:** `shipments-<customer>-<date>.csv`, built with `PlainName`, the customer's name without the folder's random suffix.
  - Manhattan's real file is DC's `shipments_download_<epoch>.csv`, and the portal's `shipments-<date>.csv` never matched it.
  - With no users and no prod, renaming breaks nobody. The name is recorded as an assumption under G2/MKP-6.
  - Range exports from the Wilders stack get `shipments-<customer>-<from>-to-<to>.csv` from the same `FileName`.
- **The old browser-wide bench is ignored, not used as a fallback.** No customer bench computer is live yet; only GFS's office and dev browsers have paired. A fallback would bring back the very bug item 4 removes.
- **Customer users keep today's behaviour** on a missing order, file or shipment. Only admins are redirected.
- **"Act as" stays on the page**, as the switcher does, rather than jumping to Orders.
- UNRESOLVED: none beyond Plan A's.

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

- [ ] 0. Re-check against Plan A as merged: its helpers, `info.version`, `actAsAction` and the `X-Expected-Tenant` plumbing. Amend this plan where they differ — verify: a dated note in Decisions.
      gate: [[acting-as-safety-fixes]] merged and on dev
            [ ] confirmed
- [ ] 1. Customer time zone, svc and UI together.
  - svc: `t.timezone` goes on `ListTenants` → `models.Tenant.Timezone` → `toTenant`. An unloadable zone lists as the default.
  - UI: `customers.ts` gives a React-`cache`d `tenantList` and `actingCustomer`. The app layout, customers page, overview, access and the `[id]` layout all use them, so one `GET /admin/tenants` per render. `customerZone(session, id)` serves the carrier and access tabs, "Deleted on" and the list's Deleted column.
  - (AC 5) — verify:
    - svc unit test for the default;
    - e2e in `tenants_e2e_test.go` (beside the deleted-customer list test): a zone set through `PUT …/export-settings` shows on the list;
    - on dev via `acting.spec.ts`: set demo D's zone to Asia/Tokyo on its Export tab and make an API key on D's Access tab while acting for another customer; the key time is in JST.
- [ ] 2. Settings while acting.
  - `settings/page.tsx` sends an admin acting for a live customer to `/settings/customers/<id>/overview`; `redirect` stays outside any try.
  - The customers list marks the acted-for row and puts an "Act as" button (outline) on other live rows.
  - The `[id]` layout notice from AC 2 has an "Act as Y" button (default variant), hidden for GFS staff and deleted customers.
  - `actingCustomer` replaces the layout's own lookup.
  - (AC 1,2) — verify, with `acting.spec.ts` on dev:
    - acting as A, Settings lands on A's Overview, and the list marks A;
    - Act as B moves the banner and the mark;
    - A's settings opened while acting as B show the notice, and Act as A clears it;
    - not acting, Settings opens the list;
    - the banner and switcher still name the acted-for customer on /orders.
- [ ] 3. Printing names its customer.
  - `this-bench.tsx` takes `account: {id, name, benchesHref?} | null`.
  - When it's null, the picker becomes "Pick a customer under Acting as". Pairing and DPI still work, and the demo printer isn't shown as off.
  - The empty state links to the customer's Bench printers tab.
  - (AC 3) — verify:
    - `acting.spec.ts` on dev: not acting → "pick a customer"; acting as A → the page names A, and the empty state links to A's tab;
    - a customer user's Printing page is unchanged.
- [ ] 4. Bench per customer, in label-print 0.2.0.
  - `PrintSettings.benches: Record<account, bench>`, with `benchFor` and `saveBenchFor`; the old `bench` is ignored.
  - `ownBenchPrintersAction` takes the page's customer and sends Plan A's `X-Expected-Tenant`; a mismatch gives a new reason, `customer_changed`.
  - `bench_unpicked` is not silent when a printer or the demo printer is set; only `not_paired` stays quiet.
  - Delete `silentPrintingConfigured`, which has no callers.
  - (AC 4) — verify:
    - label-print `pnpm test` (vitest: own pick per account, saving for A leaves B alone, a malformed `benches` reads as none, `unpair` keeps benches), `lint`, `build:check` and `build`;
    - `pnpm install` in apps/ui, then the UI gates;
    - `acting.spec.ts` on dev, with demo customers A ("Bench 1") and B ("Pack 2") added by hand on their Bench printers tabs:
      - pick per customer;
      - switching never shows "isn't on the list";
      - each dispatch toast names that customer's bench;
      - a customer user of A with the old key seeded still picks fresh.
- [ ] 5. Detail pages go back to the list.
  - `gone.tsx`: `parseGone` accepts only `order|file|shipment`, so no URL text is ever shown.
  - `orders/[id]`, `orders/files/[id]` and `shipments/[shipmentId]` guard with `mustPickCustomer`, and on a missing record call `sendAdminBack`, so only admins are redirected.
  - The list pages show the notice.
  - Remove the shipment alert's in-page back link (design.md: one back control).
  - (AC 6) — verify: `acting.spec.ts` on dev:
    - switching customer on an order lands on `/orders?gone=order` with the notice;
    - Back to GFS on an order lands on "Pick a customer" with the notice;
    - `/orders?gone=<anything else>` shows nothing;
    - add a required step to `smoke.spec.ts`: stop acting on a booked order and expect the notice.
- [ ] 6. Export names its customer.
  - svc: `GetExportSettings` also selects `name`; `exports.FileName(customer, from, to)`; `Summary.Customer`.
  - UI: the card title reads "Day-end shipment export for {customer}", and the copy is customer-neutral.
  - (AC 7) — verify:
    - unit: "Acme Ltd" gives `shipments-acme-ltd-2026-11-05.csv`, and a range gives `…-2026-11-01-to-2026-11-03.csv`;
    - fix `TestExportSettingsDefaultToTheUSSiteWithFormulasOff`, which compares the whole struct;
    - e2e: `?date=2026-11-05` gives the exact `Content-Disposition`, and the summary's `customer` is "Acme";
    - dev: acting for a demo customer, the Export page names it.

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
- 2026-11-05 — Plan-time choices from review:
  - slices are cut by feature, each spanning svc and UI, so the export-name question can only block its own slice;
  - the print path follows the page's customer, Harry's per-browser rule, rather than the cookie at print time;
  - the time zone comes from the tenant list, not a second `/me` with another acting header, which would log acting that never happened.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
- **Dead code paths.**
  - `silentPrintingConfigured()` in `print-labels.ts` has no callers.
  - The `?tenant=` upload and file paths have had no UI entry point since #65.
- **label-print is versioned** (`package.json` 0.1.0, one CHANGELOG section per version). New exports need a bump, not just a CHANGELOG line.
