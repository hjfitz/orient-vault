---
tags:
- system
- ecm
verified: '2026-11-10'
title: ecm — tracking
thesis: "ECM tracking is choreography, not orchestration. tracking-core owns the active-parcels store and decides which parcels are due, but it has no scheduler: carrier connectors pull batches over gRPC. The polling interval does not shrink with parcel age, because the code holds one value per carrier and state. After raw_tracking.v1, services react to topics and no controller directs them."
confidence: moderate
---
# ecm: tracking

```orient-bluf
{ "v": 1, "bluf": "ECM tracking is choreography, not orchestration. tracking-core owns the active-parcels store and decides which parcels are due, but it has no scheduler: carrier connectors pull batches over gRPC. The polling interval does not shrink with parcel age, because the code holds one value per carrier and state. After raw_tracking.v1, services react to topics and no controller directs them.", "confidence": "moderate", "action": "Read the prod etcd keys before you quote a polling cadence or an expiry. A tracking replacement must keep the raw event shape, the groupId strings and the derived DELIVERED bucket (see architecture G9 to G14)." }
```

Source: three read-only research reports of 2026-11-10 [1]. Code was read in `tracking-core` at `c0811087` (the ADO master head that day), in prod manifests at `a317dc0` and in Terraform at `e3c6dd9` (2025-07-30, so it may lag). No GCP, etcd or Mongo access was available. Confidence is `moderate` because prod config and the deployed images are not read. Basis tags follow the reports: **CONFIRMED** means a report read it in code, a manifest, Terraform or Datadog. The lease, expiry, bucket and publish-order claims were re-read in the local clone at `c081108`.

**Corrected later on 2026-11-10.** A second read built a usage map of every topic the prod Terraform creates, at Terraform master `35b545ce` and prod manifests `a317dc0` [30]. It found 70 topics and 145 subscriptions, not the 41 topics of the first catalogue. It also corrected the `raw_tracking.v1` consumer count below. The published page is MPK 356155424, with the source copy [[Handovers/2026-11-09-merak-replacement-pages.page7-ecm-topics]].

**Published as pages later on 2026-11-10.** The polling and expiry behaviour is MPK 356614148 and the event, status and delivery-outcome model is MPK 356614184. Both are unverified drafts, with source copies [[Handovers/2026-11-09-merak-replacement-pages.page8-tracking-chasing]] and [[Handovers/2026-11-09-merak-replacement-pages.page9-tracking-model]].

Terms: gRPC is a remote procedure call protocol. etcd is the key-value store that holds connector config. RAG is red, amber, green. POD is proof of delivery. CCIS and ICIS are the customer and internal consignment information services, the stores customers read. SUS is `shipment-update-service`.

## Short answers
- **CONFIRMED** `tracking-core` is a state store and a work-lease server, not an orchestrator. It has no cron, no timer and no push. Connectors ask it for work [2][3].
- **CONFIRMED** The polling interval does not fall as a parcel ages. Code holds one `TargetPollingMinutes` per carrier and state (`IN_TRANSIT`, `DELIVERED`, `DELETED`), with no age term [2][3]. **UNKNOWN** Prod values live in etcd, so a person could still have set `DELIVERED` shorter than `IN_TRANSIT`.
- **CONFIRMED** The chain after `raw_tracking.v1` is choreography. Terraform creates every topic and subscription, and no workflow engine or run-time controller exists in the modules read [1].
- **CONFIRMED** A tracking update is not a status string. It is three shapes: a scan event, a mapped event and a derived shipment status. The bus carries no status enum [1].

## Orchestration and polling
The page for this section is MPK 356614148, "Chasing a Parcel: How GFS Decides What to Track and When".

