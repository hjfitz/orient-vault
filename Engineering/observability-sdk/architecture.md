---
tags:
- waypoint
- observability-sdk
verified: '2026-10-13'
verified_sha: d5b181f
verified_paths:
- pkg
- docs/adr
- .github
- pnpm-workspace.yaml
- CLAUDE.md
title: observability-sdk — architecture
thesis: A pnpm workspace of one core package, a separate tracing package and three
  framework adapters, all reading one globalThis-pinned AsyncLocalStorage LogContext;
  published by version bump on push to main.
confidence: high
---
# observability-sdk — architecture

```orient-bluf
{ "v": 1, "bluf": "A pnpm workspace of one core package, a separate tracing package and three framework adapters, all reading one globalThis-pinned AsyncLocalStorage LogContext; published by version bump on push to main.", "confidence": "high", "action": "Never create a second AsyncLocalStorage, and never init a tracer anywhere except the line-1 observability-trace/init import." }
```

## Guardrails

- [technical:G1] There is exactly one ambient store: a `globalThis`-pinned `AsyncLocalStorage` under `Symbol.for("ilg.observability.log-context.store")`. Never create a second one or break the pin; two stores mean context stops flowing between signals and packages.
  — paths: pkg/observability/src/common/context/log-context.ts
- [technical:G2] The tracer inits only through the line-1 `observability-trace/init` import, never from a framework provider or constructor. `init.ts` imports `LogContext` from `observability/common/context`, never the root barrel, because the barrel pulls `node:http` before the tracer patches it. The Nest adapter takes a structural `TracerLike` and has no dependency on `observability-trace`.
  — paths: pkg/observability-trace/src/init.ts, pkg/adaptors/observability-nest/src/modules/observability.module.ts, pkg/adaptors/observability-nest/package.json
- [contract:G3] No engine or SDK type crosses the public API. Consumers see `ILogger`, `IMetrics` and `ITracer`, built only through `Log.create()`, `Metrics.create()` and `Trace.create()`. The `I`-prefixed contracts are `export type`, never `interface`.
  — paths: pkg/observability/src/index.ts, pkg/observability/src/log/logger/log.ts, pkg/observability/src/metrics/builder/metrics.ts, pkg/observability-trace/src/builder/trace.ts
- [contract:G4] Redaction is on by default and runs before any engine. Opting out is an explicit `withoutBuiltinRedaction()` or `redaction: false`. Government ids sit in the financial class, so opting out of PII still masks them.
  — paths: pkg/observability/src/log/logger/logger.builder.ts, pkg/observability/src/log/logger/redacting-logger.ts, pkg/observability/src/log/redaction
- [contract:G5] `correlationId` and trace ids never become metric tags, because of cardinality. The context-tag allowlist stays bounded and the resolved `correlationId` is spread last so a `seedContext` extractor can enrich but not clobber it.
  — paths: pkg/observability/src/metrics/interfaces/default.ts, pkg/adaptors/observability-express/src/middlewares/correlation/correlation-middleware.ts, pkg/adaptors/observability-nest/src/middlewares/correlation/correlation.middleware.ts
- [contract:G6] A version bump merged to `main` is a permanent release. `publish_if_new` skips a `name@version` already in the registry and never overwrites it, and there is no rolling tag.
  — paths: .github/workflows/publish.yaml, pkg/observability/package.json, pkg/observability-trace/package.json

## Packages (a real pnpm workspace)

Workspace globs are `pkg/*`, `pkg/adaptors/*` and `examples/*` [3]. Intra-repo dependencies use `workspace:^`, or `workspace:*` for the private harness.

