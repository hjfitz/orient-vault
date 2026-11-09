---
tags: [waypoint, ledger]
title: fuse-ui — work ledger
---
# fuse-ui — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-11-05 — Run fuse-ui on the golden runtime image

Run fuse-ui on the golden runtime image

Moves fuse-ui's runtime stage onto ilg-platform's node24-runtime:0.1-affogato (build stages to glibc node:24) and drops the Datadog serverless-init sidecar and shared volume; DD_* settings move onto the app container with the same values. Verified on dev revision fuse-ui-app-dev-00434-dcb (single container, logs tagged dd.datadog_init_version, authenticated pages render). Dev deploys now announce failures only.

PR: gfs-bifrost/fuse-ui#403

## 2026-10-29 — FUSE-1336

Offer despatches[] fields in the goods-out confirmation mapping editor

The goods-out confirmation mapping editor's field list had no despatches[] entries, so despatches[].carrier.id and despatches[].carrier.track showed on existing mappings but could not be added. Added the nine despatches[] keys from the canonical GoodsOutConfirmationDespatch to goods-out-confirmation-keys.json. Checked in the Nuzest dev mapping editor (rule added, not saved). Saving and an end-to-end confirmation are not verified. Draft PR; fuse-ui's default branch is main, not master.

PR: gfs-bifrost/fuse-ui#394

## 2026-10-19 — FUSE-1319

Label a Snap outage as Snap being unavailable

Retry Queue maps replay's new `create.snap_unavailable` failure point to the Snap zone, label "Snap was unavailable; replay once it is back"; "Failed at Snap" and the Where It Failed grouping include it, and the remedy already says replay because the failure is now retryable. Must merge after replay-service#125 is in prod (it is). Found while capturing evidence: a successfully replayed create-side failure stays as "Failed Again" until dismissed (no clear-down in replay or `replayFailure`; the FUSE-521 comment in retry-queue.const.ts is stale).

PR: gfs-bifrost/fuse-ui#345

## 2026-10-19 — Show where each failure happened in the Retry Queue

Show where each failure happened in the Retry Queue

Ship: SHIP-1019-retry-queue-failure-point. Where It Failed column, 'Failed at' zone filter and grouping from replay's failurePoint; grouped counts now respect the claimed filter. Merges only after replay-service#121 is in prod.

PR: gfs-bifrost/fuse-ui#341
PR: gfs-bifrost/fuse-ui#343

## 2026-10-19 — FUSE-1223

Required-field check counts fallback values, with a coverage panel

A required mapping field supplied only by a default no longer blocks Save (Academically Gifted Retail ID case). One `computeCoverage` (logic/required-field-coverage.logic.ts) now backs both stores' `calculateIsValid`, `validateMappingConfig` and the editor's coverage panel, so the gates cannot disagree. Defaults count on inbound flows (fileIn, shopifyIn); outbound customer mappings stay rules-only because a default on SFTP egress emits no column; `defaultsSatisfyRequiredKeys` survives only to let a template defer on outbound. States: gap (blocks save), conflict (fixed rule plus fallback), check (column rule plus fallback). Panel under the tab pills on every tab, actions Add mapping, Add fallback, Remove fallback, Remove mapping, Always send X (column rule becomes a fixed literal rule, fallback deleted). UI term is now Fallback Values; code keeps `defaults`. Fixed `serializeArg` to escape backslashes. No server change: config-service has no required-field validation. Shipped to prod slice by slice at Harry's instruction, QA skipped. [[mapping-template-library]] updated; architecture.md Validity gates rewritten.

PR: gfs-bifrost/fuse-ui#336
PR: gfs-bifrost/fuse-ui#337
PR: gfs-bifrost/fuse-ui#338
PR: gfs-bifrost/fuse-ui#340

## 2026-10-19 — Retire the order tracker's duplicates week tile

Retire the order tracker's duplicates week tile

Removed the 'Duplicates collapsed' tile from Insights > Last 7 days: tracking-service#16 stopped counting republished copies in the daily stats (they contended on stats/_all__<day>), so totals.duplicates is historic only from 2026-10-19. Per-shipment copy counts (timeline xN, detail sheet, table tooltip) still render. Re-vendored the tracker openapi (description-only). Gotcha: mise's NODE_ENV=development breaks 'next build' prerender locally; build with NODE_ENV=production. Plan retire-the-order-tracker-s-duplicates-week-tile.

PR: gfs-bifrost/fuse-ui#339

## 2026-10-19 — Sign off the runtime feature flags page plan

Sign off the runtime feature flags page plan

