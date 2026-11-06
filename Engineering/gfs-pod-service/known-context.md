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

| Requests by carrier | Count |
| --- | --- |
| DHL Parcel UK (UK Mail) | 17,607 |
| DPD | 2,310 |
| UPS | 862 |
| Evri | 110 |
| DPD Local | 77 |
| Amazon | 11 |
| BJS | 1 |

## Surprises
- **The repo's `AGENTS.md` says credentials come from `carrier-credentials-manager`.** Prod points at the legacy `gfs-carrier-credentials` service.
- **The public ingress rule isn't bound to its host.** In the manifest, `host` and `http` are separate list items, so the `/gfs-pod/*` path matches any host on that load balancer. Class-level; worth tidying.
- **DPD Local consignment PODs aren't supported** by the gateway or Connect (carrier `19`). They pick the delivered parcel instead.
- **gfs-smart-pod-service** has a disabled repo in `fenghuang` and is commented out of prod config.

## Unknowns
- Why errors (25.9k) exceed requests (21.0k). Possibly not-found PODs plus image errors, counted per call.
- Whether anything still calls the public v1 API.
- When the legacy `gfs-carrier-credentials` service will be replaced by `carrier-credentials-manager`.
