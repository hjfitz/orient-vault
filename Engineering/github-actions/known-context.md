---
tags: [waypoint, github-actions]
verified: '2026-08-24'
verified_paths: []
title: github-actions — known context
---

# github-actions — known context

`known-context.md` is exempt from staleness checks — this is interview/investigation
truth, not a claim about current source. Re-verify against code before trusting a
specific implementation detail below.

## Ownership {#ownership}

Confirmed 2026-08-24: this repo is **not** Fuse-team-owned — it's explicitly
described by its own `CLAUDE.md` as a shared, ownerless platform effort
("no single owning team, no ticket queue"; ask/escalation is
`#platform-engineering`). Harry is a **regular contributor** here, which is
personal involvement, not team ownership — don't conflate the two when
deciding who to loop in on a change. A missing convention or input is
raised in `#platform-engineering` to be added centrally, not forked into a
service repo.

## The slipway incident — why "search for the consumer set" is non-negotiable {#slipway-incident}

A real, named incident, stated directly in the repo's own CLAUDE.md: when
`0.2-bonbon` was cut, it was believed to have zero consumers. In reality,
another repo (`slipway`) had already pinned it early — the tag had been cut
on an unmerged branch first — so the breaking workflow renames in that
release rode straight into `slipway`'s CI. Every secops run on its `main`
became a no-jobs startup failure for **five days** before anyone connected
it. The lesson, stated as a rule rather than advice: never assume you know
the consumer set for a rolling tag — an actual org-wide code search for the
tag string (across at least `gfs-bifrost`, `gfs-hybrid-services`, and
`ilg-platform`) is the check, not this file or anyone's memory.

## The org rename is deliberately half-finished

Canonical org: `ilg-platform` (verified via `git remote`). The README title
and most `uses:` examples still read `gfs-platform` — both currently
resolve on GitHub, and the repo's own CLAUDE.md explicitly instructs
against a mass find-and-replace: "just be accurate, and prefer
`ilg-platform` in anything new." Don't propose or perform that cleanup
without checking whether the situation has changed.

## The self-reference lockstep hazard is the single easiest way to break a tag move silently

Covered in [[architecture]], but worth restating as a fragility class: any
reusable workflow that internally calls **another** action/workflow in this
same repo by tag must bump that internal reference in lockstep with its own
tag, every time. GitHub does not propagate "the tag this workflow was
itself invoked at" into its own `uses:` lines — each is resolved literally,
independently. This has already caused a real near-miss during the
0.2-bonbon cut (the six `secops-*` workflows' internal `secops-report@`
refs) and is exactly the kind of thing that looks fine in a diff review and
breaks silently in production the first time a caller adopts the new tag.

## `on-tag.yaml` doesn't fire for a rolling-tag move

It only triggers on `v*`-prefixed push tags. Neither `0.1-affogato` nor
`0.2-bonbon` carries a `v` prefix, so force-moving either **does not**
trigger the automatic Slack release notification — announcing a tag move
is a manual step, easy to forget precisely because the automation looks
like it should cover it.

## Verified defaults diverge from the README in specific, already-documented ways

Not a general "don't trust docs" caveat — the repo's own CLAUDE.md names
the exact divergences (Node default is 22 not 20; `secops-dep-node` has no
`pnpm_version` input despite the README implying uniformity; the
`uses:` examples inconsistently mix `@main` and rolling-tag pinning). Treat
the YAML as ground truth for defaults, the README as ground truth for the
caller-facing shape (inputs/secrets/examples) once cross-checked against
the workflow file itself.

## Unknowns

- Current status of the platform MCP server (`mcp.platform.freightops.dev`)
  mentioned in the repo's own docs section — not investigated as part of
  this onboarding pass; it's a separate MCP from the Fuse one used
  throughout the rest of this vault.
- Whether the `.github/CODEOWNERS` placeholder for `/policies/` (added in
  0.2-bonbon, still needing a real username/team as of the source read)
  has since been filled in.
