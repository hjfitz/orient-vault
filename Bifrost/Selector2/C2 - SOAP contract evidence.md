# C2 SOAP `ClientShipService`: contract evidence for golden tests

Prepared 2026-11-12 for Selector2 unit C2 and risk R2. Read-only gathering. Nothing here was run against a live Selector. All XML examples are **synthetic**, built from the evidence below. No credentials, customer data, real consignment numbers or real label bytes were copied.

## 0. How to read this

Source tags, ranked best first:

| Tag | Meaning |
| --- | --- |
| **[S]** | The legacy CSS C# source, read directly. Server truth for what the code emits. |
| **[W]** | A WSDL snapshot generated from CSS. Machine-readable, but **old** (see section 2.3). |
| **[R]** | A reply or request stored as a fixture in a client repo, described there as what "the sandbox accepted/returned". Provenance is by inference from the tests, not from a capture log. |
| **[C]** | Client code (what a caller sends and how it reads replies). |
| **[D]** | Vault or repo prose. Lowest rank. Never used alone. |

`UNVERIFIED` marks a claim I did not confirm against code, a WSDL or a recording.

Checkouts used (all read-only):

| Short | Path | Version read |
| --- | --- | --- |
| CSS | `~/code/selector/CSS` | master `414569b` (2026-10-20, "Fedex URL"), clean tree. This checkout is outside the two directories named in the brief; I used it because the vault's CSS docs name it as the source and it is the only primary evidence of server behaviour. |
| PP | `~/code/merak/parcel-portal` | main `c0b34e1`. Selector client in `apps/svc/internal/adapters/selector/`. |
| SA | `~/code/fuse/selector-adapter` | main `e5f710a`. Client in `apps/adapter/internal/adapters/selector/`. |
| RP | `~/code/fuse/selector-rest-proxy` | `05c2bea`. Node `soap` client driven by the WSDL. |
| OAS | `/tmp/claude-1000/-home-hjf-code-fuse/396b7315-aa79-43a2-af2d-63d6eb3aac55/scratchpad/rest-proxy-openapi.yaml` | Byte-identical to `RP/src/schemas/openapi.yaml` (checked with `diff`). |

## 1. Findings that change the brief (read these first)

1. **`AuthConnDetails` is not a SOAP header and is not on the wire.** It is a C# *parameter name*: `private int InternalConnection(FbConnection conn, ResponseDetails stResp, AuthenticationDetails AuthConnDetails)` (`CSS:vzClientSoapServer/InternalProcedures/CommonProcedures.cs:25`). On the wire the credentials are the **body element `AuthenticationDetails`** inside each request wrapper. The WSDL declares **no `soap:header` anywhere** (`grep` of the WSDL finds none) [W]. All three real clients (PP, SA, RP) send the body element [C]. Migration State R2, `Systems/selector/architecture.md:108`, `Engineering/css/architecture.md` guardrail G5, and `selector2/README.md:183` plus `selector2/iac/projects/selector2-api/iam.tf:2` repeat the "header" claim. The vault's `Engineering/css/overview.md` has it right ("Every request carries `AuthenticationDetails`"). A builder who implements a header will fail every client.
2. **The five operations in C2's brief are not the five operations Parcel Portal calls.** PP calls `ValidateShipment` (singular), `ProcessShipment` (singular), `DeleteShipments`, `CommitShipments` and **`DailyShipQuery`** (`PP:apps/svc/internal/adapters/selector/client.go:36,58,91,121,161`; `PP:apps/svc/README.md:171` says "Selector's `ProcessShipments` isn't used"). PP's reconcile-before-retry and void paths depend on `DailyShipQuery` (`PP:apps/svc/internal/core/dispatch/dispatch.go:206`, `core/shipments/void.go:112`). C2's done-when ("PP books against selector2 with only its URL changed") cannot pass without `ValidateShipment` and `DailyShipQuery`. SA also needs `DailyShipQuery` (`SA:.../selector/daily.go`). The plural ops `ProcessShipments`, `ValidateShipments`, `CommitShipGroup` are called only by RP. Section 4 covers the five in the brief plus `ValidateShipment` and `DailyShipQuery` as required adjuncts.
3. **Recorded real samples exist for only four operations**, and none for the three RP-only ops or for `CommitShipments` (section 2.2). PP never commits against the shared sandbox (`PP:.../selector/sandbox.go`), so PP's `commit.reply.xml` and `commit-rejected.reply.xml` are not sandbox recordings. They look hand-built. `UNVERIFIED` provenance, but the CommitShipments reply shape matches the source (section 4.5).
4. **The WSDL in the CSS repo is a 2022 snapshot and has drifted from the current source** (section 2.3). Do not generate C2's types from it alone. Where WSDL and source differ, source wins and the sandbox accepts the source's shape (PP sends `Resolution` and `AlternativeServices`, neither in the WSDL).
5. **Auth failure does not look the same across operations.** In `CommitShipGroup` the failure detail is thrown away: the reply carries only a top-level `Status` of `FAILURE` and no `ResponseDetails` (section 4.4). In `ProcessShipments`, `DeleteShipments` and `ValidateShipments`, the failure lands in only the **first** per-item status while the others stay `SUCCESS` (sections 4.2, 4.3, 4.5). All of this is [S]; none was observed on the wire.
6. **Validation errors use code `0003`, not the documented `0200`.** The doc comment lists `0200 Validation error`; the validator sets `0003` "Error" (recorded replies agree). Both are cited in section 3.6.

## 2. Evidence inventory

### 2.1 Primary sources

| Evidence | Where | Rank |
| --- | --- | --- |
| Server class, `[WebService]` namespace, 35 `[WebMethod]`s with `SoapDocumentMethod(Action, RequestElementName, ResponseElementName)` | `CSS:vzClientSoapServer/ClientShipService.asmx.cs:20-30` and per method (lines in section 4) | S |
| Wire types (XmlSerializer property order, `XmlElement` flattening, defaults) | `CSS:vzClientSoapServer/ClientShipClass.cs` (9,808 lines) | S |
| Auth, version check, `0066`, `0010`, `0020` | `CSS:.../InternalProcedures/CommonProcedures.cs:25-123, 250-263` | S |
| `ResponseDetails` helpers and the documented code table | `CSS:.../ClientShipClass.cs:1084-1395` | S |
| Full-service WSDL snapshots (35 ops, `elementFormDefault="qualified"`, SOAP 1.1 and 1.2 bindings, no headers) | `CSS:TestProcessShipment/Web References/vzCSS/ClientShipService.wsdl` (152,105 bytes; same bytes in `TestDeleteShipments` and `TestPrintManifest`); older copies in `TestValidateShipments` (142,315), `TestDailyShipQuery/Service References/cssRef/` (115,847) | W |
| Request and reply fixtures | `PP:apps/svc/internal/adapters/selector/testdata/` (20 files); `SA:apps/adapter/internal/adapters/selector/testdata/` (8 files) | R |
| Sandbox behaviour measured 2026-10-27 | `SA:docs/selector-sandbox-findings.md` | D (measured, dated) |
| Client request builders | `PP:.../selector/wire.go`, `client.go`; `SA:.../selector/types.go`, `booker.go` | C |
| Node `soap` client driven by the live WSDL | `RP:src/selector.ts`, `RP:src/handlers/selector/*.handler.ts` | C |

### 2.2 Recording coverage by operation

| Operation | Request recorded | Reply recorded | Notes |
| --- | --- | --- | --- |
| `ProcessShipment` | yes: `PP:testdata/process-multipackage.request.xml`, `SA:testdata/processshipment.request.xml` | yes: success, warning, error, auth failure, ZPL, no-consignment | PP asserts its marshalled request is byte-equal to the recorded one (`PP:.../client_test.go:116-142, 234`) |
| `ValidateShipment` (singular) | yes: `validate-ok.request.xml`, `validate-customs.request.xml` | yes: ok, invalid, customs-rejected, bad-auth | |
| `DeleteShipments` | yes: `delete.request.xml` | yes: success, unknown consignment | |
| `DailyShipQuery` | yes: `daily.request.xml` | yes: `daily.reply.xml`, `SA:testdata/reply-daily-query.xml` | not one of the five, but both clients need it |
| `CommitShipments` | **no request**; PP asserts only the group fragment (`client_test.go:429-437`) | **no real reply**; two hand-built-looking fixtures | PP refuses commits on the shared sandbox |
| `ProcessShipments`, `ValidateShipments`, `CommitShipGroup` | **none** | **none** | RP's fixtures are JS objects invented for unit tests, not XML (`RP:src/__fixtures__/selector.fixture.js`) |
| Faults | n/a | `PP:testdata/fault-soapaction.reply.xml` (wrong SOAPAction, with .NET stack text); `SA:testdata/reply-fault.xml` ("Server was unable to read request.") | HTTP status of the fault is **not** recorded: PP's test serves it as 500 (`client_test.go:522`) |

### 2.3 Where the WSDL snapshot is behind the source

Compared [W] `TestProcessShipment` WSDL against [S] types:

| Item | WSDL snapshot | Current source |
| --- | --- | --- |
| `ShipRequest.AlternativeServices` (first child) | absent | present (`ClientShipClass.cs:7960`) |
| `PrintSpecification.Resolution` | absent | present, default 203 (`:5633`) |
| `AuthenticationDetails.ClientBuildVersion` | absent | present, last child (`:860`) |
| `PrintDocument.OrderNumber`, `PrintDate` | absent | present (`:2264, 2270`) |
| `Party.UKIMS` | absent | present (`:1861`) |
| `ProcessedShipment` children | same list incl. `ConsignmentNo2` | same |

