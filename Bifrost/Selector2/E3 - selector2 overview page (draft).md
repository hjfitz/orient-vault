---
title: "Selector2 — E3 Confluence draft: selector2 overview, similarities and differences"
programme: selector2
status: draft
unit: E3
tags: [bifrost, merak, draft]
updated: "2026-11-12"
---
<!-- Draft for the MPK Confluence subsection. Not published: waits on G3 (parent page). Sibling of the E2 draft (mock carrier proxies); the link to it below becomes a Confluence page link at publish. Everything below the "Author review" divider is for Harry, not the page. -->
# selector2: overview, similarities and differences to Legacy Selector

**selector2 is a multi-tenant TypeScript service that books carrier labels through the same five operations as Legacy Selector's CSS. It keeps CSS's SOAP contract and selector-rest-proxy's REST contract, adds a terser REST v2, and books through the twelve mock carrier proxies. It runs in ilg-merak dev only, holds synthetic data only and has no customers. Engineers use it to test callers such as Parcel Portal and selector-adapter, and people drive it through its web UI.**

Nothing in production moves to it, and there is no prod environment. Where it differs from Legacy Selector, this page says how and why. Four differences are assumptions that are not yet confirmed. They are marked **Assumption**.

## What it does

selector2 serves three APIs over one set of use-cases, and a web UI over the same data.

| Surface | Path | Credentials | Contract |
| --- | --- | --- | --- |
| SOAP | `POST /ClientShipService.asmx` | Body element `AuthenticationDetails`. `UserID` is the account username and `UserPassword` is an API key | CSS's `ClientShipService`. Eight operations. HTTP 200 with the status in the body |
| REST v1 | `POST /ProcessShipments`, `POST /ValidateShipments`, `DELETE /DeleteShipments`, `POST /CommitShipGroup`, `POST /CommitShipments` | `x-api-key` | selector-rest-proxy's routes, field names and error bodies. 200, 207 or 400 by its status rule |
| REST v2 | `POST /v2/shipments`, `/v2/shipments/validate`, `/v2/shipments/delete`, `/v2/shipments/commit`, `GET /v2/services` | `x-api-key` | Terse: flat bodies, one `results` array in request order, stable error codes |
| Admin and UI | `/admin/...` | HTTP basic: account username and password | Accounts, API keys, the UI's shipment routes, CSV export |

The five label operations:

| Operation | What it does |
| --- | --- |
| ProcessShipments | Validates each shipment, books it with its carrier and returns the labels |
| ValidateShipments | Runs the same checks and books nothing |
| DeleteShipments | Cancels booked shipments, named by carrier and consignment number |
| CommitShipGroup | Commits the named consignments |
| CommitShipments | Commits every booked shipment of the named carriers, or of every carrier |

SOAP serves three more operations because Parcel Portal and selector-adapter call them: `ProcessShipment` and `ValidateShipment` (one shipment each) and `DailyShipQuery`. REST v2 merges the two commit operations into one `commit` call.

**The mock proxies.** selector2 gets every label from carrier-playground's twelve mock carrier proxies: `royalmail`, `ups`, `coll8`, `fedex`, `dpdeu`, `amazon-sfp`, `amazon`, `bjs`, `inpost`, `ocs`, `exelot` and `veho`. Each copies a production proxy's contract and holds only fake data. Veho has no production proxy. For the proxies themselves, see *Mock carrier proxies (carrier-playground)*.

**The UI.** `selector2-ui` sits behind HTTP basic auth. Contracts, services, number ranges and the mock proxies' URLs have no UI page and are read-only.

| Page | Does |
| --- | --- |
| `/` | Shows the signed-in account and its tenant. A `god` account picks a tenant |
| `/accounts`, `/accounts/[id]` | A `god` account lists and creates accounts. An account lists, creates and revokes its API keys. A key is shown once |
| `/playground` | Composes one v2 shipment, then validates, processes, commits or deletes it. Shows each item's status, rule codes and messages, the carrier call trace and the labels |
| `/shipments`, `/shipments/{id}` | Lists a tenant's shipments, filtered by status, carrier, reference prefix and despatch date. The detail page shows parcels, the call trace and a label preview |
| `/export` | Downloads shipments as CSV, one row per parcel, up to 50,000 rows |
| `/scenarios` (in build) | Presets per carrier with the mocks' failure values, and a run-all across the twelve carriers with a result grid |

