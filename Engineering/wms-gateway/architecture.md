---
tags:
- waypoint
- wms-gateway
verified_paths:
- apps/gateway/internal
- apps/gateway/openapi.yaml
- apps/gateway/tools/canonschema
- apps/gateway/Makefile
- apps/gateway/dockerfile
- iac/projects/wms-gateway
- iac/env
- .github/workflows/gen-check.yaml
verified: '2026-10-13'
verified_sha: a23a517
title: wms-gateway — architecture
thesis: 'A chi service on internal-only Cloud Run: API routes sit behind one shared
  x-api-key, the Pub/Sub push route is gated only by Cloud Run IAM, and every read
  resolves the business''s SNAP adapter through config-service and returns a validated
  canonical record.'
confidence: high
---
# wms-gateway — architecture

```orient-bluf
{ "v": 1, "bluf": "A chi service on internal-only Cloud Run: API routes sit behind one shared x-api-key, the Pub/Sub push route is gated only by Cloud Run IAM, and every read resolves the business's SNAP adapter through config-service and returns a validated canonical record.", "confidence": "high", "action": "Never grant allUsers invoker or relax ingress: the events route has no app-level auth and relies on Cloud Run IAM alone." }
```

## Guardrails

- [contract:G1] `apps/gateway/openapi.yaml` is the route contract and `bootstrap/routes_test.go` holds the router to it in both directions, including each route's auth. Add a route and its spec entry together; an unfinished route goes in `notYetBuilt`.
  — paths: apps/gateway/openapi.yaml, apps/gateway/internal/bootstrap
- [technical:G2] `canonical.gen.go` and the `# >>> canonschema:` blocks in `openapi.yaml` are generated. Never hand-edit; add the root schema to `WANTED` (and `SCHEMAS` in `embed-openapi.ts` if it belongs in the spec) and run `make gen` (`make openapi` is an alias).
  — paths: apps/gateway/internal/models/canonical, apps/gateway/tools/canonschema, apps/gateway/openapi.yaml, apps/gateway/Makefile
- [contract:G3] The response body is the bare canonical record with no `BifrostMessage` envelope; a list is the fleet's `{total, offset, count, data}` page whose items are bare records. The correlation ID rides on the `x-request-id` header, inbound and outbound.
  — paths: apps/gateway/internal/http/respond, apps/gateway/internal/http/middleware
- [technical:G4] SNAP is loosely typed, so decode it weakly (`decodeResults[T]`: `map[string]any` then `mapstructure` with `WeaklyTypedInput`), and return `schema.Parse`'s result rather than the pre-parse value.
  — paths: apps/gateway/internal/adapters/snap, apps/gateway/internal/shared/schema
- [operational:G5] The SNAP concurrency cap is set by the `snap_*` locals in Terraform and `SNAP_CONCURRENCY_LIMIT` is derived from them. Change the locals, not the code default, and remember the cap is per revision.
  — paths: iac/projects/wms-gateway/variables.tf, apps/gateway/internal/bootstrap/app.go
- [operational:G6] Log shape and metric names are a contract with Datadog. Logs must go through `observability.ResolveSink` (the sidecar tails a file, stdout alone ships nothing), and names come from `catalog.go` / `events.go`.
  — paths: apps/gateway/internal/observability
- [technical:G7] A stock position comes only from the business-filtered product catalogue, never from a stock row's embedded product. A shared SNAP host carries other businesses' products on a business's rows, and `/v2/kits` has no business field, so kit lines are read by naming the business's own kit SKUs.
  — paths: apps/gateway/internal/core/stock, apps/gateway/internal/adapters/snap

## Request path

`core/salesorder` is the reference flow and a new read endpoint should look like it. The stock routes are the exception (below).

