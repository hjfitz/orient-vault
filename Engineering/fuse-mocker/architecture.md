---
tags:
- waypoint
- fuse-mocker
verified: '2026-10-13'
verified_sha: 3da5077
verified_paths:
- apps
- iac
- .github/workflows
- mise.toml
title: fuse-mocker — architecture
thesis: 'A poly-app repo: apps/api (Go) publishes parsed, mock-marked canonical envelopes
  to Pub/Sub for a dev customer, apps/snap-api (Go) simulates SnapFulfil, and apps/ui
  (Next.js) fronts both, as three Cloud Run services that refuse to run in production.'
confidence: high
---
# fuse-mocker — architecture

```orient-bluf
{ "v": 1, "bluf": "A poly-app repo: apps/api (Go) publishes parsed, mock-marked canonical envelopes to Pub/Sub for a dev customer, apps/snap-api (Go) simulates SnapFulfil, and apps/ui (Next.js) fronts both, as three Cloud Run services that refuse to run in production.", "confidence": "high", "action": "Never publish an unparsed payload, never hand-edit the generated canonical layer, and keep all four dev-only checks." }
```

## Guardrails

- [technical:G1] Dev-only is enforced in four independent layers: no production workflow or `prod.tfvars`, Terraform `env` validation rejecting `prod`, and boot refusal in all three apps when `ENVIRONMENT` starts with `prod`. Never remove one because another seems to cover it.
  — paths: apps/api/internal/config/config.go, apps/snap-api/internal/config/config.go, apps/ui/src/config.ts, iac/projects/fuse-mocker/variables.tf
- [contract:G2] The target registry owns the publish contract, and attributes are derived, never client-supplied. The canonical parse gates every publish, and the PARSED envelope is what goes out. `recordType` is stamped on every filtered target, and `broadcast` is present-or-absent, never `"false"`. `metadata.timestamp` is unix seconds.
  — paths: apps/api/internal/core/publisher/targets.go, apps/api/internal/core/publisher/attributes.go, apps/api/internal/core/send/send.go
- [technical:G3] `internal/models/canonical/gen_*.go` is generated from the `@gfs-bifrost/types` Zod tree and is never hand-edited. Regenerate with `make gen` on every types bump, because no CI job checks it.
  — paths: apps/api/internal/models/canonical, apps/api/tools/canonschema, apps/api/Makefile
- [technical:G4] Exactly one process owns the scheduler and the load-run loops. The API holds them, pinned to `min = max = 1` with `cpu_idle` off, and the UI starts nothing. Do not "fix" the scaling.
  — paths: apps/api/internal/core/scheduler, apps/api/internal/core/load, iac/projects/fuse-mocker/cloud-run-api.tf, apps/ui/src/instrumentation.ts
- [contract:G5] fuse-mcp's `mock-*` tools are a live consumer of `apps/api/openapi.yaml`: 14 endpoints, `x-api-key`, and a 400's `issues` array surfaced verbatim. A response-shape change breaks them with no compile-time signal.
  — paths: apps/api/openapi.yaml, apps/api/scripts/mcp-contract-smoke.sh, apps/api/internal/http/controllers/errors.go
- [contract:G6] snap-api serves only the `/api/v2` routes it models, and every row it returns must satisfy the real poller's schemas. A poller or adapter change that calls a new SnapFulfil route needs the simulator extended in the same change.
  — paths: apps/snap-api/internal/http/snapwire/handler.go, apps/snap-api/internal/core/wms/enrichment.go

## Poly-app monorepo

```
apps/api/      Go (go.mod 1.25.1) — the mock publish path: the HTTP API and the background loops
apps/snap-api/ Go (go.mod 1.25.1) — the SnapFulfil WMS simulator, a controllable fake warehouse backend
apps/ui/       Next.js 16 — the operator UI, a presentation client over both Go APIs
iac/           Terragrunt: three Cloud Run services behind one HTTPS load balancer
```

Tool versions sit in the root `mise.toml` (Go 1.26.9, node 24, pnpm 11.0.8, terraform 1.9.0, terragrunt 0.50.8) and both Go dockerfiles build on `golang:1.26-alpine` [26]. `go.mod` still declares 1.25.1.

