---
tags: [handover, research-copy, ecm, tracking]
date: 2026-11-10
tldr: "Research copy: usage verdict for each of the 70 ECM Terraform Pub/Sub topics, with producers, consumers and evidence from code and manifests (2026-11-10)."
status: research-copy
---
This is a research copy, 2026-11-10, of the findings file `topic-usage-map.md`, kept in the vault so it can be found and cited. The synthesis is [[Systems/ecm/tracking]]. The published page is [[Handovers/2026-11-09-merak-replacement-pages.page7-ecm-topics]]. Where this file and [[Handovers/2026-11-09-merak-replacement-pages.tracking-topic-catalogue]] differ, this file is the later reading. Nothing was edited in Confluence, a repo or Firebird.

# ECM Pub/Sub topic usage map

Researched 2026-11-10, read-only. Built for Harry's Merak research so it can be referenced from the orient vault. Nothing was edited in any repo, Confluence, the vault, Jira or Slack. No GCP, Datadog or credential access was used. The earlier lead (tracking-events-findings.md) was treated as a lead and re-derived; where this file disagrees with it, section C6 says so.

## 0. How to read this file

Verdict key (as briefed):
- **LIVE**: a publisher and a consumer both exist in code and are deployed in the manifests (or, for infrastructure feeds, in Terraform).
- **PUBLISH-ONLY**: nothing consumes it.
- **CONSUME-ONLY**: nothing in any repo I could read publishes it.
- **ORPHAN**: neither end is live in code, manifests or Terraform.
- **UNDEPLOYED**: code exists but the manifest is absent, commented out, or at zero replicas.
- **UNKNOWN**: an end sits outside what I could read (on-prem, Cloud Run outside the cluster repo, code not in any repo).

Confidence: H = both ends read by me in code or manifest; M = one end read, the other inferred from a matching env var or name; L = mostly inferred or the live host is not checkable from here. CONFIRMED = read by an agent or me this session. STATED = a doc, comment, README or `agents.md` says it. UNKNOWN = nothing settles it.

A topic named in a doc or env var was not counted as used until a publish or subscribe call, or a Terraform subscription plus a running manifest, was found.

### Evidence sources and their limits

| Short name | What | Version | Limit |
|---|---|---|---|
| TF | ADO `GFS Cloud Infrastructure/gfs-ecm-prod-uk1`, root `main.tf` and every module that touches Pub/Sub | master `35b545ce8a78b2e6ed3061961db0453b2b3c4702`, read 2026-11-10 | The ADO tool returns no line numbers, so Terraform is cited by module and block name, not by line. ADO code search is not pinned to a commit and returned stale file versions, so it was used only to find paths. |
| MF | `prod-uk1-primary-cluster` `deploy/k8s/**` (local clone) | `a317dc0` (2026-11-06, shallow) | ADO master is `b7e16c7`, so the clone is behind by an unknown number of commits (likely Flux image-tag bumps). Workload set, replicas and env names are probably current; image tags may not be. There is no `kustomization.yaml`, so Flux applies every uncommented file (STATED by the manifest survey; the live cluster was not read). Manifest citations are `path:line`, relative to `deploy/k8s/`. |
| Other TF | `gfs-ecm-staging@17b324f`, `gfs-data-warehouse-uk1@fffa8ee`, `ecm-prod-uk1-iac@d4c2b47`, `ecm-staging-iac@8d5ddf1`, tracking-webhooks IaC | as listed | Staging module internals not read. dev, playground and finance-dev not enumerated. |
| Code | Local clones and ADO/GitHub reads, shas given per row | see 0.1 | Topic and subscription names are env vars in nearly all code, never literals. The join from code to Terraform is therefore through manifest env values and ConfigMap keys (the ConfigMaps are created by Terraform, not stored in the manifests repo). |
| Lead | `tracking-events-findings.md` | 2026-11-10 | Counts and Datadog volumes in it are quoted as "lead" where I use them; I did not query Datadog. |

Terraform subscription defaults (CONFIRMED, `modules/subscription`, read by three agents): pull; ack deadline 10 s; retry backoff 10 s to 600 s; dead-letter to `dead-letters.v1` after 10 delivery attempts; never expires; no filter; no ordering; no retention override; name `<topic>.<suffix>`. The module exposes only `filter`, `enable_message_ordering` and an optional BigQuery config, so none of the other settings can differ per subscription. In the tables below **D** means exactly these defaults. Only three prod subscriptions override anything (the status.v2 ones, section 36), plus a handful of hand-written subscriptions that bypass the module (listed in section C2).

### 0.1 Code and manifest provenance

| Repo | sha | Notes |
|---|---|---|
| tracking-core (ADO) | c081108 | shallow; .NET; one image, three roles |
| tracking-file-processor | e6da4bf | |
| tracking-patina-service | 8edfb3e | |
| gfs-pod | 811007e | not shallow |
| collections-service | d593a97 | |
| carrier-credentials-manager | 9851682 | |
| fenghuang-ftp-proxy | 6c5e9fa | |
| legacy-invoice-translator | d2ed426 | |
| shipment-identity-service (GitHub clone) | 7454a4e | |
| shipment-tracking-status-deriver | a3dc446 | |
| shipment-update-service | ccec388 | |
| parcel-eta-service | 5fbc9c7 | repo says dormant, retired 2026-07-27 |
| tracking-mapper | 44cfbf2 | |
| tracking-configuration-distribution-service | bbd5e74 | |
| carrier-services-directory | 33e2bec | |
| connect | 6c6d527 | |
| tracking-webhooks / royal-mail-sapient / slipway / upload-service-v2 | 9777dd4 / 3c880bf / f604bdd / ef6d145 | |
| node-modernizer (ADO, not cloned) | 2350a1d | |
| manage-queries-proxy, unmapped-scan-recorder, gfs-deadletter-register, sofia-query-categorisation | 0772650, ad49a45, 8c958b5, e657891 | ADO reads |
| Firebird Transfer Service, patina-service-2, action-manager-api | 8569227, b9af0a1, f4c7d2c | ADO reads |
| ICIS, CCIS-next, claims-service-next, CCDIS, reporting-ingestion, reporting-service, reporter, CACS (GitHub gfs-ecm) | 3d125f5, b2af452, 584d827, 6b267aa, 32be0e2, 1059e61, acb67c3, aeeace5 | GitHub head at read time; running images are `-next` builds, so the running tag may differ from the head read |
| Not found in any repo | | ccp-api, oz gateway, longmen, Scan Injector, the CS bot, the report-scheduler Go source, the Cloud Run `route-validation-import` service |

## A. Summary table (one line per topic)

Order: upstream, shipment identity, tracking spine, adjacent stores, infrastructure. Numbers refer to the detail sections in part B. "Subs" counts Terraform subscriptions in the topic's own project, with cross-project ones added as "+n". 70 topics are created by the prod Terraform (this matches the vault's figure). Topics found elsewhere are in table A2.

### A1. The 70 topics created in gfs-ecm-prod-uk1

