---
title: Fuse Mocker — Go API Rewrite (Overview)
status: planning
owner: Harry Fitzgerald
created: '2026-08-22'
updated: '2026-08-22'
tags: [bifrost, fuse-mocker, golang, migration, overview]
---

# Fuse Mocker — Go API Rewrite

> **Rationale and target architecture.** Live progress lives in
> [[Bifrost/Fuse Mocker Go API/Migration State|Migration State]] — that is the single source of
> truth for what has shipped. This page is the stable "why and what", not the "where we are".

**Repo:** `~/code/fuse/fuse-mocker` (github `gfs-bifrost/fuse-mocker`, branch `main`)
**Reference services:** `~/code/fuse/snap-adapter/apps/snap-adapter` (layering + monorepo),
`~/code/fuse/fuse-tui` (the org's only modern Go repo), `~/code/fuse/collector` (Nest-shaped layering)

---

## What fuse-mocker is today

One Next.js 16 app on Cloud Run (`fuse-mocker-dev`) that publishes mock canonical Fuse
messages onto the platform's Pub/Sub topics for a chosen dev customer — one-off sends,
generated payloads, saved presets, jittered persistent schedules, burst/soak load runs, an
activity log, confirmation capture/replay, and sample ingress file downloads. It impersonates
the platform's real producers (connectors/fapi on `create_record_request`, dedupe-service on
`create_record`, the Snap poller on the confirmation topics).

Dev-only, enforced in four layers. Direct commits to `main`, no PR flow, and **every push
auto-deploys to dev**. Login creds in `~/.secrets`; API key is the `api_key` output in tfstate
`dev/fuse-mocker`.

**Measured shape** (`code/src`, 17,133 lines TS/TSX):

| area | lines | fate |
| --- | --- | --- |
| `lib/**` (prod, ex-tests) | 5,545 | **→ Go** |
| `lib/**/__test__` | 3,865 | → Go tests / parity fixtures |
| `app/api/**` route handlers | ~1,300 of 1,905 | **→ Go** |
| `modules/**/*.action.ts` | ~980 | → rewritten as typed API-client calls |
| `modules/**` React views | ~4,340 | stays TypeScript |
| `observability/`, `config.ts`, `instrumentation.ts`, `proxy.ts` | 477 | split (API half → Go) |

---

## The change

Replace the API with Go, structured and named like the other Fuse backend services, logging
through `slog`, with correlation carried in `context.Context` (Go's equivalent of the fleet's
`AsyncLocalStorage` `LogContext`).

Two decisions taken up front (2026-08-22, Harry):

1. **`fuse-mocker` becomes a poly-app monorepo** — `apps/api` (Go) + `apps/ui` (Next). Not a
   move into `fuse-devtools`. This keeps the existing DNS, HTTPS load balancer, Mongo Atlas
   cluster, `api_key` secret, Datadog dashboard `r2r-76f-65i` and Confluence page `266534922`
   in place. The LB's `url_map` already has a `path_matcher`, so `/api/*` → Go backend and
   `/` → UI backend is a small, reversible IaC change.
2. **Canonical schemas are generated, never hand-ported** — see *The hard part* below.

### What this buys, observably

Not speculation — these are properties visible in the current code:

- **The scheduler and load engine are long-running background loops.** They live in a Next.js
  `instrumentation.ts` `register()` hook and force `min_instance_count = 1`,
  `max_instance_count = 1`, `cpu_idle = false` on the Cloud Run service. That is a service
  shape, not a web-app shape.
- **The load engine fires a whole per-second batch concurrently** (`Promise.allSettled`) at up
  to 10,000/s hard-max. Goroutines and a bounded worker pool express that better than a
  fire-and-forget `void runLoop()` on a single Node event loop.
- **Every capability is reachable two ways today** — an `/api/v1` route handler *and* a
  `'use server'` action, both calling the same `lib/` function. Six capabilities exist *only*
  as server actions, with no HTTP route at all. Splitting UI from API collapses that to one
  path and makes the HTTP contract the only contract.
- **The UI already pays for the API's dependency tree** — `@gfs-bifrost/types`,
  `@gfs-bifrost/pubsub`, `@google-cloud/pubsub`, `mongodb`, `winston`, `hot-shots`, `jose` all
  ship in the Next bundle's server half.

---

## Target architecture

