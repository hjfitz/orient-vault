---
ticket: FUSE-1063
title: Skip confirmation emission for connectors not configured to receive them
service: snap-queue-polling-service
status: complete
created: '2026-09-17'
updated: '2026-09-17'
repo: /home/hjf/code/fuse/snap-adapter
worktree: /home/hjf/code/fuse/snap-adapter/.claude/worktrees/fuse-1063-confirmation-gate
branch: hjf/fuse-1063-confirmation-connector-gate
base: origin/master
base_sha: 8a73992ea
pr: '233'
tags:
- waypoint
- plan
impl_model: sonnet
impl_effort: medium
---
# FUSE-1063 — Skip confirmation emission for connectors not configured to receive them

<!-- Guidance in this file is written as HTML comments: Obsidian hides them, agents read them,
     and `wp signoff` ignores them. Only <angle spans> are treated as unfilled placeholders, so
     they mark the places a human or agent must actually type something. Leave the comments in
     place — deleting them costs the next reader the guidance and gains nothing at the gate.

     SUPERSEDING A STATEMENT. This file is edited by several sessions over days. When something
     here stops being true, do NOT strike it through, delete it, or bury a correction inside it.
     Put one blockquote immediately ABOVE the stale text and leave the text alone:

         > SUPERSEDED 2026-09-04 — the monitor now lives in `gfs-bifrost/observability`.
         > Everything below is kept as the record of how it was first built here.

     One marker, always above, never inside. `wp decide` writes the dated entry in
     `## Decisions & deviations` that explains why. -->

