---
title: "Selector2 — E2 Confluence draft: mock carrier proxies"
programme: selector2
status: draft
unit: E2
tags: [bifrost, merak, draft]
updated: "2026-11-12"
---
<!-- Draft for the MPK Confluence subsection. Not published: waits on G3 (parent page). Everything below the "Author review" divider is for Harry, not the page. -->
# Mock carrier proxies (carrier-playground)

**Twelve mock carrier proxies run in ilg-merak dev at `https://<name>.mocks.merak.freightops.dev`. Each copies a production proxy's contract and logic, answers every carrier and ApiKy call itself, and holds only fake data. Use them to test label flows with no carrier account, ApiKy key or customer credentials.**

They are dev only. There is no prod environment, by design. The code is in `ilg-merak/carrier-playground`.

## The twelve mocks

| Name | Public URL | Mirrors (production host, source, version) | What it does |
| --- | --- | --- | --- |
| `royalmail` | `https://royalmail.mocks.merak.freightops.dev` | `royalmail.gfsdeliver.com`. ADO `gfs-royal-mail-proxy`, last changed 3 Nov 2026 | Creates Royal Mail labels and customs documents, manifests, changes shipment status, lists service codes |
| `ups` | `https://ups.mocks.merak.freightops.dev` | `ups.gfsdeliver.com`. ADO `GFS UPS Integration` | Passes Selector's UPS XML through (ShipConfirm, ShipAccept, Void, Locator, LabelRecovery) and serves the V2 JSON routes |
| `coll8` | `https://coll8.mocks.merak.freightops.dev` | `coll8.gfsdeliver.com`. ADO `GFS Coll8 Integration` | Creates and cancels Coll8 shipments, sends the end-of-day manifest. The label comes back in the create response, as there is no separate label route |
| `fedex` | `https://fedex.mocks.merak.freightops.dev` | `fedex.gfsdeliver.com`. GitHub `gfs-hybrid-services/fedex-proxy`, `main` `1d246f8` | Creates and cancels FedEx shipments and returns labels |
| `dpdeu` | `https://dpdeu.mocks.merak.freightops.dev` | `dpd-eu.gfsdeliver.com`. ADO `GFS DPD-Europe Integration`, `dpd-europe-proxy` | One route that creates DPD Germany or DPD Netherlands labels (SOAP upstream) |
| `amazon-sfp` | `https://amazon-sfp.mocks.merak.freightops.dev` | `new-amazon-prod.gfsdeliver.com`. GitHub `gfs-hybrid-services/amazon-proxy`, `master` `be40413` | Buys Amazon Shipping labels for Seller Fulfilled Prime orders (`AMAZON` channel) and other orders (`EXTERNAL` channel), one package per call, with a validate mode. Cancels and tracks. Refuses `BT` postcodes (the prefix check is case-sensitive) |
| `amazon` | `https://amazon.mocks.merak.freightops.dev` | `amazon.gfsdeliver.com` (Amazon Logistics). ADO `GFS Amazon Logistics Integration`, `gfs-amazon-logistics-proxy`, `master` `6f0d113` | Buys Amazon Shipping labels, cancels, and serves the tracking route that connectors-amazon polls |
| `bjs` | `https://bjs.mocks.merak.freightops.dev` | `bjs.gfsdeliver.com`. ADO `bjs-proxy` in "GFS Hybrid Services and Carrier Integrations", default branch `ed56a53` (not the GitHub copy) | Books BJS Home Delivery, returns one label per BJS product (two per package for service codes `1EXC` and `2EXC`), always as PDF whatever `labelFormat` asks for, and cancels |
| `inpost` | `https://inpost.mocks.merak.freightops.dev` | `inpost.gfsdeliver.com`. GitHub `gfs-hybrid-services/inpost-proxy`, `main` `64656dc` | Creates InPost shipments and returns, home or locker, with labels |
| `ocs` | `https://ocs.mocks.merak.freightops.dev` | `ocs.gfsdeliver.com`. ADO `ocs-proxy`, `main` `29eeaa6` | Books an OCS Worldwide parcel and returns its label |
| `exelot` | `https://exelot.mocks.merak.freightops.dev` | `exelot.gfsdeliver.com`. ADO `GFS Exelot Integration`, `main` `b21a47d` | Creates an Exelot parcel with a commercial invoice and returns its label |
| `veho` | `https://veho.mocks.merak.freightops.dev` | No production proxy exists. Built from the agreed contract (`gfs-hybrid-services/carrier-proxies`, `apps/veho-proxy`, `main` `a996061`) and the Veho spec | Creates labels, reprints, cancels, updates delivery instructions, quotes, manifests |