The label preview shows PNG and JPEG as images, PDF in a sandboxed frame, and ZPL and text as raw text. Any other format is a download.

**Where it runs on dev.** Both services are public at the Cloud Run layer and authenticate in the app. Snapshot 12 Nov 2026.

- API: `https://selector2-api-dev-qbs2p3wu5a-uc.a.run.app`
- UI: `https://selector2-ui-dev-qbs2p3wu5a-uc.a.run.app`

`GET /health/liveness` returns 200 on both with no sign-in. On the API, `GET /health/readiness` returns 200 once Postgres answers and 503 until then.

## How it is built

selector2 is one pnpm monorepo, `ilg-merak/selector2`.

- **`selector2-api`:** NestJS. The layers run `http` to `use-cases` to `core`, with `adapters` and `repositories` behind small interfaces. SOAP, REST v1, REST v2 and the admin shipment routes call the same use-cases, so their statuses cannot drift.
- **`selector2-ui`:** SvelteKit. It has no database access and no account store. It calls the API with the signed-in user's own credentials.
- **Database:** Postgres 17 on Cloud SQL, built from the platform's `database/cloud-sql-iam` module, with Drizzle and 12 tables. Logins are IAM only: there are no database passwords. Migrations run as a Cloud Run job inside the Terraform apply.
- **Cloud Run:** two services, `selector2-api-dev` and `selector2-ui-dev`, on the platform's `node24-runtime` image, with a minimum of 0 instances. Project `ilg-merak-dev-b5e3`, region `us-central1`.
- **IAM:** the API runs as a service account that can read and write tables and nothing else. A separate migrator service account changes the schema. It is also the only identity that can read the Secret Manager secret holding the `god` password.
- **Delivery:** Terragrunt for infrastructure and GitHub Actions for CI. A merge to `main` deploys to dev.

**Tenancy and authentication.** One account owns one tenant, and a tenant is a Selector site. **Assumption:** account = tenant. An account has a username, an argon2id password hash, a role (`god` or `standard`) and any number of API keys. A key is shown once and stored as a SHA-256 digest with a lookup prefix. Revoking it stops it on the next request on every instance. SOAP and REST callers present an API key. The UI and the admin routes take the account's username and password over HTTP basic. A `standard` account reaches only its own tenant. One `god` account exists, created by the migration job. The admin API cannot create another, and a `god` account names one tenant at a time on admin routes. Every row carries `tenant_id`, and no repository method is unscoped. Failed sign-ins are throttled: 10 per account and source, and 100 per source, in 15 minutes. A throttled caller gets 429 with `Retry-After`. Over SOAP it gets CSS's `0010`.

**Carrier egress.** One adapter per proxy sits behind a common port. `create` is required. `cancel`, `commit` and `validate` exist only where the proxy has them. Cancel works for seven carriers (Royal Mail, UPS, Coll8, FedEx, Amazon Logistics, BJS, Veho). Royal Mail, Coll8 and Veho take a manifest. selector2 reads each proxy's `run.app` address from carrier-playground's `mock-edge` output `service_uris`, and falls back to the public name `https://<carrier>.mocks.merak.freightops.dev`. Each request carries the contract's proxy key in `x-api-key`, a correlation id, and a Cloud Run ID token in `X-Serverless-Authorization`. The mocks are public and never read the token. An attempt times out after 20 s. The client makes at most 3 attempts and retries only when the carrier cannot have acted. It never resends a create after a timeout, a dropped connection, a 429 or a 5xx, because the carrier may have booked it. Each attempt writes one `carrier_call` row with identifiers and timings and never a body.

## Similarities with Legacy Selector

Legacy Selector's CSS is a SOAP service (ASP.NET ASMX) on each customer's hosted VM. It has 35 operations. A caller keeps its integration and changes the endpoint and the credentials. A SOAP caller changes the endpoint, the `UserID` (the account username) and the `UserPassword` (an API key). A REST v1 caller changes the base URL and `x-api-key`.

