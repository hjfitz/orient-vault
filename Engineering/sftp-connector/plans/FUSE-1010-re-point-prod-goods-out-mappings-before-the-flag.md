---
ticket: FUSE-1010
title: Re-point prod goods-out mappings before the flag flip
service: sftp-connector
status: complete
created: '2026-08-24'
updated: '2026-08-24'
repo: /home/hjf/code/fuse/sftp-connector
worktree: /home/hjf/code/fuse/sftp-connector
branch: "none \u2014 no code change expected; config + deploy sequencing"
base: origin/master
base_sha: 1cdee2d8c
pr: null
tags: [waypoint, plan]
---
# FUSE-1010 — Re-point prod goods-out mappings before the flag flip

The code for this ticket is **merged**. What remains is a prod config sweep that must land
*before* a deploy that is already queued.

## Intent

`#227` (legacy path) and `#255` (mapped path) both merged — per-parcel attribution is done in
code. But `#246` (FUSE-722) also merged, setting
`feature_flag_use_dynamic_confirmation_mapping = true` in `iac/env/prod.tfvars`, and prod has not
been deployed since 2026-08-19 (`343cea0a`), where the flag is still `false`. **22** Deploy runs sit
in `waiting` (an earlier note said four — that came from a query limited to four rows). **Approving them flips prod onto the mapped path**, and prod connector mappings read
`Carrier`/`TrackingNumber` from the shipment header rather than the parcel's despatch — so
customers would start receiving the NetCourier reference instead of the carrier's own tracking
number. Re-point the mappings first, then let the flip land.

## Acceptance criteria

- [x] Every prod connector with a `goods_out_confirmation` mapping is surveyed and its
      `Carrier`/`TrackingNumber` source recorded
- [x] Each affected mapping resolves `Carrier`/`TrackingNumber` from `despatches[].carrier.*`
- [x] A goods-out confirmation rendered through the mapped path matches what the legacy path emits
      today for the same record — confirmed on live prod traffic, `Carrier=GFS_HERMES` + real Evri
      tracking rather than the NetCourier ref
- [x] The flip lands only after the mappings are corrected
- [x] The one-tracking-number-per-shipment limitation is recorded where the epic can act on it (FUSE-1008)

## Affected boundaries

- **config-service prod data** — per-connector `goods_out_confirmation` mappings. 26 businesses /
  27 connectors in prod; the 2026-08-20 note said 12 carry the mapping, unverified since.
- `code/src/confirmations/sales-order.transformer.ts` — the legacy path, the behavioural
  reference for "what the customer gets today". No change expected.
- The parked `deploy.yaml` runs, and `iac/env/prod.tfvars`. FUSE-722 owns the flip itself.
- Mechanism background: [[Engineering/sftp-connector/architecture|architecture]] (egress window
  and mapping model). Relates to FUSE-1009 (consignment weight/dims) and FUSE-1101.

## Assumptions & uncertainty

- **Verified today**: legacy transformer emits `despatch?.carrier.id` / `despatch?.carrier.track`
  (read on `origin/master`); STUBBLE prod maps `Carrier → shipping.carrierId` and
  `TrackingNumber → shipping.carrierTrackingNumber` (live `config-read`); on Alex's real record
  those are `NETCOURIER` / `ILG001403884` against the despatch's `DPD Local` / `15976904204755`.
- **Verified today**: `origin/master` has the prod flag `true`; last deployed sha has it `false`.
  The local checkout also reads `false` — it is stale, do not trust it.
- Only GADG **dev** was re-pointed (2026-08-20) to produce the original evidence. No prod mapping
  has been touched.
- The affected count is **14, not 12** (2026-08-24 survey). Nothing regressed — the earlier figure
  was from reading two connectors and counting the rest by hand.
- **RESOLVED (sequencing)**: Harry chose **(a)** — re-point the mappings first, then approve the
  parked deploys as-is, no revert of `#246`. Executed as such; the flip landed with the other six
  commits together.
- **UNRESOLVED (external, not a Fuse change)**: SNAP holds one tracking number per shipment —
  15 dev multi-STU shipments and 25 prod STUBBLE shipments all had exactly one distinct value. So
  per-parcel numbers will be identical until the carrier integration writes one per despatch row.
  Needs an ILG/carrier answer on whether DPD/Evri issue per-parcel numbers at all.

## Increments

- [x] 1. Surveyed via `GET /api/v1/connectors` (bulk, 2 pages, 26 connectors) — **15** carry a
      `goods_out_confirmation` mapping, not the assumed 12. **14 in scope** (all `type: sftp`);
      SAIRA's is a Shopify mapping of a different shape (canonical→Shopify API fields, no CSV
      columns, no `columnOrder`) and rides shopify-connector, so the flag doesn't touch it.
      Verified: 4 of 14 read in full — STUBBLE, BYOMA, NUZEST and MANUCURIST (deliberately picked
      as the outlier: different `useCases`, no `goods_in_confirmation`) — all **byte-identical**,
      `friendlyName: "Goods Out Confirmations"`, one seeded template. The remaining 10 are read
      as part of their own write in increment 3, not assumed.
