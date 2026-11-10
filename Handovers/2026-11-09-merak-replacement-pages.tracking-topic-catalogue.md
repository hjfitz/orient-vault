---
tags: [handover, research-copy, ecm, tracking]
date: 2026-11-10
tldr: "Research copy: the 41-topic ECM tracking catalogue, the choreography chain from scan to customer, the raw_tracking.v1 schema and known weaknesses (2026-11-10)."
status: research-copy
---
This is a research copy of the findings file `tracking-events-findings.md`, kept in the vault so it can be found and cited. The synthesis is [[Systems/ecm/tracking]]. Where the two differ, the synthesis note is the later reading. Nothing was edited in Confluence, a repo or Firebird.

# ECM tracking events: topics, chain, schemas, weaknesses

Researched 2026-11-10, read-only. Window for volumes: 2026-10-23 00:00 to 2026-11-07 00:00 UTC (the canonical 15 days). Nothing was edited in Confluence, the vault or any repo.

## 0. Headline

**The chain from carrier scan to customer is choreography through Pub/Sub topics. There is no central orchestrator.** Each service subscribes to a topic, does its own job and publishes or writes its own result. The only "wiring" that is central is Terraform: one root `main.tf` in `gfs-ecm-prod-uk1` creates every topic and subscription and passes topic names between modules. That is deploy-time wiring, not run-time control.

Three things look like orchestration but are narrower than that:

1. **tracking-core controls polling only.** `consignment-manager` fills `active-parcels` from `shipments.v2.identified`; `batch-creator` leases due parcels to connectors over gRPC; `response-publisher` publishes `raw_tracking.v1`. It owns the carrier-polling loop. It does not consume or direct anything after `raw_tracking.v1`. (Scheduler detail is another agent's job.)
2. **One synchronous edge exists outside topics.** tracking-core's response-publisher POSTs each parcel's mapped events to the status deriver's HTTP API (`/api/v2/shipmentTrackingStatus/derive`) to decide the bucket DELIVERED or IN_TRANSIT. That bucket sets the parcel's poll state and expiry. So polling lifecycle depends on a request/response call into the deriver, which is a hidden coupling between the origin and a downstream consumer.
3. **The status deriver runs a self-loop.** It holds events per shipment in Mongo, closes a sliding window with a timer, publishes `expired_window`, and three of its own subscriptions on that topic publish the final statuses. That is a private pipeline inside one service, not a system orchestrator.

Counts: section 1 names 41 topics (counting the five `fb.*` replication topics as one row). 12 sit upstream, from Firebird to `shipments.v2.identified` (1.1). 21 sit on the tracking spine (1.2), of which 5 are dormant or dead: `tracking.v1`, `legacy_tracking.v1`, `parcel-eta-update` and the two `warehouse-*` topics. 8 are adjacent topics the stores subscribe to (1.3). `raw_tracking.v1` alone has 15 subscriptions and `shipments.v2.identified` has 17 plus 2 webhook push subscriptions. Terraform totals are the vault's: 70 topics and 144 subscriptions in `gfs-ecm-prod-uk1` (not recounted).

Status key: CONFIRMED = read in code, Terraform or manifest by me this session. STATED = a document or comment says it, not independently read. UNKNOWN = no source settles it.

## 1. Topic and subscription table

Subscription defaults apply to every Terraform subscription unless a row says otherwise. CONFIRMED in `modules/subscription/main.tf` (ADO `GFS Cloud Infrastructure/gfs-ecm-prod-uk1`, master, read 2026-11-10): pull, `ack_deadline_seconds = 10`, no expiry, dead-letter to `dead-letters.v1` after 10 delivery attempts, retry backoff 10 s to 600 s, name `<topic>.<suffix>`, optional `filter` and `enable_message_ordering` (default off).

Volume column: "handled" is the Datadog `sum:gfs.<service>.pubsub.<x>.handled_messages{*}.as_count()` for the window, summed by me via `execute_code`. It counts messages a subscriber handled, so it approximates publish volume where one subscriber exists. Pub/Sub's own metrics are not collected for the ECM project (stated on the MPK Journey page and the ecm-development catalogue).

### 1.1 Upstream: Firebird to identified shipment

| Topic | Publisher(s) | Subscriber(s) | Key fields | Order key | Dedupe | DLQ / retry | Volume | Evidence | Status |
|---|---|---|---|---|---|---|---|---|---|
| `fb.shipments.v1` (plus `fb.ship_pieces.v1`, `fb.ship_pieces_hist.v1`, `fb.shipment_extra.v1`, `fb.scan_access_data.v1`) | On-prem Firebird Transfer Service (ext); Slipway for Amazon UK (pilot) | `gfs-modernizer` | `{event_type, data.SHIPMENTS{all columns}}` | no | none read | default (modernizer module) | not measured; transfer shipment median lag 7.5 s (vault) | ADO main.tf `module "transfer_service"`, `module "modernizer"` (topic wiring). Payload and publisher from vault/MPK | Wiring CONFIRMED; publishers and payload STATED |
| `windowed-shipments-parcels` | `gfs-modernizer` (internal window) | `gfs-modernizer` | unknown | unknown | unknown | unknown | not measured | ADO main.tf `module "modernizer"` input `windowed_shipment_parcels_topic` | Declared CONFIRMED; role STATED (catalogue, vault: sliding 180 s) |
| `shipments.v2` | `gfs-modernizer` | `shipment-identity-service` | `consignmentNumber`, `carrier{id,idV2}`, `customer{company}`, `declaredDespatchDate`, `parcels[]`, `_legacy` | no | n/a | default | ~1.59M messages handled by SIS-side consumers (derived, see `.identified`) | ADO main.tf `module "shipment_identity_service"` (`shipment_input_topic = module.modernizer.shipment_output_topic.name`); `modules/shipment-identity-service/main.tf` | CONFIRMED wiring; payload STATED |
| `shipment-number-updates` | `gfs-modernizer` | `shipment-identity-service` | shipment-number update | no | n/a | default | n/a | same | CONFIRMED wiring |
| `tracking-events.v2`, `customers.v2` | `gfs-modernizer` | none | n/a | n/a | n/a | n/a | n/a | ADO main.tf `module "modernizer"` creates `tracking_output_topic = "tracking-events.v2"`; ecm-development catalogue says no subscription | Created CONFIRMED; no subscriber STATED |
| `shipments.v2.identified` | `shipment-identity-service` (`gfs-ecm/shipment-identity-service`) | 17 subscriptions in `gfs-ecm-prod-uk1`: tracking-core (`fenghuang.tracking-core`), gfs-pod, CCIS, ICIS, claims-service, CCDIS, shipment-update-service, status deriver, tracking-file-processor, manage-queries-proxy, sofia-query-categorisation, reporting-ingestion, customer-care-portal (ccp-api), tracking-patina-service (K8s), modernizer (v2 loop), data-warehouse (no consumer), longmen (no in-cluster consumer). Plus 2 push subscriptions in `gfs-selector-rest-prod-uk1`: Royal Mail and Evri webhooks | spread of `shipments.v2` plus `shipmentId` (counter), `shipmentIdV2` (md5 of carrier idV2 + consignment + despatch date) | no | consumers key their own stores on `shipmentId` | default for in-project; webhook push subs: ack 300 s, retry 10 to 600 s, no filter, no DLQ | **~1.59M handled** (CCIS 1,585,591; ICIS 1,586,144; SUS 1,585,970; deriver 1,585,574). Re-announcements 57.5% (vault, not re-run). New IDs ~675k (vault) | ADO main.tf `module "shipment_identity_service"` outputs `shipment_output_topic`, consumed by 16 other modules; `iac/modules/tracking-webhook/pubsub.tf` and RM `iac/projects/*/pubsub.tf` (push, no filter, no dead_letter_policy) | CONFIRMED |
| `shipment-number-updates.identified` | `shipment-identity-service` | CCIS, ICIS, reporting-ingestion | shipment plus new consignment number | no | n/a | default | 3,786 handled (CCIS, ICIS, reporting) | main.tf; Datadog | CONFIRMED |

### 1.2 Tracking spine: carrier scan to customer

| Topic | Publisher(s) | Subscriber(s) | Key fields | Order key | Dedupe | DLQ / retry | Volume | Evidence | Status |
|---|---|---|---|---|---|---|---|---|---|
| **`raw_tracking.v1`** | (1) tracking-core `response-publisher` (.NET) for all polling connectors; (2) Royal Mail webhook (standalone repo); (3) `tracking-file-processor`; (4) `shipment-update-service` mark-as-delivered (synthetic `GFS_DELIVERED_EVENT`, about 8 a week in Aug per ecm-development). Evri webhook and InPost webhook hold publish permission off in prod | 15 subscriptions in main.tf. Running: connect-hooks, CCIS, ICIS, claims-service, customer-care-portal (ccp-api), shipment-update-service, status deriver, gfs-pod, tracking-patina-service K8s (drops all), patina-service-2 Dataflow, a BigQuery rollback subscription (no code consumer). Not running: standalone tracking-mapper (replicas 0), parcel-eta-service (replicas 0), data-warehouse (manifest commented out), longmen (no in-cluster workload) | see section 3 | **no** (none of the four publishers sets one) | pre-publish: tracking-core on date plus code; RM webhook via `shipmentTrackingEventExists`. Consumers: key on event `id` (deriver `trackingEvents.<parcel>.<id>`, upsert false) | default (10 attempts then DLQ) | **~6.29M** (every full consumer handled 6,294,6xx to 6,297,029; gfs-pod 7,880,359 = shipments 1.59M + raw 6.29M). By source: polling ~6.01M, RM webhook ~218k, files ~62k (as given) | ADO tracking-core@c0811087 `Publishers/EventPublisher.cs`, `ConnectorResponseHandler.cs`; RM@3c880bf `handler/src/services/tracking.service.ts`; ADO tracking-file-processor `src/publisher.js`; SUS@ccec388 `src/api/routes/mark-as-delivered.js`, `src/api/publisher.js`; Datadog; main.tf modules | CONFIRMED |
| `file_tracking.v1` | `file-ingestion-ftp-proxy` (CronJob, every 20 min, vault) | `tracking-file-processor` | one message per collected file (GCS pointer) | no | none read | default | not measured; inferred a few thousand (tracking_file_processor handled 1,589,459, of which ~1.585M is `.identified`) | main.tf `module "tracking-file-ingestion-ftp-proxy"`, `...-processor`; Datadog | Wiring CONFIRMED; payload STATED; volume inferred |
| Evri interim topic `<env>-interim-tracking-topic` plus `...-dead-letter-topic` (in `gfs-selector-rest-prod-uk1`) | Evri webhook Cloud Run (publishes raw carrier request, headers redacted) | same service's `/events/interimTracking` (push) | `{version, carrierIdV2, receivedDate, requestId, payload (carrier's own body), request{headers,method,path,query}}` | no | no | push, ack 300 s, retry 10 to 600 s, **DLQ after 5 attempts**, DLQ has a holding subscription nothing pulls | ~563k Evri events received (vault, not re-run); 0 reach `raw_tracking.v1` | tracking-webhooks@9777dd4 `iac/modules/tracking-webhook/interimpubsub.tf`, `packages/tracking-webhook-core/src/types/interim-tracking.ts`, `iac/projects/tracking-webhook-evri/tfvars/prod.tfvars` (`pubsub_tracking_publish_enabled=false`, `pubsub_interim_tracking_enabled=true`) | CONFIRMED |
| `tracking_configuration_notifications.v1` | `tracking-configuration-distribution-service` | mapper sidecars in tracking-core, deriver, SUS, CCIS, ICIS, claims, connect-hooks; data-warehouse, longmen (no consumer) | `{type:"config_updated"}`, a trigger to re-pull mapping config over HTTP | no | n/a | default | n/a | main.tf `module "tracking_configuration_distrubution_service"`; ecm-development catalogue | Wiring CONFIRMED; payload STATED |
| `unmapped-tracking.v1` | the mapper sidecar in CCIS (topic created by the CCIS module) | `unmapped-scan-recorder` (2 replicas) to BigQuery | `{carrier, carrierCode, carrierDescription, seenAt}` | no | none | default | **11,622 handled** (matches the ~11.6k) | main.tf `module "customer_consignment_information_service"` (`unmapped_tracking_output_topic`), `module "unmapped-scan-data"`; Datadog `unmapped_scan_recorder` | CONFIRMED volume and wiring; payload STATED |
| `expired_window` | status deriver (window timer) | status deriver, three subscriptions (`shipment-exception-status`, `shipment-tracking-status`, `shipment-tracking-status-v2`) | `{shipmentId}` | no | none | default | ~4.077M messages (each of the three handled 4,077,022 to 4,077,026) | deriver@a3dc446 `src/pubsub/window-processor.js`, `src/startup.js`; ADO `modules/shipment-tracking-status-deriver/main.tf` | CONFIRMED |
| `shipment_tracking_status.v2` | status deriver | CCIS (filter `attributes.visibilityGroup="CUSTOMER_VISIBLE"`, ordering enabled), reporting-ingestion, longmen (same filter and ordering, no consumer) | `{shipmentId, trackingStatusV2{code,text,groupId,eta}}`; attributes `visibilityGroup` (`ALL`/`CUSTOMER_VISIBLE`), `groupId` | **yes: `orderingKey = shipmentId`** | none | default | **~4.077M** (CCIS 4,077,032; reporting 4,077,031) | deriver `src/pubsub/publisher.js` (`publishShipmentTrackingStatusV2`); ADO `modules/longmen-connection/main.tf` (filter, `enable_message_ordering = true`); CCIS module (filter at `customer-consignment-information-service/main.tf:127` in the July 2025 local clone, ordering true) | CONFIRMED |
| `shipment_tracking_status` (obsolete v1) | status deriver | ICIS, shipment-update-service, CCIS, reporting-ingestion (v1 sub created, not wired) | `{shipmentId, trackingStatusV2}` | no | none | default | ~4.077M (ICIS 4,077,200; SUS 4,077,143) | ADO deriver module comment "obsolete topic, use v2 instead"; Datadog | CONFIRMED |
| `shipment_exception_status` | status deriver | CCIS, ICIS, reporting-ingestion | `{shipmentId, exceptionStatus}` (RED/AMBER/GREEN) | no | none | default | ~4.077M | deriver `publisher.js`; Datadog | CONFIRMED |
| `tracking.v1` (mapped tracking) | standalone `tracking-mapper` (**replicas 0**) | `tracking-core` consignment-manager (subscription wired, vault and catalogue say no consuming code) | mapped tracking event | no | n/a | default | 0 (producer silent; catalogue confirmed via Datadog 2026-08-10) | local `prod-uk1-primary-cluster@4d4b6cb` `tracking-mapper.yaml:7` (`replicas: 0`); `tracking-core.yaml:148` (`tracking_subscription` wired); ecm-development catalogue | Producer-off CONFIRMED; "no consumer code" STATED; not re-measured |
| `legacy_tracking.v1` | tracking-core (`LegacyEventPublisher`; **off**, `ShouldPublishToLegacy=false` per vault) | none | legacy per-carrier event | no | n/a | n/a | 0 | tracking-core `fenghuang-scanning-core/main.tf` topic created; `ConnectorResponseHandler.cs` calls `_legacyEventPublisher.PublishAsync`; flag value STATED (vault) | Topic CONFIRMED; off-flag STATED |
| `scanners.consignments.V1` (in **`gfs-ecm-staging`**, not prod) | `patina-service-2` (Go, Apache Beam on Dataflow) | the on-prem Scan Injector, which calls Firebird `SET_PARCEL_HIST` and `SET_SHIPMENT_HIST` | one consignment per message: `{shipType, trackBy, consNo, carrier, parcels[{parcelNo, states[{carrCode, scanDate, scanText, signBy, ...}]}]}`; attributes `ScannerUid`, `Carrier` | no | none | not read | Injector receives ~4.51M (MPK Journey page); not re-measured | ADO patina-service-2 `ReadMe.md` ("raw_tracking.v1 to Patina-2 to scanners.consignments.V1"); ADO `modules/tracking-dataflow-patina-service/main.tf` (comment: output topic is `projects/gfs-ecm-staging/topics/scanners.consignments.V1`, publisher IAM "granted manually"); ecm-simulator `scanners-consignments-v1.ts` | Flow CONFIRMED from README and Terraform comment; the staging topic's own Terraform and subscription not seen |
| `legacy_tracking_events` (prod project) | `patina-service-2` test output | a BigQuery subscription (`...-tracking-dataflow-patina-service-bigquery`) and a test subscription | same as above | no | none | default | not measured | ADO `modules/tracking-dataflow-patina-service/main.tf` (`output_pubsub.topic = "legacy_tracking_events"`) | CONFIRMED; purpose STATED by comment |
| `raw_tracking.v1.tracking-dataflow-patina-service-bigquery` (a subscription, not a topic) | n/a | BigQuery table `patina.tracking_events_rollback` | full raw event, no topic schema | no | none | default | = raw volume | same module | CONFIRMED |
| `warehouse-tracking.v1`, `warehouse-shipment-events.v1` | data-warehouse service (manifest commented out) | BigQuery (schema'd AVRO topics) | `GFS_*` and `CARRIER_*` scan fields | no | n/a | n/a | 0 | ADO `modules/data-warehouse/main.tf`; local `data-warehouse/data-warehouse.yaml:53,115` commented replicas | Dormant, CONFIRMED |
| `parcel-eta-update` | `parcel-eta-service` (**replicas 0** since 2022) | CCIS, ICIS (not wired) | `{shipmentId, parcelNumber, from, to, scheduledDate}` | no | n/a | default | 0 | `parcel-eta-service.yaml:7`; repo `gfs-ecm/parcel-eta-service` marked dormant; catalogue | Dead, CONFIRMED |
| `invoiced_shipments_published.v1` | CCDIS | claims-service, CCIS, ICIS, SUS, reporting-ingestion, longmen (none) | `{shipmentId, shipmentIdV2, invoiceNumber, shipmentCost, ...}` | no | none | default | **633,190 handled** | ADO main.tf; Datadog | CONFIRMED |
| `invoices_published.v1`, `credit_notes_published.v1`, `invoice_charges_published.v1` | `legacy-invoice-translator` (.NET) | CCDIS, reporting-ingestion | invoice header plus GCS file URLs | no | none | default | invoice 1,453; credit notes 22 | ADO main.tf; Datadog | CONFIRMED volumes; payload STATED |

Customer delivery is not a topic. `connect-hooks` consumes `raw_tracking.v1.connect-hooks` and calls each customer's `hookUrl` over HTTPS (about 406k in the window, as given). CCIS, ICIS, Connect and the portals serve their stores over HTTP/GraphQL. The POD is fetched from carriers on read and is never published (vault, MPK Journey page; Terraform shows gfs-pod only subscribes).

### 1.3 Adjacent topics the consignment stores subscribe to

| Topic | Publisher | Subscribers | Volume (handled) | Status |
|---|---|---|---|---|
| `shipment-comments.v1` | gfs-modernizer | CCIS, ICIS, reporting | 91,873 | CONFIRMED wiring and count |
| `shipment-queries` | manage-queries-proxy | CCIS, ICIS, reporting, ccp-api | 30,956 | CONFIRMED |
| `shipment-collections.v1` | gfs-modernizer | ICIS, reporting | 32,232 | CONFIRMED |
| `parcel-claim-eligibility.v1` | claims-service | CCIS, ICIS | ~3.28M | CONFIRMED |
| `claims.v1` | claims-service | CCIS, ICIS, reporting | 21,592 | CONFIRMED |
| `marked-claimable.v1` | claims-service | CCIS | 5 | CONFIRMED |
| `gfs-tickets` (project `gfs-ecm`) | Seeker, GFS Manager | customer-care-portal | n/a | CONFIRMED wiring |
| `connect.hooks_usage.v1` | connect-hooks (dead code) | none | 0 | STATED (catalogue) |

`dead-letters.v1` is the DLQ for every default subscription. `gfs-deadletter-register` stores them and cannot replay (vault, STATED).

## 2. The chain in order, scan to customer

Each step names the consumer, what it reads, and what it emits. "Topic" means Pub/Sub, "HTTP" means a direct call.

1. **Shipment becomes known.** Firebird to Transfer Service (`fb.shipments.v1`) to `gfs-modernizer` (`shipments.v2`, 180 s window) to `shipment-identity-service` (`shipments.v2.identified`). Every later step depends on this. CONFIRMED wiring. (Internals are other pages' ground.)
2. **tracking-core learns what to track.** `consignment-manager` subscribes `shipments.v2.identified` and upserts `active-parcels`. Emits nothing to a topic. CONFIRMED (manifest, vault architecture).
3. **Source 1, polling.** A carrier connector asks `batch-creator` for a batch over gRPC, calls the carrier, returns results over gRPC to `response-publisher`. `response-publisher` dedupes on date plus code against stored events, maps through the sidecar, filters, then **publishes `raw_tracking.v1` first and persists second** (`Task.WhenAll(publishTasks)` before `UpsertTracking`). It then POSTs to the deriver's HTTP API for the DELIVERED/IN_TRANSIT bucket. CONFIRMED, tracking-core@c081108.
4. **Source 2, webhook.** The carrier POSTs. Royal Mail (live): auth, map, look the shipment up in the webhook's own Mongo copy (fed by a push subscription on `shipments.v2.identified`), then either **publish `raw_tracking.v1` and then save** the event, or save it to a retry collection when the shipment or parcel is not yet known. When a later `shipments.v2.identified` message arrives, `handleShipment` replays the parked events. Evri (shadow): publishes the raw request to its interim topic, replies 200, and a push subscription hands it back to itself; publish to `raw_tracking.v1` is off. CONFIRMED, RM@3c880bf and tracking-webhooks@9777dd4.
5. **Source 3, files.** `file-ingestion-ftp-proxy` announces a carrier file on `file_tracking.v1`. `tracking-file-processor` reads the file, matches each row to a shipment from its own copy of `shipments.v2.identified`, mints an event id (new ObjectId) and publishes `raw_tracking.v1` (plain JSON, no attributes, no ordering key). Rows that match no shipment throw `LineImportError` and go to an errored-parcels path. CONFIRMED (DX mapper and `publisher.js` read; the retry job's detail not read).
6. **Source 4, manual.** `shipment-update-service` mark-as-delivered writes Firebird through the legacy update service, then publishes a `GFS_DELIVERED_EVENT` per parcel to `raw_tracking.v1`. The event has no `id` and no `company` at SUS@ccec388. CONFIRMED.
7. **Fan-out of every scan.** Ten running consumers each take the full 6.29M: deriver, CCIS, ICIS, connect-hooks, claims-service, SUS, ccp-api, gfs-pod, patina K8s (which drops everything) and patina-service-2, plus a BigQuery rollback sink. (ccp-api and patina-service-2 are not in the Datadog handled set; they are in Terraform only.) Four more subscriptions are orphaned (section 1.2). CONFIRMED.
8. **Mapping happens in each consumer.** Each consumer calls its own tracking-mapper sidecar over HTTP, keyed by the raw carrier code, with config pushed through `tracking_configuration_notifications.v1`. Deriver example: `mapTrackingEvent` POSTs `{carrier, carrierV2, statusCode, statusDescription}` and gets `{text, code, groupId, exceptionStatus, isVisibleToCustomer}`. CONFIRMED (deriver, connect-hooks). An unmapped code becomes a message on `unmapped-tracking.v1` from the CCIS sidecar only (vault, STATED; topic wiring CONFIRMED).
9. **Derive status.** Deriver stores the mapped event under `trackingEvents.<parcelNumber>.<id>` with `upsert:false` (an event for a shipment the deriver has not seen is dropped without error), extends a sliding window (60 s per the vault, config not read), and a timer publishes `expired_window`. Three self-subscriptions turn that into `shipment_exception_status`, `shipment_tracking_status` (v1) and `shipment_tracking_status.v2` (ordered by `shipmentId`, two copies per shipment: `ALL` and `CUSTOMER_VISIBLE`). CONFIRMED.
10. **Customer-visible stores.** CCIS reads `raw_tracking.v1` plus `shipment_tracking_status.v2` (customer-visible only), plus exception, claims, comments and invoices. ICIS reads the v1 status topic. The customer portal, Connect API and staff tools query these over HTTP/GraphQL. CONFIRMED wiring; the read APIs are not part of the topic picture.
11. **Customer webhooks.** `connect-hooks` takes each raw event, drops it if `parcel.company` is missing or the company has no registration, maps via its sidecar (a throw here nacks), and POSTs `{gfsId, carrierName, consignmentNumber, parcelNumber, carrierEventTime, status, text, isDelivered}` to the customer's `hookUrl` with header `x-gfs-token`. A failed POST is logged and acked, with no retry. About 406k sent. CONFIRMED, connect@6c6d527 `apps/connect-hooks/src/tracking-handler.js`.
12. **Write-back to Firebird (parallel branch).** `patina-service-2` (Dataflow, session window per consignment) groups parcel scans into a consignment and publishes `scanners.consignments.V1` in the **staging** project; the on-prem Scan Injector calls `SET_PARCEL_HIST` and `SET_SHIPMENT_HIST`. The Kubernetes `tracking-patina-service` is present but off (`CARRIERS=NONE`, per ecm-simulator header comment citing `tracking-patina-service.yaml:80-81`). CONFIRMED flow; carrier list and Injector internals UNKNOWN (ADO variable group 141, not readable).
13. **POD.** On read, portal or Connect calls `gfs-pod-service`, which fetches from the carrier. gfs-pod subscribes to both `shipments.v2.identified` and `raw_tracking.v1` for its own cache (7.88M handled). No event is published. CONFIRMED subscription; read-path STATED.
14. **Invoice return.** Firebird billing to `legacy-invoice-translator` to `invoices_published.v1` to CCDIS to `invoiced_shipments_published.v1`, read by CCIS, ICIS, claims, SUS and reporting. CONFIRMED wiring.

### 2.1 Is there an orchestrator? Evidence

- **Terraform is the only central artefact.** `modules/fenghuang-scanning-core/main.tf` creates `raw_tracking.v1` and grants publish to one service account; every consumer module takes `module.fenghuang-scanning-core.raw_tracking_topic.name` and creates its own `<topic>.<suffix>` subscription. No module references a workflow engine, Cloud Workflows, Composer or a state-machine service (grep of the root `main.tf`, which lists all modules).
- **No consumer knows its upstream by name.** Each takes a subscription name from a ConfigMap (`tracking-core.yaml`, `connect-hooks.yaml:98`, `tracking-mapper.yaml:51`).
- **No saga or correlation record spans the chain.** The only cross-step keys are `shipmentId`, `parcelNumber` and the event `id`, each stored separately by each consumer (deriver Mongo `trackingEvents.<parcel>.<id>`; webhook Mongo shipments and retries; SUS and CCIS own stores).
- **The two direct calls** are tracking-core to deriver HTTP, and every consumer to its own mapper sidecar. Both are synchronous helper calls, not control of the chain.
- **Confirmed absent:** a replay service, a delivery log, a status-change event for the customer with a stable event id (section 5).
- **tracking-core is the closest thing to a controller.** It owns the schedule and lifecycle of polled parcels and decides when a parcel stops being polled. It does not control webhook, file or manual sources, nor anything downstream.

Confidence: high on "choreography". Medium on "nothing runs elsewhere": I read the Terraform root and manifests, but not the on-prem estate (Scan Injector host, Transfer Service) or ADO pipeline definitions.

## 3. `raw_tracking.v1` schema

There is no formal schema (tracking-core `schema/tracking-event-schema.json` is an example, per the vault). The best description is the .NET model (the origin) plus the other three publishers' dialects. Sources: ADO tracking-core@c0811087 `src/Gfs.Fenghuang.Tracking.Core.Shared/Publishers/Models.cs`; `EventPublisher.cs` (camelCase, nulls omitted, `PubsubMessage` with data only, so **no attributes and no ordering key**); `ecm-simulator@82585cc packages/ecm-data/src/events/raw-tracking-v1.ts` (a fixture that pins each publisher's dialect to code lines; secondary).

Transport: JSON in the message body. Attributes: tracking-core and the file processor set none. The Royal Mail webhook sets `carrierId` (the value of `parcel.carrierV2`) as an attribute. No subscription on `raw_tracking.v1` filters on it (no filter seen in Terraform).

| Field | Type | Publisher notes | Carrier-specific? |
|---|---|---|---|
| `id` | string | Minted by each publisher: tracking-core and the file processor and the RM webhook all use a new Mongo ObjectId; SUS's synthetic delivered event has **none** (CCIS and ICIS skip an event without one). Not derived from the carrier's own event id | No, but it is not carrier-stable: RM supplies `EventId` and the webhook puts it in `additionalData.EventId` while publishing a freshly minted `id` |
| `receivedDate` | ISO datetime | tracking-core DateTimeOffset (`+00:00`); SUS absent | No |
| `reportedDate` | ISO datetime | Carrier time. RM webhook parses a zone-less string (`YYYY-MM-DD HH:mm:ss`) and stamps it as UTC, so it is local time labelled UTC in summer (code comment: "assume it's local time"). File mappers parse per carrier (DX uses `YYMMDD` plus time as UTC) | **Yes** (semantics differ per carrier) |
| `isReportedDateLocalizable` | bool | Per source; carrier flag | **Yes** (a signal that carrier time zones differ) |
| `statusCode` | string | The carrier's raw code, never a GFS code. Synthetic `GFS_DELIVERED_EVENT` from SUS. tracking-core omits when null | **Yes, by design** (raw carrier vocabulary; this is the leak that forces every consumer to map) |
| `statusDescription` | string | Carrier's free text | **Yes** |
| `parcel.shipmentId` | int (SUS: numeric string) | From `shipments.v2.identified`. Required by the deriver (throws `TrackingEventMissingParcelInfoError` without it) | No |
| `parcel.shipmentIdV2` | string, nullable | tracking-core only | No |
| `parcel.carrier` | string | The legacy carrier name or id (file-mapper DX uses `config.carriers.dx.id`; RM uses `config.carriers.royalMailSapient.name`) | Dual identity: GFS legacy name beside `carrierV2` |
| `parcel.carrierV2` | string | Almanac id (`idV2`); used for lookups in webhooks | Dual identity. Docs disagree on example values (catalogue shows `carrier:10, carrierV2:"dpd"`; simulator header says the reverse). Types are strings throughout. UNKNOWN which is right in prod |
| `parcel.consignmentNumber` | string | Carrier's consignment number | No |
| `parcel.parcelNumber` | string, optional | Absent on a consignment-level scan (BJS); the deriver then only extends the window | No |
| `parcel.serviceCode` | string, nullable | | Carrier-ish |
| `parcel.contractNo` | string, nullable | tracking-core only | No |
| `parcel.company` | string, nullable | The tenant key (`connect-hooks` needs it); set by tracking-core from the active parcel and by the webhooks from the stored shipment | No |
| `parcel.despatchDate` | string | SUS only | No |
| `signatory.name` | string | | No |
| `location{countryCode, lat, long}` | | tracking-core serialises `lat`/`long`. **The RM webhook type names them `latitude`/`longitude`, but its mapper only ever sets `countryCode`**, so the divergence is latent | No |
| `depot.name` | string | RM puts the event location text here. Coll8 uses `delivery.depot` as a plain string | **Yes** (Coll8 variant) |
| `delivery{scheduledDate, from, to}` | | The carrier's delivery window; the deriver lifts it to ETA. DX parses it from free text in an event with code `ETA` | **Yes** (parsed per carrier) |
| `additionalData` | map of string | Free carrier-specific key/value: RM sends `EventType`, `ShipperReference`, `EventId` | **Yes, leaks carrier fields** |
| `rawData[{name, uri, response}]` | | tracking-core attaches the **full carrier response** to every event (so to every subscriber). Webhooks leave it empty; file mappers set `[]` | **Yes, full carrier payload** (may hold personal data, per the vault) |

Other relevant shapes:
- Evri interim message (section 1.2), carrying the carrier's own body.
- `shipment_tracking_status.v2`: `{shipmentId, trackingStatusV2{code, text, groupId, eta, date?}}` with attributes `visibilityGroup`, `groupId`; `orderingKey = shipmentId` (deriver `publisher.js`).
- Connect webhook body: `{gfsId, carrierName, consignmentNumber, parcelNumber, carrierEventTime, status, text, isDelivered}`. `gfsId` is `parcel.shipmentId`. `carrierEventTime` is filled from `receivedDate`, not the carrier's time (connect@6c6d527 `tracking-handler.js`, CONFIRMED; the label is wrong, as the MPK page 2 also says).
- `scanners.consignments.V1`: one consignment, one parcel, one state per message in the simulator fixture; the real Dataflow job aggregates per session window (README). The fixture is for the older K8s patina; the Dataflow shape is not read. UNKNOWN whether they match.

## 4. Known weaknesses

Each is marked with whether I could verify it in code, Terraform or a measure. The documented ones come from the vault explainers and MPK page 2.

| Weakness | Evidence read | Status |
|---|---|---|
| **Duplicates across sources.** Each publisher mints its own `id`; consumers key on `id` alone. The same scan from the connector and a webhook lands twice (deriver, CCIS, ICIS) and gives two customer webhook calls | tracking-core `EventPublisher`, RM `prepareAndPublishTracking` (`tracking.id = new ObjectId()`), file processor mappers, deriver `_addTracking`; connect-hooks has no dedupe | CONFIRMED |
| **No ordering on `raw_tracking.v1`.** Only `shipment_tracking_status.v2` sets a key. Events of one poll publish in parallel (`Task.WhenAll`) | `ConnectorResponseHandler.cs`, `EventPublisher.cs`, `publisher.js` (deriver), Terraform subscription module | CONFIRMED |
| **Publish before persist.** tracking-core and RM both publish, then store. A crash between the two repeats the event (RM guards with an exists check on retry; tracking-core's date plus code check also does) | same | CONFIRMED |
| **Early scans.** (a) RM webhook parks events until the shipment arrives (about 146k of 343k); a later `shipments.v2.identified` releases them. (b) Deriver `upsert:false` drops a scan whose shipment it has not stored yet, **silently, no error** (the vault says "drops and acks", which matches). (c) file processor throws `LineImportError` for an unknown shipment and records the row for retry. (d) `tracking-core` only tracks a parcel after `shipments.v2.identified` | RM `tracking.service.ts`; deriver `shipments-collection.js` and `handlers/tracking.js`; DX mapper | CONFIRMED |
| **Unmapped codes.** Mapping is per consumer; only the CCIS sidecar publishes unmapped codes (`unmapped-tracking.v1`, 11.6k in window); the rest may show a fallback status | CCIS module creates the topic; handled count 11,622 | Topic and count CONFIRMED; "only CCIS publishes" STATED |
| **Customer webhooks are fire-and-forget.** A failed POST is warned and acked, no retry. Nothing signs the body. The label `carrierEventTime` is the received time | `tracking-handler.js` | CONFIRMED |
| **Hidden synchronous coupling.** tracking-core calls the deriver HTTP API once per event batch per parcel; if the deriver is unavailable the status call throws inside `UpdateTrackingStatus`, after publishing | `TrackingStatusManager.cs`, `RemoteTrackingStatusV2Getter.cs` | CONFIRMED (failure behaviour inferred) |
| **Dual sources during the Evri cutover.** Evri publish is off; going live runs connector plus webhook together; dedupe is per service only | prod.tfvars; webhook README/known-context | CONFIRMED setting; effect INFERRED |
| **Shipment push subscriptions have no DLQ and no filter** in the webhook module; the interim subscription has a DLQ (5) | `pubsub.tf`, `interimpubsub.tf` | CONFIRMED |
| **Dead and dormant topics keep accumulating:** four orphaned `raw_tracking.v1` subscriptions, `tracking.v1`, `legacy_tracking.v1`, `parcel-eta-update`, `warehouse-*` | main.tf, manifests, catalogue | CONFIRMED (replicas and commented manifests at `prod-uk1-primary-cluster@4d4b6cb`, 2026-07-20) |
| **Write-back lives in the staging project and is unowned.** `scanners.consignments.V1` is in `gfs-ecm-staging`; publisher IAM "granted manually" | Terraform comment | CONFIRMED (comment); ownership STATED (vault) |
| **No replay, no retention on acked messages.** Not re-verified by me; there is no snapshot or seek config in the modules I read | vault; modules read | STATED |
| **Fan-out cost.** Every raw event is handled by about ten consumers; each of ICIS, CCIS, SUS and the deriver handles 4.08M status messages on top | Datadog | CONFIRMED |

## 5. Gaps

**Events that should exist and do not (inference, marked as such):**
1. **No "tracking event accepted/mapped" event with GFS meaning.** The bus carries only raw carrier facts; the derived status is published per shipment (v2) but not per scan, and there is no per-scan canonical event with a mapping version. CONFIRMED absence in the topics read.
2. **No outbound customer-event topic.** Customer webhooks are produced by a consumer of `raw_tracking.v1`, with no topic, no delivery log and no retry record. CONFIRMED absence; `connect.hooks_usage.v1` is dead code.
3. **No replay or dead-letter-reprocess event** for tracking; DLQ messages are stored, not redriven (vault).
4. **No carrier-account health event.** The 3002 DHL errors never pause polling (vault, tracking-core reads `HandleError` only). Not re-read.
5. **No shipment-deleted or manual-status event on the tracking bus**; manual delivery is a synthetic `raw_tracking.v1` message with no id.
6. **No POD-captured event.** The POD is fetched on read; the vault's plan "capture PODs at ingress" is a Waypoint plan, not an event.

**Services or paths whose source I could not find or did not read:**
- **`tracking-core` after c081108**: read from ADO master (resolves to c081108) only the response handler, status manager and publisher. Not read: `batch-creator`, `consignment-manager` handler, the connectors, `ErrorResponseHandler`, `TrackingEventFilter`, `HermesSucks`.
- **`gfs-modernizer`, Firebird Transfer Service, Scan Injector and `patina-service-2` Go source**: only the ReadMe and Terraform were read. `windowed-shipments-parcels` and `tracking-events.v2` roles are from Terraform names and the catalogue.
- **The `gfs-ecm-staging` Terraform** for `scanners.consignments.V1` (topic and subscription, DLQ, retention).
- **tracking-mapper sidecar and `tracking-configuration-distribution-service` source**: wiring read only.
- **CCIS and ICIS handlers**: only Terraform wiring, handled counts and the vault. Whether they skip events without an id is STATED.
- **InPost webhook**: PR open and publish off (vault); not read in code.
- **Royal Mail webhook source of truth**: the standalone repo at `3c880bf` (21 May 2026) is what I read; the vault says a move into the monorepo is in a PR. The prod build may differ.
- **Live GCP state**: no access to `gcloud` here. Topic and subscription lists are Terraform only; the local clone of `gfs-ecm-prod-uk1` is stale (commit e3c6dd9, 2025-07-30) and was used for module structure only. Subscriptions in older modules (for example `pod-service`, which lacked a raw-tracking subscription locally) were re-read from ADO master.
- **The ECM catalogue's own date**: `ecm-development@b2b67df`, docs generated 2026-08-10. Its `raw_tracking.v1` "15 subs" and the identified "17 subs" agree with what I counted in the ADO `main.tf`. Its claim that `SUS` publishes about 8 a week is from August.
- **Live-ness of manifests**: replicas read from a local clone of `prod-uk1-primary-cluster@4d4b6cb` (2026-07-20). The vault cites a newer `39fa64c`. A change since July would not show.
- **Longmen**: ecm-development calls all `*.longmen` subscriptions orphaned; the vault says the data team pulls `raw_tracking.v1.longmen` as a live feed. I could not read `gfs-data-services/gfs-pipelines` (ADO search for it failed). The two statements are not contradictory (no in-cluster workload, external consumer) but I did not verify the second.
- **Pub/Sub throughput per topic** was not available; Datadog handled counts are per subscriber. `file_tracking.v1` volume is inferred.

## 6. Evidence index

| Ref | Where | Version | Used for |
|---|---|---|---|
| T1 | ADO `GFS Cloud Infrastructure/gfs-ecm-prod-uk1` `/main.tf` plus `modules/{subscription,shipment-tracking-status-deriver,pod-service,longmen-connection,customer-care-portal,tracking-patina-service,tracking-dataflow-patina-service,data-warehouse,tracking-file-ingestion-processor,shipment-identity-service}/main.tf` | `master` read 2026-11-10 (commit sha not captured) | topic and subscription wiring, defaults, filters, ordering |
| T2 | local `~/code/k8s/gfs-ecm-prod-uk1` | `e3c6dd9` (2025-07-30, stale) | module structure only (scanning-core, CCIS, SUS, claims, parcel-eta, mapping, connect) |
| M1 | local `~/code/k8s/prod-uk1-primary-cluster` | `4d4b6cb` (2026-07-20) | replicas, env wiring: `tracking-mapper.yaml:7,51`, `parcel-eta-service.yaml:7`, `data-warehouse/data-warehouse.yaml:53,115`, `connect-hooks.yaml:98`, `tracking-core.yaml:148,368` |
| C1 | ADO `fenghuang/tracking-core` | `c0811087b8ed4dce4968bb8e9b985f6853f51a69` | `Shared/Publishers/Models.cs`, `Shared/Publishers/EventPublisher.cs`, `ResponsePublisher/Services/V1/Handlers/ConnectorResponseHandler.cs`, `Shared/TrackingStatus/TrackingStatusManager.cs`, `RemoteTrackingStatusV2Getter.cs` |
| F1 | ADO `fenghuang/tracking-file-processor` | master (`e6da4bf`) | `src/publisher.js`, `src/mappers/file-mapper-DX.js` |
| W1 | local `~/code/apiky-survey/gh/gfs-hybrid-services_tracking-webhooks` | `9777dd4` | `iac/modules/tracking-webhook/{pubsub,interimpubsub}.tf`, `packages/tracking-webhook-core/src/types/{tracking,interim-tracking}.ts`, `src/services/*`, `iac/projects/tracking-webhook-evri/tfvars/prod.tfvars` |
| W2 | local `.../gfs-hybrid-services_tracking-webhook-royal-mail-sapient` | `3c880bf` | `handler/src/services/tracking.service.ts`, `handler/src/mappers/royalmailsapient.mapper.ts`, `iac/projects/*/pubsub.tf`, `iac/env/prod.tfvars` |
| S1 | GitHub `gfs-ecm/shipment-tracking-status-deriver` | `a3dc4464` | `src/pubsub/publisher.js`, `window-processor.js`, `handlers/tracking.js`, `mongo/shipments-collection.js`, `tracking-mapper.js`, `startup.js` |
| S2 | GitHub `gfs-ecm/shipment-update-service` | `ccec388` | `src/api/routes/mark-as-delivered.js`, `src/api/publisher.js` |
| S3 | GitHub `gfs-ecm/connect` | `6c6d527` | `apps/connect-hooks/src/tracking-handler.js` |
| P1 | ADO `GFS Legacy Migration/patina-service-2` | `main` (sha not captured) | `ReadMe.md` |
| D1 | GitHub `gfs-ecm/ecm-development` | `b2b67df` | `docs/pubsub-event-catalogue.md` (secondary, 2026-08-10) |
| D2 | GitHub `gfs-ecm/ecm-simulator` | `82585cc` | `packages/ecm-data/src/events/raw-tracking-v1.ts`, `scanners-consignments-v1.ts` (secondary; pins code lines). One discrepancy found: it records the synthetic delivered event with `id: uuid()`, but `shipment-update-service@ccec388` has no `id` |
| DD | Datadog `execute_code`, `sum:gfs.<svc>.pubsub.<x>.handled_messages{*}.as_count()` | 2026-10-23 to 2026-11-07 UTC | all handled counts |
| V1 | Vault: `Systems/ecm/{overview,architecture,known-context}.md`, `Explainers/2026-11-06-life-of-a-shipment-through-ecm.md`, `...-ecm-event-world-where-its-a-mess.md`, `Handovers/2026-11-09-merak-replacement-pages.page2-tracking-events-webhooks.md`, `...diagram-tracking-carrier-to-customer.md`, `Engineering/{tracking-core,tracking-webhooks}/*` | verified 2026-11-06 to 2026-11-09 | STATED claims |
| MPK | Confluence 354975746 Shipment Journey Through ECM (read via Atlassian MCP, version 13, 2026-11-10); 355074077 read through its vault source copy `page2-tracking-events-webhooks.md`, not the live page | | STATED claims |

## 7. Corrections and cross-checks against what you already know

- **Confirmed:** `raw_tracking.v1` total ~6.29M (every complete consumer handled 6.2947M to 6.2970M). Unmapped 11,622. G4 field set (id, `parcel.shipmentId`, `parcelNumber`, `company`) matches the code; the deriver also requires `shipmentId`, and `connect-hooks` requires `company`. Publishers mint their own ids and no publisher sets an ordering key. Evri runs in shadow (publish flag false). The RM webhook parks events (retry collection) and releases on a later identified shipment.
- **New:** a fourth publisher on `raw_tracking.v1` (SUS manual delivered, rare). Four more topics on the spine than your list names (`expired_window`, `shipment_tracking_status.v2` and its two siblings, `tracking_configuration_notifications.v1`, plus the Evri interim topic). tracking-core calls the deriver synchronously. The deriver silently drops a scan for a shipment it has not stored. `scanners.consignments.V1` is in the staging project. RM's own `EventId` is kept only in `additionalData`.
- **Not confirmed:** whether the Dataflow write-back publishes one state per message (the fixture says so for the older job; the README describes aggregation).