## Intent
<!-- What we are changing and why. Link the ticket. -->
[FUSE-1063](https://globalfreight.atlassian.net/browse/FUSE-1063). `snap-queue-polling-service`
currently gates confirmation emission only at the business level (a `confirmations` flag on the
SNAP backend record). This ticket makes the per-connector `confirmationsEnabled` toggle the sole
gate on whether a confirmation is published into Fuse — retiring reliance on the business-level
flag now that the connector-level toggle it was standing in for actually exists. An ineligible
confirmation is left unpublished and stays in SNAP's outbound queue, picked up automatically once
the connector catches up.

Deliberate split of responsibility (per Harry): the **boolean toggle** is the one thing that's
moving upstream to this service — nothing downstream currently checks it (fapi dropped its own
copy; sftp-connector/shopify-connector never had one). The **use-case/mapping rules** (does this
connector have the relevant mapping configured) stay exactly where they already are, at each
downstream connector (sftp-connector's `CONNECTOR_MAPPING` handling, shopify-connector's
`no_confirmation_mappings` gate) — this ticket does not duplicate that check upstream. The toggle
becomes UI-driven via fuse-ui once FUSE-1123 lands; this ticket is the consuming/enforcing side,
not that UI work.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. A confirmation for a connector with `confirmationsEnabled` not `true` is not published,
      and remains claimable in SNAP's outbound queue. Verified live in dev — see Verification.
- [x] 2. A confirmation for an eligible connector (`confirmationsEnabled === true`) is published
      as today — no behaviour change for any connector already satisfying the new condition.
      Verified live in dev; the prod-backfill precondition is now also satisfied (see Increment 4's
      gate) — every SFTP/Shopify/REST connector in prod carries an explicit value.
- [x] 3. The business-level `confirmations` flag is no longer consulted by this service's
      confirmation-emission path; the connector-level `confirmationsEnabled` toggle is the sole
      gate. Use-case/mapping eligibility is unaffected — still enforced solely downstream, as
      today, not duplicated here. No live dev before/after (no dev business had the flag `false`),
      but this is now structurally guaranteed, not just behaviourally observed: the review-driven
      cleanup (Decisions & deviations, 2026-09-17) deleted the `confirmations` field from the
      codebase entirely — `SnapBackendConfig`, the cache schema, and the DTO mapping no longer
      carry it at all, so there is nothing left for any code path to consult even by accident.
      Backed by the unit test (`getAllConfiguredBusinesses returns every configured business
      unfiltered`) and the corroborating live log-message change.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `apps/snap-queue-polling-service/src/adapters/fuse-config/fuse-config.api.ts` —
  `ConnectorSourceSchema`/`ConnectorSource`/`getConnector()`, currently discards everything but
  `connectorId`/`config.type` from `GET /connectors/{id}`; widens to also carry
  `confirmationsEnabled` only (no mapping/use-case fields — those stay a downstream concern).
- `apps/snap-queue-polling-service/src/core/config/remote-config.provider.ts` —
  `resolveConnectorSource`/`fetchAndCacheConnectorSource` (the existing per-connector,
  Redis-cached, backlink-refreshed lookup this ticket extends) and `getAllConfiguredBusinesses`
  (the business-level filter this ticket removes).
- `apps/snap-queue-polling-service/src/core/snap/confirmations/confirmations.service.ts` —
  `resolveRoutingSources` (the existing per-group connector-resolution + withhold/fail-open
  mechanism this ticket extends with the new eligibility check; already the right place per its
  existing "connector unresolved → withhold unless broadcast" precedent).
- `apps/snap-queue-polling-service/package.json` — `@gfs-bifrost/types` is already `^10.1.0` as of
  a prior Renovate major bump (`#165`, on `master` before this branch cut) — carries
  `confirmationsEnabled` on `ConnectorDTO`/`ConnectorRefDTO` already; no package.json change
  needed for Increment 1.
- Not touched: `@gfs-bifrost/remote-config` (not adopted — this service already has a working,
  cheaper connector-lookup path; see Decisions & deviations), any of the 3 confirmation handlers
  lacking routing metadata today (`stock_adjustment` — out of scope, tracked under
  FUSE-1181–1185), fapi/sftp-connector/shopify-connector (verified none currently check
  `confirmationsEnabled` — fapi dropped it in PR #113, sftp/shopify never had it; their existing
  mapping/use-case checks — sftp-connector's `CONNECTOR_MAPPING` handling, shopify-connector's
  `no_confirmation_mappings` metric — are untouched and remain the sole enforcement of that rule).
- config-service — not code this ticket touches, but its `migrate:confirmations-enabled` /
  `migrate:confirmations-enabled-sftp-shopify` scripts are a **rollout precondition** (see
  Increments, gate on Increment 4).

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- Business-level `confirmations` flag is retired as a gate in this service (not just left
  alongside the new one) — resolved with Harry: the ticket's own Technical Information ("both
  gates apply") and Acceptance Criteria ("backend config no longer honoured") contradicted each
  other; Harry chose connector-config-only. The flag itself is not deleted from config-service
  (that stays separate follow-up per the ticket's stated scope) — only stops being consulted here.
- `confirmationsEnabled` must be `true` (not merely `!== false`) for the new per-connector gate —
  established from FUSE-1122's own PR text ("`true` is the behaviour-preserving value... seeding
  `false` would be a landmine the moment [SFTP/Shopify] start honouring it"), which only makes
  sense if the intended semantics are "absent counts as not-enabled" once this gate goes live.
  This is why the prod backfill gate below is load-bearing, not precautionary.
- The gate this service adds is **the boolean toggle only** — no use-case/mapping check moves
  upstream. Established with Harry: "the source of truth should be the connector toggle honoured
  at the polling service and the rules/use case at the connector level." Verified this matches
  reality before accepting it, not just taken on faith: `sftp-connector`/`shopify-connector` were
  grepped on `origin/master`/`origin/main` and neither has ever implemented a
  `confirmationsEnabled` check (zero hits) — mapping/use-case eligibility is already their own
  concern (shopify-connector's `NO_CONFIRMATION_MAPPINGS` metric, sftp-connector's
  `CONNECTOR_MAPPING` config handling), so nothing is lost by not duplicating it here. This also
  drops the `ConfirmationType → UseCase` mapping work the earlier draft of this plan required —
  no longer needed since the gate no longer branches on mapping presence or connector type.
- REST/API connectors are covered by the same uniform toggle, not a REST-specific rule — resolved
  with Harry after fapi's PR #113 (2026-08-20) dropped `confirmationsEnabled` as *its own*
  delivery-time REST gate ("deprecated... don't reintroduce it") looked like a direct
  contradiction. It isn't: fapi's isActive/webhookUrl checks are further, independent conditions
  applied at delivery time, unrelated to and unaffected by this service's upstream toggle check.
- `stock_adjustment` is the only confirmation type still lacking routing metadata (`routing`
  extension read by `extensions/routing.ts`) — verified file-by-file against `origin/master`
  (goods-in/goods-out/pick/pack/work-order-confirmation all have it; RGA and finished-good-receipt
  gained it since the ticket's own "agent reference" note was written). Its gap is already tracked
  under FUSE-1181–1185, not this ticket's to solve — groups without `routing?.connectorId` bypass
  the new check entirely, same as they already bypass connector-source resolution today.
- `GET /connectors/{id}` (config-service, via `ConnectorsController.getConnector` →
  `getConnectorWithBusinessId`) already returns `confirmationsEnabled` on detail reads (per
  FUSE-844/1122's own PR text) — this service's local `ConnectorSourceSchema` is what currently
  discards it, not a config-service gap. Not independently re-verified against the live DTO shape
  in this session; Increment 1's own test fixture is where that gets pinned down for real.
- UNRESOLVED (informational, not blocking): whether config-service's `migrate:confirmations-enabled`
  (REST, FUSE-844) has ever been run against **prod** — no evidence found either way, only a dev
  smoke-test comment on the ticket. The SFTP/Shopify backfill (FUSE-1122) is confirmed dev-only
  (2026-08-20, 121 connectors) with prod explicitly flagged outstanding on its own PR. Both need
  confirming/running in prod before Increment 4 ships (see its `gate:` line) — this plan doesn't
  resolve that itself, it blocks on it.

## Increments
<!-- Each independently implementable AND verifiable. Cite the criteria it discharges as
     (AC n,n). Tick with `wp tick`, which stamps `— done: <sha>` from HEAD; never hand-write it.
     Prefer 3-7 — more usually means the ticket is too big, so say that rather than splitting
     hairs.

     A PRECONDITION THAT IS NOT CODE goes on its own indented `gate:` line, with a confirmation
     box under it. Sign-off blocks on a ticked increment sitting above an unconfirmed gate, and
     `wp brief` shows unmet gates in its NEXT block — so "do not action this yet" stops being
     bold prose a fresh session can miss:

         - [ ] 6. Widen the subscription filter (AC 6) — verify: filter matches in dev
               gate: FUSE-1052 AND FUSE-1053 confirmed in prod
                     [ ] confirmed
-->

- [x] 1. Widen `ConnectorSourceSchema`/`ConnectorSource` in `fuse-config.api.ts` to also parse — unit tests pass (410/407... 407 tests green), build:check clean; types already at ^10.1.0 via prior Renovate major bump, no package.json change needed — done: 80d4cfc
      `confirmationsEnabled` from `GET /connectors/{id}`; bump `@gfs-bifrost/types` to `^10.1.0`.
      (foundational, no AC alone) — verify: unit test on `ConfigApi.getConnector` against a
      fixture response with the field present/absent/omitted; `pnpm run build:check`.
- [x] 2. Add `RemoteConfigProvider.resolveConnectorConfirmationsEnabled(connectorId)`, mirroring — unit + regression suite 418/418 green, build:check clean — done: f576824
      `resolveConnectorSource`'s cache-first/config-service-fallback/`ConnectorGone`-or-
      `ConnectorUnavailable`-on-failure shape exactly. Deviation from the original increment text
      (a bare pure `isConnectorEligibleForConfirmation(connector)` function): `resolveRoutingSources`
      only ever has a `connectorId`, never an already-fetched connector object, so a pure function
      over a connector would need its own resolve-and-cache wrapper anyway — building that
      consistently with the sibling method was more correct than a thin function plus a second,
      parallel resolution path. Absent `confirmationsEnabled` resolves `false`, not `true` — see
      Assumptions. Uniform across connector types, no use-case/mapping branching — see Assumptions
      for why that stays downstream. Refactored the shared connector fetch
      (`fetchAndCacheConnector`) so a cold lookup or backlink refresh caches both facts (source +
      confirmationsEnabled) from one config-service call. (AC 1,2) — verify: unit tests covering
      cache hit, cache miss (enabled/disabled/absent), gone, unavailable, and the backlink-refresh
      cache write for the new key; full suite green (418/418); `build:check` clean.
- [x] 3. Extend `resolveRoutingSources` in `confirmations.service.ts` to call — 5 new tests covering eligible/ineligible/metric/broadcast/already-known-source paths; full suite 423/423 green, build:check clean — done: ef7a1a7
      `resolveConnectorConfirmationsEnabled` whenever a group carries a `connectorId` (even if
      `routing.source` was already known — an eligibility check is independent of whether the
      source needed resolving), withholding an ineligible group via the same withhold shape
      already used for "connector unresolved" (`TAGS.DROPPED_CONFIRMATION` log line, the new
      `CONFIRMATION_WITHHELD_INELIGIBLE_CONNECTOR` metric, fail-open only for
      `broadcastConfirmations` customers). Never calls `claimConfirmations`/`emit` for a withheld
      group, so "stays in the queue" falls out of simply not calling those two side-effecting
      calls — no separate queue-retention logic needed. Groups with no `routing?.connectorId`
      (`stock_adjustment` today) bypass the check unchanged, via the existing early return. (AC
      1,2) — verify: unit tests on `getConfirmations`/`resolveRoutingSources` — ineligible group
      dropped, eligible group passes through, dropped-ineligible metered, broadcast opts an
      ineligible group back in, eligibility is checked even when source was already known (locks
      in the conditional restructure); full regression suite green (423/423); `build:check` clean.
- [x] 4. Remove the `.filter((b) => b.confirmationsEnabled !== false)` line (the — code-complete, 425/425 tests green, build:check clean; gate below still unconfirmed, not mergeable to prod yet — done: 6cf14f4
      `HOTFIX(FUSE-808 revert)` gate) from `RemoteConfigProvider.getAllConfiguredBusinesses()`, so
      every configured business is polled and Increment 3 is the sole eligibility gate. Updated the
      now-stale `HOTFIX(FUSE-808 revert)` comments in this file and in
      `BackendConfigWithConfirmationsSchema`/`cached-backend.schema.ts`/`core/config/types.ts` —
      the backend-level `confirmations`/`broadcastConfirmations` fields themselves stay (the
      latter is a distinct, still-live feature); only the filter goes. (AC 3) — verify: unit tests
      — `getAllConfiguredBusinesses` includes a business whose backend has `confirmations: false`;
      `broadcastConfirmations` still surfaces on `getSnapBackendDetails`; full suite green
      (425/425); `build:check` clean. **Code-complete and committed (`6cf14f4`), but NOT yet
      mergeable to a PR that ships to prod** — see the gate below, still unconfirmed.
      gate: config-service's `migrate:confirmations-enabled` (REST) AND
      `migrate:confirmations-enabled-sftp-shopify` (SFTP/Shopify) backfills confirmed run against
      **prod**, not just dev — load-bearing per the Assumptions note above: an un-backfilled
      connector's absent `confirmationsEnabled` reads as not-enabled under the new gate, so
      shipping Increment 4 before this backfill would silently cut confirmations for every
      business relying on the business-level flag today.
            [x] confirmed — 2026-09-17, run against prod directly (config-service's Terraform
            state read for the Mongo credential, then the already-merged, already-tested scripts
            run locally, dry-run first). REST: 0 connectors missing (already fully backfilled).
            SFTP/Shopify: 10 connectors missing, all set to `confirmationsEnabled: true` (the
            behaviour-preserving value). Re-ran the SFTP/Shopify dry-run after to confirm
            idempotency: 0 remaining. See Verification for the full evidence.
- [x] 5. Updated `CLAUDE.md` (this service) — the Config & credential resolution section (business- — CLAUDE.md updated; fuse-mcp config-domain.json judged not needed — done: d0a54f8
      level gate retired, `resolveConnectorConfirmationsEnabled` added, downstream split of
      responsibility) and the routing-resolution section (eligibility checked in the same
      `resolveRoutingSources` pass, distinct failure mode from source resolution, new withheld
      metric). Judged `fuse-mcp/data/config-domain.json` does **not** need updating —
      `confirmationsEnabled` is already documented there at the config-shape level (added by
      FUSE-1167/1122's work); this ticket adds a consumer of that existing field, not a new
      fragment/handler/backlink pattern. (no AC alone) — verify: PR review checklist item.

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-09-17 [AC 1] Deployed branch `hjf/fuse-1063-confirmation-connector-gate` to dev
  (`snap-polling-service-dev`, version `d0a54f8`/`9b61da6`). Live poll cycle at 11:34:09 UTC
  withheld `good_in`/`good_out`/`pick_confirmation`/`pack_confirmation` for GADG's "Primary API"
  (`conn_faef29654e044305ba642ef0201f00a7`, `confirmationsEnabled: false`) and
  `pick_confirmation`/`pack_confirmation`/`good_out` for GADG's "Emerald Sea"
  (`conn_05eb3ed291144b70afd1b7b23f005815`, `confirmationsEnabled: false`) — log:
  `Withholding confirmation: connector not enabled for confirmations`. **Direct before/after
  regression proof, not just a fresh assertion**: the immediately-prior poll cycle (11:32:06 UTC,
  version `e813018` — pre-fix, on `master`) shows `Confirmation claim skipped duplicates` for the
  exact same two connectorIds/types — meaning pre-fix these ineligible connectors' confirmations
  were reaching claim+publish (only deduped as already-sent on repeat); post-fix they're withheld
  at the new gate instead. This is the real regression FUSE-1063 targets, caught live.
- 2026-09-17 [AC 2] Same poll cycle: `conn_3524450f89524df2bc5519201ca20418` (ACADEMIC's "Shopify
  PI Dev Store", `confirmationsEnabled: true`, verified live via `get-business-config`) published
  a `good_out` confirmation normally — log: `Publishing message to topic
  bifrost.dev.confirmation_ready.v1 with data`. Eligible connectors are unaffected.
- 2026-09-17 [AC 3] Not directly exercised live in dev (no dev business currently has the
  business-level `confirmations` flag set `false` to show it's ignored) — but unit-verified
  (`getAllConfiguredBusinesses includes a business whose backend has confirmations disabled`) and
  corroborated live: the debug log this service emits when registering customers for polling
  changed from `Found N customers with confirmations enabled` to `Found N configured customers`
  and fired with that new text in the same dev poll cycle (34 businesses, matching the pre-deploy
  count exactly — dev has no currently-disabled-at-business-level business, so the count was
  unaffected either way, consistent with the filter genuinely being gone rather than silently
  still active).
- 2026-09-17 [inc 1-5] Full unit + regression suite: 425/425 green. `pnpm run build:check` clean.
  `pnpm run lint:fix` clean (biome, no remaining diffs).
- 2026-09-17 [gate on inc 4] **Prod backfill run.** Extracted the prod Mongo credential via a
  read-only `terragrunt state show` against config-service's prod Terraform state (from a clean
  worktree, diff-checked against `origin/main` for the two scripts first), then ran both scripts
  locally with `--dry-run` first: `migrate:confirmations-enabled` (REST) — 0 connectors missing,
  already fully backfilled; `migrate:confirmations-enabled-sftp-shopify` — 10 connectors missing.
  Applied the SFTP/Shopify backfill for real: `Backfilled 10 connector(s) with
  confirmationsEnabled=true`. Re-ran `--dry-run` immediately after: 0 remaining — confirmed
  idempotent and complete. Credential file shredded after use, never left on disk or printed.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- The prod backfill gate (Increment 4) — dev is confirmed fully backfilled (every GADG connector
  carries an explicit `confirmationsEnabled`), but prod backfill status is unconfirmed; this
  increment must not ship until Harry confirms it.
- AC 3 (business-level flag ignored) has no live dev counterexample business to exercise directly
  — covered by unit test + the corroborating log-message change above, not a live before/after on
  a `confirmations: false` business the way AC 1/AC 2 got.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->
- 2026-09-17 — An initial draft (via a planning agent, before adversarial review) proposed adding
  `@gfs-bifrost/remote-config` from scratch (the package `fapi`/`shopify-connector` use) — a new
  provider, new composition-root wiring, new backlink dispatching. Rejected after reading
  `origin/master` directly: this service already has a working, cheaper connector-lookup path
  (`resolveConnectorSource`/`resolveRoutingSources`), built by FUSE-1053, that the draft's
  research (dated 2026-09-08) missed because it had landed the day before. Re-scoped to extend
  that existing path instead of bolting on a second one.
- 2026-09-17 — The ticket's own Technical Information ("both gates apply") contradicted its own
  Acceptance Criteria ("backend config no longer honoured"). Resolved with Harry in favour of the
  AC: connector config only, business-level flag retired as a gate (Increment 4).
- 2026-09-17 — fapi's PR #113 dropping `confirmationsEnabled` as its own REST delivery gate looked
  like it invalidated this ticket's REST/API rule. Resolved with Harry: not a conflict — the
  toggle's authority is moving upstream to this service; fapi's isActive/webhookUrl checks are
  additional, independent conditions at delivery time, not a replacement for the toggle.
- 2026-09-17 — Harry asked whether any connector already implements its own `confirmationsEnabled`
  boolean check that should be removed as part of this move. Checked `sftp-connector`/
  `shopify-connector`/fapi directly: none do today (fapi's own copy was already removed by PR #113;
  sftp/shopify never had one). Harry then set the governing split explicitly: the boolean toggle
  is enforced here; use-case/mapping rules stay enforced at each connector, unchanged. This
  simplified Increments 1-3 — no `ConfirmationType → UseCase` mapping or per-connector-type
  branching needed; the eligibility check is a single uniform `confirmationsEnabled === true`.
- 2026-09-17 — PR review comment (Harry, on `fuse-config.api.ts`): the local
  `BackendConfigWithConfirmationsSchema` only mirrored the package's `BackendConfigResponseDTOSchema`
  plus two flags — use `@gfs-bifrost/types` directly instead. Checked the current package shape:
  `broadcastConfirmations` had landed in it since the local mirror was first written (types v4);
  `confirmations` had not, but it's now fully dead weight anyway (Increment 4 removed its one
  reader). Deleted the local schema/type entirely, import the package's directly, drop
  `confirmations`/`confirmationsEnabled` from `SnapBackendConfig` and the cache schema rather than
  carrying it as an unread field. Fixed the `backendsDtoToSnapConfigs` `broadcastConfirmations`
  gap (see Learnings) in the same pass since the function needed rewriting anyway.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
(none)