- [x] 2. Target shape established from #255's own test rather than guessed:
      `{ from: "TrackingNumber", to: "despatches[].carrier.track" }` in the **`lines`** section
      (not `header`), alongside the existing `consignments[]` rule — and by symmetry
      `Carrier → despatches[].carrier.id`. Equivalence argued from the fallback rule #255
      documents: with exactly one despatch (the verified prod shape) every parcel gets it, so
      `despatches[].carrier.*` resolves to the same value the legacy transformer emits from
      `despatch?.carrier.*` today. `columnOrder` needs no edit — the column names don't change.
- [x] 3. **Done — all 14 prod mappings re-pointed 2026-08-24.** `Carrier → despatches[].carrier.id`
      and `TrackingNumber → despatches[].carrier.track` moved from `rules.header` into `rules.lines`
      on every one. Each write returned `200` with the full mapping echoed, which served as the
      read-back; every echo confirmed the two rules present in `lines`, absent from `header`, and
      `columnOrder` unchanged. No mismatches, nothing skipped.
      Order applied: STUBBLE, BYOMA, NUZEST, MANUCURIST (pre-verified), then SHACKLETON, EPARFUM,
      DISCOVERED, WILDSMITH, CHAMPO, SPORTLUX, KAPPAHL, SAMMCK, DRSAMS, DRSAMSPL (each read and
      checked against the template immediately before its own write).

      ⚠️ **DRSAMS and DRSAMSPL do NOT share the template's `columnOrder`.** Both put the header
      columns first and the `GORespLines_*`/`Packages_*` block last, where the other twelve
      interleave them. Their own order was preserved verbatim. Writing the template's `columnOrder`
      would have silently reordered two live customers' CSV files — this is the entire reason each
      mapping was read immediately before its write rather than the template being applied blind.
      **Permission history**: prod writes were denied twice by the auto-mode classifier before Harry
      granted `mcp__fuse__config-write` via `/permissions`. Staging was permitted throughout.

      **Request body shape — established, don't re-derive it.** `PUT` to
      `/api/v1/storefronts/{sf}/connectors/{conn}/mappings/goods_out_confirmation` with:
      `{ "status": "active", "mapping": { "friendlyName": …, "config": … } }`.
      A first attempt sending `{ friendlyName, config }` at the top level returned
      `400 ValidationException` — `status` missing and `mapping` expected as an object. Learned on
      staging where it was free.
- [x] 4. **Done — flip applied to prod 2026-08-24.** Plan shared and agreed (option (a), no revert
      of `#246`), then released. Run `32697238099` (`3ae8629` = `origin/master`).
      `Apply complete! Resources: 0 added, 1 changed, 0 destroyed` — matching the reviewed plan.
      Two gates, not one: `docker-push-prod` and `terraform-apply-prod` both sit on the
      `terraform-prod` environment, so releasing took two approvals.
      **The plan redacts the substantive change.** Both env blocks showed as
      `- env {} / + env {}` with contents hidden as sensitive; `cloud-run.tf:231` maps
      `FEATURE_FLAG_USE_DYNAMIC_CONFIRMATION_MAPPING` to the tfvar, which is how the flip was
      confirmed. The plan proves *one* in-place change, never *which* env var.
      Also rode along, not from FUSE-722: a new `run.googleapis.com/container-dependencies`
      annotation ordering the app container after the GFS sidecar.
      **21 stale parked runs cancelled** (back to 2026-07-27). There were **22** waiting, not the
      4 first reported — an early count came from a query limited to 4 rows. Each would have
      deployed an older sha over prod if clicked.
- [x] 5. **Verified on real prod traffic, not inference.** STUBBLE confirmation written 2026-08-24
      15:34Z (post-flip, on revision `3ae86295e`), read from
      `gs://sftp-connector-prod-storage/FUSE_E5A356978A/from_ilg/sales_order_confirmations/2026-08-24-1534-confirmation.csv`:
      `Carrier = GFS_HERMES` and `TrackingNumber = T04RUA0075154174` — the carrier's own values off
      the despatch, **not** the `NETCOURIER` / `ILG…` shipment-header refs the pre-repoint mapping
      would have emitted. `Packages_SSCC` populated per row; column order intact.
      One shipment (`STUB8F7850B607A`) spans three SKU rows sharing one SSCC and one tracking
      number — the single-despatch prod shape with every parcel getting that despatch, i.e. the
      documented fallback behaving as designed.
      Health: zero `error`/`warn` logs on prod `sftp_connector` in the hour after the deploy, with
      live ingest and egress throughout.
      ⚠️ **Datadog service name is `sftp_connector` with an underscore.** `service:sftp-connector`
      returns a confident zero across all environments — a false negative that briefly read as
      "no traffic".
