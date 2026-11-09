---
tags: [c4, architecture, c4-component]
service: ups-proxy
level: component
source_repo: /home/hjf/code/apiky-survey/ado/GFS_UPS_Integration
source_sha: bacc88136ae8ffae7b3c50a4fb718c88b6acffd5
generated: 2026-11-09
confidence: high  # every in-boundary file was read at this sha; only the callers and the logging and metrics destinations are not source-backed
---
# ups-proxy: C4 components

ups-proxy checks the ApiKy key, then forwards UPS XML unchanged or maps JSON onto UPS's JSON APIs, using one cached OAuth token.

```orient-flow
{ "v": 1, "preset": "c4-component", "title": "Component diagram: ups-proxy (what the diagram does not show: config, logger, build and deploy)",
  "groups": [ { "id": "proxy", "label": "ups-proxy (Node/Express container)", "icon": "gke" } ],
  "nodes": [
    { "id": "app", "label": "Express app", "tech": "express, cors", "sub": "Body parsers, request id, route mounts", "kind": "step", "group": "proxy" },
    { "id": "metrics", "label": "Metrics middleware", "tech": "gfs-metrics", "sub": "Request count and timing per route", "kind": "step", "group": "proxy" },
    { "id": "apikey", "label": "ApiKy key check", "tech": "express middleware", "sub": "Validates x-api-key on every /api call", "kind": "step", "group": "proxy" },
    { "id": "ssrouter", "label": "Stepping-stone router", "tech": "express.Router", "sub": "5 POST routes, one UPS URL each", "kind": "step", "group": "proxy" },
    { "id": "sshandler", "label": "XML passthrough handler", "tech": "axios", "sub": "Forwards body unchanged, returns UPS reply", "kind": "step", "group": "proxy" },
    { "id": "v2router", "label": "V2 router", "tech": "express.Router", "sub": "5 JSON routes", "kind": "step", "group": "proxy" },
    { "id": "v2ship", "label": "V2 shipping handlers", "tech": "axios", "sub": "createLabel, getLabel, cancel", "kind": "step", "group": "proxy" },
    { "id": "v2ap", "label": "V2 access-point handlers", "tech": "axios", "sub": "Search and get by id", "kind": "step", "group": "proxy" },
    { "id": "xform", "label": "Shipment transformers", "tech": "plain JS", "sub": "7 ordered country rules on createLabel", "kind": "step", "group": "proxy" },
    { "id": "mappers", "label": "UPS mappers", "tech": "plain JS", "sub": "GFS JSON to UPS request and back", "kind": "step", "group": "proxy" },
    { "id": "token", "label": "UPS token client", "tech": "axios, lru-cache", "sub": "Client-credentials token, cached per client id", "kind": "step", "group": "proxy" },
    { "id": "errors", "label": "Error handler", "tech": "express error middleware", "sub": "Typed errors to one JSON error model", "kind": "step", "group": "proxy" },
    { "id": "health", "label": "Health probes", "tech": "lightship", "sub": "Ready and live on port 9001, delayed shutdown", "kind": "step", "group": "proxy" },
    { "id": "selector", "label": "Selector callers (CSS, Client4)", "sub": "Legacy UPS XML clients", "kind": "external", "unconfirmed": true },
    { "id": "apiky", "label": "ApiKy", "tech": "HTTPS API", "sub": "Key and profile lookup", "kind": "external" },
    { "id": "upsoauth", "label": "UPS OAuth", "tech": "HTTPS", "sub": "/security/v1/oauth/token", "kind": "external" },
    { "id": "upsxml", "label": "UPS XML API", "tech": "HTTPS, XML", "sub": "ups.app/xml and LBRecovery", "kind": "external" },
    { "id": "upsjson", "label": "UPS JSON APIs", "tech": "HTTPS, JSON", "sub": "Shipments, labels, locations", "kind": "external" },
    { "id": "dd", "label": "Datadog", "tech": "logs and metrics", "sub": "Receives logs and metrics", "kind": "external" },
    { "id": "kube", "label": "Kubernetes probes", "tech": "kubelet", "sub": "Readiness and liveness checks", "kind": "external" }
  ],
  "edges": [
    { "from": "selector", "to": "app", "label": "POST XML with x-api-key", "unconfirmed": true },
    { "from": "app", "to": "metrics", "label": "wraps every request" },
    { "from": "app", "to": "apikey", "label": "mounts on /api" },
    { "from": "apikey", "to": "apiky", "label": "GET /api/profile?token=" },
    { "from": "apikey", "to": "ssrouter", "label": "/api/stepping-stone if key valid" },
    { "from": "apikey", "to": "v2router", "label": "/api/v2 if key valid" },
    { "from": "apikey", "to": "errors", "label": "401 no key, 403 bad key" },
    { "from": "ssrouter", "to": "sshandler", "label": "UPS target URL per route" },
    { "from": "sshandler", "to": "token", "label": "authorize()" },
    { "from": "sshandler", "to": "upsxml", "label": "XML body unchanged, Bearer" },
    { "from": "sshandler", "to": "dd", "label": "logs full XML bodies" },
    { "from": "v2router", "to": "v2ship", "label": "createLabel, getLabel, cancel" },
    { "from": "v2router", "to": "v2ap", "label": "search, get by id" },
    { "from": "v2ship", "to": "token", "label": "authorize()" },
    { "from": "v2ap", "to": "token", "label": "authorize()" },
    { "from": "v2ship", "to": "xform", "label": "createLabel request" },
    { "from": "v2ship", "to": "mappers", "label": "build request, map response" },
    { "from": "v2ap", "to": "mappers", "label": "map DropLocation" },
    { "from": "v2ship", "to": "upsjson", "label": "ship, label recovery, void" },
    { "from": "v2ap", "to": "upsjson", "label": "locator search" },
    { "from": "v2ship", "to": "errors", "label": "UPSApiError on 400" },
    { "from": "v2ap", "to": "errors", "label": "UPSApiError, not found" },
    { "from": "token", "to": "upsoauth", "label": "POST client_credentials, Basic" },
    { "from": "errors", "to": "selector", "label": "JSON error model", "unconfirmed": true },
    { "from": "metrics", "to": "dd", "label": "request counts and timings", "unconfirmed": true },
    { "from": "kube", "to": "health", "label": "GET /ready, /live on 9001" },
    { "from": "app", "to": "health", "label": "signalReady, shutdown hook" }
  ] }
```

