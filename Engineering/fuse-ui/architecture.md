---
tags:
- waypoint
- fuse-ui
verified: '2026-10-14'
verified_sha: f1538e4
verified_paths:
- code/src/lib/db
- code/src/lib/audit
- code/src/lib/auth
- code/src/lib/api-client
- code/src/modules/audit-trail
- code/src/modules/translator-config-editor
- code/src/modules/transaction-history
- code/src/app/server-functions
- code/src/app/api
- code/src/proxy.ts
- code/src/config.ts
- code/src/instrumentation.ts
- code/src/const/use-case.const.ts
- code/next.config.ts
- iac/projects/fuse-ui
- iac/env
title: fuse-ui — architecture
thesis: 'fuse-ui is a Next.js 16 BFF: Server Components and Server Actions call each
  owning service through typed clients behind an app-level session gate, and keep
  only users, audit_log and template_collections in their own Mongo.'
confidence: high
---
# fuse-ui — architecture

```orient-bluf
{ "v": 1, "bluf": "fuse-ui is a Next.js 16 BFF: Server Components and Server Actions call each owning service through typed clients behind an app-level session gate, and keep only users, audit_log and template_collections in their own Mongo.", "confidence": "high", "action": "Write audit rows only through lib/audit/audit-writer.ts, and check session.role inside any admin-only action, because proxy.ts gates only /user-management by role." }
```

## Guardrails

- [contract:G1] fuse-ui's own Mongo holds `users`, `audit_log` and `template_collections` only. Never add a Fuse platform collection; read platform data through the owning service's API client.
  — paths: code/src/lib/db, iac/projects/fuse-ui/mongo.tf
- [technical:G2] Audit rows are written only through `lib/audit/audit-writer.ts` and leave the server only through `lib/audit/mask-audit-details.ts`. Calling `addAuditLog` directly brings back throwing writes and skips the `eventId` and the publish. Returning raw rows puts snapshot credentials in the RSC payload.
  — paths: code/src/lib/audit, code/src/lib/db/audit-log.collection.ts, code/src/app/server-functions/audit, code/src/app/server-functions/user/audit-log.func.ts
- [contract:G3] `proxy.ts` skips `/api/auth/*` and gates only `/user-management` by role, and any signed-in session can call any `'use server'` export. Every admin-only action, route handler or page checks `session.role` itself.
  — paths: code/src/proxy.ts, code/src/app/server-functions, code/src/app/api
- [technical:G4] The config-editor providers' prop-sync `useEffect` clears `hasPendingChanges`. Put each new injected prop in a separate effect; an unstable identity in that one discards unsaved mapping edits on every render.
  — paths: code/src/modules/translator-config-editor/providers
- [contract:G5] Transaction History's `refPaths` chains are a cross-repo contract: collector's reference search matches Record ID on the same field paths, so change both repos together. Search fails closed, so keep `toSearchChunk` and the blank-reference guard.
  — paths: code/src/modules/transaction-history, code/src/app/server-functions/customer/transaction-history.func.ts
- [technical:G6] A new `AuditTarget` needs an `ENTITY_LABEL` entry, which is a total record. A new connector `config.*` path needs a `PATH_LABEL` entry, and a `DANGEROUS_PATH_PREFIXES` entry if a change to it is risky.
  — paths: code/src/lib/db/audit-log.types.ts, code/src/modules/audit-trail

## Runtime shape: Next.js 16 App Router, Server Components and Server Actions

React 19 with the React Compiler and typed routes. `output: 'standalone'` means the image runs `node server.js` [2][48]. No separate backend process exists. All data access runs in the Next server through two file kinds under `app/server-functions/`.

- **`*.func.ts`** are reads. Server Components call them, and so do fourteen `'use client'` components, such as Transaction History paging. The router action queue serialises browser-invoked server functions. A client that needs several reads therefore calls one function that fans out on the server (`searchTransactionChunks`). Its arguments come from the browser, so it validates them itself.
- **`*.action.ts`** are mutations, called from forms and client components.

