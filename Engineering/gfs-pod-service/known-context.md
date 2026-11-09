---
tags: [waypoint, gfs-pod-service]
verified: 2026-11-06
---
# gfs-pod-service — known context

Surveyed 2026-11-06 from the repo, the prod manifest, ECM's docs and Datadog. No interview.

## Ownership
- **Team "carriers"**, per ECM's `repos.json`. John Finney makes most commits (28 of 33 in 2026); Darren Rielly made the rest. The last commit was on 2026-11-06.
- The source is in its own Azure DevOps project, **GFS POD**. ECM treats it as read-only and not ECM-owned.

## Traffic (snapshot 2026-11-06, 15 days)

| Measure | Count |
| --- | --- |
| POD requests | 20,978 |
| PODs served | 19,194 |
| Images served | 5,545 |
| POD emails sent | 203 |
| Request errors | 25,878 (includes not-found PODs) |
| Subscriber messages | about 7.8M |

Requests by carrier are under **Carriers** below.

## Carriers

From the repo at `811007e` (`src/pod-service/load-services.js`, `src/config.js`) and the prod manifest `pod-server/pod-service.yaml`. Requests are for the 15 days to 6 Nov, from Datadog `gfs.gfs_pod_service.*` (snapshot 2026-11-06).

| Carrier | How it gets the POD | Requests |
| --- | --- | --- |
| DHL Parcel UK (UK Mail) | DHL Parcel UK REST API (`api.dhl.com/parceluk`). The prod flag `DHLECOMMERCEUK_USEINSTEADOFUKMAIL=true` moves it off the old UK Mail SOAP. Images come through the internal `dhl-pod-images` service | ~17.6k |
| DPD | DPD customer REST API (`api.customers.dpd.co.uk`), per-contract credentials | ~2.3k |
| UPS | UPS Track API, OAuth, GFS's own client (a k8s secret) | 865 |
| Evri (Hermes) | Evri client-tracking API. The token comes from `evri-auth-facade`, the same one the Evri connectors use | 95 |
| DPD Local | Same code as DPD | 78 |
| Amazon Logistics UK | Through `amazon-logistics-proxy-internal` | 12 |
| BJS | Scrapes BJS's ePOD web pages and the signature image. Not an API | 1 |
| Yodel | Yodel tracking API, OAuth | 0 |
| Panther | Panther order API, plus its portal for PDFs | 0 |
| Tuffnells | Tuffnells POD SOAP service | 0 |
| FedEx | FedEx Track API, OAuth | 0 |

- **Also loaded:** `MOCKCARRIER`, a test carrier, in prod.
- **Not loaded:** the DHL Express module. Its prod URL is literally `'???'`.
- **Per-contract credentials** come from the legacy `gfs-carrier-credentials` service.
- **No POD support, despite volume:** Royal Mail (the busiest proxied carrier), Nightfreight/DX, Parcelforce, GFS International, InPost, Coll8, OCS and Exelot.

## Surprises
- **DHL Parcel UK is ~85% of POD requests** but only ~22% of the carrier volume that can be measured (snapshot 2026-11-06).
- **The repo's `AGENTS.md` says credentials come from `carrier-credentials-manager`.** Prod points at the legacy `gfs-carrier-credentials` service.
- **The public ingress rule isn't bound to its host.** In the manifest, `host` and `http` are separate list items, so the `/gfs-pod/*` path matches any host on that load balancer. Class-level; worth tidying.
- **DPD Local consignment PODs aren't supported** by the gateway or Connect (carrier `19`). They pick the delivered parcel instead.
- **gfs-smart-pod-service** has a disabled repo in `fenghuang` and is commented out of prod config.

## Unknowns
- Why errors (25.9k) exceed requests (21.0k). Possibly not-found PODs plus image errors, counted per call.
- Whether anything still calls the public v1 API.
- When the legacy `gfs-carrier-credentials` service will be replaced by `carrier-credentials-manager`.
- Whether any carrier without a POD module sends POD details inside its tracking events instead, such as a signatory in the Royal Mail webhook.