| Package | Version | Role |
| --- | --- | --- |
| `@ilg-platform/observability` (`pkg/observability`) | 1.10.0 | Core: logs, metrics and the shared substrate. Subpaths `.`, `./log`, `./metrics`, `./common/context`, `./common/correlation`, `./testing` [1] |
| `@ilg-platform/observability-trace` (`pkg/observability-trace`) | 1.0.0 | Tracing, a separate package by design (ADR-0006). Line-1 `./init` entrypoint, the only `sideEffects` file [2] |
| `@ilg-platform/observability-nest` | 1.1.0 | NestJS adapter: `ObservabilityModule.forRoot` [14] |
| `@ilg-platform/observability-express` | 2.0.0 | Express adapter: `correlationMiddleware` and re-exports of the correlation helpers only [16] |
| `@ilg-platform/observability-next` | 1.1.0 | Next.js adapter: server singleton plus edge-safe `/middleware` subpath [17] |
| `examples/{nest,express}` | private | Minimal runnable per-framework starting points |
| `examples/harness` | private, never published | Full three-signal reference. It guards cross-service correlation, ALS and `cls-hooked` interop, and the real-OTel log-to-trace bridge [21] |

```orient-flow
{ "v": 1, "title": "Workspace dependency graph",
  "nodes": [
    { "id": "obs", "label": "observability", "sub": "core: logs, metrics, LogContext", "kind": "service", "service": "observability-sdk", "tone": "accent", "ev": [1] },
    { "id": "tr", "label": "observability-trace", "sub": "engine + /init", "kind": "step", "ev": [2] },
    { "id": "nest", "label": "observability-nest", "kind": "step", "ev": [14] },
    { "id": "ex", "label": "observability-express", "kind": "step", "ev": [16] },
    { "id": "nx", "label": "observability-next", "kind": "step", "ev": [17] },
    { "id": "h", "label": "examples/harness", "sub": "private reference app", "kind": "step", "ev": [21] },
    { "id": "eg", "label": "examples/nest, express", "sub": "private", "kind": "step", "ev": [3] },
    { "id": "pm", "label": "Metrics and log peers", "sub": "hot-shots, winston, OTel metrics", "kind": "external", "ev": [1] },
    { "id": "tp", "label": "Tracer peers", "sub": "dd-trace, OTel SDK", "kind": "external", "ev": [2] }
  ],
  "edges": [
    { "from": "tr", "to": "obs", "label": "./common/context" },
    { "from": "nest", "to": "obs" },
    { "from": "ex", "to": "obs" },
    { "from": "nx", "to": "obs" },
    { "from": "h", "to": "obs" },
    { "from": "h", "to": "nest" },
    { "from": "h", "to": "tr" },
    { "from": "eg", "to": "nest" },
    { "from": "obs", "to": "pm", "label": "optional, lazy", "style": "dashed" },
    { "from": "tr", "to": "tp", "label": "optional, lazy", "style": "dashed" }
  ] }
```

Nothing reimplements the substrate. The adapters import from the `@ilg-platform/observability` root, which stays safe under classic module resolution (ADR-0007). Every package targets Node 20 or newer [1].

## The one shared `LogContext`

`run(seed, fn)` opens a scope, `set(patch)` merges onto it, and `runWith(patch, fn)` forks an isolated child scope. `get()` returns a shallow copy, so the live store never escapes [4]. The pin makes it safe for `observability-trace` to be a separate package that shares the same store.

Framework adapters seed the context in middleware, never with RxJS. `resolveCorrelationId` reads `x-correlation-id`, then `x-request-id`, then mints a UUID. Next's edge half keeps a Node-free copy [23].

