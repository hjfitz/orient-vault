---
tags: [waypoint, ledger]
title: pkg-node — work ledger
---
# pkg-node — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-11-05 — Add memTtl and a requestHeaders callback to remote-config

Add memTtl and a requestHeaders callback to remote-config

Stack A PR 1 of the remote-config 2.6/2.7 plan (increment 2). In-memory TTL option and a Config API request-headers callback that can't replace x-api-key or reach the feature-flag client; adds the 2.5.1 compat type test. No version bump (released by PR 2).

PR: gfs-bifrost/pkg-node#299

## 2026-11-05 — FUSE-1350

Build a remote-config connector index only from a complete lookup (2.5.2)

remote-config 2.5.2: caching one connector (backlink, connector-ID/username lookup, setInCache) only joins an existing business/storefront index; a business miss or resolveByType builds business indices from fetched summaries (failed connectors included), a storefront miss builds its storefront index; with no index to join, the business's/storefront's empty markers (own type + all) are cleared so a first connector is not hidden. Dev proof on DAZZA (8 sftp, 2 rest): 2.5.1 saw 1/8 and 0/2 after one backlink, 2.5.2 sees 8/8 and 2/2.

PR: gfs-bifrost/pkg-node#297

## 2026-11-02 — Add Postgres metric and dependency names to observability

Add Postgres metric and dependency names to observability

@gfs-bifrost/observability 2.5.0: CONFIG_METRIC.POSTGRES_UP/POSTGRES_LATENCY (fuse.postgres.up/latency) and DEPENDENCY.POSTGRES, the Cloud SQL counterparts of the Mongo members. Additive/minor. First consumer: config-service (unit C4).

Ship: SHIP-1028-cloudsql-repo-seam
PR: gfs-bifrost/pkg-node#296

## 2026-11-02 — Widen the zod peer to ^4.4.3 so consumers can take zod >=4.6.6

Widen the zod peer to ^4.4.3 so consumers can take zod >=4.6.6

Every zod-using package (types, ddp, rules-engine, pubsub, remote-config, observability, snap, audit) declared an exact zod 4.4.3 peer, which held each consumer on 4.4.3 and blocked the fix for GHSA-mrhx-c7xc-m3w5 (zod <4.6.6). Widened the peer to ^4.4.3 with patch bumps on all 8 packages, kept the devDependency on the 4.4.3 floor, and updated the CLAUDE.md invariant. Built and tested on both zod 4.4.3 and 4.6.7, and checked consumer-side against sftp-connector on zod ^4.6.6.

PR: gfs-bifrost/pkg-node#294

## 2026-10-28 — List a business's backends and tag backend change events with their type (types 11.4.0)

List a business's backends and tag backend change events with their type (types 11.4.0)

Delivery Backends A3 prerequisite. Optional backends refs ({backendId, type}) on the business response and optional backendType on the BACKEND_CONFIG backlink; both string-typed so new backend types don't break older readers.

PR: gfs-bifrost/pkg-node#292

## 2026-10-27 — observability 2.4.0: skip the sidecar log file when Datadog runs in-container

observability 2.4.0: skip the sidecar log file when Datadog runs in-container

resolveSink: DATADOG_ENABLED && DD_LOGS_ENABLED → stdout only (no /shared-volume FileSink, which EACCES-crashes startup on the non-root golden images). Sidecar services unchanged. Draft; unblocks Node services on node24-runtime.

PR: gfs-bifrost/pkg-node#291

## 2026-10-27 — Add a SELECTOR backend type alongside SNAP (types 11.3.0)

Add a SELECTOR backend type alongside SNAP (types 11.3.0)