- **CONFIRMED** One .NET Core 3.1 image runs three roles, chosen by `System__Mode`: consignment-manager, batch-creator and response-publisher. Prod runs 3 replicas of each [4][5].
- **CONFIRMED** Each connector runs one loop per enabled etcd batch key, that is per carrier and state. The loop asks batch-creator for a batch. If the batch was full it asks again at once, and otherwise it sleeps `IntervalSeconds` (default 30). After an error it sleeps `IntervalErrorSeconds` (default 60) [6].
- **CONFIRMED** The lease is a Mongo `FindOneAndUpdate` in batch-creator, not in the connector. It matches the carrier and state, skips parcels requested within `TargetPollingMinutes`, sets `lastRequestedAt` to now and takes the oldest first [2][3].
- **CONFIRMED** The lease stamps `lastRequestedAt` when it hands the parcel out. A failed poll counts as a poll, so the parcel waits another full interval [2].
- **ASSESSED** A new parcel has no `lastRequestedAt`, so MongoDB's ascending sort should serve it first. That is soon after creation, the opposite of a back-off. Null ordering was not tested.
- **ASSESSED** The real gap can exceed the target when more parcels are due than `BatchLimit` drains. No code prioritises older parcels.
- **CONFIRMED** A parcel is created when consignment-manager reads `shipments.v2.identified`. It upserts on parcel number and shipment ID, and sets the state to `IN_TRANSIT`, or `DELETED` for a deleted consignment. It skips a consignment with no parcels, an `untracked` contract, and an `UPDATE` for a parcel that exists [7].
- **CONFIRMED** Mongo deletes the parcel with a time-to-live (TTL) index on `expiryDate`. Each poll that yields a new, unfiltered event resets it to now plus `ExpiryDays` for that carrier and status bucket [8][9].
- **CONFIRMED** Expiry logic is in `TrackingStatusManager.cs`, `ConsignmentHandler.cs` and the TTL index, not in `ActiveParcelDomain.cs`. The 90-day shape is right but the value is per carrier and bucket [8][9].
- **UNKNOWN** The effective expiry. Prod sets `ActiveParcel__ParcelOptions__default__ExpiryDays=90` as an env var, but the code binds only the `Connectors` config section and finds no `ActiveParcel` binding [10].
- **CONFIRMED** A parcel that reaches `DELIVERED` stays polled when that carrier's `DELIVERED` etcd key is on. The state change is one-way [8][11].
- **CONFIRMED** A carrier error gets no retry and no backoff. Only a credentials error is acted on: it writes a `credential-errors` row (4 h TTL), and a contract with more than 3 rows is skipped. Prod enables that for carrier IDs 10 and 19 only. That 10 and 19 mean DPD and DPD Local is **STATED** by MPK [12][13].
- **CONFIRMED** A rate-limit answer is an ordinary carrier error. The batch is issued in parallel with no throttle in tracking-core or the framework [6].
- **CONFIRMED** A faulted per-key loop logs and stops. Nothing restarts it until the options change or the pod restarts. This was read, not exercised [6].
- **CONFIRMED** response-publisher publishes every new event to `raw_tracking.v1` first, in parallel, and writes Mongo second. A failed publish or write means the next poll finds the same events new and republishes them with fresh IDs [14].
- **CONFIRMED** response-publisher then calls the status deriver over HTTP to get a `DELIVERED` or `IN_TRANSIT` bucket. That bucket sets the parcel's state and expiry. The response-publisher pod carries a deriver sidecar, image tag `prod-53270`, which no report mapped to a git sha [4][8][11].

## What a tracking update is
The page for this section is MPK 356614184, "What a Tracking Update Means: Events, Statuses and Delivery Outcomes".

Each stage has its own shape. The same word, "status", names a different type at each stage.

| Stage | Shape | Carries | Identity |
| --- | --- | --- | --- |
| Connector to tracking-core | gRPC `ConnectorResponse` | Carrier code and text, reported time as an offset string, location, depot, signatory, delivery window, `additionalData`, raw carrier response | None yet |
| Stored on the parcel | `ActiveParcel` event in Mongo | Same fields, minus the raw response | `id`, an ObjectId minted by response-publisher |
| `raw_tracking.v1` | JSON, camelCase, nulls omitted | Stored fields plus a `parcel` block and `rawData` on every event | Same `id`. No attributes, no ordering key |
| Mapped event | Stored on the parcel, never published | GFS code, text, `groupId`, `isDelivered`, `isVisibleToCustomer`, RAG exception status, `isUnmapped` | Copies the event `id` |
| Shipment status | `{ shipmentId, trackingStatusV2 }` | `date`, `text`, `code`, `groupId`, `isVisibleToCustomer`, then `eta` or `signatory` | None. Derived across parcels |
| Customer webhook body | HTTP POST from connect-hooks | `gfsId`, `carrierName`, consignment and parcel number, `carrierEventTime`, a display `status`, `text`, `isDelivered` | No event ID |
| Legacy scan | Patina shape on `scanners.consignments.V1` | The carrier's raw code in `carrCode`, `isDelivered` fixed false | No ID (`scanId` is 0) |