Both return an `ApiResult` (`ok` with data, or an error) and do not throw on an API failure [3]. The split is the repo's controller boundary. No framework enforces it.

```orient-flow
{ "v": 1, "title": "Request path",
  "nodes": [
    { "id": "op", "label": "Operator browser", "kind": "external" },
    { "id": "px", "label": "proxy.ts", "sub": "session gate", "kind": "step", "service": "fuse-ui", "tone": "accent", "ev": [4] },
    { "id": "au", "label": "/api/auth/*", "sub": "skips the proxy", "kind": "step", "ev": [4, 5] },
    { "id": "pg", "label": "Server Components", "sub": "render per navigation", "kind": "step" },
    { "id": "fn", "label": ".func / .action", "sub": "BFF layer", "kind": "step", "ev": [3] },
    { "id": "mg", "label": "Own MongoDB", "sub": "users, audit_log, templates", "kind": "store", "ev": [6] },
    { "id": "up", "label": "Owning services", "sub": "typed clients, see below", "kind": "external", "ev": [7] }
  ],
  "edges": [
    { "from": "op", "to": "px", "label": "pages, actions" },
    { "from": "op", "to": "au", "label": "login, users", "style": "dashed" },
    { "from": "px", "to": "pg" },
    { "from": "pg", "to": "fn" },
    { "from": "fn", "to": "mg" },
    { "from": "fn", "to": "up" },
    { "from": "au", "to": "mg" }
  ] }
```

Server Components fetch through `.func.ts` in the tree (`customer/[customerId]/layout.tsx` awaits `getCustomers()` and `getCustomerStoreFronts()`). Mutations run as Server Actions wired to `@tanstack/react-form` with Zod validation. Client state (modals, tables, drafts) uses `zustand`. No global client data cache exists, so most reads render per navigation. Paged and searched views differ: Transaction History seeds a first page per record type on the server. Further pages and reference searches then run from the client, held in component state (`useReferenceSearch` caches per value).

## Auth: app-level JWT session, no load-balancer auth {#auth}

- **Session.** `lib/auth/session.ts` signs `{ email, role }` as an HS256 JWT (`jose`, `SESSION_SECRET`) in an HttpOnly, SameSite=Lax cookie. It is `secure` in production and expires after one day. `GET /api/auth/user` extends it [5].
- **Gate.** `src/proxy.ts` is Next's middleware under this app's naming. Its matcher skips paths starting `login` or `api/auth`, plus `_next/static`, `_next/image`, `.png` and `.svg`. No session redirects to `/login`. A non-admin under `/user-management` redirects to `/`. That is the proxy's only role check [4].
- **Login.** `api/auth/login/route.ts` first compares the `BASIC_AUTH_USER` and `BASIC_AUTH_PASSWORD` env pair with `===`. A match creates an admin session, and that account is the only admin. It is the shared `fuse-support@gfsdeliver.com` login, so every admin-only action (feature flags, user management) is audited under one mailbox until named admins exist (snapshot 2026-10-19). Any other login checks `users` with bcrypt [6].
- **Roles.** The type is `admin | editor | viewer`. Admin-created users are always `editor`. Nothing assigns `viewer` [8][9].
- **Role checks.** They cover `/user-management/*` (including every feature-flag server function, via `assertAdmin`), the `/api/auth/users*` routes, `listAuditLogs` and `listAuditLogFilterOptions`, the customer Change History page, and the matching nav entries. Config-mutating actions check no role, so any signed-in editor can change any customer's config [10].
- **No gate in front.** Cloud Run grants `allUsers` the invoker role with ingress open to all traffic. The load balancer config has no security policy. The login form is the only gate, and neither the app nor the load balancer rate-limits it [11][51][52].
- **ASSESSED** An org policy outside this repo may restrict the Cloud Run invoker grant. The repo cannot show it.
- `listUsers` has no role check, so any signed-in user can read every user's email and role [12].

