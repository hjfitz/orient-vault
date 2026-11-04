---
ticket: none
title: 'SFTP host C: prod cutover and VM decommission'
service: sftp-connector
status: active
created: '2026-10-20'
updated: '2026-11-03'
repo: /home/hjf/code/fuse/sftp-connector
worktree: unknown
branch: unknown
base: origin/master
base_sha: unknown
pr: null
tags:
- waypoint
- plan
impl_model: opus
impl_effort: medium
---
# none — SFTP host C: prod cutover and VM decommission

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
Plan C of three ([[sftp-host-a-monorepo-host-image-and-dev-infrastr|A]] → [[sftp-host-b-provisioning-login-audit-and-dev-cut|B]] → C). It cuts **prod** SFTP over to the host with the steps drilled in dev, one step at a time with a dwell and a check between each:

- **S1:** the static IP moves onto the load balancer, with the VM as its only backend;
- **S2:** the host joins and traffic splits by client IP;
- **S3:** the VM is drained;
- **S4:** provisioning switches to the host.

The VM then stays warm for two weeks before the SSH provisioning code and the VM are retired. Done means every prod customer is served by the multi-zone host with no change on their side (same IP, host keys, paths and keys), and the VM, admin key and SSH code are gone.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [ ] 1. The prod host on its temporary IP presents the prod VM's host-key fingerprints and a superset of its algorithms, and an internal user logs in and sees the expected tree.
- [ ] 2. S1 in prod changes nothing customers can see apart from one short connection blip: every baseline username keeps logging in to the VM.
- [ ] 3. During the prod split, each customer IP stays on one side, both sides serve the same files, and session rate, `new_file` throughput and archive/error routing stay at baseline.
- [ ] 4. After S3/S4, every username from the pre-cut prod baseline logs in to the host within 24 h. Session rate is at baseline (about 8k/day), with no spike in `ConnectorUnresolvable` or `InvalidPath`, and the first prod SFTP connector created afterwards goes ACTIVE through the host with one key.
- [ ] 5. From S2 on, every host login is in audit-service (`sftp_login`) and in Datadog logs. The VM's `auth.log` isn't mirrored or kept (Harry, 2026-10-20). `sftp-key-access-audit` reads both sides.
- [ ] 6. Through the rollback window, each step can be rolled back in the time drilled in dev.
- [ ] 7. After decommission:
  - Cloud Run boots without `SFTP_ADMIN_*`;
  - the prod plan shows only the intended deletions, with no bucket, IP, DNS or subscription diff;
  - a new dev SFTP connector still provisions end to end.
- [ ] 8. `CLAUDE.md`, both SFTP skills (and the `~/.codex` copy), the vault docs and fuse-mcp data describe the host, not the VM.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- **Prod resources:**
  - `iac/projects/sftp-host` with `host_enabled`, `vm_backend`, `host_backend` and `serve_static_ip` in `prod.tfvars`;
  - the connector's `create_sftp_user_consumer` and `SFTP_ADMIN_HOST` in `prod.tfvars`;
  - the prod VM's access config (static IP → `sftp_vm_admin_ip`);
  - the prod static IP (the IP literal is in every SFTP connector's `config.host` and config-service's `SFTP_DEFAULT_HOST`).
- **Deleted at decommission:**
  - `compute.tf` (`sftp_vm`, its unmanaged instance group, `sftp_vm_admin_ip`), `scripts/startup.sh.tpl` and `keys.tf`;
  - `cloud-run.tf:149-156` (`SFTP_ADMIN_*`, plaintext env today) and `SFTP_ADMIN_HOST`;
  - `sftp-login-audit.tf` and its variable;
  - `apps/connector/src/adapters/ssh-adapter/*`, the `core/sftp-user-builder/*` builder, `core/crypto-module/*`, and the `create_sftp_user` route at `pubsub.controller.ts:125-127` with its handler at `:644-746`;
  - the `SFTP_ADMIN_*` schema fields (`app-config/schemas.ts:74-75`) and the compose env (`docker-compose*.yaml`);
  - `node-ssh`/`ssh2` and their `allowBuilds`.
- **Kept, because the remaining publisher uses it:** `SFTPUserBuilderException.ConnectorReadFailure` (`connector.config-handler.ts:9,58`).
- **The subscription keeps its name.** It stays as the host's pull subscription; `.cloud_run_sub` is cosmetic, and renaming it forces a recreate that loses the backlog.
- **Docs and data:**
  - fuse-mcp(-server) `data/{pubsub-topology.json` (add `create_sftp_user`, publisher sftp-connector, subscriber sftp-host), `services.json`, `api-endpoints.json:182`, `deployment.json:123}`;
  - vault `architecture.md`, `operations.md`, `interfaces.md`, `known-context.md` (guardrail G5), and the UJ plan;
  - skills `/home/hjf/code/.claude/skills/{sftp-partner-key,sftp-key-access-audit}`.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- Prod volume is 8,072 sessions on 2026-10-14 across 10 users, one polling about every 15 s (UJ evidence, Audit decision log). S1's IP move drops in-flight sessions for about 30–60 s, and pollers retry. S2/S3 have no blip.
