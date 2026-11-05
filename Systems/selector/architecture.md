---
tags:
- system
- selector
verified: '2026-11-05'
title: selector — architecture
thesis: "Central set-up in Manager is copied into each site's GFS.FDB when the site registers. From then on the site runs on its own: CSS and Client4 validate and label against that local copy. Client4 is the only path that uploads shipments back to GFS."
confidence: high
---
# selector — architecture

```orient-bluf
{ "v": 1, "bluf": "Central set-up in Manager is copied into each site's GFS.FDB when the site registers. From then on the site runs on its own: CSS and Client4 validate and label against that local copy. Client4 is the only path that uploads shipments back to GFS.", "confidence": "high", "action": "Change a contract before 'get ready for registering', or run it again: later Manager edits don't reach the registration copy." }
```

## Guardrails
- [contract:G1] CSS `UploadShipments` only fires the Firebird event `SHIP_COMMITED`. Shipments reach GFS only if Client4 is running on the site's `UPLOAD_STATION = 1` PC.
  — paths: CSS/vzClientSoapServer/InternalProcedures, V4/Client/Client.Alpha/dmClient.pas
- [operational:G2] Registration copies data as it stood at "get ready for registering". Manager edits made after that are missing until you run get-ready again.
  — paths: V4-Server-UploadServer, V4-Server-Manager
- [technical:G3] Selector doesn't deduplicate. Two `ProcessShipment` calls with one reference book two shipments. Callers own idempotency.
  — paths: CSS/vzClientSoapServer/ClientShipService.asmx.cs
- [contract:G4] With `CUST_SITES.ALLOW_ROUTES = 0`, any shipment carrying a route code fails ("The usage of custom routes is prohibited").
  — paths: CSS/vzClientSoapServer/InternalProcedures
- [policy:G5] Every site DB holds carrier credentials (`CUST_CONTRACTS.CARR_KEY`/`CARR_PSW`) and user passwords (`web_users`). Never copy their values into docs, logs or tickets.
  — paths: CSS/vzClientSoapServer, V4/Client/Client.Alpha

## Data flow

```orient-flow
{ "v": 1, "title": "From set-up to billing",
  "nodes": [
    { "id": "mgr", "label": "System 4 Manager", "sub": "GFS staff set-up", "kind": "service" },
    { "id": "central", "label": "SRV_GFS.fdb", "sub": "central", "kind": "store" },
    { "id": "reg", "label": "RegisterCustSite", "sub": "upload server, CUST_SCRIPTS", "kind": "step" },
    { "id": "tools", "label": "tools-ui contract SQL", "sub": "pasted into the site DB", "kind": "step" },
    { "id": "fdb", "label": "Site GFS.FDB", "kind": "store" },
    { "id": "ship", "label": "CSS or Client4", "sub": "validate, label", "kind": "service", "tone": "accent" },
    { "id": "upl", "label": "Client4 upload", "sub": "UPLOAD_STATION = 1", "kind": "step" },
    { "id": "bill", "label": "Billing, ECM, Royal Mail", "sub": "TRANSFER_QUEUE, rm_replica", "kind": "external" }
  ],
  "edges": [
    { "from": "mgr", "to": "central" },
    { "from": "central", "to": "reg", "label": "SITE_REG = 4", "ev": [1] },
    { "from": "reg", "to": "fdb", "label": "zip of named SELECTs" },
    { "from": "tools", "to": "fdb", "label": "later contract changes", "ev": [6] },
    { "from": "fdb", "to": "ship" },
    { "from": "ship", "to": "upl", "label": "SHIP_COMMITED", "ev": [2, 3] },
    { "from": "upl", "to": "central" },
    { "from": "central", "to": "bill", "label": "DB triggers" }
  ] }
```

