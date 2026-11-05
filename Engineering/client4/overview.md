---
tags:
- waypoint
- client4
title: client4 — overview
thesis: 'Client4 (GFSClient4) is Selector''s Delphi 7 desktop app, installed on hosted VMs and customer PCs. Staff enter, import, label and manifest shipments in it. On the
  upload station it is also the site''s only link to GFS: it registers the site, pulls
  updates and uploads every committed shipment, CSS''s included.'
confidence: high
verified: '2026-11-05'
verified_paths:
- Client/Client.Alpha/dmClient.pas
- Client/Client.Alpha/uSoapUpload.pas
verified_sha: 73cfd69
---
# client4 — overview

```orient-bluf
{ "v": 1, "bluf": "Client4 (GFSClient4) is Selector's Delphi 7 desktop app, installed on hosted VMs and customer PCs. Staff enter, import, label and manifest shipments in it. On the upload station it is also the site's only link to GFS: it registers the site, pulls updates and uploads every committed shipment, CSS's included.", "confidence": "high", "action": "Find the site's UPLOAD_STATION = 1 PC first when shipments aren't reaching GFS." }
```

## Responsibility
- The warehouse UI: shipment entry, file import, customs, label printing, reprints, manifests, returns, address book.
- Carrier calls for the carriers it handles itself, through `Carriers/` units and generated SOAP clients.
- **On the upload station only** (`UPLOAD_STATION = 1`): it talks to the central upload server. It uploads committed shipments, downloads carrier and gazetteer updates, registers the site and departments, and polls site status [1][2].

## Why it exists separately
It is the original Selector, and CSS came later as a machine interface to the same database. Client4 keeps the jobs that need a person or a long-lived process at the site, such as uploads, updates and registration.

## Neighbours

```orient-flow
{ "v": 1, "title": "client4 in context",
  "nodes": [
    { "id": "staff", "label": "Warehouse staff", "kind": "external" },
    { "id": "files", "label": "Import files", "sub": "WMS drops", "kind": "external" },
    { "id": "c4", "label": "Client4", "sub": "GFSClient4.exe", "kind": "service", "tone": "accent" },
    { "id": "fdb", "label": "Site GFS.FDB", "sub": "events", "kind": "store" },
    { "id": "css", "label": "CSS", "kind": "service" },
    { "id": "upl", "label": "Upload server", "sub": "IUploadServer SOAP", "kind": "external" },
    { "id": "carriers", "label": "Carriers", "kind": "external" }
  ],
  "edges": [
    { "from": "staff", "to": "c4" },
    { "from": "files", "to": "c4", "label": "import" },
    { "from": "c4", "to": "fdb" },
    { "from": "css", "to": "fdb", "label": "SHIP_COMMITED" },
    { "from": "fdb", "to": "c4", "label": "events", "ev": [1] },
    { "from": "c4", "to": "upl", "label": "upload, updates, register", "ev": [2] },
    { "from": "c4", "to": "carriers", "label": "label" }
  ] }
```

## Where the reference lives
- [[architecture]] covers the code layout, the event loop, the upload modes and the guardrails. [[known-context]] covers the traps.
- The system view is in the `selector` system: data flow, registration and the shared database.
- `ImportDocumentation/` in the repo holds the file import specs (V2.x, V4.4, 5.3).

## What deliberately isn't here
- **The SOAP API for integrators.** That's [[css]].
- **The central upload server and Manager.** These live in the `V4-Server-*` repos. The `Server/*` folders in this repo are only pointers to them.

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "Client/Client.Alpha/dmClient.pas@73cfd69:L2096" },
  { "id": 2, "kind": "code", "ref": "Client/Client.Alpha/uSoapUpload.pas@73cfd69:L410" }
] }
```
