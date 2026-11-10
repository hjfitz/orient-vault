ECM runs as choreography through Pub/Sub topics. No central orchestrator runs at run time. Terraform wires the topics and subscriptions at deploy time. tracking-core only decides which parcels are due for polling. The prod Terraform creates 70 topics and 145 subscriptions (the vault says 144, see "Not confirmed yet"). Reading code and manifests gave these verdicts: LIVE 42, CONSUME-ONLY 9, PUBLISH-ONLY 8, UNKNOWN 5, ORPHAN 3, UNDEPLOYED 3. Datadog confirmed traffic for some topics. Backlog, acknowledgements and dead letters cannot be measured, because Datadog has no Pub/Sub metrics for the ECM prod project. On-prem services were not read, so "nothing runs outside Pub/Sub" is not ruled out.

For what ECM, Firebird and Selector are, see [Shipment Journey Through ECM](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/354975746).

## How to read this page

Each topic has one verdict. The verdict comes from code, manifests and Terraform. Datadog traffic is shown beside it and does not change it.

| Verdict | Meaning | Topics |
| --- | --- | --- |
| LIVE | A publisher and a consumer both exist in code and are deployed in the manifests (for infrastructure feeds, in Terraform). | 42 |
| CONSUME-ONLY | A consumer runs. No repo the research could read publishes the topic. All 9 have low confidence. | 9 |
| PUBLISH-ONLY | Nothing consumes the topic. | 8 |
| ORPHAN | Neither end is live in code, manifests or Terraform. | 3 |
| UNDEPLOYED | Code exists, but the manifest is absent, commented out or at zero replicas. | 3 |
| UNKNOWN | One end sits outside what could be read: on-prem, a Cloud Run service outside the cluster repo, or code in no repo. | 5 |

Of the 42 LIVE topics, 8 are fb topics where the consumer is read and the publisher is STATED or matched only by Slipway.

**Confidence letter after each verdict.** H means both ends were read in code or a manifest. M means one end was read and the other inferred from an env var or a name. L means mostly inferred, or the live host cannot be checked.

**Evidence tags.** CONFIRMED means an agent read it in code, a manifest, Terraform or Datadog. STATED means a document, comment or README says it. UNKNOWN means nothing settles it.

**Traffic column.**
- The window is 2026-10-23 00:00 to 2026-11-07 00:00 UTC (15 days). "Last 24 h" means the 24 hours to 2026-11-10 12:13 UTC.
- Numbers are the services' own counters: messages a handler processed, or messages a service says it published. They are not Pub/Sub acknowledgements. A handler that drops or nacks a message still counts it.
- Where one publisher feeds many consumers, the consumer counts agree to within 0.1 to 0.2 percent. This is why a consumer count is used as a proxy for publish volume.
- "Not measured" means no Datadog metric names the topic, or the topic was not queried. It does not mean zero.
- Datadog was queried for 41 topics. Four of them are outside the prod Terraform set. The other topics were not queried, except nine seen in passing in service metric names (the rows say so).

Abbreviations used below. CCIS is the customer consignment information service. ICIS is the internal consignment information service. CCDIS is the customer credit and debit information service. ccp-api is the API of the customer care portal. longmen is a consumer with no workload in the cluster manifests. The vault states that the data team pulls from it, and that is not verified.

## The shared subscription set-up

The Terraform subscription module sets these defaults (CONFIRMED). Unless a row says otherwise, every subscription below has them.

- Pull delivery.
- Acknowledge deadline of 10 s.
- Retry backoff from 10 s to 600 s.
- Dead letter to `dead-letters.v1` after 10 delivery attempts.
- No expiry, no filter, no message ordering, no retention override.
- Name is `<topic>.<suffix>`.

The module exposes only a filter, message ordering and an optional BigQuery configuration. Nothing else can differ per subscription through the module. Only three prod subscriptions override a module setting. Hand-written subscriptions bypass the module and so lack its dead-letter and retry settings.

| Subscription | What differs from the defaults |
| --- | --- |
| The three on `shipment_tracking_status.v2` (longmen, CCIS, reporting-ingestion) | Filter `attributes.visibilityGroup="CUSTOMER_VISIBLE"` and ordering on. They are the only subscriptions with a filter or ordering. |
| Two push subscriptions on `shipments.v2.identified`, in project gfs-selector-rest-prod-uk1 (Royal Mail and Evri webhooks) | Push delivery, acknowledge deadline 300 s, retry 10 s to 600 s, no filter, no dead letter. The carrier filter is in code only, so each webhook receives every shipment. The handler always replies 204, so a processing failure is acknowledged and lost. |
| Evri interim topic subscription (same project) | Push to the Evri service itself, acknowledge deadline 300 s, retry 10 s to 600 s, dead letter after 5 attempts. |
| `deadletter-register-sub` | Hand-written. Acknowledge deadline 10 s, no retry policy, no dead letter. |
| BigQuery subscription on `connect.usage_notifications.v1` | Hand-written. Retry 2 s to 60 s, no dead letter. |
| `gfs-tickets.customer-care-portal` | Hand-written. Same values as the defaults, written out by hand. |
| BigQuery subscriptions on `cs.bot.logs.ticket` and `cs.bot.logs.exception` | Dead letter to their own dead-letter topic after 10 attempts. |
| Holding subscriptions on the two `cs.bot.logs.deadletter.*` topics | Hand-written, no IAM, no retry policy. |
| `route_validation_import.v1.cloud_run` | Push to a Cloud Run service. Retry 10 s to 600 s, no dead letter, no acknowledge setting. |
| `gcp-logs.v1-datadog` | Push to the Datadog log intake. Acknowledge deadline 10 s, no dead letter, no retry policy. |
| Two BigQuery subscriptions in the warehouse project (`raw_tracking.warehouse.v1` and `shipment-events.warehouse.v2`) | Acknowledge deadline 10 s, retry 2 s to 60 s, no dead letter. |

