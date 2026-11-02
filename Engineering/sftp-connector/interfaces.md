---
tags:
- waypoint
- sftp-connector
verified: '2026-10-14'
verified_sha: 4e1593e
verified_paths:
- code/src/controllers
- code/src/types/confirmations/operations.ts
- iac/projects/bifrost-sftp-connector/pubsub.tf
- iac/projects/bifrost-sftp-connector/storage.tf
- code/src/pubsub/pubsub.router.ts
- iac/env
title: sftp-connector — interfaces
---
# sftp-connector — interfaces

Split out from [[Engineering/sftp-connector/architecture|architecture]] because this service has
three distinct inbound surfaces (SFTP, GCS events, Pub/Sub push) plus a file-layout contract.

## Pub/Sub push endpoints (`controllers/pubsub.controller.ts`)

| Route | Subscription source | Notes |
| --- | --- | --- |
| `POST /events/v1/file` | `new_file` (own topic, GCS notification) | ack deadline 600s; an object it doesn't handle (directory placeholder, unaccepted extension) acks 200 and logs at warn |
| `POST /events/v1/confirmation/ready/:recordType` | `stock_adjustment_ready` (own topic, own explicit route mounted before the param one), and cross-entity `confirmation_ready` with one `attributes.recordType`-filtered subscription per type. PO matches `purchase_order` or `goods_in_confirmation`, SO matches `goods_out_confirmation`; the rest match their own name | Every cross-entity subscription, RGA included, also filters on `attributes.source = "sftp" OR attributes.broadcast = "true"`: own-channel plus broadcasts. The seven carry a 10s-600s retry policy and a 10-attempt dead-letter policy so the push includes `deliveryAttempt` (the DLT is never written to; the handler records the failure at attempt 10 instead, see architecture). Stock adjustments have neither. There are no per-entity PO/SO ready subscriptions any more |
| `POST /events/v1/create_acknowledge` | `create_acknowledge` | **unfiltered** |
| `POST /events/v1/create_data_failure` | `create_data_failure` | **unfiltered** |
| `POST /events/v1/entity_error` | `entity_error` | |
| `POST /events/v1/config/revision` | `config_revision` | invalidates cached mappings |
| `POST /events/v1/create_sftp_user` | `create_sftp_user` (own topic) | |

The `create_acknowledge` and `create_data_failure` subscriptions are deliberately unfiltered: this service consumes *every*
ingress record type, so there is no `recordType` subset to filter for, and `metadata.capture`
discriminates in code. That is the documented exception to the org rule that cross-entity
subscriptions must filter — don't "fix" it.

Push is authenticated by OIDC tokens for a dedicated `pubsub_handler_invoker` service account.
Cloud Run is `INGRESS_TRAFFIC_ALL` but `run.invoker` is granted only to that SA, so nothing here
is anonymously reachable.

## Other HTTP

| Route | Purpose |
| --- | --- |
| `GET /health/liveness` | liveness |
| `/debug` (`GET /`, `POST /`, `/applyBusinessRules`, `/validate`, `/processConfirmation`) | operational tool: upload a file (50MB cap), run the real translators/rules against it, derive confirmation storage paths. Mounted in **all** environments — see known-context. |

## Outbound

- `create_record_request` — canonical records, `metadata.capture` = `SftpCapture` (a GCS
  pointer, never inline bytes).
- `create_data_failure` — row-level and file-level failures, stamped with `connectorId` and
  `transaction`.
- `confirmation_made` — egress clear-down, published after a confirmation file is written (when
  any leg delivered), for all seven types, with `attributes.recordType` (`goods_in_confirmation` / `goods_out_confirmation`
  for PO/SO). The legacy per-entity PO/SO made topics are no longer published.
- `stock_adjustment_made` — after a stock adjustment file is written.
- `confirmation_data_failure` — per-record validation failures, and one failure per record for each
  connector a confirmation could not be delivered to (routed or fan-out, with that connector's id
  on the body and envelope), plus `redelivery_exhausted` once the retry budget is spent. The push
  is still acked (a nack would redeliver and duplicate the file), so this topic is the only route
  to replay. The exceptions, which 500 so Pub/Sub redelivers: a failure publish that itself fails,
  and a fan-out `confirmation_made` that can't be published.
- config-service over HTTP (API key) for connector, mapping, warehouse-routing and DDP config.
- GCS for every file read/write; SSH to the VM for user creation.

## GCS layout — the customer-facing contract

Bucket `sftp-connector-<env>-storage`:

| Path | Meaning |
| --- | --- |
| `users.json` | source of truth for SFTP logins (see `CLAUDE.md`) |
| `<user>/to_ilg/<action_type>/<file>` | customer uploads land here; gcsfuse-mounted on the VM. The path *is* the routing — the third segment names the action (`create_sales_order`, …, `create_work_order`), and anything not exactly four segments is ignored by ingest. `.edi` is accepted only with `FEATURE_FLAG_EDI` (on in dev and prod) |
| `<user>/to_ilg/<action_type>/archive/<file>` | successfully acknowledged input |
| `<user>/to_ilg/<action_type>/error/<file>` | input that failed; never downgraded back to archive |
| `<user>/from_ilg/<type>_confirmations/<yyyy-LL-dd-HHmm>-confirmation.csv\|jsonl` | confirmation window objects the customer collects — one per username, directory and minute. `<type>_confirmations` is derived from the confirmation type, except finished-good receipts, which honour the connector's `finishedGoodReceiptEgressDirectory` |
| `<user>/from_ilg/<type>_confirmations/<MSG>_<docRef>_<ctrlRef>.edi` | EDIFACT egress (connector `egressFiletype: "edi"`, flag-gated): one message per file, created once and never overwritten |
| `<user>/from_ilg/stock_adjustment_confirmations/` | stock adjustment files, one per hourly window (csv/jsonl) or per EDI message |

UNRESOLVED: the directory name is mechanically `<confirmation_type>_confirmations`, so
work-order confirmations land in `work_order_confirmation_confirmations` — the doubled word looks
accidental, but it is what the VM startup script creates too, so it may already be a customer
contract.

Filenames, CSV column order and layout are **contractual per business but expressed as
config**, not code. A format change is a customer-visible change even though no code changed.