```orient-flow
{ "v": 1, "title": "A read: sales order",
  "nodes": [
    { "id": "ctl", "label": "Controller", "sub": "http/controllers/api/v1", "kind": "step", "ev": [1, 2] },
    { "id": "uc", "label": "Use-case", "sub": "core/salesorder", "kind": "step", "service": "wms-gateway", "tone": "accent", "ev": [3] },
    { "id": "prov", "label": "snap.Provider", "sub": "adapter per business, singleflight, TTL", "kind": "step", "ev": [4] },
    { "id": "cs", "label": "config-service", "sub": "GET /backend/{businessId}", "kind": "service", "service": "config-service", "ev": [5] },
    { "id": "ad", "label": "SNAP adapter", "sub": "shared adapterclient", "kind": "step", "ev": [6] },
    { "id": "snap", "label": "SnapFulfil", "kind": "external" },
    { "id": "val", "label": "toCanonical, schema.Parse", "sub": "the validation gate", "kind": "step", "ev": [3] }
  ],
  "edges": [
    { "from": "ctl", "to": "uc", "label": "exactly one use-case" },
    { "from": "uc", "to": "prov", "label": "Get(businessId)" },
    { "from": "prov", "to": "cs" },
    { "from": "uc", "to": "ad" },
    { "from": "ad", "to": "snap" },
    { "from": "uc", "to": "val" }
  ] }
```

The controller parses params, calls one use-case and responds with `respond.JSON`. The use-case orchestrates, maps and validates [2][3].

Layers follow the org layout: `bootstrap` (wiring, `Routes`/`NewDeps`), `http`, `core`, `adapters`, `models/canonical` (generated), `shared`, `observability`, `config`, `exceptions`. Dependencies flow http → core → adapters. `http/adapterclient` sits under `http/` but is the provider-agnostic *outbound* client. It takes any `Cache` implementation, and `adapters/cache` provides the memory and Redis one [7].

### Stock is not a pass-through read

```orient-flow
{ "v": 1, "title": "Stock snapshot",
  "nodes": [
    { "id": "req", "label": "GET /stock", "sub": "list or /sku/{sku}", "kind": "step", "ev": [8] },
    { "id": "store", "label": "Snapshot store", "sub": "per business, per instance", "kind": "store", "service": "wms-gateway", "tone": "accent", "ev": [9] },
    { "id": "build", "label": "Detached build", "sub": "singleflight, one slot", "kind": "step", "ev": [9] },
    { "id": "reads", "label": "Three paged SNAP reads", "sub": "products, stock totals, kit lines", "kind": "step", "ev": [10, 11] },
    { "id": "pos", "label": "Positions", "sub": "built once per snapshot and site", "kind": "step", "ev": [12] },
    { "id": "out", "label": "Page", "sub": "Last-Modified = build start", "kind": "step", "ev": [8] },
    { "id": "to", "label": "504 upstream_timeout", "kind": "step", "tone": "alert", "ev": [9, 13] }
  ],
  "edges": [
    { "from": "req", "to": "store" },
    { "from": "store", "to": "pos", "label": "fresh" },
    { "from": "store", "to": "build", "label": "older than max age" },
    { "from": "build", "to": "reads" },
    { "from": "reads", "to": "pos" },
    { "from": "pos", "to": "out" },
    { "from": "build", "to": "to", "label": "deadline", "style": "dashed" }
  ] }
```

**CONFIRMED** `core/stock` keeps one snapshot per business, per instance [9][12]:

- It holds the SNAP products (the business-filtered catalogue), working-good stock totals (State `W`, Status `00`) and the BOM lines of the business's kits. Reads run sequentially and uncached (`Request.NoCache`), page by page, until an empty page [10][11].
- A snapshot is rebuilt on demand once it is older than `STOCK_SNAPSHOT_MAX_AGE_SECONDS` (default 270). Age counts from the build's start, which is also the response's `Last-Modified` [9][8].
- One detached, singleflight build per business runs under `STOCK_SNAPSHOT_BUILD_TIMEOUT_SECONDS` (default 50). That timeout includes the wait for one of `STOCK_SNAPSHOT_MAX_CONCURRENT_BUILDS` slots (default 1). A failed build is never cached, and a timeout is a 504 [9][13][14].
- Positions (products and kits, sorted by SKU) are built once per snapshot and site. The list and `/sku/{sku}` read the same set [12].
- A kit is a product with `Group2 = MASTERSKU` and not `UNLINK`. Its `potentialKitQty` is derived in core (`kits.go`) from its BOM and usable stock. A sub-kit's own assembled stock is spent first, the kit's own stock is never added, and a component shared by two paths has its demand summed.
- A cycle, a BOM deeper than 8, a zero-quantity line, or no open lines gives 0 and is reported [15][12].
- Products the mapping cannot take whole are skipped or lose an optional attribute, and are reported once per build [16].
- Kit lines are read in chunks of 25 named kit SKUs, because `/v2/kits` has no business field [11].

