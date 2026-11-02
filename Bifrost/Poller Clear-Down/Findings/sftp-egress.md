# sftp-egress — sftp-connector confirmation egress vs "consume SNAP row on find"

Refs read (2026-09-29): sftp-connector@origin/master f6a15e3 ; bifrost-pubsub@origin/master cd25f95 ;
collector@origin/master f19ce57 ; replay-service@origin/main d75997f. Vault: Engineering/sftp-connector
(known-context, operations, architecture; verified 2026-09-02, sha 40ef25a - read as leads only) and memory notes
reference_sftp_triage_gotchas / reference_confirmation_gating_switches_map.
All line refs below are sftp-connector@f6a15e3 unless stated.

## 1. Flow as it is in code

Subscriptions (iac/projects/bifrost-sftp-connector/pubsub.tf), all push, OIDC, Cloud Run `.../events/v1/confirmation/ready/<recordType>`:
- confirmation_ready cross-entity topic, one sub per type, each with `filter` on attributes.recordType:
  RGA (no channel clause), pick, pack, FGR, WOC, PO (`purchase_order` OR `goods_in_confirmation`), SO (`goods_out_confirmation`);
  all except RGA also AND `(attributes.source = "sftp" OR attributes.broadcast = "true")` (pubsub.tf local channel_filter).
- stock_adjustment_ready: own topic, no filter -> `/events/v1/confirmation/ready/stock_adjustment` (dedicated handler).
- ack_deadline_seconds = 20 on all of them. NO retry_policy, NO dead_letter_policy, NO message_retention_duration
  (=> Pub/Sub defaults: immediate-ish redelivery on nack, 7-day retention) on any confirmation_ready / stock_adjustment_ready sub.
  (create_sftp_user + config_revision subs have DLTs; the confirmation subs do not, even though the topic module creates a `.dlt` topic
  - bifrost-pubsub iac/modules/topic/main.tf.)
- Cloud Run: 1 CPU / 1Gi, no explicit min/max instance settings found in cloud-run.tf. No in-memory buffer or queue anywhere in the egress path.

Handler: controllers/pubsub.controller.ts `confirmationsHandler` (route `:recordType`):
1. `isConfirmationType` else 404 (unreachable from IaC - every endpoint is a literal valid type).
2. `pubsubService.ingestEvent(body, BifrostBulkMessageSchema(z.record))` - envelope + bulk shape only.
3. `broadcast` = attributes.broadcast === "true"; then `ConfirmationEgressService.process(type, records, metadata, broadcast)`; always `204` on return.

`process()` (confirmations/confirmation-egress.service.ts:112-240):
- logs ConfirmationReceived (order refs) before any skip (l.120).
- `decodeConfirmations` per-record Zod against the canonical schema -> `{valid, invalid}` (confirmations.service.ts:114).
- legacy path only when `feature_flag_use_dynamic_confirmation_mapping=false`: only purchase_order/sales_order have registered transformers (factory.ts:475). Flag is true in dev+prod tfvars => legacy is a kill-switch; if flipped, other 5 types return with `UNSUPPORTED_TYPE` metric only (l.134-140).
- `routeToOrigin = !broadcast && !!metadata.connectorId` -> targets narrowed to that connector of that business; else fan out to all business connectors (l.143-150, 306-340).
- dynamic target selection per connector (l.373-473): isActive===ACTIVE, has username, EDI gating (feature_flag_edi_egress = **false in prod and dev** tfvars; EDI table support), `getConnectorUseCaseMapping` status ACTIVE, `hasConfig`, `getUserMappingRulesByUseCase` non-null. Each miss = `CONFIRMATION_METRIC.UNROUTABLE{reason}` + log, connector skipped.
- targets empty => return (no failure, no made) l.151-163. Invalid records are reported **only after** a target exists (l.165, comment "so undeliverable confirmations stay out of the Retry Queue").
- try{ for each target `writeConfirmation` ; if any EDI invalid -> throw ; `emitMadeConfirmation(valid)` } catch(err){ publish BifrostFailure per valid record to confirmation_data_failure } l.183-239.
- `emitMadeConfirmation` -> `PubsubRouter.emitMadeConfirmation` publishes one message per record to every topic registered for the type (PO/SO: legacy per-entity + cross-entity confirmation_made; others: confirmation_made) with attributes {recordType = made type} (pubsub.router.ts:42-66, factory.ts:439-463).
- **made is per batch of valid records, emitted after all targets are written; not per file, not per target.** A batch where some connectors were skipped as unroutable still emits made if at least one target wrote.

