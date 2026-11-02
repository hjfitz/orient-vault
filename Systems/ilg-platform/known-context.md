---
tags:
- system
- ilg-platform
verified: '2026-09-24'
title: ilg-platform — known context
---
# ilg-platform — known context

Decisions and hazards that source cannot tell you. Interview truth — exempt from commit
anchors by convention.

## Decisions

**Rolling tags for workflows and modules, semver for packages.** A CI fix must reach every
caller without a PR in each one, so the tag force-moves; a package's consumers pin deliberately, so a
fix needs a bump. Bumping a rolling tag's *number* is effectively a major release and callers
opt in.

**The toolkit owns tokens; consumers own nothing.** A local token override in a consuming app
is a fork of the design system. `fuse-ui`'s two `--primary` values are the sanctioned
exception, and they are brand, not structure.

**Security triage before dependency surgery.** A red audit gets an allowlist entry with a
`notes` line and a short expiry (7 days high, 5 critical) by default. Fix the direct
dependency where a compatible release exists. An override is reserved for an advisory that is
genuinely reachable *in our code* — if you cannot articulate the path, allowlist instead. The
short expiry is the point: it forces a return visit.

## Hazards

**A `workspace:*` dependency does not auto-follow a downstream fix.** pnpm freezes it to an
exact version at publish time, so publishing a fix in one package does **not** reach a
consumer that reads it through another package — that one needs its own bump and republish.
This has stranded a real fix for nearly two majors.

**An unbounded `>=` peer range behaves differently from `workspace:*`** and is why some
consumers need no republish at all. Check which one a package actually declares before
promising a fix has landed.

**Cross-org auth.** These repos are under `ilg-platform`, Fuse is under `gfs-bifrost`.
GitHub Packages auth, `gh search` SAML visibility and PAT scope all behave differently across
that boundary — a search that returns nothing may be blind rather than empty.

**SRE PRs are proposals.** The KTLO cloud-engineering team raises changes against some of
these repos; they are reviewed, not rubber-stamped, and never merged in Wolf-owned repos.

**Terraform state is split per environment** and concurrent pushes race the lock. Share a
plan before applying; the agreed plan covers the whole merge-and-approve chain for that
change, not each click.

## Related

[[fuse]] — principal consumer. [[ui-toolkit]] `design.md` — the design system detail.
