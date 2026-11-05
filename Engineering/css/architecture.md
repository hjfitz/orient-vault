---
tags: [waypoint, css]
title: css — architecture
thesis: "One ASMX class, ClientShipService, holds 35 web methods and delegates to large static procedure files in InternalProcedures. Every call opens the site's Firebird DB through GFSConn. Older carriers live in per-carrier procedure files. Newer ones implement ICarrier and are picked by carrier name in ACarrier.NewCarrier."
confidence: high
verified: 2026-11-05
---
# css — architecture

```orient-bluf
{ "v": 1, "bluf": "One ASMX class, ClientShipService, holds 35 web methods and delegates to large static procedure files in InternalProcedures. Every call opens the site's Firebird DB through GFSConn. Older carriers live in per-carrier procedure files. Newer ones implement ICarrier and are picked by carrier name in ACarrier.NewCarrier.", "confidence": "high", "action": "UploadShipments only fires a DB event; don't treat its success as 'sent to GFS'." }
```

## Guardrails
- [contract:G1] `UploadShipments` runs `SHIP_STATUS_CHANGED('SHIP_COMMITED')` and returns. Client4 on the upload station does the actual upload.
  — paths: vzClientSoapServer/InternalProcedures/ProcessShipProcedures.cs
- [technical:G2] No duplicate guard. A repeated `ProcessShipment` with the same reference books a second shipment.
  — paths: vzClientSoapServer/ClientShipService.asmx.cs
- [technical:G3] A new-style carrier needs an `ICarrier` class and a `case` in `ACarrier.NewCarrier`. The case string matches the contract's carrier name exactly (`"ROYAL MAIL"`, `"DPD NL"`).
  — paths: vzClientSoapServer/Carriers
- [contract:G4] With `CUST_SITES.ALLOW_ROUTES = 0`, a shipment carrying a route code fails validation.
  — paths: vzClientSoapServer/InternalProcedures/ValidateProcedures.cs
- [policy:G5] The `AuthConnDetails` header carries the user's password, and replies carry PII and labels. Don't add logging of SOAP bodies.
  — paths: vzClientSoapServer/LogSoapExtension.cs, vzClientSoapServer/Logging
- [operational:G6] While `clientdb.UPD_START = 1`, every authenticated call fails with `0066 Database updating`.
  — paths: vzClientSoapServer/InternalProcedures/CommonProcedures.cs

## Structure

```orient-flow
{ "v": 1, "title": "A ProcessShipment call",
  "nodes": [
    { "id": "asmx", "label": "ClientShipService", "sub": "web method", "kind": "service" },
    { "id": "auth", "label": "InternalConnection", "sub": "web_users, cust_sites", "kind": "step", "ev": [2] },
    { "id": "val", "label": "InternalValidateShipment", "sub": "service, options, address, customs, credit", "kind": "step", "ev": [3] },
    { "id": "carrier", "label": "Carrier code", "sub": "ICarrier or <Carrier>Procedures", "kind": "step", "ev": [4] },
    { "id": "fdb", "label": "Site GFS.FDB", "kind": "store" },
    { "id": "ext", "label": "Carrier API or GFS proxy", "kind": "external" }
  ],
  "edges": [
    { "from": "asmx", "to": "auth" },
    { "from": "auth", "to": "val" },
    { "from": "val", "to": "carrier" },
    { "from": "carrier", "to": "ext", "label": "label" },
    { "from": "carrier", "to": "fdb", "label": "Save" },
    { "from": "val", "to": "fdb", "label": "reads set-up" }
  ] }
```

```
vzClientSoapServer/
  ClientShipService.asmx.cs    the 35 web methods (about 5.9k lines)
  ClientShipClass.cs           request and response types
  ShipOptionsClass.cs          per-shipment option types
  InternalProcedures/          static procedures; Validate (10k lines), Label, ProcessShip, per-carrier files
  Carriers/                    ICarrier.cs plus newer carrier classes
  HermesPS/                    Hermes parcel shop support
  Logging/, LogSoapExtension.cs   file and HTTP log sinks
  Web References/, Service References/   generated carrier SOAP clients
  LocalSwagger/                copies of the carrier-proxy OpenAPI specs
Test*/                         manual console harnesses, one per operation
SetupCSS/, MainSetupCSS/       Visual Studio installer projects
```

## Interfaces in

| Group | Operations |
| --- | --- |
| Ship | `ProcessShipment`, `ProcessShipments`, `ShipToGroup`, `DeleteShipments` |
| Commit and upload | `CommitShipments`, `CommitShipGroup`, `UploadShipments`, `ReuploadShipments` |
| Validate | `ValidateShipment`, `ValidateShipments`, `LaneFeasibility`, `ValidateAddress`, `CheckUKAddress`, `SearchAddress` |
| Lookups | `FindAvailableServices`, `GetCustRoutes`, `FindUPSAccessPoints`, `FindInPostMachines`, `FindAvailableDPDShops`, `FindAvailablePayPoints`, `FindCarrierLocation` |
| Documents | `PrintManifest`, `PrintRMSalesOrder`, `ProcessReports`, `UPSLabelsRecovery`, `DailyShipQuery` |
| Collections | `ProcessCarrierDispatch`, `CancelCarrierDispatch` |
| Data | `ImportAddressBook`, `ExportAddressBook`, `ImportGoods`, `ExportGoods`, `GetCAOrders` |
| Admin | `UnlockService`, `CheckUpdates` |

`ProcessShipment` [1] is the most-called entry, and `UploadShipments` only posts the event [5]. Every request carries `AuthenticationDetails` (with a `VersionId`) and gets back `ResponseDetails` with a status and coded notifications.

## Interfaces out
- **Site DB.** Firebird through `FirebirdSql.Data.FirebirdClient`, using the `GFSConn` connection string in `Web.config`. `AdmDB3.fdb`, in the same folder as `GFS.FDB`, holds `clientdb.UPD_START` [2].
- **GFS carrier proxies.** Generated clients under `Service References/`: `GFSAmazon`, `GFSBJS`, `GFSColl8API`, `GFSDPDApi`, `GFSExelot`, `GFSFedexAPI`, `GFSInPost`, `GFSOcsApi`, `GFSRMApi`. The proxy URLs come from `CUST_SITES` columns.
- **Direct carrier and third-party SOAP.** Under `Web References/`: Parcelforce, DHL Freight, the older FedEx services, Hermes parcel shops, UK Mail, Spring, DPD shops, ChannelAdvisor, and GFS's credit-manager and carrier-routes services.
- **Logs.** `Logging:Sinks` picks `File` and/or `Http`. `Logging:HttpEndpoint` names the HTTP target.

## Runtime
- IIS on the customer's GFS-hosted Windows box. .NET Framework 4.8.1.
- Built in Visual Studio from `vzClientSoapServer.sln`. No pipeline. Release is by `Release-4.50.x` branch merges.

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "vzClientSoapServer/ClientShipService.asmx.cs@414569b:L1167" },
  { "id": 2, "kind": "code", "ref": "vzClientSoapServer/InternalProcedures/CommonProcedures.cs@414569b:L25" },
  { "id": 3, "kind": "code", "ref": "vzClientSoapServer/InternalProcedures/ValidateProcedures.cs@414569b:L2577" },
  { "id": 4, "kind": "code", "ref": "vzClientSoapServer/Carriers/ICarrier.cs@414569b:L1064" },
  { "id": 5, "kind": "code", "ref": "vzClientSoapServer/InternalProcedures/ProcessShipProcedures.cs@414569b:L4498" }
] }
```
