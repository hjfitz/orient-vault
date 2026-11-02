---
tags:
- waypoint
- pkg-node
verified: '2026-10-14'
verified_sha: a7ddb2f
verified_paths:
- .github
title: pkg-node — architecture
thesis: pkg-node is a pnpm workspace of eleven self-contained libraries that publish
  independently to GitHub Packages, gated on version number, joined by five internal
  dependency edges.
confidence: high
---
# pkg-node — architecture

```orient-bluf
{ "v": 1, "bluf": "pkg-node is a pnpm workspace of eleven self-contained libraries that publish independently to GitHub Packages, gated on version number, joined by five internal dependency edges.", "confidence": "high", "action": "Bump the version in the package.json of every package you change; an unbumped merge publishes nothing." }
```

## Guardrails

- [technical:G1] Publishing is version-gated, not diff-gated. Bump `version` in the PR for every package you change. A merge without the bump is a silent no-op for that package.
  — paths: pkg, .github/workflows/template-publish-node.yaml
- [contract:G2] `edi` stays canonical-agnostic: no `@gfs-bifrost/types` dependency and no canonical import. The consumer maps the intermediary to canonical.
  — paths: pkg/edi/package.json, pkg/edi/src
- [technical:G3] A `workspace:*` dependency does not follow a fix downstream. A fix to `types` or `cache` reaches a consumer of `pubsub` or `remote-config` only when that package is bumped and republished too.
  — paths: pkg/pubsub/package.json, pkg/remote-config/package.json, pkg/snap/package.json
- [contract:G4] A new named envelope type from `types` must be added to the explicit export lists in `pubsub/src/types.ts`. Callers that must keep `metadata.capture` use `ingestCreateRequestEvent`, because `ingestEvent` strips it.
  — paths: pkg/pubsub/src/types.ts, pkg/pubsub/src/ingest.ts
- [contract:G5] The root `AuditMessageSchema` stays a plain `z.object`, never a union. audit-service generates its Go envelope from its JSON Schema, and a root union generates an empty file.
  — paths: pkg/audit/src/audit-message.ts, pkg/audit/src/fuse/message.ts
- [technical:G6] `serialiseError` is an allow-list. Never widen it to `request`, `response`, `config.headers`, `config.auth` or `config.data`. That reopens the raw `Authorization` header leak into logs.
  — paths: pkg/observability/src/log/serialise-error.ts

## The packages (`pkg/*`)

One directory per package. Each owns its `package.json` and a `tsconfig.json` that extends `@tsconfig/node22`. Every package except `pubsub` also has its own `biome.json`. Nothing is inherited from the root [1][10].

