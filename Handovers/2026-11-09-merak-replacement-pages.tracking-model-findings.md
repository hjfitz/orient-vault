---
tags: [handover, research-copy, ecm, tracking]
date: 2026-11-10
tldr: "Research copy: tracking event shapes at each stage, the six status models, terminal states and the mismatches between stages (2026-11-10)."
status: research-copy
---
This is a research copy of the findings file `tracking-model-findings.md`, kept in the vault so it can be found and cited. The synthesis is [[Systems/ecm/tracking]]. Where the two differ, the synthesis note is the later reading. Nothing was edited in Confluence, a repo or Firebird.

# How ECM models tracking data: event shapes, status model, topics

Read-only research, 10 Nov 2026. Nothing was edited in Confluence, the vault or any repo. Companion to `tracking-core-findings.md` (polling and scheduler), which this file does not repeat.

## Short answer

A tracking update is not just a status string. ECM models tracking as three different things, and the word "status" means a different type at each:

1. **A scan event.** A structured object: carrier code, carrier description, reported time with an offset flag, received time, location, depot, signatory, a delivery window and a free-form dictionary. Its identity is a Mongo ObjectId minted by the publisher. This is the thing on `raw_tracking.v1`.
2. **A mapped event.** The same scan after a config-driven lookup (carrier, code, description regex) has attached GFS meaning: a GFS code and text, a string `groupId`, an `isDelivered` boolean, an `isVisibleToCustomer` boolean and a RAG exception status. The mapping is done again in every consumer, and `tracking-core` stores it but does not publish it.
3. **A shipment status.** A derived object `{ date, text, code, groupId, isVisibleToCustomer, eta | signatory }`, collapsed from all parcel events by the deriver and published as `shipment_tracking_status.v2`, with a separate RAG exception status on `shipment_exception_status`.

There is no enum or int for status in the event bus. `groupId` is a string, and its vocabulary is set by a spreadsheet, not code. There is no topic specific to delivered, exception, out for delivery, POD ready or customer notification. Delivered, attempted and the rest are values of `groupId` on one event type. Two things are separate: the RAG exception status (own topic) and the legacy Firebird write-back (own topic, own integer status model).

## Evidence key and pins

| Label | Meaning |
| --- | --- |
| CONFIRMED | read in code or in a deployed manifest |
| STATED | read in a doc, page or comment only |
| UNKNOWN | not found in source |

| Source | Pin |
| --- | --- |
| tracking-core (ADO `fenghuang/tracking-core`) | `c0811087b8ed4dce4968bb8e9b985f6853f51a69`, local shallow clone, `src/` paths below are relative to it |
| tracking-mapper (GitHub `gfs-ecm`) | `44cfbf2ef5124a14ed0583cc6fbe7e6b1f8406e0` |
| shipment-tracking-status-deriver (GitHub `gfs-ecm`) | `a3dc4464075bb94c8a2b086652ec96321d6c6e20` |
| tracking-configuration-distribution-service (TCDS) | `bbd5e7442b72214e93c571ed6f5caab7c6690cdf` |
| connect (GitHub `gfs-ecm`, holds connect-hooks) | `6c6d527bf80499f732ee59767dd22cd66d29ade4` |
| shipment-update-service (SUS) | `ccec388d9b3c85d4c88f072627fc1bf82463b614` |
| tracking-webhook-core (GitHub `gfs-hybrid-services`) | `254827c66f436d33983980825af34cc390ef0786` |
| tracking-file-processor (ADO) | `e6da4bf9a9c6036f6ffcce73af2bd4f885eee5ce` |
| tracking-patina-service (ADO) | `8edfb3e5e5529d3b95218434d7271e445462d629` |
| customer-consignment-information-service (CCIS, GitHub `gfs-ecm`) | `b2af452ee13d9c824705f508917ea3988c915fc0`, read through the GitHub MCP |
| prod-uk1-primary-cluster (ADO, manifests) | `a317dc0b90a3ef4df30fcdc82293a4abd924f74b` (2026-11-06) |
| gfs-ecm-prod-uk1 Terraform (local) | `e3c6dd9` (2025-07-30, 15 months old) |
| ecm-development docs (GitHub `gfs-ecm`) | `b2b67df02ce377acdd97b9ec714ad984e7ae2e19`, STATED only |
| Firebird procedures | `procedures.sql` in this scratchpad, the December 2025 dump of central procedures (not live) |
| MPK 355074077 | read via the Atlassian MCP in markdown, version 3, STATED |

Not local and not read as code: CCIS and ICIS beyond the two files named, claims-service, the Dataflow patina pipeline source, `patina-service-2`, the Selector scan injector, the `Gfs.Core.PubSub` NuGet. The GitHub MCP could not find `gfs-ecm/consignment-query-service` (404), so the Go enum named by the ecm-development doc was not read.

Repo paths below are `repo@short-sha path:line` where short shas are: tracking-core `c081108`, mapper `44cfbf2`, deriver `a3dc446`, TCDS `bbd5e74`, connect `6c6d527`, SUS `ccec388`, webhook-core `254827c`, file-processor `e6da4bf`, patina `8edfb3e`, CCIS `b2af452`, prod cluster `a317dc0`.

---

## Q1. The shape of one tracking event at each stage

### Stage map