## Elements

| id | name | kind | tech | responsibility | source path |
|---|---|---|---|---|---|
| app | Express app | step | express, cors, uuid | Builds the app: CORS, json/text/raw(application/xml)/urlencoded parsers, request id, mounts `/api/stepping-stone` and `/api/v2`, `GET /`, listens on `PORT` (default 9000); `index.js` starts it when `API_ENABLED=true` | `src/startup.js:14-45`, `index.js:7-22` |
| metrics | Metrics middleware | step | gfs-metrics | Counts requests and timings by `req.name` and status; counts errors by error class | `src/api/middleware/metrics.js:19-37` |
| apikey | ApiKy key check | step | express middleware, axios | Reads `x-api-key`, calls ApiKy, stores the profile on `req.principle`; 401 if missing, 500 on an ApiKy 500, otherwise 403 | `src/api/middleware/express-apiky-middleware.js:6-30` |
| ssrouter | Stepping-stone router | step | express.Router | POST `/shipConfirm`, `/shipAccept`, `/locator`, `/void`, `/labelRecovery`, each bound to a hard-coded UPS URL | `src/api/routes/index.js:6-16`, `src/config.js:5-13` |
| sshandler | XML passthrough handler | step | axios | Gets a token, logs the body, POSTs it unchanged to the target with a Bearer token, returns UPS's status and body as `application/xml` | `src/api/routes/stepping-stone.js:8-49` |
| v2router | V2 router | step | express.Router | Five routes: get access point, search access points, cancel, get label, create label | `src/api/routesV2/index.js:8-19` |
| v2ship | V2 shipping handlers | step | axios | `create-label`, `get-label`, `delete-shipping`: each authorises, builds a UPS JSON request, calls UPS, maps the reply | `src/api/routesV2/create-label.js:12-126`, `get-label.js:8-64`, `delete-shipping.js:7-32` |
| v2ap | V2 access-point handlers | step | axios | `get-access-point` and `search-access-points`: build a UPS Locator request, map `DropLocation` | `src/api/routesV2/get-access-point.js:8-54`, `search-access-points.js:9-61` |
| xform | Shipment transformers | step | plain JS | Reduces the createLabel request through canary-islands, china, norway, eu-to-gb, gb-to-eu, gb-to-rest, domestic, in that order | `src/api/routesV2/transformers/index.js:9-19` |
| mappers | UPS mappers | step | plain JS | `customer`, `package-code`, `form-type` build UPS request fields; `shipment`, `label`, `access-point` map UPS replies to GFS JSON | `src/api/routesV2/mapping/` |
| token | UPS token client | step | axios, lru-cache | One client id/secret from env; LRU cache (max 1000) keyed by client id, TTL `expires_in` minus 60 s | `src/auth.js:7-48` |
| errors | Error handler | step | express | Maps errors carrying `httpStatusCode` to `{errorId, errorCode, messages, metadata}`, 500 otherwise | `src/api/middleware/error-handler.js:27-44`, `src/errors.js` |
| health | Health probes | step | lightship | Probe server on `HEALTH_PORT` (default 9001); on shutdown waits 2 s, goes not-ready, waits 5 s | `src/lightship.js:6-18` |
| selector | Selector callers (CSS, Client4) | external | n/a | Legacy clients that send UPS XML | not in source; Waypoint `overview.md` |
| apiky | ApiKy | external | HTTPS | `https://apiky.gfsdeliver.com/api/profile` | `src/api/middleware/express-apiky-middleware.js:15-18` |
| upsoauth | UPS OAuth | external | HTTPS | `${UPS_ENDPOINT}/security/v1/oauth/token` | `src/auth.js:18` |
| upsxml | UPS XML API | external | HTTPS, XML | `onlinetools.ups.com/api/ups.app/xml/*` and `/api/webservices/LBRecovery` | `src/config.js:5-13` |
| upsjson | UPS JSON APIs | external | HTTPS, JSON | `/api/shipments/v2403/ship`, `/api/shipments/v1/void/cancel/*`, `/api/labels/v1/recovery`, `/api/locations/v2/search/availabilities/{1,64}` | `src/api/routesV2/*.js` |
| dd | Datadog | external | logs, metrics | Logger is built with `useDataDog: true`; metrics go through `gfs-metrics` | `src/logger.js:3-6`, `k8s/config.yaml` |
| kube | Kubernetes probes | external | kubelet | `/ready` and `/live` probes on port 9001 | `k8s/config.yaml` (probe blocks) |