Delivery Backends unit A1. Additive: SelectorBackendConfig (endpoint, credentials, carrier, serviceCode, optional shipperId/contractNo/dropoff/defaultWeightKg/print — from selector-adapter's booking.Connection), AnyBackendConfig union and CreateAnyBackendRequestDTO for config-service's plural route. BackendConfig/BackendFragmentSchema/SNAP DTOs untouched (snap-adapter .omit()s it; poller parses pages SNAP-only). Version race with #278 (12.0.0): second to merge renumbers.

PR: gfs-bifrost/pkg-node#290

## 2026-10-15 — Add the sftp_login audit kind

Add the sftp_login audit kind

Added a strict sftp_login Fuse audit kind to @gfs-bifrost/audit (0.2.0 -> 0.3.0, additive). It records each SFTP login attempt: username, optional connectorId, outcome, sourcePort, and optionally authMethod, key type and fingerprint, and failureReason. sftp-connector will produce it from the SFTP VM's sshd log (Ops Agent). It is strict so attacker-controlled sshd text can't ride along, and connectorId is optional for legacy SFTP users. Out-of-ticket, Audit Service programme unit UJ.

PR: gfs-bifrost/pkg-node#279

## 2026-10-14 — remote-config 2.4.0: runtime feature flag reader

remote-config 2.4.0: runtime feature flag reader

Opt-in .withFeatureFlags() exposes provider.featureFlags: sync isEnabled over a 30 s in-process snapshot (unresolvable = false, last-known kept on failure, 5 s retry, single-flight, no timers), a bounded ready(), onRefresh for consumer metrics, and ingestEvent(record) for bifrost.{env}.feature_flag_revision.v1, which refetches immediately. fetch + AbortSignal.timeout, not axios. FeatureFlagFetchException never carries the request. Live harness against the dev topic proved the event flip within the TTL. gitleaks flags fixture strings shaped like api keys, so use plain words.

PR: gfs-bifrost/pkg-node#275
PR: gfs-bifrost/pkg-node#276

## 2026-10-14 — Feature flag revision contract (types 10.15.0, observability 2.3.0)

Feature flag revision contract (types 10.15.0, observability 2.3.0)

types 10.15.0 adds FeatureFlagRevision {key, change, version?}, the refetch signal config-service publishes on bifrost.{env}.feature_flag_revision.v1. Delete has no version, unlike config_revision's -1. observability 2.3.0 adds CONFIG_METRIC.FEATURE_FLAG_PUBLISHED / _PUBLISH_FAILED, separate from the revision metrics. No schema specs, per the standing rule; the built dist was checked instead. Renovate #272 (remote-config peer >=10.14.0) merged with it.

PR: gfs-bifrost/pkg-node#273

## 2026-10-14 — Add FeatureFlagSchema with scheduled changes and the evaluation rule (types 10.14.0)

Runtime feature flags, phase 1 contract. This is workshop action L3, change process and feature flags; there is no ticket.

- types 10.14.0 adds FeatureFlagSchema.
  - It has a strict `targets` (null in v1; customer targeting comes in a later iteration) and a strict, required-nullable `scheduledChange: { at, enabled }`.
  - Pure `resolveFeatureFlag(flag, now)` and `evaluateFeatureFlag(flag, now, context)` live in `config/utilities`, the single rule that config-service and fuse-ui share.
  - It is not a config_revision fragment.
- Scheduling: readers evaluate the pending change against the clock, so there is no scheduler job. config-service's GET will project the resolved state.
- A remote-config client was added, then reverted in 47638f7: fuse-ui reads the API directly in v1. The backend event and caching approach is a follow-up ticket, and the code stays reachable at 3c738b7.
- Held as a draft until the v1 display fields from the design mock are settled.

Plan: [[runtime-feature-flags-types-featureflagschema-an]].

PR: gfs-bifrost/pkg-node#271

## 2026-10-13 — Add secrets system kind registry to @gfs-bifrost/audit (0.2.0)

Add secrets system kind registry to @gfs-bifrost/audit (0.2.0)

Secrets Hub programme H1: ./secrets subpath with strict secret_change kind, producer union, KNOWN_SECRET_CHANGE_ACTIONS. Draft.

PR: gfs-bifrost/pkg-node#270

## 2026-10-12 — Read an impossible EDIFACT date as absent (edi 0.8.1)

Read an impossible EDIFACT date as absent (edi 0.8.1)

An all-zero placeholder date (CT's DESADV DTM+361:00000000) rolled over to 1899-11-30; any date that doesn't round-trip is now absent. EDI Support unit I8.

PR: gfs-bifrost/pkg-node#269

## 2026-10-12 — Add @gfs-bifrost/audit: AuditMessage envelope, Fuse kind registry and publisher

Add @gfs-bifrost/audit: AuditMessage envelope, Fuse kind registry and publisher

New standalone package for the Audit Service programme (unit UC). AuditMessage is its own envelope, not BifrostMessage; system-scoped. Root envelope must stay a non-union for the Go codegen. ./fuse holds the kind registry. ./publisher never rejects and has no @google-cloud/pubsub dependency.

PR: gfs-bifrost/pkg-node#268

## 2026-10-09 — FUSE-1238

Add identifiers.carrierId to CanonicalWorkOrder (types 10.12.0)

Optional identifiers.carrierId on the work-order canonical so a mapping default reaches Snap's CarrierId. Numbered 10.12.0 because 10.11.0 is held by an open PR.

PR: gfs-bifrost/pkg-node#265

## 2026-10-02 — Report connectors remote-config couldn't resolve

Report connectors remote-config couldn't resolve

Poller Clear-Down E8. remote-config 2.3.0: resolveWithUnresolved returns {connectors, unresolved}; failed connectors join the business index so they're re-reported instead of vanishing. resolve() unchanged.

PR: gfs-bifrost/pkg-node#261

## 2026-09-30 — FUSE-1259

edi 0.8.0: inbound DESADV normalizer

DesadvNormalizer composes the shared readers plus a CPS walker (slicePackageGroups). packages[] = CPS tree in message order; each line carries package.{id,parentId,level,type}, sscc (nearest package with GIN+BJ) and outerSscc. Kit components stay separate lines linked by subLine.parentLine, with LIN codeList/agency as sent, so connector mappings decide roles; no partner codes in src. Raw keys only. Kitting fixture synthesised from the copacking deck (Harry OK 2026-09-30) until CT sends a real one. Gotchas: CT pack message repeats LIN+1 (line numbers not unique); CT loading GIN+BJ shares its first component across pallets.

PR: gfs-bifrost/pkg-node#257

## 2026-09-30 — FUSE-1259

edi 0.7.0: shared segment readers and raw qualifier keys

The five inbound normalizers now compose one shared reader per segment (finders/line-readers/party), with per-message policy (line terminators, unparseable-QTY handling) kept as parameters so output is unchanged. A characterisation test pins every dotted path + line count over the synthetic and CT fixtures. Additive raw keys: INSDES/ORDERS parties by NAD qualifier (role aliases kept), every PIA composite into itemIds (PIA+1 first C212 still wins), line references/goodsIds/item/subLine. Absorbs EDI Support I5. Gotcha: JSON.stringify runs Date.toJSON before a replacer, so a date-aware flatten must check instanceof Date itself.

PR: gfs-bifrost/pkg-node#256

## 2026-09-29 — FUSE-1088

types 10.8.0: movement reference, batch and expiry on stock adjustments

Optional only on CanonicalStockAdjustment: identifiers.movementRef (Snap: <SiteId>_<MoveType>_<MoveId>_<MoveLineId>, Jitterbit's EntityID shape), from/to.batchId, from/to.expiry (Date, following pick/pack/RGA; goods-in's string expiry is the outlier). Scope settled by Jack 2026-09-24 on FUSE-1088; expiry mandatory per batch in Puig INVRPT V04 §5.4.11. Published on merge.

PR: gfs-bifrost/pkg-node#254

## 2026-09-24 — FUSE-1258

types 10.5.0: batch and work-order references on FGR and WOC

Optional only: location.batchId on FGR and WOC lines; FGR identifiers.salesOrder + workOrder.customerRef (workOrderId/businessWorkOrderId existed, now populated by the poller); SnapStockMovement.FromStockId (Snap's real casing; FromStockID kept, never populated). Published 10.5.0 on merge. #232/#233 bump 10.2→10.3 and must renumber.

PR: gfs-bifrost/pkg-node#249

## 2026-09-24 — FUSE-1253

EANCOM D.96A serializers stack (edi 0.6.0)

RECADV and DESADV rebuilt, OSTRPT and INVRPT added, all generic EANCOM D.96A. Static partner codes sit in *Codes with EANCOM defaults (options.codes overrides them); per-record codes (INV/STS, qualifiers) are *Out data. Charlotte Tilbury's samples are reproduced from test-only config fixtures. Stacked as five PRs; the version bump is in the last so one publish carries all four. EdiService.serialize now takes an inline codes override.

PR: gfs-bifrost/pkg-node#244
PR: gfs-bifrost/pkg-node#245
PR: gfs-bifrost/pkg-node#246
PR: gfs-bifrost/pkg-node#247
PR: gfs-bifrost/pkg-node#248

## 2026-09-24 — FUSE-1253

edi 0.5.0 interchange + types 10.4.0 edi egress file type

edi 0.5.0 adds serializeInterchange/wrapInterchange: one message wrapped in UNA?/UNB…UNZ with a caller-supplied control ref, every partner value a caller option (customer-agnostic rule). Existing DESADV/RECADV output is byte-identical (default release stays D:01B until the serializer rework). types 10.4.0 widens EgressFiletype with "edi" and adds ediEnvelope on both SFTPIngress shapes, with plain-string qualifiers and no defaults. Rollout hazard: remote-config's connector backlink refresh isn't type-filtered, so fapi + shopify-connector must be on >=10.4.0 in prod before any connector is saved as edi.

PR: gfs-bifrost/pkg-node#241
PR: gfs-bifrost/pkg-node#242

## 2026-09-23 — rules-engine: take @gfs-bifrost/types as a peer range

rules-engine: take @gfs-bifrost/types as a peer range

rules-engine 2.1.0 published with types frozen to exactly 10.3.0 (pnpm workspace:* conversion), and its public applyRoutingRules exposes CanonicalSalesOrder, so sftp-connector (still on types 9.x) could not type-check against it. Moved types to a >=9.0.0 peer (dev dep workspace:*) like remote-config; 2.1.1, no source change. Unblocks FUSE-1221.

PR: gfs-bifrost/pkg-node#238

## 2026-09-23 — FUSE-1231

Replace ts-edifact with an in-package EDIFACT tokenizer (edi 0.4.1)

@gfs-bifrost/edi 0.4.0 couldn't load under plain Node, CJS or ESM, because its only dependency @makakwastaken/ts-edifact is mis-packaged in every published version. It had only ever run under vitest's alias/inline workaround. The first real consumer (sftp-connector, FUSE-1231) found it. 0.4.1 swaps ts-edifact for an in-package tokenizer that produces byte-identical segment output on all 14 fixtures (hash-pinned), honours UNA custom delimiters, no longer enforces charset, and has zero runtime dependencies. The PR also repaired code-quality-edi.yaml, which had called non-existent template workflows, so edi CI never ran. Merged and published.

PR: gfs-bifrost/pkg-node#237

## 2026-09-23 — FUSE-1216

Add a lookup() DSL function backed by dictionaries

Added lookup(dictionary, key[, default]) to the rules-engine DSL. Dictionaries are supplied by the caller through applyTranslationRules options (replacing the dead boolean third param) and a precompiled DictionaryLookup for getDSLRunner. Miss yields empty/default, unknown dictionary throws, keys compared as strings with optional case folding. Structural type, no types dependency; config.dictionaries passes straight in. rules-engine 2.1.0; DSL Usage Guide updated. Unknown-function-throws deliberately deferred (behaviour change for live rules).

PR: gfs-bifrost/pkg-node#235

## 2026-09-23 — FUSE-1215

Add dictionaries to the connector mapping config

Added optional named key→value dictionaries to the simple/lined connector mapping config types and schemas, so they ride the CONNECTOR_MAPPING fragment and survive remote-config validation. Names are stable identifiers unique per mapping; keys unique per dictionary (case-folded when caseInsensitive); capped at 2,000 entries. types 10.3.0. Groundwork for the rules-engine lookup() function and consumers.

PR: gfs-bifrost/pkg-node#234

## 2026-09-21 — FUSE-1034

CanonicalStockPosition (product | kit)

Added `CanonicalStockPosition` (+ schema) -- a discriminated union on `type: "product" | "kit"`, the foundational v2 canonical shape the later Get Stock API (FUSE-792) will return. The `product` arm carries an optional `quantities` object (`onHand`/`allocated`/`orderOut`/`dueIn`) and an optional `product: CanonicalProduct`. The `kit` arm carries `potentialKitQty` (derived availability) and an optional `kit: CanonicalKit` -- the kit's bill of materials (`kitId`, required `unit`, `components` each with `skuId`/`qty`/required `unit`, optional `dates`, `maintenanceIndicator`), grounded directly in Snap's real `snapKit` entity fields and inspired by, but distinct from, `CanonicalWorkOrderLine`'s COMPONENT-role convention -- a work-order line describes building one instance of a kit, this describes the kit's recipe. Deliberately does not mirror Snap's raw per-kit-record Qty-family fields, since `potentialKitQty` already represents real availability. `quantities`/`dates` are nested sub-objects rather than flat prefixed fields, matching every sibling canonical type's convention (confirmed against `CanonicalStockAdjustment`'s precedent). `CanonicalProduct`/`CanonicalProductSchema` were split out of `CanonicalMasterData`'s previously-inline `product` shape into their own first-class canonical type, so both `CanonicalMasterData` and `CanonicalStockPosition` compose from the same shape. Bumped @gfs-bifrost/types 10.1.0 -> 10.2.0.

PR: gfs-bifrost/pkg-node#227.

## 2026-09-18 — FUSE-1189

Shopify stock sync schedule fields on ShopifyIngress

Added `stockSync?: { enabled?: boolean; schedule?: { days: DayOfWeek[]; time: string } }` to `ShopifyIngress`/`ShopifyIngressConfigService` -- foundation for a fixed, ILG-configured Shopify stock-sync schedule, a leaner slice of the FUSE-658 epic than its original full self-serve frequency/anchor-time design. Grouped as one `stockSync` object rather than sibling flat fields, matching the existing `retrievalConditions` nesting convention already on `ShopifyIngress`. New `DayOfWeek` string-literal union (`"monday"`-`"sunday"`), per the file's own no-new-enums convention. Added to both `ShopifyIngress` and `ShopifyIngressConfigService` in this PR -- per the org's own FUSE-883 lesson that a field added to only one of the two gets silently stripped by remote-config consumers. Bumped @gfs-bifrost/types 10.1.0 -> 10.2.0. Zod enforces `days.min(1)` but not the time-format regex or the "required when enabled" cross-field rule -- both left to the config-service persistence ticket. Blocked follow-ons: config-service persistence/validation, fuse-ui, and snap-queue-polling-service's 15-minute trigger.

PR: gfs-bifrost/pkg-node#228.

## 2026-09-17 — FUSE-1167

confirmationsEnabled on ConnectorRefDTO

Added optional confirmationsEnabled?: boolean to ConnectorRefDTO + ConnectorRefDTOSchema (lockstep, the schema is declared z.ZodType<ConnectorRefDTO>). Was the one connector ref shape missing the flag; ConnectorDTO/ConnectorConfigService already had it. Published as 10.1.0 (additive minor, no code change needed by consumers). Composed into CustomerInformationResponseDTOSchema (connectors: z.array(ConnectorRefDTOSchema)) with no edit needed there -- flows through to config-service's business index for free once that service bumps its pin. Paired with config-service#FUSE-1167 (business-index projection + openapi.yaml + eventually the types-pin bump itself, same day, once downstream consumers of /api/v1/docs/generated needed the typed field, not just the raw projection). PR: gfs-bifrost/pkg-node#225.
## 2026-08-21 — FUSE-1078

extract @gfs-bifrost/resilience out of the snap package

New package @gfs-bifrost/resilience 0.1.0 -- the transport-agnostic resilience primitives (`PerHostCircuitBreaker`, `buildRetryPolicy`, `Semaphore`, `calculateBackoffMs`/`calculateJitterMs`/`retry`) lifted verbatim out of @gfs-bifrost/snap's `resilience`/`http` modules, as pure renames with zero changed lines. @gfs-bifrost/snap 0.4.0 takes a workspace dependency on the new package and re-exports everything from the same `./resilience`/`./http` subpaths, so the extraction is invisible to snap-adapter/snap-mcp/snap-mcp-server (verified by diffing the built export surface of all four snap subpaths before and after -- identical). Unlike snap, the new package has a single entry point with no subpaths, so consumers on classic/node10 module resolution (e.g. shopify-connector) resolve it with no `typesVersions` block needed. Groundwork for shopify-connector's per-host circuit breaker on its Shopify GraphQL path -- a second consumer of a generically-named package, rather than shopify-connector depending on something named `snap` for an unrelated capability.

PR: gfs-bifrost/pkg-node#210.

## 2026-08-12 — FUSE-855

work_order ingress-mapping use case (types 9.1.0)

Added the `work_order` ingress-mapping use case -- `UseCases.WORK_ORDER`/`"work_order"` on `UseCase`/`ALL_USE_CASES`, the config-side counterpart to the `work_order` `EntityType`/`FailureUseCase` that has existed since 8.1.0. New `WorkOrderMapping` type + `WorkOrderDTOSchema`, a lined/grouped mapping shape (mirrors `ReturnGoodsAuthorizationMapping`) since a work order has lines with component and finished-good roles, unlike the simple shape `master_data`/`stock_adjustment` use. No other file changes were needed -- `ConnectorDTOSchema`/`ConnectorConfigService`/`UseCaseEnumSchema` all derive their per-use-case keys from `ALL_USE_CASES`/`UseCases` (the mechanism the 8.3.0 FGR/WOC egress additions introduced), so they picked up `work_order` automatically. Bumped @gfs-bifrost/types 9.0.0 -> 9.1.0. First of three PRs on this ticket -- config-service and fuse-ui follow once this publishes, since config-service's `ConnectorDTOSchema` derives its keys from `ALL_USE_CASES` and would otherwise strip a use case declared only downstream (the FUSE-883 strip class).

PR: gfs-bifrost/pkg-node#202.

## 2026-08-07 — FUSE-785

CanonicalLineRole on despatch confirmation lines (9.0.0)

Added `CanonicalLineRole` (`standard`/`kit_parent`/`kit_component`) and made `role` a required field on `GoodsOutConfirmationLine`, `CanonicalPickConfirmationLine` and `CanonicalPackConfirmationLine` (+ schemas) -- breaking major, @gfs-bifrost/types 8.4.0 -> 9.0.0. A SnapFulfil Kit is a bill-of-materials link, not a product type, so fulfilling one explodes the despatch into its component lines -- designed vendor behaviour, not a misconfiguration -- and only the parent line carries the Shopify fulfilment attachment. With no explicit marker, shopify-connector had been inferring "exploded component" from an absent reference, throwing on the first component line; the throw was swallowed by `Promise.allSettled`, `confirmation_made` was never published, and SNAP re-announced the confirmation indefinitely (~29h loop on PURDYFIGG). `role` is the canonical interpretation of the raw SNAP `Level` check code (`"00"` = genuine outbound line). All three despatch line types needed it, since pick/pack/goods-out handlers all map the same `shipment.ShipmentLines` array. `CanonicalWorkOrderLineRole` was deliberately left untouched -- consumed-vs-produced is different semantics from sold-vs-exploded. Made required rather than optional since an optional field would have preserved the same ambiguity it exists to remove, and every affected consumer's own pin (7.x/8.x) strips the unknown key rather than breaking, so this was safe to publish ahead of its consumers.

PR: gfs-bifrost/pkg-node#199.

## 2026-08-06 — FUSE-1050

RGA confirmation date/batch field gaps (types 7.7.0 + rules-engine 2.0.1)

Added three optional fields to `CanonicalRGALine` -- `identifiers.batchId`, `product.upcDescription`, `dates.expiry` (+ schema) -- RGA confirmations were silently dropping this data since `CanonicalRGALine` had no field for it at all, despite reusing the same receipt/consignment Snap flow as goods-in confirmations. Bumped @gfs-bifrost/types 7.6.0 -> 7.7.0. Consumed by snap-queue-polling-service's `ReturnGoodsAuthorizationHandler`, enriching via the same `fetchStockConsignment` batch-matching path `GoodsInConfirmationHandler` already used.

A follow-up fix landed separately in @gfs-bifrost/rules-engine: `flattenObject()` was silently dropping any `Date`-valued field (a `Date`'s properties are inherited, non-enumerable methods, so `Object.entries()` on one is always empty, and the function had no special case for it before recursing). `Date` is now checked and cloned before the generic object branch; the return type widens to include `Date` so callers pick their own serialisation format rather than the shared utility imposing one. Root cause of the residual RGA-confirmation gap: unlike goods-in/out confirmations (string dates), `CanonicalReturnGoodsAuthorization`/`CanonicalRGALine` type their date fields as `Date`, so RGA was uniquely exposed on sftp-connector's dynamic confirmation-egress flatten-then-map pipeline. Bumped @gfs-bifrost/rules-engine 2.0.0 -> 2.0.1.

PR: gfs-bifrost/pkg-node#175.
PR: gfs-bifrost/pkg-node#197.

## 2026-07-28 — FUSE-635

work order support in @gfs-bifrost/types (8.1.0)

Added `work_order` to `FailureUseCase`/`FailureUseCaseSchema` so `create_data_failure` can carry a work-order WMS-submission failure -- without it, snap-adapter's failure envelope validated on the producer side (it casts `entityType as FailureUseCase`) but was rejected at every consumer's Zod boundary, so the deduper could never clear a held work order for retry (same silent-drop class as the FUSE-794 metadata strip). Added `financial.currency` and `shipping.shippingLane` to `CanonicalWorkOrder` -- Snap mandates `Currency`/`ShippingLane`/`LineValue` on any shipment and a work order lands as one (`OrderType=S10`), but the WO canonical had no `financial`/`shipping` block at all, so every work-order create failed with three MANDATORY field errors (reproduced live against GADG dev, then confirmed fixed with a 201 after resending with both fields populated). `LineValue` deliberately not added -- a work order has no sale value, so snap-adapter sends it as a create-protocol constant rather than inventing one. Both additions are optional/additive. Re-numbered from a planned 7.8.0 to 8.1.0 after the breaking businessId-required 8.0.0 landed on main mid-flight.

PR: gfs-bifrost/pkg-node#186.

## 2026-07-14 — FUSE-892

pick_confirmation/pack_confirmation on FailureUseCase

Added `pick_confirmation` and `pack_confirmation` to `FailureUseCase` (type + runtime `FailureUseCaseSchema`), letting the `confirmation_data_failure` topic's `recordType` attribute and `BifrostFailure.useCase` carry pick/pack confirmation clear-down failures. The general `UseCase` enum already had both values; only the failure-side union lagged. Additive, bumped @gfs-bifrost/types to 7.6.0. Mirrors the 5.5.0 RGA precedent. Prerequisite for snap-adapter's pick/pack OBQ clear-down failure publishing.

PR: gfs-bifrost/pkg-node#172.

## 2026-07-10 — FUSE-1012

@gfs-bifrost/observability package

New package @gfs-bifrost/observability 0.1.0 -- the first slice of the `@ilg-platform/observability-sdk` adoption work. Ships `CorrelationDetails`/`ExtendedCorrelationDetails`, the correlationId/businessId/recordType/recordId/flow shape common to nearly every service's request-scoped log context (reconciled from a fleet-wide audit of the per-service `requestor`-nesting convention), plus the `channel`/`connectorId` fields roughly half the fleet carries. `Flow` is reconciled to one shared taxonomy (`create`/`confirmation`/`release`/`redrive`/`config`/`user_creation`), replacing five divergent per-service `flow` enums -- dedupe-service's local `"dedupe"` maps onto the shared `"create"` (same pipeline stage). The field is named `channel`, not `source`, because several services already stamp a top-level Datadog runtime tag `source: "nodejs"` that collided with the old nested `requestor.source` business-meaning field. Also ships `getDefaultTags({ service, environment })`, consolidating the identical tag object every service had been duplicating in its own `observability/tags.ts`. Deliberately type/helper-only -- no AsyncLocalStorage/cls-hooked runtime binding yet; each service keeps its own correlation-context plumbing until the SDK wrapper follow-up.

PR: gfs-bifrost/pkg-node#171.

## 2026-07-07 — FUSE-885

Pick/Pack canonical confirmation types

Added `CanonicalPickConfirmation` (Snap SHIPSTAGE 29) and `CanonicalPackConfirmation` (SHIPSTAGE 39) as two standalone canonical types + Zod schemas -- not a union, not a `kind` discriminator on `GoodsOutConfirmation` -- mirroring the FGR/WOC precedent so each shape carries only the fields valid at its own stage, with discrimination living on the `recordType` Pub/Sub attribute. Pick carries picked quantities/shortages/lines with no carton/shipping/carrier/financial blocks (nothing is packed or shipped yet); Pack adds the carton `packages` block, `physical` weights, and an optional `shipping.carrier` (may or may not be assigned by the pack station). Identifiers aligned with `GoodsOutConfirmation` so IDs read uniformly across pick, pack and dispatch. Bumped @gfs-bifrost/types to 7.2.0 -- foundation for the FUSE-707 pick/pack confirmation flow; blocks the snap poller, API, SFTP, snap-adapter clear-down and collector follow-ons.

PR: gfs-bifrost/pkg-node#164.

## 2026-07-03 — FUSE-996

atomic set-if-not-exists claim primitive (cache 0.2.0)

Added an atomic claim primitive to @gfs-bifrost/cache (the INC-30 durable dedupe fix) -- `RedisCache.setIfNotExistsAsync`/`CacheService.trySetIfNotExistsAsync`, backed by redis `SET key value NX PX ttl`. Resolves `true` when the claim is won, `false` when the key already existed (a normal outcome, not an error), and rejects only on infrastructure failure, so callers can distinguish "duplicate, skip" from "cache unavailable, fail open." Claims are never retried (a re-issued `SET NX` after a lost response would see its own key and misreport a won claim as a duplicate), are network-tier only (no per-instance LRU write, no CacheMutation event -- a cross-instance claim is meaningless there), and always settle within a bounded claim timeout (default 2000ms) since node-redis parks commands on a reconnecting client's offline queue indefinitely with no rejection. A disconnected cache rejects immediately rather than queueing. Bumped @gfs-bifrost/cache 0.1.1 -> 0.2.0. First consumer: snap-queue-polling-service, deduping confirmation publishes by `identifiers.queueId`.

PR: gfs-bifrost/pkg-node#161.

## 2026-07-03 — FUSE-954

columnOrder on connector mapping config (types 7.2.0)

Added optional `columnOrder?: string[]` -- an ordered list of output CSV column names (`rule.from`/`default.key` values) -- to `LinedMappingConfig`/`SimpleMappingConfig` and their `*ConfigService` variants, plus the matching Zod schemas. Additive/optional, no lockstep required; bumped @gfs-bifrost/types 7.1.0 -> 7.2.0. The two runtime consumers (config-service, sftp-connector) deliberately stayed on `^6.3.0` and threaded `columnOrder` through local schema copies rather than bumping straight to 7.x, since 7.0.0's businessId-required major would have broken roughly 10 sftp fixture/factory sites -- migrating them onto 7.x directly is a separate follow-up.

PR: gfs-bifrost/pkg-node#162.

## 2026-07-01 — FUSE-981

ingest-capture envelope for create_record (types 7.1.0 + pubsub 0.4.0)

Added the `IngestCapture` envelope contract for `create_record_request`/`create_record` -- a discriminated union (`sftp`/`shopify`/`api`) carrying source provenance, plus a `BifrostCreateRequest` envelope, in @gfs-bifrost/types 7.1.0. SFTP capture carries a `PayloadPointer` (a pointer, not inline bytes -- GCS today) so raw files stay off Pub/Sub; Shopify capture keeps the webhook body inline since it's already small. Capture rides on the envelope metadata via the dedicated `BifrostCreateRequest` type, never the shared `BifrostMessage`, keeping it off confirmation/release/failure envelopes (mirrors the FUSE-794 provenance precedent). In the same PR, @gfs-bifrost/pubsub took a real `@gfs-bifrost/types` dependency and started re-exporting the shared envelope shapes instead of mirroring them, deleting its own duplicate block; added `PubSubIngestor.ingestCreateRequestEvent()` so `capture` actually round-trips through ingest (the base `ingestEvent` still strips it, the same strip class FUSE-794 fixed for the other metadata fields). pubsub bumped 0.3.0 -> 0.4.0. First slice of FUSE-967 (Customer Transaction History raw-payload capture); connector population and the Collector read-path are downstream follow-ups.

PR: gfs-bifrost/pkg-node#156.

## 2026-06-29 — FUSE-616

businessId required on canonical types (7.0.0)

Made `businessId` required across the canonical fleet -- `CanonicalSalesOrder`, `CanonicalRGA`, `GoodsInConfirmation`/`GoodsOutConfirmation` (added alongside the existing raw-SNAP `bizId` field), and the Work Order family (`CanonicalWorkOrder`, `CanonicalWorkOrderConfirmation`, `CanonicalFinishedGoodReceipt`). SNAP rejects a missing BizId, so the optional field was a silent path to a downstream rejection. Breaking major bump, @gfs-bifrost/types 6.3.0 -> 7.0.0. `CanonicalPurchaseOrder`/`CanonicalMasterData`/`CanonicalStockAdjustment` were already required and untouched; line-level `businessId` on `CanonicalRGALine` stays optional (snap-adapter null-coalesces to the header-level required field).

PR: gfs-bifrost/pkg-node#154.

## 2026-06-23 — FUSE-794

traceability fields on BifrostMessageMetadata

Added four optional traceability fields to `BifrostMessageMetadata` -- `source`/`connectorId`/`recordId`/`recordType` (type + `BifrostMessageMetadataSchema`) -- purely additive, no lockstep required. `source` forbids empty string, matching the already-required `BifrostFailure.source`; it's the candidate to become required in a later major once every producer populates it. Fixed a bug where `BifrostBulkMessageSchema` inlined its own narrower metadata object instead of reusing the shared schema, which would have silently stripped the new fields off every bulk (confirmation) message. Bumped @gfs-bifrost/types 6.2.0 -> 6.3.0. A companion PR widened @gfs-bifrost/pubsub's own narrow ingest metadata schema in lockstep (0.2.0 -> 0.3.0) -- pubsub defines its own metadata schema, so even after consumers adopted the wider types envelope, `ingestBifrostEvent`/`ingestBifrostBulkEvent` were still stripping the new fields on decode, meaning passthrough services (dedupe, replay) never saw inbound `source`/`connectorId`. First beneficiary: dedupe-service, which already preferred inbound `recordId`/`source` with a fallback.

PR: gfs-bifrost/pkg-node#152.
PR: gfs-bifrost/pkg-node#153.

## 2026-06-17 — FUSE-965

@gfs-bifrost/edi standalone parser programme

Built out @gfs-bifrost/edi from scratch as a standalone EDIFACT<->intermediary parser, in stages: Phase 0 extracted shared finders/coerce/qualifier helpers (no behaviour change); Phase 1 added the normalized `IntermediaryMessage` plus INSDES/PRICAT/ORDERS normalizers, fixing real structural bugs along the way (PRICAT sub-line collapse, MEA unit disambiguation, NAD party assembly); Phase 2 added the config-driven `applyFieldMap` mapping engine, proven end-to-end against real CT fixtures. A RECADV prototype validated moving to per-message-type typed intermediaries (`RecadvIntermediary` etc., replacing the generic envelope), then all three existing handlers were migrated onto that pattern. The package was then made fully standalone across three refactor stages: internalize the EDI config types (dropping the `@gfs-bifrost/types` config dependency), sever inbound from canonical types (output is the typed intermediary; mapping to canonical becomes the consumer's job via `applyFieldMap`), then sever outbound too and drop the `@gfs-bifrost/types` dependency entirely (serializers take lean message-mirroring shapes). Interchange/multi-message splitting was added (`splitMessages()`/`normalizeAll()`), RECADV was finished (added `receiptDate`), and `ts-edifact` was pinned to 0.2.15 after 0.2.16 turned out to be a broken publish with no runtime entry point. An INVRPT inbound handler was added, targeting `CanonicalStockAdjustment` (the INCREASE/DECREASE direction for the stock-movement variant was left open pending CT spec). Docs (`CLAUDE.md`, README) were kept current throughout. Finally, once the package no longer depended on `@gfs-bifrost/types`, the now-orphaned `EDI_PROFILE` config family (`EdiMessageProfile`/`EdiQualifierMap`/`EdifactMessageType`/etc.) was removed from `@gfs-bifrost/types` itself -- a breaking major bump, 5.6.0 -> 6.0.0 -- since no other consumer referenced it.

PR: gfs-bifrost/pkg-node#132.
PR: gfs-bifrost/pkg-node#133.
PR: gfs-bifrost/pkg-node#134.
PR: gfs-bifrost/pkg-node#135.
PR: gfs-bifrost/pkg-node#136.
PR: gfs-bifrost/pkg-node#137.
PR: gfs-bifrost/pkg-node#138.
PR: gfs-bifrost/pkg-node#139.
PR: gfs-bifrost/pkg-node#140.
PR: gfs-bifrost/pkg-node#141.
PR: gfs-bifrost/pkg-node#142.
PR: gfs-bifrost/pkg-node#143.
PR: gfs-bifrost/pkg-node#144.
PR: gfs-bifrost/pkg-node#147.
PR: gfs-bifrost/pkg-node#148.

## 2026-06-15 — FUSE-830

return_goods_authorization on FailureUseCase

Added `return_goods_authorization` to `FailureUseCase` (type + runtime `FailureUseCaseSchema`) so `BifrostFailure.useCase`/`FailureAttributes.recordType` can carry RGA, letting `create_data_failure` express an RGA terminal failure. `return_goods_authorization` was already a `UseCase` but had been missing from the failure union. Bumped @gfs-bifrost/types 5.3.0 -> 5.4.0. Consumed by fapi for firing the RGA confirmation webhook.

PR: gfs-bifrost/pkg-node#124.

## 2026-06-12 — FUSE-811

null-admitting ConnectorConfigService use-case keys; remote-config fixture fix

Fixed remote-config's connector fixtures to carry the two RGA keys #118 had made required-nullable on `ConnectorDTOSchema` (7 tests had been red on main since that prior merge). Widened `ConnectorConfigService`'s use-case record values to admit `null` (@gfs-bifrost/types 5.1.0 -> 5.2.0) -- the Mongo driver has always written `undefined` as `null`, so stored connector documents already had nulls; the type just hadn't matched. config-service needs this to null-coalesce the RGA keys on connectors created before those keys existed.

PR: gfs-bifrost/pkg-node#122.

## 2026-06-12 — FUSE-815

Pub/Sub attributes on PubSubRouter publishes

`PubSubRouter.publish`/`publishBatch`/`publishToTopic` accept an optional `attributes` map, passed straight to `topic.publishMessage({ data, attributes })`; omitted, behaviour is unchanged. Needed because cross-entity topics (`create_record`, `create_record_request`) carry every record type and subscribers filter on `attributes.recordType` at the subscription level -- the router previously had no way to set publish-side attributes. Bumped @gfs-bifrost/pubsub 0.1.0 -> 0.2.0. First consumer: dedupe-service's RGA gatekeeper.

PR: gfs-bifrost/pkg-node#117.

## 2026-06-04 — FUSE-832

export BifrostFailureSchema + deepPartialify helper

Exported `BifrostFailureSchema` (previously module-private; only the envelope `BifrostFailureEventSchema` was public) so consumers like the replay service can validate a failure body directly. Added `deepPartialify()`, a runtime helper that builds a deep-partial version of any Zod schema for validating records that already failed strict canonical validation -- present values still type-check, and `.default()` wrappers are dropped rather than padding failed records with fabricated values. Bumped @gfs-bifrost/types 4.2.0 -> 4.4.0 (4.3.0 skipped, reserved by the concurrent FUSE-883 branch). First consumer: the replay service's `create_data_failure` subscriber.

PR: gfs-bifrost/pkg-node#112.

## 2026-06-04 — FUSE-883

outboundTagsEnabled on ShopifyIngress

Added `outboundTagsEnabled` to the `ShopifyIngress` type and `ShopifyIngressSchema`. FUSE-881 had added the field only to `ShopifyIngressConfigService` (config-service's own shape), so `ConnectorDTOSchema` -- used by remote-config's `ConnectorBacklinkHandler` on every resolve -- silently stripped it before any consumer saw it. Bumped @gfs-bifrost/types 4.2.0 -> 4.3.0. Unblocks shopify-connector's outbound-tagging consumer gate. Lesson: a connector-config field must be added to both the `*ConfigService` type and the consumer-side ingress type/schema, or remote-config strips it.

PR: gfs-bifrost/pkg-node#111.

## 2026-06-02 — FUSE-671

egressFiletype on SFTP connector types

Added a required `egressFiletype: EgressFiletype` (`"csv" | "jsonl"`) field to both `SFTPIngress` union variants, `SFTPIngressConfigService`, and the matching `SFTPIngressSchema` variants -- `jsonl` is JSON Lines, one object per line, not a JSON array. Foundation for FUSE-673's `.jsonl` egress writing, part of the FUSE-725 JSON-egress epic. Bumped @gfs-bifrost/types 4.1.0 -> 4.2.0. Because the field is required, config-service needed its write path plus a `csv` backfill migration deployed before any consumer could bump to 4.2.0.

PR: gfs-bifrost/pkg-node#110.

## 2026-02-19 — FUSE-668

Stock Adjustment canonical types (RFC)

Added canonical stock-adjustment types and schemas aligned to the existing canonical models, plus a factory function and an enum for adjustment types (increase, decrease, set).

PR: gfs-bifrost/pkg-node#38.

## 2026-02-03 — FUSE-706

initial API types

Added an `api` directory with types and schemas for a paged API response -- the first API-shape types in @gfs-bifrost/types.

PR: gfs-bifrost/pkg-node#33.

## 2025-11-18 — FUSE-555

Goods In Confirmation types

Migrated the goods-in confirmation shape off Goods Out Confirmation onto a dedicated `GoodsInConfirmation`/`GoodsInConfirmationLine` type and schema, with optional properties reflecting the real structure. Fixture updated to match. Bumped @gfs-bifrost/types to 1.1.9.

PR: gfs-bifrost/pkg-node#15.

## 2025-10-31 — FUSE-455

batchId on GoodsInConfirmationLine

Added `batchId` to `GoodsInConfirmationLine` (type + Zod schema). Bumped @gfs-bifrost/types to 1.1.6.

PR: gfs-bifrost/pkg-node#12.

## 2025-10-20 — FUSE-409

rename SnapProduct Value field to Values

Renamed SnapProduct's `Value` field to `Values` in @gfs-bifrost/types -- the field carrying the customer's inner-box quantity string (INNERUNIT="INN" INNERQTY="5") was truncating to 2 characters and getting rejected by SNAP as too long, breaking Nuzest master-data submissions. The Snap API docs describe the field as `Value`; `Values` is what the wire actually uses.

PR: gfs-bifrost/pkg-node#11.