```
fuse-mocker/
├── apps/
│   ├── api/                        Go 1.27 — module github.com/gfs-bifrost/fuse-mocker/apps/api
│   │   ├── cmd/api/main.go
│   │   ├── internal/
│   │   │   ├── http/               controllers, middleware, dto
│   │   │   ├── core/               send, generators, scheduler, load, presets, samplefiles, capture
│   │   │   ├── adapters/           pubsub, configservice
│   │   │   ├── repositories/       the five Mongo collections
│   │   │   ├── config/             env validation + the prod refusal
│   │   │   ├── models/             GENERATED canonical types + envelope + enums
│   │   │   ├── exceptions/
│   │   │   ├── observability/      slog handler, correlation ctx, dogstatsd
│   │   │   ├── shared/
│   │   │   └── bootstrap/
│   │   ├── tools/canonschema/      the Zod→Go generator (Node, run via `make gen`)
│   │   ├── openapi.yaml            the contract both sides generate from
│   │   ├── Makefile  .golangci.yml  dockerfile  mise.toml
│   └── ui/                         Next 16 (today's `code/`), presentation only
│       └── src/lib/gen/mocker-api.client.d.ts   ← openapi-typescript, per the fuse-ui precedent
├── iac/
│   ├── env/*.tfvars                unchanged
│   └── projects/fuse-mocker/       two Cloud Run services, one LB, two backends
└── .github/workflows/
    ├── api-code-quality.yaml       Go: gofmt/build/vet/test/golangci-lint/govulncheck
    ├── ui-code-quality.yaml        today's code-quality.yaml, repointed
    ├── deploy.yaml                 both images + one terragrunt apply
    ├── tf-plan.yaml                unchanged
    └── secops.yaml                 lang: go for api, lang: ts + dep-node for ui
```

### Go layering — mirror the layer *names*, not TS idiom

`snap-adapter/apps/snap-adapter/src/` is the closest thing the fleet has to the org contract
actually implemented, and it is the model. Reviewers navigate by layer name, so the layer names
are kept exactly; file names go Go-idiomatic inside them.

Deliberately **absent**: `use-cases/` (exists in no Fuse repo), `config/user/` (the mocker's
tenant config is a read-through cache, not user config). Deliberately **present**:
`repositories/` (the mocker is Mongo-backed; `collector` is the precedent).

### The correlation model

`@gfs-bifrost/observability` v0.4.0 is the contract. A Go `correlation` package mirrors it
field-for-field over `context.Context`:

```go
type Details struct {
    CorrelationID string  // required
    BusinessID    string
    RecordType    string
    RecordID      string
    Flow          Flow    // create|confirmation|release|redrive|config|user_creation
    Channel       string
    ConnectorID   string
}
// FromContext(ctx) Details          ← Correlation.get()
// With(ctx, Details) context.Context ← Correlation.rootScope
// Child(ctx, patch) context.Context  ← Correlation.childScope (inherit + overlay)
```

Establishment, matching the fleet:
- **Inbound HTTP** — middleware mints from `x-request-id` or a fresh uuid.
- **Inbound Pub/Sub push** — the middleware's provisional id is *overwritten* from the decoded
  envelope: `metadata.correlationId → correlationId`, **`metadata.customer → businessId`**,
  `metadata.connectorId → connectorId`.
- **Per-record fan-out** — `Child`, never a mutating `Set` that lingers into the next record.
- **Outbound Pub/Sub** — spread inbound metadata, override `source`/`recordType`/`recordId`.
  Never rebuild.
- **Outbound HTTP** — `x-request-id`, read from the request context *inside* the round-tripper.
  (Note: `dedupe-service`/`sftp-connector`'s `withRequestId(fn)` evaluates `fn()` once at client
  construction, so a long-lived client stamps the first request's id on every later call. Do not
  copy that.)

### The log line

Flat JSON, no `requestor` nesting — the nested shape was deliberately retired and
`dedupe-service`'s `telemetry.e2e-spec.ts` has a test asserting `record.requestor` is undefined.

```json
{ "message": "...", "timestamp": "2026-08-22T09:14:02.113Z",
  "level": "info", "status": "info",
  "service": "fuse_mocker", "environment": "dev", "domain": "fuse",
  "source": "go", "host": "...",
  "correlationId": "mock-...", "businessId": "GADG",
  "recordType": "sales_order", "flow": "create",
  "target": "create_record_request", "messageId": "..." }
```

Traps, all observed in fleet code:
- `source` is Datadog's `ddsource` pipeline key. A message's *business* origin goes under
  **`messageSource`**, never `source`.
- No app-emitted `timestamp` on the fleet services (the intake stamps it) — but the mocker's
  current Winston pipeline *does* emit one. Match the fleet: drop it.
