# Component diagram: a tracking webhook service

This C4 level 3 diagram shows the parts of one carrier's webhook service, from the carrier's POST to `raw_tracking.v1`. It does not show any carrier's quirks beyond authentication, the monorepo and CI, health and token endpoints, or what reads `raw_tracking.v1`.

It replaces the ASCII block in "How a webhook service works" on the page "Tracking Webhook Services" (353533985, space MPK, version 3). Researched 9 Nov 2026 from that page, the vault docs and the monorepo at commit `9777dd4`, read locally.

The diagram describes the shared core as Evri uses it in prod. Royal Mail, the only service publishing today, runs an older handler that processes synchronously and has no interim topic (`Engineering/tracking-webhook-royal-mail-sapient/overview.md`). See Gaps.

Status values: `Verified in page` means the page states it. `Verified in source, not on page` means the code or Terraform shows it but the page does not. `Not confirmed` means no source settles it, so draw it dashed.

## Groups

| Group | Boundary type | Contents |
| --- | --- | --- |
| GCP project `gfs-selector-rest-prod-uk1`, europe-west2 | GCP project | E2, E6, E7 and the Cloud Run group |
| Cloud Run service (one per carrier) | Container: one Node.js service, GCP Cloud Run. Ingress is the load balancer only | E3, E4, E5, E8, E9, E10 |
| GCP project `gfs-ecm-prod-uk1` | GCP project | E13, E14 |

Outside all groups: E1, E11 and E12. The Mongo hosting is not stated anywhere I read.

## Elements

| ID | Name | C4 type | Technology or GCP product | Description | Group | Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E1 | Carrier | system | | Evri, InPost or Royal Mail. Pushes tracking events to GFS by HTTPS POST. | none | Page: How a webhook service works, first line | Verified in page |
| E2 | HTTPS load balancer | container | Cloud Load Balancing | Only way into the Cloud Run service. Gives the carrier a fixed address and certificate. | GCP project `gfs-selector-rest-prod-uk1` | Page: Part table, Endpoints. `iac/modules/tracking-webhook/load-balancer.tf` | Verified in page |
| E3 | Webhook endpoint | component | | Receives POST /tracking, runs the adapter's check, rejects non-JSON, and answers 200 once the event is queued. | Cloud Run service | Page: flow, Acknowledging row. `controllers/webhook.controller.ts` | Verified in page |
| E4 | Carrier adapter | component | | One per carrier. Authenticates each request and later maps the carrier's payload to tracking events. | Cloud Run service | Page: Auth row. `types/carrier-adapter.ts` | Verified in page |
| E5 | Interim publisher | component | | Publishes the accepted request to the interim topic. If that fails, the service answers 500. | Cloud Run service | Page: Acknowledging row. `services/interim.tracking.service.ts` | Verified in page |
| E6 | Interim topic | container | Pub/Sub topic | Holds each accepted event until the service processes it. Pushes back to the service. | GCP project `gfs-selector-rest-prod-uk1` | Page: flow. `iac/modules/tracking-webhook/interimpubsub.tf` | Verified in page |
| E7 | Interim dead-letter topic | container | Pub/Sub topic | Receives an event after 5 failed pushes. A subscription keeps it for 7 days. | GCP project `gfs-selector-rest-prod-uk1` | Page: Retries row | Verified in page |
| E8 | Interim push handler | component | | Takes the push at /events/interimTracking, checks the Google OIDC token and decodes the message. | Cloud Run service | Page: Endpoints row. `services/interim.tracking.subscription.service.ts` | Verified in page |
| E9 | Tracking service | component | | Maps, matches each event to a stored shipment, dedupes on trackingKey, then publishes it or holds it. | Cloud Run service | Page: flow, Matching row. `services/tracking.service.ts` | Verified in page |
| E10 | Shipments push handler | component | | Takes the push at /events/shipments, keeps only this carrier's shipments and stores them. | Cloud Run service | Page: flow, last line. `services/shipment.subscription.service.ts` | Verified in page |
| E11 | Shipments store | datastore | MongoDB, hosting Not confirmed | This carrier's shipments, copied from shipments.v2.identified. Used to match events. | none | Page: Matching row | Verified in page |
| E12 | Held events store (retries) | datastore | MongoDB, hosting Not confirmed | Events that matched no shipment. Replayed when the shipment arrives, within 90 days. | none | Page: flow, Matching row | Verified in page |
| E13 | shipments.v2.identified | container | Pub/Sub topic | Owned by ECM. Announces each identified shipment. Every webhook service receives it, filtered by carrier. | GCP project `gfs-ecm-prod-uk1` | Page: flow. `iac/env/prod.tfvars` | Verified in page |
| E14 | raw_tracking.v1 | container | Pub/Sub topic | Owned by ECM. Receives matched events with rawData empty and a carrierIdV2 attribute. | GCP project `gfs-ecm-prod-uk1` | Page: Output row. `iac/env/prod.tfvars` | Verified in page |

## Relationships

