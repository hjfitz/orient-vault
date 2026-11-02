---
tags:
- waypoint
- sftp-connector
verified: '2026-10-14'
verified_sha: 4e1593e
verified_paths:
- code/src
- iac
- CLAUDE.md
title: sftp-connector — architecture
thesis: An Express app on Cloud Run beside an SFTP VM turns bucket files into canonical
  records and confirmation events into mapped CSV, JSONL or EDIFACT files, acking
  a push only once the work is done or its failure is recorded.
confidence: high
---
# sftp-connector — architecture

```orient-bluf
{ "v": 1, "bluf": "An Express app on Cloud Run beside an SFTP VM turns bucket files into canonical records and confirmation events into mapped CSV, JSONL or EDIFACT files, acking a push only once the work is done or its failure is recorded.", "confidence": "high", "action": "Keep every users.json record three-field, and ack a confirmation only after it is written or its failure is published." }
```

## Guardrails
<!-- Max ~6, promoted out of known-context.md prose so a tool can push them at you BEFORE the
     mistake. `wp context --paths <what you are touching>` prints only the ones on those paths;
     `wp signoff` names any the diff touches. Prune before adding.
     kind: contract | policy | operational | technical -->

- [technical:G1] A `users.json` record missing `raw_username` makes the connector reject the
  **entire** file on the next user creation, blocking **all** SFTP onboarding (caused FUSE-976).
  — paths: apps/connector/src/core/sftp-user-builder
- [technical:G2] Concurrent instances append to one shared egress window object per customer.
  Generation preconditions and retries are the mitigation, not a guarantee — overwrites have
  happened. — paths: apps/connector/src/confirmations, apps/connector/src/gcs/storage.service.ts
- [contract:G3] Confirmation file formats are contractual per customer but expressed as
  per-business config. The config **is** the contract: a mapping edit is a customer-visible
  release with no code diff to review. — paths: apps/connector/src/confirmations, apps/connector/src/import
- [policy:G4] `/debug` is mounted in every environment with no env guard. This is known and
  accepted (`run.invoker` is restricted) — don't file it, don't remove the mount without asking.
  — paths: apps/connector/src/controllers/debug.controller.ts, apps/connector/src/app.ts
- [operational:G5] The VM is a live single point of failure and its recovery path is untested;
  there is no runbook. It stays true until the Plan B/C cut onto the multi-zone host; the cut
  script's rollback is the runbook. — paths: iac/projects/bifrost-sftp-connector
- [contract:G6] Customers connect to the SFTP **IP literal**, not the DNS name: config-service stamps
  `SFTP_DEFAULT_HOST` into every SFTP connector's `config.host` and fuse-ui prints it. Any endpoint
  change (load balancer, new host) must keep the static IP. — paths: iac/projects/bifrost-sftp-connector, iac/projects/sftp-host

## Ingress

```orient-flow
{ "v": 1, "title": "Inbound: file in, record out",
  "nodes": [
    { "id": "cust", "label": "Customer SFTP client", "kind": "external" },
    { "id": "vm", "label": "SFTP VM", "sub": "to_ilg, gcsfuse bind mounts", "kind": "step", "ev": [4, 5] },
    { "id": "b", "label": "GCS bucket", "sub": "versioned, EU", "kind": "store", "ev": [3] },
    { "id": "nf", "label": "new_file", "sub": "OBJECT_FINALIZE", "kind": "topic", "ev": [3] },
    { "id": "cr", "label": "sftp-connector", "sub": "Cloud Run, /events/v1/file", "kind": "service", "service": "sftp-connector", "tone": "accent", "ev": [1, 9] },
    { "id": "req", "label": "create_record_request", "sub": "attributes.recordType", "kind": "topic", "ev": [22] },
    { "id": "d", "label": "dedupe-service", "sub": "then snap-adapter", "kind": "service", "service": "dedupe-service", "ev": [29] },
    { "id": "fail", "label": "create_data_failure", "sub": "row and file failures", "kind": "topic", "ev": [9] },
    { "id": "cs", "label": "config-service", "sub": "mappings, connectors", "kind": "service", "service": "config-service", "ev": [27] }
  ],
  "edges": [
    { "from": "cust", "to": "vm", "label": "upload, port 22" },
    { "from": "vm", "to": "b" },
    { "from": "b", "to": "nf" },
    { "from": "nf", "to": "cr", "label": "push" },
    { "from": "cr", "to": "req", "label": "valid records" },
    { "from": "req", "to": "d" },
    { "from": "cr", "to": "fail", "label": "invalid rows, bad files" },
    { "from": "cs", "to": "cr", "label": "config API + cache", "style": "dashed" }
  ] }
```