```orient-flow
{ "v": 1, "title": "Runtime topology: three Cloud Run services, one load balancer",
  "nodes": [
    { "id": "lb", "label": "HTTPS load balancer", "sub": "mock host and crackle host", "kind": "step", "ev": [9] },
    { "id": "ui", "label": "apps/ui", "sub": "Next.js, no route handlers", "kind": "service", "service": "fuse-mocker", "ev": [35] },
    { "id": "api", "label": "apps/api", "sub": "/api/v1, /events/v1", "kind": "service", "service": "fuse-mocker", "tone": "accent", "ev": [1, 9] },
    { "id": "snap", "label": "apps/snap-api", "sub": "/api/v1 control, /api/v2 wire", "kind": "service", "service": "fuse-mocker", "ev": [18] },
    { "id": "db", "label": "MongoDB Atlas", "sub": "one cluster, own collections", "kind": "store", "ev": [36] },
    { "id": "t", "label": "Fuse topics", "sub": "6 publish targets", "kind": "topic", "ev": [2] },
    { "id": "cs", "label": "config-service", "sub": "customer setup, read-only", "kind": "service", "service": "config-service", "ev": [10] }
  ],
  "edges": [
    { "from": "lb", "to": "ui", "label": "default" },
    { "from": "lb", "to": "api", "label": "/api, /events" },
    { "from": "lb", "to": "snap", "label": "crackle host" },
    { "from": "ui", "to": "api", "label": "server-side", "style": "dashed" },
    { "from": "ui", "to": "snap", "label": "server-side", "style": "dashed" },
    { "from": "api", "to": "db" },
    { "from": "snap", "to": "db" },
    { "from": "api", "to": "t", "label": "publish" },
    { "from": "api", "to": "cs", "label": "read", "style": "dashed" }
  ] }
```

No root `package.json` or pnpm workspace exists. The apps share no dependency tree, so run `pnpm` from `apps/ui`. Workflows are per-app and path-filtered (`api-code-quality.yaml`, `snap-api-code-quality.yaml`, `ui-code-quality.yaml`). `deploy.yaml` and `tf-plan.yaml` are shared. `secops.yaml` fans out per-app jobs: a node dependency audit on `apps/ui`, Go SAST, Go dependency audit and container scan on **each** Go app, and a Terraform scan on `iac` [16][17].

All three Cloud Run services are `allUsers`-invokable. Cloud Run IAM cannot gate one route, so each app authenticates itself [13]:

| Service | Auth |
|---|---|
| `apps/api` `/api/v1` | `x-api-key` (`MOCKER_API_KEY`) or the UI session cookie [33] |
| `apps/api` `/events/v1` | the Pub/Sub token in the push URL's query string [33] |
| `apps/snap-api` `/api/v1` | its own `x-api-key` (`CONTROL_API_KEY`) [32] |
| `apps/snap-api` `/api/v2` | per-business HTTP Basic against the tenant store [31] |

The API's `/api/v1/auth/login` checks `BASIC_AUTH_USER` and `BASIC_AUTH_PASSWORD` and mints the `session` cookie the UI carries [10][1]. `/api/v1` on snap-api is open when `CONTROL_API_KEY` is unset. That is a local-dev convenience, and the deployed service always sets it [32][11].

## `apps/api` layout — org layer names, Go idiom inside them

```
cmd/api/main.go        boot: config, logger, metrics, factory, server, signal handling
internal/bootstrap/    the only layer allowed to know everything; factory.go builds each collaborator once
internal/http/         controllers (thin, narrative) / middleware / respond
internal/core/         send/ (publish path), generators/, scheduler/, load/, samplefiles/,
                        publisher/ (target registry), capture/, seed/, auth/
internal/adapters/     pubsub/, configservice/
internal/repositories/ the five Mongo collections: activity_log, captured_confirmations,
                        load_runs, presets, schedules
internal/models/       documents + DTOs; models/canonical/ is the GENERATED canonical layer
internal/observability/ slog handler, dogstatsd client, correlation/
internal/config/       validated environment
```

