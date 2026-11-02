---
tags: [waypoint, renovate-runner]
verified: '2026-08-24'
verified_paths: []
title: renovate-runner — known context
---

# renovate-runner — known context

`known-context.md` is exempt from staleness checks — this is interview/investigation
truth, not a claim about current source. Re-verify against code before trusting a
specific implementation detail below.

## Ownership

Wider Fuse team (confirmed 2026-08-24) — same shared-ownership pattern as
`bifrost-pubsub`/`pkg-node`/`core-infra`/`github-config`, despite this
repo directly underpinning the `renovate-clear`/`morning-digest` skill
workflows.

## The `secops` automerge carve-out likely no longer matches anything {#stale-secops-ref}

Verified directly, 2026-08-24: `config.js`'s `@ilg-platform` automerge
allowlist names `matchRepositories: [..., 'gfs-bifrost/secops', ...]`.
That repo moved to `ilg-platform/secops-reporting` on 2026-07-27 (per
`secops-reporting`'s and `github-config`'s own commit history) — **two
days before** this config file's own last edit (2026-07-29), so the move
predates the current config, not the other way round. If Renovate's
autodiscovery no longer surfaces anything at the old `gfs-bifrost/secops`
path (which it shouldn't, since the repo doesn't exist there any more),
this specific carve-out currently matches nothing — meaning
`secops-reporting`'s `@ilg-platform/ui-toolkit` bumps may no longer
auto-merge, contrary to the policy's own stated intent, with no error or
signal anywhere that this happened.

**Deliberately left as documented-only this pass, not fixed** — the
correct fix (if confirmed) is a one-line change in `config.js`
(`'gfs-bifrost/secops'` → `'ilg-platform/secops-reporting'`), but that's
an actual behavior change to a shared policy file, not a Waypoint
documentation task.

## `fuse-billing` is confirmed real and active

Appears by name in the `@ilg-platform` automerge allowlist with its own
CI-coverage comment ("lint+build:check+real tests (vitest)") — this
confirms it's a genuinely active repo, not dead weight in the Fuse MCP
catalog. Not yet onboarded into Waypoint as of this pass.

## The automerge policy is the actual ground truth, not any skill's summary of it

Any tool or skill (this session's `renovate-clear`, `morning-digest`,
or a future one) that claims "safe to auto-merge per the org's Renovate
policy" is making a claim about *this file*. If that claim is ever in
doubt, read `config.js` directly rather than trusting a cached summary —
including the summary in this Waypoint doc set, which is itself a
snapshot as of 2026-08-24.

## Unknowns

- Whether the `gfs-bifrost/secops` reference has since been corrected to
  `ilg-platform/secops-reporting` — not fixed during this pass, only
  documented.
- Whether `fuse-billing` is worth its own Waypoint onboarding pass.