The VM bind-mounts each user's `to_ilg` and `from_ilg` directories from the bucket through gcsfuse [5]. A bucket notification publishes every finalised object to `new_file` [3].

1. `POST /events/v1/file` receives the push. Its subscription has a 600 s ack deadline [1]. The handler acks 200 and ignores a directory placeholder, a support-log object, anything outside `<user>/to_ilg/<action>/<file>`, an unknown action directory and an unaccepted extension [9][10]. **ASSESSED** `cloud-run.tf` sets no request timeout, so the platform default of 300 s applies, below the ack deadline [2].
2. The handler downloads and parses the file [9]:
   - CSV uses `csv-parser` with trimmed headers and values. Rows whose every value is empty are dropped, because a delimiter-only line maps to nothing [33].
   - JSON and JSONL parse one `JSON.parse` per line. A line that is not a JSON object falls back to parsing the whole document as an array or object [34].
   - EDIFACT normalises through `@gfs-bifrost/edi` (below) [11].
3. `TranslatorRouter` picks the translator for the action directory: purchase order, sales order, master data, return goods authorization or work order. It applies the business's `CONNECTOR_MAPPING` rules and any mapping dictionaries through `@gfs-bifrost/rules-engine`, then validates against the canonical schema [12].
4. Only sales orders take business rules afterwards: DDP rules set `financial.dutyPaid`, and warehouse routing merges into `identifiers` [12][36].
5. Each valid record publishes to `create_record_request` as its own message. It carries `attributes.recordType`, `metadata.source = "sftp"`, the origin `connectorId` and `metadata.capture`, an `SftpCapture` that points at the GCS object and never holds the bytes [9][22].
6. Each row that fails validation publishes its own `create_data_failure` with the same capture. A file that fails before row validation publishes one file-level failure, then rethrows. A failed failure-publish is logged and counted, never thrown [9].
7. The handler builds the capture before the first fallible call. A file whose connector cannot be resolved has no business to attribute a failure to, so the handler moves it straight to `error/` [9].
8. The handler acks at the end, so a crash mid-file redelivers. `errors.ts` answers 204 for file-type, file-not-found, no-connector, no-mapping-rules and validation errors. Any other error answers 500 and redelivers [24].

### EDIFACT ingest

The action directory fixes the accepted message types: `create_sales_order` takes INSDES, `create_master_data` PRICAT, `create_purchase_order` ORDERS or DESADV, and `create_work_order` DESADV [11]. A single-type directory hands its type to the normaliser, which throws on a disagreeing UNH. A multi-type directory reads the UNH first. A file with no UNH fails, and a type outside the set fails as a misroute.

The intermediary flattens to dotted-key string rows, one per `lines[]` element with the header repeated, so the CSV translators and mappings apply unchanged [11]. Whether a DESADV is an ASN or a kitting instruction is the directory plus the mapping, never code.

`FEATURE_FLAG_EDI` is true in dev and prod [7][32]. With it off, `isFileTypeAccepted` rejects `.edi` as an invalid file type, although `ACCEPTED_FILE_TYPES` still lists it [2][10].

## Egress