| Package | Version | Role | Internal deps | Tests |
| --- | --- | --- | --- | --- |
| `types` | 10.14.0 | Single source of truth for canonical types and Zod schemas: canonical records, the `BifrostMessage`/`BifrostFailure`/ingest-capture envelopes, config fragments (incl. mapping dictionaries), Snap and API DTOs, the stock-sync shapes (export, result, single-SKU redrive, `StockSyncFailure`), and the runtime `FeatureFlag` shape with its one read rule, `resolveFeatureFlag`/`evaluateFeatureFlag` [22] | none | vitest |
| `cache` | 0.3.0 | Two-tier cache: in-process LRU plus a Redis network tier behind `CacheService`, with cockatiel retry and circuit breaker. No logger dependency | none | **jest** |
| `ddp` | 2.0.0 | Delivery-Duty-Paid rule evaluator and Zod schemas | none | vitest |
| `rules-engine` | 2.1.1 | Canonical-to-canonical mapping: the DSL (incl. `lookup()` over caller-supplied dictionaries), country-to-site/businessId routing, collapse/flatten/merge helpers | `types` (**peer**) | vitest |
| `pubsub` | 0.5.0 | `PubSubIngestor` (decode and validate) and `PubSubRouter` (publish). The router forwards an optional `PublishOptions` to `PubSub.topic()`, which enables client-side batching | `types` (dependency) | vitest |
| `remote-config` | 2.3.0 | Config event dispatcher, typed fragment and backlink handlers, Config API v1 client. `ConnectorBacklinkHandler.resolveWithUnresolved()` also returns the connector ids that failed to fetch or validate | `cache` (dependency), `types` (**peer**) | vitest |
| `edi` | 0.8.1 | EDIFACT to intermediary: tokenizer, shared segment readers, inbound normalizers (INSDES, ORDERS, PRICAT, DESADV), outbound D.96A serializers, interchange wrapper, field-map engine. No runtime dependencies | none | vitest |
| `observability` | 2.2.0 | Fuse adaptor over `@ilg-platform/observability`: `fuse.*` metric catalogue, a per-domain log-event catalogue (`IngestEvent`, `ErrorEvent`, `ConfigEvent`, `ConfirmationEvent`, `LifecycleEvent`, `DependencyEvent`), and `serialiseError` [21]. The framework builders wrap the SDK logger with `asFuseEventLogger`; `./nest` adds `InjectFuseLogger`. Five entry points: root, `/correlation`, `/nest`, `/express`, `/next` [17] | none | vitest |
| `snap` | 0.4.0 | SnapFulfil HTTP client and typed models for the 43-entity surface. Four subpaths: `/http`, `/resilience`, `/types`, `/client`. `/http` and `/resilience` re-export `resilience` [23][29] | `resilience` (dependency) | vitest |
| `resilience` | 0.1.0 | Transport-agnostic primitives: per-host circuit breaker, retry policy, backoff, semaphore | none | vitest |
| `audit` | 0.2.0 | The `AuditMessage` contract for audit-service. Not a `BifrostMessage`: it is system-scoped and usable outside Bifrost. `./fuse` holds the kind registry and `FuseAuditMessage`, a producers-only discriminated union. `./secrets` is the same shape for the Secrets Hub (`secret_change`, strict details). `./publisher` never rejects, times out at 3 s by default, and takes a structural Pub/Sub client, so it has no `@google-cloud/pubsub` dependency [15][20] | none (`zod` peer) | vitest |

## Internal dependency graph

Five edges join the packages. `ddp` and `observability` have none, so they are left out of the drawing. `audit` and `edi` have none either and are drawn to show the set is complete. [10][11][12][13][14][15][16]

```orient-flow
{ "v": 1, "title": "Internal dependencies between packages",
  "nodes": [
    { "id": "types", "label": "types", "kind": "step", "tone": "accent", "ev": [10] },
    { "id": "rules", "label": "rules-engine", "sub": "types is a peer", "kind": "step", "ev": [13] },
    { "id": "pubsub", "label": "pubsub", "sub": "types is a dependency", "kind": "step", "ev": [11] },
    { "id": "rc", "label": "remote-config", "sub": "types is a peer", "kind": "step", "ev": [12] },
    { "id": "cache", "label": "cache", "kind": "step", "ev": [28] },
    { "id": "res", "label": "resilience", "kind": "step" },
    { "id": "snap", "label": "snap", "sub": "re-exports resilience", "kind": "step", "ev": [14, 23] },
    { "id": "audit", "label": "audit", "sub": "no internal deps", "kind": "step", "ev": [15] },
    { "id": "edi", "label": "edi", "sub": "no internal deps", "kind": "step", "ev": [16] }
  ],
  "edges": [
    { "from": "types", "to": "rules", "style": "dashed" },
    { "from": "types", "to": "pubsub" },
    { "from": "types", "to": "rc", "style": "dashed" },
    { "from": "cache", "to": "rc" },
    { "from": "res", "to": "snap" }
  ] }
```

Solid edges are `workspace:*` dependencies. Dashed edges are peers: a `>=` range, dev-installed as `workspace:*`, so the consumer's own `types` is used. `rules-engine` imports `types` only as types [13].

`zod` is a peer pinned exactly to `4.4.3` (not a range) in `types`, `ddp`, `rules-engine`, `pubsub`, `remote-config`, `observability`, `snap` and `audit`. `cache`, `edi` and `resilience` import no zod. Do not loosen the pin [10].

## Build order and publish sequencing

The `needs:` graph in `publish-package.yaml` sequences publish jobs. It is not a build graph. [6]