The snapshot's commit is `6eb7c16` (2022-08-23, "CSS Updated to 4.8"); the file mtimes are the 2026-11-04 checkout. The live sandbox accepts the source shape.

## 3. Rules common to all operations

### 3.1 Transport

- HTTP `POST` to the `.asmx` URL, SOAP 1.1, `document/literal`. Both clients send `Content-Type: text/xml; charset=utf-8` and `SOAPAction: "<OperationName>"` **with the double quotes** (`PP:client.go:224-225`, `SA:client.go:110-111`). The WSDL lists the action unquoted (`soapAction="ProcessShipment"`) [W].
- A SOAP 1.2 binding (`ShipServiceSoap12`) exists at the same address [W]. No known client uses it. `UNVERIFIED` that selector2 needs it. RP uses `soap` (node), whose port choice I did not check.
- Routing is by `SOAPAction`. A wrong action gets a SOAP Fault, `faultcode` `soap:Client`, `faultstring` beginning `System.Web.Services.Protocols.SoapException: Server did not recognize the value of HTTP Header SOAPAction: <value>.` followed by a .NET stack line, and an empty `<detail />` [R: `PP:testdata/fault-soapaction.reply.xml`]. The status code of that response was not recorded; ASMX returns 500 for faults by default (`UNVERIFIED` against a capture). The missing-header case was not tested.
- Reply `Content-Type` and charset were not recorded. Reply bodies are an XML declaration with `encoding="utf-8"` and a single line (no indentation) [R].
- Business failures (`ERROR`, `FAILURE`, even bad credentials) come back as **HTTP 200** with a normal reply body, not a Fault [R: `SA:docs/selector-sandbox-findings.md` row 3; `PP:testdata/validate-badauth.reply.xml`].

### 3.2 Envelope, namespaces, no header

- Namespaces on the wire:
  - SOAP envelope `http://schemas.xmlsoap.org/soap/envelope/`, prefix `soap`.
  - Service namespace `http://justshoutgfs.com/Client/Ship/v5/` (`[WebService(Namespace=…)]` at `CSS:ClientShipService.asmx.cs:29`, and every `XmlType` in `ClientShipClass.cs`). It is the WSDL target namespace and an identifier, not an address; the domain moved to `gfsdeliver.com` and the namespace did not. Both clients send it verbatim (`PP:wire.go:13`, `SA:types.go:10`).