## BFF over other services, not a second data plane {#bff-not-data-plane}

fuse-ui's own MongoDB (`iac/projects/fuse-ui/mongo.tf`, `lib/db/mongo.connection.ts`) holds `users`, `audit_log` and `template_collections`. Each is app-local state, not platform data. `instrumentation.ts` creates their indexes at boot. An index failure logs `DatabaseIndexesFailed` and the app still starts [13].

`template_collections` is a sanctioned exception to the platform-data rule. A template stores a `MappingConfig` verbatim, and applying it copies the config into a connector mapping, so no template is read downstream and none becomes a second source of truth [14].

Everything else is fetched live from the owning service's HTTP API. `lib/api-client/api-client.ts` wraps each generated client. It adds the request-id and `x-user` headers and retries a thrown fetch three times with jittered backoff. `proxy.ts` sets `x-user` from the session email, and config-service stores it as a write's `updatedBy`, so a server function never sets its own. A network failure still rejects after the retries instead of returning `error`, so a page that checks only `!result.ok` falls through to the error boundary; catch the rejection too. It counts every call as a BFF dependency metric [7].

```orient-flow
{ "v": 1, "title": "Outbound calls",
  "nodes": [
    { "id": "ui", "label": "fuse-ui", "kind": "service", "service": "fuse-ui", "tone": "accent", "ev": [7] },
    { "id": "cfg", "label": "config-service", "sub": "customers, connectors, mappings", "kind": "service", "service": "config-service", "ev": [7] },
    { "id": "rep", "label": "replay-service", "sub": "Retry Queue", "kind": "service", "service": "replay-service", "ev": [7, 15] },
    { "id": "col", "label": "collector", "sub": "Transaction History, SKUs", "kind": "service", "service": "collector", "ev": [7] },
    { "id": "ded", "label": "dedupe-service", "sub": "record admin API", "kind": "service", "service": "dedupe-service", "ev": [16] },
    { "id": "trk", "label": "tracking-service", "sub": "Order Tracker, flag", "kind": "service", "service": "tracking-service", "ev": [7, 17, 53] },
    { "id": "shp", "label": "shopify-connector", "sub": "retrieval preview", "kind": "service", "service": "shopify-connector", "ev": [18] },
    { "id": "ots", "label": "ilg-secure-notes", "sub": "credential link", "kind": "service", "service": "ilg-secure-notes", "ev": [19] }
  ],
  "edges": [
    { "from": "ui", "to": "cfg", "label": "generated client" },
    { "from": "ui", "to": "rep", "label": "generated client" },
    { "from": "ui", "to": "col", "label": "generated client" },
    { "from": "ui", "to": "ded", "label": "fetch, hand-typed" },
    { "from": "ui", "to": "trk", "label": "vendored contract" },
    { "from": "ui", "to": "shp", "label": "fetch" },
    { "from": "ui", "to": "ots", "label": "fetch" }
  ] }
```

| Service | Client | Auth | Used for |
| --- | --- | --- | --- |
| config-service | `lib/gen/config-service.client.d.ts` | `x-api-key` | Businesses, storefronts, connectors, mappings, central config |
| collector | `lib/gen/collector-service.client.d.ts` | `x-api-key` | Transaction History, master-data SKU list |
| replay-service | `lib/gen/replay-api.client.d.ts` plus `ReplayApiPathExtensions` for `/failures/groups` | `x-api-key` | Retry Queue |
| tracking-service | `lib/gen/fuse-tracker.client.d.ts`, from vendored `lib/api-client/fuse-tracker/openapi.yaml` | Google ID token, audience = API URL, none for `http://localhost` | Order Tracker |
| dedupe-service | plain `fetch`, hand-typed `lib/types/dedupe-service.type.ts` | `x-api-key` | Dedupe Summary: list, stats, detail, release |
| shopify-connector | plain `fetch` to `/api/v1/preview` | `x-api-key` | Retrieval-condition Test button |
| ilg-secure-notes | plain `fetch` to `/api/secrets` | `x-api-key` | One-time connector credential link |