Write mechanics (gcs/storage.service.ts):
- CSV/JSONL: `upsertWindowFile` append-into-shared-window object named `<user>/from_ilg/<dir>/<yyyy-LL-dd-HHmm>-confirmation.<ext>` where the minute comes from **metadata.timestamp** (announce time), not wall clock (confirmations.service.ts:242-257, 290). Read-modify-write with ifGenerationMatch, 5 attempts on 412, row-string dedupe against existing rows (l.56-159). 5th 412 or other error -> CloudStorageException -> caught in process().
- EDI: one create-only `.edi` file per document, name `<MSG>_<docRef>_<ctrlRef>.edi`, ctrlRef = sha256(connectorId|recordType|docRef|sorted queueIds)[:14]; `createFile` ifGenerationMatch 0, 412 => "exists" counted as success (edi/build-edi-files.ts:106-150, storage.service.ts:214-229). Idempotent under redelivery AND under poller re-announce (queueId in key).
- Egress is written direct to GCS by Cloud Run; the customer collects via the SFTP VM/gcsfuse. "Made" therefore means "object persisted in GCS bucket", not "customer fetched it" (collector doc string calls made "the customer got this" - overstated).

Error -> HTTP mapping (errors.ts:51-254) relevant to confirmation handlers:
| Error | Response | Pub/Sub effect |
| PubsubEventDecodeException (bad envelope/json/shape) | 204 | ACK, dropped; log `MessageDecodeFailed` only |
| ValidationException (ZodUtils.parse) | 204 | ACK, dropped |
| PubsubException (publish failure) | 204 | ACK |
| ConfirmationException / ConfigApiException | 202 | ACK |
| ConnectorConfigException | 500 | nack -> redelivery |
| any other Error (axios 5xx, breaker open, GCS error outside try, JSON.parse) | 500 | nack -> redelivery, unbounded until 7d retention |

## 2. Exit-path table (see structured output for the machine-readable copy)