A private service, `mock-upstreams`, fakes everything the mocks call: ApiKy and every carrier API. Only the mocks can reach it.

## How to call one

**Public name.** Use `https://<name>.mocks.merak.freightops.dev` with the same paths, headers and bodies as the production proxy. Send a mock ApiKy key in `x-api-key`. Nothing else is needed.

**Direct `run.app` URI.** The `mock-edge` Terraform project (`iac/projects/mock-edge`) outputs `service_uris` and `service_account_emails`, keyed by proxy key: `royalmail`, `ups`, `coll8`, `fedex`, `dpdeu`, `amazonsfp`, `amazon`, `bjs`, `inpost`, `ocs`, `exelot`, `veho`. Note `amazonsfp` here and `amazon-sfp` in the public name. Read them with `terragrunt output service_uris` `[??]`. The Cloud Run service is `mock-<key>-cp-dev`.

Since 11 Nov 2026, `mock-edge` also takes an `invoker_members` input. It is a list of `serviceAccount:<email>` values that get `roles/run.invoker` on all twelve mocks. The mocks are still public (`allUsers`), so the grant is additive and nothing enforces it. A caller that expects IAM later can already send a Cloud Run ID token whose audience is the service URI.

**Health check.** All twelve answer `GET /health/liveness` with 200 on both the public name and the `run.app` URI. Use it on direct URLs. `amazon` answers it with a different body (`{"code":200,"message":"OK",...}`), because its catch-all answers every unrouted path with 200. Cloud Run's own frontend swallows `/healthz` on `run.app` URLs and returns an HTML 404. Through the public name, `veho` and `amazon-sfp` also serve `/healthz`. `veho` returns 404 on `/` and `/health`, and `exelot` returns 400 on `/healthz`. Do not read those as an outage.

**Cold starts.** Dev runs with no minimum instances. The first call after idle waits for a start, which may take about 5 s `[??]`.

**Keys.** The mock ApiKy knows fake keys only. They are listed in each proxy's README (`apps/<proxy>/README.md`) and in `apps/mock-upstreams/fixtures/apiky/`. Names follow `<carrier>-key-<persona>`, with small variations. `apiky-500` makes the mock ApiKy fail on any proxy. Do not use a real key.

| Mock | Key for the working path | Other mock accounts |
| --- | --- | --- |
| `royalmail` | `rm-key-acme` | `rm-key-bramble` |
| `ups` | `ups-key-testco` | `ups-key-mockbridge` |
| `coll8` | `coll8-test-key-alpha` | `coll8-test-key-bravo` |
| `fedex` | `fedex-key-alpha` (cancel with account `MOCKFX001`) | `fedex-key-bravo` |
| `dpdeu` | `dpdeu-key-alpha` | `dpdeu-key-bravo` (DPD Germany only) |
| `amazon-sfp` | `amazon-key-alpha` | `amazon-key-bravo` |
| `amazon` | `amzl-key-alpha` | `amzl-key-bravo` |
| `bjs` | `bjs-key-alpha` (send `accountId` `SMOCKBJS01` or `EMOCKBJS01`) | `bjs-key-bravo` (`SMOCKBJS02` or `EMOCKBJS02`) |
| `inpost` | `inpost-key-alpha` | `inpost-key-bravo` |
| `ocs` | `ocs-key-alpha` | `ocs-key-bravo` |
| `exelot` | `exelot-key-alpha` | `exelot-key-bravo` (PNG labels) |
| `veho` | `veho-key-alpha` | `veho-key-bravo` (no Veho account settings) |

What a bad key returns differs by mock:

| Mock | No key / unknown key / `apiky-500` |
| --- | --- |
| `royalmail`, `fedex`, `bjs`, `inpost`, `ocs`, `exelot` | 403 / 403 / 403 |
| `ups`, `coll8`, `dpdeu`, `amazon` | 401 / 403 / 500 |
| `amazon-sfp`, `veho` | 401 / 401 / 401 |