- **CONFIRMED** The raw event carries the carrier's code only. tracking-core stores its mapped result and publishes only the raw event, so each consumer maps again through its own sidecar [15][16].
- **CONFIRMED** The derived status never reaches the webhook or the Firebird side. Both come from the raw event [17].
- **CONFIRMED** The stored parcel has no ETA, no delivered flag, no POD reference, no signature image and no raw carrier response. The raw response is attached at publish time only [14][18].

## The topic spine
The chain from carrier scan to customer is choreography. A synchronous HTTP call from tracking-core to the deriver is the only edge outside a topic.

```orient-flow
{ "v": 1, "preset": "data-flow", "title": "Tracking, carrier scan to customer",
  "nodes": [
    { "id": "ship", "label": "shipments.v2.identified", "sub": "17 subscriptions", "kind": "topic" },
    { "id": "tc", "label": "tracking-core", "sub": "active-parcels, batch lease", "kind": "service", "tone": "accent" },
    { "id": "con", "label": "Carrier connectors", "sub": "pull batches, call carriers", "kind": "service" },
    { "id": "oth", "label": "Webhook, files, manual", "sub": "three more publishers", "kind": "external" },
    { "id": "raw", "label": "raw_tracking.v1", "sub": "carrier code only, no order key", "kind": "topic" },
    { "id": "der", "label": "Status deriver", "sub": "window loop, expired_window", "kind": "service" },
    { "id": "st", "label": "shipment_tracking_status.v2", "sub": "ordered by shipmentId", "kind": "topic" },
    { "id": "ex", "label": "shipment_exception_status", "sub": "red, amber, green", "kind": "topic" },
    { "id": "cc", "label": "CCIS and ICIS", "sub": "customer-visible stores", "kind": "service" },
    { "id": "hk", "label": "connect-hooks", "sub": "re-maps the raw event", "kind": "service" },
    { "id": "cu", "label": "Customer webhook", "sub": "no retry", "kind": "external" }
  ],
  "edges": [
    { "from": "ship", "to": "tc", "label": "parcel to track", "style": "dashed" },
    { "from": "tc", "to": "con", "label": "batch of due parcels" },
    { "from": "con", "to": "tc", "label": "carrier results" },
    { "from": "tc", "to": "raw", "label": "one message per new event", "style": "dashed" },
    { "from": "tc", "to": "der", "label": "HTTP: DELIVERED or IN_TRANSIT" },
    { "from": "oth", "to": "raw", "label": "scans from other sources", "style": "dashed" },
    { "from": "raw", "to": "der", "label": "every scan", "style": "dashed" },
    { "from": "der", "to": "st", "label": "after a 60 s window", "style": "dashed" },
    { "from": "der", "to": "ex", "label": "exception status", "style": "dashed" },
    { "from": "st", "to": "cc", "label": "customer-visible only", "style": "dashed" },
    { "from": "raw", "to": "hk", "label": "every scan", "style": "dashed" },
    { "from": "hk", "to": "cu", "label": "HTTP POST" }
  ] }
```

- **CONFIRMED** The deriver holds events per shipment in Mongo, closes a sliding window with a timer, and publishes `expired_window`. Three of its own subscriptions on that topic publish the final statuses [19].
- **CONFIRMED** Terraform subscriptions share these defaults unless a row says otherwise. They pull, with a 10 s acknowledge deadline. After 10 attempts a message goes to `dead-letters.v1`. Retry backoff runs 10 s to 600 s and ordering is off. The first Terraform read is 15 months old [20]. The later read at `35b545ce` found the same defaults [30].
- **CONFIRMED** `raw_tracking.v1` has four publishers. They are tracking-core, the Royal Mail webhook, `tracking-file-processor` and `shipment-update-service` (manual mark as delivered) [14][21].

