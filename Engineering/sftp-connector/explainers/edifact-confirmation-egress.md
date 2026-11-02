---
tags: [waypoint, explainer, sftp-connector]
thesis: "A connector with egressFiletype edi gets one EDIFACT interchange per document, built by its own mapping and created once under a deterministic name. An invalid message writes no file: a confirmation records a confirmation_data_failure, but a stock adjustment records nothing."
confidence: high
updated: 2026-10-19
verified: 2026-10-19
verified_sha: 7071412
verified_paths:
  - code/src/confirmations/edi/message-table.ts
  - code/src/confirmations/edi/apply-mapping.ts
  - code/src/confirmations/edi/schemas.ts
  - code/src/confirmations/edi/build-edi-files.ts
  - code/src/confirmations/confirmation-egress.service.ts
  - code/src/confirmations/stock-adjustment.service.ts
  - code/src/confirmations/stock-adjustment.transformer.ts
  - code/src/confirmations/to-confirmation-failure.ts
  - code/src/confirmations/constants.ts
  - code/src/gcs/storage.service.ts
  - code/src/types/confirmations/operations.ts
  - code/src/controllers/pubsub.controller.ts
  - code/src/app-config/config.ts
  - code/src/observability/constants.ts
  - code/src/exceptions/confirmation.exception.ts
  - code/package.json
  - iac/projects/bifrost-sftp-connector/storage.tf
title: EDIFACT confirmation egress
drifted_evidence: []
drift_checked: 2026-10-19
commits_behind: 0
---
# EDIFACT confirmation egress

```orient-bluf
{
  "v": 1,
  "bluf": "A connector with egressFiletype edi gets one EDIFACT interchange per document, built by its own mapping and created once under a deterministic name. An invalid message writes no file: a confirmation records a confirmation_data_failure, but a stock adjustment records nothing.",
  "confidence": "high",
  "action": "Watch EdiMessageInvalid on stock adjustments: nothing records them and Snap does not re-announce them."
}
```

## Mechanism

```orient-flow
{
  "v": 1,
  "title": "Canonical confirmation to EDIFACT file",
  "nodes": [
    { "id": "ready", "label": "confirmation_ready", "sub": "one route per recordType", "kind": "topic", "ev": [25] },
    { "id": "sar", "label": "stock_adjustment_ready", "sub": "own route", "kind": "topic", "ev": [25] },
    { "id": "egress", "label": "ConfirmationEgressService", "sub": "gates per connector", "kind": "step", "service": "sftp-connector", "ev": [7, 10] },
    { "id": "stock", "label": "StockAdjustmentService", "sub": "EDI branch", "kind": "step", "service": "sftp-connector", "ev": [14, 15] },
    { "id": "build", "label": "buildEdiFiles", "sub": "table · mapping · schema", "kind": "step", "tone": "accent", "ev": [1, 3, 5] },
    { "id": "lib", "label": "@gfs-bifrost/edi", "sub": "serializeInterchange", "kind": "step", "ev": [18, 20] },
    { "id": "gcs", "label": "Storage bucket", "sub": "createFile · generation 0", "kind": "store", "ev": [13] },
    { "id": "sftp", "label": "Customer SFTP", "sub": "<USER>/from_ilg/…", "kind": "external", "ev": [17] },
    { "id": "fail", "label": "confirmation_data_failure", "sub": "write_failed per record", "kind": "topic", "tone": "alert", "ev": [11, 12] },
    { "id": "replay", "label": "replay", "sub": "redrive to confirmation_ready", "kind": "service", "ev": [23] },
    { "id": "made", "label": "confirmation_made / stock_adjustment_made", "kind": "topic", "ev": [10, 14] }
  ],
  "edges": [
    { "from": "ready", "to": "egress" },
    { "from": "sar", "to": "stock" },
    { "from": "egress", "to": "build" },
    { "from": "stock", "to": "build" },
    { "from": "build", "to": "lib", "label": "valid" },
    { "from": "lib", "to": "gcs" },
    { "from": "gcs", "to": "sftp", "label": "customer collects" },
    { "from": "build", "to": "fail", "label": "invalid, confirmations only", "style": "dashed" },
    { "from": "fail", "to": "replay" },
    { "from": "egress", "to": "made", "label": "any leg delivered" },
    { "from": "stock", "to": "made", "label": "no invalid INVRPT" }
  ]
}
```

### Switching it on