## How a scan reaches a customer

Terraform is the only central artefact. Each service reads a topic, does its own job, and writes or publishes its own result. The only edges outside topics are HTTP calls.

1. **A shipment becomes known.** The Firebird Transfer Service publishes Firebird table changes to the `fb.*` topics (STATED, on-prem config not read). Slipway also publishes the Firebird-shaped message to `fb.shipments.v1` and `fb.ship_pieces.v1`. gfs-modernizer reads the `fb.*` topics and publishes `shipments.v2`. It uses a sliding window of 180 s (STATED).
2. **A shipment gets an identity.** shipment-identity-service reads `shipments.v2`. It inserts the consignment number, carrier and message id into Mongo. It publishes `shipments.v2.identified` only if the insert is new. A duplicate is acknowledged without publishing. The message adds `shipmentId` and `shipmentIdV2`. Seventeen subscriptions read this topic.
3. **tracking-core learns what to track.** Its consignment-manager reads `shipments.v2.identified` and creates parcels in Mongo. It publishes nothing to a topic. Its batch-creator hands due parcels to carrier connectors over gRPC.
4. **Scans arrive on `raw_tracking.v1`.** There are four publishers. tracking-core's response-publisher publishes the carrier connectors' results. The Royal Mail webhook publishes its own scans. tracking-file-processor publishes scans from carrier files announced on `file_tracking.v1`. shipment-update-service publishes a manual "delivered" event.
5. **Mapping happens in every consumer.** `raw_tracking.v1` carries the carrier's raw code only. Each consumer calls its own tracking-mapper sidecar to map it. Config reaches the sidecars through `tracking_configuration_notifications.v1`. An unmapped code goes to `unmapped-tracking.v1`, from the CCIS sidecar only.
6. **The status deriver builds the shipment status.** It reads `raw_tracking.v1` and `shipments.v2.identified`. It stores mapped events per shipment and closes a sliding window with a timer. The timer publishes `expired_window`. Three of the deriver's own subscriptions on that topic publish `shipment_exception_status`, `shipment_tracking_status` and `shipment_tracking_status.v2`.
7. **Customer-visible stores read the statuses.** CCIS reads `shipment_tracking_status.v2` through a customer-visible filter. ICIS, shipment-update-service and reporting-ingestion read the other status topics.
8. **Customer webhooks are not on a topic.** connect-hooks reads `raw_tracking.v1`, maps the raw event again and sends an HTTP POST to the customer's hook URL. It never carries the derived status. A failed POST is logged and acknowledged, with no retry.
9. **Legacy write-back to Firebird.** patina-service-2 (a Dataflow job whose state is UNKNOWN) reads `raw_tracking.v1` and publishes `scanners.consignments.V1`, a topic in the staging project. The on-prem Scan Injector (STATED, in no repo) writes to Firebird from it. The Kubernetes tracking-patina-service reads `raw_tracking.v1` and drops every event.

**The sidecar nuance.** tracking-core's response-publisher does not call the standalone status deriver or tracking-mapper services. Its pod carries a status deriver sidecar and a mapper sidecar. It makes one synchronous HTTP call to the deriver sidecar per poll result, after publishing. The answer, DELIVERED or IN_TRANSIT, sets the parcel's state and expiry. The standalone tracking-mapper Deployment runs at 0 replicas. This HTTP call is the only edge in the spine outside a topic.

For the polling side, see [Polling Connectors](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353697880) and [Carrier Tracking and Proof of Delivery](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353206337). For the identity step, see [Shipment Identity](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/355631312). For webhooks, see [Tracking Webhook Services](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353533985).

## Topics by job

All 70 topics created by the prod Terraform appear once, in eight groups. Topic counts: A 21, B 14, C 5, D 7, E 2, F 16, G 4, H 1.

### A. Firebird feeds (fb.\*)

All 21 topics are created by the transfer-service Terraform module. Messages are change-data-capture envelopes: `{event_type: INSERT, UPDATE or DELETE, data: {<TABLE>: {...}}}`. Slipway's envelope is `{published_timestamp, event_type, event_timestamp, data (legacy UPPER_CASE columns), meta}`. There are no attributes and no ordering key anywhere in this group.

The sources name the Firebird table for only a few topics: SHIPMENTS, SHIPMENT_EXTRA, CUSTOMERS, WEB_USERS and V_COLLECTIONS. For the others, the table is taken from the topic name.

The publisher is the open question for the whole group. The Firebird Transfer Service repo config targets 13 differently named topics (`fb.<x>.v1.prod`, project gfs-ecm), while prod Terraform creates `fb.<x>.v1` in project gfs-ecm-prod-uk1. The deployed on-prem config is in no repo. See "Not confirmed yet".

