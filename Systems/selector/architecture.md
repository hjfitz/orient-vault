---
tags:
- system
- selector
verified: '2026-11-05'
title: selector — architecture
thesis: "Manager builds packages of central set-up, and each site's Client4 pulls them into the site's GFS.FDB, at registration and on later site updates. CSS and Client4 validate and label against that local copy. Only Client4 uploads shipments back to GFS."
confidence: high
---
# selector — architecture

```orient-bluf
{ "v": 1, "bluf": "Manager builds packages of central set-up, and each site's Client4 pulls them into the site's GFS.FDB, at registration and on later site updates. CSS and Client4 validate and label against that local copy. Only Client4 uploads shipments back to GFS.", "confidence": "high", "action": "A Manager edit reaches a site only after 'get ready' (new site) or 'Site update' (live site) builds a new package." }
```

## Guardrails
- [contract:G1] CSS `UploadShipments` only fires the Firebird event `SHIP_COMMITED`. Shipments reach GFS only if Client4 is running on the site's `UPLOAD_STATION = 1` station.
  — paths: CSS/vzClientSoapServer/InternalProcedures, V4/Client/Client.Alpha/dmClient.pas
- [operational:G2] Manager edits reach a site only through a package: "get ready for registering" for a new site, "Site update" for a live one. An edit made after the package was built isn't in it.
  — paths: V4-Server-Manager/source/fmSiteReg.pas
- [technical:G3] Selector doesn't deduplicate. Two `ProcessShipment` calls with one reference book two shipments. Callers own idempotency.
  — paths: CSS/vzClientSoapServer/ClientShipService.asmx.cs
- [contract:G4] With `CUST_SITES.ALLOW_ROUTES = 0`, any shipment carrying a route code fails ("The usage of custom routes is prohibited").
  — paths: CSS/vzClientSoapServer/InternalProcedures
- [operational:G5] Site updates only add and change data. A contract or service removed in Manager stays on the site, and re-registering wipes the site, shipments included.
  — paths: V4-Server-Database/ClientScripts
- [policy:G6] Every site DB holds carrier credentials (`CARR_KEY`/`CARR_PSW`) and plaintext API user passwords (`gfs_users`, `web_users`). Never copy their values into docs, logs or tickets.
  — paths: CSS/vzClientSoapServer, V4/Client/Client.Alpha

## Hosting models

| Model | Where it runs | Who books | Sites (snapshot 2026-08-06) |
| --- | --- | --- | --- |
| **Hosted (API)** | GCP Windows VM per customer, project `gfs-cloud-selector-prod-uk1`, `<customer>.gfsdeliver.com` | CSS callers over SOAP; Client4 on the VM | 278 VMs backing 259 sites |
| **Standalone** | Client4 on the customer's own PC, local DB | staff in Client4 | about 172 marked `Standalone` |

Client4 runs in both models. It is the uploader on a hosted VM too [9]. The model is recorded only in the free-text `CUST_SITES.CUST_URL`.

## Data flow

```orient-flow
{ "v": 1, "title": "From set-up to billing",
  "nodes": [
    { "id": "mgr", "label": "System 4 Manager", "sub": "GFS staff set-up", "kind": "service" },
    { "id": "central", "label": "SRV_GFS.fdb", "sub": "central", "kind": "store" },
    { "id": "pkg", "label": "Site package", "sub": "VER_DATA or CUST_SITE_UPDATES", "kind": "step", "ev": [1] },
    { "id": "tools", "label": "tools-ui contract SQL", "sub": "site DB only", "kind": "step", "ev": [6] },
    { "id": "fdb", "label": "Site GFS.FDB", "kind": "store" },
    { "id": "ship", "label": "CSS or Client4", "sub": "validate, label", "kind": "service", "tone": "accent" },
    { "id": "upl", "label": "Client4 upload", "sub": "UPLOAD_STATION = 1", "kind": "step" },
    { "id": "bill", "label": "Pre-advice, billing, ECM", "kind": "external" }
  ],
  "edges": [
    { "from": "mgr", "to": "central" },
    { "from": "central", "to": "pkg", "label": "get ready, Site update" },
    { "from": "pkg", "to": "fdb", "label": "pulled by Client4", "ev": [4] },
    { "from": "tools", "to": "fdb" },
    { "from": "fdb", "to": "ship" },
    { "from": "ship", "to": "upl", "label": "SHIP_COMMITED", "ev": [2, 3] },
    { "from": "upl", "to": "central" },
    { "from": "central", "to": "bill" }
  ] }
```

