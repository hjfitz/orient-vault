---
tags: [customer, PURDYFIGG]
verified: '2026-09-02'
title: Purdy & Figg — Overview
---

# Purdy & Figg — Overview

**Business ID: `PURDYFIGG`.** ILG's biggest customer onboarded this year — onboarding ticket
[FUSE-963](https://globalfreight.atlassian.net/browse/FUSE-963), owned by [[Jack Bailey]]
(Product). Went live in production **2026-09-01**, alongside Saira Skin, after onboarding under
real time pressure the week of 2026-08-18.

## Integration shape

- **Sole channel: Shopify** (`purdy-figg.myshopify.com`), connector `conn_7ce8402090194b67b0f8a1de03019397`
  on the **bulk-ingest path** (enabled prod 2026-08-28) — a stateless 5-minute bulk-operation tick,
  not the metered poll. No SFTP/EDI/REST channel.
- Confirmations, outbound tags, and stock adjustments are all **off** (`confirmationsEnabled:
  false`, `outboundTagsEnabled: false`, `stockAdjustmentsEnabled: false`) as of go-live.
- Warehouse `BRACKMILLS2`, carrier `GFS_HERMES`, order class `PURDYE`.
- Upstream of Shopify: orders originate in **Unleashed** and land in Shopify already processed —
  subscriptions specifically route through **Skio** before landing as Shopify orders. Neither
  system is directly integrated with Fuse; Fuse only ever sees the Shopify order.
- Sells kits (`XTTRS` = 2×`TTRS` is the standing example) — see
  [[Bifrost/Kit Confirmations & Short-Ship (FUSE-785)]], which this customer's kit-stock timeline
  drove.

## Retrieval gating (the load-bearing config)

Orders only become visible to the bulk tick once **all** of `financial_status:paid`,
`fulfillment_status:unfulfilled`, `tag:ILG_RELEASED`, and `created_at` within the standing
lookback window are true (hard-AND — see [[known-context|known-context.md]] for why this bit
us at go-live and the current window value). `ILG_RELEASED` is P&F's own release gate, applied
by their team roughly **90 minutes** after order creation by design.

Full integration diagram: [[architecture|architecture.md]].

## History

- **Pre-go-live testing thread**: [[Bifrost/Purdy & Figg Testing/Overview|Purdy & Figg — Testing (Overview)]]
  — UAT, SKU-prefix decision (`PAF-`), the GADG bulk-ingest soak test that validated this
  customer's throughput needs, the collector scaling-cap fix it surfaced, and open items as of
  2026-08-25 (hanging dev confirmations, kit `NullReferenceException` follow-up, PURDYFIGG
  resend-loop bounded-ness). That page stays the pre-go-live record; this folder is the
  **post-go-live production** record — config decisions, incidents, and captured live state.

## Related

- [[Jack Bailey]] — FUSE-963 owner, SOW/relationship threads
- [[James Godsell]], [[Tom Dunn]] — ILG-side technical/testing contacts
- [[Bifrost/Purdy & Figg Testing/Overview]] — pre-go-live testing history
- [[Bifrost/Kit Confirmations & Short-Ship (FUSE-785)]]