- **CONFIRMED** A connector opts in with `egressFiletype: "edi"` and an `ediEnvelope`. The envelope holds the UNB sender and receiver ids, their qualifiers, and an optional test indicator [7][18].
- **CONFIRMED** The service needs `FEATURE_FLAG_EDI` and `FEATURE_FLAG_USE_DYNAMIC_CONFIRMATION_MAPPING` on. The record type needs an entry in the message table [1][7][8][16].
- **CONFIRMED** The usual gates still apply: an active connector, a username, an active use case with config, and fetchable mapping rules [7].
- **CONFIRMED** An `edi` connector never falls back to CSV. A failed EDI gate skips it and counts `fuse.confirmation.unroutable` with `edi_egress_not_enabled`, `edi_requires_dynamic_mapping`, `edi_envelope_missing` or `edi_unsupported_type` [7][8].
- **CONFIRMED** A confirmation routed to a skipped connector records an undeliverable failure for it. On fan-out, only the dynamic path records one, as `edi_not_deliverable` [7][8][10][11].

### Record type to message

| Record type | Message | Document reference |
|---|---|---|
| `purchase_order` (goods-in) | RECADV | `identifiers.receiptId` |
| `sales_order` (goods-out) | DESADV, one record per parcel | `identifiers.shipmentId` |
| `pack_confirmation` | DESADV | `identifiers.shipmentId` |
| `pick_confirmation` | OSTRPT | `identifiers.shipmentId` |
| `return_goods_authorization` | RECADV, or INVRPT by mapping | `identifiers.id` |
| `finished_good_receipt` | RECADV | `identifiers.id` |
| `work_order_confirmation` | INVRPT, component lines only | `identifiers.id` |
| `stock_adjustment` | INVRPT | `identifiers.id` |

- **CONFIRMED** A return becomes INVRPT when a header rule sets `messageType` to `INVRPT`. Any value outside a type's allowed set fails as `invalid_mapping` [1][5].
- **CONFIRMED** A work-order confirmation drops finished-good lines, because the finished-good receipt books them [1].

### How the mapping builds the message

- **CONFIRMED** A rule's `from` is a dotted path in the message shape, and its `to` is the expression over the canonical. A numeric segment builds a list in index order [3][4].
- **CONFIRMED** In a lined mapping, header rules run once on the first record. Line rules run per canonical line and write `lines.*`, or `packages.*` on DESADV [3].
- **CONFIRMED** In the simple stock-adjustment mapping, each record becomes a line. The first record's other fields become the header [3].
- **CONFIRMED** `mappingIssues` rejects a lined or simple mismatch, a line rule outside those prefixes, and a header rule that writes a line field. Any of these fails the batch once as `invalid_mapping` [3][5].
- **CONFIRMED** Header rules carry the partner's codes. `codes.*` holds per-message codes. `unh.*` holds release, version, agency and association code. The UNH reference is not configurable [4].
- **CONFIRMED** DESADV groups lines into packages by `packages.sscc`. A header `rootPackage` nests them under one outer package [2].
- **CONFIRMED** The assembled message must parse against a strict per-message schema. An unknown key or a missing required field fails it [4][5].
- **CONFIRMED** `@gfs-bifrost/edi` serializes at EANCOM D.96A by default and wraps one message in UNB…UNZ. The syntax stays at the `UNOC:3` default, and UNB carries the write time in UTC [5][18][20].

### One message, one file, written once

- **CONFIRMED** A lined mapping makes one message per confirmation. A stock-adjustment batch makes one per distinct `identifiers.id` [1][5].
- **CONFIRMED** The file is `<MSG>_<docRef>_<ctrlRef>.edi` under `<USERNAME>/from_ilg/<type>_confirmations/`. Finished-good receipts honour the connector's directory, and stock adjustments use `stock_adjustment_confirmations/` [5][9][14][17].
- **CONFIRMED** The control reference is 14 hex characters of a SHA-256 over connector id, record type, document reference and sorted queue ids. It is also the UNB, UNH and UNZ reference [6][20].
- **CONFIRMED** A document without a reference fails as `invalid_message`. Characters outside `[A-Za-z0-9_-]` in the reference become `-` [5][6].
- **CONFIRMED** `createFile` saves with `ifGenerationMatch: 0`. An existing object logs `EdiFileAlreadyExists`, is not rewritten, and the leg still counts as delivered [9][13].
- **ASSESSED** The first write wins. A redelivery reuses the name, so a corrected mapping cannot replace a file already written. This rests on [6] and [13].
- **ASSESSED** The bucket keeps object versions [24]. After the customer deletes a collected file, a resend writes it again under the same control reference. The receiver's duplicate check is the backstop.

### Failure path: confirmations