| # | Path / trigger | Today | Recorded where | Terminal | Silent | OBQ-dependent |
|---|---|---|---|---|---|---|
| 1 | Envelope/JSON/shape invalid (whole message) | 204 ack, batch dropped | log ErrorEvent.MessageDecodeFailed only | yes (dropped) | yes | yes: row still on OBQ, re-announced (and will fail again if producer bug) |
| 2 | Business has zero SFTP connectors (incl. cache empty) | ack | metric UNROUTABLE no_connectors + log NoEligibleConnectors + FORWARD skipped | yes | yes (no record) | yes |
| 3 | Origin connectorId not among business connectors | ack, "Publishes no failure: Snap holds the outbound-queue entry" (l.810) | metric CONNECTOR_UNRESOLVABLE + log | yes | yes | **yes, by explicit design** |
| 4 | Connector inactive / no username / use case inactive / no mapping config / mapping rules null | that connector skipped; if none left -> ack | metric UNROUTABLE{reason} + log | yes | yes | yes ("disabled = deferred") |
| 5 | EDI: flag off (prod), envelope missing, unsupported type | skipped like 4 | metric UNROUTABLE edi_* | yes | yes | yes |
| 6 | config-service 5xx/network/breaker open (tryGetConfig, mapping fetch) | throw -> 500 nack -> redelivery loop | logs / axios error | no (retries until success or 7d retention) | no while looping, then silent expiry | no while looping |
| 7 | config-service 4xx (401/403/404/429) on storefront list | ZodUtils.parse throws ValidationException -> 204 ack | log ValidationFailed | yes | yes | yes |
| 8 | config-service 4xx on connector detail / connector list-by-username | handleAxiosError_ resolves sub-500 (config.api.ts:744-749) -> mapping null -> classified use_case_inactive / no_mapping_rules -> skip | metric UNROUTABLE | yes | yes (misclassified) | yes |
| 9 | Some records fail canonical Zod, targets exist | failures published (BifrostFailure/record, stage confirmation_ready, attrs recordType=use-case name, stage, source=sftp, customer) | confirmation_data_failure -> replay (all 7 types) ; collector only WOC/FGR/goods-in/goods-out | yes | no if publish ok | partly (the invalid row would also be re-announced) |
| 10 | Failure publish itself fails (Pub/Sub outage) | caught, logged "Failed to publish confirmation write failure", still ack | log only (+ no metric) | yes | **yes** | yes |
| 11 | All records invalid | failures published, no made | as 9 | yes | no | - |
| 12 | Write/transform/EDI-invalid/made-publish error for valid records | catch -> failure per valid record (code `sftp-connector.<type>.write_failed`, retryable:false), ack | as 9 + metric FORWARD_FAILURE | yes (if publish ok) | no | today ALSO no made => OBQ re-announces => duplicate failure + possible duplicate file |
| 13 | Zero rows produced (mapping yields nothing) | NoRowsWritten + FORWARD skipped, **falls through to made** | log/metric | yes ("success") | yes (false success) | no |
| 14 | Window: all rows already present | skip write, made | log droppedDuplicateRows | yes | partly | no |
| 15 | EDI file already exists | "exists" treated as delivered, made | log EdiFileAlreadyExists | yes | partly | no |
| 16 | Made publish fails after file written | inside try -> failure published as write_failed although file exists; no made | failure topic | yes | misleading | today OBQ also re-announces |
| 17 | Stock adjustment: bad envelope (any 1 bad record, whole bulk validated) | 204 ack, entire batch dropped | log only | yes | yes | yes (poison batch re-announced) |
| 18 | Stock adjustment: no targets (mapping not ACTIVE etc) | return, no made, no failure | metric UNROUTABLE + log | yes | yes | **yes ("SNAP re-announces the batch once the mapping is fixed", l.128 comment)** |
| 19 | Stock adjustment: EDI invalid | metric FORWARD_FAILURE only, return, no made, no failure topic | metric | yes | yes | yes |
| 20 | Stock adjustment: GCS write throws | 500 nack loop (no failure topic exists) | logs | no | no | no while looping |
| 21 | Stock adjustment: made publish fails | PubsubException -> 204 ack; file already written | log | yes | mostly | yes (row stays, re-announce rewrites, row-dedupe absorbs) |
| 22 | Pod crash/SIGTERM/timeout mid-request | non-2xx -> nack -> redelivery; no in-memory state | none | no (retried) | no | no |
| 23 | Handler > 20s ack deadline | Pub/Sub redelivers concurrently; both runs may publish made/failure | - | - | dup | - |
| 24 | Replay redrive of an sftp failure | replay publishes to confirmation_ready with attributes {recordType} only (replay-service failures.controller.ts:654-664, failure.service.ts:751-758, pubsub.service.ts:238) -> fails sftp channel_filter for every type except RGA => never delivered to sftp | replay history says "success" | - | **yes (black hole)** | - |

## 3. Key findings

F1. Every non-error skip path (2,3,4,5,18) is metric+log only, ack'd, and its comments state that OBQ retention is the recovery. There is no durable record an operator "can find and act on" other than a counter tagged with reason. Under early consume all of these become permanent, silent loss unless converted to a recorded terminal outcome (failure record or collector state).

F2. The failure recording path is best-effort: if publishing to confirmation_data_failure fails, it is swallowed and the message is acked (paths 10, and file-level analogues). Under early consume that is loss with only a log line. It needs to be atomic with the ack (nack on failure-publish failure) - but nacking here is unsafe today because the write path has already run (dedupe absorbs re-writes for CSV rows in same window and EDI create-only, so redelivery is actually safe).

F3. Config-service error classification is wrong for 4xx: getConfigApi_ resolves any status <500, so 401/403 (e.g. rotated API key), 404, 429 become "use case inactive", "no mapping rules", "no connectors" (metric-only skip) or ValidationException (204 ack). During any config-service auth/permission fault, every confirmation is silently skipped today and only survives because OBQ rows remain.

F4. Replay redrive cannot reach sftp-connector for pick/pack/PO/SO/FGR/WOC because replay stamps only recordType and the sftp subs require source=sftp or broadcast=true. So the "error lands in replay queue" leg is not actionable for SFTP egress failures (only RGA works). Memory note reference_confirmation_gating_switches_map records the same black-hole.

