---
tags: [waypoint, pkg-node]
verified: '2026-08-24'
verified_paths: []
title: pkg-node — known context
---

# pkg-node — known context

`known-context.md` is exempt from staleness checks — this is interview/investigation
truth, not a claim about current source. Re-verify against code before trusting a
specific implementation detail below.

## Ownership

Wider Fuse team — same shared-ownership pattern as every other service
onboarded this session (confirmed 2026-08-24), despite this repo's fleet-wide
blast radius on a mistake.

## The root CLAUDE.md is one release behind its own repo {#resilience-doc-gap}

Verified directly, 2026-08-24: `pkg/resilience` was extracted out of `snap`
in the very latest commit on `origin/main` (PR #210, "extract
@gfs-bifrost/resilience out of the snap package"). The **mechanical** side of
that change landed correctly — `publish-package.yaml` has a working
`publish-resilience` job, and `snap`'s own publish job now depends on it —
but the root `CLAUDE.md`'s **prose** (its packages table and ASCII
dependency-graph diagram) still describes 9 packages and doesn't mention
`resilience` at all. This is a small, genuinely just-missed gap in an
otherwise exceptionally well-maintained file (it explicitly instructs future
editors to update the packages table on exactly this kind of change) — worth
fixing in the next PR that touches this file, not evidence the file is
generally unreliable.

**Also stale (snapshot 2026-10-14):** the root `CLAUDE.md`'s remote-config row says its `types` peer is `>=6.1.0`. Source (`pkg/remote-config/package.json`) says `>=10.13.0`, and Renovate raises it on each `types` release. Fix it in the next PR that touches the file.

## A second known gap: `edi`'s CI workflow is broken as written

> SUPERSEDED 2026-09-24 — fixed by pkg-node#237 (FUSE-1231): `code-quality-edi.yaml` now uses the same templates as the other packages, and edi PRs get green Lint/Tests checks (pkg-node#241-#248 all ran them).
> Everything below is kept as the record of the gap.

`code-quality-edi.yaml`'s `test-suite` and `lint-check` jobs reference local
workflow templates (`template-run-test-suite.yaml`,
`template-run-lint-check.yaml`) that don't exist in this repo — only
`template-prepare-node-cache.yaml` and `template-publish-node.yaml` do. This
is called out directly in the repo's own `CLAUDE.md` as a known, unfixed
problem: if you touch `pkg/edi` and need green CI, the workflow needs
rewriting to match the other six packages' pattern first, not just re-run.

## Per-package documentation is genuinely uneven — don't assume uniform quality

Only `cache` and `edi` have their own package-local `CLAUDE.md`. Of the
package READMEs: `edi`, `pubsub`, `remote-config`, and `observability` are
current and accurate; `ddp`'s is serviceable; `rules-engine`'s is a **stale
stub** that imports a `RulesEngine` export which doesn't exist and says "Add
usage examples here"; `types` and `cache` have no README at all. For any of
these, the real public surface is `src/index.ts`, not the README.

## Publishing has bitten the fleet before by being version-gated, not diff-gated

A merged PR that forgets to bump the changed package's `version` in
`package.json` is a **silent no-op** for that package — the code change
lands on `main` but nothing publishes, and the change is stranded until a
later version bump republishes it (has happened to `types`). This is stated
directly in the repo's own `CLAUDE.md` as the single most important thing to
get right when merging here. Always check the version bump is present in the
diff, not just that the PR is green.

## The pubsub/types lockstep hazard is real and hand-maintained

`@gfs-bifrost/pubsub` duplicates envelope/metadata Zod shapes from
`@gfs-bifrost/types` by hand (it takes `types` as a real dependency for
canonical types, but the envelope shapes themselves are a separate,
hand-mirrored copy). A field added to one without the other in the same PR
means the ingest schema silently strips the new field on decode — this is
the same "FUSE-794-style" strip-class bug documented repeatedly in the org's
package changelog for other packages, but here it's structural (by design of
how the two packages relate), not a one-off.

## Unknowns

- Whether the `resilience` doc gap and the `edi` CI-workflow gap have since
  been fixed — both were confirmed present (snapshot 2026-08-24), not resolved
  during this onboarding pass.
- Whether there's a plan to eventually give `pubsub` a real dependency on
  `types`'s envelope shapes instead of hand-mirroring them, closing the
  lockstep hazard structurally rather than by discipline.

## EDI serializers are customer-agnostic by rule {#edi-customer-agnostic}

Every trading-partner value in `@gfs-bifrost/edi`'s outbound serializers (RECADV, DESADV, OSTRPT, INVRPT) is a caller option with an EANCOM D.96A default (`*Codes` / `*_DEFAULT_CODES`, overridden via `options.codes`), or per-record data on the `*Out` shape. Customers appear only as test fixtures (`src/__tests__/fixtures/ct-*-config.ts` reproduce Charlotte Tilbury's samples). A partner-specific constant or branch in `src` is a defect. Durable decision: `sftp-connector/decisions/2026-09-24-edi-egress-is-customer-agnostic-partners-are-config-never-co.md`. Charlotte Tilbury's old Confluence field-coverage page (215678985) is trashed; don't cite it. (Added 2026-09-24, FUSE-1253.)

## EDI ingress is built from shared segment readers {#edi-segment-readers}
- **One reader per segment.** Since edi 0.7.0 each EDIFACT segment has one shared reader (`normalizer/{finders,line-readers,party}.ts`), and the normalizers compose them. Values are keyed by raw qualifier; the connector mapping chooses what a qualifier means.
- **The characterisation goldens are the contract.** `characterisation.test.ts` pins every dotted path the normalizers produce, because connector mappings address those paths. Adding keys is fine; changing a recorded value needs a deliberate regeneration (`EDI_UPDATE_GOLDEN=1`).
- **Per-message quirks are parameters, not bugs to unify.** Line groups end at different segments per message (INSDES/PRICAT skip UNS/UNT; ORDERS closes at UNS/CNT/UNT; RECADV/INVRPT skip UNT). Unparseable QTY handling also differs (INSDES → 0, ORDERS → dropped, PRICAT → 0 if missing / dropped if non-numeric). Unifying either changes output.
- **The Puig DESADV guides (V06, SHIPMENT V01) are both 3PL → Puig messages** (pack and loading). There is no inbound ASN spec; CT's inbound samples are the spec.
- **DESADV line numbers aren't unique.** CT's pack message repeats `LIN+1` on every line, so nothing may key DESADV lines by `lineNumber`.
