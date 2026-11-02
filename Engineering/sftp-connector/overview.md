---
tags:
- waypoint
- sftp-connector
verified: '2026-10-14'
verified_sha: 4e1593e
verified_paths:
- code/src
- CLAUDE.md
- iac/projects/bifrost-sftp-connector
- iac/env
title: sftp-connector — overview
thesis: 'sftp-connector is the file edge of Fuse: it turns customer files in one GCS
  bucket into canonical records, writes confirmations back as mapped CSV, JSONL or
  EDIFACT files, and owns the SFTP VM customers log into.'
confidence: high
---
# sftp-connector — overview

```orient-bluf
{ "v": 1, "bluf": "sftp-connector is the file edge of Fuse: it turns customer files in one GCS bucket into canonical records, writes confirmations back as mapped CSV, JSONL or EDIFACT files, and owns the SFTP VM customers log into.", "confidence": "high", "action": "Keep file formats out of the rest of the pipeline: never publish a raw file shape to Pub/Sub, and never move parsing into another service." }
```

## Responsibility

- **Inbound.** Customers drop CSV, JSON or JSONL files on the SFTP VM. EDIFACT is a fourth format behind a flag, on in dev and off in prod [9]. The service parses, maps and validates each file, then publishes canonical records to `create_record_request` [3].
- **Five record types in.** Purchase order, sales order, master data, return goods authorization and work order [3].
- **Outbound.** It consumes seven confirmation types plus stock adjustments. It writes a file per customer connector, then publishes `confirmation_made` or `stock_adjustment_made` [4][6].
- **EDIFACT out.** A connector set to `egressFiletype: "edi"` gets one message per file: RECADV, DESADV, OSTRPT or INVRPT. Returns go out as RECADV unless the mapping asks for INVRPT [5][12].
- **File lifecycle.** It moves acknowledged inputs to `archive/` and failed inputs to `error/`.
- **SFTP estate.** It owns the VM, the logins and the SSH keys [1]. A connector in `pending` state triggers user provisioning [11].

## Why it exists separately

It carries the whole SFTP surface: a VM customers log into, per-user directories, key management and file-format translation. None of that belongs in a service that speaks Pub/Sub and HTTP. The rest of the pipeline never learns that files exist.

The VM plus gcsfuse design is deliberate. Customers insist on plain SFTP, and gcsfuse makes everything downstream GCS-native [13]. Do not replace it with a managed transfer service.

## Neighbours

```orient-flow
{ "v": 1, "title": "sftp-connector in context",
  "nodes": [
    { "id": "inb", "label": "Customer uploads", "sub": "to_ilg, one GCS bucket", "kind": "store", "ev": [2] },
    { "id": "s", "label": "sftp-connector", "sub": "Cloud Run + SFTP VM", "kind": "service", "service": "sftp-connector", "tone": "accent", "ev": [3] },
    { "id": "req", "label": "create_record_request", "kind": "topic", "ev": [6] },
    { "id": "d", "label": "dedupe-service", "sub": "gate", "kind": "service", "service": "dedupe-service", "ev": [8] },
    { "id": "p", "label": "snap-queue-polling-service", "sub": "polls SNAP", "kind": "service", "service": "snap-queue-polling-service", "ev": [8] },
    { "id": "rdy", "label": "confirmation_ready", "sub": "7 filtered subscriptions", "kind": "topic", "ev": [10] },
    { "id": "out", "label": "Confirmation files", "sub": "from_ilg, same bucket", "kind": "store", "ev": [4] },
    { "id": "mad", "label": "confirmation_made", "sub": "collector, replay-service", "kind": "topic", "ev": [8] },
    { "id": "cs", "label": "config-service", "sub": "config + mappings", "kind": "service", "service": "config-service", "ev": [11] }
  ],
  "edges": [
    { "from": "inb", "to": "s", "label": "new_file push" },
    { "from": "s", "to": "req" },
    { "from": "req", "to": "d" },
    { "from": "p", "to": "rdy" },
    { "from": "rdy", "to": "s", "label": "push" },
    { "from": "s", "to": "out", "label": "write file" },
    { "from": "s", "to": "mad", "label": "after delivery" },
    { "from": "cs", "to": "s", "label": "config, revisions", "style": "dashed" }
  ] }
```

Upstream, customers upload through the bucket and the poller publishes `confirmation_ready`. Downstream, dedupe-service gates `create_record_request`, and collector and replay-service consume `confirmation_made` [8]. config-service supplies connector and mapping config. It also receives each new SFTP keypair on `customer_creation` [8].

## Where the reference lives

`CLAUDE.md` in the repo root owns four rules in detail [7]:

- The `users.json` record format and its three-field trap.
- Log redaction by the observability SDK, never a hand-rolled masker.
- The join of a confirmation's parallel arrays, and why it lives here and not in snap-adapter.
- The ack rule: every confirmation reaches a file or becomes a recorded failure, and a retry budget bounds redelivery.

[[architecture]] holds the routes, subscriptions, egress and runtime. [[known-context]] holds what source cannot say.

Do not trust the `12 subs` note in `waypoint.yaml`. `pubsub.tf` declares 14 subscriptions [10].

## What deliberately isn't here

- **Dedupe or gating.** dedupe-service decides what passes.
- **WMS knowledge.** Nothing here knows SnapFulfil exists. snap-queue-polling-service and snap-adapter own it.
- **Mapping rules as code.** config-service holds `CONNECTOR_MAPPING`. This service applies it through `@gfs-bifrost/rules-engine`, on egress too. The config is the customer contract.
- **EDIFACT parsing and serialising.** `@gfs-bifrost/edi` owns both. This service picks the message type, flattens or assembles around it, and reads or writes the file.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "iac/projects/bifrost-sftp-connector/compute.tf@a8d34bf" },
  { "id": 2, "kind": "code", "ref": "iac/projects/bifrost-sftp-connector/storage.tf@a8d34bf" },
  { "id": 3, "kind": "code", "ref": "code/src/controllers/pubsub.controller.ts@a8d34bf" },
  { "id": 4, "kind": "code", "ref": "code/src/confirmations/confirmation-egress.service.ts@a8d34bf" },
  { "id": 5, "kind": "code", "ref": "code/src/confirmations/edi/message-table.ts@a8d34bf" },
  { "id": 6, "kind": "code", "ref": "code/src/pubsub/pubsub.router.ts@a8d34bf" },
  { "id": 7, "kind": "code", "ref": "CLAUDE.md@a8d34bf" },
  { "id": 8, "kind": "doc", "ref": "fuse://pubsub-topology", "note": "publishers and subscribers of the topics drawn" },
  { "id": 9, "kind": "code", "ref": "iac/env/prod.tfvars@a8d34bf" },
  { "id": 10, "kind": "code", "ref": "iac/projects/bifrost-sftp-connector/pubsub.tf@a8d34bf" },
  { "id": 11, "kind": "code", "ref": "code/src/config/config-handlers/connector/connector.config-handler.ts@a8d34bf" },
  { "id": 12, "kind": "code", "ref": "code/src/confirmations/edi/build-edi-files.ts@a8d34bf" },
  { "id": 13, "kind": "doc", "ref": "Engineering/sftp-connector/known-context.md", "note": "owner interview 2026-08-24" }
] }
```
