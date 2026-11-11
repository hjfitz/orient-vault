---
tags: [waypoint, ledger]
---
# carrier-playground — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-11-11 — Expose mock proxy URIs and invoker grants for selector2

Expose mock proxy URIs and invoker grants for selector2

mock-edge now outputs service_uris and service_account_emails for all 12 proxies and takes invoker_members (default empty) to grant roles/run.invoker. The proxies stay public (allUsers). Applied to dev with 0 resources changed, outputs only. Cloud Run's run.app frontend swallows /healthz with an HTML 404, so call a proxy's own health route (Veho: /health/liveness) on direct URLs.

PR: ilg-merak/carrier-playground#15

## 2026-11-09 — Add a mock Veho proxy at veho.mocks.merak.freightops.dev, built from the agreed contract

Add a mock Veho proxy at veho.mocks.merak.freightops.dev, built from the agreed contract

Ship: SHIP-1106-carrier-playground. Veho has no prod proxy: mock built from the agreed contract (carrier-proxies apps/veho-proxy openapi.yaml, CID-336), the spec (Confluence 323878984) and epic CID-335's stories, with a mock Veho API v2 from Veho's public docs. All six operations; error mapping per CID-336; open questions documented against tickets (CID-343/345/346/347-351). Review fixed idempotency (lookup-before-create per the contract), a real Veho tracking host, and log safety. Smoke 42/42 across twelve names.

PR: ilg-merak/carrier-playground#14

## 2026-11-06 — Add a mock Exelot proxy at exelot.mocks.merak.freightops.dev; spread metaData like the sources

Add a mock Exelot proxy at exelot.mocks.merak.freightops.dev; spread metaData like the sources