```orient-flow
{ "v": 1, "title": "How one request's context reaches every signal",
  "nodes": [
    { "id": "req", "label": "HTTP request", "kind": "external", "ev": [23] },
    { "id": "mw", "label": "Correlation middleware", "sub": "nest, express, next", "kind": "step", "ev": [14, 16] },
    { "id": "ctx", "label": "LogContext", "sub": "one AsyncLocalStorage", "kind": "step", "tone": "accent", "ev": [4] },
    { "id": "tr", "label": "Tracer", "sub": "Datadog or OTel engine", "kind": "step", "ev": [11, 12] },
    { "id": "br", "label": "seedContextFromActiveSpan", "sub": "span ids to log keys", "kind": "step", "ev": [13] },
    { "id": "log", "label": "Logger", "sub": "context mixin", "kind": "step", "ev": [5] },
    { "id": "red", "label": "Redaction chain", "sub": "before the engine", "kind": "step", "ev": [6] },
    { "id": "sink", "label": "Sink", "sub": "stdout, file, HTTP, Datadog, tee", "kind": "step", "ev": [7] },
    { "id": "met", "label": "Metrics", "sub": "allowlisted context tags", "kind": "step", "ev": [9] },
    { "id": "exp", "label": "Exporter", "sub": "DogStatsD or OTLP", "kind": "step", "ev": [1] }
  ],
  "edges": [
    { "from": "req", "to": "mw" },
    { "from": "tr", "to": "br", "label": "logFields()" },
    { "from": "br", "to": "mw", "label": "seedContext" },
    { "from": "mw", "to": "ctx", "label": "run(seed)" },
    { "from": "ctx", "to": "log", "label": "mixin" },
    { "from": "log", "to": "red" },
    { "from": "red", "to": "sink" },
    { "from": "ctx", "to": "met", "label": "tags" },
    { "from": "met", "to": "exp" }
  ] }
```

## Logging

Output is Datadog-shaped JSON by default: `message` not pino's `msg`, ISO `timestamp`, `status` and `level`, `ddsource`, static base tags, and dynamic context through a mixin. The format is a swappable strategy [5].

`HumanFormat` is an SDK-owned renderer (colour plus aligned `key = value`, the same on pino and winston) with no `pino-pretty` dependency. The builder auto-selects it only when `environment` equals `development` exactly. Fleet environments `dev` and `local` never match, so the Nest `forRoot` options and `Observability.use()` take a `pretty` flag that forces `HumanFormat` or `DatadogFormat` regardless of the `environment` tag [5][8][15].

Sinks are a strategy too: `StdoutSink` (default), `FileSink`, `HttpSink`, `DatadogSink`, `TeeSink` (fan-out) and `DiscardSink`. `resolveSink` picks one from the environment: `LOGGING_DISABLED=true` gives `DiscardSink`, `OBSERVABILITY_LOG_FILE` gives a stdout-plus-file tee, and anything else gives stdout [7]. HTTP sinks are best-effort (in-memory buffer, never throw), so pair them with `TeeSink` where durability matters. `ILogger.close()` flushes, and the SDK never registers process-signal handlers itself. The Nest adapter closes the logger on `OnApplicationShutdown`.

## Metrics

The backend hides behind `IMetrics`. Output is a strategy (`IExporter`, no format layer). Both real exporters are optional peers, loaded lazily: `DogStatsDExporter` (hot-shots, the Datadog default) and `OtlpExporter` (any OTel backend). This is where metrics deliberately diverges from logging's bundled pino (ADR-0005), so a logging-only or OTLP-only consumer never pulls the other tree [1].

`ConsoleExporter` is the zero-dependency floor for dev and debug, not a production destination. `.build()` with no exporter installed throws, with no silent stdout fallback. Faceting tags ride from `LogContext` through a bounded allowlist whose default is `businessId`, `connectorId`, `recordType` and `flow`, never `correlationId` [9]. Emission is fire-and-forget. A throwing exporter is swallowed, and `TeeExporter` isolates each fan-out target. `FleetMetric` carries non-enforcing canonical name suffixes such as `event.received` and `external.failure` [10].

## Tracing

`observability-trace` hides the tracer behind `ITracer`, but the backend is an engine, not an exporter. `DatadogEngine` (dd-trace) and `OtelEngine` (OTLP) are optional peers, loaded lazily, and exactly one runs per process. There is deliberately no `TeeEngine`, so nothing is double-instrumented [2].