F5. Coverage of failure consumers for sftp-produced failures: replay filters cover all 7 confirmation use-case names (replay-service iac pubsub.tf: pick/pack/woc/fgr + goods_in/goods_out/return_goods_confirmation, retry 30s, DLT after 5). Collector confirmation_failure_filters cover only WOC, FGR, goods_in, goods_out, stock_adjustment (collector pubsub.tf:29-35) - pick, pack, RGA failures do not reach collector; collector made filters (l.20-25) cover only WOC, FGR, PO, SO - pick/pack/RGA made not marked processed in collector. Stock adjustment failures are never published by sftp-connector at all, so collector's stock_adjustment failure sub is inert for sftp.

F6. Duplicate semantics: CSV/JSONL windows dedupe on exact row text within the window object named by announce-minute; a poller re-announce (today's safety net) carries a new metadata.timestamp -> different minute file -> the customer receives the same rows twice, undetected. EDI is idempotent across re-announce (ctrlRef includes identifiers.queueId; if queueId is absent from records the key degrades to docRef and distinct confirmations for the same doc collide as "exists" = silent drop - open question whether queueId is always populated). Early consume removes the re-announce duplicates but any remaining duplicate now cannot be reconciled against SNAP.

F7. Latent data-loss bug independent of early consume: upsertWindowFile sets ifGenerationMatch from getMetadata before download(); if download() throws transiently (both inside one catch{}), existing="" while precondition = current generation, so save(incoming) overwrites the whole window object and destroys earlier rows already "made" (storage.service.ts:84-92, 125-127). Cleared OBQ rows for those earlier rows cannot be recovered.

F8. Row-string dedupe can drop a legitimately distinct confirmation whose mapped row text is identical to one already in the window (e.g. mappings without a unique column) - counted as success/made.

F9. Made is emitted per batch even when some targets/connectors were skipped or a zero-row file was produced (paths 13, 14 and partial-target), so "made" is not "delivered to every intended connector". Under early consume this distinction is already moot but collector's `processed` state (fed by made) is unreliable as the terminal record.

F10. Nack loops (paths 6, 20, unknown Error) have no DLQ, no backoff (no retry_policy on confirmation subs) and Pub/Sub's default 7-day retention will silently discard undelivered messages. With the OBQ row consumed at poll time, a >7-day config-service outage or a poison message that throws (e.g. GCS permission error) is terminal loss with no record.

F11. Path 16: made-publish failure is classified as write_failed although the file was written; the failure record is then misleading and a replay would (subject to F4) re-append.

F12. No buffering: confirmations are processed synchronously inside the push request; nothing is held in memory or in a durable store between receipt and write. Crash mid-request => nack => redelivery (paths 22). This is the one property that is already safe for early consume. Parallelism: multiple Cloud Run instances race on window objects (5 attempts, then failure record).

F13. Multi-consumer: a broadcast confirmation is delivered to fapi/shopify/sftp; any consumer's made clears the SNAP row (per memory note; verify in snap-adapter area). sftp skipping (path 2-5) while another consumer delivers is silent loss for the sftp leg TODAY too. Early consume makes this the norm; per-consumer terminal accounting would be needed.

## 4. Feature flags / config
- FEATURE_FLAG_USE_DYNAMIC_CONFIRMATION_MAPPING true dev+prod; FEATURE_FLAG_EDI_EGRESS false dev+prod (EDI egress inert; connectors saved as `edi` are skipped with UNROUTABLE edi_egress_not_enabled - so EDI-configured connectors currently get NOTHING and rely on OBQ retention).
- sftp-connector deliberately does not read connector-level confirmationsEnabled (poller is the only enforcer); it gates on isActive + per-use-case mapping status.

## 5. Open questions
- Is identifiers.queueId always present on records reaching sftp (drives EDI ctrlRef uniqueness)?
- What does snap-adapter do on receiving confirmation_made for a record whose OBQ row is already processed (idempotent?) - other area.
- Cloud Run min/max instances and request timeout not visible in the grep (defaults assumed); ack-deadline overrun behaviour under large files not measured.
- Prod metric volumes for UNROUTABLE reasons and FAILURE_EMIT_FAILED were not queried (no Datadog used in this pass).
- Whether the replay redrive attribute gap is intended to be fixed by stamping source/broadcast, or by loosening the sftp filter.
