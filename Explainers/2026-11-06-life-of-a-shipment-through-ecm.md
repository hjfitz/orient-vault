---
tags: [explain]
date: '2026-11-06'
title: A shipment reaches ECM only after upload, then every service rebuilds it from raw scans until a POD is fetched live on read
thesis: "A Selector label reaches ECM only after Client4 uploads it into central Firebird, and the Transfer Service, gfs-modernizer and shipment-identity-service then announce it to 19 subscriptions. Raw carrier scans flow through raw_tracking.v1 to consumers that each derive status, and back into Firebird's status through the Scan Injector, while gfs-pod fetches the POD live on read."
confidence: high
---
# A shipment reaches ECM only after upload, then every service rebuilds it from raw scans until a POD is fetched live on read

```orient-bluf
{ "v": 1, "bluf": "A Selector label reaches ECM only after Client4 uploads it into central Firebird, and the Transfer Service, gfs-modernizer and shipment-identity-service then announce it to 19 subscriptions. Raw carrier scans flow through raw_tracking.v1 to consumers that each derive status, and back into Firebird's status through the Scan Injector, while gfs-pod fetches the POD live on read.", "confidence": "high", "action": "Place carrier work on the stage table first. Label work is invisible to ECM until upload. A tracking source must publish raw_tracking.v1 with id, shipmentId, parcelNumber and company. A new carrier needs an almanac entry, mapping rows and a place on patina-service-2's carrier list." }
```

> Companion: [[2026-11-06-ecm-event-world-where-its-a-mess]] diagnoses the design. The team-facing version is MPK *Shipment Journey Through ECM* (354975746). Volumes cover the 15 days to 2026-11-06. Every claim was re-checked against code, Terraform and Datadog on 2026-11-09.

## Situation
- **CONFIRMED** Thirteen stages carry one Selector shipment from label to invoice. The table gives each stage's services and the shipment's shape. [1][2][4][5]

```orient-flow
{ "v": 1, "title": "One Selector shipment, label to POD",
  "nodes": [
    { "id": "sel", "label": "Selector", "sub": "Client4 upload station", "kind": "external" },
    { "id": "fb", "label": "Central Firebird", "sub": "SHIPMENTS, status", "kind": "store" },
    { "id": "fts", "label": "Firebird Transfer Service", "sub": "fb.shipments.v1", "kind": "service" },
    { "id": "mod", "label": "gfs-modernizer", "sub": "sliding 180 s window", "kind": "service", "ev": [2] },
    { "id": "sis", "label": "shipment-identity-service", "sub": "mints shipmentId", "kind": "service", "ev": [3] },
    { "id": "idn", "label": "shipments.v2.identified", "sub": "19 subscriptions", "kind": "topic", "tone": "accent" },
    { "id": "trk", "label": "tracking-core, webhooks, files", "sub": "poll, push, SFTP", "kind": "service", "ev": [4] },
    { "id": "raw", "label": "raw_tracking.v1", "sub": "6.29M per 15 d", "kind": "topic", "tone": "accent" },
    { "id": "stsd", "label": "status deriver", "sub": "sliding 60 s window", "kind": "service", "ev": [5] },
    { "id": "ccis", "label": "CCIS, ICIS", "sub": "consignment records", "kind": "store", "ev": [5] },
    { "id": "out", "label": "Portal, Connect, webhooks", "kind": "external" },
    { "id": "pod", "label": "gfs-pod-service", "sub": "live carrier fetch", "kind": "service", "service": "gfs-pod-service", "ev": [6] }
  ],
  "edges": [
    { "from": "sel", "to": "fb", "label": "commit, SOAP upload" },
    { "from": "fb", "to": "fts", "label": "triggers" },
    { "from": "fts", "to": "mod" },
    { "from": "mod", "to": "sis", "label": "shipments.v2" },
    { "from": "sis", "to": "idn" },
    { "from": "idn", "to": "trk", "label": "what to track" },
    { "from": "idn", "to": "ccis" },
    { "from": "idn", "to": "pod", "label": "own copy" },
    { "from": "trk", "to": "raw" },
    { "from": "raw", "to": "stsd" },
    { "from": "raw", "to": "fb", "label": "patina-2, Scan Injector", "style": "dashed" },
    { "from": "raw", "to": "ccis", "label": "events" },
    { "from": "stsd", "to": "ccis", "label": "status" },
    { "from": "ccis", "to": "out" },
    { "from": "out", "to": "pod", "label": "POD on read" }
  ] }
```

### Stage by stage