- Run the generators by hand (`pnpm run gen-*-client`); the build does not. Re-vendor the tracker contract when tracking-service's API changes.
- **ASSESSED** The config-service generator URL no longer serves the spec, so that client stays at its last generation. This comes from an earlier 401 that this pass did not re-check [20].
- shopify-connector and ilg-secure-notes report themselves unconfigured when their key is empty. They do not call out. OTS is a fixed prod instance (`ots.ilg.software`) in every environment [1][18][19].
- Dedupe Summary lists four record types and omits `work_order`, which dedupe-service also holds [16].
- `getCustomers()` reads one page of at most 100 businesses and does not page [21]. `getConnectors()` sweeps every page.
- `NEXT_PUBLIC_FAPI_SERVICE_URI` is shown to operators and written into credential bundles. fuse-ui makes no fapi calls [1][19].

## Audit trail

Every config-mutating server action writes a row with the full before and after snapshot. The targets are the 12 members of `AuditTarget` in `lib/db/audit-log.types.ts`: customer, storefront, connector, connector_mapping, backend, warehouse_routing, shipment_methods, sku_blacklist, ddp_rules, template_collection, template and user. `audit-trail.const.ts` only derives display maps from that union [22][23].

- **Snapshots.** Before and after come from the same read function, never a GET on one side and the write response on the other. config-service's read and write projections differ, so an asymmetric pair reports changes nobody made.
- **History only.** Rows record what an operator did. They never feed current config.
- **Masking.** Snapshots hold connector credentials in full. `listAuditLogs` runs every row through `mask-audit-details.ts` before it reaches a client component. A changed secret masks to a distinct token on each side and an unchanged one to the same token, so the drawer diff still flags credential changes [24].
- **Writer.** `writeAuditLog` and `writeSessionAuditLog` never throw, and callers await them inside the request. They build the whole row once: a lowercase UUID `eventId`, `timestamp`, `sourceIp` (the client hop before the load balancer) and `businessId` lifted from details [25].
- **Sink.** `AUDIT_SINK` is `mongo`, `both` or `service`, default `mongo`. `both` and `service` publish an `AuditMessage` to `AUDIT_TOPIC` (`audit.<env>.fuse.v1`) through the `@gfs-bifrost/audit` publisher. The publisher never rejects. A failure is logged and counted as `fuse.audit.publish_failed` [1][26].
- **Kind.** `lib/audit/audit-message.ts` classifies a row as `credential_access`, `user_change` or `config_change`, exactly as audit-service's legacy importer does [27].
- **Environments.** `config.ts` refuses to boot with a non-`mongo` sink and no topic. Terraform forces previews to `mongo`. It grants the runtime service account publisher on the topic outside previews. Dev sets `both`. Prod leaves the default `mongo` [1][11][28][29].
- **Reads.** Reads come only from Mongo. Rows use `eventId ?? ObjectId` as their id, so `?change=` links survive a move to audit-service [30].
- **Retention.** The TTL index is opt-in via `AUDIT_LOG_RETENTION_DAYS`. Dev and prod set 24855 days, a retain-forever placeholder [30][28][37].
- **Lockdown.** `auditConfigChange` is `server-only`. The one client-callable write, `logAuditEvent`, accepts only a connector credential view or copy in a fixed strict shape. Both readers assert admin inside [31][32].
- **Coverage.** Config actions, user routes, template saves and credential links write rows. Retry Queue actions, dedupe release and tracker notes write none.
- **Previews.** They have no load balancer, so `sourceIp` there is client-supplied [33].

