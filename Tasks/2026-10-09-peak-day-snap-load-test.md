---
tags: [adhoc-task]
date: 2026-10-09
tldr: "Peak-day (31,145 orders) soak/step/peak-window/burst tests on the real SNAP test tenant (GADG, instance 001): adapter ceiling ~0.60 orders/s (1.7x avg, 0.5x busiest hour); even spread held 4h; 0.66/s broke at 40 min; peak-window replay lost 12%; 500-order burst lost 14%, 1,000 lost ~75%. Report artifact published; follow-ups owed."
session_id: 46029d3e-e1cf-437b-acd9-d2b0212fd8c2
status: open
---
# Peak-day load and soak tests against SNAP

## Outcome
Ran the Purdy and Figg projected peak day (31,145 orders, 37,374 SKUs; Ryan's projection, attachment not readable by the agent) through Fuse and SNAP. Simulator stages clean; the real SNAP test tenant saturated at about twice the peak-day average rate, so the bursts were not run. Owed: Harry's go-ahead for the profile-shaped test, redrive of 11 held orders, and a decision on whether SNAP (via Ryan) has agreed to load on their test host.

## What was run (all 2026-10-09, UTC)
| Stage | Target | Load | Result |
|---|---|---|---|
| Smoke | HJF (simulator) | 20 orders @2/s | 20/20, no errors |
| Soak 1 | HJF (simulator) | 1,200 orders @2/s, 10 min | 0 failed, no error logs |
| Burst 2 | HJF (simulator) | 3,000 @25/s | all accepted, 0 errors; acks ~15/s, caught up |
| Burst 3 | HJF (simulator) | 5,000 @50/s | all accepted, 0 errors; acks plateau ~13/s, backlog built then drained (~7 min) |
| Smoke | GADG (real SNAP test, ilg001testapi) | 20 @2/s | 20/20 stored; 4/4 sampled present in SNAP |
| Soak | GADG | 2/s, cancelled after 870 orders (7 min) | 0 failed at mocker; SNAP saturated, see below |

HJF's backend is the fuse-mocker snap-api simulator, so those stages test Fuse's pipeline, not SNAP. Only the GADG stages touched real SNAP. #bifrost-general thread (announcement + updates 1-4) carries the running commentary; the announcement's original "no load on real SNAP hosts" line was corrected in Update 1.

## Real SNAP result (GADG soak, adapter metrics)
- Request p95 ~1.2s -> 10-26s within 3 min of starting; stayed 9-28s after load stopped until the queue emptied.
- Throughput through the adapter fell to ~0.2-0.3 requests/s (5 concurrency slots x 10-20s per request). `snap.slot_queue_depth` pinned at 24.
- No 4xx/5xx and no `snap.request.failure` counts: slowness, not errors.
- Direct read-only probes (5 sequential GETs, trivial lookup) took 8-28s each while the adapter still had in-flight calls. Baseline-vs-our-load not separated; a clean idle baseline is still to do.
- Recovery: queue empty by 12:09, p95 ~1.1-1.3s by 12:13 (~10 min after cancel).
- 11/870 orders (1.3%) hit "Timed out after 30000ms waiting for a concurrency slot", exhausted retries and landed in the replay failure inbox (not lost; redrivable). correlationId prefix `mock-pf-snap-soak1-1009`.
- Caveat on attribution: p95 also spiked to ~17s at 11:02-11:08 UTC before any GADG load from this session, so the test tenant is intermittently slow without us. GADG is Snap instance 001; Purdy and Figg runs on instance 005 (ilg005liveapi), a different database. Do not read this as 005's capacity.

## Prod anchor (7 days to 2026-10-09, environment:prod)
- snap-adapter: 49,190 successful requests (~0.08/s), 39 failures, avg p95 0.85s, max p95 105s, slot queue max 27.
- PURDYFIGG inbound records (`fuse.dedupe.event.fresh`): sales_order 5,409, purchase_order 19, master_data 3. Daily: 551-960 orders (mean 746).
- Hour-of-day shape (UTC): top 4 hours (10:00-14:00) = 43.5% of the day; busiest single hour = 20-32% of the day. Skio subscription orders arrive as a once-daily batch and Shopify bulk ingest delivers a tick at once, so instantaneous rate is higher than any hourly average.
- Scaled to 31,145/day (x41.8 vs mean day): peak-hour mean ~4,360 orders (1.2/s); worst observed hour share -> ~9,900 orders/h (2.75/s); a bulk tick of that size over ~5 min is ~33/s.
- Live config (prod): Main SFTP (master_data, sales_order, purchase_order; confirmations off), REST API connector (confirmations on, webhook egress), Shopify Live (sales_order + goods_out_confirmation); stock adjustments off everywhere.

## Risks
1. **SNAP saturates under modest load.** The adapter's 5-slot semaphore and 30s slot-wait mean that when SNAP latency is 10-20s, throughput collapses to ~0.3 req/s; orders then exhaust retries into the failure inbox. A peak hour needs several req/s.
2. **Peak is a burst, not a flat rate.** The flat 1.1/s model understates it. Skio batch + bulk ingest can deliver thousands at once, so queue depth and slot-wait timeouts, not average rate, decide failures.
3. **Shared host blast radius.** Instance 005 carries other businesses; a slow host starves the adapter's global slots. Cross-business head-of-line blocking is plausible from the design (global semaphore) but NOT demonstrated: the HJF drain had already finished before GADG load slowed things.
4. **Retry budget vs SNAP slowness.** Slot-timeouts are classed transient (503, Pub/Sub backoff) but exhaust after ~10 attempts (~16-23 min observed), turning a slow period into manual redrives.
5. **Vendor consent.** Ryan sent the projection to Snap; load on their hosted test tenant has not been confirmed with them.
6. Hygiene: `get-business-config` returns live credentials into the agent session; GADG failure inbox already holds ~407k mostly confirmation-webhook failures (two broken GADG connectors), unrelated to this test.

## Profile replay (simulator) - stopped early at Harry's call
Started a time-compressed P&F day on HJF (24h -> ~53 min, 31,145 orders in 9 rate-matched segments + a 5,000 bulk burst). Ran S1 (2,492 @4/s, complete) and S2 (2,856 of 4,765 @8/s, cancelled 12:40 UTC): 5,348 orders, 0 failed. Stopped because Fuse is not the open question, SNAP is; the peak segments (S3-S6, up to 29/s) would only have re-measured the adapter ceiling (~13/s). Segment plan: S3 08-09h 4,360 @15/s, S4 10h 3,395 @23/s, S5 11h 4,360 @29/s, S6 12-13h 5,793 @19/s, S7 14h 2,118 @14/s, S8 15-18h 2,772 @5/s, S9 19-23h 1,121 @2/s, S10 5,000 @50/s.

## Next (not started)
Scale the P&F profile down to what the GADG test tenant can absorb and ramp up from there to find the sustainable rate, after an idle-baseline latency probe and with Snap's agreement (via Ryan). Redrive the 11 held soak orders if wanted. Consider raising the adapter's 30s slot-wait / retry budget question with the owners: slow SNAP currently converts to failure-inbox entries after ~16-23 min.

## Artifacts
- k6 script (simulator-targeted, soak/burst/breakpoint profiles; not yet run): scratchpad `snap-sim-load.js`
- Profile derivation: scratchpad `pf_profile.py`, `pf_profile.json`

## Run 2: real SNAP test tenant (GADG), same day, evening UTC
Harry's correction: HJF is the simulator, so everything above only exercised Fuse. Re-ran against GADG (ilg001testapi) with an independent read-only probe every 10 s, schedules for sub-1/s rates, 1.2 lines/order via a 4:1 one-line:two-line mix, and a 10-SKU pool. Phases A (idle), B1 (0.33/s 4h), B2 (0.66/s), C (0.40/0.47/0.53/0.60 steps), D (peak window 0.73/0.93/1.2/0.8), E1/E2 (500/1,000 bursts). Phase-by-phase BLUFs are in the #bifrost-general thread (opened 1791550505.610339; the earlier simulator-run thread was deleted by Harry).
Key results: ceiling ~0.60 orders/s; B1 4,802 orders 0.08% failed; B2 queue stopped draining at 17:55Z; D 3,267 orders 397 failed (12%), queue 852, oldest 41 min; E1 70/500 failed; E2 ~750/1,000 failed; recovery 9-21 min after load stops. Bursts 2,500+ and a full 24h day not run (extrapolated).
Report: https://claude.ai/artifact/23uqLRV2r3t7PTgq9acrbY (private). Raw log: scratchpad results.md, probe.csv.
Owed: (1) redrive or clear ~1,240 failed mock orders in GADG's retry queue; (2) Snap's agreement to test load on their hosted tenant was never confirmed in-session; (3) repeat on ilg005testapi (P&F's own database) with Snap's OK; (4) raise adapter slot-wait/retry-budget, bulk-tick smoothing and queue-age alerting with owners; (5) `get-business-config` printed live prod credentials into the session, treat as exposed.
