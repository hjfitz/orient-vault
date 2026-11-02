---
tags: [waypoint, snap-mcp]
verified: '2026-08-24'
verified_paths: []
title: snap-mcp — known context
---

# snap-mcp — known context

`known-context.md` is exempt from staleness checks — this is interview/investigation
truth, not a claim about current source. Re-verify against code before trusting a
specific implementation detail below.

## Ownership

Wider Fuse team — same shared-ownership pattern as every other service
onboarded this session, snap-mcp included (confirmed 2026-08-24).

## The host-keyed credential cache is a real exposure, confirmed {#credential-cache-real}

> SUPERSEDED 2026-10-02 — fixed in snap-mcp#23 (`6bcd233`). The cache key is now host + username + password. Before the fix, the hosted `snap-mcp-prod` was serving PURDYFIGG's data to STUBBLE calls on ilg005. After the deploy, the same calls return each tenant's own outbound queue.

Confirmed directly (2026-08-24, not left as a maybe): `SnapApiService`'s
per-host Axios client cache (see [[architecture#credential-cache]]) is a real
gap, not a theoretical one to dismiss. Multiple credential sets addressing the
same SNAP host within one process's lifetime — credential rotation, or two
businesses genuinely sharing a host — will silently serve the **first**
caller's credentials to every subsequent caller for that host, with no error
and no log signal that this happened. Worth a real fix (key the cache on
`host + username`, or don't cache at all given the low call volume this
service handles) rather than something to note and move past. Flag this
explicitly if scoping any future work here.

## No CLAUDE.md/AGENTS.md exists

Like fuse-ui, this repo has no repo-local agent guide — everything in this
Waypoint doc set was derived directly from code and git history, not a
maintained document. Worth authoring one as a follow-up, particularly given
the credential-cache gap above is exactly the kind of thing a CLAUDE.md
"gotchas" section exists to carry forward.

## Two clones of one repo — same pattern as fuse-mcp, worse (no worktree)

`~/code/fuse/snap-mcp` and `~/code/fuse/snap-mcp-server` are the same GitHub
repo (`gfs-bifrost/snap-mcp`) checked out under two different directory
names — confirmed via `git remote -v` on both. Both were stale at onboarding
time (~1 month behind `origin/main`); `snap-mcp-server`'s checkout was the
more stale of the two and sat on an unrelated feature branch
(`hjf/fuse-1000-snap-mcp-live-schema-fixes`). Unlike `fuse-mcp`, there is no
`.claude/worktrees/` holding current work for this repo — anyone picking up
real work here should create one rather than editing either stale top-level
checkout directly.

## Deliberately mirrors fuse-mcp — read that service's docs too

The transport bootstrap, bearer-auth guard, and prod-only/no-dev-environment
posture are intentionally identical to `fuse-mcp`'s (both explicitly state
this in code comments and the README). If fuse-mcp's auth or transport
pattern ever changes, check whether the same change should land here too —
and vice versa. This service was **not** part of the fuse-mcp Go rewrite
programme; it remains a plain NestJS/TypeScript server with no rewrite
currently planned.

## Tolerant-read design is a deliberate tradeoff, not a bug to "fix"

A record failing schema validation on read still comes back (raw, with
`validated: false`) rather than the call erroring — see
[[architecture#tolerant-reads]]. This exists because a meaningful fraction of
the 43 modelled entities were typed straight from the OpenAPI spec without a
live host to verify against (see `@gfs-bifrost/snap`'s own changelog history
for the ongoing live-verification effort). Don't "harden" this into a hard
failure without checking whether that would just turn a partially-useful
investigation result into a completely useless error for entities not yet
verified.

## Unknowns

- Whether the credential-cache issue has since been fixed, or whether it's
  been formally accepted as an acceptable risk given actual SNAP host/tenant
  topology — not resolved during this onboarding pass, only confirmed as
  real.
- Current live-verification status of the ~28 entities `@gfs-bifrost/snap`'s
  own changelog flagged as not yet checked against a real host — this
  service inherits that gap directly through its generic tools.
