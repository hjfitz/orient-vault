---
title: G6 audit and D1 readiness, re-run for the businesses outside the allow-list
date: 2026-10-12
gate: G6
verdict: PURDYFIGG passes and is ready to add now that FUSE-1118 is in prod; MANUCURIST and newly-polled INDU are unknown (busy in SNAP, but Fuse has never seen an OBQ row); KAPPAHL, BABYMORI, SAMMCK and PHLUR are not live; no previously failing business is polled
supersedes_for: the non-allow-listed rows of [[g6-d1-readiness]]
---
# G6 audit and D1 readiness, re-run (2026-10-12)

**Verdict.**
- **Scope:** the businesses the poller polls in prod that are *not* on `CLEAR_AFTER_PUBLISH_BUSINESS_IDS` (BYOMA, WILDSMITH, EPARFUM, SPORTLUX, DOCKBAY, SAIRA, STUBBLE). Removing the allow-list would newly enable these seven: **PURDYFIGG, MANUCURIST, INDU, KAPPAHL, BABYMORI, SAMMCK, PHLUR**.
- **New since 10-02: INDU.** It has a SNAP backend on ilg002 and a confirmations-enabled SFTP connector (goods-out), so it is polled now. It is busy in SNAP: 184 despatched shipments in 7 days.
- **Pass (1): PURDYFIGG.** It is cleaner than on 10-02. 0 unexplained XDoc gaps, 0 clear-down failures, and 14 rows open for more than 1 h (down from 52). Of those 14, 11 are stock moves (C2 never clears them) and 3 are despatches stuck in a Shopify "fulfillment order CLOSED" loop.
- **Unknown (2): MANUCURIST and INDU.** Both ship daily (867 and 184 despatches in 7 days), but the poller retrieved **0 rows** for either. It polls them every 2 minutes, in the same batch as DOCKBAY, which does get rows. Their OBQs are empty. Either SNAP queues no rows to Fuse's Host, or another consumer processes every row within seconds.
- **Not live (4): KAPPAHL, BABYMORI, SAMMCK, PHLUR.** Each has only SNAP's `DUMMY`/`AUTO` placeholder shipment, 0 open rows and 0 rows retrieved.
- **Previously failing or unreadable: none is polled.** CHAMPO, LISAUK, LISAPL, DRSAMS and DRSAMSPL are all still on the poller's skip list (`snap.poll.skipped_ineligible_business`, prod), with every connector `confirmationsEnabled: false`.

**Recommendation:**
- **Add PURDYFIGG now.**
- **Hold MANUCURIST and INDU** until someone who owns their SNAP interface says whether a second consumer reads their Host. Adding them changes nothing today, because Fuse sees no rows to clear.
- **Hold the four not-live businesses** and re-run G6 at go-live.

## Verdict table

Clears are Fuse's clears in the 7 days to 2026-10-12 ~14:10Z: snap-adapter `Confirmation processed` (distinct `@record.identifiers.queueId`) plus poller `Record dropped`. "Open" is the OBQ census at 14:10Z (15:10 BST), with the count older than 1 h in brackets. "Retrieved" is the poller's `Confirmations ready to announce` record count over 7 days.

| Business | G6 | Confirmations-enabled channel(s) | 7d Fuse clears | 7d retrieved | Open (>1h) | R3 backlog on enablement | D1 notes |
|---|---|---|---|---|---|---|---|
| **PURDYFIGG** | ✅ pass | Shopify (sales_order, goods-out) + REST API (no use cases; takes routed goods-in) | 10,096 (10,085 Shopify goods-out, 11 REST) + 1 poller drop | 8,953 goods-out, 10 goods-in, 20,814 stock-adjustment | 17 (14) | **3 despatches** (already looping into replay); 11 stock moves skip and never land | 0 unexplained gaps. 0 clear-down failures (49 on 10-02). See risks below. **Add now.** |
| **MANUCURIST** | ❓ unknown | SFTP (sales_order, purchase_order, goods-out) | 0 | 0 | 0 (0) | 0 | 867 despatched shipments in 7 days. A Fuse-created PO (`WHSL13377`, receipt `MANUCF85CE40FD7`) reached stage 90 with no row ever seen. Hold. |
| **INDU** 🆕 | ❓ unknown | SFTP (goods-out) | 0 | 0 | 0 (0) | 0 | Newly polled. On ilg002. 184 despatches in 7 days, orders carry `shpfy#` refs, and Fuse created no orders for it. Hold. |
| **KAPPAHL** | n/a (not live) | SFTP | 0 | 0 | 0 (0) | 0 | Only the `AUTO`/`DUMMY` placeholder. Re-audit at go-live. |
| **BABYMORI** | n/a (not live) | SFTP (no confirmation use case mapped) | 0 | 0 | 0 (0) | 0 | The same. |
| **SAMMCK** | n/a (not live) | SFTP | 0 | 0 | 0 (0) | 0 | The same. |
| **PHLUR** | n/a (not live) | REST API (no use cases) | 0 | 0 | 0 (0) | 0 | Only the placeholder. The 46 goods-in published 09-18→10-02 have not recurred. Fuse's only SNAP activity was 77 master-data creates on 09-30. |