| Stage | Services | The shipment is | What changes |
|---|---|---|---|
| 1 Label | CSS or Client4; carrier proxy, template or direct API | Rows in the site's `GFS.FDB` | `CONS_NO` comes from `SHIP_RANGES`. Nothing is published to Pub/Sub |
| 2 Upload | Client4 on the `UPLOAD_STATION = 1` PC, central upload server | Central `SHIPMENTS`, `SHIP_PIECES` | `REG_SHIPMENTS` inserts it; a known consignment goes to `RECYCLE_SHIPS`. Upload Service v2 and DataBridge are a second route for customer files |
| 3 Replicate | Firebird triggers, on-prem Transfer Service | `fb.shipments.v1`: `{event_type, data.SHIPMENTS{…}}` | Shipment median lag 7.5 s; p95 usually under 10 s |
| 4 Translate | `gfs-modernizer` | `shipments.v2`: `consignmentNumber`, `carrier{id, idV2}`, `customer{company}`, `customs`, `parcels[]` | Sliding 180 s window. Keeps only `isDeleted` and `wasManuallyUpdated` from STATUS |
| 5 Identify | `shipment-identity-service` | + `shipmentId`, `shipmentIdV2` | New `shipmentId` once 30 days pass since first insert. `shipmentIdV2` stays stable |
| 6 Fan out | 17 in-project subscriptions, 2 webhook push subscriptions | At least 8 copies | `tracking-core` opens one record per parcel |
| 7 Scan | connectors over gRPC to `tracking-core`; Royal Mail webhook; file processor | `raw_tracking.v1` `TrackingEvent` with the carrier's raw `statusCode` | `tracking-core` dedupes on date plus code and keeps its mapping in Mongo |
| 8 Derive | mapper sidecar in `tracking-core` and six consumers; status deriver | `shipment_tracking_status.v2`: `{code, text, groupId, eta}` | ETA from the carrier's delivery window |
| 9 Show | CCIS, ICIS, `connect-hooks`, reporting | CCIS consignment: lowercased `attributes[]`, events, `trackingStatus` | 6.5% of scans become customer webhooks |
| 10 Write back | `patina-service-2`, staging topic, on-prem Scan Injector | `scanners.consignments.V1`: `parcels[].states[]` | `SET_PARCEL_HIST` adds history; `SET_SHIPMENT_HIST` sets parcel and shipment status. Runs 06:00 to 23:01 UK time |
| 11 Delivered | same path | `trackingStatus` DELIVERED, signatory in place of ETA when given | Firebird reaches a delivered code. Each consumer decides "delivered" itself |
| 12 POD | portal or Connect, then `gfs-pod-service` | `{signee, deliveryDateTime, images, deliveryAddress}`, cached 1 h | Fetched on read. On v2 the address and coordinates are GFS's, geocoded |
| 13 Invoice | Firebird billing, `legacy-invoice-translator`, CCDIS | `invoiced_shipments_published.v1`, one message per invoice line | Mostly Monday runs. SUS then refuses mark-as-deleted |

### What can change it later

| Change | Caller | Writes | Reaches ECM? |
|---|---|---|---|
| Mark as deleted | Portal, via SUS and the legacy update service | Firebird `STATUS` 100 | Only before a physical scan or invoice; CCIS and ICIS then hide it |
| Mark as delivered | Portal, same path | `STATUS` 1003 plus `GFS_DELIVERED_EVENT` | No status change; claims and SUS store the event |
| Change status | CCP agent, via MQP and SeekerAPI | `STATUS` 2000 to 2999 | Unconfirmed; at most a manual-update flag |
| Query or ticket action | Portal, CCP or n8n, via MQP, Oz and SeekerAPI | Firebird tickets and comments | Yes: `shipment-queries`, `gfs-tickets` |
| Comment | Seeker, GFS Manager | Firebird comments | Yes: `shipment-comments.v1` |
| Claim | Portal, internal claims portal | claims-service | Yes: five claims topics |
| Collection | Portal, via collections-service | Firebird collections | Staff only, in ICIS |
| Extra number | gfs-modernizer | none | Yes: CCIS and ICIS `additionalNumbers` |