| # | Stage | Type or message | Where defined | Status |
| --- | --- | --- | --- | --- |
| 1 | Carrier connector to tracking-core (gRPC) | `ConnectorResponse` with repeated `TrackingEvent`, plus `Status`, `ErrorReason` | tracking-core@c081108 `src/Gfs.Fenghuang.Tracking.Core.ResponsePublisher/Protos/connector_response_v1.proto:13-90` | CONFIRMED |
| 1a | Connector-internal (what a connector author fills in) | `Tracking.Event` in the connector framework | tracking-core@c081108 `src/Gfs.Fenghuang.Tracking.Core.Frameworks.Connector/Tracking/TrackingProvider/Tracking.cs:1-120` | CONFIRMED |
| 2 | Stored on the parcel | `ActiveParcel.TrackingEvent` in Mongo `active-parcels` | tracking-core@c081108 `src/Gfs.Fenghuang.Tracking.Core.Shared/Models/ActiveParcel.cs:73-86` | CONFIRMED |
| 3 | `raw_tracking.v1` message | Publisher model `TrackingEvent`, camelCase JSON, nulls omitted | tracking-core@c081108 `Shared/Publishers/Models.cs:14-30`, `Shared/Publishers/EventPublisher.cs:40-57` | CONFIRMED |
| 4 | Mapped event | `MappedTrackingEvent` stored on the parcel, and the mapper's HTTP response | tracking-core@c081108 `ActiveParcel.cs:55-71`; mapper@44cfbf2 `src/api/routes/map-tracking.js:39-79` | CONFIRMED |
| 5 | Derived shipment status | `{ shipmentId, trackingStatusV2 }` on `shipment_tracking_status.v2` | deriver@a3dc446 `src/derive-shipment-tracking-status-v2.js:103-130`, `src/pubsub/publisher.js:23-28` | CONFIRMED |
| 5a | Derived exception status | `{ shipmentId, exceptionStatus: { id, priority, isNew } }` | deriver@a3dc446 `src/derive-shipment-exception-status.js:46-85`, `publisher.js:15-18` | CONFIRMED |
| 6 | Customer webhook body | JSON POST from connect-hooks | connect@6c6d527 `apps/connect-hooks/src/tracking-handler.js:104-115` | CONFIRMED |
| 7 | Legacy-shaped scan for Firebird | Patina "old fashioned" event on `scanners.consignments.V1` | patina@8edfb3e `src/patina.js:34-77` | CONFIRMED shape. Whether this service publishes in prod is a separate finding, see below |
| 7a | tracking-core's own legacy message | `LegacyTrackingEvents` on `legacy_tracking.v1` | tracking-core@c081108 `Shared/Publishers/EventPublisherLegacy.cs:43-100,129-134` | CONFIRMED shape, switched off in prod |

### Field table, stage by stage

Fields are listed as they appear on the wire or in the store. A dash means the field does not exist at that stage.

