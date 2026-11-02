---
tags: [waypoint, ilg-secure-notes]
verified: '2026-08-24'
verified_paths: []
title: ilg-secure-notes — known context
---

# ilg-secure-notes — known context

`known-context.md` is exempt from staleness checks — this is interview/investigation
truth, not a claim about current source. Re-verify against code before trusting a
specific implementation detail below.

## Ownership

Confirmed 2026-08-24: **Harry's own responsibility**, narrower/personal
ownership — the same pattern as `fuse-devtools`/`distraction-dashboard`,
despite `fuse-ui` having a real, load-bearing runtime dependency on this
app for SFTP credential handover.

## fuse-ui's dev environment points at this app's PRODUCTION link

Confirmed directly, 2026-08-24: because there is no dev/staging instance
of `ilg-secure-notes`, `fuse-ui`'s **dev** environment is configured to
point at the same `https://ots.ilg.software` production URL that prod
uses. Practical implication: exercising SFTP-connector creation in
fuse-ui's dev environment mints a **real production one-time-secret
link**, not a scoped dev artifact. This is a genuine cross-environment
coupling worth knowing before assuming "dev" means "no prod side
effects" anywhere the two systems touch.

## A real, previously-shipped incident: white-on-white in production for months

The `.brand-gradient` CSS-splitting bug (see [[architecture]]) wasn't
theoretical — it actually shipped and ran in production, unnoticed, for
months, before someone caught it. Worth remembering as a concrete example
of how a silent CSS regression can hide in a low-traffic internal-adjacent
tool for a long time with nobody reporting it.

## Verified: not affected by the ui-toolkit SelectTrigger bug

Checked directly against the current source (not left as an open
question, unlike `distraction-dashboard`'s equivalent note): both `Select`
usages here render plain text options with no icons, so the inverted
Tailwind-variant bug found in `@ilg-platform/ui-toolkit`'s `SelectTrigger`
(documented in that repo's own known-context) has no visible effect here.

## A minor, low-stakes doc inaccuracy

The README's CI/CD table says "Deploy | Push to main" — the actual
default branch is `master` (confirmed via `git remote show origin`).
Cosmetic, not worth an urgent fix, but worth knowing the README isn't
byte-accurate on this one detail.

## Unknowns

- Whether there are other API/CLI consumers of `POST /api/secrets`
  beyond `fuse-ui` — the app's own CLAUDE.md mentions "CLI consumers" of
  the contract generically, but none beyond fuse-ui were confirmed during
  this pass.
