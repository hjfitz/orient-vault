# Container diagram: tracking from carrier to customer

This diagram shows the three routes that bring carrier tracking into `raw_tracking.v1`, the shipment path that feeds them, and the consumers after it. It does not show proof of delivery, webhook internals, write-back to Firebird or the carriers that have no tracking source.

It replaces the ASCII diagram in "From carrier to customer" on the page "Carrier Tracking and Proof of Delivery" (353206337, space MPK). Researched 9 Nov 2026 from that page, the vault docs and the prod cluster manifests.

Status values: `Verified in page` means the page states it. `Verified in source, not on page` means the manifests or code show it but the page does not. `Not confirmed` means no source settles it, so draw it dashed.

## Groups

| Group | Boundary type | Contents |
| --- | --- | --- |
| ECM Pub/Sub topics (project `gfs-ecm-prod-uk1`) | GCP project | E3, E12, E14 |
| GKE cluster `prod-uk1-primary-cluster` | GKE cluster, namespace `default` | E4, E6, E7, E8, E9, E11, E13, E15, E16, E17 |
| Cloud Run in `gfs-selector-rest-prod-uk1` | GCP project, europe-west2 | E10 |

The topics' project is inferred from one subscription path, `projects/gfs-ecm-prod-uk1/subscriptions/raw_tracking.v1.connect-hooks`. Treat E3 and E12 membership as `Not confirmed`.

## Elements

| ID | Name | C4 type | Technology or GCP product | Description | Group | Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E1 | Carriers | system | | Carrier APIs that connectors poll, webhook senders (Royal Mail, Evri) and SFTP servers holding tracking files. | none (external) | Page: In short; Coverage by carrier | Verified in page |
| E2 | Upstream shipment path | system | | Selector or Hub booking, Firebird, gfs-modernizer and shipment-identity-service. Publishes identified shipments. Not drawn in detail. | none (external) | Page: From carrier to customer | Verified in page |
| E3 | shipments.v2.identified | container | Pub/Sub topic | Shipments with their GFS IDs. Every tracking path matches carrier events against it. | ECM Pub/Sub topics | Page: hop table | Verified in page |
| E4 | consignment-manager | container | GKE workload | Subscribes to identified shipments and decides which parcels get tracked. Skips contracts on the untracked list. | GKE cluster | Page: hop table; tracking-core.yaml | Verified in page |
| E5 | active-parcels | datastore | MongoDB (hosting Not confirmed) | Parcels being tracked, with 90-day expiry. The untracked list is also in Mongo. | none | Page: From carrier to customer, hop table | Verified in page |
| E6 | batch-creator | container | GKE workload | Hands each connector a batch of parcels due for polling, oldest first, over gRPC. | GKE cluster | Page: How a connector works (Polling Connectors) | Verified in page |
| E7 | Polling connectors | container | GKE workload | .NET connectors, one per carrier. Eleven poll in prod. Each calls the carrier for every parcel in a batch. | GKE cluster | Polling Connectors page: In short | Verified in page |
| E8 | response-publisher | container | GKE workload | Receives connector results, de-duplicates on date and code, maps them and publishes new events. | GKE cluster | Polling Connectors page: Output row | Verified in page |
| E9 | tracking-mapper | container | GKE workload (sidecar) | Turns carrier codes into GFS statuses. Runs beside response-publisher. | GKE cluster | Page: hop table; tracking-core.yaml | Verified in page |
| E10 | Tracking webhook services | container | Cloud Run | One service per carrier receives pushed events and matches them to shipments. Royal Mail publishes; Evri runs in shadow. | Cloud Run | Page: Coverage by carrier; tracking-webhooks/architecture.md | Verified in page |
| E11 | file-ingestion-ftp-proxy | container | GKE workload (CronJob) | Collects carrier tracking files over SFTP every 20 minutes and announces each file. | GKE cluster | Page: From carrier to customer; file-ingestion-ftp-proxy/overview.md | Verified in page |
| E12 | file_tracking.v1 | container | Pub/Sub topic | One message per collected carrier tracking file. | ECM Pub/Sub topics | Page: From carrier to customer | Verified in page |
| E13 | tracking-file-processor | container | GKE workload | Parses carrier files, matches rows to shipments and publishes events. A retry job reprocesses failed rows. | GKE cluster | Page: Health; tracking-file-processor/overview.md | Verified in page |
| E14 | raw_tracking.v1 | container | Pub/Sub topic | One message per new tracking event, from all three routes. About 6.25M in 15 days. | ECM Pub/Sub topics | Page: In short; The raw_tracking.v1 contract | Verified in page |
| E15 | shipment-tracking-status-deriver | container | GKE workload | Derives each shipment's status, exceptions and ETA from raw events. | GKE cluster | Page: hop table; shipment-tracking-status-deriver.yaml | Verified in page |
| E16 | CCIS and ICIS | container | GKE workload | Customer and internal consignment stores. They hold consignment records, events and tracking status. | GKE cluster | Page: From carrier to customer | Verified in page |
| E17 | connect-hooks | container | GKE workload | Sends tracking events to customer webhooks. About 404k sent in 15 days. | GKE cluster | Page: From carrier to customer; connect-hooks.yaml | Verified in page |
| E18 | Portal, Connect API and staff tools | system | | Customer portal, Connect API and staff tools (Nexus, CCP) that show tracking to users. | none (external) | Page: From carrier to customer | Verified in page |
| E19 | Customer webhook receivers | system | | Customer systems that receive tracking webhooks. | none (external) | Page: From carrier to customer | Verified in page |

## Relationships

