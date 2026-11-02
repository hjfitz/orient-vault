---
tags:
- waypoint
- sftp-connector
verified: '2026-10-14'
verified_sha: 4e1593e
verified_paths:
- iac
- .github/workflows
- code/src/observability
- code/src/confirmations/confirmation-egress.service.ts
- code/src/http/middlewares/observability.middleware.ts
- code/src/confirmations/constants.ts
- code/src/controllers/pubsub.controller.ts
title: sftp-connector — operations
---
# sftp-connector — operations

## Deploy

`deploy.yaml` on push to `main`/`master` builds and deploys through dev then prod;
`manual-deploy.yaml` is `workflow_dispatch` for deploying a branch to dev (and applies dev
Terraform, so branch infra is testable pre-merge). `code-quality.yaml`, `secops.yaml` and
`tf-plan.yaml` gate PRs. Terragrunt lives in `iac/projects/bifrost-sftp-connector`.

**Two deployables, one repo.** Cloud Run ships on every deploy; the SFTP VM is Terraform-managed
and its behaviour comes from `scripts/startup.sh.tpl`, which only takes effect on VM
recreation or reboot. A change to the startup script is not live until the VM restarts — it now
also creates `create_work_order` under `to_ilg` and `work_order_confirmation_confirmations` /
`finished_good_receipt_confirmations` under `from_ilg`, so those directories are absent for a
customer until their VM has been through a restart.

**Behaviour switches live in `iac/env/*.tfvars`**, reaching the container as Cloud Run env vars —
changing one is a Terraform apply, not a code deploy. `feature_flag_use_dynamic_confirmation_mapping`
is `true` in **both** dev and prod: flipping it back drops confirmation egress to the hardcoded
goods-in/goods-out transformers and silences every other confirmation type entirely, so it is a
blunt kill-switch, not a tuning knob. `use_legacy_ddp_rules` and `use_legacy_mapping_rules` are
still `true` in both environments. `feature_flag_edi` (`FEATURE_FLAG_EDI`) is `true` in dev and
prod (prod since 2026-10-14): it gates EDIFACT ingest (`.edi` rejected as an invalid file type) and EDIFACT egress (a connector with
`egressFiletype: "edi"` is skipped and counted as `edi_egress_not_enabled`). `ACCEPTED_FILE_TYPES`
already lists `edi`, so the flag is the only switch.

## Observability

Datadog via `@ilg-platform/observability` with `fuse.*` metrics. Metrics worth knowing:

- `egress.window_write.retry` — a window write lost the generation race and retried. Non-zero is
  normal; sustained growth means contention worth looking at.
