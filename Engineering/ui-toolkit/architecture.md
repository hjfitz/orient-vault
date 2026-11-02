---
tags:
- waypoint
- ui-toolkit
verified: '2026-10-13'
verified_sha: db43671
verified_paths:
- packages
- .github/workflows
- apps/showcase
- pnpm-workspace.yaml
- .github/CODEOWNERS
- CLAUDE.md
title: ui-toolkit — architecture
thesis: A pnpm and Turborepo monorepo with one published component library, an internal
  tsconfig package and a private showcase app; every merged PR releases by label,
  and nobody edits the version by hand.
confidence: high
---
# ui-toolkit — architecture

```orient-bluf
{ "v": 1, "bluf": "A pnpm and Turborepo monorepo with one published component library, an internal tsconfig package and a private showcase app; every merged PR releases by label, and nobody edits the version by hand.", "confidence": "high", "action": "Never regenerate src/shadcn from upstream, and never edit the version field; put one release:* label on the PR instead." }
```

## Guardrails

- [technical:G1] `src/shadcn/` is a permanent fork. Never regenerate, re-sync or overwrite a file from upstream shadcn, whether by CLI or by pasting source. Hand-add a genuinely new primitive in the existing style. No divergence inventory exists on purpose; read `git log` for a file's history.
  — paths: packages/ui-toolkit/src/shadcn, packages/ui-toolkit/components.json, packages/ui-toolkit/biome.json
- [contract:G2] Never edit `version` in `packages/ui-toolkit/package.json`. Every PR carries exactly one `release:*` label, and `release:skip` is rejected when the PR touches `packages/ui-toolkit/src/`. The release workflow bumps the version on `main`.
  — paths: .github/workflows/release-guard.yml, .github/workflows/release.yml, packages/ui-toolkit/package.json
- [contract:G3] A change to the public surface lands with its showcase change in the same PR. The showcase imports the library only through published sub-paths, so CI fails on a removed export or a renamed required prop.
  — paths: apps/showcase, CLAUDE.md, packages/ui-toolkit/package.json
- [technical:G4] Import from a sub-path, never the package root. Never import the removed `@ilg-platform/design-system`, `@ilg-platform/form` or `@ilg-platform/data-table`.
  — paths: packages/ui-toolkit/package.json, packages/ui-toolkit/src/index.ts, packages/ui-toolkit/CLAUDE.md
- [technical:G5] The repo ships exactly one published artifact. Utilities live inlined in `src/helpers/`, and a separate utility package is never reintroduced.
  — paths: packages/ui-toolkit/src/helpers, pnpm-workspace.yaml, CLAUDE.md
- [contract:G6] `Release label` is the required status check on `main`, and it is the job name rather than `Release Guard / Release label`. The release identity needs a bypass on `main`'s ruleset to push the bump commit. **ASSESSED** Both settings live in GitHub, outside this repo.
  — paths: .github/workflows/release-guard.yml, .github/workflows/release.yml

## Layout

```orient-flow
{ "v": 1, "title": "Package layout",
  "nodes": [
    { "id": "ui", "label": "packages/ui-toolkit", "sub": "@ilg-platform/ui-toolkit", "kind": "service", "service": "ui-toolkit", "tone": "accent", "ev": [1] },
    { "id": "mods", "label": "Component modules", "sub": "app-layout, core, data-table, form", "kind": "step", "ev": [11] },
    { "id": "sh", "label": "src/shadcn", "sub": "forked primitives", "kind": "step", "ev": [11] },
    { "id": "hp", "label": "src/helpers", "sub": "inlined ts-util subset", "kind": "step", "ev": [10] },
    { "id": "tc", "label": "packages/typescript-config", "sub": "internal, unpublished", "kind": "step", "ev": [3] },
    { "id": "sc", "label": "apps/showcase", "sub": "private Next.js app", "kind": "step", "ev": [14] },
    { "id": "gh", "label": "GitHub Packages", "sub": "dist build, restricted", "kind": "store", "ev": [1] }
  ],
  "edges": [
    { "from": "ui", "to": "mods" },
    { "from": "mods", "to": "sh", "label": "built on" },
    { "from": "mods", "to": "hp" },
    { "from": "ui", "to": "tc", "label": "extends tsconfig" },
    { "from": "sc", "to": "ui", "label": "published sub-paths only" },
    { "from": "ui", "to": "gh", "label": "publish" }
  ] }
```