On `dpdeu`, and on `amazon` for create-label, the mock checks the request body before the key. These statuses apply to a body that passes that check.

**First call.** This needs no request body. It returns the service codes for a Royal Mail test customer, checked on 11 Nov 2026.

```sh
curl -H 'x-api-key: rm-key-acme' \
  https://royalmail.mocks.merak.freightops.dev/shipping/getServiceCodes
```

For a request body, copy the example in `apps/<proxy>/api/` (the production OpenAPI spec with fake examples) or the builders in `apps/<proxy>/test/helpers.ts` or `harness.ts`. UPS sample XML is in `apps/mock-upstreams/fixtures/ups/`.

**Locally.** `mise install`, `pnpm install`, then `pnpm dev` starts every mock and `mock-upstreams` (port 4000). Each mock has its own port, listed in the repo README. `GET http://localhost:4000/__calls` lists every upstream call the mocks made.

## How to trigger a failure

Failures come from magic values in the request. There are no hidden switches. Postcode and ZIP values ignore spaces and case on every mock except `royalmail`. On `royalmail`, every magic value (postcode, id and service code) must match exactly, spaces and capitals included. `veho` reads the first five digits of the ZIP. An id prefix ignores case. Any other id behaves as a real one.

| Mock | Where | Value | Caller gets |
| --- | --- | --- | --- |
| `royalmail` | `shipTo.postalCode` | `ERR 400`, `ERR 401`, `ERR 500` | A carrier error with that status (`ERR 401` is a carrier 401, not an auth failure) |
| `royalmail` | `shipTo.postalCode`, destination outside GB and IM | `NODOC CI` | The label, with a warning, and without the commercial invoice |
| `royalmail` | `shipTo.postalCode`, destination outside GB and IM | `NODOC CN23` | With a label format other than PDF: the label, with a warning, and without the CN23. With a PDF label the CN23 comes back inline, so this value has no effect |
| `royalmail` | `shipTo.postalCode`, destination outside GB and IM | `NODOC ALL` | The label, with a warning, and without the commercial invoice. The CN23 is missing too, unless the label is PDF |
| `royalmail` | `shipmentIds` | `SHIPMENT-500` | 500 on the status update. A manifest request ignores that failure |
| `royalmail` | manifest `siteId` | `MANIFEST-500` | 500 on the manifest |
| `royalmail` | `serviceCode` | `RMT48SOLD` | 500 (a disabled code) with `rm-key-acme`. Other keys get 400 no mapping |
| `royalmail` | `x-api-key` | `rm-key-inactive` | 400 no mapping; `getServiceCodes` is 500 |
| `royalmail` | `x-api-key` | `rm-key-revoked-creds`, `rm-key-auth-outage` | 403 |
| `ups` | ShipTo postcode | `FA1 1LV` | Address error `120802`: XML 200 with `ResponseStatusCode` 0, JSON 400 |
| `ups` | ShipTo postcode | `WA1 1RN` | Success with warning `120900` on the XML routes. The V2 JSON response carries no warnings |
| `ups` | ShipTo or Locator origin postcode | `TE5 500` | 500 gateway error as JSON |
| `ups` | Locator origin postcode | `NO1 0AP` | No locations, `350104` |
| `ups` | Shipper number in the XML body | `NOAUTH` | Not authorised, `120120`. V2 uses the proxy's own shipper number, so it cannot trigger this |
| `ups` | Void shipment id, label recovery tracking number | `1Z0000000000000000` | Not found (`190117` void, `151044` label recovery) |
| `ups` | V2 cancel `trackingNumber` | Anything but `1Z` plus 16 characters | `190101` invalid tracking number |
| `coll8` | `shipTo.postalCode` | `VAL 1DN` | 500 `COLL8_ERROR_CREATE_SHIPMENT` with a validation message |
| `coll8` | `shipTo.postalCode` | `ERR 500`, `ERR 503` | 500 or 503 `COLL8_ERROR_CREATE_SHIPMENT` |
| `coll8` | `shipTo.postalCode` | `NOL 4BL` | 500 `COLL8_ERROR_LABEL_TRANSLATION` |
| `coll8` | `shipTo.postalCode` | `LBL 500` | 500 `COLL8_ERROR_PACKAGE_LABEL` |
| `coll8` | `shipTo.postalCode`, PNG request | `PNG 500` | 500, plain-text conversion error |
| `coll8` | Cancel tracking number prefix | `UNKNOWN` | 404 |
| `coll8` | Cancel tracking number prefix | `CANCELLED`, `MANIFESTED` | 500 with a validation message |
| `coll8` | End-of-day manifest tracking number prefix | `UNKNOWN`, `CANCELLED` | 500 with a "not found" message |
| `coll8` | `x-api-key` | `coll8-test-key-no-account` | 403 `ACCOUNT_CODE_NOT_CONFIGURED` on create and manifest, not on cancel |
| `coll8` | `x-api-key` | `coll8-test-key-unknown-account` | 500 on create and manifest, not on cancel |
| `fedex` | `shipTo.postalCode` | `ERR 400`, `ERR 500`, `ERR 503` | A carrier error with that status |
| `fedex` | `shipTo.postalCode` | `ERR 401` | The proxy refetches its token, retries once, then 401 |
| `fedex` | `shipTo.postalCode` | `NO SHIP` | 500 "Client request failed validation" |
| `fedex` | `shipTo.postalCode` | `WARN 1NG` | 201 with a warning |
| `fedex` | `shipTo.postalCode`, `PLT: true` | `ETD 0RIG` | 201 with `mustAttachPhysically: true` |
| `fedex` | `shipTo.postalCode`, service `FXGND` | `NO SVC` | 400, no shipment created |
| `fedex` | Cancel `shipmentId` prefix | `UNKNOWN`, `CANCELLED`, `ERR500` | 500 |
| `fedex` | `x-api-key` | `fedex-key-inactive`, `fedex-key-no-account` | 400 |
| `fedex` | `x-api-key` | `fedex-key-rejected-account` | 403 carrier error |
| `dpdeu` | `shipTo.postalCode` | `FLT 400` | DPD Germany 400 `COMMON_7`; DPD Netherlands 400 `SCHEMA_ERROR` |
| `dpdeu` | `shipTo.postalCode` | `SCH 400` | 400 `SCHEMA_ERROR` |
| `dpdeu` | `shipTo.postalCode` | `ERR 500` | 500 `INTERNAL_SERVER_ERROR` |
| `dpdeu` | `shipTo.postalCode` | `SHP FLT` | DPD Germany 400 `SHIPMENT_1`; DPD Netherlands 500 |
| `dpdeu` | `shipTo.postalCode`, PNG request | `PNG 500` | 500 `PDF_CONVERSION_ERROR` |
| `dpdeu` | `x-api-key` | `dpdeu-key-bravo` | 403 for DPD Netherlands |
| `dpdeu` | `x-api-key` | `dpdeu-key-bad-login`, `dpdeu-key-no-password` | 500 |
| `dpdeu` | `x-api-key` | `dpdeu-key-revoked-token` | The first call per provider on each instance retries its login, then succeeds. The token cache is in memory |
| `amazon-sfp`, `amazon` | `shipTo.postalCode` | `ERR 400`, `ERR 403` | 500 carrying Amazon's status |
| `amazon-sfp`, `amazon` | `shipTo.postalCode` | `ERR 500` | 500, not retried |
| `amazon-sfp`, `amazon` | `shipTo.postalCode` | `ERR 429` | Four calls, then 500 |
| `amazon-sfp`, `amazon` | `shipTo.postalCode` | `RETRY 429` | 201 on the retry |
| `amazon-sfp`, `amazon` | `shipTo.postalCode` | `NO RATE` | 500 "No rate available" |
| `amazon-sfp`, `amazon` | `shipTo.postalCode` | `BUY 500` | Rates succeed, the purchase gives 500 |
| `amazon-sfp`, `amazon` | Tracking id prefix | `UNKNOWN`, `ERR500`, `ERR429`, `RETRY429` | 404, 500, 500, 200 on retry |
| `amazon` | Cancel shipment id prefix | `UNKNOWN`, `ERR500` | 400 "The shipment could not be found.", 500. `ERR429` and `RETRY429` do nothing on cancel |
| `amazon-sfp` | Cancel shipment id | Any | Cancel never fails visibly: every failure gives 200 `{}` |
| `amazon-sfp`, `amazon` | Tracking id, no prefix | Last digit 0-1, 2-7, 8-9 | `PreTransit`, `InTransit`, `Delivered` |
| `amazon-sfp`, `amazon` | `x-api-key` | `amazon-key-bad-lwa`, `amazon-key-bad-aws` (`amzl-key-…` on `amazon`) | 500; for bad AWS keys, 500 carrying Amazon's 403 |
| `bjs` | `shipTo.postalCode` | `ERR 400`, `ERR 500`, `ERR 503` | 500 carrier error carrying BJS's body |
| `bjs` | `shipTo.postalCode` | `NO RESULT`, `LABEL 404`, `XTRA PAGE` | 500 "An unexpected error occurred" |
| `bjs` | `shipTo.postalCode` | `BAD PDF` | 500 `INTERNAL SERVER ERROR` |
| `bjs` | Cancel `shipmentId` prefix | `UNKNOWN`, `CANCELLED`, `ERR500` | 500 carrier error |
| `bjs` | `x-api-key` | `bjs-key-wrong-secret`, `bjs-key-no-secret` | 500 carrier error (BJS 401) |
| `bjs` | `accountId` | Any account but `MOCKBJS01` or `MOCKBJS02` (after an `S` or `E` prefix) | 500 carrier error (BJS 401) |
| `inpost` | `shipTo.postalCode`, home delivery | `ERR 400`, `ERR 500`, `ERR 503` | 500 carrier error |
| `inpost` | `shipTo.postalCode` | `NO LABEL` | 500, label not found |
| `inpost` | `shipTo.postalCode`, PNG request | `PNG 500` | Three converter calls, then 500 |
| `inpost` | `shipTo.postalCode`, return | `NO PARCEL` | 500 |
| `inpost` | Locker `pointId` | Anything but `MOCKPT0001` to `MOCKPT0003` | 500 carrier error |
| `inpost` | `x-api-key` | `inpost-key-bad-secret`, `inpost-key-token-outage`, `inpost-key-no-credentials` | 403 |
| `inpost` | `x-api-key` | `inpost-key-wrong-org` | 500 carrier error |
| `ocs` | `shipTo.postalCode` | `ERR 400`, `ERR 500`, `ERR 503` | 599 carrier error |
| `ocs` | `shipTo.postalCode` | `NO NUMS` | 500 "An unexpected error occurred" |
| `ocs` | `shipTo.postalCode` | `MULTI PG` | A two-page label. PNG keeps page 2 only. |
| `ocs` | `shipTo.postalCode`, PNG request | `PNG 500` | 500 after four converter calls |
| `exelot` | `shipTo.postalCode` | `ERR 400`, `ERR 401`, `ERR 500`, `ERR 503` | 599 carrier error |
| `exelot` | `shipTo.postalCode`, `labelFormat: PNG`, key `exelot-key-alpha` | `PNG FAIL` | 500 after four converter calls. A PDF request gets a normal 201 |
| `exelot` | `x-api-key` | `exelot-key-bad-login` | 403 |
| `exelot` | `x-api-key` | `exelot-key-zpl`, `exelot-key-unconfigured` | 500 |
| `exelot` | `x-api-key` and `labelFormat` | `exelot-key-bravo` with a PDF request | 500 (that partner gets PNG labels) |
| `veho` | `shipTo.postalCode` (first 5 digits) | `99999`, or any ZIP but `00001` to `00010` and the values below | 400 `unserviceable_zip_code` on `shipTo.postalCode` |
| `veho` | `shipTo.postalCode` | `00422` | 400 on `shipTo.addressLine1` and `externalClient` |
| `veho` | `shipTo.postalCode` | `00401`, `00403`, `00429` | 400 `CarrierException` |
| `veho` | `shipTo.postalCode` | `00500`, `00503` | 599 after a lookup and one retry |
| `veho` | `shipTo.postalCode` | `00502`, `00408`, `00404` | 200: the order exists, or the label arrives after retries |
| `veho` | `shipTo.postalCode` | `00410` | 599 within 12 s; the order exists |
| `veho` | `shipTo.postalCode` | `00409` | Create works; cancel gives 400 `CarrierException` |
| `veho` | Order, package or manifest id | `MOCKERR404`, `MOCKERR401`, `MOCKERR429` | 400 `CarrierException` (any Veho 4xx). On a reprint, `MOCKERR404` first retries the label for about 10.8 s. As a `shippingReference`, `MOCKERR404` is not an error |
| `veho` | Order, package or manifest id | `MOCKERR500`, `MOCKERR503` | 599 |
| `veho` | Order, package or manifest id | `MOCKERRSLOW` | 599 after about 3 s: mock Veho would answer 500 after 4 s, but the proxy gives up at 3 s |