```orient-flow
{ "v": 1, "title": "Outbound: confirmation back to the customer",
  "nodes": [
    { "id": "p", "label": "snap-queue-polling-service", "sub": "polls SNAP outbound queue", "kind": "service", "service": "snap-queue-polling-service", "ev": [29] },
    { "id": "rdy", "label": "confirmation_ready", "sub": "7 subscriptions, sftp or broadcast", "kind": "topic", "ev": [1] },
    { "id": "sar", "label": "stock_adjustment_ready", "kind": "topic", "ev": [1] },
    { "id": "cr", "label": "sftp-connector", "sub": "Cloud Run", "kind": "service", "service": "sftp-connector", "tone": "accent", "ev": [13, 16] },
    { "id": "b", "label": "GCS bucket", "sub": "window object or create-only .edi", "kind": "store", "ev": [10] },
    { "id": "vm", "label": "SFTP VM", "sub": "from_ilg, gcsfuse mounts", "kind": "step", "ev": [5] },
    { "id": "cust", "label": "Customer SFTP client", "kind": "external" },
    { "id": "made", "label": "confirmation_made", "sub": "collector, replay-service", "kind": "topic", "ev": [22, 29] },
    { "id": "cdf", "label": "confirmation_data_failure", "sub": "replay-service, collector", "kind": "topic", "tone": "alert", "ev": [13, 29] }
  ],
  "edges": [
    { "from": "p", "to": "rdy" },
    { "from": "p", "to": "sar" },
    { "from": "rdy", "to": "cr", "label": "push" },
    { "from": "sar", "to": "cr", "label": "push" },
    { "from": "cr", "to": "b", "label": "write per connector" },
    { "from": "b", "to": "vm" },
    { "from": "vm", "to": "cust", "label": "collect" },
    { "from": "cr", "to": "made", "label": "after delivery" },
    { "from": "cr", "to": "cdf", "label": "any undelivered leg", "style": "dashed" }
  ] }
```

Each `confirmation_ready` subscription filters on one `recordType` and on `attributes.source = "sftp" OR attributes.broadcast = "true"`: this channel's own confirmations plus broadcasts [1]. `POST /events/v1/confirmation/ready/:recordType` decodes each record against its canonical schema [13][21]:

| Confirmation type | Ready `recordType` | Use case (mapping key) | EDIFACT message | Default `from_ilg` directory |
| --- | --- | --- | --- | --- |
| `purchase_order` | `purchase_order` or `goods_in_confirmation` | `goods_in_confirmation` | RECADV | `purchase_order_confirmations` |
| `sales_order` | `goods_out_confirmation` | `goods_out_confirmation` | DESADV, parcels split first | `sales_order_confirmations` |
| `return_goods_authorization` | `return_goods_authorization` | `return_goods_confirmation` | RECADV, or INVRPT by mapping | `return_goods_authorization_confirmations` |
| `pick_confirmation` | `pick_confirmation` | `pick_confirmation` | OSTRPT | `pick_confirmation_confirmations` |
| `pack_confirmation` | `pack_confirmation` | `pack_confirmation` | DESADV | `pack_confirmation_confirmations` |
| `finished_good_receipt` | `finished_good_receipt` | `finished_good_receipt` | RECADV | the connector's `finishedGoodReceiptEgressDirectory`, else `finished_good_receipt_confirmations` |
| `work_order_confirmation` | `work_order_confirmation` | `work_order_confirmation` | INVRPT, component lines only | `work_order_confirmation_confirmations` |

`types/confirmations/operations.ts` is the registry, and `confirmations/edi/message-table.ts` holds the message column [14][21]. After a write, goods-in and goods-out publish `goods_in_confirmation` and `goods_out_confirmation` as the made `recordType`. The other five keep their own name [21].

**Window files.** A CSV or JSONL confirmation does not get a file of its own. It appends to one shared window object per username, egress directory and minute, named `<yyyy-LL-dd-HHmm>-confirmation.<ext>` [38].

- Several Cloud Run instances write the same object. The upsert reads the object, drops incoming rows already present as exact lines, appends the rest, and saves under an `ifGenerationMatch` precondition [10].
- A 412 retries up to five attempts and counts `egress.window_write.retry`. A redelivery that adds no rows skips the write [10].
- Only a 404 starts a new window. Any other read failure throws, so a transient error cannot replace the window with the incoming rows alone [10].

