---
tags:
- waypoint
- fuse-ui
verified: '2026-10-12'
verified_paths: []
title: fuse-ui — known context
---
# fuse-ui — known context

`known-context.md` is exempt from staleness checks — this is interview/investigation
truth, not a claim about current source. Re-verify against code before trusting a
specific implementation detail below.

## Audience and ownership (confirmed 2026-08-24)

Internal-only — Fuse's own support/ops/engineering staff, never an actual customer.
The `/customer/{customerId}/...` route naming refers to the customer *being
managed*, not the user of the app. Ownership follows the same wider-Fuse-team
pattern as every other service onboarded this session, including the
`/user-management` role-gating surface — no narrower or more careful ownership
model despite that.

## FUSE-980 audit-trail work is merged {#fuse-980-parked}

> SUPERSEDED 2026-09-11 — merged (squash) as **FUSE-1138**, PR #216, 2026-08-25.
> `origin/main` carries `modules/audit-trail/`, `lib/db/audit-log.types.ts` and
> the audit server-functions; `origin/hjf/fuse-980-config-change-audit` no
> longer exists. Found stale while signing off FUSE-1070. The design decisions
> below (full-snapshot storage including secrets, masked at render; a
> zone-labelled timestamp fix) shipped as described; the retention window did
> not — see the note below.