Each proxy's README has the full list, the exact error bodies and the reasons behind each row.

## What is faithful and what is not

**Mirrored from the production proxy**

- **Contract.** Paths, methods, headers, auth, request and response bodies, status codes and error shapes. Where the source has an OpenAPI spec, a copy sits in `apps/<proxy>/api/` and requests are checked against it. Where the source differs from its spec, the mock follows the source.
- **Lookups.** A key resolves to an ApiKy profile, the profile to per-customer config and credentials, and service codes map as in the source. The stores are in memory, seeded from fixtures, with the source's document shapes.
- **Logic.** Validation, mapping and error translation are ported from the source.

**Quirks kept on purpose.** These mirror production behaviour, so a test against a mock sees what production does. They are read from the source code. They are not checked against production traffic unless a proxy's README says so.

- Weights. OCS and Exelot multiply the weight by 1000 unless the unit is exactly `KILOGRAM`, so a `GRAM` weight and any other unit are multiplied. Royal Mail never reads the weight unit, so any unit is sent as given.
- Amazon Logistics refuses PDF label requests on create. Mock Amazon lists no resolutions for PDF, so the proxy's resolution check finds no match. Validate mode does not refuse them. It also refuses `-SIG` services at purchase, because it never sends the delivery-confirmation add-on that mock Amazon requires with a signature. The `-SIG` case is inferred from the SFP proxy's code, which does send the add-on, and validate mode does not refuse it either. A request with `notes` gets 200 `{}`, validate mode included, and any unrouted path gets 200 `OK`.
- Status codes. OCS and Exelot return 599 for every carrier rejection. Other failures keep their own status, for example 500 when the carrier is unreachable and 403 when the Exelot login fails. BJS and InPost return 500 for every carrier failure. Coll8 returns 500 for its own validation errors.
- DPD Europe rejects a phone number that lacks a leading `+` or contains a space, when one is sent. For a delivery between two countries that are neither the same nor both EU members, it also requires `customs.commodities` and an `invoiceNumber` on every package.
- Selector's UPS label recovery call is sent as `text/xml`, which the UPS proxy does not parse. Through `ups` it always gets UPS error `10001` ("not well formed") with HTTP 200.
- Malformed JSON gives a 500 on `royalmail`, `coll8`, `ups` (V2 routes), `bjs`, `inpost`, `ocs`, `exelot`, `veho` and `amazon-sfp`. It gives a 400 on `fedex`, `dpdeu` and `amazon`.
- Typos in error texts are kept, for example `additonal`.