Ship: SHIP-1106-carrier-playground. Mirrors ADO GFS Exelot Integration main b21a47d (prod GKE exelot.gfsdeliver.com). Mirrored prod bugs: GRAM x1000, contactName from address.Name, every failure a 599 with no 401 retry, parcel created then 500 without labelSpecification, invoice counter returns the pre-increment value, ApiKy URL read from process.sourceMapsEnabled (always the real ApiKy). Also fixed metaData shape in the merged BJS and FedEx mocks (sources spread Ajv's array into an object). #13 restored a smoke helper the merge dropped and type-checks scripts/ in CI. Smoke 33/33 across eleven names.

PR: ilg-merak/carrier-playground#12
PR: ilg-merak/carrier-playground#13

## 2026-11-06 — Add a mock OCS proxy at ocs.mocks.merak.freightops.dev

Add a mock OCS proxy at ocs.mocks.merak.freightops.dev

Ship: SHIP-1106-carrier-playground. Mirrors ADO GFS Hybrid Services and Carrier Integrations/ocs-proxy main 29eeaa6 (= prod image prod-57357, ADO build 57357; prod GKE ocs.gfsdeliver.com). Mirrored prod bugs: every OCS rejection a 599, GRAM weight x1000, contactName from address.Name, VAT/EORI never sent, multi-page PNG keeps the last page, one shared OCS account, schema metaData spread into an object. Review fixed a log-safety test gap and the metaData shape.

PR: ilg-merak/carrier-playground#11

## 2026-11-06 — Add a mock InPost proxy at inpost.mocks.merak.freightops.dev

Add a mock InPost proxy at inpost.mocks.merak.freightops.dev

Ship: SHIP-1106-carrier-playground. Mirrors GitHub gfs-hybrid-services/inpost-proxy (prod Cloud Run, inpost.gfsdeliver.com) with its prod settings. Prod logging risks confirmed in source: LOG_CARRIER_PAYLOAD=true (TEMPORARY) logs full payloads to Datadog; the caller's ApiKy key on rejection; InPost Basic Authorization header on token failure. The mock logs none. Smoke green, Datadog clean. Smoke's InPost no-key check lost in merge, restored in the next PR.

PR: ilg-merak/carrier-playground#10

## 2026-11-06 — Add a mock BJS proxy at bjs.mocks.merak.freightops.dev

Add a mock BJS proxy at bjs.mocks.merak.freightops.dev

Ship: SHIP-1106-carrier-playground. Mirrors ADO GFS Hybrid Services and Carrier Integrations/bjs-proxy (prod GKE, bjs.gfsdeliver.com), not the GitHub copy (bjs-proxy.gfsdeliver.com, ~no traffic). Mirrored prod bugs: absent fields sent as "undefined", every BJS failure a 500, label format ignored, labels paired by position, account taken from the request. Mock BJS form limit raised to 2mb. Smoke green, Datadog clean.

PR: ilg-merak/carrier-playground#9

## 2026-11-06 — Add a mock Amazon Logistics proxy at amazon.mocks.merak.freightops.dev

Add a mock Amazon Logistics proxy at amazon.mocks.merak.freightops.dev

Ship: SHIP-1106-carrier-playground. apps/amazon-logistics-proxy mirrors ADO GFS Amazon Logistics Integration/gfs-amazon-logistics-proxy (prod: amazon-logistics-proxy on GKE, amazon.gfsdeliver.com): labels, the tracking route connectors-amazon polls, cancel, multi-company creds, IS_SECURED. Auth nuance: tracking token from the URL company but signed with the GFS record's AWS keys, which only this proxy holds. Deployed into the existing mock-amazon service. Mirrored likely prod bugs: notes -> 200 {}, PDF refused (no DPIs), -SIG refused. Smoke 19/19 across seven names, Datadog clean.

PR: ilg-merak/carrier-playground#8

## 2026-11-06 — Reposition the Amazon mock as the SFP proxy; GFS Datadog only

Reposition the Amazon mock as the SFP proxy; GFS Datadog only

Ship: SHIP-1106-carrier-playground. GitHub gfs-hybrid-services/amazon-proxy is the SFP proxy (new-amazon-prod.gfsdeliver.com), so apps/amazon-proxy -> apps/amazon-sfp-proxy with its prod settings (multi-company, SFP, Windsor), infra mock-amazonsfp, name amazon-sfp.mocks.merak.freightops.dev. ILG Datadog dual-ship removed from every mock (GFS org only). The edge switch failed: the platform networking/load-balancer module deletes a removed service's backend/cert before detaching them from the URL map/HTTPS proxy (resourceInUseByAnotherResource, repeats on retry). PR #7 kept the amazon name and the mock-amazon service for the Amazon Logistics mock instead (adds/updates only), and dropped the teardown job. Smoke 16/16 through all names.

PR: ilg-merak/carrier-playground#6
PR: ilg-merak/carrier-playground#7

## 2026-11-06 — Add a mock Amazon Logistics proxy at amazon.mocks.merak.freightops.dev

Add a mock Amazon Logistics proxy at amazon.mocks.merak.freightops.dev

Ship: SHIP-1106-carrier-playground. Prod is amazon-logistics-proxy on the prod GKE cluster (ADO GFS Cluster Configurations/prod-uk1-primary-cluster, image gfs-amazon-logistics-proxy; source in ADO project GFS Amazon Logistics Integration, not readable by the ADO MCP identity yet). Built from the GitHub modernised copy gfs-hybrid-services/amazon-proxy (same config files, same multi-company tracking route connectors-amazon polls), run as prod does (ENABLE_MULTICOMPANY=1). Prod config holds real addresses/contact: none copied. Deployed 5737fee, smoke 16/16 through all six names. Owed: diff against the prod source once access exists.

PR: ilg-merak/carrier-playground#5

## 2026-11-06 — Add a mock DPD Europe proxy at dpdeu.mocks.merak.freightops.dev

Add a mock DPD Europe proxy at dpdeu.mocks.merak.freightops.dev

Ship: SHIP-1106-carrier-playground. apps/dpd-europe-proxy mirrors ADO GFS DPD-Europe Integration/dpd-europe-proxy (SOAP to DPD DE + NL, ApiKy, fixtures for Mongo/KMS, token retry, label splitting); mock DPD SOAP in mock-upstreams; mock-dpdeu IaC; on mock-edge. Likely cause of prod's all-calls-fail-validation: the validator rejects phone numbers without a leading + (Selector sends national format), nulls, empty addressLine2, KG/CM units; KG weights also reach DPD with float noise. Self-review: lockfile blocker fixed, route order, total parcel cap, log test. Deployed 8eb6850, smoke 16/16 through all six names.

PR: ilg-merak/carrier-playground#4

## 2026-11-06 — Add a mock FedEx proxy at fedex.mocks.merak.freightops.dev

Add a mock FedEx proxy at fedex.mocks.merak.freightops.dev

Ship: SHIP-1106-carrier-playground. apps/fedex-proxy mirrors gfs-hybrid-services/fedex-proxy (createShipment, cancelShipment; openapi-backend validation, ApiKy, customers/services fixtures, mapping incl. dimension rounding and customerReferences); mock FedEx OAuth + Ship in mock-upstreams; iac/projects/mock-fedex; added to mock-edge. Self-review: no blockers (line-for-line port); clamped PNG dpi, hasOwn stock lookup, log-safety test. Deployed fee2c49, smoke 10/10 through all four names, Datadog clean. Public names attract CT-log scanners within minutes (400s, harmless).

PR: ilg-merak/carrier-playground#3

## 2026-11-06 — Serve the mock proxies at <carrier>.mocks.merak.freightops.dev

Serve the mock proxies at <carrier>.mocks.merak.freightops.dev

Ship: SHIP-1106-carrier-playground. New iac/projects/mock-edge: one global HTTPS LB (platform networking/load-balancer module, managed cert per name) plus A records in ilg-platform core-infra's dev zone (ilg-merak's deploy SA already has project-scoped dnsRecordWriter). dns_domain per env (freightops.dev dev). mock-upstreams stays private. Applied 19, certs ACTIVE in ~8 min, smoke green through the names. core-infra's ownership comment (only *.delivery.<domain>) not updated: the push to ilg-platform/core-infra was blocked by the permission classifier.

PR: ilg-merak/carrier-playground#2

## 2026-11-06 — Ship mock carrier proxies to ilg-merak dev

Ship mock carrier proxies to ilg-merak dev

Ship: SHIP-1106-carrier-playground. Self-review fixed a UPS-mock crash on non-WinAnsi label text (makeLabelPdf now substitutes; async UPS handlers pass errors to next()), a body-fragment log leak in ups-proxy, the unbounded /__calls recorder and a prefix-match on the upstream ID-token origin. CI installs now authenticate via setup-node registry-url (the npm_config_ env-var form got a 401 on the runner). Merged as ab7149c; deploy-dev applied 2+4+4+4 resources, smoke green on dev, Datadog shows no keys or bodies.

PR: ilg-merak/carrier-playground#1

## 2026-11-05 — Build mock Royal Mail, UPS and Coll8 carrier proxies with dev IaC

Build mock Royal Mail, UPS and Coll8 carrier proxies with dev IaC

New repo ilg-merak/carrier-playground: mock copies of the three busiest carrier proxies (same contracts, ApiKy auth, lookups and logic; every upstream mocked by apps/mock-upstreams; all data fake), Cloud Run IaC for ilg-merak dev (mock-*-cp-dev, state carrier-playground/mock-*), golden image, observability SDK + dd-trace, deploy and PR-plan workflows. 374 tests, local docker smoke passed. Not yet deployed.

PR: ilg-merak/carrier-playground#1
