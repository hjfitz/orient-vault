---
tags: [explain]
date: '2026-11-06'
title: A shipment reaches ECM only after upload, then every service rebuilds it from raw scans until a POD is fetched live on read
thesis: "A label lives only in Selector until upload; then Firebird CDC, gfs-modernizer and shipment-identity-service announce it to 17 subscribers, tracking-core and the webhooks publish raw carrier scans, each consumer derives status and 'delivered' itself, and gfs-pod fetches the POD live from the carrier on read."
confidence: high
---
# A shipment reaches ECM only after upload, then every service rebuilds it from raw scans until a POD is fetched live on read

```orient-bluf
{ "v": 1, "bluf": "A label lives only in Selector until upload; then Firebird CDC, gfs-modernizer and shipment-identity-service announce it to 17 subscribers, tracking-core and the webhooks publish raw carrier scans, each consumer derives status and 'delivered' itself, and gfs-pod fetches the POD live from the carrier on read.", "confidence": "high", "action": "Place any carrier change on the stage table first: label work is invisible to ECM until upload, and tracking work must publish raw_tracking.v1 with an id, shipmentId and company." }
```

> Companion: [[2026-11-06-ecm-event-world-where-its-a-mess]] diagnoses the design. Volumes cover the 15 days to 2026-11-06.

## Situation
- **CONFIRMED** Twelve stages carry one Selector shipment from label to invoice. The table below gives each stage's services and the shipment's shape. [1][2][4][5]

