---
title: "Selector2 — E2 Confluence draft: mock carrier proxies"
programme: selector2
status: draft
unit: E2
tags: [bifrost, merak, draft]
updated: "2026-11-11"
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
| `coll8` | `https://coll8.mocks.merak.freightops.dev` | `coll8.gfsdeliver.com`. ADO `GFS Coll8 Integration` | Creates and cancels Coll8 shipments, returns labels, sends the end-of-day manifest |
| `fedex` | `https://fedex.mocks.merak.freightops.dev` | `fedex.gfsdeliver.com`. GitHub `gfs-hybrid-services/fedex-proxy`, `main` `1d246f8` | Creates and cancels FedEx shipments and returns labels |
| `dpdeu` | `https://dpdeu.mocks.merak.freightops.dev` | `dpd-eu.gfsdeliver.com`. ADO `GFS DPD-Europe Integration`, `dpd-europe-proxy` | One route that creates DPD Germany or DPD Netherlands labels (SOAP upstream) |
| `amazon-sfp` | `https://amazon-sfp.mocks.merak.freightops.dev` | `new-amazon-prod.gfsdeliver.com`. GitHub `gfs-hybrid-services/amazon-proxy`, `master` `be40413` | Buys Amazon Shipping labels for Seller Fulfilled Prime orders, cancels, tracks |
| `amazon` | `https://amazon.mocks.merak.freightops.dev` | `amazon.gfsdeliver.com` (Amazon Logistics). ADO `GFS Amazon Logistics Integration`, `gfs-amazon-logistics-proxy`, `master` `6f0d113` | Buys Amazon Shipping labels, cancels, and serves the tracking route that connectors-amazon polls |
| `bjs` | `https://bjs.mocks.merak.freightops.dev` | `bjs.gfsdeliver.com`. ADO `bjs-proxy` in "GFS Hybrid Services and Carrier Integrations", default branch `ed56a53` (not the GitHub copy) | Books BJS Home Delivery, returns one label per product, cancels |
| `inpost` | `https://inpost.mocks.merak.freightops.dev` | `inpost.gfsdeliver.com`. GitHub `gfs-hybrid-services/inpost-proxy`, `main` `64656dc` | Creates InPost shipments and returns, home or locker, with labels |
| `ocs` | `https://ocs.mocks.merak.freightops.dev` | `ocs.gfsdeliver.com`. ADO `ocs-proxy`, `main` `29eeaa6` (prod image `prod-57357`) | Books an OCS Worldwide parcel and returns its label |
| `exelot` | `https://exelot.mocks.merak.freightops.dev` | `exelot.gfsdeliver.com`. ADO `GFS Exelot Integration`, `main` `b21a47d` | Creates an Exelot parcel with a commercial invoice and returns its label |
| `veho` | `https://veho.mocks.merak.freightops.dev` | No production proxy exists. Built from the agreed contract (`gfs-hybrid-services/carrier-proxies`, `apps/veho-proxy`, `main` `a996061`) and the Veho spec | Creates labels, reprints, cancels, updates delivery instructions, quotes, manifests |

A private service, `mock-upstreams`, fakes everything the mocks call: ApiKy and every carrier API. Only the mocks can reach it.

## How to call one

**Public name.** Use `https://<name>.mocks.merak.freightops.dev` with the same paths, headers and bodies as the production proxy. Send a mock ApiKy key in `x-api-key`. Nothing else is needed.

**Direct `run.app` URI.** The `mock-edge` Terraform project (`iac/projects/mock-edge`) outputs `service_uris` and `service_account_emails`, keyed by proxy key: `royalmail`, `ups`, `coll8`, `fedex`, `dpdeu`, `amazonsfp`, `amazon`, `bjs`, `inpost`, `ocs`, `exelot`, `veho`. Note `amazonsfp` here and `amazon-sfp` in the public name. Read them with `terragrunt output service_uris` `[??]`. The Cloud Run service is `mock-<key>-cp-dev`.

Since 11 Nov 2026, `mock-edge` also takes an `invoker_members` input. It is a list of `serviceAccount:<email>` values that get `roles/run.invoker` on all twelve mocks. The mocks are still public (`allUsers`), so the grant is additive and nothing enforces it. A caller that expects IAM later can already send a Cloud Run ID token whose audience is the service URI.

