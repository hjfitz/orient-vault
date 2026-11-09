---
tags: [handover, diagram-twin]
page: Proof of Delivery Service (MPK 353861642), section "How it works", and its child How Each Carrier's POD Is Retrieved (MPK 354877489)
level: C4 component
status: draft for Harry's review, not yet drawn
---
# Component diagram: gfs-pod-service

This diagram shows the parts of gfs-pod-service and the systems it talks to when it builds a shipment copy and serves a proof of delivery (POD) on the v2 API. It does not show the public v1 API, per-carrier request counts, time-zone handling, or the tracking pipeline.

## Groups

| Name | Boundary type | Contents |
| --- | --- | --- |
| Kubernetes cluster `prod-uk1-primary-cluster` | Deployment boundary: GKE cluster | The two Deployment groups below |
| Deployment `gfs-pod-service-deployment` (POD API) | Deployment boundary: Kubernetes Deployment, 3 replicas, API on and subscriber off | E8, and the Carrier modules group |
| Carrier modules (`src/pod-service`) | Code boundary inside the API process: one module per carrier | E11, E12, E13 |
| Deployment `gfs-pod-service-deployment-subscriber` | Deployment boundary: Kubernetes Deployment, 3 replicas, subscriber on and APIs off | E6 |

Both Deployments run one image. MongoDB (E7) and Redis (E9) sit outside the cluster group because the pages do not say where they run. The callers, topics and other services are outside every group.

## Elements

| ID | Name | C4 type | Technology or GCP product | Description | Group | Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E1 | Customer portal gateway | system | | The customer portal's gateway. Asks for a POD by GFS shipment ID. | none | Page 353861642, "APIs and callers", v2 row | Verified in page |
| E2 | Connect API | system | | GFS's Connect API. Returns a consignment's POD signatory and delivery time. | none | Page 353861642, "APIs and callers", v2 row | Verified in page |
| E3 | Nexus | system | | Staff app. Asks for a POD by shipment ID. | none | Page 353861642, "APIs and callers", v2 row | Verified in page |
| E4 | shipments.v2.identified | container | Pub/Sub topic | Carries each identified shipment that the subscriber copies. | none | Page 353861642, "How it works" diagram | Verified in page |
| E5 | raw_tracking.v1 | container | Pub/Sub topic | Raw tracking events. This service reads it for BJS detail links only. | none | Page 353861642, "How it works", Subscriber row | Verified in page |
| E6 | Subscriber | component | GKE workload (Deployment); Node 18, Express | Upserts each shipment into MongoDB and stores BJS detail links. About 7.8M messages in 15 days. | Deployment subscriber | Page 353861642, Deployments and Subscriber rows. `Engineering/gfs-pod-service/architecture.md` | Verified in page |
| E7 | Shipment copy | datastore | MongoDB | Own copy of each shipment: carrier, consignment, parcels and address. | none | Page 353861642, "How it works" diagram and Stores row | Verified in page |
| E8 | v2 POD API | component | GKE workload (Deployment); Node 18, Express | In-cluster API keyed on shipment ID. Looks up, caches, fetches, normalises and returns the POD. | Deployment POD API | Page 353861642, "How it works" steps 1 to 5 | Verified in page |
| E9 | POD cache | datastore | Redis; Memorystore Not confirmed | Holds each normalised POD for 3,600 seconds, keyed by carrier and consignment. | none | Page 353861642, step 2. Page 354877489, "Behaviour all the modules share" | Verified in page |
| E10 | gfs-carrier-credentials | system | | Legacy credentials service. Returns a contract's carrier account on request. | none | Page 353861642, Credentials row. Page 354877489, "Behaviour all the modules share" | Verified in page |
| E11 | REST carrier modules | component | HTTPS, REST | DHL Parcel UK (eCommerce), DPD, DPD Local, Evri, UPS, FedEx, Yodel, Panther, Amazon. Fetch POD and image. | Carrier modules | Page 354877489, "The carriers at a glance" | Verified in page |
| E12 | SOAP carrier modules | component | SOAP | UK Mail (the old DHL Parcel UK module) and Tuffnells. Fetch the POD, then the image URL. | Carrier modules | Page 354877489, "DHL Parcel UK", "Tuffnells" | Verified in page |
| E13 | BJS page-scrape module | component | HTTP page scrape | BJS has no POD API. Reads the stored link, then scrapes the ePOD page for the signature. | Carrier modules | Page 354877489, "BJS" | Verified in page |
| E14 | Carrier APIs | system | | The carriers' own POD and tracking APIs, plus BJS's ePOD web pages. | none | Page 353861642, "Carriers" table | Verified in page |
| E15 | Amazon proxy | system | | GFS's internal Amazon proxy. Returns Amazon Logistics tracking and pre-signed image links. | none | Page 354877489, "Amazon Logistics UK" | Verified in page |
| E16 | Geocode service | system | | Gives map coordinates for GFS's shipment address on v2. Owner and interface not stated. | none | Page 353861642, "How it works", Other calls row | Verified in page |
| E17 | SendGrid | system | | Third-party email service that sends POD emails. | none | Page 353861642, Other calls row. `Engineering/gfs-pod-service/overview.md` | Verified in page |