**Mapping.** `feature_flag_use_dynamic_confirmation_mapping` is true in dev and prod [7][32]. The live path serialises each record through the connector's own `CONNECTOR_MAPPING` for that use case in `core/confirmation-transformer.ts`, with its `columnOrder` and egress filetype [13]. Hardcoded transformers remain only for `purchase_order` and `sales_order`. With the flag off, every other type writes nothing [13][37].

**Targets.** A connector receives a file only when it is `ACTIVE`, has an SFTP username, and its use-case mapping is `ACTIVE` with rules that resolve [13]. Each rejecting gate counts `CONFIRMATION_METRIC.UNROUTABLE` with a `reason`. **ASSESSED** The code never reads the connector-level `confirmationsEnabled` flag. The recorded reason is that prod connector documents lack it, so a fail-closed read would silence live customers. The code shows only the missing read.

`getConnectorUseCaseMapping` returns `null` for a 404 or an absent use case. Any other non-2xx throws, so a 401, 403 or 429 never reads as "use case not present" [27].

### EDIFACT egress

A connector with `egressFiletype: "edi"` gets one EDIFACT message per file instead of a window object [13].

- **Gates.** It needs `FEATURE_FLAG_EDI`, dynamic mapping, a type in the message table and an `ediEnvelope` on the connector. Otherwise the connector is skipped with a matching `edi_*` unroutable reason [13].
- **Build.** The connector's mapping produces the message. `mappingIssues` rejects a mapping of the wrong shape, or one that writes a line field on the header [40]. `serializeInterchange` wraps the message in a UNB interchange from the `ediEnvelope` [15].
- **Returns.** A return is a RECADV by default, with `identifiers.id` as the document reference. A constant `messageType` header rule of `INVRPT` on the returns mapping switches it to an INVRPT return adjustment. The partner chooses, so the choice is config. Any `messageType` outside a record type's allowed set fails as `invalid_mapping` [14][15].
- **Codes.** The `codes.*` and `unh.*` header rules carry each partner's codes. **ASSESSED** A mandatory SSCC applies only when the mapping sets the DESADV `requireSscc` flag, and a missing batch omits `GIN+BX`. The schema declares the flag [15]; the serialiser that reads it lives in `@gfs-bifrost/edi`.
- **Shape.** A `lines` mapping makes one message per confirmation. The `simple` stock adjustment mapping groups records by `identifiers.id` [15]. Work-order confirmations send component lines only, because the finished-good receipt books the finished goods [14].
- **Name.** `<TYPE>_<docRef>_<ctrlRef>.edi`. The control reference is 14 hex characters of a SHA-256 over connector, record type, document reference and queue ids, so a redelivery reuses its file name and interchange reference [15].
- **Write.** `createFile` saves with generation 0, so an existing file reports `exists` and is not rewritten [10]. The bucket keeps object versions, so a resend after the customer collected and deleted the file writes it again under the same control reference [3]. **ASSESSED** The receiver's duplicate-interchange check is then the only backstop.
- **Failure.** A message the mapping cannot produce is a `write_failed` for that connector alone, whatever the reason: `invalid_mapping`, `invalid_message` or `unsupported_type`. Every other target still writes [13][15].

### Stock adjustments

Stock adjustments take their own route, `/events/v1/confirmation/ready/stock_adjustment`, from `stock_adjustment_ready` [1][9]. The controller validates the whole bulk envelope, so one bad record rejects the batch with nothing written [9]. The service writes one file per username per hour under `stock_adjustment_confirmations/`, named `<yyyy-LL-dd-HH>-confirmation.<ext>` [16][39].

