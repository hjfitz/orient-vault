---
tags:
- system
- ilg-platform
verified: '2026-09-24'
title: ilg-platform — design language
---
# ilg-platform — design language

**The ILG design system lives here**, in `@ilg-platform/ui-toolkit`. Every ILG product UI
inherits from it, so this is the root of the design-language tree.

The authoritative detail — tokens, the `G*` component vocabulary, radius scale, brand palette,
theme mechanism — is in `Engineering/ui-toolkit/design.md`, anchored to the real source paths
so `wp stale` catches the system moving. This doc is the system-level framing only.

## Inheritance

```orient-flow
{ "v": 1, "title": "Design language inheritance",
  "nodes": [
    { "id": "shad", "label": "shadcn and Tailwind v4", "sub": "new-york, neutral; src/shadcn is a permanent fork", "kind": "external" },
    { "id": "tk", "label": "@ilg-platform/ui-toolkit", "sub": "the design system", "kind": "service", "service": "ui-toolkit", "tone": "accent" },
    { "id": "fu", "label": "fuse-ui", "sub": "overrides the brand blue tokens", "kind": "service", "service": "fuse-ui" },
    { "id": "dd", "label": "distraction-dashboard", "sub": "zero overrides", "kind": "service", "service": "distraction-dashboard" },
    { "id": "next", "label": "Any future ILG app", "kind": "external" }
  ],
  "edges": [
    { "from": "shad", "to": "tk" },
    { "from": "tk", "to": "fu" },
    { "from": "tk", "to": "dd" },
    { "from": "tk", "to": "next" }
  ] }
```

A consuming app's `globals.css` is a thin shim that imports the toolkit. **Looking for a token
in the consuming app finds nothing** — that has cost a session already.

## The stance

Business/operator UI for people who did not build it: light-first with a real dark mode,
rounded, generous hit areas, status carried by chips and pills. Clarity over density — the
opposite pole from [[orient]], deliberately.

## Rules that outlive any one app

- **Tokens change here, never downstream.** A local override in a consuming app is a fork.
- `--primary` **is** brand blue (it was near-black long ago; that note is obsolete).
- There is **no `success`/`warning` token — only `destructive`.** Status tints are therefore
  literal Tailwind scales in consuming apps, by convention. Changing that means adding tokens
  here, not inventing a local palette.
- Every toolkit change is a semver bump + republish.
- `cursor-pointer` must be explicit — base shadcn controls do not add it.

## Reviewing it

The toolkit package has no runnable UI; `apps/showcase` in the `ui-core` monorepo is the
surface to screenshot. `/ux-review` reads `Engineering/ui-toolkit/design.md` as its project
layer.