**Not polled, not assessed:** CHAMPO, LISAUK, LISAPL, DRSAMS, DRSAMSPL, GADG, ESCENTRIC, ESCENTRICPL, BFA, ACADEMIC, SISTACO, AYMSTUDIO, EADEM, NUZEST, JOLOVESPL, DISCOVERED, SHACKLETON (17). Removing the allow-list doesn't touch them: they become D1-relevant only when a connector's confirmations are switched on, and each needs this audit first. The 10-02 verdicts stand: CHAMPO and LISAUK fail (verified), LISAPL fails (inferred), DRSAMS and DRSAMSPL are unknown.

## PURDYFIGG detail

**XDoc gaps.** The window covers `SPLU050682–060783` (10,102 numbers), and Fuse cleared 10,096 distinct rows. Six numbers have no snap-adapter clear:
- `SPLU055779` and `SPLU056622`: open DESPATCH rows, the CLOSED loop.
- `SPLU057130` and `SPLU057131`: open STOCK_MOVE rows.
- `SPLU060134`: an open STOCK_MOVE row.
- `SPLU059475`: read by id, DESPATCH `PURD1AB2791C0FE`, processed 62 s after creation. It looked like a foreign consumer, but the **poller dropped it**: `Record dropped`, "Goods-out failed: stored lines have no ordered line in SNAP" at 13:04:05Z on 10-11.

No row was processed by anyone other than Fuse.

**Open rows at 14:10Z (17):**
- **11 STOCK_MOVE rows,** created 09-29 → 10-12, all claimed every cycle.
  - C2 skips `stock_adjustment` (SAIRA confirms it: 378 skips, 0 clears).
  - So these stay on SNAP and keep re-announcing exactly as today, with REST "Confirmation could not be delivered" for `stock_adjustment` (886 in 7 days).
  - D1 neither helps nor hurts them, and they never land in replay through C2.
- **3 DESPATCH rows stuck for more than 1 h:**

  | XDoc | Shipment | Customer ref |
  |---|---|---|
  | `SPLU043101` | `PURDAEC5563AC3B` | `#6458532`, from 10-01 |
  | `SPLU055779` | `PURD361C8F99AF3` | `#6509075` |
  | `SPLU056622` | `PURD112EE1D07B5` | `#6509919` |

  - **Replay shows why:** every ~12 minutes each gets "Fulfillment order … is CLOSED in Shopify, so it cannot be fulfilled". There are 2,852 such PURDYFIGG replay failures since 10-01, nearly all from this loop.
  - **On enablement,** the next publish after a claim expires is cleared off SNAP. The loop stops, and replay keeps the failures. Support should know these 3 orders then have no automatic retry. That is the intended terminal outcome.
- **3 DESPATCH rows created in the last 5 minutes:** normal traffic.

**Risks before enabling:**
- **FUSE-1118 is in prod.**
  - shopify-connector#329 merged at 13:20Z. The `Deploy shopify-connector` run applied prod at 14:11:57Z, image pushed at 14:10:33Z.
  - Without it, a goods-out with a line that has no Shopify reference fails as a whole. Under C2 that confirmation is cleared and lands in replay undelivered, instead of looping until a fix.
  - The "Line item has no fulfillment ID" class last hit PURDYFIGG on 10-02 (148 replay rows in total).
  - **Wait for the first post-deploy hour of PURDYFIGG goods-out to be clean before adding it.**
- **Multiple fulfillment orders.** shopify-connector warned 5,592 times in 7 days: "Order has more than one fulfillment order — only the first is mapped by the template".
  - This is existing behaviour and C2 doesn't change it.
  - Any delivery failure it causes becomes a replay record rather than a re-announce once the row is cleared.
- **Volume.** About 1,440 goods-out a day, on ilg005. The C2 clear is a second PATCH alongside snap-adapter's, so it adds about 1,440 SNAP writes a day.
  - snap-adapter had **0** clear-down failures fleet-wide in 7 days, against 49 on PURDYFIGG for the 10-02 week.
  - STUBBLE, also on ilg005, has been on C2 since 10-09 with 0 `clear_failed`.

## MANUCURIST and INDU: why "unknown" and not "pass"

