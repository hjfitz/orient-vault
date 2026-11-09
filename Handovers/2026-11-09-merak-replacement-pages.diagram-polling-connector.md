# Component diagram: a polling connector and tracking-core

This diagram shows one poll cycle between a polling connector and the tracking-core services, down to the gRPC calls and the response-publisher pod. It does not show the other carriers' connectors, credentials, retries (there are none) or the webhook and file routes.

It replaces the ASCII flow in "How a connector works" on the page "Polling Connectors" (353697880, space MPK). Researched 9 Nov 2026 from that page, the vault docs, the prod manifests and the `tracking-core` source.

Status values: `Verified in page` means the page states it. `Verified in source, not on page` means the manifests or code show it but the page does not. `Not confirmed` means no source settles it, so draw it dashed.

## Groups

| Group | Boundary type | Contents |
| --- | --- | --- |
| GKE cluster `prod-uk1-primary-cluster` | GKE cluster, namespace `default` | E2, E4, E5, E6, E8, E9, E10, E11, E12 |
| tracking-core Deployments | Three Deployments from one image, `tracking-core` | E2, E4, and the response-publisher pod |
| Pod `fenghuang-tracking-core-response-publisher` | Kubernetes pod with three containers | E8, E9, E10 |
| Connector pod (for example `connectors-dhlparcel`) | Kubernetes Deployment | E5, E6 |

The pod group sits inside the tracking-core group. Both sit inside the cluster group. E1, E3, E7 and E13 stay outside every group.

## Elements

| ID | Name | C4 type | Technology or GCP product | Description | Group | Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E1 | shipments.v2.identified | container | Pub/Sub topic | Shipments with their GFS IDs. Consignment-manager subscribes to it. | none (external) | Page: How a connector works | Verified in page |
| E2 | consignment-manager | component | GKE workload | Fills active-parcels from identified shipments. Skips contracts on the untracked list. | tracking-core Deployments | Page: How a connector works; ConsignmentHandler.cs | Verified in page |
| E3 | active-parcels | datastore | MongoDB (hosting Not confirmed) | Parcels being tracked, with 90-day expiry. Database `tracking-core`, collection `active-parcels`. | none | Page: How a connector works; tracking-core.yaml | Verified in page |
| E4 | batch-creator | component | GKE workload | Streams a batch of due parcels to a connector, oldest first, for its carrier and state. | tracking-core Deployments | Page: Trigger row; tracking_batch_v1.proto | Verified in page |
| E5 | CarrierConnectorWorker | component | GKE workload (NuGet framework) | Runs the poll loop. Sleeps 30 seconds when a batch is short or empty. | Connector pod | Page: Code and Trigger rows | Verified in page |
| E6 | Carrier client | component | GKE workload | The only part a connector writes. Implements `TrackParcel()` for one carrier. | Connector pod | Page: Code row | Verified in page |
| E7 | Carrier API | system | | The carrier's tracking API. SOAP, XML or REST depending on carrier. | none (external) | Page: What runs table | Verified in page |
| E8 | response-publisher | component | GKE workload | Receives connector results, de-duplicates, maps and publishes one message per new event. | Response-publisher pod | Page: Output row; ConnectorResponseHandler.cs | Verified in page |
| E9 | tracking-mapper | container | GKE workload (sidecar) | Turns carrier codes into GFS statuses. Listens on localhost port 10000. | Response-publisher pod | Page: Output row; tracking-core.yaml | Verified in page |
| E10 | shipment-tracking-status-deriver | container | GKE workload (sidecar) | Derives the parcel's status, so the loop knows when a parcel is delivered. Listens on localhost port 11000. | Response-publisher pod | tracking-core.yaml; TrackingStatusManager.cs | Verified in source, not on page |
| E11 | etcd | datastore | | Holds each connector's batch options: carrier, state, batch limit and polling minutes. | GKE cluster | Page: Trigger and Polling interval rows; connectors-dhlparcel.yaml | Verified in page |
| E12 | tracking-configuration-distribution-service | container | GKE workload | Serves the mapping config that the tracking-mapper sidecar fetches. | GKE cluster | Page: hop table (other page); tracking-core.yaml | Verified in page |
| E13 | raw_tracking.v1 | container | Pub/Sub topic | One message per new tracking event. Shared with the webhook and file routes. | none (external) | Page: How a connector works | Verified in page |

Type note: E9 and E10 are separate container images in the pod, so they are `container`. E2, E4, E5, E6 and E8 are components of tracking-core or the connector.

## Relationships

Arrows point from the caller for gRPC, HTTP and HTTPS, and the way messages travel for Pub/Sub.