## Interfaces

**In:**

| Route | Auth | Purpose |
| --- | --- | --- |
| `GET /liveness/health` | none | Cloud Run startup probe |
| `GET /api/v1/salesorder/{businessId}/{shipmentId}` | `x-api-key` | canonical sales order |
| `GET /api/v1/stock/{businessId}` | `x-api-key` | paged positions: `offset`, `count` (default 20, max 100), repeated `sku` (max 100), `site` |
| `GET /api/v1/stock/{businessId}/sku/{sku}` | `x-api-key` | one position, summed across sites |
| `POST /events/v1/config/revision` | none in the app | Pub/Sub push |

The routes and each route's auth are listed in `openapi.yaml` and pinned to the router by `routes_test.go` [1][17].

### Authentication and exposure

**CONFIRMED** The `/api/v1` group sits behind `RequireAPIKey`: a constant-time compare of `x-api-key` against `SERVICE_AUTH_KEY`. A missing or empty header is a 401, and an empty configured key matches nothing, so it fails closed. `SERVICE_AUTH_DISABLED` turns it off and the IaC never sets it [2][18].

**CONFIRMED** The events route takes no API key, because Pub/Sub cannot send one. The app does not verify the push's OIDC token. Cloud Run IAM is the only gate [2][19].

**CONFIRMED** The Cloud Run service is not public. `cloud-run.tf` sets `ingress = "INGRESS_TRAFFIC_INTERNAL_ONLY"`, and `iam.tf` binds `roles/run.invoker` to the Pub/Sub push account and, when `caller_service_account` is set, to fapi's account. There is no `allUsers` binding anywhere in the stack [18][20]. `caller_service_account` is empty in both `dev.tfvars` and `prod.tfvars`, so only the push account can invoke the service today [21].

- **CONFIRMED** The inbound key is a Terraform `random_password` passed to the container as a plain environment variable, and exposed as a sensitive output for fapi. It is not a Secret Manager reference [18][22].
- **ASSESSED** Internal-only ingress admits the Pub/Sub push when the subscription is in the same project and targets the default `run.app` URL, as `iac/README.md` cites from Google's docs. Nothing in the repo records that a dev push succeeded.
- **UNKNOWN** Whether fapi's egress path reaches an internal-ingress Cloud Run service. `iac/README.md` lists that as open, and fapi has no gateway client yet.

### Outbound

- **config-service:** API-key auth, 2 s timeout, 2 retries. Responses are cached in a memory tier (60 s) over a Redis tier (10 min) when Redis is configured. The cached backend config includes SNAP credentials [5][23].
- **SNAP:** Basic auth per business, `SNAP_MAX_RETRY` retries (default 5), one `Limiter` shared by every business's client, a per-business circuit breaker, and singleflight on duplicate in-flight GETs. Responses are cached (`SNAP_CACHE_TTL`, default 30 min) in Redis keyed per business when Redis is configured, otherwise in memory. A live cached response is served before the limiter and breaker are consulted. Stock reads skip the cache but still take a limiter slot and go through the breaker [24][6][23].

### Persistence

None of its own. Redis (Memorystore, `BASIC` tier) is optional and holds only the two response caches. Every instance shares it. A Redis that is unreachable at boot is logged (`Dependency degraded`) and the caches run memory-only [24][25]. The provider's adapter cache and the stock snapshots are in-process, so each instance has its own and they are not consistent across instances.

### Config revision events