`/init` must load first, before instrumented libraries. This is the late-init bug the fleet's hand-rolled dd-trace setups had. It reads `SERVICE_NAME` or `DD_SERVICE` and warns when neither is set. `OBSERVABILITY_TRACE_ENGINE=otel|datadog` selects the engine, an OTLP endpoint variable infers OTel, and Datadog is the default [11][12].

`seedContextFromActiveSpan` puts the active span's ids on the shared `LogContext` under the keys each backend correlates on: `dd.trace_id` and `dd.span_id` for Datadog, `trace_id` and `span_id` for OTel. Logs then carry them and the backend links logs to traces. Trace ids ride logs, never metric tags [13].

## Redaction (ADR-0004)

A `CompositeRedactor` chain runs before any engine, on by default [6]. The key-based `CredentialsRedactor`, `FinancialRedactor` and `PiiRedactor` run first, then a value-based `CryptoRedactor` that masks PEM private-key blocks and JWTs by content wherever they sit. Consumer redactors run after the built-ins. Key masking goes by field name, and PII is never value-scanned.

- **Raw headers.** A key pattern cannot reach inside a string, so `CredentialsRedactor` masks `_header` and `rawHeaders` whole. Node's raw request preamble carries the `Authorization` line. Bare `header` is absent on purpose, because it would swallow an ordinary `headers` object [18].
- **Error names.** `PiiRedactor` keeps a bare `name` when its owner is a real `Error` (structural, any class) or its value looks error-shaped (`Error`, `Exception`, or a PascalCase token ending in one). An error's `name` and `cause.name` survive as a facet while person names stay masked [24].
- **Error walks.** The chain walks `Error` values through `ownEntries()`, since `message`, `stack` and `cause` are non-enumerable. It rebuilds copies with `blankLike()` so they stay `instanceof Error` (ADR-0004, 2026-09-17 amendment).
- **Opt-out.** `registerRedactor` adds a redactor, and `withoutBuiltinRedaction` opts out entirely.
- **`Sanitiser`.** It is the separate explicit deep-scrub tool for untrusted or forwarded payloads. It applies the same crypto value patterns, is never applied blanket, and masks an `Error`'s `name` unconditionally.

## Framework adapters (ADR-0007)

Each adapter is organised by concern with barrels. Metrics and tracing are opt-in per adapter. `ObservabilityModule` wires metrics only when `options.metrics` is present and tracing only when `options.tracer` is present, and it never inits a tracer itself [14]. Nest's `forRoot` options match `Observability.use`: `sink: "auto"`, `redaction: false` and `pretty` [15].

**Entry-point rule (ADR-0009).** `Observability.use()` and the adapters are the same bootstrap layer, so a service picks one. Nest's `forRoot` and Next's `getLogger` supersede the facade. The facade covers Express, plain Node and singletons. It logs and meters only, since the tracer must init on line 1, and it reads `service` and `environment` from `SERVICE_NAME` or `DD_SERVICE` and `ENVIRONMENT` or `DD_ENV`, never `NODE_ENV` [8][22].

The Next server entry is Node-only. The edge-safe correlation helper lives on the separate `/middleware` subpath [17].

## Testing utilities (`./testing`, ADR-0008)

These are framework-agnostic in-memory classes, never `vi.fn()` or jest mocks and never `Proxy` wrappers. Pick by what the test asserts on. **Capture fakes** (`MemorySink`, `MemoryExporter`, `MemoryEngine`) are real implementations that keep output for querying with `some`, `find` and `firstByName`. **No-ops** (`NoopLogger`, `NoopMetrics`) are inert null-objects for construction-only wiring [21].

## Build, test and publish

