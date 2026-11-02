---
tags:
- waypoint
- distraction-dashboard
verified: '2026-09-24'
verified_sha: b628e29
verified_paths:
- code/styles/globals.css
- code/app
- code/components
title: distraction-dashboard — design language
---
# distraction-dashboard — design language

Inherits **[[ui-toolkit]]'s design language** wholesale. Unlike [[fuse-ui]], it overrides
**nothing** — `code/styles/globals.css` imports the toolkit and adds `@source` scanning
lines only:

```css
@import "tailwindcss";
@import "@ilg-platform/ui-toolkit/globals.css";
@source "../node_modules/@ilg-platform/ui-toolkit/dist";
@source "../app/**/*.tsx";
@source "../components/**/*.tsx";
```

So the toolkit doc is the whole answer for tokens, radius, type, theme mechanism and
component vocabulary. Read that; this file exists to say there is no delta and to carry
anything app-specific as it appears.

Stack: Next (App Router) · `@ilg-platform/ui-toolkit` · `next-themes` ·
`@tanstack/react-table` · `lucide-react` · `react-markdown`.

## Identity

A dashboard surfacing distraction-duty state — read at a glance, usually alongside other
work rather than as the focus. Same operator-tool stance as the rest of the ILG suite:
scannable over dense.

## Not yet established

**This app has not had a `/ux-review` pass.** The facts above are read from source; no
rendered pixels have been judged. What is missing, and should be filled by the first review
rather than guessed at now:

- The real page/route inventory and which are dense-real-data vs empty.
- Whether `next-themes` is configured the way fuse-ui does it (light default, no OS follow)
  or left on the toolkit's `system` default — **check before trusting a themed screenshot.**
- Local component idioms worth reusing, and whether it leans on `GDataTable` or a bespoke
  `@tanstack/react-table` setup.
- Any literal-Tailwind status conventions, as fuse-ui has for its pills.

Run `/ux-review` (`~/.claude/skills/ux-review/`) against it and write the findings back
here; that skill reads this file as the project layer over its universal rubric.