## Relationships

| from | to | label | protocol / topic | confirmed |
|---|---|---|---|---|
| selector | app | POST XML with x-api-key | HTTP | no |
| app | metrics | wraps every request | in-process | yes |
| app | apikey | mounts on /api | in-process | yes |
| apikey | apiky | GET /api/profile?token= | HTTPS | yes |
| apikey | ssrouter | /api/stepping-stone if key valid | in-process | yes |
| apikey | v2router | /api/v2 if key valid | in-process | yes |
| apikey | errors | 401 no key, 403 bad key | in-process | yes |
| ssrouter | sshandler | UPS target URL per route | in-process | yes |
| sshandler | token | authorize() | in-process | yes |
| sshandler | upsxml | XML body unchanged, Bearer | HTTPS, XML | yes |
| sshandler | dd | logs full XML bodies | logger (gfs-logging) | yes, call site only; shipping lives in the library |
| v2router | v2ship | createLabel, getLabel, cancel | in-process | yes |
| v2router | v2ap | search, get by id | in-process | yes |
| v2ship | token | authorize() | in-process | yes |
| v2ap | token | authorize() | in-process | yes |
| v2ship | xform | createLabel request | in-process | yes |
| v2ship | mappers | build request, map response | in-process | yes |
| v2ap | mappers | map DropLocation | in-process | yes |
| v2ship | upsjson | ship, label recovery, void | HTTPS, JSON | yes |
| v2ap | upsjson | locator search | HTTPS, JSON | yes |
| v2ship | errors | UPSApiError on 400 | in-process | yes |
| v2ap | errors | UPSApiError, not found | in-process | yes |
| token | upsoauth | POST client_credentials, Basic | HTTPS | yes |
| errors | selector | JSON error model | HTTP | no |
| metrics | dd | request counts and timings | gfs-metrics | no |
| kube | health | GET /ready, /live on 9001 | HTTP | yes, probe side only |
| app | health | signalReady, shutdown hook | in-process | yes |