Counts: 17 elements, made up of 8 systems (E1, E2, E3, E10, E14, E15, E16, E17), 2 containers (E4, E5), 5 components (E6, E8, E11, E12, E13) and 2 datastores (E7, E9).

## Relationships

| From ID | To ID | Label | Technology or message | Status |
| --- | --- | --- | --- | --- |
| E4 | E6 | Deliver each identified shipment | Pub/Sub message | Verified in page |
| E5 | E6 | Deliver BJS tracking events that carry detail links | Pub/Sub message | Verified in page |
| E6 | E7 | Upsert the shipment copy and store the BJS detail link | MongoDB write | Verified in page |
| E1 | E8 | Request a POD by shipment ID | HTTP GET /pod/:shipmentId (v2, in-cluster) | Verified in page |
| E2 | E8 | Request a consignment's POD | HTTP, v2 API. The route Connect calls is not stated | Verified in page |
| E3 | E8 | Request a POD by shipment ID | HTTP GET pod/:shipmentId (v2) | Verified in page |
| E8 | E7 | Look up the carrier and consignment for the shipment | MongoDB read | Verified in page |
| E8 | E9 | Check the cache, then store the normalised POD | Redis, 3,600 second expiry | Verified in page |
| E8 | E11 | On a cache miss, fetch the POD for a REST carrier | In-process call | Verified in page |
| E8 | E12 | On a cache miss, fetch the POD for a SOAP carrier | In-process call | Verified in page |
| E8 | E13 | On a cache miss, fetch the BJS POD | In-process call | Verified in page |
| E11 | E10 | Fetch credentials for DPD, DPD Local, Evri, Yodel and Panther | HTTPS GET /ccs/{carrier}/{contract}, bearer token | Verified in page |
| E12 | E10 | Fetch the UK Mail carrier-wide login on each call | HTTPS GET /ccs/{carrier}/{contract}, bearer token | Verified in page |
| E11 | E14 | Call the carrier's POD or tracking API, then fetch the image | HTTPS, REST | Verified in page |
| E12 | E14 | Call the SOAP service, then fetch the image URL | SOAP over HTTPS | Verified in page |
| E13 | E14 | Fetch the BJS ePOD page and its signature image | HTTP GET | Verified in page |
| E13 | E7 | Read the stored BJS page link | MongoDB read | Verified in page |
| E11 | E15 | Fetch Amazon Logistics tracking and image links | HTTPS GET, X-API-Key header | Verified in page |
| E8 | E16 | Geocode GFS's shipment address (v2 only) | Not stated | Verified in page |
| E11 | E16 | Look up an address from a GPS point (Evri, Yodel, Amazon) | Not stated | Not confirmed |
| E8 | E17 | Send a POD email | SendGrid API | Verified in page |

Counts: 21 relationships. Replies travel back on the same arrow as the request, so they are not drawn. The cache fill happens inside the E8 to E9 arrow.

## Layout hint