| Field | 1. gRPC ConnectorResponse event | 2. Stored on parcel | 3. raw_tracking.v1 | 4. Mapped event | 5. Shipment status v2 | 6. Webhook body | 7. Legacy scan (patina) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Event id | - (minted later) | `id` ObjectId string | `id` | `id` copied from the event | - | - (no event id) | - (`scanId` fixed 0) |
| Shipment id | `ParcelId` on the response (internal parcel doc id, not shipmentId) | `parcel.shipmentId` int, `shipmentIdV2` string | `parcel.shipmentId`, `parcel.shipmentIdV2` | - | `shipmentId` on the message | `gfsId` | - |
| Parcel and consignment number | via `ParcelId` | `parcel.parcelNumber`, `consignmentNumber` | `parcel.parcelNumber`, `consignmentNumber` | - | - | `parcelNumber`, `consignmentNumber` | `parcels[0].parcelNo`, `consNo` |
| Carrier and customer | - | `parcel.carrier`, `carrierV2`, `carrierCode`, `company`, `customerId`, `contractNo`, `serviceCode` | `parcel.carrier`, `carrierV2`, `company`, `contractNo`, `serviceCode`, `shipmentId`, `consignmentNumber`, `parcelNumber` (no `customerId`, `carrierCode`, `despatchDate`) | - | - | `carrierName` (from almanac, `'n/a'` on failure) | `carrier` (legacy name from almanac) |
| Carrier code | `StatusCode` string | `statusCode` | `statusCode` | `Code` is the GFS code, not the carrier's | `code` is the GFS code | - | `states[0].carrCode` = carrier code |
| Text | `StatusDescription` | `statusDescription` | `statusDescription` | `text` (carrier text if `useCarrierText`, else GFS description) | `text` | `text` (mapped) | `scanText` = carrier text |
| Reported time | `ReportedDateString` (offset string) or obsolete `ReportedDate`, plus `IsReportedDateLocalizable` | `reportedDate` DateTimeOffset, `isReportedDateLocalizable` | `reportedDate`, `isReportedDateLocalizable` (null becomes true) | `date` = reportedDate (as `.DateTime`, offset dropped) | `date` | - | `scanDate` |
| Received time | `ReceivedDate` on the response | `receivedDate` | `receivedDate` | - | - | `carrierEventTime` = receivedDate | - |
| Location | `Location { CountryCode, Lat, Long }` | `location { countryCode, lat, long }` | `location { countryCode, lat, long }` | - | - | - | `latitude`, `longitude` |
| Depot | `Depot { Name }` | `depot.name` | `depot.name` | - | - | - | `scanDepotName` |
| Signatory | `Signatory { Name }` | `signatory.name` | `signatory.name` | `signatory` (name string, in the deriver's own copy) | `signatory` (only on DELIVERED or PARTIALLY_DELIVERED) | - | `signBy` |
| Delivery window | `Delivery { ScheduledDate, From, To }` | `delivery { scheduledDate, from, to }` | `delivery { scheduledDate, from, to }` | `eta { from, to, scheduledDate }` (deriver copy) | `eta` (every group except the two delivered ones) | - | `schDeliveryDate`, rebuilt from `delivery.to` and the event date |
| Group | - | - | - | `groupId` | `groupId` | `status` (display string from `groupId`) | - |
| Delivered flag | - | - | - | `isDelivered` boolean | - (derived from `groupId`) | `isDelivered` | `isDelivered` always false |
| Visibility | - | - | - | `isVisibleToCustomer` | `isVisibleToCustomer` (message body for the `ALL` and `CUSTOMER_VISIBLE` variants) | - | - |
| Exception RAG | - | - | - | `exceptionStatus { id, priority }` | separate message | - | - |
| Unmapped | - | - | - | `isUnmapped` | - | - | - |
| Free-form extras | `AdditionalData` dictionary | `additionalData` | `additionalData` | - | - | - | - |
| Raw carrier payload | `RawData[] { Name, Uri, Response }` | not stored | `rawData[]` (every event in the poll carries the whole response) | - | - | - | - |

Evidence for cells that are not on a line above:
- Stored event has no `rawData`: `ActiveParcel.cs:73-86`. The raw data is attached only at publish time: `ConnectorResponseHandler.cs:103-119` (tracking-core@c081108, `src/Gfs.Fenghuang.Tracking.Core.ResponsePublisher/Services/V1/Handlers/`).
- Gateway from proto to stored event, id and received date set in the handler: `ConnectorResponseTrackingProfile.cs:17-32` (id and receivedDate ignored on map), `ActiveParcelDomain.cs:72-73` (`ObjectId.GenerateNewId()`, `ReceivedDate = receivedDate`).
- Publisher mapping `IsReportedDateLocalizable ?? true`: `Shared/Publishers/Mapping/TrackingEventProfile.cs:20`.
- Mapper response shape: `map-tracking.js:51-65`. Deriver's own mapped event shape (adds `signatory` as a name string and `eta`): deriver@a3dc446 `src/pubsub/tracking-mapper.js:7-42`.
- Webhook body projection: `tracking-handler.js:104-115`. The mapper call in connect-hooks passes only carrier, carrierV2, statusCode, statusDescription, receivedDate: `tracking-handler.js:68-84`.
- Patina mapping: `patina.js:34-77`, `tracking-handler.js:45-51` (attributes `ScannerUid: 'fenghuang'`, `Carrier`).

### What changes between stages (the transformations that matter)

| From to | What changes | Evidence |
| --- | --- | --- |
| Carrier to connector event | The connector copies carrier code and description verbatim and maps ETA fields to `Delivery.From/To`. No GFS meaning at this stage | STATED in ecm-development@b2b67df `backend/tracking-scan-pipeline.md` (flow diagram). The shape of the framework type is CONFIRMED at `Tracking.cs` |
| gRPC event to stored event | Gains `id` (ObjectId minted by response-publisher) and `receivedDate`. `reportedDate` is parsed from `ReportedDateString` with the exact format `yyyy-MM-ddTHH:mm:sszzz` | `ActiveParcelDomain.cs:72-73`, `ConnectorResponseTrackingProfile.cs:46-56` |
| Stored event to raw_tracking.v1 | Gains the `parcel` block and `rawData`. Drops `customerId`, `carrierCode`, `despatchDate`, address, `meterNumber`. `isReportedDateLocalizable` null becomes true. Published once per new event, in parallel | `Models.cs:14-43`, `TrackingEventProfile.cs:17-24`, `ConnectorResponseHandler.cs:110-125` |
| raw event to mapped event | Carrier code and text are replaced by GFS code and text. Adds group, delivered, visibility, RAG. The raw code stays on the stored raw event only. The carrier's raw event is still on `raw_tracking.v1`, but the mapped result is not published | `map-tracking.js:58-65`, `ConnectorResponseHandler.cs:89-92` |
| mapped events to shipment status | One event per parcel wins by group precedence then date, then the parcel winners are collapsed again. Signatory or ETA is attached. The time is the winning event's reported time | `derive-shipment-tracking-status-v2.js:43-71,103-130` |
| shipment status to webhook | Not a derived-status path. The webhook does not consume the derived status. It re-maps the single raw event and sends the group as a display string | `tracking-handler.js:58-115`. This is a different path from the shipment status |
| raw event to legacy scan | Carrier's raw code goes in `carrCode`. `isDelivered` and `deleted` are hardcoded false. `schDeliveryDate` is reconstructed from `delivery.to` "HH:mm" and the event date. Amazon "Departed" is dropped | `patina.js:34-77`, `event-filter.js:3-9` |

---

## Q2. Is there a canonical status model?

**There are at least six, none of them canonical across the platform.** One type per layer, defined by different owners.

| # | Layer | Type | Values | Defined by | Status |
| --- | --- | --- | --- | --- | --- |
| A | Carrier code | Two strings, `statusCode` and `statusDescription` | Whatever the carrier sends. Not enumerated anywhere | The carrier | CONFIRMED (types), STATED (not enumerated, ecm-development `docs/consignment-status-groups.md` TL;DR) |
| B | Mapped event | Object: `code` (string), `text` (string), `groupId` (string), `isDelivered` (bool), `isVisibleToCustomer` (bool), `exceptionStatus { id, priority }`, `isUnmapped` (bool) | `groupId` is free text. Exception ids RED 200, AMBER 100, GREEN 0 | A spreadsheet in GCS parsed by TCDS and pushed to mapper sidecars. Columns `carrierMatcher, codeMatcher, descriptionMatcher, code, description, groupId, trackingIsDelivered, customerIsVisible, exceptionStatus, useCarrierText` | CONFIRMED: TCDS@bbd5e74 `src/configuration-providers/excel-parser.js:26-57` (columns, schema), `:83` (`DATA_ONLY` rows get no exception status), mapper@44cfbf2 `src/mongo/tracking-mapping-config-collection.js:68-112` |
| C | Shipment status | Object `{ date, text, code, groupId, isVisibleToCustomer, eta \| signatory }` | `groupId` string, see vocabulary below | Deriver code for precedence. CCIS validator for the filterable list | CONFIRMED |
| D | Exception status | Object `{ id, priority, isNew }`, separate message | GREEN, AMBER, RED | Deriver code | CONFIRMED: `derive-shipment-exception-status.js:1-30,46-85` |
| E | tracking-core parcel state | `TrackingState` string and `CurrentStatus { id, bucket, description }` | `TrackingState`: IN_TRANSIT, DELIVERED, DELETED. `CurrentStatus.bucket`: only "DELIVERED" or "IN_TRANSIT" is ever written. `id` and `description` are never set | tracking-core code | CONFIRMED: `ActiveParcelRepository.cs:19-21,205-221`, `RemoteTrackingStatusV2Getter.cs:63`, `ActiveParcel.cs:112-117` |
| F | Firebird legacy status | Integer, via `GET_SCAN_CODE` and the `carrier_scan_codes` and `scan_code_mapping` tables | Seen in procedure text: 202, 207, 208, 280, 290, 340, 390, 1000. Other legacy values noted in the vault: 100 deleted, 1003 delivered, 1005 closed by `CHECK_SHIP_STATUS` | Central Firebird, rows keyed by carrier, code, text | CONFIRMED for the numbers in `procedures.sql:9476-9640` (Dec 2025 dump, not live). The meaning of each number: UNKNOWN |
| G | Customer webhook display status | String | `AWAITING COLLECTION`, `IN TRANSIT`, `OUT FOR DELIVERY`, `DELIVERED`, `RETURNED`, `DATA ONLY` | connect-hooks code | CONFIRMED: connect@6c6d527 `apps/connect-hooks/src/derive-status.js:4-18` |

### The group vocabulary (layer C)

| Group | How it arises | Status |
| --- | --- | --- |
| `DATA_ONLY` | Deriver default when no usable event exists (code `200`, text `PARCEL DATA RECEIVED`, env-overridable). Also a mapped group for data-only scans. Lowest precedence | CONFIRMED: deriver `src/config.js:49-54`, `derive-shipment-tracking-status-v2.js:19-41,103-130` |
| `IN_TRANSIT` | Mapped, and the mapper's default group for any unmapped event | CONFIRMED: mapper `src/config.js:94-106` (default `'IN_TRANSIT'`) |
| `DELIVERED` | Mapped. Highest precedence | CONFIRMED: `derive-shipment-tracking-status-v2.js:24-26` |
| `PARTIALLY_DELIVERED` | Synthesised by the deriver when only some parcels are delivered. Never from a carrier | CONFIRMED: `derive-shipment-tracking-status-v2.js:62-70` |
| `OUT_FOR_DELIVERY`, `ATTEMPTED`, `HELD_AT_BRANCH`, `AWAITING_CUSTOMER_COLLECTION`, `RETURNED` | Mapped from carrier codes by the spreadsheet | The names are CONFIRMED as the accepted filter values in CCIS@b2af452 `src/routes/consignment-schemas.ts:16-27`. That the spreadsheet emits each one is STATED (ecm-development `consignment-status-groups.md` §1) and not read: the sheet is UNKNOWN |
| `OTHER` | Query-time bucket only, in the CCIS validator list | CONFIRMED in the validator, never stored: STATED |

The CCIS validator lists 10 values (9 real plus `OTHER`). **The source of those values is the spreadsheet, and nothing enforces the list.** `VALID_GROUP_IDS` is read at `TCDS src/config.js:55` and enforced at `excel-parser.js:52` only when set. Prod does not set it: STATED (ecm-development `consignment-status-groups.md` §2 and ecm-simulator `tcds-source-spreadsheet.ts:41`), and I found no `VALID_GROUP_IDS` in any prod manifest I searched (grep across the cloned manifests, no hit), so CONFIRMED as absent from them. The prod spreadsheet itself and the full list of GFS codes: UNKNOWN. The number of distinct mapped codes: UNKNOWN.

No SLA, ETA-quality or reason-code field exists on the status. "Reason" for a failed delivery is not modelled: it lives in the carrier text, or in `additionalData` if a connector put it there (UNKNOWN per carrier).

### Where the mapping lives

- Carrier code to GFS meaning: the TCDS spreadsheet, published as `tracking_configuration_notifications.v1`, then pulled by mapper sidecars over HTTP. Mapper matches `codeMatcher`, `carrierMatcher`, `carrierV2Matcher` exactly or as `'ANY'`, and `descriptionMatcher` as a case-insensitive regex, then picks the highest `gfsCode` on multiple matches (STATED in ecm-development `consignment-status-groups.md` §2, Stage A; the mapper route and the store schema are CONFIRMED, the matching function body `getMapping` was not read).
- Carrier code to Firebird legacy status: `GET_SCAN_CODE` in Firebird, a different table set (CONFIRMED text, `procedures.sql:9476-9640`).
- GFS group to customer string: `derive-status.js:4-18`. Unknown or missing groups fall back to `IN TRANSIT`.
- GFS group to delivered flag: two independent sources, see Q6.

---

## Q3. What does the stored parcel hold beyond status?

`ActiveParcel` (tracking-core@c081108 `Shared/Models/ActiveParcel.cs:7-119`), Mongo `tracking-core.active-parcels`, CONFIRMED:

| Group | Fields | Notes |
| --- | --- | --- |
| Identity | `_id`; `parcel.shipmentId` (int), `shipmentIdV2`, `parcelNumber`, `consignmentNumber` | Upsert key is (`parcelNumber`, `shipmentId`) per `tracking-core-findings.md` |
| Customer | `parcel.customerId`, `company`, `contractNo` | Set by consignment-manager at `ConsignmentHandler.cs:83-99` |
| Carrier | `parcel.carrier`, `carrierV2`, `carrierCode`, `serviceCode` | |
| Shipment context | `parcel.despatchDate`, `parcel.address { countryCode, postCode }` | Delivery address country and postcode only |
| Never populated | `itemNumber`, `meterNumber`, `shipType` | `// TODO - map` in `ConsignmentHandler.cs` (CONFIRMED) |
| Polling | `tracking.lastRequestedAt`, `lastReceivedAt` | `lastReceivedAt` is set in memory and not persisted (see companion file) |
| Event history | `tracking.events[]` (raw scans, full structure above), `tracking.mappedEvents[]` | `mappedEvents` stored per event with `id` link |
| Status | `currentStatus { id, bucket, description }` (only `bucket` set), `trackingState` | |
| Life | `createdDate`, `expiryDate`, `expiryDateV2`, `shouldPublishToLegacy`, `wasManuallyUpdated` | |

What is **not** on the stored parcel (CONFIRMED by absence in the model):
- **No ETA field at parcel level.** Delivery windows live on individual events (`delivery { scheduledDate, from, to }`). The deriver lifts the winning event's window to `trackingStatusV2.eta`.
- **No delivered flag.** Delivered is `trackingState == DELIVERED` and `currentStatus.bucket == "DELIVERED"`.
- **No POD reference.** PoD is fetched live by `gfs-pod`, not stored on the parcel (STATED in vault `overview.md`: "fetches the proof of delivery when someone asks"). `gfs-pod` was not read here, so the POD cache and keys are out of scope: UNKNOWN for this question.
- **No signature image or URL.** Only `signatory.name` per event.
- **No exception RAG** on the parcel. `mappedEvents[].exceptionStatus` per event carries it, and the aggregate is on the deriver's Mongo `shipments` document (`exceptionStatusId`, deriver `src/pubsub/mongo/shipments-collection.js:33-46`).
- **No delivery address detail** beyond country and postcode.
- **The raw carrier response is not stored**, only published.

The parcel is **active-only**: it is deleted by a Mongo TTL index (see companion file). A durable copy is held downstream: CCIS and ICIS `consignments` collections carry `trackingStatus` and `parcels[].tracking.events`: STATED (ecm-development `backend/tracking-scan-pipeline.md` §3), and CCIS mapping file read at `consignment-status.ts` for the shape the fallback derives. The Mongo schemas themselves were not read: UNKNOWN.

The deriver's own store (Mongo `shipment-tracking-status-deriver.shipments`, CONFIRMED, `shipments-collection.js:1-31`) is a different shape again: `_id = shipmentId`, `createdTimestamp`, `trackingEvents.<parcelNumber>.<eventId> = mappedEvent`, `exceptionStatusId`. Mapped events are frozen at ingest time under the mapping in force then (`src/pubsub/handlers/tracking.js:25-31`).

---

## Q4. Different types and topics per stage?

**Different types, different topics, one event type for status.** The topology of status:

| Stage | Topic or channel | Message type | Carries status as | Status |
| --- | --- | --- | --- | --- |
| Connector to tracking-core | gRPC `ConnectorResponseServiceV1.SendResponse` (client stream) | `ConnectorResponse` | Carrier code and description only. Plus `ConnectorResponseStatus` (INVALID, SUCCESS, FAILURE) and `ConnectorResponseErrorReason` (NO_ERROR, GENERIC_ERROR, CREDENTIALS_ERROR, CARRIER_API_ERROR, PARCEL_NOT_FOUND_ERROR), which are transport outcomes, not parcel statuses | CONFIRMED: `connector_response_v1.proto:9-90` |
| Carrier scan out | `raw_tracking.v1` | `TrackingEvent` (one scan, one message) | Carrier code and description. No GFS status | CONFIRMED: `EventPublisher.cs:40-57` |
| tracking-core to legacy (off) | `legacy_tracking.v1` | `LegacyTrackingEvents` (whole event history per parcel per message) | Carrier text only | CONFIRMED shape. Prod `ShouldPublishToLegacy=false` (`tracking-core.yaml:389`, prod cluster@a317dc0). Catalogue says no subscription: STATED |
| Config for mapping | `tracking_configuration_notifications.v1` | `{ type: "config_updated" }` then an HTTP pull | n/a | STATED (catalogue) |
| Unmapped codes | `unmapped-tracking.v1` | `{ carrier, carrierCode, carrierDescription, seenAt }` | n/a | CONFIRMED shape at `publisher.js:20-22` and `map-tracking.js:68-75`. Published only where `UNMAPPED_TRACKING_EVENT_TOPIC` is set, and in the prod manifests I read that is CCIS only (grep, prod cluster@a317dc0) |
| Shipment status | `shipment_tracking_status.v2` | `{ shipmentId, trackingStatusV2 }`, attributes `visibilityGroup` and `groupId`, ordering key `shipmentId` | The only place a derived GFS status is published. `groupId` rides as a message attribute | CONFIRMED: `publisher.js:23-28` |
| Shipment status, old | `shipment_tracking_status` | `{ shipmentId, trackingStatusV2 }` | Same, `isVisibleToCustomer` stripped. Obsolete, ICIS still on it (STATED) | CONFIRMED publish: `expired-window-tracking-status.js:24`, manifest comment `shipment-tracking-status-deriver.yaml:145` |
| Exception status | `shipment_exception_status` | `{ shipmentId, exceptionStatus }`. Published on every window expiry, not only on change (`isNew` is inside the object) | RAG | CONFIRMED: `expired-window-exception-status.js:41-52`. Note: the handler publishes and stores whatever `derive...` returns, whether or not `isNew`, so "published only when changed" is not what this code does. The ecm-simulator claims otherwise: STATED, not reconciled |
| Debounce | `expired_window` | `{ shipmentId }`, self-consumed by the deriver 3 times | n/a | CONFIRMED: `publisher.js:29-32`. The window is 60 s by default (`config.js:29`) |
| Customer webhook | Direct HTTP POST from connect-hooks, no topic | Body above | Display string | CONFIRMED |
| Legacy write-back | `scanners.consignments.V1` (a topic in project `gfs-ecm-staging`) | Patina legacy shape | Raw carrier code only | CONFIRMED for the topic name and the shape. The live producer is the open question below |
| Manual delivered | `raw_tracking.v1` | Synthetic event, `statusCode: 'GFS_DELIVERED_EVENT'`, `statusDescription: 'GFS_EVENT'` | Rides the raw event type | CONFIRMED: SUS@ccec388 `src/api/routes/mark-as-delivered.js:43-56` |

### Is there a topic or type for delivered, exception, out for delivery, POD ready or customer notification?

| Question | Answer | Status |
| --- | --- | --- |
| Delivered | No. `groupId = DELIVERED` on `shipment_tracking_status.v2` (and `raw_tracking.v1` scans that map to it). Consumers also subscribe by attribute `groupId`: the message sets `attributes.groupId`, which a subscription filter could use. Whether any prod subscription filters on it: UNKNOWN | CONFIRMED for the attribute (`publisher.js:26`) |
| Exception | Yes, one: `shipment_exception_status`, a RAG (GREEN, AMBER, RED). It is a separate concern from delivery status. There is no event for "failed delivery" as such: `ATTEMPTED` is a group value | CONFIRMED |
| Out for delivery | A group value only | CONFIRMED (value in the CCIS validator, `consignment-schemas.ts:16-27`) and in CCIS's own precedence list (`consignment-status.ts:10-13`) |
| POD ready | None. No topic, type or event for PoD found in the tracking path. PoD is retrieved on request by `gfs-pod`, which subscribes to `raw_tracking.v1` and `shipments.v2.identified` (STATED, catalogue). What it does with them: UNKNOWN here | Not found |
| Customer notification | None as a topic. connect-hooks consumes `raw_tracking.v1` directly and POSTs. Other notification channels (portal emails and so on): UNKNOWN, not searched | CONFIRMED for connect-hooks |

So: **one event type with a status field, plus one separate RAG message.** Delivered, attempted and returned are values, not types.

### Who consumes what (the fan-out that a replacement would have to match)

From `ecm-development@b2b67df docs/pubsub-event-catalogue.md:160-177` (STATED, a doc derived from Terraform and manifests): `raw_tracking.v1` has 15 subscriptions including the deriver, CCIS, ICIS, SUS, claims, `gfs-pod`, `connect-hooks`, patina and BigQuery. `shipment_tracking_status.v2` goes to CCIS (filtering `visibilityGroup=CUSTOMER_VISIBLE`) and reporting-ingestion. I did not re-verify the subscription list in Terraform.

**Not on the bus: the derived status never reaches the webhook or the legacy side.** The customer webhook and the legacy scan both come from the raw event. See Q6.

---

## Q5. Terminal and special states

| State | How it is represented | How it ends tracking | Evidence | Status |
| --- | --- | --- | --- | --- |
| Delivered (tracking-core) | `trackingState = DELIVERED`, set when the V2 deriver call returns group DELIVERED. One-way: the update filter excludes docs already DELIVERED | Does not end tracking. The parcel is still leased if that carrier's DELIVERED batch key is enabled in etcd. It expires on the TTL index | `TrackingStatusManager.cs:33-46`, `RemoteTrackingStatusV2Getter.cs:63`, `ActiveParcelRepository.cs:205-221` | CONFIRMED |
| Delivered (status model) | `groupId = DELIVERED`, highest precedence, carries `signatory`. Separately a mapped `isDelivered` boolean from the spreadsheet | Terminal in precedence only: nothing marks the shipment closed | `derive-shipment-tracking-status-v2.js:24-26,124-128` | CONFIRMED |
| Partially delivered | Synthetic group on multi-parcel shipments | Not terminal | `derive-shipment-tracking-status-v2.js:62-70` | CONFIRMED |
| Failed delivery | `groupId = ATTEMPTED`, a value, no reason field. Legacy side: status integers (208 delivery exception, 280 carded, 390 refused appear in `GET_SCAN_CODE`) | None | CCIS validator; `procedures.sql:9476-9640` | The group name is CONFIRMED as a valid value. That the spreadsheet maps any code to it is STATED. The legacy mapping is CONFIRMED for the unknown-text DPD fallback only |
| Returned | `groupId = RETURNED`. Legacy text "RETURNED TO SENDER" maps to 208 in the unknown-text DPD fallback | None, no terminal handling found | CCIS validator; `procedures.sql:~9505-9510` | name CONFIRMED, spreadsheet mapping STATED |
| Lost | **No lost state found in the ECM model.** Not a group, not a trackingState, not a topic. The vault notes that legacy UPS loss reporting reads 1003 as lost | n/a | none in source; vault `known-context.md` (STATED, about the legacy reader) | UNKNOWN in ECM |
| Deleted | `trackingState = DELETED`, set only from the shipment message flag `Consignment.IsDeleted` at parcel creation. There is no tracking event for deletion | Leased only if that carrier's DELETED batch key is enabled, then expires on TTL | `ConsignmentHandler.cs:130`, `ActiveParcelRepository.cs:218`, `Consignment.cs:19` | CONFIRMED |
| Untracked contract | Mongo `untracked` list. Parcels are skipped at ingest and at lease | Never created or never leased | `ConsignmentHandler.cs:59` and `ActiveParcelDomain.cs:156-165` per companion file | CONFIRMED |
| Credential pause | Mongo `credential-errors` rows, per contract | Not polled while paused | companion file | CONFIRMED |
| Mark as delivered (manual) | A synthetic `raw_tracking.v1` event, `GFS_DELIVERED_EVENT`, one per parcel, after a legacy `mark.delivered` call | Treated as an ordinary raw event downstream, if it survives | `mark-as-delivered.js:34-56` | CONFIRMED |
| Closed by Firebird | Status 1005 by `CHECK_SHIP_STATUS`, legacy only | n/a | vault `known-context.md` | STATED. The only caller in the dump is commented out |

**Finding: deletion after creation looks unreachable in this code.** `ConsignmentHandler.Upsert` returns before `UpdateState` when the message type is `UPDATE` and the parcel already exists (`ConsignmentHandler.cs:~109-124`), and `UpdateState(..., isDeleted)` is only reached after the upsert (`:130`). So a shipment that is deleted later in Firebird and re-announced as an update does not flip an existing parcel to DELETED here. What event type a deletion arrives as: UNKNOWN (the type string `_legacy.eventType` comes from `gfs-modernizer`, not read). Treat as a risk to check, not a confirmed bug.

---

## Q6. Mismatches between stages

A replacement would have to preserve or deliberately fix these.

| # | Mismatch | Where | Status |
| --- | --- | --- | --- |
| M1 | **"Delivered" has two independent sources.** The mapper's spreadsheet `trackingIsDelivered` becomes `isDelivered` (used by the Hermes post-delivery cleanup, the TrackingEventFilter and the customer webhook). The deriver uses `groupId == DELIVERED` (used for tracking-core's `trackingState`, for SUS's `isDelivered`, and for the shipment status). Nothing in code asserts they agree. Both come from the same sheet row, so they can only disagree by a data error | `TrackingEventFilter.cs:27`, `HermesSucks.cs:24`, `tracking-handler.js:92,115`, `derive-shipment-tracking-status-v2.js:24-26`, SUS `shipment-tracking-status.js:5-6` | CONFIRMED that two sources exist. That they diverge in prod: UNKNOWN. MPK 355074077 row 1 says "at least six definitions": STATED, I counted four in the code above plus CCIS's own re-derivation and ICIS (not read) |
| M2 | **Mapping is done in many places, with no mapped event on the bus.** `tracking-core` maps, stores and then publishes only the raw event. The deriver, connect-hooks, SUS, CCIS, ICIS and claims each call their own mapper sidecar. Mapped results are frozen at ingest | `ConnectorResponseHandler.cs:89-92,114-118`; `tracking.js:25-31`; `tracking-handler.js:68-90` | CONFIRMED for tracking-core, deriver, connect-hooks, SUS. CCIS, ICIS and claims sidecars: STATED (prod manifests show a mapper image in those pods, not shown to be called) |
| M3 | **The webhook does not carry the derived shipment status.** The webhook status is the event's own group, mapped from the raw event, then collapsed to five display strings. `ATTEMPTED`, `HELD_AT_BRANCH` and `PARTIALLY_DELIVERED` become `IN TRANSIT` because the lookup defaults. A customer therefore cannot see attempted delivery or held at branch in the webhook | `derive-status.js:4-18` | CONFIRMED |
| M4 | **The webhook's `carrierEventTime` is the received time**, not the carrier's reported time | `tracking-handler.js:111` | CONFIRMED. The MPK page says the same (row 4): STATED |
| M5 | **Webhook docs disagree with code.** Docs list `carrier`, code sends `carrierName`. Docs omit `carrierEventTime`. Docs call `gfsId` a string, tracking-core stores shipment id as int (`int ShipmentId`, `Publishers/Models.cs:34`), though connect-hooks may pass whatever is on the event. Docs list `DATA ONLY` as a status, code agrees | `connect-docs` `pages/web-hooks/tracking-events.mdx` vs `tracking-handler.js:104-115` | CONFIRMED mismatch (docs vs code) |
| M6 | **The webhook body has no event id, GFS code, ETA, location, signatory, or delivery proof.** Only `text`, a display `status`, and `isDelivered` | `tracking-handler.js:104-115` | CONFIRMED |
| M7 | **Failed webhook posts are dropped.** Logged and acked, no retry, no log | `tracking-handler.js:125-135` | CONFIRMED |
| M8 | **Event ids are minted by each publisher** (ObjectId): tracking-core (`ActiveParcelDomain.cs:72`), webhook-core (`tracking.service.ts` `tracking.id = new ObjectId().toString()`), file-processor (`file-mapper-DX.js` `_id()`). tracking-core's id is minted before publish and re-minted if a poll re-finds the same event, because the stored copy is only written after a successful publish. Consumers key on id | `ActiveParcelDomain.cs:72`, `ConnectorResponseHandler.cs:125-131`; webhook-core@254827c `src/services/tracking.service.ts:202`; `file-mapper-DX.js:56` | CONFIRMED |
| M9 | **The synthetic manual event is malformed relative to the schema.** No `id`, no `receivedDate`, no `parcel.company`. connect-hooks drops it (no company). Deriver and patina handle it differently (it has no `company`, so no hook; the deriver would call its mapper on `GFS_DELIVERED_EVENT`). Whether the mapper sheet has a row for that code: UNKNOWN | `mark-as-delivered.js:43-56`, `tracking-handler.js:34-46` | CONFIRMED absent fields. MPK row 7 agrees: STATED |
| M10 | **Dedupe keys differ.** tracking-core dedupes on (reportedDate, statusCode), and keeps the first version of a description forever. webhook-core dedupes against its own shipment store. Downstream stores key on event id | `TrackingEventDeduplicator.cs:45-51`, `ActiveParcelDomain.cs:172-231`; ecm-development `tracking-scan-pipeline.md` invariants 2 and 3 (STATED) | CONFIRMED for the .NET side |
| M11 | **Location field names differ.** tracking-core and patina use `lat` and `long`. webhook-core's `TrackingLocation` type uses `latitude` and `longitude`. connector framework uses `Latitude`, `Longitude` and maps to proto `Lat`, `Long` | `Models.cs:50-55`; `patina.js:71-72`; webhook-core@254827c `src/types/tracking.ts:24-28`; `Tracking.cs` | CONFIRMED. Which one a webhook carrier adapter actually emits: UNKNOWN (no adapter source read) |
| M12 | **Reported time is carried inconsistently.** Offset kept on the raw event and stored event. The mapped event drops the offset (`ReportedDate.DateTime`). The status message carries it as a string. The legacy scan converts to London via `luxon` | `TrackingMapper.cs:47`, `patina.js:64-66` | CONFIRMED |
| M13 | **Two legacy shapes.** tracking-core's own `LegacyTrackingEvents` sends the whole event history of a parcel per message, uses the parcel's carrier code (`Parcel.CarrierCode`) not the scan's code, `ScanText` only, no `IsDelivered` or `IsDeleted` (TODO comments). Patina sends one scan per message with the scan's own code and a legacy carrier name. Patina's Firebird shape also expects fields that ECM has no source for (`shipType`, `weight`, `scanId`, all fixed 0) | `EventPublisherLegacy.cs:43-100,75,86-87`; `patina.js:34-77` | CONFIRMED |
| M14 | **Patina in prod looks disabled by config.** `CARRIERS=NONE`, so the handler returns on every real carrier name. It is also hard-coded to the staging project's `scanners.consignments.V1`, with a manifest comment that prod legacy "is currently run off of this topic from staging doppelganger". Terraform separately describes a Dataflow job `tracking-patina-pipeline`: `raw_tracking.v1` input, a BigQuery rollback table, and output to `scanners.consignments.V1`. **Who actually writes legacy scans in prod: UNKNOWN.** The Dataflow job source and `patina-service-2` were not found (ADO code search for `patina-service-2` returned zero results) | `tracking-patina-service.yaml:68-82` (prod cluster@a317dc0), `tracking-handler.js:21-27`, `modules/tracking-dataflow-patina-service/main.tf:1-8` (Terraform e3c6dd9) | CONFIRMED for the manifest and handler. The inference that this service publishes nothing is mine and unrun. Reading: `config.carriers = ['NONE']`, so `config.carriers.length > 0` and the carrier check fails for any real carrier |
| M15 | **Status vocabulary on the legacy side is unrelated.** Firebird gets the raw carrier code and derives its own integer status. ECM's GFS group never reaches Firebird. Unknown codes become 207. DPD and Interlink code 17 follows a text-prefix ladder with 202 as the default | `procedures.sql:9476-9640`; vault `architecture.md` G2 (STATED) | CONFIRMED for the procedure text. The procedure is from a Dec 2025 dump |
| M16 | **Unmapped events look mapped.** An unmapped code becomes group `IN_TRANSIT`, visible to customers, with the carrier's own text. The `isUnmapped` flag is stored on the mapped event and ignored by the webhook. Only CCIS publishes unmapped codes | `map-tracking.js:50-56`, `config.js:94-106`; `tracking-handler.js:92`; prod cluster@a317dc0 grep | CONFIRMED |
| M17 | **tracking-core's own derived status is parcel-only and thin.** It POSTs only that parcel's mapped events to the deriver sidecar and keeps only a DELIVERED or IN_TRANSIT bucket. The shipment-level status (PARTIALLY_DELIVERED, precedence across parcels, ETA, visibility variants) comes from the deriver's separate asynchronous subscriber. Same function, two inputs, two outputs | `RemoteTrackingStatusV2Getter.cs:35-63`, `tracking-core.yaml:399-400,521-565`, `expired-window-tracking-status-v2.js:28-39` | CONFIRMED |
| M18 | **The same precedence rule is written four times**, with different scores. CCIS's fallback uses DELIVERED 3, OUT_FOR_DELIVERY 2, anything else 1, then sorts ascending and takes the first element, which reads as the lowest score. That is the fallback path only (used when no pre-derived status exists). It looks like a possible inversion, not run | `consignment-status.ts:10-13` and the final `nonDataEvents.sort(compareStatus)` (CCIS@b2af452), `derive-shipment-tracking-status-v2.js:19-41` | CONFIRMED the code reads that way. That it misbehaves: UNKNOWN, needs a test |
| M19 | **Ordering is partial.** `raw_tracking.v1` has no ordering key (tracking-core sets none and attaches no attributes, `EventPublisher.cs:54`). webhook-core publishes with `attributes.carrierId` only (`tracking.service.ts:58-60`). Only `shipment_tracking_status.v2` is ordered, by `shipmentId` | | CONFIRMED |
| M20 | **A 60-second debounce sits in the deriver.** A shipment's status is recalculated one window after its last event (`WINDOW_EXPIRY_SECONDS` default 60) and published twice (`ALL` and `CUSTOMER_VISIBLE`). Status latency has a built-in floor that customers of the webhook do not share | deriver `config.js:29`, `expired-window-tracking-status-v2.js:28-39` | CONFIRMED default. The prod value of the window env: not checked |
| M21 | **The raw carrier response is on every event** (`rawData[]`) and so reaches every subscriber. It may hold personal data (stated in the MPK page) | `ConnectorResponseHandler.cs:103-119` | CONFIRMED that it is attached. The personal-data claim: STATED |
| M22 | **Drift between the deployed deriver and the repo.** The prod manifest for the deriver sidecar in tracking-core uses image tag `shipment-tracking-status-deriver:prod-53270`, which I could not map to a git sha. The ecm-development doc says the standalone deriver deployment ran the legacy Azure image. Several tracking-core env vars in prod have no code binding in this clone (companion file) | `tracking-core.yaml:521-522` | UNKNOWN whether the cloned source is what runs |

### What MPK 355074077 got right and wrong (checked against code)

| Claim | Verdict |
| --- | --- |
| Row 1: tracking-core publishes the raw event and throws its own mapping away | CONFIRMED (stored, not published) |
| Row 2: each publisher mints an ObjectId | CONFIRMED for tracking-core, webhook-core, file-processor |
| Row 3: no ordering key on raw_tracking.v1, ordered only on status.v2 by shipment | CONFIRMED |
| Row 6: unmapped becomes IN TRANSIT, only CCIS publishes unmapped | CONFIRMED |
| Row 7: GFS_DELIVERED_EVENT has no id and no company | CONFIRMED. "CCIS, ICIS and claims drop or store it" not read |
| Row 8: webhook body lacks event id, status code, ETA, location, signatory | CONFIRMED |
| "ECM keeps the raw code beside the derived status. Every event carries both." | Partly wrong as stated: `raw_tracking.v1` carries the raw code only. The mapped result is stored on the parcel and in each consumer's store, never published with the raw event |
| "The deriver rates each shipment RED, AMBER or GREEN" | CONFIRMED |

---

## What I could not verify

- The prod tracking mapping spreadsheet: the full list of GFS codes, groups and `isDelivered` values. The only checks were the code, the CCIS validator list and one doc.
- Whether any prod subscription filters on the `groupId` attribute.
- Who writes legacy scans to `scanners.consignments.V1` in prod (patina disabled by config, Dataflow job source not found, `patina-service-2` not found in ADO or locally).
- What the Firebird side does with a scan after `scanners.consignments.V1` (scan injector, `SET_PARCEL_HIST`): not in source here.
- CCIS and ICIS stores beyond one mapping file and one validator, claims-service, `gfs-pod` (no POD type found, but not read).
- The Go filter enum (`consignment-query-service/consts/enums.go`): repo not reachable.
- The deletion event type from `gfs-modernizer`.
- Whether the deployed images match these shas.
- Per-carrier connector output: which carriers fill `additionalData`, a failure reason, location, signatory or a delivery window.
- Exception RAG assignment per code (in the same sheet).

## Pointers for a replacement (not recommendations)

Things the code shows a replacement would have to carry, stated as facts:
- The raw event shape is the de facto public contract, and every consumer parses it independently. `parcel.shipmentId`, `parcel.parcelNumber`, `parcel.company` and `id` are the fields consumers depend on (connect-hooks drops events with no `company`; the deriver throws on no `shipmentId`, `tracking.js:5-8`).
- A status has more structure than a string: group, GFS code, text, visibility, delivered, RAG, plus signatory or ETA, in two visibility variants.
- The webhook currently sends a lossy projection of the group, and the legacy side sees only a raw code. Either could be left as is, or fixed, but the group-to-display mapping and the raw-code-to-Firebird path are both contracts today.
