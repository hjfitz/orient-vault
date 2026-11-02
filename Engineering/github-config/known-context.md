---
tags: [waypoint, github-config]
verified: '2026-08-24'
verified_paths: []
title: github-config — known context
---

# github-config — known context

`known-context.md` is exempt from staleness checks — this is interview/investigation
truth, not a claim about current source. Re-verify against code before trusting a
specific implementation detail below.

## Ownership

Confirmed 2026-08-24: **wider Fuse team**, genuinely multi-author — the
most recent archival commit is authored by Nylah Klasson, not Harry, and
earlier history adds named individuals directly as team members through
this repo. Treat this the same way as `bifrost-pubsub`/`pkg-node`/
`core-infra` for ownership purposes.

## This is the real archival authority — use it, not the catalog, to check a repo's status

Verified directly (2026-08-24): every archived-repo fact this session
already knew from the Fuse MCP catalog (`order-management-system`, the
standalone `snap-queue-polling-service`, `shopfiy-app`) traces back to an
actual `archived = true` commit in this repo. **If a future agent needs
to know whether a `gfs-bifrost` repo is genuinely archived or dead, this
repo's `main.tf` — not the MCP catalog, not a memory note — is the
ground truth**, since the catalog has independently been found stale on
several unrelated facts this session.

## A fresh archival wave, six days before this onboarding pass

2026-08-18: `performance-tests`, `llm-analytics`, `fuse-localdev`,
`testdata-ui`, and `bifrost-lang` were all archived in one commit. None
were ever cloned into `~/code/fuse/`, so nothing else onboarded this
session was affected — but this is exactly the kind of fast-moving fact
that makes a static candidate list go stale quickly: `performance-tests`
had been named a real (if thin) onboarding candidate in this session's
original estate survey, before this archival was known.

## A repo exists that hasn't been cloned locally yet

`snap-test-automation` was created via a commit here (`#15`,
"create snap-test-automation repository") but does not exist anywhere
under `~/code/fuse/`. Not investigated further during this pass — worth
knowing it's real before assuming the local checkout tree is a complete
picture of what exists.

## `secops` left this repo's management scope entirely

The 2026-07-27 commit "Stop managing secops — moving to ilg-platform"
marks the exact moment `secops-reporting` (née `gfs-bifrost/secops`)
stopped being governed here, consistent with that repo's own move to
`ilg-platform` documented in its own known-context.

## Unknowns

- Whether `snap-test-automation` is worth its own Waypoint onboarding —
  not investigated, no local checkout to inspect.
- Whether further repos are queued for archival beyond the 2026-08-18
  wave.