- pnpm 10 (`packageManager` pins 10.24.0), Node 20 or newer, Biome (tabs, double quotes), Vitest with colocated `__test__` and `__fixture__` directories, one `expect` per `it` [21].
- `pnpm -r run build` is topological and cleans `dist` first, because a stale `dist` file can shadow a directory barrel. Specs are type-checked separately by `build:check:tests`, since the build `tsc` excludes `*.spec.ts` and vitest only transpiles [20][21].
- `publish.yaml` runs on push to `main`. It publishes in dependency order (core, trace, then the three adapters) and only when `name@version` is absent from GitHub Packages. It uses `--access restricted` and the built-in `GITHUB_TOKEN` with `packages: write`, and a consumer outside `ilg-platform` needs a `read:packages` token [19][21].
- CI is one job (`install`, `build`, `build:check:tests`, `lint`, `test`, all `pnpm -r`) plus the shared SecOps workflow for dependency audit and gitleaks [20][25].
- `pnpm-workspace.yaml` carries security overrides for transitive advisories that ride optional peers of the trace and next adapters [3].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "pkg/observability/package.json@d5b181f" },
  { "id": 2, "kind": "code", "ref": "pkg/observability-trace/package.json@d5b181f" },
  { "id": 3, "kind": "code", "ref": "pnpm-workspace.yaml@d5b181f" },
  { "id": 4, "kind": "code", "ref": "pkg/observability/src/common/context/log-context.ts@d5b181f" },
  { "id": 5, "kind": "code", "ref": "pkg/observability/src/log/logger/logger.builder.ts@d5b181f" },
  { "id": 6, "kind": "code", "ref": "pkg/observability/src/log/logger/redacting-logger.ts@d5b181f" },
  { "id": 7, "kind": "code", "ref": "pkg/observability/src/log/sink/resolve-sink.ts@d5b181f" },
  { "id": 8, "kind": "code", "ref": "pkg/observability/src/facade/observability.ts@d5b181f" },
  { "id": 9, "kind": "code", "ref": "pkg/observability/src/metrics/interfaces/default.ts@d5b181f" },
  { "id": 10, "kind": "code", "ref": "pkg/observability/src/metrics/catalogue/fleet-metrics.ts@d5b181f" },
  { "id": 11, "kind": "code", "ref": "pkg/observability-trace/src/init.ts@d5b181f" },
  { "id": 12, "kind": "code", "ref": "pkg/observability-trace/src/resolve-engine.ts@d5b181f" },
  { "id": 13, "kind": "code", "ref": "pkg/observability-trace/src/bridge/context-bridge.ts@d5b181f" },
  { "id": 14, "kind": "code", "ref": "pkg/adaptors/observability-nest/src/modules/observability.module.ts@d5b181f" },
  { "id": 15, "kind": "code", "ref": "pkg/adaptors/observability-nest/src/options/module-options.type.ts@d5b181f" },
  { "id": 16, "kind": "code", "ref": "pkg/adaptors/observability-express/src/middlewares/correlation/correlation-middleware.ts@d5b181f" },
  { "id": 17, "kind": "code", "ref": "pkg/adaptors/observability-next/src/index.ts@d5b181f" },
  { "id": 18, "kind": "code", "ref": "pkg/observability/src/log/redaction/credentials-redactor/constants.ts@d5b181f" },
  { "id": 19, "kind": "code", "ref": ".github/workflows/publish.yaml@d5b181f" },
  { "id": 20, "kind": "code", "ref": ".github/workflows/ci.yaml@d5b181f" },
  { "id": 21, "kind": "code", "ref": "CLAUDE.md@d5b181f" },
  { "id": 22, "kind": "code", "ref": "docs/adr/0009-high-level-bootstrap-facade.md@d5b181f" },
  { "id": 23, "kind": "code", "ref": "pkg/observability/src/common/correlation/resolve-correlation-id.ts@d5b181f" },
  { "id": 24, "kind": "code", "ref": "pkg/observability/src/log/redaction/pii-redactor/constants.ts@d5b181f" },
  { "id": 25, "kind": "code", "ref": ".github/workflows/secops.yaml@d5b181f" }
] }
```
