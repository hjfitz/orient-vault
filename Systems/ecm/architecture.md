---
tags:
- system
- ecm
verified: '2026-11-09'
title: ecm — architecture
thesis: "Selector and ECM meet at central Firebird. Either can be replaced on its own if the successor honours Firebird's contract on its side, but the contract is leaky: about 30 procedures write STATUS and nothing in it is versioned. Six seams carry the traffic, and three cut points are options for the Merak team."
confidence: moderate
---
# ecm: architecture

```orient-bluf
{ "v": 1, "bluf": "Selector and ECM meet at central Firebird. Either can be replaced on its own if the successor honours Firebird's contract on its side, but the contract is leaky: about 30 procedures write STATUS and nothing in it is versioned. Six seams carry the traffic, and three cut points are options for the Merak team.", "confidence": "moderate", "action": "A Selector successor must write central SHIPMENTS and publish the create message. An ECM successor must publish raw carrier scans to scanners.consignments.V1." }
```

Source: MPK *Selector and ECM Coupling* (354418743), a published draft that no verification run has checked, and its challenge findings [1][2]. Production Firebird triggers were never read. Treat every claim here as `moderate` until they are.

## Guardrails
- [contract:G1] Firebird is the seam. A successor honours its side. A Selector successor writes central `SHIPMENTS` for billing and publishes the create message for ECM. An ECM successor publishes raw carrier scans to `scanners.consignments.V1`. - paths: Firebird Transfer Service sql, node-modernizer src/translators/shipment-translator.js, patina-service-2 ReadMe.md, gfs-pipelines FIREBIRD_DDL/procedures.sql
- [contract:G2] ECM forwards the carrier's raw code, and Firebird derives the status. `GET_SCAN_CODE` maps the code. An unknown code becomes status 207 (202 for DPD and Interlink code 17). Never send ECM's own derived status. - paths: gfs-pipelines FIREBIRD_DDL/procedures.sql, patina-service-2 ReadMe.md
- [technical:G3] `gfs-modernizer` rejects a shipment whose carrier is not in the almanac. It nacks, Pub/Sub redelivers, and nothing dead-letters it. A new carrier needs an almanac entry first. - paths: node-modernizer src/message-handlers/helpers.js, src/window-processor.js
- [technical:G4] A tracking source must set `id`, `parcel.shipmentId`, `parcel.parcelNumber` and `parcel.company`. Each publisher mints its own event ID and consumers dedupe on it alone, so one scan from two sources lands twice. No `raw_tracking.v1` publisher sets an ordering key. - paths: tracking-core ConnectorResponseHandler.cs, tracking-webhooks packages/tracking-webhook-core
- [operational:G5] Identity is consignment number plus carrier, because a consignment number alone is reused (ranges wrap and Selector restores re-issue numbers, stated in the repo's design doc). The service mints a counter `shipmentId` on first sight and a Mongo expiry deletes the record 30 days after first insert, so a re-sent shipment gets a new ID. `shipmentIdV2` is a stateless hash and stays stable. Invoice lines match on the same pair. The code read matches what is deployed (one publish run, no source change since); the live expiry value is not read. - paths: shipment-identity-service src/data-access/shipment-repository.js, src/data-access/id-generator.js, src/init/index.js, Documentation/shipment-identity-service-index.md
- [technical:G7] The mint is two writes (upsert, then set the ID), so two close messages for one new shipment can each mint an ID. A save followed by a failed publish makes the redelivery look like a repeat and drops it. Both are read from code and not run. - paths: shipment-identity-service src/data-access/shipment-repository.js
- [contract:G8] The ID is customer-visible: webhook bodies carry it as `gfsId` and Connect returns it. A replacement for the identity step keeps that value, whatever it changes inside. Not every ECM store keys on it: the POD cache keys on carrier, consignment number and parcel. - paths: connect-hooks src/tracking-handler.js, gfs-pod src/pod-cache.js
- [operational:G6] Early scans wait. The Royal Mail webhook parks events until the shipment is known: about 146k of 343k in the canonical window. The Evri service reads held events for up to 90 days (a read cutoff, TTL indexes not confirmed). `tracking-core` tracks a parcel for 90 days after its last new event. - paths: tracking-webhook-royal-mail-sapient handler/src/services/tracking.service.ts, tracking-core ActiveParcelDomain.cs

## Firebird as the seam

Firebird is not a separate system here. It has no repo of its own in these sources, and its contract is defined by the two systems that meet at it. So it sits in this file.

```orient-flow
{ "v": 1, "preset": "data-flow", "title": "Where Selector and ECM meet",
  "nodes": [
    { "id": "sel", "label": "Selector", "sub": "Client4 upload, CSS", "kind": "external" },
    { "id": "fb", "label": "Central Firebird", "sub": "SHIPMENTS, status", "kind": "store", "tone": "accent" },
    { "id": "fts", "label": "Transfer Service", "sub": "fb.shipments.v1", "kind": "service" },
    { "id": "ecm", "label": "ECM", "sub": "shipments.v2.identified", "kind": "service" },
    { "id": "raw", "label": "raw_tracking.v1", "sub": "carrier scans", "kind": "topic" },
    { "id": "inj", "label": "Scan Injector", "sub": "SET_PARCEL_HIST", "kind": "step" }
  ],
  "edges": [
    { "from": "sel", "to": "fb", "label": "upload" },
    { "from": "fb", "to": "fts", "label": "triggers" },
    { "from": "fts", "to": "ecm", "label": "create message" },
    { "from": "ecm", "to": "raw", "label": "tracking events" },
    { "from": "raw", "to": "inj", "label": "legacy-shaped scans", "style": "dashed" },
    { "from": "inj", "to": "fb", "label": "status procedures" }
  ] }
```

The seams form a loop. ECM scans change Firebird rows, and those changes flow back into ECM as re-announcements.

| Seam | Runs from and to | What crosses |
| --- | --- | --- |
| 1. Shipments | Selector to Firebird to ECM | `fb.shipments.v1`, then `shipments.v2`, then `shipments.v2.identified` |
| 2. Scans and status | ECM to Firebird | `scanners.consignments.V1`, then the status procedures. Selector's IE service is a second writer |
| 3. Manual changes | Portals and agents to Firebird | Mark as deleted or delivered (100, 1003), status changes, tickets, comments, collections |
| 4. Reference data | Firebird to ECM | Customers, contracts, carriers and products as `fb.*` feeds. Manager writes the tables behind them. Carrier credentials cover six carriers |
| 5. Billing | Firebird to billing to ECM | The billing app reads `SHIPMENTS`. Invoices return as `invoices_published.v1` |
| 6. Identity | `shipment-identity-service` | The consignment and carrier pair that gives each shipment its ID |

**Not on the seam list.** The data platform extracts about 70 tables straight from Firebird. Billing and Seeker also read it directly. Slipway publishes the Firebird-shaped create message straight to `fb.shipments.v1`, around Firebird, and also exports a masked copy for billing. No direct Selector to ECM call exists: a search of the Selector repo found no Pub/Sub, `raw_tracking` or `tracking-core` reference.

**Why it is a weak seam:**
- About 30 procedures write `STATUS`, from commit and legacy scanners to the portals.
- Some columns carry more than one meaning, so `node-modernizer` hard-codes carrier rules.
- The December 2025 dump holds no triggers, and nobody has read the production ones.
- Nothing in the feeds or the procedures is versioned.
- No team owns `patina-service-2` or the Scan Injector.

## Three cut points (hypothetical options)

These are options for the Merak team. No decision exists, and the replacement itself is an unconfirmed hunch. Each keeps the legacy side running, and none removes Firebird.

1. **The shipment message.** A replacement for Selector, Firebird and the Transfer Service publishes `shipments.v2` or `fb.shipments.v1`. Slipway already does the second for Amazon shipments. A new publisher needs the carrier in the almanac, or the message is rejected.
2. **The scan write-back.** A replacement for ECM's tracking publishes legacy-shaped scans to `scanners.consignments.V1`, with the carrier's raw code in `carrCode`. `patina-service-2` does this today from `raw_tracking.v1`.
3. **The manual status route.** A replacement for the portals keeps calling the legacy shipment update service. It sets `STATUS` 100 or 1003 for one consignment and carrier.

## Duties nobody wrote down

The old systems perform these without a document. Detail is on the MPK page [1].
- Roll parcel scans into one shipment status (`SET_SHIPMENT_HIST`).
- Close shipments nobody scans, with status 1005 (`CHECK_SHIP_STATUS`). The only caller in the dump is commented out, so who runs it is not confirmed.
- Classify an unknown carrier code (`GET_SCAN_CODE`).
- Absorb bursts of change: `gfs-modernizer` holds each shipment for a sliding 180 s.
- Guard re-uploads. Manager's replace renames the old row and inserts an unbilled copy, which can bill twice.
- Carry carrier identity three ways: Firebird's alias, the almanac's legacy name and a numeric ID.

The first three come from a December 2025 dump of the central procedures. The live database may differ.

## Carrier facts settled from code (2026-11-09)

- **CONFIRMED** `dhl-pod-images` exists, and the prod manifest points the pod service at it. Only the UK Mail SOAP module calls it. Prod sets `DHLECOMMERCEUK_USEINSTEADOFUKMAIL` to `true`, so DHL Parcel UK uses the eCommerce REST module, which takes images from DHL's own URLs [3].
- **CONFIRMED** DPD Local posts the parcel number it is given. It is not on the consignment POD list, so a caller must name the parcel. Who chooses the parcel on the v2 parcel route is not confirmed: `get-parcel-pod.js` was not read [3].
- **STATED** DHL Express is both a direct API call and a template: waybill and routing codes from DHL, with the label drawn from a template. The pod service's DHL Express module is not loaded and does not work. The code path for the first claim was not recorded [2].
- **STATED** TNT makes no carrier call and is disabled in seed data. Nightline and Nightfreight are two carriers. The Royal Mail proxy column is `GFS_RM_URL`. The code paths were not recorded [2].

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "doc", "ref": "Confluence MPK 354418743 Selector and ECM Coupling (draft, unverified); Handovers/2026-11-09-merak-replacement-pages.page1-selector-ecm-coupling.md" },
  { "id": 2, "kind": "doc", "ref": "Handovers/2026-11-09-merak-replacement-pages.md (cleanup pass) and page1-challenge-findings.md: Slipway shipment.mapper.ts and usv2export.service.ts at f604bdd, Selector V4-Server-IE/Source/uSQL.pas, node-modernizer shipment-translator.js, patina-service-2 ReadMe.md, gfs-pipelines FIREBIRD_DDL/procedures.sql" },
  { "id": 3, "kind": "doc", "ref": "ADO GFS POD master d1f0ada src/config.js, src/pod-service/ukmail-service.js, src/pod-service/dpdlocal-service.js; prod-uk1-primary-cluster deploy/k8s/pod-server/pod-service.yaml (read 2026-11-09)" }
] }
```