```
packages/
├── ui-toolkit/            @ilg-platform/ui-toolkit — the published component library
│   └── src/
│       ├── app-layout/    GLayout, GSidebar, GNavMain, GSiteHeader, footer/, …
│       ├── core/          GButton, GCard, and other general components
│       ├── data-table/    GDataTable + column builders + useDataTable hooks
│       ├── form/          GTextField, GSelectField, GForm, zod validators
│       ├── helpers/       inlined utility subset (was @gfs-ecm/ts-util)
│       ├── lib/           flat utilities: useIsMobile, cn()
│       ├── shadcn/        forked primitives — flat, never reorganised
│       └── styles/        globals.css
└── typescript-config/     @ilg-platform/typescript-config — shared tsconfig bases (internal, unpublished)
apps/
└── showcase/              @ilg-platform/ui-toolkit-showcase — private Next.js app rendering every export
```

Each module except `shadcn`, `lib`, `styles` and `helpers` follows one pattern: `components/` (React, `g-*.tsx`), `logic/` (hooks and pure utilities, only if needed), `stories/` (co-located Storybook stories) and an `index.ts` barrel. `form` also has `types/`, and `app-layout` also has `footer/` [11].

**Sub-path exports.** In the checkout, `exports` points at `src/` (`.`, `./core/*`, `./shadcn/*`, `./form`, `./data-table`, `./app-layout`, two `./app-layout/footer/*` entries, `./lib/*`, `./globals.css`). `publishConfig` rewrites them to `dist/` for the tarball and sets `access: restricted` [1]. Always import from the sub-path. The root barrel exports only `core` and `lib` [15].

**Toolchain.** Node 22 or newer, pnpm 11.5.3, TypeScript 5.9, Biome 2.x with 4-space indent and single quotes, Turborepo [3]. `any` is banned, and `satisfies` beats `as`. Folder names are kebab-case [10].

## The shadcn primitive layer is a fork, not a mirror {#shadcn-fork}

`src/shadcn/` began as vendored shadcn CLI output. Upstream updates are no longer synced, so these files are first-party source with deliberate divergences from upstream [11].

- "Upstream does it differently" is not a reason to change one of these files. Divergence is the expected state.
- Biome ignores `src/shadcn/` entirely (`!src/shadcn`), so formatting there is by hand and not enforced [13].
- Adding a new primitive is fine. The CLI would rewrite sibling files and config, so write it by hand.

## The showcase app is part of the contract {#showcase}

`apps/showcase` renders every exported component inside a real app shell and imports the library only through its published sub-paths. CI type-check and build therefore fail on a removed export or a renamed required prop [10][14].

CI cannot catch a new prop nobody demoed. The root `CLAUDE.md` makes the showcase change a same-PR requirement for that reason. A showcase-only change is normally `release:skip`.

The Coverage page is generated from source by `apps/showcase/scripts/generate-coverage.mjs`, which `predev` and `prebuild` run after `generate-examples.mjs` and `generate-registry.mjs`. The committed `lib/coverage.generated.json` shows coverage moving in a PR diff [14].

`pnpm-workspace.yaml` lists `packages/*` and `apps/*`. Its `overrides` floor `sharp`, `postcss`, `nanoid` and `browserslist`, because the showcase is the only package declaring `next` as a production dependency and `next`'s transitive advisories reach the `audit-ci --prod` gate through it. Drop an override once `next` ships a range that satisfies it. `allowBuilds` denies `esbuild` and `sharp` install scripts, since both ship prebuilt binaries [2].

## Release automation — label-driven, no manual version edits {#release-automation}

```orient-flow
{ "v": 1, "title": "From PR to published version",
  "nodes": [
    { "id": "pr", "label": "Pull request", "sub": "one release:* label", "kind": "step", "ev": [5] },
    { "id": "gd", "label": "Release label check", "sub": "required status check", "kind": "step", "ev": [5] },
    { "id": "mn", "label": "main", "sub": "merge queue", "kind": "step", "ev": [5] },
    { "id": "rl", "label": "Release workflow", "sub": "highest label since last tag", "kind": "step", "tone": "accent", "ev": [4] },
    { "id": "bp", "label": "Bump commit", "sub": "chore(release) [skip ci]", "kind": "step", "ev": [4] },
    { "id": "bd", "label": "Build", "sub": "turbo, ui-toolkit and deps", "kind": "step", "ev": [4] },
    { "id": "pb", "label": "GitHub Packages", "sub": "access restricted", "kind": "store", "ev": [4] },
    { "id": "tg", "label": "Tag vX.Y.Z", "sub": "after publish", "kind": "step", "ev": [4] },
    { "id": "rc", "label": "publish-packages.yml", "sub": "manual recovery", "kind": "step", "tone": "alert", "ev": [6] }
  ],
  "edges": [
    { "from": "pr", "to": "gd", "label": "validates" },
    { "from": "gd", "to": "mn", "label": "merge" },
    { "from": "mn", "to": "rl", "label": "push" },
    { "from": "rl", "to": "bp" },
    { "from": "bp", "to": "bd" },
    { "from": "bd", "to": "pb", "label": "publish" },
    { "from": "pb", "to": "tg" },
    { "from": "rc", "to": "pb", "label": "bump pushed, publish failed", "style": "dashed" }
  ] }
```

