---
ticket: none
title: Move the connector onto the shared remote-config package
service: sftp-connector
status: active
created: '2026-11-04'
updated: '2026-11-05'
repo: /home/harry/code/fuse/sftp-connector
worktree: /home/harry/code/fuse/.worktrees/sftp-connector-remote-config
branch: hjf/sftp-connector-remote-config
base: origin/master
base_sha: c223aeb24
pr: gfs-bifrost/sftp-connector#399
tags:
- waypoint
- plan
impl_model: opus
impl_effort: medium
---
# none — Move the connector onto the shared remote-config package

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

- **2026-11-06 (inc 3b build)** — Changes from the plan as written:
  - **Mapping revisions evict, they don't cache the payload.** `handle()` has no version check, so an out-of-order or redelivered revision would re-cache an older mapping. The old path only deleted.
  - **Confirmations read by connectorId,** not by username.
  - **Only a schema failure on `/mappings/` reads as "no mapping".** A connector-level schema failure is rethrown.
  - **No package mapping-schema override.** The "duplicate dictionary names still resolve" spec became "… read as no mapping", because the gate's sweeps found no duplicates.
  - **A failed cache write still acks.** This is parity: `SaveFailure` is a `ConfigApiException`, which is acked with a 202.

- **2026-11-05 (Harry)** — Inc 1 to prod now ("merge it up + deploy"), waiving its Cloud SQL E3 soak gate. The shadow adds one config-service read per connector backlink, and the sweep is on-demand. Shipped with #397 (golden image) and #396 (Renovate), which were already on master.
## Intent
<!-- What we are changing and why. Link the ticket. -->
Out-of-ticket; Harry asked for it on 2026-11-04, after prod cut S4 moved SFTP user provisioning to the host ([[sftp-host-c-prod-cutover-and-vm-decommission|Plan C]]). `apps/connector` still has its own hand-rolled config-service layer (`apps/connector/src/config/`, about 1,360 lines). It should read config through the shared `@gfs-bifrost/remote-config` package that shopify-connector and fapi use, so fixes to the package reach sftp-connector. **The package is not a drop-in replacement.** Its strict connector schema, its O(N) username and business lookups, and its error classes would each change what customers see. So the work is a pkg-node release first (its own plan), then an adapter behind the connector's existing interfaces, one config surface at a time. Done means: in dev and prod, files ingest and confirmations egress as before, config edits still invalidate the cache, and only a thin adapter remains in `src/config/`.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [ ] 1. Every config-service read in `apps/connector` goes through `@gfs-bifrost/remote-config`. `src/config/` holds only the adapter, `GetConnectorDto`/`SftpIngressConfigSchema`, the rules transform and the raw use-case reader.
- [ ] 2. Ack/nack outcomes don't change for `config_revision` or file events: `ConfigApiException` → 202, `ConnectorConfigException` → 500, `ValidationException`/`MappingRulesException` → 204, any other error → 500 (`errors.ts:51-64,184-254`). The package's own exception classes are translated, never left to fall through.
- [ ] 3. A connector that the in-repo schema accepts today still resolves. That includes one with an enabled use case that has no `config` yet, a `null` (deleted) use case, or a malformed `ediEnvelope` (dropped, not fatal). A sweep over every SFTP connector in dev and prod shows 0 resolve failures.
- [ ] 4. A new PENDING SFTP connector publishes `create_sftp_user` **before** any cache refresh. A refresh or validation failure can't stop that publish (`connector.config-handler.ts:36-39`). In dev it goes PENDING → ACTIVE through the host.
- [ ] 5. During confirmation and stock-adjustment fan-out, a connector the package can't resolve gets a retryable failed leg carrying its `connectorId`. It is never silently skipped (the Poller Clear-Down E8 lesson).
- [ ] 6. In dev, a config edit takes effect without a deploy: connector, mapping (RGA included), DDP and routing. A deleted connector's revision is acked, and a renamed username stops resolving.
- [ ] 7. A brief config-service failure on a cold cache doesn't send a file to `error/`: a 503 followed by a 200 still ingests, because retries are kept. Config-service request rate from sftp-connector in prod stays at or below its 7-day pre-migration baseline.
- [ ] 8. Every Datadog monitor, dashboard and log-based metric that reads the connector's config events still has data. The package's per-hit cache logs are not emitted at `info`.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `apps/connector/src/config/` (replaced by an adapter); `src/factory.ts:72-145,315-349,369-422,525-594`; `src/app.ts:33-57`; `src/controllers/debug.controller.ts:51-80` (builds its own handlers).
- `src/controllers/pubsub.controller.ts:130-170`: the `POST /events/v1/config/revision` push. The endpoint and its subscription (`iac/projects/bifrost-sftp-connector/pubsub.tf:611-640`, `ack_deadline_seconds = 20`) stay; the handler calls the package's `processRevision`.
- `src/errors.ts`: ack/nack mapping (AC 2).
- Consumers: `gcs/storage.service.ts:396`; `pubsub.controller.ts:479`; `confirmations/confirmation-egress.service.ts:559,644,668,779`; `confirmations/stock-sync.service.ts:177,205,244`; `confirmations/stock-adjustment.service.ts:88,210,355`; the five rule managers; `rules/rule-manager/schema.ts:2`; `shared/helpers/config-helpers.ts`; `confirmations.service.ts:25`.
- Redis (Memorystore): the package adds an `rc:` prefixed client next to the in-repo `cfg` one, which `FileRoutingService` keeps.
- Shared package `@gfs-bifrost/remote-config` (gfs-bifrost/pkg-node `pkg/remote-config`, 2.5.1): a minor release is needed (gate on inc 3). Fuse MCP data: `services.json`/`dependencies` for sftp-connector gain the package at sign-off.
- [[edifact-confirmation-egress]]: `ediEnvelope` leniency (a bad envelope must not stop inbound files).

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- The package's connector schema is strict where the in-repo one isn't. `ConnectorUseCaseDTOSchema` requires `status`/`friendlyName`/`config`, and dictionary names must be unique. In-repo `GetConnectorDtoSchema` (`src/config/schema.ts:65-85`) checks only `useCase`, and `:13-42` drops a bad envelope instead of failing. Established by reading the source (planning agent plus grounding review).
- **The strictness reaches mapping reads as well as connector lookups.** `ConnectorMappingHandler.resolve` calls the strict `getConnector` before `getConnectorMapping` (pkg `connector-mapping.handler.ts:45-50`). So inc 3 needs the lenient schema too. Source read (grounding review).
- On a cold cache, `resolveByUsername` pages every SFTP summary and GETs each one, with no try/catch (pkg `connector.handler.ts:152-171`). One strict-invalid connector earlier in the list therefore breaks lookups for every username after it. In-repo makes 3 calls using `?userName=` (`config.api.ts:692-723`, `connector.config-handler.ts:250-262`). `resolve(businessId)` also pages every connector of the type (pkg `:370-372`). Source read.
- The package's `ConfigEventDispatcher.processRevision` runs a revision's items one after another with no catch, so the first throw skips the rest. Its connector backlink refreshes one connector, never shrinks its indices, and throws on a delete (`version -1` → 404). Cached connector reads aren't revalidated (`:444`). Source read.
- The package's `ConfigApiClient` is bare axios, with no retry, circuit breaker, `x-request-id` or user agent (`config-api.client.ts:39-44`, compare `factory.ts:72-128` and `config.api.ts:133-153`). Its memory TTL is fixed at 60 s (README :135); IaC sets `MEM_CACHE_TTL=30000` (`cloud-run.tf:136-140`). Source read.
- The package's network `ttl` has been in ms since 2.5.0 (pkg-node `CLAUDE.md`: default 3,600,000 ms; before that it was an accidental 3.6 s). Pass `NETWORK_CACHE_TTL` (600000) straight through. Don't copy fapi's `Math.floor(ttl/1000)` (fapi `remote-config-provider.service.ts:50`), which only works because fapi's input is a larger number. Inc 1's factory spec pins the unit. Source read plus pkg-node docs.
- `createCustomer` (`pubsub.controller.ts:680+`) is dead in dev and prod since S4: both tfvars have `create_sftp_user_consumer = "host"`. But a rollback-S4 still needs it, so it stays on the old layer until Plan C inc 5 deletes it. The PENDING → `create_sftp_user` publish is **not** provisioning and is ported (inc 4). `SFTPUserBuilderException` stays (with `ConnectorReadFailure` and `UserCreation`), because that publish throws it. Plan C inc 5 drops only the `UserProvision` kind. Source read plus Plan C.
- No Express consumer of the package exists: shopify-connector and fapi are Nest, and snap-adapter has its own `RemoteConfigProvider`. The Nest wrappers are a pattern only. Org-wide code search.
- Confirmation and stock mapping reads (`confirmation-egress.service.ts:779`, `stock-sync.service.ts:244`, `stock-adjustment.service.ts:355`) move from live GETs to cached-and-invalidated, like ingest. Harry, 2026-11-05: "cache is fine". The live reads were a gap, not a deliberate contract choice. With inc 3's per-item dispatch, a failed invalidation nacks and is retried instead of being lost.

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

