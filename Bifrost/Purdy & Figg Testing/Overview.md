---
title: Purdy & Figg — Testing (Overview)
status: active
owner: Harry Fitzgerald
created: '2026-08-25'
updated: '2026-08-25'
tags: [bifrost, purdy-and-figg, shopify, testing, onboarding]
---

# Purdy & Figg — Testing (Overview)

**Business ID: `PURDYFIGG`.** ILG's biggest customer onboarded this year — onboarding ticket [FUSE-963](https://globalfreight.atlassian.net/browse/FUSE-963), owned by [[Jack Bailey]] (Product). Went live/onboarded under real time pressure alongside Saira Skin the week of 2026-08-18. Product/PM tracking (SOW, go-live ledger, relationship threads) stays on [[Jack Bailey]]'s page and FUSE-963 — this page is the **testing** thread only: what's been exercised, what broke, what's still unverified.

**Went live 2026-09-01.** This page stays the pre-go-live testing record. Post-go-live production config, incidents, and captured live state now live at [[Customers/PURDYFIGG/overview|Customers/PURDYFIGG]].

Pulled together 2026-08-25 while writing up the adjacent [[Explainers/2026-08-25-gadg-bulk-ingest-soak-test-findings|GADG bulk-ingest soak test]] — that test runs against Gadgets, a different customer account, but exercises the same Shopify bulk-ingest lane Purdy & Figg's volumes need. Everything below predates that test and was scattered across meeting notes and digests; consolidating it here rather than re-deriving it next time it's needed.

## Testing threads

- **Shopify dev-app access.** James Godsell (ILG) raised a Shopify dev-app review blocker for P&F testing (2026-07-14) — without it P&F couldn't install the dev app to test against. Closed 2026-07-16/17: confirmed two working routes to create a dev store via the link.
- **SKU-prefix decision, `PAF-`.** Tom Dunn's "Purdy SKU Similarities" question closed 2026-07-16/17 — decision was a `PAF-` prefix (SNAP's 30-char SKU limit is fine with it). Follow-on still open per Tom Dunn's tracker: configure the `PAF-` prefix add/strip for Purdy & Figg (LISAUK) in the integration.
- **Shopify app UAT.** Week of 2026-08-03: "Purdy & Figg's Shopify app UAT has test orders flowing in dev" (per that week's roundup).
- **Kit confirmations.** Needed ahead of P&F's kit stock arriving in the warehouse (flagged as urgent, week of 2026-08-03) — P&F sells kits, so this is the customer the [[Bifrost/Kit Confirmations & Short-Ship (FUSE-785)]] short-ship/partial-fulfilment work was driven by. `XTTRS` (= 2× `TTRS`) is the example kit in that note — the same `TTRS` component SKU that threw a SNAP-side `NullReferenceException` in the GADG soak test today, on a different (Gadgets) account. Worth checking whether that's the same underlying SNAP defect surfacing on both accounts.
- **Bulk-ingest scaling.** Week of 2026-08-03: design validated against real throughput numbers to lift the Shopify connector's then-~1,700-orders/hour ceiling for P&F's volumes. The GADG soak test (`hjf/bulk-test-order-seeder`, `bulk_ingest_enabled_businesses`) is the multi-day load-test proof-of-readiness exercise for that same lane — run against Gadgets rather than P&F directly, deliberately ramping the order volume in the store over several days to find where the pipeline tips over. See [[Explainers/2026-08-25-gadg-bulk-ingest-soak-test-findings]].
- **Collector had no scale-out ceiling — found via the GADG soak test, fixed 2026-08-25.** As the soak test's volume ramped, `collector-dev` scaled to 33 Cloud Run instances with nothing bounding it (no `scaling.max_instance_count` had ever been set — it ran on Cloud Run's implicit default of 100). Its 28 Pub/Sub subscriptions were temporarily stubbed (push→pull) to take it out of the loop while a proper cap was sized: 15, from its dedicated Atlas cluster's M10 connection floor (1,500) ÷ Cloud Run concurrency (80). Cap is live and verified on `collector-dev` (PR `hjf/fuse-1000-collector-scaling-cap`, `gfs-bifrost/collector`). **Subscriptions are still stubbed as of 2026-08-25 20:12 BST** — pending Harry's call on restoring them into the soak test now the cap's in place. If P&F's own volumes ever approach this ceiling, this is the number that will need revisiting first, not the code.
- **~16 hanging dev confirmations — unresolved.** James Godsell asked what use case the ~16 hanging P&F dev confirmations were for (#bifrost-general, 2026-08-04) — unanswered as of the most recent tracking (2026-08-10). Tom Dunn separately guessed "stock adjustment" for the record type, also unconfirmed. Harry's own counter-question to James/[[Lee Simmons]] on a missing egress connector is unanswered too — this thread is stalled on both sides.
- **Peak job-timing investigation.** DarrenC (ilguk) investigating P&F peak job timing, still confirming with the customer's own Shopify team as of 2026-08-06.
- **Size-tag formatting.** Week of 2026-08-18: spent much of the week walking James Godsell through Fuse's mapping tools to fix P&F's size-tag formatting, ending with a written usage guide for ILG's team.

## Adjacent production signal

- **PURDYFIGG resend-loop burst, 2026-07-29** — a 90,259-record ingest burst with 2,734 failures the same day, matching the PURDYFIGG re-promote/resend loop behind [FUSE-1085](https://globalfreight.atlassian.net/browse/FUSE-1085) / [FUSE-1086](https://globalfreight.atlassian.net/browse/FUSE-1086). Failures were flat zero for the following few days, suggesting the loop is bounded — noted at the time as inference, not confirmed. Worth a fresh check given how much of the pipeline this page's soak test just exercised.

## Open questions / not done

- `PAF-` SKU prefix add/strip: decided, not yet confirmed configured in the integration.
- ~16 hanging dev confirmations: record type and use case both still unknown.
- Whether the GADG soak test's `TTRS`-kit `NullReferenceException` is the same SNAP defect class relevant to P&F's own kit confirmations — not yet checked against a P&F environment.
- PURDYFIGG resend-loop: bounded-ness was inferred, never independently reconfirmed.

## Related
- [[Jack Bailey]] — FUSE-963 owner, SOW/relationship threads
- [[James Godsell]], [[Tom Dunn]] — ILG-side technical/testing contacts
- [[Bifrost/Kit Confirmations & Short-Ship (FUSE-785)]]
- [[Explainers/2026-08-25-gadg-bulk-ingest-soak-test-findings]]
- [[Meetings/Bifrost - Operational Readiness]], [[Meetings/FUSE Shopify Load Test Call]], [[Meetings/Fuse-Bifrost Weekly Sync]]