| # | Topic | Publisher (code, deployed?) | Subs | Main consumers | Verdict | Conf |
|---|---|---|---|---|---|---|
| 1 | fb.shipments.v1 | Slipway (code real, host not in manifests); Firebird Transfer (STATED, config targets a differently named twin) | 1 | modernizer | LIVE | M |
| 2 | fb.ship_pieces.v1 | as above | 1 | modernizer | LIVE | M |
| 3 | fb.ship_pieces_hist.v1 | Firebird Transfer (STATED) | 1 | modernizer | LIVE | L |
| 4 | fb.scan_access_data.v1 | Firebird Transfer (STATED) | 1 | modernizer | LIVE | L |
| 5 | fb.customers.v1 | Firebird Transfer (STATED) | 6 | modernizer, customer-and-contract, collections-service, manage-queries-proxy, (rm range creator undeployed), (CCP, no env) | LIVE | L |
| 6 | fb.carriers.v1 | Firebird Transfer (STATED) | 2 | modernizer, carrier-services-directory | LIVE | L |
| 7 | fb.customer_sites.v1 | Firebird Transfer (STATED) | 1 | customer-and-contract | LIVE | L |
| 8 | fb.products.v1 | Firebird Transfer (STATED) | 2 | modernizer, carrier-services-directory | LIVE | L |
| 9 | fb.collections.v1 | none found | 3 | modernizer, collections-service x2 | CONSUME-ONLY | L |
| 10 | fb.cust_contracts.v1 | none found (Transfer config names `fb.customer_contracts.v1.prod`) | 3 | modernizer x2, customer-and-contract | CONSUME-ONLY | L |
| 11 | fb.cust_contract_services.v1 | none found | 2 | modernizer, customer-and-contract | CONSUME-ONLY | L |
| 12 | fb.ship_comments.v1 | none found | 1 | modernizer | CONSUME-ONLY | L |
| 13 | fb.shipment_extra.v1 | none found (Transfer config joins SHIPMENT_EXTRA into the shipments message, STATED) | 1 | modernizer | CONSUME-ONLY | L |
| 14 | fb.sage_carrier_integration.v1 | none found | 1 | claims-service | CONSUME-ONLY | L |
| 15 | fb.web_users.v1 | none found | 1 | collections-service | CONSUME-ONLY | L |
| 16 | fb.queries.v1 | none found | 1 | manage-queries-proxy | CONSUME-ONLY | L |
| 17 | fb.gfsinternational.v1 | none found | 1 | international-import-service | CONSUME-ONLY | L |
| 18 | fb.carrier_aliases.v1 | Firebird Transfer (STATED) | 0 | nobody | PUBLISH-ONLY | L |
| 19 | fb.carrier_scan_codes.v1 | Firebird Transfer (STATED) | 0 | nobody | PUBLISH-ONLY | L |
| 20 | fb.shipment_shipper.v1 | Firebird Transfer (STATED) | 0 | nobody | PUBLISH-ONLY | L |
| 21 | fb.shipment_status.v1 | Firebird Transfer (STATED) | 0 | nobody | PUBLISH-ONLY | L |
| 22 | shipments.v2 | gfs-modernizer (live, 1 replica) | 1 | shipment-identity-service | LIVE | H |
| 23 | windowed-shipments-parcels | gfs-modernizer (self-loop) | 1 | gfs-modernizer | LIVE | H |
| 24 | shipment-number-updates | gfs-modernizer | 1 | shipment-identity-service | LIVE | H |
| 25 | shipments.v2.identified | shipment-identity-service (live, 3 replicas) | 17 (+2 push) | 15 running consumers, 2 with no running workload (section 25) | LIVE | H |
| 26 | shipment-number-updates.identified | shipment-identity-service | 3 | CCIS, ICIS, reporting-ingestion | LIVE | H |
| 27 | tracking-events.v2 | gfs-modernizer (env wired, code path present) | 0 | nobody | PUBLISH-ONLY | M |
| 28 | customers.v2 | gfs-modernizer | 0 | nobody | PUBLISH-ONLY | M |
| 29 | carrier-credentials.v1 | gfs-modernizer | 2 | carrier-credentials-manager; legacy carrier-credentials deployment | LIVE | M |
| 30 | cust-contracts.v2 | gfs-modernizer | 2 | customer-and-contract, (rm range creator undeployed) | LIVE | H |
| 31 | cust-contracts-services.v2 | gfs-modernizer | 2 | customer-and-contract, (rm range creator undeployed) | LIVE | H |
| 32 | carriers.v2 | gfs-modernizer | 1 | carrier-services-directory | LIVE | H |
| 33 | products.v2 | gfs-modernizer | 1 | carrier-services-directory | LIVE | H |
| 34 | shipment-comments.v1 | gfs-modernizer | 3 | CCIS, ICIS, reporting-ingestion | LIVE | M |
| 35 | shipment-collections.v1 | gfs-modernizer | 2 | ICIS, reporting-ingestion | LIVE | M |
| 36 | raw_tracking.v1 | tracking-core response-publisher; Royal Mail webhook; tracking-file-processor; shipment-update-service (manual delivered) | 15 (+1 cross-project BigQuery) | 8 running consumers (ccp-api by env only), 1 that drops everything, 2 BigQuery sinks, 1 Dataflow subscription of unknown state, 4 with no running workload | LIVE | H |
| 37 | legacy_tracking.v1 | tracking-core (code live, flag off in prod) | 0 | nobody | ORPHAN | H |
| 38 | tracking.v1 | nobody in current code (standalone mapper at 0 replicas, code has no publisher) | 1 | nobody (env key read by no code) | ORPHAN | H |
| 39 | tracking_configuration_notifications.v1 | tracking-config-distribution-service watcher | 9 | mapper sidecars in 7 pods | LIVE | H |
| 40 | file_tracking.v1 | fenghuang-ftp-proxy CronJob (every 20 min) | 1 | tracking-file-processor | LIVE | H |
| 41 | unmapped-tracking.v1 | mapper sidecar in the CCIS pod | 1 | unmapped-scan-recorder | LIVE | H |
| 42 | expired_window | status deriver (timer, every replica) | 3 | status deriver (self-loop) | LIVE | H |
| 43 | shipment_exception_status | status deriver | 3 | CCIS, ICIS, reporting-ingestion | LIVE | H |
| 44 | shipment_tracking_status (labelled obsolete) | status deriver | 4 | ICIS, shipment-update-service (live); CCIS and reporting-ingestion have a subscription but no live reader | LIVE | H |
| 45 | shipment_tracking_status.v2 | status deriver (ordering key shipmentId) | 3 | CCIS, reporting-ingestion (live); longmen (no workload) | LIVE | H |
| 46 | parcel-eta-update | parcel-eta-service (0 replicas) | 2 | CCIS, ICIS (env var unset, so not read) | UNDEPLOYED | H |
| 47 | legacy_tracking_events | unknown (test output of the Dataflow module) | 2 | none (BigQuery sink plus a test pull sub) | UNKNOWN | L |
| 48 | dead-letters.v1 | Pub/Sub service agent for every module subscription; modernizer in code | 1 | gfs-deadletter-register | LIVE | H |
| 49 | connect.usage_notifications.v1 | connect-gateway (3 replicas) | 1 | BigQuery subscription | LIVE | M |
| 50 | connect.hooks_usage.v1 | connect-hooks env set, but the publishing function is never imported | 0 | nobody | ORPHAN | H |
| 51 | parcel-claim-eligibility.v1 | claims-service | 2 | CCIS, ICIS | LIVE | M |
| 52 | claims.v1 | claims-service (update publishing on in two of three claims Deployments) | 3 | CCIS, ICIS, reporting-ingestion | LIVE | M |
| 53 | marked-claimable.v1 | claims-service | 1 | CCIS | LIVE | M |
| 54 | claim-credit-note.v1 | claims-service (credit-note CronJob) | 2 | CCDIS, reporting-ingestion | LIVE | M |
| 55 | claims-submitted.v1 | claims-service API | 1 | claims-service subscriber (self-loop) | LIVE | M |
| 56 | warehouse-shipment-events.v1 | warehouse-shipment-materializer (manifest commented out) | 0 in prod project (+1 BigQuery in the warehouse project) | BigQuery only | UNDEPLOYED | H |
| 57 | warehouse-tracking.v1 | warehouse tracking-materializer (manifest commented out) | 0 | nobody | UNDEPLOYED | H |
| 58 | shipment-queries | manage-queries-proxy API (2 replicas) | 4 | CCIS, ICIS, ccp-api, reporting-ingestion | LIVE | H |
| 59 | report-run | gfs-reporter-next (adhoc Deployment; scheduled CronJobs made by report-scheduler) | 1 | reporting-service | LIVE | M |
| 60 | ticket-actions | oz-gateway (env set, code not found) | 1 | longmen (no workload) | UNKNOWN | L |
| 61 | invoices_published.v1 | legacy-invoice-translator (host not in manifests) | 2 | CCDIS, reporting-ingestion | LIVE | M |
| 62 | credit_notes_published.v1 | legacy-invoice-translator | 2 | CCDIS, reporting-ingestion | LIVE | M |
| 63 | invoice_charges_published.v1 | legacy-invoice-translator | 2 | CCDIS, reporting-ingestion | LIVE | M |
| 64 | invoiced_shipments_published.v1 | CCDIS | 6 | claims, CCIS, ICIS, shipment-update-service, reporting-ingestion; longmen (no workload) | LIVE | M |
| 65 | cs.bot.logs.ticket | external CS bot (no code found) | 2 | BigQuery subscription; holding sub on the DLQ | UNKNOWN | L |
| 66 | cs.bot.logs.exception | external CS bot (no code found) | 2 | BigQuery subscription | UNKNOWN | L |
| 67 | cs.bot.logs.deadletter.ticket | Pub/Sub (dead letters of the BigQuery sub) | 1 | no reader | PUBLISH-ONLY | M |
| 68 | cs.bot.logs.deadletter.exception | Pub/Sub (dead letters of the BigQuery sub) | 1 | no reader | PUBLISH-ONLY | M |
| 69 | route_validation_import.v1 | GCS bucket notification (now in another repo) | 1 push | Cloud Run `route-validation-import` | UNKNOWN | L |
| 70 | gcp-logs.v1 | two Cloud Logging sinks | 1 push | Datadog log intake | LIVE | M |

### A2. Topics outside the prod Terraform (not in the 70)

| Topic | Project | Where defined | Publisher | Consumer | Verdict | Conf |
|---|---|---|---|---|---|---|
| scanners.consignments.V1 | gfs-ecm-staging | staging Terraform, module `doppelganger` | patina-service-2 (Dataflow, job state unknown); the k8s patina service names it but drops everything | on-prem Scan Injector (STATED, not in any repo) | UNKNOWN | L |
| scanners.deadletter.v1, scanners.deadletter.firebird4.v1, doppelganger.retries.v1 | gfs-ecm-staging | same module | Pub/Sub and the doppelganger VM (not read) | BigQuery sub / doppelganger VM (not read) | UNKNOWN | L |
| `<project>-prod-interim-tracking-topic` and its dead-letter topic (Evri) | gfs-selector-rest-prod-uk1 | tracking-webhooks IaC | Evri webhook Cloud Run | itself, by push | UNKNOWN (flag on in tfvars; deployment not checkable) | M |
| gfs-tickets | gfs-ecm | not in any Terraform I could find | Seeker action-manager-api (link STATED) | ccp-api via `gfs-tickets.customer-care-portal` | LIVE | M |
| fb.*.v1.prod (13 names) | gfs-ecm | Firebird Transfer Service repo config only | Firebird Transfer Service | none found | UNKNOWN | L |
| carrier-charges.v1, estimated-costs.v1, sales.v1, adjustments.v1, shipments-legacy.v1 | none | `modules/validator2`, module call commented out in root | none | none | ORPHAN (not created) | H |
| upload_server_`<env>`.new_file.v1 and deadletter | gfs-selector-rest-prod-uk1 | upload-service-v2 IaC | GCS notification | upload-service-v2 by push | not ECM (adjacent); not assessed | |

### A3. Counts

Computed in the final section. Subscription totals: 145 by my count in the prod project (A 38, B 76, C 31), against the vault's 144 (not recounted by the lead; I did not find the missing one). Plus 1 cross-project BigQuery subscription on `raw_tracking.v1` and 1 on `warehouse-shipment-events.v1` in `gfs-data-warehouse-uk1`, 2 push subscriptions on `shipments.v2.identified` in `gfs-selector-rest-prod-uk1`, and the staging, interim and upload-service ones listed in tf-D.

## B. Per-topic detail

Shorthand: **D** = Terraform subscription defaults (section 0). "Created" is the Terraform module and block in gfs-ecm-prod-uk1@35b545c. A publisher IAM grant in Terraform shows who may publish, not who does; each publisher below is backed by a code line unless stated. Message shapes are given where an agent read them.

### B1. Upstream feeds from the legacy Firebird estate (topics 1 to 21)

Created by `modules/transfer-service` (one `google_pubsub_topic` per topic, publisher grant to service account `transfer-service`; root `module "transfer_service"` names). Common facts for all 21:

- **Publishers.** Two candidates, neither fully matched to the deployed topic names.
  - Firebird Transfer Service (`Firebird Transfer Service@8569227`, `DataRecievers/GooglePubSubReciever.cs` `RecieveData`, publish at about :29-33 per the agent; `GetPublisher` :59-75). Its `config/appsettings.json` sets `GooglePubSub.ProjectId = "gfs-ecm"` and maps 13 tables to `fb.<x>.v1.prod` topic names, for example SHIPMENTS to `fb.shipments.v1.prod` (line 17) and CUST_CONTRACTS to `fb.customer_contracts.v1.prod`. Prod Terraform creates `fb.<x>.v1` in `gfs-ecm-prod-uk1`. No bridge was found in ADO. The deployed on-prem config is not in any repo, so which names it really publishes is UNKNOWN. The vault says Transfer feeds ECM with a 7.5 s median lag (STATED), which implies the deployed config differs from the repo's.
  - Slipway (`slipway@f604bdd code/src/services/pubsub.publisher.service.ts:21`, called from `processors/processor.ts:154-157`; prod tfvars `topic_shipments = "fb.shipments.v1"`, `topic_pieces = "fb.ship_pieces.v1"`, `pubsub_publish_project = "gfs-ecm-prod-uk1"`). It publishes the Firebird-shaped envelope `{published_timestamp, event_type, event_timestamp, data{legacy UPPER_CASE columns}, meta}`; no attributes, no ordering key. Slipway runs on Cloud Run, not in the cluster manifests, so its deployed state is not checkable here.
- **Message shape (all fb topics):** change-data-capture envelope `{event_type: INSERT|UPDATE|DELETE, data: {<TABLE>: {...}}}` (consumers read `data.CUSTOMERS`, `data.WEB_USERS`, `data.V_COLLECTIONS` by table name).
- **Ordering key:** none anywhere.

