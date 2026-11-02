---
ticket: none
title: 'SFTP host B: provisioning, login audit and dev cutover'
service: sftp-connector
status: complete
created: '2026-10-20'
updated: '2026-10-29'
repo: /home/hjf/code/fuse/sftp-connector
worktree: none
branch: none
base: origin/master
base_sha: unknown
pr: null
tags:
- waypoint
- plan
impl_model: opus
impl_effort: high
---
# none — SFTP host B: provisioning, login audit and dev cutover

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
Plan B of three ([[sftp-host-a-monorepo-host-image-and-dev-infrastr|A]] → B → [[sftp-host-c-prod-cutover-and-vm-decommission|C]]). It moves SFTP user provisioning from sftp-connector's Cloud Run, which SSHes into the VM as `sftpuser` with sudo, into the Go host. It adds login audit from the host and builds the cut tooling and monitoring. Then it cuts **dev** over gradually through the load balancer:

- **S1:** the static IP moves onto the load balancer with the VM as its only backend;
- **S2:** the host joins as a second backend, splitting traffic by client IP;
- **S3:** the VM is drained out;
- **S4:** provisioning switches to the host.

Each step is rolled back once in the drill. Done means dev is served by the host alone, a new dev SFTP connector provisions through it, every dev login is audited, and each step's rollback has been exercised.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. A new connector goes PENDING → host provisions exactly one key → `UserCreationResponse` on `customer_creation` → config-service marks it ACTIVE, and the `sftp_user` audit event is published. config-service and fuse-ui need no change. — S4 2026-10-28 (conn_da089ecd… ACTIVE in ~10 s via host) + inc 1 sftp_user audit row 2026-10-22
- [x] 2. Redelivered or duplicate `create_sftp_user` messages never produce a second key, and `users.json` bytes the host didn't change are preserved exactly. — inc 1 duplicate publish 2026-10-22 (skipped not_pending, one key); rollback-S4 lint 2026-10-28
- [x] 3. Every authentication attempt on the host for a username in `users.json` emits one `sftp_login` audit event with IP, fingerprint, outcome and a deterministic `eventId`. Attempts on unknown usernames are counted and never stored or logged. — inc 2 2026-10-22: accepted/failed/closed_before_auth rows, uuidv5 eventId, unknown user 0 rows
- [x] 4. Only one `create_sftp_user` consumer is ever active, at every step and every rollback. — inc 1 test mode + S4 push-off-before-pull and rollback-S4 2026-10-28, DLT and backlog 0
- [x] 5. S1 changes nothing customers can see: same IP, same host keys, same VM behind it, with one short connection blip. — S1 2026-10-25: same IP and keys, one 18.1 s blip
- [x] 6. During the split (S2), each client IP stays on one side, both sides serve the same files, and a user provisioned during the split can log in on both sides. — S2 2026-10-27: per-IP stickiness, uploads archived on both sides, split-provisioned user logs in on both
- [x] 7. Rolling back S2 or S3 is a backend change with no IP move and no outage. Rolling back S4 restores Cloud Run provisioning without losing a `create_sftp_user` message. Rolling back S1 moves the IP back to the VM. Each is exercised in dev and timed. — S2 179 s, S3 257 s, S4 531 s drilled in dev; S1 rollback scratch only (31.5-36 s), deviation 2026-10-29
- [x] 8. Host failure, auth errors, invalid `users.json` records and provisioning failures alert through Datadog. A dev-only canary proves login, list and put on a schedule. — monitors live; users.json fault injected 2026-10-29; bad-key injection carried to Plan C, deviation 2026-10-29
- [x] 9. Prod is untouched: every merge's prod plan is a no-op for both projects. — every merge's prod plan no-op except #376's inert startup-script text, deviation 2026-10-29
- [x] 10. A folder added to the host's directory list exists for every existing dev user after the next host rollout, and for new users at provisioning; existing folders and their contents are untouched. — proven against fake-gcs-server only (Not verified), deviation 2026-10-29

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- **The Go host** (`apps/host`, Plan A's server), gaining `internal/provisioning` and `internal/audit`:
  - a new pull consumer on `create_sftp_user_<env>.v1`, the same subscription switched in place by Plan A's `create_sftp_user_consumer`;
  - publishes to `customer_creation`, consumed by config-service `core/sftp-auth-status/sftp-auth-status.handler.ts`;
  - publishes to `audit.<env>.fuse.v1`.
- **Payload contracts**, unchanged:
  - input `BifrostMessageSchema({businessId, connectorId})`;
  - output `UserCreationResponse` (`apps/connector/src/controllers/schema.ts`), with `homeDir: /home/<user>`;
  - `sftp_user` audit with the uuidv5 namespace from `apps/connector/src/core/sftp-user-builder/sftp-user-audit.ts`.
- **What the host must reproduce from today's provisioning:**
  - username `FUSE_` + `sha256(connectorId)[:10]` (`support` excluded);
  - use `config.auth` only when both `publicKey` and `privateKey` are set (`sftp-user.builder.ts:33-45`);
  - the folder skeleton, now from the host's declared directory list (Plan A inc 3), seeded with today's 5+5.
- **Connector reads:** the Config API directly from Go, with the config-service API key from Secret Manager: `GET /api/v1/connectors/{id}` for provisioning, and `GET /api/v1/connectors/?username=` for login audit, as `apps/connector/src/config/config.api.ts` calls them today. Login audit caches the username lookup, with negative entries for unknown usernames. The connector DTO is a generated Go type (Plan A's codegen).
- **`@gfs-bifrost/audit` `SftpLoginDetailsSchema`** (`pkg-node pkg/audit/src/fuse/kinds.ts:36-49`) requires `sourcePort`. The Go server has it from `RemoteAddr()`, so no package change is needed.
- **Plan A's cut plumbing:**
  - the `sftp` backend service and its `vm_backend` / `host_backend` / `serve_static_ip` tfvars;
  - the VM's unmanaged instance group;
  - `sftp_vm_admin_ip`;
  - `SFTP_ADMIN_HOST`.
- **The dev VM's access config:** static IP → `sftp_vm_admin_ip` at S1. That's an access-config swap, not an sshd, mount or reboot change.
- **The UJ plan** [[uj-sftp-login-audit-events-from-the-vm-via-ops-a]] and the Audit programme's Migration State (A1, A2, F1, G7).
- **Monitors** in the observability repo: "👤 Failed to create a SFTP user 👤" (259775062) and `[FUSE] Audit events not published` (observability#65). Both are scoped to `service:sftp_connector` and go quiet once the host provisions.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- sftp-connector publishes `create_sftp_user` to itself (`connector.config-handler.ts:447-474`) on every config backlink while a connector is PENDING, so duplicates are routine. Established from source; no other publisher in any local repo.
- Today's consumer doesn't check PENDING. It provisions whatever its cache returns. The host **will** check, reading the connector fresh from the Config API (never a cache), and skip and ack when the connector isn't PENDING. This is a deliberate change from today, recorded here.
- An SFTP connector can be set back to PENDING (`connector.update.schema.ts:15` accepts `"pending"`). By then it carries both keys from its first provisioning, so the host re-provisions with the stored key, keeping today's "supplied" semantics. Established from source.
- Two consumers at once would each generate a different key: one lands in `users.json`, the other's private key in config-service, and the customer is locked out. The S4 ordering (push off, then host pull on) guarantees one consumer. Exactly-once delivery, the PENDING check and the `users.json` generation precondition are the backstop.
- **During S1–S3, provisioning stays on Cloud Run, aimed at the VM's admin address** (`SFTP_ADMIN_HOST`). It writes the Linux user on the VM **and** `users.json` (awaited since Plan A), which the host picks up within its poll interval. So a user provisioned mid-split works on both sides, and the provisioning switch is decoupled from the traffic cut.
- Between the access-config swap and setting `SFTP_ADMIN_HOST` there's a short window where provisioning SSHes to the load balancer and fails. Pub/Sub redelivers (60 s ack deadline, 5 attempts, then the DLT subscription Plan A adds), so the window has to stay under a few minutes or the message lands in the DLT for redrive. The script sets both in one step.
- `CLIENT_IP` affinity hashes client IPs across healthy backends, so with about 10 prod customers the split is lumpy, not a clean percentage. The host's share is set by host instance count against the VM's one, starting at one host instance.
- The two sides behave differently: the VM allows shells and exec, and the host doesn't. A customer who uses them gets different results depending on the side. Plan C's `auth.log` baseline gate finds them before the prod split; in dev, the DAZZA users are SFTP-only.
- The two sides authenticate from different sources: the VM from `authorized_keys` written at its last boot sync, the host from `users.json` live. They can disagree. The sync was silently broken for 4+ months (`sftp-partner-key` skill), and DAZZA's harness user `FUSE_DD4537E9BE` isn't on the dev VM. The key-set diff gate before S2 names every difference.
- The UJ `eventId` seed (`insertId|timestamp`, `sshd:<_BOOT_ID>:<_PID>`) is journald and Cloud Logging specific. The host seeds from instance id, connection id and the handshake timestamp. Record it with `wp decide` in this plan and the UJ plan.
- Logins served by the VM during the split are only in its `auth.log` (UJ hasn't shipped).
- Rolling back S4 after the host has provisioned users means running `sync_users.sh` on the VM before it rejoins the backend service. That's safe then, since it serves nobody, but it's a mount change, which Audit gate G7 covers.
- Stale-branch manual deploys and parked Deploy runs can reapply old tfvars: `push_config`, the backend set, `SFTP_ADMIN_HOST`. Plan A inc 1's ancestor check covers manual deploys; parked runs need cancelling by hand before each step.
- Login audit runs only from the host (Harry, 2026-10-20). UJ is halted after its inc 1, and this plan's inc 2 replaces it. Logins served by the VM before S3 are not audited.
- Audit gate G7 (VM owner and recovery runbook) is satisfied by these plans for the length of the migration, not waived (Harry, 2026-10-20). The owner is Harry as plan owner; the runbook is `cut.sh`'s rollback steps, rehearsed in inc 3 and drilled in inc 4. The only G7-class change, the `sync_users.sh` run in the S4 rollback, happens only while the VM is out of the backend service and serving nobody.

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
- [x] 1. Provisioning consumer in the host, dormant behind `PROVISIONING_ENABLED=false` (AC 1,2,10). — #335-#343, #346, #347 merged; dev test-mode e2e: one key, users.json record, folders, ACTIVE, sftp_user audit, duplicate skipped — done: 8cc36c4
      gate: Plan A signed off
            [x] confirmed 2026-10-22: Plan A complete (wp signoff PASS; stack #317-#327, #329 merged)

      - `internal/provisioning`: a streaming pull (`cloud.google.com/go/pubsub`) with one message in flight per replica, decoded into the generated envelope type and validated as strictly as `BifrostMessageSchema`.
      - Read the connector fresh from `GET /api/v1/connectors/{id}` (no cache). Skip and ack when it isn't PENDING.
      - Key rule and username derivation exactly as today.
      - Upsert `users.json` as raw JSON: replace the first matching record's `ssh_key`, as today, or append a three-field record. Leave all other bytes as they are. Write with `ifGenerationMatch`, retry on 412, and await the write.
      - Folder placeholders for every entry in the directory list, with `ifGenerationMatch=0` (create-only).
      - Publish `UserCreationResponse` (checked against the golden fixtures that `apps/connector`'s Zod schema parses), then the `sftp_user` audit event.
      - Startup reconcile: every user in `users.json` × every entry in the directory list, create-only, behind the same flag. Replicas reconciling at once is safe because of the precondition. This is how a new use case's folder reaches existing users: add the entry, deploy, and the rollout creates it.
      - Metrics: `provisioning.{succeeded,skipped_not_pending,failed}`.

      — verify:
      - unit specs, one per branch: not-PENDING skip, supplied vs generated key, re-PENDING reuses the stored key, the raw upsert keeps a malformed neighbour record byte for byte, 412 retry, placeholder 412 is a no-op;
      - in dev, with the host pointed at a dev-only test topic and a test connector:
        - the `users.json` diff is exactly one record;
        - config-service's `customer_creation` handler sets `isActive`;
        - an audit-service dev row exists;
        - a second publish for the same connector is skipped (`skipped_not_pending`), and only one key exists;
        - adding a test entry to the directory list and rolling the host creates that folder for every dev user, and a second rollout creates nothing (AC 10).
- [x] 2. Login audit from the host, dev only (AC 3). — #330-#333 merged; dev rows for accepted, auth_failed and closed_before_auth; unknown user unstored and unlogged; connectorId pending inc 1 — done: 6083751
      gate: UJ decision taken (Harry); if UJ is halted, a `wp decide` SUPERSEDED marker goes into the UJ plan and the Migration State UJ row
            [x] confirmed (Harry, 2026-10-20: halted; marker and row written the same day)
      gate: audit-service retention (A1) applied in dev
            [x] confirmed 2026-10-22: audit-service#12 live in dev and prod on 8dec02b (#14 unblocked the deploy queue); dev Atlas event expireAt = occurredAt + 365d, partial TTL index expireAt_ttl

      - **One event per connection, emitted from the SSH layer:**
        - `logged_in` once `ssh.NewServerConn` returns, which is only after the signature is verified. Fingerprint from the matched key, carried in `ssh.Permissions`. IP and port from `RemoteAddr()`.
        - `login_failed`/`auth_failed` when the handshake ends with at least one key rejected and none accepted. Rejected *queries* for other keys during a normal login don't count, since that connection succeeds.
        - `too_many_attempts` at `MaxAuthTries`, and `closed_before_auth` when the client leaves before offering any key.
      - `tenantId` = `raw_username`.
      - `connectorId` comes from a username cache with negative entries.
      - Unknown usernames: counted in `fuse.sftp_login.unknown_user{reason}`, never stored or logged.
      - Deterministic `eventId` from instance id, connection id and handshake timestamp.

      — verify, dev logins on the temp IP:
      - an accepted login, a wrong key and a client closing before auth each give one `sftp_login` row with IP, fingerprint and `connectorId`;
      - replaying the same event gives no duplicate row;
      - an unknown username shows up only in the counter (grep host logs for it: no hits).
- [x] 3. Cut tooling, rehearsal, canary and monitors (AC 4,7,8). — cut.sh #352, canary #349, monitors observability#76/#80; scratch rehearsal timed — done: 4cc58ba
      - `apps/host/scripts/cut.sh <env> <step>` (`s1|s2|s3|s4` plus `rollback-sN`), dry-run by default, logging each command and timing it. Each step prints the tfvars PR it expects merged and refuses to run if the live state doesn't match the step before.
        - **S1, IP onto the load balancer, VM only:**
          - `gcloud compute instances delete-access-config` (static) then `add-access-config --address=<sftp_vm_admin_ip>` on the VM;
          - merge tfvars `vm_backend=true`, `serve_static_ip=true` (forwarding rule on the static IP → `sftp`), plus connector `SFTP_ADMIN_HOST=<admin ip>`.
          - The gap between the swap and the forwarding rule is the one connection blip.
        - **S2, split:** tfvars `host_backend=true` with the MIG at one instance (min 1, max 1), so roughly one VM to one host by client IP. Then raise the host count in steps.
        - **S3, drain the VM:** tfvars `vm_backend=false`. Connection draining lets sessions in flight finish. MIG back to size 3.
        - **S4, provisioning switch:** tfvars connector `create_sftp_user_consumer=host` (push off; messages queue), then host `PROVISIONING_ENABLED=true`.
      - Rollback mirrors each step:
        - **S4:** `PROVISIONING_ENABLED=false`, then `consumer=connector`. If the host provisioned anyone, `sync_users.sh` on the VM, plus the three-field `users.json` lint (G1).
        - **S3:** `vm_backend=true`.
        - **S2:** `host_backend=false`.
        - **S1:** delete the forwarding rule, then swap the VM's access config back to the static IP, then unset `SFTP_ADMIN_HOST`.
      - Rehearse every step and rollback on **scratch** dev resources first: a scratch address, a throwaway Debian VM with sshd, and a scratch backend service. Prove that:
        - the guest agent accepts traffic to the forwarding rule IP;
        - the access-config swap is in place, with no stop;
        - one instance group in two passthrough backend services is accepted;
        - `CLIENT_IP` affinity keeps one client on one side across reconnects.
      - A dev-only canary: Cloud Scheduler plus a Cloud Run job doing login, list and put for a canary user, never in prod (Audit scar tissue forbids synthetic events in prod).
      - Datadog monitors, in the observability repo:
        - healthy MIG instances < 2;
        - `/healthz`;
        - auth errors;
        - `users_json.invalid_record`;
        - `provisioning.failed`;
        - DLT subscription backlog > 0;
        - per-backend healthy count on `sftp`;
        - the "Failed to create a SFTP user" and "Audit events not published" monitors re-scoped to the host's service.

      — verify:
      - the rehearsal transcript, with every step and rollback timed and the four facts above proved;
      - the canary runs green for 3 days;
      - each monitor fires once on an injected fault: kill an instance, corrupt a test `users.json` record, point the host at a bad API key.
- [x] 4. Dev cut, step by step with dwell times, plus rollback drills (AC 1,4,5,6,7). — dev S1-S4 done with S2/S3/S4 rollback drills; soak exit criteria met 2026-10-29 — done: a47a245
      gate: dev key-set diff: per user, live `authorized_keys` on the VM vs `users.json`, both directions, with every key that would authenticate on only one side named and accepted
            [x] confirmed 2026-10-22 (diff: 124 VM keys, 105 users.json keys, 92 shared). **VM-only, accepted:** 23 FUSE_ users absent from users.json entirely (records removed, never deleted on the VM; no logins in the VM's ssh journal since 2026-10-17): FUSE_138C948651 FUSE_1FE406ED71 FUSE_2A2F545FC7 FUSE_2A8E5CD5D7 FUSE_2F43796781 FUSE_3630CC0CED FUSE_37B97ADA6D FUSE_3CA253292F FUSE_46C7859D75 FUSE_5FD642E5F2 FUSE_71C98836AD FUSE_723C037E3E FUSE_7537BA7E7F FUSE_7ED7EEAE07 FUSE_8A178C54EC FUSE_952015BD1F FUSE_95D4886A04 FUSE_B9D84201FE FUSE_DD4537E9BE FUSE_E520E6ADB8 FUSE_F71DB01312 FUSE_FA9477E6FC FUSE_FBFB096803; also `sftpuser` (admin, not served by the host by design) and 7 staff OS users with no authorized_keys. **users.json-only, accepted:** `FUSE_9FAC0B372F` (the host-provisioned test connector). 11 users.json keys carry a trailing newline (incl. `support`); the host's `ssh.ParseAuthorizedKey` reads the first line, so they authenticate on both sides.
      gate: every parked connector and host Deploy run older than the step being taken is cancelled
            [x] confirmed 2026-10-29: all of ours cancelled at each step; Matt's 39944835679 left on Harry's instruction (it has applied dev, so it can't reapply dev tfvars; #355). Deviation recorded.
            S1 (2026-10-25): our runs were cancelled, but Matt's connector run 39944835679 (#344, parked on `terraform-apply-prod`) was left alone on Harry's instruction. It had already applied dev, so it can't reapply dev tfvars, and #355 narrowed cut.sh's guard to runs that haven't applied the env being cut. Re-check before S2.
      gate: ~~before S4 sets `sftp_host_provisioning = live`, the host reads a dedicated config-service key scoped to what provisioning needs~~ MOVED to Plan C inc 1 (2026-10-28, Harry), see Decisions
            [x] confirmed 2026-10-28: moved, not discharged. The dev host has held the dev master key since inc 2 (login audit), so dev S4 adds no key exposure. The exposure that matters is the prod host holding the prod key.

      - Run S1 → (24 h) → S2 → (3 days, raising the host share) → S3 → (24 h) → S4.
      - In the drill, roll back each of S2, S3 and S4 once and roll forward again.

      — verify:
      - **after S1:** DNS and IP unchanged, no host-key warning, `FUSE_EC11DE9F4F` logs in and lands on the VM (its `auth.log`), the canary is green, and a new dev SFTP connector provisions through the admin address;
      - **after S2:** the canary and `FUSE_EC11DE9F4F` each stick to one side across ten reconnects; an upload on each side is archived; a connector provisioned during the split logs in on both sides;
      - **after S3:** the VM's `auth.log` shows no new sessions, and everything is served by the host;
      - **after S4:** a new dev SFTP connector goes PENDING → ACTIVE through the host, its credential bundle logs in, and an upload is archived;
      - each rollback takes the timed duration from the rehearsal, with no `create_sftp_user` message lost (subscription backlog and DLT both empty after);
      - the dev soak (Plan C's first gate) starts after S4; it ends on exit criteria, not a timer (2026-10-28, see Decisions).

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-29 [inc 3, AC 8] **Monitors against real and injected faults.**
  - **Injected:** a `bad_key` record (`FUSE_FAULTINJECT1`, raw `HJF`) went into dev `users.json` at 16:04:11Z under a generation precondition. The host logged `users.json records skipped` (`bad_key`) at 16:04:16Z, and "users.json has invalid records — dev" (335786588) alerted at 16:09:42Z. The record was removed at 16:09:55Z, leaving the file byte-identical to before the test.
  - **Fired for real during the cut (Datadog events since 2026-10-22):**
    - "SFTP backend went unhealthy" on each ramp and roll, and on the VM leaving at S3;
    - "SFTP canary failing" on the pre-key run (2026-10-22 19:47Z);
    - "Fewer than 2 healthy instances" at the ramp to 3 (2026-10-27 16:10Z).
  - **Never fired, real or injected:** `/healthz` failing, repeated failed logins, `users.json` not refreshing, user creation failed, audit publish failed, Config API unavailable, connector lookups failing, and the DLT monitor. The bad-API-key injection was not run.
  - The canary has run green on a schedule since 2026-10-22: 867/868 before S1, and every run since.
- 2026-10-28 [inc 4, AC 1, 4, 7] **Dev S4 done, drilled and re-applied. The dev cut is complete: the host serves and provisions every dev SFTP user.**
  - **S4** (#370 then #371, live 11:17Z):
    - #370 switched `create_sftp_user` from push to Cloud Run to exactly-once pull; push was off at 11:02:25Z.
    - #371's host plan fails its own precondition while push is on, by design. So #370 was merged by hand, and #371's plan was re-run and read before `cut.sh dev s4` merged it. The plan moved the template to the live subscription and removed the test topic and subscription (2 added, 2 changed, 4 destroyed).
    - **First real template roll since #364:** the new instances `7frx`, `ldwg` and `m72x` stayed UNHEALTHY on `/healthz` until their containers were up (11:10:35–42Z). No instance was falsely HEALTHY. EPARFUM made 4 logins every minute and moved to `m72x` at 11:11. The canary passed at 11:05, 11:11 and 11:15.
    - **After S4, verified:** new HJF connector `conn_da089ecd72ad455284dd653a8d6edde7` went PENDING → ACTIVE in ~10 s. The host provisioned it (`7frx`, 11:20:50Z, `key_source=generated`), and `users.json` gained a three-field record (`FUSE_44D8DBCFDB`, raw `HJF`).
    - Its private key, read from config-service into an agent, logged in through the LB and uploaded `S4-HOST-PROV-PRICAT.EDI`. The connector ingested it and routed it to `error/` because a bare connector has no mapping. Archiving of a mapped file through the host is the 2026-10-27 S2 evidence.
  - **Rollback-S4 drill** (#372 then #373, 531 s, done 11:46:04Z): the `users.json` lint passed (100 records, all three-field). The VM resync took 272 s. Backlog and DLT were both 0. The connector then provisioned `conn_0d5006789b8540a69fadc4b12d72e495` / `FUSE_DE346A2F44` in 13 s, with no host provisioning log.
    - **FINDING, fixed in #376 (merged `427a239`):** VM `sync_users.sh` set `HOME_DIR=$(eval echo "~$username")` *before* `useradd`. The host-provisioned `FUSE_44D8DBCFDB` got an account, but its `.ssh` and bind mounts went to `/home/sftpuser/~FUSE_44D8DBCFDB/`, and its VM login was `Permission denied (publickey)`.
    - A second sync fixed it: the user then logged in on the VM and saw the file it had uploaded through the host.
    - This bites only after rollback-S4 plus rollback-S3, i.e. when the VM serves users the host provisioned. The stray `/home/sftpuser/~FUSE_44D8DBCFDB` directory was left on the dev VM; its binds were unmounted by the next sync.
    - **Fix live on dev, 14:36–14:43Z:** after #376's dev apply (in place, 0/2/0), the VM's startup script was re-run over the admin route (`google_metadata_script_runner startup`, rc=0, no WARN/ERROR). The live `sync_users.sh` now reads `HOME_DIR` from `getent passwd`. `FUSE_F5930002A1`, host-provisioned at 12:19Z and never synced on the VM before, got its key and mounts in `/home/FUSE_F5930002A1` on its first sync. No new stray directory appeared. Two from the 11:39–11:41Z rollback resync remain in `/home/sftpuser/` (`~FUSE_44D8DBCFDB`, `~FUSE_9FAC0B372F`), unmounted and harmless.
  - **S4 again** (#374 then #375, live 12:19:18Z): same route, with #375's host plan read after #374 applied (3 added, 2 changed, 1 destroyed). The host provisioned `conn_e332870702df45e58f9a2a513d5f8bd2` / `FUSE_F5930002A1` in 7 s (`nk19`, 12:19:37Z).
  - **Continuity across the S4, rollback-S4 and S4-again rolls:** EPARFUM made 4 logins in each of the 56 minutes from 11:24 to 12:20Z. The canary was `host:success` ×12 from 11:20Z. The host logged no warnings from 11:00Z.
  - **FINDING, fixed in #377 (merged `a47a245`):** `cut.sh` stopped every time with `could not read live state (host_prov_state)` about 3.5 min after merging a template-changing PR. Terraform deletes the old template while instances still run from it. Each run resumed correctly once the MIG settled.
  - **Monitors:**
    - "Backend went unhealthy — dev" alerted on `sftp-host-dev` from the rolls' new-instance transitions, the known ramp-noise class.
    - "SFTP canary not running — dev" is alerting, but it isn't the cut. GCP's `run.googleapis.com/job/completed_execution_count` for the canary stopped reporting at ~00:45Z, 8 h before S3: Datadog shows 12 an hour until 00:00, then 0. All executions succeeded throughout. **UNKNOWN** cause. The monitor should read the canary's own `sftp canary` log outcome instead.
  - Parked runs: our runs for #369–#374 were cancelled. #375's (40685039778 host, 40685039643 connector) are parked at prod gates and not approved. Matt's 39944835679 and Renovate's 40662457459 were left alone.
  - **Red image scans cleared by #378** (merged `aa918c7`): go-jose/v4 4.1.6 for the host (CVE-2026-116587), and the npm-bundled undici CVEs allowlisted to 2026-11-04. Both #376 and #377 then passed their image scans. #378 rolled the dev host onto a new image (template replaced, `sftp-host:dev-768f78207160`), and #377 rolled it again because `cut.sh` sits under `apps/host`, whose tree hash is the image tag.
  - Parked runs after the merges: #375's two runs and #378's host run were cancelled as ancestors. #376's connector run (40707094751) and #377's host run (40707431426) are parked at prod gates and not approved.
  - Test connectors S4 `conn_da089ecd…`, rollback `conn_0d500678…` and re-apply `conn_e3328707…` were left in place, like S1's and S2's.
- 2026-10-28 [inc 4, AC 7] **Dev S3 done, drilled and re-applied** on Harry's go after ~20 h of S2 (decision below).
  - **S3** (#367): `cut.sh dev s3 --apply --pr 367` ran 09:32:49–09:37:18Z (269 s; drain-vm 211 s). Log `~/.local/state/sftp-cut/dev-s3-20261028T093249Z.log`.
    - Plan: the backend set went from host+VM to host, and the health check from `sftp-host-dev-ssh` to `sftp-host-dev-http`. Everything else was the usual preview-image noise on the template, MIG, canary and connector.
    - The 3 host instances went UNHEALTHY→HEALTHY on the HTTP check at 09:36:50–51Z, so the brief reset after the check swap lasted about 20 s.
    - EPARFUM made 4 logins every minute from 09:30 to 09:46, with none missed. The canary moved to the host: 09:40 and 09:45 `host:success`.
    - **After S3, verified:** the VM's `journalctl -u ssh` (over the admin route) has no customer session after the canary's 09:35:22Z run, only `sftpuser` from the admin route. Everything is served by the host.
    - "SFTP backend went unhealthy — dev" alerted on group `sftp-connector-dev-sftp-vm`. The VM logged one HEALTHY→UNHEALTHY transition as it left the backend (09:37:16Z). This is expected cut noise and the same class as the ramp noise.
  - **Rollback-S3 drill** (#368): `cut.sh dev rollback-s3 --apply --pr 368` ran to 09:52:31Z (257 s; vm-back 213 s). Backends went back to host+VM on TCP:22, all 4 HEALTHY at 09:52:09–11Z. EPARFUM was uninterrupted, and the canary returned to the VM at 09:55 (`vm:success`).
  - **S3 again** (#369): `cut.sh dev s3 --apply --pr 369` finished 10:02:05Z (240 s; drain-vm 195 s). Host-only 3/3 HEALTHY. The canary has been on the host since 10:05 and EPARFUM made 4 logins a minute throughout. The host logged no warnings from 09:30Z on.
  - Parked runs cancelled (ours, ancestors of master `c680fd6`): #367's, #368's and #363's connector run 40537438226. #369's runs (40668447069 connector, 40668446717 host) are parked at prod gates, not approved. Matt's 39944835679 and Renovate's 40662457459 were left alone.
  - **Owed:** S4 waits on the scoped config-service key gate, and the rollback-S4 drill comes with it.
- 2026-10-28 [inc 4, AC 6] **S2 dwell check-in at 00:30Z (~11 h into the split): clean.**
  - The live backend is 4/4 HEALTHY, the test backend 3/3, and the MIG 3/3 on one template. No health-check transitions since 19:30Z.
  - Canary: 130/130 green since 13:40Z, all on the VM side.
  - Host logins since 13:40Z: EPARFUM ×2,574, MANUCURIST ×108, nuzest ×43, ESCENTRIC ×10. The host logged no warning or error.
  - MANUCURIST's two former VM IPs moved to the host at the rejoin (52.21.250.44, 15:58Z) and the ramp to 3 (52.202.100.85, 16:08Z).
  - Both dev SFTP Host monitors are OK. VM-side partner logins weren't re-read; that needs the admin route.
  - Collated in orient: `Explainers/2026-10-28-sftp-host-dev-cut-s2-dwell.md`.
- 2026-10-27 [inc 4, AC 6] **Dev S2 done** after S1 held ~41 h clean (canary 498/498 since S1). `cut.sh dev s2 --apply --pr 359` ran 13:35:38–13:47:33Z (715.5 s; phase split 672.4 s, mostly connection draining as the MIG shrank 3 → 1). Log `~/.local/state/sftp-cut/dev-s2-20261027T133538Z.log`.
  - **Plan:** PR #359's host plan showed the backend set going from vm to host + vm, `target_size` 3 → 1, and a template replacement that was only the PR's preview image tag. The real dev apply was `0 added, 2 changed, 0 destroyed` (MIG, then backend service), and no instance was rebuilt. Connector plan: the image bump only.
  - **Final state:** backends=[host,vm], both HEALTHY ×1, mig=1 settled, admin_host and the forwarding rule unchanged, push on, host_prov=not-live.
  - **Two sides, both serving:** my client hit the host (`SSH-2.0-Go`) on all 10 of cut.sh's affinity connections. The canary hit the VM (OpenSSH banner) on every run after the split (13:40, 13:45, 13:50, 13:55, 14:00), all green. Through the LB, the host offers the same three pinned host keys.
  - **Real partner traffic is on the host:** `FUSE_BF827F7E3E` (EPARFUM) logs in about four times a minute from several AWS egress IPs (3.64.88.217, 3.64.142.243), all accepted. Real dev sales-order uploads kept flowing (e.g. `FUSE_1D0FDC2EC9` at 13:55, through dedupe and snap-adapter).
  - **Upload on each side archived:** the HJF "hjf test" user `FUSE_4366B07EED` uploaded a PRICAT through the host (LB from my IP, Go server) and another through the VM (admin IP, OpenSSH), with the pinned known_hosts. Both landed in `to_ilg/create_master_data/archive/` (`S2-SPLIT-HOST-PRICAT.EDI`, `S2-SPLIT-VM-PRICAT.EDI`). The VM's listing showed the file uploaded via the host, so both sides see the same storage. A first CSV pair resolved to 0 records because that connector's master_data mapping no longer matches the old CSV shape; those files were removed, and the issue is the test data, not a side.
  - **Provisioned during the split, logs in on both sides:** new connector `conn_3690bf75bd034eada5d230b0dbee5c83` ("sftp cut S2 provisioning check", HJF) provisioned `FUSE_70DC1115DA` via Cloud Run, with a three-field users.json record. Its key logged in at 14:00:51Z on the host via the LB and on the VM via the admin IP, first try on each, seeing `from_ilg`/`to_ilg`. **Left in place** (like S1's).
  - **Monitors:** "Fewer than 2 healthy instances — dev" is in a Datadog downtime (`05364d29-622e-4746-ad05-fb2197239032`, until 2026-10-31T00:00Z); cancel it once the host is ramped to 2+. All other dev SFTP Host monitors OK.
  - **Parked runs:** cancelled our #358 runs 40230337579 and 40230337576 (ancestors of master). Matt's 39944835679 is still left alone. #359's own runs (40513476330 connector, 40513476405 host) are parked at prod gates; no prod gates approved.
  - **Stickiness, checked 15:12Z (~1.5 h into the split):** each source IP stayed on one side, with no crossover. Host side from the host's `sftp login` logs; VM side from `journalctl -u ssh` over the admin route, since the dev VM's sshd lines aren't in Cloud Logging.
    - The canary made 19 of 19 runs on the VM from 35.197.208.45, all green.
    - EPARFUM `FUSE_BF827F7E3E`: its last VM session was 13:39:00, before the backend change. From 13:40:00 it made 368 logins on the host and none on the VM, from both of its IPs.
    - MANUCURIST `FUSE_521239C5D7` uses three IPs: 52.202.100.85 (7) and 52.21.250.44 (5) always on the VM, and 52.202.119.209 (7) always on the host. Stickiness is per client IP, not per user, as designed. A multi-IP partner uses both sides, and both see the same storage.
    - `FUSE_EC11DE9F4F` has made no logins, so these partners stand in for it. **AC 6 is evidenced in full.**
  - **Ramp to 2, 2026-10-27, brought forward to business hours on Harry's go as a smoke test.**
    - PR #360 (`sftp_host_size` 1 → 2). Its plan showed `target_size` 1 → 2 plus the PR preview image tag in the template. The real dev apply was `0 added, 1 changed, 0 destroyed`.
    - `cut.sh dev s2 --host-size 2 --apply --pr 360` ran 15:19:47–15:26:05Z (ramp phase 334.5 s; log `~/.local/state/sftp-cut/dev-s2-20261027T151947Z.log`).
    - New instance `sftp-host-dev-2bmz` is in europe-west2-c, alongside `5dvh` in -b, on the same template. The health check shows the VM HEALTHY ×1 and the host HEALTHY ×2.
    - **No client changed between the VM and the host** (sweep at 15:37Z):
      - The canary is still on the VM, green.
      - MANUCURIST 52.202.100.85 is still on the VM.
      - EPARFUM is still entirely on the host, now one IP per instance: 3.64.88.217 on `5dvh` and 3.64.142.243 on `2bmz`, 24 each, no failures.
      - Moving between host instances is invisible to clients (same keys and storage).
    - Downtime `05364d29…` was cancelled. All 13 dev SFTP Host monitors are OK.
    - #359's runs 40513476405/40513476330 were cancelled (ancestors of master `b7cdc56`). #360's runs 40529991273/40529991204 are parked at prod gates, with no approvals.
- 2026-10-27 [inc 4, AC 7] **Dev rollback-S2 drill, rejoin, and ramp to 3**, all in business hours on Harry's go.
  - **Rollback-S2** (#361, `sftp_host_backend`/`sftp_host_size` removed): `cut.sh dev rollback-s2 --apply --pr 361` ran 15:43:14–15:47:08Z. The host-out phase took 179.1 s from merge to live, mostly Deploy-run latency; scratch's 70 s had no Deploy run. The backend-service update operation ran 15:46:45–15:47:16Z.
    - **No client-visible outage.** EPARFUM made its 15:47:00 logins on the host, mid-propagation, and its 15:48:00 logins on the VM, first try from both IPs. No poll was missed and no login failed. MANUCURIST 52.202.100.85 stayed on the VM.
  - **Rejoin** (#362, the same change as #359): `cut.sh dev s2 --apply --pr 362` ran 15:50:59–16:02:16Z. The split phase took 658 s, mostly draining as the MIG shrank 3 → 1. Result: backends=[host,vm], both healthy. After the rejoin, EPARFUM and MANUCURIST 52.202.119.209 were back on the host, the same as the first split.
  - **Ramp to 3** (#363): `cut.sh dev s2 --host-size 3 --apply --pr 363` ran 16:04:26–16:11:12Z (ramp phase 347 s). The real dev apply was `0 added, 1 changed, 0 destroyed`. Instances: `2xtj` in -a, `3w7j` in -b, `bskg` in -c, all on the same template and HEALTHY ×3, with the VM HEALTHY ×1.
    - EPARFUM stayed on the host (both IPs on `2xtj`, every minute present). MANUCURIST 52.202.119.209 is on `bskg`, and the canary is on the VM.
    - cut.sh's own client moved from the VM to the host on this ramp. Adding instances does re-hash some client IPs, unlike scratch's 1 → 2. That's harmless to clients, since both sides have the same keys and storage.
  - **FINDING: the TCP:22 health check passes a booting host instance on the OS's own sshd.**
    - Health check `sftp-host-dev-ssh` is TCP:22, interval 10 s, healthy 2, unhealthy 3. On a new COS instance, the OS's sshd answers port 22 for about 20–30 s, with its own per-instance host keys, not the pinned three. Then cloud-init stops it and port 22 refuses until the container is up, about 70–90 s later.
    - Health-check log for `2bmz` on the ramp to 2: HEALTHY at 15:23:52, UNHEALTHY at 15:24:21 (connection refused), HEALTHY again at 15:25:31. The ramp to 3 showed the same pattern for `bskg`/`3w7j`: 16:08:40 → 16:09:23 → 16:10:33, with the container listening at 16:10:20.
    - **Customer-visible once:** EPARFUM made only 2 of its 4 logins at 15:24:00, inside `2bmz`'s false-healthy window, and the missing IP landed on `2bmz` from 15:26. COS's sshd lines aren't in Cloud Logging, so what the client saw (a host-key mismatch or an auth failure) isn't confirmed.
    - The same window opens on every new instance that joins while serving: a ramp, autohealing, or a rolling template update. **It needs fixing before S3 removes the VM and before prod.** Probe the container rather than port 22. The MIG's autohealing check already does this (HTTP 8080 `/healthz`, `iac/projects/sftp-host/compute.tf`, with the firewall open to 8080), and `/healthz` returns 200 only once users.json is loaded and the SSH listener is open. Only the LB backend's check, `sftp-host-dev-ssh`, is TCP:22. So the fix is a regional HTTP 8080 `/healthz` check on the backend service.
  - **Fix, in two PRs.**
    - **#364** (merged `082f6ab`, Deploy run 40547155194, dev apply `1 added, 2 changed, 0 destroyed`):
      - `sftp-host-dev-ssh` is now interval 5 s, healthy 10, unhealthy 3, so about 50 s of consecutive success is needed.
      - A new `sftp-host-dev-http` check probes HTTP 8080 `/healthz` (10/5/2/3, logged). The test backend uses it.
      - The `sftp` backend picks `var.sftp_vm_backend ? ssh : http`, so S3 swaps it to the HTTP check in the same apply that removes the VM.
      - The live backend recovered all 4 HEALTHY by 17:07:56 after a brief health-state reset. EPARFUM was present every minute and the canary stayed green.
    - **#365** (merged `3a0e936`, Deploy run 40568361993, dev apply `0 added, 1 changed, 0 destroyed`):
      - #364 left the test backend UNHEALTHY with probe TIMEOUTs from 209.85.204.x. Passthrough NLBs also probe from 209.85.152.0/22 and 209.85.204.0/22, and the `sftp-host-dev-health` firewall only allowed the autohealing ranges on 8080.
      - #365 adds both ranges. All 3 test-backend instances went UNHEALTHY→HEALTHY at 19:24:41Z, and the live backend stayed 4/4 HEALTHY.
      - In the 25 min around the apply: canary `vm:success` ×5, EPARFUM ×100 and MANUCURIST ×5 host logins.
      - The prod plan and apply were `No changes` (prod has no host stack yet). Both prod gates were approved under `/ship SHIP-1027-sftp-health-firewall`.
      - The parked host runs 40547155194 (#364) and 40537439143 (#363) were cancelled as ancestors. Connector run 40537438226 (#363, the newest connector Deploy) and Matt's 39944835679 were left parked.
  - Parked runs for #360/#361/#362 were cancelled (ancestors of master `37ee2e4`). #363's runs 40537439143/40537438226 are parked at prod gates, with no approvals. Matt's 39944835679 was left alone.
  - **Not yet:** the S2 dwell (3 days from 2026-10-27 → S3 no earlier than 2026-10-30), then S3 (which now also swaps the live backend to the HTTP `/healthz` check, proven on the test backend by #365).
- 2026-10-25 [inc 4, AC 5] **Dev S1 done** (`cut.sh dev s1 --apply --pr 358`, 20:18:48–20:24:19Z, 331.7 s; log `~/.local/state/sftp-cut/dev-s1-20261025T201848Z.log`). Two changes went first: #357 (`sftp_vm_backend = true`, plan was the VM backend add plus image-tag noise), and #355 (below).
  - **Gates:**
    - **Canary:** 867/868 executions green, 2026-10-22 19:40Z → 2026-10-25 19:50Z. The only failure is the pre-key run.
    - **Parked runs:** cancelled 7 parked host Deploy runs and 1 connector run (all ours, all ancestors of master, every prod plan `No changes`).
    - **Dev host:** MIG 3/3 HEALTHY and stable, and every dev SFTP host monitor is OK.
  - **Blip: 18.1 s, one outage.** My 1 s `ssh-keyscan -t ed25519` probe was down 20:19:28–20:19:46 (9 of 300 probes, about 2 s apart while down because of `-T 2`). cut.sh's 0.5 s banner probe also measured 18.0 s. The swap took 10.8 s and the rule POST 17.6 s; scratch had measured 22.5 s.
  - **Same IP and keys, no warning.** DNS `sftp.integrations.freightops.dev` → 34.142.66.200, and the forwarding rule `sftp-host-dev` is on 34.142.66.200 TCP/22 EXTERNAL, adopted by Terraform (`fr_in_tf=true`). The host keys before and after match the pinned three, and every key the probe saw was the VM's Ed25519. The banner is still `SSH-2.0-OpenSSH_9.2p1 Debian-2+deb12u10`, and the backend is `sftp-connector-dev-sftp-vm` HEALTHY x1.
  - **Re-plan check passed:** #358's re-plan showed "imports the forwarding rule; otherwise only the image tag (1 template replacement, 2 in-place)", and cut.sh merged it.
  - **Canary green through the LB:** the 20:20:27 and 20:25:21 runs succeeded with `side=vm`, `addr=34.142.66.200:22`.
  - **Logins land on the VM, client IPs preserved** (VM ssh journal since 20:19:40 Z, read over the admin route): `FUSE_BF827F7E3E` ×40 from 3.64.88.217, `FUSE_521239C5D7` from 52.21.250.44, `FUSE_6C539A96E9` from 110.173.133.231, canary `FUSE_525C87DEB7` from 35.197.208.45. `FUSE_EC11DE9F4F` hasn't logged in at all in the last 7 days, so these real partner logins stand in for it.
  - **Provisioning through the admin address:** I created connector `conn_b61ac7657ab74b7a9adf462eb04efcdc` ("sftp cut S1 provisioning check", HJF), and the connector provisioned `FUSE_F6A1BE37D1` at 20:24:50–57.
    - Revision `sftp-connector-dev-cr-00870-zth` ran it, with `SFTP_ADMIN_HOST=34.147.156.89`. The VM logged `sftpuser` from 34.34.246.238 at 20:24:51–52.
    - On the VM: the user is in `sftpgroup`, with `to_ilg`/`from_ilg` and 2 mounts.
    - The key `SHA256:f2VzaFkj…qgg8` matches across `authorized_keys`, the `users.json` record (HJF, ssh-rsa) and the connector's publicKey.
    - The admin address offered exactly the three pinned host keys.
- 2026-10-22 [inc 3] **Cut tooling merged (#352 → `4cc58ba`)** after two independent reviews.
  - **Round 1 fixes:** the swap is resumable with preconditions; failed reads stop the step; health gates on S3, rollback-S2 and S4; the two-consumer alert; `--pr` scope checks; host keys pinned.
  - **Round 2:** S1's post-swap plan check didn't allow the canary job's per-commit image update. Fixed with a diff-level parser and 20 self-test cases built from real PR plan comments, all giving the expected verdict (re-run by me).
  - **S1 redesigned:** the script creates the static-IP forwarding rule through the Compute API, which matches lb.tf field-for-field; gcloud's `--ports` stores `portRange 22-22`, which forces a Terraform replace. Terraform adopts the rule with an `import` block gated off in prod. The S1 blip on scratch is **22.5 s**, against 3–4 min if the Deploy run created the rule.
  - **Timings on scratch:** rollback-S1 31.5–36 s; S2/S3 and their rollbacks with 0 failed probes; rollback-S4 261 s.
  - **Never run live:** the GitHub side of `--pr`. Inc 4's first step is its first full run.
- 2026-10-22 [inc 3] #353 removed the canary scheduler's perpetual `retry_config` plan diff.
- 2026-10-22 [inc 3, AC 8] **Monitoring and canary live in dev.**
  - **Datadog shipping:**
    - #348 put a Datadog Agent on each host instance, but it never started: its fixed 172.30.0.2 was the first dynamic Docker address, and the SFTP host container took it (COS docker events showed a create/attach/destroy loop). #351 fixed it with `--ip-range 172.30.0.128/25`.
    - After that, `service:sftp_host` logs and `fuse.sftp_host.*` metrics arrive per instance. `login.failed` and `sftp_login.unknown_user` are already non-zero: internet scanners on `sftp-next`, counted only.
    - #350: a failed connectorId lookup increments `audit.connector_lookup_failed`.
  - **Canary (#349):**
    - The "sftp canary" connector `conn_dddbfb6a…` (user `FUSE_525C87DEB7`, provisioned by the connector on the VM and in users.json). Its key went into `sftp-host-dev-canary-key` v1, piped from config-service.
    - First job run: `success side=vm`, 2172 ms, OpenSSH banner, via the static IP `34.142.66.200`. Cloud Scheduler `*/5 * * * *` is ENABLED. The 3-day green window starts at about 19:45 UTC on 2026-10-22.
  - **Monitors (observability#76, applied 25 added / 1 changed / 0 destroyed):**
    - 24 monitors: dev copies published and notifying nobody; prod copies `draft_status = draft`, which neither evaluate nor notify, except the prod create_sftp_user DLT monitor, published because the connector already dead-letters there.
    - Dev states after apply: all OK, except "canary not running", which is No Data until the GCP execution metric arrives.
- 2026-10-22 [inc 3] **Cut tooling (#352, draft).** Rehearsed on scratch `sftp-host-rehearsal-*` resources, all deleted afterwards.
  - **The four facts:**
    - the guest agent serves the forwarding-rule IP;
    - the access-config swap is in place, about 7 s, with no stop or restart (instance id, start time and boot id unchanged);
    - one instance group can back two passthrough backend services;
    - `CLIENT_IP` affinity holds 12/12 reconnects for each of 8 client IPs, and ramping the host from 1 to 2 instances moved none.
  - **Timings on scratch:** rollback-S2 70 s and rollback-S3 71–79 s, with 0 failed probes. With the Terraform-created forwarding rule, the real S1 blip would be 3–4 min (Deploy-run latency).
  - **Independent review: BLOCK for `--apply`.** The swap isn't resumable, failed gcloud reads count as absent, and S3/rollback-S2 have no health check. Being fixed, with the faster S1 (gcloud-created forwarding rule adopted by a Terraform `import` block, reviewer-confirmed sound on TF 1.9 / google 6.41).
- 2026-10-22 [inc 1, AC 1, 2, 4, 9] **Host provisioning end to end in dev (test mode).**
  - **What's live:** #335–#339, #342 and #343 merged (`c5f73fe`; every merged tree equals its reviewed tree). #346 set dev `test` mode, and #347 fixed the type check. Dev runs `8cc36c4`, with consumers on `create_sftp_user_dev.host_test.v1.sub` only.
  - **Connector held:** the connector's `create_sftp_user_dev.v1.cloud_run_sub` was set to pull from 17:02:32 to 17:06:21 UTC. Its push config was then restored byte-identical, and no other message arrived in that window.
  - **Test connector:** `conn_176c7d97ebbf423a903f7132e91dd984` ("sftp-host provisioning test", HJF) was created PENDING. Its queued message was pulled, copied to the test topic and acked on the connector side, so the connector never provisioned it.
  - **First run: a real bug.** It logged `skipped … not_sftp`: the host compared against `"SFTP"`, while config-service sends `"sftp"`. The same mismatch made the connectorId lookup's `type=SFTP` a 400. The fakes used the host's own constant, so three review rounds missed it. Fixed in #347.
  - **Re-run at 17:26:53:**
    - `sftp user provisioned FUSE_9FAC0B372F`;
    - exactly 1 `users.json` record (raw `HJF`, RSA);
    - 10 folders plus their parents;
    - claim object `.provisioning-claims/conn_176c…`;
    - config-service reports `status: active`;
    - one `sftp_user` audit row (`created`, producer `sftp-host`, keySource `generated`, fingerprint `SHA256:NtPLwIfK…`, which matches the users.json key).
  - **Duplicate publish (17:27:38):** `skipped not_pending`; still 1 record and the same key (AC 2).
  - **Live consumer:** the connector stayed its only consumer throughout (AC 4).
  - **Prod:** no Terraform changes for the host or the connector; parked ancestor runs were cancelled.
- 2026-10-22 [inc 2 follow-up] After #347, a login as `FUSE_9FAC0B372F` (temporary key, removed afterwards) stored `sftp_login` with `connectorId: conn_176c7d97…`.
- 2026-10-22 [inc 2, AC 3] **Login audit live in dev.** #330–#333 were merged and dev applied; the MIG rolled 3/3 HEALTHY onto a template with `AUDIT_ENABLED=true` and `AUDIT_TOPIC=…/audit.dev.fuse.v1`. The host prod plan was `No changes` and was approved, so it only pushed the image. Logins on `sftp-next` at 11:15:5x UTC with a temporary `FUSE_HJFHOSTTEST` (raw `HJF`) record, read back from dev Atlas:
  - two `logged_in`/accepted rows with IP `31.51.121.239`, the source port and the right key's fingerprint;
  - a wrong key gave one `login_failed`/`auth_failed` row carrying the rejected key's fingerprint;
  - `ssh -o PreferredAuthentications=none` gave one `login_failed`/`closed_before_auth` row with no fingerprint;
  - the unknown username `FUSE_NOSUCHUSER9` produced 0 rows and 0 host log lines;
  - every row had tenant `HJF`, producer `sftp-host`, `expireAt` = occurredAt + 1y, and a uuidv5 `_id`. That `_id` is the deterministic eventId, so a replay can't duplicate a row.
  - `connectorId` is absent, as expected: there's no source until inc 1's Config API client lands.
  - The record was removed afterwards with no concurrent changes.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- [inc 1, AC 10] A new directory-list entry reaching every existing dev user on rollout was proven only against fake-gcs-server (create-only reconcile, a second run creates nothing). The real dev check would add a test folder to every dev user, so it's left until a real use-case folder ships.
- [inc 1] Claim behaviour under concurrent replicas and stalls was proven against the emulator, not real GCS. The single-message dev run exercised the claim create and settle only.

## Rollout & rollback
<!-- Added on demand. Written at plan time; amend in place as it changes.
     `Shared state touched:` is the single home for the five classes git does not own — a dev
     deploy, a prod config write, a Datadog monitor, a CI var or secret, cross-repo IaC. Reverting
     the branch undoes none of them, so if they are not written here they are not written down. -->
- **Order:**
  - inc 3's rehearsal, monitors and canary before any inc 4 step;
  - S1 → S2 → S3 → S4, never skipping;
  - within S4, push off (`consumer=host`) **before** `PROVISIONING_ENABLED=true`;
  - on rollback, the reverse.
- **Flags/config**, all dev tfvars merged on master, never through manual deploy:
  - host `vm_backend`: `false` → `true` (S1) → `false` (S3);
  - host `serve_static_ip`: `true` (S1);
  - connector `SFTP_ADMIN_HOST`: set at S1;
  - host `host_backend`: `true` (S2);
  - connector `create_sftp_user_consumer`: `host` (S4);
  - host `PROVISIONING_ENABLED`: `true` (S4).
- **One-way doors:** none in dev. Every step has a drilled rollback.
- **Rollback:** see inc 3. S2 and S3 roll back by backend change with no outage. S4 needs a VM sync if the host provisioned anyone. S1 is an IP move back.
- **Shared state touched:**
  - dev VM access config;
  - dev forwarding rules and backend services;
  - the dev `create_sftp_user` subscription mode;
  - dev `users.json`;
  - Datadog monitors in the observability repo;
  - a dev Cloud Scheduler job and Cloud Run job;
  - scratch rehearsal resources (deleted after);
  - UJ plan and Migration State rows.
- **Proof in prod:** n/a; this plan is dev-only. Prod plans stay no-op.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-10-29 (Harry)** — Plan B signed off with recorded deviations (Harry trusted the agent's recommendation, 2026-10-29). (1) AC 7: rollback-S1 was timed on scratch only (31.5-36 s); dev never rolled back past S1. Carried to Plan C inc 2 as a gate: rehearse rollback-S1 on scratch with the current cut.sh before prod S1. (2) AC 8: the bad config-service key fault was not injected, and the failed-login, provisioning, audit-publish, Config API, connector-lookup and DLT monitors have never fired. The users.json monitor fired on an injected fault; unhealthy-backend, canary and instance-count fired for real. Carried to Plan C inc 3 as a gate: bad-key injection in dev before prod login audit turns on. Prod copies stay drafts until then. (3) AC 9: #376 changed the prod VM startup-script metadata (inert until re-run), applied with the 2026-10-29 connector deploy; every other prod plan was a no-op. (4) AC 10 is proven against fake-gcs-server only (see Not verified). (5) Inc 4's parked-runs gate: Matt's 39944835679 was left on Harry's instruction; it can't reapply dev.

- **2026-10-28 (Harry)** — Agreed the follow-up below for the dev soak only: Plan C inc 1's 2-week dev soak gate is now exit criteria (72 h clean on the host since its last dev change, canary monitor on the logged outcome, unhealthy-backend monitor quiet through one roll). Prod dwells unchanged.

- **2026-10-28** — Harry: go ahead with dev S4 as planned, with the host as provisioner. The scoped config-service key gate moves from "before dev S4" to Plan C inc 1, "before the prod host holds the prod config-service key". Reasons:
  - config-service has one API key (`AUTH_API_KEY`, a single-value compare in `auth.middleware.ts`) with no scoping.
  - The dev host already holds the dev key for login audit.
  - Scoping also needs a design call: the list route returns every connector ID, and `GET /connectors/{id}` returns private keys.
- **2026-10-28 — REVISIT AFTER THE MIGRATION (Harry: "too many moving parts"):** where a user's truth lives. Today a user is split across config-service's connector record and `users.json`, joined by the `create_sftp_user` → `customer_creation` round trip. Options:
  - **(A)** The host provisions, as built. It needs a config-service key on the internet-facing box.
  - **(B)** The Cloud Run connector keeps provisioning, minus its SSH-to-VM steps, and writes `connectorId` into `users.json`. The host becomes a read-only data plane with no config-service key.
  - **(C)** config-service owns the user and writes `users.json` as a derived copy. One source of truth, one writer, no message loop. Needs a backfill of legacy users with no connector, and ends hand edits.
  - Agent recommendation: B as a stepping stone to C. Separately, we generate and store customers' private keys; accepting the customer's own public key is a product question.
- **2026-10-28** — Harry: run S3 now, not after the 3-day S2 dwell ("less concerned with dev going down and we know that we can rollback"). The reasoning: the dwell's stated job, raising the host share, was finished on day one with the ramp to 3. Dev's few partner clients add little evidence with more time. The real gates are transitions and drills, the S4 scoped-key gate, and prod-side coverage. A follow-up was proposed but not yet agreed: replace the dwell timers in Plans B and C with exit criteria (24 h steps, prod S2 exit on baseline-partner coverage, a shorter dev soak).
- **2026-10-27** — S2 ran 2026-10-27 on Harry's go. The instance-count monitor is muted by a Datadog downtime (until 2026-10-31) rather than an observability PR, so it lifts itself; cancel it early once the host is at 2+.

- **2026-10-25** — cut.sh's parked-runs guard now counts a run only until it has applied the env being cut (#355). A connector run parked on its prod approval blocked the dev cut and its rollback, even though it can't reapply dev tfvars. Prod (Plan C) still refuses on runs parked at the prod gate.

- **2026-10-24** — Harry (2026-10-24, OOO Mon): run S1 Sunday 2026-10-25 after the canary's 3-day window (~19:45 UTC), hold S2 until he's back on Tue 2026-10-27 — dwell is a minimum. For the unattended window, observability#77 routes 'SFTP canary failing — dev' and 'Fewer than 2 healthy instances — dev' to #bifrost-notifications (revert the sftp_host_dev_cut_handles local after S4 soaks; mute the instance-count one during S2, which runs one host instance). Matt notified by bot DM; no prod gates needed for the cut. Matt's parked connector run 39944835679 (#344) also removes Harry's hjf ssh key from prod VM metadata.

- **2026-10-22** — Inc 1 reviewed by three independent agents (correctness, security, rollout): all SHIP. Fixes before live go in as a 7th stacked PR: claim fencing + work deadline, shutdown-safe publish, re-read after claim, startup retry, public-key validation, https-only Config API, no key on redirects, least-privilege IAM gating, connectorId lookup only for known users with a bounded cache, and a Terraform guard against live provisioning while the connector still consumes. AC 2 holds unless config-service lags beyond the claim's settle window. Gate added on S4: a dedicated scoped config-service key.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