**Not faithful**

- Every upstream is fake. `mock-upstreams` answers for ApiKy and each carrier. Some upstream error shapes are invented, because the source shows none (BJS, OCS).
- Labels are placeholders. PDFs say `MOCK LABEL - NOT FOR CARRIAGE`. UPS GIF and PNG labels are 1x1 images. ZPL and EPL are short text programs.
- Tracking numbers, shipment ids and tokens use made-up formats.
- Carrier mocks keep no shipment state. Cancelling twice succeeds. UPS void and label recovery accept any number except the magic one.
- `veho` has no production proxy to copy. It follows the agreed contract and the Veho spec. Where the real proxy differs once built, the real one wins.
- Log output, metrics and health routes differ from production. The mocks never log bodies, labels, keys or credentials.

**Limits**

- Dev only. No prod environment, no support commitment.
- All state is in memory. A restart or a second instance starts from the fixtures. Per-instance state includes token caches, the `/__calls` recorder and, on `royalmail`, manifest totals (a manifest served by another instance returns zero shipments). `veho` keeps up to 1,000 orders per `mock-upstreams` instance, so a lookup, label or cancel can miss an order another instance created.
- Not mocked: DHL (Selector calls DHL directly, so there is no proxy to copy), Amazon's `/hooks/tracking` push handlers, and Veho webhooks, tracking and proof of delivery.
- Logs go to the GFS Datadog only. The Datadog service name is probably `mock-<key>-cp` `[??]`.