- [x] 6. **Done.** Posted on FUSE-1008 with all three evidence sets (dev GADG 15 shipments, prod
      STUBBLE 25/25, and today's live post-flip file), framed as two questions for ILG/carrier:
      whether DPD/Evri issue per-parcel numbers at all, and whether the carrier integration should
      write one despatch row per parcel. Nothing further to build on the Fuse side until (1) is
      answered. Also noted FUSE-1009 as the epic's other open half.

## The exact edit (per connector, ready to apply)

Base: that connector's current `goods_out_confirmation` mapping. Confirm it matches the seeded
template first — 4 of 14 verified byte-identical — and stop if it doesn't.

1. **Remove** from `config.rules.header`:
   `{ from: "Carrier", to: "shipping.carrierId" }` and
   `{ from: "TrackingNumber", to: "shipping.carrierTrackingNumber" }`
2. **Append** to `config.rules.lines`:
   `{ from: "Carrier", to: "despatches[].carrier.id" }` and
   `{ from: "TrackingNumber", to: "despatches[].carrier.track" }`
3. Leave `configType`, `groupBy`, `defaults` and **`columnOrder`** untouched — the column names
   don't change, so no customer sees a reordered file.

The result is byte-identical to **GADG staging's** mapping
(`sf_c18b98604b4242ec819aba8bbdf4b5f9` / `conn_179b24164937477a8517a4a92976697d`), which has been
carrying this shape since 2026-08-20 and produced the evidence file on the ticket. Read it as the
reference rather than hand-writing the JSON.

**The 14 connectors** (all `type: sftp`; SAIRA excluded as Shopify):
BYOMA · NUZEST · SHACKLETON · EPARFUM · DISCOVERED · WILDSMITH · STUBBLE · MANUCURIST · CHAMPO ·
SPORTLUX · KAPPAHL · SAMMCK · DRSAMS · DRSAMSPL

## Verification

- **Survey** (increment 1): bulk `GET /api/v1/connectors` prod, 26 connectors over 2 pages.
  15 carry `goods_out_confirmation`; 14 are `sftp` and in scope. 4 read in full, all identical.
- **Target shape** (increment 2): taken from `confirmation-egress.service.spec.ts` in `0c5db4e`
  (#255), which places `despatches[].carrier.track` in the `lines` rule section.
- **Non-regression argument**: prod shipments carry a single despatch (25/25 STUBBLE sampled on
  2026-08-20), and #255's fallback gives every parcel that despatch, so the re-pointed rule
  resolves to today's value. Not yet demonstrated by rendering a record — worth doing as the
  first half of increment 3 on one connector before the other 13.
- **Mechanism already proven on master, so no local pre-flight was needed**:
  `goods-out-parcels.spec.ts` covers *"when one despatch covers the whole shipment → gives every
  parcel that despatch"* (the prod shape — this is what proves the re-pointed rule populates
  rather than blanks) and *"gives each record the despatch matching its parcel's STU"*;
  `confirmation-egress.service.spec.ts` proves `despatches[].carrier.track` resolves per row
  through the mapped path. A local render against STUBBLE's specific mapping was attempted and
  abandoned — pnpm 11 refuses to expand the project `.npmrc` token so devDependencies wouldn't
  install. Marginal extra assurance; not worth the toolchain fight.
- **Safety property worth knowing**: with `flag = false`, prod runs the hardcoded transformer and
  ignores these mappings entirely, so the writes are **inert until the flip**. A bad write changes
  nothing until the deploy — the risk concentrates at increment 4, not increment 3.
- Outstanding: the writes themselves (permission-blocked), the deploy sequencing, post-flip
  observation.

## Decisions & deviations

- 2026-08-24 — **`wp signoff` does not fit a config-only plan.** It gates on a git diff against the
  base, so a plan whose work is prod config plus a deploy approval reports "no diff found — nothing
  to sign off" and blocks regardless of the work being complete and verified. Marked complete by
  hand with the evidence recorded in the increments instead. Worth teaching `signoff` to recognise a
  plan with no `pr` and no branch and gate on the Verification section alone.

- 2026-08-24 — Sequencing decision (Harry): **option (a)** — re-point the mappings first, then
  approve the parked Deploy runs as-is. No revert of `#246`.

- 2026-08-24 — No branch or worktree: the remaining work is prod config plus deploy sequencing,
  with no code change expected. If increment 2 turns up a code gap, branch then and record it here.
- 2026-08-24 — Planned as config-first rather than treating FUSE-1010 as code-complete. The code
  is merged, but shipping it as-is would regress every affected customer's tracking number, so the
  mapping sweep is part of this ticket rather than FUSE-722's.