1. **Set-up.** GFS staff create the customer, sites, contracts and ranges in System 4 Manager, which writes `SRV_GFS.fdb`.
2. **Get ready for registering.** Manager sets `SITE_REG = 4` and runs the type-0 registration script's SELECTs against central. It zips the results with the script and stores the zip in `CUST_SITES.VER_DATA` [1].
3. **Registration.** Client4 sends the site key, and `GetCustSiteRegData` returns that stored zip [4][10]. The script wipes the site's data, then loads it: customers and sites, contacts, consolidation, ranges, contracts, third-party accounts, site contracts, services, products, departments, upload servers, contract service ranges, default services and ChannelAdvisor settings. `CommitCustSiteReg` then sets central to 1.
4. **Later changes.** Every upload carries the site's versions, and the server answers with any pending updates. Client4 pulls them (`GetVersions`, `VerifyUpdates`, `GetVerUpdate3`). Three kinds exist:
   - **Site updates:** Manager's "Site update" button, upsert-only.
   - **Global meta updates.**
   - **Carrier route updates.**

   The pull runs only if central `AUTO_UPDATE = 1`, the site isn't locked and `block_updates` is off on the upload server.
5. **Off-package fixes.** tools-ui generates contract SQL that someone runs against the site DB. Central never sees it. The next re-registration wipes it.
6. **Shipping.** CSS or Client4 validates against the local tables and labels (see *Getting a label*).
7. **Upload.** Commit fires `SHIP_COMMITED`. Client4 on the upload station sends the shipments through `IUploadServer` [2][3]. Central then pre-advises the carrier and feeds billing.

`SITE_REG` values:

| Value | Meaning | Where it shows |
| --- | --- | --- |
| 0 | not registered | Manager's unregistered group |
| 1 | live | Registered Customers |
| 3 | locked | Locked Customers, and the site locks itself |
| 4 | ready to register | the unregistered group |
| 2 | no code sets or reads it; the label lives only in the central `REG_STATUSES` table | missing from Manager's tree; the site can't register or update. **ASSESSED**: disabled or decommissioned |

## What one site needs

| Data | Tables | Source |
| --- | --- | --- |
| Site identity, options, carrier URLs | `CUST_SITES` (about 150 columns) | package |
| Contracts and carrier credentials | `CUST_CONTRACTS`, `CUST_SITE_CONTRACTS`, `THIRD_PARTY_ACCOUNTS` | package or tools-ui |
| Services per contract | `CUST_CONTRACT_PRODUCTS`, `CUST_CONTRACT_SERVICES`, `CONTRACT_SERVICE_RANGES` | package or tools-ui |
| Consignment and item numbers | `SHIP_RANGES`, `ITEM_RANGES` | package |
| Route codes | `CUST_ROUTES` | tools-ui (re-registration wipes it) |
| Carriers, products, postcode routing, label templates | about 120 reference tables in the new-DB generator (`CUST_SCRIPTS` 411) | global and route updates |
| CSS API users | `gfs_users` with role 3 ("Web user"); `web_users` only for API version 5.1.3 | Client4 Defaults → Users [11] |
| Upload endpoints | `upl_servers` | package |

