---
tags: [explain]
date: '2026-08-24'
title: Work order confirmations doubled their lines because Snap mirrors every line onto both documents
thesis: "The WOC file wrote 4 rows for a 2-line work order because Snap puts every work-order line on both the S10 shipment and the R10 receipt, and the handler concatenated the documents instead of joining them."
confidence: high
---
# Work order confirmations doubled their lines because Snap mirrors every line onto both documents

```orient-bluf
{ "v": 1, "bluf": "The WOC file wrote 4 rows for a 2-line work order because Snap puts every work-order line on both the S10 shipment and the R10 receipt, and the handler concatenated the documents instead of joining them.", "confidence": "high", "action": "Restore a work_order_confirmation egress mapping on a GADG dev SFTP connector, then verify the WOC file." }
```

## Situation

- **CONFIRMED** QA (Schuster) moved FUSE-866 to Rework Required. The file had 4 lines, not 2. Every `Consumed` read 0. The file mislabelled roles. [1]
- **CONFIRMED** The connector only consumes a mapping, so the defect sat upstream. The producer is the work-order confirmation handler in snap-adapter. [1]
- **CONFIRMED** The handler assumed the S10 shipment holds consumed components and the R10 receipt holds finished goods produced. It concatenated the two line sets. [2]

## Assessment

- **CONFIRMED** Snap carries the same line keys on both documents. Quantities, not the document, say each line's role. [3]
- **CONFIRMED** Two independent GADG work orders show the same shape: `GADG7896F1CD757` (closed 2026-08-21) and `GADG92E4DFF6C7E` (closed 2026-08-24 11:46). Mirroring is Snap behaviour, not one odd record. [3][4]
- **CONFIRMED** Three faults followed from that one assumption. [2]

| Fault | Cause | Fix |
|---|---|---|
| Row count | `[...componentLines, ...finishedGoodLines]` emits one row per document per key | Join on `Line` key, full outer |
| Role | Role came from the source document | `QtyRequired > 0` is a component; `QtyOrdered > 0` is a finished good |
| `consumed = 0` | Handler read `QtyShipped`, which is always 0 on a work order | Read `QtyPicked`; take `produced` and `rejected` from the receipt line |

- **CONFIRMED** A component row still had a `produced` field available, and the reverse. A zero then rendered as a literal `0` in the CSV, where the customer expects blank. The handler now scopes quantities to the role. [2]
- **CONFIRMED** The full outer join keeps a receipt-only by-product line. A genuinely unclassifiable line logs a `logger.warn`. [2]
- **CONFIRMED** The fix needs no `@gfs-bifrost/types` change. The line's `quantities` object already carries all seven fields. [2]
- **CONFIRMED** Nine new behavioural assertions all failed against the base handler (`acb85ed`) and passed against the fix. A green suite alone was not the evidence. [5]
- **CONFIRMED** The merged fix is snap-adapter#204. The current handler still joins on `Line`. [6][7]

## Open items

| Item | Owner | By |
|---|---|---|
| **UNKNOWN** Verify the WOC file. No `work_order_confirmation` mapping exists on four GADG dev SFTP connectors, all 404, while `finished_good_receipt` returns 200. | QA (Schuster) | UNKNOWN |
| **UNKNOWN** Explain `RECEIPT` entries accumulating unprocessed in GADG's dev outbound queue since 2026-08-21. This looks like the FGR side not draining. | UNKNOWN | UNKNOWN |

## Evidence

```orient-evidence
{
  "v": 1,
  "items": [
    { "id": 1, "kind": "ticket", "ref": "FUSE-866", "note": "QA rejection into Rework Required" },
    { "id": 2, "kind": "doc", "ref": "Engineering/snap-adapter/plans/FUSE-866-join-woc-lines-by-line-key", "note": "plan and running state for the fix" },
    { "id": 3, "kind": "log", "ref": "Live Snap shipment and receipt GADG7896F1CD757: both carry SD014GSBBN and SD014GSXE5; QtyShipped 0 on both lines, QtyPicked 2 on the component" },
    { "id": 4, "kind": "log", "ref": "Live Snap shipment GADG92E4DFF6C7E: keys SD5QNQVCGL and SD5QNQW0AF" },
    { "id": 5, "kind": "log", "ref": "work-order-confirmation.live-payload.spec.ts: 9 assertions fail on acb85ed, pass on the fix; dev deploy run 32720753434, branch hjf/fuse-866-woc-line-join" },
    { "id": 6, "kind": "pr", "ref": "gfs-bifrost/snap-adapter#204", "note": "merged; state checked 2026-10-12" },
    { "id": 7, "kind": "doc", "ref": "Engineering/snap-adapter/explainers/work-order-family-confirmations", "note": "system explainer, verified 2026-10-12 at ccfcd9a" }
  ]
}
```