1. **Set-up.** GFS staff create the customer, sites, contracts and ranges in System 4 Manager, which writes to `SRV_GFS.fdb`.
2. **Registration.** A site set to `SITE_REG = 4` calls `RegisterCustSite` [1]. The upload server runs the named queries in `CUST_SCRIPTS` row 1, or row 2 for GFS-tuned sites. It returns them as a zip that becomes the site's `GFS.FDB` content.
3. **Later changes** reach a registered site two ways. The tools-ui contract tool generates SQL that someone pastes into the site DB [6]. The alternative is to register the site again.
4. **Reference data.** Client4 pulls carrier and routing updates with `GetLastCarrUpdate` and `GetCarrierVersions` [4].
5. **Shipping.** CSS or Client4 validates against the local tables, gets a label from the carrier, and stores the shipment.
6. **Upload.** Commit fires `SHIP_COMMITED`. Client4 on the upload station sends the shipments through `IUploadServer` [2][3].

`SITE_REG` values: 0 not registered, 1 live, 3 locked, 4 ready to register. **UNKNOWN**: what 2 means.

## What one site needs

| Data | Tables | Source |
| --- | --- | --- |
| Site identity, options, carrier URLs | `CUST_SITES` (about 150 columns) | registration, then SQL |
| Contracts and carrier credentials | `CUST_CONTRACTS`, `CUST_SITE_CONTRACTS` | Manager or tools-ui |
| Services per contract | `CUST_CONTRACT_PRODUCTS`, `CUST_CONTRACT_SERVICES`, `CONTRACT_SERVICE_RANGES` | Manager or tools-ui |
| Consignment and item numbers | `SHIP_RANGES`, `ITEM_RANGES` | Manager or tools-ui |
| Route codes | `CUST_ROUTES` | Manager or tools-ui |
| Postcode routing | gazetteer tables, `GET_*_DEPOT` procedures | gazetteer releases |
| API users | `web_users` | site set-up |
| Upload endpoints | `cust_upl_servers` | Client4 Defaults screen |

"Route" means two things. A **route code** is a `CUST_ROUTES` entry the caller names (`RouteMapCode`), gated by `ALLOW_ROUTES` [5]. **Postcode routing** is the depot lookup through the gazetteer.

**UNKNOWN**: the exact table list in the `CUST_SCRIPTS` registration rows. It lives in a central DB row, not in code.

## The two front doors

| | Client4 | CSS |
| --- | --- | --- |
| Caller | warehouse staff at a PC | customer WMS or integrator, over SOAP |
| Auth | Client4 login | `AuthConnDetails` header checked against `web_users` |
| Labels | its own `Carriers/` units | its own `Carriers/` classes |
| Upload | does it | fires `SHIP_COMMITED` only |
| Runs on | customer PCs | GFS-hosted IIS box per customer |

The two hold separate carrier code in two languages, so a carrier fix often lands twice.

## Carrier credentials

Three patterns, kept class-level here (details in the MPK *Carrier Proxies* page):
- **Per customer, in the site DB.** `CARR_KEY`/`CARR_PSW` on the contract, sent to the carrier or proxy.
- **Per customer, behind a GFS proxy.** The contract holds an ApiKy key. The proxy resolves the real credentials from MongoDB or the ApiKy profile.
- **One shared GFS account.** UPS, OCS and Coll8 use a GFS-wide account behind the proxy.

## Runtime
- **CSS:** IIS on a GFS-hosted Windows box per customer, reached at `<customer>.gfsdeliver.com/ClientServer/ClientShipService.asmx`. `GFSConn` in `Web.config` points at the site DB.
- **Client4:** a Windows desktop install on each customer PC. One PC per site is the upload station.
- **No CI, no automated tests, no central telemetry.** CSS writes file logs under `C:\Temp`, plus an optional HTTP sink.

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "V4-Server-UploadServer/IUploadServerImpl.pas@5773b8e:L1671" },
  { "id": 2, "kind": "code", "ref": "CSS/vzClientSoapServer/InternalProcedures/ProcessShipProcedures.cs@414569b:L4498" },
  { "id": 3, "kind": "code", "ref": "V4/Client/Client.Alpha/dmClient.pas@73cfd69:L2096" },
  { "id": 4, "kind": "code", "ref": "V4/Client/Client.Alpha/uSoapUpload.pas@73cfd69:L506" },
  { "id": 5, "kind": "code", "ref": "CSS/vzClientSoapServer/InternalProcedures/ValidateProcedures.cs@414569b:L9101" },
  { "id": 6, "kind": "doc", "ref": "knowledge-system vault/runbooks/carrier-contract-install.md" }
] }
```
