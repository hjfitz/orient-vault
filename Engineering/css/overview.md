---
tags: [waypoint, css]
title: css — overview
thesis: "CSS (ClientShipService) is Selector's SOAP front door: an ASP.NET ASMX service on each customer's GFS-hosted box. It validates, labels, manifests and reports shipments against that site's GFS.FDB, so integrations can ship without Client4's screens. It doesn't upload: Client4 does."
confidence: high
verified: 2026-11-05
---
# css — overview

```orient-bluf
{ "v": 1, "bluf": "CSS (ClientShipService) is Selector's SOAP front door: an ASP.NET ASMX service on each customer's GFS-hosted box. It validates, labels, manifests and reports shipments against that site's GFS.FDB, so integrations can ship without Client4's screens. It doesn't upload: Client4 does.", "confidence": "high", "action": "Check that a customer's upload-station Client4 is running before blaming CSS for missing shipments." }
```

## Responsibility
- Exposes 35 SOAP operations on `ClientShipService.asmx`: shipment processing, validation, manifests, carrier dispatch, lookups and address book or goods import and export [1].
- Authenticates each call against the site's `web_users` table [2].
- Validates a shipment against the site's contracts, services, routes and gazetteer, then gets a label from the carrier.
- Stores shipments in the site DB and marks them committed. Committing fires `SHIP_COMMITED` for Client4 to upload [3].

## Why it exists separately
Client4 is a desktop app. CSS gives a customer's WMS a machine interface to the same site database. The WMS can then book without a person at a screen. It shares the database and the business rules, but not the code. CSS is C# and carries its own copy of the carrier logic.

## Neighbours

```orient-flow
{ "v": 1, "title": "css in context",
  "nodes": [
    { "id": "callers", "label": "Callers", "sub": "WMS, selector-rest-proxy, selector-adapter, Parcel Portal", "kind": "external" },
    { "id": "css", "label": "CSS", "sub": "ClientShipService.asmx", "kind": "service", "tone": "accent" },
    { "id": "fdb", "label": "Site GFS.FDB", "kind": "store" },
    { "id": "carriers", "label": "Carriers", "sub": "direct APIs, GFS proxies", "kind": "external" },
    { "id": "client4", "label": "Client4", "sub": "upload station", "kind": "service" }
  ],
  "edges": [
    { "from": "callers", "to": "css", "label": "SOAP" },
    { "from": "css", "to": "fdb", "label": "GFSConn" },
    { "from": "css", "to": "carriers", "label": "label, manifest" },
    { "from": "fdb", "to": "client4", "label": "SHIP_COMMITED", "ev": [3] }
  ] }
```

## Where the reference lives
- [[architecture]] covers the operations, the code layout and the guardrails. [[known-context]] covers the history and the traps.
- The system view is in the `selector` system: data flow, set-up and the shared database.
- `vzClientSoapServer/docs` holds the test pack and FedEx sample requests. `LocalSwagger/` holds copies of the carrier-proxy OpenAPI specs.

## What deliberately isn't here
- **Uploading to GFS.** Client4 does it ([[client4]]).
- **Customer set-up.** Manager and registration write the site DB. CSS only reads that set-up.
- **The REST facade.** That's [[selector-rest-proxy]].

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "vzClientSoapServer/ClientShipService.asmx.cs@414569b" },
  { "id": 2, "kind": "code", "ref": "vzClientSoapServer/InternalProcedures/CommonProcedures.cs@414569b:L25" },
  { "id": 3, "kind": "code", "ref": "vzClientSoapServer/InternalProcedures/ProcessShipProcedures.cs@414569b:L4498" }
] }
```
