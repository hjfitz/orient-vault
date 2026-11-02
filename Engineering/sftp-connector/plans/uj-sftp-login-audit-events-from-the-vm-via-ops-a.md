---
ticket: none
title: UJ SFTP login audit events from the VM via Ops Agent
service: sftp-connector
status: abandoned
created: '2026-10-15'
updated: '2026-10-20'
repo: /home/hjf/code/fuse/sftp-connector
worktree: /home/hjf/code/fuse/sftp-connector/.claude/worktrees/audit-sftp-login-events
branch: hjf/audit-sftp-login-events
base: origin/master
base_sha: d90895044
pr: '312'
tags:
- waypoint
- plan
programme: Audit Service
unit: UJ
impl_model: opus
impl_effort: high
reason: 'Halted after inc 1 (Harry 2026-10-20): login audit moves to the Go SFTP host
  (sftp-host-b inc 2).'
---
# UJ SFTP login audit events from the VM via Ops Agent

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
> SUPERSEDED 2026-10-20 — halted after inc 1 (Harry). SFTP login audit now comes from the Go SFTP host ([[sftp-host-b-provisioning-login-audit-and-dev-cut]] inc 2), and the VM is retired by [[sftp-host-c-prod-cutover-and-vm-decommission]]. Everything below is kept as the record of the Ops Agent design.

Record every SFTP login to the Fuse SFTP VM as an audit event with source IP, time, business ID and connector ID (Audit Service unit UJ; out-of-ticket; decisions in `Bifrost/Audit Service/Migration State.md`, 2026-10-15). The path is: sshd's journal lines → Ops Agent, installed by an OS Config policy assignment (no SSH, no reboot) → Cloud Logging → a sink on trusted sshd fields → Pub/Sub → sftp-connector, which resolves the username to a connector and publishes an `sftp_login` AuditMessage → audit-service, which keeps it for about a year. Done means a real prod customer login shows in the fuse-ui audit log with its IP, connector and business, and the VM still recovers from a reboot.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [ ] 1. A real accepted login on the prod VM appears in audit-service and the fuse-ui audit log within ~2 min as `sftp_login` / `logged_in`, with `actor.ip`, the source port, the key fingerprint, and `tenantId` = the user's businessId from `users.json` (`raw_username`). `details.connectorId` is set whenever that username has a connector.
- [ ] 2. A failed attempt on a username in `users.json` (wrong key, closed before auth, failed password) is stored as `login_failed` with a `failureReason` (dev evidence; in prod only from organic traffic).
- [ ] 3. Attempts on usernames not in `users.json` (`Invalid user`, the `sftpuser` admin, system users, anything else) are counted in `fuse.sftp_login.unknown_user{reason}` and never stored. A username from an `Invalid user` line never appears in a log or a tag.
- [ ] 4. Only lines sshd itself wrote become events: a `logger -t sshd "Accepted publickey for …"` from a customer shell matches nothing (sink filter on `_COMM` and `_UID=0`).
- [ ] 5. Redelivery is idempotent (deterministic `eventId`), and a lookup or publish failure nacks rather than dropping. After `MAX_TRANSIENT_DELIVERY_ATTEMPTS` the event is counted as `sftp_login.dropped` and acked, and it can be backfilled from Cloud Logging with the same eventIds.
- [ ] 6. The VM still recovers. After the agent policy is applied: (a) a dev reboot runs `startup.sh` to completion ("Sync Run Complete" in the serial log) and a dev login works; (b) the prod and dev plans for the VM are in-place label/metadata only, with no `service_account`/scopes/`machine_type`/`boot_disk` diff, so `allow_stopping_for_update` never fires.
- [ ] 7. Rollback is proven in dev: the stage `removing` uninstalls the agent (assignment report COMPLIANT with the package absent), then `off` deletes the assignment. The sink's `disabled` is a working kill switch.
- [ ] 8. The agent's first start does not replay months of journal into audit-service: the sink only exports entries at or after the per-env cutoff timestamp.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- **SFTP VM** (`iac/projects/bifrost-sftp-connector/compute.tf`): labels plus `enable-osconfig` metadata only. `startup.sh.tpl` and `sshd_config` are unchanged. `allow_stopping_for_update = true` at `compute.tf:15` makes any stop-requiring diff a silent VM stop, so read every plan for it.
- **New GCP resources in sftp-connector IaC:**
  - `google_project_service` osconfig (`disable_on_destroy = false`; the project is shared)
  - `google_project_iam_member` logWriter for the VM SA. Never `_binding`, since `iam.tf:37-41` shows the authoritative form in use.
  - `google_os_config_os_policy_assignment`
  - a `google_logging_project_sink` plus a writer-identity publisher grant
  - topic `sftp_login_<env>.v1` and a push subscription