**Health check.** All twelve answer `GET /health/liveness` with 200 on both the public name and the `run.app` URI. Use it on direct URLs. Cloud Run's own frontend swallows `/healthz` on `run.app` URLs and returns an HTML 404. Through the public name, `veho` and `amazon-sfp` also serve `/healthz`. `veho` returns 404 on `/` and `/health`. Do not read those as an outage.

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
| `bjs` | `bjs-key-alpha` (send `accountId` `MOCKBJS01`) | `bjs-key-bravo` (`MOCKBJS02`) |
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

**First call.** This needs no request body. It returns the service codes for a Royal Mail test customer, checked on 11 Nov 2026.

```sh
curl -H 'x-api-key: rm-key-acme' \
  https://royalmail.mocks.merak.freightops.dev/shipping/getServiceCodes
```

For a request body, copy the example in `apps/<proxy>/api/` (the production OpenAPI spec with fake examples) or the builders in `apps/<proxy>/test/helpers.ts` or `harness.ts`. UPS sample XML is in `apps/mock-upstreams/fixtures/ups/`.

**Locally.** `mise install`, `pnpm install`, then `pnpm dev` starts every mock and `mock-upstreams` (port 4000). Each mock has its own port, listed in the repo README. `GET http://localhost:4000/__calls` lists every upstream call the mocks made.

## How to trigger a failure

Failures come from magic values in the request. There are no hidden switches. Postcode and ZIP values ignore spaces and case. An id prefix also ignores case. Any other id behaves as a real one.

| Mock | Where | Value | Caller gets |
| --- | --- | --- | --- |
| `royalmail` | `shipTo.postalCode` | `ERR 400`, `ERR 401`, `ERR 500` | A carrier error with that status |
| `royalmail` | `shipTo.postalCode`, non-GB | `NODOC CN23`, `NODOC CI`, `NODOC ALL` | The label, with a warning, and without that customs document |
| `royalmail` | `shipmentIds` | `SHIPMENT-500` | 500 on the status update |
| `royalmail` | manifest `siteId` | `MANIFEST-500` | 500 on the manifest |
| `royalmail` | `serviceCode` | `RMT48SOLD` | 500 (a disabled code) |
| `royalmail` | `x-api-key` | `rm-key-inactive` | 400 no mapping; `getServiceCodes` is 500 |
| `royalmail` | `x-api-key` | `rm-key-revoked-creds`, `rm-key-auth-outage` | 403 |
| `ups` | ShipTo postcode | `FA1 1LV` | Address error `120802`: XML 200 with `ResponseStatusCode` 0, JSON 400 |
| `ups` | ShipTo postcode | `WA1 1RN` | Success with warning `120900` |
| `ups` | ShipTo or Locator origin postcode | `TE5 500` | 500 gateway error as JSON |
| `ups` | Locator origin postcode | `NO1 0AP` | No locations, `350104` |
| `ups` | Shipper number | `NOAUTH` | Not authorised, `120120` |
| `ups` | Void shipment id, label recovery tracking number | `1Z0000000000000000` | Not found (`190117` void, `151044` label recovery) |
| `ups` | V2 cancel `trackingNumber` | Anything but `1Z` plus 16 characters | `190101` invalid tracking number |
| `coll8` | `shipTo.postalCode` | `VAL 1DN` | 500 `COLL8_ERROR_CREATE_SHIPMENT` with a validation message |
| `coll8` | `shipTo.postalCode` | `ERR 500`, `ERR 503` | 500 or 503 `COLL8_ERROR_CREATE_SHIPMENT` |
| `coll8` | `shipTo.postalCode` | `NOL 4BL` | 500 `COLL8_ERROR_LABEL_TRANSLATION` |
| `coll8` | `shipTo.postalCode` | `LBL 500` | 500 `COLL8_ERROR_PACKAGE_LABEL` |
| `coll8` | `shipTo.postalCode`, PNG request | `PNG 500` | 500, plain-text conversion error |
| `coll8` | Tracking number prefix (cancel, manifest, label) | `UNKNOWN`, `CANCELLED`, `MANIFESTED` | Failures per the Coll8 README table |
| `coll8` | `x-api-key` | `coll8-test-key-no-account` | 403 `ACCOUNT_CODE_NOT_CONFIGURED` |
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
| `dpdeu` | `x-api-key` | `dpdeu-key-revoked-token` | The first call per provider retries its login, then succeeds |
| `amazon-sfp`, `amazon` | `shipTo.postalCode` | `ERR 400`, `ERR 403` | 500 carrying Amazon's status |
| `amazon-sfp`, `amazon` | `shipTo.postalCode` | `ERR 500` | 500, not retried |
| `amazon-sfp`, `amazon` | `shipTo.postalCode` | `ERR 429` | Four calls, then 500 |
| `amazon-sfp`, `amazon` | `shipTo.postalCode` | `RETRY 429` | 201 on the retry |
| `amazon-sfp`, `amazon` | `shipTo.postalCode` | `NO RATE` | 500 "No rate available" |
| `amazon-sfp`, `amazon` | `shipTo.postalCode` | `BUY 500` | Rates succeed, the purchase gives 500 |
| `amazon-sfp`, `amazon` | Tracking or shipment id prefix | `UNKNOWN`, `ERR500`, `ERR429`, `RETRY429` | Tracking: 404, 500, 500, 200 on retry. Cancel: see the README. |
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
| `exelot` | `shipTo.postalCode`, `labelFormat: PNG` | `PNG FAIL` | 500 after four converter calls |
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
| `veho` | Order, package or manifest id | `MOCKERR404`, `MOCKERR401`, `MOCKERR429`, `MOCKERR500`, `MOCKERR503`, `MOCKERRSLOW` | That Veho status; `MOCKERRSLOW` is a 500 after 4 s |