## Assessment
> What the journey means for carrier integrations.
- **CONFIRMED** No carrier proxy publishes to Pub/Sub. ECM first hears of a Selector shipment when it lands in central Firebird. Selector's own source was not reachable. [1][4]
- **CONFIRMED** Slipway publishes Amazon Logistics UK shipments straight to `fb.shipments.v1`, at pilot volume: about 66 records since August 2026. [9]
- **CONFIRMED** The Scan Injector calls `SET_SHIPMENT_HIST`, which sets `SHIPMENTS.STATUS`. For carriers on patina-2's list, bill-on-scan billing therefore depends on ECM tracking. [8][11]
- **CONFIRMED** Firebird replicates new shipments and a filtered set of updates, about 1.8 per new shipment. Parcel edits and invoice numbers never replicate. Nobody has read the production trigger text. [2][10]
- **ASSESSED** Daytime Scan Injector writes drive about half of all `SHIPMENTS` updates, and so many of the re-announcements. This rests on minute-level correlation; overnight backlog writes almost never fire. [8]
- **CONFIRMED** The Kubernetes `tracking-patina-service` and tracking-core's legacy publisher are both off. patina-service-2 does the write-back. [7]
- **CONFIRMED** No portal, API or staff tool edits a shipment's address or route. Those exist only as ticket requests that staff action by hand. [10]
- **CONFIRMED** A tracking source must set `id`, `parcel.shipmentId`, `parcel.parcelNumber` and `parcel.company`. Both webhooks set all four. [4][5]
- **CONFIRMED** An unknown carrier makes gfs-modernizer nack the message, so Pub/Sub keeps redelivering it. Nothing dead-letters it. [2]

## Open items
| Item | Owner | By |
|---|---|---|
| Read the production `SHIPMENTS` triggers with one query on central Firebird | DBA or legacy-org access | UNKNOWN |
| Read patina-2's carrier list (ADO variable group 141) and the bill-on-scan carriers | Harry, Billing team | UNKNOWN |
| Confirm the deployed delivered code for mark-as-delivered; 1003 reads as lost in UPS reporting | legacy-shipment-update-service owner | UNKNOWN |
| Name an owner for `patina-service-2` and the Scan Injector | Harry | UNKNOWN |
| Decide Evri cutover dedupe: consumers key on `id`, so connector plus webhook doubles history | carriers team (CID-315) | UNKNOWN |

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "doc", "ref": "Systems/selector/architecture.md (Getting a label; Day end and billing handoff); Engineering/client4/architecture.md" },
  { "id": 2, "kind": "doc", "ref": "ADO GFS Legacy Migration/node-modernizer@2350a1d src/window-processor.js, src/translators/shipment-translator.js, src/message-handlers/helpers.js; Firebird Transfer Service@8569227 sql/0 to sql/4" },
  { "id": 3, "kind": "code", "ref": "shipment-identity-service/src/data-access/id-generator.js@7454a4e" },
  { "id": 4, "kind": "doc", "ref": "tracking-core (ADO fenghuang) ConnectorResponseHandler.cs, ActiveParcelDomain.cs; tracking-webhook-royal-mail-sapient@3c880bf handler/src/services/tracking.service.ts; tracking-webhooks@9777dd4; carrier-proxies@a996061" },
  { "id": 5, "kind": "doc", "ref": "STSD@a3dc446, CCIS@b2af452, ICIS@3d125f5, SUS@ccec388, claims@584d827, connect@6c6d527" },
  { "id": 6, "kind": "doc", "ref": "ADO GFS POD master src/pod-service/pod-cache.js, src/api-v1/routes/get-pod.js; MPK 353861642 Proof of Delivery Service" },
  { "id": 7, "kind": "doc", "ref": "ADO fenghuang/tracking-patina-service (CARRIERS=NONE); prod-uk1-primary-cluster tracking-core.yaml (ShouldPublishToLegacy=false)" },
  { "id": 8, "kind": "log", "ref": "Datadog gfs.doppelganger.received / injected, gfs.firebird_transfer_service.rows_transfered, gfs.gfs_modernizer.messages, shipment_identity_service.ids_created; scan-injector error stacks (LegacyDataAccess.PostData lines 126 and 192), 2026-10-22 to 2026-11-09" },
  { "id": 9, "kind": "doc", "ref": "gfs-hybrid-services/slipway@f604bdd iac/env/prod.tfvars, code/src/factory.ts, processors/shipment.mapper.ts" },
  { "id": 10, "kind": "doc", "ref": "service-core@dc00bd4 customer-gateway typedefs; connect connect-gateway routes; gfs-customer-care oz-gateway@2a82870, tickets-handler@5334293, oz-admin-ui@9f911e7" },
  { "id": 11, "kind": "doc", "ref": "gfs-data-services/gfs-pipelines@b70e8ca gfs-data-iac/DEV/_planning/Sisense/FIREBIRD_DDL/procedures.sql (Dec 2025 dump: SET_PARCEL_HIST, SET_SHIPMENT_HIST)" }
] }
```