```orient-flow
{ "v": 1, "title": "Publish job order",
  "nodes": [
    { "id": "pc", "label": "prepare-cache", "kind": "step", "ev": [6] },
    { "id": "ty", "label": "types", "kind": "step", "ev": [6] },
    { "id": "ca", "label": "cache", "kind": "step", "ev": [6] },
    { "id": "rs", "label": "resilience", "kind": "step", "ev": [6] },
    { "id": "w1", "label": "pubsub, observability, audit", "sub": "need prepare-cache only", "kind": "step", "ev": [6] },
    { "id": "w2", "label": "ddp, rules-engine, edi", "sub": "wait on types", "kind": "step", "ev": [6] },
    { "id": "rc", "label": "remote-config", "sub": "waits on types and cache", "kind": "step", "ev": [6] },
    { "id": "sn", "label": "snap", "sub": "waits on resilience", "kind": "step", "ev": [6] }
  ],
  "edges": [
    { "from": "pc", "to": "ty" },
    { "from": "pc", "to": "ca" },
    { "from": "pc", "to": "rs" },
    { "from": "pc", "to": "w1" },
    { "from": "ty", "to": "w2" },
    { "from": "ty", "to": "rc" },
    { "from": "ca", "to": "rc" },
    { "from": "rs", "to": "sn" }
  ] }
```

- `pubsub` does not wait on `types` although it depends on it. `edi` waits on `types` although it does not. The `needs:` order only avoids a race against a stale registry version.
- Each publish job builds `types`, `cache` and `resilience` first when their `dist/` is missing, then builds its own package [7].
- Locally, `pubsub` (builds `types`), `remote-config` (builds `types` and `cache`) and `snap` (builds `resilience`) carry a `pretest` hook [11][12][14].
- `rules-engine` has no `pretest`. **ASSESSED** its vitest run needs no `types` build, because it imports `types` only as types. Its `tsc` build does, because `types` resolves through `dist/index.d.ts` [13].

## Versioning and publish discipline

```orient-flow
{ "v": 1, "title": "What one publish job does",
  "nodes": [
    { "id": "chk", "label": "npm view name@version", "sub": "version gate", "kind": "step", "ev": [7] },
    { "id": "skip", "label": "Version exists: no-op", "sub": "silent, no failure", "kind": "step", "tone": "alert", "ev": [7] },
    { "id": "bld", "label": "Build deps, then package", "kind": "step", "ev": [7] },
    { "id": "pub", "label": "pnpm publish", "sub": "GitHub Packages", "kind": "store", "ev": [7] },
    { "id": "note", "label": "Slack and renovate-runner", "sub": "pkg-node-published", "kind": "service", "service": "renovate-runner", "ev": [7] }
  ],
  "edges": [
    { "from": "chk", "to": "skip", "label": "already published", "style": "dashed" },
    { "from": "chk", "to": "bld", "label": "new version" },
    { "from": "bld", "to": "pub" },
    { "from": "pub", "to": "note", "label": "on success" }
  ] }
```

- **Version-gated.** `publish-package.yaml` runs on push to `main` and on dispatch. The template publishes only when `npm view <name>@<version>` finds nothing [6][7]. A forgotten bump strands the change on `main`.
- **SemVer.** Additive is minor. Breaking is major, and a major needs every consuming repo checked first.
- **Consumers pin `^` ranges.** Each publish dispatches `pkg-node-published` to `renovate-runner` and posts to Slack [7].
- **`workspace:*` freezes at publish.** **ASSESSED** from the org changelog: pnpm turns `workspace:*` into an exact version, so `pubsub@0.4.0` shipped pinned to a `types` two majors old. Only `pubsub` (`types`), `remote-config` (`cache`) and `snap` (`resilience`) carry the edge [11][12][14].
- **Peer floors move without a publish.** Renovate raises the `types` peer floor in `rules-engine` and `remote-config` on each `types` release, with no version bump [26]. Published `rules-engine@2.1.1` carries `>=9.0.0` [25]. Source says `>=10.13.0` [13]. **ASSESSED** the next publish of either package forces every consumer onto `types` 10.13.0 or later. A consumer still on `types` 9.x would then fail its peer check.
- **`pubsub` composes `types`.** It builds its three generic-record schemas from the factories `types` exports. A new field on an existing metadata schema flows through. The export lists and the ingest method choice still need a hand (G4) [18][19].