## Not confirmed / open questions

- **Selector callers (node and two edges).** The source never names a caller; it only reads `x-api-key` and parses `application/xml`. CSS and Client4 come from Waypoint `overview.md` (verified at the same sha, 2026-11-06), not from this repo.
- **metrics to Datadog.** `src/metrics.js` wraps `gfs-metrics`; `node_modules` is not installed, so the destination is not visible. `DD_AGENT_HOST` in `k8s/config.yaml` suggests an agent but proves nothing about the library.
- **sshandler to Datadog (logs).** The call site and `useDataDog: true` are in source; `gfs-logging` was not read. Marked confirmed, with that caveat.
- **Probe paths.** The manifest probes `/ready` and `/live` on 9001 and `config.js` sets port 9001. The paths served by lightship come from the library, which was not read.
- **Production routing.** The host `ups.gfsdeliver.com` and cluster name are in Waypoint only. `k8s/config.yaml` shows a `fenghuang-gfs-ups-proxy` Deployment, which may be the dev manifest.
- **Left out on purpose.** `config.js` and `logger.js` are read by nearly every box and would add edges to everything. `src/code.js` is a scaffold stub. `api/swagger.yaml` and `express-openapi-validator` (in `package.json`) are not wired into `src/`, so no request validation exists.
- **Docs drift found.** Waypoint `architecture.md` lists the transformers alphabetically; the code order is canary-islands, china, norway, eu-to-gb, gb-to-eu, gb-to-rest, domestic.
- **Observation, not a component.** The ApiKy check writes `req.principle.profile`; nothing else in `src/` reads it, so ApiKy only gates access.

## Sources

- Repo `/home/hjf/code/apiky-survey/ado/GFS_UPS_Integration`, branch `master`, HEAD `bacc88136ae8ffae7b3c50a4fb718c88b6acffd5` ("Merged PR 12584: URL Change", 2025-06-05), clean tree.
- Read in full: `index.js`; `src/{startup,auth,config,errors,lightship,logger,metrics,utils,code}.js`; `src/api/middleware/*`; `src/api/routes/*`; `src/api/routesV2/{index,create-label,delete-shipping,get-label,get-access-point,search-access-points}.js`; `mapping/{access-point,label,shipment}.js`; `transformers/{index,canary-islands,china,domestic}.js`. Opened only to confirm usage by grep: `mapping/{customer,package-code,form-type}.js`, `transformers/{norway,eu-to-gb,gb-to-eu,gb-to-rest}.js`. Also `k8s/config.yaml` (first 140 lines), `catalog-info.yaml`, `package.json` (grep).
- Waypoint context, not ground truth: `~/Documents/obsidian/Engineering/ups-proxy/{waypoint.yaml,overview.md,architecture.md,known-context.md}`; `wp stale ups-proxy` reported no doc behind its verified paths.
- Fuse MCP `lookup-service ups-proxy`: not found (legacy ADO service, not in the Fuse catalog), so no cross-check was possible.