- With about 10 customer IPs, `CLIENT_IP` affinity splits by customer, not by percentage. One host instance next to the VM puts roughly half the customers on the host. Which ones is decided by hash, so the first S2 check lists which customers landed on which side.
- Prod applies go through two `terraform-prod` gates, and approving a prod gate ships all of master since the last prod deploy. Before each step's approval, list `git log <prod-sha>..<run-sha>`.
- known-context's position that "VM + gcsfuse is still considered correct" was about not replacing plain SFTP with a managed transfer service, and that still holds: customers keep plain SFTP, and downstream stays GCS-native. Record it with `wp decide --record` when this plan activates, and supersede the known-context line and guardrail G5 at sign-off.
- VM hardening was dropped (Harry, 2026-10-20), so the VM's shell and whole-bucket exposure lasts until S3 takes it out of service, and its port 22 stays reachable on the admin address until decommission. Re-scope the VM's firewall to the IAP range and Cloud Run's egress only after S4, if Cloud Run's egress range is fixed. TODO: check that during inc 4.
- UJ stopped after inc 1, which never installed the Ops Agent (stages `prep` in dev, `off` in prod), and Plan A inc 2 sets dev back to `off`. So decommission just deletes `sftp-login-audit.tf` and its variable; no `removing` step is needed.
- The cut is meant to be invisible to customers: no notice (Harry, 2026-10-20). S1's IP move is the only blip, about 30–60 s of dropped in-flight sessions that pollers retry. It runs in the quietest hour of the prod week, read from the inc 3 `auth.log` baseline.
- Prod dwell times (Claude, delegated by Harry 2026-10-20): S1 → 48 h → S2 → at least 1 week, raising the host share in steps → S3 → 48 h → S4. Any monitor firing or parity check failing restarts the current dwell after the fix.
- The VM stays warm for two weeks after prod S4 (Claude, delegated). Its disk is snapshotted before deletion and the snapshot kept 30 days, as insurance only: the host keys already live in Secret Manager, and `auth.log` isn't needed (Harry).

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
- [x] 1. Prod host live on a temporary IP, out of the cut path (AC 1). — prod host 3/3 HEALTHY on 34.13.39.94; keyscan = VM; ssh-audit gaps as dev; nothing written to bucket; support login not run (no key) — done: b9d344b
      gate: Plan B signed off
            [x] confirmed 2026-10-29: complete with recorded deviations (Harry); two carried here as inc 2 and inc 3 gates
      gate: dev soak exit criteria, all met (replaced the 2-week timer, 2026-10-28):
            (a) clean on the host from its last dev change (the 2026-10-28 14:50Z roll) to end of day 2026-10-29 (17:30Z): zero host warn/error lines, every canary run green, `provisioning.failed` = 0 and an empty `create_sftp_user` DLT. A rollback or a host fix for a defect in the window resets it; the planned roll for (c) does not. Shortened from 72 h by Harry on 2026-10-29;
            (b) the canary monitor (335786602) reads the canary's logged outcome, not GCP's execution count, and is OK;
            (c) the "backend went unhealthy" monitor (335786592) stays quiet through one planned dev host roll, which EPARFUM rides with no missed minute
            [x] confirmed 2026-10-29 20:21Z: (a) 0 host warn/error apart from 3 injected-fault lines, canary host:success x355, provisioning.failed 0, both create_sftp_user subs empty; (b) 335786602 OK on the logged outcome (observability#80); (c) roll 15:49-16:01Z, 0 HEALTHY->UNHEALTHY, EPARFUM 4/min (#380)
      gate: prod host keys lifted exactly as in Plan A inc 5 (every key type, piped over IAP, fingerprints matched to `ssh-keyscan`), and the prod `users.json` version history checked for signs the root path was used. Any sign stops the plan for an incident decision.
            [x] confirmed 2026-10-29: three keys into `sftp-host-prod-ssh-host-*-key` v1, fingerprints match keyscan and the IAP-pinned baseline; users.json history (35 versions) clean

      - Set `host_enabled=true` in `prod.tfvars`, with `PROVISIONING_ENABLED=false`, on the `sftp-test` temporary address. No DNS.
      - No `CONFIG_SERVICE_*` env and no IAM on any config-service key secret until S4: the app needs the key only when provisioning is on (`config.go:132`), so prod `sftp_login` events carry no `connectorId` until then.
      - TODO before prod login audit goes on (inc 3 gate): the IaC still wires the key whenever login audit is on (`provisioning.tf:6,22`, `config_api_access`/`config_api_env`). Decouple it so prod gets the key only with provisioning; dev can keep it.

      — verify:
      - `ssh-keyscan` fingerprints equal the prod VM's;
      - `ssh-audit` shows the host offers every KEX and host-key algorithm the prod VM offers;
      - the internal `support` user logs in and sees `to_ilg from_ilg`;
      - prod host logs and metrics appear in Datadog;
      - nothing is written to the prod bucket by the host.
- [ ] 2. S1 in prod: the static IP onto the load balancer, VM only (AC 2,6).
      gate: connector deploy freeze for the window; parked prod Deploy runs cancelled; S1 tfvars PRs approved in advance
            [x] confirmed 2026-11-02: freeze 15:30–17:30Z posted in #bifrost-forge and DMed to Matt and Schuster; no Deploy run in flight or parked at 15:50Z pre-flight; #386 held for `cut.sh` (no-review window, Harry's go on time and approach)
      gate: rollback-S1 rehearsed again on scratch with the current `cut.sh`, timed (carried from Plan B AC 7: dev never rolled back past S1)
            [x] confirmed 2026-11-02: two scratch cycles on `1ebd880`. S1 blip 18.0 s both times. Rollback-S1 blip 31.5 s on an idle machine (matches 10-22) and 63.6 s under load avg ~17, because gcloud reads were slow. Run the prod rollback from an unloaded machine.

      - `cut.sh prod s1`.

      — verify:
      - DNS and IP unchanged, with no host-key warning;
      - for 48 h every baseline username keeps logging in on the VM (`auth.log`);
      - ingest and archive/error rates on `service:sftp_connector` sit within the pre-cut band;
      - a new prod SFTP connector, if any is created in the window, provisions through `SFTP_ADMIN_HOST`.
- [ ] 3. S2 in prod: the split (AC 3,5,6).
      > SUPERSEDED 2026-11-02 — Harry dropped this gate for the one-day S2 trial: #388's host logging (handshake mismatches, refused shell/exec/scp requests) and the VM's sftp-server session lines, watched at S2, replace the 4-week baseline.
      gate: 4 weeks of prod `auth.log` baseline: no customer uses shell, exec or scp; client KEX and host-key algorithms are within the host's; the username set is captured for AC 4
            [x] confirmed 2026-11-02: dropped by Harry (see the SUPERSEDED note and Decisions)
      gate: before prod login audit turns on, inject a bad config-service key into the dev host and confirm "Config API unavailable" and "Login audit connector lookups failing" fire (carried from Plan B AC 8). Then publish the prod copies of the monitors that S2 makes live.
            [x] confirmed 2026-11-02: both dev monitors fired and recovered, dev restored; observability#81 merged (`de39801`) and applied 0/10/0 (run 41504609330), all 10 prod SFTP Host monitors published (Evidence)
      gate: prod `users.json` linted (every username passes `^[A-Za-z0-9_.-]+$`, no unknown key options, skip list reviewed), plus a key-set diff (live `authorized_keys` vs `users.json`, per user, both directions) with every key that would work on only one side accepted
            [x] confirmed 2026-11-02: the host's own parser reads all 41 users and 45 keys, skips none and finds no options. 0 keys work only on the host; 5 VM-only accounts never logged in and were never in users.json, so they're accepted as dormant (re-check at S2)
      gate: host `sftp_login` live in prod (with the Audit programme's prod gates A1, A2 and F1); host logs in Datadog; `sftp-key-access-audit` rewritten to read audit-service and Datadog
            [ ] confirmed — partly, 2026-11-02: #389 turned prod login audit on (host run 41491974634, `AUDIT_ENABLED` + config key), A1/A2/F1 are in the prod images, and host logs reach Datadog. `sftp-key-access-audit` rewritten (Step 3 reads both sides from S2: host `sftp_login` events via `audit-search` and `service:sftp_host` "sftp login" logs, merged with the VM's auth.log). Still owed: seeing a host event land in audit-service (Fuse MCP `audit-search` is down, 401); first real S2 login proves it

      - `cut.sh prod s2` with one host instance. List which customer IPs landed on the host.
      - Raise the host share in steps over the dwell.

      — verify:
      - each customer IP sticks to one side;
      - customers on the host have the same login cadence as their pre-split baseline;
      - uploads from host-side customers are archived;
      - the host shows zero `users_json.invalid_record` and zero auth errors;
      - ingest rates are at baseline.
- [ ] 4. S3 then S4 in prod: drain the VM, then switch provisioning (AC 4,6).
      > SUPERSEDED 2026-11-02 — Harry waived this gate: the prod host takes the shared master key from S2, for login audit's connectorId lookup and later provisioning. The scoped key is parked for a waypoint-ideate session (see Decisions).
      gate: before the prod host holds the prod config-service key (login audit or provisioning), it reads a dedicated key scoped to what it needs, not core-infra's shared master key. config-service has no scoped keys today, and the scope must stop the list route enumerating connectors and `GET /connectors/{id}` reaching non-SFTP connectors. Moved here from Plan B inc 4 on 2026-10-28, then from inc 1 to here on 2026-10-29. Moot if the post-migration revisit picks option B or C, since the host would then hold no key.
            [x] confirmed 2026-11-02: waived by Harry; the host uses the master key
      - Before `cut.sh prod s4`, re-run the prod VM's startup script over IAP, as dev did on 2026-10-28. #376's `getent` fix reached prod metadata on 2026-10-29 but not the VM's live `sync_users.sh`. Without the re-run, a host-made user can't log in on the VM after a rollback-S4.
      - `cut.sh prod s3`, then a 48 h dwell, then `cut.sh prod s4`.
      - After S3, a daily `sync_users.sh` timer goes on the VM. It's safe once the VM serves nobody, and it keeps a rollback to the VM at minutes.

      — verify:
      - the VM's `auth.log` shows no new customer sessions after draining;
      - every baseline username has logged in to the host within 24 h;
      - host session count is about baseline;
      - the first new prod SFTP connector goes ACTIVE through the host (discharged by a dev test on the same image, Harry 2026-11-04);
      - `provisioning.failed` = 0 and the DLT backlog = 0.
- [ ] 5. Shed the connector's SSH provisioning code. **One-way: this removes the rollback path** (AC 7).
      gate: two weeks after prod S4 with no rollback
            [ ] confirmed

      - Delete the SSH adapter, `SFTPUserBuilder`, the crypto keygen, the `create_sftp_user` route and handler, `UserCreationResponse` producer code that's no longer used, the `SFTP_ADMIN_*` and `SFTP_ADMIN_HOST` schema fields, the compose env, and `node-ssh`/`ssh2`.
      - Keep `SFTPUserBuilderException.ConnectorReadFailure` and `.UserCreation` (both thrown by the remaining PENDING publisher, `connector.config-handler.ts:58,473`) and the `errors.ts:89-160` branch that maps them, or move them. Drop only the `UserProvision` kind and the `isProvisionException` unwrap.

      — verify: suite green; dev deploy boots with `SFTP_ADMIN_*` still set but unused; a new dev SFTP connector provisions end to end through the host.
- [ ] 6. Decommission the VM and update docs and data (AC 7,8).
      gate: disk snapshots of the prod and dev VMs taken, kept 30 days
            [ ] confirmed

      - Delete `sftp_vm`, its instance group, `sftp_vm_admin_ip`, `startup.sh.tpl` and `keys.tf`; remove `SFTP_ADMIN_*` from `cloud-run.tf`.
      - Remove the `vm_backend` variable.
      - Re-scope the port 22 firewall to the host tag.
      - Remove the `push_config` branch and the `create_sftp_user_consumer` variable. The subscription stays.
      - Delete `sftp-login-audit.tf` and the `sftp_login_audit_stage` variable (both environments are `off` by then).
      - Rewrite `CLAUDE.md` "SFTP users & SSH keys", both skills and the codex copy, the vault docs and fuse-mcp data, pushed straight to `master` with a parity accept.

      — verify:
      - prod and dev plans list only these deletions (Cloud Run env blocks are redacted in plans, so confirm the `SFTP_ADMIN_*` removal in the deployed revision instead);
      - no bucket, IP, DNS or subscription diff;
      - Cloud Run boots;
      - a new dev SFTP connector provisions end to end;
      - `wp stale` is clean for the touched vault docs.

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-11-04 [inc 4, S4 verify] **S4 verify closed in dev on the image prod runs** (Harry: "Happy for you to test this in dev to complete S4"). Dev and prod hosts both run `sftp-host:*-40c2285dce9e`.
  - New HJF dev connector `conn_afe2a900c2c84d4b8a7e6a50d8b4ca57` (POST 17:12:00Z) went PENDING → ACTIVE in ~10 s. The host provisioned it (`qx8m`, 17:12:06Z, `keySource=generated`, `usersJson=appended`), as `FUSE_6920F20DE3`. `provisioning.succeeded` dev 1, `provisioning.failed` 0 in dev and prod.
  - Its private key, read from config-service into a temporary agent, logged in twice through the dev LB 34.142.66.200 (host key pinned against Secret Manager) on a different instance (`mdgk`), so `users.json` reached the other instances. The fingerprint matched the provisioned one. `S4-PROD-VERIFY-DEV.EDI` in `to_ilg/create_sales_order/` reached the connector at 17:13:00Z and was routed to error for "no mapping", as expected for a bare connector (same as dev S4's 2026-10-28 test).
  - Prod wiring, read-only at about 17:15Z: `create_sftp_user_prod.v1.cloud_run_sub` has no push endpoint, exactly-once on and the DLT attached; 3 open streaming pulls (one per host instance); backlog 0 on the sub and the DLT.
  - Not covered by dev: prod's own config-service write and `customer_creation` publish. The first real prod connector will show them; the provisioning monitors cover a failure.
- 2026-11-04 [inc 4, S4] **Prod S4 done: the host provisions prod SFTP users, live 10:38:29Z** (`cut.sh prod s4 --apply --pr 394 --pr 395`, log `s2-prod/prod-s4-*.log`). Harry agreed the expected plans before the run.
  - **#394** (`create_sftp_user_consumer = "host"`) merged 09:36:59Z as `7aaf3b0`. Connector run 41808929250 plan: `create_sftp_user_subscription` loses `push_config` and `enable_exactly_once_delivery` false→true (`pubsub.tf:190`, as dev's #370), and the Cloud Run image goes to `prod-7aaf3b0` (carrying Renovate #393) with the standing sidecar/env drift. Host run 41808929419: no changes. Gates approved 09:38–09:41Z. Push was off at 09:42:04Z.
  - **#395** (`sftp_host_provisioning = "live"`) merged 09:46:10Z as `c223aeb`. Host run 41809788791 plan: the instance template is replaced with the same image (`sftp-host:prod-40c2285dce9e`) and only `PROVISIONING_ENABLED=true`, `PROVISIONING_SUBSCRIPTION=…create_sftp_user_prod.v1.cloud_run_sub` and `CUSTOMER_CREATION_TOPIC=…bifrost.prod.customer_creation.v1` added. Also subscriber IAM on that subscription and publisher IAM on `customer_creation`, and the MIG version is updated (3 add, 1 change, 1 destroy). Connector run 41809788743: image `prod-c223aeb` plus drift. Gates approved 10:25–10:28Z.
  - **No-consumer window 09:42:04 → 10:38:29Z (56 min, against dev's ~2 min).** cut.sh refused #395 at 09:43:53Z on `mergeable: UNKNOWN` (GitHub recomputing after #394), and #395's dev-plan check had failed on a dev state-lock collision with #394's plan when both opened together. After a re-run, cut.sh merged it at 09:46Z. Its gates then sat about 40 min because the agent's watch loop died on a GitHub API error. Backlog and DLT were 0 at the end, so no `create_sftp_user` was held. Parked Renovate Deploy run 41801285904 (`05cfe88`, `consumer = "connector"`) was cancelled first, with Harry's go.
  - **Customers across the MIG roll (10:20–10:39Z):** 9 user/IP pairs accepted, 0 known-user failures (14 unknown-user), 0 handshake failures, 0 session errors, 4 uploads committed with 0 failed. Monitor 335786576 is No Data (log-based, no `default_zero`), not Alert.
  - **Not yet verified:** the first new prod SFTP connector going ACTIVE through the host. `provisioning.*` = 0 since live because none has been created.
- 2026-11-04 [inc 4, S4 prep] **Prod VM ready for S4.** Startup script re-run over IAP (`google_metadata_script_runner startup`, 09:05–09:10Z, rc=0). The live `sync_users.sh` now has #376's `getent` line, all 41 `users.json` usernames have fresh `authorized_keys` and 82 binds, and `/mnt/gcs_root` is mounted. The re-run reset `sshd_config` to the package default, so the `sftp-server -l INFO` logging (approved 2026-11-02) is gone from the file. It also showed why internet password brute-force reaches the VM: the script's `sed 's/^PasswordAuthentication yes/…/'` doesn't match the default's commented line, so password auth stays at its default (on). Daily `sftp-sync-users.timer` added (03:30Z, `Persistent=true`). Disable it before any rollback-S3 puts customers back on the VM. PRs #394 (`create_sftp_user_consumer = "host"`) and #395 (`sftp_host_provisioning = "live"`) opened; `cut.sh prod s4` dry run passed at 09:13Z (state: backends=[host], push on, host_prov=not-live; each PR changes only its key). Deploy run 41801285904 (Renovate #393, `05cfe88`) is parked at `terraform-prod`, and approving it after S4 would re-apply `consumer = "connector"`.
- 2026-11-04 [inc 4, S3 dwell] **Overnight, 2026-11-03 17:00Z → 2026-11-04 08:23Z on the host: clean** (`s2-prod/watch-overnight.txt`, no guard running).
  - 5,134 customer logins, all accepted, from 13 user/IP pairs, summing exactly to `login.accepted`. FUSE_BF65660F94 logged in from 34.96.62.130 (baseline 34.96.62.47), **so all 12 baseline customers have now logged in to the host.** The FUSE_C062E5C41B poller moved from 3.64.142.243 to 3.64.131.199 around 00:00Z at an unchanged ~2 a minute. The VM journal shows 0 accepted customer logins, against about 20,700 `Failed password for root` from internet brute-force on its admin IP.
  - Known-user failures (`login.failed` 1,572 − `unknown_user` 1,568) = 4, all `support` closed_before_auth from scanner IPs. 2 handshake failures, both from IPs that have never logged in. 0 upload, audit or session failures, 0 connector errors and 0 validation errors. audit-service stored 5,137 `sftp_login`. All prod SFTP Host monitors are OK.
  - **Commits vs files, 145 vs 144, explained.** GCS has 144 `to_ilg` objects since 17:00Z, matching the connector per business (EPARFUM 61, STUBBLE 59, WILDSMITH 13, ACADEMIC 11). The 145th commit, at 05:14:29Z on `sftp-host-prod-x0rl`, is `FUSE_C062E5C41B/from_ilg/sales_order_confirmations/FUSE_BOMREP_EPARFUM_20261103_2230.csv`, uploaded by C062's second RSA key `SHA256:kbTM8YB2…` from 122.161.48.10. C062's poller archived it at 05:15:06Z. The VM journal (`sftp-server -l INFO`) shows the same on 11-03: the same key, from 49.36.137.177, wrote `…20261102_2230.csv` there at 03:19:23Z, and it was read and `posix-rename`d to `.archive/` by 03:20:26Z. It's a customer workflow that isn't ingest, and the host matches the VM. **Gotcha for the watch:** `upload.committed` counts every upload, including customer writes under `from_ilg/`, so compare it with the connector's file count per `to_ilg` object, not as totals.
- 2026-11-03 [inc 4, S3 dwell] **17:00Z check, 09:46–17:00Z on the host: clean. Recommended keeping it overnight** (DM'd to Harry at 17:04Z from the rc-hjf workstation; report in `s2-prod/watch-1700.txt`).
  - 2,585 customer logins, all accepted, from 16 user/IP pairs across 11 of the 12 baseline customers. The per-pair counts sum exactly to `login.accepted` (2,585). FUSE_ABDAD7F392 (31.96.160.33 new, 80.192.54.135 baseline) and FUSE_59DC37CB09 (2.81.175.231 new; baseline 82.36.103.101) appeared after midday. FUSE_BF65660F94 (about 2 logins a week) is still unseen. The VM journal shows 0 accepted customer logins from 09:47 to 17:05Z, only internet brute-force against its admin IP.
  - Known-user failures (`login.failed` 855 − `unknown_user` 852) = 3, none new since midday: `support` closed_before_auth ×2 from scanner 193.46.255.86, and FUSE_DD2AF79592's 11:32Z one. DD2AF hasn't failed again, and it logged in successfully 3 times.
  - 14 `sftp request refused` log lines, all `simple@putty.projects.tartarus.org` (the metric says 15). The 4 handshake failures (185.140.18.4, 195.184.76.100, 195.184.76.79, 45.91.64.10) all came from IPs with 0 successful host logins in 7 days.
  - 200 uploads committed, 0 failed. That equals the connector's 199 `fuse.file.size.count` plus 1 `fuse.file.invalid_type`. 219 records emitted, with 3 validation errors (ESCENTRIC `15320 15321 ABU DHABI CSV.csv`, re-uploaded 3 times, 14:24–14:38Z; it's a content problem, and the same alert fired on 6 days in the 2 weeks before the cut) and 0 connector errors. audit-service stored 2,590 prod `sftp_login`. All prod SFTP Host monitors are OK.
  - The workstation guard ran 13:58–17:00Z with 0 signals (one poll got a Datadog 408 at 16:15Z, and the next poll covered it). Dev canary monitor 335786601 fired at 16:01Z for one `cleanup` failure (`remove …: connection lost`) at 15:45:41Z, the only failure in about 2,200 dev runs over 7 days. The dev host logged nothing for it, nothing touched the dev instance group, and the next runs passed. Prod has no canary.
  - 710 customer logins, all accepted, from 12 user/IP pairs across 9 customers (FUSE_033BE0B235, 15ADCA408F, 447A6A12D5 ×3 IPs, 84B6F5A152, 8B8F319605, C062E5C41B ×2 IPs, C232BE3BCC, DD2AF79592, E5A356978A). The per-user/IP counts sum to the `login.accepted` metric (710 against 711). The VM has had no logins since 09:47Z.
  - 41 uploads committed and 0 failed. The connector ingested 46 records with 0 validation or connector errors. audit-service stored 712 prod `sftp_login` events. The backend was HEALTHY ×3 and no prod SFTP Host monitor was non-OK.
  - The guard woke three times, none for a customer failure. `support` from 193.46.255.86 closed before auth: a daily scanner on that IP since 10-30, with about 25 scanner IPs against `support` this past week. FUSE_DD2AF79592 from its usual IP 86.98.154.68 closed before auth at 11:32Z, after a good host login at 10:24Z with its VM key fingerprint (`SHA256:n7Zd…`). 185.140.18.4 failed the handshake offering only `sk-*` host-key types, and hit the VM in the same minute.
  - **The host presents the VM's host keys.** ED25519 `4syD6…`, ECDSA `ELz2g…` and RSA `gW1am…` are identical on the NLB (34.89.6.210) and the VM (34.147.133.18) per `ssh-keyscan`, so clients pinning the VM's key see no change.
  - Still unseen on the host: FUSE_ABDAD7F392, BF65660F94 and 59DC37CB09 (2–6 logins a week on the VM).
- 2026-11-03 [inc 4, S3] **Prod S3 done: all customers on the host since 09:46:30Z.** Harry chose 100% today over holding at S2 ("100% is what I had in mind").
  - **#392** (`sftp_vm_backend = false`) was merged by `cut.sh prod s3 --apply --pr 392` as `72984d4`. Prod plans were read before the gates:
    - host run 41613083576: `sftp-host-prod` loses the VM backend and `health_checks` goes `-ssh` → `-http` (0/1/0);
    - connector run 41613083543: image tag plus standing drift.
  - **Timing:** gates approved 09:43–09:45Z; `p_s3_done` at 09:46:12Z (275 s); S3 finished in 328 s. The host is HEALTHY ×3; the VM drain ended at 09:51:18Z. The VM journal shows no accepted logins after 09:47Z.
  - **VM-only users first seen on the host, all accepted:** FUSE_C232BE3BCC (51.141.86.75, 12 logins in 8 min), FUSE_84B6F5A152 and FUSE_8B8F319605 (130.255.29.213, PuTTY/WinSCP), FUSE_15ADCA408F (20.26.12.135), and FUSE_447A6A12D5's other IP 52.21.250.44. In the 09:45–09:53Z window: 0 login failures, 0 handshake failures, 0 upload failures, 0 connector errors; audit-service stored 52 prod `sftp_login`.
  - **Not yet seen on the host:** FUSE_033BE0B235, FUSE_DD2AF79592, FUSE_ABDAD7F392, FUSE_BF65660F94, FUSE_59DC37CB09 (low-frequency pollers).
  - **Expected noise:**
    - 335786576 fired for `sftp-connector-prod-sftp-vm`, because the VM went HEALTHY → UNHEALTHY at 09:46:43Z under the new HTTP check as it was drained out.
    - Two `sftp request refused` lines of type `simple@putty.projects.tartarus.org`, a PuTTY no-reply extension that the host refuses and continues past.
  - **Guard fixes:** grouping a log aggregate by a facet a line lacks drops the line. The refused lines have no `remote`, and the handshake lines have no `error`. The guard now signals on ungrouped totals.
- 2026-11-03 [inc 3, S2] **Prod S2 done: the host serves prod beside the VM, at size 1.** Pre-flight passed at 07:45Z: no Deploy runs in flight; host 3/3 HEALTHY on `2084114` (#388, #389); VM HEALTHY; prod SFTP Host monitors OK; load 0.6.
  - **#390** (`sftp_host_backend = true`, `sftp_host_size = 1`) was merged by `cut.sh prod s2 --apply --pr 390` as `dd046fc` at 08:00:50Z. Prod plans were read before the gates:
    - host run 41600160074: backend service gains the MIG beside the VM, MIG 3 → 1 (0/2/0). The VM backend renders as remove+add only because Terraform re-renders the backend set; group, mode and failover are unchanged.
    - connector run 41600160162: image tag plus the standing drift (container-dependencies, env reorder) only.
  - **Timing:** host apply finished at 08:07:05Z; `p_s2_done` at 08:12:37Z (706 s, mostly the 300 s drain on the two removed instances); S2 finished in 759 s. Both backends HEALTHY ×1. The operator client landed on the host 10 of 10 times.
  - **Customers, 08:07–08:13Z:**
    - host: FUSE_C062E5C41B from 3.64.88.217, 12/12 accepted;
    - VM: FUSE_C062E5C41B's other IP 3.64.142.243, FUSE_C232BE3BCC (51.141.86.75), FUSE_447A6A12D5 (52.202.119.209).
    - So C062's two pollers split across the sides, and both kept working.
  - **Host clean:** 0 failed logins for known users, 0 refused requests, 0 handshake failures, 0 users.json skips, 0 audit publish failures, 0 connector lookup failures.
  - **Audit-service:** prod `fuse.audit.ingest{kind:sftp_login,outcome:stored}` went 3 (the 11-02 support test logins) → 14. **This proves host `sftp_login` events land in prod audit-service.**
  - **Noise:** 951 unknown-user attempts on the host over 08:07–08:13Z, about 60/min per instance, then tailing off. It is the same root/admin spray the VM sees, and is only counted.
  - **Hold:** monitor 335786586 (fewer than 2 healthy instances) is muted to 17:30Z because size 1 trips it by design. Harry is offline 08:20–09:00Z, so the ramp (#391, size 3) is held until 09:00Z (Harry, 08:17Z).
  - **08:28 and 08:57Z checks, clean:**
    - three customers on the host (C062 3.64.88.217, 447A 52.202.100.85, E5A3 185.132.40.199), every login accepted;
    - 16 uploads committed, 0 failed; connector ingest normal, 0 connector errors;
    - from 08:28Z on, audit-service stored exactly one prod `sftp_login` per host login (68 = 68).
  - **Ramp (#391, `sftp_host_size = 3`):**
    - merged by `cut.sh prod s2 --host-size 3 --apply --pr 391` as `5616f7e` at 08:58Z;
    - host plan: MIG `target_size` 1 → 3 only (0/1/0); connector plan: image tag plus standing drift;
    - gates approved 08:59–09:02Z, `p_s2_done` at 09:04:54Z (398 s), finished at 09:05:12Z;
    - host 3/3 HEALTHY in zones a, b and c; 335786586 unmuted and OK (`can_connect` = 3).
  - **After the ramp (09:03–09:15Z):** no customer changed side. The host has the same three users; the VM has C062 3.64.142.243, C232, DD2A. 0 known-user failures, refused requests, handshake failures or upload failures.
- 2026-11-02 [inc 3 breakglass] **Fast eject drilled on scratch:** `cut.sh` at `2084114`, `sftp-host-rehearsal-*` in bifrost-dev-global1, `CUT_HOST_FULL_SIZE=1`. Order: S1, S2, `rollback-s2 --fast`, rollback-S1, all exit 0, 20:03–20:10Z.
  - **S1:** 102.0 s, blip 18.0 s.
  - **S2:** 126.2 s. The host went HEALTHY 54 s after the resize, and both backends were HEALTHY.
  - **`rollback-s2 --fast`:** 76.8 s in total. The eject phase took 36.0 s, of which `remove-backend` was 31.4 s. The 0.5 s probe saw **no outage** (77 up, 0 down). New connections went to the VM, and sessions already on the host may drain for up to 300 s.
  - **Rollback-S1:** 103.0 s, blip 31.5 s. It ended clean: no forwarding rule, no backends, `SFTP_ADMIN_HOST` unset, VM banner on the static IP.
  - **Not covered:**
    - The probe client's affinity put it on the VM during S2, so a live host session being ejected wasn't watched.
    - Scratch Terraform holds only the forwarding rule, so the Terraform reconcile after the eject wasn't exercised. In prod that needs the revert tfvars PR, passed as `--pr`.
  - **First attempt failed** at 19:58Z: S2 timed out at 60 min. The scratch MIG had no autohealing policy, so `cut.sh`'s host-healthy check (which needs MIG instance health) could never pass. That was a fault in the scratch build only; the prod MIG has `sftp-host-prod-autoheal`. Fixed in `build-2.sh`.
  - **Cleanup:** scratch is clean. The health check survived the first cleanup because the MIG still referenced it; it was deleted by hand and `cleanup.sh` reordered. Real dev was untouched (`sftp-host-dev` 3, stable).
- 2026-11-02 [inc 3, pre-S2 deploys] **Prod host rolled onto the S2 image with login audit on; prod monitors published.**
  - **Merged:** #387 fast eject (`a700e37`), #388 host logging of handshake mismatches and refused requests (`cc3536e`), #389 `sftp_host_login_audit = true` in prod tfvars (`2084114`). Each went through review-panel and a #bifrost-forge post.
  - **Host run 41491974634** (after a state-lock 412 and a re-run): template replace from `prod-8c544588d615` to `prod-40c2285dce9e`, adding `AUDIT_ENABLED`, `AUDIT_TOPIC=…audit.prod.fuse.v1`, `CONFIG_SERVICE_URL` and the config-key secret ref. The MIG updated in place and two grants were added: 3 add, 1 change, 1 destroy. Approved and applied. Superseded runs 41491942728 and 41491959677 were cancelled. Connector run 41491974486 (image tag only) was applied.
  - **After:** `sftp-host-prod` is 3/3 HEALTHY on `sftp-host-prod-20261102173829029200000001` and stable. The host logged only `sftp host listening` ×3, with no warnings or errors.
  - **observability#81** merged (`de39801`). Apply run 41504609330 ran 0 add, 10 change, 0 destroy (`draft_status` only). All 10 prod SFTP Host monitors are OK. 335786576 (backend unhealthy) shows No Data, and has no no-data alerting.
  - **Audit path:** at 18:51:45Z one throwaway-key `support` login to the test address 34.13.39.94 logged `sftp login failed` auth_failed. Since the roll, `audit.publish_failed`, `audit.connector_lookup_failed` and `config_api.unavailable` have no points, so the master key reads. `sftp_login.unknown_user` is 7 (scanners). No success metric exists and audit-service doesn't log per event, so arrival there isn't seen directly.
- 2026-11-02 [inc 3 bad-key gate, injection half] **Both dev config-API monitors fired on an isolated dev host.** The host reads `CONFIG_SERVICE_API_KEY_SECRET_REF` (core-infra's shared key, `versions/latest`) once at boot. Injecting into the shared secret would have broken every dev reader, so the test used a standalone instance instead: `sftp-host-dev-badkey-test`, built from the live dev template's user-data with the key ref pointed at a scratch secret and the three `PROVISIONING_*` env removed. It sat outside the MIG and load balancer, and was reached over IAP as the dev canary user.
  - **Wrong key** (junk value): 3 canary logins at 16:46:01–03Z all succeeded (login audit fails open). The host logged `connector lookup for login audit failed … config-service answered 401` ×3. `Login audit connector lookups failing — dev` (335786599) went to Alert at about 16:47:40Z.
  - **Unreadable key** (scratch version disabled, instance reset at 16:48Z): the host logged `config API unavailable; retrying … FailedPrecondition` from 16:48:47Z with backoff. `Config API unavailable — dev` (335786577) went to Alert by 16:51Z.
  - **Restore:** the instance and the scratch secret (with its IAM grant) were deleted at 16:51Z. The real dev MIG never changed: same template `…20261102102129255700000001`, 3/3 HEALTHY. EPARFUM made 88 logins from 16:30 to 16:52Z (4/min). The real host logged no warn or error lines, and the canary was green on the host every 5 minutes. Both monitors were back to OK at 17:08Z.
  - The "Config API unavailable" monitor counts unreadable-key failures only. A wrong key shows only as connector lookups failing. The runbook text in the monitors already says this.
  - Prod copies: observability#81 flips the 10 prod SFTP Host monitors from draft to published. CI plan 0 add / 10 change / 0 destroy, `draft_status` only. Over 4 days every prod host failure metric was 0, and the host logged 1 `auth_failed` (`support`), under the threshold.
- 2026-11-02 [inc 3 users.json gate] **Prod `users.json` lint and key-set diff.** Lint: the current object was run through `apps/host/internal/users.Parse` at origin/master (a throwaway `cmd`, not committed). It read 41 users and 45 keys, skipped none, found no key options and no missing `raw_username`. `FUSE_15ADCA408F` carries the same key twice, which is harmless. Diff: SHA256 fingerprints from users.json against every FUSE_/support account's `.ssh/authorized_keys` and `authorized_keys2` on the VM (read over IAP, fingerprints only). **0 keys would work only on the host. 5 keys would work only on the VM**, one each for `FUSE_326A8414DC`, `3421818D70`, `4364EEE15A`, `946706C3CF` and `F14C59F5F8`. None of those 5 appears in any of the 35 users.json versions since 2025-09-30. `lastlog` says "Never logged in" for each, retained auth.log (33 days) has no line for them, their newest file is from 2025-06-06, and no folders are mounted. They're accepted as dormant legacy accounts that the host will refuse. sshd has no `Match`, `ForceCommand`, `ChrootDirectory` or `AuthorizedKeysCommand`.
- 2026-11-02 [inc 3 baseline gate, session type] **The prod VM now logs every SFTP session**, with Harry's go. At 16:44:58Z `Subsystem sftp /usr/lib/openssh/sftp-server` gained `-l INFO`: backup `/etc/ssh/sshd_config.bak-20261102-s2log`, `sshd -t` ok, `systemctl reload ssh` (no session dropped). From 16:45Z: 4 accepted FUSE_ logins and 4 `session opened for local user` lines. Those lines are tagged `sftp-server`, not the `ssh` unit, so read them with a plain `journalctl` and no `-u ssh`. Any accepted login without a matching line is shell, exec or scp. **The startup script resets `sshd_config` on boot**, so a reboot or a startup-script re-run drops this. Re-apply after one. Before that change, the week showed 0 `subsystem request` lines across about 34,600 logins (sshd only logs those at VERBOSE).
- 2026-11-02 [inc 2, AC 2] **S1 applied in prod.** `cut.sh prod s1 --apply --pr 386` from origin/master `707ee92`, 15:50:53–15:59:05Z, exit 0 (492.6 s). Log: session scratchpad `s1-prod-apply/`.
  - **Swap and blip:** the VM's access config moved to `sftp-connector-prod-sftp-vm-admin-ip` 34.147.133.18 (11.4 s). `cut.sh` created `sftp-host-prod` on 34.89.6.210 (20.3 s). The 0.5 s probe saw one outage of **18.0 s**, matching the scratch rehearsal.
  - **Plans:** #386 merged as `c26e0e3`. The host run 41475824722 plan was 1 import, 0 add, 0 change, 0 destroy (`cut.sh`'s `s1_deploy_plan_check` passed). The connector run 41475824916 plan was 0/1/0: the image tag, the standing `container-dependencies` and sidecar env drift, plus one env block (`SFTP_ADMIN_HOST`). The commit range was only #386's two tfvars lines. Both `terraform-prod` gates (2 each) were approved by the agent. Both runs succeeded.
  - **After:** DNS still 34.89.6.210 (local and 8.8.8.8). Keyscan on 34.89.6.210 is the VM's three keys, and the banner is `OpenSSH_9.2p1 Debian-2+deb12u10`. The `sftp-connector-prod-sftp-vm` backend is HEALTHY, `fr_in_tf=true`, and Cloud Run revision 00117 has `SFTP_ADMIN_HOST=34.147.133.18`.
  - **Logins on the VM (sshd journal over IAP):** the always-on pollers 3.64.142.243 ×2/min, 3.64.88.217 ×2/min and 51.141.86.75 ×1/min log in at the same rate before and after. New partners 23.20.107.80, 80.192.54.135 and 52.202.119.209 logged in after 15:56Z. The source IPs are real client IPs, so the passthrough LB preserves them.
  - **Connector:** no error lines 15:50–15:59Z. The only warnings were 2 LISAUK "Records failed CSV validation" / "Record dropped" at 15:52:01Z on the old revision 00116 (customer data; 4 each in 7 days).
  - Still owed for inc 2's verify: 48 h of baseline usernames on the VM, ingest rates in band, and a new connector provisioning through `SFTP_ADMIN_HOST` if one is created.
- 2026-11-02 [inc 2 rollback-S1 gate] **S1 and rollback-S1 re-rehearsed on scratch** (`sftp-host-rehearsal-*` in bifrost-dev-global1, `cut.sh` at origin/master `1ebd880`), two cycles, with no refusals or resumes:
  - Cycle 1, load average ~17: S1 116.3 s total, blip 18.0 s. Rollback-S1 184.6 s total, blip **63.6 s**.
  - Cycle 2, load average ~4–6: S1 107.4 s, blip 18.0 s. Rollback-S1 119.5 s, blip **31.5 s**, the same as 2026-10-22.
  - **Rollback-S1's blip grows with gcloud latency.** It runs from the forwarding-rule delete to the access-config add, and in between the script makes five gcloud reads in a row: 27.4 s under load against about 5 s idle. Run the prod rollback from an unloaded machine. Trimming those re-reads is a possible `cut.sh` follow-up.
  - Both rollbacks ended in the right state: the VM back on the static IP, no forwarding rule and none in TF state, no backends, `SFTP_ADMIN_HOST` unset, and the same banner and host keys. Blip accuracy is ±4.5 s (probe timeout).
  - Every scratch resource was deleted (09:31:14Z), and real dev was untouched. Logs are in the session scratchpad under `rehearsal3/logs/`.
- 2026-10-29 [inc 1, AC 1] **Prod host live on its test address.** #379 merged as `b9d344b`. Host Deploy run 40948665872 applied prod at 20:29:46Z: 17 added, 0 changed, 0 destroyed, matching the agreed plan.
  - **Instances:** `sftp-host-prod-{hx67,9dxm,9fh0}` are RUNNING and HEALTHY, and test backend `sftp-host-prod-test` is 3/3 HEALTHY. The test address `34.13.39.94` is what `sftp-next.integrations.ilg.software` resolves to. The live IP 34.89.6.210 still goes straight to the VM.
  - **Host keys:** `ssh-keyscan` of the test address matches the VM's three fingerprints exactly.
  - **`ssh-audit`, host vs VM:** the VM offers some algorithms the host doesn't: `group18-sha512`, `sntrup761x25519` (both names), `hmac-sha1-etm` and `umac-*`. That's the same unimplemented set as dev in Plan A. The host adds `mlkem768x25519-sha256`. Host-key and cipher lists match.
  - **`support`:** a throwaway key gets `Permission denied (publickey)`, and the host logged `sftp login failed`, so `support` is a known user. **A real `support` login was not run:** the agent has no copy of its private key.
  - **Datadog:** `service:sftp_host` logs from all three instances carry `env:prod`. `network.http.can_connect{environment:prod}` = 3, and `fuse.sftp_host.login.failed{environment:prod}` reports.
  - **Prod bucket:** nothing was written by the host. Folder reconcile runs only with provisioning or `DIRECTORY_RECONCILE_ENABLED`, and both are off. Prod logs carry no "folder reconcile done", and `.provisioning-claims/` doesn't exist. Only "sftp host listening" ×3 and the one failed login appear.
  - **Connector run 40948665870,** from the same merge, carries #345 (FUSE-1302 `stock_sync`, Schuster). Its prod plan is image plus 1 subscription added. It's parked and not approved; that's Schuster's to release.
- 2026-10-29 [inc 1 dev soak gate, (b) and (c)] observability#80 (applied 15:46Z) moved the dev canary monitors onto `gcp.logging.user.sftp_canary_runs` by outcome. Monitor 335786602 went from Alert to OK. sftp-connector#380 (dev applied 15:48Z, prod a no-op) made `sftp_host_backend_unhealthy` count only HEALTHY→UNHEALTHY transitions. A planned dev roll followed (`rolling-action replace sftp-host-dev`, 15:48:57–16:01:29Z, surge 3, 0 unavailable): 12 UNHEALTHY health-check entries, all from booting instances, and 0 HEALTHY→UNHEALTHY transitions, so 335786592 stayed quiet. EPARFUM made 4 host logins in every minute from 15:45 to 16:01. The canary ran green on the host, the host logged no warn or error lines, and the `create_sftp_user` DLT is at 0.
- 2026-10-29 [inc 1 host-key gate] The prod VM has exactly three host keys under `/etc/ssh` (`ssh_host_{rsa,ecdsa,ed25519}_key`). Each went over IAP (`sftpuser`, host key pinned) with `sudo cat … | gcloud secrets versions add --data-file=-`, so nothing was written to disk. All three are now `sftp-host-prod-ssh-host-*-key` v1, enabled. The fingerprint derived from each stored secret equals both the IAP-pinned baseline and `ssh-keyscan 34.89.6.210`: RSA `gW1amKYt…tRRI`, ECDSA `ELz2g8L3…We74`, Ed25519 `4syD6THT…KMlM`. The `users.json` history re-scan covers all 35 prod versions (newest 2026-10-27) and finds 41 distinct usernames. None falls outside `^[A-Za-z0-9_.-]+$`, none is a system user, and none is non-`FUSE_` except `support`. Prod plan for #379, run locally with `-lock=false`: 17 to add, 0 to change, 0 to destroy.
- 2026-10-29 [inc 2 gate, connector carries no foreign changes] Prod sftp-connector went from `8caeb753c` to `427a2392f` in run 40707094751. The apply finished at 15:06:05Z: 0 added, 2 changed, 0 destroyed. Revision `sftp-connector-prod-cr-00113-vm5` serves 100%. Smoke check, read-only, through 15:07Z: the revision logged "Dependency connected" ×2, then processed a confirmation, create acks and a file event. It logged no warn or error lines. The previous hour also had none.
- 2026-10-29 [inc 3 baseline gate, read-only] The prod VM's existing logs were read over IAP (`sftpuser`, host key pinned through the tunnel):
  - Host keys: ED25519 `SHA256:4syD6THTnAQNE7qP9NFu8r+Qk/9WTRjCx6f8rN2KMlM`, ECDSA `SHA256:ELz2g8L3VCSApr7ZC/Gzp8HVXQ8haj55iUZR/AUWe74`, RSA `SHA256:gW1amKYtof/IM2TI8almJrQ3PY7sx62rXXhhTyqtRRI`. The IAP-seen ED25519 equals the public IP's keyscan.
  - `auth.log` keeps 4 weekly rotations (`rotate 4`, `weekly`). The oldest line is 2026-09-27, so 33 days are on disk now. The next rotation (about 2026-11-01) drops 09-27 to 10-04. The sshd journal only reaches back to 2026-10-25 (1 GB cap, mostly brute-force noise).
  - **Username set, 2026-09-27 to 2026-10-29:** 16 `FUSE_` accounts logged in, all by publickey. Accepted logins: C062E5C41B 192,368; C232BE3BCC 45,660; 447A6A12D5 9,064; E5A356978A 8,320; 033BE0B235 5,295; DD2AF79592 534; 84B6F5A152 417; 1A6CEE3E09 109; 59DC37CB09 57; BF65660F94 39; 8B8F319605 30; A16665E851 29; 15ADCA408F 8; ABDAD7F392 7; BA985BFEE1 4; 16781BDBCD 2. Plus `hjf` 20 and `sftpuser` 11. 45 `FUSE_` accounts exist.
  - **Shell, exec and scp can't be read from these logs.** sshd runs at `LogLevel INFO`, which doesn't log the session type ("Starting session" is VERBOSE). Customers have `/bin/bash`, and there is no `ForceCommand` or chroot, so the VM does allow them.
  - **Client KEX and host-key algorithms aren't logged at INFO either.** Inc 1's check that the host offers every algorithm the VM offers covers this half instead.
- 2026-10-21 [host-key gate, users.json half] Every version of `users.json` was read and scanned:
  - dev: 154 versions from 2025-09-30 to 2026-10-21, 107 distinct usernames; prod: 33 versions from 2025-09-30 to 2026-10-08, 39 distinct usernames;
  - no usernames outside `^[A-Za-z0-9_.-]+$`, no system users (`root`, `sftpuser` and others), no shell metacharacters, no keys with `authorized_keys` options;
  - neither bucket has a lifecycle rule, so the history is complete back past #140, and gcsfuse can't delete old versions.
  - No sign the root path was ever used. The host keys themselves are still to be lifted.
- <YYYY-MM-DD> [inc <n>] <what was run, against what, and the observable result>

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- [inc 1] A real `support` login seeing `to_ilg from_ilg` on the prod host. It needs `support`'s private key, which the agent can't reach. A wrong key is refused, which shows the user is loaded.
- <what remains unproven, and what would prove it>

## Rollout & rollback
<!-- Added on demand. Written at plan time; amend in place as it changes.
     `Shared state touched:` is the single home for the five classes git does not own — a dev
     deploy, a prod config write, a Datadog monitor, a CI var or secret, cross-repo IaC. Reverting
     the branch undoes none of them, so if they are not written here they are not written down. -->
- **Order:** 1 → 2 (S1) → dwell → 3 (S2) → dwell → 4 (S3, dwell, S4) → rollback window → 5 → 6. Code goes before IaC, because `SFTP_ADMIN_*` has to stop being required by the app-config schema before the env vars disappear.
- **Flags/config, all in `prod.tfvars`, merged on master and approved through `terraform-prod`:**
  - host `host_enabled`: `true` (inc 1);
  - host `vm_backend`: `true`, `serve_static_ip`: `true`, and connector `SFTP_ADMIN_HOST` set (S1);
  - host `host_backend`: `true` (S2);
  - host `vm_backend`: `false` (S3);
  - connector `create_sftp_user_consumer`: `host`, then host `PROVISIONING_ENABLED`: `true` (S4).
- **One-way doors:**
  - inc 5 removes the connector-side consumer, so rollback to the VM is gone;
  - inc 6 deletes the VM disk; the Secret Manager host keys are the live copy, and the 30-day snapshot is insurance;
  - a host-generated private key is delivered once through `customer_creation`, unchanged from today's contract.
- **Rollback**, all with `cut.sh prod rollback-sN` as drilled in dev:
  - inc 1: `host_enabled=false`;
  - S1: forwarding rule deleted, access config swapped back to the static IP;
  - S2: `host_backend=false`, no outage;
  - S3: `vm_backend=true`, no outage;
  - S4: provisioning off and consumer back to `connector`, then `sync_users.sh` on the VM if the host provisioned anyone, plus a `users.json` three-field lint;
  - incs 5–6: forward-only.
- **Shared state touched:**
  - prod forwarding rules, backend services, VM access config and subscription mode;
  - prod Secret Manager versions;
  - a VM systemd timer (after S3);
  - VM disk snapshots;
  - fuse-mcp data on `master`;
  - skill files;
  - vault docs.
- **Proof in prod:**
  - every baseline username has a session within 24 h of each step, from `auth.log` while on the VM and from `sftp_login` rows or host logs once on the host;
  - Datadog ingest rates on `service:sftp_connector` match the pre-cut week;
  - after S3, MIG health shows 3 healthy instances across 3 zones.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-11-04** — Inc 5 scope corrected (review of [[move-the-connector-onto-the-shared-remote-config]]): `SFTPUserBuilderException.UserCreation` is thrown by the PENDING publisher that stays (`connector.config-handler.ts:473`), so it survives inc 5 with `ConnectorReadFailure`.

- **2026-11-04** — S4 verify by dev test (Harry, 2026-11-04): "the first new prod SFTP connector goes ACTIVE through the host" is discharged by a new dev connector on the same host image plus a read-only check of the prod subscription wiring, instead of waiting for a real prod connector or writing a test connector to prod config-service.

- **2026-11-03** — S3 dwell guard: login failures for `support` closed_before_auth, and handshake failures from IPs with no successful login in 7 days (VM baseline or host), are treated as scanner noise and don't trigger rollback. That's the run sheet's 'from a customer IP'.

- **2026-11-03** — S2 ramp held at size 1 from 08:13Z to 09:00Z while Harry is away from the laptop (no watcher, no breakglass from this session). Size 1 is stable: if it fails, the health check moves its customers to the VM. Ramp resumes 09:00Z (Harry, 2026-11-03).

- **2026-11-02** — S2 as a one-day trial on 2026-11-03 (Harry, 2026-11-02: 'customers are slow and very forgiving'). S2 at size 1 at 08:00Z, ramp to 3 at about 08:30Z, hold all day, then at 17:00Z keep the split overnight by default or eject. The breakglass is `rollback-s2 --fast` (#387). The split stops at S2: rollback-S3 is the Terraform path only, because S3 moves the health check to HTTP, which the VM can't pass. Dropped: the 4-week auth.log baseline gate (replaced by #388's host logging and watching at S2), the 48 h S1→S2 dwell and the 1-week S2 ramp. Prod login audit is on from S2 (#389).

- **2026-11-02** — Config-key gate waived (Harry, 2026-11-02): the prod host holds core-infra's shared config-service master key from S2. Login audit uses it for connectorId; provisioning uses it at S4. provisioning.tf already wires it when login_audit is on, so there's no IaC change. Accepted risk: a compromised host could read and write all config. The scoped key is parked for waypoint-ideate.

- **2026-11-02** — No scoped config-service key in this plan (Harry, 2026-11-02): it's outside the plan's scope. Park it for a later waypoint-ideate session. Scoping notes: a second key in config-service's auth middleware, allowed only GET /connectors/?userName&type=sftp and GET /connectors/{id} for SFTP connectors; a core-infra secret; the host IaC points at it; about 3 PRs and 200 lines. Alternative: connectorId in users.json (option B's first step).

- **2026-11-02** — S2 gating (Harry, 2026-11-02): pragmatic, with dev evidence as part of the basis. No prod test-connector canary before S2, because it repeats what dev proved. Approved: the cheap read-only gates, a fast host-eject lever in cut.sh (drilled out of hours), and sftp-server session logging on the VM for a week. Login audit stays in S2 (AC 5 unchanged), so a config-service key for the host is needed before S2, not at S4.

- **2026-11-02 (Harry)** — Parked prod runs cleared (Harry's call, 2026-11-02): shipped the newest connector run 40948665870 (b9d344b, incl. Schuster's #345 FUSE-1302 and its prod stock_sync subscription), applied 09:15Z, revision 00114 clean; cancelled Matt's 39944835679, Renovate's 40662457459 and Schuster's 40905100575 (all ancestors). Also cancelled our #377 host run 40707431426, whose tfvars had sftp_host_enabled=false and would have destroyed the prod host. Matt and Schuster told. S1 quiet window from the prod sshd journal (10-29..11-02): 18:00-03:00Z only the 4-5 constant pollers are active (~265 logins/h); S1 at 18:00Z on a weekday.

- **2026-10-29 (Harry)** — Prod sftp-connector deployed at master 427a2392f (run 40707094751, applied 15:06Z), carrying the @gfs-bifrost ^2.4.0 bump (#366) and Matt's FUSE-1324 Redis reconnect (#344). Dev has run #344 since about 10-23 with no issue, so the same reasoning applies to prod. Prod plan: image + standing sidecar drift; prod VM ssh-keys drops hjf; startup-script text gains #376's getent fix (no re-run). This clears inc 2's 'connector carries foreign changes' concern; Matt's parked run 39944835679 and Renovate's 40662457459 are now older than prod (rollback hazard), Matt asked to cancel his.

- **2026-10-29 (Harry)** — Scoped config-service key gate moved from inc 1 to inc 4 (before prod S4). Checked on origin/master: the host requires CONFIG_SERVICE_* only when provisioning is enabled (apps/host/internal/config/config.go:132); login audit runs without it and omits connectorId. So the prod host runs S1-S3 holding no config-service key, and the post-migration ownership revisit can still make this gate moot before S4.

- **2026-10-29 (Harry)** — Dev soak criterion (a) shortened from 72 h to end of day 2026-10-29 (17:30Z): the host ran clean overnight. Check at 10:21Z: no host warn/error since the 14:50Z roll, canary 235/235 green on the host, both create_sftp_user backlogs 0. A rollback or defect fix resets it; the planned roll for (c) does not.

- **2026-10-28 (Harry)** — The 2-week dev soak timer (Plan C inc 1 gate) is replaced by exit criteria. Dev has five SFTP clients (EPARFUM, the HJF canary, MANUCURIST, nuzest, INDU since S3), so time past a few days adds no new evidence; prod S2's dwell on real traffic is the real soak. Criteria: 72 h on the host since its last dev change with no host warn/error, canary green, no provisioning failures; the canary monitor reading the logged outcome; the unhealthy-backend monitor quiet through one planned roll. Prod dwells are unchanged.
- **2026-10-28** — Scoped config-service key gate moved here from Plan B inc 4 (inc 1 gate). See Plan B Decisions for the reasoning and the post-migration revisit of where SFTP user truth lives.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
(none yet. The candidates surfaced in planning are carried by Plans A and B.)