Compact topic table. The first catalogue of 41 topics is in [[Handovers/2026-11-09-merak-replacement-pages.tracking-topic-catalogue]]. Prod Terraform creates 70 topics, and the full list with a verdict for each is in [[Handovers/2026-11-09-merak-replacement-pages.topic-usage-map]]. Volumes are Datadog handled counts, 2026-10-23 to 2026-11-07 UTC [22].

| Topic | Publisher | Subscribers | Key fields | Ordering key | Dead letter | Volume | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `shipments.v2.identified` | shipment-identity-service | 17 subscriptions (tracking-core, deriver, CCIS, ICIS, claims, gfs-pod and others), 2 webhook push subscriptions | `shipmentId`, `shipmentIdV2`, consignment, parcels | none | pull: default. Push: none | about 1.59M | CONFIRMED |
| `raw_tracking.v1` | tracking-core, Royal Mail webhook, file processor, `shipment-update-service` | 15 subscriptions in the prod project: 8 with a running consumer (status deriver, connect-hooks, CCIS, ICIS, claims-service, `shipment-update-service`, `gfs-pod-service`, ccp-api), 1 that runs but drops every event (Kubernetes tracking-patina-service), 1 Dataflow job (`patina-service-2`, state UNKNOWN), 1 BigQuery sink, 4 with no running workload. One more BigQuery sink is in the warehouse project | `id`, dates, `statusCode`, `statusDescription`, `parcel{}`, `rawData` | none | default | about 6.29M | CONFIRMED, except the Dataflow job [31] |
| `expired_window` | deriver | deriver, 3 subscriptions | `shipmentId` | none | default | about 4.08M | CONFIRMED |
| `shipment_tracking_status.v2` | deriver | CCIS (filter `CUSTOMER_VISIBLE`), reporting-ingestion | `shipmentId`, `trackingStatusV2`; attributes `visibilityGroup`, `groupId` | `shipmentId` | default | about 4.08M | CONFIRMED |
| `shipment_tracking_status` (v1, obsolete) | deriver | ICIS and `shipment-update-service` read it. CCIS and reporting-ingestion have a subscription but no live reader (CCIS: STATED by the manifest env var, its code at the head commit reads only the v2 variable) | same, minus visibility | none | default | about 4.08M | CONFIRMED for ICIS and shipment-update-service, M for CCIS |
| `shipment_exception_status` | deriver | CCIS, ICIS, reporting | `shipmentId`, RAG `exceptionStatus` | none | default | about 4.08M | CONFIRMED |
| `tracking_configuration_notifications.v1` | tracking-configuration-distribution-service | mapper sidecars | `{ type: "config_updated" }` | none | default | not measured | Wiring CONFIRMED, payload STATED |
| `unmapped-tracking.v1` | CCIS mapper sidecar, the only one in the prod manifests read | `unmapped-scan-recorder` | carrier, code, description, `seenAt` | none | default | 11,622 | CONFIRMED |
| `file_tracking.v1` | `file-ingestion-ftp-proxy` | `tracking-file-processor` | one GCS pointer per file | none | default | not measured | Wiring CONFIRMED, payload STATED |
| Evri interim topic | Evri webhook | the same service, by push | the carrier's body, headers redacted | none | after 5 attempts | about 563k received, 0 to `raw_tracking.v1` | CONFIRMED setting, count STATED |
| `scanners.consignments.V1` (project `gfs-ecm-staging`) | `patina-service-2`, per its README | the on-prem Scan Injector | consignment, parcels, states with `carrCode` | none | not read | about 4.51M | Flow STATED, writer in prod UNKNOWN |
| `tracking.v1`, `legacy_tracking.v1`, `parcel-eta-update`, `warehouse-*` | none running | none | n/a | n/a | n/a | 0 | Dormant, CONFIRMED |