- **CONFIRMED** Each failed document logs `EdiMessageInvalid` with its reason and issues. Valid documents in the same batch still write [5][9].
- **CONFIRMED** Any invalid document fails that connector's leg through `WriteFailed`. The error is `InvalidEdiMessage`, and `fuse.confirmation.forward.failure` counts it by `type` [10][26].
- **CONFIRMED** The leg publishes one failure per record in the batch to `confirmation_data_failure`. Each names the connector, with code `sftp-connector.<type>.write_failed` and `retryable: false`. The handler then acks the push [11][12].
- **CONFIRMED** `confirmation_made` publishes only if another leg delivered. A routed confirmation has one leg, so its `made` is withheld [10].
- **CONFIRMED** Withholding `made` does not make Snap re-announce. The poller clears each outbound-queue row as it publishes, and snap-adapter no longer reads `made` [21][22].
- **CONFIRMED** replay persists the failure, and a redrive republishes it to `confirmation_ready`. Documents already written then hit `EdiFileAlreadyExists` [13][23].

### Failure path: stock adjustments

- **CONFIRMED** `StockAdjustmentService` checks the same EDI gates. A failed gate counts the metric and records nothing [15].
- **CONFIRMED** An invalid INVRPT logs `EdiMessageInvalid` and counts `forward.failure` with `type: stock_adjustment`. Other targets still write, and `stock_adjustment_made` is withheld for the batch [14].
- **CONFIRMED** The service publishes no failure record. Nothing re-announces the batch, because the poller cleared those rows at publish [14][21].
- **CONFIRMED** The in-code comment saying Snap re-announces the batch is stale [14][22].

### SSCC and batch

- **CONFIRMED** DESADV demands a package SSCC only when `requireSscc` is true. `packages.requireSscc` beats `codes.requireSscc`, and the default is false [4][19].
- **CONFIRMED** A missing required SSCC throws in the serializer. The document fails as `invalid_message` and takes the failure path [5][19].
- **CONFIRMED** DESADV needs at least one line unless `codes.requireLines` is false [19].
- **CONFIRMED** Nothing makes a batch mandatory. A DESADV line without one omits `PCI+36E` and `GIN+BX` and still passes [4][19].

### Observability

- **CONFIRMED** `fuse.confirmation.forward` carries `fileType`: `edi`, `csv` or `jsonl`. A delivery counts once per file type, so a broadcast to CSV and EDI connectors counts under each [10].
- **CONFIRMED** `zod_dropped` on that metric counts per target file type. `forward.failure` carries only `type` [10].
- **CONFIRMED** Stock adjustments emit no `fuse.confirmation.forward` [14].

## Boundaries

- **CONFIRMED** sftp-connector selects targets, applies the mapping, and names and writes the file. `@gfs-bifrost/edi` owns segment syntax and EANCOM defaults [5][18].
- **CONFIRMED** `confirmations/edi/` holds no partner code. Each partner's codes, qualifiers and message choice live in the connector's mapping rules [1][4].
- **CONFIRMED** The poller builds the canonical and clears Snap before sftp-connector sees it [21].
- **CONFIRMED** replay owns redrive. sftp-connector only publishes the failure [23].

## Constraints

- **CONFIRMED** The mapping is the customer contract. A mapping edit changes the file with no code diff [27].
- **ASSESSED** One bad document fails the leg for the whole batch. replay then holds failures for records whose files exist, and their redrive publishes `made` [9][10][11].
- **CONFIRMED** The failure carries type `infrastructure` and `retryable: false`, though the mapping is the usual cause [12].

## Evidence

