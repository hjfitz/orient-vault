---
tags: [explain]
date: 2026-10-27
thesis: "Fuse can book Selector shipments for customer-packed orders: the adapter is built and deployed to dev, but Selector never deduplicates, so Fuse must own idempotency, and real traffic waits on the Delivery Backends programme."
confidence: high
---
# Selector adapter spike: what we learned

```orient-bluf
{ "v": 1, "bluf": "Fuse can book Selector shipments for customer-packed orders: the adapter is built and deployed to dev, but Selector never deduplicates, so Fuse must own idempotency, and real traffic waits on the Delivery Backends programme.", "confidence": "high", "action": "PM/EM: confirm the v1 limits below (GB only, one package, no labels or tracking back) before Delivery Backends B2 goes to prod." }
```

## Situation

- **CONFIRMED** The Go `selector-adapter` turns one canonical sales order into one Selector `ProcessShipment` call. The #1–#4 stack merged it, and it runs as `selector-adapter-dev` [1][2].
- **CONFIRMED** Against the Selector sandbox it booked real consignments. It handled rejections, bad credentials, outages and redelivery as designed. I deleted every test booking afterwards [3][4].
- **CONFIRMED** It receives no traffic yet. Its subscription only takes orders the deduper tags `selector`, and nothing tags them until Delivery Backends units A3 and B1 [5].

## Assessment

- **CONFIRMED** Selector books the same reference again: three calls made three consignments. Fuse must guarantee at most one booking per order. A Firestore claim does that, and the adapter checks `DailyShipQuery` before rebooking an unknown outcome [3].
- **CONFIRMED** Bad credentials return a normal `FAILURE 0010` reply, not an error. The adapter treats it as a setup fault and retries; it never drops the order [3].
- **CONFIRMED** A booking takes about 0.43 s (p95 0.47 s over 10 calls). Selector rejects a past or missing despatch date, so Fuse sends today (UK time) when the order's date has passed [3].
- **CONFIRMED** The canonical sales order has no packages. v1 sends one package per order, using the order weight or a configured default [6].
- **ASSESSED** PM/EM should agree four v1 limits before customers depend on it. These are the spike's own decisions, not tested product needs [2]:

| v1 limit | Why |
|---|---|
| Domestic (GB) only | The adapter rejects international orders, because the canonical carries no customs data |
| One package per order | The canonical carries no packages |
| Nothing comes back | No tracking number, label or acknowledgement reaches the customer |
| An amended, already-booked order stays booked | Amendment semantics are a product question |

- **CONFIRMED** Selector config is a `SELECTOR` backend in config-service. Its management screen is a Merak portal, never fuse-ui [5].

## Open items

| Item | Owner | By |
|---|---|---|
| Agree the v1 limits above | PM/EM | before B2 prod |
| Contract and config-service units A1–A3 (A1's field set comes from this spike) | Delivery Backends | unscheduled |
| Deduper tag B1, then the live end-to-end check in B2 | Delivery Backends | after A3 |

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "pr", "ref": "gfs-bifrost/selector-adapter#4" },
  { "id": 2, "kind": "doc", "ref": "Engineering/selector-adapter/plans/selector-adapter-dev-spike.md" },
  { "id": 3, "kind": "url", "ref": "https://github.com/gfs-bifrost/selector-adapter/blob/e5f710a/docs/selector-sandbox-findings.md" },
  { "id": 4, "kind": "pr", "ref": "gfs-bifrost/selector-adapter#3" },
  { "id": 5, "kind": "doc", "ref": "Bifrost/Delivery Backends/Migration State.md" },
  { "id": 6, "kind": "pr", "ref": "gfs-bifrost/selector-adapter#2" }
] }
```