```orient-flow
{ "v": 1, "title": "One Selector shipment, label to POD",
  "nodes": [
    { "id": "sel", "label": "Selector", "sub": "CSS, Client4 label", "kind": "external" },
    { "id": "fb", "label": "Central Firebird", "sub": "SHIPMENTS after upload", "kind": "store" },
    { "id": "fts", "label": "Firebird Transfer Service", "sub": "fb.shipments.v1", "kind": "service" },
    { "id": "mod", "label": "gfs-modernizer", "sub": "180 s window", "kind": "service", "ev": [2] },
    { "id": "sis", "label": "shipment-identity-service", "sub": "mints shipmentId", "kind": "service", "ev": [3] },
    { "id": "idn", "label": "shipments.v2.identified", "sub": "17 subscribers", "kind": "topic", "tone": "accent" },
    { "id": "trk", "label": "tracking-core, webhooks, files", "sub": "poll, push, SFTP", "kind": "service", "ev": [4] },
    { "id": "raw", "label": "raw_tracking.v1", "sub": "6.29M per 15 d", "kind": "topic", "tone": "accent" },
    { "id": "stsd", "label": "status deriver", "sub": "60 s window", "kind": "service", "ev": [5] },
    { "id": "ccis", "label": "CCIS, ICIS", "sub": "consignment records", "kind": "store", "ev": [5] },
    { "id": "out", "label": "Portal, Connect, webhooks", "kind": "external" },
    { "id": "pod", "label": "gfs-pod-service", "sub": "live carrier fetch", "kind": "service", "service": "gfs-pod-service", "ev": [6] }
  ],
  "edges": [
    { "from": "sel", "to": "fb", "label": "commit, upload" },
    { "from": "fb", "to": "fts", "label": "trigger" },
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
| 0 Label | CSS or Client4; carrier proxy, template or direct API | Rows in the site's `GFS.FDB` | `CONS_NO` comes from `SHIP_RANGES`. A proxy returns the carrier's tracking number. No event exists |
| 1 Upload | Client4 upload station, upload server | Central `SHIPMENTS` and `SHIP_PIECES` rows | Billing and pre-advice can now see it |
| 2 CDC | Firebird trigger, `TRANSFER_QUEUE`, on-prem Transfer Service | `fb.shipments.v1`: `{event_type, data.SHIPMENTS{…}}` | Rows become messages. Median lag 7.6 s, p95 up to 26 min |
| 3 Translate | `gfs-modernizer` | `shipments.v2`: `consignmentNumber`, `carrier{id, idV2}`, `customer{company}`, `declaredDespatchDate`, `parcels[]` | Gathers parcels for 180 s. Resolves the carrier through the almanac. Names the tenant. Drops `STATUS` and invoice fields |
| 4 Identity | `shipment-identity-service` | `shipments.v2.identified` = input + `shipmentId` + `shipmentIdV2` | Mints `shipmentId` from a counter. `shipmentIdV2` = md5(`idV2` + cons + date) |
| 5 Fan-out | 15 in-project, 2 cross-project subscribers | About 8 separate copies | `tracking-core` opens one `active-parcels` record per parcel |
| 6 Scan | connector over gRPC to `tracking-core`; Royal Mail webhook; file processor | `raw_tracking.v1` `TrackingEvent`: `id`, `parcel{…}`, carrier `statusCode`, `reportedDate`, `delivery`, `signatory`, `rawData` | `tracking-core` dedupes on date plus code. Its GFS mapping stays in Mongo |
| 7 Derive | each consumer's mapper; status deriver | `shipment_tracking_status.v2`: `{code, text, groupId, eta}`; exception status | ETA comes from the carrier's delivery window |
| 8 Show | CCIS, ICIS, `connect-hooks`, reporting | CCIS consignment: lowercased `attributes[]`, `parcels[].tracking.events`, `trackingStatus` | Customers see status and ETA. 6.5% of scans become customer webhooks |
| 8b Write-back | `patina-service-2` (Dataflow), staging topic, on-prem Scan Injector | `scanners.consignments.V1`: one consignment, `parcels[].states[]{carrCode, scanDate, scanText, signBy}` | Seeker and bill-on-scan see the scans. The injector runs 06:00 to 23:01 UTC |
| 9 Delivered | same path | `trackingStatus` DELIVERED, with `signatory` in place of `eta` | Claims records `deliveredDate`. Each service decides "delivered" itself |
| 10 POD | portal or Connect, then `gfs-pod-service` | `{signee, deliveryDateTime, images, deliveryAddress}`, cached 1 h | Fetched from the carrier on read. Never published |
| 11 Invoice | billing app on Firebird, `legacy-invoice-translator`, CCDIS | `invoiced_shipments_published.v1`: `{shipmentId, invoiceNumber, shipmentCost}` | CCIS, ICIS, claims and SUS add invoice fields |

## Assessment
> What the journey means for carrier integrations.
- **CONFIRMED** The label side emits no events. No proxy publishes a label, manifest or "Picked" event. ECM first hears of a shipment after upload. [1][4]
- **CONFIRMED** A labelled shipment that never uploads gets no ECM tracking, portal view or POD record. Fuse's commit gap (R5) lands here. [2]
- **CONFIRMED** A new carrier needs an almanac entry first. `gfs-modernizer` dead-letters a shipment whose carrier it cannot resolve. [2]
- **CONFIRMED** A tracking source must set `id`, `parcel.shipmentId` and `parcel.company`. CCIS, ICIS and `connect-hooks` drop events without them. Both webhooks set all three. [4][5]
- **CONFIRMED** ECM scans flow back to Firebird. `patina-service-2` on Dataflow reads `raw_tracking.v1` and publishes legacy scans to a topic in the staging project. [7]
- **CONFIRMED** An on-prem Scan Injector writes them into `SHIP_PIECES_HIST` from 06:00 to 23:01 UTC: 4.51M messages in 15 days. No team claims it in any source checked. [8]
- **CONFIRMED** The Kubernetes `tracking-patina-service` and `tracking-core`'s legacy publisher are both off. They are not the write-back path. [7]
- **ASSESSED** The injector's `SET_PARCEL_HIST` procedure moves central `STATUS`, so bill-on-scan billing depends on ECM tracking. Its source sits in the unreachable legacy org. [8]
- **CONFIRMED** Manual mark-as-delivered updates Firebird, but every ECM status consumer drops its synthetic event. [5]
- **CONFIRMED** Signatories already ride `raw_tracking.v1` for the Evri connector and BJS files. No POD image does. [4]

## Open items
| Item | Owner | By |
|---|---|---|
| Name an owner for `patina-service-2` and the Scan Injector, and read `SET_PARCEL_HIST` | Harry | UNKNOWN |
| Read patina-2's supported-carrier list (ADO variable group 141) | Harry | UNKNOWN |
| Measure how often a re-insert wipes STSD's parcel history | carriers team | UNKNOWN |
| Decide Evri cutover dedupe: consumers key on `id`, so connector plus webhook doubles history | carriers team | UNKNOWN |

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "doc", "ref": "Systems/selector/architecture.md (Getting a label; Day end and billing handoff)" },
  { "id": 2, "kind": "doc", "ref": "ADO GFS Legacy Migration/node-modernizer@master src/window-processor.js, src/translators/shipment-translator.js; Firebird Transfer Service@8569227 sql/0_fts_initial_setup.sql" },
  { "id": 3, "kind": "code", "ref": "shipment-identity-service/src/data-access/id-generator.js@7454a4e" },
  { "id": 4, "kind": "doc", "ref": "Research track 'producers', 2026-11-06: tracking-core@c081108, tracking-webhook-royal-mail-sapient@3c880bf handler/src/services/tracking.service.ts, tracking-webhooks@9777dd4, tracking-file-processor@e6da4bf" },
  { "id": 5, "kind": "doc", "ref": "Research track 'consumers', 2026-11-06: STSD@a3dc446, CCIS@b2af452, ICIS@3d125f5, SUS@ccec388, claims@584d827, connect@6c6d527" },
  { "id": 6, "kind": "doc", "ref": "Engineering/gfs-pod-service/architecture.md; MPK 353861642 Proof of Delivery Service" },
  { "id": 7, "kind": "doc", "ref": "ADO GFS Legacy Migration/patina-service-2 pipeline/aggregate/filter.go and README; pipeline patina-service-2-prod build 57328 (2026-11-03); gfs-ecm-prod-uk1 main.tf fenghuang-dataflow-legacy-tracking-service; tracking-patina-service@8edfb3e (CARRIERS=NONE)" },
  { "id": 8, "kind": "log", "ref": "Datadog gfs.doppelganger.received / injected, host MEDC-APP-01-P, 2026-10-22 to 2026-11-06; service gfs.doppelganger.scan-injector errors citing SET_PARCEL_HIST and FK_SHIP_PIECES_HIST" }
] }
```