## The status model
- **CONFIRMED** No canonical status exists. At least six types exist, one per layer: the carrier's code, the mapped event, the shipment status, the RAG exception status, tracking-core's parcel bucket and the Firebird integer. The webhook adds a seventh, a display string [18].
- **CONFIRMED** `groupId` is a free string, set by a spreadsheet in Google Cloud Storage that the tracking-configuration-distribution-service parses and pushes to the mapper sidecars. Its columns include `groupId`, `trackingIsDelivered`, `customerIsVisible` and `exceptionStatus` [23].
- **CONFIRMED** The names in use are `DATA_ONLY`, `IN_TRANSIT`, `DELIVERED`, `PARTIALLY_DELIVERED`, `OUT_FOR_DELIVERY`, `ATTEMPTED`, `HELD_AT_BRANCH`, `AWAITING_CUSTOMER_COLLECTION` and `RETURNED`. The first four have a code path. The CCIS validator names the rest, and `OTHER` is a query bucket only [24][25].
- **CONFIRMED** The deriver synthesises `PARTIALLY_DELIVERED` and never takes it from a carrier. The mapper defaults any unmapped code to `IN_TRANSIT`, visible to customers [25].
- **UNKNOWN** Nothing enforces the list: `VALID_GROUP_IDS` is read only when set, and no prod manifest sets it. The prod spreadsheet, its codes and the number of mapped codes are not read.
- **CONFIRMED** tracking-core's bucket is `DELIVERED` when `groupId` equals `DELIVERED`, and `IN_TRANSIT` otherwise. Delivered also has a second source, the mapped `isDelivered` boolean. Nothing asserts they agree [11][26].
- **CONFIRMED** No topic or type exists for delivered, out for delivery, POD ready or customer notification. They are `groupId` values, or absent. Failed delivery is `ATTEMPTED` with no reason field. Lost is not modelled [26].
- **CONFIRMED** The red, amber, green (RAG) exception status has its own topic. The deriver publishes it on every window expiry, not only on change [26].

## Weaknesses
- **CONFIRMED** Publish before store. A crash between the two republishes events under new IDs, and downstream stores key on `id` [14].
- **CONFIRMED** Each publisher mints its own ObjectId. The same scan from a connector and a webhook lands twice. The Royal Mail webhook discards the carrier's event ID, which survives only in `additionalData.EventId` [14][27].
- **CONFIRMED** No ordering key on `raw_tracking.v1`, and one poll's events publish in parallel. Only the v2 status topic is ordered [14][21].
- **CONFIRMED** The deriver silently drops a scan for a shipment it has not stored. The Royal Mail webhook parks early scans (about 146k of 343k), and the file processor records an error row [19][27].
- **CONFIRMED** The webhook is lossy and fire-and-forget. It folds `ATTEMPTED`, `HELD_AT_BRANCH` and `PARTIALLY_DELIVERED` into `IN TRANSIT`, and `carrierEventTime` holds the received time. A failed POST is logged and acknowledged, with no retry [17].
- **CONFIRMED** The synthetic `GFS_DELIVERED_EVENT` has no `id` and no `parcel.company`, so `connect-hooks` drops it [28].
- **CONFIRMED** Unmapped codes look mapped, and only CCIS reports them. About 11.6k reached BigQuery in the window [25][22].
- **ASSESSED** A deriver outage makes the status call throw after the publish. The failure behaviour is inferred from code [11].

## What a replacement must preserve
These are facts the code shows, not a recommendation. The guardrail lines are in [[Systems/ecm/architecture]].
- The raw event shape is the de facto public contract. Consumers depend on `id`, `parcel.shipmentId`, `parcel.parcelNumber` and `parcel.company` (G4).
- The derived bucket and the `groupId` strings, because tracking-core's lifecycle and every consumer read them (G9).
- The publish-before-store order is a duplicate risk. A replacement picks an idempotency key or accepts duplicates (G10).
- The synchronous deriver call sets parcel state and expiry, so the lifecycle depends on it (G11).
- The id-less manual delivered event is an input that downstream code half-handles (G12).
- The group-to-display mapping and the raw-code-to-Firebird path are both contracts (G13).
- Polling is per carrier and state, with one interval scalar. Expiry refreshes on each new event (G14).

## Unknown
Detail and the full list are in [[Systems/ecm/known-context]].
- **UNKNOWN** Prod etcd values, the effective expiry, and whether prod runs the cloned source. Prod image `prod-44693` is unmapped, and several prod env vars have no binding in this clone.
- **UNKNOWN** Who writes legacy scans in prod. The Kubernetes patina service runs but drops every event (`CARRIERS=NONE`, **CONFIRMED** in the manifest and the handler [31]), and the Dataflow job's source was not found [29].
- **UNKNOWN** Live Pub/Sub state. Every topic and subscription fact comes from Terraform and manifests.