## Published surface

- Every package publishes to `https://npm.pkg.github.com` through `publishConfig`. `.npmrc` points the `@gfs-bifrost` and `@ilg-platform` scopes there and reads `GITHUB_TOKEN` [4].
- Packages with an allow-list `files: ["dist"]`: all except `ddp` and `rules-engine` [24][13]. **ASSESSED** from `package.json` alone: those two have no `files` field and no `.npmignore`, so a publish packs their `src`, tests and config as well as `dist`. Run `pnpm pack --dry-run` in each to confirm.
- `audit`, `observability` and `snap` have subpath `exports` plus a `typesVersions` block, for consumers on classic module resolution. `resilience` exposes only its root [14][15][17].

## CI

- **Code quality.** Eleven `code-quality-<pkg>.yaml` workflows, path-filtered, run `test` and `lint` through the reusable `node-run.yaml`. All pin the feature branch `@hjf/node-run-pnpm-filter`, not a released tag. That is a deliberate hold until the `filter` input lands on `@0.1-affogato`, so do not repoint the ref early [9].
- **Install.** The cross-org `@ilg-platform` install needs a PAT (`secrets.GH_TOKEN`), because the default token is same-org only. An expired PAT reddens CI fleet-wide.
- **Secops.** `secops.yaml` runs gitleaks, a dependency audit and semgrep. It runs daily at 06:00 UTC, on PRs to `main`, and on dispatch, pinned to `@0.2-bonbon`. The audit gates high and critical advisories in production dependencies only. The `audit-ci.jsonc` allowlist is empty [5][8].

## Gotchas

- **Overrides live in `pnpm-workspace.yaml`.** pnpm 10 ignores them in `package.json`. The file currently overrides `axios` to `>=1.20.0` [1].
- **Build scripts need approval.** `onlyBuiltDependencies` lists `unrs-resolver` and `ignoredBuiltDependencies` lists `esbuild`. A new dependency with a postinstall script needs an entry first [1].
- **`cache` runs jest, the rest run vitest.** `ddp` and `rules-engine` still carry a leftover `babel.config.js`. Match the package's own runner [28].
- **`pubsub` has no `biome.json` and no `vitest.config.ts`.** That is intentional. Its `lint` is a bare `biome check`.
- **A canonical schema typed `z.ZodType<T>` hides `.shape`.** Importers lose `.shape` and `.extend()` even though the runtime object has them. `CanonicalMasterDataSchema.shape.product` does not compile. To reuse part of a schema, export it as its own named schema, as `CanonicalProductSchema` was [27].
- **`mise.toml` pins `pnpm = "latest"`.** The authoritative pin is `packageManager: pnpm@10.24.0` in the root `package.json`. `latest` has been seen to reject the GitHub-Packages lockfile [2][3].
- **The repo's `CLAUDE.md` lags its tree.** It says "nine" packages and has no `resilience` row. See [[known-context#resilience-doc-gap]].
- **remote-config's Redis TTL units are wrong.** `RedisCache.setAsync` sets `PX` (milliseconds), but remote-config documents its TTL in seconds. The default `DEFAULT_REDIS_TTL = 3600` therefore means 3.6 s. Consumers pass their own TTL: fapi works out to 604.8 s, and shopify-connector to 7 days. This applies to every config fragment. Tracked in FUSE-1313.
- **A `config_revision` push refreshes Redis and one instance's in-memory LRU, never the others.** Pub/Sub push delivers each message to one Cloud Run instance. Every other instance serves its LRU copy, a fixed 60 s because the builder never calls `withTtl`, so a push can't bound staleness across instances.
- **Runtime feature flags are not a `config_revision` fragment.** `ConfigFragmentSchema` is a closed union with `fragments.min(1)`, so one unknown fragment type fails the whole revision in every subscriber that parses it. Flags are served by config-service's `/api/v1/feature-flags`. Read them through `evaluateFeatureFlag`, never `enabled` directly: a pending `scheduledChange` is evaluated against the clock.
- **Backend services read flags through remote-config 2.4.0's opt-in `provider.featureFlags`**, never their own client.
  - `isEnabled` is synchronous over an in-process snapshot with a 30 s TTL, refreshed on read, single-flight, with no timers.
  - An unresolvable flag reads false. The last-known snapshot is kept on failure, with a retry after 5 s.
  - `ingestEvent(record)` takes the decoded `feature_flag_revision` record and refetches immediately. The payload is only a signal.
  - The client is `fetch` with `AbortSignal.timeout`, because axios `timeout` stops bounding the request once headers arrive. Its errors never carry the request, so the `x-api-key` can't leak.