| Topic | What it carries (key fields) | Producers | Consumers | Traffic (15 days) | Verdict |
| --- | --- | --- | --- | --- | --- |
| `fb.shipments.v1` | Shipment rows (SHIPMENTS), legacy UPPER_CASE columns | Slipway (code real, host not in manifests); Firebird Transfer Service (STATED, config names a `.prod` twin) | gfs-modernizer | 1,906,654 (modernizer messages of type shipment; type matched to topic by name; not publishes) | LIVE, M |
| `fb.ship_pieces.v1` | Ship piece rows | Slipway; Firebird Transfer Service (STATED) | gfs-modernizer | 790,277 (modernizer messages of type parcel; matched by name only) | LIVE, M |
| `fb.ship_pieces_hist.v1` | Ship piece history rows | Firebird Transfer Service (STATED, config names a `.prod` twin) | gfs-modernizer | Not measured | LIVE, L |
| `fb.scan_access_data.v1` | Scan access data rows. The Transfer catalogue says "used for Doppelganger" (STATED) | Firebird Transfer Service (STATED) | gfs-modernizer | Not measured | LIVE, L |
| `fb.customers.v1` | Customer rows (`data.CUSTOMERS`) | Firebird Transfer Service (STATED) | gfs-modernizer; customer-and-contract-service; collections-service; manage-queries-proxy. Six subscriptions: the Royal Mail range creator is undeployed, and the ccp-api subscription has no env var in the manifest (code not found) | 36 (customer-and-contract-service handled; topic named from the subscription name in the metric, inferred) | LIVE, L |
| `fb.carriers.v1` | Carrier rows | Firebird Transfer Service (STATED) | gfs-modernizer; carrier-services-directory | Not measured | LIVE, L |
| `fb.customer_sites.v1` | Customer site rows | Firebird Transfer Service (STATED) | customer-and-contract-service | 37 (topic named from the subscription name, inferred) | LIVE, L |
| `fb.products.v1` | Product rows | Firebird Transfer Service (STATED) | gfs-modernizer; carrier-services-directory | Not measured | LIVE, L |
| `fb.collections.v1` | Collection rows (`data.V_COLLECTIONS`) | None found | gfs-modernizer; collections-service (the manifest sets the subscription but the code never reads it, so that subscription is unread; the `.v2` one is read) | Not measured | CONSUME-ONLY, L |
| `fb.cust_contracts.v1` | Customer contract rows | None found. Transfer config names `fb.customer_contracts.v1.prod`, a different name | gfs-modernizer (two handlers); customer-and-contract-service | 420 (topic named from the subscription name, inferred) | CONSUME-ONLY, L |
| `fb.cust_contract_services.v1` | Customer contract service rows | None found | gfs-modernizer; customer-and-contract-service | 458, none in the last 24 h (topic named from the subscription name, inferred) | CONSUME-ONLY, L |
| `fb.ship_comments.v1` | Shipment comment rows | None found | gfs-modernizer | Not measured | CONSUME-ONLY, L |
| `fb.shipment_extra.v1` | SHIPMENT_EXTRA rows | None found. Transfer config joins SHIPMENT_EXTRA into the shipments message (STATED) | gfs-modernizer | 1,821 (modernizer messages of type shipment_extra) | CONSUME-ONLY, L |
| `fb.sage_carrier_integration.v1` | Sage carrier integration rows | None found | claims-service subscriber | Not measured | CONSUME-ONLY, L |
| `fb.web_users.v1` | Web user rows (`data.WEB_USERS`) | None found | collections-service | Not measured | CONSUME-ONLY, L |
| `fb.queries.v1` | Query rows | None found | manage-queries-proxy subscriber | Not measured | CONSUME-ONLY, L |
| `fb.gfsinternational.v1` | International shipment rows (named from the topic) | None found | international-import-service (subscription suffix is `shipments`) | Not measured | CONSUME-ONLY, L |
| `fb.carrier_aliases.v1` | Carrier alias rows | Firebird Transfer Service (STATED) | None | Not measured | PUBLISH-ONLY, L |
| `fb.carrier_scan_codes.v1` | Carrier scan code rows | Firebird Transfer Service (STATED) | None | Not measured | PUBLISH-ONLY, L |
| `fb.shipment_shipper.v1` | Shipment shipper rows | Firebird Transfer Service (STATED) | None | Not measured | PUBLISH-ONLY, L |
| `fb.shipment_status.v1` | Shipment status rows | Firebird Transfer Service (STATED) | None | Not measured | PUBLISH-ONLY, L |

### B. Shipment creation and identity (gfs-modernizer and shipment-identity-service outputs)

gfs-modernizer registers a subscription only when its env var is set, and all 15 are set. It acknowledges on success and nacks on a throw. Its publishers send JSON with no attributes and no ordering key. shipment-identity-service publishes with no attributes and no ordering key.