- A mapping with rules writes mapped CSV or JSONL, or EDIFACT INVRPT with `edi`. A mapping without rules keeps the fixed columns [16].
- A connector whose use case cannot be read (`ConfigApiException`) is skipped as `use_case_lookup_failed` [16].
- The service never checks the connector's `isActive`, only its username and the mapping status [16].
- `stock_adjustment_made` publishes after the write, but not after an invalid EDI message. Withholding it no longer causes a re-announce: the poller clears every published row off SNAP's outbound queue itself (see Delivery contract). An invalid stock-adjustment INVRPT is lost, leaving only an `EdiMessageInvalid` log and a `fuse.confirmation.forward_failure{type:stock_adjustment}` count. No file and no failure record are written (snapshot 2026-10-19) [16].
- The subscription has no retry policy and no retry budget [1].

### Delivery contract

Every confirmation is delivered or recorded on `confirmation_data_failure` before the push acks, because an ack with neither is a lost confirmation once the poller clears the SNAP rows [23]. A recorded failure still acks, since a nack would redeliver and duplicate files. A record that fails its canonical schema is split off and published as a validation failure while the valid records still write [13].

A confirmation is **routed** when its metadata names a `connectorId` and it is not a broadcast. Target selection then narrows to that connector within the business's own connectors [13]. A broadcast, or a confirmation with no origin, **fans out** to every eligible connector.

- **Routed.** A connector that is not the business's, a gate rejection, a lookup error or a write failure is recorded against the named connector [13][23].
- **Fan-out.** The use case is read before any gate. A connector without it is benign (`use_case_not_configured`, nothing recorded). A connector with it that is not delivered is a failed leg, with its own failure carrying its `connectorId`, so replay redrives that connector only. One failing leg does not stop the others [13].
- **Made event.** `confirmation_made` publishes first when any leg delivered. A routed publish failure becomes a `write_failed` leg. A fan-out one throws `ConfirmationMadeNotRecordedException` and redelivers, so files are re-written: duplicates are accepted over loss [13][23].
- **Connectors unreadable.** One retryable `dependency` failure per record goes out with no `connectorId`, so a redrive reaches every SFTP connector [13].
- **Failure not recorded.** `ConfirmationFailureNotRecordedException` is deliberately unmapped, so it answers 500 and redelivers [13][24].

**Retry budget.** The seven `confirmation_ready` subscriptions back off 10 s to 600 s and carry a dead-letter policy of 10 attempts. The policy exists only so Pub/Sub sends `deliveryAttempt` [1]. **ASSESSED** Nothing in this stack grants the dead-letter topic any IAM, and bifrost-pubsub owns the topic, so nothing is forwarded. At attempt 10, `confirmationsHandler` records an error that would otherwise answer 5xx as a retryable `redelivery_exhausted` failure per record, then acks. If that publish fails, the push still nacks [9]. `MAX_TRANSIENT_DELIVERY_ATTEMPTS` in `pubsub.controller.ts` and `confirmation_ready_delivery_attempts` in `pubsub.tf` must stay equal.

### Companion arrays

A confirmation carries `lines[]`, `consignments[]`, `despatches[]` and `packages[]`, independently sized and ordered. `core/confirmation-transformer.ts` emits one row per driver-array element and joins a second array by index only when the lengths match. Otherwise it blanks the columns and logs [23].

Goods-out is the exception. `confirmations/goods-out-parcels.ts` splits a confirmation into one record per parcel before either egress path sees it, joining on SKU for the line and STU for the despatch [23]. `CLAUDE.md` holds the reasoning, including why the join lives here and not in snap-adapter.

## File routing