"Route" means two things. A **route code** is a `CUST_ROUTES` entry the caller names (`RouteMapCode`), gated by `ALLOW_ROUTES` [5]. **Postcode routing** is the depot lookup through the gazetteer.

## The two front doors

| | Client4 | CSS |
| --- | --- | --- |
| Caller | warehouse staff at a PC or on the VM | customer WMS or integrator, over SOAP |
| Auth | Client4 login | `AuthConnDetails` header, checked against `gfs_users` (or `web_users` for 5.1.3) |
| Upload | does it | fires `SHIP_COMMITED` only |
| Runs on | hosted VMs and standalone PCs | hosted VMs only |

## Getting a label

```orient-flow
{ "v": 1, "title": "A CSS ProcessShipment, from request to label",
  "nodes": [
    { "id": "call", "label": "Caller", "sub": "WMS, proxy, Fuse, Parcel Portal", "kind": "external" },
    { "id": "check", "label": "Auth and validate", "sub": "users, contracts, routes, gazetteer", "kind": "step", "ev": [7] },
    { "id": "num", "label": "Consignment number", "sub": "SHIP_RANGES", "kind": "step" },
    { "id": "local", "label": "Draw from template", "sub": "PDF_LABEL_TEMPLATES", "kind": "step", "ev": [8] },
    { "id": "direct", "label": "Direct carrier API", "sub": "Spring, Parcelforce, DHL Freight", "kind": "external" },
    { "id": "proxy", "label": "GFS carrier proxy", "sub": "UPS, Royal Mail, BJS, Amazon and others", "kind": "external" },
    { "id": "save", "label": "Save to site DB", "kind": "store" },
    { "id": "reply", "label": "SOAP reply", "sub": "label bytes, or printed by CSS", "kind": "step" }
  ],
  "edges": [
    { "from": "call", "to": "check" },
    { "from": "check", "to": "num" },
    { "from": "num", "to": "local", "label": "most carriers" },
    { "from": "num", "to": "direct" },
    { "from": "num", "to": "proxy", "label": "base64 label back" },
    { "from": "local", "to": "save" },
    { "from": "direct", "to": "save" },
    { "from": "proxy", "to": "save" },
    { "from": "save", "to": "reply" }
  ] }
```

1. **Auth.** CSS checks the header against the site's API users.
2. **Validate.** It checks the service, options, address and postcode, customs and credit against the site DB [7].
3. **Number.** It allocates the consignment number from the contract's `SHIP_RANGES` row.
4. **Label.** Both apps draw from the same template tables, keyed by `products.label_id`. The carrier decides the path [8][12]:

| Path | Carriers (CSS) | Client4 differs |
| --- | --- | --- |
| **Template**, no carrier call | Interlink/DPD Local, Parceline/DPD, ANC, Yodel/HDNL, Hermes, Nightfreight, Tuffnells, Palletforce, Panther, Clipper, City Sprint, GFS Mail, Collect+, WnDirect, the European posts, DHL Freight ship type 1 | `label_id = 0` means "use the carrier's PDF" for any carrier; CSS applies that only to Parcelforce and UK Mail |
| **Template plus a carrier call** | DHL Express (AWB from DHL), I-Parcel, Doddle and P2P depots (routing call) | same |
| **GFS carrier proxy** | UPS (UPS XML format, `UPS_URL` points at the GFS UPS proxy), Royal Mail, DPD NL, DPD DE, Coll8, Exelot, OCS, BJS, Amazon, `FEDEX`, `INPOST`, old Royal Mail API | `FEDEX` and `INPOST` go **direct** to the carrier |
| **Direct carrier API** | Spring, DHL Freight, Aramex, Packeta, Chronopost, Hermes parcel shops, `FEDEX_OLD`; Parcelforce and UK Mail when `label_id = 0` | same; TNT exists only in Client4 |