| # | Topic | Subscriptions (all D unless noted) | Subscribers and live? | Notes |
|---|---|---|---|---|
| 1 | fb.shipments.v1 | `.modernizer.v2` | gfs-modernizer: `node-modernizer@2350a1d src/pubsub/subscriber.js start()`; MF `modernizer/modernizer.yaml:65-75`, 1 replica, live | publishers: Slipway (literal match), Transfer (STATED) |
| 2 | fb.ship_pieces.v1 | `.modernizer.v2` | modernizer, live | as above |
| 3 | fb.ship_pieces_hist.v1 | `.modernizer.v2` | modernizer (env `TRACKING_EVENT_INPUT_SUBSCRIPTION`), live | Transfer config names `.prod` twin |
| 4 | fb.scan_access_data.v1 | `.modernizer.v2` | modernizer, live | Transfer catalog says "used for Doppelganger" (STATED) |
| 5 | fb.customers.v1 | `.modernizer.v2`; `.customer-and-contract-svc`; `.rm_range_creator`; `.fenghuang.collections_service`; `.customer-care-portal`; `.manage-queries-proxy` | modernizer live; customer-and-contract live (MF `customer-and-contract-service.yaml`, 2 replicas, flags on); rm range creator UNDEPLOYED (MF `jingwei/royal-mail-range-creator.yaml:1-146` fully commented); collections-service live (`CUSTOMERS_SUBSCRIPTION`); manage-queries-proxy live; ccp-api: no `PUBSUB_CUSTOMERS_*` env in `customer-care-portal/ccp-api-service.yaml`, so the CCP sub has no consumer by manifest (ccp-api code not found) | six subscriptions; two have no running reader |
| 6 | fb.carriers.v1 | `.modernizer.v2`; `.carrier-services-directory` | modernizer live; carrier-services-directory live (`ENABLE_LISTENERS` and `USE_V1_SUBSCRIPTIONS` true, MF `carrier-services-directory.yaml:78-82`; code `index.js:57-70`, `src/update-listener.js:13,28`) | |
| 7 | fb.customer_sites.v1 | `.customer-and-contract-svc` | customer-and-contract live (`CUSTOMER_SITE_SUBSCRIPTION`, CACS@aeeace5 `src/startup.ts`) | |
| 8 | fb.products.v1 | `.modernizer.v2`; `.carrier-services-directory` | both live | |
| 9 | fb.collections.v1 | `.modernizer.v2`; `.fenghuang.collections_service`; `.fenghuang.collections_service.v2` | modernizer live; collections-service: manifest sets `COLLECTIONS_SUBSCRIPTION` (`fenghuang/collections-service.yaml:228-232`) but the code never reads it (`collections-service@d593a97 index.js:67-69` reads only credentials, normalization and customers; README :42 lists it). So the `.collections_service` subscription is unread; `.v2` (normalization) is read | publisher not found |
| 10 | fb.cust_contracts.v1 | `.modernizer.cust_contracts_carrier_credentials.v2`; `.modernizer.cust_contracts.v2`; `.customer-and-contract-svc` | modernizer (two handlers) live; customer-and-contract live | Transfer config targets `fb.customer_contracts.v1.prod`, a different name |
| 11 | fb.cust_contract_services.v1 | `.modernizer.v2`; `.customer-and-contract-svc` | both live | publisher not found |
| 12 | fb.ship_comments.v1 | `.modernizer.v2` | modernizer live | publisher not found |
| 13 | fb.shipment_extra.v1 | `.modernizer.v2` | modernizer live (`SHIPMENT_EXTRA_INPUT_SUBSCRIPTION`) | Transfer config joins SHIPMENT_EXTRA into the shipments message (STATED) |
| 14 | fb.sage_carrier_integration.v1 | `.claims-service` | claims subscriber live (MF `claims-service.yaml:507,529`, 5 replicas) | publisher not found |
| 15 | fb.web_users.v1 | `.fenghuang.collections_service` | collections-service live (`CREDENTIALS_SUBSCRIPTION`, `data.WEB_USERS`) | publisher not found |
| 16 | fb.queries.v1 | `.manage-queries-proxy` | manage-queries-proxy subscriber live (MF `manage-queries-proxy.yaml:287-301`, 2 replicas) | publisher not found |
| 17 | fb.gfsinternational.v1 | `.shipments` (suffix is `shipments`, not the service name) | international-import-service live (MF `international/international-import-service.yaml:133`; image `gfs-hub-import`; code repo mapping STATED, `import-service@806c137 src/pubsub/subscriber.js`) | publisher not found |
| 18 | fb.carrier_aliases.v1 | none | nobody | no consumer module in root `main.tf`, no env anywhere |
| 19 | fb.carrier_scan_codes.v1 | none | nobody | as above |
| 20 | fb.shipment_shipper.v1 | none | nobody | as above |
| 21 | fb.shipment_status.v1 | none | nobody | as above |

Verdict reasoning for the fb group: LIVE where the consumer is running and a publisher is at least STATED (1 to 8); CONSUME-ONLY where no repo I could read publishes the topic (9 to 17); PUBLISH-ONLY where Transfer's config lists the table but no consumer exists (18 to 21). All of this hangs on the on-prem Transfer config, which I could not see; the Datadog join will decide it quickly, since each consumed topic has a handled-message count.

### B2. Modernizer outputs and shipment identity (topics 22 to 35)

gfs-modernizer (`node-modernizer@2350a1d`; image `gfs-modernizer:prod-57109`, MF `modernizer/modernizer.yaml:14-16`, 1 replica; repo-to-image mapping is STATED by name). It registers a subscription only if the matching env var is set (`src/index.js` opts block); all 15 are set. Ack on success, nack on throw (`src/message-handlers/helpers.js messageHandlerWrapper`); a subscription `error` or `close` event sets liveness false and SIGTERMs the process (`subscriber.js handleError`). Publishers (`src/pubsub/publisher.js start()/publish()`): `topic.publish(Buffer.from(JSON.stringify(data)))`, no attributes, no ordering key; failure logs and rethrows. Output topics come from env `*_OUTPUT_TOPIC` (MF `modernizer.yaml:125-200`); `DEAD_LETTER_OUTPUT_TOPIC` is a literal `projects/gfs-ecm-prod-uk1/topics/dead-letters.v1` (MF `modernizer.yaml:200-201`).

Terraform: all 12 modernizer topics are created in `modules/modernizer` with publisher grants to SA `modernizer`; the modernizer's own 15 subscriptions are the `module "<x>_subscription"` blocks there (all D, listed per topic in B1 and section 25).

| # | Topic | Publisher | Subscriptions | Subscribers | Notes |
|---|---|---|---|---|---|
| 22 | shipments.v2 | modernizer (`SHIPMENT_OUTPUT_TOPIC`) | `.fenghuang.shipment-identity-service` | shipment-identity-service (MF `fenghuang/shipment-identity-service.yaml:14`, 3 replicas) | spread of the shipment: `consignmentNumber`, `carrier{id,idV2}`, `customer`, `declaredDespatchDate`, `parcels[]`, `_legacy` (STATED, tracking-core model) |
| 23 | windowed-shipments-parcels | modernizer | `.modernizer` | modernizer | self-loop; sliding window (180 s per vault, STATED). Only the modernizer SA touches it |
| 24 | shipment-number-updates | modernizer (`SHIPMENT_NUMBER_UPDATE_TOPIC`, also used as `trackingIdTopic`) | `.fenghuang.shipment-identity-service` | shipment-identity-service | |
| 27 | tracking-events.v2 | modernizer (`TRACKING_EVENT_OUTPUT_TOPIC`, env set at MF `modernizer.yaml:135-139`) | none | none | no consumer in Terraform, manifests or code (dev has consumers: `tracking-event-broker` sampled sub, `shipment-info-service`; neither is in prod). Whether the modernizer actually publishes here in prod is UNKNOWN: the publish function exists, the call volume is not checkable. Expect quiet or not, Datadog will say |
| 28 | customers.v2 | modernizer (`CUSTOMER_OUTPUT_TOPIC`) | none | none | as above |
| 29 | carrier-credentials.v1 | modernizer (`CARRIER_CREDENTIALS_OUTPUT_TOPIC`) | `.fenghuang.carrier_credentials_manager`; `.fenghuang.carrier_credentials_manager_legacy` (created by `modules/carrier-credentials`; the legacy one uses a hand-made SA `gfscarriercredentials`) | carrier-credentials-manager subscriber (MF `fenghuang/carrier-credentials-manager-subscriber.yaml:2,119`, 1 replica; `carrier-credentials-manager@9851682 src/subscriber/index.js:8-10`, nack on validation failure and exception, ack on success; runs only when `APPLICATION_MODE=subscriber`); `gfs-carrier-credentials-deployment` (MF `carrier-credentials/carrier-cs.yml:18,78`, 3 replicas; its source repo is not identified, code comment in Terraform says legacy, to be removed) | `carrier-cs.yml` is a `.yml` file: it is applied only if Flux includes that extension (not confirmed) |
| 30 | cust-contracts.v2 | modernizer | `.customer-and-contract-svc`; `.rm_range_creator` | customer-and-contract (`USE_V2_SUBSCRIPTIONS=true`, MF `customer-and-contract-service.yaml:159`); rm range creator UNDEPLOYED | |
| 31 | cust-contracts-services.v2 | modernizer | same two | same | |
| 32 | carriers.v2 | modernizer | `.carrier-services-directory` | carrier-services-directory (`USE_V2_SUBSCRIPTIONS`, `index.js:76-86`) | |
| 33 | products.v2 | modernizer | `.carrier-services-directory` | same | |
| 34 | shipment-comments.v1 | modernizer | `.customer-consignment-information-service`; `.internal-consignment-information-service`; `.reporting-ingestion` | CCIS, ICIS, reporting-ingestion (all live by manifest) | lead measured 91,873 handled in the window |
| 35 | shipment-collections.v1 | modernizer (variable named `shipment_claim_output_topic`) | `.internal-consignment-information-service`; `.reporting-ingestion` | ICIS, reporting-ingestion | lead: 32,232 |