```orient-flow
{ "v": 1, "title": "File routing: acknowledge or fail",
  "nodes": [
    { "id": "sa", "label": "snap-adapter", "sub": "WMS accept or reject", "kind": "service", "service": "snap-adapter", "ev": [29] },
    { "id": "ack", "label": "create_acknowledge", "sub": "unfiltered", "kind": "topic", "ev": [1] },
    { "id": "fail", "label": "create_data_failure", "sub": "unfiltered", "kind": "topic", "ev": [1] },
    { "id": "cr", "label": "sftp-connector", "service": "sftp-connector", "tone": "accent", "kind": "service", "ev": [17] },
    { "id": "r", "label": "Redis claim", "sub": "SET NX, 120 s pending", "kind": "store", "ev": [17] },
    { "id": "b", "label": "archive/ or error/", "sub": "beside the original path", "kind": "store", "ev": [17] }
  ],
  "edges": [
    { "from": "sa", "to": "ack", "label": "accepted" },
    { "from": "sa", "to": "fail", "label": "rejected" },
    { "from": "ack", "to": "cr", "label": "push" },
    { "from": "fail", "to": "cr", "label": "push" },
    { "from": "cr", "to": "r", "label": "claim once" },
    { "from": "cr", "to": "b", "label": "guarded move" }
  ] }
```

`core/file-routing` moves a processed object into an `archive/` or `error/` segment beside its original path [17]. `create_acknowledge` archives, and `create_data_failure` moves to `error/`. This service's own ingest failures publish to `create_data_failure` too [9]. Both subscriptions are unfiltered, because this service consumes every ingress type and `metadata.capture` discriminates in code [1]. Both routes act only when the capture is an SFTP capture, points at GCS and names this bucket [17].

- A Redis claim (`SET NX`, 120 s pending TTL, then a `done` marker) makes each move run once per file and correlation id. With Redis down, the claim fails open and the move runs unclaimed [17].
- A move is guarded by the object's generation. It stamps `fuseCorrelationId` on the destination and skips when a newer upload has replaced the file [17].
- `error/` is sticky. A failure escalates an already archived copy of the same upload, and a later acknowledge never downgrades it [17].
- A third push route, `entity_error`, writes snap-adapter's record errors to a support CSV in the bucket. Ingest ignores that prefix [9][10].

## SFTP user creation

A connector config revision that carries a CONNECTOR backlink with `isActive = PENDING` publishes `create_sftp_user` to this service's own topic [19]. `provisionIfPending` runs first, so a failed connector read fails the event and retries. The push then reaches `core/sftp-user-builder` [9][18].

1. The builder derives the login: `FUSE_` plus 10 uppercase hex characters of the connector id's SHA-256. The name `support` is excluded [18].
2. It reuses the connector's keypair when both keys exist, else generates one in `core/crypto-module` [18].
3. It SSHes onto the VM with the admin key (`adapters/ssh-adapter`) to create the OS user in `sftpgroup`, write `authorized_keys` with `tee` (one key, overwriting), and bind-mount the user's `to_ilg` and `from_ilg` directories [18].
4. It upserts a record into `users.json` in the bucket and awaits the write, so a failed write fails provisioning instead of reporting the user active. The whole file is schema-validated on every read and write [18].
5. It publishes the result and keypair to `customer_creation`, which config-service consumes [9][29].

Provisioning creates only five `from_ilg` directories: master data, sales order, purchase order, work order and finished-good receipt. Pick, pack, return and stock adjustment directories appear on first write, because gcsfuse mounts with `--implicit-dirs` [5][35].

## Modules

| Path | Role |
| --- | --- |
| `controllers/` | `pubsub.controller.ts` (every push route), `debug.controller.ts`, `health.controller.ts` |
| `import/` | parse (`csv`, JSONL, EDIFACT) and `translators/` per record type |
| `confirmations/` | egress target selection, per-type decode, goods-out parcel split, legacy transformers, failure mapping (`to-confirmation-failure.ts`), stock adjustment egress |
| `confirmations/edi/` | EDIFACT egress: record-to-message table, mapping application, interchange assembly |
| `core/confirmation-transformer` | canonical to mapped CSV or JSONL rows, column ordering |
| `rules/rule-manager` | one manager per record type: mapping rules, plus DDP and warehouse routing for sales orders |
| `config/` | config-service client, Redis-backed handlers for connector, `mapping_rules`, `warehouse-routing` and `ddp-rules` |
| `pubsub/` | router: topic registrations per action and confirmation type |
| `core/file-routing` | archive and error placement |
| `core/sftp-user-builder`, `core/crypto-module`, `adapters/ssh-adapter` | SFTP user lifecycle |
| `gcs/` | storage service: window upsert, create-only writes, generation-pinned moves |

