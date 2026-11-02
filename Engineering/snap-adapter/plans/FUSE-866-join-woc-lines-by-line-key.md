---
ticket: FUSE-866
title: Join WOC lines by Line key
service: snap-adapter
status: complete
created: '2026-08-24'
updated: '2026-10-05'
repo: /home/hjf/code/fuse/snap-adapter
worktree: /home/hjf/code/fuse/snap-adapter/.claude/worktrees/fuse-866-woc-line-join
branch: hjf/fuse-866-woc-line-join
base: origin/master
base_sha: acb85ed4b
pr: '204'
tags:
- waypoint
- plan
---
[]()# FUSE-866 — Join WOC lines by Line key

QA rework on a merged ticket. The **producer** is wrong, not the connector.

## Intent

`WorkOrderConfirmationHandler.confirmationsToCanonical` builds lines by concatenating
`shipment.ShipmentLines` and `finishedGoodReceipt.ReceiptLines`. Real Snap data shows both
documents mirror **the same line keys**, so a 2-line work order emits 4 canonical lines with
roles assigned by source document and `consumed` taken from `QtyShipped` — which is
structurally 0 because a work order never despatches. Replace the concatenation with a full
outer join on `Line`, derive role from plan quantities, and take actuals from the right side of
each document.

Scope is snap-adapter only. sftp-connector needs no change — it applies a mapping to whatever
lines it receives; it just needs re-verification once the producer is fixed.

## Acceptance criteria

- [x] A confirmation for a 2-key work order carries exactly **2** lines, one per `Line` key
- [x] Component line: `role=component`, `quantities.consumed = QtyPicked`, `required = QtyRequired`
- [x] Finished-good line: `role=finished_good`, `produced = QtyReceived`, `rejected = QtyRejected`
- [x] A receipt-only line key still appears (full outer, not shipment-driven)
- [x] An unclassifiable key is warned about, never silently mislabelled
> SUPERSEDED 2026-10-05 — met in substance on a fresh work order. `GADG7896F1CD757` had already been processed and could not be re-run. QA ran `GADG22E3C9CA151` on 2026-08-28 and passed it: 2 rows in exactly the expected shape. See the 2026-10-05 sign-off bullet under Verification.
- [x] The SFTP file for `GADG7896F1CD757` matches QA's expected 2-row output — the one AC still
      open; see increment 6 and Decisions below

## Affected boundaries

- `apps/snap-queue-polling-service/src/core/snap/confirmations/work-order-confirmation.confirmation-handler.ts`
  (+ its spec) — the only production file this should need.
- `CanonicalWorkOrderConfirmation` line shape is **unchanged** — `quantities` already carries
  `ordered/required/allocated/picked/consumed/produced/rejected` on one flat object, so a joined
  line needs no `@gfs-bifrost/types` bump. Verified against the installed `.d.ts`.
- Downstream consumers see a changed line *count and shape* on the same contract:
  sftp-connector egress mapping (the file QA reviewed) and fapi's WOC webhook (FUSE-868).
- `work-order.discriminator.ts` — the receipt lookup itself works and is out of scope.
- **Doc-scope note for sign-off:** snap-adapter's `waypoint.yaml` / `architecture.md` describe
  the write side (`apps/snap-adapter`) and treat the poller as a sibling. This change is in
  `apps/snap-queue-polling-service`, so either extend those docs or split the poller into its own
  vault folder.

## Assumptions & uncertainty

- **Both documents mirror every line key** — now **two** independent observations, not one:
  `GADG7896F1CD757` (closed 2026-08-21, keys `SD014GSBBN`/`SD014GSXE5`) and `GADG92E4DFF6C7E`
  (closed 2026-08-24 11:46, keys `SD5QNQVCGL`/`SD5QNQW0AF`). Identical pattern in both:
  component carries `QtyRequired`/`QtyPicked` with `QtyOrdered` 0, finished good carries
  `QtyOrdered` 1 with `QtyRequired` 0. Not a one-off.
