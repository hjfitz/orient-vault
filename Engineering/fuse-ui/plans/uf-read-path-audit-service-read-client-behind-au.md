---
ticket: none
title: 'UF read path: audit-service read client behind AUDIT_READ_SOURCE'
service: fuse-ui
status: complete
created: '2026-10-12'
updated: '2026-10-15'
repo: /home/hjf/code/fuse/fuse-ui
worktree: /home/hjf/code/fuse/fuse-ui/.claude/worktrees/audit-read-path
branch: hjf/audit-read-path
base: origin/main
base_sha: 9aa61742b
pr: '307'
tags:
- waypoint
- plan
programme: Audit Service
unit: UF
impl_model: opus
impl_effort: high
---
# Audit Service UF — read path: audit-service read client behind AUDIT_READ_SOURCE

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
fuse-ui's audit pages read its own Mongo `audit_log`. This adds a read client for audit-service's read API, selected by a new `AUDIT_READ_SOURCE` (`mongo` | `service`, default `mongo`), so the "UF cutover and removal" plan's single one-way-door deploy can flip reads together with `AUDIT_SINK=service`. Under `mongo` nothing changes. Under `service` the audit list, filters, deep links and connector history render from audit-service, still behind the admin guard and masked in fuse-ui (G3). Stacked on nothing; the dual-publish plan (#300–#302, #305) is the sibling, and the switch itself stays off here.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. With `AUDIT_READ_SOURCE=mongo` (every env, after every PR here) the audit pages, filters, page-number paging, `?change=` behaviour and connector history are unchanged.
- [x] 2. With `service`, the global and customer audit lists and their filter options come from `GET /api/v1/systems/fuse/events` and `/filter-options`, mapped back to `AuditLogView`.
- [x] 3. With `service`, paging is next/previous over the service cursor (client-side back-stack), a filter change resets it, and a capped count shows "1000+".
- [x] 4. With `service`, a `?change={id}` deep link (UUID or legacy 24-hex) opens the change even when it isn't on the current page; on the customer page an event from another tenant is not found.
- [x] 5. Rows from the service go through the same `assertAdmin` and `maskAuditLog` as Mongo rows; an editor is refused.
- [x] 6. fuse-ui calls audit-service with a Google ID token for its SA (audience = the service URL), using one generalised ID-token helper shared with the fuse-tracker client.
- [x] 7. Config refuses an inconsistent pair: `AUDIT_SINK=service` with read ≠ `service`, and `AUDIT_READ_SOURCE=service` with `AUDIT_SINK=mongo`. `service` read needs a parseable `AUDIT_SERVICE_URL`.
- [x] 8. IaC carries `audit_service_url` per env as a tfvars literal (no remote state) and `audit_read_source` defaulting to `mongo`, forced to `mongo` in previews; no tfvars sets it to `service`.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- **Read server functions:** `code/src/app/server-functions/user/audit-log.func.ts` (`assertAdmin`, `listAuditLogs`, `listAuditLogFilterOptions`; new `getAuditLog`).
- **New source switch:** `code/src/lib/audit/audit-reader.ts`, `audit-service-reader.ts`, `audit-event.ts` (inverse of `audit-message.ts` `toAuditMessage`). Masking stays in `mask-audit-details.ts:71` `maskAuditLog`.
- **Types:** `code/src/lib/db/audit-log.types.ts` (`AuditLogQuery` gains `cursor`; `AuditLogPage` becomes `{logs,total}` | `{logs,total,totalCapped,nextCursor}`). `audit-log.collection.ts` untouched.
- **Callers (exactly three):** `app/user-management/audit-log/page.tsx`, `app/customer/[customerId]/changes/page.tsx`, `modules/connector/components/connector-change-history.tsx`.
- **UI:** `modules/audit-trail/components/audit-log-table.tsx`, `audit-detail-drawer.tsx`, `logic/audit-filters.logic.ts`. Cursor helpers mirror `modules/order-tracker/logic/tracker-params.logic.ts:192-218`; `CursorPagination` (`list-controls.tsx:187-248`) is tied to tracker params, so copy or generalise it.
- **HTTP client:** `code/src/lib/api-client/fuse-tracker/id-token.ts` → `api-client/id-token.ts`; `api-client.ts` (new `auditServiceClient`, openapi-fetch + `makeWrapFetch`); `observability/metrics/bff-dependency-metric.type.ts` (`AUDIT_SERVICE`); copied `api-client/audit-service/openapi.yaml`, `package.json` `gen-audit-service-client` → `src/lib/gen/audit-service.client.d.ts`.
- **Config:** `code/src/config.ts` (`AUDIT_READ_SOURCE`, `AUDIT_SERVICE_URL`, superRefine, `auditLog.readSource`, `auditService.uri`).
- **IaC:** `iac/projects/fuse-ui/variables.tf`, `cloud-run.tf`, `iac/env/{dev,prod}.tfvars`.
- **Inter-service dependency (new):** fuse-ui → audit-service HTTP read. Sign-off: fuse-mcp `service-dependencies.json`.
- **audit-service contract consumed** (origin/main ddefd56): `routes.go:36-41`, `controllers/read.go`, `core/query/query.go`, `openapi.yaml`. No audit-service change needed.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- fuse-ui-dev and fuse-ui-prod SAs are already audit-service readers (`run.invoker` + `READ_CALLERS`) — read audit-service `iac/env/{dev,prod}.tfvars`, `iam.tf:21-28`, `cloud-run.tf:69`.
- Query params: `tenantId`, `targetType`, `targetId`, `actorId`, `action`, `from`/`to` (RFC 3339 with zone; `toISOString()` is fine), `limit` (≥1 integer else 400; >100 silently clamped), `cursor` (opaque, forward only). Response `{events, nextCursor, total, totalCapped}`; filter options `{actors, tenants}` — read `read.go`, `query.go`.
- Error bodies: app errors are `{message}`, but Cloud Run IAM rejections are not JSON and openapi omits 401/403/500 on get and filter-options — the reader must not assume a JSON error body. Read `respond.go`, `caller.go`, `openapi.yaml`.
- The verifier passes an empty audience (`adapters/idtoken/verifier.go:15-18`); Cloud Run enforces it. A wrong audience fails as a non-JSON 401.
- `GET /events/{id}` is not tenant-scoped (`repositories/read.go:90-100`); the customer page filters by `businessId` itself.
- Service rows carry real `details` minus `businessId` (lifted to `tenantId`), so diffs, `friendlyName` and `storefrontId` still render; only the `details.businessId` fallback goes dead and `tenantId` covers it — read `audit-message.ts`, `legacy.go:54-64`.
- The service's tenant filter options are a superset of Mongo's `distinct('businessId')`, because legacy `details.businessId` rows get lifted. Accepted as more correct.
- Pager copy follows the order tracker ("page N", previous/next) plus "1000+ records" when capped; an old `?page=N&change=` link under `service` opens the change on the first page. Defaults taken, not product decisions.

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
- [x] 1. **Generalise the ID token and add the generated audit-service client.** Move `fuse-tracker/id-token.ts` to `api-client/id-token.ts` (`idTokenAuthHeaders(audience)`, `server-only`), switch the tracker client to it, add `auditServiceClient` + `BFF_DEPENDENCY.AUDIT_SERVICE`, the copied spec, gen script and generated types. Nothing calls the new client. PR-A. (AC 6) — verify: new id-token specs (localhost → `{}`; one client per audience; a failed client is evicted); suite/lint/build:check(+tests); a dev deploy from a branch rebased on a main that includes #305, then the tracker list and a shipment detail load and Datadog shows no 401/403 from `fuse-tracker` after the deploy. — done: c60dc64
- [x] 2. **Read mapping, source switch and config, still inert.** `audit-event.ts` (`fromAuditEvent`, query and filter-option mappers; connector history passes `targetEntity: 'connector'` so the service query uses its `target.type`+`target.id` index), `audit-service-reader.ts` (404 → null, non-JSON errors tolerated), `audit-reader.ts`, the `AuditLogPage` union, `getAuditLog`, and the config keys and guard. Nothing sets the flag yet. PR-B, stacked on A. (AC 1,2,5,7) — verify: one `it` per mapped field and query param; 404 → null; `mongo` returns the collection result untouched; a secret in a service row is masked from `listAuditLogs` and, separately, from `getAuditLog`; `getAuditLog` refuses an editor; existing `audit-log.func.spec` stays green with its mock moved to `../../../../lib/audit/audit-reader` (it would otherwise load api-client's observability bundle); no config/Zod-only specs; a dev deploy under `mongo` shows page 2 via `page=` returns rows 26–50 and an off-page `?change=` still shows "Change not in view". — done: 7fa6e21
- [x] 3. **Cursor pager, "1000+" and deep links.** Cursor + back-stack parsing and next/previous helpers in `audit-filters.logic.ts`; both pages pass the cursor and, on a cursor page, resolve `?change=` via `getAuditLog` into a `pinnedLog` (customer page drops another tenant's event); table branches on `'nextCursor' in page`, a filter change clears the cursor, and the label shows "1000+" when capped; drawer not-found copy for cursor mode. PR-C, stacked on B. (AC 3,4) — verify: specs for next pushes the current cursor (`~` first), previous pops, previous from page 2 clears the cursor, "1000+" vs exact label; local `next dev` with `AUDIT_READ_SOURCE=service`, `AUDIT_SINK=both` and the dev URL under ADC impersonating fuse-ui-dev: next → next → previous returns the same rows, filter change resets, a UUID `?change=` off-page opens, another tenant's id on a customer page is not found, connector history renders, an editor is refused; screenshots of each. — done: 8c55186
      > SUPERSEDED 2026-10-12 — verified end to end against a local audit-service fed by the real import tool instead (see Evidence), so dev's event count no longer gates this increment.
      gate: dev `AUDIT_SINK=both` live (#305 merged and deployed), so dev audit-service holds events to page through
            [x] confirmed
- [x] 4. **IaC: the URL and the switch, off.** `audit_read_source` (default `mongo`, validated; `local.audit_read_source` forces `mongo` in previews), `audit_service_url` (default `""`), two env blocks, and the dev/prod URL literals confirmed with `gcloud run services describe audit-service-{env} --format='value(uri)'`. Lands last so nothing can set `service` before the pager exists. Same PR as 3. (AC 8) — verify: dev plan = two new env vars + the known standing drift, no add/destroy, shared with Harry before merge; prod plan the same after merge; preview plan shows `mongo`. — done: 8c55186

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
- 2026-10-15 [AC 1-8] **The deployed read path is proven.** Dev was rehearsed with #323 (751/751; every customer equal). Prod read from the service from #326 on, using the real `fuse-ui-prod` SA and the prod audience, so no Token Creator grant was needed.
  - After #325, prod shows 255 records. The legacy link opens on the audit log page and on `/customer/BYOMA/changes`, and shows "Change not found" on PHLUR.
  - #325 later removed the `mongo` read mode and the config guard (AC 1, 7, 8), which were verified while they existed (Evidence below).
<!-- Newest first, dated. -->
- 2026-10-12 [inc 3,4, AC 1,2,3,4,5,8] **Local end to end on 8c55186 against the real audit-service** (API from `origin/main` ddefd56; Mongo seeded with 1,100 fuse-ui rows, 440 legacy, tenant `OLD` only in `details.businessId`; copied by `import-legacy` → read 1100, `-verify` present 1100; a local proxy adds my `gcloud` identity token, which the verifier accepts because it passes an empty audience; no token → 401). fuse-ui `next dev` with `AUDIT_READ_SOURCE=service AUDIT_SINK=both`, headless Chrome:
  - "1000+ records"; Next, Next, Previous → page 2 rows identical; Previous → page 1 identical, empty query string.
  - Off-page UUID `?change=` and oldest legacy 24-hex `?change=` both open; the GADG password change opens masked and no snapshot secret appears in any page's HTML; `/customer/HJF/changes?change=<GADG id>` → "Change not found" (471 records).
  - Page 2 then entity = Connector → `?entity=connector`, Page 1, 314 records.
  - Parity, service total vs Mongo `countDocuments` with fuse-ui's filter: equal for HJF 471, GADG 314, OLD 157, connector 314, connector_mapping 157, user 158, backend 314, viewed 79, deleted 157, b@x.com 367, targetId conn-1 314; unfiltered 1100 vs 1000+ (capped).
  - Same data under `mongo`: "1100 records", Page 1/2 of 44, off-page `?change=` → "Change not in view", no cursor pager.
  - Dev tf plan (PR #310, run 38301211395): 0 add / 1 change / 0 destroy — two new env vars on `fuse-ui-app` plus the image and the standing drift (sidecar env swap, `container-dependencies` annotation, `max_instance_count 100 -> null`).
  - Jest 1006/1006; `tsc` clean; `next build` compiled.
- 2026-10-12 [inc 2, AC 1,2,5,7] **Dev deploy of 7fa6e21 under `mongo`** (manual-deploy run 38299499896; 0 add / 1 change / 0 destroy, image only; #305 still open, so dev sink unchanged). Headless Chrome as the env admin on `/user-management/audit-log`:
  - page 1: "713 records", "Page 1 of 29", 25 rows; `?page=1`: "Page 2 of 29", 25 rows, none shared with page 1.
  - `?change=` an id from page 2 → drawer with "Change not in view" (unchanged rule); `?change=` a page-1 legacy ObjectId row → drawer opens with the masked diff.
  - Config guard (local `tsx` import of `config.ts`): mongo/mongo, both/mongo, both/service, service/service boot; service/mongo, mongo/service and service read without a URL are refused with their messages.
  - Locally: specs for each mapped field and query param, cursor page, 404 → null, Cloud Run non-JSON 403 and service 400 messages, mongo passthrough vs service, masking of a service row in list and in `getAuditLog` (separate `it`s), `getAuditLog` refuses an editor, Mongo get by legacy ObjectId. Jest 989/989; `tsc` clean; `next build` compiled.
- 2026-10-12 [inc 1, AC 6] **Dev deploy of c60dc64** (manual-deploy run 38298236792; dev plan 0 add / 1 change / 0 destroy, image only; dev still on `AUDIT_SINK=mongo`, so no IaC moved). Logged in to `fuse.freightops.dev` as the env admin:
  - `/order-tracker` → 200 with live tracker data (Needs action 1,310; GADG work queue), via `fuseTrackerClient` and the moved `idTokenAuthHeaders`.
  - `/order-tracker?section=shipments&businessId=GADG` → 200 with shipment rows. The shipment detail opens client-side, so the server render covers the list only.
  - `/api/order-tracker/export?section=shipments&businessId=GADG` → 200 `text/csv`, 600 KB, the second call site (`fuseTrackerFetchRaw`).
  - Locally: 5 id-token specs (localhost → {}, header returned, audience passed, one client per audience, fresh client after a failure); Jest 955/955; `tsc` clean; `next build` compiled.

### Not verified
> SUPERSEDED 2026-10-13 — the existing `{system, target.type, target.id, occurredAt}` index serves this query (explain: 13 keys, 5 docs, 4 ms on 200k events). No follow-up index needed; see Decisions.
- **Connector history on audit-service as history grows.** The query sends `targetId` without `targetType` (see Decisions), and audit-service has no `{system, target.id, occurredAt}` index, so it falls back to scanning newest-first and the capped count scans up to 1,000 matches. Fine at dev volume. Follow-up: add that index in audit-service before prod reads flip.
- **List parity and legacy links on real migrated data.** Proven locally on seeded data through the real importer (Evidence, inc 3,4); still to repeat on dev's real rows in the cutover plan's dev rehearsal.
- **A deployed Cloud Run read** (the real SA, Terraform env wiring and audience). Local impersonation skips them. First proven in the dev rehearsal, where reads flip anyway.
- **A prod read before the one-way door.** Proposed as a gate on the cutover plan's prod step: a human-run curl as fuse-ui-prod with `--audiences` set to the prod URL, using a temporary Token Creator grant that is reverted and recorded (the UE.4 precedent).

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-10-13** — Dropped the follow-up audit-service index on {system, target.id, occurredAt}. Explain on 200k seeded events (8 target types, 5k ids): connector history by target.id alone uses the existing {system, target.type, target.id, occurredAt} index (13 keys examined, 5 docs, 4 ms, in-memory SORT over the matches only). With few target types, Mongo seeks within each type instead of scanning them.

- **2026-10-12** — Increment 3's service-mode check ran locally against a real audit-service (origin/main) fed by the real import-legacy, not via local ADC impersonation (no Token Creator on fuse-ui-dev) or a dev flip (shared dev would read a half-populated store). It also gave per-filter parity on seeded data. getAuditLog takes an optional businessId so the customer page can't open another tenant's change (audit-service get-by-id is not tenant-scoped). The #305 gate on inc 3 is superseded by this.

- **2026-10-12** — Rejected the review's 'connector history should send targetType connector': connector history deliberately shows connector_mapping rows too, which are written with the connector's id as targetId (storefronts.action.ts auditConfigChange('created'|'deleted', 'connector_mapping', connectorId, …)). Filtering by type would drop mapping changes. The index gap moves to audit-service as a follow-up (an index on {system, target.id, occurredAt}). Also: getAuditLog reads by id from both sources (Mongo matches eventId, or _id for a 24-hex legacy id) rather than throwing under mongo.

- **2026-10-12** — AUDIT_SERVICE_URL (optional, default '') moved into increment 1: api-client.ts builds auditServiceClient at module load and needs its base URL. On its own it does nothing; AUDIT_READ_SOURCE and the sink/read guard stay in increment 2. Dev deploy for inc 1 ran before #305 merged, so it could not reset dev's sink.
- **2026-10-12** — The plan was reviewed on three dimensions (history, grounding, increments). Changes from the draft:
  - **No importer run before the read flip.** The agreed rollout freezes Mongo at the single cutover deploy and runs the one migration straight after. An earlier import would also hollow out the dev rehearsal.
  - **The IaC switch lands last, in the same PR as the pager.** Otherwise `service` could be set while paging still sent `skip`, and page 2 would silently repeat page 1.
  - **Config keys move into increment 2,** where the reader first reads them.
  - **Mongo stays on offset paging.** It is the rollback lever only before cutover. After cutover, Mongo reads hide post-cutover events (R1), and UF.3 deletes the offset branch.
  - **The config guard against mismatched sink and read is adopted.** It follows from the recorded cutover design, where both flags flip in one deploy.
  - **A generated client over a hand-written one,** following the fuse-tracker precedent. Drift in the copied spec shows up as type errors on regeneration.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
(promoted to audit-service known-context.md, 2026-10-15)