## Runtime

- **Cloud Run.** An Express 4 app, not Nest [8][25]. One container at 1 vCPU and 1 Gi, plus a Datadog `serverless-init` sidecar at 500m and 256 Mi that dual-ships logs and metrics. Egress to Redis goes over Direct VPC and everything else over the public path [2]. **ASSESSED** No scaling block is set, so Cloud Run's default instance and concurrency limits apply [2].
- **Invocation.** `ingress` is `INGRESS_TRAFFIC_ALL`, and `run.invoker` is bound only to the `pubsub_handler_invoker` service account [2][6]. The app verifies no token itself. `/debug` mounts in every environment with no guard [8].
- **VM.** An `e2-small` Debian 12 instance with a static IP, a firewall rule for tcp/22 from anywhere, and a DNS A record in the ilg-platform zone [4][31]. Its startup script installs gcsfuse and writes `sync_users.sh`, which re-mounts the bucket at `/mnt/gcs_root` and rebuilds every user's keys and bind mounts from `users.json` [5].
- **SSH exposure.** **ASSESSED** The repo configures no chroot, `ForceCommand` or `Match` block. The startup script resets `sshd_config` to the Debian package default, users get `/bin/bash`, and the gcsfuse mount is mode 770 for `sftpgroup`, which every customer joins. The VM service account also holds `objectAdmin` on the bucket [4][5][6][18]. If the package default applies, a customer login can read other customers' directories. Check the live VM.
- **Bucket.** EU, versioned, `force_destroy = true`, with an `OBJECT_FINALIZE` notification only [3].
- **Redis.** Memorystore caches connector and mapping config through `@gfs-bifrost/cache`, with a 600 s network TTL and a 30 s in-memory TTL [2]. A `CONNECTOR_MAPPING` revision rewrites the fragment and deletes `mapping_rules:{username}|{useCase}` for purchase order, sales order, master data and work order [20]. There is no database: GCS is the only durable store this service owns.
- **Secrets.** The config-service key comes from Secret Manager. `SFTP_ADMIN_PRIVATE_KEY` is a plain Cloud Run env var from a Terraform-generated key [2][30].
- **Switches.** `FEATURE_FLAG_EDI` and `FEATURE_FLAG_USE_DYNAMIC_CONFIRMATION_MAPPING` come from `iac/env/*.tfvars` [7][26][32]. Terraform also sets `USE_LEGACY_DDP_RULES` and `USE_LEGACY_MAPPING_RULES`, which no source file reads [2][26].
- **Shutdown.** On SIGTERM the service stops new pushes, lets in-flight handlers ack, then flushes the Datadog sink inside 8 s, before Cloud Run's SIGKILL [28].

### Known gaps

