# B5-B8 / D5: carrier-playground contract digest for the Selector2 egress adapters

Snapshot: `ilg-merak/carrier-playground` `origin/main` `ae57c96` (#15), read via `git show origin/main:<path>` only. No live mock was called. Fixture key names only; no secret values are reproduced.
Citation form: `path:line` is repo-relative to carrier-playground unless it starts with `mu-` (shorthand for `apps/mock-upstreams/src/...`) or is marked as vault. Where a carrier section says `UNVERIFIED`, nobody checked it against a running service or production.

How this was built: one reader per carrier pair read each proxy's source, tests, spec, README and the matching `mock-upstreams` router, and wrote the per-carrier sections below (unedited, so each keeps its own line citations). I then checked the cross-cutting claims in "Common shape" myself against source (the ones cited with my own line numbers) and spot-checked the highest-stakes ones (OCS and Exelot weight multiplier, DPD EU validator, Amazon Logistics PDF refusal). Source beat README and beat the E2 draft wherever they disagreed; the disagreements are listed in "Discrepancies".

Contents: 1. Common shape. 2. Cross-carrier matrices. 3. Per-carrier sections (royalmail, ups, coll8, fedex, dpdeu, amazon-sfp, amazon, bjs, inpost, ocs, exelot, veho). 4. Implications for the egress port. 5. Discrepancies against the E2 draft and the handover. 6. Open questions and unverified items.

---

# 1. Common shape

## 1.1 URLs, keys and the ID token

- Public name per proxy: `https://<name>.mocks.merak.freightops.dev`, `<name>` in `royalmail, ups, coll8, fedex, dpdeu, amazon-sfp, amazon, bjs, inpost, ocs, exelot, veho` (`README.md:39`). The edge map keys are the same except `amazonsfp` (public label `amazon-sfp`) (`iac/projects/mock-edge/edge.tf:4`).
- Config source for selector2: `mock-edge` outputs `service_uris` (run.app URI per key) and `service_account_emails`, keyed `royalmail, ups, coll8, fedex, dpdeu, amazon, amazonsfp, bjs, inpost, ocs, exelot, veho` (`iac/projects/mock-edge/outputs.tf:9-17`). `invoker_members` (list of `serviceAccount:<email>`) grants `roles/run.invoker` on every proxy (`iac/projects/mock-edge/edge.tf:47`, `variables.tf:34-43`). The output description says "Call with a Cloud Run ID token whose audience is the URI" (`outputs.tf:10`).
- Every proxy service is also bound to `allUsers` invoker (example `iac/projects/mock-veho/cloud-run.tf:55-63`, "public by design"). So the ID token is not enforced today.
- **No proxy reads the inbound `Authorization` header.** `git grep -i authorization` over `apps/*/src` shows only outbound uses (e.g. `apps/royal-mail-proxy/src/integrations/http.ts:46`, `apps/ups-proxy/src/auth.ts:22`). The proxies' own ID-token precedent is `X-Serverless-Authorization: Bearer <token>` on calls to mock-upstreams (`packages/mock-kit/src/upstream-auth.ts:37`), token fetched from the metadata server with `audience` = the target origin, cached 3000 s (`upstream-auth.ts:5-30`). Putting the ID token in `Authorization: Bearer` is therefore harmless to the apps. UNVERIFIED: what Cloud Run's frontend does with a Bearer on an `allUsers` service. The safe, proven choice is the `X-Serverless-Authorization` form with `audience` = the run.app URI (not the public `*.mocks.merak.freightops.dev` name, which is a load-balancer host; UNVERIFIED whether an audience of the public name would validate).
- The ApiKy key goes in **`x-api-key`** on every proxy (see each `app.ts`; ApiKy lookup `GET {APIKY_BASE_URL}/api/profile?token=<key>` with the proxy's own service key, `packages/apiky-client/src/index.ts:31-43`). The mock ApiKy answers 401 for a bad service key, 500 for the token `apiky-500`, 403 for any unknown token (`mu-apiky/index.ts:31-47`). The key selects the customer profile, which (per carrier) selects credentials, accounts, warehouses, service entitlements. Nothing about the customer or carrier credentials goes in the request body.
- Fixture key names follow `<carrier>-key-<persona>`; the per-carrier sections list the exact names and what each triggers.

## 1.2 What a bad key returns (status and body differ by carrier)

Verified against each `app.ts` / middleware by the section authors (see each "Auth and headers"):

| carrier | no key | unknown key | `apiky-500` | body |
| --- | --- | --- | --- | --- |
| royalmail, fedex, bjs, inpost, ocs, exelot | 403 | 403 | 403 | `{code:"FORBIDDEN", message:"Authentication failed", details:"Principal <undefined or unknown or an id> could not be authenticated. No additional detail was provided."}` |
| ups | 401 | 403 | 500 | `{errorId, errorCode, messages, metadata}` JSON, even on XML routes |
| coll8 | 401 `{message:"No API key provided"}` | 403 `{message:"Not authorised"}` | 500 `{errorId, errorCode:"SYSTEM_ERROR", messages}` | three different shapes |
| dpdeu | 401 `{message}` | 403 `{message}` | 500 `{code,message,details}` | the 401 and 403 have no `code`; and only when the body already passed spec validation (see 1.5) |
| amazon (Logistics) | 401 `{message}` | 403 `{message}` | 500 `{message}` | gate bodies have no `code` |
| amazon-sfp, veho | 401 | 401 | 401 | RFC 7807 `application/problem+json` `AuthenticationException` |

An adapter cannot tell "bad key" from "ApiKy outage" on any of the 403-everywhere carriers or on sfp/veho. The E2 draft's status table is right at status level (verified); its body shapes are not described.

## 1.3 Health and unknown routes

- `GET /health/liveness` returns 200 `{"ok":true}` with no auth on every proxy except Amazon Logistics, where it falls into the catch-all (200 `{"code":200,"message":"OK","detail":"Server is OK and ready to handle requests"}`) (`apps/amazon-logistics-proxy/src/app.ts:107,222`; handlers: `apps/<carrier>-proxy/src/app.ts` at the lines `git grep -i health` returns, e.g. `apps/ups-proxy/src/app.ts:31`, `apps/veho-proxy/src/app.ts:63`).
- Extra health: `/healthz` on amazon-sfp (`app.ts:110`) and veho (`app.ts:69`); `/ready`, `/health` (and `/live` per the section) on ups (`app.ts:38`); `GET /` returns 200 `ok` on royalmail, ups, coll8, fedex, ocs, exelot (see sections). `veho` returns 404 on `/` and `/health`; exelot returns 400 (not 404) on `/healthz`.
- Unknown route: royalmail, fedex, bjs, inpost, ocs, exelot return **400** `VALIDATION ERROR` "Requested path not found"; veho and amazon-sfp return **404** problem+json; coll8 returns 500; **Amazon Logistics returns 200 "OK" for any unrouted path under `/shipping`** (after the key check), so a typo'd path looks like success.

## 1.4 Mirroring Selector's call

The proxies copy GFS's production carrier proxies; the request body is the common "CSS" carrier-proxy body (`labelSpecification`, `shipFrom`, `shipTo`, `packages[]`, `serviceCode`/`serviceType`, optional `customs`), and the happy-path scripts say whose call each copies: royalmail "CSS's createLabel, as CarrierRoyalMail.cs sends it", ups "CSS's ShipConfirm then ShipAccept" with a Windows-1252 header, fedex/bjs/inpost/amazon "as Selector sends it", exelot "as GFSI sends it" (`scripts/smoke.mts:55-304`). Veho is the exception: there is no production proxy; it follows the agreed contract (`README.md:21`). Route shapes differ though: nine proxies expose `POST /shipping/createLabel`; fedex uses `POST /shipping/createShipment`; coll8 `POST /labelling/CreateLabel`; ups `POST /api/stepping-stone/shipConfirm` then `/shipAccept` (XML) or `POST /api/v2/shipping/createLabel` (JSON). The smoke script's request builders (`apps/<carrier>-proxy/test/helpers.ts` or `harness.ts`, imported at `scripts/smoke.mts:11-24`) are the quickest source of a valid body per carrier.

## 1.5 Request-processing order (matters for D5 and for error handling)

Body parsing (`express.json()`) runs first on all of them, so malformed JSON is answered before any auth check. After that the order differs:

| order | carriers |
| --- | --- |
| route match, **auth, then** schema | royalmail (`app.ts:134-155`), fedex, bjs, inpost, ocs, exelot, amazon-sfp, veho, coll8 (auth on `/labelling` before the OpenAPI validator), ups |
| **schema, then auth** | dpdeu (`apps/dpd-europe-proxy/src/app.ts:87-88`; `scripts/smoke.mts:416`) and amazon (Logistics) `createLabel` (`scripts/smoke.mts:426`); amazon cancel and tracking check the key first |
| unknown route answered **before** auth | royalmail, fedex, bjs, inpost, ocs, exelot, amazon-sfp, veho |

Malformed JSON: 500 on royalmail, coll8, ups V2, bjs, inpost, ocs, exelot, veho, amazon-sfp; **400** on fedex (`VALIDATION ERROR`), dpdeu (`SYNTAX_ERROR`), amazon (Logistics, `Request failed schema validation`). (The E2 draft says "several mocks"; the split above is from the sections.)

## 1.6 Error-body families

1. **openapi-backend family** (royalmail, fedex, bjs, inpost, ocs, exelot): `{code, message, details, metaData?}`. `code` is a string with spaces: `VALIDATION ERROR` (400), `FORBIDDEN` (403), `CARRIER SERVER ERROR`, `INTERNAL SERVER ERROR`. Validation `metaData` is Ajv's error array spread into an object keyed `"0"` (bjs/ocs sections cite `exceptions.ts:43-49` and `:47-48`). Carrier failure status: royalmail and fedex pass the carrier's status through (create), bjs and inpost always 500, ocs and exelot always **599**. `details` carries the carrier's own body and may be an object, a string, HTML, or empty. The typo `additonal` is live in bjs/exelot/ocs.
2. **CSS-style, per carrier**: coll8 `{errorId, errorCode: COLL8_ERROR_*|SYSTEM_ERROR, messages}` (JSON text sent as `text/html` on create/cancel, real JSON on eodManifest, bare text on PNG failures); dpdeu `{code: VALIDATION|VALIDATION_ERROR|SYNTAX_ERROR|SCHEMA_ERROR|…, message, details}`; ups `{errorId, errorCode, messages, metadata}`; amazon and amazon-sfp handler errors `{code:<number>, message, detail}`.
3. **RFC 7807 problem+json**: veho, and amazon-sfp's framework errors (`type, title, status, detail, errors?`).

An adapter must key on `code`/`errorCode`/`type` and the body text, not only the HTTP status, and must not trust `Content-Type` (coll8 and ups mislabel bodies).

## 1.7 Success shape and labels

- The common success body (royalmail, fedex, bjs, ocs, exelot, amazon-sfp, veho): `{shipmentId, secondaryShipmentId?, warnings[], packages:[{documents:{label:{labelStream}, trackingId}}]}`. The label is **raw base64, never a data URI**, in `documents.label.labelStream`. Variants: amazon and amazon-sfp put `trackingId` at package level (`packages[].trackingId`) and omit `warnings` when empty; bjs, royalmail, fedex, ocs, exelot nest `trackingId` under `documents`; coll8 and dpdeu return `packages[].documents` as a bare base64 **string** (coll8 adds `trackingId` and `consignmentNo`); **inpost returns PascalCase** `{ShipmentId, TrackingNumber, Packages:[{documents:{trackingId,label:{labelStream}}}]}` (`inpost` section; `scripts/smoke.mts:261-268`); ups XML returns `<GraphicImage>` per package in ShipAccept (XML), ups V2 returns `{shipmentId, packages[]}`; veho adds `packageId`, `trackingUrl`, `consignmentNumber`.
- The spec files in `apps/<proxy>/api/` often say PascalCase `ShipmentId`/`Warnings` while the code sends camelCase (royalmail, ocs, exelot sections). Follow the code.
- Success status is 201 on royalmail, fedex, sfp, amazon, bjs, inpost, ocs, exelot; **200** on coll8, dpdeu, veho and ups.
- Encodings: ZPL/EPL come back **base64-encoded** text (inpost, coll8, royalmail, amazon, fedex); PNG on several carriers is produced by an internal PDF-to-PNG converter that retries and can fail independently (coll8, dpdeu, inpost, ocs, exelot).
- Mock labels are placeholders: PDFs say `MOCK LABEL - NOT FOR CARRIAGE` (`packages/mock-kit/src/label.ts:52`); 4x6 inch (288x432 pt) default (`label.ts:35-36`).

## 1.8 Statefulness and idempotency

Carrier mocks keep no shipment state except: royalmail manifest totals (per instance), veho orders (up to 1,000 per mock-upstreams instance; create is idempotent per `shippingReference`), exelot's invoice counter, token caches. Cancelling twice succeeds on most (not on veho). No proxy has a retry-safe create: exelot and royalmail can create a real mock parcel and then 500; exelot and veho document duplicate-on-retry hazards (sections). All state resets on restart or on another instance (dev runs scale-to-zero).

## 1.9 Failure scenarios (D5)

All twelve trigger failures through **magic values in request data**, never hidden switches (`AGENTS.md:26-27`). The pattern: `shipTo.postalCode` (UPS: ShipTo postcode; veho: first 5 ZIP digits) for create-time failures; a **prefix on the shipment/tracking id** for cancel/track/manifest (`UNKNOWN`, `CANCELLED`, `ERR500`, `MOCKERR…`); **fixture key names** for account-level failures (`<carrier>-key-bad-…`, `-inactive`, `-unconfigured`, `-malformed-profile`); and `apiky-500` for ApiKy outage. Normalisation is **not uniform** (the E2 draft claims it is): ups, coll8, fedex, dpdeu, bjs, inpost, ocs, exelot, amazon and amazon-sfp (shared mock Amazon) strip all whitespace and upper-case postcodes before comparing; veho keys on the first 5 ZIP digits; **royalmail magic values are exact, case- and space-sensitive**; sfp's `BT` postcode refusal is a case-sensitive prefix check. Several magic values only fire after the mock's own validation passes (a request the mock finds invalid yields that validation error instead), and PNG-specific ones fire only for a PNG request. Each carrier section has a verified table.

---

# 2. Cross-carrier matrices

Operations the proxy actually offers (Y = yes, N = no route; "unsupported" means a generic interface must not call it):

| carrier | create | validate | cancel | commit / manifest | reprint | track | notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| royalmail | Y `POST /shipping/createLabel` | N | Y via `POST /shipping/updateShipmentStatus {status:"Cancel"}` | Y `POST /shipping/manifestShipments` | N | N | also `GET /shipping/getServiceCodes` |
| ups | Y XML 2-step (`/api/stepping-stone/shipConfirm` then `shipAccept`) or V2 JSON one-shot | V2 `?validate=true` (still creates in the mock) | Y XML `void`, V2 `DELETE` | N | Y XML `labelRecovery` (broken for CSS's `text/xml`), V2 `GET` | N | locator / access points |
| coll8 | Y `POST /labelling/CreateLabel` | N | Y `POST /labelling/CancelShipment?trackingId=` | Y `POST /labelling/eodManifest` | N | N | |
| fedex | Y `POST /shipping/createShipment` | N | Y `POST /shipping/cancelShipment` (needs `accountNumber`) | N | N | N | |
| dpdeu | Y `POST /shipping/createLabel` | N | N | N | N | N | create only |
| amazon-sfp | Y | Y `?mode=validate` (rates only) | Y `POST /shipping/{shipmentId}/cancel` (always 200 `{}`) | N | N | Y `GET /shipping/tracking/{channelType}/{company}/{trackingId}` | |
| amazon | Y | Y `?mode=validate` (weaker than create) | Y same route | N | N | Y same route | |
| bjs | Y | N | Y `POST /shipping/cancelShipment` | N | N | N | |
| inpost | Y `createLabel`, `createReturnLabel` | N | N | N | N | N | create only (two routes) |
| ocs | Y | N | N | N | N | N | create only |
| exelot | Y | N | N | N | N | N | create only; retry duplicates |
| veho | Y | N | Y `POST /shipping/{shipmentId}/cancel` (whole order) | Y `POST /shipping/manifest` (by packageIds) | Y `GET /shipping/packages/{packageId}/label?labelFormat=` | N | also quote and update delivery instructions |

Consequence: of Selector2's five label operations (`ProcessShipment(s)`, `ValidateShipments`, `DeleteShipments`, `CommitShipGroup`, `CommitShipments`, per `Migration State` B9, vault), **only create exists everywhere**. Delete exists on 8 of 12; commit/manifest on 3 of 12; validate on 3 of 12 (sfp, amazon, and ups V2).

Label formats and weight rule per carrier (requested vs what you actually get):

| carrier | label formats the proxy accepts | gets back | weight rule (send this) |
| --- | --- | --- | --- |
| royalmail | PDF, PNG, ZPL203DPI, ZPL300DPI | one base64 blob; customs docs (CN23, commercial invoice) always PDF, separate; no CN22 | unit is **never read**; send KILOGRAM; a GRAM value is treated as kg (`royalmail` section) |
| ups | XML: GIF/PNG/PDF image or ZPL/EPL/SPL/STARPL thermal; V2: ZPL/PDF/PNG/GIF | per-package base64 | forwarded verbatim (KGS/LBS/OZS), no conversion |
| coll8 | PDF, PNG, ZPL | per-package base64 (ZPL as base64 of text) | no conversion; send kg |
| fedex | PDF, PNG, ZPL (paired `labelStockType`) | per-package base64 + optional commercial invoice PDF | GRAM/KILOGRAM/POUND converted correctly |
| dpdeu | PDF, PNG, ZPL | one base64 string per parcel | send **GRAM** integers; KILOGRAM x100 unrounded gives non-integers DPD rejects |
| amazon-sfp | ZPL, PDF, PNG (203 or 300 DPI for ZPL/PNG) | 6x4 in | unconverted; zero weight takes the consignment value forced to KILOGRAM |
| amazon | **ZPL and PNG only** (PDF is a 500 at create) | 6x4 in | same as sfp |
| bjs | spec PDF or PNG; **`labelFormat` is ignored, always PDF** | one label per BJS product (2 per package for `1EXC`/`2EXC`) | GRAM/KILOGRAM converted correctly |
| inpost | PDF, PNG, ZPL, EPL (all base64) | one label | GRAM sent as `G`, KILOGRAM as `KG` |
| ocs | PDF, PNG | one blob; PNG keeps the last page only | **any unit but exactly `KILOGRAM` is multiplied by 1000** |
| exelot | PDF, PNG; must equal the partner's provisioned format; never ZPL | one label | **any unit but exactly `KILOGRAM` is multiplied by 1000** |
| veho | PDF, PNG, ZPL203DPI (ZPL300DPI refused) | one per parcel | converted to lb correctly; <= 50 lb, sides <= 48 in |

Error surface summary (what a carrier-side rejection looks like to the caller):

| carrier | carrier rejection status | where the carrier's reason lives |
| --- | --- | --- |
| royalmail | carrier's status (400/401/500), `code:"CARRIER SERVER ERROR"` | `details` |
| ups XML | HTTP 200 with `ResponseStatusCode` 0 and `Error[]` in the XML | XML body |
| ups V2 | 400 numeric `errorCode`, `messages:[{code,message}]` | `messages` |
| coll8 | 500 `COLL8_ERROR_*` | `messages` |
| fedex | create: FedEx's status; cancel: always 500 `Unknown error : CarrierError: …` | `details` text |
| dpdeu | 400 with DPD fault code (DE `SHIPMENT_1`, NL 500) | `details` |
| amazon-sfp, amazon | 500 `{code:500,message,detail}` | `detail` free text (Amazon's status only inside the text) |
| bjs, inpost | 500 `CARRIER SERVER ERROR` | `details` |
| ocs, exelot | **599** `CARRIER SERVER ERROR` | `details` |
| veho | any upstream 4xx becomes 400 `CarrierException` (no reason); 5xx/timeout becomes 599 | nothing from Veho is passed on |

---

# 3. Per-carrier sections

Each section below was extracted from source by a separate reader and is reproduced unedited, including its own "Notes for the E2 draft" and "README-vs-source discrepancies". Order: royalmail, ups, coll8, fedex, dpdeu, amazon-sfp, amazon, bjs, inpost, ocs, exelot, veho.


---

## royalmail (Royal Mail; apps/royal-mail-proxy; mirrors royalmail.gfsdeliver.com)

All paths below are relative to `~/code/merak/carrier-playground` at `origin/main`. Upstream = "mock Sapient" in `apps/mock-upstreams/src/royalmail/index.ts` (cited `mock:`). Proxy sources cited as `apps/royal-mail-proxy/...`.

### Operations and routes

| Operation | METHOD path | Supported? | Notes |
| --- | --- | --- | --- |
| validate | none | NO | No validate/dry-run route and no `validate` flag. Spec-level validation happens on every createLabel (`apps/royal-mail-proxy/src/app.ts:148-155`); there is no way to validate without creating a shipment. |
| create-ship (label) | POST `/shipping/createLabel` | yes | 201. Creates the Sapient shipment (`POST /v4/shipments/rm`) and returns the label; for dutiable (non GB/IM) destinations also fetches/returns CN23 and commercial invoice. `apps/royal-mail-proxy/src/app.ts:187-189`, `src/integrations/royalmail-integration.ts:96-146`. One package only (spec `maxItems: 1`, `api/royalmail-integration-api.yaml:118-123`). |
| delete-cancel | POST `/shipping/updateShipmentStatus` with `status: "Cancel"` | yes (via status change) | There is NO dedicated cancel/DELETE route. Cancel is one value of the status enum `Hold|Cancel|Release|Picked` (`api/royalmail-integration-api.yaml:673-679`). 204, empty body. Accepts a batch of ids (batches of 99 in parallel, `src/integrations/royalmail-integration.ts:20,70-93`). |
| commit-manifest | POST `/shipping/manifestShipments` | yes | 201 array of manifests (base64 PDF `manifestImage`). Marks `shipmentIds` Picked first (failure ignored, `royalmail-integration.ts:158-172`), then `POST /v4/manifests/rm` with `Status:'Picked', Async:false` (`src/services/royalmail-service.ts:290-297`). |
| reprint | none | NO | No reprint/label-recovery route. (Sapient `printDocument` is only called internally for customs docs, `royalmail-integration.ts:57-67`.) |
| track | none | NO | Tracking number and `CarrierTrackingUrl` come back from Sapient but the proxy returns only `trackingId`; the URL is dropped (`royalmail-service.ts:273-286`). |
| other: service codes | GET `/shipping/getServiceCodes` | yes | 200 `string[]` of enabled GFS service codes for the key's account, from local fixtures not Sapient (`royalmail-integration.ts:198-212`). Does a Sapient token fetch first purely as an auth check. |
| other: health | GET `/health/liveness` (200 `{"ok":true}`), GET `/` (200 text `ok`) | yes, no auth | `app.ts:127-132`. |

Route matching is case-sensitive, trailing slash ignored, method-sensitive; anything else is a 400 `VALIDATION ERROR` "Requested path not found" with `metaData:{request:{method(lowercase),path}}` (`app.ts:46-63`; test `apps/royal-mail-proxy/test/auth.test.ts:104-120`). Note: unknown route returns 400, not 404, and the route check runs BEFORE auth (`app.ts:134-146`), so an unknown path with no key is still 400, not 403.

Middleware order (`app.ts:122-208`): correlation -> `express.json()` -> health routes -> route match -> x-api-key auth -> OpenAPI request validation -> body restore + stateOrRegion check -> handler -> global error handler. `express.json()` is first, so malformed JSON is a 500 even before the route/auth check.

### Auth and headers

- Header: `x-api-key` only (`app.ts:139`). Looked up as `GET {APIKY_BASE_URL}/api/profile?token=<key>` with the proxy's own service key (`packages/apiky-client/src/index.ts:31-43`). Profile must carry `profile.royalmailCustomerId` = the Sapient shipping account id (`royalmail-integration.ts:41-44`); the rest of the profile is unused.
- Fixture key NAMES (`apps/mock-upstreams/fixtures/apiky/royal-mail.json`, README table lines 52-62):
  - `rm-key-acme` (account ending a001): everything works; own Sapient creds; products TPN24, TPS48, CRL48, MTA, OLA; locations `101`, `102` (`apps/mock-upstreams/fixtures/royalmail/accounts.json`, `apps/royal-mail-proxy/fixtures/customers.json`).
  - `rm-key-bramble` (b001): service-wide Sapient creds; TPN24, CRL48; location `201`.
  - `rm-key-inactive` (c001): `isActive:false`; Sapient account exists (location `301`).
  - `rm-key-revoked-creds` (d001): Sapient rejects the stored creds.
  - `rm-key-auth-outage` (e001): Sapient token endpoint returns 500.
  - `rm-key-unconfigured` (f001): no customer document.
  - `rm-key-malformed-profile`: profile has no `profile` block.
  - `apiky-500`: mock ApiKy returns 500 (apiky mock `apps/mock-upstreams/src/apiky/index.ts:37-40`). Any other string: mock ApiKy 403.
- Missing key, unknown key, ApiKy 500, ApiKy unreachable: ALL give the same 403 (`app.ts:139-141`; `src/integrations/apiky-integration.ts:9-20`; `test/auth.test.ts:18-32`). Body: `{"code":"FORBIDDEN","message":"Authentication failed","details":"Principal undefined could not be authenticated. No additional detail was provided."}` (note literal `undefined`: `new AuthenticationError()` is built with no principal, `app.ts:141`, `src/exceptions.ts:29-35`).
- Sapient auth failure (revoked creds, token endpoint 500, or any exception in the token fetch) -> 403 with the account id filled in: `Principal 00000000-0000-4000-8000-00000000d001 could not be authenticated...` (`src/integrations/get-royalmail-access-token.ts:29-31`; `test/auth.test.ts:84-95`). Applies to ALL four operations including getServiceCodes (token fetched first). Token cache: per account, 5 minutes, max 100 entries (`src/stores/access-token-cache.ts:6-7`); failures are not cached.
- Other required headers: `Content-Type: application/json` for bodies (see Request). No `Accept` requirement. Inbound `Authorization: Bearer` (Cloud Run IAM) is never read by the proxy (only `x-api-key` is read; `Authorization` appears only on outbound Sapient calls, `src/integrations/http.ts:46`), so it is ignored. Whether the deployed Cloud Run service itself is public: UNVERIFIED (not in this app's code).

### Request

`POST /shipping/createLabel` (spec `CreateLabelRequest`, `api/royalmail-integration-api.yaml:98-147`; code `src/services/royalmail-service.ts:155-246`). Validated with express-openapi-validator against the spec; extra properties are allowed (the spec's own example carries `orderID` and `shippingAccountId`, which the code never reads).

Spec-required: NOTHING at the top level (no `required` on `CreateLabelRequest`). So a request with no `shipTo` or no `labelSpecification` passes validation and then crashes into a 500 (`royalmail-integration.ts:115` reads `labelSpecification.labelFormat` unguarded AFTER Sapient has created the shipment; `royalmail-service.ts:126` reads `shipTo` unguarded). Nested requireds (only if the parent object is sent):
- `labelSpecification.labelFormat` required; enum `PDF | PNG | ZPL203DPI | ZPL300DPI` (`yaml:469-480`). The mock Sapient also accepts `DATASTREAM`, `PDF4X3`, `PNG4X3` (`mock:61`) but the proxy validator rejects them first (400).
- `shipFrom`/`shipTo` (Address): required `addressLine1, city, name, postalCode, stateOrRegion` (`yaml:225-230`). `stateOrRegion` must be present as a key but may be `""` (the validator would default it; the proxy re-checks the original body and rejects a missing one, `app.ts:80-95,176-184`). Limits: name 1-60, companyName <=35, lines 1-60, city 1-50, countryCode exactly 2, postalCode 1-20, phoneNumber 1-20, email <=64, vat/eori <=30.
- `packages`: array, minItems 1, maxItems 1. Package fields all optional, but `value` needs `currency` (len 3) + `value` (0-99999); `weight` needs `unit` (enum `GRAM | KILOGRAM`) + `value`; `dimensions.unit` enum `INCH | CENTIMETER` (`yaml:322-373`).
- `customs`: if sent, `commodities` required (min 1); each commodity requires `quantity` (int >=1), `description` (<=80), `hsCode` (<=8), `value{currency,value}`; `reasonForExport` enum `Gift | Commercial Sample | Documents | Sale of Goods | Return of Goods | Mixed Content | Other`; `sku` <=30, `manufacturerProductId`/`standardisedProductId` <=50 (`yaml:374-468`).
- `contentType` enum `NDX | DOX | HV`; `descriptionOfGoods` 1-70; `businessTransactionType` enum `B2C|B2B|D2C|C2B` (validated but never read by the code); `safePlaceLocation` <=30.

What the code actually reads (everything else is ignored): `serviceCode`, `contentType`, `labelSpecification.labelFormat`, `descriptionOfGoods`, `shippingLocationId`, `shipFrom.*` (optional in practice: absent shipFrom just yields an empty Shipper.Address), `shipTo.*`, `packages[0].{value.currency, packageClientReferenceId}`, all packages for `weight.value`, `value.value`, `dimensions`, `customs.*`, `safePlaceLocation`. NOT read: `weight.unit`, commodity `weight.unit`, commodity `value.currency`, `businessTransactionType`, `packages[].description`, `whatThreeWords`.

Effective extra requirements imposed by (mock) Sapient on top of the spec, returned as carrier 400 `CARRIER SERVER ERROR` with Sapient's `Errors[]` (`mock:151-272`): `serviceCode` (mapped), `contentType` present and in NDX/DOX/HV (E1001/E1002), `descriptionOfGoods` non-empty, `labelFormat` known, Shipper.ShippingAccountId = the key's account (E1004), shipping location in the account (E1004; defaults to the account's default location when `shippingLocationId` omitted, `mock:191`), Destination `name` <=50 (stricter than the GFS 60), `addressLine1`, `city`, `countryCode`, `postalCode` if GB, >=1 package with numeric `DeclaredWeight > 0` (`mock:254-262`), and `Items` for any non-GB/IM destination unless `contentType === 'DOX'` (`mock:264-272`). (Mock may be stricter or looser than real Sapient: UNVERIFIED.)

Units and mappings:
- Service code: GFS code (`RMT24`, `RMT24LL`, `RMT48S`, `RMT48SOLD`, `RM48`, `RMINTT`, `RMINTS`, `RMSD1`) -> Royal Mail product via local `fixtures/services.json` (TPN24, TPN24, TPS48, TPS48, CRL48, MTA, OLA, SD1), only if the customer is active and the product is on its list (`src/stores/royalmail-store.ts:71-93`). Match is exact-case. `getServiceCodes` returns the GFS side.
- Weight: proxy sends `DeclaredWeight = packages[i].weight.value` as-is and NEVER reads `weight.unit` (`royalmail-service.ts:223`, items `:238`). A `GRAM` value is therefore sent as if kilograms. Mock Sapient interprets DeclaredWeight as KG (`weightGrams = DeclaredWeight*1000`, `mock:293`; manifest `TotalWeight` is KG, `mock:461,481`). So 500 GRAM shows as 500 KG on the manifest.
- Dimensions: `unit === 'INCH'` -> value/2.54 (backwards; should multiply); anything else (incl. `CENTIMETER`, or no unit) passes through (`royalmail-service.ts:193-195,226-228`). Test `test/royalmail-service.test.ts:176`.
- Currency: only `packages[0].value.currency` is read (`ShipmentInformation.CurrencyCode`, `:204`); `QuotedLandedCost` = sum of package `value.value` (`:217`).
- Dates: not accepted. `ShipmentDate` and `InvoiceDate` are server "today" UTC `YYYY-MM-DD` (`:119,202,215`).
- Country codes: ISO alpha-2. Dutiable iff destination not `GB`/`IM` (`mock:65,264`).
- Package type: from the service's `packageType` (`PARCEL`->Parcel, `LARGE LETTER`->LargeLetter, `LETTER`, `PRINTED PAPER`) not from the request (`royalmail-service.ts:107-117,220`).
- Enhancements: built from the service flags plus request data: `Signed` if service.signed; `SMS` only if service.sms AND shipTo.phoneNumber non-empty; `Email` only if service.email AND shipTo.email non-empty; `Safeplace` only if service.safePlace AND `safePlaceLocation`; `LocalCollect`, `CustomsEmail`, `CustomsPhone` from flags (`royalmail-service.ts:124-152`). `CarrierSpecifics.serviceLevel` is sent lower-case (only RM48 has one, `"02"`).
- Label format/encoding: request `labelSpecification.labelFormat` is forwarded verbatim as Sapient `LabelFormat`.

`POST /shipping/manifestShipments` (`yaml:556-569`): `{siteId?: string, shipmentIds?: string[]}`, both optional; non-string siteId -> 400 validation. `siteId` becomes `ShippingLocationId`; omitted means all of the account's locations (mock `mock:446`). No `serviceCode` in the response (spec lists it; code omits it, `royalmail-service.ts:300-322`).

`POST /shipping/updateShipmentStatus` (`yaml:670-694`): `{status: Hold|Cancel|Release|Picked, reason?: string, shipmentIds: string[] (minItems 1 if present)}`. No required fields at all: `{"status":"Hold"}` with no ids is a 204 no-op without calling Sapient (`royalmail-integration.ts:76-79`; `test/manifest-status.test.ts:193-196`); a missing/invalid status with ids passes spec validation only if absent, then Sapient (mock) 400s E1002.

`GET /shipping/getServiceCodes`: no body; query params ignored.

Validation errors (spec failures): 400 `{"code":"VALIDATION ERROR","message":"Client request failed validation","details":"Failed to validate client request","metaData":[{"instancePath":"/requestBody/...","keyword":"required|enum|maxItems|minItems|type|...","params":{"missingProperty":"..."} (only for required),"message":"..."}]}` (`app.ts:65-78,156-175`; `test/create-label.test.ts:299-317`). Only the first/some errors may be reported.

### Response

createLabel success: HTTP 201, JSON, camelCase (NOT the spec's PascalCase `ShipmentId/TrackingNumber/Warnings`; `royalmail-service.ts:273-286`):
```
{ shipmentId, secondaryShipmentId (== shipmentId), warnings: string[],
  packages: [ { documents: { label: { labelStream }, trackingId } } ],   // always exactly one entry
  documents?: { cn23?: { documentStream }, commercialInvoice?: { documentStream } } }  // dutiable only
```
- `shipmentId` is the Sapient ShipmentId (needed for status change / manifest). In the mock it is a UUID-shaped string that encodes account, location, destination, tracking serial, weight (`apps/mock-upstreams/src/royalmail/ids.ts:56-88`). Treat as opaque.
- `trackingId`: `Packages[0].TrackingNumber`, mock format `TT` + 8 digits + check digit + `GB` (S10; `mock/documents.ts:14-21`; test regex `^TT\d{9}GB$`). Only the FIRST package is returned.
- `label.labelStream`: base64 of the raw label bytes (not a data URI). PDF -> `%PDF-`; PNG -> 400x600 grey PNG; `ZPL203DPI`/`ZPL300DPI` -> base64 of ZPL text starting `^XA` (`mock/documents.ts:7-11,64-90`; `test/create-label.test.ts:38-51`). One blob, no per-format wrapper.
- Customs: only when Sapient returns inline `Documents` (mock: iff destination not GB/IM, `mock:314-317`). Both documents are ALWAYS PDF (spec, `yaml:526,535`; test `create-label.test.ts:130-133`):
  - `cn23`: if requested `labelFormat === 'PDF'` it is the inline `Documents` string; otherwise fetched with `POST /v4/shipments/printDocument/rm/{id}` `{DocumentType:'CN23',NumberOfCopies:1}` (`royalmail-integration.ts:121-133`). Literal comparison to `'PDF'`.
  - `commercialInvoice`: always fetched (`DocumentType:'CI'`), A4 PDF (`royalmail-integration.ts:134-141`; `mock:350-357`).
  - There is NO CN22 anywhere (grep clean). Only CN23 and CI.
  - If a fetch fails: error is logged, the label is still returned (201), and a warning is appended: `"CN23 customs declaration could not be retrieved for this shipment."` / `"Commercial invoice could not be retrieved for this shipment."` (`royalmail-service.ts:248-249,262-269`). If both fail the `documents` key is omitted entirely (`:268`). Domestic: no `documents` key, `warnings: []`.
- `warnings` is the only warnings channel; Sapient's own warnings are not forwarded.

manifestShipments success: 201 array `[{manifestImage (base64 PDF), manifestNumber (8 digits), carrierCode:'RM', totalWeight (KG number), weightUnitOfMeasure:'KG', totalShipments, totalItems, manifestDate 'YYYY-MM-DD', createdDateUtc ISO, shippingLocation{shippingLocationId,locationAlias,locationCountry,locationPostcode}, shippingAccount{shippingAccountId,accountName,accountAlias,accountNumber}}]` (`royalmail-service.ts:300-322`; `test/manifest-status.test.ts:46-71`). One manifest per location that had Picked shipments; `[manifest with 0 shipments]` if none (`mock:454`). Spec enum for `weightUnitOfMeasure` is `KG | Grams` but only `KG` is ever produced (UNVERIFIED for real Sapient).

updateShipmentStatus success: 204, empty body.

getServiceCodes success: 200 `string[]` in services-collection order, not the customer-list order (`royalmail-store.ts:95-112`), e.g. acme: `["RMT24","RMT24LL","RMT48S","RM48","RMINTT","RMINTS"]` (`test/service-codes.test.ts:15-21`). Disabled codes (`RMT48SOLD`) are excluded; `RMSD1` is on no customer's list.

### Error shape

Common shape (all four ops): `{ "code": string, "message": string, "details": any }`, plus `metaData` only for VALIDATION ERROR (`src/exceptions.ts:20-22,50-52`).

| Status | code | message | details | When |
| --- | --- | --- | --- | --- |
| 400 | `VALIDATION ERROR` | `Client request failed validation` | `"Requested path not found"` / `"Failed to validate client request"` / `"No mapping found for service code X for customer <accountId>"` | unknown route; spec failure; no service-code mapping (inactive customer, unknown code, product not on list, unconfigured customer) (`metaData:{}` for the mapping case) |
| 403 | `FORBIDDEN` | `Authentication failed` | `Principal <accountId or undefined> could not be authenticated. No additional detail was provided.` | see Auth |
| Sapient's status (400, 401, 500 ...) | `CARRIER SERVER ERROR` | `Server error received from RoyalMail` | Sapient's JSON body (`{"Message":"Invalid Request","Errors":[{"Message","Cause","ErrorCode":"E1001..E1004"}]}`), or the string `"Request failed with status code N"` when Sapient has no body, or the Node network error text (status 500) | Sapient non-2xx (`royalmail-integration.ts:46-52`); also 500 for getServiceCodes when the customer has no enabled codes: `No mapped GFS service Codes found for accountid <id>` (`:205-209`) |
| 500 | `INTERNAL SERVER ERROR` | `An unexpected error occurred` | `An unexpected error occurred on the server, no additional detail is available` | any non-ProxyError: malformed JSON, profile without `profile.royalmailCustomerId`, disabled service code (TypeError, `royalmail-service.ts:161`), missing `shipTo`/`labelSpecification` (`global-error.ts:30-34`) |

- Carrier-failure status is passed through verbatim (400/401/500...), NOT normalised. A Sapient 401 (mock postcode `ERR 401`) reaches Selector as HTTP 401, which looks like an auth failure but is a `CARRIER SERVER ERROR` with `details:"Request failed with status code 401"`.
- Malformed JSON: generic 500 (`test/create-label.test.ts:338-344`), BEFORE route matching/auth. Non-JSON content type is NOT 415: body treated as `{}` (`app.ts:163-167`; `test/manifest-status.test.ts:184-191` proves 204 for a text/plain updateShipmentStatus). For createLabel a `{}` body ends as 400 "No mapping found for service code undefined ..." (derived from `royalmail-service.ts:160`, `store:71-78`; not directly tested).
- Request body limit: express default 100 kb; an oversize body is a generic 500 (derived; UNVERIFIED by test).
- The 500 `InternalError` class and its typo default text (`additonal`, `exceptions.ts:76`) is dead code here: no code path constructs it, so that typo never reaches a caller (grep). Same for `An validation error occurred` default (`:45`): every ValidationError passes an explicit detail.

### Failure scenarios for D5 (magic values)

All Sapient-level magic values are EXACT, case-sensitive, whitespace-sensitive string matches (`mock:136,144,368,419,70`; no normalisation anywhere in `apps/royal-mail-proxy/src` or `apps/mock-upstreams/src/royalmail`; the proxy passes `postalCode` through untouched, `royalmail-service.ts:173`). `ERR 500` fires; `err 500`, `ERR500`, `ERR  500` do not (they fall through to normal handling).

| Operation | field | magic value | where verified | what the caller sees |
| --- | --- | --- | --- | --- |
| createLabel | `shipTo.postalCode` | `ERR 400` | `mock:144-149` | 400 `CARRIER SERVER ERROR`, details `{Message:"Invalid Request",Errors:[{Message:"The postcode is invalid.",Cause:"Destination.Address.Postcode",ErrorCode:"E1002"}]}` (`test/create-label.test.ts:236-255`) |
| createLabel | `shipTo.postalCode` | `ERR 401` | `mock:140-143` | 401 `CARRIER SERVER ERROR`, details string `"Request failed with status code 401"` (no body) (`create-label.test.ts:262-268`) |
| createLabel | `shipTo.postalCode` | `ERR 500` | `mock:136-139` | 500 `CARRIER SERVER ERROR`, details `{Message:"An error has occurred.",Errors:[{Message:"System error",Cause:null,ErrorCode:"E1000"}]}` |
| createLabel | `shipTo.postalCode` (dutiable, i.e. `countryCode` not GB/IM) | `NODOC CN23` | `mock:70,289,346-349` | 201; CN23 fetch fails. Only matters when `labelFormat != 'PDF'` (inline CN23 is used for PDF, no fetch). Non-PDF: `documents` has only `commercialInvoice`, `warnings:["CN23 customs declaration could not be retrieved ..."]`. With PDF: nothing happens (no warning). |
| createLabel | same | `NODOC CI` | same | 201; `documents` has only `cn23`, warning for the commercial invoice (works for any label format) |
| createLabel | same | `NODOC ALL` | same | 201; PDF label: `cn23` (inline) present, CI missing + CI warning only. Non-PDF label: no `documents` key at all, two warnings. |
| createLabel | `shipTo.name` | length > 50 | `mock:206-213` | 400 `CARRIER SERVER ERROR`, `Cause:"Destination.Address.ContactName"` E1002 (spec allows 60) |
| createLabel | `shipTo.countryCode` non GB/IM, no `customs` (contentType != DOX) | n/a | `mock:264-272` | 400 carrier error, `Cause:"Items"` E1001 |
| createLabel | `shippingLocationId` | not a location of the account (e.g. `999`) | `mock:198-204` | 400 carrier error `Cause:"Shipper.ShippingLocationId"` E1004 |
| createLabel | `serviceCode` | `RMT48SOLD` (disabled), with `rm-key-acme` | `apps/royal-mail-proxy/fixtures/services.json:40-46`; `royalmail-store.ts:89-92` | 500 generic `INTERNAL SERVER ERROR` (NOT a carrier error; not a 400) (`create-label.test.ts:218-224`). With `rm-key-bramble` the code is 400 "No mapping" instead (TPS48 not on its list). |
| createLabel | `serviceCode` | unknown, or product not on the key's list (e.g. `RMSD1`), or lower-case `rmt24` | `store:71-93` | 400 `VALIDATION ERROR`, `No mapping found for service code X for customer <id>`, `metaData:{}` |
| createLabel / all ops | `x-api-key` | `rm-key-inactive` | fixtures `customers.json:16-21` | createLabel 400 no-mapping; `getServiceCodes` 500 `CARRIER SERVER ERROR` `No mapped GFS service Codes found for accountid ...c001`. manifestShipments and updateShipmentStatus still WORK for this key (they skip the mapping; the Sapient account c001 exists, `accounts.json:49-63`, and uses default creds). |
| createLabel / all ops | `x-api-key` | `rm-key-unconfigured` | `royalmail-store.ts:71-93,95-99` | createLabel 400 no-mapping; getServiceCodes 500; manifest/status: token with default creds works but the account `...f001` does not exist in the mock Sapient -> manifest 400 `E1004` carrier error; status 204 (status accepts anything) |
| all ops | `x-api-key` | `rm-key-revoked-creds` | `mock:98-106`; `test/auth.test.ts:84-95` | 403 `FORBIDDEN` naming account d001; no Sapient API call made |
| all ops | `x-api-key` | `rm-key-auth-outage` | `mock:98-101` (client id `mock-client-auth-500`) | 403 `FORBIDDEN` naming account e001 |
| all ops | `x-api-key` | `rm-key-malformed-profile` | `royalmail-integration.ts:43`; `test/auth.test.ts:48-54` | 500 generic `INTERNAL SERVER ERROR` |
| all ops | `x-api-key` | `apiky-500` / unknown / absent | `apiky-integration.ts:9-20` | 403 `FORBIDDEN` `Principal undefined ...` |
| updateShipmentStatus | `shipmentIds[]` | contains exactly `SHIPMENT-500` (case-sensitive; checked before status validation) | `mock:368-371` | 500 `CARRIER SERVER ERROR` (Sapient body) (`manifest-status.test.ts:164-167`). Batched 99 at a time in parallel, so any one batch containing it fails the call. |
| updateShipmentStatus | `status` | omitted while ids present | `mock:372-375` | passes spec validation, Sapient 400 E1002 `The status is invalid.` -> 400 `CARRIER SERVER ERROR` |
| manifestShipments | `siteId` | `MANIFEST-500` | `mock:418-422` | 500 `CARRIER SERVER ERROR` (the Picked step before it is attempted first and ignored) |
| manifestShipments | `siteId` | not a location of the account | `mock:430-439` | 400 `CARRIER SERVER ERROR` `Cause:"ShippingLocationId"` E1004 |
| manifestShipments | `shipmentIds` | contains `SHIPMENT-500` | `royalmail-integration.ts:158-172` | NOT a failure: Picked-step failure is swallowed, manifest still 201 (`manifest-status.test.ts:106-109`) |

### Quirks mirrored from production

- `GRAM` weight sent as if KG, and the unit is never read at all, for packages and commodities (`apps/royal-mail-proxy/src/services/royalmail-service.ts:223,238`). Not covered by any proxy test. Sapient's own `WeightUnitOfMeasure` on manifests is `KG`.
- `INCH` dimensions divided by 2.54 instead of multiplied (`:193-195`).
- Response is camelCase, spec is PascalCase; `secondaryShipmentId` repeats `shipmentId`; tracking URL dropped; only `Packages[0]` returned (`:273-286`).
- `CarrierSpecifics.serviceLevel` lower-case key (`:131`).
- A disabled service code, missing `shipTo` or missing `labelSpecification` is a generic 500 (unguarded reads); with a missing `labelSpecification` Sapient has ALREADY created the shipment when the 500 fires (`royalmail-integration.ts:105-115`) -> orphan shipment, retry creates a second one.
- Manifest ignores the result of the Picked step (`royalmail-integration.ts:158-172`); manifest response omits `serviceCode`.
- `getServiceCodes` fetches a Sapient token it does not use and reports "no codes" as a 500 `CARRIER SERVER ERROR` (`:198-212`).
- Malformed JSON is a 500, not 400. Unknown route is 400 `VALIDATION ERROR`, not 404, and is decided before auth.
- 403 for every auth failure incl. "no key"; its details say `Principal undefined` when no principal was resolved.
- `shipTo.stateOrRegion` must be a present key (may be empty) or the call is a 400 (`app.ts:80-95`).
- Sapient errors keep PascalCase `Message/Cause/ErrorCode` inside `details`; codes `E1000` system, `E1001` required, `E1002` invalid, `E1003` not-available, `E1004` not-found (`mock:52`).
- Spec weights are GRAM/KILOGRAM but the unit is ignored; spec dimension enum is INCH/CENTIMETER.

### Statefulness / ordering constraints

- Proxy is stateless except the per-instance Sapient token cache (5 min, per account) and the in-memory fixture stores. No idempotency key; calling createLabel twice creates two shipments.
- Order: createLabel -> (optional) updateShipmentStatus Hold/Release/Cancel/Picked -> manifestShipments. manifestShipments marks the passed `shipmentIds` Picked itself, so an explicit Picked call is not required.
- Status calls are NOT validated against existing shipments: ids that were never created, already cancelled, or cancelled twice all return 204 (mock keeps no shipment state: `mock:392-411`, README "Status changes are always accepted"). A Cancel does not make a later createLabel/manifest fail. UNVERIFIED how real Sapient behaves on double-cancel.
- The one stateful piece is in the mock upstream: each `mock-upstreams` instance remembers the shipments it saw marked Picked (`mock:42-44,88,392-411`). A manifest served by a DIFFERENT instance (Cloud Run may run several) returns a manifest with `totalShipments: 0` and no error (`apps/royal-mail-proxy/README.md:87-89`; `mock-upstreams royalmail.test.ts:105`). Manifesting removes the shipments from the picked set, so a second manifest call for the same ids returns an empty manifest. Status `Hold`/`Release`/`Cancel` removes an id from the picked set (`mock:395-397`). Expect flaky totals if a flow is split across calls; assert on `manifestNumber` shape rather than counts.
- `rm-key-inactive`/`rm-key-unconfigured`: createLabel and getServiceCodes fail but manifest/status can still succeed (see D5 table).
- Shipment ids are only meaningful for the account/key that created them (manifest filters by the key's account, `mock:443-447`).

### Adapter implications and leaks

- No validate and no dedicated cancel: a generic `validate()` must be unsupported for royalmail; a generic `cancel(id)` must call `updateShipmentStatus {status:"Cancel", shipmentIds:[id], reason}` and expect 204 with empty body. Cancel/Hold/Release/Picked are all the same route.
- Generic `commit-manifest` maps to `manifestShipments`; it returns a LIST of manifests (possibly empty-total), base64 PDF per manifest, not a single manifest id. It is also the only endpoint with a `siteId` (Royal Mail "shipping location") concept; `shippingLocationId` on createLabel is the same id. These location ids are per-key (`101/102` for acme, `201` bramble) and come from Royal Mail account setup, not Selector.
- Account identity is the ApiKy key, not a request field; the request must not carry credentials. The adapter must hold one key per Selector tenant.
- Label is a single base64 blob (`packages[0].documents.label.labelStream`); requested format (PDF/PNG/ZPL203DPI/ZPL300DPI) decides the bytes. Customs documents are a separate shipment-level `documents` object, always PDF, optional, with failures surfaced only as `warnings` strings (match on text) while status stays 201. An adapter must treat missing customs docs for a non-GB destination as a soft failure.
- Tracking id: `packages[0].documents.trackingId`; shipment handle for later calls: `shipmentId`. Both are needed (`trackingId` for the customer, `shipmentId` for cancel/manifest).
- One package per call (maxItems 1): multi-parcel Selector shipments must be split into multiple createLabel calls.
- Weight: send KILOGRAM (value in kg) always; a GRAM value would be treated as kg. Dimensions: send CENTIMETER (INCH is divided, not multiplied).
- 401/400/500 from the carrier are passed through with the carrier status. A generic error mapper must key on `code` (`CARRIER SERVER ERROR` vs `VALIDATION ERROR` vs `FORBIDDEN` vs `INTERNAL SERVER ERROR`), not HTTP status: 401 can be a carrier error, 403 is the only auth failure, 500 can be carrier, proxy bug, or unsafe retry after an orphan shipment.
- Service codes are GFS-specific codes (`RMT24`, ...), discoverable via `GET /shipping/getServiceCodes`; per-account.
- Required `stateOrRegion` key, `contentType`, `descriptionOfGoods`, packages[0].weight.value > 0, customs for non-GB/IM (these are Sapient-required but not spec-required: they surface as carrier 400s, not validation 400s).
- Case/space-sensitive magic values (unlike UPS).

### README-vs-source discrepancies, and UNVERIFIED

README-vs-source (royal-mail-proxy README, `apps/royal-mail-proxy/README.md`):
- README line 14: "(inline if the label is a PDF, otherwise fetched as a PDF)": correct but add: the comparison is the literal string `'PDF'`; any other format (including `PDF4X3`, which the proxy rejects anyway) triggers a fetch.
- README line 30 (403 row): "403 ... No key, an unknown key, ApiKy down": correct. The `details` text for the no-key/unknown-key/ApiKy-down case literally says `Principal undefined`, which the README elides as `<shippingAccountId>` (only the Sapient-credential 403 has the real id).
- README line 75: "`NODOC CN23` only matters for non-PDF labels": correct. But also: `NODOC ALL` with a PDF label does NOT remove the CN23 (inline), only the CI. README says "That customs document fetch fails" without that detail.
- README line 75 says the NODOC rows apply to non-GB. Source: `NODOC[postcode]` is encoded into the shipment id regardless of country (`mock:289`); it only has an effect when the destination is dutiable (non GB/IM). IM is also non-dutiable, README says "non-GB".
- README line 91 table row `shipmentIds SHIPMENT-500`: only the status-update path fails; in `manifestShipments` the same value is swallowed (README says so in "Manifesting ignores failures", but the D5 table in the E2 draft does not).
- README says tokens are cached "whatever `expires_in` says" (true: `src/stores/access-token-cache.ts:7`).
- Spec vs source (acknowledged in README 133-148): response camelCase; `weightUnitOfMeasure` enum; no `required` at the top of `CreateLabelRequest`.
- Spec `servers: url: royalmail.gfsdeliver.com` (yaml:11-12) has no scheme; irrelevant to callers.

UNVERIFIED:
- Whether real Sapient/royalmail.gfsdeliver.com behaves like the mock for: double-cancel, manifest of never-picked ids, `shipFrom` omitted, field-length limits, label formats beyond the four in the enum, whether non-GB/IM is the actual dutiable rule (the mock invents it, `mock:64-65`), `DOX` exemption from Items.
- Deployed Cloud Run auth/IAM for the mock proxy and whether an inbound `Authorization` header would be stripped by the platform.
- Selector's actual Royal Mail client code (`GFSRMApi`, `RoyalMail.pas`) is not in this repo; which fields it really sends is inferred from `scripts/smoke.mts:55-71` (uses `domesticRequest()` from `apps/royal-mail-proxy/test/helpers.ts:58-98`: labelFormat PDF, contentType NDX, shippingLocationId 101, GB->GB, one package KILOGRAM/CENTIMETER, serviceCode RMT24, descriptionOfGoods, businessTransactionType B2C).
- Whether oversize bodies/`PayloadTooLarge` give 500 (derived from `global-error.ts:30-34`, not tested).
- Real Sapient behaviour for `GRAM` (the proxy sends the number unmodified; whether Sapient's account setting interprets it as grams or kg is unknown).

### Notes for the E2 draft

Claims in the E2 draft (`~/Documents/obsidian/Bifrost/Selector2/E2 - mock proxies page (draft).md`) that the source contradicts or that are incomplete for royalmail:
1. Line 85 (and the failure-table intro): "Postcode and ZIP values ignore spaces and case. An id prefix also ignores case." FALSE for royalmail. Every royalmail magic value is an exact, case- and space-sensitive match: `ERR 400/401/500`, `NODOC *` (`apps/mock-upstreams/src/royalmail/index.ts:70,136,140,144`), `SHIPMENT-500` (`:368`), `MANIFEST-500` (`:419`), and service code `RMT48SOLD` (`apps/royal-mail-proxy/src/stores/royalmail-store.ts:73-76,90`). Only UPS normalises (`apps/mock-upstreams/src/ups/shipment.ts:19`).
2. Line 90: "`NODOC CN23`, `NODOC CI`, `NODOC ALL` ... The label, with a warning, and without that customs document": incomplete. `NODOC CN23` has no effect for PDF labels; `NODOC ALL` with a PDF label still returns the CN23 (inline) and warns only about the invoice; with a non-PDF label `NODOC ALL` removes the whole `documents` key. The postcode must be on a dutiable (non GB/IM) destination.
3. Line 89: "`ERR 401` ... A carrier error with that status": correct, but state that it is HTTP 401 with `code:"CARRIER SERVER ERROR"`, which is easily mistaken for an auth failure (auth failures are 403 only).
4. Line 91: "`SHIPMENT-500` ... 500 on the status update": correct but it only fails `updateShipmentStatus`; inside `manifestShipments` it is swallowed (manifest returns 201).
5. Line 93: "`RMT48SOLD` ... 500 (a disabled code)": true only for `rm-key-acme` (TPS48 on its list); for `rm-key-bramble` it is a 400 no-mapping. The 500 is the generic `INTERNAL SERVER ERROR` body, not a carrier error.
6. Line 94: "`rm-key-inactive` 400 no mapping; getServiceCodes is 500": correct for those two; add that manifestShipments and updateShipmentStatus still succeed for this key.
7. Line 179: "Royal Mail sends a `GRAM` weight as if it were kilograms": correct but understated: the weight unit is never read at all (any unit is passed through as the number), and manifest `totalWeight` comes back in KG. Related unlisted quirk: `INCH` dimensions are divided by 2.54.
8. Line 184: "Typos in error texts are kept, for example `additonal`": for royalmail the `additonal` text is in dead code (`apps/royal-mail-proxy/src/exceptions.ts:76`, `InternalError` is never constructed) and never reaches a caller; it is live in bjs/exelot/ocs.
9. Line 20: the "Creates Royal Mail labels and customs documents, manifests, changes shipment status, lists service codes" row is accurate; consider adding that there is NO validate, NO dedicated cancel (cancel = status change) and NO reprint/track.
10. Lines 64-70: royalmail 403/403/403 for no key/unknown/`apiky-500`: correct. (Also 403 when the Sapient credentials are bad, which the table omits.)
11. Line 183: "Malformed JSON gives a 500, not a 400": correct for royalmail (generic `INTERNAL SERVER ERROR`).
12. Not in the draft but worth adding for royalmail: unknown route returns 400 (not 404); non-JSON content type is accepted as an empty body; a manifest served by another mock-upstreams instance has zero shipments; `stateOrRegion` must be present.


---

## ups (UPS; apps/ups-proxy; mirrors ups.gfsdeliver.com)

Paths are relative to `~/code/merak/carrier-playground` at `origin/main`. Proxy sources are `apps/ups-proxy/...`; the upstream faker is `apps/mock-upstreams/src/ups/*` (cited `mock-ups:`). The proxy is TWO products in one process: (A) a "stepping-stone" XML passthrough (what Selector uses today per README `apps/ups-proxy/README.md:9-24`) and (B) a V2 JSON API that maps a GFS JSON contract onto UPS Shipping API v2403. Both sit behind the same ApiKy check.

### Operations and routes

Base: all business routes live under `/api` (ApiKy-protected). Router matching is Express default = case-insensitive and trailing-slash tolerant (`apps/ups-proxy/src/app.ts:53-55`, README 28-29: CSS calls `/ShipConfirm`, source mounts `/shipConfirm`).

| Operation | METHOD path | Supported? | Notes |
| --- | --- | --- | --- |
| validate | V2 `POST /api/v2/shipping/createLabel?validate=true` | yes (V2 only) | `validate=true` -> UPS `RequestOption:'validate'`, anything else `'nonvalidate'` (`src/api/routesV2/create-label.ts:20,28`). It still CREATES the shipment/label in the mock (mock ignores RequestOption, `mock-ups json.ts:78-153`); real UPS "validate" semantics UNVERIFIED. XML: no separate op; `<RequestOption>validate|nonvalidate</RequestOption>` is just forwarded (mock ignores it). UPS two-step XML ShipConfirm is itself the "validate + quote" step (see below). |
| create-ship (XML, step 1) | POST `/api/stepping-stone/shipConfirm` | yes | XML in/out. Returns charges + `ShipmentDigest` + `ShipmentIdentificationNumber`. No labels yet. Forwards to `{UPS_XML_ENDPOINT}/api/ups.app/xml/ShipConfirm` (`src/config.ts:39-45`). |
| create-ship (XML, step 2) | POST `/api/stepping-stone/shipAccept` | yes | Takes the digest from ShipConfirm; returns tracking numbers + base64 labels (+ international `Form`). Forwards to `.../xml/ShipAccept`. |
| create-ship (JSON) | POST `/api/v2/shipping/createLabel` | yes | One-shot: ship + label, 200 JSON `{shipmentId, packages[]}` (`create-label.ts:101`). UPS `POST /api/shipments/v2403/ship`. |
| delete-cancel (XML) | POST `/api/stepping-stone/void` | yes | Forwards to `.../xml/Void`. |
| delete-cancel (JSON) | DELETE `/api/v2/shipping/:consignmentNumber/cancel?trackingNumber=` | yes | 204 on success. UPS `DELETE /api/shipments/v1/void/cancel/{consignmentNumber}?trackingnumber=` (`routesV2/delete-shipping.ts:13-25`). |
| commit-manifest | none | NO | UPS has no manifest/end-of-day route in this proxy (XML or V2). ShipAccept is the commit step for a shipment (ShipConfirm is not billed until accepted in real UPS: UNVERIFIED here). |
| reprint (XML) | POST `/api/stepping-stone/labelRecovery` | yes, but BROKEN for CSS | Forwards to `{UPS_XML_ENDPOINT}/api/webservices/LBRecovery`. CSS sends `text/xml`, which the proxy cannot parse, so CSS label recovery gets UPS error 10001 (see Quirks). Client4 (`application/xml`) works. |
| reprint (JSON) | GET `/api/v2/shipping/:trackingNumber/label?format=ZPL` | yes | `format` default `ZPL`, upper-cased (`get-label.ts:16,27`); returns `{label:{image}, trackingId}` (no `format`). |
| track | none | NO | |
| other: locator (XML) | POST `/api/stepping-stone/locator` | yes | Forwards to `.../xml/Locator`. |
| other: access point by id | GET `/api/v2/access-points/country/:countryCode/access-point/:id` | yes | 200 mapped access point or 404. |
| other: access point search | POST `/api/v2/access-points/search` | yes | `{results:[...]}`. |
| other: health | GET `/health/liveness` (`{"ok":true}`), `/live` (`SERVER_IS_NOT_SHUTTING_DOWN`), `/ready` and `/health` (`SERVER_IS_READY`), `/` (`ok`) | yes, no auth | `app.ts:31-40,56-58`. |
| other: CORS | OPTIONS any | yes, no auth | 204; `Access-Control-Allow-Origin: *` on every response (`src/api/middleware/cors.ts`). |

Anything else under `/api/...`: no catch-all route, so Express's default HTML 404 (`Cannot POST /api/...`) after the ApiKy check (derived from `app.ts:53-59`; UNVERIFIED by test).

Middleware order (`app.ts:19-59`): correlation -> health probes -> CORS -> `express.json()` -> `express.text()` -> `express.raw({type:'application/xml'})` -> `express.urlencoded` -> request id -> `/api` ApiKy -> `/api/stepping-stone` and `/api/v2` routers -> `/` -> error handler. Body parsers run BEFORE auth, so malformed JSON with no key is a 500, not a 401. Default 100 kb body limit on every parser (derived; UNVERIFIED for prod).

### Auth and headers

- Header: `x-api-key` (read via `req.headers['x-api-key']`, `src/api/middleware/express-apiky-middleware.ts:10`) on every `/api/*` route, XML and JSON alike. Lookup `GET {APIKY_URL}/api/profile?token=<key>` with the proxy's service key (`packages/apiky-client/src/index.ts:31-43`). The profile is attached to the request and never used; so which valid key is used makes no difference (profile is only `{company}`).
- Fixture key NAMES (`apps/mock-upstreams/fixtures/apiky/ups.json`, README 90-95): `ups-key-testco` (Testco Widgets Ltd), `ups-key-mockbridge` (Mockbridge Trading), `apiky-500` (ApiKy outage). Anything else: ApiKy 403.
- Missing key -> 401; unknown key -> 403; ApiKy 500 or unreachable -> 500; all as JSON error body (see Error shape) even on the XML routes (`express-apiky-middleware.ts:11-33`; `test/auth.test.ts:21-52`).
- UPS-side auth is the proxy's own: one shared OAuth client credentials grant `POST {UPS_ENDPOINT}/security/v1/oauth/token` (Basic auth, `grant_type=client_credentials`), token cached per client id for `expires_in - 60` seconds (`src/auth.ts:15-54`). The caller never supplies UPS credentials; Selector's own UPS account is only expressed in the XML `ShipperNumber`/`AccountNumber`.
- Other headers: for XML routes the request `Content-Type` MUST be `application/xml` (parameters like `; charset=...` are fine) or the body is destroyed (see Request). For V2 JSON routes `Content-Type: application/json`. Response content type: XML routes ALWAYS `application/xml; charset=utf-8` (even when the body is JSON, `stepping-stone.ts:31-33`); V2 routes `application/json`. Inbound Cloud Run `Authorization: Bearer` is never read (only the outbound UPS call sets Authorization, `stepping-stone.ts:24`, `src/upstream.ts:37`), so it is ignored. Whether the deployed service is public: UNVERIFIED.

### Request

#### A. XML passthrough (`/api/stepping-stone/*`)

The proxy does no parsing or validation. Body handling (`stepping-stone.ts:9-13`; README 55-61):
- `Content-Type: application/xml` -> raw bytes forwarded unchanged to UPS (including a `Windows-1252` declaration; CSS bytes reach UPS as sent), UPS gets `Content-Type: application/xml`, `Accept: */*`, `Authorization: Bearer <shared token>`.
- `Content-Type: text/plain` -> the string.
- ANYTHING ELSE, notably `text/xml` and a missing Content-Type: the body parsers leave `req.body = {}` and the proxy POSTs the two characters `{}` to UPS. UPS answers its "not well formed" error (`ErrorCode 10001`) as HTTP 200 XML. `test/stepping-stone.test.ts:183-202`.
- Max body 100 kb (derived).
Selector must therefore send `Content-Type: application/xml`. CSS (C#, `UPSProcedures.cs`) sends `<?xml version="1.0" encoding="Windows-1252"?>` + no whitespace + `application/xml`, EXCEPT label recovery which it sends as UTF-8 `text/xml` (breaks). Client4 (Delphi) sends `<?xml version="1.0"?>` + `application/xml` (`apps/mock-upstreams/fixtures/ups/README.md:5-9`). Paths are called with the operation name appended (`CUST_SITES.UPS_URL = https://ups.gfsdeliver.com/api/stepping-stone/` + `ShipConfirm`...), any letter case.

XML request envelopes (as Selector sends them; samples `apps/mock-upstreams/fixtures/ups/*.xml`). The MOCK UPS reads only the fields below; real UPS needs more (not enforceable here: UNVERIFIED):

| Route | Root element | Fields the mock reads (path under root) | Mock errors (UPS-shaped codes) |
| --- | --- | --- | --- |
| ShipConfirm | `ShipmentConfirmRequest` | `Request/TransactionReference/CustomerContext` (echoed); `Shipment/Shipper/ShipperNumber`; `Shipment/Service/Code`; `Shipment/ShipTo/Address/{PostalCode,CountryCode,City}`; each `Shipment/Package/PackageWeight/Weight` (one package per `<Package>`; unit ignored, treated as kg); `LabelSpecification/LabelPrintMethod/Code` (ZPL/EPL/SPL/STARPL win) else `LabelSpecification/LabelImageFormat/Code` (GIF/PNG/PDF) else GIF; presence of `Shipment/ShipmentServiceOptions/InternationalForms` -> adds a PDF form on accept (`mock-ups xml.ts:112-151`). NB `LabelSpecification` is a child of the root, not of `Shipment`. | `120100` no ShipperNumber; `120120` ShipperNumber `NOAUTH`; `120202` no ShipTo CountryCode; `121210` no Service/Code; `120700` no Package; `120802` postcode `FA1 1LV` (`mock-ups shipment.ts:56-108`) |
| ShipAccept | `ShipmentAcceptRequest` | `ShipmentDigest` (copied verbatim from ShipConfirm), `Request/TransactionReference/CustomerContext` | `128089` invalid/absent digest (`xml.ts:158-168`) |
| Void | `VoidShipmentRequest` | `ShipmentIdentificationNumber` at the ROOT (CSS) or inside `Request/` (Client4) or `ExpandedVoidShipment/ShipmentIdentificationNumber` (`xml.ts:229-232`) | `190100` no id; `190117` id `1Z0000000000000000` |
| LabelRecovery | `LabelRecoveryRequest` | `TrackingNumber` at root or in `Request/`; `LabelSpecification/LabelImageFormat/Code` or `Request/LabelImageFormat/Code` (default GIF) (`xml.ts:256,268-271`) | `151044` no or magic tracking number |
| Locator | `LocatorRequest` | `LocationSearchCriteria/AccessPointSearch/PublicAccessPointID` or `LocationID`; `OriginAddress/AddressKeyFormat/{CountryCode,PostcodePrimaryLow}`; `OriginAddress/MaximumListSize` or `LocationSearchCriteria/MaximumListSize` (cap 50, default 10) (`xml.ts:292-309`; `shipment.ts:269-279`) | `350104` origin postcode `NO1 0AP` or nothing found; HTTP 500 for `TE5 500` |

Wrong root element -> `10002` "well formed but the document is not valid"; empty or non-XML body -> `10001` (`xml.ts:78-104`). Both HTTP 200.

Declared-but-ignored by the mock: `RequestOption` (validate), dimensions, addresses beyond ShipTo country/postcode/city, payment, `ShipFrom`.

#### B. V2 JSON (`/api/v2/*`)

No validation; types are loose (`src/api/routesV2/types.ts`; README 148-154: "request bodies aren't validated, so a malformed body is a 500, not a 400").

`POST /api/v2/shipping/createLabel[?validate=true|false]` body `shippingRequest` (`api/openapi.yaml:423-484`):
- Required by the spec (not enforced): `shipTo`, `shipFrom`, `labelSpecification.labelFormat`, `serviceCode`. Required by the CODE (unguarded reads that throw -> 500): `shipTo` and `shipFrom` objects each WITH an `address` object (`routesV2/mapping/customer.ts:19-24`), and `packages.items[].weight` (`create-label.ts:52-54`). `test/v2.test.ts:183-186`.
- Party (`shipFrom`/`shipTo`): `companyName` (-> UPS `Name` AND `CompanyDisplayableName`), `name` (-> `AttentionName`), `phone`, `email`, `accountNumber` (-> `ShipperNumber`), `taxNumber`, `locationId`, `iossOrVoec` (-> `VendorInfo.VendorCollectIDNumber`), `address{street1,city,stateProvinceCode,postalCode,countryCode,isResidential}`. Spec requires `companyName` and `accountNumber` on a party (`openapi.yaml:611-615`), code does not. Single `street1` only.
- `serviceCode` forwarded raw as `Service.Code` (spec enum of 2-char UPS codes: `01 02 03 07 08 11 12 13 14 17 54 59 65 M2..M7 70 71 72 74 75 82..86 96`, `openapi.yaml:414`). `returnService.code` optional (`'9'` forced when ShipTo country is `CN`, `transformers/china.ts:9`).
- `description` -> `Description` (trimmed). Shipper number is NOT from the request: `Shipper.ShipperNumber` and the bill-shipper `AccountNumber` are the proxy's `SHIPPER_NUMBER` env (`create-label.ts:22,33,37`), payment type `01`.
- `packages.items[]` (one UPS `Package` per item): `description`, `comments`, `packageCode` (enum names mapped to UPS codes: LETTER 01, CUSTOMER_PACKAGE 02, TUBE 03, PAK 04, EXPRESS_BOX 21, 10KG_BOX 25, 25KG_BOX 24, SMALL/MEDIUM/LARGE_BOX 2a/2b/2c, PALLET 30, ..., unknown values pass through, `mapping/package-code.ts`), `dimensions{unit CM|IN,length,width,height}` (stringified, forwarded raw), `weight{unit KGS|LBS|OZS, value}` (value stringified: "UPS rejects a number here", `create-label.ts:53-54`), `commodityCode`, `originCountryCode` (for customs `Product`). Units are passed through unconverted.
- `serviceOptions.internationalForms{type,comments,declarationStatement}`: `type` mapped INVOICE 01, CO 03, NAFTA_CO 04, PARTIAL_INVOICE 05, PACKING_LIST 06, CUSTOMER_GENERATED_FORMS 07, AIR_FREIGHT_PACKAING_LIST 08 (sic), CN22 09, UPS_PREMIUM_CARE 10, EEI 11 (`mapping/form-type.ts`). The block is ALWAYS sent (even domestic/no forms), as a sibling of `Shipment` not inside it (`create-label.ts:58-75`), so mock/real UPS sees it as `ShipmentRequest.ShipmentServiceOptions`; the mock only honours `Shipment.ShipmentServiceOptions` (`mock-ups json.ts:95-96`), so NO form is ever produced via V2 in the mock.
- `labelSpecification.labelFormat` enum `ZPL | PDF | PNG | GIF` (spec); sent raw as `LabelImageFormat.Code`; `ZPL` additionally adds `LabelStockSize {Height:'6',Width:'4'}` (`create-label.ts:76-84`). Omitted -> mock default GIF.
- Transformers (applied in order canaryIslands, china, norway, euToGb, gbToEu, gbToRest, domestic; `routesV2/transformers/index.ts`) mutate VendorInfo: ShipTo `CN` -> `ReturnService.Code '9'`; ShipTo `NO` -> `0357` + `VOEC` prefix on the number; ShipTo in GB/GG/JE/IM -> `0359` then (if ShipFrom GB and ShipTo Europe incl. GB) overwritten with `0356`; ShipFrom GB to non-Europe -> removes both vendor fields. Canary-islands and domestic transformers never fire (they look inside `Shipment` while the options sit beside it). Only visible in the UPS request, not in the response.

`DELETE /api/v2/shipping/:consignmentNumber/cancel?trackingNumber=...`: path `consignmentNumber` = shipment identification number. Query is `trackingNumber` (NOT `trackingId` as the swagger says). If missing the proxy sends the literal string `undefined` upstream, which the mock then rejects 190101 (`test/v2.test.ts:206-211`).

`GET /api/v2/shipping/:trackingNumber/label?format=ZPL|PDF|PNG|GIF`: `format` default `ZPL`, upper-cased.

`GET /api/v2/access-points/country/:countryCode/access-point/:id`: no body.

`POST /api/v2/access-points/search`: `{origin:{countryCode,postalCode,street1,street2,street3,county,city}, limit (default 10), radius (default 75), unit (default "MI")}`. Street lines are sent under the misspelt UPS key `AdressLine` so UPS never uses them (`search-access-points.ts:41`).

### Response

#### A. XML routes
HTTP status and body are exactly UPS's, `Content-Type: application/xml; charset=utf-8` (`stepping-stone.ts:28-33`). UPS reports business errors as HTTP 200 with `ResponseStatusCode` 0 (README 52-53), so Selector must read the XML, not the status.

Common response block: `<Response><TransactionReference><CustomerContext>echoed</CustomerContext><XpciVersion>1.0001</XpciVersion></TransactionReference><ResponseStatusCode>1|0</ResponseStatusCode><ResponseStatusDescription>Success|Failure</ResponseStatusDescription>[<Error><ErrorSeverity>Hard|Warning</ErrorSeverity><ErrorCode/><ErrorDescription/>[<ErrorLocation><ErrorLocationElementName/></ErrorLocation>]</Error>...]</Response>` (`mock-ups xml.ts:49-65`). Built with no pretty-printing, declaration `<?xml version="1.0"?>`.

- ShipConfirm success root `ShipmentConfirmResponse`: `Response`, `ShipmentCharges/{TransportationCharges,ServiceOptionsCharges,TotalCharges}/{CurrencyCode GBP,MonetaryValue}`, `BillingWeight/{UnitOfMeasurement/Code KGS, Weight}` (min 0.5, rounded up to 0.5), `ShipmentIdentificationNumber` (== first tracking number, `1Z` + 6-char shipper + 2-char service + 7 digits + check digit, e.g. `1ZMOCK0111xxxxxxxx`), `ShipmentDigest` (base64 JSON of the whole plan; opaque, MUST be sent back verbatim to ShipAccept) (`xml.ts:138-150`; `shipment.ts:150-165`). A `WA1 1RN` postcode adds a Warning `<Error>` (code `120900`) with ResponseStatusCode still `1`.
- ShipAccept success root `ShipmentAcceptResponse`: `ShipmentResults/{ShipmentCharges, BillingWeight, ShipmentIdentificationNumber, PackageResults[], Form?}`. Each `PackageResults`: `TrackingNumber`, `ServiceOptionsCharges`, `LabelImage/{LabelImageFormat/Code, GraphicImage (base64), HTMLImage (base64 HTML, GIF only)}`. One PackageResults per `<Package>` sent to ShipConfirm; per-package labels, no combined blob. Label format code echoes: `ZPL|EPL|SPL|STARPL` (base64 of printer text), `PDF` (real PDF), `GIF` (1x1 placeholder + HTMLImage), `PNG` (1x1 placeholder) (`mock-ups labels.ts:32-91`). International forms: `<Form><Code>01</Code><Description>All Requested International Forms</Description><Image><ImageFormat><Code>PDF</Code>...</ImageFormat><GraphicImage>base64 PDF</GraphicImage></Image></Form>` present iff the ShipConfirm had `Shipment/ShipmentServiceOptions/InternationalForms` (`xml.ts:192-215`). Warnings: none on accept.
- Void success root `VoidShipmentResponse`: `Response` + `Status/{StatusType/Code 1, StatusCode/Code 1}` (`xml.ts:240-248`). Void twice, or of an unknown (non-magic) id: still success (mock is stateless).
- LabelRecovery success root `LabelRecoveryResponse`: `ShipmentIdentificationNumber`, `LabelResults/{TrackingNumber, LabelImage{LabelImageFormat/Code, GraphicImage, HTMLImage?}}` (`xml.ts:273-286`).
- Locator success root `LocatorResponse`: `SearchResults/DropLocation[]` each with `LocationID`, `Geocode`, `AddressKeyFormat{ConsigneeName,AddressLine,PoliticalDivision2,PoliticalDivision1?,PostcodePrimaryLow,CountryCode}`, `PhoneNumber`, `Distance{Value, UnitOfMeasurement{Code MI}}`, `StandardHoursOfOperation` (text), `LatestGroundDropOffTime`, `AccessPointInformation{PublicAccessPointID,ImageURL,AccessPointStatus{Code 01 active|02 inactive}}` (`xml.ts:316-345`).
- Gateway errors (mock `TE5 500`): HTTP 500, body JSON `{"response":{"errors":[{"code":"10500","message":"Mock UPS internal server error"}]}}` but still labelled `application/xml` (`stepping-stone.ts:33`; `test/stepping-stone.test.ts:262-281`).

#### B. V2 routes
- createLabel 200: `{ "shipmentId": "<1Z...>", "packages": [ { "trackingId": "<1Z...>", "label": { "image": "<base64>", "format": "ZPL|PDF|PNG|GIF" } }, ... ] }` (`routesV2/mapping/shipment.ts`, `mapping/label.ts`). One entry per package, per-package labels. `label.image` = `InternationalSignatureGraphicImage ?? GraphicImage`, raw base64 (no data URI). `shipmentId` = UPS `ShipmentIdentificationNumber` (== first `trackingId`). NO charges, NO forms/customs documents (the proxy drops `Form` and the mock never creates one), NO warnings: the `WA1 1RN` Alert upstream is dropped, so V2 callers see a plain success (README says "JSON: an Alert" about the upstream, not the proxy output).
- cancel 204 empty.
- label recovery 200: `{ "label": { "image": "<base64>" }, "trackingId": "..." }`; `label.format` is ABSENT because the proxy reads `ImageFormat` but UPS names it `LabelImageFormat` there (`mapping/label.ts:10-13`, `get-label.ts:48`; `test/v2.test.ts:222-227`).
- access point (by id) 200: `{id, imageUrl, isActive (AccessPointStatus.Code==='01'), name, schedule:[{day:'SUN'..'SAT',open:'HH:MM',close:'HH:MM'}] (HoursType 10 only; closed day -> '' ''), address:{countryCode,city,county?,street1,postalCode,geo:{lat,lng}}, distance:{value,unit}}` (`mapping/access-point.ts:46-73`; `test/v2.test.ts:254-281`). Search 200 `{results:[...same shape...]}`; no hits is a 400 (see D5), not an empty list. Inactive point `U99000003` still returned with `isActive:false`.

### Error shape

All proxy-originated errors (both XML and V2 routes) are JSON: `{ "errorId": "<request uuid>", "errorCode": "<string|number>", "messages": [...], "metadata": {} }` (`src/api/middleware/error-handler.ts:7-31`; README 66-83). `metadata` is always `{}`. On XML routes this JSON is returned with `Content-Type: application/json` (the `application/xml` label is applied only to proxied UPS responses).

| Case | Status | errorCode | messages |
| --- | --- | --- | --- |
| No `x-api-key` | 401 | `UNAUTHORIZED` | `[null]` |
| ApiKy rejects the key | 403 | `FORBIDDEN` | `["Your account does not have access to use this service"]` |
| ApiKy 500 / unreachable | 500 | `INTERNAL_SERVER_ERROR` | `["Internal Server Error"]` |
| UPS OAuth refused/unreachable, UPS 5xx on a V2 route, unexpected UPS body shape, malformed JSON, unguarded TypeError (missing shipTo/shipFrom/address/weight), non-400 4xx from UPS on a V2 route | 500 | `INTERNAL_SERVER_ERROR` | `["Internal Server Error"]` |
| UPS 400 on a V2 createLabel / cancel / label / search | 400 | `400` (a number, not a string) | UPS's `response.errors` array, e.g. `[{"code":"120802","message":"Address Validation Error on ShipTo address"}]` (`src/errors.ts:58-70`) |
| V2 access point by id not found (UPS 400) | 404 | `NOT_FOUND` | `["Access point not found"]` |

- XML routes: UPS business failures are 200 + XML (`ResponseStatusCode` 0); only transport/gateway failures are non-200: UPS HTTP 5xx is passed through with its status and (JSON) body; proxy-side failures (OAuth, unreachable, ApiKy) are the JSON error above with 500.
- Malformed JSON on V2: generic 500 (`INTERNAL_SERVER_ERROR`), not 400, even before the ApiKy check (parsers run first). `express.json` errors lack `httpStatusCode`, so the handler reports 500 (`error-handler.ts:11-18`).
- V2 400 from UPS has no `message` strings in `messages`; it is an array of `{code, message}` objects (different from the 401/403/500 string arrays). A client must branch on `errorCode`.

### Failure scenarios for D5 (magic values)

UPS magic values are normalised: spaces removed and upper-cased (`mock-ups shipment.ts:19`: `norm = v.replace(/\s+/g,'').toUpperCase()`), so `fa1 1lv`, `FA11LV`, ` FA1  1LV ` all fire. This applies to postcodes, the shipper number, and the unknown-shipment id. It does NOT apply to the V2 cancel tracking-number regex (case-insensitive `^1Z[0-9A-Z]{16}$`, `mock-ups json.ts:158`). Constants in `mock-ups shipment.ts:4-17`.

| Operation | field | magic value | where verified | what the caller sees |
| --- | --- | --- | --- | --- |
| ShipConfirm (XML) | `Shipment/ShipTo/Address/PostalCode` | `FA1 1LV` | `shipment.ts:100-107`, `xml.ts:136` | HTTP 200 XML, `ResponseStatusCode 0`, `ErrorSeverity Hard`, `ErrorCode 120802` "Address Validation Error on ShipTo address", `ErrorLocationElementName ShipmentConfirmRequest/Shipment/ShipTo/Address/PostalCode` (`test/stepping-stone.test.ts:235-242`) |
| createLabel (V2) | `shipTo.postalCode` | `FA1 1LV` | `json.ts:101` -> proxy `create-label.ts:96-98` | 400 `{errorCode:400, messages:[{code:"120802",message:"Address Validation Error on ShipTo address"}]}` (`test/v2.test.ts:164-171`) |
| ShipConfirm (XML) | ShipTo postcode | `WA1 1RN` | `shipment.ts:110-119`, `xml.ts:140` | 200 success (`ResponseStatusCode 1`) plus `<Error><ErrorSeverity>Warning</ErrorSeverity><ErrorCode>120900</ErrorCode>` |
| createLabel (V2) | `shipTo.postalCode` | `WA1 1RN` | `json.ts:126-134` | upstream 200 with `Alert`, but the proxy drops it: caller sees an ordinary 200 success, no warning |
| ShipConfirm (XML) | ShipTo postcode | `TE5 500` | `shipment.ts:99`, `xml.ts:135` | HTTP 500, JSON body `{"response":{"errors":[{"code":"10500",...}]}}`, header `application/xml` (`test/stepping-stone.test.ts:262-281`) |
| createLabel (V2) | `shipTo.postalCode` | `TE5 500` | `json.ts:100`, `upstream.ts:40` | 500 `INTERNAL_SERVER_ERROR` generic body (`test/v2.test.ts:178-181`) |
| Locator (XML) | `OriginAddress/AddressKeyFormat/PostcodePrimaryLow` | `TE5 500` | `shipment.ts:270` | HTTP 500 JSON gateway error (as ShipConfirm) |
| V2 access-points/search | `origin.postalCode` | `TE5 500` | `json.ts:218` | 500 `INTERNAL_SERVER_ERROR`. NOT triggerable via V2 get-access-point-by-id (no postcode is sent upstream, `get-access-point.ts:17-28`). |
| Locator (XML) | origin postcode | `NO1 0AP` | `shipment.ts:271`, `xml.ts:311-314` | 200 XML `ResponseStatusCode 0`, error `350104` "No locations found" |
| V2 access-points/search | `origin.postalCode` | `NO1 0AP` | `json.ts:219-220` | 400 `errorCode 400`, `messages:[{code:"350104",message:"No locations found"}]` (`test/v2.test.ts:328-331`) |
| V2 access point by id | `:id` unknown (e.g. `U00000000`) | | `shipment.ts:273-278` | 404 `NOT_FOUND` `["Access point not found"]`. Fixture ids: `U99000001`-`U99000003` GB (`U99000003` inactive), `U99000004` FR (README 116). When `id` is given the country is ignored for matching. |
| ShipConfirm (XML) | `Shipment/Shipper/ShipperNumber` | `NOAUTH` | `shipment.ts:66-73` | 200 XML failure, `120120` "The shipper number is not authorised for this account" (`test/stepping-stone.test.ts:244-251`) |
| createLabel (V2) | (proxy env `SHIPPER_NUMBER`, not a request field) | `NOAUTH` | `create-label.ts:22` | NOT triggerable by a caller; only by deploying the proxy with `SHIPPER_NUMBER=NOAUTH` (then 400 `messages:[{code:"120120"...}]`). The E2 row for the shipper number applies to the XML route only. |
| Void (XML) | `ShipmentIdentificationNumber` | `1Z0000000000000000` | `xml.ts:238-239` | 200 XML failure `190117` "No shipment found within the allowed void period" (`test/stepping-stone.test.ts:163-170`). Missing id: `190100`. |
| cancel (V2) | path `:consignmentNumber` | `1Z0000000000000000` | `json.ts:161-165` | 400 `messages:[{code:"190117",...}]`. The magic value is on the PATH id, not the `trackingNumber` query (the proxy test uses it in both, `test/v2.test.ts:213-218`). |
| cancel (V2) | query `trackingNumber` | anything not matching `^1Z[0-9A-Z]{16}$` (case-insens.), incl. missing (proxy sends literal `undefined`) | `json.ts:157-160` (checked BEFORE the path-id magic) | 400 `messages:[{code:"190101",message:"Invalid tracking number"}]` |
| LabelRecovery (XML) | `TrackingNumber` | `1Z0000000000000000` or absent | `xml.ts:257-266` | 200 XML failure `151044` "No shipment found for the tracking number" |
| label (V2) | path `:trackingNumber` | `1Z0000000000000000` | `json.ts:180-182` | 400 `messages:[{code:"151044",...}]` |
| any XML route | request `Content-Type` | `text/xml` or none (CSS label recovery) | `stepping-stone.ts:9-13`; `xml.ts:85` | 200 XML failure `10001` "The XML document is not well formed" (proxy sent `{}`) |
| any XML route | body | wrong root element | `xml.ts:93-101` | 200 XML failure `10002` |
| ShipAccept (XML) | `ShipmentDigest` | tampered or absent | `xml.ts:158-168` | 200 XML failure `128089` |
| any `/api` route | `x-api-key` | absent / unknown / `apiky-500` | `express-apiky-middleware.ts` | 401 `UNAUTHORIZED` / 403 `FORBIDDEN` / 500 `INTERNAL_SERVER_ERROR` |
| any route | proxy env `CLIENT_ID` | `ups-oauth-401` | `mock-ups index.ts:8,44`; README 110 | every route 500 `INTERNAL_SERVER_ERROR` (deployment-level, not caller-triggerable) |

### Quirks mirrored from production

- XML routes forward the body byte for byte; the only accepted XML content type is `application/xml`; `text/xml` and absent content type are replaced by `{}`, which is why CSS label recovery cannot work through this proxy (`stepping-stone.ts:9-13`, README 55-61, `test/stepping-stone.test.ts:183-202`).
- UPS errors on XML routes are HTTP 200 + `ResponseStatusCode 0`; UPS JSON gateway errors on those routes keep their 5xx status but are labelled `application/xml` (`stepping-stone.ts:31-33`).
- All paths case-insensitive (Express default).
- V2 create-label builds `ShipmentServiceOptions` beside `Shipment`, so the domestic and canary-islands transformers never fire; GB to GB ends with `VendorCollectIDTypeCode 0356` because "EU" in the source is countries-list's continent EU = Europe (README 160-165; `routesV2/transformers/gb-to-eu.ts:4-11`).
- `AdressLine` misspelt in access-point search; `VendorInfo: {}` sent for parties without IOSS/VOEC; label recovery `format` always absent (`LabelImageFormat` vs `ImageFormat`) (README 166-168).
- A UPS 4xx other than 400 on a V2 route becomes 500 (reaches code expecting success) (README 169).
- V2 cancel sends `trackingnumber=undefined` when `trackingNumber` is missing (swagger documents it as `trackingId`) (`delete-shipping.ts:15`).
- `numPieces` and `packs` in the V2 spec are never read; the form-type name `AIR_FREIGHT_PACKAING_LIST` keeps its typo (`mapping/form-type.ts:8`).
- Error `metadata` is always `{}`; `messages: [null]` for a missing key; `errorCode` is a number for UPS-400 passthroughs and a string elsewhere.
- Wire details of the mock UPS that differ from real UPS (not production-mirrored): label images GIF/PNG are 1x1 placeholders; `ShipmentDigest` is base64 JSON; weight unit is ignored (LBS treated as KGS) and BillingWeight is always KGS; currency GBP; JSON lists (`PackageResults`, `DropLocation`) are always arrays (real UPS may return a single object) (README 118-132).

### Statefulness / ordering constraints

- XML create is strictly two-step: ShipConfirm -> take `ShipmentDigest` -> ShipAccept. The digest embeds the plan, so ShipAccept works on any mock-upstreams instance and after restarts; tracking numbers are random (7 digits), collisions possible but rare (`shipment.ts:149-165`; README 129-130). Labels exist only after ShipAccept in the XML flow; ShipConfirm alone creates nothing a caller can use.
- V2 create is one call; no digest.
- Void and label recovery take any id/number except the magic one (mock keeps no state): voiding twice, voiding something never created, and recovering a label for an arbitrary number all succeed (README 127-128; `json.ts:155-204`). No ordering constraint between create and cancel/label in the mock.
- Proxy state: only the OAuth token cache (per client id, `expires_in - 60` s). No idempotency; repeated ShipConfirm creates new numbers.
- Calls can be split across Cloud Run instances safely (stateless).

### Adapter implications and leaks

- No manifest, no tracking. Generic `commit-manifest` must be unsupported for ups. Generic `validate` is only the V2 `?validate=true`, which in practice still creates; the XML two-step is a quote/confirm step, not a free validation.
- A generic `createShipment` must special-case the XML flow: two HTTP calls with a server-issued opaque digest (ShipConfirm -> ShipAccept), per-package labels in ShipAccept, forms in `Form`, and errors in a 200 body (`ResponseStatusCode`, `Error[]`). An adapter that treats HTTP 200 as success will mis-handle every UPS business error. XML parsing (Windows-1252 declaration possible in the REQUEST; responses are UTF-8 `<?xml version="1.0"?>`) is required in the adapter if it speaks the XML routes.
- If Selector2 uses V2 instead: single call, JSON, no digest, UPS 400s surface as 400 with a numeric `errorCode` and `messages` as `{code,message}` objects, UPS 5xx/proxy faults as 500 with string `messages`; no warnings and no customs/forms documents are returned (the generic result's `documents`/`warnings` must be empty for ups V2); `label.format` is not returned on recovery, so the adapter must remember what it requested.
- Which transport is "real"? README says Selector (CSS and Client4) uses the XML stepping-stone and the V2 routes show no traffic (README 21-24: ~6.3k ShipConfirm, 6.2k ShipAccept, 41 Void, 211 key-less 401s over 22 Oct-5 Nov 2026; "nothing shows [V2] are used"). Per-carrier decision: UNVERIFIED which one Selector2 should target; XML is the proven one.
- Content-Type discipline: the adapter must send `application/xml` for XML (never `text/xml`).
- The caller cannot choose the shipper account on V2 (proxy env `SHIPPER_NUMBER`); on XML the caller sets `ShipperNumber`/`AccountNumber` in the XML, and the real proxy passes them straight to UPS under the shared GFS OAuth client (account authorisation is UPS's job). Mock only checks non-empty and `NOAUTH`.
- Weights/dimensions: units are forwarded verbatim (KGS/LBS/OZS, CM/IN); the proxy does no conversion; the mock treats all weights as kg.
- Label format knobs differ per transport: XML `LabelPrintMethod/Code` (thermal: ZPL/EPL/SPL/STARPL) beats `LabelImageFormat/Code` (GIF/PNG/PDF); V2 only `labelFormat` (ZPL/PDF/PNG/GIF per spec).
- Error mapper must key on shape per transport: XML routes may also return the proxy JSON error (auth, OAuth, upstream down) or a JSON 5xx labelled `application/xml`; check the body's first character, not only `Content-Type`.
- Tracking number format `1Z` + 16 chars; `shipmentId` equals the first package's tracking number.
- Access points are a UPS-specific concept (`locator`/`access-points`); generic interface needs an `other` operation.

### README-vs-source discrepancies, and UNVERIFIED

README (`apps/ups-proxy/README.md`) vs source:
- README 99: "Postcodes match with spaces removed, case-insensitively. They apply to the XML and the JSON APIs alike." Correct; extend: also the shipper number and the unknown-shipment id use the same `norm` (`shipment.ts:19,66,238,257`), but the V2 cancel `trackingNumber` check is a case-insensitive regex of `1Z`+16 alphanumerics, not `norm`.
- README 108 "Void shipment id, label recovery tracking number `1Z0000000000000000`": for V2 cancel the magic id is the PATH `consignmentNumber` (`json.ts:156,161`), not the `trackingNumber` query; the trackingNumber query only has to be a well-formed `1Z`+16 (the magic value itself passes that regex).
- README 106 "Shipper number (XML `Shipper/ShipperNumber`; V2 uses `SHIPPER_NUMBER`)": accurate, but it means V2 `NOAUTH` is not caller-triggerable (README implies equivalence with the XML row).
- README 104 for `WA1 1RN`: "(JSON: an Alert)": that is the upstream mock; the V2 proxy output discards it (`mapping/shipment.ts:9-17`).
- README 103/109 do not say V2 get-access-point cannot hit the postcode magic values (no postcode in that request, `get-access-point.ts:17-28`); only search can.
- README "Access points: `U99000001`-`U99000003` in GB (`U99000003` inactive)": matches `shipment.ts:192-262`.
- The swagger/openapi differences (`trackingId` vs `trackingNumber`, `consignmentNumber` vs `trackingNumber` path param, `accessPointId` vs `id`, `{packages}` vs `{label,trackingId}`) are listed in README 145-154 and verified in code.
- README says logs and `UPS_XML_ENDPOINT` default; `.env.example` confirms (`apps/ups-proxy/.env.example`).

UNVERIFIED:
- Real UPS behaviour of everything the mock invents: error codes outside the ones the README flags as UPS-real (the README itself says "not every one is UPS's real code", README 113-114), `validate` semantics, digest lifetime/billing at ShipConfirm vs ShipAccept, label formats, void windows.
- Which XML fields Selector's production code really sends: only the mock fixtures (`apps/mock-upstreams/fixtures/ups/*.xml`) derived from `UPSProcedures.cs` / `uUPSClient.pas` (neither is in this repo). The mock does not enforce, for instance, `ShipFrom`, `PaymentInformation`, `PackagingType`, dimensions.
- Real-UPS XML requests may exceed the 100 kb default body limit (derived from express defaults in `app.ts:43-46`; prod limit unknown).
- Whether a Windows-1252 body survives intact through the mock upstream (the mock reads it via `express.text`, default utf-8 decoding of the request; only ASCII fixtures are tested, `test/stepping-stone.test.ts:85-90`). The proxy itself forwards bytes untouched.
- V2 `validate=true` real effect; whether V2 will ever be enabled for Selector.
- Deployed Cloud Run auth/IAM and whether an inbound `Authorization` header is stripped.

### Notes for the E2 draft

Claims in `~/Documents/obsidian/Bifrost/Selector2/E2 - mock proxies page (draft).md` that the source contradicts or that are incomplete for ups:
1. Line 21 ("Passes Selector's UPS XML through (ShipConfirm, ShipAccept, Void, Locator, LabelRecovery) and serves the V2 JSON routes"): accurate, but incomplete: XML routes need `Content-Type: application/xml`; CSS label recovery sends `text/xml` and the proxy turns the body into `{}`, so it ALWAYS returns UPS error 10001 (HTTP 200). XML business errors are HTTP 200. There is no manifest, validate-only or tracking route.
2. Line 96 (`FA1 1LV` -> "Address error `120802`: XML 200 with `ResponseStatusCode` 0, JSON 400"): correct. Add that V2 400 carries `errorCode:400` (a number) and `messages:[{code,message}]`.
3. Line 97 (`WA1 1RN` -> "Success with warning `120900`"): true for the XML route only. The V2 route drops the alert; the caller sees an ordinary success.
4. Line 98 (`TE5 500` ShipTo or Locator origin postcode -> "500 gateway error as JSON"): true for XML routes (JSON body, `application/xml` content-type, status 500). On V2 the proxy turns it into its own generic 500 (`errorCode INTERNAL_SERVER_ERROR`, `messages:["Internal Server Error"]`), not the UPS body. V2 get-access-point-by-id cannot trigger it (only search can).
5. Line 99 (`NO1 0AP` -> "No locations, `350104`"): XML 200 + `ResponseStatusCode 0`; V2 search 400 `messages:[{code:"350104"...}]`. Not triggerable on V2 get-by-id.
6. Line 100 (Shipper number `NOAUTH`): only the XML route lets a caller set it. On V2 the shipper number is the proxy's `SHIPPER_NUMBER` env, so a V2 caller cannot trigger it.
7. Line 101 (Void shipment id / label recovery tracking number `1Z0000000000000000`): for V2 cancel it is the path `consignmentNumber` that carries the magic id (not the `trackingNumber` query). Void/label recovery on XML: HTTP 200 with the `190117`/`151044` error.
8. Line 102 (V2 cancel `trackingNumber` "Anything but `1Z` plus 16 characters" -> `190101`): correct; precisely `^1Z[0-9A-Z]{16}$`, case-insensitive, checked before the id magic; a missing `trackingNumber` is sent as the literal `undefined` and hits 190101.
9. Line 85 ("Postcode and ZIP values ignore spaces and case. An id prefix also ignores case."): TRUE for ups (`mock-ups shipment.ts:19`); contrast royalmail where it is false.
10. Lines 64-70: ups 401/403/500 for no key / unknown key / `apiky-500`: correct. Errors are the JSON `errorId/errorCode/messages/metadata` shape even on XML routes.
11. Line 183 ("Malformed JSON gives a 500, not a 400, on several mocks"): applies to ups V2 (generic `INTERNAL_SERVER_ERROR`), and malformed JSON is evaluated before the ApiKy check.
12. Line 79 ("UPS sample XML is in `apps/mock-upstreams/fixtures/ups/`"): correct (CSS and Client4 samples, `css-*.xml`, `client4-*.xml`).
13. Missing from the draft and worth adding for ups: the ShipConfirm -> ShipAccept digest flow; label (GIF/ZPL/EPL/PDF/PNG) is per-package and base64 in `GraphicImage`; the `application/xml` content-type requirement; V2 returns no charges/forms/warnings; label-recovery `format` is absent; and the README's own production-traffic note that V2 appears unused.


---

## coll8 (Coll8; apps/coll8-proxy; mirrors coll8.gfsdeliver.com)
All citations are `path:line` on origin/main (ae57c96). Secret values in fixtures are elided.

### Operations and routes
| operation | METHOD path | supported? | notes |
| --- | --- | --- | --- |
| create-ship (+label) | POST `/labelling/CreateLabel` | yes | One call creates the shipment at Coll8 then fetches one label per package; labels come back inline. `apps/coll8-proxy/src/app.ts:66`, `src/labelling.ts:49-84`. Path is case-insensitive (Express); Client4 sends `/labelling/createLabel` (`test/routes.test.ts:76-79`). |
| delete-cancel | POST `/labelling/CancelShipment?trackingId=<consignmentNo>` | yes | No body needed. `app.ts:67`, `labelling.ts:86-100`. |
| commit-manifest | POST `/labelling/eodManifest` | yes | End-of-day manifest. Body `{shippingDate, trackingIds[]}`. `app.ts:68`, `labelling.ts:102-135`. |
| validate | - | NOT supported | No route. Validation only happens as a side effect of CreateLabel (Coll8 rejects, proxy maps to 500). |
| reprint / standalone label fetch | - | NOT supported | No route. `getPackageLabel` is internal to CreateLabel (`src/coll8-api.ts:45-67`). So "label" prefix magic values cannot be triggered from outside (see D5 table). |
| track | - | NOT supported | |
| other | GET `/` -> 200 `ok` (no auth, `app.ts:58-60`); GET `/health/liveness` -> 200 `{"ok":true}` (no auth, not logged, `app.ts:51-53`) | yes | Everything else (unknown path, wrong method) -> 500 SYSTEM_ERROR (see Error shape). |

Middleware order (`app.ts:49-70`): correlation, `/health/liveness`, `express.json()` (default 100kb limit, strict), requestId, request log, `apikyAuth` mounted on `/labelling` only, `GET /`, express-openapi-validator against `api/swagger.json`, routes, `classifyError`, `errorHandler`. Consequence: body JSON parse happens BEFORE auth (malformed JSON gets 500 with no key); auth happens BEFORE schema validation (no key + invalid body gets 401); schema validation happens before the handler.

### Auth and headers
- Header: `x-api-key` only (`src/middleware.ts:36`). `Authorization: Bearer ...` from the caller is never read, so it is ignored (no code path inspects it). UNVERIFIED: whether Cloud Run IAM in front of the service consumes/rejects it (infra, not in this app).
- Fixture key NAMES (`apps/mock-upstreams/fixtures/apiky/coll8.json`, README `apps/coll8-proxy/README.md:50-57`): `coll8-test-key-alpha` (account `MOCKC8-0001`), `coll8-test-key-bravo` (`MOCKC8-0002`), `coll8-test-key-no-account` (profile `{}`), `coll8-test-key-unknown-account` (account `MOCKC8-9999`, rejected by Coll8). `apiky-500` (mock ApiKy returns 500, `apps/mock-upstreams/src/apiky/index.ts:37-40`). Anything else: mock ApiKy 403 (`apiky/index.ts:41-45`).
- ApiKy lookup: `GET {APIKY_BASE_URL}/api/profile?token=<caller key>` with the proxy's own service key in `x-api-key` (`packages/apiky-client/src/index.ts:32-36`). The account code is read from `profile.profile.accountCode` (`src/labelling.ts:18-29`).
- Failure matrix (`src/middleware.ts:34-60`):
  - No/empty `x-api-key`: 401, `{"message":"No API key provided"}` (pretty-printed JSON, `writeJson` at `middleware.ts:8-11`, 401 at `:38`).
  - Key unknown to ApiKy (or any ApiKy non-500 status incl. 401 for a bad service key): 403 `{"message":"Not authorised"}` (`:57`).
  - `apiky-500` / ApiKy 500: `next(e)` -> `classifyError` -> 500 `{errorId, errorCode:"SYSTEM_ERROR", messages:{message:"ApiKy returned 500"}}` (`:51-55`, `:63-71`; test `routes.test.ts:161-164`).
  - ApiKy unreachable: 500 `{message:"ApiKy unreachable", name:"ApiKyError"}` (`:46-50`). Not triggerable via fixtures.
- Per-operation account-code requirement (important): CreateLabel and eodManifest call `getAccountCode` (`labelling.ts:62`, `:104`) and fail 403 `ACCOUNT_CODE_NOT_CONFIGURED` when the profile lacks `accountCode`. CancelShipment does NOT call it (`labelling.ts:86-100`), so `coll8-test-key-no-account` and `coll8-test-key-unknown-account` can still cancel.
- Content-Type: CreateLabel/eodManifest need `application/json` bodies (swagger requestBody `api/swagger.json:33-41,74-83`). CancelShipment must send NO body, or an empty body (see quirks).

### Request
CreateLabel body (`api/swagger.json:89-195`; TS shape `src/map/css-to-coll8.ts:41-52`).
Schema-required: `serviceProvider` (string, never read by code), `labelSpecification.labelFormat` (string), `consignment.weight{unit,value}` (both required `:229`), `packages[]` (array; no minItems, each item requires `dimensions` object `:136`, dimensions inner fields all optional `:196-216`), `shipFrom`, `shipTo` (address required: `name, addressLine1, city, countryCode, postalCode, email, mobileNumber` `:316`), `serviceType`. Unknown extra properties are allowed (no additionalProperties:false).
What the code actually reads (`css-to-coll8.ts:105-192`):
- `serviceType` -> Coll8 `serviceType`: `D2S`->`drop2shop-Collect` (no signature), `D2SR`->`drop2shop-Return` + `signatureServices:[{service:"SignatureName"}]`, `D2HB`->`drop2me` + `SignatureName`, `DSHB`->`drop2me` + `SignatureRequired`; any other string passes through unchanged (`:62-68`, `:184-186`). Mock Coll8 only knows `drop2me`, `drop2shop-Collect`, `drop2shop-Return` (`apps/mock-upstreams/fixtures/coll8/coll8.json:14`; check at `apps/mock-upstreams/src/coll8/index.ts:152-155`) -> an unknown code gives 500 COLL8_ERROR_CREATE_SHIPMENT, message "The service type is not supported. ServiceType" (`test/failures.test.ts:47-50`).
- Weight: `consignment.weight.unit` `KILOGRAM`->`KG`, ANY OTHER VALUE PASSES THROUGH UNCHANGED (`:70-72`); no GRAM/POUND conversion, no unit validation in proxy or mock Coll8. `weight.value` is sent as-is. EVERY package gets the whole consignment weight and unit (`:154-155`); it is not split across packages.
- Dimensions: `dimensions.length` -> Coll8 `depth`, `width`, `height` as-is, `dimensions.unit` -> `uomDimensions` as-is (swagger example `CM`; tests use `CENTIMETER`) (`:147-153`). No rounding, no unit conversion.
- Packages: `description`, `packagingType` (default `Box`, read though absent from swagger), `packageClientReferenceId` (first package only -> `references[0]` customerReference), `invoiceNumber` (first package only -> `retailerInvoice.invoiceNumber`) (`:128,139,177-182`).
- Customs: if `customs.commodities` non-empty, every package gets the full `packageItems` list built from the commodities: `value = value.value / quantity` (unit price), `invoiceAmount = value.value` (line total), `countryOfOrigin` default `GB`, `packagingType` default `CT`, `hsCode`, weight with `KILOGRAM`->`KG` (`:156-170`). `countryOfOrigin` and commodity `packagingType` are read but not in swagger (`api/swagger.json:231-254`). Quantity 0 would divide by zero (UNVERIFIED effect).
- Invoice: explicit `invoice{invoiceNumber,currencyCode,totalAmount,shippingAmount}` wins (currency default `EUR`, amounts default 0, `shippingAmount`->`shippingCost`); else if commodities exist, `retailerInvoice = {invoiceNumber: packages[0].invoiceNumber, currencyCode:"EUR" (hard-coded, ignores commodity currency), totalAmount: sum of commodity value.value}`; else no `retailerInvoice` (`:115-133`, `getTotalValue` `:74-78`).
- Addresses (`:80-102`): `addresses[0]` = shipFrom, `[1]` = shipTo; `postalCode`->`postCode`; `name`->`contact.contactName`; `phoneNumber`, `email`, `mobileNumber` copied; `eoriNumber` is IGNORED (always `''`); `addressLocationType` always `residential`; `addressLine2/3` always `''`. Missing optional fields become `''`.
- `shippingDate` = today's UTC date, server-chosen (`:141`); callers cannot set it.
- `labelType` sent to Coll8 create = caller's `labelFormat` lower-cased (`:187`) (so `png` is sent at create even though the label fetch asks for `pdf`).
- NOT read: `serviceProvider`, `serviceOptions`, `shipFrom/shipTo.eoriNumber`, `shipTo.state` only copied.
Label format (`labelling.ts:52-60`): `labelFormat` is lower-cased; `pdf` and `png` -> fetch `pdf` from Coll8; `zpl` -> fetch `zpl`; anything else (e.g. `GIF`, `EPL`) -> `NOT_SUPPORTED` 500 with message `Unsupported label format: <lower-cased>`. This check runs before the account-code check and before any upstream call.
Coll8 required-field checks in mock Coll8 (`apps/mock-upstreams/src/coll8/index.ts:161-180`): for BOTH addresses `addressLine1`, `city`, `postCode`, `countryCode` must be non-blank, else Coll8 400 -> proxy 500 COLL8_ERROR_CREATE_SHIPMENT, messages like `The City field is required. shipTo.City` (property rewrite `Addresses[0]`->`shipFrom`, `[1]`->`shipTo`, `src/errors.ts:47-49`). Empty `packages` -> "At least one package is required. Packages" (mock `:156-160`).
eodManifest body (`api/swagger.json:318-334`): `shippingDate` (string) and `trackingIds` (string[]) both required; empty array passes schema and succeeds. `shippingDate` is parsed with `new Date(...)`; unparseable -> 500 INTERNAL_SERVER_ERROR (below); parseable values are normalised to `YYYY-MM-DD` via `toISOString().substring(0,10)` (`css-to-coll8.ts:195-205`), so a datetime string is accepted. `trackingIds` are sent as `trackingNumbers` with `numberOfShipments = length`.
CancelShipment: `trackingId` query value is taken as everything after the LAST `=` in the raw `originalUrl`, still URL-encoded (`labelling.ts:89`), and inlined into the upstream path (`coll8-api.ts:73`). A request with no `=` in the URL sends the whole path as the id (UNVERIFIED outcome: derived, likely 404 passthrough from Coll8 route miss, code COLL8_ERROR_CANCEL_SHIPMENT). Extra query params after `trackingId` would corrupt the id (the last `=` wins).
Schema validation failure: 400 `{errorId, errorCode:"SCHEMA_VALIDATION_FAILURE", messages:{message:"request/body must have required property 'serviceType'"}}`, application/json (`middleware.ts:63-66`; test `routes.test.ts:133-141`).

### Response
CreateLabel success: 200 `application/json` (`labelling.ts:77`):
`{ "id": 1, "packages": [ { "id": <1-based idx>, "documents": "<base64 string>", "trackingId": "<package tracking no.>", "consignmentNo": "<shipment tracking no., same on all packages>" } ], "errors": [] }` (`src/map/coll8-to-css.ts:56-77`; spec `api/swagger.json:335-374`). `id` is the constant 1. One entry per Coll8 `packageTrackingNumbers[]`; one label per package; no shipment-level label, no customs/invoice document, no warnings field (`errors` is always `[]`).
- `documents` encoding (`coll8-to-css.ts:19-53`): PDF request -> Coll8's own base64 PDF string passed through; ZPL request -> Coll8 returns ZPL text in `data.zpl[0]`, proxy base64-encodes it as ASCII (so decode base64 to get the ZPL program); PNG request -> Coll8's PDF is POSTed to the PDF converter `{PDF_CONVERTER_SERVICE_ENDPOINT}/pdfconverter` body `{pdfString}` and the returned `pngString` (base64 PNG) is used. Only `[0]` of the Coll8 label array is used. No data-URI prefix.
- Tracking: for cancel/manifest use `packages[].consignmentNo`; the per-package id is `packages[].trackingId` (mock formats: consignment `GFSU99<digit>` + 9 digits, package = consignment + `001`,`002`..., `apps/mock-upstreams/src/coll8/index.ts:210-215`). The mock does not distinguish whether cancel/manifest receive a consignment or package number (accepts any non-magic string); real-Coll8 behaviour UNVERIFIED.
- Packages ordering: `Promise.all` over packages; first rejection wins (`coll8-to-css.ts:62-66`).
CancelShipment success: 200 `{"message":"Shipment cancelled"}` (Coll8 body passed through, `labelling.ts:93`; mock `index.ts:323`).
eodManifest success: 200 `{"message":"EOD Manifest added for Ship Date <YYYY-MM-DD>"}` (`index.ts:304`).
Success bodies use `res.send(object)` so they are `application/json`.

### Error shape
Three distinct shapes depending on route and failure kind:
1. Proxy/framework errors (`middleware.ts:74-98`): JSON `{errorId, errorCode, messages}`, `application/json`. Used for: schema failure (400 SCHEMA_VALIDATION_FAILURE, `messages:{message}`), every other framework error (500 SYSTEM_ERROR, `messages:{message}`), and anything with no `httpStatusCode` (500 INTERNAL_SERVER_ERROR, `messages:["Internal Server Error"]`, `:76-78`).
2. CreateLabel and CancelShipment carrier errors (`labelling.ts:78-83`, `:94-99`): body is `scrub(String(e.message))` where `e.message` is the JSON-stringified payload `{errorId, errorCode, messages}` (`errors.ts:77-91`) sent with `res.send(<string>)`, so Content-Type is `text/html; charset=utf-8` although the body is JSON text (test `routes.test.ts:110-121`: asserts `text/html; charset=utf-8` and `JSON.parse(res.text)`). An adapter must JSON.parse the text body regardless of Content-Type.
3. eodManifest carrier errors (`labelling.ts:112-134`): real `application/json`. Status = `e.httpStatusCode` if 400..599 else 500. Body = parsed payload; if the message is not JSON (e.g. bad date) body is `{errorId, errorCode:"INTERNAL_SERVER_ERROR", messages:["<text>"]}` (messages is an ARRAY here, an object elsewhere) (`:122-129`; test `routes.test.ts:274-287`).
Status derivation for Coll8GenericError (`errors.ts:35-75`):
- Coll8 validation body `{errors:[...]}` -> ALWAYS 500 whatever status Coll8 returned; `messages` = array `[{message:"<message> <property>"}]` with `Addresses[0]`->`shipFrom`, `Addresses[1]`->`shipTo` (`:43-49`). Empty `errors` list -> `messages:{message:[]}` (`:50-52`).
- Auth0 body with `error_description` -> Auth0's status, `messages:{message:<description>}` (`:53-56`).
- Any other upstream body -> upstream status with `messages` = upstream body; empty body -> `messages:{message:"Request returned status code N"}` (`:57-63`).
- No `response` but has `.message` (network error) -> 500 `{message}`; string -> 500 `{message:<string>}` (`:65-72`).
- `redactSecretKeys` redacts any key matching authorization|token|secret|password|api[-_]?key|credential|cookie to `[REDACTED]` in echoed bodies; `scrubSecrets` also replaces the caller key, service key, client secret and current bearer token anywhere in the body (`errors.ts:10-27`, `app.ts:33-38`).
Error codes: `COLL8_ERROR_CREATE_SHIPMENT`, `COLL8_ERROR_PACKAGE_LABEL`, `COLL8_ERROR_LABEL_TRANSLATION` (hard-coded 500, `errors.ts:111-116`), `COLL8_ERROR_CANCEL_SHIPMENT` (used for cancel AND eod, `coll8-api.ts:78,93`), `COLL8_TOKEN_FAILURE`, `NOT_SUPPORTED`, `ACCOUNT_CODE_NOT_CONFIGURED` (403 via `labelling.ts:23-26`).
Plain-text error (not JSON at all): failed PNG conversion -> 500, body exactly `An error has occured while converting the PDF label to PNG` (typo "occured" kept) (`errors.ts:131-138`, `labelling.ts:82` sends `e.message` text; test `failures.test.ts:125-131`).
Malformed JSON body: 500 SYSTEM_ERROR JSON (body-parser SyntaxError has `.message` so `classifyError` maps it, `middleware.ts:66-67`); returned BEFORE auth. Unknown path / wrong method: validator not-found/405 -> 500 SYSTEM_ERROR `{message:"not found"}` for unknown routes (`test/routes.test.ts:298-306`); for `/labelling/*` unknown routes auth runs first. Body > 100kb: UNVERIFIED (default express.json limit, expected 500 SYSTEM_ERROR via the same path).
No 599 anywhere in coll8; carrier validation = 500, carrier 5xx/other statuses pass through.

### Failure scenarios for D5 (magic values)
Postcode magic values are the shipTo `postalCode`, normalised by stripping ALL whitespace and upper-casing before compare (`apps/mock-upstreams/src/coll8/index.ts:51-52,182`), so `val1dn`, `VAL  1DN` and `VAL 1DN` all fire. Magic compare runs only after the required-address-field checks pass.
| operation | field | magic value | where verified | what the caller sees |
| --- | --- | --- | --- | --- |
| CreateLabel | shipTo.postalCode | `VAL 1DN` | `mock-upstreams/src/coll8/index.ts:18,183-191` | 500 `COLL8_ERROR_CREATE_SHIPMENT`, text/html JSON, `messages:[{message:"The postcode is not valid for the destination country. shipTo.PostCode"}]` (`test/failures.test.ts:36-45`) |
| CreateLabel | shipTo.postalCode | `ERR 500` | `index.ts:192-195` | 500 `COLL8_ERROR_CREATE_SHIPMENT`, `messages:{message:"An error has occurred."}` (`failures.test.ts:52-61`) |
| CreateLabel | shipTo.postalCode | `ERR 503` | `index.ts:196-199` | 503 `COLL8_ERROR_CREATE_SHIPMENT`, `messages:{message:"Request returned status code 503"}` (`failures.test.ts:63-72`) |
| CreateLabel | shipTo.postalCode | `ECH 0ED` | `index.ts:200-208` | 400 `COLL8_ERROR_CREATE_SHIPMENT`; messages echo the upstream body with credentials redacted: `{message:"The request is invalid.", request:{headers:{authorization:"[REDACTED]"}}, detail:"Rejected request carrying ... [REDACTED]"}`. Tests that secrets never leak (`failures.test.ts:85-93`). Missing from the E2 draft. |
| CreateLabel | shipTo.postalCode | `NOL 4BL` | `index.ts:210-211,241-244`; coll8-to-css `:27-29,36-38` | shipment created, label has `data:{}` -> 500 `COLL8_ERROR_LABEL_TRANSLATION`, `messages:{message:"Coll8 response does not contain label data"}`. Fires for PDF, PNG and ZPL alike. |
| CreateLabel | shipTo.postalCode | `LBL 500` | `index.ts:236-240` | shipment created, label fetch 500 -> 500 `COLL8_ERROR_PACKAGE_LABEL`, `messages:{message:"An error has occurred."}` (any format) |
| CreateLabel | shipTo.postalCode + `labelFormat` PNG | `PNG 500` | `index.ts:126-129,265`; `coll8-to-css.ts:43-50` | ONLY when labelFormat is PNG: 500 plain text `An error has occured while converting the PDF label to PNG`. With PDF or ZPL, `PNG 500` returns a normal 200 (the failure marker lives in the PDF and only the converter looks at it). |
| CreateLabel | shipTo.postalCode | (missing city/addressLine1/postalCode/countryCode on either address) | `index.ts:161-180` | 500 `COLL8_ERROR_CREATE_SHIPMENT`, messages `[{message:"The City field is required. shipFrom.City"}, ...]` |
| CreateLabel | serviceType | any code not in {`D2S`,`D2SR`,`D2HB`,`DSHB`, `drop2me`, `drop2shop-Collect`, `drop2shop-Return`} | `index.ts:152-155` | 500 `COLL8_ERROR_CREATE_SHIPMENT`, `[{message:"The service type is not supported. ServiceType"}]` |
| CreateLabel | labelSpecification.labelFormat | anything other than pdf/png/zpl (case-insensitive) e.g. `GIF` | `src/labelling.ts:52-60` | 500 `NOT_SUPPORTED`, text/html JSON, `messages:{message:"Unsupported label format: gif"}`; no upstream call |
| CreateLabel / eodManifest | x-api-key | `coll8-test-key-no-account` | `labelling.ts:19-29` | 403 `ACCOUNT_CODE_NOT_CONFIGURED`, `messages:{message:"No Coll-8 account code is configured for this API key"}`; CreateLabel: text/html JSON; eod: JSON. No Coll8 call (`routes.test.ts:123-131`). NOT triggered on CancelShipment. |
| CreateLabel / eodManifest | x-api-key | `coll8-test-key-unknown-account` | `index.ts:66-69,147-151,272-275` | 500 `COLL8_ERROR_CREATE_SHIPMENT` (or `COLL8_ERROR_CANCEL_SHIPMENT` for eod), `[{message:"Account 'MOCKC8-9999' is not recognised. Account.AccountCode"}]` (`failures.test.ts:74-83`). Cancel does not send an account so it succeeds. Missing from E2. |
| any /labelling | x-api-key | none / unknown / `apiky-500` | `middleware.ts:38,57,51-55` | 401 `{"message":"No API key provided"}` / 403 `{"message":"Not authorised"}` / 500 SYSTEM_ERROR JSON |
| CancelShipment | trackingId (prefix, case-insensitive) | `UNKNOWN` | `index.ts:309-312,37-42,53` | 404 `COLL8_ERROR_CANCEL_SHIPMENT` text/html JSON `messages:{message:"Shipment 'UNKNOWN-0001' not found."}` (status 404, not 500, `routes.test.ts:212-224`) |
| CancelShipment | trackingId | `CANCELLED` | `index.ts:313-316` | 500 `COLL8_ERROR_CANCEL_SHIPMENT`, `[{message:"The shipment is already cancelled. TrackingNumber"}]` |
| CancelShipment | trackingId | `MANIFESTED` | `index.ts:317-322` | 500 `COLL8_ERROR_CANCEL_SHIPMENT`, `[{message:"The shipment has already been manifested. TrackingNumber"}]` |
| eodManifest | trackingIds[i] (prefix) | `UNKNOWN` or `CANCELLED` (also empty string) | `index.ts:290-303` | 500 JSON, `errorCode:"COLL8_ERROR_CANCEL_SHIPMENT"`, `messages:[{message:"Tracking number 'UNKNOWN-0001' was not found. TrackingNumbers[0]"}]` (one entry per offender) (`routes.test.ts:259-272`) |
| eodManifest | trackingIds | `MANIFESTED` prefix | `index.ts:290-299` | NOT an error for manifest (succeeds). README matrix agrees (`README.md:84-88`). |
| eodManifest | shippingDate | non-parseable date | `css-to-coll8.ts:196-198`, `labelling.ts:122-129` | 500 JSON `{errorId, errorCode:"INTERNAL_SERVER_ERROR", messages:["Invalid shipping date, must be in YYYY-MM-DD format"]}` |
| label fetch | package tracking prefix `UNKNOWN` | - | `index.ts:226-229` | NOT reachable via the proxy: package numbers are minted by the mock, so a caller cannot choose one. README/E2 list "label" under the prefix scenarios; it cannot fire externally. (If it fired: Coll8 404 `{message}` -> PackageLabelError status 404, not 500, because only `LabelTranslationError` is forced to 500.) |
| any | Coll8 token | `CLIENT_ID=token-500` / wrong `CLIENT_SECRET` | `index.ts:80-92,96-99`; `token-manager.ts:29-31` | Config-time, not caller-controllable. 500 / 401 `COLL8_TOKEN_FAILURE` (`failures.test.ts:179-199`). Caller cannot trigger. |
| any /labelling | body | non-JSON body with `content-type: application/json` | `app.ts:54`; `routes.test.ts:226-232` | 500 `SYSTEM_ERROR` BEFORE auth (this is Client4's CancelShipment) |
Behaviours that look like scenarios but are not: no cancel-twice, no cancel-after-manifest, no manifest-of-cancelled for real shipments (stateless; only the prefixes above fail) (`README.md:102-103`).

### Quirks mirrored from production
- Coll8 validation errors are always surfaced as 500, even though Coll8 said 400 (`src/errors.ts:44-49`; E2 line 181 correct).
- Carrier-error bodies for CreateLabel and CancelShipment are JSON text served as `text/html`; eod errors are `application/json` (`labelling.ts:82,98` vs `:130-133`).
- Error message format `"<message> <property>"` with property text appended and `Addresses[n]` renamed (`errors.ts:47-49`).
- `COLL8_ERROR_CANCEL_SHIPMENT` is reused for end-of-day failures (`coll8-api.ts:93`), as in the source.
- Typo kept: `occured` in the PNG conversion error (`errors.ts:135`).
- Weight/dimension units pass straight through (only `KILOGRAM`->`KG`); whole consignment weight copied to every package (`css-to-coll8.ts:70-72,154-155`).
- Commodity-derived invoice is always `EUR` and its total sums each commodity's `value.value` (the line total, not unit price x quantity) (`css-to-coll8.ts:125-131`).
- `eoriNumber` dropped, `addressLocationType` always `residential` (`:80-102`).
- Cancel id = text after the last `=` of the raw URL (`labelling.ts:89`).
- Client4's cancel posts the consignment number as an `application/json` body that fails JSON parsing -> always 500 SYSTEM_ERROR before auth; CSS sends an empty body and works (`README.md:44-46`; `routes.test.ts:226-232`). Selector2 must send no body (an empty body with JSON content-type is fine: `routes.test.ts:187-195`).
- ApiKy 500: the source crashes the process on Node 18; the mock returns 500 SYSTEM_ERROR (`README.md:116-118`).
- Statelessness: nothing remembered between calls; cancel twice / cancel after manifest only fail via prefixes (`README.md:90-105`).
- Real-Coll8 behaviours (what Coll8 does with GRAM weights, mixed units, package vs consignment ids) are not modelled; the mock Coll8 does not validate `uomWeight`/`uomDimensions` at all (`mock-upstreams/src/coll8/index.ts:145-220`).

### Statefulness / ordering constraints
- Per-instance state: only the proxy's cached Coll8 bearer token (refreshed when < `TOKEN_EXPIRY_LIMIT` = 5 min remain, `token-manager.ts:34-43`, `config.ts:35`) and the `/__calls` recorder. No shipment store (`README.md:92-105`).
- Create must precede label by construction (label is inside CreateLabel). Cancel and manifest do NOT require a prior create: any non-magic id succeeds, including never-seen ids (`routes.test.ts:205-210`). So ordering cannot be tested for real; use prefixes.
- Not idempotent/retry-aware: CreateLabel mints a fresh tracking number every call; no dedupe. Safe-to-retry is the caller's problem. Proxy makes one attempt at the PDF converter and no retries on Coll8 (`README.md:135`).
- Multi-instance safe: tokens and scenario digits are encoded in the values (`README.md:95-100`).

### Adapter implications and leaks
- There is no validate and no reprint; a generic interface needs `create` returning inline label(s), `cancel(consignmentNo)`, `commitManifest(date, consignmentNos[])`. Cancel and manifest identify shipments by `consignmentNo`, not package `trackingId`; the adapter must persist `consignmentNo`.
- Manifest takes a date and a list of ids and is account-scoped via the API key's profile; no manifest document is returned, only `{message}`.
- Label format is selected by the caller via `labelSpecification.labelFormat` (`PDF`|`PNG`|`ZPL`); the response is a per-package base64 blob (ZPL is base64 of the ZPL text). PNG goes through an extra converter that can fail independently.
- Error-parsing must handle three bodies: JSON-text-as-text/html (create/cancel), application/json (eod and framework), and bare plain text (PNG conversion failure). Do not trust Content-Type. `messages` is sometimes an array of `{message}`, sometimes an object `{message}`, sometimes an arbitrary upstream object, sometimes (eod non-Coll8 error) an array of strings.
- A "carrier rejection" is a 500 here; use `errorCode` (COLL8_ERROR_*) to distinguish carrier validation (500 + `COLL8_ERROR_CREATE_SHIPMENT`) from proxy faults (500 + `SYSTEM_ERROR`).
- Weight must be sent as KG or KILOGRAM values yourself; no conversion happens. All packages carry the consignment total weight.
- Customs: pass `customs.commodities` (value is the LINE total; quantity must be >= 1) or an explicit `invoice`; there is no separate customs document in the response. Currency defaults to EUR in the derived invoice regardless of commodity currency.
- Selector service codes `D2S/D2SR/D2HB/DSHB` map to Coll8 types and signature services; unknown codes pass through and fail at Coll8.
- Cancel must not send a JSON body that is not valid JSON; send an empty body (query-param only).
- shipTo needs email and mobileNumber to pass the schema (required), addressLine1/city/postalCode/countryCode non-blank to pass Coll8.
- `ACCOUNT_CODE_NOT_CONFIGURED` is raised per operation (create, eod) not at auth time.

### README-vs-source discrepancies, and UNVERIFIED
- README says the unknown-prefix label row yields "404 (500 COLL8_ERROR_PACKAGE_LABEL)" (`README.md:86`). Source: `PackageLabelError` is not forced to 500 (only `LabelTranslationError` is, `errors.ts:111-116`), so it would be 404; moreover the case is unreachable from the proxy API. The `Label` column of the README matrix describes an internal call.
- README implies `NOL 4BL`/`LBL 500`/`PNG 500` are "label" scenarios; `PNG 500` only bites on PNG requests (README says "PNG requests", E2 says the same, consistent). Fine.
- README says apiky 500 -> "500 SYSTEM_ERROR" in Deviations only; the 401/403/500 table in README is consistent with source (`README.md:29-30,116-118`).
- README says paths are case-insensitive "and the validator follows it" (`README.md:20`): consistent with test `routes.test.ts:76-79`.
- swagger lists `serviceProvider` required, but the code never reads it; `serviceOptions`, `eoriNumber` unused; `countryOfOrigin` and commodity/package `packagingType` are read but absent from swagger.
- swagger error schema example (`api/swagger.json:395-418`) shows `messages:{message}` object; real bodies also use arrays.
- UNVERIFIED: behaviour with a missing `trackingId` query on cancel; request bodies >100kb; missing/odd Content-Type on CreateLabel (validator 415 mapped to 500 SYSTEM_ERROR per README `:42-43`); whether the real Coll8 accepts a package number for cancel/manifest; whether Cloud Run ignores a caller `Authorization: Bearer`; real-prod fidelity of anything (README states quirks are read from source, not checked against traffic).

### Notes for the E2 draft
- Line 108 ("Tracking number prefix (cancel, manifest, label)"): the label case cannot be triggered through the proxy (no label route; tracking numbers are minted server-side). Cancel/manifest prefix outcomes should be stated explicitly: cancel `UNKNOWN` = 404 (not 500), cancel `CANCELLED`/`MANIFESTED` = 500, manifest `UNKNOWN`/`CANCELLED` = 500 JSON, manifest `MANIFESTED` = succeeds, cancel/eod error bodies differ (text/html JSON vs application/json).
- Line 109 (`coll8-test-key-no-account` -> 403 `ACCOUNT_CODE_NOT_CONFIGURED`): true only for CreateLabel and eodManifest. CancelShipment never reads the account code and succeeds with that key. Also missing: `coll8-test-key-unknown-account` (500, "Account 'MOCKC8-9999' is not recognised") and the `ECH 0ED` postcode (400 with redacted echo).
- Line 107 (`PNG 500`): fires only when `labelFormat` is PNG; with PDF/ZPL it returns 200.
- Line 22 ("returns labels"): there is no separate label route; labels are inline in CreateLabel's response.
- Line 103-106: error bodies for CreateLabel are JSON text with `Content-Type: text/html`; callers must not rely on Content-Type.
- Line 181 ("Coll8 returns 500 for its own validation errors"): correct; also add that Coll8 validation errors are rewritten as `"<message> <property>"`.
- Line 183 ("Malformed JSON gives a 500, not a 400, on several mocks"): true for coll8 (500 SYSTEM_ERROR, before auth). Not true for fedex (400 VALIDATION ERROR, `apps/fedex-proxy/src/middlewares/global-error.ts:16-18`).
- Line 179 (weights): coll8 does no weight conversion at all (not even GRAM); worth listing beside OCS/Exelot/Royal Mail quirks.
- Line 69: coll8 apiky-500 -> 500 is a JSON `SYSTEM_ERROR` body `{errorId,errorCode,messages:{message:"ApiKy returned 500"}}`; no key is `{"message":"No API key provided"}`, unknown key is `{"message":"Not authorised"}`.


---

## fedex (FedEx; apps/fedex-proxy; mirrors fedex.gfsdeliver.com)
All citations are `path:line` on origin/main (ae57c96). Secret values in fixtures are elided.

### Operations and routes
| operation | METHOD path | supported? | notes |
| --- | --- | --- | --- |
| create-ship (+label, +customs invoice) | POST `/shipping/createShipment` | yes | 201. Labels and (for customs shipments) the commercial invoice come back inline. `apps/fedex-proxy/src/app.ts:86-89`. |
| delete-cancel | POST `/shipping/cancelShipment` | yes | Body `{accountNumber, shipmentId}`; 204 no body. `app.ts:90-93`, `src/integrations/fedex-integration.ts:138-181`. |
| validate | - | NOT supported | No route. The proxy performs service/lane validation as part of createShipment (see below) and, for `FXGND`, a FedEx transit-times availability pre-check (`fedex-integration.ts:65-83`). |
| commit-manifest | - | NOT supported | No route (FedEx close/manifest is not implemented). |
| reprint / label fetch | - | NOT supported | Labels only in the create response. |
| track | - | NOT supported | |
| other | GET `/` -> 200 `ok` (`app.ts:78-80`); GET `/health/liveness` -> 200 `{"ok":true}` (`app.ts:72-74`) | yes | Unknown path or wrong method -> 400 VALIDATION ERROR (`app.ts:100-106`). |
Routing is by openapi-backend 5.19.0 against `api/fedex-integration-api.yaml` (`app.ts:83-127`; README `apps/fedex-proxy/README.md:19-23`). Paths are case-sensitive; a trailing slash is ignored (`test/routes.test.ts:52-66`). Order of checks: global `express.json({limit:'1mb'})` (`app.ts:77`) -> route match -> `x-api-key` security -> schema validation -> handler (test `routes.test.ts:91-94` "checks the key before the body"; unknown route is answered with no key at all, `routes.test.ts:34-45`).

### Auth and headers
- Header: `x-api-key` (security scheme `api_key`, `api/fedex-integration-api.yaml:1148-1152`; read at `app.ts:118`). No other required header except `Content-Type: application/json` for the body. A caller `Authorization: Bearer ...` is never read (ignored). UNVERIFIED: Cloud Run IAM in front of the app.
- Fixture key NAMES (`apps/mock-upstreams/fixtures/apiky/fedex.json`; README `:73-83`): `fedex-key-alpha` (Alpha Test Freight Ltd, FedEx account `MOCKFX001`, all codes), `fedex-key-bravo` (Bravo Mock Goods Ltd, `MOCKFX002`, `FXIP` only), `fedex-key-inactive` (customer `isActive:false`), `fedex-key-no-account` (customer has no `fedexAccountNumber`), `fedex-key-unconfigured` (profile has a `fedexCustomerId` but no customer document), `fedex-key-rejected-account` (account `MOCKFX999`, unknown to mock FedEx), `fedex-key-malformed-profile` (profile without `profile` block), `apiky-500` (ApiKy returns 500). Anything else: ApiKy 403. Service key name for the proxy's own ApiKy call: value elided.
- ApiKy lookup `GET {APIKY_BASE_URL}/api/profile?token=<key>` (`packages/apiky-client/src/index.ts:32-36`); the shipping account is `profile.fedexCustomerId` (GUID), read unguarded (`fedex-integration.ts:49-51`).
- Failure matrix:
  - No key, unknown key, ApiKy 500, ApiKy unreachable: ALL identical 403 `{code:"FORBIDDEN", message:"Authentication failed", details:"Principal unknown could not be authenticated. No additional detail was provided."}` (`src/exceptions.ts:25-37`, `src/integrations/apiky-integration.ts:5-20`, `app.ts:107-109`; tests `routes.test.ts:70-89`). No FedEx call is made.
  - `fedex-key-malformed-profile`: 500 `{code:"INTERNAL SERVER ERROR", message:"An unexpected error occurred", details:"An unexpected error occurred on the server, no additional detail is available"}` (TypeError from unguarded `principal.profile`, `src/middlewares/global-error.ts:48-52`; `routes.test.ts:101-111`).
  - `AUTH_ENABLED=false` (config): ApiKy skipped; create uses body `shippingLocationId`, cancel uses `accountNumber` as the shipping account id (`app.ts:117`, `fedex-integration.ts:90,139`). Default is true (`src/config.ts:39`). Not caller-controllable.
- A key resolves to a customer (`customers.json`: `shippingAccountId`, `customer`, `isActive`, `fedexAccountNumber`, `fedexServicesList`) which decides the allowed GFS service codes and the FedEx account used on create. On CANCEL the FedEx account is whatever the caller puts in the body; the key's customer is used only to fetch a token (`fedex-integration.ts:148-160`). So `fedex-key-alpha` can cancel with `accountNumber:"MOCKFX002"` (any account known to mock FedEx: `MOCKFX001`..`003`, `apps/mock-upstreams/fixtures/fedex/fedex.json:5-9`).

### Request
POST /shipping/createShipment (spec `api/fedex-integration-api.yaml:59-285`; TS `src/services/fedex.service.types.ts:188-220`). Schema-required: `serviceCode`, `shipFrom`, `shipTo`, `labelSpecification`, `packages` (minItems 1, maxItems 1: exactly ONE package, `:85-90`). `customs` is optional in the spec (the TS type says required, but code guards `request.customs`).
- Address (`:286-385`): required `name, addressLine1, city, postalCode, stateOrRegion` (`stateOrRegion` may be `''`; its spec default is not applied). Optional: `companyName`(<=35), `addressLine2/3`, `countryCode` (2 chars, optional in spec but required in practice, below), `contactName`, `email`, `phoneNumber`, `vat`, `tinType`, `whatThreeWords`. `address.name` is NEVER sent to FedEx; the contact name comes only from `contactName` (README `:184`; `fedex.service.ts:35-41`). Max lengths enforced by schema (name 60, city 50, postalCode 20, phone 20 etc.).
- Package (`:386-464`): required `value{currency(3 chars),value(0..99999)}`, `weight{unit,value}`, `dimensions` (object; inner fields optional in schema but `unit` is needed in practice, below). `weight.unit` enum `GRAM|KILOGRAM|POUND`: `GRAM` is converted to KG (`value/1000`, 3 dp), `KILOGRAM`->`KG`, `POUND`->`LB` (`fedex-create-shipment-mapper.ts:140-145`, `fedex.service.ts:79-84`). `dimensions.unit` enum `INCH|CENTIMETER` -> `IN|CM`; missing/other unit -> 400 `Invalid dimensions unit: <v>` (`fedex.service.ts:86-94`). Dimensions are `Math.round`ed to whole numbers (a missing dimension becomes NaN -> `null` -> mock FedEx 400 "Package dimensions must be whole numbers.", `mapper:156-161`, mock `:209-216`). `packageClientReferenceId` (<=30) and `invoiceNumber` (<=30) are sent as CUSTOMER_REFERENCE / INVOICE_NUMBER customer references and print as REF / INV; empty strings send nothing (`mapper:32-41`). `description` -> `itemDescription`. `value` is only used when `requestExtraLiability` is true (declared value, currency mapped via `getCurrency`).
- `labelSpecification` (required both): `labelFormat` enum `PDF|PNG|ZPL203DPI|ZPL300DPI`; `labelStockType` enum `PAPER_4X6, PAPER_7X4.75, STOCK_4X6, STOCK_4X6.75_LEADING_DOC_TAB, STOCK_4X8, STOCK_4X9_LEADING_DOC_TAB` (`:1026-1061`). PAPER_* must go with PDF/PNG, STOCK_* with ZPL (mock FedEx 400 "Invalid values in Label Stock Type for LABEL" on mismatch, `mock-upstreams/src/fedex/index.ts:267-278`; test `create-shipment.test.ts:474-480`). Mapping (`fedex.service.ts:48-77`): `PDF` -> FedEx `imageType PNG`, resolution 203, then PNG is converted to a one-page PDF sized to the stock (4x6 = 288x432pt); `PNG` -> `PNG`, no resolution sent (mock defaults 203); `ZPL203DPI|ZPL300DPI` -> `ZPLII` with 203/300; the `.` is stripped from the stock type (`PAPER_7X4.75` -> `PAPER_7X475`). The code also maps `EPL*` -> `EPL2` but the spec enum excludes EPL, so schema validation rejects it.
- `serviceCode` (GFS code, e.g. `FXIP`) resolved per customer (see service validation). Fixture codes: `FXIP`->`INTERNATIONAL_PRIORITY`, `FXIPE`->`FEDEX_INTERNATIONAL_PRIORITY_EXPRESS`, `FXIE`->`INTERNATIONAL_ECONOMY`, `FXUKN`->`FEDEX_NEXT_DAY_END_OF_DAY`, `FXGND`->`FEDEX_GROUND`, `FXGHD`->`GROUND_HOME_DELIVERY`, `FXIPF` (disabled), `FXFF` (on no customer list) (`fixtures/services.json`, `fixtures/customers.json`; the real service table is MongoDB in production).
- Service/lane validation (`src/stores/fedex-store.ts:66-96`, `src/services/fedex-service-validation.ts`): code must exist, be enabled, and be on the customer's `fedexServicesList` else 400 `No mapping found for service code X for customer <customer name, or the shipping account id if no customer doc>`; inactive customer -> 400 `Customer <name> is not active`. THEN, for every service (even ones with no `validations`), BOTH origin and destination are resolved to a FedEx region from `shipFrom/shipTo.countryCode` + `stateOrRegion` via `src/data/country-codes.ts` (subdivision rows first, then country rows); an unknown country -> 400 `No country-codes mapping for country: XX`; both empty -> 400 `Country code is required for service validation` (`fedex-service-validation.ts:36-73`). `allowedCountryCodes` is applied only when the ORIGIN is in the rule's region; `excludedCountryCodes` only when the DESTINATION is (`:87-126`). E.g. `FXUKN`: from EU region only to GB; `FXIE`: destination IE excluded in region EU; `FXGND`/`FXGHD`: from US region only to US. GB is in FedEx region `EU` (`test/service-validation.test.ts:15-17`).
- Remaining validation order in the mapper (`fedex-create-shipment-mapper.ts:106-225`): service mapping + customer credentials in parallel; `No account number configured for partner <shippingAccountId>` (400); label spec; `PLT` without `customs` -> 400 `PLT requires customs details to be provided` (`:134-136`); shipment special services (`only one COD`, `RETURNS_CLEARANCE type OTHER requires description`, `Invalid currency: X` for non-3-char); per-package weight/packaging (`Packaging type X is not allowed for weight W U`; `YOUR_PACKAGING` limit 32 kg / 70 lb, or 68 kg / 150 lb when the FedEx service type contains "express", `fedex.service.ts:122-157`; other packaging types smaller); payor (`Payor is required when paymentType is: RECIPIENT|THIRD_PARTY` or whenever `payor` present is built; `paymentType` default `SENDER`). Any non-ValidationError thrown while mapping becomes 500 `INTERNAL SERVER ERROR` (`:222-225`).
- Customs (`fedex.service.ts:196-261`): `customs.commodities` required (>=1; `description` <=80, `hsCode` <=8 and sliced to 8, `quantity` int >=1, `value{currency,value<=99999}`); `reasonForExport` enum `Gift|Commercial Sample|Documents|Sale of Goods|Return of Goods|Mixed Content|Other` -> `GIFT|SAMPLE|NOT_SOLD|SOLD|RETURNED_GOODS|OTHER`; `incoTerms` `DDP` -> duties paid by SENDER, any other non-empty value -> RECIPIENT; `invoiceId` -> invoice number; commodity `weight` GRAM->KG (3 dp); `sku/manufacturerProductId/standardisedProductId` produce `EU_DE_MINIMIS` regulatory details only when the destination is one of the 27 EU member states (`src/data/eu-member-states.ts`) and `sku` is set. Currency: ISO -> FedEx codes for 15 currencies, notably `GBP`->`UKL`, `JPY`->`JYE`, `CHF`->`SFR` (`:97-120`). `customsValue` and `unitPrice` are both the commodity `value.value` per line (NOT multiplied by quantity); `totalCustomsValue` = sum of those values in the first commodity's currency (`:213-259`; README `:188-189`).
- Spec fields accepted but NEVER read by code: `contentType`, `businessTransactionType`, `descriptionOfGoods`, `whatThreeWords`, address `name`, `shippingLocationId` (read only when `AUTH_ENABLED=false`). Spec `default`s are not applied (`packagingType` defaults in code to `YOUR_PACKAGING`, `pickupType` to `USE_SCHEDULED_PICKUP`). `shipDatestamp` and `pickupDetail` are forwarded verbatim; the spec's Saturday-delivery/pickup rules (Friday/Saturday, GB-only) are NOT enforced by the code (grep finds no day-of-week logic in `apps/fedex-proxy/src`). `format: date` is not validated (README `:22-23`).
- PLT: `PLT:true` adds special service `ELECTRONIC_TRADE_DOCUMENTS` and `etdDetail{requestedDocumentTypes:["COMMERCIAL_INVOICE"]}` (`fedex.service.ts:332-335`). A customs shipment always requests a PDF commercial invoice document (`shippingDocumentSpecification`, `:274-289`) regardless of PLT.
- Request size: body limit 1 MB; over -> 413 (`global-error.ts:8-15`). Malformed JSON -> 400 `Request body is not valid JSON`, evaluated before routing/auth, so no key is needed to get it (`global-error.ts:16-18`, `app.ts:77`; `routes.test.ts:161-168`).
POST /shipping/cancelShipment (`api/fedex-integration-api.yaml:1132-1147`): required `accountNumber` and `shipmentId` (strings; empty strings pass the schema but are rejected in code with 400 `accountNumber and shipmentId (tracking number) are required to cancel a shipment`, `fedex-integration.ts:142-147`). Sent to FedEx as `PUT /ship/v1/shipments/cancel` with `{accountNumber:{value}, deletionControl:"DELETE_ALL_PACKAGES", trackingNumber}`.
Schema errors: 400 `{code:"VALIDATION ERROR", message:"Client request failed validation", details:"Failed to validate client request", metaData:{"0":{instancePath,schemaPath,keyword,params,message}, "1":...}}` (array spread into an object keyed "0","1"..., `exceptions.ts:39-60`, `app.ts:94-99`; test `routes.test.ts:129-150`; a second package yields `keyword:"maxItems"`, `:152-159`).

### Response
createShipment success: 201 `application/json` (`app.ts:88`, mapper `src/services/fedex-create-shipment-response-mapper.ts:58-109`):
`{ shipmentId, secondaryShipmentId, warnings: string[], packages: [ { documents: { label: { labelStream: "<base64>" }, trackingId } } ], documents?: { commercialInvoice: { documentStream: "<base64 PDF>", mustAttachPhysically: boolean } } }`
- `shipmentId` and `secondaryShipmentId` are both FedEx's master tracking number (mock: `9999` + 8 digits, 12 digits). With the one-package limit, `packages[0].documents.trackingId` equals `shipmentId` (`create-shipment.test.ts:30-38`). Cancel uses `shipmentId`.
- `labelStream`: raw base64 (no data-URI). PDF request -> one-page PDF converted from FedEx's 203-DPI PNG at the stock size; PNG request -> FedEx PNG as-is; ZPL requests -> base64 of ZPL text (mock). One label per package (always one).
- `warnings`: FedEx alert messages (all alerts, NOTE and WARNING alike, `:82`), plus a fixed physical-invoice warning (`PHYSICAL_INVOICE_WARNING`, `:44-45`) pushed when a commercial invoice exists and `mustAttachPhysically` is true (`:90-93`).
- `documents.commercialInvoice` is present ONLY when FedEx returned a `COMMERCIAL_INVOICE` shipment document, i.e. when the request had `customs` (`:86-88,100-107`; test `create-shipment.test.ts:90-93`).
- `mustAttachPhysically = completedEtdDetail.type !== "ELECTRONIC_DOCUMENTS_ONLY"` (`:90-91`). `completedShipmentDetail` is only returned by the mock when ETD was requested (`PLT:true`). Therefore: customs without PLT -> `true` + warning (test `create-shipment.test.ts:74-80`); PLT:true -> `false`, `warnings:[]` (`:82-88`); PLT:true + postcode `ETD 0RIG` -> `true` + warning (`:451-454`).
cancelShipment success: 204, empty body (`app.ts:92`; test `cancel-shipment.test.ts:14-17`).

### Error shape
Common body for every proxy error (`exceptions.ts:2-23`, `global-error.ts:44-47`): `{code, message, details}` plus `metaData` only on `VALIDATION ERROR`. `application/json`.
| code | status | when |
| --- | --- | --- |
| `VALIDATION ERROR` | 400 | unknown path/method (`details:"Requested path not found"`, `metaData:{request:{method:"post" (lower-case), path}}`), schema failure, malformed JSON, every lookup/mapping rule. `message` is always `"Client request failed validation"`; `details` carries the specific text. 413 for body > 1 MB. |
| `FORBIDDEN` | 403 | no/unknown key, ApiKy failure (`message:"Authentication failed"`). Note this is the proxy's own code; a FedEx 403 surfaces as `CARRIER SERVER ERROR` 403. |
| `CARRIER SERVER ERROR` | FedEx's status on create/availability errors; 500 for everything else on create; ALWAYS 500 on cancel | `message` and `details` are both the detail string. On create the detail is FedEx's first `errors[0].message`, or `JSON.stringify(body)` when none (`"{}"` for an empty body) (`fedex-integration.ts:107-115`); token failure `Failed to get token: <status> - <body>` (500, `auth.service.ts:78`); FedEx unreachable `fetch failed` (500); 2xx with no `transactionShipments` -> 500 `Client request failed validation` (the mapper throws a ValidationError, which the create `catch` re-wraps as a carrier 500, `fedex-integration.ts:128-135`, `response-mapper.ts:64-69`). |
| `INTERNAL SERVER ERROR` | 500 | `message:"An internal server error occurred"` with `details`=the error text for mapping crashes; `message:"An unexpected error occurred"` for anything unclassified. |
Cancel: every failure is re-wrapped as 500 `CARRIER SERVER ERROR` with detail `Unknown error : <ErrorName>: <message>` (e.g. `Unknown error : CarrierError: Shipment is already cancelled.`; for a missing customer doc `Unknown error : AuthenticationError: Authentication failed`) (`fedex-integration.ts:173-180`; `cancel-shipment.test.ts:32-67`). FedEx's own 4xx/403/404 and "cancelledShipment:false" are all 500. The only cancel 400s are the schema/validation errors and the empty-string check.
Create passthrough statuses: a FedEx 400/401/403/404/500/503 reaches the caller with that same status (e.g. 401 after the single token-refresh retry `auth.service.ts:36-48`, 403 for `fedex-key-rejected-account`, 503 with `details:"{}"`).
Carrier-failure status: FedEx's own status (400/401/403/500/503) on create. There is no 599 here. Differs from the common shape: `code` strings contain spaces (`"VALIDATION ERROR"`, `"CARRIER SERVER ERROR"`, `"INTERNAL SERVER ERROR"`), `metaData` is an object keyed "0","1" (not an array) for schema errors.

### Failure scenarios for D5 (magic values)
Recipient postal code: stripped of ALL whitespace and upper-cased before compare, so `err400`, `ERR  400`, `err 400` all fire (`apps/mock-upstreams/src/fedex/index.ts:66-67,280`). They are checked in mock FedEx AFTER its own label-stock checks (`:267-278`) and AFTER the proxy's validation (service/lane/packaging/PLT/etc.), so a request that fails proxy validation never reaches them.
| operation | field | magic value | where verified | what the caller sees |
| --- | --- | --- | --- | --- |
| createShipment | shipTo.postalCode | `ERR 400` | `mock-upstreams/src/fedex/index.ts:18,281-289` | 400 `CARRIER SERVER ERROR`, message=details=`Recipient postal code or routing code is invalid.` (`create-shipment.test.ts:398-408`) |
| createShipment | shipTo.postalCode | `ERR 401` | `index.ts:290-293`; `auth.service.ts:36-48` | mock FedEx 401 on every ship call; proxy drops the token, refetches (extra `/oauth/token` call), retries once, then returns 401 `CARRIER SERVER ERROR` `Access token expired. Please modify your request and try again.` (`create-shipment.test.ts:410-426`) |
| createShipment | shipTo.postalCode | `ERR 500` | `index.ts:294-297` | 500 `CARRIER SERVER ERROR`, detail = FedEx "We encountered an unexpected error..." text |
| createShipment | shipTo.postalCode | `ERR 503` | `index.ts:298-301` | 503 `CARRIER SERVER ERROR`, `details:"{}"`, `message:"{}"` (`create-shipment.test.ts:433-436`) |
| createShipment | shipTo.postalCode | `NO SHIP` | `index.ts:302-305` | 500 `CARRIER SERVER ERROR`, message/details `Client request failed validation` (not 400) (`:438-441`) |
| createShipment | shipTo.postalCode | `WARN 1NG` | `index.ts:363-372` | 201, `warnings:["Recipient Postal-City Mismatch."]` (plus the physical-invoice warning if a customs invoice needs attaching) (`:443-449`) |
| createShipment | shipTo.postalCode + `PLT:true` + `customs` | `ETD 0RIG` | `index.ts:385-394`; `response-mapper.ts:90-93` | 201, `documents.commercialInvoice.mustAttachPhysically:true` and the physical-invoice warning (`:451-454`). Without `customs`: 400 `PLT requires customs details to be provided` (no invoice). |
| createShipment | shipTo.postalCode, serviceCode `FXGND` (and shipFrom US -> shipTo US) | `NO SVC` | `index.ts:229-241`; store `checkServiceAvailability` from `validations[].validateServiceAvailability` (`fixtures/services.json:38-40`) | 400 `CARRIER SERVER ERROR`, `The requested service is not available between the origin and destination.`; no ship call made (`:456-467`). Only `FXGND` runs the availability check; other services with this postcode succeed normally. |
| createShipment | serviceCode | unknown / disabled (`FXIPF`) / not on list (`FXFF`) | `fedex-store.ts:66-80` | 400 VALIDATION ERROR `No mapping found for service code <X> for customer <name>`, `metaData:{customerId, customer}` |
| createShipment | serviceCode + lanes | `FXUKN` outside GB; `FXIE` to IE; `FXGND`/`FXGHD` not US->US; unknown country | `fedex-service-validation.ts:87-126`, `:63-67` | 400 VALIDATION ERROR `Service FEDEX_NEXT_DAY_END_OF_DAY is not allowed for destination US / NY from origin region EU` etc. |
| createShipment | x-api-key | `fedex-key-inactive` | `fedex-store.ts:82-87` | 400 VALIDATION ERROR `Customer Cobble Fake Traders is not active` |
| createShipment | x-api-key | `fedex-key-no-account` | `mapper:114-119` | 400 VALIDATION ERROR `No account number configured for partner 00000000-0000-4000-8000-0000000fd001` |
| createShipment | x-api-key | `fedex-key-unconfigured` | `fedex-store.ts:66-80`; `servicecode-mapping.service.ts:14-20` | 400 VALIDATION ERROR `No mapping found for service code FXIP for customer 00000000-0000-4000-8000-0000000fe001` |
| createShipment | x-api-key | `fedex-key-rejected-account` (account `MOCKFX999`) | `mock index.ts:192-195` | 403 `CARRIER SERVER ERROR` (not code `FORBIDDEN`), detail `We could not authorize your credentials. Please check your permissions and try again.` |
| createShipment | x-api-key | `fedex-key-malformed-profile` | `fedex-integration.ts:49-51` | 500 `INTERNAL SERVER ERROR` `An unexpected error occurred` |
| any | x-api-key | none / unknown / `apiky-500` | `app.ts:116-123` | 403 `FORBIDDEN` (all three identical) |
| createShipment | labelSpecification | PAPER_* with ZPL (or STOCK_* with PDF/PNG) | `mock index.ts:275-278` | 400 `CARRIER SERVER ERROR`, `Invalid values in Label Stock Type for LABEL` (`create-shipment.test.ts:474-480`) |
| createShipment | package.weight / packagingType | e.g. `FEDEX_ENVELOPE` with 1.2 KG | `fedex.service.ts:122-157` | 400 VALIDATION ERROR `Packaging type FEDEX_ENVELOPE is not allowed for weight 1.2 KG` |
| createShipment | paymentType | `RECIPIENT`/`THIRD_PARTY` without `payor` | `mapper:67-73,168-169` | 400 `Payor is required when paymentType is: THIRD_PARTY` |
| cancelShipment | shipmentId (prefix, case-insensitive) | `UNKNOWN` | `mock index.ts:414-421,68` | 500 `CARRIER SERVER ERROR`, `Unknown error : CarrierError: Tracking number cannot be found. Please correct the tracking number and try again.` |
| cancelShipment | shipmentId | `CANCELLED` | `index.ts:427-436`; `fedex-integration.ts:162-170` | 500 `Unknown error : CarrierError: Shipment is already cancelled.` |
| cancelShipment | shipmentId | `ERR500` | `index.ts:423-426` | 500 `Unknown error : CarrierError: We encountered an unexpected error...` |
| cancelShipment | accountNumber | any not in `MOCKFX001`..`003` (e.g. `MOCKFX999`) | `index.ts:405-408` | 500 (FedEx's 403 is re-wrapped) `Unknown error : CarrierError: We could not authorize your credentials...` (`cancel-shipment.test.ts:51-57`) |
| cancelShipment | x-api-key | `fedex-key-unconfigured` | `auth.service.ts:59-64`; `fedex-integration.ts:173-180` | 500 `Unknown error : AuthenticationError: Authentication failed` (no token without a customer doc) (`cancel-shipment.test.ts:64-67`) |
| cancelShipment | body | `accountNumber` or `shipmentId` missing / empty | schema; `fedex-integration.ts:142-147` | 400 VALIDATION ERROR (missing: schema `metaData`; empty string: `accountNumber and shipmentId (tracking number) are required...`) |
| any | body | malformed JSON / > 1 MB | `global-error.ts:8-18` | 400 `Request body is not valid JSON` / 413 |
Config-time (not caller-controllable): `FEDEX_CLIENT_ID=token-500` -> 500 `Failed to get token: 500 - ...`; wrong client secret -> 500 `Failed to get token: 401 - ...` (`create-shipment.test.ts:483-502`).

### Quirks mirrored from production
- Cancel turns every failure into 500 with `Unknown error : <Name>: <message>`, FedEx 4xx and "not cancelled" included (`fedex-integration.ts:173-180`; README `:185-186`).
- Cancel uses the CALLER's `accountNumber`, not the customer's `fedexAccountNumber` (README `:185`).
- A disabled service, an unlisted service and a customer with no document all read "No mapping found" (README `:187`).
- `customsValue`/`unitPrice` = the commodity value; `totalCustomsValue` sums them without multiplying by quantity (`fedex.service.ts:213-259`).
- The availability check looks only at the HTTP status, not what FedEx quoted (README `:190`).
- `Address.name` never sent to FedEx; `contactName` is the only person name (README `:184`).
- PDF labels are really FedEx PNGs at 203 DPI converted to PDF (`fedex.service.ts:45-71`; `response-mapper.ts:47-56`).
- Dimensions rounded to whole numbers; Ground Home Delivery forces `residential:true`; `YOUR_PACKAGING` limit rises to 68 kg for service names containing "express" (`mapper:126-128,156-161`; `fedex.service.ts:130`).
- Source defects kept: `ValidationError` spreads Ajv's errors array into an object keyed "0","1" (`exceptions.ts:48-49`); method in the not-found `metaData` is lower-case.
- 401 handling: one token refresh and one retry on a FedEx 401, then the 401 is returned (`auth.service.ts:36-48`). Tokens cached per shipping account until 60 s before expiry (`:83-88`).
- A FedEx 2xx with an empty `transactionShipments` is a carrier 500, not 400 (`NO SHIP`).
- ApiKy failure and key failure collapse to the same 403 (unlike coll8's 401/403/500).
- Spec defaults not applied; `stateOrRegion` stays required; exactly one package (`maxItems:1`) (README `:191-193`).
- Statefulness: none; mock FedEx stores nothing (README `:136-139`).

### Statefulness / ordering constraints
- No shipment store anywhere; cancel does not require a prior create. Any tracking number not starting with `UNKNOWN`/`CANCELLED`/`ERR500` cancels successfully, including never-created ones and repeated cancels of the same number (`mock index.ts:403-441`). Cancel twice succeeds twice.
- Per-instance state: the FedEx token cache keyed by shipping account (`auth.service.ts:27`). Mock tokens are valid on any mock instance (README `:136-138`).
- create is not idempotent (new tracking number each call). The proxy retries only the single 401 case; a second create is the caller's choice.
- Account for cancel is whatever is sent in the body; there is no tie to the account that created the shipment.
- Availability pre-check (only `FXGND`) happens before the ship call: two upstream calls, ordered (`create-shipment.test.ts:253-257`).

### Adapter implications and leaks
- Supports create-ship and cancel only; validate, commit-manifest, reprint and track must be capability-flagged as absent. Manifest in particular does not exist; a generic "commit manifest" must be a no-op or unsupported for fedex.
- One package per request (`maxItems:1`); multi-parcel orders need one call per parcel (or the adapter must reject).
- Cancel needs the FedEx account number (the customer's `fedexAccountNumber`, e.g. `MOCKFX001`) plus the `shipmentId`; the adapter must store/know the account number, which is not returned by create. Wrong account -> 500, indistinguishable from "already cancelled" except by the detail text.
- Success statuses differ from other carriers: create is 201, cancel is 204 with no body.
- All cancel failures are 500 with the failure reason only in `details` text (parse `Unknown error : CarrierError: ...`); cannot be classified by status.
- Create failures: carrier-side failures keep FedEx's status; validation failures are 400 `VALIDATION ERROR` with human text in `details`; the `metaData` is not an array. Auth is always 403 `FORBIDDEN`, even for an ApiKy outage, so a transient ApiKy failure looks like a bad key.
- Service-code semantics are per customer and need a lane: origin and destination country/state are mandatory in practice (even though the spec leaves `countryCode` optional); `stateOrRegion` is required (empty string allowed). Unknown countries fail 400 for every service.
- Label: caller chooses `labelFormat` + a paired `labelStockType` (PAPER_* for PDF/PNG, STOCK_* for ZPL); there is no EPL via the spec; base64 in `packages[0].documents.label.labelStream`.
- Customs: customs invoice is a separate base64 PDF at `documents.commercialInvoice.documentStream`; `mustAttachPhysically` and the injected warning string must be surfaced; PLT requires `customs` or 400.
- Weight units: GRAM/KILOGRAM/POUND accepted (GRAM converted); dimension unit required in practice; dimensions rounded.
- Warnings are plain strings in `warnings[]` (FedEx alerts, including NOTE-type ones).
- `shipDatestamp`, `pickupDetail`, Saturday services are passed through without proxy-side checks; real FedEx would enforce them (mock FedEx does not).

### README-vs-source discrepancies, and UNVERIFIED
- README (`:77`) says `fedex-key-unconfigured`: "cancel is 500 (no token without a document)": consistent with source, detail text `Unknown error : AuthenticationError: Authentication failed`.
- README "Other values" (`:123-124`) says a FedEx account other than `MOCKFX001-003` gives "403 `FORBIDDEN.ERROR`" on create AND cancel. True upstream; the caller sees 403 `CARRIER SERVER ERROR` on create but a 500 on cancel (re-wrapped), which README states only implicitly (`:185-186`).
- README `:39` says `INTERNAL SERVER ERROR` is "an unexpected error while mapping"; also fires for the key `fedex-key-malformed-profile` via the generic unclassified path.
- README `:34` lists "Any lookup or mapping rule below" as 400; the `NO SHIP`/carrier-shaped 500 `Client request failed validation` looks like a validation error but is a CARRIER 500 (README `:38` is correct).
- Spec says `customs` optional; TS type `customs: CustomsInput` required (`fedex.service.types.ts:208`); code treats it as optional.
- Spec describes Saturday delivery/pickup preconditions (Friday ship date, GB domestic, Saturday pickup date); source has no such checks.
- Spec `countryCode` is optional but is required in practice; spec `dimensions.unit` optional but required in practice.
- Spec enums exclude EPL; code supports `EPL2` mapping internally.
- UNVERIFIED: whether openapi-backend coerces types (e.g. numeric `accountNumber`); behaviour for non-JSON content-type on create (req.body would be `{}` and schema fails with 400, derived not tested); real-FedEx behaviour of any mapped field (README says logic ported from source, mock FedEx is invented); whether Cloud Run IAM consumes a caller Bearer; service table contents in production (fixtures are invented codes).

### Notes for the E2 draft
- Line 54 ("`fedex-key-alpha` (cancel with account `MOCKFX001`)"): correct; add that any known mock account (`MOCKFX001-003`) works in the cancel body regardless of which key is used, and that `fedex-key-bravo` creates only `FXIP`.
- Line 68: fedex "403 / 403 / 403" is correct (all three are the same `FORBIDDEN` body, including `apiky-500`).
- Line 112 (`NO SHIP` -> "500 'Client request failed validation'"): correct; add that it is a `CARRIER SERVER ERROR` body, not a 400 `VALIDATION ERROR`.
- Line 114 (`ETD 0RIG` with `PLT: true`): correct but `customs` must also be present (else 400 `PLT requires customs details to be provided`); without PLT, any customs shipment already returns `mustAttachPhysically:true`.
- Line 115 (`NO SVC` with `FXGND`): correct; the request must also be a US-origin to US-destination lane (FXGND only allows that) or it fails earlier with a 400 VALIDATION ERROR; the failure body is `CARRIER SERVER ERROR` 400 with FedEx's message.
- Line 116 (cancel prefixes -> 500): correct; add that wrong/unknown `accountNumber` and `fedex-key-unconfigured` also 500 and that "already cancelled" only fires via the `CANCELLED` prefix (cancelling the same real id twice succeeds).
- Line 117-118: correct (400 `VALIDATION ERROR` for inactive/no-account; `fedex-key-rejected-account` -> 403 `CARRIER SERVER ERROR`). Omitted but real: `fedex-key-unconfigured` (create 400 "No mapping found", cancel 500) and `fedex-key-malformed-profile` (500 `INTERNAL SERVER ERROR`).
- Line 111 (`ERR 401`): correct; the resulting body is a 401 `CARRIER SERVER ERROR`.
- Line 183 (malformed JSON gives 500 on several mocks): fedex is 400 `VALIDATION ERROR` (`Request body is not valid JSON`).
- Line 179 (weights): fedex converts GRAM correctly (divide by 1000, 3 dp) and POUND->LB; no quirk to list.
- Not covered by the draft: the fixed one-package limit (a second package is a 400 schema error with `keyword:"maxItems"`), 201/204 success statuses, and absence of validate/manifest/reprint.


---

## dpdeu (DPD Europe proxy: DPD Germany + DPD Netherlands; apps/dpd-europe-proxy; mirrors dpd-eu.gfsdeliver.com)

All paths below are relative to repo root, lines from origin/main. Port 4105 (`apps/dpd-europe-proxy/src/config.ts:23`).

### Operations and routes

| Operation | METHOD path | Supported? | Notes |
| --- | --- | --- | --- |
| create-ship (label) | POST `/shipping/createLabel` | YES, the only business route | One call = ApiKy lookup, optional DPD login, SOAP `storeOrders`, label split. `src/app.ts:87-92`, `src/labelling.ts:54-111` |
| validate | none | NO | No dry-run/validate mode. The joi `validator.ts` is an internal pre-check on the create path, not an operation |
| delete / cancel | none | NO | No cancel route; `/shipping/<anything else>` hits the catch-all 200 OK body (`app.ts:94-96`) |
| commit / manifest | none | NO | |
| reprint | none | NO | |
| track | none | NO | |
| health | GET `/health/liveness` | yes, no auth | `200 {"ok":true}`; registered before request-id, request log, auth (`app.ts:78-80`). Not in the source |
| catch-all | any method, any other path | yes | `200 {"code":200,"message":"OK","detail":"Server is OK and ready to handle requests"}` (`app.ts:94-96`); but any path under `/shipping` needs a valid key first (`app.ts:88`), no key gives 401 (`test/routes.test.ts:66-75`) |
| wrong method on label path | GET/PUT/... `/shipping/createLabel` | no | Key check first (no key: 401), then 500 generic (not 405) (`app.ts:43-54, 89-91`; `test/routes.test.ts:143-146`) |

Pipeline order for POST `/shipping/createLabel` (`app.ts:76-92`, `labelling.ts:54-68`):
1. `express.json()` (malformed JSON gives 400 `SYNTAX_ERROR`, even with no key).
2. Spec validation (content-type, then JSON-schema) gives 400 `VALIDATION_ERROR`. **Runs before auth**, so a bad body with no key is 400, not 401.
3. ApiKy on `/shipping/*`: no key 401, ApiKy 4xx 403, ApiKy 5xx/unreachable 500.
4. Controller: joi `postLabellingValidator` gives 400 `VALIDATION`.
5. Customer lookup `{company, provider}` gives 403 `FORBIDDEN`.
6. Token (cache or login), SOAP `storeOrders`, split, 200.

### Auth and headers

- Header: `x-api-key` only (case-insensitive header name). `src/middlewares/apiky.ts:9`. Spec also names it `X-API-Key` (`api/swagger.yaml:13-17`).
- `Content-Type: application/json` required on the POST. Missing/other content type is a spec-validation 400 (see Error shape). `charset` suffix is tolerated (split on `;`, `spec-validator.ts:31`).
- Cloud Run `Authorization: Bearer ...`: never read by any proxy code (no `authorization` reference in `apps/dpd-europe-proxy/src`; grep). Ignored. The mock-edge service is public (`allUsers`, `iac/projects/mock-dpdeu/cloud-run.tf:54-60`). UNVERIFIED: whether Cloud Run's own frontend rejects a malformed Bearer on a public service.
- Key fixtures (`apps/mock-upstreams/fixtures/apiky/dpdeu.json`; DPD logins in `apps/dpd-europe-proxy/fixtures/customers.json`, passwords elided):

| `x-api-key` | ApiKy company | DPD logins held | Effect |
| --- | --- | --- | --- |
| `dpdeu-key-alpha` | `MOCK-DPDEU-ALPHA` | DE `mockde-alpha`, NL `mocknl-alpha` | works for both providers |
| `dpdeu-key-bravo` | `MOCK-DPDEU-BRAVO` | DE `mockde-bravo` only | `serviceProvider: "DPD NL"` gives 403 FORBIDDEN |
| `dpdeu-key-bad-login` | `MOCK-DPDEU-CHARLIE` | DE + NL, wrong passwords | DPD login fault gives 500 generic |
| `dpdeu-key-no-password` | `MOCK-DPDEU-DELTA` | DE, empty password | 500 generic, no DPD call (`token-manager.ts:37-38`) |
| `dpdeu-key-revoked-token` | `MOCK-DPDEU-ECHO` | DE + NL | seeded stale cached tokens (`fixtures/tokens.json`; values start `mock-dpd-`, not the issued `mockdpd-` format) so first storeOrders is rejected, proxy re-logs-in and resends: caller sees 200 |
| `dpdeu-key-no-company` | none (profile `{}`) | none | company undefined gives 403 FORBIDDEN (`store.ts:23-24` eq(undefined,..)) |
| `apiky-500` | | | mock ApiKy 500 gives proxy 500 generic |
| anything else | | | mock ApiKy 403 gives proxy 403 |

- ApiKy lookup (`packages/apiky-client/src/index.ts:31-43`): `GET {APIKY_BASE_URL}/api/profile?token=<caller key>` with service key header; non-2xx throws `ApiKyError(status)`, network error becomes status 500.
- Responses:
  - No `x-api-key`: 401 `{"message":"No API key provided"}` (`apiky.ts:10-13`).
  - ApiKy any status other than exactly 500 (401/403/404, and also 502/503): 403 `{"message":"Not authorised"}` (`apiky.ts:18-25`, only `status === 500` takes the error path).
  - ApiKy 500 or unreachable: falls to error handler: 500 `{"code":"INTERNAL_SERVER_ERROR","message":"Internal Server Error","details":"An internal server error has occured."}` (`error-handler.ts:19-22`; `test/routes.test.ts:54-64`).
  - Profile with no `profile` block at all: `profile.profile.company` destructure throws TypeError inside try, so 500 generic (`labelling.ts:56-60`). UNVERIFIED by test; derived from code. Not reachable with fixtures (the `no-company` fixture has `"profile": {}`).
- Auth/error bodies of 401/403 are `{message}` only (no `code`), unlike all other errors (`{code,message,details}`).
- All JSON is pretty-printed (2-space) with `Content-Type: application/json` (no charset) via `writeJson` (`middlewares/writer.ts:4-7`).

### Request

Body is validated against `api/swagger.yaml` `CreateLabelRequest` (Swagger 2.0, z-schema 6; `ignoreUnknownFormats`; no `additionalProperties:false`, so unknown keys pass).

Required top level (`swagger.yaml:58-65`): `serviceProvider`, `labelSpecification`, `consignment`, `packages`, `shipFrom`, `shipTo`, `serviceType`. Optional: `customs`, `serviceOptions`.

| Field | Spec | What code actually reads |
| --- | --- | --- |
| `serviceProvider` | enum `"DPD DE"`, `"DPD NL"` (exact, case-sensitive) (`:89-93`) | selects SOAP client (`soap/index.ts:21-25`) and the customer row (`labelling.ts:62,67`) |
| `labelSpecification.labelFormat` | required, enum `ZPL`, `PDF`, `PNG` (`:94-104`) | DE: `printOptions.printOption[0].outputFormat`, NL: `printOptions.printerLanguage`; `PNG` is sent to DPD as `PDF`; `paperFormat: 'A6'` fixed (`dpd-de/map.ts:15-22`, `dpd-nl/map.ts:12-14`). No resolution/size param |
| `consignment.weight` | `{unit: GRAM or KILOGRAM, value: number}`, both required (`:105-121`; note `Consignment` has no `type: object`) | `getWeight` (`soap/shared.ts:82-100`) |
| `packages` | array, min 1, max 999 (`:73-78`); each requires only `packageClientReferenceId` (string, max 35) | see below |
| `packages[].dimensions` | **optional in spec**; if present: `length,width,height` number 1..999, `unit` enum `CENTIMETER` only, all four required | **required by code**: `getVolume(parcel.dimensions)` on undefined throws TypeError, 500 generic (`dpd-de/map.ts:55`, `dpd-nl/map.ts:49`; README line 68). Test pins this only for `serviceOptions` (`test/create-label.test.ts:135-139`) |
| `packages[].description` | string max 35 | NL only, as `customsContent` of the first parcel's international block (`dpd-nl/map.ts:86`); DE ignores |
| `packages[].invoiceNumber` | string max 20 | `packages[0].invoiceNumber` becomes customs invoice for non-EU international; joi requires it on EVERY package for non-EU international |
| `packages[].packageClientReferenceId` | required, max 35 | `parcels[].customerReferenceNumber1` |
| `serviceType` | enum `E10,E12,E18,B2B,CL` (`:282-290`) | DE: `B2B` sent as `CL` (`dpd-de/map.ts:28`); NL: passed as is (`dpd-nl/map.ts:20`) |
| `serviceOptions.saturdayDelivery` | optional boolean | **object required by code**: `data.serviceOptions.saturdayDelivery` on undefined throws, 500 generic (`dpd-de/map.ts:59`, `dpd-nl/map.ts:53`; pinned `test/create-label.test.ts:135-139`) |
| `shipFrom` / `shipTo` | `Address`: required `name, addressLine1, city, postalCode, countryCode` (`:216-224`) | see Address below |
| `customs.commodities[]` | `customs` optional; if present `commodities` required min 1; each requires `quantity` (integer >=1), `description` (max 80), `hsCode` (max 8), `value{currency (exactly 3 chars), value 0..99999}`, `weight{unit GRAM or KILOGRAM, value >=0}` (`:161-215`) | see Customs |

Address (`swagger.yaml:216-281`): `name` 1..35; `companyName` <=35; `addressLine1` 1..35; `addressLine2` **minLength 1** (empty string rejected, omit instead), <=35; `state` <=2 chars (full state names fail); `city` 1..35; `countryCode` exactly 2 chars (no pattern; case not enforced); `postalCode` 1..**9** chars; `email` <=50 (no format); `phoneNumber` **minLength 1**, <=30; `vat` <=30; `eori` <=30. No `null` anywhere (Swagger 2.0 has no nullable): `null` gives `Expected type string but found type null at <path> in request body` (`test/routes.test.ts:114-120`).

Units/encodings:
- Weight units: only `GRAM` / `KILOGRAM` (Selector-style `KG` fails the spec: `No enum match for: KG at consignment.weight.unit in request body`, `test/routes.test.ts:98-104`). Dimension unit: only `CENTIMETER`. Currency: free 3-char string, passed through. Country: 2-char, passed through; `customsOrigin` for DE is `countries.alpha2ToNumeric(shipFrom.countryCode)` (`dpd-de/map.ts:99`), NL passes alpha-2 (`dpd-nl/map.ts:96`).
- Weight mapping (`soap/shared.ts:82-100`): single consignment weight is averaged over parcels: `avg = value*qty/numParcels`. `GRAM`: `Math.ceil(avg/10)` decagrams (always an integer). `KILOGRAM`: `avg*100` **unrounded**. DE additionally sends `mpsWeight` = whole consignment (`numParcels: 1`) (`dpd-de/map.ts:25`); NL sends none. Mock DPD requires `mpsWeight`, `weight`, `volume` to match `^\d+$` (`mock-upstreams/src/dpd/index.ts:99, 235-245`), so `KILOGRAM 1.1` gives `110.00000000000001` and a 400 `SCHEMA_ERROR` (`test/create-label.test.ts:127-133`). Also fails: `0.07 kg` (`7.000000000000001`), `1.15 kg` (`114.99999999999999`, derived by arithmetic), any kg value / parcel count that is not a clean multiple. Negative weight also fails (`-` not matched). **Safe path: send GRAM.**
- Volume (`shared.ts:102-109`): `LLLWWWHHH` cm, each side `Math.ceil`ed, `('0'+n).slice(-3)`; a side under 10 renders two digits (`5` gives `05`, so `5x5x5` is `050505`, `1x1x1` is `010101`); 10..99 give 3 digits (`030`); 100..999 give 3 digits. Unit other than CENTIMETER throws (unreachable, spec enum).
- Money (`shared.ts:79`): `toFixed(2)` with the dot removed (`12.5` gives `1250`); commodity values summed for customs amount; currency of first commodity.
- Dates: `customsInvoiceDate` is `yyyyMMdd` of the server's local "now" (`shared.ts:60-63`); no date input from caller.
- Label encodings: see Response.

Address cleanup: `normalize()` (`shared.ts:65-76`) drops undefined/null/'' and trims strings, recursively, for `sender` and `recipient`; the whole order is also normalised at the end, EXCEPT when the delivery has `commodities` AND is same-country or EU-to-EU: then `return mapped` early, un-normalised beyond the per-address pass (`dpd-de/map.ts:69-71`, `dpd-nl/map.ts:63-65`). A whitespace-only required address field passes the spec, is trimmed to empty and dropped, so DPD gives `COMMON_7` (`Mandatory field 'recipient/name1' is missing.`).

DE vs NL mapping differences (carrier-selection quirks the adapter cannot see):
- DE does NOT send `addressLine2` (no `street2`); NL does (`dpd-de/map.ts:29-50` vs `dpd-nl/map.ts:21-44`).
- Predict (email notification block, channel `1`, language `en`) is added whenever `shipTo.email` is set; DE skips it for `B2B` (`dpd-de/map.ts:64-66`), NL always adds (`dpd-nl/map.ts:58-60`).
- Customs (non-domestic, non-EU, `commodities.length > 0` only): DE puts `international` on `productAndServiceData` (`customsTerms '06'`, per-line `customsOrigin` numeric, only `shipFrom.vat` used, `eori` ignored); NL puts `international` on `parcels[0]` with `exportReason '01'`, copies `vat`/`eori` onto the sender, uses alpha-2 origin. Commodity lines can't be tied to a parcel, so only single-parcel customs is meaningful (comment `dpd-de/map.ts:68`).
- DE reads `shipmentResponses[].faults`; NL never does (`dpd-nl/map.ts:108`).

Validator (`src/validator.ts`, joi 17.13.3; run at `labelling.ts:64-65`, after spec validation and ApiKy). Options: `abortEarly: true`, label wrap `[]`, `stripUnknown` (`validator.ts:6-10`). Exactly what it checks, in order (joi validates keys in schema order, then the object-level custom rule):

1. `shipFrom` required object: `phoneNumber` (optional, `.allow('', null)`) then `countryCode` (required string).
2. `shipTo`: same.
3. `customs` optional object with optional `commodities` array; `packages` array of objects with optional `invoiceNumber` (`.allow('', null)`).
4. Object-level `bodyValidator` (`:20-45`): if `shipFrom.countryCode === shipTo.countryCode` (exact string equality) pass; else if `euMember(to) && euMember(from)` pass; else (international, non-EU on either side) require `customs.commodities.length > 0` (else `customs.commodities is required for international deliveries`), then every `packages[i].invoiceNumber` truthy (else `packages[i].invoiceNumber is required for international deliveries`, first failing index only).

Phone rule (`isPhone`, `:47-54`): applies only when the value is a non-empty string (`''` and `null` skip it via `.allow`; absent skips). Fails when `value.includes(' ')` (ASCII space only) OR `!value.startsWith('+')`. Message: `<path> must be a valid phone number with international prefix (+)` where path is `shipFrom.phoneNumber` or `shipTo.phoneNumber`. No digit-count, no E.164 regex: `+`, `+44-7700-900000`, `+447700900000` all pass; `01000000000`, `00447700900000`, `(+44)7700900000`, `+44 7700 900000` fail. Only the FIRST error is reported (abortEarly, and `QueryValidationError` takes `details.pop()`, `errors.ts:21-25`); `shipFrom` is checked before `shipTo`, so a bad `shipFrom` phone masks a bad `shipTo` phone.

What Selector-shaped input passes or fails (through HTTP, i.e. after the spec stage):

| Input | Result |
| --- | --- |
| phone omitted on both | passes validator (and spec) |
| phone `''` | rejected earlier by the SPEC (`minLength: 1`), 400 `VALIDATION_ERROR`, `String is too short (0 chars), minimum 1 at shipTo.phoneNumber in request body` (same form as `test/routes.test.ts:106-112`; derived for phoneNumber). The joi `.allow('')` is unreachable over HTTP |
| phone `null` | rejected earlier by the SPEC: `Expected type string but found type null at shipTo.phoneNumber in request body` (derived from `test/routes.test.ts:114-120`) |
| national format `01000000000` | 400 `VALIDATION` / `A validation error has occurred.` / details `shipFrom.phoneNumber must be a valid phone number with international prefix (+)` (`test/routes.test.ts:149-161`; `test/validator.test.ts:48-53`) |
| `+44 1234 567890` | same 400 (space) (`test/validator.test.ts:41-46`) |
| `+441234567890` | passes |
| shipFrom `GB` to shipTo `DE`/`NL`, no `customs` | 400 `VALIDATION` details `customs.commodities is required for international deliveries`: GB is **not** EU (`test/validator.test.ts:88-95`). A UK Selector site shipping to DPD DE/NL hits this on every call unless customs + per-package `invoiceNumber` are sent |
| `NL`/`DE` to `FR` etc. (both EU) | no customs needed (`test/validator.test.ts:81-86`) |
| same country | no customs needed |
| non-EU with `customs` but a package lacking `invoiceNumber` | 400 `VALIDATION` `packages[0].invoiceNumber is required for international deliveries` |
| `countryCode` missing | caught by the spec first (`Missing required property: countryCode ...`); the joi `[shipTo.countryCode] is required` message is unreachable over HTTP |
| lowercase `countryCode` (`de`) | spec passes (length 2 only); joi equality is case-sensitive; `euMember('de')` UNVERIFIED (package `is-european@1.0.4`, `apps/dpd-europe-proxy/package.json:20`, source not in repo; tests use uppercase only). Send uppercase alpha-2 |

Conclusion on the handover claim ("DPD Europe's validator probably rejects every Selector call"): true of the code only if Selector sends a phone that is non-empty and national-format or space-containing on `shipFrom` or `shipTo` (shipFrom phone is the same every call, so it would fail every call), or ships from GB to DE/NL without customs. A call with no phone numbers and both countries EU (or same) passes. The README says this is read from code, not production logs (`README.md:129-131`); whether real Selector sends such numbers is UNVERIFIED here.

### Response

Success: `200` (the swagger says 201 but the code sends 200 via `writeJson(res, 200, ...)`, `labelling.ts:51`; README lines 24-25).

```
{ "packages": [ { "trackingId": "<parcel number>", "documents": "<base64>" }, ... ] }
```
- One entry per parcel, in DPD's parcel-number order (`labelling.ts:34`). `trackingId` = DPD `parcelLabelNumber`; the mock makes 14 digits: DE prefix `09981`, NL `05221` + 9 random digits (`mock-upstreams/src/dpd/index.ts:51,60,285-287`).
- `documents`: a **string** (not an object), base64, no data-URI prefix, one label per parcel:
  - `PDF`: single-page PDF per parcel (`pdf-lib` copy of each page, author `GFS`, `label-splitter.ts:15-29`).
  - `ZPL`: base64 of one `^XA ... ^XZ` block per parcel (`label-splitter.ts:6-13`).
  - `PNG`: proxy asks DPD for PDF, POSTs the whole multi-page PDF to the PDF converter `POST {root}/pdfconverter/stream?scale=874` (`Content-Type: application/pdf`, `Accept: multipart/form-data`), every non-string multipart part becomes one base64 PNG (`pdfconverter-service.ts:3-4,10-31`). Mock PNG is a 288x432 greyscale placeholder (`mock-upstreams/src/coll8/png.ts:13`), scale param ignored by the mock.
- DPD returns ONE document for the whole shipment (DE `orderResult.output.content`; NL `orderResult.parcellabelsPDF`, which holds ZPL too when ZPL was requested); the proxy splits it and pairs labels to parcel numbers **by position**. A count mismatch is only logged (`labelling.ts:26-32`); the extra/missing `documents` key is then absent (undefined dropped by JSON.stringify).
- No customs/invoice documents are returned, no warnings array, no shipment id (nothing to cancel).
- Unknown `labelFormat` would return the document unsplit (`label-splitter.ts:40-41`), unreachable (spec enum).

### Error shape

All proxy-originated errors except 401/403 key errors: pretty-printed `{ "code", "message", "details" }`, `Content-Type: application/json` (`error-handler.ts:54`). `details` is omitted when undefined (so DPD-fault errors are `{code, message}`).

| Case | Status | `code` / `message` / `details` |
| --- | --- | --- |
| no key | 401 | `{"message":"No API key provided"}` |
| ApiKy non-500 failure | 403 | `{"message":"Not authorised"}` |
| spec failure | 400 | `VALIDATION_ERROR` / `Request failed schema validation` / `<first z-schema message> at <dotted path> in request body` (body root path is empty, so two spaces: `Missing required property: serviceProvider at  in request body`, `test/routes.test.ts:89-96`). Only the first error is reported (`error-handler.ts:39`) |
| content-type not `application/json` (or absent) | 400 | `VALIDATION_ERROR` / `Request failed schema validation` / `undefined at undefined in request body` (`spec-validator.ts:31-35` plus `error-handler.ts:39-43`; `test/routes.test.ts:122-129`) |
| malformed JSON | 400 | `SYNTAX_ERROR` / `The request body is invalid` / the JSON parser message (`error-handler.ts:24-29`; `test/routes.test.ts:131-141`). Note: unlike amazon-sfp (500) |
| joi validator | 400 | `VALIDATION` / `A validation error has occurred.` / the one joi message |
| no customer for (company, provider) | 403 | `FORBIDDEN` / `No access for provider` / `Your company does not have access to use DPD NL. Please contact support.` (provider interpolated) (`errors.ts:3-14`) |
| DPD validation fault (DE `detail.faults.{faultCode,message}`; or DE `shipmentResponses[].faults[0]`) | 400 | `code` = DPD fault code UPPER-CASED, `message` = DPD message, no `details` (`errors.ts:73-90`) |
| any SOAP fault with only `faultcode`/`faultstring` | 400 | `SCHEMA_ERROR` / `faultstring` minus `System.Web.Services.Protocols.SoapException:`, trimmed, first line (`split('\r\n')`) / no details (`errors.ts:92-106`) |
| DPD login failure, undecryptable (empty) password, unknown fault shape, DPD HTTP 500 / non-SOAP body | 500 | `INTERNAL_SERVER_ERROR` / `Internal server error` / `An internal error has occured. If the error persists please contact support` (`errors.ts:42-52,59-71,108-120`) |
| PDF converter failure (non-2xx or unparsable multipart) | 500 | `PDF_CONVERSION_ERROR` / `An error has occured while converting the PDF label to PNG` / the converter's response text (a JSON string, mock: `{"message":"PDF conversion failed"}`) (`errors.ts:29-40`) |
| anything else (TypeError from missing `serviceOptions`/`dimensions`, wrong method, ApiKy outage, ZPL/PDF parse failure) | 500 | `INTERNAL_SERVER_ERROR` / `Internal Server Error` (capital S) / `An internal server error has occured.` (`error-handler.ts:19-22`) |

Carrier-failure status: 400 for DPD business/schema faults, 500 for everything infrastructural. Typos kept on purpose: `occured`. The 500 message casing differs between the two generic 500 families (`Internal server error` vs `Internal Server Error`).

**NL oddity:** NL's validation fault carries `{faultCode, faultstring}` in `detail.faults`, the proxy tests `faultCode && message`, so NL validation faults fall to the generic branch: 400 `SCHEMA_ERROR` with DPD's top-level `faultstring` (`dpd-nl/index.ts:22-27,35-37`; `test/create-label.test.ts:172-178`). Same business error is `COMMON_7` on DE but `SCHEMA_ERROR` on NL.

### Failure scenarios for D5 (magic values)

Magic = `shipTo.postalCode`, compared after removing ALL whitespace and upper-casing (`mock-upstreams/src/dpd/index.ts:67-68`), so `flt400`, `FLT  400`, `Flt 400` all fire. Max 9 chars (spec) so all fit. Applies to both DE and NL. Checks run in this order inside mock DPD (so earlier failures mask magic zips): token, print format, orders count, parcels total >99, mandatory fields, orderType, product, parcel count, integer weights/volumes, then the magic zip (`index.ts:157-283`).

| Operation | Field | Magic value | Where verified | What the caller sees |
| --- | --- | --- | --- | --- |
| create | `shipTo.postalCode` | `FLT 400` | `mock-upstreams/src/dpd/index.ts:35,248-257`; `test/create-label.test.ts:101-107,172-178` | DE: 400 `{code:"COMMON_7", message:"The zip code is not valid for the destination country."}`. NL: 400 `{code:"SCHEMA_ERROR", message:"The zip code is not valid for the destination country."}` |
| create | `shipTo.postalCode` | `SCH 400` | `index.ts:36,258-265`; `test/create-label.test.ts:109-112,180-185` | 400 `SCHEMA_ERROR`; DE message `Unmarshalling Error: The 'zipCode' element is invalid - The value is invalid according to its datatype.`; NL same minus prefix, first line only (derived from `index.ts:81-91`, `errors.ts:99-101`) |
| create | `shipTo.postalCode` | `ERR 500` | `index.ts:37,266-272`; `test/create-label.test.ts:122-125` | DPD returns HTTP 500 + HTML; proxy 500 `INTERNAL_SERVER_ERROR` (`Internal Server Error` generic family: `client.ts:77` throws plain Error) |
| create | `shipTo.postalCode` | `SHP FLT` | `index.ts:38,273-282`; `test/create-label.test.ts:114-120,187-190` | DE: 400 `{code:"SHIPMENT_1", message:"The shipment was rejected."}`. NL: 500 `INTERNAL_SERVER_ERROR` (TypeError, NL never reads faults) |
| create | `shipTo.postalCode` + `labelFormat: "PNG"` | `PNG 500` | `index.ts:39,283,322-325`; `labels.ts:4-5,37`; `test/create-label.test.ts:141-148` | 500 `{code:"PDF_CONVERSION_ERROR", message:"An error has occured while converting the PDF label to PNG", details:"{\"message\":\"PDF conversion failed\"}"}`. With PDF or ZPL requested: normal 200 (marker only matters to the converter) |
| create | `consignment.weight` | KILOGRAM with fractional product (`1.1`) | `index.ts:99,235-245`; `shared.ts:94-96`; `test/create-label.test.ts:127-133` | 400 `SCHEMA_ERROR`, DE message `Unmarshalling Error: The 'mpsWeight' value '110.00000000000001' is not a valid integer.`; NL names `weight` (derived) |
| create | `packages` length | > 99 parcels | `index.ts:43,178-187`; spec allows 999 | 400 DE `COMMON_9` / `At most 99 parcels are allowed per request.`; NL `SCHEMA_ERROR` with that message (derived; per README) |
| create | `shipTo.name`/`addressLine1`/`city`/`postalCode` etc. | whitespace only (`"   "`) | `index.ts:195-213`; `shared.ts:65-76` | DE 400 `COMMON_7` `Mandatory field 'recipient/name1' is missing.` (path varies); NL `SCHEMA_ERROR` with same text (derived) |
| create | `serviceType` | product not offered by country | `index.ts:218-222` | `COMMON_8`. **Unreachable through the proxy with shipped fixtures**: DE offers CL,E10,E12,E18 and `B2B` is rewritten to `CL`; NL offers all five (`fixtures/dpd/dpd.json`). UNVERIFIED that this could ever fire |
| create | `x-api-key` | `dpdeu-key-bravo` + `serviceProvider: "DPD NL"` | `customers.json`; `test/create-label.test.ts:193-204` | 403 `FORBIDDEN` / `No access for provider` / `Your company does not have access to use DPD NL. Please contact support.` |
| create | `x-api-key` | `dpdeu-key-no-company` | `dpdeu.json:24-27`; `test/create-label.test.ts:206-209` | 403 `FORBIDDEN` (details `...use DPD DE...` or whichever provider) |
| create | `x-api-key` | `dpdeu-key-bad-login` | DPD `badLogin` fault `LOGIN_8` (DE) / `ERR_DELICOM_LOGIN_FAILED` (NL) (`index.ts:54,62`); `test/create-label.test.ts:211-221` | 500 generic `Internal server error` / `An internal error has occured. ...` |
| create | `x-api-key` | `dpdeu-key-no-password` | `token-manager.ts:37-38`; `test/create-label.test.ts:223-226` | 500 same body, zero DPD calls |
| create | `x-api-key` | `dpdeu-key-revoked-token` | `tokens.json`; `index.ts:71-72,139-146`; `test/create-label.test.ts:96-99,167-170` | 200 success. Internally: storeOrders (rejected) + login + storeOrders = 2 order calls. The retry is once per (username, provider) per proxy INSTANCE (cache is in memory, `store.ts:26-30`, README lines 120-121), so only the first call per instance |
| any | `x-api-key` | `apiky-500` | `mock-upstreams/src/apiky/index.ts:37-40`; `test/routes.test.ts:54-64` | 500 `INTERNAL_SERVER_ERROR` / `Internal Server Error` / `An internal server error has occured.` |
| any | `x-api-key` | any unknown value | `apiky/index.ts:41-45` | 403 `{"message":"Not authorised"}` |
| any | `x-api-key` | header absent, valid body | `apiky.ts:10-13` | 401 `{"message":"No API key provided"}`; with an invalid body: 400 `VALIDATION_ERROR` (spec first) |

### Quirks mirrored from production

- Spec validation BEFORE auth (`app.ts:87-88`): smoke script knows this (`scripts/smoke.mts:416-424` sends a valid body for the keyless check).
- Status 200 not 201; spec `maxItems: 1` on response packages is wrong and not enforced (`swagger.yaml:291-309`).
- Weight: KILOGRAM `value*100` with no rounding gives non-integer decagrams; GRAM is `ceil(g/10)` (`shared.ts:93-96`). Per-parcel weights are the AVERAGE of the one consignment weight, so per-parcel `ceil` can sum to more than `mpsWeight`.
- Volume under 10 cm renders as two digits (`shared.ts:105-107`).
- Typos: `occured` in three message families (`errors.ts:35,43,60,109`, `error-handler.ts:22`).
- Two different generic-500 bodies (`Internal server error` with the "An internal error has occured. If the error persists please contact support" details vs `Internal Server Error` with "An internal server error has occured.").
- Provider fault asymmetry: DE reads `shipmentResponses[].faults` and `detail.faults.message`; NL does neither (see Error shape).
- B2B is `CL` with no Predict on DE; real `B2B` with Predict on NL.
- Predict is added on any email, which is also an input to DPD.
- Token fault retry: exactly one retry with a fresh login, only for DE `LOGIN_5`/`LOGIN_6` and NL `ERR_DELICOM_TOKEN_EXPIRED` (`dpd-de/index.ts:30-32`, `dpd-nl/index.ts:30-32`, `labelling.ts:82-105`). A second token failure on the retry is not caught and surfaces as generic 500 (`TokenExpiredError` has no `httpStatusCode`, `errors.ts:123-128`). Token lifetime: DPD `authTokenExpires`, else 24h (`token-manager.ts:5,47`); mock issues 86400s (`fixtures/dpd/dpd.json:2`).
- Malformed JSON is 400 here, not 500.
- Paths are case-insensitive (Express default).
- Only the single failing check is returned (joi `abortEarly`, `details.pop()`; spec: first of z-schema errors).

### Statefulness / ordering constraints

- Stateless per request for the caller: no cancel/manifest/reprint, no shipment id returned, nothing to call before or after. Every successful call mints fresh parcel numbers (not idempotent; resending buys/creates another DPD order in the real system).
- Per-instance state: DPD token cache keyed `{username, provider}`, seeded from `fixtures/tokens.json`, in memory (`store.ts`); on a multi-instance Cloud Run service the first call per instance per provider does an extra login (added latency) and `dpdeu-key-revoked-token` demonstrates its retry once per instance.
- Mock DPD is stateless (tokens are self-describing `mockdpd-<de|nl>-<expiry>-<userhash>-<uuid>`, `mock-upstreams/src/dpd/index.ts:71-72`).
- ApiKy lookup is per request (no cache), so latency = ApiKy call + (login) + storeOrders + (converter).

### Adapter implications and leaks

- `serviceProvider` is mandatory and carrier-selecting: the adapter must carry "DPD DE" vs "DPD NL" per carrier/service config; `serviceType` is NOT tied to provider (NL accepts `B2B`, DE rewrites it to `CL`, both accept E10/E12/E18/CL).
- Credentials, depot, DPD user are server-side (company -> customer row by exact `{company, provider}`); the caller has no way to pick. A key that works for DE can 403 for NL.
- No cancel / manifest / reprint / track / validate: the generic interface must report these as unsupported for dpdeu, not call a route.
- Normalisation the adapter must do before sending: weight in `GRAM` (integers) to dodge the kg float bug; units exactly `GRAM`/`KILOGRAM`/`CENTIMETER` (not `KG`/`CM`); omit (never send `''` or `null`) `addressLine2`, `phoneNumber`; phone `+<digits>` with no spaces or omit; `state` max 2 chars (omit full region names); `postalCode` <= 9 chars; names/lines <= 35; `packageClientReferenceId` <= 35 (required per package); always send `serviceOptions: {}` and `dimensions` on every package (code needs them though the spec doesn't).
- UK-origin to DE/NL needs `customs.commodities` + per-package `invoiceNumber` (GB is non-EU); each commodity needs integer `quantity`, `hsCode` <= 8 chars, `description` <= 80, 3-char currency, value <= 99999.
- Label handling: one base64 string per package; position-paired, so an adapter should check `len(packages) == len(parcels)`; for PNG the label depends on an extra converter hop (new failure mode `PDF_CONVERSION_ERROR` only on PNG).
- Error mapping: 400 families with different shapes (`VALIDATION_ERROR`/`VALIDATION`/`SYNTAX_ERROR`/`SCHEMA_ERROR`/DPD fault code), 401/403 have `{message}` only, 403 `FORBIDDEN` is `{code,message,details}`; 500s carry generic text only. No retry guidance in bodies; DPD ERR 500 and ApiKy outage are both plain 500 (indistinguishable).
- Auth-order leak: a request with an invalid body and no/invalid key gets 400 before 401/403.

### README-vs-source discrepancies, and UNVERIFIED

Discrepancies:
- README line 31 and `src/validator.ts:4` comment refer to `src/validator.js` (the source repo's name); the file here is `validator.ts`. Cosmetic.
- README says the validator rejects phones lacking `+` or containing a space (`README.md:134-136`): accurate, but incomplete: it does not state that absent/empty/null phones skip the rule (`validator.ts:60,66`), that `''` and `null` are in practice rejected by the spec before joi (`swagger.yaml:269-273`), nor that GB-origin to DE/NL is non-EU and needs customs (`validator.ts:26-31`; `test/validator.test.ts:88-95`). README line 138-140 on spec strictness is correct.
- README table (line 66) lists `INTERNAL_SERVER_ERROR` / `Internal server error` for login failures and `Internal Server Error` for the catch-all: correct, but they are two distinct strings (see Error shape).
- README (lines 106, 107-109) lists `COMMON_8` (product unavailable) as a reachable outcome; with the shipped fixtures and spec enum it cannot be triggered via the proxy (derived).
- The spec declares `dimensions` optional and `serviceOptions` optional; code needs both (500 otherwise) (README line 68 mentions it only in the generic-500 row).

UNVERIFIED:
- Whether `is-european@1.0.4`'s `euMember` accepts lowercase or alpha-3 codes (package source not in the repo; tests only use uppercase alpha-2).
- Whether real Selector sends national-format/space-containing phone numbers to DPD Europe (README: "Selector sends national-format numbers ... to the other proxies"; no Selector source here).
- Exact z-schema message text for constraints other than those pinned by tests (enum, missing required, minLength, type, maxLength forms are standard but only enum/required/minLength/type are pinned in `test/routes.test.ts`).
- Joi key-validation order (derived from schema key order; test `validator.test.ts` only exercises one error at a time).
- Behaviour of Cloud Run frontend on an invalid inbound `Authorization` header.
- DE `COMMON_9`/`COMMON_7` bodies for NL and the `weight` field name in NL's integer fault were derived from `mock-upstreams/src/dpd/index.ts` + `errors.ts`, not from a dedicated proxy test.

### Notes for the E2 draft

- Line 182 ("DPD Europe rejects a phone number that lacks a leading `+` or contains a space"): true of the code but misleading as a blanket quirk. Only for a present, non-empty phone on `shipFrom` or `shipTo`; an omitted phone passes; `''`/`null` fail earlier at the spec with a different error (`VALIDATION_ERROR`, not `VALIDATION`). Suggest adding: error body is 400 `{code:"VALIDATION", message:"A validation error has occurred.", details:"shipFrom.phoneNumber must be a valid phone number with international prefix (+)"}`, and that GB origin to DE/NL needs customs.
- Line 183 ("Malformed JSON gives a 500, not a 400, on several mocks"): dpdeu is the opposite, malformed JSON gives 400 `SYNTAX_ERROR` (even without a key). amazon-sfp is a 500.
- Lines 66-70 / 69 (dpdeu "401 / 403 / 500"): correct, but "no key = 401" only holds when the body is valid; spec validation runs first, so an invalid body with no key gets 400. Bodies: 401 `{"message":"No API key provided"}`, 403 `{"message":"Not authorised"}`, 500 generic `{code,message,details}`.
- Line 126 ("The first call per provider retries its login, then succeeds"): precisely, the stale cached token is rejected by `storeOrders`, then the proxy logs in again and resends; the retry only happens once per proxy instance per provider (in-memory cache), not "per key".
- Line 24/55: fine. `dpdeu-key-bravo` is DE only (confirmed `customers.json`).
- Line 184 (typos kept, e.g. `additonal`): dpdeu has its own: `occured` (`errors.ts:35,43,60,109`; `error-handler.ts:22`).
- Rows 119-125 all confirmed against source; add the `PNG 500` note that it only fires when `labelFormat` is `PNG`, and that earlier mock checks (e.g. fractional kg weight) mask a magic zip.


---

## amazon-sfp (Amazon Shipping, Seller Fulfilled Prime + off-Amazon "EXTERNAL" channel; apps/amazon-sfp-proxy; mirrors new-amazon-prod.gfsdeliver.com)

Paths relative to repo root, lines from origin/main. Port 4106 (`apps/amazon-sfp-proxy/src/config.ts:51`). Not the Amazon Logistics proxy (`apps/amazon-logistics-proxy`, separate mock). Deployed with `AMAZON_ENVIRONMENT=production`, `ENABLE_MULTICOMPANY=true`, `SUPPORT_SFP=true`, `SUPPORT_WINDSOR=true` (`iac/projects/mock-amazonsfp/cloud-run.tf:35-39`).

### Operations and routes

| Operation | METHOD path | Supported? | Notes |
| --- | --- | --- | --- |
| create-ship | POST `/shipping/createLabel` | YES | Server-side two-step: Amazon `getRates` then `purchaseShipment`, in one caller request. 201 (`labelling.handler.ts:197-354`) |
| validate | POST `/shipping/createLabel?mode=validate` | YES | Rates only, no purchase, 200 or 400 (`:208-220`). Query enum only `validate` (`api/api.yaml:16-23`); any other `mode` value is a spec 400 |
| delete / cancel | POST `/shipping/{shipmentId}/cancel` | YES (but never fails) | Calls Amazon `PUT /shipping/v2/shipments/{id}/cancel`; **every failure becomes 200 `{}`** (`:373-392`) |
| track | GET `/shipping/tracking/{channelType}/{company}/{trackingId}` | YES | Amazon `GET /shipping/v2/tracking`; company from URL, not the caller's profile (`tracking.handler.ts`) |
| commit / manifest | none | NO | |
| reprint | none | NO | No re-fetch of an existing label |
| health | GET `/healthz` (200 `{status:"ok", uptime:"<N>s"}`), GET `/health/liveness` (200 `{"ok":true}`) | yes, no auth | `app.ts:104-112`. Not in the openapi spec |
| other | unknown path or method | 404 problem+json | `NotFoundException`, `instance: "<method lower-case> <path>"`; evaluated BEFORE auth (route first) (`app.ts:127-129`; `test/routes.test.ts:42-65`) |

Pipeline order (`app.ts:72-146`, README line 28-29): route match, then `x-api-key` security handler (ApiKy), then request validation (openapi-backend/Ajv against `api/api.yaml` with the `ServiceType` enum replaced from `config/services.yaml`), then the handler. So: unknown route 404 even with no key; no/invalid key 401 even with an invalid body (`test/routes.test.ts:83-86`); invalid body 400 only for authenticated callers. `express.json()` runs before all of it (`app.ts:108`), so malformed JSON is 500 (below).

### Auth and headers

- Header: `x-api-key` (`app.ts:133`; spec `api_key` apiKey in header `X-API-Key`, `api.yaml:143-147`). Multiple values (array) also 401.
- `Content-Type: application/json` for the POST (express.json + openapi requestBody). No other required header. Cloud Run `Authorization: Bearer` is never read by the proxy (only used as outbound SigV4 `authorization` to the mock Amazon); ignored.
- ApiKy lookup: `GET {APIKY_BASE_URL}/api/profile?token=<key>` (`@playground/apiky-client`); ANY exception (404/403/500/unreachable) is caught and becomes 401 (`app.ts:136-141`). `APIKY_DISABLED=true` skips the lookup but the header is still required, and the flag is ignored when `NODE_ENV`/`ENVIRONMENT` starts with `prod` (`config.ts:48,54`; `test/routes.test.ts:104-126`). Deployed `ENVIRONMENT = var.env` (likely `dev`), `APIKY_DISABLED` unset, so ApiKy is on.
- Key fixtures (`apps/mock-upstreams/fixtures/apiky/amazon.json`; credentials in `apps/amazon-sfp-proxy/fixtures/credentials.json`, secrets elided):

| `x-api-key` | ApiKy company / profile | Credentials | Effect |
| --- | --- | --- | --- |
| `amazon-key-alpha` | `ALPHA TEST`; warehouse `Sampleford`; displayName `Alpha Test Shop`; amazonShipperId + amazonSellerId set | own AWS key + both non-SFP and complete SFP LWA login | everything works, EXTERNAL and AMAZON |
| `amazon-key-bravo` | `BRAVO MOCK`; warehouse `NOWHERE`; no ids, no displayName | own AWS key; SFP login incomplete (only `sfprefreshToken`) | default-site warning `Using default warehouse location`; SFP orders silently fall back to non-SFP login |
| `amazon-key-default-creds` | `CHARLIE SAMPLE`; warehouse `TESTVILLE` | no record | env-var default login |
| `amazon-key-bad-lwa` | `DELTA BADLWA` | record with wrong LWA client secret | create: 500 `Internal server error`/`Internal server error`; cancel: 200 `{}`; track (for that company in URL): 500 |
| `amazon-key-bad-aws` | `ECHO BADAWS` | AWS key unknown to mock Amazon | create: 500 carrying Amazon's 403 text; cancel 200 `{}` |
| `amazon-key-box-dims` | `FOXTROT BOXES` | no record | has its own default box sizes in `config/dims2.yaml` |
| `amazon-key-no-profile` | profile lacks `profile` block | company `''`, default login | works; warehouse `''` so default-site warning |
| `apiky-500` | | | 401 |
| anything else / absent | | | 401 |

- Auth failure body is the framework's RFC 7807, `content-type: application/problem+json`, status 401 (the spec says 403) (`exceptions.ts:33-46`; `test/routes.test.ts:22-27,68-81`):
```
{ "type":"AuthenticationException", "title":"There was an error authenticating your request",
  "detail":"Principal unknown could not be authenticated. No additional detail was provided.", "status":401 }
```
- Credential selection (`credentials-manager.ts:37-68`, `amazon-access-token.ts`, `access-token-cache.ts`): by `profile.profile.company` exact (case-sensitive) match on `credentials.json`; no record or `ENABLE_MULTICOMPANY=false` gives env defaults. `channelType: AMAZON` (SFP) uses the `sfp*` LWA fields only when all three are set, else non-SFP. Access token cached 5 min per `company|SFP/NON-SFP`, max 100 (`access-token-cache.ts:7-9`). Cancel always uses the NON-SFP login (`labelling.handler.ts:378`). Tracking uses the URL company, `isSfp` only for `sfp-amazon`/`sfp-evri`, and signs with the DEFAULT AWS keys (company `''`) (`tracking.handler.ts:54-58`).

### Request

POST `/shipping/createLabel` body = `CreateLabelRequest` (`api/api.yaml:292-428`, additionalProperties not restricted). Required top level: `channelDetails`, `labelSpecification`, `packages`, `shipFrom`, `shipTo`, `serviceType`, `consignment`. Optional: `notes`.

| Field | Spec | Behaviour (code) |
| --- | --- | --- |
| `channelDetails.channelType` | required, enum `EXTERNAL`, `AMAZON` | handler uppercases; `AMAZON` = SFP order (`labelling.handler.ts:76`). Anything else is a spec 400 |
| `channelDetails.amazonOrderDetails.orderId` | optional object; if present `orderId` required | upstream (mock Amazon) requires it for `AMAZON` (400 InvalidInput, surfaced as 500) (`mock-upstreams/src/amazon/index.ts:333-336`) |
| `channelDetails.sellerDisplayName` | optional | if set, copied to every package as `sellerDisplayName` and removed from `channelDetails`; wins over profile `displayName` (`:156-164`) |
| `serviceType` | required; enum (replaced at start-up by `config/services.yaml`; same 14 values): `SWA-UK-PREM`, `SWA-UK-2D`, `PRIME-PREMIUM-UK-MFN`, `STD-UK-MFN`, `ECON-UK-MFN`, `HERMES_UK_MFN_NEXTDAY_MERCHANT`, `HERMES_UK_MFN_STANDARD_MERCHANT`, each also with `-SIG` | `-SIG` stripped (`/-SIG/g`) for the rate match and adds `valueAddedServices.signatureOnDelivery: {}` to the rates request (`:185-189`); match is case-insensitive on Amazon's `serviceId` (`:204-206`); NOT sent to Amazon (dropped) |
| `labelSpecification` | required; `labelFormat` enum `ZPL`/`PDF`/`PNG`, **`labelResolution` also required integer (even for PDF)** | see label format below |
| `consignment.weight` | required `{unit: GRAM/KILOGRAM/OUNCE/POUND, value}` | dropped from the Amazon request; used ONLY when a package weight is 0 (see below) |
| `packages` | array, **min 1, max 1** (`api.yaml:343-346`); a second package is a spec 400 `{problem:"maxItems"}` (`test/routes.test.ts:149-153`) | single parcel only |
| `packages[].dimensions` | required `{length,width,height (numbers), unit: INCH/CENTIMETER}` | passed through unconverted; if any of length/width/height `=== 0`, replaced from `config/dims2.yaml` by `weight <= maxWeightKg` (company-specific row if the `for` matches the company case-insensitively, else `default`), with a warning; no fit gives 500 `No dims available` (`:137-154`; `utils/dims-from-weight.ts:42-53`). Lookup uses `weight.value` **whatever the unit** (500 GRAM looks up 500 kg) |
| `packages[].weight` | required `{unit GRAM/KILOGRAM/OUNCE/POUND, value}` (no minimum) | passed through unconverted; **if any package weight is falsy (0)**, ALL packages get `consignment.weight.value / n` (2dp, remainder on the last) with unit forced to `KILOGRAM` regardless of the consignment's unit (`:127-135`; `utils/calculate-avg-weights.ts`), warning per parcel `Parcel reference X has been given a default weight of <n>Kg`. A consignment in GRAM with a 0 package weight therefore sends the gram figure labelled KILOGRAM (derived from code, no test) |
| `packages[].packageClientReferenceId` | required string | passed through; printed on the mock label |
| `packages[].insuredValue` | required `{unit: GBP only, value >= 0.01}` | passed through |
| `packages[].items[]` | required, min 1; each requires `quantity` (int >=1) and `weight`; optional `itemIdentifier`, `description`, `isHazmat`, `itemValue{unit GBP, value >=0.01}` | passed through |
| `shipFrom` / `shipTo` (`Address`) | required: `name`, `addressLine1`, `city`, `postalCode`, **`stateOrRegion`** (send `''` if none); `countryCode` is **not** required by the spec (but mock Amazon 400s without it, see below). Limits: name/lines 1..60, city <=50, `postalCode` 1..20, `email` <=64, `phoneNumber` 1..20, countryCode exactly 2 | EXTERNAL: request `shipFrom` is IGNORED and replaced by the `sites.yaml` address matched on profile `warehouse` (case-insensitive `gfsName`), default site plus warning `Using default warehouse location` when no match (`:171-183`; `warehouse-manager.ts:53-63`); AMAZON (SFP): the request's `shipFrom` is kept. `shipTo` line breaks (`\r`, `\n`) in `addressLine1/2/3` become spaces (`:99-103`) |
| `notes[]` | optional; items `{noteType: DELIVERY, note}` | first `DELIVERY` becomes `shipperInstruction: {deliveryNotes: {noteType, note}}`; `notes` removed (`:110-116`) |

Other handler rules, in order (`labelling.handler.ts:70-195`):
1. Fetch LWA access token (`getAccessToken(company, isSfp)`); failure gives 500 `{code:500,message:"Internal server error",detail:"Internal server error"}`. This is BEFORE the BT and SFP checks, so a login failure hides those 400s (README line 227).
2. `SUPPORT_WINDSOR` + `shipTo.postalCode.startsWith('BT')` (case-sensitive, untrimmed, any channel): 400 `{code:400,message:"Bad request",detail:"BT postal codes are not supported"}`. Deployed with Windsor on (`cloud-run.tf:39`), so BT postcodes are rejected on the live mock.
3. `AMAZON` order with `SUPPORT_SFP` off: 400 `Amazon orders are not currently supported` (deployed on, so does not fire).
4. Weight and dimension defaulting (above).
5. profile `displayName` set on every package; `amazonSellerId` added into `channelDetails.amazonOrderDetails` for SFP; for EXTERNAL with profile `amazonShipperId`: `shipmentForShipperNumber = amazonShipperId` and `quoteForShipperNumber = AMAZON_QUOTE_FOR_SHIPPER_NUMBER` (`:191-194`). AMAZON orders send no shipper numbers.
6. getRates, rate pick, label pick, purchase.

Label format selection (`:251-306`): among the rate's document specs of the requested `labelFormat`, the size whose area is closest to 6x4 inch wins (mock offers PDF 11x8.5in, 15x10cm, 6x4in; PNG and ZPL 6x4in, DPIs 203/300; `mock-upstreams/src/amazon/index.ts:81-87`). `dpi` is sent to Amazon only when that spec lists DPIs; `labelResolution` must then be one of 203/300 or 500 `Label resolution unavailable` (`detail`: `Requested label resolution 150DPI not available. Available resolutions are [203, 300].`). For PDF `labelResolution` is required by the spec but otherwise ignored. If the rate has no spec in the format: 500 `Label format unavailable` (`No label format available for X. Available formats are [...]`).

### Response

- create: `201` JSON `application/json` (`:354`):
```
{ "shipmentId": "mock-shp-<uuid>",
  "packages": [ { "trackingId": "<id>", "documents": { "label": { "labelStream": "<base64>" } } } ],
  "warnings": ["..."] }          // warnings key only when non-empty
```
  - `labelStream` = Amazon's `packageDocuments[type=LABEL].contents`, base64, raw (no data URI), in the requested format (PDF 6x4in page, PNG at 6x4in x dpi, ZPL text). One label per package (always one package). Missing LABEL doc leaves `label: {}` (undefined dropped).
  - `trackingId`: mock Amazon `TBA9999` + 8 digits (AMZN_UK services) or `9999` + 12 digits (Evri/HERMES_UK services) (`mock-upstreams/src/amazon/index.ts:122-126`).
  - `shipmentId` is what `cancel` needs; tracking needs the `trackingId`.
  - `warnings` strings: `Using default warehouse location`; `Parcel reference X has been given a default weight of <n>Kg`; `Parcel reference X has been given default dimensions of L x W x H`.
  - No customs/invoice documents, no price, no carrier name returned.
- validate (`?mode=validate`): `200 {rateForRequestedService, eligibleRates, ineligibleRates, warnings}` where the rate objects are Amazon's (`rateId, carrierId, carrierName, serviceId, serviceName, billedWeight, totalCharge{unit,value}, promise, supportedDocumentSpecifications, availableValueAddedServiceGroups, requiresAdditionalInputs`) (`labelling.handler.ts:208-215`; mock `index.ts:364-390`). `warnings` is always an array here. No match: 400 `{code:400,message:"Invalid request",detail:"No rates available, or invalid request"}`. No label-format/resolution check, no requestToken exposed.
- cancel: `200` with Amazon's `payload` (mock: `{}`), JSON.
- track: `200 {trackingId, trackingSummary, events, promisedDeliveryDate}` where `trackingSummary` = Amazon `summary.status` (`PreTransit`/`InTransit`/`Delivered`), `events` = Amazon `eventHistory` passed through unchanged as `{eventCode, location{city,stateOrRegion,countryCode,postalCode}, eventTime, shipmentType}` (NOT the spec's `code`/`time`) (`tracking.handler.ts:83-88`; `test/cancel-and-track.test.ts:62-65`). `proofOfDelivery` and other summary fields are dropped.

### Error shape

Two families:

1. Framework errors (RFC 7807, `content-type: application/problem+json`; `exceptions.ts`):
   - 401 `AuthenticationException` (above).
   - 400 `{type:"BadRequestException", title:"There was an error validating your request", detail:"One or more validation errors occurred.", status:400, errors:[{field, problem}]}`; `field` = Ajv `missingProperty` or `type` param, absent for most keywords (`enum`, `maxItems`); `problem` = Ajv keyword (`required`, `enum`, `maxItems`, ...). One entry per Ajv error (`exceptions.ts:53-70`).
   - 404 `{type:"NotFoundException", title:"Resource Not Found", status:404, detail:"The route or resource could not be found", instance:"post /shipping/createShipment"}`.
   - 500 anything unexpected, **malformed JSON included** (`express.json` error reaches the last handler): `{code:"INTERNAL SERVER ERROR", message:"An unexpected error occurred", details:"An unexpected error occurred on the server, no additional detail is available"}` with content-type `application/problem+json` (`exceptions.ts:92-107`; `test/routes.test.ts:160-174`). Note: `code` is a string with a space here.
2. Handler errors `{code:<numeric status>, message, detail}` (`application/json`; `respond.ts:4-10`, note `detail` not `details`):

| Status | message | detail |
| --- | --- | --- |
| 400 | `Bad request` | `BT postal codes are not supported` / `Amazon orders are not currently supported` |
| 400 | `Invalid request` | `No rates available, or invalid request` (validate mode only) |
| 500 | `Internal server error` | `Internal server error` (token acquisition failed), or `<e.message> - <Amazon errors[0].message> - <Amazon errors[0].details>`, e.g. `Request failed with status code 400 - The ship to address is not valid. - ` (trailing `- ` because Amazon `details` is `''`); for a non-HTTP error it ends `- undefined` (`:365-369`) |
| 500 | `No rate available` | `No rate available for service X - <ineligibility reasons joined ', '> . Available services are ['A','B']` e.g. `...for channel EXTERNAL.. Available services are ['SWA-UK-PREM','SWA-UK-2D']` (double full stop kept; `test/create-label.test.ts:295-303`) |
| 500 | `No dims available` | `No default dimensions available for  30kg` (double space kept) |
| 500 | `Label format unavailable` / `Label resolution unavailable` | texts above |
| 404 | `Not found` | `The requested shipment could not be found` (tracking) |
| 500 | `Internal server error` | `Internal server error` (tracking, any non-404 failure) |
| 501 | `Not implemented` | `Tracking API is not yet available for <channelType>` |

Carrier-failure status: every Amazon-side failure (400/403/429/5xx, bad AWS keys) on create is **500** with Amazon's status and message in `detail`; ineligible service is 500 (not 400) outside validate mode. Cancel never errors.

### Failure scenarios for D5 (magic values)

Magic `shipTo.postalCode` values apply to `getRates` (both create and validate), matched after removing all whitespace and upper-casing (`mock-upstreams/src/amazon/index.ts:60-61`): `err400`, `ERR  400`, `Err 400` all fire. They are evaluated after mock Amazon's own validation (addresses need `addressLine1, city, postalCode, countryCode` on BOTH shipFrom and shipTo; each package needs weight > 0, length/width/height > 0, and 1..100 items; `channelType` EXTERNAL/AMAZON; `orderId` for AMAZON; `index.ts:308-336`). A request missing `shipTo.countryCode` (spec-valid) therefore gives 500 `...status code 400 - shipFrom and shipTo need addressLine1, city, postalCode and countryCode. - `.

| Operation | Field | Magic value | Where verified | What the caller sees |
| --- | --- | --- | --- | --- |
| create / validate | `shipTo.postalCode` | `ERR 400` | `mock-upstreams/src/amazon/index.ts:30,339-342`; `test/create-label.test.ts:305-312` | 500 `{code:500,message:"Internal server error",detail:"Request failed with status code 400 - The ship to address is not valid. - "}`; one upstream call (4xx not retried) |
| create / validate | `shipTo.postalCode` | `ERR 403` | `index.ts:31,343-346` | 500, detail `Request failed with status code 403 - Access to requested resource is denied. - ` |
| create / validate | `shipTo.postalCode` | `ERR 500` | `index.ts:32,347-350`; `test/create-label.test.ts:314-317` | 500, detail `Request failed with status code 500 - We encountered an internal error. Please try again. - `; POST so NOT retried (1 upstream call) |
| create / validate | `shipTo.postalCode` | `ERR 429` | `index.ts:33,351-354`; `http-client.ts:30-43`; `test/create-label.test.ts:319-329` | upstream 429 every time: 4 attempts (initial + 3 retries, backoff 200/400/800 ms +0-20%, so about 1.4 to 1.7 s extra latency), then 500 detail `Request failed with status code 429 - You exceeded your quota for the requested resource. - ` |
| create / validate | `shipTo.postalCode` | `RETRY 429` | `index.ts:34,355-358,199-205`; `test/create-label.test.ts:331-334` | first attempt throttled, retry succeeds: normal 201 / 200, extra ~200 ms. The mock keys "already throttled" on the request's SigV4 `Authorization` header, which carries `x-amz-date` (second resolution) and the body hash: the same body re-sent within the same second is NOT throttled again; on multiple mock-upstreams instances the retry may be throttled again (README lines 157-160) |
| create | `shipTo.postalCode` | `NO RATE` | `index.ts:35,361-362,416-419`; `test/create-label.test.ts:295-303` pattern | 500 `{code:500,message:"No rate available",detail:"No rate available for service <svc> - The destination is not serviceable.. Available services are []"}` |
| validate | `shipTo.postalCode` | `NO RATE` | `labelling.handler.ts:216-218` | 400 `{code:400,message:"Invalid request",detail:"No rates available, or invalid request"}` |
| create | `shipTo.postalCode` | `BUY 500` | `index.ts:36,404,469-472`; `test/create-label.test.ts:336-341` | rates succeed, purchase POST 500, not retried: 500 detail `Request failed with status code 500 - We encountered an internal error. Please try again. - ` |
| create / validate | `serviceType` vs `channelType` | e.g. `STD-UK-MFN` with `EXTERNAL` (or `SWA-UK-PREM` with `AMAZON`) | `fixtures/amazon/amazon.json` channels; `test/create-label.test.ts:295-303` | create: 500 `No rate available` naming the ineligibility reason `The service is not available for channel EXTERNAL.`; validate: 400 `Invalid request`. Channel map: EXTERNAL = `SWA-UK-PREM`, `SWA-UK-2D`; AMAZON = `PRIME-PREMIUM-UK-MFN`, `STD-UK-MFN`, `ECON-UK-MFN`, `HERMES_UK_MFN_NEXTDAY_MERCHANT`, `HERMES_UK_MFN_STANDARD_MERCHANT` |
| create | `shipTo.postalCode` | any starting `BT` | `labelling.handler.ts:105-108`; `test/create-label.test.ts:358-367` | 400 `{code:400,message:"Bad request",detail:"BT postal codes are not supported"}` (case-sensitive prefix, so `bt1 1aa` is not caught); proxy check, no Amazon call |
| create | `labelSpecification.labelResolution` | PNG/ZPL with value not in {203,300} | `labelling.handler.ts:275-291`; `test/create-label.test.ts:257-267` | 500 `Label resolution unavailable` |
| create | `x-api-key` | `amazon-key-bad-lwa` | `fixtures/credentials.json` (DELTA BADLWA); `test/create-label.test.ts:343-349` | 500 `{code:500,message:"Internal server error",detail:"Internal server error"}`; 401 from LWA is not retried |
| create | `x-api-key` | `amazon-key-bad-aws` | `index.ts:285-288`; `test/create-label.test.ts:351-356` | 500 detail `Request failed with status code 403 - The security token included in the request is invalid. - ` |
| create | `x-api-key` | `amazon-key-bravo` | `test/create-label.test.ts:62-65` | 201 with `warnings: ["Using default warehouse location"]` |
| any | `x-api-key` | absent / unknown / `apiky-500` | `app.ts:132-142`; `test/routes.test.ts:68-81` | 401 problem+json AuthenticationException (all three identical) |
| track | `trackingId` prefix | `UNKNOWN` (case-insensitive) | `index.ts:42,527-530`; `test/cancel-and-track.test.ts:98-104` | 404 `{code:404,message:"Not found",detail:"The requested shipment could not be found"}` |
| track | `trackingId` prefix | `ERR500` | `index.ts:531-534`; `test/cancel-and-track.test.ts:106-109` | GET retried 3 times (4 upstream calls), then 500 `{code:500,message:"Internal server error",detail:"Internal server error"}` |
| track | `trackingId` prefix | `ERR429` | `index.ts:535-538`; `test/cancel-and-track.test.ts:111-114` | 429 every time, 4 attempts, 500 same body |
| track | `trackingId` prefix | `RETRY429` | `index.ts:539-542`; `test/cancel-and-track.test.ts:116-119` | 200 after one retry (same-signature caveat as above) |
| track | `trackingId` (no magic prefix) | last char digit | `index.ts:170-181`; README lines 123-124 | 0-1 gives 1 event, `PreTransit`; 2-5 gives 3 events, `InTransit`; 6-7 gives 4 events, `InTransit`; 8-9 gives 5 events, `Delivered`. A non-digit last character parses to NaN, treated 0: `PreTransit`. The id need not have been created; any string <= 64 chars (longer: 400 InvalidInput, surfaced as 500) |
| track | `channelType` path | not `external`/`sfp-amazon`/`sfp-evri` (case-insensitive) | `tracking.handler.ts:27-37`; `test/cancel-and-track.test.ts:77-83` | 501 `Not implemented` before any token call; `sfp-evri` queries carrier `HERMES_UK`, others `AMZN_UK` |
| track | `company` path | company whose LWA login fails (`DELTA BADLWA`) | `test/cancel-and-track.test.ts:121-124` | 500 `Internal server error` |
| cancel | `shipmentId` prefix | `UNKNOWN` | `index.ts:509-512`; `test/cancel-and-track.test.ts:36-39` | Amazon 400, **caller gets 200 `{}`** |
| cancel | `shipmentId` prefix | `ERR500` | `index.ts:513-516`; `test/cancel-and-track.test.ts:41-44` | Amazon 500 on a PUT, retried 3 times (4 calls), **caller gets 200 `{}`** after about 1.4 s |
| cancel | `shipmentId` prefix | `ERR429`, `RETRY429` | `index.ts:507-518` (no handling) | no effect: 200 `{}` (the 429 prefixes are tracking-only) |
| cancel | `x-api-key` | `amazon-key-bad-lwa` (or bad-aws) | `labelling.handler.ts:377-391`; `test/cancel-and-track.test.ts:46-49` | 200 `{}`; no upstream cancel call for bad-lwa |

### Quirks mirrored from production

- Cancel swallows every failure into 200 `{}` (`labelling.handler.ts:388-390`, README line 58, 224-225); a caller cannot tell a real cancel from a failed one, including twice-cancel and never-existed ids (mock Amazon is stateless: any id not prefixed `UNKNOWN`/`ERR500` cancels fine, `index.ts:507-518`).
- Retry policy (axios-retry reproduction, `http-client.ts:3-43,80-91`): up to 3 retries; 429 and "no response/network error" retried for any method (including the purchase POST); 5xx retried only for GET/PUT/HEAD/OPTIONS/DELETE (so tracking GET and cancel PUT retry on 5xx; rates/purchase POST do not). Delay `2^n * 100 ms` + up to 20% jitter; a `Retry-After` header is read as MILLISECONDS. Callers see the effect only as latency and a final 500.
- Network-failure retry on the purchase POST means a lost response can buy a second shipment in the real system (source behaviour, derived).
- Weight/dims quirks: defaulting ignores units (`calculate-avg-weights.ts`, `dims-from-weight.ts`; README line 228: `500 GRAM looks up 500 kg`); consignment unit forced to KILOGRAM on defaulting.
- `-SIG` services: suffix stripped for matching; `signatureOnDelivery` requested; when the chosen rate requires any value-added-service group, the purchase sends only `DELIVERY_CONFIRMATION`, whatever the groups offer (`labelling.handler.ts:308-320`).
- Ineligible service is a 500, not a 400 (`:241-248`), except in validate mode.
- Access token is fetched before the Windsor and SFP checks (login failure masks the 400s).
- Tracking signs with the default AWS keys, with the access token of the URL's company (`tracking.handler.ts:55-58`).
- An SFP (`AMAZON`) order keeps `shipTo` (the source's strip is commented out) (`test/create-label.test.ts:168-171`).
- The tracking id is interpolated unencoded into the Amazon query string (`amazon-api-client.ts:55-59`): a `&` or `#` in the id would alter the upstream query (derived).
- Error `detail` text format `<axios message> - <Amazon message> - <Amazon details>` with trailing `- `.
- Malformed JSON: 500 problem+json (not 400). Unknown path: 404 before auth. 401 for ApiKy outage (not 500).
- Mock defaults deliberately differ from the source (README lines 205-206): `AMAZON_ENVIRONMENT` production, `SUPPORT_SFP`/`SUPPORT_WINDSOR` true.

### Statefulness / ordering constraints

- create does rates then purchase inside one request; nothing to call first. The mock Amazon carries rate ids/services/package refs in a self-contained `requestToken` (TTL 600 s) so no shared state; the proxy never exposes the requestToken or rateId.
- Not idempotent: each create issues a new `mock-shp-<uuid>` and new tracking id; no client reference dedupe (`packageClientReferenceId` is only printed).
- cancel needs no prior create (the id is not checked, apart from the `UNKNOWN`/`ERR500` prefixes); can be repeated; always 200.
- track needs no prior create either (status derived from the last digit of the id).
- Per-instance state: LWA access-token cache (5 min, per company+SFP flag), `RETRY 429` throttled-signature set in mock-upstreams (bounded 1000, per mock instance), `sites.yaml`/`dims2.yaml`/`services.yaml` read once.
- The service enum and sites/dims are config files loaded at start-up (`app.ts:60-70`), so enum changes need a redeploy.

### Adapter implications and leaks

- Amazon SFP is TWO modes under one route: `channelType: EXTERNAL` (non-Amazon-order, Amazon Shipping services `SWA-UK-*`; shipFrom replaced by the profile warehouse; shipper numbers added) vs `AMAZON` (SFP; needs `amazonOrderDetails.orderId`; shipFrom kept; services `*-MFN` / Evri). The adapter must choose the channel and a matching `serviceType`; a mismatched pair gives 500 `No rate available`.
- Single package only (`maxItems: 1`): multi-parcel orders cannot be sent in one call.
- A `validate` operation exists and is cheap (rates only, no purchase, 200/400). It does NOT test label format/resolution. A generic validate can map to `?mode=validate`; a successful validate means the service is eligible for that channel and destination.
- Spec-required quirks the adapter must always send: `stateOrRegion` (even `''`), `labelResolution` (even for PDF), `insuredValue` (GBP, >= 0.01), `items[]` (>= 1, each with `quantity` and `weight`), `channelDetails`, `consignment.weight`; sensible non-zero weight and dimensions to avoid defaulting; and in practice `countryCode` on both addresses (mock Amazon 400s otherwise even though the spec does not require it).
- Weights/dims are NOT unit-converted by the proxy; send `KILOGRAM`/`CENTIMETER` consistently. Avoid zero weights (the unit-forcing quirk).
- Label: `documents.label.labelStream` (nested object, base64), format chosen by `labelFormat`; PNG/ZPL require `labelResolution` 203 or 300; PDF is always 6x4 in.
- Errors: framework (problem+json with `type/title/detail/errors`, or the 500 `{code:"INTERNAL SERVER ERROR",message,details}`) vs handler (`{code:<number>,message,detail}`); 500 is used for carrier rejections, so the status code carries no retryability signal; the real Amazon status/message is only in the free-text `detail`.
- cancel always returns 200 `{}`: the adapter cannot detect cancel failure; if a cancel confirmation is needed it must be inferred elsewhere (e.g. tracking, UNVERIFIED how Amazon reports it).
- Tracking is by `trackingId` with `{channelType}/{company}` in the path; `company` is the ApiKy company name (URL-encode spaces, e.g. `ALPHA TEST`); only `external`/`sfp-amazon`/`sfp-evri` supported, others 501.
- Latency: 429 and 5xx-on-GET/PUT scenarios cost 1.4 to 1.7 s; expect the first call per company after a cold start to include an LWA token call.
- Credentials/ids are all server-side (company -> AWS keys, LWA, shipper/seller ids, warehouse); the caller only supplies a key.

### README-vs-source discrepancies, and UNVERIFIED

Discrepancies:
- `.env.example:21` sets `SUPPORT_WINDSOR=false`; `config.ts:61`, README line 11/177 and the deployed `iac/projects/mock-amazonsfp/cloud-run.tf:39` say true (the code default is true). The deployed value (true) governs the live mock.
- README line 6 (not the Amazon Logistics proxy) fine; README line 22 says track route is polled by connectors-amazon at `{endpoint}/external/{company}/{parcel}`, but the route here is `/shipping/tracking/{channelType}/{company}/{trackingId}` (README treats `{endpoint}` as including `/shipping/tracking`; consistent with `scripts/smoke.mts:174-176`).
- README routes table does not flag `packages` `maxItems: 1` or that `labelResolution` and `stateOrRegion` are required (both are in `api.yaml`, pinned in `test/routes.test.ts:149-153`).
- README (line 82-86) says "zero weights become the consignment weight shared across packages"; it does not say the unit is forced to KILOGRAM regardless of the consignment unit (`labelling.handler.ts:130`).
- README (line 69-71 and 110-120 magic table) lists `UNKNOWN`/`ERR500` cancel prefixes as Amazon 400/500 (accurate) but does not point out that `ERR429`/`RETRY429` have no effect on cancel (README says "none").
- Spec/doc drift kept from source (README lines 232-234): cancel spec documents 404 but code always 200 `{}`; spec 403 vs actual 401; tracking events are `eventCode`/`eventTime` not `code`/`time`; `Error.code` documented string but handler sends a number; `ValidatedLabelResponse` documents only `warnings`.
- `api.yaml` `CreateLabelRequest` does not require `countryCode`, but mock Amazon does (`mock-upstreams/src/amazon/index.ts:308-312`); real Amazon behaviour UNVERIFIED.

UNVERIFIED:
- Whether the deployed mock's `ENVIRONMENT`/`NODE_ENV` makes `APIKY_DISABLED` irrelevant: it is unset, so ApiKy is on regardless.
- Real Amazon behaviour behind any of these mocks (all upstream shapes are the mock's invention, README lines 141-163); the `-SIG` / DELIVERY_CONFIRMATION handling is from the source code only.
- Whether a retry of `RETRY 429` lands on the same mock-upstreams instance on the deployed multi-instance service.
- Cancel confirmation semantics in real Amazon.

### Notes for the E2 draft

- Line 25 ("Buys Amazon Shipping labels for Seller Fulfilled Prime orders, cancels, tracks"): incomplete. It serves two channels (`EXTERNAL` Amazon Shipping and `AMAZON` SFP), and also has a validate (rates-only) mode `?mode=validate`. Single package only.
- Lines 66-70 (`amazon-sfp` "401 / 401 / 401"): correct for no key / unknown key / `apiky-500`. Body is RFC 7807 problem+json `AuthenticationException` with 401 (not `{message}`). Note unknown routes 404 before any key check; malformed JSON is a 500 (line 183 correct for this mock).
- Line 127 (`ERR 400`, `ERR 403` -> "500 carrying Amazon's status"): confirmed; the status is only in the `detail` text (`Request failed with status code 400 - ...`), the HTTP status is 500.
- Line 129 (`ERR 429` "Four calls, then 500"): confirmed (1 initial + 3 retries); adds about 1.4 to 1.7 s.
- Line 130 (`RETRY 429` "201 on the retry"): confirmed with caveat: the throttle is keyed per SigV4 `Authorization` header (includes second-resolution timestamp + body hash), so a second identical request in the same second is not throttled, and across mock instances the retry can be throttled again. Applies to validate mode (200) too.
- Line 131 (`NO RATE` -> 500 "No rate available"): true for create; in `?mode=validate` it is 400 `Invalid request`.
- Line 133 (id prefixes): confirmed for tracking. Cancel: the README table says only `UNKNOWN`/`ERR500` do anything; the caller ALWAYS gets 200 `{}` on cancel, so say so (it is not "see the README", the answer is: no failure is ever visible).
- Line 134 (last digit 0-1 / 2-7 / 8-9 -> PreTransit/InTransit/Delivered): confirmed (digit 0-1 PreTransit, 2-7 InTransit, 8-9 Delivered; non-digit last char is PreTransit).
- Line 135 (`amazon-key-bad-lwa`, `amazon-key-bad-aws`): confirmed. Add: bad-lwa gives a bare 500 (`detail: "Internal server error"`), bad-aws a 500 carrying Amazon's 403 text; on cancel both give 200 `{}`.
- Line 56 keys (`amazon-key-alpha`, `amazon-key-bravo`): confirmed; bravo is the default-warehouse-warning / incomplete-SFP-login account, not a different "bad" account.
- Line 180 (`-SIG` "inferred from the SFP proxy's code"): about the other mock; for THIS proxy the `-SIG` handling is explicit source (`labelling.handler.ts:185-189,308-320`): suffix stripped, `signatureOnDelivery` requested, `DELIVERY_CONFIRMATION` purchased.
- Line 43: `amazon-sfp` serves `/healthz` through the public name: confirmed (`app.ts:110-112`), plus `/health/liveness`.


---

## amazon (Amazon Logistics; apps/amazon-logistics-proxy; mirrors amazon.gfsdeliver.com)

All paths are relative to the repo root, line numbers from origin/main. `upstream` = `apps/mock-upstreams/src/amazon/index.ts` (shared with amazon-sfp; cited as `mu-amazon`). Default port 4107. Not the SFP proxy.

### Operations and routes

| Operation | METHOD path | Supported? | Notes |
| --- | --- | --- | --- |
| validate | POST `/shipping/createLabel?mode=validate` | yes | Rates only, never buys. 200 `{warnings:[...]}` (array can be empty: `{warnings: []}`) if a rate exists for the (de-`-SIG`ed) service, else 400 `{code:400,message:"Invalid request",detail:"No rates available, or invalid request"}` (labelling.service.ts:234-241). Does NOT check label format, DPI or `-SIG`: a PDF or `-SIG` request validates 200 and then fails on create. `mode` is the only allowed value `validate`; any other value is a 400 (swagger.ts:133-135, app.ts:147) |
| create-ship | POST `/shipping/createLabel` | yes | Rates (`POST /shipping/v2/shipments/rates`) then purchase (`POST /shipping/v2/shipments`). 201 (labelling.service.ts:224-327). Exactly 1 package (spec maxItems 1) |
| delete-cancel | POST `/shipping/{shipmentId}/cancel` | yes | HTTP verb is POST, no body, no schema validation, upstream is `PUT /shipping/v2/shipments/{id}/cancel` (amazon-api-client.ts:36-43). 200 with body `{}` (Amazon's `payload`) (labelling.service.ts:80-88, mu-amazon:507-518). No content-type check |
| commit-manifest | none | NOT supported | `/shipping/<anything-else>` is not routed; it falls to the catch-all and returns 200 OK (see Other) |
| reprint | none | NOT supported | same catch-all trap |
| track | GET `/shipping/tracking/{channelType}/{company}/{trackingId}` | yes | `GET /shipping/v2/tracking?carrierId=..&trackingId=..` upstream. Detail below. swagger.yaml:25-66, tracking.service.ts |
| other | GET `/api-docs` | yes | No auth. Swagger JSON with `ServiceType` enum from config/services.yaml (app.ts:122-125) |
| other | any other method/path (incl. `GET /health/liveness`, `GET /`) | catch-all | 200 `{"code":200,"message":"OK","detail":"Server is OK and ready to handle requests"}`; under `/shipping/**` the x-api-key check runs first (app.ts:156-228) |

Route matching is case-insensitive with optional trailing slash (swagger.ts:59, test routes.test.ts:85-91). A known path with the wrong method is a 400 with an `Allow` header, body `detail:"undefined at undefined in request body"` (app.ts:128-132, routes.test.ts:154-157). Express JSON is pretty-printed with 2 spaces, `content-type: application/json` always (writer.ts:14-19).

### Auth and headers

- Header: `x-api-key` (swagger.yaml:13-17). Checked only for paths matching `/^\/shipping(?:$|[/.])/i`, only when `IS_SECURED !== 'false'` (default secured) (app.ts:156-160, config.ts:50). `/api-docs` and the catch-all need no key.
- Working key fixtures (apps/mock-upstreams/fixtures/apiky/amazon-logistics.json): `amzl-key-alpha` (company `AMZL ALPHA`, warehouse `Sampleford`, has displayName + amazonShipperId), `amzl-key-bravo` (`AMZL BRAVO`, warehouse `NOWHERE`, so default-warehouse warning, signs with env-var AWS keys), `amzl-key-fallback` (`AMZL CHARLIE`, no credentials record, falls back to the `GFS` record), `amzl-key-bad-lwa` (`AMZL DELTA`), `amzl-key-bad-aws` (`AMZL ECHO`), `amzl-key-box-dims` (`AMZL FOXTROT`, own box sizes), `amzl-key-no-profile` (profile with no `profile` block: company `""`, GFS record). `apiky-500` makes mock ApiKy fail.
- Missing key: 401 `{"message":"No API key provided"}` (app.ts:161-164). Unknown key (ApiKy 403): 403 `{"message":"Not authorised"}` (app.ts:176-177). `apiky-500`: ApiKy 500, retried 3x (200/400/800 ms backoff, ~1.4-1.7 s total), then 500 `{"message":"Internal server error"}` (app.ts:89-101, 170-174). Any non-500 ApiKy failure (incl. 401 service-key) maps to 403. No `code` or `detail` key on these three bodies.
- ORDERING TRAP: on `createLabel` the schema validator runs BEFORE ApiKy, so a bad body with no/invalid key is a 400 not a 401 (app.ts:121-154 precede 156-181; routes.test.ts:95-98). Cancel and tracking have no body validation, so key check comes first.
- Other headers: createLabel requires `content-type: application/json` (any `;charset` ok); anything else is the 400 "undefined at undefined" (app.ts:136-140, routes.test.ts:140-147). Cancel and tracking do not check content-type. `Accept` not read.
- `Authorization: Bearer` on the inbound request: never read by app code (git grep for `authorization` in src finds nothing); ignored. The ID-token wrapper in main.ts:7 is outbound-only (mock-kit upstream-auth). UNVERIFIED: whether Cloud Run IAM at the edge (mock-edge terraform) requires/strips a Bearer, not in this app's source.
- With `IS_SECURED=false` (the "internal" prod deployment, not the mocks.merak public one per README:11-14) no key is needed and company is `""` (GFS credentials record) (routes.test.ts:160-184).
- ApiKy profile fields consumed: `profile.company`, `.warehouse`, `.displayName`, `.amazonShipperId` (app.ts:187-199).

### Request

Schema = swagger.yaml `CreateLabelRequest` (swagger.yaml:334-457), validated by Ajv reworded in z-schema style (swagger.ts:99-145). `serviceType` enum is REPLACED at startup by config/services.yaml, so the yaml enum (`SWA-UK-PRIME-PREM` etc.) is dead.

Required top-level: `channelDetails`, `labelSpecification`, `packages`, `shipFrom`, `shipTo`, `serviceType`, `consignment` (swagger.yaml:336-343). Optional: `notes`.

| Field | Rules |
| --- | --- |
| `serviceType` | one of `SWA-UK-PREM`, `SWA-UK-2D`, `SWA-UK-PREM-SIG`, `SWA-UK-2D-SIG` (config/services.yaml:2-6). Mock Amazon only has rates for those two bare ids on channel `EXTERNAL` (fixtures/amazon/amazon.json: SWA-UK-PREM "Amazon Shipping One Day" 3.5, SWA-UK-2D "Two Day" 2.75). `-SIG` is stripped (`replace(/-SIG/g,'')`) for the rate match (labelling.service.ts:211-214) |
| `labelSpecification` | `labelFormat` enum `ZPL|PDF|PNG`, `labelResolution` integer (DPI), both required (swagger.yaml:300-316). What is actually accepted: see Quirks (PDF refused; ZPL/PNG only at 203 or 300) |
| `channelDetails` | `channelType` required, enum `EXTERNAL|AMAZON`; optional `sellerDisplayName` (overrides profile displayName, then removed from the request), `amazonOrderDetails.orderId`. `AMAZON` -> 400 `{code:400,message:"Bad request",detail:"Amazon orders are not currently supported"}` unless `SUPPORT_SFP=true` (labelling.service.ts:153-159; mock runs SFP off, README:11-12). Use `EXTERNAL` |
| `consignment` | `weight{unit,value}` required. Only read when a package has no weight (below) |
| `shipFrom` | required by schema but ALWAYS REPLACED by the profile's warehouse site address (sites.yaml via `warehouse`, case-insensitive; no match -> default site + warning `Using default warehouse location`; no usable default -> built-in fake address) (labelling.service.ts:199-209). Whatever the caller sends is discarded |
| `shipTo` | `Address`: required `name`(1-60), `addressLine1`(1-60), `city`(1-50), `postalCode`(1-20), `stateOrRegion` (may be `""`). Optional `addressLine2/3`(minLength 1: empty string fails schema), `companyName`, `countryCode`(len 2), `email`(<=64), `phoneNumber`(1-20). `\r` removed and `\n`->space in lines 1-3 (labelling.service.ts:130-138). `countryCode` is NOT schema-required but mock Amazon rejects a rate request whose shipTo lacks addressLine1/city/postalCode/countryCode (mu-amazon:308-312), which surfaces as a generic 500 (see Error shape). So send `countryCode` |
| `packages` | array minItems 1, maxItems 1. Each requires `dimensions{length,width,height,unit INCH|CENTIMETER}`, `weight{unit GRAM|KILOGRAM|OUNCE|POUND, value}`, `packageClientReferenceId`, `insuredValue{unit GBP only, value>=0.01}`, `items[]` (min 1; each requires `quantity>=1` int and `weight`; optional `itemIdentifier`, `description`, `isHazmat`) (swagger.yaml:385-453) |
| `notes` | optional array of `{noteType:"DELIVERY", note}`. ANY presence, even `[]`, triggers the 200 `{}` quirk |

Code-vs-spec behaviours:
- Weight: units are passed through UNCONVERTED to Amazon (mock only checks value > 0, mu-amazon:319). If any package `weight.value` is falsy (0), the consignment weight value is split across packages with `calculateAvgWeights` and written back as `{unit:'KILOGRAM', value}` EVEN IF the consignment unit was GRAM/OUNCE/POUND (consignment unit is ignored), with a warning `Parcel reference <ref> has been given a default weight of <n>Kg` (labelling.service.ts:163-171, calculate-avg-weights.ts). Test: 1.5 KILOGRAM consignment -> 1.5Kg (create-label.test.ts:189-199).
- Dimensions: if any of length/width/height `=== 0`, the whole box is replaced from config/dims2.yaml: smallest set whose `maxWeightKg >= weight.value` (unit ignored: 500 GRAM looks up as 500 kg), the company's own box (case-insensitive `for` match) else `default`. Warning `Parcel reference <ref> has been given default dimensions of L x W x H`. The box object includes a `for` key which is forwarded to Amazon. No set big enough (>20 kg-ish; test uses 30 kg) -> 500 `{code:500,message:"No dims available",detail:"No default dimensions available for  30kg"}` (double space kept) (labelling.service.ts:173-186, dims-from-weight.ts:40-51, create-label.test.ts:234-246). Default boxes are CENTIMETER: 29.6x20.9x8.4 (<=2 kg), 39.1x30.1x14 (<=7), 45x35x25 (<=15), 55x45x35 (<=20) (config/dims2.yaml).
- `profile.displayName` goes on each package as `sellerDisplayName`; `amazonShipperId` -> `shipmentForShipperNumber` + `quoteForShipperNumber` (config `AMAZON_QUOTE_FOR_SHIPPER_NUMBER`, default `MOCKQUOTE0001`) (labelling.service.ts:188-222).
- `consignment`, `labelSpecification`, `serviceType` are deleted from the rates request (labelling.service.ts:124-128). `notes` is NOT deleted but the code throws before sending.
- Rates request sent upstream is otherwise the caller body (+ replaced shipFrom, address cleanup, `valueAddedServices:{signatureOnDelivery:{}}` for `-SIG`).
- Validation errors: 400 `{"code":400,"message":"Request failed schema validation","detail":"<first Ajv error in z-schema words> at <dotted.path> in request body"}`, e.g. `Missing required property: shipTo at  in request body` (two spaces when path empty), `No enum match for: X at serviceType in request body`, `Array is too long (2), maximum 1 at packages in request body` (app.ts:110-118, routes.test.ts:100-129). Only the first error is reported. Malformed JSON / wrong content-type / bad `mode` / no body: same 400 with `detail:"undefined at undefined in request body"` (routes.test.ts:131-152).
- Date formats: none in the request. Currency: GBP only. Country: ISO alpha-2.

### Response

- Create success: 201 `{"shipmentId":"mock-shp-<uuid>","packages":[{"trackingId":"TBA9999########","documents":{"label":{"labelStream":"<base64>"}}}],"warnings":[...]}`. `warnings` key is OMITTED when empty (labelling.service.ts:323-327; test create-label.test.ts:44-47). trackingId is at package level (`packages[].trackingId`), label at `packages[].documents.label.labelStream`. Only 1 package ever, only a `LABEL` document (`requestedDocumentTypes:['LABEL']`); no customs/invoice documents.
- `labelStream` = raw base64, no data-URI prefix. ZPL: base64 of ASCII text starting `^XA` (mu-amazon:141-151, create-label.test.ts:39-42). PNG: base64 PNG, 6x4 inch at requested DPI (mu-amazon:133-140). PDF: not obtainable (see Quirks).
- Mock tracking ids: `TBA9999` + 8 random digits (Amazon UK carrier AMZN_UK) (mu-amazon:122-126). Because the last digit is random, a freshly created parcel's first tracking poll returns a random stage.
- Validate success: 200 `{"warnings":[...]}`.
- Cancel success: 200, body `{}` (the Amazon `payload`) (labelling.service.ts:88, cancel-and-track.test.ts:28-31).
- Tracking success (200, key order): `{"trackingId":"..","trackingSummary":"PreTransit|InTransit|Delivered","events":[{"eventCode","location":{"city","stateOrRegion","countryCode","postalCode"},"eventTime":"<ISO>","shipmentType":"FORWARD"}...],"promisedDeliveryDate":"<ISO>","proofOfDelivery":{...}}`. `proofOfDelivery` only when delivered: `{deliveryLocationCoordinates:{latitude,longitude}, deliveryImageURL:"https://example.test/amazon/pod/<id>.jpg", receivedBy:"MOCK RECIPIENT"}`. `promisedDeliveryDate` and `proofOfDelivery` are `undefined` (key dropped) when absent (tracking.service.ts:86-92; mu-amazon:170-193; cancel-and-track.test.ts:66-82). Events are Amazon's raw objects, not mapped; `eventCode` values: `ReadyForReceive`, `PickupDone`, `ArrivedAtCarrierFacility`, `OutForDelivery`, `Delivered`.
- Tracking stage from the LAST CHAR of the tracking id (`Number(last)||0`, non-digit = 0): 0-1 -> 1 event `ReadyForReceive`, summary `PreTransit`; 2-5 -> 3 events (to `ArrivedAtCarrierFacility`), `InTransit`; 6-7 -> 4 events (adds `OutForDelivery`), `InTransit`; 8-9 -> 5 events (adds `Delivered`), `Delivered` + proofOfDelivery (mu-amazon:170-181). The README/E2 "2-7 InTransit" is right on summary but 6-7 have one more event than 2-5.
- Tracking events are time-relative to "now" (start = now - 3 days, +12 h per event); promisedDeliveryDate = now + 1 day (mu-amazon:174-186). Not deterministic across calls.

### Error shape

No single common shape. Three families:
1. Gate errors (ApiKy): `{message}` only (401/403/500) (app.ts:162,177,174).
2. createLabel / cancel / most tracking errors: `{code, message, detail}` with numeric `code` (labelling.service.ts, tracking.service.ts:31-35, 79-84). Exception: tracking 500 is `{"message":"Internal server error","detail":"Internal server error"}` with NO `code` (tracking.service.ts:75).
3. Schema 400: `{code:400, message:"Request failed schema validation", detail}`.
- Status codes seen: 200 (validate ok / cancel ok / catch-all / the `notes` quirk), 201, 400, 401, 403, 500, 501 (tracking, unknown channel), 404 (tracking not found), plus passthrough of LWA's status on cancel token failure (e.g. 401) and Amazon's status on cancel failure (e.g. 400, 500).
- createLabel: every Amazon failure (rates or purchase, any status incl. 400/403/429/500) -> HTTP 500 `{"code":500,"message":"Internal server error - <Amazon errors[0].details>","detail":"<axios-style message e.g. Request failed with status code 400>"}`. Mock Amazon always sends `details:""`, so `message` is literally `"Internal server error - "` (trailing `- `), and Amazon's own message text (e.g. "The ship to address is not valid.") is NOT surfaced anywhere (labelling.service.ts:329-340; mu-amazon:68-70, 339-342). Non-HTTP errors give `"Internal server error - undefined"`.
- createLabel token failure (bad LWA login / no credentials record): 500 `{code:500,message:"Internal server error",detail:"Internal server error"}` (labelling.service.ts:110-122).
- Other createLabel errors: 500 `No dims available` (above); 500 `No rate available` `detail: "No rate available for service <id> - <ineligibility reasons joined by ', ' or 'no reason provided'>. Available services are ['A','B']"` (so with NO RATE: `...SWA-UK-PREM - The destination is not serviceable.. Available services are []`, double period kept) (labelling.service.ts:245-258, create-label.test.ts:250-261); 500 `Label format unavailable` `detail: "No label format available for X. Available formats are ['PDF','PNG','ZPL']"` (can't trigger from the enum); 500 `Label resolution unavailable` `detail: "Requested label resolution <n>DPI not available. Available resolutions are [<list>]."` (labelling.service.ts:263-284).
- No LABEL document in purchase response: throws TypeError inside the try -> 500 `Internal server error - undefined` (labelling.service.ts:312-321).
- Cancel errors: token failure -> LWA's status with `{code:<status>, message:<LWA error>, detail:<error_description>}` (bad-lwa: 401 `invalid_client` / `Client authentication failed`) (labelling.service.ts:62-77, cancel-and-track.test.ts:56-62). Amazon failure -> Amazon's own status, `{code, message: errors[0].message, detail: errors[0].details || axios message}` (labelling.service.ts:89-97).
- Tracking errors: unknown channel 501 `{code:501,message:"Not implemented",detail:"Tracking API is not yet available for <channel as sent>"}`; Amazon 404 -> 404 `{code:404,message:"Not found",detail:"The requested shipment could not be found"}`; everything else incl. token failure and Amazon 429/500 -> 500 no-code body above.
- Malformed JSON on createLabel: 400 (NOT 500) `{code:400,message:"Request failed schema validation",detail:"undefined at undefined in request body"}` (routes.test.ts:131-138). Contrast bjs (500).
- Uncaught handler error (outside the controller `.catch`): 500 `text/plain` `Internal Server Error` (app.ts:230-233).

### Failure scenarios for D5 (magic values)

Magic values live in mock Amazon (`mu-amazon`). Normalisation: postal code magic = strip ALL whitespace then uppercase, then equality with the whitespace-stripped magic, so `err400`, `Err 400`, `ERR  400` all fire (mu-amazon:60-61). Id prefixes: case-insensitive `startsWith` (mu-amazon:62). They are checked on `shipTo.postalCode` as the proxy forwards it (after address cleanup; postal code is untouched), and only AFTER mock Amazon's own validation (addresses, 1-5 packages, positive weight/dims, 1-100 items, channelType) passes (mu-amazon:309-336).

| Operation | Field | Magic value | Where verified | What the caller sees |
| --- | --- | --- | --- | --- |
| create, validate | `shipTo.postalCode` | `ERR 400` | mu-amazon:339-342; create-label.test.ts:369-372 | Amazon 400 -> proxy 500 `{code:500,message:"Internal server error - ",detail:"Request failed with status code 400"}` (also in validate mode, since rates are called) |
| create, validate | `shipTo.postalCode` | `ERR 403` | mu-amazon:343-346 | Amazon 403 -> same 500, detail `...status code 403` |
| create, validate | `shipTo.postalCode` | `ERR 500` | mu-amazon:347-350; create-label.test.ts:384-387 | 500 same shape, detail `...500`; POST so NOT retried (1 call) |
| create, validate | `shipTo.postalCode` | `ERR 429` | mu-amazon:351-354; test:374-377 | proxy retries 3x on 429 (4 upstream calls, backoff 200/400/800 ms, ~1.5 s added), then 500 detail `...status code 429` |
| create, validate | `shipTo.postalCode` | `RETRY 429` | mu-amazon:355-358, throttleOnce keyed on the signed `Authorization` header; test:379-382 | first call 429, retry succeeds -> normal 201 (or 200 for validate). Adds ~200 ms. Caveat: keyed on the SigV4 signature, so two caller requests that sign identically (same second, same body) share the "already throttled" memory |
| create, validate | `shipTo.postalCode` | `NO RATE` | mu-amazon:361-362, 417-419; test:250-261, 322-328 | create: 500 `message:"No rate available"` + detail above; validate: 400 `Invalid request` |
| create only | `shipTo.postalCode` | `BUY 500` | mu-amazon:404, 469-472; test:389-393 | rates OK, purchase 500 -> 500 `Internal server error - ` / `...status code 500`. Validate returns 200 (never buys) |
| create | `shipTo.postalCode` | `BT...` | labelling.service.ts:140-146; test:342-352 | 400 `Bad request`/`BT postal codes are not supported` ONLY with `SUPPORT_WINDSOR=true` (default off, so the mock sends it on and returns 201). Proxy-side, not mock Amazon |
| cancel | `{shipmentId}` prefix | `UNKNOWN` | mu-amazon:509-512; cancel-and-track.test.ts:39-49 | HTTP 400 (NOT 404) `{code:400,message:"The shipment could not be found.",detail:"Request failed with status code 400"}` |
| cancel | `{shipmentId}` prefix | `ERR500` | mu-amazon:513-516; test:51-54 | PUT 5xx retried 3x (4 upstream calls) -> 500 `{code:500,message:"We encountered an internal error. Please try again.",detail:"Request failed with status code 500"}` |
| cancel | `{shipmentId}` prefix | `ERR429`, `RETRY429` | mu-amazon:507-518 (no branch) | NOT special on cancel: 200 `{}` (README table says "none") |
| track | `{trackingId}` prefix | `UNKNOWN` | mu-amazon:527-530; test:102-108 | 404 `{code:404,message:"Not found",detail:"The requested shipment could not be found"}` |
| track | `{trackingId}` prefix | `ERR500` | mu-amazon:531-534; test:110-116 | 500 `{"message":"Internal server error","detail":"Internal server error"}` (no code). GET so retried 3x upstream |
| track | `{trackingId}` prefix | `ERR429` | mu-amazon:535-538; test:118-121 | 429 every time, 4 upstream calls, then the same no-code 500 |
| track | `{trackingId}` prefix | `RETRY429` | mu-amazon:539-542; test:123-126 | 200 after one retry |
| track | `{trackingId}` last char | 0-1 / 2-7 / 8-9 | mu-amazon:170-181 | PreTransit / InTransit / Delivered(+proofOfDelivery) |
| track | `{channelType}` | anything but `external`, `sfp-amazon`, `sfp-evri` (case-insensitive) | tracking.service.ts:23-36; test:94-100 | 501 Not implemented. `sfp-evri` -> carrierId `HERMES_UK`, others `AMZN_UK`; ids shorter than 64 chars; mock requires carrierId in {AMZN_UK,HERMES_UK} (mu-amazon:521-526) |
| all | `x-api-key` | `amzl-key-bad-lwa` | credentials.json (company `AMZL DELTA`, wrong client secret); labelling.service.ts:110-122; test create-label.test.ts:150-156 | create: 500 bare `{code:500,message:"Internal server error",detail:"Internal server error"}`; cancel: 401 `invalid_client`; track with company `AMZL DELTA` in the URL: 500 no-code |
| create | `x-api-key` | `amzl-key-bad-aws` | AMZL ECHO has an unknown AWS access key id; mu-amazon:285-288; test:158-164 | Amazon 403 -> 500 `{message:"Internal server error - ",detail:"Request failed with status code 403"}` (create/cancel; tracking signs with the GFS key so is unaffected) |
| all | `x-api-key` | `apiky-500` | app.ts:170-174 | 500 `{message:"Internal server error"}` after ~1.5 s of ApiKy retries |
| create | `serviceType` | any `-SIG` id, create only | mu-amazon:360, 462-468; create-label.test.ts:268-275 | 500 `Internal server error - ` / `Request failed with status code 400` (see Quirks). Validate: 200 |
| create | `labelSpecification.labelFormat` | `PDF` (any resolution) | labelling.service.ts:270-284; test:300-308 | 500 `{code:500,message:"Label resolution unavailable",detail:"Requested label resolution <n>DPI not available. Available resolutions are []."}`. Validate: 200 |
| create | `labelSpecification.labelResolution` | any value other than 203/300 for ZPL/PNG (e.g. 600, 0) | labelling.service.ts:270-284; test:285-298 | 500 `Label resolution unavailable` `...Available resolutions are [203, 300].` |
| create | `notes` | any array | labelling.service.ts:148-151; test:332-340 | 200 `{}` (see Quirks) |

### Quirks mirrored from production

(README marks these "mirrored on purpose" from the ADO source; none is verified against prod traffic. The proxy logic is a port, so the proxy-side behaviour is real to the source; the Amazon-side premises are mock-modelled.)

- **PDF refusal (exact).** Trigger: `labelSpecification.labelFormat == "PDF"`, any `labelResolution` (even 0 or 203). Path: mock Amazon lists three PDF document specs (11x8.5 in, 15x10 cm, 6x4 in), each with `supportedDPIs: []` (mu-amazon:81-87). The proxy picks `specs.find(s => s.format === 'PDF')` = the FIRST PDF spec (11x8.5 in) (labelling.service.ts:261), then requires `po.supportedDPIs.some(dpi == requested)`; `[].some` is false (labelling.service.ts:271-278); the fallback list shown is the empty `supportedDPIs`. Result: HTTP 500 `{"code":500,"message":"Label resolution unavailable","detail":"Requested label resolution 203DPI not available. Available resolutions are []."}`. The `Label format unavailable` message is not used: PDF format IS found. Purchase is never attempted. Validate mode skips this block so `?mode=validate` with PDF returns 200 (labelling.service.ts:234-241 returns before 260). The SFP proxy handles it with `po.supportedDPIs.length === 0 ||` (apps/amazon-sfp-proxy/src/handlers/labelling.handler.ts:280, and only sends `dpi` when DPIs exist, :304-306); this proxy lacks both. ACCEPTED formats: `ZPL` and `PNG`, 6x4 inch only, DPI exactly 203 or 300 (`==` comparison so `"203"` would match, but swagger types it integer so strings 400 earlier). The `find` takes the first spec in the format, so if PDF were ever fixed it would buy the 11x8.5 in one, not 6x4 (mock models this on purpose, mu-amazon:80). Whether real Amazon lists no DPIs for PDF: UNVERIFIED (inferred from the SFP proxy's special-casing, not observed).
- **`notes` -> 200 `{}` (exact).** `if (ratesRequest.notes) throw new ReferenceError('notes is not defined')` (labelling.service.ts:148-151; the comment says the source reads an undeclared variable). `[]` is truthy so even an empty array fires. The controller `.catch` calls `writeJson(res, e)`; an Error is not a `ResponsePayload` so it is sent as HTTP 200, and `JSON.stringify(new Error())` is `"{}"` (app.ts:204-207, writer.ts:14-19). Result: 200, body `{}`, no label, no Amazon rates call, even with `?mode=validate`. Position in the pipeline: AFTER swagger validation (so `notes` items must still be `{noteType:"DELIVERY",note:string}` or you get the 400), AFTER ApiKy, AFTER the LWA token fetch (a bad-lwa key gets its 500 first), AFTER the Windsor BT check (when enabled), BEFORE the AMAZON-channel check, dims and weight logic. A caller that checks only `status===200` will think a label was created: the body has no `shipmentId`/`packages`. The test suite pins it as "source quirk" (create-label.test.ts:331-340).
- **`-SIG` refusal (exact) and its provenance.** `-SIG` ids are in the enum (services.yaml:5-6). The proxy strips `-SIG`, sets `ratesRequest.valueAddedServices = { signatureOnDelivery: {} }` and matches the rate on the bare id (labelling.service.ts:211-217). Mock Amazon, seeing `signatureOnDelivery`, adds +1 to the charge, marks group `DELIVERY_CONFIRMATION_GROUP` `isRequired:true` and records `signature:true` in the requestToken (mu-amazon:360, 371, 379-388, 394-399). The proxy's purchase body is only `{requestToken, rateId, requestedDocumentSpecification}` (labelling.service.ts:294-298): it never sends `requestedValueAddedServices`. Mock Amazon refuses: 400 `InvalidInput "DELIVERY_CONFIRMATION is a required value-added service for this rate."` (mu-amazon:462-468). The proxy turns that into HTTP 500 `{"code":500,"message":"Internal server error - ","detail":"Request failed with status code 400"}`; the Amazon message text is lost (create-label.test.ts:268-275 asserts only status 500, detail `Request failed with status code 400` and no `requestedValueAddedServices` in the purchase). Validate mode returns 200 for `-SIG`. So `-SIG` can never be bought through this mock, but passes validate.
- **Is E2's "inferred from the SFP proxy's code" right?** Yes as a statement of provenance, and the mock README says the same (apps/amazon-logistics-proxy/README.md:210). Evidence chain: (a) the SFP proxy DOES add `requestedValueAddedServices:[{id:'DELIVERY_CONFIRMATION'}]` when the chosen rate has a required VAS group (apps/amazon-sfp-proxy/src/handlers/labelling.handler.ts:308-320, comment "Amazon only accepts DELIVERY_CONFIRMATION"); (b) this proxy's code has no equivalent (labelling.service.ts:260-310), and a git grep for `DELIVERY_CONFIRMATION` / `requestedValueAddedServices` in apps/amazon-logistics-proxy/src returns nothing; (c) the enforcement of "required group must be requested" exists only in mock Amazon (mu-amazon:379-388, 462-468), written for this proxy's mock (commit 5737fee "Mock Amazon Logistics carrier proxy (#5)"). Nothing in the repo shows prod Amazon rejecting a logistics `-SIG` purchase. UNVERIFIED against prod: the refusal is proxy-source-faithful (the omission is real in the ported code) but Amazon's response to it is modelled, not observed.
- Ineligible service outside validate mode is a 500, not 400 (labelling.service.ts:245-258); inside validate it is a 400.
- `ENABLE_MULTICOMPANY` read for truthiness, `false` is on (config.ts:60, README:251). `AMAZON_ENVIRONMENT` unset = production, empty string = sandbox (config.ts:46-47). These are env facts not visible to callers.
- Access token is fetched before the Windsor/SFP checks, so an LWA failure hides their 400s (labelling.service.ts:110-146).
- Retry behaviour visible to callers: 429 or no-answer retried 3x for any method; 5xx retried 3x only for GET/PUT (so cancel and tracking 5xx retry, rates/purchase 5xx do NOT) (http-client.ts:29-35). Backoff 2^n*100 ms (+up to 20%); a `Retry-After` header is read as milliseconds (http-client.ts:37-43). Caller-visible latency: ~1.5 s on the ERR 429 / cancel ERR500 / track ERR500 paths.
- Tracking id placed into Amazon's query string unencoded (amazon-api-client.ts:54-58).
- Tracking token/signature split: LWA token for the URL `{company}`, SigV4 for company `""` which resolves to the `GFS` record (tracking.service.ts:43, 52-57; test cancel-and-track.test.ts:129-163). The caller's x-api-key only has to be a valid key; its profile company is irrelevant to tracking. An unknown company name falls back to GFS. A company whose login fails (`AMZL DELTA`) gives 500 whoever calls.
- `ApiKy` unreachable (network) = treated as ApiKy 500 (README:222-223).

### Statefulness / ordering constraints

- Fully stateless upstream: the rates `requestToken` is a self-contained base64url blob valid 600 s, carrying the rate ids, signature flag and failPurchase flag; the mock keeps no shipment store (mu-amazon:103-120, 392-405). Proxy keeps only an LWA access-token cache (5 min, per company, shared by label/cancel/track) and throttle-once memory in the mock (up to 1000 signatures).
- Rates-then-purchase is internal to one createLabel call; callers do one POST. There is no separate "rate" operation to expose. Purchase reuses `requestToken` and the first `rateId` for the chosen service from the same rates response (labelling.service.ts:232, 294-298).
- Cancel needs no prior create: any id not prefixed `UNKNOWN`/`ERR500` returns 200 `{}`, including ids never issued and ids cancelled before. Cancel twice succeeds twice. Cancel a created `mock-shp-<uuid>` works. Cancel takes the shipment id (`shipmentId`), not the tracking id.
- Tracking needs no prior create: it derives from the id string, so any `TBA...` id works. Tracking id of a created parcel is NOT linked to cancel state (cancelling does not change tracking).
- Idempotency: none. Calling create twice produces two shipments with different `mock-shp-` ids and tracking ids. No de-dup on `packageClientReferenceId`.
- Single package per request (maxItems 1): a multi-parcel consignment needs one createLabel per parcel (each gets its own shipmentId).

### Adapter implications and leaks

- Cancel uses the Amazon `shipmentId` (from the create response) in the URL path with POST; tracking uses the `trackingId` and needs the `company` NAME in the path (e.g. `AMZL ALPHA`, URL-encode the space) plus `channelType` `external`. A generic adapter must store both ids per parcel and the company name (not derivable from the API key response).
- Validate = `?mode=validate`, but it is weaker than create: it will pass PDF, `-SIG` and anything else that fails later. A generic "validate then ship" flow cannot rely on validate to predict create success for this carrier.
- Success signalling is not just HTTP status: `notes` returns 200 with `{}`. Adapter must check for `shipmentId` and `packages[0].trackingId` + `labelStream` on a 200/201, and treat a 200 without them as failure. Also the catch-all 200 `{code:200,message:"OK"...}` for any wrong path.
- No `commit-manifest`, no `reprint`: calls to such paths (even valid-looking ones under `/shipping`) return 200 OK with the "Server is OK" body. An adapter must NOT map unsupported operations to this host. Never treat the catch-all 200 as success.
- Request the label as ZPL or PNG at 203/300 DPI only; never PDF (PNG for a printable raster, ZPL for thermal). `labelResolution` is always required even for formats where it is meaningless. 6x4 inch only.
- Refuse/strip `notes` before sending (or deliberately drop delivery notes for this carrier); do not set `channelType: AMAZON`; do not send `-SIG` services.
- `shipFrom` content is ignored (replaced from the profile warehouse); the sender address the caller sends never reaches Amazon. Profile warehouse name must exist in sites.yaml or a warning appears.
- Weight/dims: send positive weights and real dims in a supported unit. Zero weight/dim triggers default substitution (unit-blind, consignment unit ignored, so a GRAM consignment would be treated as kg). Warnings arrive in the 201 `warnings[]` and must be surfaced or tolerated.
- Error bodies lose Amazon's reason text (mock `details` empty), so error mapping must key on `message`+`detail` strings, e.g. `No rate available`, `Label resolution unavailable`, `No dims available`, `Internal server error - `. Three distinct body shapes (gate `{message}`, `{code,message,detail}`, no-code tracking 500). Status mapping: carrier failure is HTTP 500 for create; cancel passes Amazon's status (400/500); tracking uses 404/501/500.
- `x-api-key` check ordering differs between create (validation first) and cancel/track (key first). Latency budget: failure paths can take 1.5 s+ because of 3 upstream retries; cold start extra.
- Auth model for tracking is company-name-in-URL; with the internal deployment it needs no key, with the secured one any valid key. ApiKy company drives which Amazon credentials are used for create/cancel.

### README-vs-source discrepancies, and UNVERIFIED

README-vs-source:
- README table says `-SIG` is stripped and "asks Amazon for `signatureOnDelivery`" and the quirk section says "never send the delivery-confirmation add-on": consistent with source. README:158 says cancel of `UNKNOWN` gives "Amazon's 400: caller gets 400 `The shipment could not be found.`": the 400 is the HTTP status and that string is `message`; `detail` is the axios text `Request failed with status code 400` (test:39-49). Not a discrepancy, just imprecise.
- README:63 error table row "200 body `{}`: Any request with `notes`" is correct but omits that it happens after token fetch, so with `amzl-key-bad-lwa` a notes request is a 500 not a 200.
- README:60 lists `Label format unavailable`; unreachable for current enum (ZPL/PDF/PNG all present in mock Amazon).
- README:143-151 magic table says ERR 400/ERR 403 give "500 `Internal server error - ` with `Request failed with status code 400`/`403`": correct; but it omits that Amazon's own message text is never surfaced.
- README says `services.yaml` mounts `SWA-UK-PREM`, `SWA-UK-2D` + `-SIG`; swagger.yaml enum (`SWA-UK-PRIME-*`) is overridden and misleading (swagger.ts:15-21). `/api-docs` shows the effective enum.
- swagger.yaml `Error.code` is a string and `details` (not `detail`) while code sends numeric `code` and `detail` (README:259-260 acknowledges).
- swagger.yaml documents cancel as `POST` and tracking `X-API-Key` 401/403 only; actual bad key 500 on ApiKy outage is not in the spec.
- Spec says `consignment` is required but the code only reads it when a package weight is 0; `shipFrom` required but discarded.
- The `/docs` Swagger UI is not served (README:218-219); only `/api-docs`.

UNVERIFIED:
- Real Amazon behaviour behind PDF (empty `supportedDPIs`) and `-SIG` (required delivery-confirmation group): inferred from the SFP proxy and from mock modelling, not seen in prod traffic or Amazon docs in this repo.
- That connectors-amazon polls `GET {endpoint}/external/{company}/{parcel}` (stated in README:25; no consumer code in this repo).
- Cloud Run edge IAM treatment of an inbound `Authorization: Bearer` (outside app code).
- Whether very large weights (>20 kg) with non-zero dims pass: mock Amazon has no upper weight check (mu-amazon:317-324), so only the zero-dims path hits "No dims available". Mock Amazon limits (max 5 packages, max 100 items, max DPI 600) are not reachable through the 1-package schema except items.
- Behaviour of negative dimensions or non-numeric weights past schema (Ajv catches types; negative values reach Amazon where `>0` is checked and give the generic 500).

### Notes for the E2 draft

Claims at E2 lines 26, 57, 69, 127-135, 180 about `amazon`:
- Line 180 "Amazon Logistics refuses PDF labels": correct but imprecise. It is the create call only; `?mode=validate` accepts PDF with 200. Exact failure: 500 `Label resolution unavailable` / `...Available resolutions are [].` (labelling.service.ts:280-284). Accepted formats: ZPL and PNG only, 203 or 300 DPI. Worth stating so Selector2 requests ZPL/PNG.
- Line 180 "answers 200 `{}` to any request with `notes`": correct (even `notes: []`, even in validate mode). Add: it is after the LWA token fetch, so `amzl-key-bad-lwa` gets the 500 first; swagger validation still applies to note items.
- Line 180 "refuses `-SIG` services": correct for create (500 `Internal server error - ` / `Request failed with status code 400`), but `?mode=validate` returns 200 for `-SIG`. "The `-SIG` case is inferred from the SFP proxy's code": TRUE and fairly stated: the refusal is enforced by mock Amazon only (mu-amazon:462-468) and the omission is in this proxy's code; prod's Amazon behaviour is not observed. The README itself says it is "not confirmed against this proxy in prod" (README:210). The E2 wording is acceptable; if "read from the source code" is the page's framing (line 177), the -SIG item is an exception that the page already flags.
- Line 133 "Tracking or shipment id prefix ... Tracking: 404, 500, 500, 200 on retry. Cancel: see the README": tracking part correct. For cancel the real behaviour is: `UNKNOWN` -> HTTP 400 (not 404) with message "The shipment could not be found."; `ERR500` -> 500 (after 3 retries); `ERR429` and `RETRY429` do nothing on cancel (200 `{}`). The "ERR429/RETRY429 prefix" row applies to tracking only. Also the row conflates "tracking id prefix" and "shipment id prefix".
- Line 134 "Tracking id, no prefix, last digit 0-1 / 2-7 / 8-9": correct for the summary; 2-5 and 6-7 differ in event count (3 vs 4). Non-digit last char = stage 0.
- Line 127 "ERR 400, ERR 403 -> 500 carrying Amazon's status": the 500's `detail` carries `Request failed with status code 400/403`; Amazon's message is not carried (message is `Internal server error - ` with empty tail).
- Line 135 `amzl-key-bad-lwa`: 500 on create, but 401 `invalid_client` on cancel, and 500 no-code on tracking only if the company in the URL is `AMZL DELTA` (the token follows the URL company, not the key). `amzl-key-bad-aws` only breaks create/cancel (tracking signs with the GFS record). E2 text says "(`amzl-key-…` on `amazon`)" which is right but the bad-key ids are `amzl-key-bad-lwa` / `amzl-key-bad-aws`.
- Line 69 bad-key table "amazon: 401 / 403 / 500": correct (bodies `{message}` only: "No API key provided", "Not authorised", "Internal server error"). Add that for `createLabel` a schema-invalid body returns 400 before the key check.
- Line 57 keys: `amzl-key-alpha` / `amzl-key-bravo` correct; `amzl-key-bravo` works but yields the `Using default warehouse location` warning in the 201 and signs with the env-var AWS key. Other fixture names exist (`-fallback`, `-box-dims`, `-no-profile`).
- Line 26 row: accurate. Missing: no validate-vs-create parity, no manifest/reprint, catch-all 200 trap, create returns exactly one package.


---

## bjs (BJS Home Delivery; apps/bjs-proxy; mirrors bjs.gfsdeliver.com)

Paths relative to repo root, lines from origin/main. `mu-bjs` = `apps/mock-upstreams/src/bjs/index.ts`. Default port 4108. Follows the ADO `bjs-proxy` (not the GitHub copy) (README.md:3-11). Books furniture-style one-man/two-man/1.5-man deliveries; BJS "orders" are created, not "shipments".

### Operations and routes

| Operation | METHOD path | Supported? | Notes |
| --- | --- | --- | --- |
| validate | none | NOT supported | No `mode=validate`, no dry-run. Every valid request creates a real (mock) order |
| create-ship | POST `/shipping/createLabel` | yes | Builds a BJS order form, `POST {BJS}/v1/order/create`, downloads the one PDF BJS links to, splits it per page, pairs page i with BJS product i. 201 (bjs-integration.ts:44-77, bjs-service.ts:114-136) |
| delete-cancel | POST `/shipping/cancelShipment` | yes | JSON body `{accountId, reason, shipmentId}` (all required). `PUT {BJS}/v1/order/cancel` with header `CarrierReference` and form body `CancelledReason`. 204, empty body (bjs-integration.ts:79-106, app.ts:74-77) |
| commit-manifest | none | NOT supported | unknown path: 400 `VALIDATION ERROR` "Requested path not found" |
| reprint | none | NOT supported | same; the label is only returned at create |
| track | none | NOT supported | tracking number = per-package barcode returned at create; no tracking route in this proxy |
| other | GET `/` -> 200 `ok` (text); GET `/health/liveness` -> 200 `{"ok":true}` | both unauthenticated | not in OpenAPI; liveness is not logged (app.ts:55-64) |

Routing is by openapi-backend 5.19.0 against api/bjs-integration-api.yaml. Paths are case-sensitive, a trailing slash is ignored (routes.test.ts:49-63). A known path with the wrong method is the same "Requested path not found" 400 (method lower-case in `metaData.request.method`) (app.ts:84-90, routes.test.ts:44-47).

### Auth and headers

- Header: `x-api-key` (yaml:367-371). Pipeline order (README:24-26, routes.test.ts:88-91): route, then security (ApiKy), then request schema. So a bad body with no/invalid key is a 403, not a 400 (opposite of amazon).
- ApiKy profile lookup once, no retry (apiky-integration.ts:5-21). The profile's `profile.bjsSecret` becomes the BJS `Key` header (bjs-integration.ts:46, 58). The BJS account is NOT from the profile: it is the caller's `accountId` (README:157-158).
- Key fixtures (apps/mock-upstreams/fixtures/apiky/bjs.json): `bjs-key-alpha` (secret for account `MOCKBJS01`), `bjs-key-bravo` (secret for `MOCKBJS02`), `bjs-key-wrong-secret` (a secret BJS does not know), `bjs-key-no-secret` (`profile: {}`; no `Key` header is sent), `bjs-key-malformed-profile` (no `profile` block), `apiky-500`. Secret values elided. Mock BJS accounts: `MOCKBJS01`, `MOCKBJS02` (fixtures/bjs/bjs.json); each account's key must match (mu-bjs:98-101), so `bjs-key-bravo` with `MOCKBJS01` is refused by BJS.
- Missing key, ApiKy-rejected key, and ApiKy down (`apiky-500`) all produce 403 `{"code":"FORBIDDEN","message":"Authentication failed","details":"Principal undefined could not be authenticated. No additional detail was provided."}` (exceptions.ts:25-37; routes.test.ts:66-86). Non-string key header = same.
- `bjs-key-malformed-profile`: 500 generic "An unexpected error occurred" (`principal.profile.bjsSecret` on undefined) (routes.test.ts:98-101).
- `Authorization: Bearer` inbound: never read by app code (git grep `authorization` in apps/bjs-proxy/src: no hits); ignored. The ID-token wrapper (main.ts:7) is outbound-only. UNVERIFIED: Cloud Run edge IAM behaviour.
- Content-type: JSON body parsed by `express.json()` (100 kb limit, app.ts:60-61). Request needs `content-type: application/json`. UNVERIFIED what a POST with no/other content-type returns (openapi-backend sees no body; not tested).

### Request

Schema: api/bjs-integration-api.yaml `CreateLabelRequest` (yaml:60-155). Ajv reports only the first error. Unknown properties allowed.

Required (create): `accountId`, `labelSpecification{labelFormat: "PDF"|"PNG"}`, `shipFrom`, `shipTo`, `packages` (1-99 items), `serviceCode` (string), `orderNumber` (yaml:63-70). Optional: `deliveryInstructions`, `otherInstructions`, `orderReference`, `statusNote`. Read by code but NOT in the spec: `tradingName`, `released` (bjs-service.ts:84-85).

`Address` (shipFrom and shipTo): required `name`(1-60), `addressLine1`(1-60), `city`(1-50), `postalCode`(1-20), `stateOrRegion` (required, can be `""`; no default applied) (yaml:156-163). Optional: `companyName`(<=35), `addressLine2/3`(minLength 1), `countryCode`(2 chars), `whatThreeWords`, `contactName`, `email`(<=64), `phoneNumber`(1-20), `vat`, `eori`. `countryCode`, `companyName`, `vat` are never read by the code (UK domestic only; no international handling).

`Package`: NO required fields. `weight{unit GRAM|KILOGRAM, value}` (both required if weight present; OUNCE/POUND are not valid), `dimensions{length,width,height,unit INCH|CENTIMETER}` (no required keys), `description`, `productCode`; `clientReferenceId` appears in the spec example but is not in the schema and not read.

Field mapping to the BJS form (`application/x-www-form-urlencoded`, header `Response: json`, header `AccountNumber`, header `Key`) (bjs-service.ts:69-111, bjs-integration.ts:34-62):

| BJS form field | From |
| --- | --- |
| `Released` | `released?.toString() \|\| 'True'` (so `false` -> `"false"`, absent -> `"True"`) |
| `TradingName` | `tradingName \|\| shipFrom.name` |
| `OrderNumber` | `orderNumber` |
| `Recipient` | `shipTo.name \|\| shipTo.contactName` |
| `Address` | `addressLine1, addressLine2, addressLine3, city, stateOrRegion` joined by `", "`, blank/whitespace parts dropped (bjs-service.ts:23-30). Postcode is separate |
| `Postcode` | `shipTo.postalCode` (raw) |
| `Products` | JSON string, see below |
| `OrderReference`, `ContactMobile` (`shipTo.phoneNumber`), `ContactEmail` (`shipTo.email`), `DeliveryInstructions`, `OtherInstructions`, `StatusNote` | straight; ABSENT => the literal string `"undefined"` is sent (every value goes through `String()`; bjs-integration.ts:34-37) |
| `ExpressRequired` | `"true"` / `"false"` / `"null"` from the accountId prefix |
| `ServiceType`, `TimedService`, `ServiceLevel`, `DeliveryPoint`, `OrderType` | from the service-code table, included only when set |
| `what3words` | `shipTo.whatThreeWords` if set |
| `ConsignorEORI` | `shipFrom.eori` if set |

**accountId prefix rule** (bjs-integration.ts:21-31; mapping.test.ts:11-27): `accountId` is a string. If the first character (any case) is `S` -> strip it, `ExpressRequired="false"`; `E` -> strip, `ExpressRequired="true"`. Any other first character: account used as is and `ExpressRequired="null"` (the string, since `String(null)`). Empty or non-string `accountId`: no strip, `expressFlag=null`. The same stripping applies to cancel (without ExpressRequired). Valid mock accounts: `SMOCKBJS01`, `EMOCKBJS01`, `MOCKBJS01` (and `...02`). Because stripping is purely on the first letter, a real account number that begins with S or E would be damaged unless the caller always prefixes. Mock BJS ignores `ExpressRequired`.

**Service codes** (`serviceCode`, case-sensitive exact match via `Object.hasOwn`; src/services/servicecode-mapping.ts:12-234; 24 codes):

| Code(s) | ServiceLevel | Flags | Product `Type` |
| --- | --- | --- | --- |
| `1MAN` | 1 Man | none | Deliver |
| `1SAT` / `1SUN` | 1 Man | `ServiceType` Sat / Sun | Deliver |
| `1MAM` / `1MPM` / `1EVE` | 1 Man | `TimedService` AM / PM / Evening | Deliver |
| `1RTS` | 1 Man | `OrderType` Return | Collect, `CollectionAction: "RTS"` |
| `1EXC` | 1 Man | `OrderType` Standard | per package: Deliver AND a Collect copy (EXCHANGE_CODES, bjs-service.ts:20, 42, 63) |
| `2MAN` | 2 Man | none | Deliver |
| `2ROC` | 2 Man | `DeliveryPoint` Room Of Choice | Deliver |
| `2SAT` / `2SUN` / `2MAM` / `2MPM` / `2EVE` | 2 Man | as the 1-man equivalents | Deliver |
| `2RTS` | 2 Man | `OrderType` Return | Collect, NO CollectionAction |
| `2EXC` | 2 Man | `OrderType` Standard | per package: Deliver AND a Collect copy |
| `15MN`, `15SA`, `15SU`, `15AM`, `15PM`, `15EV` | 1.5 Man | `DeliveryPoint` Hallway; Sat / Sun / AM / PM / Evening for the suffix | Deliver |
| `15EX` | 1.5 Man | Hallway, `OrderType` Standard | ONE item of Type `"Deliver and Collect"` per package (NOT split into two) |

Unknown code (including the spec's own example `"Standard"`, case variants like `2man`): the mapper throws; caught and rethrown as InternalError -> 500 `{"code":"INTERNAL SERVER ERROR","message":"An internal server error occurred","details":"An internal server error occurred. No additonal detail is available."}`, no BJS call made (bjs-service.ts:74-110, servicecode-mapping.ts:232-234; create-label.test.ts:220-228).

**Products JSON** (one entry per package; bjs-service.ts:36-66): `Type`, `Code`(=`productCode`), `Description`, `Weight` (kg string: GRAM/1000, KILOGRAM as is; `toString()`, so 92.5 -> `"92.5"`), `Height`/`Width`/`Length` (METRES: CENTIMETER/100; anything else, including MISSING unit, treated as INCH*0.0254), `Cube` (m3, 3 dp, `"0"` when no `dimensions`), `CollectionAction` when the service has one. All values are strings. A dimensions object missing a side gives `"NaN"` strings (mapping.test.ts:98-102). Absent weight => `Weight` omitted (JSON.stringify drops undefined).

Validation errors: 400 `{"code":"VALIDATION ERROR","message":"Client request failed validation","details":"Failed to validate client request","metaData":{"0":{"instancePath":"/requestBody","schemaPath":"#/properties/requestBody/required","keyword":"required","params":{"missingProperty":"orderNumber"},"message":"must have required property 'orderNumber'"}}}`. `metaData` is Ajv's first error as an OBJECT keyed `"0"` (the source spreads the array) (exceptions.ts:43-49, routes.test.ts:105-125). `instancePath` is `/requestBody` + nested path.

Weight units in the schema: GRAM and KILOGRAM only. Dimension units INCH, CENTIMETER. No currency. No dates.

### Response

Create success 201 (bjs-service.ts:130-135, yaml:303-347):
`{"shipmentId":"MOCKBJS-########","secondaryShipmentId":"<same>","warnings":[],"packages":[{"documents":{"label":{"labelStream":"<base64 single-page PDF>"},"trackingId":"MOCKBJS-########-001"}}, ...]}`.
- `shipmentId` and `secondaryShipmentId` are both BJS `result.carrier_reference`. `warnings` is always `[]`.
- trackingId is under `packages[].documents.trackingId` (NOT at package level, differs from amazon where it is `packages[].trackingId`). It is BJS's per-product `barcode`.
- Labels: BJS returns `result.labels` = ONE URL to ONE multi-page PDF; the proxy GETs it (no auth header) and splits it with pdf-lib into one single-page PDF per page, base64, no data-URI (pdf-label-splitter.ts:5-24). Page i is paired with `result.products[i].barcode`, so pairing is by POSITION (bjs-service.ts:122-128).
- One label per BJS PRODUCT, not per package: `1EXC`/`2EXC` send two products per package so the caller gets 2 labels per package, interleaved Deliver, Collect per package (mu-bjs:160-165; create-label.test.ts:192-200; smoke.mts BJS section). Response items carry no Deliver/Collect marker, only the barcode index. UNVERIFIED how real BJS labels/orders collect copies.
- `labelFormat` is IGNORED: PNG request gets PDFs (create-label.test.ts:70-73). Only PDF is ever returned. `labelSpecification.labelFormat` enum is `PDF|PNG` only; `ZPL`/`EPL` -> 400 validation (routes.test.ts:140-143).
- No customs/invoice document. No tracking URL.
- Mock BJS result (invented envelope; README:119-125): `{"success":true,"result":{"carrier_reference":"MOCKBJS-########","order_number":..,"labels":"<origin>/bjs/v1/labels/<ref>?count=N","products":[{"barcode":"<ref>-001","type":..,"code":..}]}}` (mu-bjs:154-166). Label PDFs are mock-kit pages (MOCK LABEL - NOT FOR CARRIAGE, no address) (mu-bjs:77-91).
- Cancel success: 204, empty body (cancel-shipment.test.ts:19-22).

### Error shape

Common shape (exceptions.ts:1-81, global-error.ts:26-35): `{ "code": "<CODE>", "message": "...", "details": ... }`, `code` is a STRING with spaces (not a number). Validation errors add `metaData`.

| Status | `code` | `message` | `details` | When |
| --- | --- | --- | --- | --- |
| 400 | `VALIDATION ERROR` | `Client request failed validation` | `Failed to validate client request` (+ `metaData` Ajv error) or `Requested path not found` (+ `metaData:{request:{method,path}}`) | schema fail / unknown route or method |
| 403 | `FORBIDDEN` | `Authentication failed` | `Principal undefined could not be authenticated. No additional detail was provided.` | no key / bad key / ApiKy down |
| 500 | `CARRIER SERVER ERROR` | `Server error received from BJS` | BJS's response body (parsed JSON object, or raw text for non-JSON e.g. HTML) | ANY non-2xx from BJS on create or cancel |
| 500 | `INTERNAL SERVER ERROR` | `An internal server error occurred` | `An internal server error occurred. No additonal detail is available.` (typo kept) | unknown serviceCode, label bytes not a PDF |
| 500 | `INTERNAL SERVER ERROR` | `An unexpected error occurred` | `An unexpected error occurred on the server, no additional detail is available` | everything else (below) |

- Carrier failure status is ALWAYS HTTP 500 regardless of BJS's status (BJS 400/401/404/409/422/500/503 all become 500) (bjs-integration.ts:64, 101-104; CarrierError default 500). The BJS HTTP status is NOT in the body; it is only inferable from `details`. The 422 mock-BJS validations (`OrderNumber is required` etc., mu-bjs:111-125) also surface as 500 carrier errors.
- BJS unreachable: create -> 500 CARRIER with `details:"An unknown error occurred"` (bjs-integration.ts:64, create-label.test.ts:265-273); cancel -> generic 500 "An unexpected error occurred" because `error.response.data` is read unguarded (bjs-integration.ts:103, cancel-shipment.test.ts:103-111).
- Generic "An unexpected error occurred" 500 also for: malformed JSON, body over 100 kb (body-parser errors are not ProxyErrors), profile without `profile` block, BJS 2xx without `result`, label download failure, more PDF pages than BJS products (undefined `barcode`) (routes.test.ts:150-161, create-label.test.ts:275-293). Malformed JSON is a 500, NOT a 400 (contrast amazon: 400).
- Cancel failure with an empty BJS body: `details` is `{status, data:""}` in the mock (README:171-172: source would put an unserialisable axios object).
- 204 on cancel success has no body at all.

### Failure scenarios for D5 (magic values)

Normalisation: recipient postcode magic = strip ALL whitespace, uppercase, compare to the whitespace-stripped magic (so `err400`, `ERR  400` fire) (mu-bjs:41-42). Cancel prefixes = `toUpperCase().startsWith` on the raw `CarrierReference` header (the proxy sends it `encodeURIComponent`ed, prefix unaffected) (mu-bjs:202-214). Postcode magic fires only after mock BJS auth + validation pass (account/key, `OrderNumber`/`Recipient`/`Address`/`Postcode` present and not `"undefined"`, `ServiceLevel` known, `Products` array 1-198 with Type in {Deliver, Collect, Deliver and Collect}) (mu-bjs:105-125, 127-143).

| Operation | Field | Magic value | Where verified | What the caller sees |
| --- | --- | --- | --- | --- |
| create | `shipTo.postalCode` | `ERR 400` | mu-bjs:128-131; create-label.test.ts:230-240 | 500 `CARRIER SERVER ERROR` / `Server error received from BJS` / `details:{"success":false,"message":"Postcode is not in a BJS delivery area"}` |
| create | `shipTo.postalCode` | `ERR 500` | mu-bjs:132-135; test:242-245 | 500 CARRIER, `details:{"success":false,"message":"An error occurred while creating the order"}` |
| create | `shipTo.postalCode` | `ERR 503` | mu-bjs:136-139; test:247-250 | 500 CARRIER, `details` = the HTML string `<html><body><h1>503 Service Unavailable</h1></body></html>` |
| create | `shipTo.postalCode` | `NO RESULT` | mu-bjs:140-143; test:275-278 | BJS 200 `{success:true}` with no `result` -> 500 generic `An unexpected error occurred` |
| create | `shipTo.postalCode` | `LABEL 404` | mu-bjs:151; test:280-283 | order OK, label URL 404s (`Not Found` text) -> 500 generic `An unexpected error occurred` (no BJS order is rolled back; mock stateless) |
| create | `shipTo.postalCode` | `BAD PDF` | mu-bjs:152, 182-185; test:285-288 | label URL serves `MOCK LABEL - NOT A PDF` -> `splitLabels` throws -> 500 `INTERNAL SERVER ERROR` / `An internal server error occurred` / `...No additonal detail is available.` |
| create | `shipTo.postalCode` | `XTRA PAGE` | mu-bjs:147-150; test:290-293 | label PDF has products+1 pages -> `products[n].barcode` TypeError -> 500 generic `An unexpected error occurred` |
| cancel | `shipmentId` prefix | `UNKNOWN` | mu-bjs:203-206; cancel-shipment.test.ts:73-83 | 500 CARRIER, `details:{"success":false,"message":"Order not found"}` |
| cancel | `shipmentId` prefix | `CANCELLED` | mu-bjs:207-210; test:85-91 | 500 CARRIER, `details:{"success":false,"message":"Order is already cancelled"}` |
| cancel | `shipmentId` prefix | `ERR500` | mu-bjs:211-214; test:93-96 | 500 CARRIER, `details:{"success":false,"message":"An error occurred while cancelling the order"}` |
| create, cancel | `x-api-key` | `bjs-key-wrong-secret` | fixtures apiky/bjs.json; mu-bjs:98-101, 106-109; create test:252-258, cancel test:98-101 | 500 CARRIER, `details:{"success":false,"message":"Invalid AccountNumber or Key"}` (BJS 401 hidden in the 500) |
| create, cancel | `x-api-key` | `bjs-key-no-secret` | profile `{}` -> no `Key` header; create test:102-105 | same BJS 401 -> 500 CARRIER |
| create, cancel | `x-api-key` | `bjs-key-malformed-profile` | routes.test.ts:98-101 | 500 generic `An unexpected error occurred` |
| all | `x-api-key` | none / unknown / `apiky-500` | apiky-integration.ts:5-21; routes.test.ts:73-86 | 403 `FORBIDDEN` for all three |
| create, cancel | `accountId` | any account except `MOCKBJS01`/`MOCKBJS02` after stripping a leading S/E (e.g. `SMOCKBJS99`, `XMOCKBJS01`) | mu-bjs:98-101; create test:260-263 | BJS 401 -> 500 CARRIER, `details:{"success":false,"message":"Invalid AccountNumber or Key"}` |
| create, cancel | `accountId` vs key | `bjs-key-bravo` with `MOCKBJS01`, or alpha with `MOCKBJS02` | mu-bjs:100 (key must match that account) | same 401 -> 500 CARRIER |
| create | `serviceCode` | anything not in the 24-code table (case-sensitive; includes `Standard`, `2man`) | servicecode-mapping.ts:232-234; test:220-228 | 500 `INTERNAL SERVER ERROR` / `An internal server error occurred`; no upstream call |

All postcode magics fire deterministically. References are random (`MOCKBJS-` + 8 digits), never colliding with the `UNKNOWN`/`CANCELLED`/`ERR500` prefixes, so a created order can always be cancelled.

### Quirks mirrored from production

(README:146-165 "mirrored on purpose"; proxy logic is a port of the ADO source; none verified against prod traffic.)
- Every BJS failure is HTTP 500 with BJS's body in `details` (bjs-integration.ts:64, 101-104). Caller cannot distinguish BJS 400 vs 401 vs 5xx by status.
- Absent optional fields sent to BJS as the string `"undefined"`; unprefixed account sends `ExpressRequired=null` (README:150-152). Visible only upstream, but a mock-BJS validation of `"undefined"` for Postcode/Address/Recipient/OrderNumber would 422 (mu-bjs:49, 111-116).
- `labelFormat` ignored: PNG asked, PDF returned.
- Label/product pairing by position: more pages than products -> 500; fewer pages silently drop trailing products (bjs-service.ts:122-128).
- `1EXC`/`2EXC` -> two products per package, so two labels per package; `15EX` is one "Deliver and Collect" product (bjs-service.ts:42-63).
- Malformed JSON and >100 kb bodies -> generic 500 (not 400) because the error handler only knows its own classes (global-error.ts:26-35).
- Dimensions with no unit are inches; a side missing -> `"NaN"` (bjs-service.ts:33, mapping.test.ts:82-102).
- Weight GRAM/1000 only; no rounding of kg.
- Cancel reads `e.response.data` unguarded: BJS-unreachable on cancel is the generic 500, on create a CARRIER error (bjs-integration.ts:103).
- Typos kept: `additonal` (exceptions.ts:78), `An validation error` (exceptions.ts:46).
- `stateOrRegion` stays required (the spec's `default: ''` is not applied by openapi-backend validation) (README:159, routes.test.ts:127-132).
- The `Released` default is `"True"`; `released:false` sends `"false"` (mapping.test.ts:124-128).
- No retry anywhere: ApiKy once, BJS once (http.ts has no retry loop).

### Statefulness / ordering constraints

- Mock BJS is stateless (no memory; README:126-127, mu-bjs:93-216). Create returns a fresh random `MOCKBJS-########`; the label URL carries `?count=N` so the download works on any instance.
- Cancel needs no prior create: any `shipmentId` not starting `UNKNOWN`/`CANCELLED`/`ERR500` gets 204, including never-issued ids and ids already cancelled. Cancel twice succeeds twice in the mock (unlike real BJS where a second cancel is presumably 409; UNVERIFIED). Use `CANCELLED-...` ids to exercise the "already cancelled" error.
- No cancel-after-label or dispatch constraints modelled. No tracking.
- Idempotency: none. Two creates make two orders (different references); `orderNumber` is not de-duplicated.
- Label download is a second HTTP hop made by the proxy to `<proxy's BJS origin built from the request Host/X-Forwarded-Proto>/bjs/v1/labels/<ref>?count=N`; the label cannot be fetched again by the caller (no reprint).
- Account/secret pairing is checked on every call: create and cancel must use an `accountId` whose key matches the caller's profile secret.

### Adapter implications and leaks

- No validate and no commit/manifest/reprint/track: a generic interface must mark these unsupported for bjs (nothing to call; do not fall through to another path).
- ONE REQUEST = ONE ORDER, MANY LABELS: the number of returned labels is the number of BJS products (packages x2 for `1EXC`/`2EXC`), not the number of packages sent. The adapter must keep the mapping `packages[i] -> labels[i]` as position, and handle exchange services returning 2n labels. Per-package tracking ids are `documents.trackingId` (nested), and the order-level id is `shipmentId` (also repeated as `secondaryShipmentId`).
- Labels are always PDF (labelFormat ignored; spec only allows PDF|PNG, so ZPL/EPL fail validation). A thermal-label consumer cannot get ZPL from this carrier.
- `serviceCode` must be one of 24 exact case-sensitive codes; an adapter must translate Selector's service ids to these codes itself (Selector-level concept: 1MAN/2MAN/15MN families + SAT/SUN/AM/PM/EVE timed variants, RTS returns, EXC exchanges, `2ROC`). Unknown -> opaque `INTERNAL SERVER ERROR`.
- `accountId` is overloaded: first-letter S/E carries a standard/express flag and is stripped. The adapter must always prefix S or E (and never feed a raw account that starts with S/E unprefixed).
- Weight units only GRAM or KILOGRAM; dims only CENTIMETER or INCH (missing unit = inches). `stateOrRegion` must be present (use `""`). `orderNumber` required. Optional text fields omitted become the string `"undefined"` at BJS (visible only if BJS echoes them).
- Error mapping cannot rely on HTTP status: everything carrier-side is 500. Branch on `body.code` (`CARRIER SERVER ERROR` / `INTERNAL SERVER ERROR` / `VALIDATION ERROR` / `FORBIDDEN`) and then on `details` (BJS's own body) / `message`. `code` is a string with spaces, `details` is polymorphic (object, string, HTML string). BJS 4xx vs 5xx is indistinguishable except by reading `details.message`.
- Malformed JSON and oversized body = 500, not 400, and carry the same generic body as truly internal errors.
- 403 for any auth failure including ApiKy outage (cannot tell bad key from ApiKy down).
- Auth check precedes schema check; unknown routes give 400 `VALIDATION ERROR`.
- Cancel returns 204 with no body, needs `accountId` + `reason` + `shipmentId` (the carrier reference from create), and does NOT use the per-package barcode.

### README-vs-source discrepancies, and UNVERIFIED

README-vs-source:
- README:27-28 says `tradingName`, `released`, `shipTo.whatThreeWords` and `shipFrom.eori` "are read though the spec doesn't list them". `whatThreeWords` (yaml:211-213) and `eori` (yaml:234-239) ARE in the spec's Address schema; only `tradingName` and `released` are unlisted (yaml:60-104). `vat`, `companyName`, `countryCode` ARE in the spec but never read.
- README:19 gives the create response as `{shipmentId, secondaryShipmentId, warnings: [], packages: [{documents: {label: {labelStream}, trackingId}}]}`: matches source. Worth stressing `trackingId` is inside `documents` (spec yaml:324-337 agrees).
- README:63 "`labelFormat` is required but ignored": matches (yaml:293-302 requires `labelFormat`, enum PDF|PNG).
- README:71 "403 FORBIDDEN ... or ApiKy down": matches (apiky-integration.ts swallows 500s too).
- README table of error bodies omits that a 400 `VALIDATION ERROR` is also returned for an unknown path even without a valid key? UNVERIFIED (openapi-backend calls `notFound` before security per README:26, but not tested without a key).
- The OpenAPI example `serviceCode: "Standard"` (yaml:150) is not in the code's table; copying the spec's example gets a 500. The spec is also silent about the 24 codes.
- yaml:57-58 documents cancel's 204 response only; the real 500 CARRIER bodies are not in the spec.
- yaml tags `status` for cancel; no effect.
- README:20 says cancel is `{accountId, reason, shipmentId}`: matches, and `shipmentId` is sent URI-encoded (cancel-shipment.test.ts:36-39).

UNVERIFIED:
- Everything about real BJS: the upstream error envelope (`success`, `message`), `result` extra fields, whether real exchange orders return Deliver/Collect labels and how they are ordered, whether `ExpressRequired`/service flags are validated or priced, real double-cancel behaviour, real tracking. README:119-124 says these are invented/untested; the repo has no BJS error samples.
- What a createLabel POST without `content-type: application/json` returns.
- Max pages through the label URL (mock `count` max 199, `MAX_PRODUCTS` 198).
- Cloud Run edge IAM / inbound Bearer.
- Behaviour of the `released` flag beyond the form value (mock ignores).

### Notes for the E2 draft

Claims at E2 lines 27, 58, 68, 136-141, 181, 188 about `bjs`:
- Line 27 "returns one label per product": correct and important; clarify "product" is a BJS product line, one per package, TWO per package for `1EXC`/`2EXC` (15EX is one). Not "one per package".
- Line 58 "`bjs-key-alpha` (send `accountId` `MOCKBJS01`)": works, but an unprefixed `MOCKBJS01` sends `ExpressRequired=null`; the real convention is `SMOCKBJS01` (standard) or `EMOCKBJS01` (express), which are stripped to `MOCKBJS01`. Suggest "send `accountId` `SMOCKBJS01` (or `EMOCKBJS01`; the S/E prefix is stripped)". The `bjs-key-bravo` account is `MOCKBJS02`; bravo with `MOCKBJS01` is refused.
- Line 68 "bjs 403 / 403 / 403": correct (all three are the FORBIDDEN body). Contrasts with amazon: bjs checks the key before the body, amazon after.
- Lines 136-139 postcode and cancel-prefix scenarios: all correct. `ERR 400/500/503` -> 500 CARRIER ERROR carrying BJS's body (the 503 body is an HTML string, not JSON). `NO RESULT`, `LABEL 404`, `XTRA PAGE` -> 500 "An unexpected error occurred" correct. `BAD PDF` -> 500 `INTERNAL SERVER ERROR` correct (message `An internal server error occurred`, not "unexpected"). Cancel `UNKNOWN`/`CANCELLED`/`ERR500` -> 500 carrier error carrying `Order not found` / `Order is already cancelled` / `An error occurred while cancelling the order`.
- Line 140 `bjs-key-wrong-secret`, `bjs-key-no-secret` -> 500 carrier error (BJS 401): correct. Missing from the table: `bjs-key-malformed-profile` -> 500 generic "An unexpected error occurred".
- Line 141 "Any account but `MOCKBJS01` or `MOCKBJS02` (after an `S` or `E` prefix)": correct but the prefix is optional (an unprefixed `MOCKBJS01` also works), and an account is also refused if its key does not match the caller's profile secret (`bjs-key-bravo` + `MOCKBJS01`).
- Line 181 "BJS ... return 500 for every carrier failure": correct (hard-coded in `CarrierError`, bjs-integration.ts:64, 101-104). Not every BJS error is a 500: caller-side errors are 400 (schema), 403 (auth). Also malformed JSON in bjs is a 500; on amazon it is a 400. If line 183 (malformed JSON on "several mocks") names mocks, bjs is on the list, amazon is not.
- Line 188 "Some upstream error shapes are invented ... (BJS, OCS)": agrees with README:119-124. Matches source.
- Table claim that bjs has validate/manifest: not made. E2 does not say bjs has no validate; should be explicit that it has none.


---

## inpost (InPost; apps/inpost-proxy; mirrors inpost.gfsdeliver.com)
All paths relative to repo `ilg-merak/carrier-playground`, `origin/main`. Source = `apps/inpost-proxy/src/**`; spec = `apps/inpost-proxy/api/inpost-integration-api.yaml` (abbrev. `spec`); upstream faker = `apps/mock-upstreams/src/inpost/index.ts` (abbrev. `mu`).

### Operations and routes
| operation | METHOD path | supported? | notes |
| --- | --- | --- | --- |
| create-ship (+ label, one call) | POST `/shipping/createLabel` | yes | 201. Creates shipment, then immediately GETs its label, optionally PDF->PNG. src/app.ts:94-96, src/integrations/inpost-integration.ts:106-164 |
| create return (+ label) | POST `/shipping/createReturnLabel` | yes | 201, same request schema and response shape. Upstream `returns/shipments`. src/app.ts:97-99, inpost-integration.ts:177-194 |
| validate | none | NO | no dry-run/validate route |
| delete / cancel | none | NO | no cancel route; unknown path = 400 "Requested path not found" (app.ts:113-119) |
| commit-manifest | none | NO | |
| reprint / label retrieval alone | none | NO | label is fetched only inside create (`getLabel`, inpost-integration.ts:76-104); not exposed as a route |
| track | none | NO | spec has a `service` tag but no routes (spec:13-17) |
| health | GET `/` (200 `ok`, app.ts:84-86); GET `/health/liveness` (200 `{"ok":true}`, app.ts:76-78, before request log) | yes | no auth on either |

Order of processing (app.ts:72-146): correlation mw -> liveness -> request log -> `express.json()` (100kb default) -> `bodyAsExpress5` (non-JSON body => `req.body` undefined) -> `/` -> openapi-backend: route -> security (`x-api-key`) -> schema -> handler -> globalErrorHandler. Paths case-sensitive; wrong method on a known path = not-found 400 (test/routes.test.ts:50-53).

### Auth and headers
- Header: `x-api-key` only (spec:574-578; app.ts:136-142). Resolved via ApiKy `GET {APIKY_BASE_URL}/api/profile?token=<key>` with service key header (packages/apiky-client/src/index.ts:31-43). `profile.CustomerId` = shipping account id (inpost-integration.ts:111).
- Fixture key NAMES (apps/mock-upstreams/fixtures/apiky/inpost.json; secret values elided): `inpost-key-alpha` (account `MOCK-INPOST-ALPHA`, org `MOCKORG001`), `inpost-key-bravo` (`MOCK-INPOST-BRAVO`, `MOCKORG002`), `inpost-key-bad-secret`, `inpost-key-token-outage`, `inpost-key-wrong-org`, `inpost-key-no-credentials`, `inpost-key-malformed-profile`, `apiky-500`.
- Missing key / unknown key / `apiky-500` / ApiKy 5xx / ApiKy unreachable / ApiKy 200 with non-JSON: all 403 `{code:"FORBIDDEN", message:"Authentication failed", details:"Principal unknown could not be authenticated. No additional detail was provided."}` (src/exceptions.ts:21-37; apiky-integration.ts:5-21 swallows every error; test/routes.test.ts:12-16,64-83). There is NO 401 anywhere.
- `inpost-key-malformed-profile` (ApiKy 200 but no `profile` block) is NOT a 403: `principal.profile.CustomerId` throws TypeError => generic 500 `{code:"INTERNAL SERVER ERROR", message:"An unexpected error occurred", details:"An unexpected error occurred on the server, no additional detail is available"}` (inpost-integration.ts:111; global-error.ts:28-36; test/routes.test.ts:90-93).
- Key checked BEFORE body validation (test/routes.test.ts:80-83).
- Content-Type must be `application/json`; anything else leaves body undefined and gives 400 `details:"request must have required property 'requestBody'"` (test/routes.test.ts:179-186; app.ts:46-50). `Accept` is not read. No code reads `Authorization`, so a Cloud Run `Authorization: Bearer` header is ignored (mock edge is public per E2 draft; IAM enforcement UNVERIFIED here).
- Per-account InPost credentials: `fixtures/credentials.json` keyed by `shippingAccountId` (`{customer, shippingAccountId, inpostClientId, inpostClientSecret, inpostOrgId}`; secrets elided), `findOne` semantics, src/stores/inpost-store.ts:13-20. Org id is NOT in the request; it comes from this document (get-inpost-access-token.ts:24).
- InPost token: `POST {INPOST_BASE_URI}/oauth2/token`, Basic client-id:secret, form `grant_type=client_credentials`, scope `api:returns:write api:returns:read api:shipments:write api:points:read` (get-inpost-access-token.ts:9,26-37). Cached per account, LRU 100, TTL 10 min regardless of `expires_in`; failures not cached; a revoked cached token is not retried (src/stores/access-token-cache.ts:5-9).

### Request
Body: `CreateLabelRequest` (spec:65-121), same for both routes. Spec `required`: only the body itself (spec:33,53); top-level fields are ALL optional in the spec, but the code/mock make several effectively required.

| field | spec | what code does / effective requirement |
| --- | --- | --- |
| `labelSpecification.labelFormat` | enum PDF, PNG, ZPL203DPI, ZPL300DPI, EPL203DPI (spec:510-522); `labelSpecification` not required | Absent => proxy 400 `"Invalid label format: undefined"` `metaData:{labelFormat}` (inpost.service.ts:192-209) AFTER an InPost token call. Effectively required. Mapped to InPost `Accept`: PDF and PNG -> `application/pdf;format=A6`; ZPL203DPI -> `text/zpl;dpi=203`; ZPL300DPI -> `text/zpl;dpi=300`; EPL203DPI -> `text/epl2;dpi=203` (inpost.service.ts:192-209) |
| `serviceCode` | enum `STD`,`EXP`,`HSTD`,`HEXP` (spec:95-102); optional | `HSTD`/`HEXP` = home delivery (needs `shipTo`). ANYTHING else including absent = locker (needs `lockerAddress`). Spec enum blocks other strings at schema stage. Priority `EXPRESS` for `HEXP`,`EXP`, else `STANDARD` (inpost.service.ts:24-35). Home adds VAS `proofOfDelivery:true` (:158) |
| home/locker rule | n/a | Home code w/o `shipTo` or locker code w/o `lockerAddress` => 400 `VALIDATION ERROR`, details `"Appears to be a home delivery request based on service code but no shipTo address provided"` / `"Appears to be a locker delivery request based on service code but no locker address provided"`, `metaData:{serviceCode}` (inpost.service.ts:37-55). Thrown after token fetch (inpost-integration.ts:112-113). If a locker code arrives with both addresses, locker wins (test/mapping.test.ts:141-144) |
| `shipFrom` (Address) | optional; Address required fields: `addressLine1, city, firstName, lastName, postalCode, phoneNumber, email` (spec:200-207) | Sent as `sender` contact + `origin` {countryCode UPPER, street=addressLine1, city, postalCode}. Absent => empty strings => mock InPost 400 on `origin.countryCode` => proxy 500 carrier error (mu:118). `shipFrom.eori` -> `customsClearance.eoriNumber` |
| `shipTo` (Address) | optional | Home only. `destination` {countryCode UPPER, street=addressLine1, city, postalCode}. `countryCode` is optional in spec (spec:248-254) but missing => `''` => mock 400 `destination.countryCode` (mu:127-129) => 500 carrier error. Effectively required for home |
| `lockerAddress` (PointAddress) | required inside: `countryCode, pointId, firstName, lastName, email, phoneNumber` (spec:308-314) | `destination` = `{countryCode UPPER, pointId}`; recipient contact = locker's names/email/phone. Mock accepts pointId `MOCKPT0001..0003` only (exact, case-sensitive: mu:123-125, fixtures/inpost/inpost.json points) |
| `packages[]` | optional; minItems 1 maxItems 1 (spec:87-92) | Missing/null => `parcels: []` => mock 400 `parcels: At least one parcel is required` => 500 carrier error (mu:132-133). 2 packages => 400 `"/packages must NOT have more than 1 items"` |
| `packages[0].weight` | optional; `{unit: GRAM|KILOGRAM, value:number}` both required if present (spec:379-392) | `KILOGRAM`->`{amount,unit:"KG"}`; ANYTHING ELSE (i.e. GRAM) -> `{amount,unit:"G"}`. NO multiplication (inpost.service.ts:167-169). Absent weight => key dropped from JSON => mock 400 `parcels[0].weight` (mu:136-138) => 500 carrier error. Effectively required, must be > 0 |
| `packages[0].dimensions` | optional `{length,width,height,unit: INCH|CENTIMETER}` | Always sent with `unit:"CM"`. `INCH` => each `Math.round(n*2.54*1000)/1000`; else values passed as-is; absent dims => zeros; absent individual dim => 0 (inpost.service.ts:115-133). Mock does not check dims |
| `packages[0].value` {currency(3), value 0..99999} | optional | -> `customsClearance.value`/`.currency` on the parcel |
| `packages[0].description` / `descriptionOfGoods` (1..70) | optional | `contentsDescription = description || descriptionOfGoods` (inpost.service.ts:173) |
| `packages[0].packageClientReferenceId` | optional | `references.trackableReference` only when truthy; echoed back by mock inside upstream parcels but proxy does not return it |
| `customs.commodities[]` | `customs` optional; if present `commodities` required, minItems 1; each needs `quantity,description,value` (spec:407-509) | EVERY commodity is copied onto EVERY parcel's `customsClearance.contents` (`hsCode, description, productOriginCountryCode = (countryOfOrigin || shipFrom.countryCode || '').toUpperCase(), quantity, unitWeight(G/KG), unitValue`) (inpost.service.ts:142-153). Parcel `customsClearance` is sent even with no customs |
| `customs.incoTerms`, `.invoiceId`, `.invoiceDate`, `.reasonForExport`, `.shippingCost` | optional | -> top-level `customsClearance`: `incoterm`; `invoice {number, issueDate}` only if `invoiceId` (date defaults to today UTC `YYYY-MM-DD`); `exportReason`: Gift->GIFT, Commercial Sample->SAMPLE, Sale of Goods->SALES, all other enum values (Documents, Return of Goods, Mixed Content, Other) DROPPED; `shippingCost {amount,currency}` (zero allowed). `customsClearance` omitted entirely when empty (inpost.service.ts:57-90,179,188) |
| In spec but NEVER read by code | | `contentType`, `shippingLocationId`, `businessTransactionType`, `safePlaceLocation`, `addressLine2/3`, `stateOrRegion`, `contactName`, `whatThreeWords`, `vat`, `customs.preRegistrationNumber/Type`. (`companyName`, `commodity.weight` and `commodity.hsCode` ARE read.) |

Units/enums summary: weight GRAM|KILOGRAM -> G|KG; dimensions INCH|CENTIMETER -> CM; currency 3-letter, passed through; country code upper-cased in mapping (lowercase accepted, helpers use `gb`); dates YYYY-MM-DD (spec pattern spec:438); label format list above.

Validation errors (proxy): 400 `{code:"VALIDATION ERROR", message:"Client request failed validation", details:"<instancePath minus /requestBody or 'request'> <Ajv message>", metaData:{request:{method(lowercase),path}, validationErrors:[ajv errors]}}`. Ajv stops at first failure, so details names ONE field (README:196-197 vs app.ts:104-110 which would join with `; `; test/routes.test.ts:151-154). E.g. `"/shipTo must have required property 'lastName'"`, `"/packages must NOT have more than 1 items"`, `"/contentType must be equal to one of the allowed values"`.

Minimal viable home request (derived from test/helpers.ts:95-135 + mock checks): `labelSpecification.labelFormat`, `serviceCode:"HSTD"`, `shipFrom{firstName,lastName,addressLine1,city,countryCode,postalCode,email,phoneNumber}`, `shipTo{same}`, `packages[{weight{unit,value>0}}]`. Locker: replace `shipTo` with `lockerAddress`, `serviceCode:"STD"`; keep `shipFrom` (mock needs `origin.countryCode` on locker too).

### Response
- Success 201 JSON (both routes), always `res.status(201).send(obj)` (app.ts:95,98): `{ShipmentId, TrackingNumber, Packages:[{documents:{trackingId, label:{labelStream}}}]}` (inpost.service.ts:211-222). `ShipmentId` = `TrackingNumber` = `documents.trackingId` = InPost tracking number (`MOCKIP`+16 digits in the mock; `MOCKNOLABEL…`/`MOCKPNGFAIL…` for scenarios, mu:36,98-99). For returns the number is `parcels[0].trackingNumber` of the return response (inpost-integration.ts:183-192).
- `dropOffCode`: key present in code but ALWAYS absent (proxy never sets `enableDropOffCode`; mu:270-271). `ConsignmentCarrierTrackingUrl` and `Warnings` (in types/spec) are never set. Key order exactly `['ShipmentId','TrackingNumber','Packages']` (test/create-label.test.ts:47).
- Exactly ONE package, ONE label, no customs/invoice document, no per-package multiple labels.
- `labelStream` = base64 of whatever InPost returned, for EVERY format (`Buffer.from(arrayBuffer).toString('base64')`, inpost-integration.ts:99). So ZPL/EPL are base64-encoded text programs, not raw text. PDF = A6 (298x420pt in mock, mu:155-156). No data-URI prefix.
- PNG: label fetched as PDF, base64 PDF posted as `application/pdf` bytes to `{PDF_CONVERTER_URI}/pdfconverter/stream?scale=875` with `accept: multipart/form-data` (pdf-to-png-converter.service.ts:4-5,30-34). Response multipart; LAST non-string part becomes the label (:53-57). Mock: one PNG per page, ~621x875 (`round(875*105/148)` x 875, mu:357; derived), at most 50 pages (413 beyond), `scale` 1..2000. Retry: up to 3 attempts total on HTTP 500 or network error, NO delay (:9-25). Non-OK after retries => `InternalError` (below).
- PNG is ignored for ZPL/EPL (conversion only when `labelFormat === 'PNG'`, inpost-integration.ts:155).

### Error shape
Common body `{code, message, details}` (+`metaData` for validation) (exceptions.ts:16-18, 55-57). Methods are lower-case in metaData.

| status | code | message | when |
| --- | --- | --- | --- |
| 400 | `VALIDATION ERROR` | `Client request failed validation` | unknown path/method (`details:"Requested path not found"`, `metaData:{request}`); schema failure; home/locker rule; missing labelSpecification; non-JSON body |
| 403 | `FORBIDDEN` | `Authentication failed` | bad/missing key, ApiKy failure, no credentials doc (`details:"No credentials found for specified partner"`), any InPost token failure (401/500/unreachable/network) => `details:"Principal <accountId> could not be authenticated. No additional detail was provided."` (get-inpost-access-token.ts:17-22,49-51) |
| 500 | `CARRIER SERVER ERROR` | `Error response from carrier` | InPost shipment or label call answered anything other than 200/201 (inpost-integration.ts:90,136). `details:{message, httpStatus:"<code> <statusText>", body}`; `message` = `Failed to create shipment` / `Failed to create return shipment` / `Failed to get label for tracking number <n>`; `body` = InPost JSON with `instance` key deleted if it is a non-array object, else raw text (HTML) or null (exceptions.ts:60-107). InPost's own 400s, 401s and 403s ALL become 500 |
| 500 | `INTERNAL SERVER ERROR` | `An internal server error occurred` | PDF converter non-OK after retries (`details:"PDF converter returned 500: Internal Server Error"`); return response with no parcels (`details:"Failed to create return shipment: response did not contain any parcels"`) |
| 500 | `INTERNAL SERVER ERROR` | `An unexpected error occurred` | everything else: malformed JSON, body >100kb, malformed ApiKy profile, InPost unreachable after token, 2xx non-JSON from InPost; `details:"An unexpected error occurred on the server, no additional detail is available"` (global-error.ts:28-36) |

No 401, no 404 (other than path-not-found 400), no 599. Mock InPost's own problem body (RFC 7807 `{status,type,title,detail?,instance,errors?}`, mu:73-96) appears inside `details.body` for carrier errors.

### Failure scenarios for D5 (magic values)
Postal-code magics: `shipTo.postalCode`, normalised by stripping ALL whitespace + upper-casing (`normalise`, mu:59-60), so `err 400`, `ERR400` and ` e r r 4 0 0` all fire. Only home destinations (locker destination has no `postalCode`; mu:238). Validation (400 from mock) is evaluated first, so a magic postcode combined with a request the mock finds invalid (e.g. no weight) yields a 400 problem, not the magic (mu:242-250 before 251-261).

| operation | field | magic value | where verified | what the caller sees |
| --- | --- | --- | --- | --- |
| createLabel, createReturnLabel | `shipTo.postalCode` | `ERR 400` | mu:238-250 | mock 400 `ValidationFailed` `errors:{"destination.postalCode":[...]}` => proxy 500 `CARRIER SERVER ERROR`, `details.httpStatus:"400 Bad Request"`, `details.body` = problem JSON sans `instance` |
| same | same | `ERR 500` | mu:251-254 | 500 `CARRIER SERVER ERROR`, `details.httpStatus:"500 Internal Server Error"`, body problem JSON |
| same | same | `ERR 503` | mu:255-261 | 500 `CARRIER SERVER ERROR`, `details.httpStatus:"503 Service Unavailable"`, `details.body` = HTML string (`<html>...503 Service Temporarily Unavailable...`) |
| same (incl. returns) | same | `NO LABEL` | mu:263-264,299-306 | shipment created, label 404 => 500 `CARRIER SERVER ERROR`, `details.message:"Failed to get label for tracking number MOCKNOLABEL<16d>"`, `httpStatus:"404 Not Found"`, body `ResourceNotFound` problem. Fires for every labelFormat |
| same, `labelFormat:"PNG"` only | same | `PNG 500` | mu:265-266,158-160,341-344 | PDF label has a failure marker; converter returns 500; 3 converter calls total, then 500 `INTERNAL SERVER ERROR` `message:"An internal server error occurred"`, `details:"PDF converter returned 500: Internal Server Error"`. With PDF/ZPL/EPL requests: normal 201 (marker only on PDF; PDF returned as-is) |
| createReturnLabel ONLY | same | `NO PARCEL` | mu:273-277 | mock 201 `{parcels:[]}` => 500 `INTERNAL SERVER ERROR` `message:"An internal server error occurred"`, `details:"Failed to create return shipment: response did not contain any parcels"`. On createLabel it is a normal success |
| createLabel/createReturnLabel (locker) | `lockerAddress.pointId` | any value not exactly `MOCKPT0001`,`MOCKPT0002`,`MOCKPT0003` (no normalisation, case-sensitive) | mu:123-125; fixtures/inpost/inpost.json | mock 400 `errors:{"destination.pointId":["Point does not exist."]}` => 500 `CARRIER SERVER ERROR` `httpStatus:"400 Bad Request"` (test/create-label.test.ts:170-181) |
| any | `x-api-key` `inpost-key-bad-secret` | exact key | fixtures/apiky/inpost.json; credentials.json; mu:206-210 | InPost token 401 => 403 `FORBIDDEN`, `details:"Principal MOCK-INPOST-BAD-SECRET could not be authenticated. No additional detail was provided."` |
| any | `inpost-key-token-outage` | exact key (clientId `token-500`) | mu:198-201 | InPost token 500 => 403 `FORBIDDEN`, details naming `MOCK-INPOST-TOKEN-OUTAGE` |
| any | `inpost-key-no-credentials` | exact key | inpost-store.ts; no credentials doc for `MOCK-INPOST-UNCONFIGURED` | 403 `FORBIDDEN` `details:"No credentials found for specified partner"`; no InPost call |
| any | `inpost-key-wrong-org` | exact key (stored org `MOCKORG999`, login belongs to `MOCKORG005`) | mu:227-230 | token OK, shipment call 403 from InPost => 500 `CARRIER SERVER ERROR` `httpStatus:"403 Forbidden"` |
| any | `inpost-key-malformed-profile` | exact key | fixtures/apiky/inpost.json (no `profile`) | 500 `INTERNAL SERVER ERROR` "An unexpected error occurred" (NOT 403) |
| any | `x-api-key` `apiky-500` / unknown / none | | apiky mock | 403 `FORBIDDEN` "Principal unknown" |
| any | body | malformed JSON; >100kb | app.ts:81 | 500 "An unexpected error occurred" |
| createLabel | `serviceCode` / address mismatch, missing `labelSpecification` | | inpost.service.ts | 400 (see Request) |
| mock-side validation (not magic) | parcel weight missing/<=0; no recipient email AND phone; blank destination street/city/postalCode/countryCode; blank `origin.countryCode`; >10 parcels | | mu:103-147 | 500 `CARRIER SERVER ERROR` with `details.body.errors` keyed by dotted path |
| label | `Accept` not one of the four media types | | mu:307-311 | unreachable through the proxy (it only sends valid ones) |

### Quirks mirrored from production
- Every InPost non-200/201 is a 500 carrier error, including InPost 400/401/403 (inpost-integration.ts:90-98,136-144; README "Production behaviour mirrored", read from code, not prod traffic).
- Failed InPost token call is a 403 FORBIDDEN, so a carrier outage looks like the caller's auth failing (get-inpost-access-token.ts:49-51).
- Token fetched before the request is checked: missing `labelSpecification` or wrong address/service pairing still costs a token call (inpost-integration.ts:112-115; test/create-label.test.ts:247-253).
- Malformed JSON and >100kb bodies are 500, not 400 (global-error.ts:32-36).
- Ajv first-failure-only `details` (see above).
- PNG keeps only the LAST page of the converter output (pdf-to-png-converter.service.ts:53-57).
- Returns reuse the outbound mapping unchanged: `shipFrom` is sender+origin, `shipTo` is destination/recipient (inpost.service.ts:135-190; README:199-200). Returns "type" is only the upstream path.
- Every commodity is copied onto the one parcel (inpost.service.ts:142-153).
- Home delivery gets `proofOfDelivery:true`; locker does not.
- `dropOffCode` never returned.
- Export reasons Documents/Return of Goods/Mixed Content/Other silently dropped.
- 403 detail for missing/invalid key says `Principal unknown` (OCS says `Principal undefined`).

### Statefulness / ordering constraints
- No cross-call state in the mock (mock InPost keeps nothing; tokens and tracking numbers carry their scenario in their text: `mock-inpost-at-<exp>-<org>-<uuid>`, mu:40-42; `MOCKIP|MOCKNOLABEL|MOCKPNGFAIL`+16 digits, mu:36-37). Each call makes a new tracking number; no idempotency key, no dedupe on `packageClientReferenceId`.
- Proxy holds one per-instance state: access-token cache (100 accounts, 10 min). A multi-instance deployment may issue multiple tokens; harmless.
- Create and label are one atomic call from the caller's view. If label fetch fails after shipment creation (`NO LABEL`), the InPost shipment exists but the caller gets a 500 and no tracking number; retrying creates ANOTHER shipment (orphan).
- No cancel exists, so nothing to order against.

### Adapter implications and leaks
- One call gives shipment + label; no separate label/reprint/cancel/manifest/validate. A generic interface needs these as unsupported.
- Home vs locker is chosen by `serviceCode` (HSTD/HEXP vs everything else) and requires different address fields (`shipTo` vs `lockerAddress`). Adapter must set the code and the matching block; sending both is tolerated (locker wins if non-home code).
- Returns are a separate route with the same body; adapter must decide which of shipFrom/shipTo maps to consumer vs warehouse (proxy does no swapping).
- Weight must be present and > 0 (spec says optional); `countryCode` on shipFrom/shipTo must be sent (spec says optional); `email` and `phoneNumber` are required on every Address and on PointAddress (spec:200-207,308-314). `shipFrom` is needed even for lockers.
- Service codes accepted: `STD`,`EXP`,`HSTD`,`HEXP`; other strings rejected by schema.
- Labels: base64 for ALL formats including ZPL/EPL (decode before printing). PNG depends on a converter and can fail with 500 `INTERNAL SERVER ERROR` after retries; PNG keeps only the last page (always 1 page for InPost A6).
- Error classification: carrier problems are 500 `CARRIER SERVER ERROR` with InPost status/body in `details`; auth/credential/tokens are 403. Distinguish retry-worthy cases by `details.httpStatus` (`"503 …"`, `"500 …"` vs `"400 …"`) and by `code` (`INTERNAL SERVER ERROR` = converter or empty return; `FORBIDDEN` = credentials). There is no 599 convention (unlike OCS).
- Max 1 package per request.
- Account selection is by API key only (ApiKy profile -> credentials -> org); no org/credentials in the request.
- No `Warnings`, no tracking URL, no drop-off code in responses.

### README-vs-source discrepancies, and UNVERIFIED
README vs source (README is generally accurate; deviations are small):
- README:62 says `details` is `<field> <Ajv message>` "only ever the first failure" while app.ts:104-110 is written to join with `; `; behaviour = first failure only (tests confirm). Not a conflict in outcome.
- README:84 lists `inpost-key-malformed-profile` -> generic 500; the E2 bad-key table (E2 lines 64-70) groups `inpost` as 403/403/403 and omits this key (see Notes below).
- README says the mock InPost "recipient needs an email or a phone"; the proxy spec requires BOTH on Address/PointAddress, so a request without both never reaches the mock (400 from the proxy first).
- Spec says `serviceCode`, `labelSpecification`, `packages`, `shipFrom`, `shipTo`/`lockerAddress` optional; code/mock make labelSpecification, packages[0].weight, shipFrom.countryCode, destination countryCode effectively required.
- spec `servers.url: inpost.gfsdeliver.com` has no scheme (spec:11-12) — cosmetic.
- spec `CreateLabelResponse` (spec:523-573) lists `ConsignmentCarrierTrackingUrl`, `Warnings`, `dropOffCode`; code never returns the first two and never returns `dropOffCode` either.
- Spec `description` for `packages[0].weight` (spec:381) is copy-pasted ("Declared monetary value") — cosmetic.

UNVERIFIED:
- Whether real InPost requires `countryCode` for locker destinations (mock does not check it; mu:123-125).
- Real InPost behaviour for label unavailability, drop-off codes on returns, revoked cached token (README only says read from code, not prod logs).
- Cloud Run IAM / Bearer handling on the deployed mock (no code reads `Authorization`; deployment config not read).
- `Content-Type: application/json; charset=...` variants (express.json handles; not tested here).
- Exact PNG pixel size from the mock (derived ~621x875 from mu:357, not asserted in a test I read).
- Real-prod behaviour of everything under "Production behaviour mirrored on purpose": inferred from source code, not production traffic (README:181-182).

### Notes for the E2 draft
Claims about inpost in the excerpt, checked against source:
- Line 28 (table row): "Creates InPost shipments and returns, home or locker, with labels" — correct. `main 64656dc` and prod host come from the README only (README:3-5); not verifiable in code.
- Lines 59 / 68 (keys, bad-key table): keys correct. Bad-key `403 / 403 / 403` is correct for none/unknown/`apiky-500`, BUT `inpost-key-malformed-profile` (a fixture key) returns 500 "An unexpected error occurred", not 403. The table is silent on it.
- Lines 142-148 (failure table): all rows consistent with code, with these refinements the draft omits: (a) `NO LABEL` and `PNG 500` also fire on `createReturnLabel`; `NO PARCEL` fires ONLY on `createReturnLabel`; (b) `PNG 500` fires only when `labelFormat` is `PNG`, and the 500 is code `INTERNAL SERVER ERROR`, whereas `ERR *`/`NO LABEL`/unknown pointId are code `CARRIER SERVER ERROR`; (c) `NO PARCEL` is also `INTERNAL SERVER ERROR`, not carrier error; (d) magic postcodes ignore ALL whitespace and case; (e) the key rows: `inpost-key-bad-secret`/`token-outage` name the account in the 403 details; (f) pointId match is exact and case-sensitive (no normalisation).
- Line 181: "BJS and InPost return 500 for every carrier failure" — true for carrier failures; but note InPost auth-side failures are 403, and the 500 carries two different `code`s.
- Line 183: "Malformed JSON gives a 500, not a 400" — correct for InPost.
No claim about InPost found that the source contradicts.


---

## ocs (OCS Worldwide; apps/ocs-proxy; mirrors ocs.gfsdeliver.com)
All paths relative to repo `ilg-merak/carrier-playground`, `origin/main`. Source = `apps/ocs-proxy/src/**`; spec = `apps/ocs-proxy/api/ocs-integration-api.yaml` (abbrev. `spec`); upstream faker = `apps/mock-upstreams/src/ocs/index.ts` (abbrev. `mu`). Mirrors the ADO `ocs-proxy` repo, NOT the newer GitHub `carrier-proxies/apps/ocs-proxy` (README:9-10).

### Operations and routes
| operation | METHOD path | supported? | notes |
| --- | --- | --- | --- |
| create-ship (+ label, one call) | POST `/shipping/createLabel` | yes | 201. Books parcel at OCS (`POST {OCS_SERVICE_URI}`), returns its label; PNG via converter. src/app.ts:77-81, src/integrations/ocs-integration.ts:38-60 |
| validate | none | NO | |
| delete / cancel | none | NO | unknown path/method = 400 "Requested path not found" (app.ts:88-94) |
| commit-manifest | none | NO | |
| reprint / track | none | NO | |
| health | GET `/` (200 `ok`, app.ts:71-73); GET `/health/liveness` (200 `{"ok":true}`, app.ts:65-67) | yes | no auth |

Single operation only. Middleware order (app.ts:61-120): correlation -> liveness -> request log -> `express.json()` (100kb) -> `/` -> openapi-backend route -> security -> schema -> handler -> globalErrorHandler. Paths case-sensitive; a trailing slash is ignored (test/routes.test.ts:55-63).

### Auth and headers
- Header `x-api-key` only (spec:407-411; app.ts:109-115). ApiKy lookup `GET /api/profile?token=<key>` with service key (apiky-client:31-43). The profile is read ONLY for its `name` (logged, ocs-integration.ts:39); it does NOT select an OCS account.
- Fixture key NAMES (apps/mock-upstreams/fixtures/apiky/ocs.json): `ocs-key-alpha`, `ocs-key-bravo`, `apiky-500` (ApiKy 500). Profiles are `{name, profile:{}}`; no per-customer config. Both keys book under the same OCS account (`OCS_USER`/`OCS_TOKEN`, default `MOCKOCS001`/value elided, config.ts:27-28), sent inside the OCS request body (ocs-service.ts:124-125; test/routes.test.ts:97-101). README:50-53: the source's Mongo `credentials` collection is not read.
- Missing key / unknown key / `apiky-500` / ApiKy unreachable / ApiKy non-JSON: all 403 `{code:"FORBIDDEN", message:"Authentication failed", details:"Principal undefined could not be authenticated. No additional detail was provided."}` (exceptions.ts:25-37 — "undefined" because the source never passes the principal; test/routes.test.ts:12-16,70-89). No 401.
- Key is checked before the body (test/routes.test.ts:86-89).
- Content-Type: `express.json()` only parses `application/json`; other content types: UNVERIFIED (Express 4 leaves `{}`; likely a spec 400, see below). `Accept` not read. No code reads `Authorization`, so a Cloud Run Bearer is ignored by the app (IAM enforcement UNVERIFIED).

### Request
Spec `required` (spec:44-50): `labelSpecification, shipFrom, shipTo, packages, shippingReference, serviceCode`.

| field | spec | what the code does |
| --- | --- | --- |
| `labelSpecification.labelFormat` | required; enum `PDF`,`PNG` only (spec:353-362) | PNG => label converted (below). No ZPL/EPL |
| `serviceCode` | required; enum `ES1`,`EL1`,`EP1`,`EE1` (spec:64-71) | passed unchanged as OCS `service`; no per-customer lookup (ocs-service.ts:133) |
| `incoTerms` | optional; enum `DDP`,`DDU` | -> `termsOfTrade` |
| `shippingReference` | required string | -> `reference` |
| `orderID` | NOT in spec (allowed as extra property) | read by code -> `orderID` (ocs-service.ts:126). Selector sends it (spec example:82) |
| `shipFrom` / `shipTo` (Address) | required fields: `addressLine1, city, name, postalCode, stateOrRegion` (spec:155-160). `stateOrRegion` is required in spite of `default: ''` (test/routes.test.ts:108-129). `countryCode`, `phoneNumber`, `email`, `contactName` optional | mapAddress (ocs-service.ts:64-81): OCS `name` = `companyName` if non-blank else `name`; `contactName` = `contactName` only (fallback reads `address.Name`, never present, so omitted); `address1/2/3`, `town`=`city`, `county`=`stateOrRegion`, `postcode`, `country`=`countryCode` (not upper-cased), `telephone`=`phoneNumber`, `email`. Recipient additionally `mobile`=`phoneNumber`. `vat`, `eori` accepted but never sent |
| `packages` | exactly 1 (minItems 1, maxItems 1; spec:58-63) | only `packages[0]` used |
| `packages[0].weight` | required `{unit: GRAM|KILOGRAM, value:number}`, both required (spec:275-288) | SEE WEIGHT RULE below |
| `packages[0].dimensions` | optional `{length,width,height,unit: INCH|CENTIMETER}` | -> `packages[0].dim1/dim2/dim3` = length/width/height as STRINGS. `INCH` => `(String(n)*2.54).toString()` unrounded; missing dim in INCH => `"NaN"`; missing in CM => key dropped (ocs-service.ts:96-105,115-117) |
| `packages[0].value` | optional `{currency(3), value 0..99999}` | -> top-level `total` (string) and `currency` |
| `packages[0].items[]` | required, minItems 1; each requires `quantity(int>=1), description(<=80), hsCode(<=10), value{currency,value}` (spec:303-351) | -> `packages[0].contents[]`: `name`=description, `quantity`(string), `unit`=value.value (string), `total`=value*quantity (float product as string, e.g. `"0.30000000000000004"`), `hscode`, `mid`=midCode (only if truthy), `sku` (only if truthy), `countryorigin`=countryOfOrigin. Item `currency` is never sent |
| ignored | | `packages[0].description`, `packageClientReferenceId`, `vat`, `eori` |

WEIGHT RULE (the one that matters), ocs-service.ts:107-109:
`weight = packages[0].weight.unit === 'KILOGRAM' ? value : value * 1000`.
- Accepted units (spec enum): `KILOGRAM` and `GRAM` only; anything else fails the schema with 400 before reaching this code.
- `KILOGRAM`: value unchanged (1.5 -> `"1.5"`).
- `GRAM`: value MULTIPLIED by 1000 (1 g -> `"1000"`; 1500 g -> `"1500000"`). The condition is "not KILOGRAM", so the multiplier applies to every non-KILOGRAM unit, not specifically GRAM. Never divided. Pinned by test/ocs-service.test.ts:19-31 and README:168-169.
- The same variable feeds three fields: top-level `weight` (string), top-level `volumetricWeight` (string, identical), and `packages[0].weight` (a NUMBER, not string; ocs-service.ts:113-114,131-132; test/ocs-service.test.ts:33-36).
- Missing weight object/value: code would throw TypeError (`weight.toString()`), but the spec makes weight required so the schema rejects first. With `packages: []`/absent the schema also rejects.
- What unit OCS itself expects: UNVERIFIED (README:168 calls the x1000 "meant to be divided"; mock prints `"<weight> kg"` on the label, mu:61).

Validation errors: 400 `{code:"VALIDATION ERROR", message:"Client request failed validation", details:"Failed to validate client request", metaData:{"0":{instancePath,schemaPath,keyword,params,message}}}`. `metaData` is Ajv's errors ARRAY spread into an object keyed `"0"`,`"1"` (exceptions.ts:47-48; app.ts:82-87). Tests show one entry (first failure only; test/routes.test.ts:109-146). `instancePath` starts with `/requestBody/...`.

Minimal valid request (test/helpers.ts:85-145): `labelSpecification.labelFormat`, `serviceCode`, `shippingReference`, `shipFrom` and `shipTo` each with `name, addressLine1, city, postalCode, stateOrRegion`, `packages:[{weight{unit,value}, items:[{description,hsCode,quantity,value{currency,value}}]}]`. Mock OCS additionally requires a non-blank recipient postcode (mu:114-118) and valid service.

### Response
- Success 201 JSON (app.ts:80): `{shipmentId, secondaryShipmentId, warnings:[], packages:[{documents:{label:{labelStream}, trackingId}}]}` (ocs-service.ts:143-165). `shipmentId` = `secondaryShipmentId` = `trackingId` = OCS `numbers[0]` (mock: `8800` + 8 digits, mu:137). `warnings` always `[]`.
- Field names are LOWER camel (`shipmentId`, `warnings`), unlike the spec's response schema which says `ShipmentId`, `SecondaryShipmentId`, `Warnings` (spec:363-376 vs example spec:399-406 and code).
- `labelStream` = base64 string. PDF format: OCS's base64 PDF passed through unchanged (`result.label`, ocs-service.ts:148). Mock: 4x6in page(s) (mock-kit label.ts:35-36 defaults 288x432pt).
- Exactly ONE label blob, one package entry, even if OCS returns several `numbers` (only `[0]` used). No customs/invoice docs. No ZPL/EPL.
- Multi-page: `MULTI PG` gives a 2-page PDF (page 1 288x432, page 2 288x288; mu:66-79). PDF request => both pages inside the single base64 PDF. PNG request => converter returns one PNG per page, and the LAST page's PNG only is returned (convert-pdf-to-png-service.ts:44-49). Test: 288x288 PNG (test/create-label.test.ts:74-81).
- PNG: base64 PDF -> bytes -> `POST {PDF_CONVERTER_SERVICE_ENDPOINT}/pdfconverter/stream?scale=1754` (A4 height at 150dpi; convert-pdf-to-png-service.ts:3-4,12), `content-Type: application/pdf`, `Accept: multipart/form-data`; multipart answer parsed with `formData()`; last non-string part base64'd. Mock PNG dimensions follow the PDF page size in points, capped 1200px per side (mu:172), so a 4x6 page => 288x432 PNG. Max 20 pages (413).
- Converter retry: on network error or HTTP 500, up to 3 retries (4 calls total), waiting `attempt x PDF_CONVERTER_RETRY_DELAY_MS` = 0, 1000, 2000 ms (default 1000, config.ts:30; convert-pdf-to-png-service.ts:15-36). A persistent converter 500 therefore costs >= 3 s before the 500 is returned. Any other non-OK status (e.g. 422) is final with no retry.

### Error shape
Common `{code, message, details}` (exceptions.ts:20-22); `metaData` only on validation.

| status | code | message | when |
| --- | --- | --- | --- |
| 400 | `VALIDATION ERROR` | `Client request failed validation` | unknown path/method (`details:"Requested path not found"`, `metaData:{request:{method(lowercase),path}}`); schema failure (above) |
| 403 | `FORBIDDEN` | `Authentication failed` | key problems (above) |
| 599 | `CARRIER SERVER ERROR` | `Server error received from Ocs` | OCS answered ANY non-2xx. `details` = OCS's body as received: parsed JSON, else raw text, `""` if empty (ocs-integration.ts:25-33,49-53). The proxy hard-codes `carrierErrorCode: 500`, and `CarrierError` maps `<500 -> 400`, `>=500 -> 599` (exceptions.ts:67), so the 400 branch is dead code and a carrier 400/401/503 all surface as 599 |
| 500 | `INTERNAL SERVER ERROR` | `An internal server error occurred` | PDF converter answered non-OK (after retries): `details:"An internal server error occurred. No additonal detail is available."` (typo "additonal" kept, exceptions.ts:78) |
| 500 | `INTERNAL SERVER ERROR` | `An unexpected error occurred` | anything else: malformed JSON, body >100kb, OCS unreachable (TypeError reading `e.response.data` in source; here a fetch rejection), converter unreachable, OCS success without `numbers`; `details:"An unexpected error occurred on the server, no additional detail is available"` (global-error.ts:30-34) |

HTTP status 599 is non-standard; a client must not treat it as a network error. Malformed JSON is a 500, not 400 (test/routes.test.ts:158-165).

### Failure scenarios for D5 (magic values)
Magic = `shipTo.postalCode` (arrives at mock as `recipient.postcode`), compared after removing ALL whitespace and upper-casing (`normalise`, mu:36-37), so `err 400`/`ERR400` fire. They apply only AFTER mock checks pass: account/token (401), service (400), packages count (<=20), contents count (<=999), non-blank postcode (400 `Recipient postcode is required`) (mu:96-118).

| operation | field | magic value | where verified | what the caller sees |
| --- | --- | --- | --- | --- |
| createLabel | `shipTo.postalCode` | `ERR 400` | mu:120-123 | mock 400 `{status:"error", message:"Recipient postcode is not valid for this service"}` => 599 `CARRIER SERVER ERROR`, `details` = that object (test/create-label.test.ts:148-158) |
| createLabel | same | `ERR 500` | mu:124-127 | mock 500 `{status:"error", message:"Internal server error"}` => 599, details = that object |
| createLabel | same | `ERR 503` | mu:128-131 | mock 503 empty body => 599, `details:""` (test:165-168) |
| createLabel | same | `NO NUMS` | mu:132-135 | mock 200 `{status:"success", label:""}` (no `numbers`). PDF request: TypeError => 500 `INTERNAL SERVER ERROR` "An unexpected error occurred" (test:180-183). PNG request: UNVERIFIED, inferred: converter is called first with an empty body (ocs-service.ts:148-149), mock converter 422 (mu:153-156) => non-OK => 500 "An internal server error occurred" (no retry on 422) |
| createLabel | same | `MULTI PG` | mu:66-79,141 | 201; PDF has 2 pages (page 2 is 4x4in); PNG request returns page 2 only (288x288) |
| createLabel, `labelFormat:"PNG"` | same | `PNG 500` | mu:80,142-143,157-160 | label PDF carries a failure marker; converter 500 x4 calls (0/1/2 s waits, >=3 s total) => 500 `INTERNAL SERVER ERROR` "An internal server error occurred" + `"...additonal detail..."` (test:194-209). PDF request: normal 201 |
| createLabel | OCS credentials (deployment config, not request) | `OCS_USER`/`OCS_TOKEN` differ from fixture | mu:96-99 | every call => 599 with `details:{status:"error", message:"Invalid account or token"}` (test:170-178). Not caller-triggerable |
| createLabel | `x-api-key` | none / unknown / `apiky-500` | apiky mock | 403 FORBIDDEN "Principal undefined..." |
| createLabel | body | malformed JSON; >100kb | app.ts:70 | 500 "An unexpected error occurred" (test/routes.test.ts:158-170) |
| createLabel | schema | missing `stateOrRegion`; `serviceCode` not in ES1/EL1/EP1/EE1; 2 packages; empty `items` | spec | 400 VALIDATION ERROR, `metaData["0"].keyword` = `required`/`enum`/`maxItems`/`minItems` (test/routes.test.ts:108-146) |
| createLabel | OCS unreachable (infra) | | test/create-label.test.ts:185-190 | 500 "An unexpected error occurred" (NOT 599) |
| createLabel | converter unreachable (infra) | | test:211-216 | 500 "An unexpected error occurred" after retries |

### Quirks mirrored from production
- Every OCS rejection is a 599 regardless of OCS status (ocs-integration.ts:51-52; exceptions.ts:67; README:162-163).
- Grams multiplied by 1000, KILOGRAM untouched; condition is `!== 'KILOGRAM'` (ocs-service.ts:107-109).
- `weight` and `volumetricWeight` are always identical (ocs-service.ts:131-132); `packages[0].weight` is a number, the others strings.
- Dimensions: strings; inch conversion unrounded; `"NaN"` for missing inch dimension.
- Commodity `total` = float product (`"0.30000000000000004"`).
- `contactName` never falls back to `name` (reads capital-N `Name`).
- VAT/EORI/`packageClientReferenceId`/package `description` ignored.
- 403 detail reads "Principal undefined".
- One shared OCS account for every caller; ApiKy profile does not pick it.
- Multi-page PNG keeps the last page only.
- OCS unreachable and OCS-success-without-`numbers` are generic 500, not 599.
- Malformed JSON and >100kb are 500.
- Typos kept: `additonal` (exceptions.ts:78), `An validation error occurred` (exceptions.ts:46, default only).
- All read from source, not verified against production traffic (README:160 context).

### Statefulness / ordering constraints
None. Stateless mock (mu header: "keeps nothing in memory"); every call mints a new `8800`-prefixed number. No idempotency: the same `shippingReference`/`orderID` booked twice creates two parcels. No cancel exists, so a booked parcel cannot be undone through this proxy. No per-instance caches in the proxy. If PNG conversion fails (`PNG 500`), the OCS parcel has already been booked but the caller gets a 500 and no tracking number (orphaned parcel); a retry books another.

### Adapter implications and leaks
- Only create+label in one call; validate/cancel/manifest/reprint/track are unsupported.
- Weight: send KILOGRAM for the expected result; GRAM is silently inflated x1000 (a faithful-to-prod bug). An adapter that normalises weights to one unit should pick KILOGRAM; do NOT send GRAM expecting conversion to kg.
- Required fields stricter than a generic model: `name` and `stateOrRegion` on both addresses (empty string `''` for stateOrRegion would satisfy required but `minLength` is not set on it; `name` min 1), `shippingReference`, exactly one package with >=1 item each with `hsCode` and `value`. `countryCode` not required by schema yet needed by real OCS (UNVERIFIED).
- `orderID` is a hidden extra field the code reads.
- Service codes: only `ES1`,`EL1`,`EP1`,`EE1`; label formats only PDF/PNG.
- Error classification: carrier failure = HTTP 599 (check `status >= 599` or `code === "CARRIER SERVER ERROR"`), `details` is opaque OCS body (string or object, possibly `""`). 500 = converter or proxy fault or OCS unreachable. 403 = auth. 400 = our schema.
- Latency: PNG failures can take >= 3 s because the OCS proxy sleeps between converter retries (InPost proxy does not sleep). Use generous client timeouts.
- Label: base64, single blob; PDF may be multi-page (page 2 may be a different size); PNG is last page only, so for PDF consumers handle multi-page, for PNG consumers be aware pages are dropped.
- `trackingId` = `shipmentId` = `secondaryShipmentId`; no tracking URL; `warnings` always empty.

### README-vs-source discrepancies, and UNVERIFIED
README vs source:
- README:41 says OCS non-2xx is 599; true (via the hard-coded 500). Source also contains a `<500 -> 400` branch (exceptions.ts:67) that is unreachable; README mentions the mapping.
- README:50-52 says the source README describes a MongoDB `ocs.credentials` collection that no code reads — consistent with src (no store module exists in `apps/ocs-proxy/src`).
- README:63 says "`packages[0].weight` (number)" — consistent. README:64 says "`packages[0].dim1`/`dim2`/`dim3`"; consistent.
- README:96 says PDF `MULTI PG` returns "both pages" — consistent with mu:66-79, but note the pages are different sizes (4x6 then 4x4).
- Spec response schema keys (`ShipmentId`, `SecondaryShipmentId`, `Warnings`, `packages`) disagree with spec example and code (`shipmentId`, `secondaryShipmentId`, `warnings`).
- Spec `servers.url` has no scheme; `Package.weight` description is copy-pasted "Declared monetary value" — cosmetic.
- Spec marks `shipTo.countryCode` optional but real OCS likely needs it (UNVERIFIED); proxy sends `country: undefined` => key dropped; mock does not check.

UNVERIFIED:
- PNG + `NO NUMS` outcome (inferred above).
- Whether OCS expects grams or kilograms in `weight` (code multiplies; mock labels as kg).
- Non-JSON content-type behaviour (`text/plain`) for this proxy (no test; Express 4 body `{}` likely gives a spec 400).
- Cloud Run IAM / Authorization handling.
- `prod-57357` image tag in the E2 draft: `git grep 57357` over origin/main returns nothing; README only names image `gfs-ocs-integration` and commit `29eeaa6`.
- All "production behaviour" claims: from source code, not prod traffic.

### Notes for the E2 draft
- Line 29 (table row): "ADO `ocs-proxy`, `main` `29eeaa6` (prod image `prod-57357`)" — `29eeaa6` and ADO repo match README:3-6; `prod-57357` appears nowhere in the repo (`git grep` empty). UNVERIFIED, do not state it as fact. Description "Books an OCS Worldwide parcel and returns its label" is correct.
- Lines 60,68 (keys, bad-key table): `ocs-key-alpha`/`ocs-key-bravo` correct; `403/403/403` correct (details text says "Principal undefined").
- Line 149: `ERR 400/500/503` -> "599 carrier error" correct (503 gives `details:""`).
- Line 150: `NO NUMS` -> "500 'An unexpected error occurred'" correct for a PDF request only; with `labelFormat: PNG` it is likely a different 500 (`An internal server error occurred`, via a 422 from the converter). UNVERIFIED.
- Line 151: "`MULTI PG` A two-page label. PNG keeps page 2 only." correct; add that page 2 is a different size (4x4in) and that a PDF request gets both pages in one base64 PDF.
- Line 152: "`PNG 500` 500 after four converter calls" correct; add: PNG-only, takes >= 3 s (0/1/2 s waits), and the body is `An internal server error occurred` (not the unexpected-error text).
- Line 179: "OCS and Exelot multiply a GRAM weight by 1000" — correct but imprecise: code multiplies any unit that is not exactly `KILOGRAM`; spec enum limits it to GRAM|KILOGRAM so equivalent for valid requests. KILOGRAM is untouched.
- Line 181: "OCS and Exelot return 599 for every carrier rejection" — correct for OCS rejections; OCS unreachable and OCS-success-without-numbers are plain 500, and converter failure is 500.
- Line 184: "Typos kept, for example `additonal`" — correct; it is the OCS converter-failure body (exceptions.ts:78).
- Line 188: "Some upstream error shapes are invented (BJS, OCS)" — correct (README:113-114).


---

## exelot (Exelot; apps/exelot-proxy; mirrors exelot.gfsdeliver.com, ADO `GFS Exelot Integration` main b21a47d)

All paths relative to repo root `carrier-playground`, line numbers from `origin/main`. Express + openapi-backend 5.11.1 against `apps/exelot-proxy/api/exelot-integration-api.yaml`. Port 4110 locally; Cloud Run container port 8080 (`iac/projects/mock-exelot/cloud-run.tf:19`).

### Operations and routes

| operation | METHOD path | supported? | notes |
| --- | --- | --- | --- |
| validate | none | NO | no validate/rate/service-lookup route |
| create-ship (parcel + label) | POST `/shipping/createLabel` | YES, the only business route | one call = Exelot login (token cached) + commercial invoice PDF + create parcel + label. Success is **201**. `apps/exelot-proxy/api/exelot-integration-api.yaml:17-38`, handler `apps/exelot-proxy/src/app.ts:84-97` |
| delete / cancel | none | NO | no cancel route; a parcel once created cannot be undone through this proxy |
| commit / manifest | none | NO | |
| reprint | none | NO | re-calling createLabel creates a **second** parcel (no idempotency, see Statefulness) |
| track | none | NO | |
| health | GET `/health/liveness` -> 200 `{"ok":true}`; GET `/` -> 200 text `ok` | YES | `src/app.ts:72-74`, `:78-80`. `/` is the source's LB check; liveness is mock-only and unlogged. `/healthz`, `/health` are NOT served: they fall to the openapi notFound handler and return **400** `VALIDATION ERROR` "Requested path not found" (`src/app.ts:104-110`), not 404 |

Order of processing (`src/app.ts:48`, README:22-26): correlation, `/health/liveness`, request log, `express.json()` (100kb default), `GET /`, then openapi-backend = route match, then `x-api-key` security handler, then schema validation, then handler. An unknown path or wrong method is answered **before** auth (so no key needed to get the 400), and a bad key is answered before schema errors (`test/routes.test.ts:72-75`).

### Auth and headers

- Header: `x-api-key` (spec `securitySchemes.api_key`, `api/exelot-integration-api.yaml:386-390`). Looked up via ApiKy `GET {APIKY_BASE_URL}/api/profile?token=<key>` with service key header (`packages/apiky-client/src/index.ts:32-37`). In the deployed mock `APIKY_BASE_URL` is `<mock-upstreams>/apiky` (`iac/projects/mock-exelot/cloud-run.tf:30`).
- Fixture key names (`apps/mock-upstreams/fixtures/apiky/exelot.json:3-28`): `exelot-key-alpha` (partner `MOCK-PARTNER-ALPHA`, PDF labels, works), `exelot-key-bravo` (`MOCK-PARTNER-BRAVO`, PNG labels), `exelot-key-zpl` (`MOCK-PARTNER-CHARLIE`, ZPL labels), `exelot-key-bad-login` (`MOCK-PARTNER-DELTA`, stored password wrong), `exelot-key-unconfigured` (`MOCK-PARTNER-ECHO`, no credentials doc), `exelot-key-malformed-profile` (profile has no `profile` block), `apiky-500` (ApiKy 500, `apps/mock-upstreams/src/apiky/index.ts:37-40`). Service key for ApiKy lookup: fixture value elided.
- No key / unknown key / `apiky-500` / ApiKy unreachable: all identical **403** `{"code":"FORBIDDEN","message":"Authentication failed","details":"Principal undefined could not be authenticated. No additional detail was provided."}` (`src/exceptions.ts:25-37`, `src/integrations/apiky-integration.ts:5-21` swallows every ApiKy failure to `undefined`; `src/app.ts:120-126`). Content-Type is `application/json` (express `.send(obj)`, `src/middlewares/global-error.ts:25`), not problem+json.
- Exelot login failure (wrong creds or login URL unreachable): 403 same body but `details: "Principal <partnerId> could not be authenticated. ..."` (`src/integrations/get-exelot-access-token.ts:22-25`) - leaks the partner id.
- Authenticated key whose profile lacks `profile.exelotPartnerId` block (`exelot-key-malformed-profile`): auth passes, then TypeError -> generic 500 (`src/integrations/exelot-integration.ts:15-16,33`). Partner with no credentials document (`exelot-key-unconfigured`): TypeError at `get-exelot-access-token.ts:11-13` -> generic 500.
- Content-Type: body is parsed only by `express.json()` (`src/app.ts:77`); the spec declares `application/json` required (`api/...yaml:25-31`). UNVERIFIED: what a non-JSON content-type returns (openapi-backend requestBody handling not exercised in tests).
- `Authorization: Bearer ...`: neither `src/` file reads an Authorization header (`git grep -i authorization -- apps/exelot-proxy/src` empty), so the app ignores it. UNVERIFIED: whether Cloud Run's frontend rejects an invalid bearer on an `allUsers` service. `X-Serverless-Authorization` is only set on the proxy's calls to mock-upstreams (`packages/mock-kit/src/upstream-auth.ts:33-39`).
- "Always calls real ApiKy" (handover claim): **this describes the production source, not the mock.** README:129-132 and `apps/royal-mail-proxy/README.md:109-110`: the prod code reads `process.sourceMapsEnabled.APIKY_AUTH_URI` (always undefined) so prod always calls the production ApiKy URL whatever env says. The mock replaces that with `APIKY_BASE_URL` + `/api/profile` through `@playground/apiky-client` (URL-encodes the key). No real host is hard-coded anywhere in `apps/exelot-proxy/src` (grep for `gfsdeliver|apiky.io|https://` finds only a log string at `apiky-integration.ts:14`). The deployed mock calls mock-upstreams' fake ApiKy only. Exelot login, create-parcel and the PDF converter likewise go to mock-upstreams (`cloud-run.tf:30-34`); the source's hard-coded converter host `ecm.gfsdeliver.com` is replaced by `PDF_CONVERTER_SERVICE_ENDPOINT` (README:133-135).

### Request

Body `CreateLabelRequest` (`api/exelot-integration-api.yaml:41-134`). **Nothing at top level is required by the schema** (no `required:` on `CreateLabelRequest`), so missing parts fail later in code as generic 500s (see Error shape).

What the code reads (`src/services/exelot-service.ts:35-89`, `src/pdf-generation/pdf-invoice-generator.ts:50-159`):

| request field | used as | spec | notes |
| --- | --- | --- | --- |
| `labelSpecification.labelFormat` | caller's wanted format | enum `PDF`,`PNG` (`:331-340`) | read **after** the parcel is created (`exelot-integration.ts:57`); absent -> TypeError -> 500 after Exelot made the parcel (`test/create-label.test.ts:108-116`) |
| `orderID` | Exelot `orderID`; invoice "Shipment Ref" | not in spec `properties` | extra props allowed |
| `shipFrom` / `shipTo` | Exelot `sender` / `receiver` | `Address` required: `addressLine1`,`city`,`name`,`postalCode`,`stateOrRegion` (`:137-142`); NOT required by spec: `countryCode`, `phoneNumber`, `email`, `contactName` | absent `shipFrom`/`shipTo` object -> generic 500 (invoice `buildAddress(undefined)`, `test/routes.test.ts:152-156`) |
| address `name` / `companyName` | Exelot `name` = `companyName` if non-blank else `name` (`:21`) | name max 60, companyName max 35 | invoice prints `name` only, never `companyName` (`invoice:94-96`) |
| `contactName` | Exelot `contactName` = `contactName` else `address.Name` (capital N, never exists) -> dropped (`:22`) | | so no contactName sent unless caller supplies it |
| `addressLine1/2`, `city`, `stateOrRegion`, `countryCode`, `postalCode`, `phoneNumber` | `addrLine1`, `addrLine2`, `city`, `state`, `country`, `zip`, `phoneNumber` (`:23-29`) | `addressLine3`, `vat`, `eori` unused in the Exelot body | `countryCode` is ISO alpha-2, min/max length 2; sender `vat`/`eori` only appear on the invoice (`invoice:82,87`) |
| `shipTo.email` | receiver `email` only (sender email never sent, `:30`) | max 64 | |
| `packages[0]` | only the first package is read | `minItems 1`, `maxItems 1` (`:52-54`) | a second package -> 400 `VALIDATION ERROR` metaData `maxItems`. Absent `packages` -> TypeError -> generic 500 (`test/exelot-service.test.ts:87-89`) |
| `packages[0].weight` `{unit,value}` | Exelot `weight` and `volumetricWeight` (identical, both strings) | `unit` enum `GRAM`,`KILOGRAM`; `weight` object optional but if present `unit` and `value` required (`:254-267`) | see weight quirk below |
| `packages[0].dimensions` `{length,width,height,unit}` | `dimL/dimW/dimH` strings | `unit` enum `INCH`,`CENTIMETER` (`:279-281`) | `INCH` -> each x 2.54, unrounded float (`:51-55`); anything else (incl. unit omitted) is passed as given, i.e. treated as cm. Dimensions absent -> `dimL` etc. `undefined`, dropped. INCH with a missing side sends the string `"NaN"` |
| `packages[0].description`, `value.value`, `value.currency`, `weight.value` | Exelot `items.{description,declaredValue,currency,weight}` (`:57-64`), `weight` here is the **raw unconverted** value | `value.currency` exactly 3 chars; `value.value` 0..99999 | invoice also prints `Currency: <packages[0].value.currency>` and `Reference / Order No: packageClientReferenceId` |
| `customs.commodities[]` | Exelot `itemList[]`: `description`,`hscode` (from `hsCode`),`declaredValue`,`quantity` (strings), optional `countryOfOrg` (from `countryOfOrigin`), `sku` (`:36-43`) | commodity requires `quantity` (int >=1), `description` (<=80), `hsCode` (<=8), `value{currency,value}` (`:292-296`); `customs` itself optional | absent `customs` -> `itemList: []` and an invoice with no lines. Per-commodity `weight` is NOT in the spec but the invoice reads `commodity.weight.value` for "Unit Weight"/totals; when absent the column is blank and the total prints `NaN` |
| `serviceLine` | Exelot `serviceLine` | enum `XLT`,`XLT_P` (`:59-64`) | absent is allowed by the schema but mock Exelot then 400s (`serviceLine` "is not a supported service line") -> 599 |
| `incoTerms` | Exelot `incoterms` (note lowercase key) | enum `DDP`,`DDU` | invoice **always** prints "Terms of Trade: DDU" and "UK origin" regardless (`invoice:127,348`) |
| `invoiceId` | Exelot `invoiceID`; invoice number | string | absent -> invoice number from in-memory counter, 7-digit zero padded, **counter value before increment**, starts at 1 (`invoice:433-436`, `src/stores/exelot-store.ts:33-38`, `fixtures/next-numbers.json`); `invoiceID` upstream is then dropped |

**Weight unit quirk (verified):** `weight = unit === 'KILOGRAM' ? value : value * 1000` (`src/services/exelot-service.ts:66-68`). So **any unit other than the exact string `KILOGRAM` is multiplied by 1000** (GRAM 500 -> `"500000"`), and no weight object at all gives `NaN * 1000` -> the string `"NaN"` (mock Exelot rejects, see D5). Exelot never receives a unit. Because the spec enum is only `GRAM`/`KILOGRAM`, `POUND`/`OUNCE`/lowercase units are rejected with 400 `VALIDATION ERROR` (Ajv `enum`) before reaching this code. Zero weight -> `"0"` -> mock Exelot 400 -> 599. No maximum weight is enforced anywhere.

**Required by mock Exelot (upstream), reachable through the proxy** (`apps/mock-upstreams/src/exelot/index.ts:55-80`): sender and receiver `name`,`addrLine1`,`city`,`country` (receiver `zip` too), `serviceLine` in `XLT`/`XLT_P`, `Number(weight) > 0`, `invoiceFile` a base64 PDF with `fileType: "pdf"` (always true via proxy), `itemList` an array of <= 999 items. Consequence: **`shipFrom.countryCode` / `shipTo.countryCode` are optional in the spec but mandatory in practice**; omitting them gives 599 with Exelot's 400 body as `details`.

**Invoice text restriction:** the invoice is drawn with pdf-lib standard Times Roman (WinAnsi). Any character outside WinAnsi in any printed field (names, address lines, city, email, phone, vat, eori, commodity description, order ids, etc.) makes pdf-lib throw -> generic 500 **before Exelot is called** (`test/create-label.test.ts:224-230`, `invoice:49` comment). UNVERIFIED: embedded newlines in a field (pdf-lib normally also throws on `\n` with WinAnsi). Country names on the invoice come from a table; unknown code prints `undefined` (`src/services/country-codes.ts:1,253-256`).

Order of side effects inside one call (`src/integrations/exelot-integration.ts:33-57`): token fetch/login -> (debug-data short-circuit) -> map request incl. build invoice PDF and consume invoice number -> POST parcel -> map label. So login errors beat body mapping errors; the invoice counter is consumed even if Exelot later fails.

### Response

Success **201** (`src/app.ts:91`), `application/json`:

```
{ "shipmentId": <Exelot barcode>, "secondaryShipmentId": <Exelot xltID>, "warnings": [],
  "packages": [ { "documents": { "label": { "labelStream": "<base64>" }, "trackingId": <same barcode> } } ] }
```
(`src/services/exelot-service.ts:116-121`.) Always exactly one package, one label, `warnings` always `[]`. The camelCase above is what is sent; the spec's response schema uses `ShipmentId`/`SecondaryShipmentId`/`Warnings` and is not enforced (README:164-165). No customs/invoice document is returned (the commercial invoice goes to Exelot inside the parcel request and is never echoed, except under the `RETURN_DEBUG_PDF=1` switch, off in dev: `cloud-run.tf:35-36`).

Label: raw base64 of the file bytes (no data-URI prefix, no `labelFormat` echo). Format matrix (`exelot-service.ts:105-114`):

| caller `labelFormat` | upstream returns PDF | upstream returns PNG | upstream returns anything else (ZPL) |
| --- | --- | --- | --- |
| `PDF` | PDF passed through | 500 | 500 |
| `PNG` | converted by PDF converter, **last page only**, scale 1754 | PNG passed through | 500 |

So the caller **never receives ZPL** (the ZPL partner `exelot-key-zpl` is always a 500). Converter: `POST {PDF_CONVERTER_SERVICE_ENDPOINT}/pdfconverter/stream?scale=1754`, multipart response, last non-string part wins; retried on network error or 500 up to 3 more times with waits 0,1,2 s, then 500 (`src/pdf-generation/convert-pdf-to-png-service.ts:6,18,34-40,46-60`). Mock label content: PDF from `makeLabelPdf` (4x6, "MOCK LABEL - NOT FOR CARRIAGE", service, town+zip, weight), PNG a blank mock PNG (`apps/mock-upstreams/src/exelot/index.ts:82-97`). Ids: barcode `MOCKXLT` + 9 digits, xltID `MOCKID` + 9 digits (`:153,169`). A converter returning no file part yields `labelStream: undefined` (key dropped from JSON) with a 201.

### Error shape

Common shape (`src/exceptions.ts:2-23`): `{ "code": string, "message": string, "details": any }`, plus `metaData` for validation. `Content-Type: application/json` (NOT problem+json; contrast veho).

| status | `code` / `message` | when |
| --- | --- | --- |
| 400 | `VALIDATION ERROR` / "Client request failed validation"; `details` "Failed to validate client request"; `metaData` = Ajv errors object keyed `"0"`,`"1"`... (array spread into object, `exceptions.ts:47-48`) | schema failure: e.g. `serviceLine` not XLT/XLT_P, 2nd package (`maxItems`), missing `stateOrRegion`, bad `weight.unit`. `test/routes.test.ts:99-131` |
| 400 | `VALIDATION ERROR`, `details` "Requested path not found", `metaData {request:{method,path}}` (method lower-case) | unknown path or wrong method (also `/healthz`, `GET /shipping/createLabel`) |
| 403 | `FORBIDDEN` / "Authentication failed" | no key, bad key, ApiKy down, or Exelot login failure (see Auth) |
| 599 | `CARRIER SERVER ERROR` / "Server error received from Exelot"; `details` = Exelot's response body (parsed JSON if it parses, else text, `""` for empty) | **any** non-2xx from Exelot create-parcel incl. 4xx (`exelot-integration.ts:54`). `CarrierError` has a code path for `<500 -> 400` (`exceptions.ts:67`) but the only caller hard-codes 500, so the 400 branch is dead and a 4xx from Exelot is 599 |
| 500 | `INTERNAL SERVER ERROR` / "An internal server error occurred", `details` "An internal server error occurred. No additonal detail is available." (typo `additonal` kept) | label format rules refused (ZPL, or PNG when PDF asked), PDF converter failed, invoice counter missing (`exceptions.ts:71-81`) |
| 500 | `INTERNAL SERVER ERROR` / "An unexpected error occurred", `details` "An unexpected error occurred on the server, no additional detail is available" | everything else: malformed JSON, body > 100kb, missing `profile` block, partner without credentials, Exelot unreachable (fetch throws), body without `shipFrom`/`shipTo`/`packages`, non-WinAnsi text, body without `labelSpecification` (after parcel created) (`src/middlewares/global-error.ts:28-32`, `README:47`) |

Malformed JSON and oversize body are the generic **500**, not 400. An unreachable Exelot (network error) is a generic 500, whereas an unreachable Exelot **login** is 403.

### Failure scenarios for D5 (magic values)

Normalisation: mock Exelot compares `shipTo.postalCode` with all whitespace stripped and upper-cased (`apps/mock-upstreams/src/exelot/index.ts:36-37`), so `err 400`, `ERR400`, `Err  400` all fire. They are evaluated **after** the mock's own body checks, which run only if the proxy's body already satisfies them (`:128-134`). The proxy itself passes `postalCode` through unchanged, so the value must also satisfy the proxy schema (1-20 chars).

| operation | field | magic value | where verified | caller sees |
| --- | --- | --- | --- | --- |
| createLabel | `shipTo.postalCode` | `ERR 400` | `mock-upstreams/src/exelot/index.ts:136-139` | 599 `CARRIER SERVER ERROR`, `details` = `{"status":"error","message":"Validation failed","errors":[{"field":"receiver.zip","message":"is not a valid zip code"}]}` |
| createLabel | `shipTo.postalCode` | `ERR 401` | `:140-143` | 599, `details` `{"status":"error","message":"Unauthorized"}`; no re-login, cached token stays (`test/create-label.test.ts:138-141`) |
| createLabel | `shipTo.postalCode` | `ERR 500` | `:144-147` | 599, `details` `{"status":"error","message":"Internal server error"}` |
| createLabel | `shipTo.postalCode` | `ERR 503` | `:148-151` | 599, `details: ""` (empty body) |
| createLabel + `labelFormat: PNG` | `shipTo.postalCode` | `PNG FAIL` | `:82-96`, converter `:184-187`; `test/create-label.test.ts:100-106` | 500 "An internal server error occurred" after **4** converter calls (initial + 3 retries, waits 0+1+2 s ~ 3 s). Only for a PDF-label partner (`exelot-key-alpha`); with `labelFormat: PDF` the same value returns a normal 201 PDF; `exelot-key-bravo` passes PNG through so it never fires |
| createLabel | `x-api-key` | missing / unknown / `apiky-500` | `ApiKy mock :31-47` | 403 `FORBIDDEN` "Principal undefined..." |
| createLabel | `x-api-key` | `exelot-key-bad-login` | `fixtures/credentials.json` (password value elided) | 403 `FORBIDDEN`, details "Principal MOCK-PARTNER-DELTA ..." |
| createLabel | `x-api-key` | `exelot-key-zpl` | `fixtures/exelot/exelot.json` accounts[2] `labelFormat: ZPL` | 500 "An internal server error occurred" whatever `labelFormat` asked (parcel IS created) |
| createLabel | `x-api-key` + `labelFormat` | `exelot-key-bravo` with `labelFormat: PDF` | `exelot-service.ts:108-110` | 500 "An internal server error occurred" (parcel IS created); `PNG` request succeeds without converter |
| createLabel | `x-api-key` | `exelot-key-unconfigured` | `get-exelot-access-token.ts:11-13` | 500 "An unexpected error occurred" |
| createLabel | `x-api-key` | `exelot-key-malformed-profile` | `exelot-integration.ts:33` | 500 "An unexpected error occurred" |
| createLabel | `packages[0].weight` | omitted, or value 0 | `exelot-service.ts:66-75`, mock `index.ts:69` | 599, Exelot 400 body names field `weight` "must be a positive number" (derived by reading code; no test) |
| createLabel | `shipFrom.countryCode` / `shipTo.countryCode` | omitted | mock `index.ts:58-59` | 599, Exelot 400 body field `sender.country` / `receiver.country` "is required" (derived) |
| createLabel | any text field | character outside WinAnsi (e.g. `Lukasz` with Polish L-stroke) | `test/create-label.test.ts:224-230` | 500 "An unexpected error occurred", no Exelot call |
| createLabel | body | malformed JSON / > 100kb | `test/routes.test.ts:138-150` | 500 "An unexpected error occurred" |
| createLabel | body | no `labelSpecification` | `test/create-label.test.ts:108-116` | 500 "An unexpected error occurred" **after the parcel was created** |
| createLabel | `serviceLine` | not `XLT`/`XLT_P` | `test/routes.test.ts:122-125` | 400 `VALIDATION ERROR`, metaData[0].keyword `enum`, no Exelot call |
| createLabel | `packages` | 2 items | `test/routes.test.ts:127-131` | 400 `VALIDATION ERROR`, `maxItems` |

No operation other than createLabel exists, so D5 has no id-prefix scenarios for Exelot.

### Quirks mirrored from production

- GRAM is multiplied by 1000, not divided; every non-`KILOGRAM` unit gets x1000 and is sent as both `weight` and `volumetricWeight`; no unit is sent to Exelot (`src/services/exelot-service.ts:66-77`, README:152-153).
- 599 `CARRIER SERVER ERROR` for **every** Exelot non-2xx, 4xx included; 401 from Exelot neither drops the cached token nor retries even though the spec doc asks for both (`exelot-integration.ts:54`, README:156-157).
- Malformed JSON / oversize body = generic 500; missing credentials doc = generic 500, not 403 (README:158-159).
- Token fetched and invoice built/numbered before `labelSpecification` is checked, so a body without it creates a real parcel and then 500s (README:160-161).
- Invoice number = counter value **before** increment; invoice text hard-codes "Terms of Trade: DDU" and "UK origin" regardless of `incoTerms` (README:162-163, `invoice:127,348`).
- `contactName` fallback reads `address.Name` (capital N), so it is dropped when the caller omits `contactName` (`exelot-service.ts:22`).
- Error text typo `additonal` kept (`exceptions.ts:79`). Unknown path/method is 400 not 404.
- Only `packages[0]` is mapped; spec forces exactly one package. Exelot receives `incoterms` (lowercase) from `incoTerms`.
- Source ordering: route, key, schema (README:22-26).

### Statefulness / ordering constraints

- No operation depends on another; no create-before-X ordering.
- **Not idempotent**: calling createLabel twice with the same `orderID`/`invoiceId` creates two parcels and two barcodes (the mock Exelot "keeps nothing in memory", README:99-101).
- Per-instance in-memory state in the proxy: Exelot token cache (per partner id, 5 min TTL, max 100, concurrent misses share one login; failed logins not cached) (`src/stores/access-token-cache.ts:5-9`); invoice counter (starts at 1, increments per request lacking `invoiceId`, resets on a new instance) (`exelot-store.ts:26-38`). Mock Exelot tokens are stateless and valid 24 h across instances (README:99-101, `mock-upstreams/src/exelot/index.ts:29-31,111-112`).
- Dev Cloud Run has `min_instance_count = 0` (`iac/env/dev.tfvars:4`), so the first call after idle is a cold start (and a login).

### Adapter implications and leaks

- Only **create** exists. A generic validate/delete/commit/manifest interface must mark all three unsupported for Exelot (return "not supported" without calling).
- Success is **201** not 200. Label path is `packages[0].documents.label.labelStream`; tracking number is `packages[0].documents.trackingId` == `shipmentId`; carrier reference 2 is `secondaryShipmentId`. One parcel, one label only.
- Customer must ask for the label format the partner is provisioned for: `PDF` for alpha, `PNG` for bravo; PDF-asked-but-PNG-provisioned is a 500 **after** a parcel was created (leaked, un-cancellable orphan). ZPL is impossible. The adapter should translate per-account label format config into `labelSpecification.labelFormat`.
- Weight: send **KILOGRAM only**. `GRAM` is x1000 (looks like a bug but is mirrored); POUND/OUNCE are rejected by schema. Always send a positive weight object.
- Always send `shipFrom.countryCode`/`shipTo.countryCode`, `serviceLine` and `labelSpecification` even though the schema marks them optional. Send ASCII/WinAnsi-only text; transliterate before sending or the proxy 500s with no useful message.
- Error mapping: treat 599 as "carrier rejected, see `details` (Exelot's own body, shape unknown/unstable: object, string or empty)", 400 = our request invalid (Ajv `metaData` keyed by index), 403 = bad ApiKy key **or** bad partner login (disambiguate via `details` containing a partner id), 500 = proxy/format problem (distinguish the two 500 `message` strings). 599 is a non-standard status: make sure the HTTP client and retry logic treat it as a 5xx-class carrier failure.
- Retry safety: a 599/500 after the parcel was created may already have created the parcel (500 for format mismatch, missing `labelSpecification`, converter failure). Blind retry creates duplicates; no cancel exists.
- Use `x-api-key` only; `/health/liveness` for probes (`/healthz` gives 400).
- Body size < 100kb (label requests are small; commodities lists could exceed with huge customs).

### README-vs-source discrepancies, and UNVERIFIED

README vs source (README:1-165 vs code):
- README:44 table lists "`Principal <partner id> could not be authenticated`" for 403; matches `get-exelot-access-token.ts:22-25`. OK.
- README:45 "599 any non-2xx": matches; but `exceptions.ts:66-67` contains a dead 4xx->400 branch that the README does not mention (not a behavioural discrepancy).
- README:30 says `shipmentId`/`trackingId` = barcode and `secondaryShipmentId` = xltID: matches `exelot-service.ts:117-120`.
- README:80 says magic zip comparison ignores "spaces and case"; code strips **all** whitespace runs and upper-cases (`index.ts:36`). Consistent.
- README:93 says "`weight` a positive number" for mock Exelot: code is `Number(body.weight) > 0` (`index.ts:69`), so a numeric string passes and `"NaN"` fails. Consistent.
- README does not state the converter retry timing (0/1/2 s waits): `convert-pdf-to-png-service.ts:34-40` (attempt x 1000 ms; attempts 0..3).
- Spec (`api/exelot-integration-api.yaml:341-385`) response keys `ShipmentId`/`Warnings` do not match what is sent (acknowledged README:164-165). Spec `CreateLabelResponse.example` itself uses camelCase.
- Spec marks `weight.unit` required only inside a `weight` object, while code requires a weight object (`createLabelRequest.packages[0].weight?.unit` reads without guard; absent -> `"NaN"`). Spec lists no per-commodity `weight` but invoice reads it.

UNVERIFIED:
- Non-`application/json` request content type behaviour.
- Cloud Run frontend behaviour for an invalid `Authorization: Bearer` on the public service.
- Embedded newline handling in invoice text.
- Real Exelot's expected weight unit (sent unitless; mock accepts any positive number).
- Behaviour of real production Exelot error bodies: all upstream error bodies here are the mock's invention (`index.ts:51-53,108,125-126`), except as noted by the source.
- Maximum Cloud Run instance count (not set in `iac/projects/mock-exelot/cloud-run.tf`; module default unknown).

### Notes for the E2 draft

Cross-check of `E2 - mock proxies page (draft).md` lines 30, 61, 68, 153-157, 179, 181:

- Line 30 (exelot row): host and ADO/commit details match README:3-10. "Creates an Exelot parcel with a commercial invoice and returns its label": correct (but only PDF/PNG label ever comes back; the page does not say that ZPL cannot be returned).
- Line 61 (`exelot-key-bravo` "PNG labels"): correct, but add that a **PDF** request with bravo is a 500 and a PNG request passes straight through with no converter.
- Line 68 (exelot 403/403/403): correct for no key, unknown key, `apiky-500`. Missing nuance: `exelot-key-bad-login` is also 403 but with the partner id in `details`.
- Line 153 (`ERR 400/401/500/503` -> 599 carrier error): correct; add (a) matching ignores all spaces and case, (b) it only fires if the request already passes the mock Exelot's own required fields (`countryCode`, positive weight, etc.), else 599 with a different Exelot 400 body, (c) `details` carries Exelot's body.
- Line 154 (`PNG FAIL` + `labelFormat: PNG` -> 500 after four converter calls): correct, but only for a PDF-label partner (alpha); with `labelFormat: PDF` it returns a normal 201.
- Line 155 (`exelot-key-bad-login` -> 403): correct.
- Line 156 (`exelot-key-zpl`, `exelot-key-unconfigured` -> 500): correct status. Different bodies: zpl -> "An internal server error occurred" (parcel created first), unconfigured -> "An unexpected error occurred".
- Line 157 (`exelot-key-bravo` with a PDF request -> 500): correct.
- Line 179 ("OCS and Exelot multiply a GRAM weight by 1000"): correct for Exelot, but precisely: every unit other than the exact string `KILOGRAM` is multiplied; spec only allows `GRAM`/`KILOGRAM`; missing weight becomes `"NaN"`.
- Line 181 ("OCS and Exelot return 599 for every carrier rejection"): correct for Exelot's create-parcel non-2xx. But not every Exelot-side failure is 599: label-format mismatches, converter failure and an unreachable Exelot (network) are 500, and an Exelot **login** failure is 403.
- Missing from the page for Exelot: no cancel/validate/reprint; 201 (not 200) on success; unknown paths (including `/healthz`) return **400**, not 404; `GET /` returns 200 `ok`; the "always calls real ApiKy" statement refers to production source only, the mock never calls real ApiKy.


---

## veho (Veho; apps/veho-proxy; NO production host: built contract-first from the agreed OpenAPI, `gfs-hybrid-services/carrier-proxies` apps/veho-proxy main a996061, plus Veho v2.2 public API)

All paths relative to repo root `carrier-playground`, line numbers from `origin/main`. Express + openapi-backend 5.21.2 + ajv-formats, against `apps/veho-proxy/api/openapi.yaml` (`apps/veho-proxy/src/app.ts:6,73-79`). Port 4112 locally. README:3-18: "There is no production Veho proxy to copy"; where the real proxy later differs, the real one wins.

### Operations and routes

Exactly six business routes, all in the spec; plus two health routes that are NOT in the spec.

| operation | METHOD path | supported? | notes |
| --- | --- | --- | --- |
| validate | none | NO | no validate / service-lookup route. `POST /shipping/quote` is the closest (rate, not validation). The proxy does **not** pre-check ZIP serviceability (README:301-303) |
| create-ship (order + label per parcel) | POST `/shipping/createLabel` (`createLabel`) | YES | 200. Veho calls: `GET /v2/orders?externalId=`, `POST /v2/orders`, `GET /v2/labels/{packageId}.{pdf\|png\|zpl}` per parcel (`src/handlers.ts:139-188`). `api/openapi.yaml:35-169` |
| reprint | GET `/shipping/packages/{packageId}/label?labelFormat=` (`reprintLabel`) | YES | 200 `{packageId, documents:{label}}`. `labelFormat` query is required (spec `:183-188`). `handlers.ts:190-198`, `openapi.yaml:171-232` |
| delete / cancel | POST `/shipping/{shipmentId}/cancel` (`cancelShipment`) | YES, whole order only | Veho `PUT /v2/orders/{_id}/events/cancelled`. No per-parcel cancel: `POST /shipping/packages/{id}/cancel` is 404 (`test/operations.test.ts:167-170`). `handlers.ts:200-209` |
| other: update delivery instructions | PUT `/shipping/{shipmentId}/deliveryInstructions` (`updateDeliveryInstructions`) | YES | Veho `PATCH /v2/orders/{_id}` with `{instructions}` only; echoes what was sent. `handlers.ts:211-224` |
| other: quote | POST `/shipping/quote` (`getQuote`) | YES | Veho `POST /v2/quote/rate`. `handlers.ts:226-262` |
| commit / manifest | POST `/shipping/manifest` (`createManifest`) | YES | Veho `POST /v2/manifests`, chunks of 100. `handlers.ts:264-312` |
| track | none | NO | tracking, webhooks, POD photos and reconciliation are "not caller-facing operations, so not built" (README:304-305). Only a `trackingUrl` string is returned from create |
| health | GET `/healthz` -> 200 `{"status":"ok","uptime":"<n>s"}`; GET `/health/liveness` -> 200 `{"ok":true}` | YES, not in spec | `src/app.ts:62-71`. `GET /` and `GET /health` are **404** (`NotFoundException`, they fall through to openapi `notFound`, `app.ts:89-91`) |

Pipeline order (`src/app.ts:46-110`): correlation, `/health/liveness`, request log, `express.json()`, `express.urlencoded`, `/healthz`, then openapi-backend: route match, `x-api-key` security handler, schema validation, handler. So an unknown route is 404 **without** needing a key; a bad key is 401 before any schema error (`test/routes.test.ts:68-71`).

Unknown path/method body: 404 `{"type":"NotFoundException","title":"Resource Not Found","status":404,"detail":"The route or resource could not be found","instance":"<method lower-case> <path>"}` (`src/exceptions.ts:79-96`).

### Auth and headers

- Header `x-api-key` (spec `securitySchemes.api_key`, `api/openapi.yaml:479-484`). Missing/array header -> immediate `AuthenticationException` (`app.ts:96-98`). Otherwise ApiKy `GET {APIKY_BASE_URL}/api/profile?token=<key>` (`app.ts:100-105`); any ApiKy error (403, 500, unreachable) -> same 401. `APIKY_ENABLED` anything but `true` accepts any non-empty key without ApiKy (`config.ts:53`, `app.ts:99`; not set in cloud-run.tf besides `"true"`, `iac/projects/mock-veho/cloud-run.tf:32`).
- Fixture key names (`apps/mock-upstreams/fixtures/apiky/veho.json`): `veho-key-alpha` (Alpha Test Freight Inc: `carrierNotifications: true`, `hazmatApproved: true`, `tenderFacilityId: MOCKFACILITY000000001`), `veho-key-bravo` (Bravo Mock Goods Inc: empty `profile {}`, so notifications off, hazmat refused, no facility), `apiky-500` (ApiKy 500). Service key and Veho upstream apikey values: fixture values elided.
- No key / unknown key / `apiky-500`: all **401** `application/problem+json` `{"type":"AuthenticationException","title":"There was an error authenticating your request","detail":"Principal unknown could not be authenticated. No additional detail was provided.","status":401}` (`src/exceptions.ts:33-46`).
- Per-account settings come **only** from the ApiKy profile's `profile.veho` block (`src/mapping.ts:30-37`): `carrierNotifications` (default false), `hazmatApproved` (default false), `tenderFacilityId` (default none). All accounts share a single upstream Veho key `VEHO_API_KEY` sent as the `apikey` header (`src/veho-client.ts:37`, README:174). There is no per-account Veho credential.
- Other headers: nothing required besides `Content-Type: application/json` for JSON bodies (`express.json`, `app.ts:67`). UNVERIFIED: behaviour for a non-JSON content type on a body route.
- `Authorization: Bearer ...`: `src/` never reads an Authorization header (`git grep -i authorization -- apps/veho-proxy/src` is empty), so the app ignores it. UNVERIFIED: Cloud Run frontend behaviour for an invalid bearer on the public (`allUsers`) service.

### Request

Veho uses GFS units; the proxy converts to pounds / inches / USD cents (`openapi.yaml:10`, `src/mapping.ts:11-21`).

**createLabel** (`CreateLabelRequest`, `openapi.yaml:775-807`). Required: `shippingReference`, `serviceCode`, `labelSpecification`, `shipFrom`, `shipTo`, `packages` (min 1, **no maxItems** in the spec; mock Veho caps at 50, `mock-upstreams/src/veho/index.ts:61,269-272`).

| field | rule | notes |
| --- | --- | --- |
| `shippingReference` | string min 1 | sent as Veho `externalId`; **the idempotency key** |
| `serviceCode` | string min 1; code-checked against `VEHO_SERVICE_MAP` | only `VEHO_GROUND_PLUS` -> `groundPlus` and `VEHO_PREMIUM_ECONOMY` -> `premiumEconomy` (`config.ts:61-63`); anything else (incl. inherited names like `constructor`) -> 400 `{field:"serviceCode",problem:"enum"}` (`handlers.ts:79-84`, `test/create-label.test.ts:136-161`) |
| `labelSpecification.labelFormat` | enum `PDF`,`PNG`,`ZPL203DPI`,`ZPL300DPI` | `ZPL300DPI` passes the schema but code refuses: 400 `{field:"labelSpecification.labelFormat",problem:"notSupported"}` (`handlers.ts:86-90`, `mapping.ts:21`). PDF/PNG/ZPL203DPI map to Veho `pdf`/`png`/`zpl` |
| `dispatchDate` | `format: date` (ajv-formats; `2026-02-31` is rejected as `format`, `test/routes.test.ts:124-127`) | optional; default **today in UTC** (`mapping.ts:40,79`); copied to **every package** as both `dispatchDate` and `shipDate`. Spec says "Today or later" but the proxy does not check; mock Veho tolerates yesterday (24h grace, `mock-upstreams/src/veho/index.ts:125,181`) and older gives 400 `dispatchDate`/`invalid_date` (twice: once for `dispatchDate`, once for `shipDate`) (`test/create-label.test.ts:431-437`) |
| `shipFrom` (`Address`) | required: `name`,`addressLine1`,`city`,`stateOrRegion`,`postalCode`,`countryCode` (2 chars, **not** restricted to US) | sent as `fromAddress` {`addressLine1`,`addressLine2`,`city`,`state`,`zipCode`,`country`}; `shipFrom.companyName` -> `fromName` (only if present); `shipFrom.name`, `phoneNumber`, `email` are **never sent**. Sender `stateOrRegion` is not upper-cased. Mock Veho validates `fromAddress.zipCode` against `^\d{5}(-?\d{4})?$` (`index.ts:58,226-227`) so a non-US sender postcode gives 400 `shipFrom.postalCode`/`invalid_string` |
| `shipTo` (`DeliveryAddress`) | required: `name`,`addressLine1`,`city`,`stateOrRegion`,`postalCode`,`countryCode`. `stateOrRegion` `^[A-Za-z]{2}$`; `postalCode` `^\d{5}(-?\d{4})?$` (ZIP or ZIP+4, hyphen optional); `countryCode` enum `["US"]` (`openapi.yaml:698-739`) | US-only. Sent as `recipient`,`company`,`destination{street,apartment,city,state(UPPERCASE),zipCode,country:"US"}` (`mapping.ts:84-95`). `phoneNumber`/`email` are sent **only if the account has `carrierNotifications: true`** (alpha yes, bravo no); then mock Veho validates phone 10-15 digits and an email shape, else 400 `shipTo.phoneNumber`/`shipTo.email` `invalid_string` (`index.ts:246-253`) |
| `deliveryInstructions` | string | sent as `instructions` unchanged; > 1000 chars -> 400 `deliveryInstructions`/`invalid_type` (mock limit `MAX_INSTRUCTIONS`, `index.ts:65`) |
| `serviceOptions.deliveryPin` | boolean default false | true -> `attendedDelivery.verificationType "pinVerification"` on each package |
| `serviceOptions.limitedQuantityDangerousGoods` | boolean default false | true on a non-hazmat account -> 400 `{field:"serviceOptions.limitedQuantityDangerousGoods",problem:"notSupported"}` (`handlers.ts:149-151`); on a hazmat account -> `specialHandling.hazmat.limitedQuantity: true` |
| `packages[].packageClientReferenceId` | required string min 1; **must be unique** within the request | duplicates -> 400 `{field:"packages",problem:"uniqueItems"}` (code check, `handlers.ts:147-148`; the spec allows them). Sent as package `externalId`; used to match Veho packages back to parcels |
| `packages[].weight` | required `{unit enum GRAM,KILOGRAM,OUNCE,POUND; value number >= 0}` | converted to lb with proper divisors (`mapping.ts:11`; **contrast exelot**: grams divide correctly). Sent unrounded. Zero is rejected (see limits) |
| `packages[].dimensions` | optional on create (required on quote) `{length,width,height >= 0, unit enum CENTIMETER,INCH}` | -> inches, unrounded |
| `packages[].value` | optional `{currency enum USD, value >= 0}` | -> `declaredValue` in integer USD cents `Math.round(v*100)` (`mapping.ts:19`). Non-USD rejected by schema |
| `packages[].description` | optional | default `"Parcel"`, trimmed-blank -> default, cut to 50 chars (`mapping.ts:114-117`) |

**Local limits (checked before any Veho call, all parcels reported together)** (`mapping.ts:6-70`): weight must be > 0 (`exclusiveMinimum`) and `round(lb) <= 50` (`maximum`); each side > 0 and `round(inches) <= 48`; volume of the **rounded** sides `<= 9849.6` cu in (`packages.N.dimensions.volume`, only reported if no side already too big). 50.4 lb passes, 50.5 lb fails (`test/create-label.test.ts:190-201`). Errors: 400 BadRequestException `errors: [{field:"packages.0.weight",problem:"maximum"}, ...]`.

**ZIP rules (all verified in mock Veho `mock-upstreams/src/veho/index.ts`)**: only the **first five digits** are used (`zip5`, `:122`). Serviceable ZIPs are exactly `00001`-`00010` (fixture `apps/mock-upstreams/fixtures/veho/veho.json`) plus the 11 magic ZIPs (`index.ts:300-301`). **Every realistic ZIP (e.g. 10001, 90210) is "unserviceable" in the mock**: 422 `unserviceable_zip_code` at `destination.zipCode` -> caller 400 `{field:"shipTo.postalCode",problem:"unserviceable_zip_code"}`. A malformed ZIP (e.g. `0001`) is caught earlier by the schema: 400 `{problem:"pattern"}` with no field (`test/routes.test.ts:102-108`). The sender ZIP is only pattern-checked, never serviceability-checked.

**getQuote** (`QuoteRequest`, `openapi.yaml:891-917`): required `shipFrom`,`shipTo` (each `{postalCode (ZIP pattern), countryCode: "US"}` only) and `packages` (1..10, each requires `weight` **and `dimensions`**); optional `serviceCode`, `dispatchDate`. Same limits/service-code check as create; sends `originationZip`,`deliveryZip`,`serviceClass` (only when a code was given),`shipDate` (only if `dispatchDate`) and converted sizes (`handlers.ts:226-243`). Delivery ZIP follows the same serviceability list; sender ZIP is not checked. Missing `dimensions` -> 400 `{field:"dimensions",problem:"required"}` (`test/operations.test.ts:287-290`).

**createManifest** (`ManifestRequest`, `openapi.yaml:948-968`): required `dispatchDate` (date), `packageIds` (min 1, no max; strings min 1); optional `loadReference` (-> Veho `loadId`), `transitType` enum `TRUCK`,`PLANE` default `TRUCK` (sent lower-cased). Sends `dispatchDate` and `shipDate` both = `dispatchDate`, account `tenderFacilityId` (only if set), in chunks of 100 in order (`handlers.ts:294-306`).

**updateDeliveryInstructions**: body `{deliveryInstructions: string minLength 1}` (`openapi.yaml:863-869`); empty -> 400 `{problem:"minLength"}`.

**cancel / reprint**: no body. Reprint `packageId` path param min 1 and `labelFormat` query required.

Validation errors (schema): 400 `BadRequestException`, `errors: [{field?, problem}]` where `problem` = Ajv keyword and `field` = `params.missingProperty ?? params.type` (`src/exceptions.ts:59-70`): `field` is present **only** for `required` errors (and then it is the **leaf property name only, no parent path**) and, oddly, for `type` errors (where `field` is the expected type name, e.g. `"string"`). `enum`, `pattern`, `minItems`, `format`, `minLength`, `maxItems` give `{problem}` only.

### Response

- createLabel **200**: `{shipmentId, consignmentNumber, packages:[{packageClientReferenceId, packageId, trackingId, trackingUrl, documents:{label:{labelFormat, labelStream}}}], warnings:[]}` (`handlers.ts:176-187`). `shipmentId` = Veho order `_id`; `consignmentNumber` = first parcel's `trackingId`; one entry in `packages` per parcel **in request order**, matched by `packageClientReferenceId`; **one label per parcel, in the requested format**, no combined blob. `labelFormat` echoes the **requested** value (e.g. `ZPL203DPI`), `labelStream` is **raw base64 of the label bytes** (no data-URI) (`handlers.ts:71`). `trackingUrl` = `VEHO_TRACKING_URL_BASE` + trackingId; default and dev value `https://track.veho.mock.invalid/#/trackingid/` (fake host, `config.ts:60`, `cloud-run.tf:37`). `warnings` is always `[]`. Mock ids: order `MOCK`+13 chars, package `PKGMOCK`+10, tracking `VHMOCK`+8 digits (README:230-233). Mock labels: PDF 4x6 "MOCK LABEL - NOT FOR CARRIAGE" with service/destination/weight/description, PNG mock image, ZPL text starting `^XA` (`mock-upstreams/src/veho/index.ts:538-561`).
- reprint **200**: `{packageId, documents:{label:{labelFormat, labelStream}}}`.
- cancel **200**: `{shipmentId, status:"CANCELLED"}`.
- update instructions **200**: `{shipmentId, deliveryInstructions}` (echo of what was sent, not Veho's response).
- quote **200**: `{serviceCode?, packages:[{packageClientReferenceId?, quoteId?, rate:{currency:"USD", value}, transitTimeDays, billableWeight?:{unit:"POUND", value}, zone, assumedInjectionPostalCode?}]}`; items matched to parcels **by position** (`handlers.ts:245-261`). Mock quote values are made up: transit 3 days (5 for `premiumEconomy`), zone `1 + (last two ZIP digits mod 8)`, rate from billable weight (`index.ts:610-631`). Quotes are indicative only.
- manifest **200**: `{packageIdsAccepted:[...], packageIdsNotFound:[...]}`. Unknown ids are listed in `packageIdsNotFound` with a 200 (not an error). A background retry of the not-found ids runs 60 s later (`VEHO_MANIFEST_RETRY_DELAY_MS`, in-process, `timer.unref()`), only logs, nothing caller-visible (`handlers.ts:278-292,307-310`). Veho 4xx/5xx on any chunk fails the whole request; earlier chunks stay manifested.

### Error shape

All errors are RFC 7807 `Content-Type: application/problem+json` (`src/exceptions.ts:25-30`), shape `{type, title, status, detail, instance?, errors?}`. **Different from exelot's `{code,message,details,metaData}`.**

| status | `type` / `title` | `detail` | when |
| --- | --- | --- | --- |
| 400 | `BadRequestException` / "There was an error validating your request" | "One or more validation errors occurred." + `errors:[{field?,problem}]` | schema failure; proxy checks (service code, `ZPL300DPI`, limits, uniqueItems, hazmat); or Veho 400/422 **with** `errors[]` (code -> `problem`, path -> mapped GFS `field`, else Veho path joined with `.`; Veho `message` is never returned or logged) (`src/veho-client.ts:90-109`, `src/mapping.ts:130-226`) |
| 400 | `CarrierException` / "An error has occured with the upstream carrier" (typo `occured` kept) | "Server error received from veho", no `errors` | Veho answered any other 4xx: 400 without `errors[]`, 401, 403, 404, 429, 3xx, "already cancelled", "already received". Nothing from Veho is passed on |
| 401 | `AuthenticationException` | "Principal unknown could not be authenticated..." | see Auth |
| 404 | `NotFoundException` / "Resource Not Found" | "The route or resource could not be found", `instance:"<method> <path>"` | unknown route/method |
| 599 | `CarrierException` | "Server error received from veho" | Veho 5xx, Veho timeout (`VEHO_TIMEOUT_MS` 3000 ms per call) or network failure, label still 404 at the end of the 12 s budget on **create**, duplicate live orders for one `shippingReference`, or the post-unknown-outcome lookup failing with anything but 404 |
| 500 | none (not the Problem shape): `{"code":"INTERNAL SERVER ERROR","message":"An unexpected error occurred","details":"An unexpected error occurred on the server, no additional detail is available"}` **but sent as `application/problem+json`** (`exceptions.ts:146-152`) | | anything unexpected: malformed JSON (`test/routes.test.ts:134-148`), and "Veho order is missing a package" when an idempotently-returned existing order has no package matching a parcel's `packageClientReferenceId` (`handlers.ts:159-162`) |

`InternalServerException` (`exceptions.ts:117-130`, Problem-shaped 500) is defined but **never thrown** anywhere in `src/` (`git grep InternalServerException` finds only its definition), although the spec's 500 response (`openapi.yaml:518-528`) documents that shape. Malformed JSON is 500, not 400.

CarrierException status rule (`exceptions.ts:98-104`): upstream status `< 500` -> 400; `>= 500` or no answer (`undefined`) -> 599.

### Failure scenarios for D5 (magic values)

Mock Veho is `apps/mock-upstreams/src/veho/index.ts`; magic ZIPs `MAGIC_ZIP` `:17-29` (first 5 digits, `00xxx`); magic ids `MAGIC_ID` `:32-39`, case-insensitive (`magic()` upper-cases, `:139-141`). Checks run in the mock after its own body validation. Prod-style timings: proxy per-call timeout 3 s, mock "slow" = 4 s (`SLOW_MS`, `:42`), so a slow answer is always a proxy timeout. All "caller sees" are after proxy mapping.

| operation | field | magic value | where verified | caller sees |
| --- | --- | --- | --- | --- |
| createLabel | `shipTo.postalCode` (first 5) | any ZIP not `00001`-`00010` and not a magic ZIP, e.g. `99999`, `10001` | `index.ts:300-301,381-386` | 400 BadRequest `[{field:"shipTo.postalCode",problem:"unserviceable_zip_code"}]` |
| createLabel | `shipTo.postalCode` | `00422` | `:367-380` | 400 BadRequest `[{field:"shipTo.addressLine1",problem:"invalid_address_field"},{field:"externalClient",problem:"invalid_external_client"}]` (second path unmapped so Veho path used); Veho messages echo the street but are never returned/logged |
| createLabel | `shipTo.postalCode` | `00401` / `00403` | `:146-153` | 400 CarrierException; lookup happened, no second lookup |
| createLabel | `shipTo.postalCode` | `00429` | `:154-157` | 400 CarrierException; GET then POST only, no retry (`test/create-label.test.ts:449-452`) |
| createLabel | `shipTo.postalCode` | `00500` / `00503` | `:158-165` | 599: calls are lookup (none) -> create (5xx) -> lookup (none) -> create (5xx) -> 599 (`test/create-label.test.ts:480-490`). Nothing created |
| createLabel | `shipTo.postalCode` | `00502` | `:433-436` | **200**: mock creates the order then answers 500; proxy looks it up and returns it |
| createLabel | `shipTo.postalCode` | `00408` | `:437` | **200** after ~3 s: create times out (3 s vs 4 s), lookup finds the order |
| createLabel | `shipTo.postalCode` | `00404` | `:393-394` (labels 404 for 1.5 s, `LABEL_LATE_MS`) | **200** after label retries at 250/750/1750 ms (~1.75 s) |
| createLabel | `shipTo.postalCode` | `00410` | `:391-392` (label never ready) | **599** after ~10.8 s (cumulative waits 250+500+1000+2000+3000+4000 = 10.75 s; the next 4 s wait would pass the 12 s budget, `handlers.ts:56-77`). Order **exists** and is not cancelled |
| createLabel -> cancel | `shipTo.postalCode` | `00409` | `:428`, `:506-509` | create 200; later cancel -> 400 CarrierException ("already received") |
| createLabel | `shippingReference` (lookup) | `MOCKERR404` | `:142-145`, `:450` | lookup finds nothing, order is created: 200 (`test/create-label.test.ts:537-540`) |
| createLabel | `shippingReference` | `MOCKERR401` / `MOCKERR429` | `:146,154` | 400 CarrierException, nothing created (`test/create-label.test.ts:548-552`) |
| createLabel | `shippingReference` | `MOCKERR500` / `MOCKERR503` | `:158-165` | 599, nothing created (the lookup fails before any create) |
| createLabel | `shippingReference` | `MOCKERRSLOW` | `:166-170` | 599 after ~3 s (lookup times out), nothing created |
| createLabel | `labelSpecification.labelFormat` | `ZPL300DPI` | `handlers.ts:86-90` | 400 BadRequest `notSupported`, no Veho call |
| createLabel | `serviceCode` | anything but the two mapped codes | `handlers.ts:79-84` | 400 BadRequest `enum` on `serviceCode`, no Veho call |
| createLabel | `packages[].weight`/`dimensions` | over 50 lb / 48 in / 9849.6 cu in / zero | `mapping.ts:48-70` | 400 BadRequest per field, no Veho call |
| createLabel | `serviceOptions.limitedQuantityDangerousGoods` | true with `veho-key-bravo` | `handlers.ts:149-151` | 400 BadRequest `notSupported`, no Veho call |
| createLabel | `x-api-key` | missing/unknown/`apiky-500` | `app.ts:96-105` | 401 `AuthenticationException` |
| reprintLabel | `packageId` | `MOCKERR404` or any id the mock does not know | `index.ts:142-145`, `:532-536` | **400 CarrierException after ~10.8 s** of 404 retries (`handlers.ts:195-196`) |
| reprintLabel | `packageId` | `MOCKERR401` / `MOCKERR429` | `:146,154` | 400 CarrierException immediately (non-404 label error maps at once, `handlers.ts:72`) |
| reprintLabel | `packageId` | `MOCKERR500` / `MOCKERR503` | | 599 |
| reprintLabel | `packageId` | `MOCKERRSLOW` | | 599 after ~3 s |
| reprintLabel | `labelFormat` | `ZPL300DPI` | `handlers.ts:193` | 400 BadRequest `[{field:"labelFormat",problem:"notSupported"}]` |
| cancelShipment | `shipmentId` | `MOCKERR404`, unknown id | `:142-145,461-465` | 400 CarrierException |
| cancelShipment | `shipmentId` | `MOCKERR401` / `MOCKERR429` | | 400 CarrierException |
| cancelShipment | `shipmentId` | `MOCKERR500` / `MOCKERR503` | | 599 |
| cancelShipment | `shipmentId` | `MOCKERRSLOW` | | 599 after ~3 s |
| cancelShipment | order state | already cancelled, or from a `00409` create | `:502-509` | 400 CarrierException (**cancel twice is NOT idempotent**) |
| updateDeliveryInstructions | `shipmentId` | same `MOCKERR*` ids | `magic()` via `orderRoute` `:456-467` | 404/401/429 -> 400 CarrierException; 500/503/SLOW -> 599 |
| updateDeliveryInstructions | order state | order already cancelled | `:488-491` | 400 CarrierException (Veho answers `{message}` without `errors[]`) |
| updateDeliveryInstructions | `deliveryInstructions` | > 1000 chars | `:484-487` | 400 BadRequest `[{field:"deliveryInstructions",problem:"invalid_type"}]` (`test/operations.test.ts:203-207`) |
| getQuote | `shipTo.postalCode` | `00401`/`00403` | `:600`, `magic zip` | 400 CarrierException |
| getQuote | `shipTo.postalCode` | `00429` | | 400 CarrierException |
| getQuote | `shipTo.postalCode` | `00500` / `00503` | | 599 (`test/operations.test.ts:302-305`) |
| getQuote | `shipTo.postalCode` | `00408` | `:601-605` | 599 after ~3 s |
| getQuote | `shipTo.postalCode` | `00404`,`00409`,`00410`,`00422`,`00502` | `:300-301` (serviceable) | normal 200 quote (these have no quote-specific effect) |
| getQuote | `shipTo.postalCode` | any ZIP not `00001`-`00010`/magic | `:606-609` | 400 BadRequest `[{field:"shipTo.postalCode",problem:"unserviceable_zip_code"}]` |
| createManifest | `packageIds[]` | any id equal to a `MOCKERR*` value | `:672` | whole request fails: `MOCKERR404`/`401`/`429` -> 400 CarrierException; `MOCKERR500`/`503` -> 599; `MOCKERRSLOW` -> 599 after ~3 s. **Not** listed in `packageIdsNotFound` |
| createManifest | `packageIds[]` | unknown id (no magic) | `:675-679` | 200 with the id in `packageIdsNotFound`; logs a retry 60 s later |
| createManifest | `dispatchDate` | more than ~1 day in the past | `:667`, `datesErrors` `:174-186` | 400 BadRequest `[{field:"dispatchDate",problem:"invalid_date"}]` |
| any | Veho wrong upstream key | (config `VEHO_API_KEY` mismatch) | `:348-354`; `test/create-label.test.ts:464-469` | 400 CarrierException (a Veho 401 is a 400, not an auth error) |

E2's "MOCKERR* -> That Veho status" is therefore a translation: the caller never sees Veho's 401/404/429/503 itself, only 400 (any 4xx) or 599 (5xx/timeout).

### Quirks mirrored from production

There is no production to mirror: these are the contract's/framework's behaviours, kept on purpose (README:274-288).

- 599 for upstream 5xx/timeouts; any upstream 4xx (401, 403, 404, 429, "already received") collapses to **400 CarrierException with no detail** (`exceptions.ts:98-115`). No throttling or Retry-After handling (README:283-284).
- Veho validation errors are **400** not 422 (spec text says 422; contract and CID-336 agreed "400 now, 422 later", README:285-286).
- "Label not yet available" is a plain 599 with no order id or tracking id (framework `CarrierException` carries no detail); ids are only logged (README:279-281,130-132). Consequence for callers (derived): the 599 body gives **no `packageId`**, so the stated recovery "reprint later" (`openapi.yaml:530-533`) cannot be driven from the 599 alone. Re-posting createLabel with the same `shippingReference` is the working recovery, because the lookup returns the existing order and refetches labels.
- Schema errors mostly lack `field`; malformed JSON is generic 500 (README:287-288).
- Idempotency (D-20): every create is preceded by `GET /v2/orders?externalId=<shippingReference>`; one live (not `lastEvent: cancelled`) order is returned (labels refetched), two or more -> 599 + error log, none or 404 -> create (`handlers.ts:92-137`). After a create timeout/5xx the lookup is repeated and the create is retried **once** (attempt 2); a 4xx on create is never retried (`handlers.ts:122-136`). A lookup failure before any create is mapped normally (4xx -> 400, 5xx -> 599, `handlers.ts:101-105`); after an unknown outcome any non-404 lookup failure is 599.
- Limits are checked on **rounded** values, but converted values are sent unrounded (D-14) (`mapping.ts:47-65`, README:318-320).
- Descriptions default to "Parcel" and are cut to 50 chars (D-21); `fromName` is sent only when `shipFrom.companyName` is set; dates default to today UTC; one Veho order with one package per parcel and never `packageCount`; never sends `signatureRequired`, `dryIce`, `barCode`, `slaDeliveryDate`, `consumerExpectedServiceDate` or `includeQuote` (README:96-110).
- Typos kept: `occured` in the CarrierException title.

### Statefulness / ordering constraints

- **State lives in mock Veho (mock-upstreams), in memory, per instance, max 1000 orders** (oldest dropped first, and their packages with them) (`mock-upstreams/src/veho/index.ts:60,302-313`, README:230-231). The proxy itself is stateless. Consequences: on multiple mock-upstreams instances, or after a cold start / restart (dev has `min_instance_count = 0`, `iac/env/dev.tfvars:4`), lookups, reprints, cancels, updates and manifests can miss an order created earlier. A missed reprint/cancel/update is a 400 CarrierException (reprint only after ~10.8 s). UNVERIFIED: max Cloud Run instance count for `mock-upstreams` (not set in `iac/projects/mock-upstreams/cloud-run.tf`).
- Order of calls: create first; `shipmentId` (cancel, update) and `packageId` (reprint, manifest) come from the create response. Cancel then create with the **same** `shippingReference` creates a fresh order because cancelled orders are excluded from the idempotency lookup (`handlers.ts:107`, `test/create-label.test.ts:586-595`).
- Create idempotent per `shippingReference` **regardless of API key**: the mock's order lookup does not filter by account, so `veho-key-alpha` and `veho-key-bravo` using the same reference share an order (`index.ts:442-453`, derived). A reused reference with different parcel references (different `packageClientReferenceId`) makes the proxy throw "Veho order is missing a package" -> generic 500 (README:310-313).
- Cancel is once-only: a second cancel (and a cancel of a `00409` order) is 400. Update after cancel is 400. Label fetch/reprint after cancel still works (the mock label route does not check cancelled state, `index.ts:522-563`; derived). Manifest does not check state: cancelled or already-manifested packages are accepted again (derived from `index.ts:673-684`).
- Manifest not-found retry is an in-process timer; a restart loses it (README:329-330).
- Labels for a new order can 404 for a short time (mock `00404` simulates it; the proxy retries up to 12 s).
- Health: `/healthz` (framework check) and `/health/liveness` (Cloud Run); `GET /` and `GET /health` are 404 (not an outage).

### Adapter implications and leaks

- Supports create, reprint, cancel, manifest (commit), plus update-instructions and quote; **no validate, no track**. A generic interface needs: validate -> unsupported; delete -> `POST /shipping/{shipmentId}/cancel` keyed by the **order id** (not tracking number, not parcel id; whole order only); commit/manifest -> keyed by **packageIds** (not shipmentId); reprint keyed by **packageId** with an explicit `labelFormat`.
- The adapter must persist `shipmentId` and each `packageId` returned by create (the proxy is stateless and offers no lookup by tracking number or reference).
- Per-parcel structure: one call yields N parcels each with its own tracking id, label and `packageClientReferenceId`; `consignmentNumber` = first parcel tracking id. Parcel references **must be unique**. A 599 on create can mean the order exists (label timeout): recover by re-posting the same `shippingReference`, not by posting a fresh reference (duplicates).
- Error handling: errors are problem+json, not `{code,message}`; distinguish `type` (`BadRequestException` vs `CarrierException`). `field` is optional and for `required` is only a leaf name; use `problem` + `field` when present. 400 `CarrierException` carries no reason at all (cannot tell "already received" from a bad key or 404).
- Timeouts: the caller must tolerate ~11-12 s on create (label wait) and ~11 s on reprint of an unknown package; per-Veho-call proxy timeout is 3 s and one create retry can add another 3+ s. `00408` takes ~3 s.
- US-only: `shipTo.countryCode` must be `US`, state two letters, ZIP 5 or 5+4; currency USD only; weight <= 50 lb; sides <= 48 in; volume <= 9849.6 cu in (after rounding); dimensions mandatory for quote.
- Service codes are provisional (`VEHO_GROUND_PLUS`, `VEHO_PREMIUM_ECONOMY`) and configured server-side via `VEHO_SERVICE_MAP`; a real Selector2 service code table will need a mapping to these.
- Notifications and hazmat are per-account flags in the ApiKy profile, invisible to the caller: with alpha, bad phone/email values fail the create; with bravo they are silently dropped. Hazmat requested on bravo is a 400.
- Label formats supported: PDF, PNG, `ZPL203DPI`; `ZPL300DPI` is advertised in the schema but always refused.
- In this mock, only ZIPs `00001`-`00010` (and magic ZIPs) deliver; any real ZIP is unserviceable (so real-looking test data fails).
- No tracking-number-based operations; `trackingUrl` points at a fake `.invalid` host.

### README-vs-source discrepancies, and UNVERIFIED

**OpenAPI (`apps/veho-proxy/api/openapi.yaml`) vs code - precise routes:**

- Spec paths: exactly `/shipping/createLabel` (POST, `:35`), `/shipping/packages/{packageId}/label` (GET, `:171-174`), `/shipping/{shipmentId}/cancel` (POST, `:234-237`), `/shipping/{shipmentId}/deliveryInstructions` (PUT, `:280-283`), `/shipping/quote` (POST, `:336-339`), `/shipping/manifest` (POST, `:417-420`). Code `createHandlers` returns exactly the six matching operationIds (`src/handlers.ts:314`). Verified equal.
- In code but not in spec: `GET /healthz` (`app.ts:69-71`) and `GET /health/liveness` (`app.ts:63-65`).
- Spec has no `404` response; code answers unknown paths with a 404 `NotFoundException` (`app.ts:89-91`).
- Spec 500 = `InternalServerException` Problem body with detail "The Veho request could not be built" (`openapi.yaml:518-528`); code's 500 is `{code,message,details}` (sent as problem+json) and `InternalServerException` is never thrown (`exceptions.ts:117-130,146-152`).
- Spec allows zero weight/dimensions (`minimum: 0`, `openapi.yaml:628,637-645`); code rejects zero with `exclusiveMinimum` (`mapping.ts:51,59`).
- Spec describes the proxy checking the ZIP against Veho's serviceable list (`openapi.yaml:700-702`, VEHO-SVC-001); code does **not** pre-check (README:301-303); the unserviceable error comes from Veho's 422.
- Spec "dispatchDate: Today or later" (`:792`); no local check, only mock Veho's 24 h grace.
- Spec does not mention the `uniqueItems` check on `packageClientReferenceId` (code-only, `handlers.ts:147-148`; README:89-91 admits the schema allows it), nor the hazmat `notSupported` problem (mentioned only in a `description`, `:768-773`).
- Spec createLabel has no `maxItems` on `packages`; mock Veho caps at 50 (400 `packages`/`too_big`). Spec quote caps at 10 (`:907`) so >10 fails in schema with no field.
- Spec `Dimensions.unit`/`Weight.unit` enums match `UNITS_PER_IN`/`UNITS_PER_LB` (`mapping.ts:11-12`). Spec `Money.currency` enum USD; code's quote response defaults currency to `USD` if Veho omits it (`handlers.ts:252`).
- Spec errors describe `errors[].field` as optional "for enum, pattern, minItems, format" (`:568-571`); actually `field` is also set for `type` errors (as the type name) and `required` gives the leaf name only (`exceptions.ts:65-69`). Spec's `missingDimensions` example `field: dimensions` matches.
- Spec `servers.url` is the mock public host (`:29-30`), not a production host.

**README vs source:**
- README:32-33 health routes match `app.ts:62-71`.
- README:50 "404 `NotFoundException` ... method lower-case" matches (`exceptions.ts:93`).
- README:198 says `00500` -> "lookup (none), create, lookup (none), one retry (500 again): 599": code has two creates and two lookups (matches `test/create-label.test.ts:480-490`); not a discrepancy but "one retry" means the second create.
- README:209 says an unknown id on reprint "after its retries" is 400: confirmed, ~10.8 s. README does not state this duration.
- README:203 says `00410` is a 599 "within 12 s"; the actual figure with default config is about 10.8 s.
- README:230-231 "at most 1,000 orders" confirmed (`index.ts:60`).
- README:213 mentions Veho's 100 ids a manifest; proxy chunks so callers are not limited.

UNVERIFIED:
- Real Veho behaviour: every upstream behaviour (labels timing, rate maths, serviceable ZIP list, error codes) comes from the mock plus the public v2.2 spec (README:16); no real Veho traffic checked. README:337-349 lists known source disagreements (422 vs 400, label 404 window, fromAddress required, serviceable-zips shape, rounding).
- Ajv `allErrors` setting of openapi-backend (whether multiple schema errors are all reported or only the first); tests only show single-error cases.
- Non-JSON content type; Authorization bearer handling at the Cloud Run frontend.
- Max instance count of `mock-upstreams` (state sharing).
- `tests`: log-safety and mapping tests (`test/log-safety.test.ts`, `test/mapping.test.ts`) were not read.

### Notes for the E2 draft

Cross-check of `E2 - mock proxies page (draft).md` lines 31, 43, 62, 70, 158-165, 181:

- Line 31 (veho row): "No production proxy exists. Built from the agreed contract (`gfs-hybrid-services/carrier-proxies`, `apps/veho-proxy`, `main` `a996061`)": matches README:3-6. "Creates labels, reprints, cancels, updates delivery instructions, quotes, manifests": matches the six routes. Not stated: no validate, no track.
- Line 43: "`veho` and `amazon-sfp` also serve `/healthz`. `veho` returns 404 on `/` and `/health`": confirmed by code (`app.ts:62-71`; no `/` or `/health` route, falls to `notFound` 404).
- Line 62 / 70: `veho-key-alpha`, `veho-key-bravo` (no Veho account settings): correct; `401 / 401 / 401`: correct (`app.ts:96-105`, `exceptions.ts:33-46`).
- Line 158 (`99999` or any ZIP but `00001`-`00010` and the values below -> 400 `unserviceable_zip_code` on `shipTo.postalCode`): correct. Add: only the first 5 digits matter; ZIP+4 works.
- Line 159 (`00422` -> 400 on `shipTo.addressLine1` and `externalClient`): correct. The `externalClient` field is Veho's raw path because it has no GFS mapping.
- Line 160 (`00401`, `00403`, `00429` -> 400 `CarrierException`): correct.
- Line 161 (`00500`, `00503` -> 599 after a lookup and one retry): correct in outcome, but the sequence is lookup, create, lookup, create (two lookups, two creates).
- Line 162 (`00502`, `00408`, `00404` -> 200): correct. `00408` takes about 3 s (proxy times out at 3 s then finds the order).
- Line 163 (`00410` -> 599 within 12 s; the order exists): correct; real figure is about 10.8 s.
- Line 164 (`00409` create works; cancel gives 400 `CarrierException`): correct.
- Line 165 (`MOCKERR*` ids -> "That Veho status; `MOCKERRSLOW` is a 500 after 4 s"): **misleading**. The caller never sees Veho's 401/404/429/503. Any 4xx becomes 400 `CarrierException`; 500/503/timeout becomes 599. `MOCKERRSLOW` (a 500 after 4 s in the mock) is a proxy timeout at 3 s so the caller sees 599 after about 3 s. `MOCKERR404` as a `shippingReference` is not an error (the create proceeds). As a `packageId` on reprint it is a 400 after about 10.8 s. On a manifest id it fails the whole request (400), not `packageIdsNotFound`. The ids apply to `shippingReference` (lookup), order id (cancel, update), package id (reprint, manifest); "Order, package or manifest id" covers those but not "reference".
- Line 181 (status code conventions): the page lists OCS/Exelot 599, BJS/InPost 500, Coll8 500; veho also uses 599 (5xx/timeout/label never ready) and 400 for every upstream 4xx. Worth one extra bullet: veho errors are `application/problem+json`, unlike the others.
- Missing from the page: veho state is per mock-upstreams instance (max 1000 orders), so cancel/reprint/manifest after idle or on another instance fails; reprint of an unknown package takes about 10.8 s to 400; every real-looking ZIP is unserviceable; `serviceCode` must be `VEHO_GROUND_PLUS` or `VEHO_PREMIUM_ECONOMY`; US-only; label formats `PDF`/`PNG`/`ZPL203DPI` (`ZPL300DPI` refused).



---

# 4. Implications for the egress port

## 4.1 The minimal common interface that covers all twelve

Only one operation exists everywhere, so the port is a small required core plus optional capabilities. Sketch (TypeScript; names are suggestions, shapes are the part that matters):

```ts
interface CarrierEgress {
  readonly key: CarrierKey                       // 'royalmail' | 'ups' | ... | 'veho'
  readonly caps: {
    validate: boolean; cancel: boolean; commit: boolean; reprint: boolean; track: boolean
    labelFormats: LabelFormat[]                  // what the proxy accepts (section 2 matrix)
    maxParcelsPerCall: number                    // 1 for royalmail, fedex, sfp, amazon, ocs, exelot, inpost
  }
  create(req: ShipRequest, ctx: CallCtx): Promise<EgressResult<Created>>
  validate?(req: ShipRequest, ctx: CallCtx): Promise<EgressResult<Warnings>>
  cancel?(ref: CarrierRef, ctx: CallCtx): Promise<EgressResult<void>>
  commit?(refs: CarrierRef[], on: Date, ctx: CallCtx): Promise<EgressResult<Manifest[]>>
}
type Created = {
  carrierRef: Record<string, string>             // opaque, persisted: see 4.2 item 2
  parcels: { trackingId: string; label: { format: LabelFormat; base64: string }; clientRef?: string }[]
  documents: { kind: 'customs' | 'invoice'; mime: 'application/pdf'; base64: string }[]
  warnings: string[]
}
type EgressResult<T> =
  | { ok: true; value: T; trace: CallTrace }
  | { ok: false; kind: 'auth' | 'invalid' | 'rejected' | 'unavailable' | 'unsupported'; carrierStatus?: number
      carrierCode?: string; detail?: string; mayHaveCreated: boolean; trace: CallTrace }
```

- `ctx` carries the proxy base URL (from the `service_uris` output), the tenant's per-carrier `x-api-key`, the ID token, a correlation id, and a timeout. Nothing else: the proxies take no credentials in the body (1.1).
- **Capabilities are data, not exceptions.** `validate`, `cancel`, `commit` are absent (not "throws") for the carriers in the section 2 table. B9's use-cases ask `caps` first. `commit` on 9 of 12 carriers is therefore local only (mark committed in Postgres, call nothing), which agrees with B9's "commit marks a shipment committed and goes no further".
- `mayHaveCreated` matters: royalmail, exelot and veho can 500 or 599 **after** a carrier-side shipment exists (see the exelot, royalmail and veho sections). A retry layer must not blindly re-post create.
- `kind: 'rejected'` is the carrier-said-no class and must be derived per carrier from the status/code/shape rules in 1.6, not from the HTTP status (599 on ocs/exelot, 500 on bjs/inpost/amazon, 400 on veho, 200-with-error on ups XML).
- `trace` is B5's recorded call: carrier key, operation, proxy URL path, status, duration, retry count, and identifiers (shipmentId/trackingId); never bodies, labels, addresses or keys (programme invariant, vault Migration State).

## 4.2 Places where one interface leaks (ranked by how much code each costs)

1. **Shipment lifecycle handles differ per carrier and are not derivable from tracking numbers.** Cancel/commit need a carrier-specific handle that create returns and the adapter must persist: royalmail `shipmentId` (cancel via status change and manifest), fedex `shipmentId` **plus the FedEx account number**, coll8 `consignmentNo` (not the package `trackingId`), bjs carrier reference (not the barcode), amazon/sfp `shipmentId` (cancel) vs `trackingId` plus the ApiKy **company name** in the URL (tracking), veho order `shipmentId` for cancel but **`packageId`s** for manifest and reprint. Hence `carrierRef: Record<string,string>` and a column for it in B1's shipment/parcel tables. (Sections: royalmail, fedex, coll8, bjs, amazon, veho.)
2. **"Create" is not one call or one result shape.** ups XML is a two-call ShipConfirm to ShipAccept flow with a server-issued digest and errors inside an HTTP 200 body; the success and label shapes differ (several families in 1.7: PascalCase on inpost, a bare base64 string per package on coll8/dpdeu, `trackingId` nested or not); bjs returns 2 labels per package for `1EXC`/`2EXC`; veho/coll8/dpdeu return N labels for N parcels paired **by position**; royalmail/fedex/ocs/exelot/sfp/amazon/inpost accept exactly one package per call, so multi-parcel shipments become several calls on those carriers (and a partial-failure problem).
3. **Error classification cannot use HTTP status.** See 1.6 and the error table in section 2: the same status means different things (500 is carrier-rejected on bjs/inpost/amazon, an internal fault on others; 403 is auth on most, a carrier error on fedex (`fedex-key-rejected-account`) and a DPD NL entitlement failure; 401 is auth on ups/coll8/dpdeu/sfp/veho but a carrier error on royalmail), and some failures are 200 (ups XML, amazon `notes`, amazon catch-all). Each adapter needs its own classifier and a fixture-backed test per scenario in D5's grid.
4. **Account/entitlement is the API key, but the request still carries carrier-specific selectors**: dpdeu `serviceProvider` (`DPD DE` vs `DPD NL`), sfp `channelType` (`EXTERNAL` vs `AMAZON`) with a matching `serviceType`, bjs `accountId` prefix `S`/`E`, fedex cancel `accountNumber`, royalmail `shippingLocationId`, inpost home vs locker by `serviceCode` plus `lockerAddress`, exelot label format that must equal the partner's provisioning, veho per-account hazmat/notifications flags that change validation. The port's `ShipRequest` stays canonical; each adapter owns the mapping, and B1's "carrier account" row needs a per-carrier `options` JSON beside the key.
5. **Service codes are per-carrier vocabularies**: royalmail GFS codes (`RMT24`...) discoverable via `GET /shipping/getServiceCodes`; bjs 24 exact case-sensitive codes; veho `VEHO_GROUND_PLUS`/`VEHO_PREMIUM_ECONOMY`; ocs `ES1/EL1/EP1/EE1`; exelot `XLT/XLT_P`; inpost `STD/EXP/HSTD/HEXP`; fedex per-customer lists; amazon `SWA-UK-*` (+`-SIG` that the Logistics proxy cannot honour). A tenant-scoped service table (B1) maps Selector service to (carrier, proxy service code).
6. **Units and normalisation must be done before the call**, per the matrix in section 2: send KILOGRAM to ocs, exelot, royalmail, coll8, amazon, sfp; GRAM integers to dpdeu; never GRAM to ocs/exelot expecting a conversion; inch/cm per carrier. A wrong unit does not error, it silently changes the shipment (ocs/exelot x1000, royalmail grams as kg). B3 validation or the adapter must normalise, and the unit rule should be a per-adapter unit test.
7. **Label format is a negotiation, not a parameter**: bjs ignores it (PDF always), exelot requires the partner's provisioned format, amazon refuses PDF at create but accepts it under `?mode=validate`, ocs/exelot/royalmail drop pages or customs differently, ZPL is impossible on exelot/ocs/bjs, and the stored label's format must be remembered because ups V2 reprint does not echo it. Store the format actually returned (sniff the magic bytes: `%PDF-`, PNG signature, `^XA`), not the format requested.
8. **Timing and retry visibility**: veho create can take ~11-12 s and reprint of an unknown package ~10.8 s; ocs/exelot PNG converter failures cost >= 3 s; amazon 429 scenarios 1.4-1.7 s; coll8/ocs/exelot have 100 kB body limits, ups likely the same (derived, UNVERIFIED), fedex 1 MB; first call after idle includes a cold start. The client timeout must be per carrier, >= 15 s.
9. **Per-instance state**: veho cancel/reprint/manifest and royalmail manifest can miss shipments after idle or on another instance; the adapter cannot fix this, the D5 grid must run create plus follow-up quickly and treat a miss as an environment failure, not a carrier verdict.

## 4.3 B5-B8 specific decisions the sources force

- **B5 (royalmail first).** Royalmail needs the richest port surface of the first adapter: create (201, one package), `updateShipmentStatus` for cancel, `manifestShipments` for commit (201 array, base64 PDF `manifestImage`, per-location), customs documents as separate PDFs with soft-failure warnings, and `GET getServiceCodes` as a free auth probe. Its manifest response is per instance state in the mock (0 shipments if another instance served create). ID-token and `x-api-key` plumbing: see 1.1.
- **B6.** UPS: choose the transport deliberately. Selector (CSS/Client4) uses the XML stepping-stone; the README's own production traffic note says V2 shows no use (ups section, README lines cited there). XML needs `Content-Type: application/xml` (never `text/xml`, which turns the body into `{}`), HTTP 200 business errors, and an XML parser; V2 has no charges, forms or warnings and no manifest. Coll8: no label route, labels inline, cancel by consignment number with no body. FedEx: cancel needs the account number; every cancel failure is 500.
- **B7, Amazon Logistics and PDF.** Decision needed (I recommend: request ZPL or PNG at 203/300 DPI from the adapter and map Selector's PDF request to PNG; do not reproduce the 500 by default, but add it as a named D5 scenario via `labelFormat: PDF`). Basis: the refusal is the proxy's DPI check meeting mock Amazon's fixture of empty `supportedDPIs` for PDF (`apps/mock-upstreams/src/amazon/index.ts:80-84`, `apps/amazon-logistics-proxy/src/labelling.service.ts:270-284`); `?mode=validate` accepts PDF with 200 so validate cannot predict it. Real Amazon behaviour is inferred, not observed (amazon README line 209 says so). Same for `-SIG` (the Logistics proxy never sends the delivery-confirmation add-on; sfp does).
- **B7, DPD EU validator.** The validator is a faithful copy of production's `validator.js`. What it rejects (dpdeu section): a non-empty `shipFrom`/`shipTo` phone lacking a leading `+` or containing a space; international (non-same-country, non-both-EU) shipments without `customs.commodities` and per-package `invoiceNumber`; and the spec rejects `null`/`''` optionals and units outside `GRAM`/`KILOGRAM`/`CENTIMETER`. "Probably rejects every Selector call" is the mock README's own hypothesis (`apps/dpd-europe-proxy/README.md:129-142`, "Not confirmed"): it only holds if Selector sends national-format phones, nulls or `KG`/`CM`. I recommend the adapter **normalise to valid input** (E.164 without spaces or omit the field, omit empty optionals, GRAM integers, always `dimensions` and `serviceOptions: {}`) and expose the rejection paths as D5 scenarios, rather than reproducing a failure by default. If the intent is to reproduce production's likely failure, make it a tenant-level "strict legacy" option, not the default.
- **B8.** OCS and Exelot: send KILOGRAM; their x1000 on GRAM is a mirrored defect (ocs/exelot sections). Exelot: no cancel, no ZPL, one package, and a create that can leave an orphan parcel on a 500, so the adapter must not auto-retry. Veho: no production proxy, so the contract can change; state is per instance; every real-looking ZIP is unserviceable in the mock (only `00001`-`00010`); errors are problem+json; label formats PDF/PNG/ZPL203DPI.

## 4.4 D5 (mock scenarios) implications

- One preset per carrier = the carrier's happy-path request (from `apps/<proxy>/test/helpers.ts` / `harness.ts`, which `scripts/smoke.mts:11-24` imports) plus a set of scenario overrides: `shipTo.postalCode` magic values for create, id-prefix for cancel/track/manifest, fixture key names for account faults. The per-carrier "Failure scenarios for D5" tables are verified against `mock-upstreams` and give exact status and body gist.
- Scenarios that need chaining (cancel `UNKNOWN`, manifest ids) work on **synthesised ids**, not real create output; scenarios needing a created shipment (veho `00409`, cancel-twice) need create first.
- Skip or mark as not-triggerable: coll8 label-prefix scenarios (no label route), ups V2 `NOAUTH` (shipper number is env-fixed), ups V2 get-by-id `TE5 500`, amazon-sfp cancel failures (always 200), fedex/amazon behaviours that depend on a prior mock validation passing.
- Run the grid with per-carrier timeouts (veho up to ~12 s), sequentially for veho, and expect cold-start latency on the first call per carrier.
- Never include postal codes or ZIPs that look like real addresses; the mocks use fake `TE1 1ST`-style values (`AGENTS.md:18`).

---

# 5. Discrepancies: where the source disagrees with the E2 draft or the handover

E2 line numbers refer to `~/Documents/obsidian/Bifrost/Selector2/E2 - mock proxies page (draft).md` (vault, read-only). Each item is traced to a carrier section above.

1. **E2 L85, "Postcode and ZIP values ignore spaces and case. An id prefix also ignores case."** False for **royalmail**: every magic value is an exact, case- and space-sensitive match (`apps/mock-upstreams/src/royalmail/index.ts:70,136,140,144,368,419`; `royalmail-store.ts:73-76`). True for ups, coll8, fedex, dpdeu, bjs, inpost, ocs, exelot, amazon, amazon-sfp (postcodes); veho uses the first 5 ZIP digits; sfp's `BT` check is case-sensitive.
2. **E2 L183, "Malformed JSON gives a 500, not a 400, on several mocks."** Split: 500 on royalmail, coll8, ups V2, bjs, inpost, ocs, exelot, veho, amazon-sfp; **400** on fedex, dpdeu (`SYNTAX_ERROR`), amazon (Logistics).
3. **E2 L179, GRAM quirks.** OCS/Exelot: the multiplier applies to **every unit that is not exactly `KILOGRAM`** (`apps/ocs-proxy/src/services/ocs-service.ts:109`, `apps/exelot-proxy/src/services/exelot-service.ts:68`), and a missing weight becomes `"NaN"` on exelot. Royalmail: the unit is **never read** at all, not only for GRAM. Coll8 does no conversion either. DPD EU, not mentioned, multiplies KILOGRAM x100 unrounded.
4. **E2 L181, "OCS and Exelot return 599 for every carrier rejection."** True for rejections; not for OCS unreachable or success without numbers (500), exelot label-format mismatch, converter failure or unreachable (500), or exelot login failure (403).
5. **E2 L29 and handover, "prod image `prod-57357`".** Appears nowhere in the repo (`git grep` empty). Cannot be stated as fact.
6. **E2 L180, Amazon Logistics.** (a) The PDF refusal is create-only (`?mode=validate` returns 200 for PDF and for `-SIG`); it is the proxy's DPI check against **mock Amazon's** fixture, so it demonstrates the source's behaviour given an assumed upstream, not observed production behaviour. (b) "inferred from the SFP proxy's code" is accurate for `-SIG`: the refusal lives in mock Amazon, and the Logistics proxy never sends the add-on; the SFP proxy explicitly supports `-SIG`. (c) Any request with `notes` returns 200 `{}` even in validate mode; any unrouted `/shipping/...` path returns 200 OK.
7. **E2 L182 and handover, DPD EU validator.** Narrower than stated (phone only when present and non-empty; `''`/`null` fail earlier at the spec with a different code `VALIDATION_ERROR`, not `VALIDATION`), and it omits the international customs/invoice requirement. The handover's "probably rejects every Selector call" is the README's unconfirmed hypothesis, conditional on what Selector sends (`apps/dpd-europe-proxy/README.md:129-142`).
8. **E2 L165, veho `MOCKERR404/401/429/500/503/SLOW`, "That Veho status".** Misleading: the caller sees only 400 `CarrierException` (any upstream 4xx) or 599 (5xx/timeout). `MOCKERRSLOW` is a 599 after about 3 s (proxy timeout), not a 500 after 4 s. `MOCKERR404` as a `shippingReference` is not an error. Unknown package on reprint takes about 10.8 s before the 400.
9. **E2 L108-109, coll8.** Label-prefix scenarios cannot be triggered (no label route); `coll8-test-key-no-account` gives `ACCOUNT_CODE_NOT_CONFIGURED` on create and eodManifest only, not cancel; `coll8-test-key-unknown-account` (500) is omitted; cancel `UNKNOWN` is 404, not 500.
10. **E2 L133, Amazon cancel.** Logistics: cancel of `UNKNOWN` is **400** "The shipment could not be found."; `ERR500` 500; `ERR429`/`RETRY429` do nothing on cancel. amazon-sfp: cancel **never fails visibly** (every failure becomes 200 `{}`). The row conflates tracking-id and shipment-id prefixes.
11. **E2 L93-94, royalmail.** `RMT48SOLD` gives 500 only for `rm-key-acme` (bramble gets 400 no-mapping). `NODOC CN23` has no effect for a PDF label; `NODOC ALL` with a PDF still returns the CN23. `SHIPMENT-500` fails only `updateShipmentStatus` (swallowed inside manifest). `ERR 401` is a carrier 401 with `code:"CARRIER SERVER ERROR"`; auth failure is 403 only.
12. **E2 L58, bjs.** The real convention is an `S`/`E` prefix on `accountId` (`SMOCKBJS01`/`EMOCKBJS01`, stripped before use); an unprefixed `MOCKBJS01` works but sends `ExpressRequired=null`. `bjs` returns one label per BJS product (two per package for `1EXC`/`2EXC`), and `labelFormat` is ignored (always PDF).
13. **E2 L68 and L147, inpost.** `inpost-key-malformed-profile` gives 500, not 403. `NO PARCEL` fires only on `createReturnLabel`. inpost returns PascalCase and has no cancel/reprint.
14. **E2 L97, ups.** `WA1 1RN` warning only on the XML route (V2 drops it). `NOAUTH`, `TE5 500` on get-by-id and some others cannot be triggered via V2. CSS label recovery sends `text/xml`, so it always gets UPS error 10001 (HTTP 200). V2 has no manifest, no tracking, no forms.
15. **E2 L43, health.** Amazon Logistics answers `/health/liveness` through its catch-all (different body); exelot returns 400 on `/healthz`.
16. **E2 L25, amazon-sfp.** Also has a validate mode, serves two channels (`EXTERNAL` Amazon Shipping and `AMAZON` SFP), refuses `BT` postcodes (case-sensitive prefix), and is single-package. 401 bodies are problem+json.
17. **E2 L126, dpdeu `dpdeu-key-revoked-token`.** The retry happens once per proxy instance per provider (in-memory token cache), not per key; the "no key = 401" row only holds when the body already passes spec validation.
18. **E2 L154, exelot `PNG FAIL`.** Fires only for a PDF-provisioned partner with `labelFormat: PNG` (alpha); a PDF request returns a normal 201.
19. **E2 L21-22, L30 (descriptions).** coll8 has no separate label route (labels inline); exelot can only ever return PDF/PNG; royalmail has no validate, cancel route or reprint; nine of the twelve have no validate. These absences matter for B9.
20. **Handover, "Exelot always calls the real ApiKy".** True of the production source only. The mock reads `APIKY_BASE_URL` and calls mock-upstreams' fake ApiKy; no real host is hard-coded (exelot section, README lines cited there). The handover says `origin/main` is `d98fd9b`; it is `ae57c96` (the E2 draft already reflects this).
21. **Statements in the E2 draft that held:** the bad-key status table (L64-70) at status level; key names (L49-62); the veho health-route note (L43); the dpdeu failure rows (L119-125); the amazon tracking-stage rule (L134).

---

# 6. Open questions and what could not be verified

Open questions (decisions, not facts):
1. **UPS transport for selector2**: XML stepping-stone (proven by the README's own prod-traffic note, 22 Oct-5 Nov 2026) or V2 JSON (simpler, but no charges, forms, warnings, manifest)? Recommendation: XML for contract fidelity to CSS, V2 only if Selector2's callers never need charges or international forms.
2. **Where do tenant carrier keys live?** Each tenant needs one `x-api-key` per carrier (the key chooses the carrier customer profile). B1's "carrier account" row must hold an encrypted, retrievable key (not a hash) and a per-carrier `options` JSON; B2's hashed API keys are for Selector2's own callers, a different thing.
3. **Multi-parcel splitting on one-package carriers** (royalmail, fedex, sfp, amazon, ocs, exelot, inpost): split into N calls and aggregate, or reject at B3 validation? A partial failure leaves orphan carrier shipments (no cancel on exelot/ocs/inpost).
4. **Validate semantics**: only sfp, amazon, ups V2 can validate remotely, and amazon's validate under-reports. `ValidateShipments` should be local (B3) plus an optional remote check; confirm that is the intent.
5. **Retry policy on `mayHaveCreated` failures** (royalmail, exelot, veho, bjs/inpost converter failures): no auto-retry, or retry-by-lookup where available (veho re-post of the same `shippingReference` is idempotent; royalmail/exelot are not).
6. **DPD EU and Amazon PDF handling**: see 4.3 (recommended: normalise and map PDF to PNG by default; expose the failures as scenarios).
7. **Service-code translation ownership** for the 12 vocabularies (4.2 item 5), including whether Selector2 discovers royalmail codes at runtime via `getServiceCodes`.

Could not verify (no live calls, no prod access, no running services):
- Cloud Run frontend behaviour with an ID token on an `allUsers` service, and whether the public LB hostname is a valid ID-token audience (1.1).
- Real carrier behaviour for any "mirrored" quirk: every one is read from source, not production traffic unless a README says so (ups README's traffic counts are the one exception and are the README's own claim).
- Actual max-instance count of `mock-upstreams` (affects veho and royalmail state loss); cold-start duration of the proxies (E2 says ~5 s, taken from the handover's note on mock-upstreams).
- `is-european` package behaviour on lowercase/alpha-3 codes (dpdeu section), non-JSON content-type behaviour on several openapi-backend carriers (ocs, exelot, veho sections), ups unknown-path behaviour, royalmail/amazon real response fields that the mocks never emit (manifest `weightUnitOfMeasure: Grams`).
- Production sources themselves (ADO and GitHub repos named in the READMEs and the commit hashes in the E2 draft); not accessed. Veho has no production proxy at all.
- Whether `origin/main` has moved since `ae57c96`: `git fetch` was not run (read-only rule); the snapshot is the local clone's `origin/main`.
