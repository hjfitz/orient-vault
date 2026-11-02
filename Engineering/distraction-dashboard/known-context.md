---
tags: [waypoint, distraction-dashboard]
verified: '2026-08-24'
verified_paths: []
title: distraction-dashboard — known context
---

# distraction-dashboard — known context

`known-context.md` is exempt from staleness checks — this is interview/investigation
truth, not a claim about current source. Re-verify against code before trusting a
specific implementation detail below.

## Ownership

Confirmed 2026-08-24: **Harry's own initiative**. The product is
explicitly designed as a shared, team-wide operational console (one login,
whole team uses it during distraction duty) — but maintenance of the code
is his, the same pattern as `fuse-devtools`. Don't conflate "the whole
team uses this" with "the whole team maintains this."

## No test suite is an accepted, explicit tradeoff, not an oversight {#no-tests}

`pnpm test` is literally an echo command. The repo's own CLAUDE.md states
the real verification bar directly: lint, `build:check`, then a manual
login + Playwright screenshot pass — with an explicit instruction to test
soft navigation (clicking through the app), not just full page loads,
because a real prod-breaking bug (removing a Next-managed `<head>`
element crashes React's head reconciliation on client-side navigation)
passed every full-load smoke test that existed at the time. Treat "no
tests" as this repo's deliberate current state, and the screenshot pass as
the actual gate — don't propose writing a test suite as an obvious
improvement without checking whether that tradeoff has already been
made deliberately elsewhere in similarly-scoped internal tools.

## Heavy `@ilg-platform/ui-toolkit` consumer — cross-check the known SelectTrigger bug

The bulk of this repo's recent git history is Renovate bumps of
`@ilg-platform/ui-toolkit` (12 of the last 15 commits at last read). This
repo is exactly the kind of consumer that would hit the previously-found
`SelectTrigger` icon-stacking bug (documented in `ui-toolkit`'s own
`known-context.md`) if it renders any `Select` with icon options in its
value. Not confirmed either way during this pass — worth checking directly
if a Select anywhere in this dashboard shows its icon stacked above its
label.

## A deliberate, itemized "data we already have but don't show" backlog

The CLAUDE.md carries a specific, prioritized list of high-value additions
that need no new GitHub scopes or write-token decisions — nightly
silent-stop detection via the `event=schedule` filter, PR merge-readiness
chips off data already fetched, deployment/dependabot/rate-limit
visibility. If asked "what should this dashboard do next," this list is
the answer to check first, not a fresh brainstorm — see
[[architecture]] for the specifics.

## No `secops.yaml` in this repo

Unlike nearly every other repo onboarded this session (Fuse and
ilg-platform alike), there's no dependency-audit/gitleaks/semgrep workflow
here. Not confirmed whether this is a deliberate call (a dev-only,
read-only, no-third-party-write internal tool) or simply never added —
flagged rather than assumed either way.

## Unknowns

- Whether any `Select` component in this dashboard is affected by
  `ui-toolkit`'s known `SelectTrigger` bug — not checked directly during
  this pass.
- Whether the missing `secops.yaml` is a deliberate scoping decision or
  an oversight.