| What a caller sees | Legacy Selector (CSS) | selector2 |
| --- | --- | --- |
| SOAP endpoint | `ClientShipService.asmx`, SOAP 1.1, routed by `SOAPAction`, namespace `http://justshoutgfs.com/Client/Ship/v5/` | The same file name at the root, matched in any case. SOAP 1.2 is answered too. A client changes its whole URL |
| Credentials | Body element `AuthenticationDetails` with `VersionId`, `UserID` and `UserPassword`. No SOAP header | The same. `VersionId` 5.0.0 and 5.1.x are accepted |
| Business failures | HTTP 200 with a status in the body, bad credentials included | The same |
| Status codes | `0002` warning, `0003` error, `0030` invalid structure, `0010` authentication failed, `0020` version not recognised, `0040` database error | The same codes and wording. SOAP and REST v1 echo them |
| Delete refusals | `0400 Shipment not found`, `0400 Shipment Already Deleted`, `0401 Upload Shipment can't be deleted` | The same |
| Unknown action | An ASMX fault: `soap:Client`, HTTP 500 | The same |
| REST v1 | selector-rest-proxy: five routes, PascalCase field names, 200, 207 or 400 | The same routes, methods and field names. Error bodies have the proxy's shapes with its typos corrected. The default print spec is ZPLII, 203 dpi, `PAPER_4X6` |
| Service selection | Carrier name, contract number and service code, or a route code. Checks run in this order: carrier name, contract, route. A route overrides the rest | The same order, against the tenant's tables |
| Carrier names | `ROYAL MAIL`, `UPS`, `COLL8`, `FEDEX`, `DPD NL`, `DPD DE`, `AMAZON LOGISTICS UK`, `BJS`, `INPOST`, `OCS`, `EXELOT` | The same names. `VEHO` is selector2's own, because CSS has no Veho |
| Carrier path | The proxy carriers go through GFS proxies | The same, through the proxies. On dev these are the mocks |
| Numbers and units | Consignment and parcel numbers come from the proxy's reply. Weights in kg, dimensions in cm | The same |
| Commit | Marks a shipment committed. A committed shipment cannot be deleted | The same |
| Validation | CSS's rule codes and messages | The same wording for every rule selector2 reproduces (see Differences) |

## Differences

An **Assumption** is a decision the build made without a product owner's confirmation. The owner can reverse it.