- **New push route** `POST /events/v1/sftp_login` (`code/src/controllers/pubsub.controller.ts:99-127`) and a new `code/src/core/sftp-login-audit/`. It reuses `connector.config-handler.ts:241-311` `getConfigByUsername` and `pubsub/audit-event.publisher.ts`.
- **Contracts:**
  - A new `sftp_login` kind in `@gfs-bifrost/audit`, 0.3.0, in pkg-node.
  - The kind is published to the existing `audit.<env>.fuse.v1`.
  - audit-service per-kind retention (`expireAt` plus a partial TTL index): a separate audit-service change, A1.
  - fuse-ui labels: a separate fuse-ui change, F1.
- **Fuse MCP:** `pubsub-topology.json` (new topic, sink as publisher) and `api-endpoints.json` (new route).
- **Observability:**
  - New `fuse.sftp_login.*` metrics.
  - The `[FUSE] Audit events not published` monitor (observability#65) says sftp-connector failures are "lost". That's no longer true for `sftp_login`, which redelivers, so update its text and tag publishes by `kind`.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, not invented. -->
- **No logging agent runs on either VM.** Only `serial_port_1_output` reaches Logging, and it has no sshd lines. Established with live `gcloud logging read` 2026-10-15.
- **osconfig is off in both projects.** Neither VM has `enable-osconfig`, and project metadata is empty. Established with read-only gcloud by the grounding review.
- **The Ops Agent `systemd_journald` receiver keeps native journal field names** (`MESSAGE`, `SYSLOG_IDENTIFIER`, `_COMM`, `_UID`, `_PID`, `_BOOT_ID`), and the log name equals the receiver id. Established from the Ops Agent docs and `confgenerator`. Live entries pin it in inc 2.
- **The receiver reads the whole journal on first start** (fluent-bit `Read_From_Tail` off). The sink cutoff (AC 8) stops downstream replay, but the agent still uploads the backlog to Logging once. Established from `ops-agent confgenerator/logging_receivers.go`.
- **sshd INFO formats follow OpenSSH 9.2 `auth.c auth_log`.** `Failed publickey` for a valid user is VERBOSE until the 3rd failure, then INFO. Single wrong-key sessions show only `Connection closed by authenticating user … [preauth]`. Established from source knowledge; inc 2 captures real fixtures.
- **Password auth is probably on.** `startup.sh.tpl:18-21` copies the stock `sshd_config`, which comments out the line its seds target. Inferred from the file, unverified on the live daemon. Fixing it is out of scope (sshd change, G7).
- **Volume** is 8,072 sessions on 2026-10-14 across 10 users, one of them polling every ~15s. Established from the serial-console session lines.
- **Customers get `/bin/bash`, with no chroot or `ForceCommand`.** Every customer is in `sftpgroup`, which owns the 770 gcsfuse mount, and the VM SA token is reachable from a shell. So a customer can already read other customers' files and use the VM SA. Adding `logWriter` lets a shell write Logging entries directly; the `_COMM`/`_UID` filter stops `logger` forgery but not direct API writes. Source: `architecture.md:252` (ASSESSED, unverified live) and `startup.sh.tpl:93`.
- **RESOLVED 2026-10-15 (Harry): users are still managed through `users.json`.** Records are `{raw_username = businessId, username, ssh_key}` (`core/sftp-user-builder/schema.ts`), with no connectorId. So `users.json` decides who is a Fuse user and which business they belong to, and the connector lookup only adds `connectorId`. The admin user isn't in `users.json`, so it is counted only.
- **RESOLVED 2026-10-15 (Harry): fold it into what we deploy.** F1 ships fuse-ui with SFTP logins hidden by default and a "Show SFTP logins" toggle. A2 adds an `excludeKind` read filter to audit-service. Every login is still stored.
- **Shared-shell exposure:** predates this work and is larger than the login-forgery risk. Harry chose not to raise a ticket (2026-10-15). Out of scope.

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
Sibling work outside this repo:
- **P1** (pkg-node): `sftp_login` kind, `@gfs-bifrost/audit` 0.3.0.
- **A1** (audit-service): per-kind retention. A code map `{fuse: {sftp_login: 365d}}` sets `expireAt = occurredAt + d` at ingest. `Insert` drops a producer `expireAt`. The TTL index has `partialFilterExpression {expireAt: {$exists: true}}`. G1, G3, the explainer, CLAUDE.md and known-context are amended.
- **A2** (audit-service): an `excludeKind` (repeatable) filter on `GET /events` and `/filter-options`, plus openapi.
- **F1** (fuse-ui): `sftp_user` target, `logged_in`/`login_failed` labels, summary cases, and the drawer badge fallback (#309's `sftp_user` events render raw today too). SFTP logins are hidden by default on the global and customer audit pages, with a "Show SFTP logins" toggle that sends `excludeKind=sftp_login` when off. Needs A2.

Order: P1 ∥ A1+A2 ∥ inc 1, then F1 after A2 → inc 2 → inc 3 → inc 4 → inc 5 → inc 6 → inc 7. The VM is staged by one variable, `sftp_login_audit_stage` = `off | prep | agent | removing`. The flag drives `desired_state`, not `count`, so going back never orphans an installed agent.

- [ ] 1. **VM prep in dev** (stage `prep`): osconfig API (`disable_on_destroy=false`), VM SA `logging.logWriter` (`_member`), VM label `fuse-ops-agent=sftp-sshd` and metadata `enable-osconfig=TRUE`. dev.tfvars `prep`, prod.tfvars `off`. (AC 6b)
  - Verify:
    - The PR plan shows `google_compute_instance.sftp_vm` as `~ update in-place`, with labels and metadata only and no `service_account`/scopes/`machine_type`/`boot_disk`.
    - The post-merge `terraform-plan-prod` shows no change from this flag.
    - `gcloud compute os-config inventories describe sftp-connector-dev-sftp` returns data.
    - A dev login by a named existing dev user still works.
  - gate: name an existing dev `users.json` user whose connector holds a private key, for the dev logins in inc 1, 2 and 6. The DAZZA harness user isn't on the dev VM.
    [x] confirmed — `FUSE_EC11DE9F4F` (DAZZA "sftpfive", `conn_16365bead0a14d24813d3618a57d22d7`); the private key comes from its connector GET; baseline `sftp ls` worked 2026-10-15
- [ ] 2. **Agent policy in dev** (stage `agent`). `google_os_config_os_policy_assignment`, with `depends_on` the API:
  - Targeting: label plus Debian 12 inventory filter; rollout `fixed = 1`.
  - Resources:
    - apt repo `google-cloud-ops-agent-bookworm-2`
    - pkg `google-cloud-ops-agent`, `INSTALLED` (or `REMOVED` when the stage is `removing`)
    - a `file` for `config.yaml`
    - an `exec` that restarts the agent when the config hash changes
  - Config: one `systemd_journald` receiver `sftp_sshd`; `exclude_logs` keeps only `_COMM` sshd/sshd-session lines; logging `default_pipeline` with no receivers; metrics `default_pipeline` with no receivers (memory headroom on the e2-small, #140).
  - No sink yet, so nothing is exported or stored. Merge before verifying: a later master apply would destroy a branch-applied assignment and orphan the agent. (AC 6a, 7)
  - Verify:
    - The assignment report is COMPLIANT and `ops-agent-health` is clean.
    - `logs/sftp_sshd` holds sshd lines only.
    - Commit one real entry per line type as parser fixtures.
    - **Dev reboot:** `Sync Run Complete` in the serial log, no dpkg-lock failure, and a dev login works.
    - **Rollback drill:** `removing` → COMPLIANT with the package gone → `agent` again.
    - Agent RSS and VM memory are watched for 24h.
- [ ] 3. **Parser and mapper on real fixtures:**
  - Bump `@gfs-bifrost/audit` to 0.3.0, adding it to `minimumReleaseAgeExclude`.
  - Add `code/src/core/sftp-login-audit/`:
    - `log-entry.schema.ts`
    - `sshd-line.parser.ts`, returning `accepted | failed | invalid_user | closed_preauth | ignored`. It anchors at the line end, handles IPv6 and `keyboard-interactive/pam`, and treats `Failed publickey` after 3 attempts as ordinary.
    - `sftp-login-audit.ts`, mapping to the envelope: `eventId` = uuidv5(`insertId|timestamp`), `tenantId` = `users.json` `raw_username`, `details.connectorId` optional, target `{sftp_user, username}`, actor `{customer, username, ip}`, `correlationId` = `sshd:<_BOOT_ID>:<_PID>`.
  - (AC 1, 2, 5)
  - Verify (vitest, one behaviour per `it`):
    - every inc-2 fixture parses as expected;
    - the ignore list is ignored;
    - the fingerprint equals `publicKeyFingerprint()` of the same key;
    - the `eventId` is stable;
    - the output passes `FuseAuditMessageSchema`.
  - gate: P1 published as 0.3.0
    [ ] confirmed
- [ ] 4. **Push endpoint and resolution:**
  - `POST /events/v1/sftp_login` → `SftpLoginAuditService.record`, in this order:
    1. Unparsed or ignored lines are counted, then 204.
    2. `invalid_user` is counted with no username anywhere, then 204.
    3. **Resolve the user from `users.json`,** read through the existing storage service, cached ~5 min and refetched at most once a minute on a miss. A username not in it (admin, `root`, anything else) is counted as `unknown_user{reason:not_in_users_json}`, then 204.
    4. **Add `connectorId` through `getConfigByUsername`,** with a negative cache. `MissingConnector` means the event is stored without `connectorId` (a legacy user).
    5. **Any other lookup error nacks.** That includes the `users.json` read, a raw axios error, or a `ValidationException` from `config.api.ts:692-723`. They're wrapped in `SftpLoginLookupException` and mapped to 500 in `errorHandler` (not `isNackedError`, which only feeds confirmations).
    6. On publish `timeout` or `publish_failed`, throw so the message redelivers.
    7. After `MAX_TRANSIENT_DELIVERY_ATTEMPTS`, count `dropped` and ack.
  - Also: `flow` union, log catalogue, factory wiring. A CLAUDE.md rule: usernames from `Invalid user` lines are never logged. Audit publish failures for this kind log at warn and are tagged with `kind`. (AC 3, 5)
  - Verify:
    - Controller and service specs, one per branch above, including a logger spy proving no invalid username is logged.
    - Dev: POST a push envelope built from an inc-2 fixture to the dev Cloud Run URL. The event is in dev audit-service with `expireAt`, and a repost gives `outcome:duplicate`.
  - gate: A1 deployed to dev
    [ ] confirmed
- [ ] 5. **Topic, subscription and sink, dev and prod** (inert in prod, where no `sftp_sshd` log exists):
  - Topic `sftp_login_<env>.v1`.
  - A push subscription with OIDC, retry 10–600s, and a `dead_letter_policy` that keeps `deliveryAttempt` in the body (with the app budget, per the decision log).
  - A `google_logging_project_sink` (`unique_writer_identity`), plus a publisher grant for the `writer_identity` on this topic only.
  - Filter:
    - `resource.type="gce_instance"`
    - `resource.labels.instance_id` from the VM resource
    - `log_id("sftp_sshd")`
    - `jsonPayload._COMM=("sshd" OR "sshd-session")` AND `jsonPayload._UID="0"`
    - the MESSAGE prefixes (Accepted / Invalid user / Failed, but not "for invalid user" / closing "authenticating user")
    - `timestamp >= var.sftp_login_audit_since`
  - (AC 1, 2, 4, 8)
  - Verify:
    - Real dev logins (accepted, wrong key, `nosuchuser`) give the expected rows and counters within 2 min.
    - `logger -t sshd "Accepted publickey for <dev user> from 192.0.2.1 port 1 ssh2"` from the dev user's shell gives nothing.
    - A pre-cutoff journal entry is not exported.
    - `logging.googleapis.com/exports/error_count` = 0.
    - The prod plan shows additions only.
    - Kill switch: `disabled = true` stops delivery.
- [ ] 6. **Prod VM prep** (prod stage `prep`). (AC 6b)
  - Verify:
    - The post-merge `terraform-plan-prod` is in-place labels and metadata on the VM, plus API and IAM additions, and nothing that stops the VM.
    - List master between the prod sha and the run's sha before approving.
    - Prod inventory returns data.
    - The serial-console session rate is unchanged for 1h.
  - gate: the prod usernames seen in serial-console session lines over 7 days are all in prod `users.json`. Any that aren't are named here, since they would be counted rather than stored.
    [ ] confirmed
- [ ] 7. **Prod agent** (prod stage `agent`). (AC 1, 6, 8)
  - Verify:
    - The assignment report is COMPLIANT.
    - Real traffic only, never a synthetic login: `fuse.sftp_login.recorded{outcome:accepted}` is about the session rate, rows appear in fuse-ui with IP/connector/business, and `unknown_user` is counted.
    - Prod VM memory and the agent's RSS hold for 24h.
    - Rollback trigger: memory > 80% or any login failure spike → stage `removing`.
  - gate: A1 in prod, with the TTL index listed on the M10. A2 and F1 in prod (logins hidden by default). The inc-2 24h memory watch is clean.
    [ ] confirmed

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-15 [inc 1] Baseline before any VM change: `sftp` as `FUSE_EC11DE9F4F` to the dev VM lists `from_ilg to_ilg`. `terraform validate` (1.9.0) passes on 3d47880. Draft PR gfs-bifrost/sftp-connector#312.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- **Direct Logging API writes with the VM SA from a customer shell.** These can still forge an entry in `sftp_sshd`. The `_COMM`/`_UID` filter only covers `logger`. This is bounded by the pre-existing shared-shell exposure (UNRESOLVED).
- **Whether Cloud Logging accepts the agent's first-start backlog.** The sink cutoff makes it irrelevant downstream; the one-off Logging ingest cost is unmeasured until inc 2.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-10-20 (Harry)** — Halted after inc 1 (PR #312, dev prep only, no agent installed). SFTP login audit moves to the new Go SFTP host, which emits sftp_login itself (sftp-host-b inc 2); the VM is retired by sftp-host-c. Dev stage goes back to off in sftp-host-a inc 2.
- **2026-10-15 — Overrides the decision log's "add the agent to `startup.sh.tpl`; roll back by removing the policy":**
  - **No startup-script install.** apt at boot would race the OS Config install for the dpkg lock. The script runs `set -e` before `sync_users.sh`, so it would break the VM's only recovery path (G5). A rebuilt VM gets the agent by label within one policy cycle (~10–15 min).
  - **Rollback is two-step.** Deleting an assignment leaves the agent installed, so the `removing` stage comes first (AC 7).
- **2026-10-15 — App-level retry budget, not a DLT hold.** This follows the standing preference for `MAX_TRANSIENT_DELIVERY_ATTEMPTS`. The repo's DLT topics have no subscriptions, so dead-lettered messages vanish. An exhausted login is counted and can be backfilled from Logging by eventId.
- **2026-10-15 — Sink on trusted journald fields** (`_COMM`, `_UID`), not `SYSLOG_IDENTIFIER`, which any `logger -t` sets.
- **2026-10-15 — Agent metrics off.** The host-metrics pipeline runs an OTel collector on an e2-small with a resource-exhaustion incident in its history (#140). It can be turned on later on evidence.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
- **`startup.sh.tpl:18-21`'s `PermitRootLogin`/`PasswordAuthentication` seds are no-ops.** The script copies the stock Debian `sshd_config` (commented defaults) first, so OpenSSH defaults apply. Unverified on the live daemon.
- **`errors.ts` `isNackedError` doesn't decide push ack/nack.** It only feeds the confirmations "redelivery exhausted" check. `errorHandler` maps exceptions to status: `ConfigApiException` → 202, `ConnectorConfigException` → 500 (logs `cause` with the username), `ValidationException` → 204.
- **`config.api.ts` `getConnectorByUsername` doesn't wrap errors.** A transport error is a raw axios 500; a schema mismatch is a `ValidationException` that gets acked silently.
- **The DLT topics in `pubsub.tf` have no subscriptions,** so a dead-lettered message is dropped.
- **The dev VM carries an unmanaged label** `alias=sftp-connector-dev-sftp`. Expect it in plan output.
- **architecture.md and operations.md (stale by #309)** omit the `sftp_user/created` audit publish and the `audit.publish_failed` metric and monitor.
- **When audit-service#12 (A1+A2) merges, amend the audit-service vault notes.**
  - `architecture.md:35` G1: every query index leads with `system`; `expireAt_ttl` is the deletion-only exception.
  - `architecture.md:39` G3: a partial TTL index driven by `ingest.Retention`.
  - `architecture.md:132`: the index list.
  - `known-context.md:24`: kept forever except `sftp_login`, which keeps 365d from occurredAt.
  - `explainers/audit-event-flow.md:67,79`: `expireAt` at ingest, the `excludeKind` filter, and the TTL.
- **audit-service `make test-mongo` force-removes the fixed container `audit-test-mongo`,** so concurrent runs kill each other.