- `elementFormDefault="qualified"` [W]: every element, wrapper and children, is in the service namespace. Recorded requests and replies put `xmlns="…/v5/"` once on the wrapper element and let children inherit it [R]. Sending unqualified children (for example `xmlns=""`) would not match `UNVERIFIED`.
- The request `soap:Envelope` carries only `xmlns:soap`. Recorded requests and replies have **no `soap:Header`** [R]. Replies also declare `xmlns:xsi` and `xmlns:xsd` on the envelope [R].
- Every operation is `SoapParameterStyle.Default`: the body holds one **wrapper element** (the `RequestElementName`), whose single child is the **parameter** (named after the C# parameter), whose children are the type's fields. The reply mirrors it: wrapper `ResponseElementName`, one child named `<MethodName>Result`.

Wrapper table [S unless noted]. Wire names, copied from the `SoapDocumentMethod` attributes:

| Operation (SOAPAction) | Request wrapper | Parameter child | Reply wrapper | Result child | `CSS:ClientShipService.asmx.cs` |
| --- | --- | --- | --- | --- | --- |
| `ProcessShipment` | `RequestedShipment` | `ShipRequest` | `ProcessedShipment` | `ProcessShipmentResult` | 1165-1167 |
| `ProcessShipments` | `RequestedShipments` | `ShipRequests` | `ProcessedShipments` | `ProcessShipmentsResult` | 1458-1462 |
| `ValidateShipment` | `RequestedValidateShipment` | `ShipRequest` | `ValidatedShipment` | `ValidateShipmentResult` | 4830-4833 |
| `ValidateShipments` | `RequestedValidateShipments` | `ShipRequests` | `ValidatedShipments` | `ValidateShipmentsResult` | 4710-4712 |
| `DeleteShipments` | `RequestedDeleteShipments` | `Shipments` | `ProcessedDeleteShipments` | `DeleteShipmentsResult` | 1685-1688 |
| `CommitShipGroup` | `RequestedCommitShipGroup` | `ShipGroupRequest` | `ProcessedCommitShipGroup` | `CommitShipGroupResult` | 1917-1920 |
| `CommitShipments` | `RequestedCommitShipments` | `CarrierShipments` | `ProcessedCommitShipments` | `CommitShipmentsResult` | 2067-2070 |
| `DailyShipQuery` | `RequestedDailyQuery` | `DailyRequest` | `ProcessedDailyQuery` | `DailyShipQueryResult` | 5021-5024 |

[W] agrees on every wrapper, parameter and result name (checked by parsing the snapshot's element definitions). Note the oddities: `DeleteShipments`' parameter child is `Shipments`, but its inner repeated element is `RequestedShipments`; `ProcessShipments`' `ShipRequests` holds `Shipments`, whose items are `RequestedShipment`.

### 3.3 Element order and array shapes

- Child order follows the **property declaration order** of each class in `ClientShipClass.cs`, which XmlSerializer uses as an `xs:sequence` [S]. Both Go clients marshal in struct order and say so (`PP:wire.go:15-16`). Replies were emitted in that order in every recording [R].
- Order tolerance: SA tested one case (a future `DespatchDate` moved after `CarrierService`) and Selector still validated it clean [R: findings row 9]. One case only; do not generalise. RP's handlers build objects in an order that differs from the sequence (for example `CommitShipments` puts `AuthenticationDetails` last, but the class order is `ManifestCopies, SiteID, PrintSpecification, AuthenticationDetails, CarrierServiceGroups`), but whether the `soap` library reorders to the WSDL is `UNVERIFIED`.
- Arrays have two shapes, set per property:
  - **Flat repeats** (`[XmlElement("X")]`): `Packages`, `PrintDocuments`, `Labels`, `ConsignmentNo`, `CarrierServiceGroups`, `ShipGroups`, `Consignments`, `CarrierDocuments`, `ErrorShipGroups`, `RequestedShipments` (delete), `Shipments` (delete reply), `DailyShipments`.
  - **Wrapped**: `ShipRequests.Shipments` -> `<Shipments><RequestedShipment>…</RequestedShipment>…</Shipments>`; `ShipReplies.Shipments` -> `<Shipments><ProcessedShipment>…`; `ValidatedShipments.ValidatedShips` -> `<ValidatedShips><ValidatedShipment>…`; `RequestedPackage.PackageUnits` -> `<PackageUnits><PackageUnit>…`. [S: absence of `XmlElement` on those properties; W `ArrayOfRequestedShipment`, `ArrayOfProcessedShipment`, `ArrayOfValidatedShipment`, `ArrayOfPackageUnit` agree; R for `PackageUnits` in `process-multipackage.request.xml`; RP builds `Shipments: { RequestedShipment: [...] }` which is the wrapped shape.]
- A property with an `xxxSpecified` twin (`AlternativeServices`) is emitted only when specified. Null strings are omitted; empty strings are emitted as `<X />` (recorded `<StatusDescription />`) [R].
- A typo is part of the wire: `Recipient.AdditionalReferences` serialises as **`AdditionalRefrences`** (`CSS:ClientShipClass.cs:9578`; RP also writes the typo in `src/handlers/selector/util.ts`).

### 3.4 Authentication

- Body element `AuthenticationDetails` [S:`ClientShipClass.cs:822-870`], child order: `VersionId{Major, Minor, Intermediate}` (that order, [S:874-930]), `UserID`, `UserPassword`, optional `ClientBuildVersion`. Max length 100 on `UserID` and `UserPassword`.
- Where it sits per operation (all siblings of the payload fields, at the position given by declaration order):

| Operation | Parent | Position among siblings |
| --- | --- | --- |
| `ProcessShipment`, `ValidateShipment` | `ShipRequest` | last (after `Shipment`) |
| `ProcessShipments`, `ValidateShipments` | `ShipRequests` | second (after `AlternativeServices`, before `Shipments`, `PrintSpec`) |
| `DeleteShipments` | `Shipments` | first (before `RequestedShipments`) |
| `CommitShipGroup` | `ShipGroupRequest` | first (before `ShipGroups`) |
| `CommitShipments` | `CarrierShipments` | fourth (after `PrintSpecification`, before `CarrierServiceGroups`) |
| `DailyShipQuery` | `DailyRequest` | first |

- `VersionId` semantics [S:`CommonProcedures.cs:250-263`]: `5.0.0` (Major 5, Intermediate 0, Minor 0) returns role 0 -> credentials checked in `gfs_users` where `admin_user = 3`; Major 5 with Intermediate 1 returns role `1 + Minor`; role 4 (Minor 3) checks `web_users`; anything else, or a null `VersionId`, is "not recognised". PP, SA and RP all send `5.0.0` [C: `PP:client.go:21`, `SA:types.go:119`, `RP:src/selector.ts` `getAuthenticationDetails`].
- Web-originated callers (`Intermediate = 1`, Minor 1 or 3) take different branches in `ProcessShipment`, `DeleteShipments` and `CommitShipments` (credit restore, `COMMIT_WEB_SHIPMENTS`) [S: `ClientShipService.asmx.cs:1198-1201, 1714-1717, 2103-2110`]. No recorded caller uses them. **Out of scope for C2 unless the owner says otherwise.**
- Order of checks inside `InternalConnection` [S:`CommonProcedures.cs:25-123`]: (1) version (`0020`); (2) database-updating flag (`0066`); (3) credentials (`0010`, or `0040` on a Firebird error). So during maintenance, even a wrong password gets `0066`, and credentials are never checked.

### 3.5 `ResponseDetails` and the status envelope

`ResponseDetails` [S:`ClientShipClass.cs:1084-1393`; W agrees], child order and required-ness:

| Child | Type | Required on the wire | Notes |
| --- | --- | --- | --- |
| `Status` | `ResponseStatusType` | yes (value type) | `SUCCESS`, `NOTE`, `WARNING`, `ERROR`, `FAILURE`, in that severity order [S:`ClientShipClass.cs:502-509`] |
| `StatusCode` | string | no | omitted when null |
| `StatusMessage` | string | no | omitted when null |
| `StatusDescription` | string | no | initialised to `""`, so emitted as `<StatusDescription />` when empty |

Three different containers wrap it [S]:

| Container | Shape | Used by |
| --- | --- | --- |
| bare `ResponseDetails` (named `ShipmentStatus`, `Status` or `ResponseDetails` by field) | `Status, StatusCode, StatusMessage, StatusDescription` | `ProcessedShipment.ShipmentStatus`, `ProcessedDeleteShipment.Status`, `CarrierDocument.ResponseDetails`, `ErrorShipGroup.ResponseDetails`, `DailyShipResponse.Status` |
| `StatusResponse` | `Status` (enum) then `ResponseDetails` (object); constructor defaults to `SUCCESS` with `StatusCode "0000"` and `StatusDescription ""` [S:`ClientShipClass.cs:1440-1445`] | `ValidateShipment` result, `ValidatedShipments.Status`, `ValidatedShipment.Status` |
| top-level aggregate enum | a bare `Status` or `ResponseStatus` enum element | `ShipReply.ResponseStatus`, `ShipReplies.ResponseStatus`, `DeleteShipmentsResponse.Status`, `CommitShipGroupResponse.Status`, `CommitShipmentsResponse.Status` |

Helper semantics worth pinning in tests [S:`ClientShipClass.cs:1137-1218`]:

- `AddWarning(msg)`: if status is `SUCCESS`, becomes `WARNING` with code `0002`, message `Warning`; appends `msg` to the description, newline-separated.
- `AddValidationError(msg)` and `AddError(msg)`: if status was `SUCCESS` or `WARNING`, code becomes `0003`, message `Error`; status becomes `ERROR` unless already `FAILURE`; description appended. (So a prior warning line is kept in the description of the later error, and the code switches from `0002` to `0003`. Recorded: `SA:testdata/reply-error-past-date.xml`, `PP:testdata/validate-invalid.reply.xml`.)
- `AddResponseError(msg)` and `AddFailure(msg)`: status `FAILURE`, code `0003` if it was `SUCCESS` or `WARNING`.
- `SetFailureStatus(status, code, message, description)`: overwrites status, code, message, then appends description.
- Aggregation: most multi-item operations set the top-level status to the highest enum value across items (`SUCCESS` lowest, `FAILURE` highest), by `>` on the enum [S: `ClientShipService.asmx.cs:1569-1574, 1901-1907, 2494-2506`].

### 3.6 Status codes defined or observed

Documented table (a comment, not enforced) [S:`CSS:ClientShipClass.cs:1297-1313`, repeated `:1331-1347`]:

| Level | Code | Message |
| --- | --- | --- |
| SUCCESS | 0000 | Success |
| NOTE | 0001 | Notes |
| WARNING | 0002 | Warnings |
| ERROR | 0100 | Priority database setting parameters missing |
| ERROR | 0110 | Site locked. Upload committed shipments in order to continue work. |
| ERROR | 0120 | Unable to produce labels. Your Parcel Number range is too small to support the number of parcels in this consignment. Please contact support |
| ERROR | 0130 | FedEx server is unavailable |
| ERROR | 0200 | Validation error |
| ERROR | 0201 | Print Label/document error |
| ERROR | 0300 | Upload server error |
| ERROR | 0400 | Shipment Already Deleted |
| ERROR | 0401 | Upload Shipment can't be deleted |
| FAILURE | 0010 | Authentication Failed |
| FAILURE | 0020 | VersionId is not recognized |
| FAILURE | 0030 | Request structure is invalid |
| FAILURE | 0040 | Database error |
| (any) | 0003 | Any Error or Failure (message column only) |

What the code actually emits (set sites found by `grep` over `CSS:vzClientSoapServer`, excluding generated references):

| Code | Level | Message / description | Source |
| --- | --- | --- | --- |
| `0066` | FAILURE | message `Database updating`, description `Database maintanence. Please, wait several minutes` (sic) | `CommonProcedures.cs:52`; trigger: `select first 1 UPD_START from clientdb` in `AdmDB3.fdb` equals 1 (`:35-47`). **Not in the documented table.** |
| `0010` | FAILURE | `Authentication Failed`, `Wrong user/password` (also used with the exception text if the credential query throws a non-Firebird exception) | `CommonProcedures.cs:107, 116`; recorded `PP:testdata/validate-badauth.reply.xml`, `SA:testdata/reply-failure-auth.xml` |
| `0020` | FAILURE | `VersionId is not recognized` (message and description identical) | `CommonProcedures.cs:121` |
| `0030` | FAILURE | `Request structure is invalid`, description = .NET exception message | `ClientShipService.asmx.cs:1348, 1535, 1561, 1662, 1743, 1789, 1897, 2490`. Delete's per-item bad input uses description `Request structure is invalid` (`:1743-1745`) and FedEx-on-old-version uses message `Invalid request structure` (`:1790`) |
| `0040` | FAILURE | `Database error`, description = Firebird message | `:1344, 1557, 1658, 1877, 1893, 2161, 2307, 2478` |
| `0040` | FAILURE | message `Request structure is invalid` (not `Database error`) in the `ValidateShipments` catch-all | `:4811` (inconsistent with `0030` elsewhere) |
| `0003` | ERROR/FAILURE | `Error`; set by `AddError`, `AddValidationError`, `AddFailure`, `AddResponseError` | `ClientShipClass.cs:1172-1216`; recorded `PP:testdata/process-invalid.reply.xml` (`Postcode required.`), `validate-invalid.reply.xml` |
| `0002` | WARNING | `Warning`; `AddWarning`; also `Processed shipments not found` in `CommitShipments` | `ClientShipClass.cs:1163-1169`; `ClientShipService.asmx.cs:2229-2234`, `2440-2450` |
| `0000` | SUCCESS | set explicitly on `StatusResponse` constructor and on some carrier paths; **absent** on a plain successful `ProcessShipment`, `DeleteShipments` or per-package status | `ClientShipClass.cs:1444`; recorded `PP:testdata/process-zpl.reply.xml` has no `StatusCode` |
| `0110` | ERROR | `Site locked`, `Site locked. Upload committed shipments in order to continue work.` | `CommonProcedures.cs:278-282` |
| `0400` | ERROR | `Shipment not found`, `Shipment Already Deleted` (both set message = description) | `ClientShipService.asmx.cs:1758-1766`; recorded `PP:testdata/delete-unknown.reply.xml` |
| `0401` | ERROR | `Upload Shipment can't be deleted` | `:1772-1775` |
| `0200` | ERROR | credit-balance failure text; manifest sub-errors | `ProcessShipProcedures.cs:4334`, `ValidateProcedures.cs:9648, 10130`, `ManifestProcedures.cs:1914-1981` |
| `0500` | ERROR | `Error`, `No shipments to manifest.` | **Observed only in** `PP:testdata/commit-rejected.reply.xml`. **No `"0500"` literal exists in CSS** (`grep` finds none), so that fixture is not server truth. Treat as invented. |
| `0999` | FAILURE | `FedEx API cancel` | `FedexApiProcedures.cs:1555` |

Note where sources disagree (also in section 6): the documented `0200` "Validation error" vs the code and recordings using `0003`; the documented `0400` text "Shipment Already Deleted" vs the code using it only for the already-deleted branch and `Shipment not found` for the missing branch.

Observed message strings used by validation, with locations in `CSS:vzClientSoapServer/InternalProcedures/ValidateProcedures.cs`: `Warning: Company name is missing.` (`:126`, adds a `WARNING`, still books), `Postcode required.` (`:7457`), `City/Town required.` (`:171, 193`), `Chosen date of despatch is earlier than today.` (`:7631`; a missing `DespatchDate` deserialises to `0001-01-01` and hits the same error, [R: findings row 4]), `Goods description required.` (`:241, 558, 576, 703`), `Phone/Mobile required.` (`:802, 1106`), `Selected service is not supported for this area.` (`:1092`). The file has about 367 `Add*` calls, so this is a sample, not the list (R5 in the programme).

## 4. Per-operation evidence

In every example below: values are synthetic (`EXAMPLE_USER`, `EXAMPLE_PASSWORD`, `TEST000…` consignment numbers, a fake base64 label). Examples marked "constructed" are derived from source field order and have not been seen on the wire. Examples marked "recorded structure" mirror a recorded reply with values replaced.

Shared synthetic building blocks (referred to as `[AUTH]`, `[PRINTSPEC]`):

```xml
<!-- [AUTH] -->
<AuthenticationDetails>
  <VersionId><Major>5</Major><Minor>0</Minor><Intermediate>0</Intermediate></VersionId>
  <UserID>EXAMPLE_USER</UserID>
  <UserPassword>EXAMPLE_PASSWORD</UserPassword>
</AuthenticationDetails>
<!-- [PRINTSPEC] as PP and SA send it -->
<PrintSpecification>
  <Resolution>203</Resolution><TextCN23>0</TextCN23><PrintDocs>false</PrintDocs>
  <LabelSpecType>PDF</LabelSpecType><LabelOrientType>BOTTOM_EDGE_OF_TEXT_FIRST</LabelOrientType>
  <LabelStock>PAPER_4X6</LabelStock>
</PrintSpecification>
```

`PrintSpecification` enums [S:`ClientShipClass.cs`]: `LabelSpecType` is `PrintDocumentType` (`DPL, EPL2, PDF, PNG, ZPLII, TXT, XML`); `LabelOrientType` is `BOTTOM_EDGE_OF_TEXT_FIRST` or `TOP_EDGE_OF_TEXT_FIRST`; `LabelStock` includes `PAPER_4X6`, `PAPER_7X4.75` (enum text has a dot), `STOCK_4X6`, and others (`:333-362`). RP's default is `ZPLII`, 203, `PAPER_4X6`, `PrintDocs false` (`RP:src/handlers/selector/defaults.ts`); PP defaults to `PDF`, SA is configured per connection.

Required-on-the-wire fields below mean **schema-required** (a value-typed child with `minOccurs=1` [W], so omitting it deserialises to a default that may still fail validation). Separately, the validator demands business fields (postcode, etc.). The two lists are not the same; PP's comment "Required value fields are never omitempty" (`PP:wire.go:15-16`) is the practical rule.

### 4.1 `ProcessShipment` (SOAPAction `"ProcessShipment"`)

**Request.** `<RequestedShipment><ShipRequest>…` [S:`ClientShipClass.cs:7948-8010`; W]:

| Field (in order) | Type | Required | Notes |
| --- | --- | --- | --- |
| `AlternativeServices` | bool | no (`Specified` twin) | in source, not in the WSDL snapshot. Sent as `false` by PP and SA. `WantAlternativeServices(Specified, value)` gates it (`:1219`) |
| `PrintSpecification` | `PrintSpecification` | schema: `TextCN23`, `LabelSpecType`, `LabelOrientType`, `LabelStock` value-typed (required); `Resolution` default 203; `MergeDocs`, `PrintDocs`, `ThermalPdf` optional bools; `LabelPrinter`, `DocumentPrinter` strings | `PrintDocs true` plus a `LabelPrinter` makes CSS print instead of returning bytes [D:`Systems/selector/architecture.md`] |
| `Shipment` | `RequestedShipment` | yes | children `Recipient`, `Shipment` (details), optional `PayPoint` |
| `AuthenticationDetails` | see 3.4 | yes | last |

`Recipient` [S:`:9537-9636`]: `SequenceId` (int, req), `SaveAB` (int, req), `AdditionalRefrences`* (string, repeat), `ShipmentReference` (max 35), `ConsigneeReference` (max 35), `AddressAndContact` (`Party`), optional `ConsigneeNotifications`. `Party`: `IOSS, VAT, EORI, UKIMS, Company` (max 50), `ContactAddress`, `ContactPerson`. `Address`: `Geocode, AddressReference, Street` (50), `District` (35), `County` (35), `Town` (50), `Postcode` (15), `CountryCode` (2, default `GB`), `UrbanCode, Residential`. `Person`: `PersonName, Phone, Fax, Mobile, E_Mail, PersonTin`. PP always sends a `ContactPerson` element because **Selector fails with a null reference when it is absent** (`PP:client.go:287`; that comment is the only evidence, [C] and unconfirmed by a recording).

`Shipment` details [S:`:6590-7092`], the fields PP/SA set, in order: `Liquids` (bool, req), `CarbonNeutral` (bool, req), `ShipperId` (int, req; 0 and 12345 both booked in the sandbox [R]), `DepartmentCode`, `DespatchDate` (xs:date `yyyy-MM-dd`, req; must be today or later in UK time unless the carrier is exempt, `ValidateProcedures.cs:7621-7634`), `CarrierService`{`ContractNo` (20), `RouteMapCode` (6), `Carrier`, `ServiceCode`, `PackageCode`, `Dropoff` (enum, req: `REGULAR_PICKUP, REQUEST_COURIER, DROP_BOX, BUSINESS_SERVICE_CENTER, STATION`)}, `Packages`* (`RequestedPackage`: `PackageType, ExpLicense` (bool, req)`, PackageUnits, ItemID` (int, req)`, Weight` (decimal, req)`, Dimensions`{`PackLength, PackHeight, PackWidth` ints, all req if present}`, Content`), `ConsolidateShipment` (bool, req), `CustomsDetails`, `Instructions`, `Content`, `TotalWeight` (decimal, req), `Packs` (int, req), `ShipmentID` (int, req). Many more optional carrier blocks exist (`FreightDetails`, `CODDetails`, `HazardDetails`…); neither client uses them. `CustomsDetails`' required value fields in the recorded Canada request: `Proforma, PLT, DocOnly, Admissibility, TermsOfSale, Purpose, RecipientType, CustomsInvoiceDate`, and per commodity `QuantityUnitCode, ExportLicenseExpirationDate, NumberOfPieces, Quantity, Weight` (`PP:testdata/validate-customs.request.xml`; PP's comment says `ExportLicenseExpirationDate` is required whether or not a licence applies, `PP:wire.go:189`).

**Reply.** `ProcessedShipment/ProcessShipmentResult` = `ShipReply` [S:`:7548-7580`]: `ResponseStatus` (enum, req), `Shipment` (`ProcessedShipment`). `ProcessedShipment` children in order [S:`:6017-6180`]: `SpringLabels`*, `PickupWindow`, `DeliveryWindow`, `CarrierCharge`, `CarrService` (echoes `ContractNo, Carrier, ServiceCode, Dropoff` [R]), `Charges`*, `Consolidated` (bool, always emitted), `ShipmentStatus` (`ResponseDetails`), `Packages`* (`ProcessedPackage`: `ItemNo, ConsignmentNo, SequenceID, ItemID, PackageNo, Labels`* (…more optional)), `PrintDocuments`*, `ShipmentID` (int, echoes the request's, or 1 if the request had no shipment block: `ClientShipService.asmx.cs:1204-1207`; the sandbox echoed 0 for 0 [R: findings row 2]), `ReturnConsignmentNo`*, `ConsignmentNo2`*, **`ConsignmentNo`*** last. A booked reply carries `ConsignmentNo` once per package inside `Packages` **and** once at the end of `Shipment` [R]. Multi-package bookings share one shipment-level consignment and have per-package `PackageNo` [R: `PP:testdata/process-multipackage.reply.xml`]. `PrintDocument` (labels): `SequenceID, Image` (base64Binary), `Printed` (bool), `Description`, `NumberOfCopies`, `DocumentType` (`PDF` or `ZPLII` in recordings) [S:`:2253-2360`; R]. Label bytes are base64 in `Image`; PP tolerates line-wrapped base64 (`PP:wire.go` `base64Bytes`), which hints CSS may wrap it, `UNVERIFIED`.

**Status behaviour** [S:`ClientShipService.asmx.cs:1170-1355`]: `ResponseStatus` = `ShipmentStatus.Status` at the end (`:1355`). `WARNING` and `NOTE` still book. A shipment with status `FAILURE`, or `ERROR` unless `Shipment.SaveNotValid` is set, is not processed further. The alternative-services retry (`AlternativeServices`) can rewrite the service and re-validate; PP and SA send `false`. All exceptions become `0030` or `0040` FAILURE (`:1344-1348`).

**Observed codes** (all [R]): `ERROR 0003 Error` ("Postcode required."; "Warning: Company name is missing.\nChosen date of despatch is earlier than today."); `WARNING 0002 Warning` ("Warning: Company name is missing.", books); `FAILURE 0010` bad credentials; `SUCCESS` with no code. A `SUCCESS` with no consignment at all appears in `PP:testdata/process-no-consignment.reply.xml` and `SA:testdata/reply-success-no-consignment.xml`; both clients treat it as transient/undecodable. Whether real Selector emits that is `UNVERIFIED` (probably hand-built to test client handling). SA also tests a reply with `FAILURE` and no `Shipment` element at all (`reply-failure-no-shipment.xml`), `UNVERIFIED` as real.

**No duplicate guard**: three calls with the same `ShipmentReference` booked three consignments; `DailyShipQuery` returns the reference **upper-cased** [R: findings rows 1, 6; S: guardrail in `Engineering/css/architecture.md`]. (Selector2's G4 decision intentionally departs from this.)

**Synthetic pair, success** (recorded structure, PDF label):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body>
<RequestedShipment xmlns="http://justshoutgfs.com/Client/Ship/v5/"><ShipRequest>
  <AlternativeServices>false</AlternativeServices>
  <PrintSpecification><Resolution>203</Resolution><TextCN23>0</TextCN23><PrintDocs>false</PrintDocs><LabelSpecType>PDF</LabelSpecType><LabelOrientType>BOTTOM_EDGE_OF_TEXT_FIRST</LabelOrientType><LabelStock>PAPER_4X6</LabelStock></PrintSpecification>
  <Shipment>
    <Recipient><SequenceId>0</SequenceId><SaveAB>0</SaveAB><ShipmentReference>EX-REF-001</ShipmentReference>
      <AddressAndContact><Company>Example Ltd</Company>
        <ContactAddress><Street>1 Example Street</Street><Town>Exampleton</Town><Postcode>EX1 1AA</Postcode><CountryCode>GB</CountryCode></ContactAddress>
        <ContactPerson><PersonName>Sam Example</PersonName><Phone>07700900000</Phone><E_Mail>sam@example.invalid</E_Mail></ContactPerson>
      </AddressAndContact></Recipient>
    <Shipment><Liquids>false</Liquids><CarbonNeutral>false</CarbonNeutral><ShipperId>1</ShipperId><DespatchDate>2030-01-01</DespatchDate>
      <CarrierService><ContractNo>EXCONTRACT</ContractNo><Carrier>EXCARRIER</Carrier><ServiceCode>EXSVC</ServiceCode><Dropoff>REGULAR_PICKUP</Dropoff></CarrierService>
      <Packages><ExpLicense>false</ExpLicense><ItemID>1</ItemID><Weight>1.25</Weight></Packages>
      <ConsolidateShipment>false</ConsolidateShipment><TotalWeight>1.25</TotalWeight><Packs>1</Packs><ShipmentID>0</ShipmentID></Shipment>
  </Shipment>
  <AuthenticationDetails><VersionId><Major>5</Major><Minor>0</Minor><Intermediate>0</Intermediate></VersionId><UserID>EXAMPLE_USER</UserID><UserPassword>EXAMPLE_PASSWORD</UserPassword></AuthenticationDetails>
</ShipRequest></RequestedShipment></soap:Body></soap:Envelope>
```

```xml
<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema"><soap:Body>
<ProcessedShipment xmlns="http://justshoutgfs.com/Client/Ship/v5/"><ProcessShipmentResult><ResponseStatus>SUCCESS</ResponseStatus><Shipment>
  <CarrService><ContractNo>EXCONTRACT</ContractNo><Carrier>EXCARRIER</Carrier><ServiceCode>EXSVC</ServiceCode><Dropoff>REGULAR_PICKUP</Dropoff></CarrService>
  <Consolidated>false</Consolidated>
  <ShipmentStatus><Status>SUCCESS</Status><StatusDescription /></ShipmentStatus>
  <Packages><ConsignmentNo>TEST0000000001</ConsignmentNo><SequenceID>1</SequenceID><ItemID>1</ItemID><PackageNo>TEST0000000001</PackageNo>
    <Labels><SequenceID>1</SequenceID><Image>JVBERi0xLjQgU1lOVEhFVElDLUxBQkVM</Image><Printed>false</Printed><NumberOfCopies>1</NumberOfCopies><DocumentType>PDF</DocumentType></Labels></Packages>
  <ShipmentID>0</ShipmentID><ConsignmentNo>TEST0000000001</ConsignmentNo>
</Shipment></ProcessShipmentResult></ProcessedShipment></soap:Body></soap:Envelope>
```

**Synthetic reply, validation error with a prior warning** (recorded structure; note the code changed from `0002` to `0003`):

```xml
<ProcessedShipment xmlns="http://justshoutgfs.com/Client/Ship/v5/"><ProcessShipmentResult><ResponseStatus>ERROR</ResponseStatus><Shipment><Consolidated>false</Consolidated>
  <ShipmentStatus><Status>ERROR</Status><StatusCode>0003</StatusCode><StatusMessage>Error</StatusMessage><StatusDescription>Warning: Company name is missing.
Postcode required.</StatusDescription></ShipmentStatus><ShipmentID>0</ShipmentID></Shipment></ProcessShipmentResult></ProcessedShipment>
```

**Synthetic reply, `0066`** (constructed from `CommonProcedures.cs:52` and the `ProcessShipment` flow; envelope wrapper omitted):

```xml
<ProcessedShipment xmlns="http://justshoutgfs.com/Client/Ship/v5/"><ProcessShipmentResult><ResponseStatus>FAILURE</ResponseStatus><Shipment><Consolidated>false</Consolidated>
  <ShipmentStatus><Status>FAILURE</Status><StatusCode>0066</StatusCode><StatusMessage>Database updating</StatusMessage><StatusDescription>Database maintanence. Please, wait several minutes</StatusDescription></ShipmentStatus><ShipmentID>0</ShipmentID></Shipment></ProcessShipmentResult></ProcessedShipment>
```

### 4.2 `ProcessShipments` (SOAPAction `"ProcessShipments"`)

No recorded wire sample. Everything below is [S] and [W]; RP drives it via node `soap`.

**Request.** `<RequestedShipments><ShipRequests>`: `AlternativeServices` (bool), `AuthenticationDetails`, `Shipments` (wrapped: `<Shipments><RequestedShipment>…</RequestedShipment>*</Shipments>`; `RequestedShipment` has the same content as 4.1's `Shipment`), `PrintSpec` (note: **`PrintSpec`, not `PrintSpecification`**; one shared spec for all shipments) [S:`ClientShipClass.cs:7810-7870`]. RP sends `Shipments.RequestedShipment` (array) and `PrintSpec` with its defaults, with shipments that fail its EU commodity pre-check removed (`RP:process-shipments.handler.ts`).

**Reply.** `ProcessedShipments/ProcessShipmentsResult` = `ShipReplies`: `ResponseStatus`, `Shipments` (wrapped: `<Shipments><ProcessedShipment>…</ProcessedShipment>*</Shipments>`) [S:`:7507-7545`]. Each `ProcessedShipment` has the same content as 4.1's `Shipment`.

**Behaviour** [S:`ClientShipService.asmx.cs:1458-1573`]:

- One shipment slot is created per request item up front, `ShipmentStatus` initialised to `SUCCESS` with no code, `ShipmentID` echoed from the item or `i + 1`.
- **Auth is checked once and written only to item 0** (`InternalConnection(conn, shipReplies.Shipments[0].ShipmentStatus, …)`, `:1490`). On failure items 1..n keep status `SUCCESS` and the top-level `ResponseStatus` becomes `FAILURE` (max across items). Contrast the site-locked case, where item 0's status is copied to the others (`:1545-1551`).
- `ShipRequests.PrintSpec` is `.Clone()`d without a null check (`:1506`), so omitting it throws and each affected item becomes `FAILURE 0030 Request structure is invalid` with the .NET message, expected text `Object reference not set to an instance of an object.` (`UNVERIFIED` for the exact text; PP filters that phrase out of user messages, `PP:errors.go:118`, which is evidence real replies contain it).
- `Shipments == null` returns only `ResponseStatus FAILURE` with no `Shipments` (`:1464-1468`). An empty array does not null-check and `shipReplies.Shipments[0]` throws.
- Final `ResponseStatus` is the maximum item status (`:1569-1574`).

**Synthetic pair, two shipments, one fails** (constructed; envelope wrapper omitted; the request body shown abbreviated by `…` where it repeats 4.1):

```xml
<RequestedShipments xmlns="http://justshoutgfs.com/Client/Ship/v5/"><ShipRequests>
  <AlternativeServices>false</AlternativeServices>
  <AuthenticationDetails>…[AUTH]…</AuthenticationDetails>
  <Shipments>
    <RequestedShipment><Recipient>…EX-REF-001…</Recipient><Shipment>…</Shipment></RequestedShipment>
    <RequestedShipment><Recipient>…EX-REF-002, no Postcode…</Recipient><Shipment>…</Shipment></RequestedShipment>
  </Shipments>
  <PrintSpec><TextCN23>0</TextCN23><PrintDocs>false</PrintDocs><LabelSpecType>ZPLII</LabelSpecType><LabelOrientType>BOTTOM_EDGE_OF_TEXT_FIRST</LabelOrientType><LabelStock>PAPER_4X6</LabelStock></PrintSpec>
</ShipRequests></RequestedShipments>
```

```xml
<ProcessedShipments xmlns="http://justshoutgfs.com/Client/Ship/v5/"><ProcessShipmentsResult><ResponseStatus>ERROR</ResponseStatus><Shipments>
  <ProcessedShipment><Consolidated>false</Consolidated><ShipmentStatus><Status>SUCCESS</Status><StatusDescription /></ShipmentStatus>
    <Packages><ConsignmentNo>TEST0000000002</ConsignmentNo><SequenceID>1</SequenceID><ItemID>1</ItemID><PackageNo>TEST0000000002</PackageNo>
      <Labels><SequenceID>1</SequenceID><Image>XlhBXkZPNTAsNTBeRkRTWU5USEVUSUNeRlNeWFo=</Image><Printed>false</Printed><NumberOfCopies>1</NumberOfCopies><DocumentType>ZPLII</DocumentType></Labels></Packages>
    <ShipmentID>1</ShipmentID><ConsignmentNo>TEST0000000002</ConsignmentNo></ProcessedShipment>
  <ProcessedShipment><Consolidated>false</Consolidated><ShipmentStatus><Status>ERROR</Status><StatusCode>0003</StatusCode><StatusMessage>Error</StatusMessage><StatusDescription>Postcode required.</StatusDescription></ShipmentStatus><ShipmentID>2</ShipmentID></ProcessedShipment>
</Shipments></ProcessShipmentsResult></ProcessedShipments>
```

### 4.3 `ValidateShipments` (SOAPAction `"ValidateShipments"`) and `ValidateShipment`

`ValidateShipment` (singular) is what PP calls; its request is the **same `ShipRequest` as 4.1 under wrapper `RequestedValidateShipment`**; its result is a `StatusResponse` (`Status`, `ResponseDetails`) [S:`ClientShipService.asmx.cs:4830-4921`]. Recorded: ok (`Status SUCCESS`, `ResponseDetails` with `StatusCode 0000`, empty description), invalid (`ERROR 0003`, newline-joined messages), customs-rejected, bad auth (`FAILURE 0010`) [R: `PP:testdata/validate-*.reply.xml`]. It books nothing [R: findings row 5]. An example of the OK reply, recorded structure:

```xml
<ValidatedShipment xmlns="http://justshoutgfs.com/Client/Ship/v5/"><ValidateShipmentResult><Status>SUCCESS</Status>
  <ResponseDetails><Status>SUCCESS</Status><StatusCode>0000</StatusCode><StatusDescription /></ResponseDetails></ValidateShipmentResult></ValidatedShipment>
```

`ValidateShipments` (plural): **no recorded sample.** Request: wrapper `RequestedValidateShipments`, parameter `ShipRequests` with exactly the content of 4.2 (`AlternativeServices`, `AuthenticationDetails`, wrapped `Shipments`, `PrintSpec`). Reply `ValidatedShipments`/`ValidateShipmentsResult` = `ValidatedShipments` [S:`ClientShipClass.cs:6396-6414`]: `Status` (`StatusResponse`) then `ValidatedShips` (wrapped; each `ValidatedShipment` = `Status` (`StatusResponse`) then `RequestedShipment` (an **echo** of the input shipment after validation, cloned, so server-side mutations such as upper-casing the contact name or defaulting `DespatchDate` show up in it) [S:`ClientShipService.asmx.cs:4730-4734`; mutation sites e.g. `ValidateProcedures.cs:122, 7626`]).

Behaviour [S:`:4710-4820`]:

- No shipments requested: `ValidateShipments` returns top `Status ERROR` via `AddValidationError("None shipments requested for validation")` (`:4723`), message `Error`, code `0003`, and no `ValidatedShips`. A `null` `Shipments` array throws before that (`:4721` dereferences `.Length`), `UNVERIFIED` what the caller sees (probably an HTTP 500 fault).
- Auth failure is recorded on `ships.Status.ResponseDetails` only (`:4738`). Each `ValidatedShips[i].Status` stays at its constructed default, `SUCCESS` with code `0000`. So a bad password yields top-level `FAILURE` but every item `SUCCESS`. RP maps per-item errors to 200/207/400 and would see no per-item errors here. `UNVERIFIED` against a recording.
- Catch-all uses code **`0040`** with message `Request structure is invalid` (`:4811`), unlike `0030` elsewhere.
- Top `Status` = `ResponseDetails.Status` at the end (`:4819`); per-item `Status.Status` copies each item's `ResponseDetails.Status` (`:4801`). The top level is not the maximum of the items: item errors do not raise the top-level status, only the top-level's own `ResponseDetails` does.

**Synthetic pair** (constructed; envelope omitted; second item invalid):

```xml
<RequestedValidateShipments xmlns="http://justshoutgfs.com/Client/Ship/v5/"><ShipRequests>
  <AlternativeServices>false</AlternativeServices><AuthenticationDetails>…[AUTH]…</AuthenticationDetails>
  <Shipments><RequestedShipment>…</RequestedShipment><RequestedShipment>…no Postcode…</RequestedShipment></Shipments>
  <PrintSpec>…</PrintSpec></ShipRequests></RequestedValidateShipments>
```

```xml
<ValidatedShipments xmlns="http://justshoutgfs.com/Client/Ship/v5/"><ValidateShipmentsResult>
  <Status><Status>SUCCESS</Status><ResponseDetails><Status>SUCCESS</Status><StatusCode>0000</StatusCode><StatusDescription /></ResponseDetails></Status>
  <ValidatedShips>
    <ValidatedShipment><Status><Status>SUCCESS</Status><ResponseDetails><Status>SUCCESS</Status><StatusCode>0000</StatusCode><StatusDescription /></ResponseDetails></Status><RequestedShipment>…echo…</RequestedShipment></ValidatedShipment>
    <ValidatedShipment><Status><Status>ERROR</Status><ResponseDetails><Status>ERROR</Status><StatusCode>0003</StatusCode><StatusMessage>Error</StatusMessage><StatusDescription>Postcode required.</StatusDescription></ResponseDetails></Status><RequestedShipment>…echo…</RequestedShipment></ValidatedShipment>
  </ValidatedShips></ValidateShipmentsResult></ValidatedShipments>
```

### 4.4 `CommitShipGroup` (SOAPAction `"CommitShipGroup"`)

**No recorded sample, no client other than RP, and no PP/SA use.** [S:`ClientShipService.asmx.cs:1917-2057`; types `ClientShipClass.cs:8502-8610, 4169-4213`].

**Request.** `<RequestedCommitShipGroup><ShipGroupRequest>`: `AuthenticationDetails`, `ShipGroups`* (flat; each `CarrierShipGroup`: `Carrier` (string), `Consignments`* (flat strings)). RP sends `ShipGroups: <body array>` (`RP:commit-ship-group.handler.ts`).

**Reply.** `<ProcessedCommitShipGroup><CommitShipGroupResult>`: `CommitTime` (xs:dateTime, req), `Status` (enum, req), `ErrorShipGroups`* (flat; each `ErrorShipGroup`: `ShipGroup` (`CarrierShipGroup`), `ResponseDetails`).

**Behaviour:**

- `CommitTime` is `DateTime.Today.AddHours(now.Hour)…` to the second, server local time. Its wire format (offset or none) is `UNVERIFIED`; `DateTime.Today` has local kind, so a `+hh:mm` suffix is likely.
- `InternalConnection` writes into a local `rd`, then **only `rd.Status` is copied** to the reply (`:1928-1929`). **No `ResponseDetails` is ever returned for an auth, version or `0066` failure.** The reply is `Status FAILURE`, no `ErrorShipGroups`. RP special-cases exactly this: it throws a 400 when `Status` is `FAILURE`/`ERROR` and `ErrorShipGroups` is absent (`RP:commit-ship-group.handler.ts`, "`!('ErrorShipGroups' in …)`").
- A null or empty `ShipGroups` sets `Status FAILURE` (`:1930-1931`) even after a good login (and then, if auth succeeded, the loop is still entered; `foreach` over null throws, `UNVERIFIED` outcome).
- Per-consignment errors collect in `ErrorShipGroups`, each with `ResponseDetails.StatusMessage = "Commit error"`, **no code**, and description text built with `string.Format` (`:1990-2014`):
  - status 0, `ERROR`: `"{carrier} consignment {cons} not found"`
  - carrier is Royal Mail, `WARNING`: `"Use  method CommitShipments for carrier {carrier}"` (two spaces, sic)
  - already committed, `WARNING`: `"{carrier} consignment {cons} already commited"` (sic)
- If any error entries exist and the top status was `SUCCESS`, it becomes `WARNING` (`:2052-2056`). A Firebird exception rolls back and sets `ERROR`; any other exception sets `FAILURE` (`:2040, 2048`).
- `carrier` is upper-cased on the way in; consignment numbers are upper-cased for lookup (`:1950, 1973, 1984`).
- Side effects: `update shipments set status = status + 2, manifest_date = …`, then `EXECUTE PROCEDURE SHIP_COMMITED` and `SHIP_STATUS_CHANGED('SHIP_COMMITED')` (`:1951-1960, 2029-2031`). Selector2's brief says commit goes no further than marking; fine for C2. The numeric `status` values (1, 2, +2) are used inconsistently with `DeleteShipments` (which sets `status = 2` to mean deleted, `:1863`, while commit selects `status = 2` rows to commit, `:1955`). I did not resolve the meaning of the numbers; see Gaps.

**Synthetic pair** (constructed):

```xml
<RequestedCommitShipGroup xmlns="http://justshoutgfs.com/Client/Ship/v5/"><ShipGroupRequest>
  <AuthenticationDetails>…[AUTH]…</AuthenticationDetails>
  <ShipGroups><Carrier>EXCARRIER</Carrier><Consignments>TEST0000000001</Consignments><Consignments>TEST0000000404</Consignments></ShipGroups>
</ShipGroupRequest></RequestedCommitShipGroup>
```

```xml
<ProcessedCommitShipGroup xmlns="http://justshoutgfs.com/Client/Ship/v5/"><CommitShipGroupResult>
  <CommitTime>2030-01-01T09:30:00</CommitTime><Status>WARNING</Status>
  <ErrorShipGroups><ShipGroup><Carrier>EXCARRIER</Carrier><Consignments>TEST0000000404</Consignments></ShipGroup>
    <ResponseDetails><Status>ERROR</Status><StatusMessage>Commit error</StatusMessage><StatusDescription>EXCARRIER consignment TEST0000000404 not found</StatusDescription></ResponseDetails></ErrorShipGroups>
</CommitShipGroupResult></ProcessedCommitShipGroup>
```

Auth failure or `0066` for this operation (constructed; note the absence of any detail):

```xml
<ProcessedCommitShipGroup xmlns="http://justshoutgfs.com/Client/Ship/v5/"><CommitShipGroupResult><CommitTime>2030-01-01T09:30:00</CommitTime><Status>FAILURE</Status></CommitShipGroupResult></ProcessedCommitShipGroup>
```

### 4.5 `DeleteShipments` (SOAPAction `"DeleteShipments"`) and `CommitShipments` (SOAPAction `"CommitShipments"`)

#### `DeleteShipments`

**Request.** `<RequestedDeleteShipments><Shipments>`: `AuthenticationDetails` first, then `RequestedShipments`* (flat; each `DeleteShipment`: `ConsignmentNo`, `Carrier`) [S:`ClientShipClass.cs:8834-8898`; W; R]. PP and RP send the carrier (PP: from the connection, `PP:client.go:91-100`).

**Reply.** `<ProcessedDeleteShipments><DeleteShipmentsResult>`: `Shipments`* (flat; each `ProcessedDeleteShipment`: `ConsignmentNo`, `Carrier`, `Status` (`ResponseDetails`)) then `Status` (enum) [S:`:8900-8982`]. Note `Shipments` precedes `Status`, and each item's `Status` element is itself a `ResponseDetails` (`Status` nested in `Status`) [R].

**Behaviour** [S:`ClientShipService.asmx.cs:1685-1905`]:

- Items are initialised with the caller's `ConsignmentNo` and `Carrier` echoed, `Status = new ResponseDetails()` (status default `SUCCESS`).
- `Shipments == null` returns just `Status FAILURE` (`:1690-1694`).
- Auth failure goes into **item 0 only** (`:1712`); right after, `Shipments.AuthenticationDetails.VersionId.Major` is dereferenced with no null guard (`:1714`), so a null `AuthenticationDetails` throws and is caught as `0030` appended to item 0 (`UNVERIFIED`).
- The carrier is normalised (`CheckCarrName`) then upper-cased and trimmed to 20 chars; consignment trimmed to 35 (`:1730-1750`).
- Per item: blank carrier or consignment -> `FAILURE 0030 "Request structure is invalid"` (description and message both) (`:1741-1745`). Not found -> `ERROR 0400 "Shipment not found"`. `status == 2` -> `ERROR 0400 "Shipment Already Deleted"`. `status > 2` -> `ERROR 0401 "Upload Shipment can't be deleted"`. Otherwise carrier-specific cancellation (FedEx, Royal Mail, UPS, Amazon, …) then `SUCCESS`; on success **no `StatusCode`/`StatusMessage` is set** (recorded `delete.reply.xml`: `<Status><Status>SUCCESS</Status><StatusDescription /></Status>`).
- Successful deletes are applied in one transaction: `update shipments set status = 2 …` then `SHIP_STATUS_CHANGED('SHIP_DELETED')` (`:1858-1862`); a Firebird error rolls back and flips every `SUCCESS` item to `FAILURE 0040` (`:1869-1885`).
- Top `Status` = maximum item status (`:1905-1911`).

**Synthetic pair, one good one unknown** (recorded structure):

```xml
<RequestedDeleteShipments xmlns="http://justshoutgfs.com/Client/Ship/v5/"><Shipments>
  <AuthenticationDetails>…[AUTH]…</AuthenticationDetails>
  <RequestedShipments><ConsignmentNo>TEST0000000001</ConsignmentNo><Carrier>EXCARRIER</Carrier></RequestedShipments>
  <RequestedShipments><ConsignmentNo>TEST0000009999</ConsignmentNo><Carrier>EXCARRIER</Carrier></RequestedShipments>
</Shipments></RequestedDeleteShipments>
```

```xml
<ProcessedDeleteShipments xmlns="http://justshoutgfs.com/Client/Ship/v5/"><DeleteShipmentsResult>
  <Shipments><ConsignmentNo>TEST0000000001</ConsignmentNo><Carrier>EXCARRIER</Carrier><Status><Status>SUCCESS</Status><StatusDescription /></Status></Shipments>
  <Shipments><ConsignmentNo>TEST0000009999</ConsignmentNo><Carrier>EXCARRIER</Carrier><Status><Status>ERROR</Status><StatusCode>0400</StatusCode><StatusMessage>Shipment not found</StatusMessage><StatusDescription>Shipment not found</StatusDescription></Status></Shipments>
  <Status>ERROR</Status>
</DeleteShipmentsResult></ProcessedDeleteShipments>
```

#### `CommitShipments`

**Request.** `<RequestedCommitShipments><CarrierShipments>`: `ManifestCopies` (int, optional, default 2), `SiteID` (int, req), `PrintSpecification`, `AuthenticationDetails`, `CarrierServiceGroups`* (flat; each `CarrierServiceGroup`: `Carrier`, `ServiceType` enum, req: `DOMESTIC, DOMESTIC_FREIGHT, EUROROAD, INTERNATIONAL, ANY, DOMESTIC_DETAIL, RM_TRACKED, RM_HV_TRACKED, RM_RANGES, RM_OBA, RM_RELAY, RM_COMMON`) [S:`ClientShipClass.cs:8428-8500, 4215-4265, 185-213`]. PP sends `ManifestCopies 1`, `SiteID` 0, a PDF spec (`PP:client.go:121-135`).

**Reply.** `<ProcessedCommitShipments><CommitShipmentsResult>`: `CommitShips` (int, req), `Status` (enum, req), `CarrierDocuments`* (flat; each `CarrierDocument`: `CarrierServiceGroup`, `PrintDocument` (the manifest: `SequenceID, Image, Printed, Description, NumberOfCopies, DocumentType`), `ResponseDetails`) [S:`:8528-8576, 8067-8110`; PP fixtures R/hand-built].

**Behaviour** [S:`ClientShipService.asmx.cs:2067-2510`]:

- Four branches: (a) any group naming `ROYAL MAIL` or `COLL8`: manifest via the carrier proxy first (`:2083-2100`); (b) web version (5.1.1 or 5.1.3): `COMMIT_WEB_SHIPMENTS` stored procedure, filling `CommitShips` (`:2103-2175`); (c) generic: for each (or every) carrier with printed shipments, mark `status = status + 2`, fire `SHIP_COMMITED`, and render a PDF manifest per carrier via `InternalGetReport` (`:2178-2420`); (d) fall-through: a single `CarrierDocument` whose `ResponseDetails` is `rd`, i.e. the auth/version/`0066` failure (`:2458-2466`).
- **`CommitShips` is only set in branch (b).** In the generic branch (c) it stays at its default 0 even when shipments were committed. PP's `commit.reply.xml` shows `CommitShips 3` with a manifest, which cannot come from branch (c) as read. Treat that fixture's count as invented (`UNVERIFIED`). PP only reads `CommitShips` as a count (`PP:client.go:138`).
- No printed shipments for the requested groups: `WARNING 0002 "Processed shipments not found"` (when no groups were given, on `rd` at `:2229-2234`, and at `:2440-2450`) or per-group `ERROR` with code `0002` (sic) and the same text (`:2262-2268`). The second form is `ERROR` carrying a warning code.
- Auth failure or `0066`: one `CarrierDocument` with only `ResponseDetails`; top `Status` = the maximum across documents (`:2494-2506`), so `FAILURE`.
- Manifest documents are `PrintDocument.DocumentType = PDF`, `NumberOfCopies = ManifestCopies` (min 1) for most carriers, rendered from a report (`:2338-2362`). Several carriers (FedEx, P2P, Hermes parcel shop, Amazon, OCS, BJS, Exelot, DPD NL/DE, Coll8, FedEx API, Royal Mail non-relay) get **no** manifest document and just an item with `SUCCESS` (`:2320-2332`).
- Committing against the shared sandbox is a known hazard: it closes out every tester's shipments on the `TEST` account, so PP refuses to send (`PP:sandbox.go`). Do not record real `CommitShipments` samples there.

**Synthetic pair** (constructed; generic branch):

```xml
<RequestedCommitShipments xmlns="http://justshoutgfs.com/Client/Ship/v5/"><CarrierShipments>
  <ManifestCopies>1</ManifestCopies><SiteID>0</SiteID>
  <PrintSpecification><Resolution>203</Resolution><TextCN23>0</TextCN23><PrintDocs>false</PrintDocs><LabelSpecType>PDF</LabelSpecType><LabelOrientType>BOTTOM_EDGE_OF_TEXT_FIRST</LabelOrientType><LabelStock>PAPER_4X6</LabelStock></PrintSpecification>
  <AuthenticationDetails>…[AUTH]…</AuthenticationDetails>
  <CarrierServiceGroups><Carrier>EXCARRIER</Carrier><ServiceType>DOMESTIC</ServiceType></CarrierServiceGroups>
</CarrierShipments></RequestedCommitShipments>
```

```xml
<ProcessedCommitShipments xmlns="http://justshoutgfs.com/Client/Ship/v5/"><CommitShipmentsResult>
  <CommitShips>0</CommitShips><Status>SUCCESS</Status>
  <CarrierDocuments><CarrierServiceGroup><Carrier>EXCARRIER</Carrier><ServiceType>ANY</ServiceType></CarrierServiceGroup>
    <PrintDocument><SequenceID>1</SequenceID><Image>JVBERi0xLjQgU1lOVEhFVElDLU1BTklGRVNU</Image><Printed>false</Printed><NumberOfCopies>1</NumberOfCopies><DocumentType>PDF</DocumentType></PrintDocument>
    <ResponseDetails><Status>SUCCESS</Status><StatusDescription /></ResponseDetails></CarrierDocuments>
</CommitShipmentsResult></ProcessedCommitShipments>
```

(Per-document `CarrierServiceGroup.ServiceType` is `ANY` in the generic branch by construction, `:2218, 2252`, regardless of the requested type. PP's fixture shows `DOMESTIC`; `UNVERIFIED` which carrier path produced that.)

### 4.6 `DailyShipQuery` (SOAPAction `"DailyShipQuery"`), required by PP and SA

[S:`ClientShipService.asmx.cs:5021-5190`; types `ClientShipClass.cs:9157-9265`; R: `PP:testdata/daily.*`, `SA:testdata/reply-daily-query.xml`]. Request `<RequestedDailyQuery><DailyRequest>`: `AuthenticationDetails`, `ShipDate` (xs:dateTime; both clients send `YYYY-MM-DDT00:00:00`), `SiteId` (int, req; both send 0), `Carrier` (optional), `ShipmentState` (enum, req: `ANY, IMPORTED_WITH_ERRORS, PREPARED, PRINTED, DELETED, MANIFESTED, MANIFESTED_DELETED, UPLOADED, UPLOADED_DELETED`). Reply `<ProcessedDailyQuery><DailyShipQueryResult>`: `Status` (bare `ResponseDetails`), `DailyShipments`* (flat; `ConsignmentNo, Carrier, ShipRef, Packs, Status` (ShipState text), `PrintTime` (xs:dateTime **without** offset in recordings)). `ShipRef` is upper-cased. There is no query by reference. The `Carrier` element is optional; PP and SA both omit it. Both clients read only `ConsignmentNo, Carrier, ShipRef, Status` (and `Packs` in PP).

## 5. What the callers do (fields filled and operations used)

| Client | Operations | Source |
| --- | --- | --- |
| **Parcel Portal** (Go) | `ValidateShipment`, `ProcessShipment`, `DeleteShipments`, `CommitShipments`, `DailyShipQuery`. One shipment per call; batches loop single calls (`PP:apps/svc/README.md:171`). Never `ProcessShipments`, `ValidateShipments`, `CommitShipGroup`. | `PP:client.go:36-196` |
| **selector-adapter** (Go) | `ProcessShipment`, `DailyShipQuery` only (`SA:internal/adapters/selector/client.go`, `daily.go`). The explainer's claim that it derives the endpoint by dropping `?wsdl` is not what the code does: `SELECTOR_ENDPOINT` is required config (`SA:internal/config/config.go:78`). | |
| **selector-rest-proxy** (Node, `soap` lib, WSDL fetched on **every request**: `RP:src/selector.ts` `getClient`) | `ProcessShipments`, `ValidateShipments`, `DeleteShipments`, `CommitShipGroup`, `CommitShipments`. Never singular process/validate. | `RP:src/handlers/selector/*.handler.ts` |

Fields filled:

- **PP** `ProcessShipment`/`ValidateShipment`: `AlternativeServices=false`; `PrintSpecification` (203, `TextCN23=0`, `PrintDocs=false`, `PDF` or `ZPLII`, `BOTTOM_EDGE_OF_TEXT_FIRST`, `PAPER_4X6`); `Recipient` (`SequenceId 0`, `SaveAB 0`, refs, `Company`, address incl. `District`/`County`, `CountryCode`, always a `ContactPerson`); details (`Liquids false`, `CarbonNeutral false`, `ShipperId`, `DespatchDate`, `CarrierService{ContractNo, Carrier, ServiceCode, Dropoff=REGULAR_PICKUP default}`, `Packages` with `PackageType`, `ExpLicense false`, `PackageUnits`, `ItemID` i+1, `Weight`, `Dimensions` only if any dimension >0, `Content`; `ConsolidateShipment false`; `CustomsDetails` only for customs shipments with `Proforma true`, `Admissibility PKG`, `RecipientType`; `Instructions`; `Content`; `TotalWeight`; `Packs`; `ShipmentID 0`); `AuthenticationDetails` with `VersionId 5.0.0` (`PP:client.go:252-340`).
- **SA** `ProcessShipment`: same skeleton with `ContractNo/Carrier/ServiceCode/Dropoff` from config, one `RequestedPackage{ItemID 1, Weight}` and `TotalWeight/Packs 1`; `ContactPerson` only if any contact datum exists (`SA:booker.go:35-72`). It does not always send `ContactPerson`, unlike PP. A recorded SA success has no contact person with Company present, so both shapes are accepted by the sandbox; PP's comment attributes a failure to a missing `ContactPerson`, possibly when there is no company either. `UNVERIFIED` which.
- **RP**: builds JS objects for node `soap`, defaulting `PrintSpec` and auth (`RP:selector.ts`, `defaults.ts`); passes the caller's JSON body through for the shipment content.

Client-side reading of replies (what compatibility must preserve):

- PP and SA treat only `ERROR` and `FAILURE` as rejection; `NOTE` and `WARNING` are bookings (`PP:client.go:201`, `SA:client.go:175-181`).
- Both decode by element name with a **namespace-agnostic** child match for results, and require the wrapper (`ProcessedShipment`, `ValidatedShipment`, `ProcessedDeleteShipments`, `ProcessedCommitShipments`, `ProcessedDailyQuery`) and the `*Result` child.
- PP maps SOAP `Fault` first, then HTTP >=300, then undecodable (`PP:client.go:236-248`); SA classifies in the same spirit (`SA:client.go:141-185`).
- Both treat `StatusCode 0010` as a configuration fault (PP: retryable, "credentials not accepted"; SA: `ConfigFault`) (`PP:errors.go:83`, `SA:booker.go:89`).
- PP's retry decision depends on whether the request was sent (`httptrace.WroteRequest`); no wire impact.

## 6. Where sources disagree

| Topic | Source A | Source B | Verdict |
| --- | --- | --- | --- |
| Auth location | `AuthConnDetails` **header**: `Systems/selector/architecture.md:108`, `Engineering/css/architecture.md` G5, `selector2/README.md:183`, `iam.tf:2`, R2 | `AuthenticationDetails` **body element**: [S] `CommonProcedures.cs:25`, [W] no header, [C] PP, SA, RP, vault `Engineering/css/overview.md` | B. A is a misreading of a C# parameter name. |
| Validation error code | doc comment `0200 Validation error` (`ClientShipClass.cs:1305`) | code and recordings `0003` (`ClientShipClass.cs:1172-1216`, `PP:testdata/validate-invalid.reply.xml`) | Code and recordings. `0200` only appears in credit-balance and manifest paths. |
| Commit no-op code | PP fixture `commit-rejected.reply.xml`: `0500 / No shipments to manifest.` | `grep` for `"0500"` in CSS: none; CSS's no-shipments case is `0002 "Processed shipments not found"` | CSS. The PP fixture is not server truth. |
| Delete not-found text | RP mock fixture: `Shipment not fount` ("mock the selector typo", `RP:src/__fixtures__/selector.fixture.js:217`) | CSS: `Shipment not found` (`ClientShipService.asmx.cs:1759-1760`); PP recording `delete-unknown.reply.xml` agrees | CSS and PP. The "fount" typo exists elsewhere (`FedexProcedures.cs:552`, `DHLFreightProcedures.cs:553`: "account not fount") but not here. |
| Status enum | WSDL and source: five values | RP OpenAPI `ResponseDetails.Status` adds `PENDING` (`OAS` line 760) | WSDL and source. `PENDING` is never emitted by CSS. |
| Commit `CommitShips` | PP fixture count 3 | source: only set in the web branch, 0 otherwise | Source. See 4.5. |
| WSDL vs source | see 2.3 | | Source. |
| Endpoint from WSDL | explainer `Explainers/2026-10-27-selector-adapter-spike-shape.md` (ASSESSED: derives from `?wsdl`) | `SA:config.go:78` `SELECTOR_ENDPOINT` | Code. |
| Operation names in the brief | `ValidateShipments`, `ProcessShipment(s)` | PP uses singular `ValidateShipment` and `DailyShipQuery` | Both ops exist; C2 needs more than five. |

## 7. Gaps

No primary evidence was found for the following. Each is a place where a golden test would currently rest on a guess.

1. **No real recorded wire samples for `ProcessShipments`, `ValidateShipments`, `CommitShipGroup`, or any `CommitShipments` request or real reply.** Everything for these is derived from source order and WSDL. Recording one of each against a non-shared Selector instance (not `sandbox.gfsdeliver.com` for commits) is the most valuable follow-up.
2. **HTTP-level details were never captured**: reply `Content-Type`/charset, status code of a Fault (assumed 500), behaviour when `SOAPAction` is missing, SOAP 1.2 requests, `GET ?wsdl` and `?disco` responses. RP fetches the WSDL on every request, so if selector2 is ever to be pointed at by RP's SOAP path it must serve a compatible `?wsdl`. PP and SA do not need one.
3. **Element-order tolerance and unqualified-namespace tolerance of the real server are unknown** beyond one case; a strict C2 parser may reject requests the real server accepts (RP may emit non-sequence order).
4. **Wire format of `xs:dateTime`/`xs:date` values** (`CommitTime` offset, `PrintTime` precision, `DespatchDate` with an offset) beyond the two recorded `PrintTime` forms.
5. **What an unrecognised or empty request does**: `.NET` exception text per operation (the `Object reference not set…` phrase is only inferred from PP's filter), HTTP 500 vs 200, and null `AuthenticationDetails` handling in each operation.
6. **The numeric `shipments.status` values** (0, 1, 2, +2, 3, 4, 8, 9…) and their mapping to `ShipState` text (`PRINTED`, `DELETED`, `MANIFESTED`, …). Delete and commit read as inconsistent about `2` (`ClientShipService.asmx.cs:1863` vs the commit `update … where (status = 2)` near `:1955`). Selector2's data model needs this table from the database schema, not from CSS.
7. **Which validation messages Selector2 must reproduce.** About 367 `Add*` calls in `ValidateProcedures.cs`; this file samples about ten. B3 owns the list, but there is no machine-readable catalogue.
8. **Whether `0066` has ever been observed live.** It is in the source and in vault prose only; no recording. Also unknown: whether maintenance windows return HTTP 200 with the failure in the body, as the code implies, or a gateway error first.
9. **Authenticated-failure shape in ops the real clients never see failing**: `ProcessShipments`/`DeleteShipments` item-0-only reporting and `CommitShipGroup`'s status-only reply are read from code, not observed.
10. **Label payload encoding details**: whether CSS wraps base64 at 76 chars (PP's decoder tolerates it), and label `DocumentType` for carriers other than the PDF/ZPLII recorded.
11. **Confluence was not searched.** The repos already hold the source, WSDL snapshots and fixtures, so I did not spend the optional MCP queries. Page 351764483 and the Legacy Selector tree may hold an architecture view but are unlikely to hold a wire contract.
12. **Provenance of the Parcel Portal and selector-adapter fixtures** is inferred from test names and comments ("the request the sandbox accepted", `PP:client_test.go:116, 142`); neither repo stores a capture log.