| Area | Legacy Selector (CSS) | selector2 | Why |
| --- | --- | --- | --- |
| Hosting and deployment | One install per customer site. CSS runs under IIS on a hosted GCP Windows VM, on .NET Framework 4.8.1. Each release is a DLL copied by hand to the VMs that need it. No pipeline | One deployment: two Cloud Run services in ilg-merak dev, built with Terraform and GitHub Actions. A merge to `main` deploys | A multi-tenant, SaaS-style replacement, dev only |
| Data model and storage | One Firebird database per site (`GFS.FDB`), shared with Client4 | One multi-tenant Postgres 17 database with 12 tables, Drizzle, and labels stored as bytes. The mapping is below | Harry asked for a clean replacement, not a port: "more like a replacement than like-for-like" |
| Tenancy | A site is a database | A tenant is a site. Every row has `tenant_id`, child rows point at parents by `(id, tenant_id)`, and no query is unscoped. One account owns one tenant | One database serves many tenants. **Assumption:** account = tenant |
| Credentials and keys | API users are `gfs_users` (role 3) or `web_users`. Passwords are stored and compared in plain text. No lockout. Carrier keys sit in the site database | Argon2id password hashes. API keys stored as SHA-256 digests, shown once, revocable. SOAP `UserPassword` is an API key, never the account password. Failed sign-ins are throttled. A carrier key is a reference to a published mock key and is never stored | Callers are the tenant's own API users, stored hashed, with no ApiKy. Both services are public, so the app must authenticate |
| Validation scope | About 10,000 lines in `ValidateProcedures.cs`, about 367 checks, for every carrier Selector supports | The rule groups that the twelve carriers and five operations reach, with CSS's codes and wording. Left out: postcode format tables, PAF lookup, state tables, field-length limits, departments, route permission, credit checks. CSS bugs are fixed, and rules are added from the proxies' contracts | Most of CSS's validation serves carriers selector2 does not have. Every reproduced rule traces to CSS source or a proxy contract. `validation-scope.md` lists each |
| Numbering | `SHIP_RANGES`, `ITEM_RANGES` and stored procedures allocate numbers. For the twelve proxy carriers CSS takes the numbers from the proxy's reply | The same for the twelve: the carrier's numbers are stored. The `number_range` table exists and no code allocates from it | Nothing in the five operations needs ranges. **Assumption:** the numbering unit was dropped on that finding |
| A repeated reference | Books a second shipment. No duplicate guard | Returns the tenant's live shipment for that reference with its stored labels, and calls no carrier. REST v2 marks it `existing: true`. A failed or deleted shipment frees the reference. A committed one keeps it. A booking under 5 minutes old answers `in_progress` | Retries are safe. **Assumption:** this deliberate difference can be reversed |
| Shipment id | SOAP echoes the `ShipmentID` the caller sent | SOAP still echoes the caller's. REST v1 and v2 return selector2's own id, or 0 for a shipment never stored | REST v2 names a shipment by `id` for delete and commit. Reason for v1: `[??]` |
| Commit | Marks shipments. CSS also renders a PDF manifest for most carriers. A web commit clears the labels | Marks a shipment `committed` and goes no further. Royal Mail, Coll8 and Veho are sent a manifest request, and only carrier manifests are returned. Labels are kept. `CommitShipGroup` commits Royal Mail too, where CSS refused | selector2 has no upload and keeps no manifest of its own |
| Events | `UploadShipments` fires the Firebird event `SHIP_COMMITED`. Client4 on the upload station catches it and uploads to GFS | None. selector2 publishes no events and uploads nothing. Data leaves only through the UI's CSV export and the carrier calls | Self-contained build: no Firebird, no upload |
| Billing and credit checks | Validation includes credit checks, and credit can be restored. Billing is a separate Delphi app that reads shipments after upload | None | Out of scope by decision |
| Carriers in scope | Every carrier Selector supports, direct APIs and GFS proxies. About 130 carrier-option rules. 35 SOAP operations | The twelve proxy carriers. Eight SOAP operations. No template-drawn labels and no direct-API carriers | Decided 11 Nov 2026 |
| Printing | A request can print through a `LabelPrinter` | Never prints. Labels come back as bytes in the reply and `Printed` is false | selector2 returns labels and prints nothing |
| REST v2 | None. selector-rest-proxy is the only REST API | A terse API defined for selector2: resources, one shape per call, flat bodies, per-item results, stable codes (`docs/rest-v2.md`) | **Assumption:** "terse" was undefined, so the build agent (Claude) defined it. It can be changed |
| Request limits | CSS: 4 MiB, no tag, depth or item limit. selector-rest-proxy: 100 kB, no list cap | SOAP: 1 MiB, 75,000 tags, 32 levels, 1,000 items. REST: 1 MiB, at most 100 entries per list | SOAP bodies are parsed before the caller is authenticated, so the cap bounds what an anonymous request costs |
| Maintenance refusal | `0066 Database updating` while the site database updates | Never | There is no site database to update |
| Observability and logging | Logs stay on the host (file and HTTP sinks). Since Oct 2026 the last carrier request and reply are written to disk under `C:\temp`. There is no central telemetry: Datadog sees only the carrier proxies | JSON logs with Datadog service tags `selector2-api` and `selector2-ui`, and `x-request-id` on every line and response. No body, label, address, key or credential is ever logged. Each proxy attempt leaves a `carrier_call` row, shown as the call trace in the UI | Replies carry personal data and labels |
| Site features | Departments, a route-permission switch (`ALLOW_ROUTES`), consolidation, an address book, per-site proxy URLs | Left out. The proxy address is per carrier, from configuration. selector2 never consolidates | Each can be added later without changing the tables |
| Carriers with no cancel | `[??]` | DPD, Amazon SFP, InPost, OCS and Exelot have no usable cancel through their proxy. A delete removes the shipment in selector2 only and says so | The proxy has no cancel route, or swallows every cancel error |

### The data model, table by table

