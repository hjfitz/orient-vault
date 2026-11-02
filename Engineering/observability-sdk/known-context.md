---
tags: [waypoint, observability-sdk]
verified: '2026-08-24'
verified_paths: []
title: observability-sdk — known context
---

# observability-sdk — known context

`known-context.md` is exempt from staleness checks — this is interview/investigation
truth, not a claim about current source. Re-verify against code before trusting a
specific implementation detail below.

## Ownership {#ownership}

Confirmed 2026-08-24: **Matt Shaw is the effective owner/designer** of this
SDK. Harry is a regular consumer here, not a contributor — a materially
different relationship than his involvement in `github-actions` or
`terraform-modules` (regular contributor to both). Don't default to "wider
Fuse team" or attribute design decisions here to Harry; the ADR trail
points to a single primary design voice.

## "Tolaria" is an old internal codename, not a separate system

The CLAUDE.md references a "Tolaria note" (`observability-sdk-plan.md`) as
the source of the full dated decision log. Confirmed: **Tolaria was the old
internal codename for this observability library itself**, from before it
was de-mythologised (ADR-0001 §4) — not a separate external tool or system
this vault needs to integrate with. Treat any surviving "Tolaria" reference
in the repo the same way as the retired Norse package names
(`muninn`/`huginn`/`sleipnir`): historical naming, not a live pointer to
chase.

## fapi is the proof point behind the 1.0.0 stability claim

`1.0.0` wasn't cut on a schedule — it was cut **after** fapi's dev
deployment passed all three signals (logs, metrics, traces) cleanly in a
real soak. If asked how confident to be in this SDK's production-readiness
for a new consumer, that's the concrete evidence to point to, not just the
version number.

## The abandoned `pkg-node` PoC is a real trap for a future agent

`pkg-node/pkg/observability` (in the Fuse monorepo, documented separately
in this vault) is explicitly called out in this repo's own CLAUDE.md as an
**abandoned proof-of-concept — not prior art**. A future agent skimming
`pkg-node` and finding a same-named `observability` package there could
easily assume it's an earlier version of *this* SDK or a Fuse-specific fork
worth reconciling with. It is neither — `@gfs-bifrost/observability` (also
in `pkg-node`) is the real, current Fuse-facing adaptor over *this* repo;
the PoC is dead weight with no relationship to the shipped design.

## Design discipline is unusually strict and consistently enforced

Nine numbered ADRs, each cited by name in the CLAUDE.md next to the rule it
justifies (not just asserted) — package topology, logging engine model,
redaction/PII, metrics backend posture, tracing-as-separate-package,
adapter composition, testing surface, and the bootstrap facade. Style
rules are similarly exacting and stated as non-negotiable: `I`-prefixed
behaviour-contract types must be `export type`, never `interface`; no
`as SomeType` casts; classes + static-factory + builder idiom only, no
functional-style module APIs. A contribution that doesn't fit these
patterns is a sign to stop and ask, per the repo's own explicit instruction,
not to work around them locally.

## Unknowns

- Current fleet-wide adoption status of this SDK beyond fapi (tracked as
  FUSE-1012) — not investigated as part of this onboarding pass.
- Whether any other Fuse service besides fapi has completed its own soak
  onto `1.x`, or whether fapi remains the sole production-proven consumer.
