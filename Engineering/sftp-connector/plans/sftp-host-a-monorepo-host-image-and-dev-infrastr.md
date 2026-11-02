---
ticket: none
title: 'SFTP host A: monorepo, host image and dev infrastructure'
service: sftp-connector
status: complete
created: '2026-10-20'
updated: '2026-10-22'
repo: /home/hjf/code/fuse/sftp-connector
worktree: /home/hjf/code/fuse/sftp-connector/.claude/worktrees/sftp-host-a-signoff
branch: master
base: c9f3f0e04
base_sha: c9f3f0e04
pr: '329'
tags:
- waypoint
- plan
impl_model: opus
impl_effort: high
---
# none — SFTP host A: monorepo, host image and dev infrastructure

<!-- Guidance in this file is written as HTML comments: Obsidian hides them, agents read them,
     and `wp signoff` ignores them. Only <angle spans> are treated as unfilled placeholders, so
     they mark the places a human or agent must actually type something. Leave the comments in
     place — deleting them costs the next reader the guidance and gains nothing at the gate.

     SUPERSEDING A STATEMENT. This file is edited by several sessions over days. When something
     here stops being true, do NOT strike it through, delete it, or bury a correction inside it.
     Put one blockquote immediately ABOVE the stale text and leave the text alone:

         > SUPERSEDED 2026-09-04 — the monitor now lives in `gfs-bifrost/observability`.
         > Everything below is kept as the record of how it was first built here.

     One marker, always above, never inside. `wp decide` writes the dated entry in
     `## Decisions & deviations` that explains why. -->

## Intent
<!-- What we are changing and why. Link the ticket. -->
Plan A of three: Plan A (this one) → [[sftp-host-b-provisioning-login-audit-and-dev-cut|Plan B]] → [[sftp-host-c-prod-cutover-and-vm-decommission|Plan C]]. Together they replace the single-zone SFTP VM with a **drop-in**, GCS-native SFTP host that runs multi-zone, and move SFTP user provisioning off Cloud Run into it. Hardening the VM first was dropped (Harry, 2026-10-20), so the VM's exposure stays until the prod cut; the record is in [[harden-the-sftp-vm-sftp-only-per-user-isolation-|the abandoned Plan H]].

