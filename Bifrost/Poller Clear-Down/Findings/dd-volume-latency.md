# dd-volume-latency: production empirical baseline (Datadog, prod, 2026-09-15 to 2026-09-29 ~10:00Z)

Scope: how much the "row stays on the SNAP OBQ" safety net is exercised today. All numbers are prod (`@environment:prod` / `environment:prod`), UTC days. 2026-09-29 is a partial day.

## Refs read

- pkg-node origin/main 4d62ab9: `pkg/observability/src/catalog/confirmations.type.ts` (CONFIRMATION_METRIC).
- snap-adapter origin/master 3c1578b (worktree early-consume-feasibility): `apps/snap-queue-polling-service/src/observability/catalog/snap-polling.type.ts`, `src/core/snap/confirmations/confirmations.service.ts` (RETRIEVED at L146, PUBLISHED at L393, CLAIM_DUPLICATE L406, CLAIM_FAIL_OPEN L419, withhold L199/L225), `queue-lane.ts` (dropClaimed L107-150), `src/core/cache/cache.service.ts` L115-150 (claim key), `config.schemas.ts:64` (`REDIS_CONFIRMATION_CLAIM_TTL_MS` default 600000), `apps/snap-adapter/src/http/controllers/event.controller.ts` L~150-215 (`handleConfirmationMade`), `apps/snap-adapter/src/adapters/confirmations/confirmations.service.ts` (PATCH `/v2/snapoutbound/{queueId}/processed`).
- Prod runtime versions seen in logs: poller and snap-adapter `b7ad73c` (in master; 4 commits behind 3c1578b, all Renovate/RGA). Poller `7a6cbb7` deployed 2026-09-23 08:30Z (contains FUSE-1063 #240 stage-1 eligibility filter and #241 skip-already-claimed-before-enrichment, committed 09-21). Poller `8275c2c` ran 09-18 08:47Z to 09-23 08:30Z (1.78M log lines).
- Datadog metrics and logs as listed below. No Pub/Sub or SNAP calls made. One recordId trace read log bodies only.

## Metric catalogue reality check

- Exists in prod (poller `snap-polling-service`, tags `type`, `businessId`, `environment`): `fuse.confirmation.retrieved`, `fuse.confirmation.published`, `snap.confirmation.claim.duplicate`, `snap.confirmation.hanging`, `snap.confirmation.withheld_ineligible_connector`, `snap.confirmation.withheld_unresolved_connector` (tag `reason`), `snap.confirmation.map_skipped`, `snap.poll.skipped_ineligible_business`, `snap.outbound.claimed_entry_skipped` (tag `lane`).
- Exists, snap-adapter: `snap.confirmation_handled` (tag `recordtype`, `connectorid`), `snap.confirmation_handled.failure`.
- Egress side: `fuse.confirmation.made.emitted` and `fuse.confirmation.failure.emitted` exist for fapi (`channel:rest`) only; no per-connector made metric for sftp/shopify. `fuse.confirmation.unroutable` (tags service, reason, type, businessId) is emitted by every egress service for every confirmation it receives but cannot route (a broadcast "not mine" signal, so it does not identify truly orphaned confirmations).
- Does NOT exist / no data in 14d: `snap.confirmation.claim.fail_open` (no series; and no "Confirmation claim unavailable, failing open" log in 14d). There is no metric for OBQ depth, oldest-row age, or per-queueId announce count. The announce log ("Confirmations ready to announce") carries only recordType, count and customers, not queueIds. Only snap-adapter's "Confirmation processed" log carries `record.identifiers.queueId` (from ~09-18).
- Metric caveat: `retrieved` is counted after routing-source resolution and before the claim; `published` after the claim; `retrieved - published` = claim duplicates.
- Query caveat: `get_datadog_metric raw_data:true` trims null buckets on sparse series, so day alignment of sparse series is unreliable; the dense series (good_out, stock_adjustment) and all log-derived tables are aligned.

## (1) Volume per type per day (poller metrics)

Poller rows, prod. `published` includes re-announcements after claim TTL expiry, so it is not a distinct-row count.

| day | good_out retrieved | good_out published | good_out claim dup | stock_adj retrieved | stock_adj published | good_in retr=pub | pick/pack |
|---|---|---|---|---|---|---|---|
| 09-15 | 2104 | 2104 | 0 | 19 | 17 | 3 | none |
| 09-16 | 1702 | 1433 | 269 | 3 | 3 | 4 | none |
| 09-17 | 9768 | 3784 | 5984 | 5 | 2 | 5 | none |
| 09-18 | 41783 | 10230 | 31554 | 2399 | 489 | 6 | announce log: pick 5472, pack 5928 |
| 09-19 | 57600 | 10397 | 47203 | 3600 | 640 | 0 | pick 8640, pack 9360 |
| 09-20 | 60421 | 12901 | 47520 | 3601 | 641 | 0 | pick 8640, pack 9360 |
| 09-21 | 63257 | 14711 | 48546 | 3695 | 723 | 8 | pick 6720, pack 7053 |
| 09-22 | 67788 | 15954 | 51834 | 5540 | 1132 | 10 | pick 5048, pack 5042 |
| 09-23 | 28978 | 10201 | 18777 | 2161 | 477 | 4 | pick 1792, pack 1792 |
| 09-24 | 4840 | 4832 | 8 | 361 | 361 | 9 | none |
| 09-25 | 2655 | 2655 | 0 | 372 | 372 | 4 | none |
| 09-26 | 1574 | 1574 | 0 | 369 | 369 | 0 | none |
| 09-27 | 1996 | 1996 | 0 | 369 | 369 | 1 | none |
| 09-28 | 4532 | 4532 | 0 | 1342 | 1342 | 8 | none |
| 09-29 (partial) | 1106 | 1106 | 0 | 863 | 863 | 1 | none |

- Claim-duplicate totals in 14d: good_out about 251,700; stock_adjustment about 16,900 (all types stop after the 09-23 08:30Z deploy, when drop-already-claimed-before-enrichment made the announce-time claim rarely reached).
- Pick/pack: announced in the storm window 09-18 to 09-23 only (counts from log `count` sum); nothing since 09-24 (GADG connector "gone", then stage-1 filtering). No pick/pack confirmation_made was ever handled in the 14d (0 made events).
- RGA: 7 rows announced 09-18, 8 rows 09-22; 0 made.

Made / cleared at snap-adapter (log `POST /events/v1/confirmation/made/*`, and "Confirmation processed" = PATCH processed succeeded), prod, per day:

| day | sales_order made | purchase_order made | stock_adjustment made | cleared ("processed") |
|---|---|---|---|---|
| 09-15 | 3696 | 3 | 6 | (log not present yet) |
| 09-16 | 1673 | 4 | 1 | (n/a) |
| 09-17 | 2483 | 5 | 0 | (n/a) |
| 09-18 | 2416 | 6 | 0 | 1904 + 6 (from mid-day) |
| 09-19 | 0 | 0 | 0 | 0 |
| 09-20 | 2133 | 0 | 1 | 2133 + 1 |
| 09-21 | 3232 | 8 | 0 | 3232 + 8 |
| 09-22 | 3998 | 10 | 5 | 3998 + 10 + 5 |
| 09-23 | 2643 | 4 | 0 | 2643 + 4 |
| 09-24 | 2213 | 9 | 0 | same |
| 09-25 | 2171 | 4 | 0 | 2170 + 4 |
| 09-26 | 1094 | 0 | 0 | same |
| 09-27 | 1440 | 1 | 0 | same |
| 09-28 | 3823 | 8 | 1 | same |
| 09-29 (partial) | 765 | 1 | 0 | same |

- 14d made by business: PURDYFIGG sales_order 25,218; STUBBLE 3,019; DRSAMS 2,003; SPORTLUX 1,188; EPARFUM 702; CHAMPO 546; BYOMA 396; SAIRA 277; WILDSMITH 227; DRSAMSPL 142; DISCOVERED 43; SHACKLETON 29. PO made: 63 total. Stock adjustment made: PURDYFIGG 7, SAIRA 7 (14d).
- Collector agrees with made: "Confirmation marked processed" per day about equals made (e.g. 09-28 3831, 09-22 4008). "Confirmation stored" is lower than made (09-28: 1066 stored vs 3831 processed; 09-25: 803 vs 2175). Not explained; see open questions.
- Made-per-type coverage 09-25 to 09-28 (poller published vs made): good_in 13 vs 13 (100%); good_out 10,757 vs 8,528 (79%; the remainder is stuck rows re-announced, see section 3); stock_adjustment about 2,450 vs 1 (about 0%).
- Hour-of-day (UTC) made profile over 09-22..09-28: activity 04:00 to 22:59, peak 10:00-16:00 (hour 14: 1,897 events over the 7d); 23:00 to 03:59 essentially zero.
- Poll cadence: one poll every 2 minutes (720 announce log events per day per lane; 15 stage-1 "skipping businesses" logs per 30 min). Peak announce burst since 09-24: 23 good_out rows in one minute.

## (2) Announce to made latency

Method: join poller "Confirmations ready to announce" (min ts per correlationId) to snap-adapter "made" logs on `correlationId`. The correlationId is minted per poll and carried end to end, so this is time from the poll-cycle announce to the made request reaching snap-adapter. It does NOT measure time from first sighting of a row (announce logs lack queueId), and a re-announced row gets a fresh correlationId.

Daily, all types (seconds):

| day | made | matched | p50 | p90 | p99 | max |
|---|---|---|---|---|---|---|
| 09-15 | 3705 | 3705 | 1.3 | 7.3 | 13.9 | 19.8 |
| 09-16 | 1678 | 1678 | 1.9 | 6.4 | 11.6 | 43.7 |
| 09-17 | 2488 | 2487 | 3.9 | 8.6 | 13.1 | 17.8 |
| 09-18 | 2422 | 2422 | 4.6 | 9.7 | 18.4 | 25.5 |
| 09-20 | 2134 | 2134 | 5.1 | 11.4 | 16.9 | 21.6 |
| 09-21 | 3240 | 3240 | 4.8 | 9.1 | 15.0 | 21.3 |
| 09-22 | 4013 | 4013 | 5.9 | 12.6 | 20.7 | 37.8 |
| 09-23 | 2647 | 2647 | 3.9 | 10.1 | 22.0 | 26.4 |
| 09-24 | 2222 | 2222 | 3.9 | 9.3 | 20.3 | 29.8 |
| 09-25 | 2175 | 2175 | 3.9 | 11.8 | 23.3 | 28.0 |
| 09-26 | 1094 | 1094 | 3.8 | 9.1 | 14.2 | 16.8 |
| 09-27 | 1441 | 1441 | 4.5 | 9.9 | 16.0 | 35.9 |
| 09-28 | 3832 | 3832 | 4.8 | 12.8 | 22.0 | 34.5 |
| 09-29 | 776 | 776 | 3.0 | 8.1 | 13.6 | 15.9 |

- Every made event matches an announce correlationId (0 unmatched over 14d except 1 on 09-17), max latency 43.7 s in 14d.
- Per business, last 24h (goods-out): PURDYFIGG (Shopify; 2,998 made) p50 6.2 s, p90 13.9, p99 22.9, max 34.5; SPORTLUX 0.7/1.9/2.6/2.8; STUBBLE 0.7/1.3/2.6/6.7; EPARFUM 0.6/1.2/2.0/2.5; CHAMPO 0.7/1.9/1.9/2.1; WILDSMITH 0.6/1.6/1.8/2.5; SAIRA 1.5/2.6/3.0/3.5. Per-egress (rest/sftp/shopify) split is not derivable: the made log carries connectorId but not connector type; PURDYFIGG is the Shopify connector (messageSource: shopify in log). The slow tail is PURDYFIGG (Shopify API).
- Implication: in the healthy path a made lands 1 to 44 s after announce, far inside the 10 min claim TTL, so the claim never expires before a normal delivery. Anything longer than ~10-12 min is re-announced.
- Because a re-announced row is always matched to its latest announce, this metric hides delivery delay for rows that were re-announced repeatedly (see section 3, 09-19).

## (3) Re-announcement (how often the safety net fires)

There is no per-queueId announce count. Evidence is assembled from four angles.

1. Claim cycle length: a stuck row is re-announced about every 11.7 to 12 minutes (10 min claim TTL plus the 2 min poll). PURDYFIGG stock_adjustment 09-25/26/27: 124/123/123 announce events per day, each exactly 3 rows (369 rows/day). BFA stock_adjustment 09-23: 256 events x 8 rows. So each stuck row is announced about 120 times per day.
2. Before 09-23 08:30Z the poller re-enriched and re-retrieved claimed rows every 2 min poll (`retrieved` plateau 4,800 per 2 h good_out, 300 per 2 h stock_adjustment while `published` was about 880 and 55), and the claim suppressed them (dup metric above).
3. Persistent claimed-but-uncleared rows per poll (log "Skipping already-claimed queue items", 24h to 09-29 10:00Z): PURDYFIGG DESPATCH 720 events, skipped 3 to 7 per poll (min 3, max 7), 3,994 total; PURDYFIGG STOCK_MOVE 620 events, skipped 2 to 16, 9,505 total; CHAMPO few. PURDYFIGG DESPATCH has skipped >= 1 row at every poll since the log first appeared (09-23): daily min 1 to 4, max 4 to 7. Since made lands within ~6 s, rows still claimed 2 minutes later have not been cleared, i.e. they are stuck, not in flight. `snap.outbound.claimed_entry_skipped` (7d, avg per sample): despatch about 281, stock_move about 128.
4. Announced minus made, 09-25 to 09-28, good_out: 10,757 announced vs 8,528 made; the ~2,229 difference (about 557/day) fits 4 to 5 stuck despatch rows re-announced 120 times/day.

Current stuck sets (last 7 days):
- PURDYFIGG stock_adjustment: 3 rows from 09-24 to 09-27 (369 announced/day), 16 rows from 09-28 (864 announced in the first 10 h of 09-29). Made count for PURDYFIGG stock_adjustment: 7 in 14 days.
- BFA stock_adjustment: 8 to 9 rows, announced every poll until the 09-23 deploy (5,190 rows announced on 09-22, 2,048 on 09-23); no made.
- PURDYFIGG DESPATCH: 1 to 7 rows persistently claimed each poll.
- SISTACO good_out: about 46 stuck rows (manual-origin broadcast metric 6,630 to 7,029/day on 09-19..09-22 = 46 x 144 cycles/day). DRSAMS (about 600/day on 09-20..22), LISAPL (about 410/day), LISAUK (about 280 to 610/day) similarly.
- GADG pick/pack/good_out/good_in: withheld each poll (see section 4).

> SUPERSEDED 2026-10-02 — the SPORTLUX re-presentation below was an operator re-push of 09-11→09-18 confirmations, not SNAP reopening rows; see [[Poller Clear-Down/Findings/g3-sportlux-represent|G3 findings]].

Re-delivery after a clear (queueId level, snap-adapter "Confirmation processed" with `record.identifiers.queueId`, 09-18 to 09-29): 25,188 queue rows cleared once; 143 cleared twice; 3 cleared three times, all SPORTLUX. Two episodes: (a) 33 rows first cleared 09-18, cleared again about 3.99 days later (span p50 344,681 s) on 09-22; (b) 113 rows cleared 2 to 3 times within 10 to 22 minutes on 09-22 around 14:16 to 14:38Z. Trace of one: queueId SPLU003840 (recordId S-SO-024206, connector conn_bad08...) made+processed at 14:16:14, 14:26:21, 14:38:09 (PATCH processed logged success each time), three distinct correlationIds. So SNAP re-presented the row after a logged-successful clear, it was re-announced after claim expiry, delivered and made again. Cause unknown from logs.

Multi-made records overall (14d, made events per recordId): 29,472 once, 2,136 twice, 22 three times, 5 records 5 to 14 times. This is NOT a clean duplicate signal: PURDYFIGG has 1,890 multi-made records with median span 3.4 s (one order with several queue rows/despatches). The clean duplicate evidence is the queueId table above.

## (4) Backlog, withheld and deferred (no OBQ-depth metric exists)

- Withheld (rows left on OBQ, `Withholding confirmation` warn plus metric), GADG connector reason `gone`: pack_confirmation about 780 per sample, pick about 720, good_out about 300, good_in about 60, RGA 2 to 6, each sample every poll interval; series 09-17 21:12Z to 09-22/23 (ends when 7a6cbb7 deployed, which stops polling ineligible businesses). Totals over 14d: pack 38,509, pick 36,285, good_out 15,229, good_in 2,228 (sums of per-poll counts, so they count the same rows many times). BFA good_in withheld ineligible: 12,038 (per-poll sums), 09-17 to 09-22.
- Stage-1 skip (`snap.poll.skipped_ineligible_business`, since 09-23 08:32Z): 21 businesses are not polled at all every cycle: eadem, nuzest, sammck, babymori, kappahl, escentric, dockbay, jolovespl, discovered, shackleton, gadg, escentricpl, phlur, lisapl, bfa, drsams, academic, sistaco, aymstudio, lisauk, drsamspl. Their OBQ depth and age are unknown (no metric); they are the "disabled connector = deferred" population. Businesses currently polled: PURDYFIGG, SPORTLUX, STUBBLE, EPARFUM, WILDSMITH, CHAMPO, SAIRA, BYOMA (from the 24h announce log).
- Hanging (`snap.confirmation.hanging`): 4 in 14d (3 samples). map_skipped: 2,296 (09-15/09-16 only, "Unable to map confirmation" errors, later stopped).
- OBQ fetch failures: "Outbound queue fetch failed" 17,192 errors 09-18 to 09-24 13:12Z, cause HTTP 401 (example: ESCENTRICPL STOCK_MOVE); ESCENTRICPL 2,160/day 09-19 to 09-22; LISAPL/LISAUK 1,191 to 1,265/day 09-23/24; others 09-18. Those queues cannot be read (poll.failure only). 09-16 09:04Z to 09-17 08:44Z: "unable to make request to SNAP" 774 plus "Error fetching from outbound queue" 768.

## (5) Clear-down failures

- snap-adapter `snap.confirmation_handled.failure`: 2 in 14 days. Logs: 2026-09-16 14:00:19Z (PURDYFIGG #6369469, queueId SPLU016608, `failed to clear confirmation down`, socket hang up ECONNRESET, PATCH `/v2/snapoutbound/SPLU016608/processed`, version 556af83) and 2026-09-25 14:36:26Z (PURDYFIGG #6423783, queueId SPLU031080, `Confirmation clear-down failed`, socket hang up, version 1135a83). Neither record has a second made/processed event afterwards in the 14d window (checked snap_adapter logs by recordId), so I cannot tell whether the row was cleared by another route, re-announced with a delivery skipped downstream, or is still on the OBQ.
- Code (snap-adapter master 3c1578b): `handleConfirmationMade` returns 202 first (`event.controller.ts` L~150), then clears; on clear failure it logs, increments the failure metric and publishes a `confirmation_data_failure` (`emitConfirmationFailure`). A failed clear is therefore never retried by Pub/Sub; it relies on the row staying on the OBQ, and on the failure record.
- "SNAP request failed" errors (24 on 09-22 to 09-28) and the 09-22 18:08 to 18:19 retry-exhausted burst are separate SNAP request failures, not tied to clear-down here.
- confirmation_data_failure at large: replay-service `POST /event/confirmation-failure` per day: 35, 108, 50 (09-15..17), then 4,359 / 6,630 / 7,623 / 8,499 / 3,636 (09-18..09-22), then 35, 120, 39, 0, 1, 112, 81 (09-23..09-29). The 09-18..09-22 storm (30,747 posts) is repeated manual-origin failures for the same stuck rows re-announced every 10 min (SISTACO alone 6,630/day). Collector "Confirmation marked failed": 35 (09-23), 114, 37, 0, 1, 109, 78 (09-29). Failures are recorded (collector and replay), but a stuck row produced a fresh failure every 10 minutes for days.

## (6) Claim service

- Duplicate suppression (`claim.duplicate`): about 251.7k good_out and about 16.9k stock_adjustment in 14d, effectively all before 09-23 08:30Z (last 8 on 09-24). Log "Confirmation claim skipped duplicates": 18,256 events, 09-15 to 09-24 12:18Z. After the deploy the drop-before-enrichment path (`claimed_entry_skipped`) took over: 10,370 "Skipping already-claimed queue items" logs 09-23 to 09-29.
- Fail-open: zero in 14d (no metric series, no log).
- Claim TTL default 600,000 ms (10 min). The observed ~11.7 to 12 min re-announce cycle is consistent with that default; the prod env override was not read.

## (7) Cadence

Poll every 2 minutes per lane (DESPATCH, STOCK_MOVE, receipts, etc.); about 30 polls per hour per lane; ~720/day. Made traffic runs 04:00 to 23:00 UTC.

## The made-path outage of 09-18 22:00Z to 09-20 07:00Z (a real safety-net event)

- Zero made events reached snap-adapter from about 2026-09-18 22:00Z to 2026-09-20 07:00Z (hourly count of `POST /events/v1/confirmation/made` is 0), and again from 2026-09-20 ~14:00Z to 2026-09-21 ~04:00Z (single-digit). snap-adapter was alive throughout (hundreds to thousands of other logs per hour, entity creation errors).
- Poller kept announcing every poll (270 announce events per hour, flat), `retrieved` plateaued at 4,800 per 2 h good_out (about 80 rows/poll), published about 880 per 2 h (the same rows re-announced each 10 min), 41k to 67k good_out retrievals/day.
- When made resumed (09-20 07:00Z onward: 112, 287, 353, 438 per hour), all backlog rows were made and cleared, each with a fresh correlationId and 1 to 22 s latency after its latest announce. So the row-on-OBQ net absorbed a ~33 h downstream/return-path stall without loss. The stall's root cause is not established (shopify-connector was up, skipping non-routable businesses; no snap-adapter errors on the made path). Sales-order made per day was 2,133 to 4,000 after, i.e. the backlog drained within the day.
- Under early consume none of those rows would remain on the OBQ; whether they were lost would depend entirely on downstream durability during such a stall.

## Queries used (exact)

Metrics (`get_datadog_metric`): `sum:fuse.confirmation.retrieved{environment:prod} by {type}.as_count().rollup(sum, 86400)`; same for `fuse.confirmation.published`, `snap.confirmation.claim.duplicate`, `snap.confirmation_handled{environment:prod} by {recordtype}`, `snap.confirmation_handled.failure`, `fuse.confirmation.made.emitted`, `fuse.confirmation.failure.emitted`, `fuse.confirmation.unroutable{environment:prod} by {reason}`, `snap.confirmation.withheld_ineligible_connector`, `snap.confirmation.withheld_unresolved_connector`, `snap.confirmation.map_skipped`, `snap.confirmation.hanging`, `snap.confirmation.claim.fail_open{*}` (no data), `snap.poll.skipped_ineligible_business by {businessid}`, `snap.outbound.claimed_entry_skipped by {lane}`, `fuse.confirmation.manual_origin_broadcast by {type,businessid}`.

Logs (`analyze_datadog_logs`, DDSQL): announce volumes `filter: service:snap-polling-service @environment:prod "Confirmations ready to announce"` with `@recordType`, `@customers`, `@count` extra columns; claimed skips `"Skipping already-claimed queue items"` with `@businessId`, `@transactionType`, `@skippedCount`; made `service:snap_adapter @environment:prod "POST /events/v1/confirmation/made"`; cleared `"Confirmation processed"` grouped by `@record.identifiers.queueId`; latency: CTE over `(service:snap-polling-service ... "Confirmations ready to announce") OR (service:snap_adapter ... "POST /events/v1/confirmation/made")` joining `ann` (MIN(ts) by `@correlationId` where svc = snap-polling-service) to `mad` on correlationId, `APPROX_PERCENTILE`; replay `service:replay_service "POST /event/confirmation-failure"`; collector `service:collector_service ("Confirmation marked" OR "Confirmation stored")`; version timelines by `version` for poller, shopify-connector.

## Open questions

1. Why did no made event reach snap-adapter 09-18 22:00Z to 09-20 07:00Z? Egress stalled or return path down? (shopify/fapi/sftp internals not read.)
2. After the two failed clear-downs (SPLU016608, SPLU031080), is the row still on PURDYFIGG's OBQ? (Would need a read-only SNAP OBQ lookup; not done: needs prod credentials.)
> SUPERSEDED 2026-10-02 — answered: a manual re-push (see [[Poller Clear-Down/Findings/g3-sportlux-represent|G3 findings]]).
3. What is SNAP doing on 2026-09-22 ~14:00Z for SPORTLUX (146 rows re-presented after successful PATCH processed, 3x within 22 min)? Re-queue, replay, or PATCH not persisted?
4. Which PURDYFIGG despatch rows (1 to 7) are permanently claimed, and why is no made emitted for them (Shopify kit-component filter, unfulfillable orders)? And do the 16 PURDYFIGG STOCK_MOVE rows correspond to a connector with stock_adjustment egress deliberately off (sftp `use_case_inactive`)?
5. Made (3,696) exceeds poller published (2,104) on 09-15 and 09-16 (1,673 vs 1,433). Other sources of confirmation_ready or made (replay redrive)? Not explained.
6. Collector "Confirmation stored" is materially lower than "marked processed" (e.g. 09-28 1,066 vs 3,831). Does the collector persist every announced confirmation, or a subset? Matters if collector is meant to be the durable record of terminal outcomes.
7. Actual prod `REDIS_CONFIRMATION_CLAIM_TTL_MS` (default 10 min inferred from cadence).
8. Is there any alert on the stuck sets (stock_adjustment re-announce loop, GADG withheld) today? None found in the metrics catalogue reviewed.