- `service` is a hard-coded snake_case literal (`fuse_mocker`), never read from env.
- `host` is dropped by the sidecar for SNAP metrics; irrelevant here but don't rely on it.
- Support-facing lines carry `audience: "support"`.

**Sink** — the Cloud Run stack tees logs to a file, not just stdout. `serverless-init` tails
`shared-volume/logs/*.log` off an in-memory `empty_dir` volume. So: `StdoutSink` normally, and
`Tee(stdout, /shared-volume/logs/app.log)` when `DATADOG_ENABLED=true`. A naive
`slog.NewJSONHandler(os.Stdout, …)` loses every Datadog log line.

### Metrics

DogStatsD to `localhost:8125`, namespace `fuse`, service as a **tag** not part of the name.
Names unchanged so the dashboard and any monitors keep working:
`fuse.mocker.publish{target,recordType,outcome}`, `fuse.mocker.schedule_tick`,
`fuse.mocker.load_run_message{mode,outcome}`.

The fleet auto-copies exactly four context keys onto every metric —
`{businessId, connectorId, recordType, flow}` — and **`correlationId` is deliberately excluded**
(unbounded cardinality). Reproduce that allowlist.

---

## The hard part: canonical schema parity

`@gfs-bifrost/types` is the org's single source of truth and is ~2,834 lines of Zod across 13
canonical record types. Go cannot import it. And the mocker publishes the **Zod-parsed**
envelope, so parsing is not just validation — it mutates the payload.

### Verified, not assumed (probed 2026-08-22)

All 12 record schemas the mocker uses convert cleanly via zod 4's
`z.toJSONSchema(s, { io, unrepresentable: "any", cycles: "ref" })` — 24/24 OK, input and output
modes. **But JSON Schema alone is insufficient**, and the probe showed exactly why:

| construct | JSON Schema output | recoverable from JSON Schema? |
| --- | --- | --- |
| `dateSchema` = `z.preprocess(tryDeriveDate, z.date())` | `{}` (i.e. "any") | ❌ no type at all |
| `z.string().default("")` | `{"type":"string"}` | ⚠️ only as `required(output) − required(input)`; **the default value is lost** |
| `z.coerce.number()` | `{"type":"number"}` | ❌ coercion invisible |
| `financial.dutyPaid` = `z.transform(parseBoolean)` | `{}` | ❌ |

So the generator **walks the Zod tree directly** (`schema._zod.def`). Also verified — a generic
walker over `CanonicalSalesOrderSchema` recovered:

- **9 defaults with their values** (`identifiers.shipmentId = ""`, `shipmentLines[].skuId = ""`, …)
- **38 `z.coerce.number()` fields**
- **17 pipes/transforms**, with `dates.*` distinguishable as `transform → date` (the shared
  `dateSchema`) from `financial.dutyPaid`'s bare `transform`
- **zero unhandled node types** — the walker covers the whole tree

### The approach

1. `apps/api/tools/canonschema/` — a small Node tool that imports `@gfs-bifrost/types`, walks
   the 12 record schemas + the 2 envelope schemas, and emits committed Go source: structs
   (`time.Time` for date nodes, string consts for the 5 runtime enums) plus a normalisation
   table (defaults to apply, fields to coerce, dates to parse, `dutyPaid` to `parseBoolean`).
2. `make gen` regenerates. Generated files are committed and CI fails if regenerating produces
   a diff — so a `@gfs-bifrost/types` bump can't drift silently.
3. **A golden parity harness is the actual proof.** Fixtures go through TS `safeParse` and
   through the Go validator; the two output JSONs are byte-compared. This is the gate for every
   unit that touches canonical data, and the standing detector for `types` bumps (the changelog
   shows those land often).

Date parsing must reproduce `parseDateFromString`: `/` → `-`, then `yyyy-MM-dd`, then
`dd-MM-yyyy`, then a permissive fallback.

---

## Contract sources of truth

Two generated contracts, one each direction — matching the fleet precedent where `fuse-ui`
generates typed clients from live OpenAPI (`gen-config-service-client`,
`gen-collector-service-client`, `gen-replay-api-client`).

```
apps/api/openapi.yaml
   ├── oapi-codegen         → Go server interface + request/response types
   └── openapi-typescript   → apps/ui/src/lib/gen/mocker-api.client.d.ts
```

The spec is written **first**, from the measured 20-route surface, and frozen before any handler
is implemented.