| CSS | selector2 | Note |
| --- | --- | --- |
| One database per site, `CUST_SITES` | `tenant` | A tenant is a site |
| `CUST_SITES` address, `SHIP_SHIPPER` | `sender_address` | One per tenant, not copied onto each shipment |
| `gfs_users` (role 3), `web_users` | `account`, `api_key` | Hashes instead of plain text |
| `CUST_CONTRACTS` | `carrier_account` | The same key: contract number and carrier. `CARR_KEY` becomes `credential_ref`. `CARR_PSW` is not stored |
| `CUST_CONTRACT_PRODUCTS`, `PRODUCTS` | `service` | `carrier_service_code` is what the proxy is sent. No department column |
| `CUST_CONTRACT_SERVICES` | Not kept | Only the old Royal Mail API used it |
| `CUST_ROUTES` | `route` | Points at one service, which gives carrier, contract and service |
| `SHIP_RANGES`, `ITEM_RANGES`, `NEXT_CONS_NO`, `NEXT_PARCEL_NO` | `number_range` | Unused, as above |
| `SHIPMENTS` | `shipment` | Status codes 1, 2, 3 and 101 become `booked`, `deleted` and `committed`. selector2 adds `booking` and `failed` |
| `SHIP_PIECES` | `parcel` | Parcel numbers are unique within a shipment, not across all shipments |
| `SHIP_LABELS` | `label` | Bytes. Formats use the Selector API's `DocumentType` names |
| `CHECK_CARRIER` | A fixed carrier-name list | A site cannot rename a carrier |
| CSS file logs, request and reply dumps | `carrier_call` | Identifiers and timings, never a body |

Other behaviours that differ:

- A deleted or failed shipment frees its consignment number. CSS's key covers every row.
- A ship group is not a table. `CommitShipGroup` names shipments by carrier and consignment number.
- Contract numbers are matched as sent. CSS reads the last three characters of a Royal Mail or InPost contract number as B2B or B2C.
- Customs and commodities are sent to the carrier and not kept.

Left out of the schema: departments, `ALLOW_ROUTES`, consolidation, the address book, print settings, credit, site locking and update state, range recycling, check digits, Royal Mail manifest storage, `TMP` numbers for failed shipments, Firebird events, upload and billing, per-site proxy URLs, and the global reference tables (`CARRIERS`, `COUNTRIES`, `PRODUCTS` as a catalogue).

## Not included

- **Firebird events, upload to GFS and billing.**
- **Credit checks.**
- **Real data.** Never import a real site, customer, key or label.
- **A prod environment and any cutover.**
- **Carriers beyond the twelve proxy carriers.** DHL is not included.
- **27 of CSS's 35 SOAP operations.** An unknown action gets ASMX's fault. Lookups, address book, goods import and export, manifest printing and the other operations are not served.
- **A WSDL.** `?wsdl` answers 404. A client that builds its proxy from the WSDL at run time cannot use SOAP.
- **Web-client behaviour.** Versions 5.1.1 and 5.1.3 are accepted and treated as 5.0.0.
- **Printing, departments, consolidation, the address book and route permission.**
- **Number-range allocation.**
- **Carrier credentials from Secret Manager.** A `secret:` reference is refused with `credential_unavailable`.
- **Postcode format tables, PAF lookup and state tables** in validation.

## Status and limits

**State on 12 Nov 2026** (`main` at `6442634`). Merged: the API (SOAP, REST v1, REST v2, admin routes, the twelve carrier adapters, validation, accounts and API keys) and the UI's sign-in and accounts pages. In review: the playground, shipment list and detail, label preview and CSV export. In build: the scenarios page.

**Dev only, synthetic data only.**

**No live end-to-end run with a real tenant on dev yet.**

- Nobody can sign in as `god`. Only the migrator service account can read the `god` password secret, and no person has been found who can.
- Tests run against a local Postgres. Parcel Portal's and selector-adapter's own Selector clients booked against a local selector2 on 12 Nov 2026 with only the endpoint and credentials changed. Nothing in CI runs against the deployed dev services.
- Dev tenants have no way to get carrier contracts. The API has no route to create carrier accounts, and the migration job creates only the `god` account. The synthetic seed provides contracts locally, and refuses to run against Cloud SQL.