- **Role discriminator**: shipment `QtyRequired > 0` → component, `QtyOrdered > 0` →
  finished_good. Confirmed on both documents for this work order.
- **Fallback (decided with Harry)**: plan quantities first; if ambiguous, `QtyPicked > 0` →
  component and `QtyReceived > 0` → finished_good; still ambiguous → component **and**
  `logger.warn`. Never silent.
- **Field-merge policy**: shipment side wins identity and plan fields; the receipt supplies
  `produced`, `rejected` and `dateProduced`; a receipt-only key is mapped entirely from the
  receipt.
- `ReceiptId == ShipmentId` on this work order, but the filter that actually matched was
  `SupplierRef eq CustomerRef` (the third candidate). UNRESOLVED: whether `ReceiptId` equals
  `ShipmentId` reliably enough to add as a cheap first probe — needs a second observed work order.
- Local `node_modules` has types 7.7.0 while `package.json` declares `^9.2.1` — install in the
  worktree, don't trust the stale tree.
- Prod writes nothing until FUSE-722 flips `useDynamicConfirmationMapping`; dev is the only place
  this is observable end to end.

## Increments

- [x] 1. Join by `Line` key in `joinLines` — verified: "emits one line per line key rather than one per document" asserts 2 lines, fails on the base handler
- [x] 2. `deriveRole` with the agreed chain — verified: 4 tests (required-only, ordered-only, unclassifiable→component, warn-called)
- [x] 3. `consumed = QtyPicked`, `produced`/`rejected` from the matched receipt line — verified: consumed=2, produced=1, rejected=3 on the fixture
- [x] 4. Shipment-wins merge with receipt enrichment; receipt-only keys still surface — verified: "surfaces a receipt-only line as an unplanned by-product"
- [x] 5. Header aggregates recomputed off the joined lines — verified: totalComponents/totalFinishedGoods = [1,1], totalConsumed=2, totalProduced=1
- [x] 6. Dev end-to-end: confirm the SFTP file is QA's expected 2 rows — **awaiting a decision
      on deploying this branch to dev** (see below). The canonical half is already proven against
      unedited Snap payloads; what is unverified is the connector rendering the corrected shape
      to a file.

## Verification

- **2026-10-05 [sign-off] QA re-test, read from Jira FUSE-866 (read-only).** Comments 23339/23340 (Schuster Efigenio, 2026-08-28 16:59 BST): "This new code looks good" and "Test Passed". They show the dev SFTP file for fresh work order `GADG22E3C9CA151` (WO-20260819-00031): 2 rows, `component, TTRS3, SD62HJ6WDD, consumed 2, produced blank` and `finished_good, TTRS4, SD62HJ7NJL, consumed blank, produced 1`. This is QA's expected shape for `GADG7896F1CD757` on a new work order. Only the joined, role-scoped handler can produce it: the old handler wrote 4 rows with `consumed 0`. The image sha behind that run was not recorded, and the Datadog logs for 08-28 are past retention (searched, flex tier included: no hits). PR #204 merged 2026-09-01 as `2205468b`, and the poller in prod is `prod-0f2024c`, which is later. Jira is still In QA.

- **Unit**: 34 tests in the WOC spec, whole app suite 285 passing; typecheck and biome clean.
- **Tests bite**: the 9 new behavioural assertions were run against the base handler
  (`acb85ed`) and **all 9 failed**, then passed against the new one. A green suite alone would
  not have shown the join was doing anything.
- **Fixtures** rebuilt from the live GADG dev documents (mirrored `SD014GSBBN` / `SD014GSXE5`
  keys) rather than the previous invented `1` / `2` shapes.
- **Live payloads**: `work-order-confirmation.live-payload.spec.ts` drives the handler with the
  verbatim Snap responses and asserts the exact rows QA expects —
  `[component, TTRS3, SD014GSBBN, consumed 2, produced absent]` and
  `[finished_good, TTRS4, SD014GSXE5, consumed absent, produced 1]`. Schema-valid.
