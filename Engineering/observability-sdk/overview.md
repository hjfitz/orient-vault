---
tags:
- waypoint
- observability-sdk
verified: '2026-10-13'
verified_sha: d5b181f
verified_paths:
- README.md
- CLAUDE.md
- .github/workflows/publish.yaml
- .github/CODEOWNERS
- pkg/observability/package.json
title: observability-sdk — overview
thesis: observability-sdk is the ILG platform's published logs, metrics and traces
  library. Five npm packages share one ambient LogContext, and the repo has no runtime
  of its own.
confidence: high
---
# observability-sdk — overview

```orient-bluf
{ "v": 1, "bluf": "observability-sdk is the ILG platform's published logs, metrics and traces library. Five npm packages share one ambient LogContext, and the repo has no runtime of its own.", "confidence": "high", "action": "none" }
```

## Responsibility

- It publishes `@ilg-platform/observability`, `-trace`, `-nest`, `-express` and `-next` to GitHub Packages [1][3].
- One field set once (`correlationId`, `businessId`, a trace id) rides logs, metrics and traces through a shared `AsyncLocalStorage` [2].
- It owns the Datadog-shaped log format and default PII redaction. Metrics and trace backends hide behind `ILogger`, `IMetrics` and `ITracer` [2].
- It replaces the Winston, `cls-hooked` and hand-written masking that about twelve fleet services each rolled themselves [1].

## Why it exists separately

Logs, metrics and traces are an ILG-platform concern, not a Fuse one. The Fuse monorepo cannot own a library every platform service installs.

`@gfs-bifrost/observability` in `pkg-node` is the thin Fuse-shaped wrapper. It takes this SDK as an optional peer [5].

The team retired the Norse-named packages (`muninn`, `huginn`, `sleipnir`, `observability-core`). `pkg-node/pkg/observability` is an abandoned proof of concept, not prior art [2]. "Tolaria" was this library's old internal codename, not a separate system.

**ASSESSED** Matt Shaw designs and owns it. `.github/CODEOWNERS` names a single owner, and the 2026-08-24 interview in [[known-context]] says Harry consumes it and does not contribute [6].

## Neighbours

```orient-flow
{ "v": 1, "title": "observability-sdk in context",
  "nodes": [
    { "id": "sdk", "label": "observability-sdk", "sub": "5 published packages", "kind": "service", "service": "observability-sdk", "tone": "accent", "ev": [1, 3] },
    { "id": "gh", "label": "GitHub Packages", "sub": "@ilg-platform scope", "kind": "store", "ev": [3] },
    { "id": "pn", "label": "pkg-node", "sub": "@gfs-bifrost/observability 2.2.0", "kind": "service", "service": "pkg-node", "ev": [5] },
    { "id": "fapi", "label": "fapi", "sub": "core + nest adapter", "kind": "service", "service": "fapi", "ev": [5] },
    { "id": "sc", "label": "shopify-connector", "sub": "core + nest adapter", "kind": "service", "service": "shopify-connector", "ev": [5] },
    { "id": "fleet", "label": "Other services", "sub": "collector, dedupe, replay, sftp, snap-adapter, fuse-ui", "kind": "external", "ev": [5] },
    { "id": "dd", "label": "Datadog", "sub": "logs, DogStatsD, dd-trace", "kind": "external", "ev": [4] },
    { "id": "otel", "label": "OTLP backend", "sub": "metrics and traces", "kind": "external", "ev": [4] }
  ],
  "edges": [
    { "from": "sdk", "to": "gh", "label": "publish on push to main" },
    { "from": "gh", "to": "pn" },
    { "from": "gh", "to": "fapi" },
    { "from": "gh", "to": "sc" },
    { "from": "gh", "to": "fleet" },
    { "from": "fapi", "to": "dd", "label": "optional peers", "style": "dashed" },
    { "from": "fleet", "to": "dd", "style": "dashed" },
    { "from": "fleet", "to": "otel", "style": "dashed" }
  ] }
```

**ASSESSED** Nine repos at `origin/HEAD` depend on the core package at `^1.10.0` or a catalog entry. They are pkg-node, fapi, collector, dedupe-service, replay-service, sftp-connector, shopify-connector, snap-adapter and fuse-ui. fapi, shopify-connector and pkg-node also take `-nest`, and fuse-ui takes `-next` [5]. That comes from a manifest scan of local checkouts, not from the registry. No scanned manifest declares `-trace` or `-express`.

fapi is the pilot. `1.0.0` was cut after its dev deployment passed all three signals [[known-context]].

## Where the reference lives

[[architecture]] holds the package graph, the `LogContext` rules, and the logging, metrics, tracing and redaction design. Nine ADRs in `docs/adr/` carry the rationale. Read them before you change anything.

Do not trust the root `CLAUDE.md` on two points. It says "no `pretty` flag anywhere", but the Nest adapter and `Observability.use()` both take `pretty`. It also calls `1.0.0` the current stable cut, but the core package is `1.10.0` [2][4]. [[known-context]] holds the ownership and codename history.

## What deliberately isn't here

- **A required backend.** Both metrics exporters and both tracing engines are optional peers, loaded lazily. A logging-only consumer pulls neither tree.
- **`cls-hooked` and RxJS.** Correlation is a plain `AsyncLocalStorage`.
- **Engine types in the public API.** pino, hot-shots and dd-trace stay behind the `I`-prefixed contracts.
- **A deployed service.** There are no routes, no infrastructure code and no container image. `examples/harness` is a private Nest app that never ships [3].
- **Fuse-specific naming.** `@gfs-bifrost/observability` in pkg-node owns that layer.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "README.md@d5b181f" },
  { "id": 2, "kind": "code", "ref": "CLAUDE.md@d5b181f" },
  { "id": 3, "kind": "code", "ref": ".github/workflows/publish.yaml@d5b181f" },
  { "id": 4, "kind": "code", "ref": "pkg/observability/package.json@d5b181f" },
  { "id": 5, "kind": "doc", "ref": "package.json of nine consumer repos at origin/HEAD, scanned 2026-10-13", "note": "pkg-node, fapi, collector, dedupe-service, replay-service, sftp-connector, shopify-connector, snap-adapter, fuse-ui" },
  { "id": 6, "kind": "code", "ref": ".github/CODEOWNERS@d5b181f" }
] }
```