```orient-flow
{ "v": 1, "title": "Audit write and read path",
  "nodes": [
    { "id": "ac", "label": "Config-mutating action", "sub": "before + after snapshot", "kind": "step", "ev": [22] },
    { "id": "aw", "label": "audit-writer", "sub": "never throws", "kind": "step", "service": "fuse-ui", "tone": "accent", "ev": [25] },
    { "id": "ml", "label": "audit_log", "sub": "Mongo, TTL opt-in", "kind": "store", "ev": [30] },
    { "id": "tp", "label": "audit.<env>.fuse.v1", "sub": "sink both or service", "kind": "topic", "ev": [26, 29] },
    { "id": "as", "label": "audit-service", "kind": "service", "service": "audit-service", "ev": [29] },
    { "id": "rd", "label": "Admin readers", "sub": "listAuditLogs, masked", "kind": "step", "ev": [24, 31] }
  ],
  "edges": [
    { "from": "ac", "to": "aw" },
    { "from": "aw", "to": "ml", "label": "sink mongo or both" },
    { "from": "aw", "to": "tp", "label": "publish", "style": "dashed" },
    { "from": "tp", "to": "as" },
    { "from": "ml", "to": "rd", "label": "mask at read" }
  ] }
```

## Design system and component layering

- **`@ilg-platform/ui-toolkit`** (shadcn-based) is the shared design system: primitives under `shadcn/*` plus app-layout pieces such as `GNavigationGuardProvider`. Do not hand-roll a primitive it already has.
- **`components/`** holds app-wide generic pieces: dialogs, theme provider, icons.
- **`modules/<feature>/components/`** holds feature UI, such as `customer-sidebar`, `connector` and `order-tracker`. Extend this layer for new feature work, not `components/`.
- **`const/use-case.const.ts`** holds `useCaseRegistry`. One entry per use case supplies its labels, direction, icon and connector types [34].

## Route surface (representative, not exhaustive)

| Area | Routes |
| --- | --- |
| Customers | `/customer`, `/customer/[customerId]`, storefront and connector pages, `.../connector/[connectorId]/[useCase]` (mapping editor) |
| Central config | `/customer/[customerId]/account-management/central-configurators/{backend,ddp,shipping-methods,sku-ignore,vas,warehouse-routing}` |
| Operational | `/customer/[customerId]/{exceptions,dedupe-summary,transaction-history,changes}`. `exceptions` is the Retry Queue. `changes` is the admin-only Change History. |
| Templates | `/templates`, `/templates/[collectionId]`, `/templates/[collectionId]/[useCase]` |
| Order tracker | `/order-tracker` (flag-gated), `/api/order-tracker/export` (CSV stream) |
| User management | `/user-management`, `/user-management/users`, `/user-management/audit-log`, all admin-only |
| Auth and API | `/login`, `/api/auth/*`, `/api/log-error`, `/api/customer/[customerId]/master-data/skus` |
| Central admin | `/central-admin` and `/central-admin/rules-mapping` are stub pages with no nav link |

`/` redirects to `/customer`. The top nav shows Customers and Templates, Order Tracker with the flag, and User Management for admins [35][36].

## Feature flags

**Runtime flags** live in config-service (`/api/v1/feature-flags`), never in fuse-ui's Mongo (G1). A server component reads one with `isFeatureEnabled(key, default)` (`lib/feature-flags/is-feature-enabled.ts`). It fetches the whole list once per request (React `cache()`, no cross-request cache) under a 1 s timeout and evaluates with `evaluateFeatureFlag` from types, so a due scheduled change applies on read with nothing written. Unreachable, slow, an unknown key, or a flag that fails validation all return the code default and log `FellBackToDefault`; it never renders an error page. Admins manage flags at `/user-management/feature-flags` (create, switch, schedule, edit, delete). Each write is audited as target `feature_flag/<key>` with snapshots read back via GET, `before` null on create and `after` null on delete (G2). Only switch, schedule and edit send `expectedVersion`; create and delete don't. fuse-ui evaluates with no context, so a flag with `targets` set elsewhere reads false here, while the drawer's hard-coded label still says "Everyone". There's no per-customer targeting in v1. Dev flags reach every preview env, because previews read dev config-service. `fuse-ui.mapping-dictionaries` is the first reader, and its default is still the env flag below.

