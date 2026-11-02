---
tags:
- waypoint
- pkg-node
verified: '2026-10-13'
verified_sha: ab780a5
verified_paths:
- pnpm-workspace.yaml
- package.json
- CLAUDE.md
- .github/workflows/publish-package.yaml
- .github/workflows/template-publish-node.yaml
- pkg/edi/package.json
- pkg/rules-engine/readme.md
title: pkg-node — overview
thesis: pkg-node publishes the eleven @gfs-bifrost libraries every Fuse service installs,
  and it publishes a package only when that package's version number is new.
confidence: high
---
# pkg-node — overview

```orient-bluf
{ "v": 1, "bluf": "pkg-node publishes the eleven @gfs-bifrost libraries every Fuse service installs, and it publishes a package only when that package's version number is new.", "confidence": "high", "action": "Bump the package version in every PR that changes a package, or the change never publishes." }
```

## Responsibility

- It holds eleven packages under `pkg/*`. Each publishes to GitHub Packages as `@gfs-bifrost/<name>` [1][2].
- **Contracts:** `types` (canonical records, envelopes, config shapes) and `audit` (the audit-event envelope).
- **Runtime helpers:** `cache`, `resilience`, `pubsub`, `remote-config` and `observability`.
- **Engines and clients:** `rules-engine` (mapping DSL, routing), `ddp`, `edi` (EDIFACT) and `snap` (SnapFulfil client and models).
- It runs nothing. The root has no Dockerfile, no Cloud Run service and no telemetry. It publishes libraries only [2].
- Ownership is the wider Fuse team. `known-context` records that, and the repo has no CODEOWNERS file.

## Why it exists separately

One versioned copy of the canonical types and the event envelope beats one copy per service. Services pin a `^` range. Renovate then carries each fix to them.

The cost is blast radius. A breaking change reaches every consumer at once. A major bump needs a check of every consuming repo first.

## Neighbours

```orient-flow
{ "v": 1, "title": "pkg-node in context",
  "nodes": [
    { "id": "pkg", "label": "pkg-node", "sub": "11 packages", "kind": "service", "service": "pkg-node", "tone": "accent", "ev": [1, 2] },
    { "id": "reg", "label": "GitHub Packages", "sub": "@gfs-bifrost scope", "kind": "store", "ev": [3] },
    { "id": "ren", "label": "renovate-runner", "kind": "service", "service": "renovate-runner", "ev": [3] },
    { "id": "svc", "label": "Fuse services", "sub": "pin ^ ranges", "kind": "external" }
  ],
  "edges": [
    { "from": "pkg", "to": "reg", "label": "publish if version is new" },
    { "from": "pkg", "to": "ren", "label": "pkg-node-published" },
    { "from": "ren", "to": "svc", "label": "bump PRs" },
    { "from": "reg", "to": "svc", "label": "install" }
  ] }
```

A merge to `main` publishes each package whose version is new, then dispatches `pkg-node-published` once per package [3]. **ASSESSED** renovate-runner turns that dispatch into the downstream bump PRs, from the repo's own CLAUDE.md. This repo only sends the event.

## Where the reference lives

- [[architecture]] holds the package table, the dependency graph, publish order, CI and tooling gotchas.
- [[known-context]] holds interview truth and is exempt from staleness checks.
- The per-package changelog lives in the org contract (`~/code/CLAUDE.md`, "Package Changelog"), not in this repo. It is context, not proof. Read `package.json` and `src/index.ts` for what a package exports.
- The repo's own `CLAUDE.md` lags its tree. It says "nine" packages, and its graph omits `resilience`. [[architecture]] lists the drift.
- Package READMEs vary. The `rules-engine` readme is a stub that imports a `RulesEngine` export that does not exist [4]. `types` and `cache` have no README.

## What deliberately isn't here

- **Root scripts and root config.** Each package owns its `tsconfig`, `biome.json` and test config. Run scripts with `pnpm --filter`.
- **A `types` dependency in `edi`.** `edi` stays canonical-agnostic [5]. The consumer maps the intermediary to canonical.
- **Overrides in `package.json`.** pnpm 10 ignores them there. They live in `pnpm-workspace.yaml` [1].
- **Per-package change history.** The org contract owns it.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "pnpm-workspace.yaml@ab780a5" },
  { "id": 2, "kind": "code", "ref": ".github/workflows/publish-package.yaml@ab780a5" },
  { "id": 3, "kind": "code", "ref": ".github/workflows/template-publish-node.yaml@ab780a5" },
  { "id": 4, "kind": "code", "ref": "pkg/rules-engine/readme.md@ab780a5" },
  { "id": 5, "kind": "code", "ref": "pkg/edi/package.json@ab780a5" }
] }
```