Arrows point from the caller for gRPC, HTTP and SFTP, and the way messages travel for Pub/Sub.

| From | To | Label | Technology or message | Status |
| --- | --- | --- | --- | --- |
| E2 | E3 | Publishes each identified shipment (about 665k in 15 days) | Pub/Sub, `shipments.v2.identified` | Verified in page |
| E3 | E4 | Delivers shipments so one record per parcel can be opened | Pub/Sub subscription | Verified in page |
| E4 | E5 | Upserts the parcels to track, with 90-day expiry | MongoDB | Verified in page |
| E7 | E6 | Asks for the next batch of due parcels, which stream back on the same call | gRPC `GetBatch` | Verified in page |
| E6 | E5 | Picks the oldest-due parcels for that carrier and state | MongoDB | Verified in page |
| E7 | E1 | Polls the carrier API for every parcel in the batch | HTTPS, SOAP or XML by carrier | Verified in page |
| E7 | E8 | Sends each parcel's tracking result | gRPC `SendResponse` | Verified in page |
| E8 | E9 | Sends new events for mapping to GFS statuses | HTTP, in the same pod | Verified in page |
| E8 | E14 | Publishes one message per new event | Pub/Sub, `raw_tracking.v1` | Verified in page |
| E1 | E10 | Pushes tracking events (Royal Mail, Evri) | HTTPS `POST /tracking` | Verified in page |
| E3 | E10 | Delivers shipments so pushed events can be matched | Pub/Sub subscription | Verified in page |
| E10 | E14 | Publishes matched events (Royal Mail live; Evri publishes none) | Pub/Sub, `raw_tracking.v1` | Verified in page |
| E11 | E1 | Collects tracking files from carrier SFTP servers every 20 minutes | SFTP | Verified in page |
| E11 | E12 | Announces each collected file | Pub/Sub, `file_tracking.v1` | Verified in page |
| E12 | E13 | Delivers the file announcement for parsing | Pub/Sub subscription | Verified in page |
| E3 | E13 | Delivers shipments so file rows can be matched | Pub/Sub subscription | Verified in page |
| E13 | E14 | Publishes matched file rows as events | Pub/Sub, `raw_tracking.v1` | Verified in page |
| E14 | E15 | Delivers every event for status derivation | Pub/Sub subscription | Verified in page |
| E14 | E16 | Delivers every event to the consignment stores | Pub/Sub subscription | Verified in source, not on page |
| E14 | E17 | Delivers every event for customer webhook rules | Pub/Sub subscription | Verified in source, not on page |
| E15 | E16 | Publishes status, exceptions and ETA | Pub/Sub (topic not named on page) | Verified in page |
| E16 | E18 | Serves consignment status and events to users and staff | Mechanism not stated | Verified in page |
| E17 | E19 | Sends customer webhooks (about 404k in 15 days) | HTTPS webhook | Verified in page |

Counts: 19 elements, 23 relationships.

Source for the two manifest-only arrows: `connect/connect-hooks.yaml` sets `TRACKING_SUBSCRIPTION` to `raw_tracking.v1.connect-hooks`. `customer-consignment-information-service.yaml` and `internal-consignment-information-service.yaml` set `RAW_TRACKING_SUBSCRIPTION`.

## Layout hint

Read left to right. Put E1 and E2 in a left column. Put the three route lanes in the middle: polling on top, webhooks in the middle, files at the bottom. E14 joins them on the right, and consumers E15 to E19 follow in a final column.

Run the shipment path along the top: E2, E3, E4, E5. Draw E3 to E10 and E3 to E13 as long arrows that drop down to their lanes.

## Key needed

- Dashed line and the label `Not confirmed`: nothing in this file needs it as an arrow. Use it only if Harry rejects a status above.
- Pub/Sub icon on E3, E12 and E14. GKE icon on workloads. Cloud Run icon on the group label and E10. Cylinder for E5.
- Plain box with no icon for E1, E2, E18 and E19, which are not GCP products. Say so in the key.
- Arrow rule: from the caller for gRPC, HTTP and SFTP, and the way messages travel for Pub/Sub.

## Gaps

- **The page puts connect-hooks after CCIS and ICIS.** The manifest shows connect-hooks has its own subscription to `raw_tracking.v1`. This draws the manifest version. The page text needs fixing.
- **The page's path counts do not add up.** Polling 5.44M, webhooks 215k and SFTP 54k sum to about 5.71M, not 6.25M. The per-carrier table sums to about 6.25M, with polling carriers at about 5.97M. This diagram quotes only the 6.25M total.
- **MongoDB hosting for `active-parcels` is not confirmed.** The page says only "Mongo". The box has no GCP icon until someone confirms where it runs.
- **Topic ownership is inferred.** Only the `raw_tracking.v1` subscription path names a project. The cluster's own project is also not confirmed.
- **The namespace is `default`, not `fenghuang`.** The vault says `fenghuang`, but that is the manifest folder. The manifests say `namespace: default`.
- **The deriver's output topic is not on the page.** The explainer names `shipment_tracking_status.v2`, which is a vault source only.
- **How portal, Connect API and staff tools read CCIS and ICIS is not stated.** The arrow shows data direction only.
- **Not drawn, on purpose:** Amazon SFP shipments via Slipway, the webhook interim topic and Mongo, and BigQuery for unmatched events. Also Cloud Storage in the file proxy.
- **The standalone tracking-mapper Deployment has no explanation on the page.** It reads a raw-tracking input subscription and publishes a mapped-tracking topic. Its role is Not confirmed.
- **The untracked list's contents are Not confirmed**, as the page already says.