The feature snapshots config-service's before/after API responses around each
write to give operators a change history that config-service itself doesn't
have (see
[[../config-service/known-context#no-audit-trail|config-service's known-context]]
for the motivating incident — a bad connector edit that was undiagnosable for two
days).

`AUDIT_LOG_RETENTION_DAYS` is set in both `iac/dev.tfvars` and `iac/prod.tfvars`
(24855 days, an explicit "retain forever" placeholder pending real product input
on the actual window — the epic calls for 30 days) — **not** "set nowhere in
`iac/`" as an earlier memory entry claimed; that memory was stale, not this doc.

## Two real production/dev incidents already traced to this app's tooling

> SUPERSEDED 2026-10-12 — masking moved server-side at read (fuse-ui#299); see [[architecture#bff-not-data-plane]].
- **Full-snapshot audit storage includes secrets, masked only at render** — a
  deliberate decision (not an oversight) made while building the parked FUSE-980
  work, because a partial snapshot would make a diff meaningless. If this lands,
  the masking-at-render boundary is load-bearing — don't let a raw snapshot reach
  an unmasked surface.
- **This app's own preview-env state was destroyed by a different service's sweep
  script**: shopify-connector's preview-env cleanup enumerated a bare `dev-pr-*`
  prefix in the shared `gs://gfs-bifrost-tfstate` bucket, misclassified fuse-ui's
  `dev-pr-198/199/200` as its own, and ran a destroy against them. fuse-ui's own
  nightly sweep workflow (`fuse-ui-preview-env-sweep.yaml`) exists partly because
  of this — but the underlying hazard (a shared bucket, prefix-based discovery
  across unrelated services) is a fleet-wide pattern, not unique to this app.

## The MCP catalog is stale on auth

`services.json` currently lists "BASIC auth" as a fuse-ui responsibility. Verified
directly: there is no Basic Auth or IAP anywhere in this app's Terraform — auth is
entirely app-level, a JWT session cookie enforced by `proxy.ts`. This is at least
the fourth MCP-catalog staleness finding across the five services onboarded this
session (also seen on snap-queue-polling-service's idempotency claim,
snap-adapter's publisher/subscriber direction, and config-service's
`customer_creation` publish claim) — treat the Fuse MCP service catalog as a
starting point, not ground truth, and verify anything load-bearing against the
actual Terraform/code.

## No CLAUDE.md — this Waypoint doc set is the first agent-maintained map

Unlike every other service onboarded this session, fuse-ui has no repo-local
`CLAUDE.md`/`AGENTS.md`. Its `README.md` is unmaintained boilerplate. There is
real institutional knowledge in this codebase (the `.func`/`.action` convention,
the BFF-not-data-plane rule, the auth gate in `proxy.ts`) that currently exists
only in the code itself and in this Waypoint doc set — there is a real gap here
that a repo-local `CLAUDE.md` would close, unlike the other four services which
already had one.

**`next dev` now writes `code/AGENTS.md` and `code/CLAUDE.md`** (Next's agent-rules generator),
and edits `next-env.d.ts`. Delete and revert them; don't commit them. Committing them would be a
team decision about a repo-local CLAUDE.md, not a side effect of a dev run. (2026-10-19)

**`mise x -- pnpm build` fails locally** with `Cannot read properties of null (reading
'useContext')` while prerendering `/_global-error`. `mise.toml` sets `NODE_ENV=development`.
Build with `NODE_ENV=production`, as CI effectively does. Standalone `pnpm typecheck` in a fresh
worktree shows `AppHref` errors until a build has generated the typed routes. CI runs `next
build`, not `tsc`. (2026-10-19)

## Stale, dirty local checkout — leave it alone

Verified 2026-08-24: `~/code/fuse/fuse-ui` sits on branch
`hjf/fuse-1000-secops-02-migrate-fuse-ui`, ~5 weeks behind `origin/main`, with
uncommitted edits to the parked audit-log feature. This may be legitimate paused
work — it was left entirely untouched. All current-state claims in this doc set
were read from `origin/main` via `git show`/`git log`, anchored to sha `ec79f7a`.
**Waypoint tooling implication**: a bare `wp verify fuse-ui <doc>` here would stamp
this stale/dirty local HEAD, not `ec79f7a` — don't trust `wp verify`/`wp stale` for
this service without first confirming the checkout is current.

## Sparse test coverage is the current real state, not a guess

~27 spec files across ~385 `.ts`/`.tsx` source files; `jest --passWithNoTests` in
CI. This is stated as fact from a direct count, not an assumption about frontend
apps in general — verify the ratio hasn't meaningfully shifted before repeating it.

## Transaction History — search semantics and known browse defects

Reference search (FUSE-1239/1240) matches on collector's side, per record type, on the same
field paths as this repo's `refPaths` chains — see the guardrail in [[architecture]].

- **Correlation-ID search matches the latest ingest's ID.** Collector overwrites a record's
  `metadata.correlationId` on every re-ingest, so a re-polled order (e.g. a Shopify order
  re-sent each poll) keeps one `_id` but changes correlation ID — GADG `#11437` carried three
  in about an hour on 2026-09-23. A correlation ID copied from an older log line can find
  nothing; search the order reference instead. Say so when handing support the feature.
- **Known defects in browse, not search** (snapshot 2026-09-23 — none filed yet):
  - Refresh doesn't update the browsed rows: `byEntity` in `transaction-history-view.tsx` is
    seeded once by a `useState` initializer and nothing re-syncs it from the server-rendered
    `tabs`, so `router.refresh()` changes nothing visible. (Search mode's Refresh re-runs the
    search and does work.)
  - Browse `loadNextChunk` drops a per-type page failure silently (`if (!result.ok) return;`).
  - Browse misorders rows once the merged, newest-first list reaches past the oldest loaded
    row of the densest record type — rows from another type then sort ahead of that type's
    not-yet-loaded newer rows. It can happen inside the first load (100 per type), not only
    after paging.
  - Collector's unfiltered list sorts on `lifecycle.createdAt` alone (stored to the second),
    so browse paging can skip or repeat rows at timestamp ties; the search route adds an
    `_id` tiebreak and doesn't.

## Audit log hardening findings (2026-10-12, fixed in fuse-ui#299)

- **Before #299, audit writes could break the action they recorded.** A failed insert after
  `createUser` lost the one-time password; on reset-password the hash was already overwritten,
  locking the user out. `logAuditEvent` and `auditConfigChange` were client-callable, so any
  session could forge rows; template saves wrote audit rows fire-and-forget on CPU-throttled
  Cloud Run; snapshots reached the browser unmasked in the RSC payload. All fixed; the
  architecture doc describes the current shape.
- **The shared redacting logger throws when handed a `MongoServerError`.**
  `@ilg-platform/observability`'s `CredentialsRedactor.restoreErrorName_` assigns `name`, which is
  getter-only on driver errors, so `logger.error(…, { error })` with a Mongo error throws — inside
  a `catch` that becomes the request's failure. The audit writer logs plain `errorName`/`errorMessage`;
  the user routes' outer `catch` blocks still pass the raw error. Shared package bug unfixed
  (snapshot 2026-10-12).
- **`sourceIp` is spoofable on previews.** `extractClientIp` takes the hop before the Google load
  balancer; previews have no load balancer.
- **`audit_log` row eras** (what the audit-service legacy importer handles): E1 #111 (FUSE-823,
  users only); E2 #189 (credential access, `businessId` only in `details`); E3 #216 (snapshots);
  E4 templates; E5 #298 (`sourceIp`); E6 #300 (`eventId`). The epic's "FUSE-837" reference has no
  record anywhere.

## The config-service client generator is broken (snapshot 2026-10-19)

`pnpm gen-config-service-client` targets `https://config.fuse.freightops.dev/api/v1/docs/openapi.yaml`,
which returns 401. Nest serves `/api/v1/docs-yaml` and `/api/v1/docs-json`. The feature-flag work
regenerated the client by hand from config-service's committed `openapi.yaml` instead. Repointing
the script is AC 1 of [[regenerate-the-config-service-client-from-the-ge]].

## Required-field coverage — what the data looks like (snapshot 2026-10-19)

- Constants are authored two ways: a fallback row, or a rule whose `from` reads no column, such as
  `upper('ECOM')`. Coverage asks `isConstantFrom` whether a `from` is fixed. `classifyFrom` calls any
  function an expression, and an unlexable `from` is never fixed.
- Shopify `sales_order` mappings in the wild already hold the "check" shape, a column rule plus a
  fallback on the same key. Dev ACADEMIC has `identifiers.shipmentId` with a fallback of `AUTO` and
  the `fulfillmentOrders[0].id` rule. FUSE-979 is the survey of fallbacks used as constants.
- The ticket's `customer.id` is the Shopify source column. The Retail ID canonical key is
  `identifiers.customerId`. The UI says Fallback while the stored type keeps the name `defaults`.
- `shopifyOut` holds the Fuse field in `from`, but the required check reads `to` on every flow.
  The check may already be wrong there. Nobody has driven it.
- `Customers/ACADEMIC/` has no `known-context.md` and nothing on the 14 Sep incident. Prod ACADEMIC
  has no `sales_order`, so the incident's mapping was dev or since removed.

## Unknowns

- Whether a repo-local `CLAUDE.md` should be authored as a follow-up to this
  onboarding pass — flagged, not decided, during this session.
- Whether the FUSE-980 branch's design decisions (e.g. the counted-diff fix, the
  zone-labelled-timestamp fix) have since been superseded by other work on
  `origin/main` that touches the same files — not diffed during this pass.