## How selector2 will use them (planned)

selector2 is a planned TypeScript replacement for Selector's label-getting. It is intended to use these mocks as its carrier egress in dev. It will read each mock's URI from the `mock-edge` outputs and call it with a Cloud Run ID token. The mocks stay public for now, so the token is sent but not required.

## Changing or adding a mock

The repo is a pnpm workspace:

- `apps/<carrier>-proxy`: one mock proxy and its README, spec copy, fixtures and tests.
- `apps/mock-upstreams`: one server with a router and fixtures for ApiKy and each carrier.
- `packages/mock-kit` and `packages/apiky-client`: the logger, mock PDF labels, ID sequences and ApiKy lookup.
- `iac/projects/mock-<key>`: one Cloud Run service per mock. `iac/projects/mock-edge` holds the load balancer, DNS and outputs.
- `scripts/smoke.mts`: one happy path per mock, run through the public names.

A new mock touches the app, a `mock-upstreams` router and fixtures, a `mock-<key>` IaC project, the `proxies` map in `edge.tf`, the `deploy-dev` and `tf-plan-pr` matrices, the smoke script, and the READMEs. Run `pnpm lint`, `pnpm typecheck` and `pnpm test` before a PR. A merge to `main` deploys to dev.

Never remove a name from `mock-edge`. The platform load-balancer module deletes a backend before it detaches it, and the apply fails. Only add or update.

