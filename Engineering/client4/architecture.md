---
tags:
- waypoint
- client4
title: client4 — architecture
thesis: 'A Delphi 7 VCL app: fmMain holds the screens, the dmClient data module holds
  the site DB connection and reacts to Firebird events, and uSoapUpload talks to the
  central upload server through one StartConnection call that switches on a mode number.'
confidence: high
verified: '2026-11-05'
verified_paths:
- Client/Client.Alpha/dmClient.pas
- Client/Client.Alpha/uSoapUpload.pas
- Client/Client.Alpha/gfsConst.pas
- Client/Client.Alpha/Carriers
verified_sha: 73cfd69
---
# client4 — architecture

```orient-bluf
{ "v": 1, "bluf": "A Delphi 7 VCL app: fmMain holds the screens, the dmClient data module holds the site DB connection and reacts to Firebird events, and uSoapUpload talks to the central upload server through one StartConnection call that switches on a mode number.", "confidence": "high", "action": "Treat UPLOAD_STATION as load-bearing: it decides which PC talks to GFS." }
```

## Guardrails
- [contract:G1] Only the station with `UPLOAD_STATION = 1` uploads, downloads updates and handles `SHIP_COMMITED` from CSS. Clear it on every PC and the site stops reaching GFS without an error.
  — paths: Client/Client.Alpha/dmClient.pas
- [technical:G2] `StartConnection(mode, …)` is the single entry to the upload server. Mode numbers are hard-coded at call sites, so a new mode means editing both `uSoapUpload.pas` and its callers.
  — paths: Client/Client.Alpha/uSoapUpload.pas, Client/Client.Alpha/dmClient.pas
- [technical:G3] Event names in `gfsConst.pas` must match what the DB procedures post (`SHIP_COMMITED`, with one T). Renaming either side silently breaks the link.
  — paths: Client/Client.Alpha/gfsConst.pas
- [policy:G4] `cust_upl_servers` holds the upload server credentials (`GFS_USER`/`GFS_PSW`). The Defaults screen shows them. Never copy the values out.
  — paths: Client/Client.Alpha/fmDefaults.pas

## Structure

```orient-flow
{ "v": 1, "title": "Committed shipment to GFS",
  "nodes": [
    { "id": "commit", "label": "Commit", "sub": "Client4 screen or CSS", "kind": "step" },
    { "id": "ev", "label": "SHIP_COMMITED", "sub": "Firebird event", "kind": "topic" },
    { "id": "dm", "label": "dmClient", "sub": "MainEvents handler", "kind": "service", "ev": [1] },
    { "id": "soap", "label": "uSoapUpload", "sub": "StartConnection(0) = UploadShips", "kind": "service", "ev": [2] },
    { "id": "srv", "label": "cust_upl_servers", "sub": "GFS_HOST, UPL_ORDER", "kind": "store", "ev": [3] },
    { "id": "upl", "label": "Upload server", "kind": "external" }
  ],
  "edges": [
    { "from": "commit", "to": "ev" },
    { "from": "ev", "to": "dm", "label": "UPLOAD_STATION = 1" },
    { "from": "dm", "to": "soap" },
    { "from": "soap", "to": "srv", "label": "endpoint per order" },
    { "from": "soap", "to": "upl", "label": "IUploadServer" }
  ] }
```

```
Client/
  Client.Alpha/                 the app (GFSClient4.dpr, Delphi 7 .dof)
    fmMain.pas                  main window and tabs (about 9.6k lines)
    dmClient.pas/.dfm           DB connection, datasets, Firebird event handler (about 5.7k lines)
    uSoapUpload.pas             upload server client and mode switch (about 2k lines)
    gfsUploadServer.pas         generated IUploadServer SOAP interface
    gfsConst.pas                constants, including the event names
    Carriers/                   BJS, COLL8, DPD_Core/DE/NL, Exelot, OCS, RoyalMail
    fm*.pas                     one form per dialog: customs, options per carrier, import, manifest
    *Service*.pas               generated carrier SOAP clients
  BackupApp/, BackupRestore/    site DB backup tools (BackupApp is C#)
  DailyPassword/                daily password tool
  UpdateUtil/                   updater
  ExportData/                   export tool
Server/*                        README stubs pointing at the V4-Server-* repos
ImportDocumentation/            import file specs
```