- Full app suite: 288 passing across 31 files; typecheck and biome clean; tree clean.
- **Config gap found while preparing the QA handoff (2026-08-24)**: no `work_order_confirmation`
  egress mapping exists on **any** GADG dev SFTP connector. Checked Primary SFTP
  (`conn_179b2416…`), ILG Test Account (`conn_94adbd7e…`), AlexP-Test (`conn_b4a450ea…`) and
  Custom CSV (`conn_bc5142d5…`) — all 404, while `finished_good_receipt` returns 200 on Primary
  SFTP, so the path shape is right and the 404 is real. PR #249 recorded adding that mapping to
  Primary SFTP on 2026-08-13 and QA had a WOC file this morning, so it existed and has since
  gone. **Until it's restored, no WOC file can be written in dev regardless of this fix** —
  raised with QA rather than re-created unilaterally, since it's their test connector.
- **Outstanding**: the file itself. Two work-order DESPATCH entries are sitting unprocessed in
  GADG's dev outbound queue (`GAOB001170` / `GAOB001175`, created 11:36 and 11:46 on 2026-08-24),
  so deploying this branch to dev would drain them and write real files. That consumes QA's
  in-flight test data, so it needs a human decision rather than being done unilaterally.

## Decisions & deviations

- 2026-09-02 — **Reconciled after merge; still BLOCKED on increment 6, not marked complete.**
  [PR #204](https://github.com/gfs-bifrost/snap-adapter/pull/204) merged to `master`
  2026-09-01 (`pr:` was still `null` on this plan — the plan wasn't updated at merge time, only
  now caught and backfilled). Jira has since moved to **In QA**. Ticked the 5 acceptance
  criteria the merged diff already satisfies (proven via the pre-fix-fails/post-fix-passes unit
  tests and the live-payload fixture — see Verification). The 6th AC / increment 6 — the actual
  SFTP file matching QA's expected 2-row output — is **not** ticked: per the PR's own notes, no
  live dev end-to-end run has actually happened with this fix yet (the dev environment cycled
  through other deploys after the 08-24 branch deploy), so QA's current re-test is the first
  real check of it. Before trusting that result, confirm the deployed `version` sha matches this
  PR's merge commit — same stale-image trap that hit FUSE-1050. Stays `active` until that's
  confirmed.
- 2026-08-24 — Live payload fixture committed as a `.ts` module rather than JSON: importing
  `.json` type-checks only with `resolveJsonModule`, and changing a shared tsconfig for one test
  fixture is not worth it. Also matches the repo's existing `__fixtures__` convention.

- 2026-08-24 — **Added role-scoped quantities** (`scopeQuantitiesToRole`), not in the original
  increments. QA's expected file has `Consumed` blank on the finished-good row and `Produced`
  blank on the component row; a joined line carrying the opposite side at `0` renders as a real
  `0` in the customer's CSV. So `consumed` is dropped from finished-good lines and
  `produced`/`rejected` from component lines.
- 2026-08-24 — Renamed `componentLineToCanonical`/`finishedGoodLineToCanonical` to
  `shipmentLineToCanonical`/`receiptLineToCanonical` and passed `role` in. Not cosmetic: the
  mappers are per-source-document now, and role is no longer implied by which one ran.
- 2026-08-24 — Existing spec fixtures encoded the wrong model (one document per role) and were
  rebuilt on live data. Expectation changes were the point of the ticket, not test-fitting.
- 2026-08-24 — Plan assumed local types 7.7.0; a clean worktree install resolves **9.3.0**, and
  the line `quantities` shape is unchanged there. No types bump needed, as planned.

- 2026-08-24 — Planned as a snap-adapter change under FUSE-866 (kept on the SFTP ticket, per
  Harry) rather than a new producer-side defect; QA re-verifies where they raised it.
- 2026-08-24 — Role fallback: actuals tiebreak then component + warn, chosen over QA's literal
  "document-of-origin" rule, which no longer disambiguates once lines are joined (an ambiguous
  key sits on both documents).