`release-guard.yml` rejects any PR that touches the `version` line of `packages/ui-toolkit/package.json`. Every PR carries exactly one label, and the guard fails closed if it cannot diff against the base [5].

| Label | Bump | Use for |
| --- | --- | --- |
| `release:patch` | `x.y.Z` | Bug fix, style tweak, internal refactor, no API change |
| `release:minor` | `x.Y.0` | New component, new prop, new export, backwards-compatible |
| `release:major` | `X.0.0` | Removed export, renamed prop, breaking behaviour change |
| `release:skip` | none | CI, docs or repo tooling only, nothing reaches consumers |

The guard also runs on `merge_group` and reports success at once, so it can be a required check without stalling the merge queue [5].

On push to `main`, `release.yml` reads the label of every PR merged since the last `vX.Y.Z` tag. It bumps by the highest level present (major, then minor, then patch) and ignores skip and unlabelled PRs. It then commits the bump as `github-actions[bot]`, builds, publishes with `--access restricted`, and tags the published version. Deriving the bump from everything since the last tag, not from one merge event, keeps a batch landing at once from losing a release [4].

- **Warning, not failure.** A merged PR with no `release:*` label logs a warning and is not released. Dispatching the workflow with a `bump` input releases it by hand [4].
- **Retries.** The bump push retries three times when `main` moves underneath it [4].
- **Token.** The push uses `RELEASE_TOKEN` when that secret exists and `GITHUB_TOKEN` otherwise. Whichever one it is needs a bypass on `main`'s ruleset. **UNKNOWN** Which identity is configured today, since the ruleset and secrets are not in the repo.
- **Recovery.** When a run pushes the bump but fails before publishing, dispatch `publish-packages.yml`. It publishes and tags the version already on `main`. A re-run of Release would bump a second time. If that version is already published, `pnpm publish` fails on the duplicate and nothing is tagged [6].
- **Concurrency.** One release runs at a time, with `cancel-in-progress: false`.

## CI

- `code-quality.yml` runs lint, type-check, unit tests, Storybook tests, build and a Storybook build, filtered by Turborepo to packages changed against the base. A second job runs visual regression inside a pinned `mcr.microsoft.com/playwright` image, because Chromium on bare `ubuntu-latest` renders fonts differently from the baselines [7].
- `secops.yml` calls the shared secret scan and Node dependency audit from `ilg-platform/github-actions` at `0.2-bonbon`, daily and on every PR [8].
- `.github/CODEOWNERS` routes every change to `@ilg-platform/ui-toolkit-maintainers`. It only requests review until branch protection requires code-owner review [9].
- `.husky/pre-commit` runs `pnpm lint && pnpm check-types`.

## Build and run

```bash
pnpm install
pnpm build           # turbo, all packages
pnpm lint            # Biome
pnpm check-types
pnpm --filter @ilg-platform/ui-toolkit storybook
pnpm --filter @ilg-platform/ui-toolkit-showcase dev   # http://localhost:3100
```

Run `lint-fix` and `check-types` on every changed package before calling a task done [10].

## Cross-org install requirement

Installing `@ilg-platform/ui-toolkit` needs a `GITHUB_TOKEN` that can read packages, and an `.npmrc` mapping the `@ilg-platform` scope to `https://npm.pkg.github.com`. The workspace packages resolve locally, so building this repo needs no token [12].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "packages/ui-toolkit/package.json@db43671" },
  { "id": 2, "kind": "code", "ref": "pnpm-workspace.yaml@db43671" },
  { "id": 3, "kind": "code", "ref": "package.json@db43671" },
  { "id": 4, "kind": "code", "ref": ".github/workflows/release.yml@db43671" },
  { "id": 5, "kind": "code", "ref": ".github/workflows/release-guard.yml@db43671" },
  { "id": 6, "kind": "code", "ref": ".github/workflows/publish-packages.yml@db43671" },
  { "id": 7, "kind": "code", "ref": ".github/workflows/code-quality.yml@db43671" },
  { "id": 8, "kind": "code", "ref": ".github/workflows/secops.yml@db43671" },
  { "id": 9, "kind": "code", "ref": ".github/CODEOWNERS@db43671" },
  { "id": 10, "kind": "code", "ref": "CLAUDE.md@db43671" },
  { "id": 11, "kind": "code", "ref": "packages/ui-toolkit/CLAUDE.md@db43671" },
  { "id": 12, "kind": "code", "ref": "README.md@db43671" },
  { "id": 13, "kind": "code", "ref": "packages/ui-toolkit/biome.json@db43671" },
  { "id": 14, "kind": "code", "ref": "apps/showcase/package.json@db43671" },
  { "id": 15, "kind": "code", "ref": "packages/ui-toolkit/src/index.ts@db43671" }
] }
```