5. **Save.** It stores the shipment and label in the site DB.
6. **Reply.** It returns the label as bytes (`Image`, base64 on the wire). With `PrintSpecification.PrintDocs` and a named `LabelPrinter`, CSS prints through `PrintPDFLib` instead. Client4 prints at the bench.

For template carriers the carrier first hears of the shipment at pre-advice, after upload.

## Day end and billing handoff

Billing has no intake interface. A separate Delphi billing app, owned by Finance and outside the Selector repos, bills straight from central `SHIPMENTS` rows [14][15]. The handoff is a correct row there, written exactly once.

```orient-flow
{ "v": 1, "title": "From commit to invoice",
  "nodes": [
    { "id": "commit", "label": "Commit", "sub": "CSS or Client4", "kind": "step" },
    { "id": "upl", "label": "Client4 upload", "sub": "upload station", "kind": "step" },
    { "id": "usv2", "label": "upload-service collection", "sub": "manifests, CSVs, Slipway", "kind": "store" },
    { "id": "db", "label": "DataBridge", "sub": "every 10 minutes", "kind": "service" },
    { "id": "ship", "label": "Central SHIPMENTS", "sub": "INVOICE_NUMBER empty", "kind": "store", "tone": "accent" },
    { "id": "bill", "label": "Billing app", "sub": "per-customer schedule", "kind": "external" },
    { "id": "edi", "label": "Carrier EDI charges", "sub": "supplementary invoices", "kind": "external" },
    { "id": "pub", "label": "invoices_published.v1", "sub": "after Finance publishes", "kind": "topic" }
  ],
  "edges": [
    { "from": "commit", "to": "upl", "label": "SHIP_COMMITED" },
    { "from": "upl", "to": "ship", "label": "REG_SHIPMENTS", "ev": [16] },
    { "from": "usv2", "to": "db" },
    { "from": "db", "to": "ship", "label": "REG_WILKO_*", "ev": [17] },
    { "from": "ship", "to": "bill" },
    { "from": "edi", "to": "bill", "label": "matched on cons no + carrier" },
    { "from": "bill", "to": "pub", "label": "legacy-invoice-translator" }
  ] }
```

- **What billing needs:** one row per (`CONS_NO`, `CARRIER`), with parcels in `SHIP_PIECES`. The fields are customer, site, contract, service, package, `DESPATCH_DATE`, packs, weight, receiver postcode and country, reference and surcharge flags. `INVOICE_NUMBER` must be empty or -1, and the contract must be GFS-billed (`BILL_TYPE = 1`).
- **When:** each customer has its own schedule (daily, weekly defaulting to Monday, or monthly). There's no hard cut-off: each run bills everything not yet invoiced, so a late shipment lands on the next invoice.
- **Bill trigger, set per contract (`BILL_ON_SCAN`):**
  - 0: on upload, any status except 100.
  - 1: after the carrier scan, status above 200 and not 310. Carrier tracking is part of the handoff for these contracts.
  - 2: GFS International. Billed, but the mechanism is **UNKNOWN**.
- **After the run:**
  - Carrier EDI charges are billed as supplementary invoices.
  - Finance publishes separately, because runs get rolled back. `legacy-invoice-translator` then writes the invoice files to Cloud Storage and publishes `invoices_published.v1`.
  - CCDIS matches invoice lines on consignment number plus carrier, against `shipments.v2.identified`.
- **What breaks it:**
  - A shipment never arrives: the upload station is off, a CSS booker never commits, a Slipway export fails, or DataBridge skips a row [17].
  - A shipment arrives twice: Manager's recycle-replace inserts a fresh copy, or the upload server commits a partial batch and the client re-sends [16].
  - A delete after upload never reaches central.
  - About 57.5k shipments with negative invoice numbers are never selected.

Full write-up: MPK *Legacy Selector - Day End and Billing Handoff* (page 353566845).

