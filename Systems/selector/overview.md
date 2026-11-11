---
tags:
- system
- selector
verified: '2026-11-05'
title: selector — overview
thesis: "Selector is GFS's legacy shipping system. Each customer site runs its own copy: Client4, a Delphi desktop app, and CSS, a SOAP service, both working on one site-local Firebird database. Together they rate, label, manifest and upload shipments to GFS. Part of Merak's output is to replace it."
confidence: high
---
# selector — overview

```orient-bluf
{ "v": 1, "bluf": "Selector is GFS's legacy shipping system. Each customer site runs its own copy: Client4, a Delphi desktop app, and CSS, a SOAP service, both working on one site-local Firebird database. Together they rate, label, manifest and upload shipments to GFS. Part of Merak's output is to replace it.", "confidence": "high", "action": "Treat a CSS-only customer as also needing Client4: CSS never uploads shipments itself." }
```

**What it is.** A per-site install, in one of two models. **Hosted:** a GCP Windows VM per customer runs CSS under IIS at `<customer>.gfsdeliver.com/ClientServer/ClientShipService.asmx`, next to that site's `GFS.FDB`. Client4 on the VM does the uploads. **Standalone:** Client4 on the customer's own PC, with a local database. In August 2026 there were 278 hosted VMs and about 1,000 registered sites.

**Who uses it.** Warehouse staff ship through Client4's screens. Customer WMSes and integrators call CSS over SOAP, either directly or through selector-rest-proxy. Fuse's selector-adapter and Parcel Portal are CSS callers too.

**Why it matters.** Selector holds the customer's carrier contracts, number ranges, routes and gazetteer. It turns a shipment into a carrier label. Billing only sees a shipment once it reaches GFS's central database, so the upload step is load-bearing.

## Components

| Component | Where | Onboarded |
| --- | --- | --- |
| CSS (`vzClientSoapServer`) | ADO `Legacy GFS Ticketing/CSS` | yes — [[css]] |
| Client4 (`GFSClient4`) | ADO `Legacy GFS Ticketing/V4`, `Client/Client.Alpha` | yes — [[client4]] |
| Site database `GFS.FDB` | Firebird, one per site; schema in `V4-Server-Database` | part of both |
| Central estate: UploadServer, Manager, Database, IE and others | `V4-Server-*` repos | no — neighbours |
| Carrier proxies, selector-rest-proxy, ApiKy | GKE, Cloud Run | no — see [[carrier-proxies]], [[selector-rest-proxy]] |

## Neighbours

```orient-flow
{ "v": 1, "title": "One customer's Selector",
  "nodes": [
    { "id": "wms", "label": "Customer WMS", "sub": "or selector-rest-proxy, Fuse, Parcel Portal", "kind": "external" },
    { "id": "staff", "label": "Warehouse staff", "kind": "external" },
    { "id": "css", "label": "CSS", "sub": "SOAP, IIS", "kind": "service", "tone": "accent" },
    { "id": "client4", "label": "Client4", "sub": "Delphi desktop", "kind": "service", "tone": "accent" },
    { "id": "fdb", "label": "Site GFS.FDB", "sub": "Firebird", "kind": "store" },
    { "id": "carriers", "label": "Carriers", "sub": "direct APIs and GFS proxies", "kind": "external" },
    { "id": "upl", "label": "Upload server", "sub": "central, SOAP", "kind": "external" },
    { "id": "central", "label": "SRV_GFS.fdb", "sub": "central DB, Manager", "kind": "store" }
  ],
  "edges": [
    { "from": "wms", "to": "css", "label": "ProcessShipment" },
    { "from": "staff", "to": "client4" },
    { "from": "css", "to": "fdb" },
    { "from": "client4", "to": "fdb" },
    { "from": "css", "to": "carriers", "label": "label" },
    { "from": "client4", "to": "carriers", "label": "label" },
    { "from": "fdb", "to": "client4", "label": "SHIP_COMMITED event" },
    { "from": "client4", "to": "upl", "label": "upload, pull updates" },
    { "from": "upl", "to": "central" }
  ] }
```

The arrow that surprises people runs from `fdb` to `client4`. CSS's `UploadShipments` only fires a Firebird event. Client4 on the station marked `UPLOAD_STATION = 1` catches it and does the upload [1][2].

## Where the reference lives
- [[architecture]] covers data flow, set-up, the two front doors and the shared database. [[known-context]] covers ownership, hosting and fragility.
- Confluence holds the long form under *Legacy Selector* in the MPK space (page 351764483). Customer data flow is page 352157700 [3]. The site, central and between-the-two sides are pages 357171228, 357531678 and 357367820 (11 Nov 2026).
- Member internals: [[css]] and [[client4]] in `Engineering/`.

## What deliberately isn't here
- **The central V4-Server-* estate.** UploadServer, Manager, Database, IE, Notifier, Backup and the gazetteer generators are neighbours, not members.
- **Carrier proxies and selector-rest-proxy.** They have their own folders.
- **The replacement.** Merak will replace part of Selector. No programme or epic tracks it yet (snapshot 2026-11-05).

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "CSS/vzClientSoapServer/InternalProcedures/ProcessShipProcedures.cs@414569b:L4498" },
  { "id": 2, "kind": "code", "ref": "V4/Client/Client.Alpha/dmClient.pas@73cfd69:L2096" },
  { "id": 3, "kind": "doc", "ref": "Confluence MPK 352157700 Legacy Selector - Customer Data Flow" }
] }
```