- **RGA mapping cache.** The invalidation list omits `return_goods_authorization`, yet ingest caches that mapping under the same key pattern. After an edit, RGA ingest serves the old mapping until the cache TTL expires [12][20][37].
- **`users.json` upload.** `updateUsersJson` does not await the upload. A failed upload surfaces only as an unhandled rejection, and provisioning still reports success. The read-modify-write has no generation precondition [18].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "iac/projects/bifrost-sftp-connector/pubsub.tf@a8d34bf" },
  { "id": 2, "kind": "code", "ref": "iac/projects/bifrost-sftp-connector/cloud-run.tf@a8d34bf" },
  { "id": 3, "kind": "code", "ref": "iac/projects/bifrost-sftp-connector/storage.tf@a8d34bf" },
  { "id": 4, "kind": "code", "ref": "iac/projects/bifrost-sftp-connector/compute.tf@a8d34bf" },
  { "id": 5, "kind": "code", "ref": "iac/projects/bifrost-sftp-connector/scripts/startup.sh.tpl@a8d34bf" },
  { "id": 6, "kind": "code", "ref": "iac/projects/bifrost-sftp-connector/iam.tf@a8d34bf" },
  { "id": 7, "kind": "code", "ref": "iac/env/prod.tfvars@a8d34bf" },
  { "id": 8, "kind": "code", "ref": "code/src/app.ts@a8d34bf" },
  { "id": 9, "kind": "code", "ref": "code/src/controllers/pubsub.controller.ts@a8d34bf" },
  { "id": 10, "kind": "code", "ref": "code/src/gcs/storage.service.ts@a8d34bf" },
  { "id": 11, "kind": "code", "ref": "code/src/import/csv/edi-to-json.ts@a8d34bf" },
  { "id": 12, "kind": "code", "ref": "code/src/import/translators/router.ts@a8d34bf" },
  { "id": 13, "kind": "code", "ref": "code/src/confirmations/confirmation-egress.service.ts@a8d34bf" },
  { "id": 14, "kind": "code", "ref": "code/src/confirmations/edi/message-table.ts@a8d34bf" },
  { "id": 15, "kind": "code", "ref": "code/src/confirmations/edi/build-edi-files.ts@a8d34bf" },
  { "id": 16, "kind": "code", "ref": "code/src/confirmations/stock-adjustment.service.ts@a8d34bf" },
  { "id": 17, "kind": "code", "ref": "code/src/core/file-routing/file-routing.service.ts@a8d34bf" },
  { "id": 18, "kind": "code", "ref": "code/src/core/sftp-user-builder/sftp-user.builder.ts@a8d34bf" },
  { "id": 19, "kind": "code", "ref": "code/src/config/config-handlers/connector/connector.config-handler.ts@a8d34bf" },
  { "id": 20, "kind": "code", "ref": "code/src/config/bifrost.config.service.ts@a8d34bf" },
  { "id": 21, "kind": "code", "ref": "code/src/types/confirmations/operations.ts@a8d34bf" },
  { "id": 22, "kind": "code", "ref": "code/src/pubsub/pubsub.router.ts@a8d34bf" },
  { "id": 23, "kind": "code", "ref": "CLAUDE.md@a8d34bf" },
  { "id": 24, "kind": "code", "ref": "code/src/errors.ts@a8d34bf" },
  { "id": 25, "kind": "code", "ref": "code/package.json@a8d34bf" },
  { "id": 26, "kind": "code", "ref": "code/src/app-config/config.ts@a8d34bf" },
  { "id": 27, "kind": "code", "ref": "code/src/config/config.api.ts@a8d34bf" },
  { "id": 28, "kind": "code", "ref": "code/src/index.ts@a8d34bf" },
  { "id": 29, "kind": "doc", "ref": "fuse://pubsub-topology", "note": "publishers and subscribers of the topics drawn" },
  { "id": 30, "kind": "code", "ref": "iac/projects/bifrost-sftp-connector/keys.tf@a8d34bf" },
  { "id": 31, "kind": "code", "ref": "iac/projects/bifrost-sftp-connector/dns.tf@a8d34bf" },
  { "id": 32, "kind": "code", "ref": "iac/env/dev.tfvars@a8d34bf" },
  { "id": 33, "kind": "code", "ref": "code/src/import/csv/csv-to-json.ts@a8d34bf" },
  { "id": 34, "kind": "code", "ref": "code/src/import/csv/json-lines-to-json.ts@a8d34bf" },
  { "id": 35, "kind": "code", "ref": "code/src/core/sftp-user-builder/constants.ts@a8d34bf" },
  { "id": 36, "kind": "code", "ref": "code/src/import/translators/sales-order.translator.ts@a8d34bf" },
  { "id": 37, "kind": "code", "ref": "code/src/factory.ts@a8d34bf" },
  { "id": 38, "kind": "code", "ref": "code/src/confirmations/confirmations.service.ts@a8d34bf" },
  { "id": 39, "kind": "code", "ref": "code/src/confirmations/stock-adjustment.transformer.ts@a8d34bf" },
  { "id": 40, "kind": "code", "ref": "code/src/confirmations/edi/apply-mapping.ts@a8d34bf" }
] }
```