#### 25. shipments.v2.identified [LIVE, H]
- **Created:** `modules/shipment-identity-service`, block `shipment_output_topic`, publisher grant to SA `shipment-identity-service`.
- **Publisher:** shipment-identity-service (`shipment-identity-service@7454a4e src/publisher.js:14`, `client.topic(topic).publishMessage({ json })`; topic from env `SHIPMENT_OUTPUT_TOPIC`, `index.js:17`; MF `fenghuang/shipment-identity-service.yaml:14`, image `gfs-shipment-identity-service-next:prod-20260807082608`, 3 replicas). It reads `shipments.v2`, inserts `(consignmentNumber, carrier.id, message.id)` into Mongo, and publishes only if the insert is new; a duplicate is acked without publishing (`src/subscriber.js:33`, `message-handler.js:40,57`). Message: the original shipment plus `shipmentId` (Mongo counter) and `shipmentIdV2` (hash of carrier idV2 + consignment + despatch date). No attributes, no ordering key. A system error nacks.
- **Subscriptions (17 in gfs-ecm-prod-uk1, all D):** `.modernizer.v2`, `.fenghuang.tracking-core`, `.fenghuang.tracking-files`, `.shipment-tracking-status`, `.tracking-patina-service`, `.longmen`, `.customer-consignment-information-service`, `.internal-consignment-information-service`, `.claims-service`, `.data-warehouse`, `.shipment-update-service`, `.gfs-pod-service`, `.customer-care-portal`, `.manage-queries-proxy`, `.fenghuang.query-categorisation-service`, `.reporting-ingestion`, `.customer-credit-and-debit-information-service`.
- **Push subscriptions in project gfs-selector-rest-prod-uk1 (2):** `tracking-webhook-evri-prod-shipments-subscription` and `gfs-track-webhook-royalmail-sapient-prod-shipments-subscription`. Push to each webhook's Cloud Run service at `/events/shipments`, OIDC, ack 300 s, retry 10 to 600 s, no filter, no dead-letter (tracking-webhook-core@254827c `iac/tracking-webhook/pubsub.tf:2-31`; RM `iac/projects/gfs-hsci-tracking-webhook-royal-mail-sapient/pubsub.tf:3-32`). The carrier filter is in code only (`shipment.subscription.service.ts:95-106` keeps `carrier.idV2` in the app's list, RM hard-codes `"26"`, `handler/src/config.ts:152`), so every shipment is delivered to both. The handler always replies 204 (`pubsub.controller.ts:31-44`), so a processing failure is acked and lost.
- **Running subscribers (CONFIRMED by manifest env and code):** modernizer; tracking-core consignment-manager (`ConsignmentManager__Subscriber__Subscription`, MF `tracking-core.yaml:42`, 3 replicas, `ConsignmentSubscriberService.cs:40`, nack on invalid JSON, validation failure and exception, `PubSubMessageHandler.cs:45-73`); tracking-file-processor (MF `tracking-file-processor.yaml:13`, client-side filter `CARRIERS_OF_INTEREST` default `20,35,13,39,40,42,41`, `config.js:34-36`); status deriver (`startup.js:46`); tracking-patina-service (MF `tracking-patina-service.yaml:13`; stores shipments in Mongo even though its tracking handler drops all events); CCIS (10 replicas); ICIS (3); claims (subscriber, 5); shipment-update-service (4); gfs-pod-service subscriber (3); ccp-api (env only, code unseen); manage-queries-proxy subscriber (2); sofia subscriber (1); reporting-ingestion (5); CCDIS subscriber (3).
- **Not running:** data-warehouse (MF `data-warehouse/data-warehouse.yaml:1-222` commented out), longmen (no workload in the cluster manifests).
- Volume (lead, Datadog handled counts in the 15-day window): about 1.59M per full consumer.

#### 26. shipment-number-updates.identified [LIVE, H]
Publisher: shipment-identity-service (`src/publisher.js:14`, env `SHIPMENT_NUMBER_UPDATE_OUTPUT_TOPIC`). Subscriptions (D): `.customer-consignment-information-service`, `.internal-consignment-information-service`, `.reporting-ingestion`. Consumers live in the manifests (CCIS and ICIS `SHIPMENT_NUMBER_UPDATE_SUBSCRIPTION`, reporting-ingestion same). Lead: 3,786 handled.

### B3. Tracking spine (topics 36 to 47)

#### 36. raw_tracking.v1 [LIVE, H]
- **Created:** `modules/fenghuang-scanning-core`, block `raw_tracking` (name from root literal). Publisher grants in Terraform to three SAs: `fenghuang-scanning-core`, `tracking-ingestion-processor`, and the Dataflow rollback SA `fenghuang-dataflow-rollback`; separately `shipment-update-service` (module `shipment-update-service`, block `shipment_update_svc_tracking_publisher`). RM webhook grant sits in the webhook repo.
- **Publishers (code, 4 live):**
  1. tracking-core response-publisher: `src/Gfs.Fenghuang.Tracking.Core.Shared/Publishers/EventPublisher.cs:54`; topic from `PubSubSettings__RawTrackingTopic`, required at startup (`PubSubSettings.cs:8,13`); called at `ConnectorResponseHandler.cs:114` from gRPC `ConnectorService.cs:55`. MF `fenghuang/tracking/tracking-core.yaml:258` (3 replicas; env `PubSubSettings__RawTrackingTopic` from ConfigMap key `raw_tracking_topic`). JSON, camelCase, nulls omitted; `new PubsubMessage { Data }` only, so no attributes and no ordering key. All carrier connectors reach this path over gRPC; none of the connectors-* repos touch Pub/Sub (zero hits in `src/`).
  2. Royal Mail webhook: `tracking.service.ts:81` via `pubsub.publisher.service.ts:21`, attribute `carrierIdV2`; `pubsub_tracking_publish_enabled = true` in RM prod tfvars (`iac/env/prod.tfvars:19`). Deployed state on Cloud Run is UNKNOWN. Evri and acme webhooks have the flag false (`tracking-webhook-evri/tfvars/prod.tfvars:14`).
  3. tracking-file-processor: `src/publisher.js:9`, `publishMessage({ json })`, topic from `PUBSUB_TRACKING_TOPIC`; called from `handlers/files.js:21` and the errored-parcels CronJob (MF `tracking-file-processor.yaml:113`, hourly). No attributes.
  4. shipment-update-service mark-as-delivered: `src/api/publisher.js:9` (HTTP `PATCH /shipment/:id/mark-as-delivered`, `mark-as-delivered.js:34-46`), synthetic `GFS_DELIVERED_EVENT`; `TRACKING_OUTPUT_TOPIC` set at MF `shipment-update-service.yaml:42`. Rare (lead: about 8 a week in August).
- **Subscriptions (15 in-project, all D; plus 1 cross-project):**

| Subscription | Consumer | Running? |
|---|---|---|
| `.fenghuang.tracking-mapper` | standalone tracking-mapper | NO: MF `fenghuang/tracking/tracking-mapper.yaml:7` replicas 0, and `tracking-mapper@44cfbf2` has no code that reads a raw-tracking subscription (its only Pub/Sub sites are the config-change subscriber and the unmapped publisher) |
| `.tracking_patina_service` | k8s tracking-patina-service | running but drops everything: `CARRIERS=NONE` (MF `tracking-patina-service.yaml:81-82`); handler keeps an event only if the list is empty or contains the carrier (`tracking-patina-service@8edfb3e src/subscriber/tracking-handler.js:21`, `config.js:20`), so every event is acked and discarded |
| `.tracking-patina-service-dataflow` | patina-service-2 (Dataflow) | UNKNOWN: Terraform creates the subscription and IAM only, the Dataflow job is launched from Azure release pipelines (`patina-service-2@b9af0a1 build/azure.release.prod.pipeline.yml`) |
| `.tracking-dataflow-patina-service-bigquery` | BigQuery sink to `patina.tracking_events_rollback` | yes, no code (single `data` column, hour partitioned, `write_metadata` false) |
| `.shipment-tracking-status` | status deriver | live (MF `shipment-tracking-status-deriver.yaml:19`, 5 replicas) |
| `.parcel-eta-service` | parcel-eta-service | NO: MF `parcel-eta-service.yaml:7` replicas 0 |
| `.connect-hooks` | connect-hooks | live (MF `connect/connect-hooks.yaml:16,97`, 3 replicas; `apps/connect-hooks/index.js:71`, `maxMessages 10`) |
| `.longmen` | none in cluster | no workload; an external consumer is STATED by the vault, not verified |
| `.customer-consignment-information-service` | CCIS | live |
| `.internal-consignment-information-service` | ICIS | live |
| `.claims-service` | claims subscriber (`TRACKING_SUBSCRIPTION`, MF `claims-service.yaml:514`) | live |
| `.data-warehouse` | data-warehouse tracking-materializer | NO: manifest commented out |
| `.shipment-update-service` | shipment-update-service subscriber | live (`SUBSCRIBER_ENABLED=true`, MF `shipment-update-service.yaml:285`; subscription created only if env set and after waiting on the mapper endpoint, `src/subscriber/index.js:56`) |
| `.gfs-pod-service` | gfs-pod subscriber (BJS delivered events only, status codes BEP1910 or BEP1935, `handlers/tracking.js`) | live (MF `pod-server/pod-service.yaml:409,480`, 3 replicas); the API Deployment has `SUBSCRIBER_ENABLED=false` (:248) |
| `.customer-care-portal` | ccp-api | env set (MF `ccp-api-service.yaml:69`); code not found |
| `raw_tracking.warehouse.v1` (project gfs-data-warehouse-uk1) | BigQuery to `RawPubSubData.raw-unmapped-tracking`, `write_metadata` true | yes, no code; ack 10 s, retry 2 to 60 s, no dead-letter (`gfs-data-warehouse-uk1@fffa8ee main.tf` module `raw_tracking_stream`; internals not read) |