All five PRs merged (#316, #317, #318-#320) and the ACs are met; targeting (AC 4) is out of v1. Still owed: remove FEATURE_FLAG_MAPPING_DICTIONARIES and its tfvars. That waits on creating the prod flag fuse-ui.mapping-dictionaries, and prod config-service has no flags at all (snapshot 2026-10-19). The gen-config-service-client script still 401s; repointing it is [[regenerate-the-config-service-client-from-the-ge]] AC 1. Learnings promoted into architecture (Feature flags, BFF, Auth), design Traps, operations (previews) and known-context.

Plan: [[runtime-feature-flags-audited-flag-page]].

## 2026-10-15 — Label SFTP audit events and hide SFTP logins by default

Label SFTP audit events and hide SFTP logins by default

Labels the sftp_user target and logged_in/login_failed actions, adds readable summaries for SFTP logins and SFTP user creations, and gives the drawer a raw-string/gray fallback for unknown actions/targets.
SFTP logins (~8k/day) are hidden on the global and customer audit pages unless ?sftpLogins=show; hidden sends excludeKind=sftp_login to audit-service /events and /filter-options. A login action filter always includes logins; ?change= deep links are unaffected.
Depends on the parallel audit-service excludeKind PR being deployed first (unknown params are ignored until then).

PR: gfs-bifrost/fuse-ui#333

## 2026-10-15 — Show each connector's confirmation outcome on the order tracker

Show each connector's confirmation outcome on the order tracker

Order tracker unit C7 (per-connector part, on tracking-service C6): re-vendored the spec, confirmationPhase fails while any connector fails, list-dot tooltips list connectors, sheet confirmation rows get a connector table; a lone seeded 'unknown' entry is hidden.

PR: gfs-bifrost/fuse-ui#332

## 2026-10-15 — Act on the order tracker UX review

Act on the order tracker UX review

Order tracker unit C7: approved items 1, 3-16, 18 and three minors from the 18-item UX review - phone layout (status under ref, Fix first, vertical stepper), one outage notice with Retry, cold-load skeleton, lane naming, list dates, sheet ordering, not-found next step. Per-connector breakdown left for C6.

PR: gfs-bifrost/fuse-ui#331

## 2026-10-15 — Check the vendored tracking-service spec against tracking-service main

Check the vendored tracking-service spec against tracking-service main

Order tracker unit B10: Tracker Contract workflow diffs the vendored tracking-service openapi.yaml against tracking-service main and checks the generated client is current; PR-path-filtered + weekday schedule, non-required. Re-vendored three drifted description lines.

PR: gfs-bifrost/fuse-ui#330

## 2026-10-15 — Sort the order tracker lists by date and limit them to a date window

Sort the order tracker lists by date and limit them to a date window

Order tracker unit C8: last-activity/received sort and date windows (presets + custom UK days) on the shipments and returns lists, carried into the CSV export; disabled with a reason during search and attention. Unblocked by the tracking-service cutover (indexes only in the new database).

PR: gfs-bifrost/fuse-ui#329

## 2026-10-15 — Remove the Mongo audit path from fuse-ui

Remove the Mongo audit path from fuse-ui

UF.3: fuse-ui now only publishes audit events (audit.<env>.fuse.v1) and only reads from audit-service. Deleted audit-log.collection.ts, the AUDIT_SINK / AUDIT_READ_SOURCE / AUDIT_LOG_RETENTION_DAYS config, guards and IaC vars, and offset paging (cursor pager always). Preview envs get an empty topic + service URL via IaC locals: they record nothing and read an empty log. Mongo audit_log is frozen at 255 prod rows, all present in audit-service; dropping it is UH, still behind G6. Merged after #328 and a 0-missing catch-up import; Harry approved in chat.

PR: gfs-bifrost/fuse-ui#325

## 2026-10-15 — Cut prod's audit log over to audit-service

Cut prod's audit log over to audit-service

Prod fuse-ui audit_sink both -> service: new audit events go to audit-service only, Mongo audit_log is now frozen (G6 still gates the drop). Flipped early (Harry waived the 24h soak) once 6 real prod events were stored, publish_failed 0, DLT 0, Mongo 255 = service 255 per tenant. Catch-up import (Mongo -> service, idempotent) runs after deploy; #325 removes the Mongo code path next.

PR: gfs-bifrost/fuse-ui#328

## 2026-10-15 — Point the order tracker at the tracking-service API

Point the order tracker at the tracking-service API

Repointed fuse_tracker_api_url in dev and prod tfvars from the legacy fuse-tracker API to tracking-service, after both envs cut over on 2026-10-14. Unblocks destroying the legacy stack.

PR: gfs-bifrost/fuse-ui#327

## 2026-10-14 — Read prod's audit log from audit-service

Read prod's audit log from audit-service

prod.tfvars audit_read_source=service while audit_sink stays both, so it is reversible (Mongo still gets every event). Preceded by the prod legacy import under both: 249 inserted, 0 failed, verify 249/249, per-tenant parity exact. fuse-ui-prod is audit-service-prod's run.invoker and only READ_CALLERS entry.

PR: gfs-bifrost/fuse-ui#326

## 2026-10-14 — Turn on audit dual-publish in prod

Turn on audit dual-publish in prod

prod.tfvars audit_sink=both: prod writes audit_log and publishes the same eventId to audit.prod.fuse.v1 (publisher grant already applied with #305). Starts the prod soak; the one-way sink=service flip waits for ≥24h of both with real events stored and fuse.audit.publish_failed=0, dead-letter=0. Prod volume is a handful of events a day.

PR: gfs-bifrost/fuse-ui#324

## 2026-10-14 — Cut dev's audit log over to audit-service

Cut dev's audit log over to audit-service

dev.tfvars: audit_sink=service + audit_read_source=service in one deploy (the config guard refuses a mismatched pair); dev audit_log frozen, then the legacy import (audit-service cmd/import-legacy, source db fuse-ui-app, read-only audit_migration user from #306) copies it in. Rehearsal of the prod cutover; prod uses a safer order (migrate under both, read=service under both, then sink=service + catch-up import) — see Audit Service Migration State decision log 2026-10-14.

PR: gfs-bifrost/fuse-ui#323

## 2026-10-14 — Admin Feature Flags page (stack #318-#320)

Admin Feature Flags page (stack #318-#320)

Platform -> Feature Flags at /user-management/feature-flags: list with All/On/Off/Scheduled counts and search, New Flag, and a drawer to switch (behind a confirm), schedule a change in UK time (cancellable), read history from the audit log, edit details and delete. Every write sends expectedVersion, so a concurrent change gives 409 and the latest version is shown. Writes reuse the audited server functions from #316. x-user already comes from the proxy, so no new plumbing. Verified live against dev config-service, including a scheduled flip with no write. Gotchas: GDateField minDate=new Date() disables today; a throwing zod refine turns into tanstack's 'async function passed to sync validator'. Plan inc 3.

PR: gfs-bifrost/fuse-ui#318
PR: gfs-bifrost/fuse-ui#319
PR: gfs-bifrost/fuse-ui#320

## 2026-10-14 — Read feature flags at runtime, starting with mapping dictionaries

Read feature flags at runtime, starting with mapping dictionaries

Runtime feature flags in fuse-ui, part 2 (reader and first adopter); workshop action L3, with no ticket.

- The server-only isFeatureEnabled(key, default) reads /api/v1/feature-flags once per request via React cache, with no cross-request cache, races a 1 s timeout, parses each flag with FeatureFlagSchema, and evaluates with evaluateFeatureFlag. Any failure returns the default and logs a warning.
- Why a race rather than an AbortSignal: configServiceClient retries 3 times with jitter.
- fuse-ui.mapping-dictionaries now gates the Dictionaries tab in both mapping editors, defaulting to the FEATURE_FLAG_MAPPING_DICTIONARIES env value. The dev flag is seeded to resolve true.
- Verified live against dev config-service: the tab hides and shows on a flip and on a scheduled change, with 5 screenshots on the evidence branch.
- Follow-up: once the prod flag exists, remove the env var and its tfvars.

Plan: [[runtime-feature-flags-audited-flag-page]].

PR: gfs-bifrost/fuse-ui#317

## 2026-10-14 — Add feature-flag client types, audit target and admin server functions

Add feature-flag client types, audit target and admin server functions

Runtime feature flags in fuse-ui, part 1; workshop action L3, with no ticket.

- The config-service client is regenerated from its committed openapi.yaml, giving +243 additive lines. Gotcha: run biome format afterwards, or it's a 6.7k-line reformat.
- feature_flag is now an AuditTarget, which classifies as config_change.
- Admin-only server functions for list, get, create, update and delete. Before and after are both read via GET and recorded with auditConfigChange; a refused write records no audit row.
- Admin-only was the default chosen, matching the design. Prod flips are audited as the shared fuse-support@ admin until named admins exist.
- No page yet: that is inc 3, gated on config-service prod. The reader is inc 4.

Plan: [[runtime-feature-flags-audited-flag-page]].

PR: gfs-bifrost/fuse-ui#316

## 2026-10-14 — Show confirmation mappings in the direction the data flows

Show confirmation mappings in the direction the data flows

Egress (confirmation) mappings are stored from = file column, to = Fuse field and inverted by sftp-connector, but the editor rendered them like ingress. The table and rule modal now put the Fuse field first on egress, with direction-aware labels, tooltips and modal copy; Expression tab hidden on egress; CHANGE_ME_ rows marked Rename. Presentation only.

PR: gfs-bifrost/fuse-ui#314

## 2026-10-14 — Turn the mapping dictionaries flag on in prod

Turn the mapping dictionaries flag on in prod

Sets feature_flag_mapping_dictionaries = true in iac/env/prod.tfvars so prod shows the Dictionaries tab and lookup() in the mapping editor. Backend (config-service, sftp-connector, shopify-connector) already has the dictionary commits in its last successful prod deploy, checked by ancestry. No ticket: the dictionary tickets are all Done. Merged as f1538e4 and deployed 2026-10-14. Prod plan 0/1/0 on fuse-ui-app-prod (image, flag env, standing sidecar/container-dependencies/scaling drift, same as the previous plan). Live: fuse-ui-app-prod-00068-g9f, image prod-f1538e4, FEATURE_FLAG_MAPPING_DICTIONARIES=true. Not re-driven in the prod UI; whether any customer mapping already uses a dictionary was not checked.

PR: gfs-bifrost/fuse-ui#313

## 2026-10-14 — FUSE-1256

Turn FEATURE_FLAG_EDI_EGRESS on in prod

prod.tfvars adds feature_flag_edi_egress = true, merged only after sftp-connector's prod flag was live. Prod plan 0/1/0 on fuse-ui-app-prod (image + the flag env + standing sidecar and scaling drift); the deploy also shipped Renovate #311. Live: fuse-ui-app-prod-00067-8pn Ready, image prod-d610a91, FEATURE_FLAG_EDI_EGRESS=true. The connector form now offers EDIFACT in prod.

PR: gfs-bifrost/fuse-ui#312

## 2026-10-12 — Page the audit log over audit-service's cursor, and wire the read switch

Page the audit log over audit-service's cursor, and wire the read switch

UF read path PR-C (3/3). Cursor back stack (cursor/cursors in URL, ~ = first page) in audit-filters.logic; table branches on 'nextCursor' in page; '1000+ records' when capped; off-page ?change= fetched via getAuditLog(id, businessId?) (tenant check in fuse-ui since audit-service get-by-id isn't tenant-scoped). IaC: audit_read_source (mongo; previews forced) + audit_service_url literals. Verified locally end to end against real audit-service + import-legacy, with per-filter parity.

PR: gfs-bifrost/fuse-ui#310

## 2026-10-12 — Read the audit log from audit-service behind AUDIT_READ_SOURCE

Read the audit log from audit-service behind AUDIT_READ_SOURCE

UF read path PR-B (2/3). lib/audit/audit-reader.ts switches Mongo vs audit-service on AUDIT_READ_SOURCE (default mongo); audit-service-reader.ts + audit-event.ts (fromAuditEvent inverse of toAuditMessage); AuditLogPage = offset | cursor union; getAuditLog(id) in both sources (24-hex legacy ids via _id). Config refuses sink/read mismatch. Connector history keeps targetId-only (includes connector_mapping rows) — audit-service needs a {system,target.id,occurredAt} index before prod reads. No IaC yet.

PR: gfs-bifrost/fuse-ui#308

## 2026-10-12 — Add an audit-service API client with a shared ID-token helper

Add an audit-service API client with a shared ID-token helper

UF read path PR-A (1/3). fuse-tracker/id-token.ts → api-client/id-token.ts (idTokenAuthHeaders(audience), server-only); generated auditServiceClient from audit-service openapi.yaml (gen-audit-service-client), BFF dependency audit-service; optional AUDIT_SERVICE_URL. Inert: nothing calls the client. Verified on dev: tracker list + CSV export through the moved helper.

PR: gfs-bifrost/fuse-ui#307

## 2026-10-12 — Add a read-only Atlas user for the audit-service import

Add a read-only Atlas user for the audit-service import

mongodbatlas_database_user.audit_migration (read on fuse-ui.audit_log only; DB also holds password hashes) plus sensitive output audit_migration_mongodb_uri for import-legacy -source-uri. count=0 in previews. Audit Service UF cutover prerequisite; remove with the Mongo path.

PR: gfs-bifrost/fuse-ui#306

## 2026-10-12 — Turn on audit dual-publish in dev

Turn on audit dual-publish in dev

One-line dev.tfvars change (audit_sink = "both"); dev plan 0 add / 1 change / 0 destroy. Starts the UF dev soak: new dev audit rows should land in audit-service under the same eventId with publish_failed and the dev .dlt at zero. #299–#302 merged and in prod (9aa6174, AUDIT_SINK=mongo) earlier the same day.

PR: gfs-bifrost/fuse-ui#305

## 2026-10-12 — FUSE-1255

Stop listing returns as not sent on EDIFACT connectors

Removed EDI_UNSUPPORTED_CONFIRMATIONS and the 'Not sent as EDIFACT' warning; sftp-connector#307 sends returns as EDIFACT now.

PR: gfs-bifrost/fuse-ui#304

## 2026-10-12 — Dual-publish audit events to audit-service behind AUDIT_SINK

Dual-publish audit events to audit-service behind AUDIT_SINK

Stacked drafts on #299: #300 mints a lowercase UUID eventId per audit row (row id = eventId ?? ObjectId, so ?change= links survive cutover); #301 adds AUDIT_SINK/AUDIT_TOPIC env vars and a by-name pubsub.publisher grant on audit.<env>.fuse.v1 (previews forced to mongo, no grant); #302 publishes via @gfs-bifrost/audit when sink=both, mapper mirrors audit-service legacy.Kind/Map, validated with FuseAuditMessageSchema before send, failures counted as fuse.audit.publish_failed{reason}. Native stack #303. Local run proved store in audit-service dev. dev flips to both in a later tfvars PR.

PR: gfs-bifrost/fuse-ui#300
PR: gfs-bifrost/fuse-ui#301
PR: gfs-bifrost/fuse-ui#302

## 2026-10-12 — Harden the audit log ahead of the audit-service cutover

Harden the audit log ahead of the audit-service cutover

Draft gfs-bifrost/fuse-ui#299 (Audit Service unit UA). All server-side audit writes go through lib/audit/audit-writer.ts (server-only, never throws, awaited); logAuditEvent only accepts a connector credential view/copy; auditConfigChange is server-only; listAuditLogs/listAuditLogFilterOptions check admin themselves; lib/audit/mask-audit-details.ts masks snapshots pairwise before rows leave the server. Gotcha: the shared redacting logger throws on a MongoServerError, so the writer logs plain errorName/errorMessage. UF swaps the writer's sink to audit-service.

PR: gfs-bifrost/fuse-ui#299

## 2026-10-09 — Record and show the source IP on audit log rows

Record and show the source IP on audit log rows

Audit rows now store the client IP (hop before the Google LB in x-forwarded-for, spoof-resistant) as optional sourceIp; Audit Log table and drawer show it. Old rows show a dash. Verified locally against a throwaway Mongo (real audited action, spoofed leading hop ignored); dev manual-deploy green.

PR: gfs-bifrost/fuse-ui#298

## 2026-10-09 — FUSE-1253

Add EDIFACT egress option to the SFTP connector form behind a feature flag

Connector edit form output-file-type gains EDIFACT (egressFiletype edi) with ediEnvelope fields (sender/receiver id + qualifier, test indicator), a warning listing confirmation types with no EDIFACT message, display label and pending-changes/audit-summary entries. Hidden behind featureFlags.ediEgress (FEATURE_FLAG_EDI_EGRESS). Flag-off payload carries no ediEnvelope. Paths: code/src/config.ts, code/src/modules/connector/{components/sftp-connector-config.tsx,components/sftp-edi-envelope.tsx,logic/sftp-connector-form.logic.ts}, code/src/modules/audit-trail/logic/. Flag wired into iac and on in dev afterwards (0b593e1).

PR: gfs-bifrost/fuse-ui#275

## 2026-10-09 — FUSE-1238

Work-order mapping editor: carrier key and line number label

Added identifiers.carrierId (Carrier) to the Work Order key list, and on Work Order Confirmation lines added soLineId as Line Number and relabelled line to Snap Line Key. Two hand-maintained JSON key lists, no code change. Merged; prod deploy gate pending.

PR: gfs-bifrost/fuse-ui#296

## 2026-10-07 — Turn the order tracker into an L2 work queue

Turn the order tracker into an L2 work queue

Overview leads with Needs action grouped by customer; failed records (queue, lists, sheet) link to their replay failure (Fix) and Transaction History; Today by customer from /stats/businesses; Recurring on Insights with mapping links; What to do and held-duplicate release in the sheet; Orders in flight on the customer dashboard. Lookups are server-side, batched per business, and degrade to no link.

PR: gfs-bifrost/fuse-ui#292

## 2026-10-07 — Fit the app header on phones and light the ILG wordmark in dark mode

Fit the app header on phones and light the ILG wordmark in dark mode

Below md the top-nav links move into a toolkit Sheet behind an accessible menu button (shared item list, so the Order Tracker flag and admin gate hold in both); the 390px page no longer scrolls sideways (828 -> 390 on /, /customer, /templates, /user-management, /order-tracker). The ILG wordmark is inlined from public/img/ilg-logo.svg with its navy as currentColor (navy light, white dark); no light ILG asset exists in the repo or ui-toolkit. From a UX review; Harry approved a standalone PR.

PR: gfs-bifrost/fuse-ui#291

## 2026-10-07 — Move the order tracker out of Central Admin

Move the order tracker out of Central Admin

The order tracker now lives at its own top-level page, /order-tracker, with a full-width layout and a top-nav entry. Both are behind FEATURE_FLAG_ORDER_TRACKER. /central-admin/order-tracker permanently redirects (308) to it and keeps the query string. Live in prod as f93045b.

PR: gfs-bifrost/fuse-ui#290

## 2026-10-07 — Act on support feedback on the order tracker

Act on support feedback on the order tracker

Support's first feedback round on the hidden order tracker. The attention view is split into a 'Needs action' lane and a 'Running late' lane, with attempt counts and failure age measured from the first failure. Insights figures now come from the tracker API's single definitions. The on-time tile and the Delivered step are removed. Unmatched records no longer tick stages Fuse never saw. Rows open on click, pills match Transaction History's outlined dots, AUTO shipment ids are hidden and dates use the Transaction History format. Pairs with tracking-service 53bee46 and 20b9d2f.

PR: gfs-bifrost/fuse-ui#289

## 2026-10-06 — Bump sharp and source-map-js to clear the dependency audit

Bump sharp and source-map-js to clear the dependency audit

The nightly dependency audit went red on GHSA-wq5f-xc86-pv6w (sharp <0.35.5) and GHSA-68fv-2mgg-jv7q (source-map-js <1.2.2), both transitive. Lockfile-only bump. It was blocking #287's checks.

PR: gfs-bifrost/fuse-ui#288

## 2026-10-06 — Add a hidden order tracker page for support

Add a hidden order tracker page for support

A flag-gated /central-admin/order-tracker page (no nav entry) reads the fuse-tracker API with a Google ID token. It brings the tracker's shipments, returns, attention, insights, bulk lookup, export and notes into fuse-ui. The flag is on in dev and prod, and the fuse-ui runtime service accounts are invokers on the tracker API. Straight merge per Harry: no changelog row and no Slack post.

PR: gfs-bifrost/fuse-ui#287

## 2026-09-29 — FUSE-1238

Choose where a confirmation replay goes from the Retry Queue

The Retry Queue failure panel gains a Delivery card for confirmation failures. It shows where a replay will go (the connector that failed, or one an operator chose), and lets an operator pick another of the business's connectors or go back to the original. When there is nowhere to send it, for example the poller's no-originating-connector records, the card says so and Replay is disabled until a connector is chosen. It uses replay-service#103's routing override and regenerates the replay client from dev. Verified locally against dev services: a UI-routed replay reached fapi only. Merges after replay-service#102/#103 are in prod. Poller Clear-Down unit B3.

PR: gfs-bifrost/fuse-ui#282

## 2026-09-24 — FUSE-1253

EDIFACT egress option on the SFTP connector form behind FEATURE_FLAG_EDI_EGRESS

Third egressFiletype option + ediEnvelope fields (UNB ids/qualifiers/test), uncovered-type + mapping-rewrite warnings, dangerous-change on switch/envelope edit, display/audit/pending-changes. Flag read from config.ts featureFlags, unset everywhere (no iac). Client regenerated from committed config-service openapi. Evidence branch hjf/fuse-1253-edi-egress-evidence — delete after merge.

PR: gfs-bifrost/fuse-ui#275

## 2026-09-24 — FUSE-1240

Restore Transaction History search in prod after a parked-run rollback

3f39fbf (the search stack) reached prod at 17:34Z on 09-23. Three minutes later another session approved FUSE-1220's older parked Deploy run 746c6af, and revision 00053 rolled prod back to before #272 (no search box) until 09:10Z on 09-24. Restored by approving main's ae14bc5 (746c6af + #272 + rules-engine 2.1.1 + ui-toolkit 1.35.3), after cancelling the 6 parked runs from 09-23/24. 22 older ones (09-04 → 09-22) were still parked afterwards; `gh run list --status waiting` under-reported them, so list with --limit 200 and filter on status. Gotchas: approving any older parked Deploy run rolls prod back, so cancel them when a newer release goes out and re-check the live revision minutes after approving; two Deploy runs created seconds apart race on the prod tfstate lock (412), and a parked run's failed plan job can't be re-run, so cancel and re-run the whole run.

PR: gfs-bifrost/fuse-ui#272

## 2026-09-23 — FUSE-1240

Search Transaction History by the reference a customer quotes

One box searches every record type (all 12) for a value equal to its Record ID, correlation id, reference, customer order or SO number, via collector's ?reference= (FUSE-1239). Three-PR stack: searchTransactionChunks server function (one parallel fan-out on the server, because Next serialises browser-invoked server functions; validates targets + reference with zero GETs when invalid; fails closed on a page with no correlationId, i.e. a collector ignoring the param) -> search form + results line (inline error derived from the rejected value so Back clears it) -> view wiring (?search= pushed to history, drops record; popstate re-reads; drawer lookup spans search + browse and doesn't report missing while settling; Refresh re-runs the search). Verified locally vs dev: 53/53 values across 12 types match collector per-type totals; 2,194-match correlation id paged 300 rows, 0 repeats. Gotcha: correlation-id search matches the latest ingest's id (collector overwrites on re-ingest). jest needs virtual mocks for ui-toolkit subpaths. Shipped on Harry's call ~1h into the plan's 24-48h collector soak. [[FUSE-1240-multi-field-reference-search-in-transaction-hist]]

PR: gfs-bifrost/fuse-ui#270, gfs-bifrost/fuse-ui#271, gfs-bifrost/fuse-ui#272

## 2026-09-23 — FUSE-1220

Edit mapping dictionaries and use lookup() in the mapping editor, behind a flag

Adds dictionaries to fuse-ui's mapping editor as a 3-PR stack, all gated by a new FEATURE_FLAG_MAPPING_DICTIONARIES server env var. The flag is off unless 'true', and it's set nowhere, so dev and prod are unchanged. First PR: regenerated config-service client, dictionaries carried through both editor stores, and dry-run resolving lookup() against the mapping's dictionaries. Second: a Dictionaries tab with an editor dialog (entries table, paste-in, case-insensitive toggle) validated with the shared MappingDictionariesSchema; with the flag off, existing dictionaries round-trip untouched through save. Third: lookup() in the expression builder, with a dictionary dropdown and an unknown-dictionary warning. Verified locally against real dev config-service with the flag on in the local process only.

PR: gfs-bifrost/fuse-ui#267
PR: gfs-bifrost/fuse-ui#268
PR: gfs-bifrost/fuse-ui#269

## 2026-09-23 — FUSE-809

Remove the business-level backend confirmations toggle

Backend form loses "Enable Confirmations" and the backend card its Confirmations row; the switch has done nothing since FUSE-1063. "Broadcast Confirmations" stays. Connector "Send confirmations" tooltip corrected: the poller now enforces it for every connector type and holds withheld confirmations on the OBQ rather than dropping them. Generated config-service client hand-edited to drop confirmations? (codegen source URL returned 401).

PR: gfs-bifrost/fuse-ui#260

## 2026-09-23 — FUSE-1240

Show every collector record type in Transaction History

Wraps in FUSE-1207 + work orders: RGA, work orders, pick/pack confirmations, WOC and FGR get TRANSACTION_ENTITIES entries, v1 fetchers and page seeding; refPaths use only collector-declared search paths so any Record ID shown is searchable; a type collector doesn't serve yet degrades to the existing failed-types note. Needs collector#110 in prod before release. Evidence: row counts = collector v1 totals for all six on GADG.

PR: gfs-bifrost/fuse-ui#265

## 2026-09-23 — FUSE-1240

Add the Transaction History reference-search hook

useReferenceSearch caches per (value, record type), fetches only missing in-scope types, pages/retries/refreshes per type, drops overtaken responses; takes its fetcher as an argument so it landed before the collector #108 regen.

PR: gfs-bifrost/fuse-ui#264

## 2026-09-23 — FUSE-1240

Add Transaction History search outcome and status states

searchOutcome classifies a multi-type search (loading / all failed / no matches / hidden by filters / results with per-type failures) and a status component renders each (on the page since gfs-bifrost/fuse-ui#272). Search types live in logic/transaction-history-search.logic.ts.

PR: gfs-bifrost/fuse-ui#263

## 2026-09-23 — FUSE-1240

Keep correlation id out of the Transaction History payload panel

PR 1 of the UI reference search: toDisplayRow lifts collector's new top-level correlationId off the record onto the row (drawer row only when present) so it never lands in the Canonical Payload panel/download — must reach prod before collector FUSE-1239 PR B. Also extracts toVisibleRows/findSelected into logic/transaction-history-rows.logic.ts, behaviour-neutral (characterisation spec first). Plan: [[FUSE-1240-multi-field-reference-search-in-transaction-hist]].

PR: gfs-bifrost/fuse-ui#262

## 2026-09-23 — FUSE-1238

Transaction History: ingest time, lifecycle status, status filters

Transaction History moves off collector's legacy per-use-case routes (which strip lifecycle) onto api/v1/records. It gains Status and Ingested columns, defaults to newest-ingested ordering, filters the range on ingest time, and turns the status chips into client-side filters. Rows and the drawer are keyed on the collector _id, because an order and its confirmation share a customer reference and the old ref-keyed lookup opened the wrong one.

PR: gfs-bifrost/fuse-ui#261

## 2026-09-11 — FUSE-1070

Mapping Template Library — storage, browse and CRUD

Built the foundation of the Mapping Template Library entirely inside fuse-ui: a third
Mongo collection (`template_collections`, sanctioned exception to the "never add a
Fuse platform collection here" rule — copy-on-apply keeps it from becoming a second
source of truth), a Templates nav area, browse/search, collection detail, and full
CRUD for both collections and per-use-case templates. Every default value on a
template carries a **pre-set / to-be-advised** mark (sidecar, not baked into the
`MappingConfig`), replacing the old literal `'TBA'` string convention that FUSE-1074
imports from. Both writes are audited (`template_collection` / `template` targets).

Eight stacked PRs (#220-227) + a dependency-audit fix (#228), all merged to `main`
2026-09-03/04. Landed as `main`/customer-facing (increment 1, the editor-decoupling
refactor) then library-only surface — see [[../architecture#bff-not-data-plane]] and
the new `## Guardrails` section for the load-bearing traps found along the way
(prop-sync effect clearing `hasPendingChanges`, the `configType` discriminator, the
`ENTITY_LABEL` total-Record scar, the two `calculateIsValid` copies staying deliberately
un-unified).

Two real defects were caught only by driving the UI, not by any test: the customer-side
Save gate counted rules only (a to-be-advised default would have left Save permanently
disabled — the exact case the feature exists for), and adding a use case persisted a
blank template that the new validity gate then rejected. Both fixed before merge.

Update 2026-09-11 (found at sign-off, well after this plan's last edit): FUSE-1074
already shipped too — fuse-ui#212 merged 2026-09-07, unblocking a 4-PR stack
(#229-235? verify exact range) that added an "Import ILG Standard" action, retired the
code-managed `getDefaultMappingConfig`/`default-translator-config.ts` path entirely,
and imports today's `'TBA'` defaults as to-be-advised marks. Neither shipped through a
Waypoint plan (`wp find` tracks nothing for FUSE-1073/1074) — this ledger entry is the
first record of it existing. FUSE-1073 (apply a template onto a real connector mapping)
still appears to be outstanding — not independently verified here.

Full detail, decisions and verification transcript: [[../plans/FUSE-1070-template-library-storage-browse-and-crud|the plan]].
## 2026-08-26 — FUSE-1138

Config and connector change audit trail

Added a config and connector change audit trail — 26 config-mutating server actions now write before/after snapshots to a new `audit_log` collection, browsable three ways: a customer-scoped global view (`/customer/{id}/changes`), an inline history card on each connector's own page (admin-only), and the existing platform-wide `/user-management/audit-log` page unified to span both user-management and config/connector changes with a new customer filter. Full before/after snapshots are stored, including secrets — masked at render, a deliberate design call. Added `AUDIT_LOG_RETENTION_DAYS` env var, set to 24855 days (~68 years, the largest whole-day value that fits MongoDB's 32-bit `expireAfterSeconds` TTL limit) as a "retain forever" placeholder pending real product input on the actual retention window (epic AC calls for 30 days). Fixed a test-determinism bug in `date-formatting.spec.ts` where assertions hardcoded UTC-relative expected values that only held on CI's UTC runners.

PR: gfs-bifrost/fuse-ui#216

## 2026-08-12 — FUSE-855

work_order ingress-mapping configurator

Added a `work_order` ingress-mapping configurator, riding the existing generic mapping editor (SFTP-only, matching purchase_order/master_data/return_goods_authorization — no customer sends a work order via Shopify). One new `useCaseRegistry` entry drives every derived list (friendly names, filter chips, dot colours, connector-type availability) automatically. Added a target-field fixture for the mapping editor's field picker with real `CanonicalWorkOrder` header/line paths; no required-field enforcement yet, matching the stock_adjustment/FGR/WOC precedent. Part of a 3-PR stack (pkg-node types → config-service → this).

PR: gfs-bifrost/fuse-ui#205

## 2026-08-04 — FUSE-1025

FGR + WOC egress mapping configurators

Made Finished Good Receipts and Work Order Confirmations configurable in the UI as outbound use cases on a connector, reusing the existing generic mapping editor route (no new page needed). Added canonical key lists derived from `CanonicalFinishedGoodReceipt`/`CanonicalWorkOrderConfirmation` so the editor can offer and label target fields, including the WOC `role` component-vs-finished-good discriminator. Refactored per-use-case metadata (friendly name, icon, colours, direction, confirmation-ness, connector availability) from seven separate exhaustive maps across four modules into a single registry entry per use case, with tests pinning every derived map for the existing ten use cases so the refactor is a verified no-op for them. No required mapping fields enforced yet for either new use case — that's a per-customer spec decision, not derivable from the canonical.

PR: gfs-bifrost/fuse-ui#188

## 2026-07-20 — FUSE-1000

Automatic per-PR preview environments for fuse-ui

Added per-PR Cloud Run preview environments for fuse-ui. New `is_preview_env` Terraform flag skips the load balancer, managed SSL cert, DNS record and dedicated Mongo Atlas cluster for a preview env, instead reusing dev's shared Mongo cluster isolated by a per-PR database name and Atlas user. Fixed two latent bugs found along the way: `root.hcl`'s state-bucket logic previously routed any env other than the literal string "dev" to the prod GCS bucket, and the Cloud Run service account was hardcoded to `fuse-ui-${var.env}` so every preview env would have collided on the same SA as real dev.

Added CI automation: a preview Cloud Run instance builds and deploys automatically on PR open/push (keyed `dev-pr-<n>`) and tears down on close/merge, with deploy/destroy sharing a concurrency group to avoid racing Terraform state, and a single upserted PR comment carrying the live preview URL. Added a nightly sweep workflow (Mon-Fri) as a safety net that finds and tears down orphaned `dev-pr-*` state whose PR has closed or gone quiet, guarded to never touch `dev/`/`prod/` state.

PR: gfs-bifrost/fuse-ui#171
PR: gfs-bifrost/fuse-ui#172
PR: gfs-bifrost/fuse-ui#173

## 2026-07-20 — FUSE-1050

Fix RGA confirmation mapping template + field-picker + validation

Companion fix to FUSE-1049 on the confirmation (egress) side. The default RGA confirmation template, its field-picker dictionary and its required-fields validation were all written against `GoodsInConfirmation`'s field shape, but RGA confirmations are actually built as `CanonicalReturnGoodsAuthorization`/`CanonicalRGALine` — a different, RGA-specific canonical with no `supplier.*`/`status.*` block and differently-nested shipping fields — so almost every mapping rule silently read nothing. Corrected the paths (customer reference, identifiers, shipping carrier/tracking, SKU, quality/variance/stock-status) and applied the same fix to GADG's live dev connector mapping, not just the template. Deliberately left Description/Batch/Expiry Date unfixed — `CanonicalRGALine` has no batch/expiry field and the confirmation handler doesn't populate description, which needs a canonical type extension, not a mapping correction.

PR: gfs-bifrost/fuse-ui#175

## 2026-07-20 — FUSE-1049

Fix RGA ingress mapping template + field-picker + validation

Fixed the "use standard template" default for a new RGA ingress connector — it wrote `supplier.reference`/`product.skuId` into a freshly-created connector's mapping, neither of which exist on `CanonicalReturnGoodsAuthorization`/`CanonicalRGALine`, and never mapped four required fields (`identifiers.id`, `identifiers.businessSkuId`, `identifiers.returnAuthorizationId`, `location.owner`) — so any connector built from the template failed canonical validation on every line. Removed the invalid paths from the field-picker dropdown and corrected the editor's required-fields validation to check the real paths. Dropped the unused `order.type: "R01"` template default (snap-adapter hardcodes `OrderType` to `S01` for RGA creates). Verified end-to-end against GADG's live dev connector — corrected CSV/JSONL files landed cleanly as real Snap receipts.

PR: gfs-bifrost/fuse-ui#174

## 2026-07-06 — FUSE-954

Drag-and-drop CSV column ordering for SFTP confirmations

Added a "Set column order" control to the confirmation mapping editor (SFTP connectors only) — a drag-to-reorder modal over the mapping's output columns, persisted via the existing mapping save (`columnOrder` rides on `updateConnectorMapping`). Follow-up restricted the control to confirmation use cases only (goods_in/goods_out/return_goods confirmations) and excluded default-value columns from reordering; baked a standard column order into the SFTP template's egress confirmation configs. Final PR regenerated the config-service client to carry `columnOrder` natively and dropped the temporary type intersection used as a stopgap.

Known caveat: the RGA confirmation mapping is keyed under `return_goods_confirmation` in the UI/template, but sftp-connector's egress reads RGA confirmations under `return_goods_authorization` — so goods-in/goods-out column ordering works end-to-end, but RGA ordering doesn't take effect on egress until that routing is reconciled.

PR: gfs-bifrost/fuse-ui#160
PR: gfs-bifrost/fuse-ui#161
PR: gfs-bifrost/fuse-ui#162

## 2026-06-30 — FUSE-952

Customers list rebuilt as a data table; one-time SFTP credential link

Rebuilt the Customers page as a sortable data table (replacing the card grid) showing each customer's connectors, use-cases and integration status, with a URL-driven filter bar (search, connector-type, use-case, status) and a bulk `GET /api/v1/connectors` join to avoid N+1 lookups.

Added a "Credential Link" button on the SFTP connector config header — generates a single-use, 24h one-time link (via the ILG one-time-secrets service) bundling the connector's connection details and credentials, minted server-side so credential material never round-trips through the browser. Prod-only (OTS has no dev instance).

PR: gfs-bifrost/fuse-ui#149
PR: gfs-bifrost/fuse-ui#150

## 2026-06-18 — FUSE-967

Transaction History MVP (customer-scoped canonical record browser)

New per-customer Transaction History page under the customer admin blade — a tabbed, read-only browser of the canonical records the Collector holds (Goods In/Out, their confirmations, Master Data, Stock Adjustments). Added a record-level detail drawer showing the canonical payload (copy + download); the raw-as-received payload renders as a "not captured" placeholder pending future raw-capture work. Record ID resolves to the customer's own business reference (e.g. PO `businessOrderNumber`), not the internal WMS id. Lifecycle status is a deferred "Unknown" placeholder — the Collector exposes no platform status yet. Regenerated the Collector OpenAPI client (stale ~5 months) to pick up the stock-adjustment and confirmation DTOs. Deliberately an MVP: omits connector, direction, correlation tracing, raw payload, and time/status filters, pending Collector backend work.

PR: gfs-bifrost/fuse-ui#137

## 2026-06-12 — FUSE-809

Restore the backend confirmations toggle (FUSE-809 revert)

Reverted the UI side of FUSE-809 after config-service re-exposed the backend `confirmations` flag and made it required on create again — the UI's backend create was failing with a 400 (`confirmations: expected boolean, received undefined`). Restored the "Enable Confirmations" toggle on the backend config form (create + update) and the Confirmations row in display mode; hand-patched the generated config-service client types to re-add the `confirmations` fields since regenerating from the live spec would have dropped newer unserved fields. All restored sites marked `HOTFIX(FUSE-809 revert)` pending a per-connector confirmation toggle.

PR: gfs-bifrost/fuse-ui#132

## 2026-06-11 — FUSE-953

Replace VPC connector + NAT with Direct VPC egress

Deleted the Cloud Router, NAT gateway and VPC connector from fuse-ui's Terraform — fixed-cost resources billed 24/7 that fuse-ui's Cloud Run service was never actually attached to (no `vpc_access` block existed in the IaC), so removal was deletion-only with no cutover window. VPC and subnet were kept. Fleet-wide rollout of the FUSE-953 network lever, pattern piloted on dedupe-service.

PR: gfs-bifrost/fuse-ui#129

## 2026-06-03 — FUSE-672

Display and toggle SFTP connector egress filetype

Last PR in the FUSE-725 stack (pkg-node → config-service → sftp-connector → fuse-ui) adding CSV/JSONL egress filetype support to SFTP connectors. Regenerated the config-service client for the new `SFTPIngress.egressFiletype` field (required, csv|jsonl); SFTP connector create now sends `egressFiletype: 'csv'` to satisfy the new required field. Added an "Outbound File Format" select (CSV | JSON Lines) to the connector edit surfaces, and a read-view chip showing the current format.

PR: gfs-bifrost/fuse-ui#127

## 2026-01-30 — FUSE-713

Purchase Order mapping copy fix

Updated purchase order mapping copy.

PR: gfs-bifrost/fuse-ui#72

## 2026-01-27 — FUSE-120

Remove duplicate check for shipment method snap codes

Removed the duplicate check for shipment method snap codes — these aren't guaranteed unique across configs.

PR: gfs-bifrost/fuse-ui#66