### Route namespaces — `/api/v1` and `/events/v1` only

Harry's constraint (2026-08-22): every endpoint lives under exactly one of two prefixes. Nothing
else is served. Usefully, the mocker's Cloud Run container declares **no `startup_probe`** (only
the sidecar has one, on TCP 12345), so unlike the rest of the fleet there is no infra-mandated
`/health/liveness` to carve out — the constraint can be applied literally.

`/events/v1` is for **inbound Pub/Sub push**, matching the fleet's existing vocabulary
(`/events/v1/record/create/:recordType`, `/events/v1/confirmation/ready/:recordType`, …).
`/api/v1` is for everything a human or the MCP calls.

Three routes move; the other 17 are already compliant:

| today | becomes | consequence |
| --- | --- | --- |
| `GET /api/health` | `GET /api/v1/health` | none — nothing external calls it |
| `POST /api/auth/login` | `POST /api/v1/auth/login` | the UI login page's fetch target |
| `POST /api/v1/confirmations/capture/{recordType}` | `POST /events/v1/confirmation/capture/{recordType}` | **all 10 Pub/Sub push subscriptions repoint** — IaC, part of `X3` |

`proxy.ts`'s matcher must be widened to exclude `events/v1` as well as `api/v1`, or the push
endpoint gets redirected to the login page.

---

## Invariants that must not break

Carried over from the repo `CLAUDE.md` plus what the port newly exposes:

- **Dev-only, four layers**: no prod workflow, no `prod.tfvars`, Terraform `env` validation
  rejects `prod`, config refuses to boot when `ENVIRONMENT` starts with `prod`. The Go config
  package must carry the same refusal.
- **The target registry owns the publish contract.** `recordType` stamped on the three
  cross-entity topics only (an unstamped message there is delivered to nobody); `source` /
  `broadcast` on `confirmation_ready` only, and `broadcast` is **present-or-absent, never
  `"false"`**; the three legacy topics get **zero** attributes. Attributes are always derived,
  never client-supplied.
- **Canonical validation gates every publish**, and the **parsed** envelope is what gets
  published (unknown keys stripped). `metadata.timestamp` is unix **seconds**.
- **Mock traffic is always identifiable**: `metadata.source` is `"mock"` or `"mock-<channel>"`,
  never a bare real source. `mock-` correlation ids, `MOCK-` references, references randomised
  by default.
- **Snap field lore stays true.** `mockReference` is **exactly 15 chars** (bisected live: 15
  passes, 16 fails — the `@gfs-bifrost/snap` `.max(20)` is wrong). `mockShortRef` 13 for POs.
  `order.type` ≤ 3 chars. UoM is `EA`, never `EACH`. Sales-order lines are `shipmentLines`;
  PO/RGA use `lines`. `OwnerId` mandatory at header *and* line. These comments are the only
  record of a live incident where 1,000 orders failed — port the comments, not just the code.
- **Exactly one instance owns the background loops.** Whichever service runs the scheduler and
  load engine must be `min = max = 1`, `cpu_idle = false`. Two instances double-fire every
  schedule.
- **`fuse-mcp` is a live external consumer.** Five tools (`mock-send`, `mock-generate`,
  `mock-schedule`, `mock-load-run`, `mock-activity`) hit 14 endpoints with `x-api-key`, and rely
  on the 400 body carrying structured validation issues. See the state doc's contract table.
- **10 Pub/Sub push subscriptions** point at `/api/v1/confirmations/capture/{recordType}?token=`
  on the Cloud Run URL. Repointing them is IaC, and it is part of the cutover, not an
  afterthought.

---

## What stays TypeScript

- Everything under `apps/ui/src/modules/**` React views and `app/**/page.tsx`.
- `proxy.ts` page gating (it verifies the same session cookie).
- Four client-safe `lib/` modules the views import directly and which have no server
  dependencies: `send/origin.ts`, `send/recent-orders.ts`, `observability/datadog-link.ts`,
  `observability/correlation-id.ts`.
- `apps/api/tools/canonschema/` — the generator is Node by necessity; it imports Zod.

---

## Related

- [[project_fuse_mocker]] — the accumulated field lore and round-by-round history
- [[reference_gfs_bifrost_checkouts]], [[reference_ilg_platform_workflows]]
- [[reference_cloudrun_domain_mapping_region]] — why the custom domain rides a global HTTPS LB
- [[reference_fuse_dashboards]] — Datadog dashboard `r2r-76f-65i`
- Confluence service page `266534922` (Bifrost space → Services)