**Other limits.**

- Four SOAP operations have no recorded real sample: `ProcessShipments`, `ValidateShipments`, `CommitShipGroup` and `CommitShipments`. Their reply tests prove selector2 matches CSS's source as read, not the real server.
- A create that may have reached the carrier (a timeout, a dropped connection, a 429 or a 5xx) keeps its reference as `booking`. A repeat is `in_progress` until 5 minutes pass, and then books again. A caller should check with the carrier before resending.
- A commit marks the shipment first and tells the carrier second. A crash between the two leaves a shipment committed in selector2 that Royal Mail, Coll8 or Veho never manifested. Nothing retries it.
- The UI remembers a good sign-in for 60 seconds, so a revoked account can still pass for up to a minute.

**Open risks.**

- **R1, org-contract departures:** SvelteKit replaces the contract's Next.js, and Drizzle replaces its no-ORM default. Both are recorded in `AGENTS.md`. The contract's owner has not yet been told.
- **R4, the IAM path is not enforced:** the mocks stay public, so the ID token selector2 sends is never required. Making them private would remove their public names.
- **R7, public endpoints with a login:** both services are on the internet with app-level auth, and the seeded `god` account can create accounts. Mitigations: a random password from Secret Manager, argon2id hashes, throttling per account and per source, and hashed keys. Dev only, synthetic data.
- **R8, no instance cap:** the platform's Cloud Run module cannot cap instances. A public service can scale out until the 25-connection `db-f1-micro` runs out. After that readiness returns 503 and the migrator cannot connect. The fix is a cap in the platform module.
- **R9, readiness is invisible to Cloud Run:** Cloud Run probes only liveness. A service that never reaches its database stays "ready" and returns 503 from readiness. A startup probe on readiness is the fix, and it needs checking against what the platform module allows.

## Where to find things

- **Code:** `ilg-merak/selector2`. The `docs/` folder holds `data-model`, `validation-scope`, `shipment-use-cases`, `rest-v1`, `rest-v2`, `soap`, `carrier-egress`, `auth`, `admin-api` and `ui`. `AGENTS.md` holds the invariants and the recorded departures.
- **Mock proxies:** `ilg-merak/carrier-playground`, and *Mock carrier proxies (carrier-playground)*.
- **Legacy Selector:** the *Legacy Selector* tree in the MPK space (page 351764483).
- **Programme record:** `Bifrost/Selector2/` in the Obsidian vault. `Migration State.md` holds the decision log, gates and risks. `Engineering/selector2/` holds the Waypoint explainers.
- **Owner after the programme:** `[??]`.

---

## Author review (not part of the page)

Gaps marked `[??]` in the page:

1. **Reason REST v1 returns selector2's `ShipmentID`.** `docs/rest-v1.md` says it does and that Selector echoed the caller's. No source says why. SOAP still echoes the caller's (`docs/soap.md`).
2. **What CSS does for carriers whose proxy has no usable cancel** (DPD, Amazon SFP, InPost, OCS, Exelot). The sources describe only selector2's behaviour (`docs/shipment-use-cases.md`, `docs/carrier-egress.md`).
3. **Owner after the programme.** `owner: bifrost` in `waypoint.yaml` is inferred from the vault folder, and `known-context.md` says no record names an owner.

Unsure of:

- **The audience sentence in the summary.** "Engineers use it to test callers such as Parcel Portal and selector-adapter, and people drive it through its web UI" is read from the C2 and D-unit done-when lines and the Migration State summary. No source names an audience.
- **The UI section is written as it will be after D2 and D4 land.** At drafting (`origin/main` `6442634`) only the sign-in and accounts pages are merged. The playground, list, label preview and export are in `docs/ui.md` on `origin/hjf/d2-playground` (`f73d8be`, unreviewed). The `/scenarios` row comes from the D5 line in Migration State and your brief. No code or doc for it exists yet, and `docs/ui.md` on the branch says it is "not in the navigation yet". Re-check the table before publishing.
- **The dev hostnames** come from `Engineering/selector2/operations.md` (snapshot 12 Nov 2026). The README gives only the project and service names.
- **The four **Assumption** labels** (account = tenant, a repeated reference, REST v2's shape, the dropped numbering unit). Say whether to keep them, soften them or drop them before publishing. The REST v2 row names Claude. Decide whether the page should.
- **Page length.** The Differences table has 19 rows plus the data-model table. Splitting the data-model table onto a child page would shorten the parent.
- **Figures that are snapshots or counts from other docs:** "about 367 checks" (`docs/soap.md`, C2 evidence), "about 130 carrier-option rules" (`docs/validation-scope.md`), "27 of 35 operations" (`docs/soap.md`).
- **Risks left off by your brief:** R2, R3, R5 and R6. R2 appears as the four-unrecorded-operations limit.

Source contradictions (the page follows the source named first):

1. **REST v1 size limits.** `docs/rest-v1.md`: a body is at most 1 MiB and each list at most 100 entries. `docs/rest-v2.md`, side-by-side table: "Size limits: none" for selector2 REST v1.
2. **DPD phone numbers.** `docs/carrier-egress.md` (DPD Europe): selector2 "does not pre-check or rewrite" them and passes on the proxy's refusal. `docs/validation-scope.md` (rules added from the proxy contracts): the validation chain refuses a phone number that does not start `+` or contains spaces, with a note to drop the rule "if the adapter rewrites them instead". The page states neither.
3. **Where SOAP credentials sit.** The page follows `docs/soap.md`, `docs/auth.md`, the Waypoint architecture note (G3) and C2 evidence finding 1: the body element `AuthenticationDetails`. Migration State's Scar tissue still says "CSS's `AuthConnDetails` header carries a password", and `Engineering/css/architecture.md` guardrail G5 says the same. The SUPERSEDED note in Migration State sits under R1 but describes R2.
4. **The numbering unit.** The Migration State table marks B4 dropped (❌) with no decision-log entry for the drop. The ship-mode entry says "B4 deferred". The B1 entry says "Harry decides whether B4 is dropped". `known-context.md` and the ledger say dropped. `docs/data-model.md` says the table "is kept because the numbering work was planned against it, and that plan should be checked against this finding". The page says no code allocates numbers and marks the drop an assumption.
5. **What a `god` account sees.** Migration State B2 and `docs/ui.md` say a `god` account "sees every tenant". `docs/admin-api.md` and the Waypoint architecture note say it names one tenant per admin request, never gets an every-tenant scope, and acts on its own (empty) tenant over REST and SOAP. The page follows the second.
6. **Done-when versus evidence.** Migration State marks C2 merged with done-when "books against selector2 dev". `docs/soap.md` records the client runs as local. Migration State C1 done-when is "selector-rest-proxy's own contract tests pass … with only the URL and key changed". `docs/rest-v1.md` records 20 of 28 passing unchanged, with the six failures asserting Selector sandbox data. The page reports the recorded evidence.
7. **`ShipmentID`.** `docs/rest-v1.md` says selector2's id is returned. `docs/soap.md` says SOAP echoes the request's own. Both are on the page as a difference between transports. It is not a contradiction, but a reader may expect one rule.
8. **Smaller items, not on the page.** `known-context.md` counts 25 units with B11 added mid-run, but the Migration State table has 24 rows and no B11 (it appears in the ledger and the Waypoint notes). The README's opening paragraph on `origin/main` still says the SOAP and REST APIs, adapters and UI "arrive in later units". The E2 draft's last section, "How selector2 will use them (planned)", is out of date now that the adapters and egress are built. Update it before both pages publish.

What a reader would expect that the sources do not say:

- Who owns and supports selector2, and any support commitment.
- How a person gets a tenant, an API key or carrier contracts on dev today. The `god` password is unreadable and there is no contract-creation route.
- Whether selector2 will ever get a prod environment or real customers. The record says "dev only, no cutover" and names no trigger to change that.
- Data retention for stored shipments and labels, and the cost of running it.
- Any measured latency, throughput or capacity beyond the 25-connection database limit.
- Whether the SOAP check with Parcel Portal and selector-adapter passes on dev. Only local runs are recorded.
- Whether the deployed dev services match `6442634`. `known-context.md` says the last deploy run was not read.
- Confirmation from you of REST v2's shape (`docs/rest-v2.md`) and of account = tenant.
