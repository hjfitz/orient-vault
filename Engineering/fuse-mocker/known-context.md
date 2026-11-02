---
tags: [waypoint, fuse-mocker]
verified: '2026-08-24'
verified_paths: []
title: fuse-mocker — known context
---

# fuse-mocker — known context

`known-context.md` is exempt from staleness checks — this is interview/investigation
truth, not a claim about current source. Re-verify against code before trusting a
specific implementation detail below.

**The deepest source for this service's history is the Obsidian vault's
`Bifrost/Fuse Mocker Go API/Overview.md` and `Migration State.md`** (owned by
Harry Fitzgerald) — a full risk register, unit ledger, and decision log for
the completed Go rewrite. What follows is what's durable beyond that
programme-specific record.

## Ownership

Wider Fuse team — same shared-ownership pattern as every other service
onboarded this session (confirmed 2026-08-24), including now that the Go
rewrite itself is done.

## SNAP field lore is load-bearing and easy to lose by "cleaning up" {#snap-field-lore}

Several generator constraints exist only because a real incident happened
and someone wrote down what fixed it — not because they look reasonable in
the abstract:

- `MockReference` must be **exactly 15 characters**. `@gfs-bifrost/snap`'s
  own schema claims a 20-character max and is simply wrong — verified live
  against GADG dev by bisection (15 passes, 16 fails with `Invalid Length`).
  A 1,000-order burst once failed **in its entirety** on a single
  21-character reference.
- `order.class` has no config source and its valid values are
  **per-business and per-entity-type** (`GADW` for a GADG sales order,
  `STDREC` for a receipt, `CUSRTN` for an RGA) — passing `orderClass`
  explicitly overrides a correct config default with a wrong one.
- An RGA needs `identifiers.businessRgaNumber` or snap-adapter's
  `createDeterministicId` throws before ever reaching SNAP.
- Sales-order lines are `shipmentLines`; PO/RGA use `lines` — unknown keys
  are stripped silently, so using the wrong array name "validates" and
  produces a lineless order with no error.
- A fabricated `MOCK-SKU-n` is rejected outright (`No Product Found`) — real
  SKUs are required to actually reach SNAP.

**None of this is speculative hardening** — it's the accumulated cost of
real failures, preserved deliberately through the Go rewrite rather than
re-derived. Don't simplify a generator constraint that looks arbitrary
without checking whether it's one of these first.

## The Fuse MCP catalog is stale here too

`lookup-service("fuse-mocker")`'s tech stack still describes a pure
Next.js/Node/MongoDB stack with no mention of Go — stale relative to the
completed poly-app rewrite. This is at least the **ninth** consecutive
MCP-catalog staleness finding across the services onboarded this session;
by this point it's fair to treat the catalog as reliably a release or two
behind reality for any service that's had recent structural change, and to
verify anything load-bearing directly against the code.

## `fuse-mcp` is a real, easily-broken consumer of this exact contract

Five `mock-*` tools call 14 endpoints here with `x-api-key`, and depend on
the **literal shape** of a 400 response's `issues` array — not just the
status code. `apps/api/openapi.yaml` is the contract; a response-shape
change here breaks that consumer with no compile-time signal on the
mocker's side, only a runtime failure the next time an agent calls the
affected tool.

## Three tracked, not-yet-closed follow-ups from the rewrite

Per the migration's own "Left for Harry" list — confirmed still relevant as
of this onboarding pass, not resolved during it:

- **`Z3`**: a `go-run.yaml` reusable CI workflow is drafted
  (`go-run.yaml.draft`, in the vault migration folder) but not yet raised
  with `#platform-engineering`. Two repos (`fuse-mocker`, `fuse-mcp`)
  currently hand-roll their own Go CI rather than sharing one.
- **Confluence changelog + `#bifrost-forge` post** for the rewrite — not yet
  done as of the migration doc's last update.
- **Two deliberately-accepted small duplications**: `apps/ui/src/lib/auth/
  session.ts` still exports `encrypt`/`createSession`/`updateSession` at
  zero importers now that the API mints sessions; and `apps/ui`'s
  `lib/load/caps.const.ts` duplicates the API's load-run tier thresholds
  with nothing enforcing the two stay in sync. Both are known, not
  accidental — check the migration doc before "fixing" either as if it were
  an oversight.

## CI runs on PR, but deploy runs on every push — a real gap, tracked not fixed

`code-quality`/`secops`/`tf-plan` trigger on `pull_request` plus a nightly
cron; `deploy.yaml` triggers on push to `main`. Combined with the no-PR-flow
convention, this means **every deploy to dev currently ships with no CI gate
having run against it** — the nightly cron finds problems hours later, not
before they ship. Flagged directly in the migration doc as "fine for a
one-line fix, not fine for a language rewrite," with adding `push:` to the
quality workflows' triggers proposed as a cheap fix — not yet done as of
this onboarding pass.

## An easily-missed extra consumer of Fuse pub/sub topics — check this repo explicitly for any topic decommission

fuse-mocker is dev-only and was never on FUSE-1059's 7-repo consumer list for the PO/SO
legacy-topic decommission (fapi/snap-adapter/sftp-connector/shopify-connector/replay-service/
collector/bifrost-pubsub) — so when those topics were deleted, this repo's own dev capture
subscriptions and the Go API's target registry (`apps/api/internal/core/publisher/targets.go`)
were left pointing at deleted infrastructure, caught only after the fact (fixed in
fuse-mocker#16, 2026-09-16). GCP does **not** cascade-delete a subscription when its topic is
deleted — an orphaned subscription just sits permanently undeliverable, silent, with nothing
flagging it. Any future Fuse pub/sub topic decommission should explicitly check this repo's
`iac/projects/fuse-mocker/pubsub-capture.tf` / `remotes.tf` / `iam.tf` and its Go target
registry, not assume the service repos' consumer list is exhaustive.

Also worth noting: this repo's own `CLAUDE.md` referenced a `code/src/lib/publisher/targets.const.ts`
file as the authoritative target registry — that whole `code/` TypeScript app has since been
removed from `main` (replaced by `apps/api`, a Go rewrite, and `apps/ui`); the CLAUDE.md
reference is stale documentation, not a second live implementation. Worth a doc fix next time
someone's in this file.

## Unknowns

- Current status of the three "left for Harry" follow-ups above — not
  re-checked during this onboarding pass, only confirmed they existed as
  open items in the migration doc.
- Whether the CI-only-on-PR / deploy-on-every-push gap has since been closed.
