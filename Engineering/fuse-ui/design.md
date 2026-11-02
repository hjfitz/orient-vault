---
tags:
- waypoint
- fuse-ui
verified: '2026-09-24'
verified_sha: ae14bc5
verified_paths:
- code/src/app/globals.css
- code/src/app/layout.tsx
- code/src/components/app-theme-provider.tsx
- code/src/modules/customers-list
title: fuse-ui — design language
---
# fuse-ui — design language

Inherits **[[ui-toolkit]]'s design language** wholesale; that doc is the parent and is not
repeated here. This one records what fuse-ui **overrides, adds, or gets wrong**.

Next 16 (App Router, React 19, Server Components) · Tailwind v4 · shadcn "new-york" ·
`@ilg-platform/ui-toolkit`.

## Identity

An **operator / admin tool** used by ILG support and ops staff — not by the engineers who
built it. Someone triaging a customer issue under pressure must find the right row without
learning the UI first.

**Density stance: comfortable, not compressed.** Do not drag this toward a dense console
aesthetic; a "fix" that makes fuse-ui denser, darker or monospaced is a regression here,
however well it would score against a tool built for its own author.

## Theme — overridden

Wires **`next-themes` directly** (`code/src/components/app-theme-provider.tsx`) rather than
the toolkit's `GThemeProvider`, which hardcodes `defaultTheme="system"` and forwards no
props:

```tsx
<ThemeProvider attribute="class" defaultTheme="light" enableSystem>
```

**fuse-ui deliberately does not follow the OS into dark.** The class lands on `<html>`
(which carries `suppressHydrationWarning`), so the toolkit's `.dark` tokens apply.
`next-themes` resolves to one shared copy across app and toolkit, so `GModeToggle` still
reads this context. Both themes are first-class — a fix must hold in both.

## Tokens — two overrides

`code/src/app/globals.css` is a ~17-line shim: it imports the toolkit's `globals.css`, adds
`@source` for class scanning, wires `--font-mono` to Geist Mono, and overrides the brand
primary at both ends:

| | light | dark | (toolkit default) |
| --- | --- | --- | --- |
| `--primary` | `#202e56` navy | `oklch(0.7 0.13 268)` | `#0e44a4` / `oklch(0.6939 0.2335 248.08)` |

Everything else is the toolkit's. Status tints use literal Tailwind scales, per the
toolkit's missing `success`/`warning` tokens:

```
all_active     bg-green-100  text-green-800   · dot bg-green-500
needs_review   bg-yellow-100 text-yellow-800  · dot bg-yellow-500
not_configured bg-gray-100   text-gray-800    · dot bg-gray-400
```

## Type

Geist Sans throughout, **Geist Mono for identifiers, business IDs and code**. Tailwind's
default scale (`text-3xl`, `text-sm`, `text-xs`) — never pixel literals.

Page header idiom: `<h1 className="text-3xl font-bold">` + a count `Badge`
(`border-transparent bg-muted text-muted-foreground`) + a `text-sm text-muted-foreground`
purpose line. Filter/group labels are
`text-xs font-medium uppercase tracking-wide text-muted-foreground`.

## Reference module

**`code/src/modules/customers-list/*` is the current house style.** Copy its idioms:

- **`StatusPill`** — a `Badge` + `size-1.5 rounded-full` dot, with a `text-xs
  text-muted-foreground` sub-line under it carrying the detail (`7/10 connectors active`).
- **`SegmentedFilter`** — a row of `Button`s, `size="sm"`,
  `variant={selected ? 'default' : 'ghost' | 'outline'}`, count in a small `tabular-nums`
  badge inside the button.
- **`CustomerCell`** — dark rounded-square monogram, name over the business ID in uppercase
  muted mono.
- Result count above the table (`Showing 31 of 31 customers`) — an honest total, already the
  house pattern. Keep it; never render a count computed from an already-truncated list.

Reuse `UseCaseLabel` / `AppConnectorTypeIcon` / `useCaseFriendlyNames` rather than
re-deriving labels.

## Traps

- **`--primary` IS brand blue.** Advice to avoid `text-primary` and reach for literal
  `text-blue-600` because primary was near-black (`oklch(0.205 0 0)`) is obsolete — that
  changed when tokens moved into the toolkit.
- **Clickable card containing other controls → stretched link.** Card is `relative`; the
  real `<Link>` carries `after:absolute after:inset-0 after:content-['']`; nested controls
  get `relative z-10`. biome rejects `role="link"` on a `<div>` and `onClick` on a static
  element, so this is the accessible *and* lint-clean recipe.
- **Typed routes** (`typedRoutes: true`): a dynamic href in a `const` widens to `string` and
  fails `<Link href>`. Cast `as AppHref` (`@/lib/utils/next-helpers`); an inline template
  literal passed straight to `href` needs no cast.
- **`GDateField minDate={new Date()}` disables today.** The calendar compares each day at
  midnight against now; pass `startOfDay(new Date())`.
- **A Zod `.refine` that throws during a sync parse breaks tanstack-form** with "async function
  passed to sync validator": Zod's standard-schema `validate` falls back to a Promise when the
  sync parse throws. Guard refines against empty or partial input.
- Running locally needs backing services (`code/Makefile` → `watch`). Committed screenshots
  under `shots/` are real rendered evidence when it will not come up — but they are
  point-in-time, so prefer live pixels.
- Branch off **`origin/main`**, not `master`. Full Fuse org contract applies: worktree, PR,
  screenshot evidence.

Reviewed with `/ux-review` (`~/.claude/skills/ux-review/`), which reads this file as the
project layer over its universal rubric.