Put the three callers (E1 to E3) at the left, all pointing at the v2 POD API (E8) in the middle of the POD API Deployment group. Put the subscriber Deployment group with its two topics (E4, E5) along the top, with MongoDB (E7) and Redis (E9) between the two groups. Put the Carrier modules group at the right, with the credentials service (E10), Carrier APIs (E14) and Amazon proxy (E15) beyond it. Put the geocode service (E16) and SendGrid (E17) below.

## Key needed

- Dashed box or arrow with the label `Not confirmed`: the item is not proved by any source I read (the E11 to E16 arrow, and the Memorystore note on E9).
- Cylinder: a datastore. Plain rectangle: a component, container or external system.
- Pub/Sub icon on E4 and E5. GKE icon on the cluster group label. No other GCP icon appears, because no other product is confirmed.
- Arrows run in the direction of the request.
- The carrier module boxes list their carriers in the description. They stand for one module per carrier, 11 carriers in all.
- The test carrier `MOCKCARRIER` is loaded in prod but not drawn. The DHL Express module is not loaded and not drawn.

## Gaps

- **Redis hosting is unknown.** The pages say Redis only. Whether it is Memorystore, and whether it sits in the cluster, is Not confirmed. The same goes for where MongoDB runs.
- **Where OAuth tokens are cached is unknown.** Page 353861642 says tokens are cached until they expire. It does not say if the store is Redis or process memory, so no arrow is drawn.
- **Active DHL Parcel UK module is unknown in prod.** Page 353861642 says a prod setting moves it off the UK Mail SOAP service. Page 354877489 says the repo does not set that flag and the prod value is Not confirmed. So E12's UK Mail module may be idle, and E11's DHL eCommerce module may carry the traffic. Both are drawn because both are loaded.
- **The DHL image service name is unconfirmed.** Page 353861642 says images come through `dhl-pod-images`. Page 354877489 found no such name in the repo, only an `imageHrefResolver` setting that defaults to localhost. I left it off the diagram.
- **The Amazon proxy instance is not pinned.** Page 353861642 names `amazon-logistics-proxy-internal`. Page 354877489 says the base URL is not in the repo. E15 shows the proxy, not a named instance.
- **The geocode service is thin.** The pages say "a geocode service" with no name, owner or protocol. Page 354877489 mentions a separate address lookup from a GPS point for Evri, Yodel and Amazon. Whether that is the same service is Not confirmed, so that arrow is dashed.
- **Callers' exact routes are not all known.** Connect's own route is given (`GET /connect/consignment/{gfsId}/pod`), but the route it calls on this service is not. The traffic split between the three callers is not known either.
- **The POD email path is unclear.** Page 353861642 lists "a request POD email to the call centre, about 205 in 15 days" among the callers, and elsewhere counts 203 emails sent. Who receives the email, and which caller triggers it, is Not confirmed.
- **Credentials do not come from the credentials service for every carrier.** UPS, FedEx, DHL eCommerce and Amazon use environment secrets. Tuffnells uses the contract as the account code. BJS has none. The arrows from E11 and E12 name only the carriers that do call it.
- **The repo's own `AGENTS.md` disagrees with prod.** It names `carrier-credentials-manager`. Prod points at the legacy `gfs-carrier-credentials`, per `Engineering/gfs-pod-service/architecture.md` guardrail G2. The diagram follows prod. A replacement date is Not confirmed.
- **Two code versions.** Page 353861642 was read at `811007e`. Page 354877489 was read at `d1f0ada`, two pull requests later. The change moved FedEx to consignment lookups. The diagram is unaffected.
- **Left off by design.** The public v1 API (no caller found), `evri-auth-facade` (Evri's token), Google Maps static maps (listed, purpose not stated), and the idle carriers' request counts. Adding them would pass the 20-box limit or add unexplained arrows.
- **Pub/Sub delivery style is unknown.** The pages do not say whether the subscriber pulls or receives pushes. The arrows say "deliver" for that reason.
- **Not checked live.** Page 354877489 states that no carrier was called. Nothing here has been run against the live service.
