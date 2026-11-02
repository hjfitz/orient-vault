---
tags:
- waypoint
- ui-toolkit
verified: '2026-10-13'
verified_sha: db43671
verified_paths:
- README.md
- CLAUDE.md
- packages/ui-toolkit/package.json
- .github/workflows/release.yml
- .github/CODEOWNERS
- packages/ui-toolkit/CLAUDE.md
title: ui-toolkit — overview
thesis: ui-toolkit is the shared React component library for ILG products, published
  as one package to GitHub Packages. The gfs-ecm team owns the design and Fuse apps
  consume it.
confidence: high
---
# ui-toolkit — overview

```orient-bluf
{ "v": 1, "bluf": "ui-toolkit is the shared React component library for ILG products, published as one package to GitHub Packages. The gfs-ecm team owns the design and Fuse apps consume it.", "confidence": "high", "action": "none" }
```

## Responsibility

- It publishes `@ilg-platform/ui-toolkit`: forked shadcn primitives, the G-components (`GLayout`, `GButton`, `GCard`, `GDataTable`, `GTextField`), forms, a data table and app-layout shell components [3][7].
- The repo is a pnpm and Turborepo monorepo. It holds one published package, an internal `typescript-config` package, and a private showcase app [2].
- A merged PR releases the package. Its `release:*` label sets the version bump, and nobody edits `version` by hand [1][4].

## Why it exists separately

Fuse did not build it. It is a copy of the relevant slice of `gfs-ecm/ui-core`. `ui-core/apps/ecm-next` stays the primary consumer and the reference for a component's intended behaviour [2].

Extraction let the toolkit version on its own under the `@ilg-platform` scope. Each product takes a semver release at its own pace instead of vendoring a copy of `ui-core`.

**ASSESSED** The gfs-ecm team owns it. The evidence is the CODEOWNERS team `ilg-platform/ui-toolkit-maintainers`, the `CXD-` commit prefixes from a different tracker, and the 2026-08-24 interview in [[known-context]] [6]. That interview says Harry only consumes it. The git log shows Harry Humby, on Harry's team, contributing since the showcase app landed.

## Neighbours

```orient-flow
{ "v": 1, "title": "ui-toolkit in context",
  "nodes": [
    { "id": "uc", "label": "gfs-ecm/ui-core", "sub": "origin and reference app ecm-next", "kind": "external", "ev": [2] },
    { "id": "ui", "label": "ui-toolkit", "sub": "@ilg-platform/ui-toolkit", "kind": "service", "service": "ui-toolkit", "tone": "accent", "ev": [3] },
    { "id": "gh", "label": "GitHub Packages", "sub": "@ilg-platform scope", "kind": "store", "ev": [4] },
    { "id": "fui", "label": "fuse-ui", "kind": "service", "service": "fuse-ui", "ev": [5] },
    { "id": "fapi", "label": "fapi", "sub": "portal", "kind": "service", "service": "fapi", "ev": [5] },
    { "id": "dd", "label": "distraction-dashboard", "kind": "service", "service": "distraction-dashboard", "ev": [5] },
    { "id": "sr", "label": "secops-reporting", "sub": "ui, ^1.18.3", "kind": "service", "service": "secops-reporting", "ev": [5] },
    { "id": "oth", "label": "Other consumers", "sub": "fuse-billing, ecm-next", "kind": "external", "ev": [2, 5] }
  ],
  "edges": [
    { "from": "uc", "to": "ui", "label": "extracted from" },
    { "from": "ui", "to": "gh", "label": "publish on merge" },
    { "from": "gh", "to": "fui" },
    { "from": "gh", "to": "fapi" },
    { "from": "gh", "to": "dd" },
    { "from": "gh", "to": "sr" },
    { "from": "gh", "to": "oth" }
  ] }
```

**ASSESSED** Five repos declare the package on their default branch. Four sit at `^1.34.0` or newer: fuse-ui, fapi, distraction-dashboard and fuse-billing. secops-reporting sits at `^1.18.3` [5]. The scan covered local checkouts only. ecm-next lives outside them, and the README and CODEOWNERS name it as a consumer.

## Where the reference lives

[[architecture]] holds the layout, the shadcn fork rule, the showcase contract and the release automation. `packages/ui-toolkit/CLAUDE.md` is the authoritative guide to component conventions, and `design.md` records the design system. [[known-context]] holds ownership history and one live bug.

Do not trust `packages/ui-toolkit/CHANGELOG.md`. It stops at 1.17.1, and the package is at 1.35.3 [3].

## What deliberately isn't here

- **Synced shadcn primitives.** `src/shadcn/` is a permanent fork, and upstream shadcn is never pulled back in.
- **A utility package.** A vendored subset of `@gfs-ecm/ts-util` lives in `src/helpers/`, so the repo ships exactly one artifact [7].
- **Hand-edited versions.** The release workflow bumps the version on `main` from PR labels.
- **A deployed service.** There are no routes, no infrastructure code and no container image. The showcase is a private Next.js app run locally [1].
- **The old split packages.** `@ilg-platform/design-system`, `@ilg-platform/form` and `@ilg-platform/data-table` no longer exist [7].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "README.md@db43671" },
  { "id": 2, "kind": "code", "ref": "CLAUDE.md@db43671" },
  { "id": 3, "kind": "code", "ref": "packages/ui-toolkit/package.json@db43671" },
  { "id": 4, "kind": "code", "ref": ".github/workflows/release.yml@db43671" },
  { "id": 5, "kind": "doc", "ref": "package.json of fuse-ui, fapi (portal), distraction-dashboard, fuse-billing and secops-reporting at origin/HEAD or origin/main, scanned 2026-10-13" },
  { "id": 6, "kind": "code", "ref": ".github/CODEOWNERS@db43671" },
  { "id": 7, "kind": "code", "ref": "packages/ui-toolkit/CLAUDE.md@db43671" }
] }
```