Arrows point from the caller, or the way a message travels for Pub/Sub. The 200 answer is drawn because the page names acknowledging as a step.

| From ID | To ID | Label | Technology or message | Status |
| --- | --- | --- | --- | --- |
| E1 | E2 | Post a tracking event | HTTPS POST /tracking | Verified in page |
| E2 | E3 | Pass the request through | HTTPS | Verified in page |
| E3 | E4 | Ask the adapter to authenticate the request | In-process call | Verified in page |
| E3 | E5 | Hand over the authenticated JSON request to be queued | In-process call | Verified in page |
| E5 | E6 | Publish the request to the interim topic | Pub/Sub publish | Verified in page |
| E3 | E1 | Acknowledge with 200 once queued, or 500 so the carrier retries | HTTP response, via the load balancer | Verified in page |
| E6 | E8 | Push each queued event to the service | Pub/Sub push, Google OIDC, /events/interimTracking | Verified in page |
| E6 | E7 | Dead-letter an event after 5 failed pushes | Pub/Sub dead-letter policy | Verified in page |
| E8 | E9 | Pass the decoded event on for processing | In-process call | Verified in page |
| E9 | E4 | Ask the adapter to map the carrier payload to tracking events | In-process call | Verified in source, not on page |
| E9 | E11 | Find the shipment by carrier and consignment, then parcel. Check and record trackingKey | MongoDB query and update | Verified in page |
| E9 | E14 | Publish each matched, new event, when publishing is enabled | Pub/Sub, raw_tracking.v1, attribute carrierIdV2 | Verified in page |
| E9 | E12 | Hold an event that matches no shipment or parcel | MongoDB upsert on trackingKey | Verified in page |
| E13 | E10 | Push each identified shipment | Pub/Sub push, Google OIDC, /events/shipments | Verified in page |
| E10 | E11 | Store the shipment when it is this carrier's | MongoDB upsert | Verified in page |
| E10 | E9 | Ask the tracking service to release held events for that consignment | In-process call | Verified in page |
| E9 | E12 | Read the held events for that consignment, publish them, then delete them | MongoDB query and delete | Verified in page |

## Layout hint

Read left to right. Put the carrier, load balancer and Cloud Run group in a left-to-middle row. Put the interim topic and its dead-letter topic below the group's left edge. Keep the interim round trip (E5, E6, E8) as a loop under the group's top row.

Put the Mongo stores on the right inside reach of the Tracking service, below it. Put the `gfs-ecm-prod-uk1` group at the far right, with `shipments.v2.identified` above `raw_tracking.v1` and the shipments handler nearest the first.

## Key needed

- Dashed box or arrow with the label `Not confirmed`: none in this file. Use it if Harry rejects a status above.
- Pub/Sub icon on E6, E7, E13 and E14. Cloud Load Balancing icon on E2. Cloud Run icon on its group label.
- No GCP icon on the two Mongo cylinders, because the hosting is not stated. Say so in the key.
- Plain small boxes for components. Plain box for the carrier, which is not a GCP product.
- Arrow rule: from the caller, or the way a message travels. The acknowledgement is the one reply drawn.

## Gaps

- **The page's order differs from the code.** The page says match, then dedupe, then map. In `tracking.service.ts`, `processRequest` calls the adapter's `mapTracking` first, then looks up the shipment, then checks for a duplicate by trackingKey, then publishes. The diagram follows the code. The page text needs fixing.
- **Royal Mail does not match this diagram.** Its older handler has no interim topic and processes in the request (`Engineering/tracking-webhook-royal-mail-sapient/overview.md`). It is the only service publishing. I did not read its code. Its shape here is Not confirmed.
- **The interim path is switchable.** In the core, if the interim service is off, the endpoint matches and publishes inside the request. Evri's prod tfvars turn it on (`iac/projects/tracking-webhook-evri/tfvars/prod.tfvars`), and its variable defaults to off. The page does not mention the switch.
- **"Up to 90 days" is a read window, not proof of deletion.** The code ignores held events older than 90 days by `createdAt`. Physical deletion needs the TTL indexes, which the core README calls optional. Whether prod has them is Not confirmed.
- **The shipments window is not on the page.** Shipment matching also ignores stored shipments older than 90 days. The page states 90 days for held events only.
- **Mongo hosting is not stated.** The connection string sits in Secret Manager. No page or file I read names the cluster. The page asks for a same-cluster check before Royal Mail moves in.
- **The shipments subscription has no dead-letter topic.** It only backs off, so a poison shipment message redelivers. The page says so. It is not drawn because the diagram has one dead-letter topic.
- **Dead-letter depth is unknown.** The page already lists it. Nothing here shows whether anyone reads the dead-letter subscription.
- **Not drawn on purpose:** the health and verification endpoints, and the token endpoint and JWT check Royal Mail uses. Also Evri's signature lookup and token cache, Secret Manager and Datadog.
- **Ownership of the two ECM topics is inferred from the project in tfvars.** Their publishers and other subscribers are not shown here.