**Env flags** are booleans in `config.ts`, on only when exactly `'true'`: `FEATURE_FLAG_MAPPING_DICTIONARIES` (Dictionaries tab and `lookup()` in the mapping editor), `FEATURE_FLAG_EDI_EGRESS` (the `edi` egress file type and `ediEnvelope` fields on the SFTP connector form) and `FEATURE_FLAG_ORDER_TRACKER`. All three are Terraform variables wired to Cloud Run env, and all three are on in dev and prod (dictionaries in prod since 2026-10-14, fuse-ui#313) [1][28][29][37]. See [[operations]].

## Order tracker: support's view over tracking-service

`/order-tracker` (`app/order-tracker/page.tsx`, `modules/order-tracker/`, `server-functions/order-tracker/`) is a standalone, sidebar-free page. It holds an L2 work queue (failures grouped by customer, each linked to its Retry Queue failure and to Transaction History searched by the ref), shipments and returns lists, a detail sheet, insights and bulk lookup. It reads tracking-service's API [17][38].

- The writes are tracker notes (author is always the session email) and Release hold, which calls dedupe-service [16][39][55].
- The flag gates the page, its server functions, its actions and the export route. All answer 404 with it off [54]. `config.ts` refuses to boot with the flag on and no valid `FUSE_TRACKER_API_URL`. `/central-admin/order-tracker` redirects here with a 308 [1][2][38][54].
- Any signed-in user can open it. The customer dashboard also shows an "Orders in flight" card behind the flag [38][56].
- Calls degrade against an older tracker API. A missing per-business day route renders without it. An API that 400s `attention=action` gets both lanes fetched and split in `order-tracker.func.ts`. The UI and tracking-service deploy in either order [17].

## Mapping editor

- **Engine.** `@gfs-bifrost/rules-engine` is a direct dependency. The expression builder parses the DSL (`parseDsl`), and the Test Mapping dry run uses `getDSLRunner` in the browser. The connectors run the same engine downstream [40][41][57].
- **Dictionaries.** They ride on the mapping config (`config.dictionaries`). The editor adds, updates and removes them through `stores/dictionary-reducers.ts` and validates with `MappingDictionariesSchema` from `@gfs-bifrost/types` (`logic/mapping-dictionary.logic.ts`). The dry run builds one `DictionaryLookup` per run for `lookup()` [41].
- **Required keys.** The required mapping keys per use case and their labels are hard-coded in `configuration.func.ts` and `server-functions/data/*-keys.json`. config-service does not supply them [42].
- **Discriminator.** Branch a `MappingConfig` on `config.configType === 'lines'`. `LinedMappingConfig` carries `configType`, but `GroupedTranslatorConfig` does not. `isGroupedTranslatorConfig` (`'groupBy' in config`) narrows to the grouped type and drops the union [43][44].
- **Validity gates.** The customer editor's `calculateIsValid` (grouped and simple stores) and the template save gate `validateMappingConfig` both call `computeCoverage`, so they cannot disagree. A default counts as handling a required key on every inbound flow. On an outbound flow only a template counts it, through `defaultsSatisfyRequiredKeys`, because a default on an outbound file emits no column. The Test Mapping dry run still pools header and line rules, so a header default can satisfy a line requirement there but not in the gate [43][45][46][58].

## Build, test, deploy

- **Tooling.** `code/mise.toml` pins `bun` 1.2.20 as the task runner, with `node 24` and `pnpm` 11.0.8. CI and the Dockerfile install with pnpm. Lint is Biome. `check-and-lint` is typecheck plus `lint:fix` [20][47][48].
- **Tests.** `pnpm test` runs Jest in jsdom with `--passWithNoTests`, so CI passes a run with zero tests. The ref has 76 spec files against 493 other `.ts` and `.tsx` files under `code/src` [20][49].
- **Jest limits.** `jest.mock` has no `@/` mapper, so mock by relative path. Jest cannot load `@ilg-platform/ui-toolkit`'s ESM-only subpath exports. A spec that reaches the toolkit stubs each subpath with `jest.mock('<subpath>', …, { virtual: true })` (`app-data-table.spec.tsx`). Server-function specs mock `lib/api-client/api-client` by relative path [49].
- **CI.** `code-quality.yaml` runs lint, test and build on PRs and nightly at 06:00 UTC [50].
- **Deploy.** Per-PR preview environments, the nightly sweep, the prod approval gate and deploy mechanics live in [[operations]].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "code/src/config.ts@ca5962f" },
  { "id": 2, "kind": "code", "ref": "code/next.config.ts@ca5962f" },
  { "id": 3, "kind": "code", "ref": "code/src/lib/utils/result.ts@ca5962f" },
  { "id": 4, "kind": "code", "ref": "code/src/proxy.ts@ca5962f" },
  { "id": 5, "kind": "code", "ref": "code/src/lib/auth/session.ts@ca5962f" },
  { "id": 6, "kind": "code", "ref": "code/src/app/api/auth/login/route.ts@ca5962f" },
  { "id": 7, "kind": "code", "ref": "code/src/lib/api-client/api-client.ts@ca5962f" },
  { "id": 8, "kind": "code", "ref": "code/src/app/api/auth/users/route.ts@ca5962f" },
  { "id": 9, "kind": "code", "ref": "code/src/lib/db/users.collection.ts@ca5962f" },
  { "id": 10, "kind": "code", "ref": "code/src/app/server-functions/storefronts/storefronts.action.ts@ca5962f" },
  { "id": 11, "kind": "code", "ref": "iac/projects/fuse-ui/iam.tf@ca5962f" },
  { "id": 12, "kind": "code", "ref": "code/src/app/server-functions/user/users.func.ts@ca5962f" },
  { "id": 13, "kind": "code", "ref": "code/src/instrumentation.ts@ca5962f" },
  { "id": 14, "kind": "doc", "ref": "Engineering/fuse-ui/plans/FUSE-1070-template-library-storage-browse-and-crud.md" },
  { "id": 15, "kind": "code", "ref": "code/src/app/server-functions/central-admin/failures.func.ts@ca5962f" },
  { "id": 16, "kind": "code", "ref": "code/src/app/server-functions/customer/dedupe-summary.func.ts@ca5962f" },
  { "id": 17, "kind": "code", "ref": "code/src/app/server-functions/order-tracker/order-tracker.func.ts@ca5962f" },
  { "id": 18, "kind": "code", "ref": "code/src/app/server-functions/storefronts/retrieval-condition-preview.func.ts@ca5962f" },
  { "id": 19, "kind": "code", "ref": "code/src/app/server-functions/storefronts/connector-credential-link.func.ts@ca5962f" },
  { "id": 20, "kind": "code", "ref": "code/package.json@ca5962f" },
  { "id": 21, "kind": "code", "ref": "code/src/app/server-functions/customer/customer.func.ts@ca5962f" },
  { "id": 22, "kind": "code", "ref": "code/src/app/server-functions/audit/audit-config-change.func.ts@ca5962f" },
  { "id": 23, "kind": "code", "ref": "code/src/lib/db/audit-log.types.ts@ca5962f" },
  { "id": 24, "kind": "code", "ref": "code/src/lib/audit/mask-audit-details.ts@ca5962f" },
  { "id": 25, "kind": "code", "ref": "code/src/lib/audit/audit-writer.ts@ca5962f" },
  { "id": 26, "kind": "code", "ref": "code/src/lib/audit/audit-publisher.ts@ca5962f" },
  { "id": 27, "kind": "code", "ref": "code/src/lib/audit/audit-message.ts@ca5962f" },
  { "id": 28, "kind": "code", "ref": "iac/env/dev.tfvars@ca5962f" },
  { "id": 29, "kind": "code", "ref": "iac/projects/fuse-ui/variables.tf@ca5962f" },
  { "id": 30, "kind": "code", "ref": "code/src/lib/db/audit-log.collection.ts@ca5962f" },
  { "id": 31, "kind": "code", "ref": "code/src/app/server-functions/user/audit-log.func.ts@ca5962f" },
  { "id": 32, "kind": "code", "ref": "code/src/app/server-functions/audit/log-audit-event.func.ts@ca5962f" },
  { "id": 33, "kind": "code", "ref": "code/src/lib/utils/client-ip.ts@ca5962f" },
  { "id": 34, "kind": "code", "ref": "code/src/const/use-case.const.ts@ca5962f" },
  { "id": 35, "kind": "code", "ref": "code/src/app/page-header.tsx@ca5962f" },
  { "id": 36, "kind": "code", "ref": "code/src/app/central-admin/rules-mapping/page.tsx@ca5962f" },
  { "id": 37, "kind": "code", "ref": "iac/env/prod.tfvars@ca5962f" },
  { "id": 38, "kind": "code", "ref": "code/src/app/order-tracker/page.tsx@ca5962f" },
  { "id": 39, "kind": "code", "ref": "code/src/modules/order-tracker/components/sheet-help.tsx@ca5962f" },
  { "id": 40, "kind": "doc", "ref": "CLAUDE.md, Package Changelog, @gfs-bifrost/rules-engine 2.1.0" },
  { "id": 41, "kind": "code", "ref": "code/src/modules/translator-config-editor/logic/dry-run-mapping.logic.ts@ca5962f" },
  { "id": 42, "kind": "code", "ref": "code/src/app/server-functions/configuration.func.ts@ca5962f" },
  { "id": 43, "kind": "code", "ref": "code/src/modules/translator-config-editor/logic/translator-config.logic.ts@ca5962f" },
  { "id": 44, "kind": "code", "ref": "code/src/lib/gen/config-service.client.d.ts@ca5962f" },
  { "id": 45, "kind": "code", "ref": "code/src/modules/translator-config-editor/stores/grouped-config-editor/grouped-config-editor-store.ts@ca5962f" },
  { "id": 46, "kind": "code", "ref": "code/src/modules/translator-config-editor/logic/mapping-config-validity.logic.ts@ca5962f" },
  { "id": 47, "kind": "code", "ref": "code/mise.toml@ca5962f" },
  { "id": 48, "kind": "code", "ref": "code/dockerfile@ca5962f" },
  { "id": 49, "kind": "code", "ref": "code/jest.config.ts@ca5962f" },
  { "id": 50, "kind": "code", "ref": ".github/workflows/code-quality.yaml@ca5962f" },
  { "id": 51, "kind": "code", "ref": "iac/projects/fuse-ui/backend.tf@ca5962f" },
  { "id": 52, "kind": "code", "ref": "iac/projects/fuse-ui/cloud-run.tf@ca5962f" },
  { "id": 53, "kind": "code", "ref": "code/src/lib/api-client/fuse-tracker/id-token.ts@ca5962f" },
  { "id": 54, "kind": "code", "ref": "code/src/lib/api-client/fuse-tracker/tracker-result.ts@ca5962f" },
  { "id": 55, "kind": "code", "ref": "code/src/app/server-functions/order-tracker/order-tracker.action.ts@ca5962f" },
  { "id": 56, "kind": "code", "ref": "code/src/app/customer/[customerId]/page.tsx@ca5962f" },
  { "id": 57, "kind": "code", "ref": "code/src/modules/translator-config-editor/components/expression-builder/expression-builder.tsx@ca5962f" },
  { "id": 58, "kind": "code", "ref": "code/src/modules/translator-config-editor/logic/required-field-coverage.logic.ts@6f0d67f" }
] }
```