This plan:
- turns sftp-connector into a monorepo: `apps/connector` (today's `code/`) and `apps/host`;
- gets the connector IaC ready for the switch, and fixes today's provisioning bugs on the way;
- builds the host as **our own Go SFTP server** in `apps/host`, on `golang.org/x/crypto/ssh` (SSH protocol) and `github.com/pkg/sftp` (SFTP protocol), following wms-gateway's Go app as the precedent. We write the server and its GCS file system, not the protocols;
- makes it a **portable container**: everything comes from env vars and mounted files, it runs unprivileged on an internal port, and nothing in it assumes the machine underneath. On GCP that machine is a MIG instance acting as a plain container host;
- gives the host one declared list of per-user folders, so a new Fuse use case is a one-line change plus a deploy;
- stands it up in dev on a temporary IP, with prod left dormant;
- lays the ground for a gradual cut: the VM becomes a load-balancer backend beside the host, so traffic can be split and the VM drained, and provisioning SSH can target the VM directly.

Done means the dev host serves real dev customers' files on a temporary IP, with the VM's host keys and its exact visible tree, and prod has no running host.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. A client on the host starts in `/home/<user>` and sees only `to_ilg` and `from_ilg`. Absolute and relative paths under `/home/<user>/{to_ilg,from_ilg}` behave as on today's VM. The VM's other surfaces (shells, `/mnt/gcs_root`) are deliberately not reproduced.
- [x] 2. Nothing outside the user's own `to_ilg`/`from_ilg` can be reached by any path: no other prefix, `users.json` or `support/logs/`. Shell, exec, scp, pty, env, X11, agent and port forwarding, and mkdir in `/home/<user>` are all refused.
- [x] 3. Files behave as on the VM:
  - an upload produces a byte-identical object at today's object name with exactly one finalize, and Cloud Run archives it or routes it to `error/` as today;
  - writes at offsets and resumed uploads work;
  - a transfer cut off before the client closes the file creates no object;
  - rename, delete, mkdir, rmdir of an empty folder, and set-times all behave as the clients in the test matrix expect;
  - egress files download.
- [x] 4. The host presents the VM's host-key fingerprints for every key type the VM has. Its key-exchange, cipher and MAC lists match the VM's (`ssh-audit` diff), except algorithms `x/crypto/ssh` doesn't implement; each of those is listed with the fallback clients negotiate instead.
- [x] 5. A `users.json` key edit takes effect within the poll interval with no restart. A malformed record is skipped and counted while every other user still logs in. Every key of a multi-key user works.
- [x] 6. Losing a replica or rolling a deploy doesn't stop service: clients reconnect. The host only listens once `users.json` is loaded, so the load balancer's TCP check means "ready", and `/healthz` (autohealing) fails if the SSH listener stops.
- [x] 7. Prod stays dormant: every merge's prod plan is a no-op or creates only the SA and secrets. No prod MIG instance or forwarding rule exists.
- [x] 8. The monorepo move changes no behaviour: Terraform state prefixes are unchanged, the connector deploys dev and prod from `apps/connector`, and a dev file drop is archived.
- [x] 9. The split is ready but inert: the VM sits in an unmanaged instance group, a second reserved "admin" address exists for it, and Cloud Run's provisioning SSH can be pointed at that address by config (`SFTP_ADMIN_HOST`), with no change to serving until Plan B uses them.
> SUPERSEDED 2026-10-22 — #329 rebuilt the image after the local compose suite ran; the real-client checks (WinSCP, psftp, OpenSSH probes, ingest) ran against the digest serving now.
- [x] 10. The image is portable: a static Go binary on distroless, non-root, listening on 2022, configured only by env vars and mounted files (host keys from files, or a Secret Manager reference), with GCP access through Application Default Credentials, JSON logs on stdout and metrics to a DogStatsD address from env. The digest that passed the local compose suite is the one serving in dev.
- [x] 11. The folder skeleton is a declared list owned by the host, seeded with today's 5+5 directories and validated at start-up. The reconcile that applies it is create-only and safe to run on several replicas at once; removing an entry never deletes a folder.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- **Repo layout:**
  - `code/` → `apps/connector/`; new `apps/host/` (a Go module); per-app workflows following snap-adapter's naming (`<app>-{on-push,manual-deploy,code-quality,blackbox-testing}.yaml` with `paths:`, one `secops.yaml` with per-app jobs).
  - The Go side follows **wms-gateway's `apps/gateway`**:
    - Go 1.27, `cmd/` + `internal/`;
    - a distroless `static-debian12:nonroot` image;
    - `golangci-lint`, `go vet` and `go test -race` in code-quality;
    - `secops-dep-go` and `secops-container` at `0.2-bonbon`;
    - a `gen-check` workflow for generated models;
    - `datadog-go/v5` for metrics.
  - `iac/projects/bifrost-sftp-connector` **keeps its path**: its state key is `<env>/bifrost-sftp-connector` (`root.hcl:16`), and `storage.tf:4` has `force_destroy = true` on the customer bucket.
  - New `iac/projects/sftp-host`.
- **Reusable workflows:**
  - `ilg-platform/github-actions` `docker-build-push@0.1-affogato`: `working_directory` defaults to `code` and is the build context.
  - `terragrunt@0.1-affogato`: `tf_var_extra_N_value` are **secrets**, masked in plan output, so the host image goes through `tf_var_image_name`.
  - `secops-*@0.2-bonbon`: take `working_directory`; `secops-dep-node` needs `audit-ci.jsonc` there.
- **Connector IaC:**
  - `pubsub.tf:161-191`: the `create_sftp_user` subscription (static `push_config`, 20 s ack deadline, `max_delivery_attempts = 5` into a DLT topic with no subscription);
  - `compute.tf` (`sftp_vm`, `sftp_static_ip`);
  - `outputs.tf`, which already has `storage_bucket` and `sftp_static_ip`.
- **Provisioning target:** `pubsub.controller.ts` `createCustomer` builds the SSH target from `connector.config.host`/`port`. Once the static IP fronts a load balancer, that address can land on the host, which refuses `sftpuser`, so provisioning needs its own address for the VM.
- **Connector code:** `config/config-handlers/connector/connector.config-handler.ts:447-474`. sftp-connector publishes `create_sftp_user` to **itself** on every config backlink while a connector is PENDING, and the catch at `:466-473` swallows publish failures.
- **The host's contracts:**
  - `users.json`, three-field records (G1);
  - object names `<user>/{to_ilg,from_ilg}/<dir>/<file>`;
  - archive/error under `to_ilg/<action>/` (`file-routing.service.ts:413-421`);
  - folder placeholder objects, as gcsfuse `mkdir` creates them today;
  - `homeDir` `/home/<user>`, printed in fuse-ui's credential bundle (`credential-bundle.logic.ts:53-54`).
- **The IP is a contract.** Customers are given `config.host`, which config-service stamps as the **IP literal** `SFTP_DEFAULT_HOST` (`storefront.service.ts:953`; `config-service iac/env/*.tfvars:5`).
- **The DNS zone** is owned by ilg-platform-ec02 (C11, #266): the test record goes there, via the `ilg_core_infra` remote state.
- **Out of repo:** vault `waypoint.yaml` (`key_paths`, `commands.root`, language now TypeScript + Go); fuse-mcp `services.json` (`directory`, plus a new `sftp-host` service entry at Plan C).

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- The precedent for the move is snap-adapter: self-contained per-app directories with their own lockfile, `mise.toml`, `audit-ci.jsonc`, `tests/` and compose, and no root workspace. Read on origin. The names `apps/connector` and `apps/host` depart from the precedent's service-named directories (`apps/snap-adapter`); Harry chose them.
- `.trivyignore` is resolved from the repo root, so it stays where it is. Source: the reusable workflow.
- Renamed `workflow_dispatch` workflows can't be dispatched until they're on the default branch, so inc 1 has no pre-merge dev deploy. Its evidence comes after merge.
- Removing `push_config` turns the subscription to pull in place, and `enable_exactly_once_delivery` is mutable. That comes from provider docs and magic-modules, not checked at google 6.41.0, and #264 shipped an "add-only" Pub/Sub change as a destroy+create. Inc 2 rehearses it on a scratch subscription and reads the plan for `-/+`.
- **What the libraries give us** (established from their docs; the inc 3 prototype proves each against real clients):
  - `x/crypto/ssh` handles key exchange, ciphers, MACs, host keys and the auth exchange;
  - our `PublicKeyCallback` decides which keys are accepted, but a connection is only handed to us after the client has proved it holds the private key, so "logged in" is certain;
  - `net.Conn.RemoteAddr()` gives the client's IP **and port**;
  - which channels and requests to allow is entirely our code: only `session` channels with `subsystem sftp`, and nothing else.
- **`pkg/sftp`'s request server** takes four handler interfaces (file reads, file writes, file commands, listing) that we implement over GCS. A writer that implements its `TransferError` hook is told when a transfer fails, which is how a dropped upload is told apart from a clean close. To prove in the inc 3 prototype.
- **GCS has no random writes, and gcsfuse stages each open file on local disk**, so offset writes and resumed uploads work today. The host does the same:
  - writes go to a staging file, uploaded as one object on clean close;
  - opening an existing object for write without truncate first downloads it into staging;
  - staging lives in `STAGING_DIR` (container scratch on the instance disk), size-capped by config.
- **Rename** is copy then delete on GCS, as with gcsfuse:
  - plain SFTP rename fails if the target exists (SFTP v3);
  - `posix-rename@openssh.com` overwrites;
  - directory rename is refused unless the prototype shows a client needs it.
- **Host keys are lifted from the VM, not regenerated.** Customers' clients have pinned them; many automated clients fail hard on a changed key instead of prompting, so new keys would break the "invisible cut". The host offers **every** key type the VM has (Debian 12 generates RSA, ECDSA and Ed25519). In SSH the client's preference order picks the host-key algorithm, so a client gets the same key type from the host as from the VM, which matters for clients that store only one key. Dev and prod have different keys, each lifted from its own VM. RSA is served with `rsa-sha2-256/512`, as OpenSSH 9.2 does.
- **Residual risk carried by lifting:** the VM had a source-established root path (`users.json` usernames `eval`'d at boot), so a key read off it can't be proven never to have leaked. The `users.json` history check (inc 5 and Plan C gates) looks for signs it was used. Rotating keys later needs customer coordination, since `x/crypto/ssh` doesn't do OpenSSH's host-key update extension; it's out of scope here and only triggered by that check.
- `x/crypto/ssh` doesn't implement every algorithm OpenSSH 9.2 offers (for example `sntrup761x25519`). Clients negotiate the next shared one. The inc 5 `ssh-audit` diff lists the gaps, and the inc 5 real-client matrix proves nobody fails.
- The host's contracts with other services are Zod schemas in TypeScript. Following wms-gateway's `canonschema` and audit-service's `auditschema`, a small tool in `apps/host/tools/` emits JSON Schema from:
  - `@gfs-bifrost/types` (the `BifrostMessage` metadata, the connector DTO);
  - `@gfs-bifrost/audit` (the `AuditMessage` envelope and the `sftp_user` / `sftp_login` details).

  `go-jsonschema` turns that into Go, and `gen-check` fails on drift.
- **`UserCreationResponse` is a local schema** in `apps/connector/src/controllers/schema.ts`, not in `@gfs-bifrost/types`, so it's covered by golden JSON fixtures in `apps/host/testdata/`, which a spec in `apps/connector` parses with that schema. It has no arrays, so Go's nil-slice-to-`null` trap doesn't apply to it.
- One health check serves both backends of the `sftp` backend service, so it has to be TCP: the VM has no HTTP health endpoint. The host opens its SSH port only after `users.json` loads, so an open port means ready. MIG autohealing keeps its own HTTP check on `/healthz`.
- A Debian VM in a passthrough backend accepts packets addressed to the forwarding rule's IP because the guest agent installs a local route for it. Normal GCE behaviour; Plan B's dev rehearsal proves it on this VM.
- konlet / `gce-container-declaration` was shut down on 2026-07-31 (Google deprecation notice), so instances run the container through cloud-init.
- A passthrough NLB doesn't rewrite ports, so the instance must answer on 22. The image listens on 2022 unprivileged and the container host publishes `22:2022`. Docker's iptables DNAT keeps the client's source IP for external traffic, so no host networking is needed (verify in inc 3a and inc 5). The instance's own sshd is disabled: instances are replaced, never logged into, so there's no operator SSH path and no port clash.
- Logs won't reach Datadog by themselves. The `datadog-integration` sink and forwarder were deleted on 2026-07-23 (FUSE-1000). The image doesn't bundle an agent: it logs JSON to stdout and sends metrics to `DD_AGENT_HOST`. On the MIG, the deployment runs a Datadog agent container beside it; on another runtime, that runtime's agent.
- Cloud NAT was removed for cost in FUSE-953 (#181). The host needs egress to config-service (public `run.app`) and Datadog. Default: Cloud NAT for the host subnet only. Record it with `wp decide` as a deliberate reversal for a new workload.
- VM hardening is deferred (Harry, 2026-10-20). Until Plan C's cut, customers keep shells on the VM and can read and write the whole bucket, `users.json` included. The host closes that by construction: no shells, and only `<user>/to_ilg/` and `<user>/from_ilg/` exist. Customers who rely on shell, exec or scp will break at the cut; Plan C's `auth.log` baseline gate finds them first.
- Password auth: nobody uses it today (Harry, 2026-10-20), but the host keeps the seam for it (inc 3b). When it's needed:
  - hashes only (argon2id), never plaintext;
  - offer both `password` and `keyboard-interactive`, since many clients send passwords through the latter;
  - pick the store then. **Not `users.json` while the connector still writes it:** its `SFTPUserConfigSchema` is a plain `z.object`, so a parse-and-rewrite would strip an unknown `password_hash` field from every record. fuse-ui already has an `sftpPassword` credential field, so config-service is the likelier source.
- The internal `support` user gets only `to_ilg`/`from_ilg`, like every other user, and not `support/logs/` (Harry, 2026-10-20).
- Today, a client that drops mid-upload probably leaves a partial object that gets ingested (gcsfuse flushes on close, and sshd closes the file on disconnect). The host deliberately doesn't. Unverified; the inc 3 prototype measures the VM's behaviour in dev so the difference is known, not assumed.

## Increments
<!-- Each independently implementable AND verifiable. Cite the criteria it discharges as
     (AC n,n). Tick with `wp tick`, which stamps `— done: <sha>` from HEAD; never hand-write it.
     Prefer 3-7 — more usually means the ticket is too big, so say that rather than splitting
     hairs.

     A PRECONDITION THAT IS NOT CODE goes on its own indented `gate:` line, with a confirmation
     box under it. Sign-off blocks on a ticked increment sitting above an unconfirmed gate, and
     `wp brief` shows unmet gates in its NEXT block — so "do not action this yet" stops being
     bold prose a fresh session can miss:

         - [ ] 6. Widen the subscription filter (AC 6) — verify: filter matches in dev
               gate: FUSE-1052 AND FUSE-1053 confirmed in prod
                     [ ] confirmed
-->
- [x] 1. Monorepo move, `code/` → `apps/connector`, behaviour-neutral, in its own PR (AC 8). — #317 merged; dev+prod deployed from apps/connector, prod plan Cloud Run only — done: b1fffd3
      - `git mv code apps/connector`. Move `tests/`, `docker-compose*.yaml` and `tests/Dockerfile` in under it; their `./code` and `code/` references are at `docker-compose.yaml:31,90,146,150`, `docker-compose-4pipeline.yaml:30,81,137,141` and `tests/Dockerfile:8,26`.
      - Rename the workflows to `connector-{on-push,manual-deploy,code-quality,blackbox-testing}.yaml` with `working_directory: apps/connector`, and `paths:` covering `apps/connector/**`, `iac/projects/bifrost-sftp-connector/**`, `iac/env/**` and the workflow file itself.
      - Delete `deploy.yaml` and `manual-deploy.yaml` **in the same PR**, so nothing deploys twice.
      - `connector-manual-deploy` fails unless `origin/master` is an ancestor of HEAD. A stale branch must not undo cutover switches; a stale manual deploy destroyed the SFTP DNS record on 2026-09-15.
      - `secops.yaml` jobs get `working_directory: apps/connector`. The SecOps report slug changes once.
      - Blackbox network name.
      - `CLAUDE.md` paths, plus a per-app `CLAUDE.md`.
      - Delete the empty root `package-lock.json`.
      - `scripts/get-key.sh` is already broken: it reads `tls_private_key.user_key`, which no longer exists. Delete it and say so.

      gate: Harry accepts the open branches and worktrees against `code/` rebasing across the rename
            [x] confirmed (Harry, 2026-10-20)

      — verify:
      - `git log --follow apps/connector/src/app.ts` keeps history;
      - `terragrunt render --format json` shows the same state prefix before and after;
      - PR checks green (`connector-code-quality`, `secops`, `connector-blackbox-testing`), with gitleaks not re-flagging the moved fixture keys;
      - after merge: `connector-on-push` deploys dev and the revision is healthy;
      - a CSV dropped into dev `FUSE_EC11DE9F4F/to_ilg/create_sales_order/` is archived;
      - the prod plan shows only the image tag;
      - the vault `waypoint.yaml` and fuse-mcp `services.json` are updated.
- [x] 2. Connector prep: inert switches and fixes for today's provisioning bugs, applied to both environments (AC 7,9). — #318 merged; dev+prod 3/2/0, ack 60s, DLT sub, VM group, admin IP reserved; provisioning e2e FUSE_9ABEDC586D — done: 5b702d2
      - Add `create_sftp_user_topic_id` and `create_sftp_user_subscription_id` to `outputs.tf`.
      - Add `lifecycle { prevent_destroy = true }` to `sftp_bucket` and `sftp_static_ip`, and `ignore_changes = [network_interface[0].access_config]` to `sftp_vm`.
      - Make `push_config` a dynamic block on a new variable `create_sftp_user_consumer` (`connector` | `host`, default `connector`, and set in `dev.tfvars`/`prod.tfvars` only). `host` also sets `enable_exactly_once_delivery = true`.
      - Raise `ack_deadline_seconds` from 20 to 60 now. Today a redelivery overlaps the SSH provisioning still in flight and can generate a second key.
      - Add a pull subscription on the `create_sftp_user` DLT topic, so an exhausted provisioning message can be recovered instead of lost.
      - Put `sftp_vm` in an unmanaged instance group (`google_compute_instance_group`, connector project) and output its self link. Membership is in place and changes no traffic.
      - Reserve a second regional address, `sftp_vm_admin_ip`, unattached for now; Plan B gives it to the VM when the static IP moves to the load balancer. Output it.
      - Firewall: port 22 on the VM from the passthrough health-check ranges (`35.191.0.0/16`, `209.85.152.0/22`, `209.85.204.0/22`).
      - `SFTP_ADMIN_HOST` (optional, validated in `app-config/schemas.ts`, from a tfvar defaulting to empty): when set, `createCustomer` SSHes there instead of `connector.config.host`.
      - Make the publish failure at `connector.config-handler.ts:466-473` fail the event, as its own comment at `:37-38` says it should.
      - Set `sftp_login_audit_stage = "off"` in `dev.tfvars` (it's `prep`; no agent was ever installed, so `off` is a straight revert of PR #312's IAM grants, label and metadata). Login audit now comes only from the host.
      - Await the `users.json` upload in `SFTPUserBuilder.updateUsersJson` (`sftp-user.builder.ts:196`), so a failed write fails provisioning instead of reporting ACTIVE for a user that disappears at the next reboot.

      — verify:
      - unit specs: a publish failure rejects; with `SFTP_ADMIN_HOST` set the SSH target is that address, and unset it's `connector.config.host` (today's behaviour);
      - dev and prod plans show in-place `~` only, with no `-/+` on any subscription;
      - a **scratch** dev subscription goes push → pull plus exactly-once in place, and a published message survives the switch;
      - after dev apply, a new dev SFTP connector still goes PENDING → ACTIVE through Cloud Run.
- [x] 3. Host foundation: prototype, then the SSH layer and users, as two stacked PRs (AC 2,5,6,10,11, proved locally). — #320-#323 merged; refusals and users.json edits proven live on sftp-next — done: 5d14485
      gate: no SFTP connector has `auth.mode` PASSWORD (count via `config-read`), or Harry accepts that password auth stays unsupported
            [x] confirmed (Harry, 2026-10-20: nobody uses password auth; leave room to add it later)

      **3a, prototype (evidence, not merged as product code).** About 300 lines on a branch: public-key auth from a test `users.json`, the virtual tree, list and stat, a staged upload to fake-gcs-server. Run OpenSSH `sftp`, WinSCP, FileZilla, paramiko and `ssh2-sftp-client` against it. The transcript must prove:
      - WinSCP's set-times after upload, FileZilla's directory listing, and `posix-rename` behave;
      - `TransferError` (or equivalent) separates a dropped upload from a clean close;
      - a resumed upload works through staging;
      - `x/crypto/ssh` only returns a connection after signature verification, with the matched key available;
      - Docker's `-p 22:2022` keeps client source IPs on COS;
      - in dev, what the **VM** does with a dropped upload today, for the record.

      **3b, the SSH layer and users** (`apps/host`, following wms-gateway's layout):
      - `cmd/host`, plus `internal/config` (env, validated once), `internal/hostkeys` (files, or a Secret Manager reference), `internal/users`, `internal/sshserver`, `internal/directories`, `internal/observability` (JSON `slog`, `datadog-go`).
      - `internal/users`, the `users.json` cache:
        - checks the object's generation every 15–30 s, plus a rate-limited refresh on an unknown username;
        - validates per record: a usable record has a username matching `^[A-Za-z0-9_.-]+$` and a parseable key; the rest are skipped and counted;
        - multi-key users are every record sharing a username;
        - records without `raw_username` still authenticate and are counted;
        - unknown `authorized_keys` options make start-up fail.
      - `internal/auth`, so password auth can be added later without touching the SSH layer:
        - one authenticator interface with a method per SSH auth type (public key now; password and keyboard-interactive later);
        - each user record holds a list of typed credentials, so a password hash can be added as another credential kind;
        - the server registers an `ssh` callback only for enabled methods: public key always, password and keyboard-interactive only behind `AUTH_PASSWORD_ENABLED` (default off, and nothing implements it yet);
        - tests pin that with the flag off a password attempt is refused without consulting any store, and that keyboard-interactive is never offered.
      - `internal/sshserver`:
        - host keys and the algorithm lists matched to the VM;
        - `MaxAuthTries` 6; a handshake timeout; caps on concurrent sessions per user and overall;
        - only `session` channels and only `subsystem sftp` accepted; shell, exec, pty, env, X11 and agent requests rejected; `direct-tcpip` and `tcpip-forward` refused;
        - the listener opens only after `users.json` has loaded;
        - `/healthz` on :8080.
      - `internal/directories`: the declared folder list in `apps/host/config/directories.json` (paths under `to_ilg/` or `from_ilg/`, validated at start-up, seeded with today's 5+5 from `sftp-user-builder/constants.ts` and `startup.sh.tpl`), plus the create-only reconcile code. Reconcile stays behind a flag that's off until Plan B.
      - A Dockerfile on `distroless/static-debian12:nonroot`, port 2022. The `host-code-quality` and `secops` jobs come in this PR.
      - Unknown usernames never appear in a log line or a tag (UJ AC 3 rule).

      — verify (unit tests plus compose):
      - auth matrix: a right key, the second key of a multi-key user, a wrong key, an unknown user and a malformed record all behave as specified;
      - a `users.json` edit is picked up within the poll interval;
      - `ssh u`, `ssh u ls`, `ssh -L`, scp and a pty request are all refused;
      - no listener before `users.json` loads, and `/healthz` fails when the listener stops;
      - an invalid directory list fails start-up;
      - the image runs as non-root with no shell in it.
- [x] 4. SFTP on GCS: the file system (AC 1,2,3, proved locally). — #324-#325 merged; real ingest via psftp, OpenSSH and WinSCP archived — done: a79a678
      - `internal/sftpfs` implements `pkg/sftp`'s handlers over GCS:
        - **Path mapping:** `/`, `/home` and `/home/<u>` are synthetic, list-only folders. `/home/<u>/{to_ilg,from_ilg}/…` maps to `<u>/{to_ilg,from_ilg}/…`. Paths are cleaned, then must resolve inside those two roots, otherwise the request is refused. NUL and control characters are rejected, and object keys are built only from the authenticated user and the cleaned path.
        - **Reads:** GCS range readers.
        - **Writes:** staged to `STAGING_DIR`, uploaded as one object on clean close, discarded on `TransferError` or disconnect. Open without truncate on an existing object downloads it into staging first, so resume works. The staging size is capped.
        - **Listing:** prefix plus delimiter, paged. Placeholder objects show as folders and never as files. Stat on a prefix returns a folder.
        - **Commands:** `Rename` (copy then delete; plain rename fails if the target exists; `posix-rename` overwrites); `Remove`; `Mkdir` (placeholder); `Rmdir` (only if empty); `Setstat` accepted and ignored; symlinks and hard links refused.
      - Metrics: `uploads`, `bytes`, `aborted_uploads`, `path_refused`, per user.

      — verify (compose with fake-gcs-server, plus a client matrix of OpenSSH `sftp`, paramiko, `ssh2-sftp-client` and `lftp`):
      - login lands at `pwd=/home/<u>`, `ls` = `to_ilg from_ilg`, and absolute and relative paths both work;
      - uploading `a b.csv` gives one object with an identical name and one finalize;
      - a disconnect mid-upload leaves no object;
      - a resumed upload completes with the right bytes;
      - rename, overwrite-rename, delete, mkdir, rmdir and set-times behave;
      - `cd ..`, `/home/<other>`, `/users.json`, `../../<other>/to_ilg`, an encoded `..` and a NUL in a name are all refused;
      - a 1 GB upload stays within the staging cap.
- [x] 5. Dev infrastructure on a temporary IP with prod dormant, as two stacked PRs (AC 1-7,10). — #326 #327 #329 merged; 3-zone MIG healthy, VM keys, ssh-audit parity, replica kill, prod dormant — done: 00c1028
      gate: dev host keys lifted from the dev VM into Secret Manager: every `/etc/ssh/ssh_host_*_key` listed, each piped over IAP straight into its secret (`sudo cat … | gcloud secrets versions add --data-file=-`, nothing on disk anywhere), fingerprints recorded and matched to `ssh-keyscan` of the VM, and `users.json` version history checked for signs the root path was used (`root`, system users, shell metacharacters in usernames)
            [x] confirmed 2026-10-21: three keys into `sftp-host-dev-ssh-host-*-key` v1, fingerprints match keyscan; users.json history clean (2026-10-20)

      **5a, workflows and a project shell.**
      - `host-{on-push,manual-deploy}.yaml` with `paths: apps/host/**, iac/projects/sftp-host/**`, plus a host leg in `tf-plan.yaml` (it hard-codes the connector project today) and `gen-check`.
      - The image tag is the `apps/host` tree hash (`git rev-parse HEAD:apps/host`), passed through `tf_var_image_name`, so an `iac/env` edit never rolls the MIG.
      - `iac/projects/sftp-host` contains:
        - a least-privilege SA with `storage.objectUser` on the bucket, via `_member` (no project-level `serviceAccountTokenCreator`, which `iam.tf:37-41` binds authoritatively);
        - `ssh_host_{rsa,ecdsa,ed25519}_key` secrets with `prevent_destroy` and an accessor binding;
        - `terraform_remote_state` on the connector project, using the split buckets (dev `gfs-bifrost-tfstate`, prod `gfs-bifrost-tfstate-prod`, as in `remote.tf:2`).
      - `host_enabled` is `true` in dev and `false` in prod.

      **5b, the serving infrastructure.**
      - Instance template: COS as a container host. cloud-init runs the host image with `--restart=always -p 22:2022` and its env vars (the image fetches its own host keys through its Secret Manager reference), a Datadog agent container beside it, and the instance's own sshd disabled.
      - Regional MIG across europe-west2-a/b/c, size 3, autohealing on `:8080/healthz`.
      - Two regional external passthrough backend services, both with a TCP:22 health check, connection draining and `CLIENT_IP` session affinity:
        - `sftp-test`: the MIG only, behind a forwarding rule on a **temporary** address. `sftp-next.integrations.freightops.dev` goes in the ilg-platform zone.
        - `sftp`: the cut's backend service. Its backends are switched per env by `vm_backend` / `host_backend` tfvars (both `false` here), and its forwarding rule on the static IP is behind `serve_static_ip` (`false`). Nothing serves through it until Plan B.
      - Firewall: 22 from 0.0.0.0/0; 8080 from the health-check ranges. No operator SSH.
      - Cloud NAT for the host subnet.
      - Update policy `max_unavailable=0`, `max_surge=3`.

      — verify, in dev against the real bucket:
      - real clients log in as `FUSE_EC11DE9F4F` on the temp IP: OpenSSH sftp, WinSCP, FileZilla, and paramiko or ssh2-sftp-client;
      - `ssh-keyscan` fingerprints from the temp IP equal the dev VM's, and `ssh-audit` gaps are only the listed unimplemented algorithms;
      - an upload is archived by Cloud Run (`fuse.*` ingest logs), and an egress confirmation file downloads;
      - deleting one instance: the client reconnects and the MIG self-heals;
      - a no-op apply leaves sessions up;
      - client IPs in host logs are the real client addresses (DNAT preserved them);
      - the same image digest that passed the compose suite is the one serving (AC 10);
      - host logs and metrics appear in Datadog;
      - the plan shows the `sftp` backend service with no backends and no forwarding rule, and the API accepts the MIG in both backend services (one instance group in two passthrough backend services; an assumption until then);
      - the prod plan shows only the SA, the secrets and no instances (AC 7).

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-22 [inc 5, AC 3, 4] **Real WinSCP on Windows (Matt Shaw).**
  - On the VM first (the connector's host address): WinSCP's default "preserve timestamp" SETSTAT after upload failed with `Permission denied` (code 3). The file still uploaded and archived, so this is existing VM behaviour, probably `gcsfuse` presenting the files as root-owned.
  - On the host: login at 09:39:26 UTC from 51.155.180.225 with the connector's own key (`SHA256:rFB8eNvJ…Sd8`). `HOSTTEST-master-data_mjs_2.csv` archived at 09:40:25. Matt saw no error, so the host accepts SETSTAT, though it doesn't keep the timestamp.
  - Locally, `sftp put -p` against the host succeeds; the file keeps its upload time and mode.
- 2026-10-22 [inc 2] **Provisioning end to end on the merged code.** Harry created the CSV connector `conn_8c3b81896c4e4c74b02dd904eb2c1bb6` on HJF in fuse-ui. The connector logged the whole provisioning run:
  - 09:00:38 UTC, `User key generation started`, then `User created`, `SSH key configured`, `Directories mounted`, `User added to users.json` and `users.json updated on GCS`;
  - 09:00:45, `User provisioned`, then `POST /events/v1/create_sftp_user` 204.
  - The user is `FUSE_9ABEDC586D` (raw `HJF`, RSA). All 10 skeleton folders are in the bucket, and the host serves them.
- 2026-10-22 [inc 5] **CSV through the host on that connector.**
  - The first upload went to `error/` on a canonical validation failure, `product.identifiers.businessId` undefined: the fuse-ui mapping had no `businessId` default.
  - After adding the default `product.identifiers.businessId = HJF`, `SFTPHOSTTEST006` archived and dedupe holds it.
  - "hjf test"'s mapping was briefly given two extra CSV rules for a pre-check (`SFTPHOSTTEST003` archived) and then restored to its 4 EDI rules.
  - The replay-service failure record for the first `SFTPHOSTTEST006` attempt remains; there's no delete API.
- 2026-10-22 [inc 5, AC 1, 3] **Real ingest through the host, end to end.** HJF's only ingesting SFTP connector is "hjf test" (`conn_1435…`, user `FUSE_4366B07EED`, EDIFACT). Its other two users (`FUSE_55C26F6079`, `FUSE_2C8D3A4425`) map to no current connector.
  - Built a PRICAT from the archived `CT-REAL2-PRICAT.EDI` with new values (SKU `SFTPHOSTTEST001`, GTIN `5060696999014`).
  - Added a temporary second key for that user and uploaded with `sftp` via `sftp-next` into `to_ilg/create_master_data/` at 08:54:35 UTC.
  - The connector validated and emitted it. Dedupe holds `SFTPHOSTTEST001` (correlation `67a81ade…`), snap-adapter's `create_acknowledge` came back, and the file was in `archive/` at 08:54:37.
  - The key was then removed; `users.json` is identical to before. File B (`SFTPHOSTTEST002`, GTIN `5060696999021`) is kept for the WinSCP tester.
- 2026-10-22 [inc 5, AC 4] #329 merged as `00c1028`. Dev rolled 3/3 HEALTHY onto template `…20261022083616760200000001`; prod plan `No changes` (the host stays dormant). `ssh-audit` of `sftp-next` against the dev VM:
  - only on the host: `mlkem768x25519-sha256` (the post-quantum stand-in);
  - only on the VM: `sntrup761x25519` x2, `group18-sha512`, `umac-64/128(-etm)`, `hmac-sha1-etm`, all of which `x/crypto` doesn't implement;
  - every other kex, cipher, MAC and host-key algorithm is identical;
  - the host-key fingerprints are still the VM's.
- 2026-10-21 [inc 5, AC 5, 1, 2] Real login on `sftp-next`, using a dedicated test record (`FUSE_HJFHOSTTEST`, raw `HJF`, throwaway Ed25519 key) added to dev `users.json` under a generation precondition:
  - The login worked on the first try, 11 s after the write, with no restart. The client verified the host against the VM's pinned keys (`HostKeyAlias` = the VM IP).
  - The session started in `/home/FUSE_HJFHOSTTEST` and showed only `to_ilg` and `from_ilg`.
  - The host logged `sftp login` with `remote: 31.51.121.239:51444`, the client's real IP, so the passthrough NLB and `docker -p` keep the source address. The entry also carried the fingerprint and both usernames.
  - The record was then removed (the file is identical to before), the next login was refused, and the user left nothing in the bucket.
  - The sub-folders were absent: reconcile runs only at start-up and only with `DirectoryReconcileEnabled`, and in Plan A folder creation belongs to connector provisioning, which a hand-added record skips.
- 2026-10-21 [inc 5, AC 6] Replica kill: `sftp-host-dev-mznm` (zone b) deleted at 21:24:52 UTC.
  - An `ssh-keyscan` of `sftp-next` every 5 s answered 60 out of 60 times, so there was no outage.
  - The MIG's `repair.recreateInstance` ran 7 s after the delete. The new instance was inserted at 21:31:01, and all 3 were HEALTHY by about 21:33.
- 2026-10-21 [inc 2, 5, AC 7, 9] Prod approved by Harry and applied:
  - connector run 39660819167 (`8caeb75`): `3 added, 2 changed, 0 destroyed`;
  - host run 39661812650 (`71e9bee`): `11 added`.
  - Prod after:
    - revision `sftp-connector-prod-cr-00112-rsr` Ready on `8caeb75`, with no WARNING+ logs;
    - `SFTP_ADMIN_HOST` not set, so provisioning still goes to the connector host;
    - sub ack deadline 60 s, and the DLT sub exists;
    - the VM is still on 34.89.6.210 (`OpenSSH_9.2p1`), and the admin IP 34.147.133.18 is `RESERVED`, not attached;
    - the host is dormant: no MIG, no forwarding rule, and 0 versions in all 3 prod secrets.
  - Parked runs: 7 older runs cancelled. 31 zombie runs from 2025 can't be cancelled or rejected (422), and nothing can deploy from them.
- 2026-10-21 [inc 5, AC 4] `ssh-audit` diff, host (`sftp-next`, 34.147.147.5) vs dev VM (34.142.66.200), and the VM's `sudo sshd -T`. The host was also offering four SHA-1 algorithms the VM never offered (`group14-sha1`, `ssh-rsa` host signatures, `hmac-sha1-96`, `ssh-rsa` client signatures): `x/crypto` defaults. Fixed in draft #329, which pins the VM's lists minus what's unimplemented and adds back `group-exchange-sha256` and `group16-sha512`. AC 4 waits on #329 plus a rerun of the diff. Real gaps: `sntrup761` (ML-KEM replaces it), `group18-sha512`, `umac-*`, `hmac-sha1-etm`. Banner reads `SSH-2.0-Go`, not OpenSSH.
- 2026-10-21 [inc 5, AC 4] Host-key gate met. All three keys (RSA 3072, ECDSA, Ed25519) went from the dev VM into `sftp-host-dev-ssh-host-*-key` v1:
  - Route: `sftpuser` with the tfstate admin key in a throwaway `ssh-agent`, then `sudo cat … | gcloud secrets versions add --data-file=-`. Nothing hit disk, the agent was killed afterwards, and `gcloud compute ssh` wasn't used.
  - The admin IP isn't on the VM yet (access_config is ignored until S1), so this went over the static IP.
  - The fingerprints derived from each stored secret, `ssh-keyscan` of the VM and `ssh-keyscan` of the host on the temp IP all agree: RSA `9kGzafft…UWYY`, ECDSA `/pBGyzAC…YiY4`, Ed25519 `VNlCUVeW…e4wo`.
- 2026-10-21 [inc 5, AC 6 partial] #327 applied to dev with 12 adds (the SA and secrets were already in state from #326). There are 3 instances, one each in a/b/c, all RUNNING and HEALTHY on autoheal (`/healthz`) and on the `sftp-host-dev-test` backend. `sftp-next.integrations.freightops.dev` resolves to 34.147.147.5. The host offers `publickey` only.
- 2026-10-21 [inc 1, 2, AC 7-9] The stack drained to master: #317 `b1fffd3`, #318 `5b702d2`, #320–#325, #326 `8caeb75`, #327 `71e9bee`. Every dev apply succeeded. Prod plans from the parked Deploy runs:
  - #317: `0/1/0`, Cloud Run only.
  - #318: `3/2/0`, the admin IP, the VM's instance group, the DLT sub, Cloud Run and the ack deadline; the VM itself isn't touched.
  - host (#326): `11/0/0`, the SA and 3 secrets.
  - Dev after #318: `create_sftp_user` sub ack deadline 60s, the DLT sub exists, `sftp-connector-dev-cr-00858` Ready on `5b702d2`, the unmanaged group `sftp-connector-dev-sftp-vm` (b, size 1) and the admin IP 34.147.156.89 reserved. The VM still serves on the static IP, and there were no connector ERROR logs in 30 min.
- 2026-10-21 [inc 5, built, not applied] PRs #326 (5a: workflows, service account, secrets) and #327 (5b: instance group, load balancers, NAT, DNS), stacked on #325:
  - `terraform validate` clean;
  - read-only plans against real state: dev `23 to add` (11 + 12), prod `11 to add` (5a only, dormant), `0 to change, 0 to destroy` in both;
  - the cloud-init template rendered with stand-ins parses, and its `docker run` carries the right env, bucket and secret references.
  - Not yet applied: dev applies after the stack merges. Then the host keys are lifted, then #327's instances boot.
- 2026-10-21 [host-key gate, users.json half] Every version of `users.json` was read and scanned:
  - dev: 154 versions from 2025-09-30 to 2026-10-21, 107 distinct usernames; prod: 33 versions from 2025-09-30 to 2026-10-08, 39 distinct usernames;
  - no usernames outside `^[A-Za-z0-9_.-]+$`, no system users (`root`, `sftpuser` and others), no shell metacharacters, no keys with `authorized_keys` options;
  - neither bucket has a lifecycle rule, so the history is complete back past #140, and gcsfuse can't delete old versions.
  - No sign the root path was ever used. The host keys themselves are still to be lifted.
- 2026-10-20 [dev e2e] **FileZilla, run by Harry** against the host image run locally (`127.0.0.1:2022`, dev bucket, as sftpfive `FUSE_EC11DE9F4F`, with the folder-time fix):
  - "spot on";
  - 3 logins;
  - an upload of a master-data CSV into `to_ilg/create_master_data/` was ingested by dev (8 records held by dedupe, file routed to `error/`, as expected for DAZZA).
  - Torn down: container, scratch users file, both uploaded objects, the 8 dedupe records, the copied credentials, and the test keys.
- 2026-10-20 [dev e2e, ahead of inc 5] The real host image, run on Harry's machine against the real dev bucket `sftp-connector-dev-storage`:
  - setup: ADC credentials; a scratch users file `hjf-scratch/users.json` holding `FUSE_EC11DE9F4F` (DAZZA sftpfive) with a key made for the test; no connector config changed.
  - **Ingest:** an `sftp put` of `HJFE2E141720.csv` into `to_ilg/create_sales_order/`, under the exact name, then the full pipeline:
    - sftp-connector dev: `Incoming file event`, then `Records validated`, then `Records to send resolved`, then `Emitting records`;
    - collector `Record stored`, dedupe `Record published`, snap-adapter `Entity creation in SNAP failed` (DAZZA has no Snap backend in dev, as expected), replay `Failure stored`, collector `Record marked failed`;
    - sftp-connector `File routed` to `error/`.
  - **Real GCS operations:**
    - a download of an object placed in `from_ilg`;
    - mkdir in `to_ilg`;
    - `posix-rename` overwrites, and a plain rename onto an existing file is refused (`file already exists`): the copy precondition works on real GCS;
    - set-times and chmod accepted;
    - resume (`put` half, `reput`): `cmp` identical;
    - a 200 MB upload killed mid-way leaves no object.
  - **PuTTY `psftp` 0.78** (the SSH/SFTP code under WinSCP and FileZilla), in a container:
    - login and listing;
    - WinSCP's temp-name pattern (`put x.filepart`, then `mv` to `x`), delete-then-rename over an existing file, chmod, resume from offset 1000000 (`cmp` identical), mkdir and rmdir;
    - into `create_sales_order` with the temp-name pattern: dev logs `File is not a valid type` for the `.filepart` (ignored), then the renamed `.csv` is ingested and routed. That's the same as WinSCP on the VM today.
  - **Found and fixed (#325, `caf75c4`):** folder modified times went out as Go's zero time, shown as `Jan 1 0001` in `ls -l` and wrapping to 2042 in the 32-bit timestamp. Folders now carry the host's start time; the tests fail without the fix.
  - **Cleanup:** the scratch users file and every test object deleted; both dedupe records released. replay-service still holds 2 dev failure records from the test (no delete API).
- 2026-10-20 [inc 4] PRs #324 (GCS object store, `exit-status`) and #325 (`sftpfs`), stacked on #323:
  - `go test -race` passes everywhere, and `sftpfs` passes 10 times in a row (21 file system tests through the real `pkg/sftp` client, plus a 13-case path table);
  - mutation checks: disabling the abort path fails the dropped-upload test, and removing `exit-status` fails its test;
  - 6 adapter tests against fake GCS; golangci-lint shows 0 issues.
  - **Real image against fake GCS:**
    - **OpenSSH `sftp`:** the batches pass (tree, `a b.csv`, escapes refused, mkdir and rmdir, download, a resume that `cmp`s identical, set-times, rename-over);
    - **dropped upload:** a 300 MB upload killed mid-way leaves no object;
    - **`scp`:** modern `scp` up and down rc 0 (rc 1 before the `exit-status` fix); `scp -O` refused;
    - **refusals:** exec and `-L` forwarding refused, and the other user sees only their own files;
    - **paramiko** and **`ssh2-sftp-client` 12** pass.
- 2026-10-20 [inc 3b, second half] PR #323, stacked on #322:
  - `go test -race` passes in every package; the SSH server's 12 tests pass 10 times in a row; golangci-lint shows 0 issues;
  - image smoke test against fake GCS:
    - `/healthz` is 503 until `users.json` exists, then 200;
    - an OpenSSH login is accepted and logged with `raw_username` and fingerprint;
    - exec is refused, and sftp is refused (no file system until inc 4);
    - the served host-key fingerprint equals the mounted key;
    - the image runs as `nonroot` with no shell.
  - Every increment 3 piece has landed across #320, #321, #322 and #323.
- 2026-10-20 [inc 3b, first half] PRs #320, #321 and #322, stacked on #318. Go 1.27.1:
  - `go build`, `go vet`, `go test -race` and golangci-lint v2 clean at each of the three commits independently;
  - 43 tests: config 5, observability 2, users 14, auth 7, directories 10, and 3 GCS adapter tests against fake-gcs-server (`-backend memory`);
  - the CI job runs fake GCS too.
  - Not yet built: host keys, the SSH server, health, the Dockerfile and wiring (inc 3b, second half).
- 2026-10-20 [inc 3a] Prototype: about 330 lines of Go on `x/crypto/ssh` v0.58.0 and `pkg/sftp` v1.13.11, run against fake-gcs-server. The source is in the session scratchpad and isn't committed. Results:
  - **OpenSSH `sftp`:**
    - `pwd` is `/home/FUSE_PROTO` and `ls` is `from_ilg  to_ilg`; absolute and relative paths both work;
    - `put "a b.csv"` gives an object with an identical name;
    - `/home/OTHER`, `/users.json`, `../../OTHER/...` and mkdir in `/home/FUSE_PROTO` are all refused; mkdir and rmdir inside `to_ilg` work;
    - the second key of a multi-key user works, and a wrong key is refused.
  - **Dropped upload:** an `sftp` killed mid-upload of 300 MB gives `transfer_error: unexpected EOF` then `upload_discarded`, and no object. `pkg/sftp` calls `TransferError` before `Close` for every handle still open when the session ends (`request-server.go:206-216`).
  - **Resume:** `put` half then `reput` full: the reopen has `trunc:false, append:true`, the server stages the existing object and appends, and `cmp` gives identical bytes.
  - **Set-times and rename:** `put -p` and `chmod` arrive as `Setstat`, accepted and ignored. OpenSSH `rename` arrives as `posix-rename@openssh.com` and overwrites an existing target.
  - **Refusals:** shell (`pty-req`, `shell`), `exec`, `direct-tcpip` forwarding to 169.254.169.254, and legacy `scp -O`. Modern `scp` (SFTP mode) works.
  - **Audit:** a client offering a known public key without the private key gets `Server accepts key` from the callback, then `Permission denied`, and no `logged_in`. Only a completed `NewServerConn` is a login.
  - **paramiko** (container): cwd, listing, stat on a synthetic folder, `putfo`, `utime`, `posix_rename`, `getfo`, and the other user refused.
  - **`ssh2-sftp-client` 12** (container, RSA key): cwd, `list`, `exists`, `put`, `rename`, `get`, and the other user refused.
  - **Bug the real server must avoid:** `ReadAt` at or past end of object must return `io.EOF`. Returning the GCS range error made OpenSSH's `get` report `Failure` even though the bytes were complete.
- 2026-10-20 [inc 2] Branch `hjf/sftp-connector-host-prep`, stacked on #317:
  - `apps/connector`: 44 files / 880 tests pass (5 new: publish failure fails the event; `SFTP_ADMIN_HOST` set vs unset picks the SSH target; a failed `users.json` upload rejects; a new user is written as a three-field record). Lint and `build:check` clean.
  - `terraform validate` (1.9.0) clean.
  - Read-only plans (`-lock=false`, dummy Datadog keys so only those env lines differ):
    - **dev:** 3 to add (admin IP, VM instance group, DLT subscription), 3 to change, 3 to destroy. The VM change is in place: `enable-osconfig` metadata removed. The subscription's ack deadline goes 20 → 60. The 3 destroys are #312's `prep` grants (log/metric writer IAM members) and the `osconfig` service resource, which has `disable_on_destroy = false`.
    - **prod:** 3 to add, 2 to change, 0 to destroy; the VM is untouched.
  - A first prod plan run from a terragrunt cache initialised against dev state showed mass replacements, and `prevent_destroy` refused the bucket and static-IP destroys. Rerun with a clean cache, it was as above.
  - **Push → pull rehearsal** on a scratch dev topic and subscription (`hjf-scratch-sftp-sub-rehearsal`, destroyed after):
    - Terraform showed `~ enable_exactly_once_delivery false -> true`, `- push_config`, `1 to change`: in place;
    - a message published while the subscription was push was pulled once the subscription became pull;
    - Pull returned `FAILED_PRECONDITION: This method is not supported for this subscription type` for about the first minute after the change.
- 2026-10-20 [inc 1] PR #317 CI all green: code quality (test, lint, build), blackbox, dependency audit, image scan, gitleaks, Terraform scan. The dev plan is `0 to add, 2 to change, 0 to destroy`: the Cloud Run image, plus `fuse-ops-agent` added to the dev VM's labels (#312's `prep` stage, which hadn't reached the VM yet; label-only, in place). Inc 2's `stage = off` removes it again.
- 2026-10-20 [inc 1] Local, branch `hjf/sftp-monorepo-move` (pre-merge; no dev deploy is possible because the renamed `workflow_dispatch` workflows aren't on master yet):
  - `apps/connector`: `pnpm test` 43 files / 875 tests passed; `pnpm lint` clean (259 files); `pnpm build:check` clean.
  - `docker compose config` on both compose files resolves every path to `apps/connector/{.npmrc,src,tests,tests/data,tests/results}`, with project name `sftp-connector` (network `sftp-connector_default` unchanged).
  - `docker build -f dockerfile .` from `apps/connector` (the CI build context) succeeds.
  - Blackbox suite run as CI runs it, from `apps/connector` (host ports remapped locally only, 8085→18085 and 3000→13000, because another session's emulator and a local Next server held them): 14 suites, identical case for case to master's nightly run of 2026-10-20 06:13 (10 ingest suites with 0 cases, 4 confirmation suites passed).
  - `iac/` untouched, so the connector's state prefix can't have changed; `terragrunt render` not needed.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- [inc 2] A brand-new dev SFTP connector provisioning end to end through `create_sftp_user` on the merged code. A direct test needs config-service creds, which aren't readable locally (a GH secret), and won't be extracted from a running service. Do it through fuse-ui, or with Harry.
- [dev e2e] The WinSCP application itself (FileZilla verified by Harry; WinSCP's PuTTY code verified as `psftp`); the load balancer and MIG network path; host keys from Secret Manager; Datadog. All inc 5.
- [inc 3a] WinSCP and FileZilla: they can't run on this machine. They move to inc 5's real-client check in dev.
- [inc 3a] Docker `-p 22:2022` keeping the client source IP on COS: needs a real instance; inc 5.
- [inc 3a] What the VM does with a dropped upload today: the VM is down (GCP incident). To measure when it's back.
- [inc 1] The post-merge dev deploy through `connector-on-push`, the dev CSV drop, and the prod plan showing only the image tag. They need the merge.

## Rollout & rollback
<!-- Added on demand. Written at plan time; amend in place as it changes.
     `Shared state touched:` is the single home for the five classes git does not own — a dev
     deploy, a prod config write, a Datadog monitor, a CI var or secret, cross-repo IaC. Reverting
     the branch undoes none of them, so if they are not written here they are not written down. -->
- **Order:** 1 → 2 → 3 (a→b) → 4 → 5 (a→b). Inc 2 must apply in **both** environments before 5a exists, so the host's remote state can read the new outputs.
- **Flags/config:**
  - `create_sftp_user_consumer` = `connector` in both environments (inert until Plan B);
  - `SFTP_ADMIN_HOST` unset in both environments (inert until Plan B);
  - host `vm_backend`, `host_backend`, `serve_static_ip` all `false`;
  - host directory reconcile off;
  - `host_enabled` = dev `true`, prod `false`;
  - `ack_deadline_seconds` on `create_sftp_user` goes 20 → 60.
- **One-way doors:** none in this plan. The host keys' Secret Manager versions are protected by `prevent_destroy`, and after Plan C they're the only live copy apart from the VM's machine image.
- **Rollback:**
  - inc 1: revert the PR (the SecOps slug change is cosmetic);
  - inc 2: revert;
  - incs 3–4: nothing shared;
  - inc 5: `host_enabled=false`, which removes the MIG and NLB and keeps the SA and secrets.
- **Shared state touched:**
  - dev connector deploys;
  - prod connector applies (inc 1 image, inc 2 IaC);
  - dev host infrastructure;
  - Secret Manager host-key versions added by hand;
  - a test DNS record in the ilg-platform zone;
  - Cloud NAT (dev);
  - the fuse-mcp `services.json` directory;
  - the vault `waypoint.yaml`.
- **Proof in prod:** inc 1/2 prod deploys healthy, with ingest throughput at baseline in Datadog (`service:sftp_connector`); prod host plan dormant.

## Options considered
<!-- Added on demand. Why this approach and not the others — the thing the planning agent is
     asked for and the plan has otherwise had nowhere to put. Promote to a durable record with
     `wp decide --record` when it is worth defending in a review six months out. -->
- **Chosen: our own Go server on `x/crypto/ssh` + `pkg/sftp`** (Harry, 2026-10-20). Our needs are narrow: public keys, two folders, GCS, Fuse provisioning and audit. Owning the server makes GCS, user management and the folder structure ours to shape. It also removes the AGPL question, gives login audit the client port and a signature-verified login, and lets us decide what a dropped upload does. The cost is client compatibility and hardening being ours, managed by the client matrix and the load-balancer split.
- **Rejected: SFTPGo plus a Node control process.** It's mature, but AGPL, a hook-and-log-parsing integration, and no client port for audit.
- **Rejected: our own SSH protocol code.** We own the server, not the protocols.
- **Rejected: Node's `ssh2` as the server.** Its SFTP server side is low-level and much less used than `pkg/sftp`.
- **Rejected: OpenSSH plus gcsfuse in a container.** It keeps every fragility (Linux users, sync, mounts) and multiplies it by the number of replicas.
- **Chosen: Go for the whole host, provisioning and audit included,** with contract types generated from the Zod schemas (wms-gateway / audit-service precedent) and golden fixtures for `UserCreationResponse`.
- **Rejected: a Node sidecar for provisioning.** That would bring back two processes in one image.
- **Chosen: a regional MIG behind a passthrough NLB.** There's no cluster to own. The NLB preserves client IPs (needed for audit and allowlists) and reuses the regional static IP.
- **Rejected for now: GKE Autopilot.** It's a cluster to run for one workload, and the rest of Fuse is Cloud Run. Because the image is portable, moving to it later is a deployment change, not a rebuild.
- **Rejected: Cloud Run.** It can't serve raw TCP 22.
- **Chosen: a portable image on plain container hosts.** Nothing in the image depends on the VM: config by env, keys by mounted file or secret reference, ADC for GCP credentials, stdout logs, an unprivileged port. The MIG instances hold no state and allow no login.
- **Rejected: host networking and VM-installed tooling** (agents, key files written by cloud-init). It would tie the image to a GCE VM.
- **Chosen: the host owns the folder skeleton as a declared list.** Today it's hard-coded twice (`constants.ts` and `startup.sh.tpl`) and only reaches existing users when the VM reboots.
- **Rejected: deriving folders from `@gfs-bifrost/types` use cases.** The folder names aren't uniform (`create_<x>` inbound, `<x>_confirmations` outbound, `work_order_confirmation_confirmations`), and not every use case has an SFTP folder, so a mapping would hide decisions an explicit list makes visible.
- **Chosen: staged writes**, matching gcsfuse's offset writes and resume. Streaming writes that only accept in-order data would be leaner, but would break a client that resumes.
- **Chosen: `users.json` stays the user store.** That means zero change for config-service, fuse-ui and the runbooks, and rollback to the VM keeps working because the sync reads the same file.
- **Deferred: Firestore or config-service as the user store**, as a later, separate migration.
- **Chosen: a new `iac/projects/sftp-host` project**, following the precedent. MIG rolls are decoupled from Cloud Run deploys, and the blast radius is smaller. The IP, DNS, bucket and topic stay in connector state, because they outlive the VM.
- **Rejected: extending the connector project.** Every connector deploy would plan the MIG.
- **Chosen: reuse the IP**, since customers are given the IP literal, and partners may allowlist it.

## Handback
<!-- Append-only, newest first. Written by `wp handback`, never by hand.
     Sign-off never clears this section — a refuted approach is exactly what a
     later session needs and what ## Learnings would have deleted. -->

### 2026-10-22 11:05
- **stopped:** Plan A complete 2026-10-22; Plan B (provisioning in the host, host login audit, cut tooling, dev cut) is next
- **tried and abandoned:** Learnings not promoted, resolved or refuted: (1) create_sftp_user dead-lettering into a DLT with no subscription was fixed by #318, which added the subscription. (2) 'scripts/get-key.sh is broken' was refuted 2026-10-20: it reads orphaned tfstate entries by design (apps/connector/CLAUDE.md).
- **turn:** agent

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-10-22** — No explainer at Plan A sign-off: customers are still served by the VM, so present-tense system truth is unchanged. The SFTP-serving explainer is owed at Plan B sign-off, once the host serves dev.

- **2026-10-22** — Sign-off: 18 learnings promoted to known-context.md (SFTP host migration (2026-10)) and architecture.md (G5 reworded, new G6: keep the static IP; guardrail paths moved to apps/connector). Two resolved/refuted items to Handback. Guardrails G1-G6 touched by renames only; none breached.

- **2026-10-22** — Host accepts SETSTAT as a no-op (no timestamp/mode kept) where the VM rejects it with Permission denied; kept as-is — strictly friendlier for WinSCP defaults, and the VM never preserved timestamps either. Revisit only if a customer syncs by remote mtime.

- **2026-10-21** — Host algorithms pinned to the VM's sshd -T lists rather than x/crypto defaults (which add SHA-1 kex/MACs/signatures the VM never offered); ML-KEM kept as the PQ stand-in for sntrup761. Draft #329.

- **2026-10-21** — Inc 5 ships as #326 and #327. The host instances sit on the default network beside the VM, so both can be backends of one backend service, and port 22 is already open there. Cloud NAT on the default subnet (PGA is off) reverses FUSE-953's NAT removal for this workload only. Datadog is deferred: COS ships logs and metrics to Cloud Logging and Monitoring, and the Datadog agent waits for a Secret Manager-held API key with Plan B's monitors, rather than putting the key in instance metadata. The 5b merge is gated on the dev host keys being in Secret Manager.

- **2026-10-20** — Inc 4 ships as #324 (GCS store, plus the exit-status fix found by the scp smoke test) and #325 (sftpfs and wiring). The adapter implements sftpfs.Store using standard fs.ErrNotExist / fs.ErrExist. A no-overwrite copy checks the target before the precondition, for emulator parity.

- **2026-10-20** — Inc 3b is split to stay near the PR size target: #320 (scaffold, config, observability, CI), #321 (users and auth), #322 (directories and the GCS adapter), then a further stacked PR for host keys, the SSH server, health, the Dockerfile and wiring. The directory list lives in internal/directories/directories.json (go:embed can't reach apps/host/config/). The Datadog service tag is sftp_host.

- **2026-10-20 (Harry)** — Password auth: no connector uses it, so the host ships public-key only, with an auth seam (typed credentials per user, one authenticator interface, password/keyboard-interactive callbacks behind AUTH_PASSWORD_ENABLED, default off) so it can be added later without reworking the SSH layer.

- **2026-10-20** — Plan A ships as a native GitHub stack: #317 (inc 1, hjf/sftp-monorepo-move) then #318 (inc 2, hjf/sftp-connector-host-prep). Frontmatter tracks the stack's tip branch and worktree; later increments stack on it.

- **2026-10-20** — Inc 2 adds no health-check firewall for the VM: sftp_fw already allows 22 from 0.0.0.0/0 on the default network with no target tags, so the passthrough health-check ranges are covered. A dedicated rule only matters once Plan C re-scopes port 22. SFTP_ADMIN_HOST is a dynamic env block, absent unless set, so the default plan doesn't change Cloud Run's env.

- **2026-10-20** — Inc 1 keeps scripts/get-key.sh: apps/connector/CLAUDE.md documents it as reading orphaned tfstate entries, so 'broken' wasn't established. The connector's CLAUDE.md moves to apps/connector with a short root CLAUDE.md as the layout index; README untouched. Biome and vitest exclude the moved tests/ so lint and test scope are unchanged. Inc 1 ships on branch hjf/sftp-monorepo-move.
- 2026-10-20: the host is our own Go server on `golang.org/x/crypto/ssh` + `github.com/pkg/sftp`, not SFTPGo (Harry). It makes GCS, user management and the folder structure ours to shape, removes the AGPL question, and gives login audit the client port and a signature-verified login.
- 2026-10-20: `support/logs/` is not exposed to the `support` SFTP user on the host; it gets only `to_ilg`/`from_ilg` like everyone else (Harry).

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
(none)