## Firebird events handled
`dmClient` registers its events through a `TIBEvents` component (`MainEvents`) and reacts to them [1]:

| Event | What Client4 does |
| --- | --- |
| `SHIP_COMMITED` | reloads the lists; the upload station starts an upload |
| `SHIP_IMPORTED` | refreshes the import tab when auto-refresh is on |
| `SHIP_PRINTED` | refreshes the shipment list |
| `SHIP_UPLOADED` | when the site uses ChannelAdvisor (`USE_CA`), posts shipped status back |
| `UPD_DOWNLOAD` | the upload station starts an update download |
| `SITE_UPDATE`, `LOCK_STATUS`, `NEW_STATION`, `UPDATE_DEFS` and others | site and station state changes |

## Interfaces out: upload server modes

`StartConnection(mode, manual, zip, key)` picks the endpoint from `cust_upl_servers` in `UPL_ORDER` and runs one operation [2][3]:

| Mode | Operation |
| --- | --- |
| 0 | upload committed shipments |
| 1, 2 | get carrier versions, download an update |
| 3, 4 | download the registration package (`GetCustSiteRegData`, the zip Manager stored at "get ready"), commit the registration |
| 5 | re-upload |
| 6 | register a department |
| 7 | Royal Mail sales order |
| 8 | upload shipment info |
| 9, 15 | auto-commit shipments |
| 10, 13 | Hermes update |
| 11, 12 | site status, echo |
| 14 | Royal Mail services |

## Updates
- **What arrives.** Every upload sends the site's versions, and the server answers with what's pending. `GetVersions`, `VerifyUpdates` and `GetVerUpdate3` then fetch:
  - Manager "Site update" packages (upsert-only)
  - global meta and route updates
  - new Client4 exes, uploaded through Manager's Versions screen
- **How it applies.** The packages are stored through `SAVE_DOWNLOAD`. Each station's `CheckBinUpdates` launches `updUtil.exe`, which waits for Client4 to exit and swaps the exe.
- **When it runs.** Only on central `AUTO_UPDATE = 1`, an unlocked site, and the upload station.

## Carrier paths that differ from CSS
- **`FEDEX`** calls FedEx's old SOAP API directly (`uFedex.pas`), using `CUST_SITES.FEDEX_URL`. CSS sends `FEDEX` to the GFS FedEx proxy.
- **`INPOST`** calls the old InPost API directly. The URL and token come from the contract's `CARR_KEY`/`CARR_PSW`. CSS uses the GFS InPost proxy.
- **`products.label_id = 0`** means "use the carrier's PDF" for any carrier (`CheckPdfLabels`, `uFunc.pas:27448`). In CSS it does so only for Parcelforce and UK Mail.
- **UPS** builds the UPS XML request itself (`uUPSClient.pas`) and sends it to `UPS_URL`, which is the GFS UPS proxy.

## Runtime
- A Windows desktop install on each customer PC, with one PC per site marked as the upload station.
- It is built in the Delphi 7 IDE and uses InterBase Express and DevExpress grids. There's no pipeline and no tests.

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "Client/Client.Alpha/dmClient.pas@73cfd69:L2070-L2125" },
  { "id": 2, "kind": "code", "ref": "Client/Client.Alpha/uSoapUpload.pas@73cfd69:L410-L426" },
  { "id": 3, "kind": "code", "ref": "Client/Client.Alpha/uSoapUpload.pas@73cfd69:L1270" }
] }
```