| From | To | Label | Technology or message | Status |
| --- | --- | --- | --- | --- |
| E1 | E2 | Delivers each identified shipment | Pub/Sub subscription | Verified in page |
| E2 | E3 | Upserts one record per parcel to track | MongoDB | Verified in page |
| E11 | E5 | Supplies batch limit, polling minutes and which states are switched on | etcd keys, one set per carrier | Verified in page |
| E5 | E4 | Asks for the next batch for its carrier and state | gRPC `TrackingBatchServiceV1.GetBatch` | Verified in page |
| E4 | E3 | Picks the oldest-due parcels and stamps `LastRequestedAt` | MongoDB `FindOneAndUpdate` | Verified in source, not on page |
| E4 | E5 | Streams the due parcels back, up to the batch limit | gRPC server stream | Verified in page |
| E5 | E6 | Hands each parcel to the carrier client | In-process call, `TrackParcel()` | Verified in page |
| E6 | E7 | Asks the carrier about every parcel in the batch at once | HTTPS, SOAP or XML by carrier | Verified in page |
| E5 | E8 | Streams each parcel's result to the publisher | gRPC `ConnectorResponseServiceV1.SendResponse` | Verified in page |
| E8 | E3 | Checks stored events so only new ones pass, on date and code | MongoDB | Verified in page |
| E8 | E9 | Sends new events to be mapped to GFS statuses | HTTP `localhost:10000/api/tracking/map` | Verified in page |
| E9 | E12 | Fetches the mapping config | HTTP, `/api/config/v1` | Verified in page |
| E8 | E13 | Publishes one message per new event | Pub/Sub, `raw_tracking.v1` | Verified in page |
| E8 | E10 | Asks for the parcel's status after publishing | HTTP `localhost:11000` | Verified in source, not on page |
| E8 | E3 | Saves the new status, expiry and tracked state on the parcel | MongoDB | Verified in source, not on page |

Counts: 13 elements, 15 relationships.

Two arrows join E8 and E3, and two join E4 and E3. Keep them as separate labelled lines, or merge each pair into one line with a two-part label.

## Layout hint

Put the carrier connector pod on the left and the tracking-core group on the right. Run the poll cycle top to bottom: batch request, parcels back, carrier call, results to the publisher.

Place E3 in the middle, between the two groups, so E2, E4 and E8 reach it without crossing the gRPC lines. Put E1 above E2, E13 to the right of the pod, and E11 above the connector pod.

## Key needed

- Pub/Sub icon on E1 and E13. GKE icon on the cluster group label and the workloads. Cylinder for E3 and E11.
- Plain box with no icon for E7, which is not a GCP product. E11 (etcd) has no GCP icon either.
- Label gRPC arrows with the method name. Mark the two streamed arrows (E4 to E5, E5 to E8) as streams.
- Dashed line and the label `Not confirmed`: nothing here needs it. Use it only if Harry rejects a status above.

## Gaps

- **The page omits the status-deriver sidecar.** The response-publisher pod runs three containers: the app, tracking-mapper and shipment-tracking-status-deriver. The page names only the mapper. The deriver's result sets the parcel's expiry and delivered state, so it matters for "Stopping".
- **The page says "up to 100 due parcels" but also says the batch size is Not confirmed.** The batch limit comes from each connector's etcd key, so 100 is unproven. This diagram says "up to the batch limit".
- **The connector, not the batch-creator, reads etcd for limit and polling minutes.** The connector sends both in the `GetBatch` request. The vault's flow diagram agrees.
- **The page does not say the publisher writes to Mongo.** Source shows it reads stored events for dedupe and writes events, mapped events, status and expiry back.
- **MongoDB hosting for `active-parcels` is not confirmed.** The page says only "Mongo". The box has no GCP icon until someone confirms where it runs.
- **The namespace is `default`, not `fenghuang`.** The vault says `fenghuang`, but that is the manifest folder.
- **Not drawn, on purpose:** `carrier-credentials-manager` for DPD, DPD Local, Panther and FedEx, the BigQuery sink for unmatched events, and the legacy publish path, which is off (`ShouldPublishToLegacy=false`).
- **A standalone `fenghuang-tracking-mapper` Deployment also exists.** It reads a raw-tracking input subscription and publishes a mapped-tracking topic. Its role is Not confirmed.
- **The prod etcd values and the untracked list are Not confirmed**, as the page already says.
- **The consignment-manager manifest also sets a tracking subscription.** Source shows no use of it, so the diagram draws only the shipment subscription. Not confirmed.