Contributor and agent rules are in `AGENTS.md`: same contract, lookups and logic; every upstream mocked; all data fake; never log bodies, labels, keys or credentials.

---

## Author review (not part of the page)

Gaps marked `[??]` in the page (unchanged by the 12 Nov correction pass):

1. The `terragrunt output service_uris` command was not run. It follows from `root.hcl` (needs `TF_VAR_env=dev` and state access).
2. The cold-start time of about 5 s comes from the handover's note on `mock-upstreams`. It was not measured for the proxies.
3. The Datadog service name `mock-<key>-cp` is inferred from the `SERVICE_NAME` env var. It was not checked in Datadog.

Corrected on 12 Nov 2026 against `origin/main` `ae57c96`, from the B5-B8 contract digest. Each fix was re-read in source first.

- Postcode and id matching: `royalmail` matches every magic value exactly (`apps/mock-upstreams/src/royalmail/index.ts:136-144,289,368,419`). All other mocks normalise postcodes (each router's `normalise`). `veho` reads 5 ZIP digits (`veho/index.ts:122`).
- Malformed JSON: 400 on `fedex` (`fedex-proxy/src/middlewares/global-error.ts:16-17`), `dpdeu` (`error-handler.ts:24-29`) and `amazon` (`amazon-logistics-proxy/src/app.ts:141-144`). The other nine give 500.
- Weights: OCS and Exelot multiply unless the unit is exactly `KILOGRAM` (`ocs-service.ts:109`, `exelot-service.ts:68`). Royal Mail never reads the unit (`royalmail-service.ts:223`).
- Status codes: 599 only for carrier rejections. OCS and Exelot network failures are 500 (`ocs-integration.ts:44`, `exelot-integration.ts:47-54`).
- `prod-57357` removed. It appears nowhere in the repo.
- Amazon Logistics: PDF refusal is create-only (`labelling.service.ts:234-241` returns before the check at 270-284) and comes from mock Amazon listing no PDF resolutions (`mock-upstreams/src/amazon/index.ts:82-84`). `-SIG` is refused by mock Amazon (`index.ts:465-466`). `notes` gives 200 `{}` before validate mode (`labelling.service.ts:148-151`, `writer.ts:14-18`).
- Amazon cancel: `amazon` returns 400 for `UNKNOWN`, 500 for `ERR500`, and ignores `ERR429`/`RETRY429` (`amazon/index.ts:507-518`). `amazon-sfp` cancel always gives 200 `{}` (`labelling.handler.ts:388-391`).
- DPD Europe: phone rule applies only when a phone is sent, and an international customs and invoice rule exists (`validator.ts:26-42,47-54`). The `dpdeu-key-revoked-token` retry happens once per instance and provider (`token-manager.ts:30-35`).
- Veho `MOCKERR*`: 4xx gives 400 and 5xx gives 599 (`exceptions.ts:98-105`). `MOCKERRSLOW` is a 599 after the proxy's 3 s timeout (`config.ts:56`, `mock-upstreams/src/veho/index.ts:42,166-170`). `MOCKERR404` as a `shippingReference` is a lookup miss (`handlers.ts:102`). A reprint retries a label 404 for about 10.8 s (`handlers.ts:56-77`, `config.ts:57-58`).
- Royal Mail: `RMT48SOLD` fails with 500 only for `rm-key-acme` (`royal-mail-proxy/fixtures/customers.json`, `services.json`). `NODOC CN23` has no effect on a PDF label (`royalmail-integration.ts:120-142`). `SHIPMENT-500` is swallowed inside a manifest (`royalmail-integration.ts:159-171`).
- Coll8: cancel `UNKNOWN` is 404 and `CANCELLED`/`MANIFESTED` are 500 (`errors.ts:35-63`). The proxy has no label route (`app.ts:66-68`). The no-account key applies to create and manifest only (`labelling.ts:62,104`). `coll8-test-key-unknown-account` added.
- BJS: `accountId` takes an `S` or `E` prefix (`bjs-integration.ts:21-31`), and `labelFormat` is ignored (`bjs-service.ts:116`).
- UPS: `WA1 1RN` warning is XML only (`ups-proxy/src/api/routesV2/mapping/shipment.ts:9-17`). `NOAUTH` is XML only (`create-label.ts:22`). Label recovery sent as `text/xml` is not parsed (`ups-proxy/src/app.ts:43-46`).
- Exelot `PNG FAIL` only fires for a PDF partner (`mock-upstreams/src/exelot/index.ts:82-97`).
- `amazon-sfp`: validate mode, two channels, single package, `BT` refusal (`amazon-sfp-proxy/src/handlers/labelling.handler.ts:74-76,105-108`, `api/api.yaml:343-346`, `config.ts:60-61`).
- Health: `amazon` answers `/health/liveness` through its catch-all (`amazon-logistics-proxy/src/app.ts:222-228`). `exelot` returns 400 on unknown paths (`exelot-proxy/src/app.ts:104-110`).

Digest claims the source did not support, or that needed no page change:

- Digest item 13 (InPost): `inpost-key-malformed-profile` gives 500 per the README and fixtures, but the page never listed that key, so nothing changed. `NO PARCEL` already said "return" on the page.
- Digest item 19: the other absences (no Royal Mail validate, cancel or reprint; nine mocks without validate) were not stated on the page, so nothing changed.
- Digest item 20: "Exelot always calls the real ApiKy" is true of the production source only (README line 129). The mock reads `APIKY_BASE_URL` (`exelot-proxy/src/config.ts:31`). It stays off the page.

Still unconfirmed:

- The DPD Europe claim that its validator "probably rejects every Selector call" is the README's own hypothesis (`apps/dpd-europe-proxy/README.md`, "Why production probably fails validation on every call"), read from code with no production logs. It stays off the page.
- The `-SIG` refusal is inferred from the SFP proxy's code. It is not confirmed against the production Logistics proxy.
- The production sources and commit hashes named in the table were not accessed. Only the mock READMEs state them.

Judgement calls for you:

- The DPD Europe rules and the Amazon Logistics `-SIG` refusal sit in "Quirks kept on purpose". Both are described neutrally. Drop either if you would rather not publish them before you raise them.
- Left out on purpose: token and key logging in the production proxies, and Exelot always calling the real ApiKy in production. The mock READMEs in the repo still state them, and the page points readers at those READMEs.
- The public hostnames, fake keys and fake account numbers (`MOCKFX001`, `MOCKBJS01`) are all from the repo's own docs and fixtures.
- The page names ADO repo names and commit hashes of the production sources, taken from the mock READMEs and the handover. Check you are happy for the wiki to show them.
- Selector's `CUST_SITES` column for each proxy's URL is known only for UPS (`UPS_URL`). The page does not name the others.
- The selector2 section follows the vault's Selector2 Overview (mocks as egress, ID token sent, mocks stay public). It is marked planned.
- `origin/main` is `ae57c96` (#15). The handover still says `d98fd9b` (#14). The page reflects `ae57c96`.