- **gitleaks fails PRs on fixture strings shaped like API keys** (`"test-api-key-7f3c"` hit the generic-api-key rule on #275). It scans every commit in the PR, so the fix is rewriting the commit; a follow-up commit doesn't clear it. Use plain words such as `"fixture"`.
- **`pkg/types` carries its own `pnpm-lock.yaml`.** **ASSESSED** it is a stray: the workspace installs from the root lockfile, and no other package has one.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "pnpm-workspace.yaml@ab780a5" },
  { "id": 2, "kind": "code", "ref": "package.json@ab780a5" },
  { "id": 3, "kind": "code", "ref": "mise.toml@ab780a5" },
  { "id": 4, "kind": "code", "ref": ".npmrc@ab780a5" },
  { "id": 5, "kind": "code", "ref": "audit-ci.jsonc@ab780a5" },
  { "id": 6, "kind": "code", "ref": ".github/workflows/publish-package.yaml@ab780a5" },
  { "id": 7, "kind": "code", "ref": ".github/workflows/template-publish-node.yaml@ab780a5" },
  { "id": 8, "kind": "code", "ref": ".github/workflows/secops.yaml@ab780a5" },
  { "id": 9, "kind": "code", "ref": ".github/workflows/code-quality-audit.yaml@ab780a5", "note": "same shape in all eleven" },
  { "id": 10, "kind": "code", "ref": "pkg/types/package.json@ab780a5" },
  { "id": 11, "kind": "code", "ref": "pkg/pubsub/package.json@ab780a5" },
  { "id": 12, "kind": "code", "ref": "pkg/remote-config/package.json@ab780a5" },
  { "id": 13, "kind": "code", "ref": "pkg/rules-engine/package.json@ab780a5" },
  { "id": 14, "kind": "code", "ref": "pkg/snap/package.json@ab780a5" },
  { "id": 15, "kind": "code", "ref": "pkg/audit/package.json@ab780a5" },
  { "id": 16, "kind": "code", "ref": "pkg/edi/package.json@ab780a5" },
  { "id": 17, "kind": "code", "ref": "pkg/observability/package.json@ab780a5" },
  { "id": 18, "kind": "code", "ref": "pkg/pubsub/src/types.ts@ab780a5" },
  { "id": 19, "kind": "code", "ref": "pkg/pubsub/src/ingest.ts@ab780a5" },
  { "id": 20, "kind": "code", "ref": "pkg/audit/src/audit-message.ts@ab780a5" },
  { "id": 21, "kind": "code", "ref": "pkg/observability/src/log/serialise-error.ts@ab780a5" },
  { "id": 22, "kind": "code", "ref": "pkg/types/src/pubsub/types/stock-sync.type.ts@ab780a5" },
  { "id": 23, "kind": "code", "ref": "pkg/snap/src/resilience/index.ts@ab780a5" },
  { "id": 24, "kind": "code", "ref": "pkg/ddp/package.json@ab780a5" },
  { "id": 25, "kind": "pr", "ref": "gfs-bifrost/pkg-node#238", "note": "rules-engine 2.1.1, peer >=9.0.0" },
  { "id": 26, "kind": "pr", "ref": "gfs-bifrost/pkg-node#267", "note": "peer floor raised, no version bump" },
  { "id": 27, "kind": "code", "ref": "pkg/types/src/canonical/schemas/master-data.schema.ts@ab780a5" },
  { "id": 28, "kind": "code", "ref": "pkg/cache/package.json@ab780a5" },
  { "id": 29, "kind": "code", "ref": "pkg/snap/src/http/index.ts@ab780a5" }
] }
```
