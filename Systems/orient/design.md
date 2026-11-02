---
tags:
- system
- orient
verified: '2026-09-24'
title: orient — design language
---
# orient — design language

The system has exactly one rendered surface — the [[orient]] app — and its design language is
documented at the service level: `Engineering/orient/design.md`, anchored to
`app/globals.css`, `src/components/ui-lang` and `StateSwatch.tsx` so `wp stale` catches drift.

This doc carries only the system-level framing.

## The stance, and why it is the opposite of [[fuse]]'s

**One expert reader who already knows the domain**, at 07:00 and after hours. That single
assumption licenses everything: maximum density, 11–13px monospace, dark-only, no hero
whitespace, `g <chord>` navigation, sections that are a rule and a label rather than a card.

[[fuse]]'s surfaces assume the opposite reader — ILG support staff under pressure who did not
build the thing. Same craft bar, opposite density. **Neither may be reviewed against the
other**, which is exactly why `/ux-review` splits its universal rubric from a per-project
design doc.

## Dark-only is a decision, not a gap

`app/globals.css` defines one palette and sets `color-scheme: dark`. Its own comment gives the
reason: one theme halves contrast work across the vault's ~4,800 table rows, and Obsidian is a
keystroke away when light reading is wanted. A review should discharge the light/dark check
explicitly ("dark-only by design") rather than filing it as a finding.

## Three semantic colours

`accent` amber (the one all-purpose colour), `alert` red (a real problem), `done` green.
Everything else is `fg-2` at an opacity step. Adding a fourth needs a reason, not a use case.

## Related

`Engineering/orient/design.md` — the full language. `/ux-review` reads it as the project layer.
