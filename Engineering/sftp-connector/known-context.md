---
tags: [waypoint, sftp-connector]
title: sftp-connector — known context
---
# sftp-connector — known context

What source cannot tell you. Established by interview 2026-08-24 unless marked otherwise.

## Intentional design

The **VM + gcsfuse** design is pragmatic and still considered correct — customers insist on
plain SFTP, and gcsfuse makes everything downstream GCS-native for free. Don't treat it as
legacy to be replaced by a managed transfer service.

**SFTP onboarding is automated** through the `create_sftp_user` topic; manual `users.json`
edits are the exception (a partner or EDI intermediary bringing their own key). The
`scripts/get-key.sh` path — GFS generating the keypair and handing over a private key — is the
genuinely legacy part.

## Fragility — the three that actually bite

1. **Egress window write races.** Concurrent Cloud Run instances append to one shared window
   object per customer. Generation preconditions and retries are the mitigation, not a
   guarantee; overwrites have happened before and were fixed once already.
2. **The `users.json` three-field trap.** A record missing `raw_username` makes the connector
   reject the *entire* file on the next user creation, which blocks **all** SFTP onboarding.
   This caused FUSE-976. Detail lives in the repo's `CLAUDE.md`.
3. **The VM is a live single point of failure.** One `e2-small`. If it or its gcsfuse mounts
   wedge, no customer can deliver or collect anything. Recovery is a reboot — the startup script
   re-runs the user sync and rebuilds mounts — but there is **no formal runbook** and the failure
   path is untested.

Notably *not* a live pain point: mapping-config drift. It looks like an obvious hazard given how
much behaviour is config-driven, but it isn't what bites in practice.

## Two writers to `authorized_keys`

Found by reading source 2026-08-24, and worth knowing before touching either path:

- `sftp-user-builder` (the automated `create_sftp_user` flow) writes `authorized_keys` with
  `tee` — **one key, overwriting** — while also upserting the `users.json` record.
- `sync_users.sh` on the VM **rebuilds** `authorized_keys` from *every* `users.json` record
  matching that username, which is how multi-key users work.

So the automated path and the sync script disagree on multi-key semantics. Adding a second key
must go through `users.json` + a sync run, per `CLAUDE.md` — not through the automated flow.

## Contractual surfaces

Confirmation file **formats are contractual per customer but expressed as per-business config**
(`CONNECTOR_MAPPING`, column order, filenames). The config is the contract: changing a
business's mapping is a customer-visible change with no code diff to review. Treat config edits
for a live business with the same care as a schema change.

## Accepted risks

`/debug` — 50MB upload, real rule application, confirmation path derivation — is mounted in
every environment with no env guard. This is **known and accepted**: `run.invoker` is restricted
to the Pub/Sub invoker SA, which is considered sufficient. Don't file this as a finding; don't
remove the guard-less mount without asking.

## What surprises people

- **SFTP users aren't in Terraform.** A bucket file plus a VM script own logins, and
  `terraform apply` deliberately won't touch them (since #128).
- **Egress appends to a shared window object**, rather than writing a file per confirmation.
  EDIFACT egress is the exception: it writes one create-only `.edi` file per confirmation.
- **A confirmation record that fails canonical validation goes to the Retry Queue**, not the
  bin. It's published to `confirmation_data_failure`, but only when sftp-connector has a target
  for it. An all-invalid batch writes nothing and emits no `confirmation_made`, so SNAP
  re-announces it.
- **Stock adjustments are the exception to per-record validation.** The controller validates the
  whole bulk envelope, so one bad record rejects the entire batch (`MessageDecodeFailed`, 204,
  nothing written).
- **Customer references only come from mapping.** Since the types 10.x adoption, the canonical
  factories emit no `order.customerRef` / `workOrder` / `businessRgaNumber`. An unmapped
  reference, or a blank column (the rules engine drops `""`), fails ingest validation and never
  becomes a placeholder: dedupe keys on the reference.
- **Reading a storefront returns its embedded connectors' `config.auth` in full**, SFTP private
  key included. To read mappings, use the connector mapping endpoints instead.

