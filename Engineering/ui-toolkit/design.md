---
tags:
- waypoint
- ui-toolkit
verified: '2026-09-24'
verified_sha: db43671
verified_paths:
- packages/ui-toolkit/src/styles/globals.css
- packages/ui-toolkit/src/shadcn
- packages/ui-toolkit/src/core/components
- packages/ui-toolkit/src/app-layout/components
title: ui-toolkit — design language
---
# ui-toolkit — design language

The **ILG design system**. Every `ui-core` app inherits from here, so this doc is the parent
of every consuming app's own `design.md` — a consumer's doc records only what it *overrides*
or adds. Consumers today: [[fuse-ui]], [[distraction-dashboard]].

Stack: Tailwind v4 · shadcn ("new-york", base `neutral`) · lucide icons · React 19.

Lives in the **`ui-core` monorepo**: the package is `packages/ui-toolkit/`, and
`apps/showcase/` is the rendered surface to screenshot when reviewing the system itself
(the package has no runnable UI of its own). Paths below are repo-relative.

## Identity

Business/operator UI for people who did not build it. **Clarity and scannability over
density.** Light-first with a real dark mode, rounded, generous hit areas, chips and pills
carrying status. Nowhere near a tactical-console aesthetic — that is deliberate, not a gap.

## Theme

**Light-first, dark via a `.dark` class on `<html>`** — not a media query, not `data-theme`.
The package declares `@custom-variant dark (&:is(.dark *))`, so every `dark:` utility hangs
off that class. `GThemeProvider` ships here but hardcodes `defaultTheme="system"` and
forwards no props, which is why fuse-ui wires `next-themes` directly instead.

Anything screenshotting a consuming app must seed the stored theme **before** page scripts
run, or it captures a light page labelled dark.

## Tokens (`packages/ui-toolkit/src/styles/globals.css`)

Standard shadcn semantic set — `background` `foreground` `card` `popover` `primary`
`secondary` `muted` `accent` `destructive` `border` `input` `ring` `chart-1..5` `sidebar-*`
— plus `body` / `body-foreground`.

`--primary` is **brand blue**, set from `--color-brand-gfs-blue` (`#0e44a4` light) and
`--color-brand-mid-blue` (dark). A consumer may override both ends; fuse-ui does.

ILG brand palette: `brand-gfs-blue` `brand-mid-blue` `brand-light-blue` `brand-navy-blue`
`brand-mid-grey` `brand-light-grey` `brand-green` `brand-light-green` `brand-orange`
`brand-light-orange`.

**There is no `success` or `warning` token — only `destructive`.** Status tints are
therefore literal Tailwind scales in consuming apps (`bg-green-100 text-green-800`), and
that is house convention, not a token violation. Changing it means adding tokens here.

`--radius: 0.625rem` → `sm 6px · md 8px · lg 10px · xl 14px`; pills are `rounded-full`.
`--font-sans: var(--font-geist-sans)`. The `container` utility caps at `104rem`.

## Components

Everything is `G`-prefixed and imported by sub-path (`@ilg-platform/ui-toolkit/core`,
`/form`, `/data-table`, `/app-layout`, `/shadcn/<primitive>`). **Reach for a `G*` first,
a shadcn primitive second, bespoke last.**

- **Layout** — `GLayout` `GSidebar` `GNavMain` `GNavUser` `GSiteHeader` `GSiteFooter`
  `GPageContent` `GSubPageHeader` `GTopNav` `GContainer` `GHeading` `GModeToggle`
- **Data** — `GDataTable` `GTable` `GPagination` `GSortableColumnHeader` `GSortIcon`
  `GStatistic` `GSummary` `GDetails` `GList` `GOverflowScroller`
- **Form** — `GForm` `GFormField` `GTextField` `GSelectField` `GMultiSelect` `GCombobox`
  `GAutocomplete` `GDateField` `GDatePicker` `GDateRangePicker` `GTimeField` `GNumberField`
  `GPasswordField` `GCheckField` `GCheckboxField` `GRadioField` `GTagInput` `GSearchInput`
  `GSaveCancelActions` `GFieldError`
- **Feedback** — `GAlert` `GChip` `GCard` `GButton` `GConfirm` `GDangerDelete`
  `GDialogProvider` `GTooltip` `GInfoTooltip` `GLoading` `GErrorRetry` `GPageLoadingSpinner`
  `GWarnOnNavigation` `GNavigationGuardProvider`

Source layout is a consistent three-folder pattern per sub-module
(`components/` · `logic/` · `stories/` · `index.ts`); `shadcn/` is flat and treated as
third-party — never reorganised. Storybook stories are co-located.

## Conventions

- **`cursor-pointer` must be explicit** — base shadcn `Button` / `Switch` do not add it.
- Every change is a **semver bump in `package.json`** and a republish; this is a published
  package consumed inside and outside the monorepo. A token tweak is never a local edit in
  a consuming app.
- `docs/components.md` and `docs/bootstrap.md` ship inside the package — read them before
  adding a bespoke component that may already exist.

## Traps

- A consuming app's `globals.css` is usually a thin shim that imports this file; looking for
  a token there finds nothing. The real definitions are here.
- Tailwind v4 needs `@source` pointing at `node_modules/@ilg-platform/ui-toolkit/dist` in
  each consumer or toolkit class names are not scanned and silently do not generate.
- `SelectTrigger` has a known duplicate-icon bug.
- A client-side import can pull server-only deps into the bundle.

Reviewed against the rubric with `/ux-review` (`~/.claude/skills/ux-review/`), which reads
this file as the project layer. See [[fuse-ui]] `design.md` for the consumer-side overrides.