```orient-flow
{ "v": 1, "title": "Config revision push",
  "nodes": [
    { "id": "rev", "label": "config_revision", "sub": "push, OIDC, retry 10 to 600 s", "kind": "topic", "ev": [26] },
    { "id": "route", "label": "POST /events/v1/config/revision", "sub": "Cloud Run IAM only", "kind": "step", "service": "wms-gateway", "tone": "accent", "ev": [2, 26] },
    { "id": "uc", "label": "core/configrevision", "kind": "step", "ev": [19] },
    { "id": "cfg", "label": "Cached backend config", "sub": "memory and Redis", "kind": "store", "ev": [5] },
    { "id": "prov", "label": "Provider adapter", "sub": "dropped, rebuilt on next read", "kind": "step", "ev": [4] }
  ],
  "edges": [
    { "from": "rev", "to": "route" },
    { "from": "route", "to": "uc" },
    { "from": "uc", "to": "cfg", "label": "1. forget" },
    { "from": "uc", "to": "prov", "label": "2. invalidate" }
  ] }
```

`core/configrevision` acts on a `BACKEND_CONFIG` fragment or resource [19]. It forgets the business's cached backend config first, then drops the business's adapter from the provider, so the next read rebuilds it. Fragment data is never decoded beyond `businessId`, because it holds credentials. A resource link maps to a business through `/backends/{id}` or `/business/{id}/backend`; an unmapped link is logged and skipped.

Only the instance that receives the push is corrected. The others catch up through the memory-tier and adapter TTLs, 60 s each by default [23]. A malformed payload answers 200, an applied or ignored one 204, and a failed invalidation 503 so Pub/Sub redelivers [19][27].

## Errors

Adapters translate upstream failures into `exceptions.*` at their boundary, and `respond.DomainError` maps them to HTTP [13]:

| Case | Status | `code` |
| --- | --- | --- |
| business has no backend config | 404 | `backend_not_configured` |
| backend type is not SNAP | 501 | `backend_type_unsupported` |
| SNAP answers 401 or 403 | 502 | `backend_credentials_rejected` |
| config-service errors or times out | 503 | `config_unavailable` |
| bad query parameter | 400 | `invalid_query` |
| a stock snapshot build runs out of its deadline | 504 | `upstream_timeout` |
| not found (a SNAP "no matching entity", an unknown SKU) | 404 | none |
| `ErrNotImplemented` (mapped, but nothing returns it now) | 501 | none |
| canonical-validation failure, anything unmapped | 502 | none (the upstream misbehaved, not us) |

## Canonical layer

`tools/canonschema` turns Zod schemas into JSON Schema and then Go with `go-jsonschema`. It reads `@gfs-bifrost/types` first and `@gfs-bifrost/snap/types` second, because both export a different `SnapProductSchema` and the first wins [28]. The details that bite:

- It converts only the types listed in `WANTED`. Coercion (`z.coerce`) is not reproduced, `dateSchema` becomes `interface{}`, and discriminated unions don't compile.
- A root union makes `go-jsonschema` write an empty file without an error, so `gen-check` passes vacuously: assert the generated arm names. Roots in `UNION_ROOTS` are split into one schema per arm, named after its `type` tag (`CanonicalStockPosition` becomes `...Product` and `...Kit`).
- Schemas from the Snap package are `.optional().nullable()` and generate `interface{}` fields. Only the SNAP stock-total and kit roots collapse optional-nullable fields to pointers (`NULLABLE_AS_POINTER`). Doing it for every schema turns `SnapShipment.CustomerOrder` into a pointer that `ptr.FromAny[string]` silently reads as nil.
- `embed-openapi.ts` throws unless the schema's `# >>> canonschema:` marker pair is already in `openapi.yaml` [29].
- `gen-check` in CI fails when the committed Go output or `openapi.yaml` is stale against the pinned package versions [30].

## Runtime

