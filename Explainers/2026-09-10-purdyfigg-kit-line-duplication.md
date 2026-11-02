---
tags: [explain]
date: 2026-09-10
thesis: "A masked TypeError in snap-adapter's metrics interceptor turned a transient SNAP failure into a false permanent one. Dedupe re-collected one PURDYFIGG kit order 16 times, and a repeat PUT duplicated its component lines in SNAP."
confidence: moderate
---
# A masked TypeError turned one PURDYFIGG kit order into a duplicate-line shipment in SNAP

```orient-bluf
{ "v": 1, "bluf": "A masked TypeError in snap-adapter's metrics interceptor turned a transient SNAP failure into a false permanent one. Dedupe re-collected one PURDYFIGG kit order 16 times, and a repeat PUT duplicated its component lines in SNAP.", "confidence": "moderate", "action": "Ask the warehouse to check shipment PURDCE5A8C4CBBC before despatch, and decide who sweeps other shipments duplicated in the same window." }
```

## Situation

- **CONFIRMED** Support (Joseph, ILG ops) escalated shipment `PURDCE5A8C4CBBC` (order `#6330760`, Purdy & Figg). SNAP shows each kit component line twice. He had no correlation ID. [3]
- **CONFIRMED** The shipment sits at Stage 39 (Pack). Components `CP3220A`, `CP3231` and `CP3237` each appear twice. [3]
- **CONFIRMED** The same bug had already been under investigation that morning under FUSE-1147. [5][6]

## Assessment

- **CONFIRMED** Fuse received a clean order. The held canonical record has one `shipmentLines` entry: kit SKU `FG1090`, qty 1. [1]
- **CONFIRMED** The order failed 16 times, 16:55 to 18:10 BST on 2026-09-09. Every failure carried the identical masked message. [2]
- **CONFIRMED** The failure-metrics interceptor in `axios-metrics.ts` read `config.requestStart` without a null guard. The read threw `Cannot read properties of undefined`, which hid the real SNAP error. [4]
- **CONFIRMED** The masked error classified as `mode: unexpected, transient: false`. The classifier never saw the retryable error beneath it. [2]
- **ASSESSED** `handleSnapFailure` then released the dedupe hold instead of nacking for redelivery. Dedupe deletes a released record, so the next 5-minute bulk tick re-collected the order as new. This rests on the 16 repeats and the FUSE-1147 plan. [2][6]
- **ASSESSED** Each retry reused the same deterministic `ShipmentId`, so it landed on the same SNAP shipment. SNAP re-ran the kit bill-of-materials explosion and appended a second set of component lines. The FUSE-1147 investigation found that kit duplication tracks 500-class re-PUTs, while a non-kit re-PUT gets a harmless 400. [6]
- **CONFIRMED** The guard fix merged on 2026-09-07. Its deploy sat on an unapproved gate until 2026-09-10, so production kept running the bug. [4][6]

| Step | Actor | Event |
|---|---|---|
| 1 | snap-adapter | PUTs the shipment with the parent kit line only |
| 2 | SNAP | Fails; the real cause stays masked |
| 3 | snap-adapter | Classifies the failure permanent, releases the hold |
| 4 | dedupe-service | Deletes the hold; the next tick re-collects the order |
| 5 | SNAP | On a repeat PUT, re-explodes the kit bill-of-materials |

## Open items

| Item | Owner | By |
|---|---|---|
| **UNKNOWN** Which of the 16 attempts hit SNAP's 500 path. The logs cannot tell, so why only one duplication pass happened is also unknown. | snap-adapter | unset |
| **UNKNOWN** The original SNAP error behind the first failure. The interceptor masked it before classification. | snap-adapter | unset |
| The warehouse checks `PURDCE5A8C4CBBC` before despatch. The code fix does not repair existing duplicate lines. | Support / ops | unset |
| No ticket covers sweeping other shipments duplicated in the same window. Only this one is known. | Harry | unset |
| Spot-check at migration: FUSE-1147 follow-ups #217 and #218 both merged 2026-09-10. Their production deploy is unchecked. | Harry | unset |

## Evidence

```orient-evidence
{
  "v": 1,
  "items": [
    { "id": 1, "kind": "log", "ref": "replay-get-failure, prod, id 5028a33a-e07d-4cf5-88c6-c13957b8558b: canonical record with one shipmentLines entry", "note": "held failure record" },
    { "id": 2, "kind": "log", "ref": "replay-list-failures, prod, search '#6330760': 16 identical failures, 16:55-18:10 BST 2026-09-09", "note": "masked message and classification" },
    { "id": 3, "kind": "log", "ref": "snap-get-shipment PURDCE5A8C4CBBC: three component SKUs present twice, Stage 39", "note": "SNAP state at the time of writing" },
    { "id": 4, "kind": "pr", "ref": "gfs-bifrost/snap-adapter#216", "note": "null guard in the failure-metrics interceptor; merged 2026-09-07" },
    { "id": 5, "kind": "ticket", "ref": "FUSE-1147" },
    { "id": 6, "kind": "doc", "ref": "Engineering/snap-adapter/plans/FUSE-1147-stop-re-putting-live-shipments.md", "note": "wider investigation, progress log, #216/#217/#218 stack" }
  ]
}
```
