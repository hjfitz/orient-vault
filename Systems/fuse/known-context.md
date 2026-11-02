---
tags:
- system
- fuse
verified: '2026-09-24'
title: fuse — known context
---
# fuse — known context

System-level decisions and constraints that source cannot tell you. Per-service nuance lives
in `Engineering/<service>/known-context.md`; per-customer nuance in `Customers/<ID>/`.

Exempt from commit anchors by convention (same reasoning as a service's `known-context.md`):
this is interview truth, not a description of code.

## Decisions that shaped the platform

**Canonical-first, no exceptions.** Raw or connector-shaped payloads never reach the event
bus. The rule is absolute because every previous "temporarily bypass it" became permanent.

**`recordType`, not `use_case`.** Decided 2026-05-08 (Oliver Denton). In code and on Pub/Sub
attributes the identifier is camelCase `recordType`. "Use case" survives as the conversational
term in docs and tickets — the rename applies to identifiers, not vocabulary. Older code still
carries the legacy names; do not introduce new ones, do not rename outside a scoped cutover.

**Cross-entity topics filter at the subscription, not in code.** `create_record`,
`create_acknowledge`, `create_data_failure` carry every record type discriminated by an
`attributes.recordType` filter declared in Terraform. Never subscribe unfiltered and branch in
the application.

**Manual retry budget over Pub/Sub DLQs.** A failure should be inspectable and redrivable by a
human, not silently parked. Hence replay-service as a failure inbox with a
"would this pass the canonical gate?" answer built in.

**Shared types are one package.** `@gfs-bifrost/types` is the single source of truth; a type
needed by two services goes there first. The package changelog in `~/code/CLAUDE.md` is
unusually detailed on purpose — the fleet's pins diverge, and a fix published in `types` does
**not** reach a consumer that reads it through another pkg-node package until that package is
itself bumped and republished.

## Constraints you cannot design away

**SnapFulfil is a vendor WMS.** No notice on prod upgrades. Its quirks are contract, not bugs:
a kit explodes into component lines on despatch (only the parent carries the attachment);
some write-time validation failures return HTTP 2xx with `{Status:"Error"}`; several entity
routes reject OData params outright.

**No cancellation or amendment path exists.** Once a record is created there is no
Fuse-mediated way to withdraw or revise it. This comes up repeatedly in support and the honest
answer is out-of-band intervention.

**Config is deep-merged, not replaced.** config-service PATCH uses lodash `mergeWith` with
arrays replaced — so a minimal PATCH is lossless, and a "full document" PUT is the dangerous
one.

**A connector-config field must be added in two places** or `remote-config` silently strips it
before any consumer sees it. This has bitten at least three times (FUSE-883, FUSE-954,
FUSE-1025) and is the single most repeated own-goal in the platform.

## Ways of working

- Every PR gets a `wp ledger` entry, ticketed or not — orient's `/ledger` is built from them,
  and an unrecorded PR is invisible there.
- Evidence is required on every PR, including backend-only ones. Passing unit tests are not
  evidence.
- A red check on your PR is yours to clear even when your change did not cause it; the fix
  goes in its own PR off the default branch.
- Sprints are variable-length. Story points are reconciled from Slack poker rounds.

## Related

[[ilg-platform]] for the shared CI, IaC and UI surfaces every Fuse repo depends on.
[[orient]] for the tooling that reads and writes this vault.