- **The poller's view.** It polls them every 2 minutes; the batch `MANUCURIST,PHLUR,DOCKBAY,INDU` is polled 60 times in 2 h. DOCKBAY, in the same batch, yielded 1,557 records in 7 days. MANUCURIST and INDU yielded **0**.
- **SNAP's view.** SNAP shows 867 and 184 stage-90 shipments over the same 7 days. Neither business's OBQ had an open row at 14:10Z.
- **No poller metric fired for them:** `withheld_ineligible_connector`, `withheld_unresolved_connector` and `cross_tenant_entry_skipped` are all empty in prod.
- **A slow foreign consumer like LISAUK's is ruled out.** LISAUK's consumer took 7–265 s per row, and against a 2-minute poll it would lose hundreds of rows to Fuse over 1,051 despatches.
- **Two explanations remain:**
  - SNAP doesn't queue these businesses' transactions to the Host the Fuse API user reads. This is the most likely.
  - An event-driven consumer processes every row within seconds.
- **The question that settles it** goes to whoever owns MANUCURIST's and INDU's SNAP interface: which Hosts are configured for DESPATCH/RECEIPT outbound, and is anything else reading them?
- **Allow-listing them is a no-op today:** the poller never publishes a row for them, so there is nothing to clear. They are held so they don't silently start clearing the day rows appear without this question answered.

## Clear skip reasons: `snap.outbound.clear_skipped{reason}`, prod, 7 days

The metric is emitted **only for allow-listed businesses** (the `OutboundQueueClearer` returns before metering for anyone else). So these counts cover the seven listed businesses, not "all polled businesses".

| Reason | Count | Breakdown |
|---|---|---|
| `stock_adjustment` | 378 | SAIRA 378 |
| `broadcast` | 6 | WILDSMITH 4 goods-in, EPARFUM 1 goods-in, BYOMA 1 goods-out |
| `unrouted` | 0 | |
| `no_subscription` | 0 | |
| `no_queue_id` | 0 | |

- **`snap.outbound.cleared`, same window:** DOCKBAY 1,002, STUBBLE 533, EPARFUM 431, WILDSMITH 154, SPORTLUX 149, SAIRA 68, BYOMA 21.
- **`snap.outbound.clear_failed`:** 0.
- **Only the 6 broadcast rows still depend on snap-adapter's `confirmation_made` clear-down** (D2's blocker). Stock adjustments depend on the legacy `stock_adjustment_made` path, which D2 keeps.
- **For PURDYFIGG, inferred because it is not metered:**
  - The snap-adapter clears carry `messageSource` `shopify` (10,085) and `rest` (11), all routed.
  - So the expected skips on enablement are its stock adjustments only: about 3,000 records a day re-announced as `stock_adjustment`, an unchanged loop.
  - Broadcast and unrouted counts for it are not measurable until it is listed.

## Method deltas from 10-02
- **Roster:** read live from config-service, prod. There are now **31 businesses** (INDU is new) and 14 are polled. The 17-business skip list is confirmed by `snap.poll.skipped_ineligible_business` split by `environment:prod`. The `env` tag is `serverless` for both environments, so group by `environment`.
- **Poll cadence is now about 2 minutes,** not the 10 minutes stated on 10-02. This strengthens the zero-retrieval inference for MANUCURIST and INDU.
- **Gap analysis** bucketed distinct queueIds by `floor(n/100)` in DDSQL and drilled into buckets under 100, instead of sampling.
- **SNAP reads** were all direct HTTPS GETs with each business's own credentials (no snap MCP), 26 calls in total:
  - 7 OBQ censuses.
  - 1 OBQ read by id.
  - 6 newest-3-shipments.
  - 3 shipments by id.
  - 2 processed-row probes.
  - 2 shipped-in-7-days listings.
  - 2 Fuse-created MANUCURIST order/PO lookups.
  - 3 failed or empty queries: one rejected OData filter, and the processed-row probe returns nothing because the OBQ API lists open rows only.
- **No writes of any kind.**

## Caveats and what could not be verified
- **MANUCURIST and INDU G6:** not established. The explanation is inferred from zero retrieval and was not observed.
- **Skip reasons for non-listed businesses** can't be measured; the metric only fires for listed ones.
- **FUSE-1118 effect in prod:** deployed at 14:11:57Z. No post-deploy PURDYFIGG goods-out was checked for the fix's behaviour.
- **The 3 CLOSED-loop orders:** the audit didn't establish why Shopify closed them (cancelled, or fulfilled elsewhere). That is a support question, not a G6 one.
- **Not live** (KAPPAHL, BABYMORI, SAMMCK, PHLUR) and the 17 skip-list businesses: G6 must be re-run before or at go-live.
- **Datadog flex tier** reaches back about 15 days. All windows here are 7 days apart from the 14-day `Entity created in SNAP` check.