- **Message (tracking-core's shape, the origin):** `id` (new ObjectId, minted by each publisher), `parcel{shipmentId, shipmentIdV2, carrier, carrierV2, consignmentNumber, parcelNumber, serviceCode, contractNo, company}`, `receivedDate`, `reportedDate`, `isReportedDateLocalizable`, `statusCode` (raw carrier code), `statusDescription`, `signatory`, `location`, `depot`, `delivery`, `additionalData`, `rawData[]` (`Shared/Publishers/Models.cs`). The RM webhook adds attribute `carrierIdV2`; the other three set none, so no subscription filter on attributes could match them (and none is set).
- **Ordering key:** no. **Dedupe:** per publisher only.
- Volume (lead): about 6.29M in the window; every full consumer handled 6.2947M to 6.2970M.

#### 37. legacy_tracking.v1 [ORPHAN, H]
- **Created:** `modules/fenghuang-scanning-core`, block `legacy_tracking` (literal).
- **Publisher code:** `Shared/Publishers/EventPublisherLegacy.cs:95` (`LegacyEventPublisher.PublishAsync`), called at `ConnectorResponseHandler.cs:122`; topic `PubSubSettings__LegacyTrackingTopic` is required even when off (`PubSubSettings.cs:9,14`), set from ConfigMap key `legacy_tracking_topic` (MF `tracking-core.yaml:258` block).
- **Gate:** `LegacyPublisher__Options__default__ShouldPublishToLegacy = "false"` (MF `tracking-core.yaml:389-390`); no per-carrier override in prod. The flag is read per call with no code default; with the flag false the call is a no-op.
- **Subscriptions:** none. **Verdict basis:** publisher switched off in prod and no consumer in Terraform, manifests or code. (The dev manifest has the flag true for `dpd`, which is why the code path still matters.)

#### 38. tracking.v1 [ORPHAN, H]
- **Created:** `modules/fenghuang-tracking-mapping`, block `mapped_tracking_topic`, publisher grant to SA `fenghuang-tracking-mapping`.
- **Publisher:** none in current code. `tracking-mapper@44cfbf2` publishes only `UNMAPPED_TRACKING_EVENT_TOPIC` (`src/publisher.js:21`) and subscribes only to the config-change subscription (`index.js:42`); grep for `MAPPED_TRACKING`, `RAW_TRACKING` and `tracking.v1` in that repo finds nothing outside tests. The standalone Deployment still carries `MAPPED_TRACKING_TOPIC` and `RAW_TRACKING_SUBSCRIPTION` env names but is scaled to 0 (MF `tracking-mapper.yaml:2,7`). The repo-to-image link (`gfs-tracking-mapper-next` to `gfs-ecm/tracking-mapper`) is inferred from names.
- **Subscription:** `.fenghuang.tracking-core` (module `fenghuang-scanning-core`, block `tracking_subscription`). The manifest sets `TrackingEventManager__Subscriber__Subscription` from ConfigMap key `tracking_subscription` on the consignment-manager (MF `tracking-core.yaml:42` block; dev manifest :117-121), but a grep of tracking-core `src` finds no code that reads that key. `agents.md:16` in tracking-core claims it subscribes to `tracking.v1`; the code does not.
- Terraform, manifest and docs all still wire it; nothing in code uses it. Lead said "no consuming code, STATED"; this is now CONFIRMED from code.

#### 39. tracking_configuration_notifications.v1 [LIVE, H]
- **Created:** `modules/tracking-configuration-distrubution-service` via `modules/topic` (publisher grant `tracking-config-dist-service`).
- **Publisher:** tracking-configuration-distribution-service watcher: `src/pubsub/notifier.js:13`, `topic.publishJSON({ type: 'config_updated' })` after a successful config sync (`configuration-synchronizer.js:41`); runs when `ENABLE_WATCHER=true`, polling every 300 s by default. MF `fenghuang/tracking-configuration-distrubution-service.yaml:27`, 1 replica, topic from ConfigMap key `notifications_topic`.
- **Subscriptions (9, all D):** `.fenghuang.tracking-core`, `.shipment-tracking-status`, `.connect-hooks`, `.longmen`, `.customer-consignment-information-service`, `.internal-consignment-information-service`, `.claims-service`, `.data-warehouse`, `.shipment-update-service`.
- **Subscribers:** the tracking-mapper sidecar (`gfs-tracking-mapper-next`) in the claims subscriber, connect-hooks, CCIS, ICIS, shipment-update-service, deriver and tracking-core response-publisher pods, each with its own `TRACKING_MAPPING_CONFIG_SUBSCRIPTION` (for example MF `connect/connect-hooks.yaml:158`, `customer-consignment-information-service.yaml:396`). Code: `tracking-mapper@44cfbf2 index.js:42`; the message content is ignored and any message triggers a full config re-pull over HTTP (`src/subscribers/tracking-mapping-config.js`). `longmen` and `data-warehouse` subscriptions have no running workload.

#### 40. file_tracking.v1 [LIVE, H]
Created by `modules/tracking-file-ingestion-ftp-proxy` (`modules/topic`, grant `tracking-file-ingestion-ftp`, duplicated by an explicit grant). Publisher: `fenghuang-ftp-proxy@6c5e9fa src/publisher.js:16` (`publishMessage({ json })`), called after the file is written to FTP and GCS (`carrier-file-proc.js:34`; `carrier-processor.js:23`); MF `fenghuang/tracking/file-ingestion-ftp-proxy.yaml:118` CronJob `*/20 * * * *`. Message `{carrier, carrierIdV2, file (bucket path), createdAt}`, no attributes. Subscription `.fenghuang.tracking-files` (D). Subscriber: tracking-file-processor `src/startup.js:12` (env `PUBSUB_FILE_SUBSCRIPTION`), handler downloads the file, maps and publishes to `raw_tracking.v1`; returns silently if no mapper for the carrier (`handlers/files.js:12`). Live gate `SUBSCRIBER_ENABLED` is true (MF `tracking-file-processor.yaml:97`).

#### 41. unmapped-tracking.v1 [LIVE, H]
Created by `modules/customer-consignment-information-service` (`module "unmapped_tracking_output_topic"`, grant `customer-consignment-info-svc`). Publisher: the tracking-mapper sidecar, `src/publisher.js:21`, called from `POST /api/tracking/map` when no mapping matches (`map-tracking.js:68-74`); on only when `UNMAPPED_TRACKING_EVENT_TOPIC` is set. In prod only the CCIS subscriber pod sets it (MF `customer-consignment-information-service.yaml:290-294` on the app container and :408-412 on the sidecar; no other manifest sets it). Message `{carrier, carrierCode, carrierDescription, seenAt}`, no attributes. Subscription `.unmapped_scan_input` (created by `modules/unmapped-scan-data`, D, plain pull). Subscriber: unmapped-scan-recorder (`unmapped-scan-recorder@ad49a45 src/processor.js:20-54`, MF `fenghuang/unmapped-scan-reporter.yaml:7`, 2 replicas, inserts to BigQuery). The `agents.md` in that repo says the publisher is "tracking-mapper"; the ecm-simulator catalogue says "connectors"; the code supports the CCIS sidecar only. Lead: 11,622 handled.

#### 42 to 45. The status deriver topics [LIVE, H]
Service: shipment-tracking-status-deriver (`@a3dc446`; MF `fenghuang/shipment-tracking-status-deriver.yaml:19`, 5 replicas, `PUBSUB_ENABLED=true` :159, `API_ENABLED=false` :157). Created by `modules/shipment-tracking-status-deriver` (grants to SA `shipment-tracking-status`). Every replica runs the window timer (`window-processor.js:19`, every `WINDOW_PROCESSING_SECONDS`, default 1 s). Ack and nack come from the shared `gfs-node-pubsub-subscriber` library, whose source is in no clone: UNKNOWN (the code-github agent read its `create-subscription.ts` and found nack on throw, never dead-letter in code).

| # | Topic | Publish site | Subscriptions | Notes |
|---|---|---|---|---|
| 42 | expired_window | `src/pubsub/publisher.js:30` from `window-processor.js:19`; payload `{shipmentId}` | `.shipment-exception-status`, `.shipment-tracking-status-v2`, `.shipment-tracking-status` (all D, unfiltered, so each handler sees every message) | self-loop; lead: 4.077M per subscription |
| 43 | shipment_exception_status | `publisher.js:16`, `{shipmentId, exceptionStatus}` | CCIS, ICIS, reporting-ingestion (`.customer-consignment-information-service`, `.internal-...`, `.reporting-ingestion`) | all three read in manifests |
| 44 | shipment_tracking_status | `publisher.js:20`, `{shipmentId, trackingStatusV2}` | `.customer-consignment-information-service`, `.internal-consignment-information-service`, `.reporting-ingestion`, `.shipment-update-service` | Terraform comment says obsolete. Live readers: ICIS (MF `internal-consignment-information-service.yaml:288`) and shipment-update-service (MF `shipment-update-service.yaml` `SHIPMENT_TRACKING_STATUS_SUBSCRIPTION`; it uses `groupId` for `isPhysical` and `isDelivered`). CCIS: manifest sets `SHIPMENT_TRACKING_STATUS_SUBSCRIPTION` (:306) but the CCIS-next code reads only the V2 variable (`b2af452 src/startup.ts`; GitHub head, running tag may differ). reporting-ingestion: no v1 key in the manifest and no v1 handler |
| 45 | shipment_tracking_status.v2 | `publisher.js:24`, `{shipmentId, trackingStatusV2}`; attributes `visibilityGroup` (`ALL` or `CUSTOMER_VISIBLE`), `groupId`; **orderingKey `shipmentId`**; two publishes per shipment | `.longmen`, `.customer-consignment-information-service`, `.reporting-ingestion`, each with filter `attributes.visibilityGroup="CUSTOMER_VISIBLE"` and `enable_message_ordering = true`; otherwise D | the only topic in ECM with an ordering key and the only three subscriptions with a filter. The deriver's client is built without publisher options (agent note), so whether ordering is honoured on publish is UNKNOWN. longmen has no running workload |

#### 46. parcel-eta-update [UNDEPLOYED, H]
Created by `modules/parcel-eta-service` (`modules/topic`, grant `parcel-eta-service`). Publisher code: `parcel-eta-service@5fbc9c7 src/subscriber/tracking-handler.js:37`, `{from, to, shipmentId, shipmentIdV2, parcelNumber}`. MF `fenghuang/parcel-eta-service.yaml:2,7`: replicas 0. Terraform subscriptions `.customer-consignment-information-service` and `.internal-consignment-information-service` (D) exist, but neither manifest sets a parcel-ETA env var (grep of both files finds none), and both services' code skips a subscription whose env is unset. So both ends are idle. The raw_tracking subscription for this service is in section 36.

#### 47. legacy_tracking_events [UNKNOWN, L]
Created by `modules/tracking-dataflow-patina-service` via `modules/topic` (grant `fenghuang-dataflow-tracking`); the module comment says "outputs for testing purpose". Subscriptions: a BigQuery sub to `patina.dataflow_legacy_events` and a pull sub `.tracking-patina-service-dataflow` (both module defaults except the BigQuery retry). No code consumer. Publisher: the Dataflow job's output topic is a parameter from an Azure variable group (not readable); the Terraform comments and the README say the real output is the staging topic `scanners.consignments.V1`. Whether anything publishes here is UNKNOWN.

### B4. Dead letters, Connect, claims, warehouse, queries, reporting, tickets (topics 48 to 60)

#### 48. dead-letters.v1 [LIVE, H]
Created by `modules/deadletter`. Publishers: the Pub/Sub service agent (grant in the module) for every module subscription's dead-letter policy; the modernizer SA and the Dataflow SA hold explicit grants; modernizer also publishes in code (`DEAD_LETTER_OUTPUT_TOPIC`, MF `modernizer.yaml:200`). Subscription `deadletter-register-sub` (hand-written in `modules/gfs-deadletter-register`: ack 10 s, no expiry, no retry policy, no dead-letter policy). Subscriber: gfs-deadletter-register (`gfs-deadletter-register@8c958b5 src/subscriber.js:35-41`; MF `fenghuang/gfs-deadletter-register.yaml:13,105` literal subscription path, 1 replica). It stores to Mongo and acks on success (`:20`); on a failed validation or an exception it neither acks nor nacks. It cannot replay (STATED, vault).

#### 49. connect.usage_notifications.v1 [LIVE, M]
Created by `modules/gfs-connect` (`module "usage_notifications"`, grant `gfs-connect-gateway`). Publisher: connect-gateway `apps/connect-gateway/src/middlewares/usage-publisher.js:25`, wired at `src/server.js:43`; live only if `USAGE_TOPIC` is set (MF `connect/connect-gateway.yaml:17`, 3 replicas, value from ConfigMap `gfs-connect-gateway/usage_topic`, not verifiable). One message per HTTP request, no attributes; sink failures swallowed. Subscription `connect.usage_notifications.v1.bigquery.v1`: BigQuery, hand-written, ack 10 s, retry 2 to 60 s, no dead-letter, table `GFS_Connect.raw-connect-usage`, `write_metadata` unset. No application consumer.

#### 50. connect.hooks_usage.v1 [ORPHAN, H]
Created by `modules/gfs-connect` (`module "hooks_usage"`, grant `gfs-connect-hooks`). connect-hooks has env `USAGE_TOPIC=projects/gfs-ecm-prod-uk1/topics/connect.hooks_usage.v1` (MF `connect/connect-hooks.yaml:99`), but the only publishing function, `apps/connect-hooks/src/usage-notifier.js:7` (`createNotifier`), is never imported anywhere in the repo (grep CONFIRMED by the code agent). No subscription.

#### 51 to 55. Claims topics [LIVE, M]
Created by `modules/claims-service`, one `module "<x>_topic"` each, grant `claims-svc`. Publishers in `claims-service-next@584d827 src/publisher/index.ts` (`topic.publishJSON(message)`, no attributes, no ordering key; call sites for eligibility, marked-claimable, credit note and submitted claim were not located by the agent). Manifest env (MF `fenghuang/claims-service.yaml`): API Deployment at :34 sets `CLAIM_UPDATES_ENABLED=true` (:135), `CLAIM_UPDATE_TOPIC` (:172), `MARKED_CLAIMABLE_TOPIC` (:177), `CREDIT_NOTE_TOPIC` (:182), `CLAIM_SUBMITTED_TOPIC` (:187); the second API Deployment (:275) has it `false` (:359); the CronJob `fenghuang-claims-service-job` (`*/5 * * * *`) has it true (:793) and publishes credit notes; the subscriber Deployment (:430, 5 replicas) sets `PARCEL_CLAIM_ELIGIBILITY_TOPIC`. The link from each publish function to the Terraform topic is by matching ConfigMap key names (`claims_event_topic` to `claims.v1`, and so on): M.
- **parcel-claim-eligibility.v1:** subs `.customer-consignment-information-service`, `.internal-consignment-information-service`; both read it (`CLAIM_ELIGIBILITY_SUBSCRIPTION`). Lead: about 3.28M handled.
- **claims.v1:** payload `{ claim, date }` (`src/types.ts ClaimUpdatePublisher`), published from `src/store/baseStore.ts` when `CLAIM_UPDATES_ENABLED`. Subs: CCIS, ICIS, reporting-ingestion (`CLAIM_SUBSCRIPTION` in the first two, `CLAIMS_SUBSCRIPTION` in the third). Lead: 21,592.
- **marked-claimable.v1:** sub `.customer-consignment-information-service` only (CCIS `SHIPMENT_MARKED_CLAIMABLE_SUBSCRIPTION`, MF `customer-consignment-information-service.yaml:275`). ICIS has none. Lead: 5.
- **claim-credit-note.v1:** subs `.customer-credit-and-debit-information-service`, `.reporting-ingestion`. Exported as `credit_note_topic` and wired through the root.
- **claims-submitted.v1:** one sub, `.claims-service`, consumed by the claims subscriber itself (`CLAIM_SUBMITTED_SUBSCRIPTION`, MF `claims-service.yaml:519`); not exported in `outputs.tf`, so a private loop.
- **claims `SUBSCRIBER_ENABLED`:** false on both API Deployments (:163, :369), true only on the subscriber (:507). claims' own `TRACKING_MAPPING_SUBSCRIPTION` env (code) is not set on the app container, so claims' `tracking_mapping` subscriber is skipped; the sidecar mapper holds the `tracking_configuration_notifications.v1.claims-service` subscription (MF :665).

#### 56 and 57. warehouse-shipment-events.v1, warehouse-tracking.v1 [UNDEPLOYED, H]
Created by `modules/data-warehouse` (raw resources; grant `roles/pubsub.editor` to `data-warehouse-svcs`; AVRO schemas `shipment_schema` and `tracking_schema`, JSON encoding). Code exists in ADO repos `warehouse-shipment-materializer` (`index.js@7db2782`, publishes `topic.publish(createEncodedAvroRecord(...))` at :81, subscribes `INPUT_SUBSCRIPTION` at :57) and `warehouse-tracking-materializer` (`index.js@a59596c`, :138 and :102). The manifest (MF `data-warehouse/data-warehouse.yaml:1-222`) is commented out entirely: no replicas. The Terraform `*.data-warehouse` input subscriptions on `shipments.v2.identified`, `raw_tracking.v1` and `tracking_configuration_notifications.v1` therefore have no reader. In the warehouse project, a BigQuery subscription `shipment-events.warehouse.v2` (ack 10 s, retry 2 to 60 s, no dead-letter, `use_topic_schema` true, `gfs-data-warehouse-uk1@fffa8ee main.tf`) still consumes `warehouse-shipment-events.v1`; its only candidate publisher is not running. `warehouse-tracking.v1` has no subscription at all.

#### 58. shipment-queries [LIVE, H]
Created by `modules/manage-queries-proxy` (raw resource, grant `manage-queries-proxy`). Publisher: manage-queries-proxy `src/publisher.js:8-30` (`topic.publish(Buffer.from(JSON.stringify({shipmentId, shipmentIdV2, queryId, date, company, raisedBy, contact, category, consignmentNumber, carrierId})))`, no attributes); MF `fenghuang/manage-queries-proxy.yaml:27,154` (API, 2 replicas). Subscriptions (D): `.customer-consignment-information-service`, `.internal-consignment-information-service`, `.customer-care-portal`, `.reporting-ingestion`. Lead: 30,956 handled.

#### 59. report-run [LIVE, M]
Created by `modules/reporter` (grant `scheduled-reporter-svc`). Publisher: reporter `src/publisher.js` (`client.topic(config.pubsub.topic).publish(Buffer.from(JSON.stringify(data)))`, env `REPORTER_TOPIC`), called from `src/scheduled/handlers/claim.js`, `claimV2.js`, `shipment.js`, `shipmentV2.js` in scheduled mode (`SCHEDULED_REPORT_MODE`). Deployed as image `gfs-reporter-next:prod-20260923191843` (MF `fenghuang/reporting/adhoc-reporter.yaml:34-67`, 1 replica) and as per-report CronJobs created by the `gfs-report-scheduler-next` CronJob in namespace `gfs-reporting` (MF `reporting/report-scheduler.yaml:58,74-117`; those child CronJobs are created at run time and are not in the manifests repo). `REPORTER_TOPIC` is not in the manifests repo; it would come from the `reporter` ConfigMap named by `REPORTER_CONFIGMAP_NAME` (created by Terraform, not read). Subscription `.reporting-service` (D). Subscriber: reporting-service (`reporting-service@1059e61 src/subscriber/index.js`, `REPORTER_SUBSCRIPTION`; MF `reporting/reporting-service.yaml:152,221`, `SUBSCRIBER_ENABLED=true`, 1 replica).

#### 60. ticket-actions [UNKNOWN, L]
Created by `modules/oz/oz-gateway` (`module "ticket_actions_topic"`, grant `oz-gateway-service`). oz-gateway (images `gfs-oz-gateway-next`; MF `oz/oz-gateway-service.yaml:68,349`) has `REPORTING_TICKET_ACTIONS_TOPIC` from ConfigMap key `ticket_actions_topic`, but the oz source is not in any repo I could read, so whether it publishes is UNKNOWN. Subscription `.longmen` (D) is the only one; longmen has no workload in the cluster manifests. This is a pair of idle-looking ends, not a proven dead path.

### B5. Invoicing, infrastructure (topics 61 to 70)

#### 61 to 63. invoices_published.v1, credit_notes_published.v1, invoice_charges_published.v1 [LIVE, M]
Created by `modules/legacy-invoice-translator` (grant `legacy-invoice-translator-svc`). Publisher: legacy-invoice-translator (`legacy-invoice-translator@d2ed426 Domain/Invoices/InvoicePublisher.cs:59`, `Domain/CreditNotes/CreditNotePublisher.cs:61`, `Domain/Invoices/InvoiceChargeChargePublisher.cs:61`; clients built in `PublisherClientProvider.cs:35-48`; triggered by Firebird remote events, not Pub/Sub, `Program.cs:114-118`). Message: invoice header plus GCS file URLs (`number, customer, date, type, isSupplementary, netValue, vatValue, totalValue, details{url}, pdf{url}`), no attributes. The service does not appear in the cluster manifests (grep of `deploy/k8s` finds no translator workload), so its host is UNKNOWN; the lead's Datadog counts (1,453 invoices, 22 credit notes, STATED) show it is running somewhere. Config drift: the README names `CollectionInvoicePublishedTopic`, the code reads `InvoiceChargesPublishedTopic`. Subscriptions (D): `.customer-credit-and-debit-information-service` (each of the three) and `.reporting-ingestion` (each of the three). Both services read them (MF `customer-credit-and-debit-information-service.yaml:294-314`; `reporting-data-ingestion.yaml:127-187`).

#### 64. invoiced_shipments_published.v1 [LIVE, M]
Created by `modules/customer-credit-and-debit-information-service` (`module "invoiced_shipments_topic"`, grant `ccdis-svc`). Publisher: CCDIS. `src/publisher.js` exports `publish(topic, data)` (`client.topic(topic).publish(Buffer...)`), topic from `config.subscriber.topics.invoiceShipment` (env `INVOICE_SHIPMENT_TOPIC`, MF `customer-credit-and-debit-information-service.yaml:289`, key `invoiced_shipments_published_topic`). The GitHub agent could not find the call site and wrote "no publish found"; I confirmed that a publisher module exists, but I did not read the call site. The lead's 633,190 handled messages show it publishes in prod. Subscriptions (D): `.claims-service`, `.longmen`, `.customer-consignment-information-service`, `.internal-consignment-information-service`, `.shipment-update-service`, `.reporting-ingestion`. Message `{shipmentId, shipmentIdV2, invoiceNumber, shipmentCost, ...}` (lead). Longmen has no workload.

#### 65 to 68. cs.bot.logs.* [UNKNOWN / PUBLISH-ONLY]
Created by `modules/cs-bot-logs` (two instances). `cs.bot.logs.ticket` and `cs.bot.logs.exception` carry protobuf schemas (`cs.bot.logs.ticket`, `cs.bot.logs.exception`), JSON encoding; publisher grant to SA `cs-bot-logs-service-account`; the publishing CS bot is not in any repo I could read (UNKNOWN). Each has a BigQuery subscription (`.bq-sub`, dead-letter to its own DLQ topic after 10 attempts, tables `CS_Bot_Action_Logs.bot_logs_ticket` and `bot_logs_exception`, `use_topic_schema` true). The BigQuery write uses the default Pub/Sub service agent, whose BigQuery rights are not granted in this repo (UNKNOWN). `cs.bot.logs.deadletter.ticket` and `.exception` have a hand-written holding subscription each (no IAM, no retry policy), and no reader. The two DLQ topics are PUBLISH-ONLY by design; the service-agent publish grant on them is not in this module (UNKNOWN whether granted elsewhere).

#### 69. route_validation_import.v1 [UNKNOWN, L]
Topic, GCS-service-agent publisher grant and push subscription `route_validation_import.v1.cloud_run` (to Cloud Run service `route-validation-import`, OIDC, retry 10 to 600 s, no dead-letter, no ack setting) are in `modules/checkout/route-validation` (still in prod Terraform). The GCS bucket notification that publishes to it was moved out by a root `removed` block to `gfs-ecm/ecm-prod-uk1-iac@d4c2b47` `buckets_batch2b.tf` (that file's header says the topic stays here). The Cloud Run service is not in the cluster manifests; the k8s `checkout-route-validation-api` (MF `checkout/route-validator.yaml:33-39`) is a separate Deployment at replicas 0 with no Pub/Sub env. No source found.

#### 70. gcp-logs.v1 [LIVE, M]
Created by `modules/gcp-logging`. Publishers: two project log sinks (`dataflow-sink`, severity at least WARNING on `dataflow_step`; `cloud-function-sink`, severity at least INFO on `cloud_function`), writer identity `cloud-logs@system.gserviceaccount.com`. Subscription `gcp-logs.v1-datadog`: hand-written push to the Datadog GCP log intake (no OIDC, no dead-letter, no retry policy, ack 10 s). The push endpoint URL embeds an API key; the key is not reproduced here. No application code.

### B6. Topics outside the prod Terraform (table A2)

- **scanners.consignments.V1** (project `gfs-ecm-staging`): created by `gfs-ecm-staging@02ad01b modules/doppelganger/main.tf` (`google_pubsub_topic.consignment_output_topic`; publisher grant to the doppelganger VM service account). Subscriptions in staging: `scanners.consignments.V1.scan.injector.v2` (pull by SA `scan-injector-subscriber`, dead-letter to `scanners.deadletter.v1` after 10; the comment says it is used by the Scan Injector on the PROD environment, STATED) and `.scan.injector.firebird4` (a Firebird 4 test). Publishers: patina-service-2 Dataflow (`pipeline/sinks/pubsub.sink.go WriteLegacyEventTracking`, topic from the variable group parameter `PUBSUB_LEGACY_TRACKING_EVENTS_TOPIC`, project `PUBSUB_STAGING_PROJECT`; job state unknown) and the k8s patina service (`LEGACY_TRACKING_TOPIC` hard-coded to the staging topic, MF `tracking-patina-service.yaml:70-71`, with the comment at :68-69 "Hardcoded to the staging topic, that is the correct topic, it was never pushed to prod; prod legacy is currently run off of this topic from staging doppelganger"; `CARRIERS=NONE` drops every event). Message: legacy scanner event, attributes `ScannerUid`, `Carrier`. The Scan Injector is on-prem and in no repo. Verdict UNKNOWN.
- **Evri interim topic** and **dead-letter topic** (`gfs-selector-rest-prod-uk1`): Evri webhook publishes the raw carrier request (`interim.tracking.service.ts:94`, attributes `carrierIdV2`) and a push subscription hands it back to its own `/events/interimTracking` (ack 300 s, retry 10 to 600 s, dead-letter after 5, no filter); the dead-letter subscription is pulled by nothing (7-day retention). `pubsub_interim_tracking_enabled = true` and `pubsub_tracking_publish_enabled = false` in the Evri prod tfvars, so Evri runs in shadow and publishes nothing to `raw_tracking.v1`. The monorepo plan says the Evri cutover to the monorepo is "Not started", so the split Evri repo is the live one if any; deployed state is not checkable here.
- **gfs-tickets** (project `gfs-ecm`): no Terraform found. Subscribed from prod by `gfs-tickets.customer-care-portal` (`modules/customer-care-portal`, hand-written because `../subscription` cannot take a full topic path; needs a manual `attachSubscription` grant in gfs-ecm; ack 10 s, retry 10 to 600 s, dead-letter 10). Publisher: Seeker `action-manager-api@f4c7d2c SeekerAPI/Helpers/TicketActions.cs:338-361` and `Helpers/GooglePubSub.cs:22-45` (fire-and-forget, exceptions swallowed to the console; also a ticket-lock topic at `TicketHelpers.cs:136,173`); the topic id is configuration, so that the Seeker publishes to `gfs-tickets` specifically is STATED by a Terraform comment. Subscriber: ccp-api env `PUBSUB_TICKET_ACTIONS_SUBSCRIPTION` (MF `customer-care-portal/ccp-api-service.yaml:161-168`); code not found. The dev CCP deliberately has no subscriptions.
- **Validator2 topics** (`carrier-charges.v1`, `estimated-costs.v1`, `sales.v1`, `adjustments.v1`, `shipments-legacy.v1`): the root module call is commented out in full and nothing else instantiates the module (CONFIRMED), so Terraform no longer creates them. They may survive in GCP from an earlier apply (UNKNOWN). The catalogue agrees they do not exist in prod. No ADO or GitHub hit for `sales.v1`, `adjustments.v1`, `shipments-legacy.v1`.
- **fb.*.v1.prod** (project `gfs-ecm`): named only in the Firebird Transfer Service repo config and catalog; no Terraform or manifest references them.
- **Not mapped:** staging module-internal topics (about 37 names mirror prod), dev, playground and finance-dev stacks, and the legacy `GFS Cloud Infrastructure` repo (historical).

## C. Cross-checks

### C1. Topics by verdict

- **ORPHAN (3):** legacy_tracking.v1 (publisher off by flag), tracking.v1 (no publisher in code), connect.hooks_usage.v1 (publisher function never imported). Plus the five validator2 topics, which are not created at all (table A2).
- **UNDEPLOYED (3):** parcel-eta-update, warehouse-shipment-events.v1, warehouse-tracking.v1.
- **PUBLISH-ONLY (8):** fb.carrier_aliases.v1, fb.carrier_scan_codes.v1, fb.shipment_shipper.v1, fb.shipment_status.v1 (all depend on the unseen on-prem Transfer config); tracking-events.v2 and customers.v2 (modernizer publish path present, no consumer anywhere; actual publishing unverified); cs.bot.logs.deadletter.ticket and .exception.
- **CONSUME-ONLY (9, all low confidence):** fb.collections.v1, fb.cust_contracts.v1, fb.cust_contract_services.v1, fb.ship_comments.v1, fb.shipment_extra.v1, fb.sage_carrier_integration.v1, fb.web_users.v1, fb.queries.v1, fb.gfsinternational.v1. Each has a running consumer and no publisher in any repo I could read. These are the first topics to check against Datadog: if they carry traffic, the publisher is the on-prem Transfer Service on a newer config than the repo.
- **UNKNOWN (5):** legacy_tracking_events, ticket-actions, cs.bot.logs.ticket, cs.bot.logs.exception, route_validation_import.v1.
- **LIVE (42):** 34 with both ends read; 8 fb topics (1 to 8) where the consumer is read and the publisher is STATED or matched only by Slipway.

### C2. Terraform subscriptions with no running code consumer

| Subscription | Why no consumer | Confidence |
|---|---|---|
| `tracking.v1.fenghuang.tracking-core` | env key set (`TrackingEventManager__Subscriber__Subscription`), read by no code; topic has no publisher | H |
| `raw_tracking.v1.fenghuang.tracking-mapper` | standalone mapper at replicas 0; current code has no raw-tracking consumer | H |
| `raw_tracking.v1.parcel-eta-service` | replicas 0 | H |
| `parcel-eta-update.customer-consignment-information-service`, `parcel-eta-update.internal-consignment-information-service` | no env var in either manifest; code skips an unset subscription; publisher off | H |
| `shipment_tracking_status.reporting-ingestion` | no v1 key in the manifest, no v1 handler in code | M |
| `shipment_tracking_status.customer-consignment-information-service` | manifest sets the env (`customer-consignment-information-service.yaml:306`) but CCIS-next code (GitHub head `b2af452`) reads only the V2 variable | M (head may differ from the running tag) |
| `fb.customers.v1.customer-care-portal` | no customers env in `ccp-api-service.yaml`; ccp-api code not found | L |
| `fb.collections.v1.fenghuang.collections_service` | manifest sets `COLLECTIONS_SUBSCRIPTION` (`collections-service.yaml:228-232`); `index.js:67-69` never reads it | H |
| All three `*.data-warehouse` subscriptions (shipments.v2.identified, raw_tracking.v1, tracking_configuration_notifications.v1) | manifest commented out | H |
| All six `*.longmen` subscriptions (including `ticket-actions.longmen`, `shipment_tracking_status.v2.longmen` with filter and ordering) | no longmen workload in the cluster manifests; the vault says the data team pulls `raw_tracking.v1.longmen` (STATED, not verified; no longmen repo exists in ADO or gfs-ecm GitHub; there is no ADO project named for data services) | H for "no workload"; the external consumer is UNKNOWN |
| `fb.customers.v1.rm_range_creator`, `cust-contracts.v2.rm_range_creator`, `cust-contracts-services.v2.rm_range_creator` | `jingwei/royal-mail-range-creator.yaml` commented out in full | H |
| `raw_tracking.v1.tracking_patina_service` | consumer runs but discards every event (`CARRIERS=NONE`) | H |
| `raw_tracking.v1.tracking-patina-service-dataflow` | Dataflow job state unknown; unread backlog would accumulate (no expiry) | L |
| `legacy_tracking_events.tracking-patina-service-dataflow` (named `scan_injector_test`) and the BigQuery sub on the same topic | test purpose by comment; BigQuery sub needs no code | M |
| `cs.bot.logs.deadletter.ticket-sub`, `cs.bot.logs.deadletter.exception-sub` | holding subs, no IAM, no reader | M |
| `route_validation_import.v1.cloud_run` | push to a Cloud Run service not in the manifests; source not found | L |
| `shipments.v2.identified.longmen` | see longmen row | |

Hand-written subscriptions that bypass the shared module (so they lack its dead-letter and retry settings): `deadletter-register-sub` (no retry, no dead-letter), `connect.usage_notifications.v1.bigquery.v1` (retry 2 to 60 s, no dead-letter), `gfs-tickets.customer-care-portal` (same values written out by hand), `cs.bot.logs.*.deadletter.*-sub`, `route_validation_import.v1.cloud_run`, `gcp-logs.v1-datadog`, the Dataflow module's BigQuery subs, and the unrun validator2 subs. Cross-project: `raw_tracking.warehouse.v1` and `shipment-events.warehouse.v2` (warehouse project, retry 2 to 60 s, no dead-letter).

### C3. Consumers or publishers in code or manifests that name something Terraform does not create

| Item | Where | Finding |
|---|---|---|
| `fb.<x>.v1.prod` (13 names), project `gfs-ecm` | `Firebird Transfer Service@8569227 config/appsettings.json:17` and onward, `catalog-info.yaml:15-32` | No Terraform or manifest creates or reads these. Prod Terraform creates `fb.<x>.v1` without `.prod`, in `gfs-ecm-prod-uk1`. Eight prod fb topics (9 to 17 minus `cust_contracts`) are not in the repo's table mapping at all, and `fb.cust_contracts.v1` is `fb.customer_contracts.v1.prod` in the repo. The deployed on-prem config is the missing piece |
| `scanners.consignments.V1`, `scanners.deadletter.*`, `doppelganger.retries.v1` | prod manifest `tracking-patina-service.yaml:71`; patina-service-2 parameters | Exist only in the staging project, outside the prod Terraform; publisher IAM "granted manually" (module comment) |
| `projects/gfs-ecm/topics/gfs-tickets` | root `module "customer-care-portal"`; Seeker code | Owned by project gfs-ecm; no Terraform for it was found |
| `PUBSUB_SUBSCRIPTION`, `carrier-credentials.v1.fenghuang.carrier_credentials_manager_legacy` | `carrier-credentials/carrier-cs.yml:78` | Exists in Terraform (`modules/carrier-credentials`); the consuming repo is not identified, and the `.yml` extension may not be applied by Flux |
| `LIFECYCLE_EVENT_TOPIC_NAME`, `MAPPED_SCAN_TOPIC_NAME`, `TRACKING_SUBSCRIPTION_NAME` (gfs-lyfe); `DESPATCH_TOPIC_NAME`, `DELIVERY_TOPIC_NAME`, subscription env (carrier-sla-calculator); `tracking-events.v2.identified-shipment-info-service`, `shipments.v2.identified-shipment-info-service` (shipment-info-service) | ADO repos; dev manifests only | Not in prod Terraform or manifests (absence checked in `a317dc0`). Dev and legacy only |
| `PubSubReplicator`, `Message Sampler`, `identity-server-proxy` | ADO repos (Cloud Functions, nodejs8-era) | Deployment unknown; not in prod Terraform |
| CCIS-next `PARCEL_ETA_UPDATE_SUBSCRIPTION`, ICIS same | GitHub `b2af452`, `3d125f5` | The code names it; the manifests omit it; Terraform creates the subscription |
| claims `TRACKING_MAPPING_SUBSCRIPTION` | claims-service-next code | Not set on the app container in prod; the mapper sidecar holds the notifications subscription as `TRACKING_MAPPING_CONFIG_SUBSCRIPTION` (MF `claims-service.yaml:665`) |
| sofia `CUSTOMERS_SUBSCRIPTION` | `sofia-query-categorisation@e657891` code | Terraform creates only the shipments subscription for sofia; the manifest does not set the customers variable |
| `customer-and-contract-service` `USE_V1_SUBSCRIPTIONS` and `USE_V2_SUBSCRIPTIONS` both true | MF `customer-and-contract-service.yaml:157,159` | Both generations of topic are consumed; whether v1 `fb.*` and v2 are both still fed depends on C1 |
| invoice translator `InvoiceChargesPublishedTopic` | code vs README (`CollectionInvoicePublishedTopic`) | The env name in the deployed config is unknown; the translator is not in the cluster manifests |

### C4. Terraform topics absent from the ECM catalogue, and the reverse

Catalogue: `gfs-ecm_ecm-development@b2b67df docs/pubsub-event-catalogue.md` (secondary, STATED).
- In my findings but not the catalogue: `warehouse-shipment-events.v1`, `warehouse-tracking.v1`, `route_validation_import.v1`, `scanners.consignments.V1`, `scanners.deadletter.v1`, `scanners.deadletter.firebird4.v1`, `doppelganger.retries.v1`, `fb.shipments.v1`, `fb.ship_pieces.v1`, `fb.ship_pieces_hist.v1`, `fb.scan_access_data.v1`, `windowed-shipments-parcels`, the webhook interim topics, `upload_server_*.new_file.v1`, the cs.bot.logs topics (not checked by the agents against the catalogue), and the two warehouse-project BigQuery subscriptions.
- In the catalogue (STATED) and not in any prod Terraform: `carrier-charges.v1`, `estimated-costs.v1`, `sales.v1`, `adjustments.v1`, `shipments-legacy.v1` (validator2, not instantiated).
- `ticket-actions`, `gfs-tickets`: Terraform for `gfs-tickets` is not in any repo I found.

### C5. Count reconciliation

| Item | This map | Lead or vault |
|---|---|---|
| Topics created in gfs-ecm-prod-uk1 | 70 (A 47, B 13, C 10) | 70 (vault) |
| Subscriptions in gfs-ecm-prod-uk1 | 145 (A 38, B 76, C 31) | 144 (vault, "not recounted") |
| `raw_tracking.v1` subscriptions | 15 in-project (+1 cross-project) | 15 |
| `shipments.v2.identified` subscriptions | 17 in-project (+2 push, other project) | 17 plus 2 |
| Running `raw_tracking.v1` consumers | 8 running (connect-hooks, CCIS, ICIS, claims, shipment-update-service, deriver, gfs-pod, ccp-api by env only) plus patina (runs, drops all) plus 2 BigQuery sinks; Dataflow unknown | "10 with a running consumer" |
| Subscriptions with a filter | 3 (all `shipment_tracking_status.v2`) | same |
| Subscriptions with ordering | 3 (same) | same |
| Push subscriptions in prod project | 2 (`route_validation_import.v1.cloud_run`, `gcp-logs.v1-datadog`); none are the module's | not stated |

Cross-project push and BigQuery subscriptions consuming ECM topics: 2 push (webhooks), 1 interim push (Evri), 2 BigQuery (warehouse project).

### C6. Where this map disagrees with, or goes beyond, the lead

1. **`tracking.v1`.** The lead said the subscription is wired and docs say no consuming code (STATED). Now CONFIRMED in code: nothing reads the env key, and the producer's code no longer exists either. The lead listed it as a dormant spine topic; it is dead in all three layers.
2. **Mapped tracking publisher.** The lead said the standalone mapper (replicas 0) is the producer. The current `tracking-mapper` code has no publisher for `tracking.v1` at all; its manifest env names are residue.
3. **`unmapped-tracking.v1` publisher.** Lead: the CCIS mapper sidecar. CONFIRMED, and narrower: only the CCIS pod sets the topic env (MF `customer-consignment-information-service.yaml:290,408`). Two other documents (the ecm-simulator catalogue and `unmapped-scan-recorder/agents.md`) name connectors or the standalone mapper; the code supports neither.
4. **Patina "drops all".** Confirmed with the line: `tracking-handler.js:21` plus `CARRIERS=NONE`. It still subscribes to `shipments.v2.identified` and stores shipments.
5. **`legacy_tracking.v1` off flag.** Lead: STATED. Now CONFIRMED in the prod manifest (`tracking-core.yaml:389-390`, default false, no overrides).
6. **Running consumer counts.** `ccp-api` is counted by env only (code not found); `patina-service-2` cannot be counted (job state unknown); BigQuery sinks need no code.
7. **New beyond the lead:** the `fb.*` publisher mismatch (C3); `tracking-events.v2`, `customers.v2` consumer-free; `connect.hooks_usage.v1` dead code; `shipment_tracking_status` (v1) still has live readers (ICIS, shipment-update-service) despite its obsolete label; v1 and ETA subscriptions that the manifests and code ignore; the warehouse project's two BigQuery subscriptions; `warehouse-shipment-events.v1` has a live subscription but no live publisher; `gfs-tickets` is cross-project; `claims-submitted.v1` is a private loop; the `fb.collections.v1` subscription that the manifest sets and the code ignores.
8. **The lead's `file_tracking.v1` volume was inferred.** I did not improve on that.

### C7. Topics I expect to be quiet (for the Datadog and backlog join)

Zero or near-zero traffic expected, with the reason. If any shows traffic, the verdict above is wrong in the way noted.
- `tracking.v1`, `legacy_tracking.v1`, `parcel-eta-update`, `warehouse-tracking.v1`, `warehouse-shipment-events.v1`, `connect.hooks_usage.v1`: dead, off or undeployed. Traffic on `legacy_tracking.v1` would mean someone flipped a flag; on `warehouse-shipment-events.v1` would mean an unlisted publisher.
- `tracking-events.v2`, `customers.v2`: modernizer outputs with no consumer; the handled-message metric will not exist, so check Pub/Sub publish metrics (not collected for the ECM project per the lead) or the modernizer's own metric.
- `fb.carrier_aliases.v1`, `fb.carrier_scan_codes.v1`, `fb.shipment_shipper.v1`, `fb.shipment_status.v1`: publish-only; if the Transfer Service publishes them the backlog on any manually added subscription would grow; no handled-message metric exists.
- `marked-claimable.v1` (lead: 5 in the window), `claim-credit-note.v1`, `claims-submitted.v1`, `credit_notes_published.v1` (lead: 22): low volume by nature.
- `ticket-actions`, `cs.bot.logs.*`, `route_validation_import.v1`, `gcp-logs.v1`: no application metric is expected; use the infrastructure side.
- Consumers whose subscription backlog should be growing or flat: `parcel-eta-update.*` (nobody reads), `raw_tracking.v1.fenghuang.tracking-mapper`, `raw_tracking.v1.parcel-eta-service`, the three `*.data-warehouse`, the six `*.longmen` (unless an external consumer pulls them), the three `*.rm_range_creator`, `tracking.v1.fenghuang.tracking-core`, `shipment_tracking_status.reporting-ingestion`, `shipment_tracking_status.customer-consignment-information-service`, `fb.customers.v1.customer-care-portal`, `fb.collections.v1.fenghuang.collections_service`, `cs.bot.logs.deadletter.*-sub`. For each, a count of undelivered messages that rises over days means no reader; a count that is flat near zero means a reader exists that I did not find (especially the longmen subscriptions and the two Dataflow ones).
- High volume expected (a sanity check on the join): `raw_tracking.v1` about 6.29M, `shipments.v2.identified` about 1.59M, `expired_window` and the three status topics about 4.08M, `parcel-claim-eligibility.v1` about 3.28M (all lead figures).

### C8. What I could not verify

- **The live state of anything outside Terraform and the manifests:** no GCP access. Terraform proves topics, subscriptions and IAM, not that they were applied; a manifest proves a Deployment, not that it is healthy.
- **The on-prem Firebird Transfer Service and Scan Injector:** code for the first is in ADO but its deployed config is not; the second is in no repo. Every fb topic's publisher and `scanners.consignments.V1`'s consumer rest on this.
- **Whether the Dataflow job (patina-service-2) is running,** and what topics its variable group names.
- **Source for ccp-api, the oz gateway, longmen, the CS bot, the report-scheduler, the Cloud Run `route-validation-import`, and the invoice-translator host.** The `-next` services (CCIS, ICIS, claims, CCDIS, reporting) are GitHub repos whose heads I read; the running image tags could differ from those heads. The matching ADO repos are disabled.
- **Ack and nack on throw for the shared `gfs-node-pubsub-subscriber` library** as built into each image (the GitHub agent read a copy at `3a057e4`: nack on throw, never dead-letter in code) and for `Gfs.Core.PubSub.*` in tracking-core.
- **Whether the claims publish functions are called** (definitions read; call sites mostly not located) and the CCDIS publish call site (publisher module read, caller not).
- **Terraform line numbers:** the ADO tool returns none, so Terraform is cited by module and block name. ADO code search is not commit-pinned, so file-level shas that agents quoted from it are file commits, not heads.
- **Manifests:** the local clone is behind ADO master (`b7e16c7`). The Flux repo's local clone is also behind. That the cluster is prod-uk1 is stated in PR text, not read from the cluster. Child CronJobs created by report-scheduler at run time are not in the repo.
- **Staging module internals, dev, playground and finance-dev stacks,** and `internal-exporter` (code not read; its manifest has no Pub/Sub env).
- **The vault-versus-Terraform subscription difference** (144 against my 145): not located.
- **Slack, Jira, Confluence and the vault were not consulted** beyond reading the vault's `Systems/ecm` notes for context.