There is deliberately no `use-cases/` (no Fuse repo has one) and no `config/user/` (the mocker's tenant config is a read-through cache, not user config). `internal/layering_test.go` **mechanically enforces** the dependency direction: nothing below the transport layer may import `internal/http`, and only bootstrap may import every layer [24].

## `apps/snap-api` — the SnapFulfil WMS simulator

A controllable **fake warehouse backend**, not a production WMS. snap-adapter and the poller (`snap-queue-polling-service`) call it as a business's SNAP host, so the pipeline round-trips through it. It has the same org layer names and Go idiom as `apps/api`: validated config with prod refusal, slog Datadog handler, `layering_test`, lazy Mongo. It shares the mocker's service account, Mongo cluster and Datadog keys, and uses its own `x-api-key`. It has no Pub/Sub, no config-service secret and no background loops. `apps/api` never calls it. The UI reaches it server-side through `SNAP_API_URL` and `SNAP_API_KEY` [35].

```orient-flow
{ "v": 1, "title": "snap-api: wire, control plane and the queue the poller reads",
  "nodes": [
    { "id": "sa", "label": "snap-adapter", "sub": "writes", "kind": "service", "service": "snap-adapter", "ev": [19] },
    { "id": "sq", "label": "snap-queue-polling-service", "sub": "reads, clears", "kind": "service", "service": "snap-queue-polling-service", "ev": [19] },
    { "id": "ops", "label": "Operator UI", "sub": "Snap section", "kind": "step", "ev": [18] },
    { "id": "wire", "label": "/api/v2 wire", "sub": "per-business Basic auth", "kind": "step", "service": "fuse-mocker", "tone": "accent", "ev": [19, 31] },
    { "id": "ctl", "label": "/api/v1 control plane", "sub": "x-api-key", "kind": "step", "service": "fuse-mocker", "ev": [18, 32] },
    { "id": "wms", "label": "WMS state machine", "sub": "internal/core/wms", "kind": "step", "service": "fuse-mocker", "ev": [20] },
    { "id": "q", "label": "Outbound queue", "sub": "DESPATCH, RECEIPT, STOCK_MOVE", "kind": "store", "ev": [30] },
    { "id": "db", "label": "MongoDB", "sub": "snap_entities, businesses", "kind": "store", "ev": [11] }
  ],
  "edges": [
    { "from": "sa", "to": "wire", "label": "PUT orders, products" },
    { "from": "sq", "to": "wire", "label": "GET queue, stock; PATCH processed" },
    { "from": "ops", "to": "ctl", "label": "seed, advance, adjust, arm faults" },
    { "from": "ctl", "to": "wms" },
    { "from": "wire", "to": "db" },
    { "from": "wms", "to": "q", "label": "each transition" },
    { "from": "q", "to": "db" }
  ] }
```

Two HTTP surfaces, grouped by auth so the policy is structural rather than a flag on every route (`internal/bootstrap/app.go`) [18]:

- **`/api/v2`** is the SnapFulfil WebAPIv2 wire, with per-business **HTTP Basic auth** resolved from the tenant store. A bad credential gets 401. snap-adapter writes through it and the poller reads through it.
- **`/api/v1`** is the operator control plane, with **`x-api-key`**. The Snap Simulator UI drives it to seed businesses, inventory and kits, advance orders, post stock adjustments, arm faults and watch the queue. The key is the Terraform output `snap_api_key` [11].

The `/api/v2` routes are the ones `snapwire.Mount` registers: shipments, receipts, products, product alternates, NMFC codes, kits, attachments, `snapoutbound`, stock totals (and kit totals), stock movements, stock consignment and detail, StU consignment, despatch stock and special conditions [19]. Anything else is not served.

An **active WMS state machine** (`internal/core/wms`) drives the data. Records land on the wire, and an operator advances a shipment or receipt through stages or posts a stock adjustment. Every transition drops an **outbound-queue item** (`internal/core/outboundqueue`) whose Key grammar matches what the poller parses. The poller reads it to build a confirmation, then clears it [20][30]. Stock totals move for real: receive credits, pick reserves, despatch ships out and releases. They are unclamped, so an oversold row reads negative and a Stock Sync's own clamp is what gets exercised.

The simulator is only as good as the poller's schemas. The poller parses each row against its full schema (columns nullable but present), so a row missing a column fails the fetch before any mapping runs. **ASSESSED** from the simulator's own comments, since the poller lives in another repo. Stock Detail, despatch-stock and outbound stock-consignment rows therefore carry the full column set with numeric quantities [34]. The per-line `/v2/stockmovements` routes, pick moves, work-order R10/S10 pairing and batch plumbing (`lines[]`, `batch`, `expiry`, `batches` on advance) are modelled on what live GADG SNAP returns. Closing an order stamps the completion dates SNAP sets (`DateReceipt`, `DateShipment`, `DateClosed`).

Behaviours modelled on real SNAP, each with its own test:

- `PATCH /v2/snapoutbound/{id}/processed` on an unknown id answers 200 with `{"Status":"Error"}`, not Success [19].
- Faults armed through the control plane fire on the write routes **and** on the outbound-queue clear, so the poller's clear-failure path is reachable [22].
- Stock rows differ by facility and state as well as SKU, site, owner and status. Extra key segments apply only when state is not `W` or a facility is given, so older rows keep their keys.
- `/v2/stocktotals` embeds the Product with `Group1`, takes `ne` and `/`-path `$filter`, and 400s an unknown `$orderby` with SNAP's wording. Every read reports `Successes: n/n`.
- `/v2/kits` serves one row per component line. `/v2/stocktotalskit` computes availability by assembling kits one at a time from a shared pool, resolving nested kits (`internal/core/wms/availability.go`). A row counts as usable stock when it is state W, status 00 and not `UNLINK`, at Qty minus QtyDueOut clamped at zero (`models/snap/stock.go`, `UsableStock`) [21].

The stock and kit reads are shaped for wms-gateway's end-to-end tests through a simulator-backed business.

## Dev-only, enforced in four independent layers {#dev-only}

The stack has no production Terraform workflow and no `prod.tfvars`. Terraform's own `env` variable validation rejects `"prod"` [8]. **All three** apps refuse to boot when `ENVIRONMENT` starts with `prod` [5][6][7]. These are four independent checks, not one. Do not remove any of them even if another seems to make it redundant.

## The publish path — the canonical validation gate publishes the PARSED envelope

`apps/api/internal/core/send/send.go` is the one place a message goes out [4]. The gates run in order:

1. Resolve the target and its `recordType`.
2. Reject a payload whose `identifiers.businessId` differs from the send's `businessId`. A mismatched envelope would misroute downstream.
3. Build the metadata: `customer`, a `mock-` correlation id, `timestamp`, `recordType`, `source`, `connectorId` and, on single-record envelopes, `recordId`.
4. Parse the envelope against the canonical schema. Parsing **strips unknown keys, applies defaults, coerces numbers and normalises dates**, and the *parsed* result is what gets published. `metadata.timestamp` is unix seconds.
5. Derive the attributes and publish.
6. Write an activity row. A failed activity write never reports a published message as failed. A load run writes one summary row at the end, not one per message.

A validation failure maps to 400 and a publish failure to 502. The target registry (`internal/core/publisher/targets.go`) owns the contract per target: topic, envelope shape (single or bulk), allowed record types and attribute policy. Attributes are always **derived**, never client-supplied [2][3].

| Target | Envelope | `recordType` attribute | Other attributes |
|---|---|---|---|
| `create_record_request`, `create_record` | single | stamped | none |
| `confirmation_ready` | bulk | stamped (nine types) | `source`, `broadcast` |
| `sales_order_confirmation_ready`, `purchase_order_confirmation_ready` | bulk | stamped, fixed to `goods_out_confirmation` / `goods_in_confirmation`; both publish onto `confirmation_ready` | none |
| `stock_adjustment_ready` | bulk | none (subscribers unfiltered) | none |

- Every subscription on a filtered topic filters on `recordType`, so an unstamped message is delivered to nobody. `dispatch` and `receipt` are reserved labels no filter matches. A send aimed at one publishes for real and delivers to nobody, which makes a zero-side-effect load sink.
- `broadcast` is present-or-absent, **never** the string `"false"`, because a filter testing for presence would match it.
- A push resolves its record type through a map built in registry order with later entries winning. Under `goods_out_confirmation` and `goods_in_confirmation` a push therefore resolves to the PO/SO targets, and `confirmation_ready`'s own variants are reachable only as `dispatch` and `receipt`. This reads as unintended and mirrors the TypeScript this was ported from.

Mock traffic stays identifiable. `metadata.source` is `"mock"` or `"mock-<channel>"`, never a bare real source. `connectorId` is stamped from the chosen channel's real connector, which is a pointer and not a source spoof. A confirmation send can opt into `omitSource`, which **deliberately drops `metadata.source` and the `source` attribute** rather than spoofing one. That applies only on the `/api/v1/messages` send path, since presets, schedules and load runs still stamp it. The `mock-` correlation id and `MOCK-` references always hold. References are randomised by default, because dedupe identity is `identifiers.id` plus customer, so a repeated reference gets held rather than duplicated.

## The canonical layer is generated, never hand-ported

`internal/models/canonical/gen_*.go` comes from `tools/canonschema`, which **walks the Zod definition tree** of `@gfs-bifrost/types` directly. It does not use `z.toJSONSchema()`, which is provably lossy here: the shared `dateSchema` renders as `{}`, a `.default()` keeps its presence but loses its *value*, and `z.coerce.number()` disappears entirely. Since the publisher sends the parsed record, all three would change the bytes on the wire if lost [23].

`make gen` regenerates, and `make gen-check` fails if the committed output is stale. It is a **local** gate. No workflow runs it, and the Makefile and generated-file header comments claiming CI does are wrong [15][16]. `make parity` is the drift detector in practice: fixtures run through real Zod and through the Go interpreter, and validity, failing paths and normalised output are all compared.

`gen_schema.go` last changed when `@gfs-bifrost/types` was 10.2.0. `canonschema/package.json` now resolves 10.13.0, so the committed schema has not tracked later additive fields. `stock_adjustment` has no `identifiers.movementRef` or `from`/`to` batch and expiry, and `work_order` has no `identifiers.carrierId`. The parse strips them from any published envelope [23]. **ASSESSED** The version that introduced each field comes from the org's Package Changelog, not from this repo.

Hard-won semantics encoded here, each with its own test:

- **Two date flavours, easy to conflate.** `dateSchema` (71 nodes) parses `yyyy-MM-dd` then `dd-MM-yyyy` in the **local** timezone. The one `z.coerce.date()` node (`master_data.product.maintenance.dateHeld`) is a bare JS `new Date()`. It reads the same string **month-first** and treats a bare `YYYY-MM-DD` as **UTC**. Conflating them shifts a date by months. Canonical date parsing is therefore timezone-dependent platform-wide. The same fix belongs upstream in `@gfs-bifrost/types`, not here.
- **`z.coerce.number()` reproduces JS `Number()` quirks on purpose.** `Number("")` is `0` and `Number(true)` is `1`. A stricter Go conversion would reject payloads the TypeScript accepts.
- **Three coercion conventions coexist.** Create-side records coerce numbers and parse dates. Goods-in and goods-out confirmations use plain `z.number()` and string dates. `stock_adjustment` mixes both. Do not assume create-side semantics everywhere.

## Generators — SNAP field lore lives in comments, ported deliberately

Generators are pure functions of `(seed, options, defaults, rand, clock)`. They touch no config, database or Pub/Sub and are deterministic under test. Precedence is always explicit option, then config default, then hard-coded fallback. The comments encoding SNAP's real field constraints are the only record of a live incident: a 1000-order burst that failed entirely on a 21-character reference. See [[known-context#snap-field-lore]].

## HTTP surface

Every endpoint lives under exactly one of two prefixes, by explicit constraint. Nothing else is served [1].

- **`/api/v1`** is everything a human or the MCP calls: send, validate, generate, sample files, presets, schedules, load runs, activity, captured and sent confirmations, targets, reference reads and auth. `/api/v1/health`, `/auth/login` and `/auth/logout` sit outside the auth guard.
- **`/events/v1`** is inbound Pub/Sub push only: `/events/v1/confirmation/capture/{recordType}?token=`.

```orient-flow
{ "v": 1, "title": "Inbound capture: confirmations pushed back to the mocker",
  "nodes": [
    { "id": "p", "label": "Real producers", "sub": "snap poller via snap-adapter and others", "kind": "external", "ev": [12] },
    { "id": "t", "label": "confirmation_ready", "sub": "plus stock_adjustment_ready", "kind": "topic", "ev": [12] },
    { "id": "s", "label": "10 capture subscriptions", "sub": "9 filtered by recordType, 1 unfiltered", "kind": "step", "ev": [12] },
    { "id": "a", "label": "/events/v1/confirmation/capture", "sub": "token query check", "kind": "service", "service": "fuse-mocker", "tone": "accent", "ev": [1, 33] },
    { "id": "db", "label": "captured_confirmations", "sub": "replayable from the UI", "kind": "store", "ev": [1] }
  ],
  "edges": [
    { "from": "p", "to": "t" },
    { "from": "t", "to": "s" },
    { "from": "s", "to": "a", "label": "push" },
    { "from": "a", "to": "db", "label": "capture once" }
  ] }
```

Both prefixes are served by `apps/api`. `api_serves_traffic = true` in `iac/env/dev.tfvars` (the Terraform default is `false`), so the load balancer's `/api`, `/api/*`, `/events` and `/events/*` rules point at the API backend. All ten capture push subscriptions post to the API's Cloud Run URL directly, bypassing the load balancer [9][12][14]. The flag is described in `iac` as revertible in one apply, but `apps/ui` has no route handlers left. Flipping it back routes every API client at a Next app that would 404.

The capture handler acks every permanent rejection (malformed body, unknown record type, invalid envelope) and nacks only a storage failure. A redelivered duplicate is a normal outcome and not an error.

`fuse-mcp`'s five `mock-*` tools call 14 of these endpoints with `x-api-key`. They read this stack's `api_service_url` output (the API service, not the UI's `service_url`) and depend on a 400 response's `issues` array surviving verbatim [25]. Changing a response shape here breaks that consumer silently. `apps/api/scripts/mcp-contract-smoke.sh` is the manual check, read-only by default.

## Background loops — exactly one owner

The scheduler (15 s ticker, atomic Mongo claim per due schedule) and the load-run engine both live in `apps/api` [28]. The load-run engine handles burst and soak runs with three advisory cap tiers (warn, confirm, hard max) and drift-corrected per-second batching. One concurrent run is the only invariant, and it is always hard-rejected [29]. `api_owns_background_loops = true` in `iac/env/dev.tfvars` (Terraform default `false`) sets `BACKGROUND_LOOPS_ENABLED=true`, pins the API service to `min = max = 1` and turns `cpu_idle` off [10][14]. `apps/ui`'s `instrumentation.ts` starts metrics and nothing else [27]. Two owners would double-fire every schedule.

## Build / test / deploy

- **No PR flow, by team agreement.** Work lands as direct commits to `main`, and every push auto-deploys to dev. Nothing gates that push. `api-code-quality`, `snap-api-code-quality`, `ui-code-quality` and `secops` run on `pull_request`, a 06:00 cron and manual dispatch, never on push [16][17]. Run the local gates yourself before pushing.
- `cd apps/api && make fmt-check && go build ./... && go vet ./... && TZ=UTC go test ./... && make lint`
- `cd apps/snap-api && make fmt-check && go build ./... && go vet ./... && go test ./... && make lint`
- `cd apps/ui && pnpm lint:fix && pnpm lint && pnpm test && pnpm build`
- Cloud Run runs three services behind one global HTTPS load balancer (`iac/projects/fuse-mocker/{cloud-run,cloud-run-api,cloud-run-snap-api}.tf`). The stack owns a Mongo Atlas Flex cluster that both Go services share [36], and its own `api_key` and `snap_api_key` Terraform outputs. snap-api rides the shared load balancer on its own host, `crackle.devtools.fuse.freightops.dev`, through a separate managed certificate and host rule [9][11]. The `cloud-run-snap-api.tf` header comment saying it sits behind no load balancer is stale. `PUBLIC_BASE_URL` is not set in the IaC, so the control plane's `backend-config` endpoint returns a placeholder host in dev.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "apps/api/internal/bootstrap/app.go@3da5077" },
  { "id": 2, "kind": "code", "ref": "apps/api/internal/core/publisher/targets.go@3da5077" },
  { "id": 3, "kind": "code", "ref": "apps/api/internal/core/publisher/attributes.go@3da5077" },
  { "id": 4, "kind": "code", "ref": "apps/api/internal/core/send/send.go@3da5077" },
  { "id": 5, "kind": "code", "ref": "apps/api/internal/config/config.go@3da5077" },
  { "id": 6, "kind": "code", "ref": "apps/snap-api/internal/config/config.go@3da5077" },
  { "id": 7, "kind": "code", "ref": "apps/ui/src/config.ts@3da5077" },
  { "id": 8, "kind": "code", "ref": "iac/projects/fuse-mocker/variables.tf@3da5077" },
  { "id": 9, "kind": "code", "ref": "iac/projects/fuse-mocker/load-balancing.tf@3da5077" },
  { "id": 10, "kind": "code", "ref": "iac/projects/fuse-mocker/cloud-run-api.tf@3da5077" },
  { "id": 11, "kind": "code", "ref": "iac/projects/fuse-mocker/cloud-run-snap-api.tf@3da5077" },
  { "id": 12, "kind": "code", "ref": "iac/projects/fuse-mocker/pubsub-capture.tf@3da5077" },
  { "id": 13, "kind": "code", "ref": "iac/projects/fuse-mocker/iam.tf@3da5077" },
  { "id": 14, "kind": "code", "ref": "iac/env/dev.tfvars@3da5077" },
  { "id": 15, "kind": "code", "ref": "apps/api/Makefile@3da5077" },
  { "id": 16, "kind": "code", "ref": ".github/workflows/api-code-quality.yaml@3da5077" },
  { "id": 17, "kind": "code", "ref": ".github/workflows/deploy.yaml@3da5077" },
  { "id": 18, "kind": "code", "ref": "apps/snap-api/internal/bootstrap/app.go@3da5077" },
  { "id": 19, "kind": "code", "ref": "apps/snap-api/internal/http/snapwire/handler.go@3da5077" },
  { "id": 20, "kind": "code", "ref": "apps/snap-api/internal/core/wms/wms.go@3da5077" },
  { "id": 21, "kind": "code", "ref": "apps/snap-api/internal/models/snap/stock.go@3da5077" },
  { "id": 22, "kind": "code", "ref": "apps/snap-api/internal/http/snapwire/faults.go@3da5077" },
  { "id": 23, "kind": "code", "ref": "apps/api/internal/models/canonical/gen_schema.go@3da5077" },
  { "id": 24, "kind": "code", "ref": "apps/api/internal/layering_test.go@3da5077" },
  { "id": 25, "kind": "code", "ref": "apps/api/scripts/mcp-contract-smoke.sh@3da5077" },
  { "id": 26, "kind": "code", "ref": "mise.toml@3da5077" },
  { "id": 27, "kind": "code", "ref": "apps/ui/src/instrumentation.ts@3da5077" },
  { "id": 28, "kind": "code", "ref": "apps/api/internal/core/scheduler/scheduler.go@3da5077" },
  { "id": 29, "kind": "code", "ref": "apps/api/internal/core/load/caps.go@3da5077" },
  { "id": 30, "kind": "code", "ref": "apps/snap-api/internal/core/outboundqueue/outboundqueue.go@3da5077" },
  { "id": 31, "kind": "code", "ref": "apps/snap-api/internal/http/snapwire/basicauth.go@3da5077" },
  { "id": 32, "kind": "code", "ref": "apps/snap-api/internal/http/middleware/apikey.go@3da5077" },
  { "id": 33, "kind": "code", "ref": "apps/api/internal/http/middleware/auth.go@3da5077" },
  { "id": 34, "kind": "code", "ref": "apps/snap-api/internal/core/wms/enrichment.go@3da5077" },
  { "id": 35, "kind": "code", "ref": "iac/projects/fuse-mocker/cloud-run.tf@3da5077" },
  { "id": 36, "kind": "code", "ref": "iac/projects/fuse-mocker/mongo.tf@3da5077" }
] }
```