- **EDI is behind one flag, `FEATURE_FLAG_EDI` (Terraform `feature_flag_edi`), on in dev and prod (prod since 2026-10-14, sftp-connector#310).** It gates ingest as well as confirmations: while it's off, `isFileTypeAccepted` treats `.edi` as unaccepted, so the file logs "File is not a valid type" and stays where it was dropped. `ACCEPTED_FILE_TYPES` still lists `edi` and isn't the switch. Switching a connector to `edi` means rewriting its confirmation mapping, so it can't fall back to CSV afterwards.
- **EDI routing (since FUSE-1259):** an action directory accepts a *set* of EDIFACT types. `create_purchase_order` takes ORDERS or DESADV; `create_work_order` takes DESADV. In a multi-type directory the file's UNH picks the normalizer, a type outside the set fails as `EdiMessageTypeMismatchError` naming the accepted types, and a file with no UNH is rejected. Whether a DESADV is an ASN or a kitting instruction is the folder plus the mapping, never code.
- **EDI rows hold strings.** `toRow` stringifies every value, so `mul`/`add` on row variables fail, and "component qty × kit qty" can't be written as a rule. A rules-engine `if` with 2 args throws only when the condition is false; always pass 3.
- **A misrouted or unparseable file logs twice.** The file-level failure returns 500, so Pub/Sub redelivers once: "File not found in cloud storage" and then `already_in_error`. The file still lands in `error/` once.
- **A file whose record dedupe holds stays in the folder root.** No ack or failure ever routes it to `archive/` or `error/`.
- **Dev e2e against the fuse-mocker simulator:**
  - Seed finished goods as plain products, because `explodeKits` replaces a kit SKU with its BOM.
  - HJF's simulator runs with `strictValidation` off, so Snap length caps only bite when it's switched on (`PUT /api/v1/businesses/HJF/validation {"strict":true}`).
  - The poller links an R10 to its S10 via `Prime` first (the mocker stamps `Prime = ShipmentId`), then `SupplierRef`, then `SupplierOrder`, then `CustomerRef = SupplierRef`.

## Fan-out test gap: the null-vs-inactive fold is unpinned (2026-10-02)

The fan-out spec's "writes nothing" cases are one `describe.each` (around `:1406-1425` at E1). No test
pins how a null use case and an inactive one fold together. E1 changed that classification (no use case =
benign, inactive = failed leg), so a regression there would pass the suite. Worth a dedicated test the next
time that code is touched.

## Egress and mapping gotchas (FUSE-1253, FUSE-1088)

Found while building EDIFACT egress and mapped stock adjustment files. Each was re-checked against
`origin/master` (`648ee6e`) on 2026-10-05.

- **Stock adjustments ignore the connector's `isActive`.** `stock-adjustment.service.ts`
  (`eligibleTargets`) checks only the SFTP username and the `stock_adjustment` mapping's status.
  Confirmation egress also checks the connector itself (`isActiveConnector`). So an inactive
  connector with an active stock adjustment mapping still gets files: GADG dev's inactive "ILG
  Test Account" does. This was already true before FUSE-1088.
- **`metadata.connectorId` names the origin connector, not the egress target.** Confirmation
  egress uses it to route a non-broadcast confirmation back to its origin (`routeToOrigin`). Each
  egress target carries its own `ConfirmationTarget.connectorId`, added for EDIFACT control
  references. Don't use one in place of the other.
- **`transformConfirmations` rows don't record which rule made a column.** A row is a flat
  `{...header, ...line}`. A record with no lines gives one header-only row, or no row at all if its
  header is also empty. The EDI module (`confirmations/edi/apply-mapping.ts`) applies the header and
  line rules itself rather than using these rows.
- **The storage bucket has versioning on** (`iac/projects/bifrost-sftp-connector/storage.tf`). So
  EDIFACT's create-only write (`ifGenerationMatch: 0`) only guards files that haven't been
  collected yet. A resend after the customer has fetched and deleted the file writes it again,
  with the same control reference. The receiver's duplicate-interchange check is the backstop.
  (The `reference_sftp_triage_gotchas` memory note said versioning was off. It is on.)
- **`ICloudStorageService` has four test doubles.** They are `__fixtures__/storage.service.fixture.ts`,
  `core/file-routing/__fixtures__/file-routing.fixture.ts`, and the inline mocks in the
  confirmation-egress and stock-adjustment specs. A new interface method needs all four.
- **config-service `PUT …/mappings/{useCase}` can't remove a key from `config`.** Its save is an
  aggregation-pipeline `$set`, which merges sub-documents, so a key the body leaves out (such as
  `columnOrder`) survives. Arrays are replaced. To really unset a key, DELETE the mapping and POST
  it again. Both work because a deleted use case is stored as null. Matters when restoring a dev
  mapping after a test.
- **The Charlotte Tilbury (Puig) EDIFACT user guides are local**, in
  `~/code/fuse/edi-guides/PUIG EDI standards EDIFACT/`: DESADV V06 and DESADV SHIPMENT V01,
  INSDES V05, INVRPT V04, OSTRPT V04, PRICAT V06 and RECADV V04. DESADV V06 is D96A EAN005 with
  `BGM+351`, and `GIN+BJ` SSCC is mandatory. RECADV V04 is D96A EAN003 with `BGM+352`. None of
  them has a UNB section. They are the input to CT conformance work.

## SFTP host migration (2026-10)

The VM is being replaced by the multi-zone Go host in `apps/host` (plans `sftp-host-a/b/c`). What the build taught, beyond the source:

- **The VM itself is weaker than it looks.**
  - #140 (2026-04-02) replaced FUSE-241's per-user 700 mounts with one `sftpgroup` 770 mount, so every customer can read and write the whole bucket, `users.json` included. The root-run `sync_users.sh` `eval`s every username (`startup.sh.tpl`), and customers have `/bin/bash` shells.
  - A chroot was tried and backed out (`b2efea0`, no reason recorded). The startup script's `rm -f /etc/ssh/sshd_config.d/*` wipes any override on boot.
  - `sftpuser` (the provisioning admin) is in `sftpgroup` on older VMs, so a `Match Group sftpgroup` rule would hit provisioning too.
  - `users.json` history up to 2026-10-20 shows no sign the `eval` path was used.
- **The VM refuses SETSTAT** (WinSCP's default "preserve timestamp" after upload) with `Permission denied`; the file still lands. The host accepts it as a no-op and keeps no timestamp or mode.
- **Client behaviour the host relies on.**
  - Modern OpenSSH `scp` (9.0+) runs over SFTP, so it works on an SFTP-only server; only `scp -O` is refused.
  - A server must send `exit-status` when the subsystem ends, or `scp` reports `Exit status -1` though the file arrived.
  - WinSCP's default upload writes `x.filepart`, then renames it. The connector ignores the `.filepart` event and ingests the final name.
  - PuTTY's `psftp` is a usable Linux stand-in for WinSCP and FileZilla.
- **`pkg/sftp`'s request server** treats a handle still open at session end as a failed transfer. OpenSSH, paramiko, ssh2-sftp-client, psftp and WinSCP all close properly.
- **Push → pull subscription switch:** it's in place and keeps the backlog, but Pull returns `FAILED_PRECONDITION` for about a minute afterwards. Consumers must retry it at start-up, and the cut script must wait it out.
- **fake-gcs-server for host tests:** use `-backend memory`, because the filesystem backend drops `dir/` placeholders. It ignores `ifGenerationMatch=0` on copies, and `-public-host` must be reachable from the reader container.
- **The blackbox suite's ten ingest suites check zero records** and pass, on master's nightly too. Only the four confirmation suites test anything. Pre-existing; needs its own fix.
- **`sftp-user.builder.ts` replaces only the first matching `users.json` record**, so a multi-key user's first key gets overwritten on re-provisioning.
- **`UserCreationResponse`** (sftp-connector → config-service) isn't in `@gfs-bifrost/types`; each side defines it locally.
- **`terragrunt@0.1-affogato`'s `tf_var_extra_N_value`** inputs are secrets and masked in plan output. Use `tf_var_image_name` for anything a reviewer must see.
- **The `support` SFTP user** has never had `support/logs/` under its home; only the shared `/mnt/gcs_root` mount reaches it. The host doesn't expose it.
- **A shared static IP needs a separate admin address for the VM.** Cloud Run provisions by SSHing to `connector.config.host`. Once that IP fronts a load balancer, the SSH can land on either backend, so S1 moves the VM to its own admin IP (`SFTP_ADMIN_HOST`).
- **A health check on port 22 passes a booting COS instance.** The OS's own sshd answers for 20–30 s before cloud-init stops it. Probe the container's `/healthz` instead. Passthrough NLBs also probe from 209.85.152.0/22 and 209.85.204.0/22, so the firewall needs both ranges.
- **Health-check logs record only state changes.** A booting instance logs UNHEALTHY→UNHEALTHY, so only HEALTHY→UNHEALTHY means a backend failed.
- **GCP's Cloud Run job `completed_execution_count` can stop reporting while every run succeeds** (from 2026-10-28 00:45Z). Monitor what the job logs, not the job metric.
- **The `sftp-key-access-audit` skill's "Expiring" note is past due** (snapshot 2026-10-29): the audit-service cutover happened on 2026-10-15.

## Unknowns

- Is there an intended owner or trigger for hardening the VM (HA, or a managed replacement), or
  is the single-point-of-failure risk simply accepted indefinitely?
- Does anything depend on `/events/v1` route naming, or could the event surface be renamed with
  only subscription changes?