| Topic | What it carries (key fields) | Producers | Consumers | Traffic (15 days) | Verdict |
| --- | --- | --- | --- | --- | --- |
| `shipments.v2` | The shipment: `consignmentNumber`, `carrier{id,idV2}`, `customer`, `declaredDespatchDate`, `parcels[]`, `_legacy` (STATED) | gfs-modernizer (1 replica) | shipment-identity-service (3 replicas) | 1,585,447 (identity service handled) | LIVE, H |
| `windowed-shipments-parcels` | `[??]`. A sliding window of 180 s (STATED) | gfs-modernizer | gfs-modernizer (self-loop) | 1,585,459 (modernizer messages of type windowed_shipment_parcels) | LIVE, H |
| `shipment-number-updates` | A shipment number update `[??]` | gfs-modernizer | shipment-identity-service | 3,786 | LIVE, H |
| `shipments.v2.identified` | The original shipment plus `shipmentId` (Mongo counter) and `shipmentIdV2` (hash of carrier idV2, consignment and despatch date) | shipment-identity-service | 17 subscriptions, 15 with a running consumer: gfs-modernizer, tracking-core, tracking-file-processor, status deriver, tracking-patina-service (stores shipments), CCIS, ICIS, claims-service, shipment-update-service, gfs-pod-service, ccp-api, manage-queries-proxy, query-categorisation service, reporting-ingestion, CCDIS. No running consumer: data-warehouse (manifest commented out) and longmen. Plus 2 push subscriptions (Royal Mail and Evri webhooks) | 1,585,439 (identity service published; every full consumer within 0.1 to 0.2 percent). ccp-api has outcome counters, so it runs even though its code was not found | LIVE, H |
| `shipment-number-updates.identified` | The shipment number update after identity (payload STATED) | shipment-identity-service | CCIS; ICIS; reporting-ingestion | 3,786 | LIVE, H |
| `tracking-events.v2` | `[??]` | gfs-modernizer (env set, publish function present; whether it publishes in prod is UNKNOWN) | None | Not measured | PUBLISH-ONLY, M |
| `customers.v2` | `[??]` | gfs-modernizer (same caveat) | None | Not measured | PUBLISH-ONLY, M |
| `carrier-credentials.v1` | Carrier credential records (shape not read) | gfs-modernizer | carrier-credentials-manager subscriber (1 replica, nacks on a validation failure or an exception); a legacy carrier-credentials deployment (3 replicas, source repo not identified, Terraform comment says legacy and to be removed) | Not measured | LIVE, M |
| `cust-contracts.v2` | Customer contract records (shape not read) | gfs-modernizer | customer-and-contract-service; the Royal Mail range creator (undeployed) | 420 (metric names it `cust_contracts.v2`; inferred) | LIVE, H |
| `cust-contracts-services.v2` | Customer contract service records (shape not read) | gfs-modernizer | customer-and-contract-service; the Royal Mail range creator (undeployed) | 458, none in the last 24 h (metric names it `cust_contracts_services.v2`; inferred) | LIVE, H |
| `carriers.v2` | Carrier records (shape not read) | gfs-modernizer | carrier-services-directory | Not measured | LIVE, H |
| `products.v2` | Product records (shape not read) | gfs-modernizer | carrier-services-directory | Not measured | LIVE, H |
| `shipment-comments.v1` | Shipment comments (shape not read) | gfs-modernizer | CCIS; ICIS; reporting-ingestion | 91,873 (CCIS handled) | LIVE, M |
| `shipment-collections.v1` | Shipment collections (shape not read) | gfs-modernizer (the Terraform variable is named `shipment_claim_output_topic`) | ICIS; reporting-ingestion | 32,232 (ICIS handled) | LIVE, M |

### C. Carrier scans in

The raw scan topic, its file feed and the dormant tracking topics.