- cold-start histogram + counter, emitted on listen.
- `CONFIRMATION_METRIC.UNROUTABLE`, tagged with the `reason` the connector was skipped —
  `no_connectors`, `no_username`, `connector_inactive`, `connector_unresolvable`,
  `use_case_inactive`, `no_mapping_config`, `no_mapping_rules`, `unsupported_type`, and the EDI set
  `edi_egress_not_enabled`, `edi_requires_dynamic_mapping`, `edi_envelope_missing`,
  `edi_unsupported_type` (taxonomy in `observability/constants.ts`), and two local to the egress
  code (`confirmations/constants.ts`): `use_case_not_configured` (a fan-out connector with no use
  case for the type, benign) and `use_case_lookup_failed` (the use case couldn't be read). First thing to query when a
  customer reports a confirmation file that never arrived. `CONFIRMATION_METRIC.FORWARD` is also
  tagged with `fileType`.
- Every request increments `REQUEST_METRIC.COUNT` from `http/middlewares/observability.middleware.ts`,
  which also opens the correlation scope from `x-request-id`.

Connector/config objects carry live credentials (SFTP private keys, REST API keys) and are
logged directly, relying on the SDK's on-by-default redaction. `CLAUDE.md` forbids re-adding a
hand-rolled masker; if a gap appears, fix it in the SDK.

## Failure modes

- **VM down or mounts wedged** → total outage in both directions, with no formal runbook.
  Reboot re-runs the user sync and rebuilds mounts. See
  [[Engineering/sftp-connector/known-context|known-context]].
- **Egress window contention** → confirmations can overwrite each other if the generation
  precondition path regresses. This has happened and was fixed once.
- **Source file gone** (already moved or deleted) → the handler **acks** rather than retrying
  forever.
- **Business has no SFTP connector** but confirmations are enabled → acked as a no-op. Before
  the fix this 500-looped: 288 error pairs in 11 minutes in dev, tripping the error monitor.
- **Confirmation that cannot be delivered** → a `confirmation_data_failure` per record, so it
  reaches replay instead of vanishing into a counter. Routed: the named connector is missing from
  the business, a gate rejected it, or its lookup or write failed. Fan-out: each connector that has
  the use case but wasn't delivered gets its own failure; connectors without the use case record
  nothing; unreadable connectors give one failure with no `connectorId`. If recording a failure
  fails, the push 500s on purpose and redelivers.
- **Fan-out `confirmation_made` can't be published** → the push 500s and redelivers, re-writing the
  files (window rows already there are dropped, EDI names are create-only). Duplicates over loss.
- **Transient errors that keep failing** → after 10 delivery attempts the confirmation is recorded
  as a retryable `redelivery_exhausted` failure and acked; if that can't be published the push is
  still nacked. The 10 is `MAX_TRANSIENT_DELIVERY_ATTEMPTS`, mirrored by
  `confirmation_ready_delivery_attempts` in `pubsub.tf`. There is no DLT consumer.
- **Config-service error on a use-case read** → only a 404 means "use case not present"; a
  401/403/429/5xx is a lookup failure (recorded as a retryable dependency failure for confirmations,
  skipped and counted for stock adjustments), never a silent drop.
- **Window object can't be read** (anything but a 404) → the write fails and is recorded, rather
  than replacing the window with only the incoming rows.
- **Confirmation record fails its canonical schema** → published as a validation failure, the valid
  records in the same batch still write; if none are valid nothing is written.
- **EDIFACT mapping yields an invalid message** → no file for that message, other targets still
  written, and that connector's leg recorded as `write_failed`. Stock adjustments publish no
  failure, so nothing is made-published and SNAP re-announces the batch.
- **Connector switched off in the UI** → no confirmation egress at all, on either the dynamic or
  the legacy path, whatever its per-use-case mappings still say. Counted as `connector_inactive`,
  separately from an inactive use case.
- **Connector carries a use case this service doesn't know** → its Zod enum rejects the unknown
  member outright rather than stripping it, so connector resolution throws and *every* file for
  that connector stops processing, whatever its own use case. Adding `work_order` to a connector
  took GADG dev ingest down this way. A new use case therefore needs the `@gfs-bifrost/types`
  bump *and* the matching key on the local `config/schema.ts` deployed here before anyone enables
  it on a connector.
- **Connector unresolvable for an incoming file** → the file is moved straight to `error/` and
  acked. Nothing at that point can name the business, so no attributed `create_data_failure` is
  published; the file's presence in `error/` is the only signal.
- **Unaccepted file type or malformed path** → logged at **warn**, not error, and acked. This is
  customer error, and error-level logging of it once tripped the Fuse error-rate monitor (27
  hits) when the SFTP bind mounts were remounted.
- **File-level parse failure** (before any row validates) → a file-level `create_data_failure`,
  so the customer's file lands in `error/` rather than vanishing.
- **Slow large files** → the `new_file` subscription's ack deadline is 600s for this reason;
  lowering it will cause redelivery and duplicate publishing.

## Routine operations

- **Add a public key for an existing user**: edit `users.json` in the bucket with all three
  fields, then run `sudo /usr/local/bin/sync_users.sh` on the VM (or reboot). Editing the bucket
  alone does nothing. Full procedure is in the repo's `CLAUDE.md`; the `sftp-partner-key` skill
  automates the partner-key case.
- **Never hand-edit `authorized_keys`** on the VM — the sync rebuilds it from `users.json`.
- **Reprocess a file**: re-upload it, or move the object back out of `archive/`. An object in
  `error/` will not be downgraded automatically.
- **Nightly blackbox tests** run at 06:00 and on PRs, with their own containerised fake
  config-server under `tests/config-server/`.