Cloud Run in `europe-west2`, at most 5 instances, a 60 s request timeout, 512Mi and 1 CPU for the app. A Datadog `serverless-init` sidecar ships logs and metrics to both the GFS and ILG accounts. Direct VPC egress carries private-range traffic (Redis); config-service, SNAP and Datadog use the managed public path. The app runs from a distroless static image built from Go 1.27 [18][31].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "apps/gateway/openapi.yaml@a23a517" },
  { "id": 2, "kind": "code", "ref": "apps/gateway/internal/bootstrap/app.go@a23a517" },
  { "id": 3, "kind": "code", "ref": "apps/gateway/internal/core/salesorder/salesorder.go@a23a517" },
  { "id": 4, "kind": "code", "ref": "apps/gateway/internal/adapters/snap/provider.go@a23a517" },
  { "id": 5, "kind": "code", "ref": "apps/gateway/internal/adapters/configservice/request.go@a23a517" },
  { "id": 6, "kind": "code", "ref": "apps/gateway/internal/http/adapterclient/request.go@a23a517" },
  { "id": 7, "kind": "code", "ref": "apps/gateway/internal/http/adapterclient/adapterclient.go@a23a517" },
  { "id": 8, "kind": "code", "ref": "apps/gateway/internal/http/controllers/api/v1/stock.go@a23a517" },
  { "id": 9, "kind": "code", "ref": "apps/gateway/internal/core/stock/snapshot.go@a23a517" },
  { "id": 10, "kind": "code", "ref": "apps/gateway/internal/adapters/snap/stock.go@a23a517" },
  { "id": 11, "kind": "code", "ref": "apps/gateway/internal/adapters/snap/kits.go@a23a517" },
  { "id": 12, "kind": "code", "ref": "apps/gateway/internal/core/stock/list.go@a23a517" },
  { "id": 13, "kind": "code", "ref": "apps/gateway/internal/http/respond/respond.go@a23a517" },
  { "id": 14, "kind": "code", "ref": "apps/gateway/internal/config/config.go@a23a517" },
  { "id": 15, "kind": "code", "ref": "apps/gateway/internal/core/stock/kits.go@a23a517" },
  { "id": 16, "kind": "code", "ref": "apps/gateway/internal/core/stock/products.go@a23a517" },
  { "id": 17, "kind": "code", "ref": "apps/gateway/internal/bootstrap/routes_test.go@a23a517" },
  { "id": 18, "kind": "code", "ref": "iac/projects/wms-gateway/cloud-run.tf@a23a517" },
  { "id": 19, "kind": "code", "ref": "apps/gateway/internal/core/configrevision/configrevision.go@a23a517" },
  { "id": 20, "kind": "code", "ref": "iac/projects/wms-gateway/iam.tf@a23a517" },
  { "id": 21, "kind": "code", "ref": "iac/env/prod.tfvars@a23a517" },
  { "id": 22, "kind": "code", "ref": "iac/projects/wms-gateway/outputs.tf@a23a517" },
  { "id": 23, "kind": "code", "ref": "apps/gateway/internal/config/config.go@a23a517", "note": "cache TTLs, SNAP retries and breaker defaults" },
  { "id": 24, "kind": "code", "ref": "apps/gateway/internal/bootstrap/app.go@a23a517", "note": "newSnapCache, getSnapBuilder, ConnectRedis" },
  { "id": 25, "kind": "code", "ref": "iac/projects/wms-gateway/cache.tf@a23a517" },
  { "id": 26, "kind": "code", "ref": "iac/projects/wms-gateway/pubsub.tf@a23a517" },
  { "id": 27, "kind": "code", "ref": "apps/gateway/internal/http/controllers/events/v1/configrevision.go@a23a517" },
  { "id": 28, "kind": "code", "ref": "apps/gateway/tools/canonschema/src/index.ts@a23a517" },
  { "id": 29, "kind": "code", "ref": "apps/gateway/tools/canonschema/src/embed-openapi.ts@a23a517" },
  { "id": 30, "kind": "code", "ref": ".github/workflows/gen-check.yaml@a23a517" },
  { "id": 31, "kind": "code", "ref": "apps/gateway/dockerfile@a23a517" }
] }
```