## Research copies
- [[Handovers/2026-11-09-merak-replacement-pages.tracking-core-findings]]: polling, lease, lifecycle, errors.
- [[Handovers/2026-11-09-merak-replacement-pages.tracking-topic-catalogue]]: the first catalogue of 41 topics, the chain, the `raw_tracking.v1` schema, weaknesses, gaps.
- [[Handovers/2026-11-09-merak-replacement-pages.tracking-model-findings]]: event shapes per stage, status model, terminal states, mismatches.
- [[Handovers/2026-11-09-merak-replacement-pages.topic-usage-map]] and [[Handovers/2026-11-09-merak-replacement-pages.topic-datadog-usage]]: all 70 prod Terraform topics with verdicts, and their Datadog counters. The later reading wherever it differs from the catalogue.
- [[Handovers/2026-11-09-merak-replacement-pages.page7-ecm-topics]]: the published topic page (MPK 356155424).
- [[Handovers/2026-11-09-merak-replacement-pages.page8-tracking-chasing]]: the published polling page (MPK 356614148).
- [[Handovers/2026-11-09-merak-replacement-pages.page9-tracking-model]]: the published event and status page (MPK 356614184).

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "doc", "ref": "Handovers/2026-11-09-merak-replacement-pages.tracking-core-findings.md, ...tracking-topic-catalogue.md and ...tracking-model-findings.md (research copies, 2026-11-10)" },
  { "id": 2, "kind": "code", "ref": "src/Gfs.Fenghuang.Tracking.Core.Shared/DataAccess/ActiveParcelRepository.cs@c081108:L104-128", "note": "the lease: FindOneAndUpdate, oldest lastRequestedAt first. Re-read 2026-11-10" },
  { "id": 3, "kind": "code", "ref": "src/Gfs.Fenghuang.Tracking.Core.Shared/DataAccess/ActiveParcelDomain.cs@c081108:L149", "note": "passes dataIn.TargetPollingMinutes to the lease. Re-read 2026-11-10" },
  { "id": 4, "kind": "code", "ref": "deploy/k8s/fenghuang/tracking/tracking-core.yaml@a317dc0", "note": "prod manifest: replicas, System__Mode, ExpiryDays env var, ShouldPublishToLegacy=false, sidecar images" },
  { "id": 5, "kind": "code", "ref": "src/Gfs.Fenghuang.Tracking.Core.ConsignmentManager/Subscriber/MessageHandler/ConsignmentHandler.cs@c081108:L51-130", "note": "creation, skip rules, initial expiry" },
  { "id": 6, "kind": "code", "ref": "src/Gfs.Fenghuang.Tracking.Core.Frameworks.Connector/Tracking/Batch/BatchRequestManager.cs@c081108:L46-52", "note": "loop sleeps. The per-key worker and request handler are in the same project" },
  { "id": 7, "kind": "code", "ref": "src/Gfs.Fenghuang.Tracking.Core.ConsignmentManager/Subscriber/MessageHandler/ConsignmentHandler.cs@c081108:L111-130", "note": "UPDATE for an existing parcel returns before the state update" },
  { "id": 8, "kind": "code", "ref": "src/Gfs.Fenghuang.Tracking.Core.Shared/TrackingStatus/TrackingStatusManager.cs@c081108:L33-69", "note": "status call, state update, expiry refresh. Re-read 2026-11-10" },
  { "id": 9, "kind": "code", "ref": "src/Gfs.Fenghuang.Tracking.Core.Shared/DataAccess/ActiveParcelRepository.cs@c081108:L237-245", "note": "TTL index on expiryDate. The expiryDateV2 index is commented out. Re-read 2026-11-10" },
  { "id": 10, "kind": "code", "ref": "src/Gfs.Fenghuang.Tracking.Core.Shared/Settings/ActiveParcelConfiguration.cs@c081108", "note": "ExpiryDays read from the Connectors section, with a default fallback" },
  { "id": 11, "kind": "code", "ref": "src/Gfs.Fenghuang.Tracking.Core.Shared/TrackingStatus/RemoteTrackingStatusV2Getter.cs@c081108:L63", "note": "bucket is DELIVERED when groupId equals DELIVERED. Re-read 2026-11-10" },
  { "id": 12, "kind": "code", "ref": "src/Gfs.Fenghuang.Tracking.Core.ResponsePublisher/Services/V1/ErrorResponseHandler/ErrorResponseHandler.cs@c081108:L26-30", "note": "only CredentialsError is acted on" },
  { "id": 13, "kind": "doc", "ref": "Confluence MPK 353697880 Polling Connectors (v11), source of the carrier IDs 10 and 19 as DPD and DPD Local" },
  { "id": 14, "kind": "code", "ref": "src/Gfs.Fenghuang.Tracking.Core.ResponsePublisher/Services/V1/Handlers/ConnectorResponseHandler.cs@c081108:L103-131", "note": "publish in parallel, then Mongo writes. Re-read 2026-11-10" },
  { "id": 15, "kind": "code", "ref": "src/Gfs.Fenghuang.Tracking.Core.Shared/Publishers/Models.cs@c081108:L14-43", "note": "raw_tracking.v1 message model" },
  { "id": 16, "kind": "code", "ref": "src/pubsub/tracking-mapper.js@a3dc446:L7-42", "note": "deriver's own mapper call and mapped-event shape" },
  { "id": 17, "kind": "code", "ref": "apps/connect-hooks/src/tracking-handler.js@6c6d527:L58-135", "note": "webhook body, re-map of the raw event, no retry" },
  { "id": 18, "kind": "code", "ref": "src/Gfs.Fenghuang.Tracking.Core.Shared/Models/ActiveParcel.cs@c081108:L7-119", "note": "stored parcel model: what it holds and lacks" },
  { "id": 19, "kind": "code", "ref": "src/pubsub/mongo/shipments-collection.js@a3dc446", "note": "deriver store, upsert false, so a scan for an unknown shipment is dropped" },
  { "id": 20, "kind": "code", "ref": "modules/subscription/main.tf@e3c6dd9", "note": "subscription defaults. Terraform from 2025-07-30 may lag the deployed state" },
  { "id": 21, "kind": "code", "ref": "src/api/routes/mark-as-delivered.js@ccec388:L43-56", "note": "manual delivered event, no id and no company" },
  { "id": 22, "kind": "log", "ref": "sum:gfs.<service>.pubsub.<x>.handled_messages{*}.as_count(), 2026-10-23 00:00 to 2026-11-07 00:00 UTC (Datadog)" },
  { "id": 23, "kind": "code", "ref": "src/configuration-providers/excel-parser.js@bbd5e74:L26-57", "note": "spreadsheet columns and schema, tracking-configuration-distribution-service" },
  { "id": 24, "kind": "code", "ref": "src/routes/consignment-schemas.ts@b2af452:L16-27", "note": "CCIS accepted groupId filter values" },
  { "id": 25, "kind": "code", "ref": "src/config.js@44cfbf2:L94-106", "note": "tracking-mapper default group IN_TRANSIT for an unmapped code" },
  { "id": 26, "kind": "code", "ref": "src/derive-shipment-tracking-status-v2.js@a3dc446:L19-130", "note": "group precedence, PARTIALLY_DELIVERED, delivered handling" },
  { "id": 27, "kind": "code", "ref": "handler/src/services/tracking.service.ts@3c880bf", "note": "Royal Mail webhook: parks events, mints its own id, publishes before save" },
  { "id": 28, "kind": "code", "ref": "apps/connect-hooks/src/tracking-handler.js@6c6d527:L34-46", "note": "events with no company are dropped" },
  { "id": 29, "kind": "doc", "ref": "tracking-patina-service.yaml@a317dc0:L68-82 (CARRIERS=NONE); patina-service-2 ReadMe.md; modules/tracking-dataflow-patina-service/main.tf@e3c6dd9 (staging topic comment)" },
  { "id": 30, "kind": "doc", "ref": "Handovers/2026-11-09-merak-replacement-pages.topic-usage-map.md (research copy, 2026-11-10): prod Terraform master 35b545ce, prod manifests a317dc0, 70 topics and 145 subscriptions" },
  { "id": 31, "kind": "doc", "ref": "Handovers/2026-11-09-merak-replacement-pages.topic-usage-map.md, raw_tracking.v1 and Kubernetes tracking-patina-service rows; tracking-patina-service.yaml@a317dc0 and the handler at 8edfb3e. Datadog counters in ...topic-datadog-usage.md" }
] }
```