- [x] 1. Wire the provider, dispatch in shadow, and sweep every connector (AC 3,8). — dev only: sweep 73/73, shadow clean on a connector and a mapping revision; prod sweep and merge wait on the E3 gate — done: f6f1a0e
      gate: Config Service Cloud SQL E3 soak signed off before inc 1 reaches prod (E3 checks a cache-miss read from sftp-connector on the old path; due about 2026-11-10). Dev can go first.
            [ ] confirmed

      - Add `@gfs-bifrost/remote-config` 2.5.1. `buildRemoteConfigProvider()` in `factory.ts`: `mode: "full"`, Redis from `NETWORK_CACHE_*`, `memCapacity` from `MEM_CACHE_CAPACITY`, `ttl` = `NETWORK_CACHE_TTL` in ms. Init with a bounded race, copying shopify's `remote-config-init.ts` (the INC-40 lesson). The logger shim demotes `info` to `debug`.
      - Shadow: `configurationEventHandler` runs the old path first, unchanged. Then it runs `processRevision` per item under a 5 s timeout (the push ack deadline is 20 s; FUSE-1078 was a redelivery loop) inside a log-only catch, emitting `remote_config.shadow_dispatch_failed{connectorId,fragment,cause}`.
      - Sweep: `GET /debug/remote-config/sweep` (behind `/debug`'s existing `run.invoker` restriction, G4). It calls `resolveByConnectorId` for every SFTP connector and returns failures grouped by cause. Run in dev and prod and record the 2.5.1 baseline in Evidence.
      — verify: `pubsub.controller.spec` "dispatches each revision item to remote-config", "a remote-config failure or timeout does not change the status code"; `factory.spec` "builds the provider with the TTL in ms"; a dev mapping edit logs a shadow dispatch with no failure; the sweep runs in dev and prod.

- [x] 2. DDP rules and warehouse routing through the package (AC 1,2,6). — prod 00127: real STUBBLE/EPARFUM files archived with sites and dutyPaid matching the old revision; dev live routing change applied without deploy — done: b4195b0
      - `RemoteConfigFragmentAdapter` implements `IFragmentConfig<DDPRule[]>`/`<RoutingRule[]>`, wired into `buildRuleManagers` and `DebugController`.
      - A config-service failure → `[]` and a logged `FetchFailed`, as today. That `[]` is no longer cached, which is a deliberate fix. Provider not ready → throw (nack), not `[]`.
      - Dispatch for DDP and routing fragments now propagates errors per item: a failed invalidation nacks. `deriveFragmentKey` makes those cases no-ops instead of throws.
      - Delete `config-handlers/ddp-rules/`, `config-handlers/warehouse-routing/`, `getDdpRulesForBusiness` and `getWarehouseRoutingRules`.
      — verify: adapter spec "returns rules", "[] on config-service failure, not cached", "[] on schema failure", "provider not ready nacks", "a failed DDP invalidation nacks"; the `sales-order.rule-manager` specs stay green; dev: change a routing rule, and the next sales-order file routes by it.

- [x] 3. Mapping rules for ingest, confirmations and stock through the package (AC 1,2,3,6,7). — prod 00129: sweep 30/30 + 113/113 mappings; real STUBBLE/EPARFUM files archived and WILDSMITH/STUBBLE confirmations processed through the package's mapping reads — done: e17c9ca
      gate: `@gfs-bifrost/remote-config` 2.6.0 published ([[remote-config-2-6-2-7-opt-in-connector-handling-|pkg-node plan]], stack A), with `withConnectorSchema` applied to mapping resolves; the sweep on 2.6.0 with sftp's schema shows 0 failures in dev and prod
            > 2026-11-05: 2.6.0 published (pkg-node#299/#300, `91fba57`). The sweep on 2.6.0 with sftp's schema is still owed, in dev and in prod.
            > 2026-11-06: dev half met: on #401 `9851537` the sweep resolved 73/73 connectors and 201/201 mappings with sftp's schema. The prod sweep is owed after #401 merges. The sweep now covers mappings, because 2.6.0's mapping read is strict on duplicate dictionary names and keys, which `withConnectorSchema` doesn't reach.
            > 2026-11-06: prod met: on `b4195b0` (revision `00127-2hm`) the sweep resolved 30/30 connectors and 113/113 mappings, 0 failed. No prod mapping trips the strict mapping schema, so 3b needs no package mapping-schema override today.
            [x] confirmed

      - Bump to 2.6.0. Add `'@gfs-bifrost/remote-config@2.6.0'` to `pnpm-workspace.yaml`'s release-age exclusions. Set `memTtl: MEM_CACHE_TTL` (30 s) and `requestHeaders` for `x-request-id`.
      - The sftp connector schema passed to `withConnectorSchema` models the **flat** wire use case `{useCase, status, friendlyName, config?}`, `null` allowed. The current nested `{useCase, mapping?}` `GetConnectorDtoSchema` (`schema.ts:44-58`) would strip every use case through the package. It keeps the `ediEnvelope` preprocess.
      - Adapter: username → connectorId (still through the old connector config at this stage), then `handler(CONNECTOR_MAPPING).resolve`, then the in-repo `transformConfigRulesFromMappingResponse`.
      - Errors: a 404 cause → `MappingRulesException` for ingest, and `null` for the `getUserMappingRulesByUseCase` callers. 5xx and network errors are rethrown. Package calls are wrapped in the existing cockatiel policy (`handleWhen(transient)`).
      - Mapping dispatch propagates errors per item. The RGA invalidation gap is fixed (`bifrost.config.service.ts:26-31`).
      - Confirmation and stock mapping reads become cached, like ingest (decision 2026-11-05).
      - Delete `MappingRulesConfigHandler`, `invalidateMappingRulesCache` and `getUserMappingRulesByUseCase`. `getConnectorUseCaseMapping` stays as a thin raw reader, because `hasConfig: false` can't be represented through the package.
      — verify: mapping adapter spec (memory-mode provider plus nock) "a CONNECTOR_MAPPING revision then a read refetches", "RGA is invalidated", "duplicate dictionary names still resolve", "404 → MappingRulesException", "503 then 200 resolves", "503 ×3 rethrows"; confirmation-egress, stock-sync and stock-adjustment specs stay green; dev: edit a PO column mapping and ingest a PO with the new mapping; egress one confirmation of each type.

- [ ] 4. Connector lookups and backlinks through the package; the old layer stays in the tree, unused (AC 1,2,4,5,6,7).
      > 2026-11-05: the Plan C inc 5 part is met (sftp-connector#398, `6a4956c`, in prod 15:09Z; Harry waived its 2-week gate). The 2.7.0 and 7-day-shadow parts are still open, so the box stays unticked.
      gate: Plan C inc 5 merged and in prod (no earlier than 2026-11-18); remote-config 2.7.0 published (pkg-node plan stack B, including its dev proof of the username lookup); 7 days of prod shadow with 0 `shadow_dispatch_failed` and a prod sweep with 0 failures
            [ ] confirmed

      - Bump to 2.7.0 and opt in: `withConnectorHandling({ lookup: "server-filtered", evictOnDelete: true, backlinkTypes: [ConnectorType.SFTP] })`. Revisions go through `processRevisionSettled`, and `ConfigRevisionDispatchException.fromResult` throws for a nack. Outcomes are logged through `serialiseError`.
      - Business lookups (`resolve`/`resolveWithUnresolved`) stay on the package's scan. The business-route lookup is pkg-node inc 7 and is not a dependency here.
      - `RemoteConfigConnectorAdapter` implements `IBacklinkConfig<GetConnectorDto[]>`.
        - An empty `getConfig` → `ConnectorConfigException` plus the metric.
        - A username lookup checks equality.
        - Package calls are wrapped in cockatiel.
        - `ERROR_METRIC.CONFIG_API` is re-emitted.
        - Business IDs are uppercased at the adapter.
      - Backlink order:
        1. Parse the connector leniently, and if it is PENDING publish `create_sftp_user` (throwing `SFTPUserBuilderException` → 500 on failure).
        2. Then `processRevision`.
        3. A `-1` delete acks.
        4. A non-SFTP connector acks (the package's `backlinkTypes`), and an unparseable one acks and logs, as `config.api.ts:663-669` does today. This keeps sftp-connector out of the "bump every consumer before a new type" list (EDI Support, Delivery Backends R1).
      - `selectTargets` (`confirmation-egress.service.ts:559`) and `stock-adjustment.service.ts:88` use `resolveWithUnresolved`. Each unresolved connector gets a retryable failed leg with its `connectorId`.
      - Double dispatch ends: the old connector handler is no longer called.
      — verify: adapter spec with one case per inventory row, plus "PENDING publishes before refresh", "a refresh failure still publishes", "deletion acks", "a non-SFTP connector acks", "a renamed username stops resolving", "an unresolved connector gets a failed leg", "503 then 200 on resolveByUsername ingests"; dev from a cold cache: one file per use case ingests; confirmations, a stock adjustment and a stock sync egress; a new PENDING connector goes ACTIVE through the host; deleting a connector is acked; a connector edit invalidates.

- [ ] 5. Delete the old layer and prune its observability (AC 1,8).
      gate: 7 days in prod after inc 4 with no new 5xx or DLT on the `config_revision` subscription, no rise in files routed to `error/`, and config-service request rate at or below baseline (AC 7); every `ConfigCacheEvent` name searched in Datadog monitors, dashboards and log-based metrics, and each one with hits retargeted first
            [ ] confirmed

      - Delete `bifrost.config.service.ts`, `config.api.ts`, `config-handlers/connector/`, `constants.ts`, the unused types, fixtures and specs, and the shadow code and sweep endpoint.
      - Keep `CustomerEventCreationFailed`, which the PENDING publish emits (`connector.config-handler.ts:467`).
      - Keep the config-API cockatiel builder only as the adapter's retry policy.
      — verify: `pnpm test`, `lint:fix` and `build:check` green with `knip` showing no unused exports in `src/config`; after the dev deploy, every monitor found by the gate's search still evaluates with data for 24 h; one file per use case still ingests in dev.

**Separate plan, gate for inc 3 and inc 4:** [[remote-config-2-6-2-7-opt-in-connector-handling-|pkg-node: remote-config 2.6/2.7]]. Every item is opt-in, so fapi (`^2.5.1`) and shopify are unaffected.
- **2.5.2** fixes FUSE-1350 (a business's cached connector list built from one connector) by default.
- **2.6.0** (`memTtl`, `requestHeaders`, `withConnectorSchema`) gates inc 3.
- **2.7.0** (`evictOnDelete`, `backlinkTypes`, server-filtered `resolveByUsername`, `processRevisionSettled`) gates inc 4.
- A business-route `resolve` is that plan's inc 7; this plan doesn't wait for it.

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
- **2026-11-05: inc 1 in prod** (sftp-connector#399 `1089b9a`, deployed in `ca658a7` with #396/#400 at 16:30Z, revision `sftp-connector-prod-cr-00126-cbj`; Harry waived the E3 gate).
  - **Review fixes before merge** (backend/security/tests panel): the ack no longer waits for the shadow, `dispatch` never rejects, a failed init disposes its provider, a single in-flight sweep, endpoint-pattern grouping, and errors reported by name only.
  - **Dev re-verified:** the ack at 15:45:42Z came before the shadow finished at 15:45:43Z; sweep 73/73.
  - **Prod:** remote-config initialised, 29 acks all 204, no warnings or errors on the revision, logs in Datadog via the in-container agent.
  - **Prod sweep baseline:** 30/30 resolved, 0 failed, in 253 ms. config-service's own `?type=sftp` total is also 30.
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-11-05 [inc 1] Dev, branch `f6f1a0e` (sftp-connector#399), on remote-config 2.5.2.
  - `GET /debug/remote-config/sweep` resolved 73/73 SFTP connectors, 0 failures, in 0.6 s; config-service's own `?type=sftp` total is also 73. This is the 2.5.2 dev baseline. **The prod baseline is owed**, after the E3 gate.
  - Shadow on real revisions: a CONNECTOR backlink (HJF test connector rename) gave 1 item, 0 failed, 30 ms; a `CONNECTOR_MAPPING` fragment (a mapping POSTed onto the HJF test connector) gave 1 item, 0 failed, 5 ms. No error logs on the revision.
  - Suite 913/913. The specs the plan named pass: per-item dispatch, failure/timeout keeps the status, and TTL in ms. Dev was put back on master `fd66dfb` afterwards.

- 2026-11-06 [inc 3a] Dev, sftp-connector#401 `9851537` (revision `00913-slw`), on remote-config 2.6.0 with `RemoteConfigConnectorSchema`.
  - `GET /debug/remote-config/sweep`: 73/73 connectors and 201/201 mappings resolved, 0 failed, in 3.2 s. A local read-only run before the deploy matched.
  - The revision's logs show no warnings or errors. The package's per-request lines are at `debug` (AC 8).
  - Review-panel caught that an SFTP-only schema would fail every Shopify or REST connector backlink, since `config_revision` is unfiltered. Fixed with a union that sends non-SFTP connectors through the package's own schema.
- 2026-11-06 [inc 2] Dev, stack #401 + #402 `3cec982` (revision `00914-722`). Files went into the dev bucket under DAZZA `FUSE_2ACED20A9B` (no Snap backend in dev, so records fail downstream and files go to `error/`, as on 10-20).
  - Rules were read through the package: its "Resolving DDP rules / warehouse routing from config API" lines appear. A second file within the TTL made no fetch.
  - Routing: FI → `42069`, AT → `00090`, and GB matched no rule so kept the mapping default `0006`.
  - DDP: AD with Class A came out duty-paid; the Class B control did not. The FI rule's class and effective-date conditions correctly kept a classless order unpaid.
  - Live change (AC 6): a PUT adding AD to DAZZA's `0010` rule was acked 200 on `config/revision`, and the package saved `warehouse_routing:DAZZA`; the shadow skipped the item. The next AD order routed to `0010` without a redeploy. DAZZA's rules were then restored and diffed equal, and the restore was applied the same way.
  - No warnings or errors from the change. The `MappingRulesException` came from the debug translate route's hard-coded `sftp_user`, which has no dev connector (pre-existing).
- 2026-11-06 [inc 2 + 3a] Prod, stack merged as `fb482fd` (#401) and `b4195b0` (#402); Deploy run 42231060718. The prod plan was the image plus the standing sensitive-env reorder (0/1/0). Both gates were approved, and prod is live on `b4195b0`, revision `00127-2hm`.
  - Prod sweep with sftp's schema: 30/30 connectors and 113/113 mappings, 0 failed, 1.4 s.
  - First real batch on the new revision (14:20Z): 5 sales-order files (STUBBLE, EPARFUM) archived. Sites (all `0010`) and the STUBBLE duty-paid mix match the old revision `00126` for the same businesses. No warnings or errors; 12 file events 200 and 78 acks 204.

- 2026-11-06 [inc 3b] Dev, sftp-connector#404 `3f6d833` (revision `00916-74p`).
  - **Ingest, live edit (AC 6):** DAZZA's sales-order `order.customerRef` was repointed to `Addresses_Postcode`. The revision was applied as an eviction (14 use cases evicted, shadow 0 items, `config/revision` 200), and the next file logged reference `AD500`. After the restore, the next file logged `RC403D154340`, and the restored mapping deep-equals the original. The first file after each revision refetched from config-service inside the cache TTL.
  - **Egress (AC 1):** GADG pick, RGA and stock-adjustment confirmations, sent through the fuse-mocker API as broadcasts, each read their mapping through the package. Each wrote files with the mapped columns.
  - **Sweep:** 73/73 connectors and 201/201 mappings. No errors on the revision.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- [inc 1] The prod sweep and prod shadow: both wait on the E3 gate and the merge.
- [inc 1] Shadow on a connector delete (`version -1`): expected to fail, because the package's refresh 404s. That's pkg-node 2.7.0's `evictOnDelete`.

## Rollout & rollback
<!-- Added on demand. Written at plan time; amend in place as it changes.
     `Shared state touched:` is the single home for the five classes git does not own — a dev
     deploy, a prod config write, a Datadog monitor, a CI var or secret, cross-repo IaC. Reverting
     the branch undoes none of them, so if they are not written here they are not written down. -->

- **Order:** 1 → 2 → (pkg-node 2.6.0) → 3 → (Plan C inc 5 in prod) → 4 → 5.
  - **Separate prod deploys:** each increment gets its own prod deploy. Approving a prod gate ships all of master (Plan C), so none of these may ride on the one-way inc 5 deploy, and inc 5 must not ride on one of these.
  - **Inc 4 before Plan C inc 5:** this would port the PENDING publish while `createCustomer` still reads through the old layer. It works, but it changes the rollback-S4 path during the rollback window, so don't.
- **Flags/config:** none. Every env var used already exists (`NETWORK_CACHE_*`, `MEM_CACHE_*`, `CONFIG_SERVICE_*`). No IaC change.
- **One-way doors:** none in this plan. Inc 5 deletes code, which a revert restores. The only one-way door nearby is Plan C inc 5's.
- **Rollback:** a git revert per increment, then a deploy. The two Redis prefixes (`cfg`, `rc:`) never collide, and old keys age out within the 600 s TTL, so no cache flush is needed in either direction.
- **Shared state touched:**
  - **Dev and prod deploys** of sftp-connector per increment.
  - **Config writes:** dev config-service edits for the verify steps. One test connector in dev for inc 4, on HJF, left in place like the cut's.
  - **Datadog:** monitors are retargeted in inc 5 only if the gate's search finds hits.
  - **pkg-node:** a 2.6.0 publish (its own plan).
  - **(none)** for prod config writes, CI vars and IaC.
- **Proof in prod:**
  - Baseline taken before inc 1: the `config_revision` push 2xx/5xx rate, files routed to `error/` per day, config-service request rate from sftp-connector over 7 days.
  - After inc 4: those three at or below baseline, 0 `shadow_dispatch_failed`, and the next real prod connector going ACTIVE.

## Options considered
<!-- Added on demand. Why this approach and not the others — the thing the planning agent is
     asked for and the plan has otherwise had nowhere to put. Promote to a durable record with
     `wp decide --record` when it is worth defending in a review six months out. -->

- **Chosen — an adapter behind the existing interfaces, one surface at a time, with shadow dispatch until inc 4.**
  - The confirmation and stock services (`confirmation-egress.service.ts` alone is 950 lines) branch on precise error classes and `null`s, and their specs encode that.
  - The adapter is the one place errors get translated.
  - Shadow dispatch measures the package against real config before anything depends on it.
- **Chosen — fix the gaps in pkg-node, not work around them here.**
  - Strictness (gap 1) has no clean workaround in this repo, because the package validates before it returns anything.
  - The O(N) lookups are load problems that fapi and shopify share.
- **Rejected — rewrite the call sites onto the package API directly.** It spreads error translation across six services and rewrites their specs, with no gain.
- **Rejected — big-bang swap.** Gaps 1 and 4 would hit every SFTP customer at once.
- **Rejected — exact parity with latent bugs.** Three changes are deliberate and each is called out in its PR:
  - caching `[]` after a DDP or routing fetch failure;
  - the missing RGA invalidation;
  - one bad connector failing a whole business lookup. It becomes a recorded, retryable failed leg, not a silent drop.
- **Option, out of scope:** move `FEATURE_FLAG_EDI` and `FEATURE_FLAG_USE_DYNAMIC_CONFIRMATION_MAPPING` from env vars to the package's `FeatureFlagReader`.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-11-06** — Inc 3 ships as two PRs (Harry agreed). **3a** is behaviour-neutral: the 2.6.0 bump, `memTtl`, `requestHeaders` and sftp's flat connector schema, with the shadow and sweep switched to that schema and nothing reading through the package. Its dev and prod sweep clears inc 3's gate. **3b** is the mapping switch-over itself. Why: the gate's sweep needs 3a's code, and one PR would exceed ~700 lines. Inc 2 and 3a are built in parallel; dev verification is sequenced, since dev is shared.
- **2026-11-05 (inc 1 build)** — Changes from the plan as written:
  - **Concurrent shadow:** shadow items run concurrently, each with a 5 s bound, so the whole shadow is bounded at 5 s rather than N × 5 s against the 20 s ack deadline.
  - **Uncached sweep:** the sweep uses its own `mode: "none"` provider, because cached reads aren't revalidated.
  - **Package errors at warn:** the package's `error` logs go out at `warn` while it's only in shadow, so they don't show in the dashboard's "Error logs" widget.
  - **Version:** pinned `^2.5.2`, not 2.5.1.
- **2026-11-05** — Confirmation and stock mapping reads go through the cache (Harry: "I don't think we should be hitting the config service immediately - cache is fine"). The live per-confirmation GETs were a gap with no recorded reason, not a G3 contract safeguard. A mapping edit reaches confirmation output within the invalidation path (seconds) or, worst case, the 600 s network TTL.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->

- **remote-config (pkg-node):**
  - `ConnectorMappingHandler.resolve` validates the whole connector strictly before reading a mapping, so one connector-level schema failure blocks every mapping read for that connector.
  - On a cold cache, `resolveByUsername` throws for every username after the first strict-invalid connector in the summary list.
  - `processRevision` aborts a revision's remaining items on the first throw.
  - Cached connector reads aren't revalidated, although the README says they are.
  - These belong in pkg-node's Waypoint docs and affect fapi and shopify-connector too.
- **sftp-connector:**
  - In-repo `upsertAllBusinessConnectors` rewrites only businesses that still have a connector, so a business whose last connector is deleted keeps a stale cache entry until TTL.
  - The PENDING → `create_sftp_user` publish stays in the connector after Plan C inc 5. It is what triggers the host's provisioning, so `SFTPUserBuilderException` (`ConnectorReadFailure`, `UserCreation`) survives inc 5.
- Confirmation and stock egress reading mappings live (one config-service GET per confirmation) was never a deliberate choice for G3; ingest has always used the cache. Confirmed by Harry 2026-11-05.
- (Resolved 2026-11-05) The remote-config network TTL unit is ms (pkg-node `CLAUDE.md`, 2.5.0), and fapi's divided value works out to about 604.8 s, consistent with pkg-node `architecture.md:164`. The draft's "600 ms" fear applied only if sftp copied fapi's divide.
