---
tags:
- system
- fuse
verified: '2026-09-24'
title: fuse — design language
---
# fuse — design language

**Fuse does not own a design language — it consumes [[ilg-platform]]'s.** This doc exists to
say where the real one is, which surfaces inherit it, and what is Fuse-specific.

The system doc that matters is [[ilg-platform]] `design.md`; the authoritative per-repo doc is
`Engineering/ui-toolkit/design.md`.

## How the language reaches a Fuse surface

```orient-flow
{ "v": 1, "title": "How the design language reaches a Fuse surface",
  "nodes": [
    { "id": "tk", "label": "ui-toolkit", "sub": "ilg-platform system", "kind": "service", "service": "ui-toolkit" },
    { "id": "fu", "label": "fuse-ui", "kind": "service", "service": "fuse-ui", "tone": "accent" },
    { "id": "dd", "label": "distraction-dashboard", "kind": "service", "service": "distraction-dashboard" },
    { "id": "look", "label": "fuse-ui navy", "sub": "brand blue #202e56 light, oklch(.7 .13 268) dark", "kind": "step" }
  ],
  "edges": [
    { "from": "tk", "to": "fu", "label": "tokens, G* components, .dark class" },
    { "from": "tk", "to": "dd", "label": "same, zero overrides" },
    { "from": "fu", "to": "look", "label": "overrides the brand tokens behind --primary" }
  ] }
```

Both Fuse front-ends are **consumers**. Neither may fork the design system: a token change is
a `@ilg-platform/ui-toolkit` semver bump and republish, never a local edit. `fuse-ui`'s two
`--primary` overrides are the only sanctioned divergence and they are brand, not structure.

## The stance, in one line

An **operator tool for ILG support and ops staff who did not build it** — clarity and
scannability over density. Anything that pushes a Fuse surface toward a dense, dark,
monospaced console is a regression, however good it would look to an engineer.

This is the opposite pole from [[orient]], which is deliberately maximum-density for a single
expert reader. The two systems must not be judged against each other.

## Surfaces

| Surface | Doc | Reviewed |
| --- | --- | --- |
| [[fuse-ui]] | `Engineering/fuse-ui/design.md` | yes — tokens, theme, reference module |
| [[distraction-dashboard]] | `Engineering/distraction-dashboard/design.md` | **no pixels yet** — stack only |

## Reviewing one

`/ux-review` (`~/.claude/skills/ux-review/`) holds a running surface against its universal
rubric **plus** the service's own `design.md` as the project layer. It resolves the design doc
from this vault. Findings that change a stated fact go back into the doc and get re-anchored
with `wp verify` in the same session.