## Releases
- **Client4 and DB updates:** someone uploads the zipped exe in Manager's Versions screen into central `CUST_SITE_UPDATES`. Upload stations on auto-update download it over SOAP, and `updUtil.exe` swaps the exe on each station [13]. The manual route is SQL scripts plus a hand-copied exe.
- **CSS:** only `vzClientSoapServer.dll` ships, copied by hand into the `ClientServer` IIS app on each VM. Releases go out as "GFS Enterprise" from GFSIT SharePoint, announced by Chris Cumings, and only to the sites that need them. The repo's `Web.config` never reaches production.
- **No CI anywhere.** Builds happen in Visual Studio and the Delphi 7 IDE.

## Carrier credentials

Three patterns, kept class-level here (details in the MPK *Carrier Proxies* page):
- **Per customer, in the site DB.** `CARR_KEY`/`CARR_PSW` on the contract, sent to the carrier or proxy.
- **Per customer, behind a GFS proxy.** The contract holds an ApiKy key. The proxy resolves the real credentials from MongoDB or the ApiKy profile.
- **One shared GFS account.** UPS, OCS and Coll8 use a GFS-wide account behind the proxy.

## Telemetry
- CSS writes file logs on each VM, plus an optional HTTP sink.
- The old sink is SMXI's LoggingServer at `logging.gfsdeliver.com`. It is public, has no auth and forwards nowhere.
- Its successor is [[carrier-logging]] on Cloud Run, which can copy to Datadog. That copy shipped switched off (snapshot 2026-11-05).
- No CSS or Client4 logs reach Datadog. The carrier proxies' logs are the only central view.

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "V4-Server-Manager/source/fmSiteReg.pas@a9bfab7:L455-L480" },
  { "id": 2, "kind": "code", "ref": "CSS/vzClientSoapServer/InternalProcedures/ProcessShipProcedures.cs@414569b:L4498" },
  { "id": 3, "kind": "code", "ref": "V4/Client/Client.Alpha/dmClient.pas@73cfd69:L2096" },
  { "id": 4, "kind": "code", "ref": "V4/Client/Client.Alpha/uSoapUpload.pas@73cfd69:L1372" },
  { "id": 5, "kind": "code", "ref": "CSS/vzClientSoapServer/InternalProcedures/ValidateProcedures.cs@414569b:L9101" },
  { "id": 6, "kind": "doc", "ref": "knowledge-system vault/runbooks/carrier-contract-install.md" },
  { "id": 7, "kind": "code", "ref": "CSS/vzClientSoapServer/InternalProcedures/ValidateProcedures.cs@414569b:L2577" },
  { "id": 8, "kind": "code", "ref": "CSS/vzClientSoapServer/InternalProcedures/ProcessShipProcedures.cs@414569b:L108-L130" },
  { "id": 9, "kind": "doc", "ref": "ilg-tech-services/carrier-logging docs/architecture.md" },
  { "id": 10, "kind": "code", "ref": "V4-Server-UploadServer/IUploadServerImpl.pas@5773b8e:L442-L480" },
  { "id": 11, "kind": "code", "ref": "CSS/vzClientSoapServer/InternalProcedures/CommonProcedures.cs@414569b:L76-L88" },
  { "id": 12, "kind": "code", "ref": "V4/Client/Client.Alpha/uFunc.pas@73cfd69:L27448" },
  { "id": 13, "kind": "code", "ref": "V4/Client/UpdateUtil/uUpd.pas@73cfd69" },
  { "id": 14, "kind": "doc", "ref": "Confluence Billing 311394359 Legacy Billing – Invoicing & Scheduling" },
  { "id": 15, "kind": "doc", "ref": "Confluence MPK 353566845 Legacy Selector - Day End and Billing Handoff" },
  { "id": 16, "kind": "code", "ref": "V4-Server-Database/Updates/update_284.sql@82dde6b:L3-L204" },
  { "id": 17, "kind": "doc", "ref": "gfs-hybrid-services/UploadServiceV2DataBridge ShipmentProcessor.cs" }
] }
```