Each proxy's README has the full list, the exact error bodies and the reasons behind each row.

## What is faithful and what is not

**Mirrored from the production proxy**

- **Contract.** Paths, methods, headers, auth, request and response bodies, status codes and error shapes. Where the source has an OpenAPI spec, a copy sits in `apps/<proxy>/api/` and requests are checked against it. Where the source differs from its spec, the mock follows the source.
- **Lookups.** A key resolves to an ApiKy profile, the profile to per-customer config and credentials, and service codes map as in the source. The stores are in memory, seeded from fixtures, with the source's document shapes.
- **Logic.** Validation, mapping and error translation are ported from the source.

**Quirks kept on purpose.** These mirror production behaviour, so a test against a mock sees what production does. They are read from the source code. They are not checked against production traffic unless a proxy's README says so.

- Weights. OCS and Exelot multiply a `GRAM` weight by 1000. Royal Mail sends a `GRAM` weight as if it were kilograms.
- Amazon Logistics refuses PDF labels, answers 200 `{}` to any request with `notes`, and refuses `-SIG` services. The `-SIG` case is inferred from the SFP proxy's code.
- Status codes. OCS and Exelot return 599 for every carrier rejection. BJS and InPost return 500 for every carrier failure. Coll8 returns 500 for its own validation errors.
- DPD Europe rejects a phone number that lacks a leading `+` or contains a space.
- Malformed JSON gives a 500, not a 400, on several mocks.
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

Gaps marked `[??]` in the page:

1. The `terragrunt output service_uris` command was not run. It follows from `root.hcl` (needs `TF_VAR_env=dev` and state access).
2. The cold-start time of about 5 s comes from the handover's note on `mock-upstreams`. It was not measured for the proxies.
3. The Datadog service name `mock-<key>-cp` is inferred from the `SERVICE_NAME` env var. It was not checked in Datadog.

Judgement calls for you:

- The DPD Europe phone rule and the Amazon Logistics `-SIG` refusal sit in "Quirks kept on purpose". Both are described neutrally. Drop either if you would rather not publish them before you raise them. The `-SIG` case is inferred from the SFP proxy's code, not confirmed in prod.
- Left out on purpose: token and key logging in the production proxies, Exelot always calling the real ApiKy, and the claim that DPD Europe's validator rejects every Selector call. The mock READMEs in the repo still state them, and the page points readers at those READMEs.
- The public hostnames, fake keys and fake account numbers (`MOCKFX001`, `MOCKBJS01`) are all from the repo's own docs and fixtures.
- The page names ADO repo names and commit hashes of the production sources, taken from the mock READMEs and the handover. Check you are happy for the wiki to show them.
- Selector's `CUST_SITES` column for each proxy's URL is known only for UPS (`UPS_URL`). The page does not name the others.
- The selector2 section follows the vault's Selector2 Overview (mocks as egress, ID token sent, mocks stay public). It is marked planned.
- `origin/main` is `ae57c96` (#15). The handover still says `d98fd9b` (#14). The page reflects `ae57c96`.