| Topic | What it carries (key fields) | Producers | Consumers | Traffic (15 days) | Verdict |
| --- | --- | --- | --- | --- | --- |
| `raw_tracking.v1` | One scan as JSON, camelCase, nulls omitted: `id`, `receivedDate`, `reportedDate`, `isReportedDateLocalizable`, `statusCode` (the carrier's raw code), `statusDescription`, `parcel{shipmentId, shipmentIdV2, carrier, carrierV2, consignmentNumber, parcelNumber, serviceCode, contractNo, company}`, `signatory`, `location`, `depot`, `delivery`, `additionalData`, `rawData[]`. No ordering key. The Royal Mail webhook adds attribute `carrierIdV2`. The other three publishers set no attributes | 4: tracking-core response-publisher; Royal Mail webhook; tracking-file-processor; shipment-update-service (manual delivered event) | 15 subscriptions in the prod project. Running (8): status deriver, connect-hooks, CCIS, ICIS, claims-service, shipment-update-service, gfs-pod-service, ccp-api (by env var and Datadog counters). Runs but drops every event: Kubernetes tracking-patina-service. Dataflow patina-service-2 (state UNKNOWN). A BigQuery sink to a rollback table. No running workload (4): tracking-mapper, parcel-eta-service, data-warehouse, longmen. One more BigQuery sink sits in the warehouse project | 6,294,672 (CCIS handled; every full consumer 6,294,668 to 6,297,029; last 24 h 598,367) | LIVE, H |
| `file_tracking.v1` | `{carrier, carrierIdV2, file (bucket path), createdAt}`. No attributes | fenghuang-ftp-proxy (CronJob every 20 min) | tracking-file-processor | 3,963 (ftp proxy published; the metric's topic tag is the literal `_object_object`, so the attribution is inferred) | LIVE, H |
| `legacy_tracking.v1` | tracking-core's own legacy event: the whole event history of a parcel per message (CONFIRMED shape) | tracking-core (publisher code present, switched off in prod) | None | Not measured | ORPHAN, H |
| `tracking.v1` | A mapped tracking event (STATED). No code publishes it | None in current code | None. A subscription for tracking-core exists, and no code reads its env key | Not measured | ORPHAN, H |
| `legacy_tracking_events` | Legacy scanner events. Terraform calls it an output "for testing purpose" | UNKNOWN (the Dataflow job's output topic is a parameter that was not readable) | A BigQuery subscription and a test pull subscription. No code consumer | Not measured | UNKNOWN, L |

`raw_tracking.v1` publishers in the window, from Datadog proxies:
- tracking-core response-publisher: 6,011,685 new and updated events.
- Royal Mail webhook: 218,082 published.
- tracking-file-processor: 54,125 published, plus 7,384 on a separate errored-parcels metric.
- shipment-update-service: 4, with no topic tag, so not confirmed as `raw_tracking.v1`.

The first three sum to 6,283,896.

### D. Mapping, status and exceptions

| Topic | What it carries (key fields) | Producers | Consumers | Traffic (15 days) | Verdict |
| --- | --- | --- | --- | --- | --- |
| `tracking_configuration_notifications.v1` | `{type: "config_updated"}`. The content is ignored. Any message makes the sidecar re-pull the full mapping config over HTTP | tracking-configuration-distribution-service watcher (publishes after a successful config sync; polls every 300 s by default; 1 replica) | 9 subscriptions. Mapper sidecars in tracking-core, status deriver, connect-hooks, CCIS, ICIS, claims-service and shipment-update-service pods. longmen and data-warehouse have no workload | 3 or 4 handled per sidecar, none in the last 24 h. No publisher metric | LIVE, H |
| `unmapped-tracking.v1` | `{carrier, carrierCode, carrierDescription, seenAt}`. No attributes | The mapper sidecar in the CCIS pod. Only that pod sets the topic env var | unmapped-scan-recorder (2 replicas, writes to BigQuery) | 11,622 | LIVE, H |
| `expired_window` | `{shipmentId}` | Status deriver (a window timer on every replica) | Status deriver (three of its own subscriptions) | 4,077,022 to 4,077,026 per subscription | LIVE, H |
| `shipment_exception_status` | `{shipmentId, exceptionStatus}`, a red, amber or green status. Published on every window expiry, not only on change | Status deriver | CCIS; ICIS; reporting-ingestion | 4,077,022 (CCIS handled) | LIVE, H |
| `shipment_tracking_status` | `{shipmentId, trackingStatusV2}`. Terraform labels it obsolete | Status deriver | ICIS and shipment-update-service read it. CCIS and reporting-ingestion have a subscription but no live reader | 4,077,200 (ICIS handled) | LIVE, H |
| `shipment_tracking_status.v2` | `{shipmentId, trackingStatusV2}`. Attributes `visibilityGroup` (`ALL` or `CUSTOMER_VISIBLE`) and `groupId`. Ordering key `shipmentId`. Two publishes per shipment | Status deriver. Whether ordering is honoured on publish is UNKNOWN | CCIS and reporting-ingestion (filter `CUSTOMER_VISIBLE`, ordering on); longmen (same filter, no workload) | 4,077,032 (CCIS handled) | LIVE, H |
| `parcel-eta-update` | `{from, to, shipmentId, shipmentIdV2, parcelNumber}` (from code) | parcel-eta-service (0 replicas) | CCIS and ICIS have subscriptions, but neither manifest sets the env var, so neither reads it | Not measured | UNDEPLOYED, H |

### E. Customers and webhooks

Customer webhooks are HTTP calls from connect-hooks and use no topic. Only the Connect usage topics are here.

| Topic | What it carries (key fields) | Producers | Consumers | Traffic (15 days) | Verdict |
| --- | --- | --- | --- | --- | --- |
| `connect.usage_notifications.v1` | One message per HTTP request to connect-gateway. No attributes. Fields not read `[??]` | connect-gateway (3 replicas). Live only if its usage-topic setting is set, and the value is not verifiable | A BigQuery subscription into a usage table. No application consumer | Not measured | LIVE, M |
| `connect.hooks_usage.v1` | Nothing is published | None. connect-hooks has the env var set, but the only publishing function is never imported | None | Not measured | ORPHAN, H |

### F. Claims, queries, tickets, invoices, reports and bot logs

| Topic | What it carries (key fields) | Producers | Consumers | Traffic (15 days) | Verdict |
| --- | --- | --- | --- | --- | --- |
| `parcel-claim-eligibility.v1` | Claim eligibility (shape not read) | claims-service | CCIS; ICIS | 3,279,568 (CCIS handled) | LIVE, M |
| `claims.v1` | `{claim, date}` | claims-service (update publishing is on in two of its three Deployments) | CCIS; ICIS; reporting-ingestion | 21,592 | LIVE, M |
| `marked-claimable.v1` | A shipment marked claimable (shape not read) | claims-service | CCIS | 5 (2 in the last 24 h) | LIVE, M |
| `claim-credit-note.v1` | A claim credit note (shape not read) | claims-service (credit-note CronJob, every 5 min) | CCDIS; reporting-ingestion | 1,006, none in the last 24 h (metric alias `claimCreditNotes`, topic name unknown; same count as `claims-submitted.v1`, probably the same flow; inferred) | LIVE, M |
| `claims-submitted.v1` | A submitted claim (shape not read) | claims-service API | claims-service subscriber (a private loop; not exported in Terraform outputs) | 1,006, none in the last 24 h (topic name inferred from a dev subscription) | LIVE, M |
| `shipment-queries` | `{shipmentId, shipmentIdV2, queryId, date, company, raisedBy, contact, category, consignmentNumber, carrierId}`. No attributes | manage-queries-proxy (API, 2 replicas, and subscriber) | CCIS; ICIS; ccp-api (env var only); reporting-ingestion | 30,956 (API 6,101 plus subscriber 24,855 published) | LIVE, H |
| `report-run` | A report run request `[??]` | gfs-reporter-next (an ad hoc Deployment, and scheduled CronJobs created by the report-scheduler) | reporting-service (1 replica) | Not measured | LIVE, M |
| `ticket-actions` | `[??]` | oz-gateway (env var set, code not found; whether it publishes is UNKNOWN) | longmen subscription only, no workload | Not measured | UNKNOWN, L |
| `invoices_published.v1` | Invoice header plus file URLs: `number`, `customer`, `date`, `type`, `isSupplementary`, `netValue`, `vatValue`, `totalValue`, `details{url}`, `pdf{url}`. No attributes | legacy-invoice-translator (host not in the cluster manifests; triggered by Firebird remote events, not Pub/Sub) | CCDIS; reporting-ingestion | 1,441 published (consumers read 1,452 to 1,453) | LIVE, M |
| `credit_notes_published.v1` | Credit note header plus file URLs (the map describes one shape for the three invoice topics) | legacy-invoice-translator | CCDIS; reporting-ingestion | 22 | LIVE, M |
| `invoice_charges_published.v1` | Invoice charge header plus file URLs (same note) | legacy-invoice-translator | CCDIS; reporting-ingestion | 3,352, none in the last 24 h | LIVE, M |
| `invoiced_shipments_published.v1` | `{shipmentId, shipmentIdV2, invoiceNumber, shipmentCost, ...}` | CCDIS (the publisher module was read, the call site was not) | claims-service; CCIS; ICIS; shipment-update-service; reporting-ingestion; longmen (no workload) | 633,190 (685 in the last 24 h) | LIVE, M |
| `cs.bot.logs.ticket` | Bot ticket log records (protobuf schema, JSON encoding) | The external bot the sources call the CS bot (no code found) | A BigQuery subscription into a ticket log table | Not measured | UNKNOWN, L |
| `cs.bot.logs.exception` | Bot exception log records (protobuf schema, JSON encoding) | The CS bot (no code found) | A BigQuery subscription into an exception log table | Not measured | UNKNOWN, L |
| `cs.bot.logs.deadletter.ticket` | Dead letters of the ticket BigQuery subscription | Pub/Sub (dead-letter policy). The service-agent publish grant is not in this module, and whether it is granted elsewhere is UNKNOWN | None. A hand-written holding subscription exists | Not measured | PUBLISH-ONLY, M |
| `cs.bot.logs.deadletter.exception` | Dead letters of the exception BigQuery subscription | Pub/Sub (same caveat) | None. A hand-written holding subscription exists | Not measured | PUBLISH-ONLY, M |

POD has no topic. gfs-pod-service reads `shipments.v2.identified` and `raw_tracking.v1` for its own cache and publishes nothing.

### G. Warehouse and operations

| Topic | What it carries (key fields) | Producers | Consumers | Traffic (15 days) | Verdict |
| --- | --- | --- | --- | --- | --- |
| `warehouse-shipment-events.v1` | Shipment events under an AVRO schema, JSON encoding | warehouse-shipment-materializer (manifest commented out) | No subscription in the prod project. A BigQuery subscription in the warehouse project still reads it | Not measured | UNDEPLOYED, H |
| `warehouse-tracking.v1` | Tracking events under an AVRO schema. `GFS_*` and `CARRIER_*` scan fields (STATED) | The warehouse tracking-materializer (manifest commented out) | None. No subscription at all | Not measured | UNDEPLOYED, H |
| `route_validation_import.v1` | `[??]` | A bucket notification, now defined in another repo. The topic stays in the prod Terraform | The Cloud Run service route-validation-import, by push. It is not in the cluster manifests and its source was not found | Not measured | UNKNOWN, L |
| `gcp-logs.v1` | Log entries from two project log sinks: Dataflow steps at WARNING or above, and cloud functions at INFO or above | Two Cloud Logging sinks | A push subscription to the Datadog log intake | Not measured | LIVE, M |

### H. Dead letters

| Topic | What it carries (key fields) | Producers | Consumers | Traffic (15 days) | Verdict |
| --- | --- | --- | --- | --- | --- |
| `dead-letters.v1` | Messages that failed delivery on a module subscription | The Pub/Sub service agent, for every module subscription. gfs-modernizer also publishes to it in code | gfs-deadletter-register (1 replica). It stores each message in Mongo and acknowledges on success. On a failed validation or an exception it neither acknowledges nor nacks. It cannot replay (STATED) | 84 "DeadLetter registered" log lines, 1 in the last 24 h. This is a log count, not a Pub/Sub metric, and cannot be tied to a subscription | LIVE, H |

## Topics that look in use but are not

| Topic or item | Why it looks in use | What the evidence shows | Status |
| --- | --- | --- | --- |
| `tracking.v1` | Terraform topic, a tracking-core subscription, an env key in the manifest, and a tracking-core doc that says it subscribes | No code publishes it. The standalone tracking-mapper has no publisher and runs at 0 replicas. No code reads the env key. Dead in Terraform, manifest and docs alike | CONFIRMED (code) |
| `legacy_tracking.v1` | tracking-core has live publisher code and requires the topic setting at startup | The prod manifest sets the publish flag to false by default with no per-carrier override. No subscription exists. The dev manifest sets it true for one carrier | CONFIRMED (prod manifest) |
| `parcel-eta-update` | Topic, plus subscriptions for CCIS and ICIS | The publisher, parcel-eta-service, runs at 0 replicas. The repo says dormant and retired 2026-07-27. Neither consumer sets the env var, and both skip an unset subscription | CONFIRMED |
| `warehouse-shipment-events.v1` and `warehouse-tracking.v1` | Topics with schemas, and a BigQuery subscription in the warehouse project | Both materializer manifests are commented out entirely. The three `data-warehouse` input subscriptions have no reader. Traffic on `warehouse-shipment-events.v1` would mean a publisher the research did not find | CONFIRMED |
| `tracking-events.v2` and `customers.v2` | gfs-modernizer has the env vars set and a publish function | No subscription in Terraform, manifests or code in prod. Whether gfs-modernizer publishes to them is UNKNOWN | CONFIRMED (no consumer); UNKNOWN (publishing) |
| `fb.carrier_aliases.v1`, `fb.carrier_scan_codes.v1`, `fb.shipment_shipper.v1`, `fb.shipment_status.v1` | The Firebird Transfer Service config lists the tables (STATED) | No subscription and no env var anywhere. Everything rests on the unread on-prem config | STATED |
| `connect.hooks_usage.v1` | connect-hooks has the topic env var set | The only publishing function is never imported anywhere in the repo | CONFIRMED |
| Kubernetes tracking-patina-service | It has a live `raw_tracking.v1` subscription, and Datadog shows 6,294,707 handled | `CARRIERS=NONE`. The handler keeps an event only if the list is empty or contains the carrier, so it drops every event. The counter still counts the drops. It does still store shipments from `shipments.v2.identified` | CONFIRMED |
| `scanners.consignments.V1` (project gfs-ecm-staging, outside the 70) | It is the write-back topic the on-prem Scan Injector reads (STATED) | It lives in the staging project, and publisher access was "granted manually". Publishers are patina-service-2 (Dataflow, state UNKNOWN) and the Kubernetes patina service, which is hard-coded to this topic and drops every event. A manifest comment says the staging topic is the correct one, was never pushed to prod, and that prod legacy runs from it through staging "doppelganger" | UNKNOWN |
| Evri interim topic and its dead-letter topic (project gfs-selector-rest-prod-uk1, outside the 70) | Datadog shows 562,788 messages received | The Evri webhook publishes the raw request to its own interim topic and a push subscription hands it back. The flag for publishing to `raw_tracking.v1` is false, so Evri runs in shadow. Deployed state is not checkable | CONFIRMED (tfvars setting); UNKNOWN (deployed state) |
| `fb.<x>.v1.prod` (13 names, project gfs-ecm) | The Firebird Transfer Service config and catalogue name them | No Terraform or manifest creates or reads them | STATED |
| `carrier-charges.v1`, `estimated-costs.v1`, `sales.v1`, `adjustments.v1`, `shipments-legacy.v1` | The vault catalogue lists them (STATED) | The Terraform module call is commented out and nothing else instantiates it, so prod Terraform no longer creates them. They may survive from an earlier apply (UNKNOWN) | CONFIRMED (not created) |

Subscriptions with no running reader. These are Terraform subscriptions whose backlog would grow if the topic carries traffic, and none of that can be measured.
- `tracking.v1.fenghuang.tracking-core` (confidence H).
- `raw_tracking.v1.fenghuang.tracking-mapper` and `raw_tracking.v1.parcel-eta-service`, both at 0 replicas (H).
- `parcel-eta-update` for CCIS and for ICIS (H).
- `shipment_tracking_status` for reporting-ingestion (M). Also for CCIS (M): the manifest sets the env var, but the CCIS code at the head commit reads only the v2 variable. The running tag may differ.
- `fb.customers.v1.customer-care-portal` (L, ccp-api code not found).
- `fb.collections.v1.fenghuang.collections_service` (H, manifest sets it and code never reads it).
- All three `*.data-warehouse` subscriptions (H, manifest commented out).
- All six `*.longmen` subscriptions (H for "no workload"; the external consumer is UNKNOWN).
- The three `*.rm_range_creator` subscriptions (H, manifest commented out).
- `raw_tracking.v1.tracking_patina_service` (H, runs but drops everything).
- `raw_tracking.v1.tracking-patina-service-dataflow` (L, Dataflow job state unknown).
- The test subscription and the BigQuery subscription on `legacy_tracking_events` (M).
- The two holding subscriptions on the `cs.bot.logs.deadletter.*` topics (M).
- `route_validation_import.v1.cloud_run` (L, source not found).

## Things that surprised us

1. **`tracking.v1` is wired three times and used by no code.** Terraform, the manifest and the repo docs all wire it. No code publishes it and no code reads the subscription's env key. An earlier lead named the standalone mapper as the publisher. Current mapper code has no publisher for it.
2. **The obsolete status topic carries the full volume.** `shipment_tracking_status` is labelled obsolete in Terraform. It still carries 4,077,200 messages in the window. ICIS and shipment-update-service read it.
3. **Nine topics have a running consumer and no readable publisher.** The Transfer Service repo config names different topics from the ones Terraform creates. Datadog shows traffic on `fb.shipment_extra.v1` (1,821), `fb.cust_contracts.v1` (420) and `fb.cust_contract_services.v1` (458). So a publisher exists that no repo shows. The publisher for these is `[??]`.
4. **A consumer reads every scan and drops it.** The Kubernetes tracking-patina-service has `CARRIERS=NONE`. The write-back topic it names lives in the staging project, and nobody in the sources can say who writes it in prod.
5. **Some subscriptions have no one behind them.** Six longmen subscriptions, three data-warehouse subscriptions and three range-creator subscriptions have no workload in the manifests. `tracking-events.v2` and `customers.v2` have no subscription at all. `warehouse-shipment-events.v1` still has a live BigQuery subscription whose only candidate publisher is not running.

## What a replacement would need to keep

Hypothetical and short. Merak replacing ECM is only a hunch, and these are facts the code shows.

- **Message fields consumers rely on.** `id`, `parcel.shipmentId`, `parcel.parcelNumber` and `parcel.company`. connect-hooks drops an event with no company, and the status deriver throws on a missing `shipmentId`.
- **Dedupe on `id`, with no ordering key.** Each publisher mints its own `id`, and consumers dedupe on it alone. No `raw_tracking.v1` publisher sets an ordering key. Only `shipment_tracking_status.v2` is ordered, by `shipmentId`.
- **The raw carrier code only on `raw_tracking.v1`.** The mapped result is stored but never published. Each consumer maps again through its own sidecar.
- **The `groupId` strings and the DELIVERED or IN_TRANSIT bucket.** `groupId` is a free string from a spreadsheet, and nothing enforces the list. tracking-core's parcel state and every status reader depend on the values.
- **The dead-letter default.** After 10 attempts a message goes to `dead-letters.v1`. gfs-deadletter-register stores it and cannot replay it (STATED).

## Not confirmed yet

- Live GCP state. No GCP access was available. Terraform proves topics, subscriptions and IAM, not that they were applied.
- The on-prem Firebird Transfer Service's deployed config and the Scan Injector. Every `fb.*` publisher and the consumer of `scanners.consignments.V1` rest on them. The Scan Injector is in no repo.
- Whether the patina-service-2 Dataflow job runs, and which topics its variable group names. Its source for the prod run is `[??]`.
- Source for ccp-api, the oz gateway, longmen, the CS bot, the report-scheduler and the Cloud Run route-validation-import service. Also the invoice translator's host, and what the CS bot is.
- Whether the manifests match the running cluster. The local clone is at a317dc0 and the remote master is at b7e16c7, so the clone is behind by an unknown number of commits. Image tags may differ, and the cluster was not read.
- The subscription count. The research counted 145 in the prod project. The vault says 144, not recounted. The missing one is `[??]`.
- The `fb.*` naming mismatch. The Transfer Service repo config names `fb.<x>.v1.prod` in project gfs-ecm. Prod Terraform creates `fb.<x>.v1` in project gfs-ecm-prod-uk1. The deployed config is `[??]`.
- Datadog gaps:
  - No Pub/Sub metrics exist for the ECM prod project, so backlog, oldest unacknowledged age, acknowledgements and dead-letter counts are not measured.
  - Topics outside the 41 queried were not measured, apart from nine seen in passing. The 41 include four outside the prod Terraform set.
  - The push subscriptions in gfs-selector-rest-prod-uk1, patina-service-2 in prod, data-warehouse, longmen, tracking-mapper and parcel-eta-service are not measured.
  - Several counts name a topic by inference from a metric or subscription name. The rows say so.
- Message shapes not read: `windowed-shipments-parcels`, `shipment-number-updates`, `tracking-events.v2`, `customers.v2`, `ticket-actions`, `report-run`, `route_validation_import.v1`, `connect.usage_notifications.v1`, and the claims topics other than `claims.v1`.
- Call sites for most claims publish functions, and for the CCDIS publish to `invoiced_shipments_published.v1`.
- Acknowledge and nack behaviour of the shared subscriber library in each image, and of tracking-core's Pub/Sub libraries.
- Whether `shipment_tracking_status.v2` ordering is honoured on publish. The deriver's client is built without publisher options.
- Whether Flux applies the `carrier-cs.yml` manifest, because of its `.yml` extension.
- Whether the BigQuery write on `cs.bot.logs.*` has the rights it needs. Terraform shows two subscriptions on each of `cs.bot.logs.ticket` and `cs.bot.logs.exception` but describes one.
- The parcel-eta-service history. The repo says retired 2026-07-27. An earlier finding said 0 replicas since 2022.
- Topics outside the prod Terraform, in staging, dev, playground and finance-dev, and the staging module internals.

## Sources

Research ran on 2026-11-10, read-only.

| Source | Version |
| --- | --- |
| Prod Terraform, `gfs-ecm-prod-uk1` | master 35b545ce8a78b2e6ed3061961db0453b2b3c4702 |
| Prod cluster manifests, `prod-uk1-primary-cluster` | a317dc0 (2026-11-06, shallow local clone; remote master is b7e16c7) |
| Other Terraform | gfs-ecm-staging 17b324f (the doppelganger module was read at 02ad01b), gfs-data-warehouse-uk1 fffa8ee, ecm-prod-uk1-iac d4c2b47, ecm-staging-iac 8d5ddf1, tracking-webhooks IaC |
| tracking-core | c081108 |
| tracking-file-processor | e6da4bf |
| tracking-patina-service | 8edfb3e |
| gfs-pod | 811007e |
| collections-service | d593a97 |
| carrier-credentials-manager | 9851682 |
| fenghuang-ftp-proxy | 6c5e9fa |
| legacy-invoice-translator | d2ed426 |
| shipment-identity-service | 7454a4e |
| shipment-tracking-status-deriver | a3dc446 |
| shipment-update-service | ccec388 |
| parcel-eta-service | 5fbc9c7 |
| tracking-mapper | 44cfbf2 |
| tracking-configuration-distribution-service | bbd5e74 |
| carrier-services-directory | 33e2bec |
| connect | 6c6d527 |
| tracking-webhooks, royal-mail-sapient, slipway, upload-service-v2 | 9777dd4, 3c880bf, f604bdd, ef6d145 |
| node-modernizer (gfs-modernizer) | 2350a1d |
| manage-queries-proxy, unmapped-scan-recorder, gfs-deadletter-register, sofia-query-categorisation | 0772650, ad49a45, 8c958b5, e657891 |
| Firebird Transfer Service, patina-service-2, action-manager-api | 8569227, b9af0a1, f4c7d2c |
| CCIS-next, ICIS, claims-service-next, CCDIS, reporting-ingestion, reporting-service, reporter, customer-and-contract service | b2af452, 3d125f5, 584d827, 6b267aa, 32be0e2, 1059e61, acb67c3, aeeace5 (GitHub head at read time; the running image tag may differ) |
| Datadog | Application metrics, window 2026-10-23 00:00 to 2026-11-07 00:00 UTC, plus the 24 h to 2026-11-10 12:13 UTC |
| Not found in any repo | ccp-api, the oz gateway, longmen, the Scan Injector, the CS bot, the report-scheduler Go source, the Cloud Run route-validation-import service |

The per-topic facts come from the research map of 2026-11-10. Where it differs from the earlier findings, the map is used. The vault notes ecm tracking and ecm architecture supply the spine and the settled facts.

Related pages:
- [Shipment Journey Through ECM](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/354975746)
- [Shipment Identity](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/355631312)
- [Carrier Tracking and Proof of Delivery](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353206337)
- [Polling Connectors](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353697880)
- [Tracking Webhook Services](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353533985)