```orient-evidence
{
  "v": 1,
  "items": [
    { "id": 1, "kind": "code", "ref": "code/src/confirmations/edi/message-table.ts@7071412:L114-173", "note": "record type to message table, alternatives, component lines only" },
    { "id": 2, "kind": "code", "ref": "code/src/confirmations/edi/message-table.ts@7071412:L56-83", "note": "DESADV groups lines by packages.sscc, rootPackage" },
    { "id": 3, "kind": "code", "ref": "code/src/confirmations/edi/apply-mapping.ts@7071412", "note": "mappingIssues and header/line rule application" },
    { "id": 4, "kind": "code", "ref": "code/src/confirmations/edi/schemas.ts@7071412", "note": "strict message schemas, codes, UNH options, optional batch" },
    { "id": 5, "kind": "code", "ref": "code/src/confirmations/edi/build-edi-files.ts@7071412:L48-150", "note": "documents, parse, serializeInterchange, file name" },
    { "id": 6, "kind": "code", "ref": "code/src/confirmations/edi/build-edi-files.ts@7071412:L170-195", "note": "control reference and docRef sanitising" },
    { "id": 7, "kind": "code", "ref": "code/src/confirmations/confirmation-egress.service.ts@7071412:L714-843", "note": "connector gates and EDI envelope" },
    { "id": 8, "kind": "code", "ref": "code/src/confirmations/confirmation-egress.service.ts@7071412:L845-927", "note": "legacy path skips edi; skip metric" },
    { "id": 9, "kind": "code", "ref": "code/src/confirmations/confirmation-egress.service.ts@7071412:L999-1071", "note": "writeEdiFiles and createEdiFile" },
    { "id": 10, "kind": "code", "ref": "code/src/confirmations/confirmation-egress.service.ts@7071412:L148-453", "note": "process, deliver, WriteFailed, made, forward metric" },
    { "id": 11, "kind": "code", "ref": "code/src/confirmations/confirmation-egress.service.ts@7071412:L455-505", "note": "one failure per record per failed leg" },
    { "id": 12, "kind": "code", "ref": "code/src/confirmations/to-confirmation-failure.ts@7071412:L15-36", "note": "write_failed failure body" },
    { "id": 13, "kind": "code", "ref": "code/src/gcs/storage.service.ts@7071412:L218-233", "note": "createFile with ifGenerationMatch 0" },
    { "id": 14, "kind": "code", "ref": "code/src/confirmations/stock-adjustment.service.ts@7071412:L78-168", "note": "stock adjustment write, withheld made, stale comment at L156" },
    { "id": 15, "kind": "code", "ref": "code/src/confirmations/stock-adjustment.service.ts@7071412:L277-322", "note": "stock adjustment EDI gates" },
    { "id": 16, "kind": "code", "ref": "code/src/app-config/config.ts@7071412", "note": "featureFlags.edi and useDynamicConfirmationMapping" },
    { "id": 17, "kind": "code", "ref": "code/src/types/confirmations/operations.ts@7071412:L64-85", "note": "fileTypeForEgress, getEgressDirectory" },
    { "id": 18, "kind": "url", "ref": "https://github.com/gfs-bifrost/pkg-node/blob/63d441b2a5115e0e3553e3e0a302362b680bb6f9/pkg/edi/src/serializers/interchange.ts#L47-L91", "note": "edi 0.8.1: UNB from envelope, UNOC:3 default, 1-14 char control reference" },
    { "id": 19, "kind": "url", "ref": "https://github.com/gfs-bifrost/pkg-node/blob/63d441b2a5115e0e3553e3e0a302362b680bb6f9/pkg/edi/src/serializers/desadv.serializer.ts#L199-L289", "note": "requireLines, requireSscc, batch PCI+GIN only when present" },
    { "id": 20, "kind": "url", "ref": "https://github.com/gfs-bifrost/pkg-node/blob/63d441b2a5115e0e3553e3e0a302362b680bb6f9/pkg/edi/src/edi.ts#L183-L193", "note": "serializeInterchange: UNH reference = control reference" },
    { "id": 21, "kind": "url", "ref": "https://github.com/gfs-bifrost/snap-adapter/blob/76f6fbf0326106ad478c1ce0e6e76702f774a178/apps/snap-queue-polling-service/src/core/snap/confirmations/outbound-queue.clearer.ts#L90-L106", "note": "poller clears rows at publish, stock adjustments included" },
    { "id": 22, "kind": "pr", "ref": "gfs-bifrost/snap-adapter#294", "note": "retired the made-driven clear-down for stock adjustments; #292 did it for confirmation_made" },
    { "id": 23, "kind": "doc", "ref": "fuse://pubsub-topology confirmation_data_failure", "note": "replay persists; redrive republishes to confirmation_ready" },
    { "id": 24, "kind": "code", "ref": "iac/projects/bifrost-sftp-connector/storage.tf@7071412", "note": "bucket versioning enabled" },
    { "id": 25, "kind": "code", "ref": "code/src/controllers/pubsub.controller.ts@7071412:L100-111", "note": "stock adjustment and confirmation routes" },
    { "id": 26, "kind": "code", "ref": "code/src/exceptions/confirmation.exception.ts@7071412", "note": "InvalidEdiMessage" },
    { "id": 27, "kind": "doc", "ref": "Engineering/sftp-connector/architecture.md", "note": "guardrail G3: the config is the contract" }
  ]
}
```

## Related

[[Engineering/sftp-connector/architecture|sftp-connector architecture]] ·
[[Engineering/sftp-connector/interfaces|interfaces]] ·
[[Engineering/snap-adapter/explainers/work-order-family-confirmations|work-order family confirmations]]
