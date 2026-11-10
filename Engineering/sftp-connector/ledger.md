---
tags: [waypoint, ledger]
title: sftp-connector — work ledger
---
# sftp-connector — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-11-10 — FUSE-1351

Create the pick, pack, stock adjustment and returns confirmation folders for every SFTP user

Added from_ilg/pick_confirmation_confirmations, pack_confirmation_confirmations, stock_adjustment_confirmations and return_goods_authorization_confirmations to apps/host/internal/directories/directories.json, so the host's create-only reconcile makes them up front for every user (EDICOM can't connect to a folder that doesn't exist). stock_sync is deliberately left out until its name is confirmed (FUSE-1302). Shipped by /ship, to prod ahead of QA. Dev: 388 created across 3 replicas (97 non-CT users x 4). Prod: image prod-9f782e1cb1bf live on 3 healthy hosts, reconcile created 164 (41 users x 4), no errors. FUSE-1351 stays open: prod has no CT user yet, stock snapshot folder name unconfirmed. The five CT dev users were given these folders, plus a tentative stock_sync, by hand beforehand.

PR: gfs-bifrost/sftp-connector#408

## 2026-11-06 — Stop counting redelivery deferrals and customer rejections as request failures

Stop counting redelivery deferrals and customer rejections as request failures

request.failure counted every errorHandler path, so the overview dashboard's request success rate showed ~92% since 06:00 on 2026-11-06 with no fault: 13 of 16 failures were deliberate routing deferrals, 3 were customer input/config. Deferrals now emit file_routing.deferred{trigger}, customer-input errors emit request.rejected, /health no longer counts towards fuse.request. Dashboard widget (Datadog UI) still to be changed to (request - failure) / request after deploy.

PR: gfs-bifrost/sftp-connector#405

## 2026-11-05 — Run sftp-connector on the golden runtime image

Run sftp-connector on the golden runtime image

Moved the connector Cloud Run app onto ilg-platform's node24-runtime:0.1-affogato golden image and dropped its Datadog serverless-init sidecar. The agent now runs in-container, and DD_* moved onto the app container with the sidecar's values. The SFTP host VM is unchanged. Verified on dev: one container and no volumes, logs tagged dd.datadog_init_version, a real DAZZA SFTP master_data ingest, and a goods-out confirmation egress. ssh2's native binding loads in the image, and SIGTERM drains under datadog-init.

PR: gfs-bifrost/sftp-connector#397
## 2026-11-06 — Read mapping rules through @gfs-bifrost/remote-config

Read mapping rules through @gfs-bifrost/remote-config

Inc 3b of the remote-config plan: ingest, confirmation, stock-sync and stock-adjustment mapping reads go through the package's CONNECTOR_MAPPING handler; mapping revisions are applied live as an eviction before the ack; MappingRulesConfigHandler and getUserMappingRulesByUseCase deleted. Dev-verified (live mapping edit on DAZZA ingest; GADG pick/RGA/stock-adjustment egress; sweep 73/73, 201/201).

PR: gfs-bifrost/sftp-connector#404

## 2026-11-06 — Read DDP rules and warehouse routing through remote-config

Read DDP rules and warehouse routing through remote-config

Plan inc 2: a fragment adapter feeds the sales-order rule managers from the package; read failures degrade to [] uncached with status-only logs; DDP/routing revision items apply live first and a failed apply nacks. Old DDP/routing config handlers deleted. Stacked on #401.

PR: gfs-bifrost/sftp-connector#402

## 2026-11-06 — Move sftp-connector onto remote-config 2.6.0 with its own connector schema

Move sftp-connector onto remote-config 2.6.0 with its own connector schema

Behaviour-neutral first half of plan inc 3: remote-config 2.6.0, memTtl 30 s, x-request-id per request, and sftp's lenient connector schema (union with the package schema for non-SFTP connectors) on the shadow and sweep providers. The sweep now also resolves every configured mapping, because 2.6.0's mapping read is strict on duplicate dictionary names/keys and withConnectorSchema doesn't cover it. Dev sweep on 9851537: 73/73 connectors, 201/201 mappings.

PR: gfs-bifrost/sftp-connector#401

## 2026-11-05 — Describe users.json as served by the SFTP host, not the VM

Describe users.json as served by the SFTP host, not the VM

Connector notes corrected after the cutover: the host polls users.json every 20 s and re-reads on an unknown username; the VM sync script is pre-cutover and the prod VM is stopped. Also re-triggers the prod Deploy that #399's merge push didn't start.

PR: gfs-bifrost/sftp-connector#400

## 2026-11-05 — Run remote-config in shadow beside the connector's config layer (increment 1)

Run remote-config in shadow beside the connector's config layer (increment 1)

Increment 1 of move-the-connector-onto-the-shared-remote-config. Adds @gfs-bifrost/remote-config 2.5.2, dispatches every config_revision item to it after the in-repo layer (5 s bound per item, never changes the ack; remote_config.shadow_dispatch_failed on failure), and GET /debug/remote-config/sweep. Dev: sweep 73/73 resolved; connector and mapping revisions dispatched clean. Draft; prod is gated on the Cloud SQL E3 soak sign-off.

PR: gfs-bifrost/sftp-connector#399

## 2026-11-05 — Remove the connector's SSH user provisioning (cutover step 5)

Remove the connector's SSH user provisioning (cutover step 5)

Plan C step 5, built ahead of its gate and held as a draft until 2026-11-18. Deletes the create_sftp_user push route and handler, the SSH adapter, SFTPUserBuilder, key generation, and the user-creation response and sftp_user audit publishing (the host does all of these since S4), plus SFTP_ADMIN_* and two topic env vars and four dependencies. Merging removes the provisioning rollback to the VM.

PR: gfs-bifrost/sftp-connector#398

## 2026-11-04 — Move prod SFTP provisioning to the host (cut S4)

Move prod SFTP provisioning to the host (cut S4)

Plan C inc 4, S4: prod create_sftp_user consumption moves from the connector's SSH-to-VM path to the multi-zone host, which consumes the event and publishes UserCreationResponse on customer_creation. PR 1 turns the connector's push subscription off; PR 2 sets sftp_host_provisioning = live. Merged in order by cut.sh prod s4. Prep done 2026-11-04: prod VM startup script re-run (09:05Z, rc=0, getent fix live, 41 users resynced) and a daily sync_users.sh timer (03:30Z) on the VM.

PR: gfs-bifrost/sftp-connector#394
PR: gfs-bifrost/sftp-connector#395

## 2026-11-03 — Take the prod SFTP VM out of the backend service (cut S3)

Take the prod SFTP VM out of the backend service (cut S3)

Plan C S3, 2026-11-03 (Harry: 100% was the intent for today): prod tfvars sftp_vm_backend = false; health check moves to the host's HTTP /healthz. Rollback is Terraform only (~10 min). cut.sh prod s3 merges it.

PR: gfs-bifrost/sftp-connector#392

## 2026-11-03 — Ramp the prod SFTP host to 3 instances (cut S2)

Ramp the prod SFTP host to 3 instances (cut S2)

Plan C S2 ramp, 2026-11-03: prod tfvars sftp_host_size = 3 after the 08:12Z split; cut.sh prod s2 --host-size 3 merges it.

PR: gfs-bifrost/sftp-connector#391

## 2026-11-03 — Add the host to prod SFTP's backend service (cut S2)

Add the host to prod SFTP's backend service (cut S2)

Plan C S2 trial, 2026-11-03: prod tfvars sftp_host_backend = true, sftp_host_size = 1; cut.sh prod s2 merges it. A ramp PR to size 3 follows.

PR: gfs-bifrost/sftp-connector#390

## 2026-11-02 — Log refused SFTP requests and algorithm mismatches on the host

Log refused SFTP requests and algorithm mismatches on the host

Ahead of the prod trial cutover (2026-11-03), the host now logs `sftp request refused` (username and type; exec keeps only the program's base name, env isn't logged) and `ssh handshake failed` (client address, what failed, what the client offered, from `*ssh.AlgorithmNegotiationError`). Both were metric-only, so a customer who hit scp, shell or an old algorithm couldn't be named. Each distinct line is throttled to once per 10 minutes (`internal/sshserver/throttle.go`, 4,096 keys). Unknown usernames are still never logged.

PR: gfs-bifrost/sftp-connector#388

## 2026-11-02 — Add a fast host eject to cut.sh rollback-s2

Add a fast host eject to cut.sh rollback-s2

S2 emergency lever (Harry, 2026-11-02). `cut.sh rollback-s2 --fast` removes the host from the live backend service with gcloud in seconds (sessions drain 300 s), then with --pr merges the R2 tfvars PR, whose plan check_eject_plan limits to MIG size + image tag. GitHub reads come after the eject and only warn. A plain rollback-s2 now refuses after an un-reconciled fast eject (live state would read as done). New reader tf_backends. Drill on scratch is out of hours; the scratch Terraform holds only the forwarding rule, so the reconcile plan is first exercised for real in prod.

PR: gfs-bifrost/sftp-connector#387

## 2026-11-02 — Cut prod SFTP S1: static IP through the load balancer

Cut prod SFTP S1: static IP through the load balancer

Prod S1 applied 2026-11-02 15:51–15:59Z by `cut.sh prod s1 --apply --pr 386`. The VM moved to the admin IP 34.147.133.18, and `sftp-host-prod` serves 34.89.6.210 to the VM backend only. One 18.0 s blip. Host plan was an import only (s1_deploy_plan_check passed); the connector added SFTP_ADMIN_HOST. Same host keys, DNS unchanged, customer logins continuing on the VM with real client IPs. Rollback is `cut.sh prod rollback-s1`, run from an unloaded machine (its blip grows with gcloud latency). Next: 48 h dwell, then the inc 3 gates before S2.

PR: gfs-bifrost/sftp-connector#386

## 2026-11-02 — Put the prod SFTP VM behind the host backend ahead of S1

Put the prod SFTP VM behind the host backend ahead of S1

Plan C inc 2 prerequisite: prod sftp_vm_backend=true adds the VM's instance group to sftp-host-prod (TCP:22 check). No forwarding rule yet, so no customer change. Open, awaiting plan agreement.

PR: gfs-bifrost/sftp-connector#385

## 2026-11-02 — Let cut.sh run S1 in prod by checking the Deploy run's plan

Let cut.sh run S1 in prod by checking the Deploy run's plan

Plan C inc 2 prerequisite. tf-plan.yaml plans dev only, so prod S1 refused. Prod now checks the host Deploy run's terraform-plan-prod log after the merge (check_import_plan) before anyone approves the gate; the script never approves. 3 new self-test cases on a real prod Deploy log; dry-run of prod s1 reads cleanly. Open.

PR: gfs-bifrost/sftp-connector#384

## 2026-11-02 — Clear the nightly dependency audit and image scan

Clear the nightly dependency audit and image scan

Nightly DevSecOps Scans went red (run 41398319895): follow-redirects 1.16.1 (GHSA-mrwp-f3q8-3g9p, HIGH) failed both audit-ci and Trivy, and the zod GHSA-mrhx-c7xc-m3w5 allowlist entry expired. Bumped follow-redirects to 1.16.2 in the lockfile (inside axios's range), then re-evaluated and re-dated the zod entries (audit-ci + .trivyignore) and the npm-bundled undici Trivy entries to 2026-11-09. The zod root cause is pkg-node#294; once it publishes, the connector bumps zod to ^4.6.6 and drops both zod entries.

PR: gfs-bifrost/sftp-connector#382

## 2026-10-29 — Sign off SFTP host Plan B: dev cut complete

Sign off SFTP host Plan B: dev cut complete

Dev is fully on the multi-zone Go host: it serves every dev login (S3) and provisions every new SFTP user (S4), with S2/S3/S4 rollbacks drilled in dev (179/257/531 s). Signed off 2026-10-29 with deviations carried into Plan C: rollback-S1 timed on scratch only (re-rehearse before prod S1), bad config-service key fault not injected (before prod login audit), #376's inert prod VM startup-script text. Gotchas promoted to known-context (admin IP for a shared static IP, port-22 health check passes booting COS, HEALTHY->UNHEALTHY is the only real failure signal). PRs #330-#380, observability#76/#77/#80.

## 2026-10-29 — Count only healthy-to-unhealthy SFTP backend transitions

Count only healthy-to-unhealthy SFTP backend transitions

sftp_host_backend_unhealthy log metric adds previousHealthState=HEALTHY, so booting instances on a planned roll no longer fire the backend-unhealthy monitor (dev soak criterion c). Dev history since 10-25: every real transition kept, zero roll entries matched. Open, awaiting plan agreement.

PR: gfs-bifrost/sftp-connector#380

## 2026-10-29 — Run the prod SFTP host on its test address

Run the prod SFTP host on its test address

Plan C inc 1. prod.tfvars sftp_host_enabled=true; every other host flag default (no backends on the live IP, provisioning and login audit off, no config-service key). Prod plan 17 to add, 0 change, 0 destroy. Prod host keys lifted into Secret Manager v1 the same day, fingerprints matched; prod users.json history clean. Open, awaiting plan agreement and the dev soak exit criteria.

PR: gfs-bifrost/sftp-connector#379

## 2026-10-28 — Clear red image scans: go-jose 4.1.6, allowlist bundled undici

Clear red image scans: go-jose 4.1.6, allowlist bundled undici

Master's nightly secops went red at 06:09Z 2026-10-28 on new advisories. Bumps go-jose/v4 to 4.1.6 in apps/host (CVE-2026-116587) and allowlists the npm-bundled undici 6.28.0 CVEs (CVE-2026-109383, CVE-2026-87018) to 2026-11-04 in .trivyignore with notes. Unblocks #376 and #377. Merged aa918c7; dev host rolled to the new image; prod gate left parked.

PR: gfs-bifrost/sftp-connector#378

## 2026-10-28 — Keep cut.sh reading provisioning state while a template roll is mid-way

Keep cut.sh reading provisioning state while a template roll is mid-way

host_prov_state failed on an instance whose template Terraform had already deleted, stopping every S4/rollback-S4 run mid-roll. A not-found template now counts as mixed; other read failures still stop. Open.

PR: gfs-bifrost/sftp-connector#377

## 2026-10-28 — Give a user new to the SFTP VM its keys and folders on the first sync

Give a user new to the SFTP VM its keys and folders on the first sync

sync_users.sh resolved HOME_DIR via eval echo ~user before useradd, so a users.json-only user (one the host provisioned) got .ssh and bind mounts under a literal ~user dir and couldn't log in on the VM until a second sync. Found in the rollback-S4 drill. Open, awaiting plan agreement.

PR: gfs-bifrost/sftp-connector#376

## 2026-10-28 — Re-apply dev cut S4 after the rollback drill (2 of 2)

Re-apply dev cut S4 after the rollback drill (2 of 2)

provisioning=live again; host provisioned a new connector in 7 s (12:19Z).

PR: gfs-bifrost/sftp-connector#375

## 2026-10-28 — Re-apply dev cut S4 after the rollback drill (1 of 2)

Re-apply dev cut S4 after the rollback drill (1 of 2)

consumer=host again.

PR: gfs-bifrost/sftp-connector#374

## 2026-10-28 — Drill dev rollback-S4: hand user creation back to the connector (2 of 2)

Drill dev rollback-S4: hand user creation back to the connector (2 of 2)

create_sftp_user_consumer=connector. rollback-s4 531 s; backlog and DLT empty; the connector then provisioned a new user in 13 s.

PR: gfs-bifrost/sftp-connector#373

## 2026-10-28 — Drill dev rollback-S4: stop host provisioning (1 of 2)

Drill dev rollback-S4: stop host provisioning (1 of 2)

sftp_host_provisioning=off. cut.sh's VM resync then exposed a sync_users.sh bug (fixed in #376).

PR: gfs-bifrost/sftp-connector#372

## 2026-10-28 — Provision dev SFTP users from the host (dev cut S4, 2 of 2)

Provision dev SFTP users from the host (dev cut S4, 2 of 2)

sftp_host_provisioning=live: host template on the live subscription, test topic/sub removed. MIG rolled with no false-healthy instance and no missed EPARFUM login. A new HJF connector went PENDING to ACTIVE in ~10 s via the host; its key logged in through the LB and uploaded.

PR: gfs-bifrost/sftp-connector#371

## 2026-10-28 — Hand dev SFTP user creation to the host (dev cut S4, 1 of 2)

Hand dev SFTP user creation to the host (dev cut S4, 1 of 2)

create_sftp_user_consumer=host: the live create_sftp_user subscription goes from push-to-Cloud-Run to exactly-once pull. Merged by hand so PR 2's host plan could be read: its precondition refuses while push is on.

PR: gfs-bifrost/sftp-connector#370

## 2026-10-28 — Re-apply dev cut S3 after the rollback drill

Re-apply dev cut S3 after the rollback drill

Rolled S3 forward again after the drill: cut.sh dev s3, 240 s, host-only 3/3 HEALTHY on /healthz, canary on the host from 10:05Z.

PR: gfs-bifrost/sftp-connector#369

## 2026-10-28 — Drill dev rollback-S3 (VM back behind the load balancer)

Drill dev rollback-S3 (VM back behind the load balancer)

Rollback-S3 drill: sftp_vm_backend=true restores host+VM and the TCP:22 check. cut.sh dev rollback-s3: 257 s, all HEALTHY, canary back on the VM, EPARFUM uninterrupted.

PR: gfs-bifrost/sftp-connector#368

## 2026-10-28 — Serve dev SFTP from the host only (dev cut S3)

Serve dev SFTP from the host only (dev cut S3)

Dev cut S3 on Harry's go (dwell shortened from 3 days to ~20 h). sftp_vm_backend=false takes the VM out of the sftp-host-dev backend; the backend's health check moves to HTTP 8080 /healthz in the same apply. cut.sh dev s3: 269 s, no client blip, VM sshd shows no customer session after drain.

PR: gfs-bifrost/sftp-connector#367

## 2026-10-27 — Let passthrough load balancer health checks reach the SFTP host's /healthz

Let passthrough load balancer health checks reach the SFTP host's /healthz

Follow-up to #364: the new HTTP 8080 /healthz check on host-only backends timed out because the host_health firewall (iac/projects/sftp-host/compute.tf) only allowed the autohealing probe ranges; passthrough NLBs also probe from 209.85.152.0/22 and 209.85.204.0/22. Caught on the dev -test backend before S3 relied on it.

Ship: SHIP-1027-sftp-health-firewall. Merged 3a0e936. Dev apply: firewall only. The test backend went 3/3 HEALTHY on /healthz at 19:24:41Z. The prod apply was a no-op.

PR: gfs-bifrost/sftp-connector#365

## 2026-10-27 — Stop a booting SFTP host instance passing the load balancer's health check

Stop a booting SFTP host instance passing the load balancer's health check

Dev S2 ramps showed a new COS host instance passing the TCP:22 LB health check on the OS's own sshd (~20-30s, wrong host keys) before cloud-init stopped it, then refusing until the container started; EPARFUM lost a poll at 15:24. iac/projects/sftp-host/lb.tf: while the VM is a backend the ssh check stays TCP:22 but needs ~50s healthy (interval 5, healthy 10); host-only backends (sftp once sftp_vm_backend=false, and -test) use a new HTTP 8080 /healthz check. S3 now swaps the sftp backend's check in the same apply.

PR: gfs-bifrost/sftp-connector#364

## 2026-10-27 — Grow the dev SFTP host to three instances

Grow the dev SFTP host to three instances

Final S2 ramp: sftp_host_size 1 -> 3 in iac/env/dev.tfvars after the rollback-S2 drill (#361) and rejoin (#362), applied with cut.sh dev s2 --host-size 3. Dev only. Rollback: sftp_host_size = 1.

PR: gfs-bifrost/sftp-connector#363

## 2026-10-27 — Rejoin the dev SFTP host after the rollback-S2 drill

Rejoin the dev SFTP host after the rollback-S2 drill

Roll-forward half of the rollback-S2 drill: sftp_host_backend=true, sftp_host_size=1 back into iac/env/dev.tfvars (same change as #359), applied with cut.sh dev s2. Ramp to 3 follows. Dev only.

PR: gfs-bifrost/sftp-connector#362

## 2026-10-27 — Run the dev rollback-S2 drill

Run the dev rollback-S2 drill

Rollback-S2 drill: removed sftp_host_backend/sftp_host_size from iac/env/dev.tfvars so the host leaves the dev LB backend (VM serves all) and the MIG returns to its default 3. Applied with cut.sh dev rollback-s2 and timed; S2 re-run and ramped to 3 straight after. Dev only.

PR: gfs-bifrost/sftp-connector#361

## 2026-10-27 — Grow the dev SFTP host to two instances

Grow the dev SFTP host to two instances

Dev cut S2 ramp: sftp_host_size 1 -> 2 in iac/env/dev.tfvars, applied with cut.sh dev s2 --host-size 2 during business hours as a smoke test on Harry's go. Raises the host's share of client IPs and spreads it across two zones; existing client IPs should keep their side. Rollback: sftp_host_size = 1.

PR: gfs-bifrost/sftp-connector#360

## 2026-10-27 — Run dev SFTP cut S2: split traffic between the VM and the host

Run dev SFTP cut S2: split traffic between the VM and the host

tfvars sftp_host_backend=true, sftp_host_size=1 in dev, merged and applied by cut.sh dev s2 --apply. CLIENT_IP affinity; one host instance against the VM. Rollback: cut.sh dev rollback-s2 (sftp_host_backend=false|absent, sftp_host_size=3|absent). Evidence in Plan B inc 4.

PR: gfs-bifrost/sftp-connector#359

## 2026-10-25 — Narrow cut.sh's parked-runs guard to the env being cut

Narrow cut.sh's parked-runs guard to the env being cut

parked_runs now ignores a run once its terraform-apply-<env> job has completed, matching deploys_in_flight. Without this, Matt's connector run parked on prod (39944835679) would have refused dev S1 and rollback-s1 after the first tfvars merge. Prod cuts still refuse on runs parked at the prod gate.

PR: gfs-bifrost/sftp-connector#355

## 2026-10-25 — Run dev SFTP cut S1: static IP onto the load balancer

Run dev SFTP cut S1: static IP onto the load balancer

S1 of the dev cut, run by cut.sh. The VM is now the only backend behind forwarding rule sftp-host-dev on 34.142.66.200, the VM itself is on its admin address 34.147.156.89, and the connector provisions over SFTP_ADMIN_HOST. Blip 18.1 s, host keys unchanged, canary green with side=vm, and a new connector (FUSE_F6A1BE37D1) provisioned through the admin address. S2 is held until Harry is back (2026-10-27). Rollback: cut.sh dev rollback-s1 --apply --pr <revert of #358's keys>.

PR: gfs-bifrost/sftp-connector#357
PR: gfs-bifrost/sftp-connector#358

## 2026-10-25 — Clear the connector dependency audit (zod, body-parser)

Clear the connector dependency audit (zod, body-parser)

Bumped body-parser to ^1.20.9 and express to ^4.22.3, which clears GHSA-27r3-jxmh-p828. The connector parses JSON with inflate on. zod GHSA-mrhx-c7xc-m3w5 / CVE-2023-54404 is allowlisted in audit-ci.jsonc and .trivyignore until 2026-11-01, because every @gfs-bifrost package peer-pins zod 4.4.3 exactly. Follow-up: widen that peer range in pkg-node. The npm-bundled undici CVE-2026-109869 in the node:24-alpine image is added to .trivyignore.

PR: gfs-bifrost/sftp-connector#356

## 2026-10-22 — Add the SFTP cutover script, rehearsed on scratch resources (Plan B inc 3A, #352)

Add the SFTP cutover script, rehearsed on scratch resources (Plan B inc 3A, #352)

apps/host/scripts/cut.sh <env> s1|s2|s3|s4|rollback-sN: dry-run by default. --apply needs --pr N, scoped to iac/env/<env>.tfvars and the step's keys. Each step refuses unless live GCP state matches the previous step's end; failed reads stop the step. S3 needs the host healthy, rollback-S2 the VM, and S4/rollback-S4 alert on two consumers. The swap resumes, requires the target RESERVED with no users, and asserts the project. S1 swaps the VM to its admin IP, then creates the static-IP forwarding rule through the Compute API (gcloud --ports stores portRange 22-22, which forces a Terraform replace); lb.tf adopts it with an import block gated off in prod. The S1 blip on scratch is 22.5 s, against 3-4 min if a Deploy run created the rule. Rehearsed every step and rollback on sftp-host-rehearsal-* scratch: the guest agent serves the LB IP; the access-config swap is in place (no restart across 8 swaps); one instance group can back two backend services; CLIENT_IP affinity holds 12/12 reconnects. A first review blocked --apply (no resume, failed reads read as absent, missing health gates); all fixed, and a second review is pending.

PR: gfs-bifrost/sftp-connector#352

## 2026-10-22 — Ship the SFTP host's metrics and logs to Datadog, plus a dev canary (Plan B inc 3C/3B)

Ship the SFTP host's metrics and logs to Datadog, plus a dev canary (Plan B inc 3C/3B)

#348: a Datadog Agent container on each host instance (API key from Secret Manager into a root-only tmpfs env file; DogStatsD at a fixed address on the host's Docker network; container logs as service:sftp_host; /healthz check), plus SSH health-check logging and a log-based metric counting backends going UNHEALTHY. #351 fixed #348 in dev: the agent's fixed 172.30.0.2 is Docker's first dynamic address, the SFTP host container took it, and the agent never started (a create/attach/destroy loop in COS docker events). Dynamic addresses now come from 172.30.0.128/25. #350: a failed connectorId lookup increments audit.connector_lookup_failed and logs a warning. #349 (merging): a dev-only canary Cloud Run job every 5 minutes as FUSE_525C87DEB7 ("sftp canary" connector on HJF), pinned to the dev host keys, reporting side=vm|host from the banner. Monitors are in observability#76 (24, prod copies drafts until Plan C).

PR: gfs-bifrost/sftp-connector#348

## 2026-10-22 — Fix the SFTP host's connector type check, and run dev provisioning in test mode

Fix the SFTP host's connector type check, and run dev provisioning in test mode

#346 sets dev sftp_host_provisioning = test: the host consumes only the dev-only create_sftp_user host_test subscription, so real dev provisioning stays with the connector. #347: the host compared config.type to "SFTP", but config-service and @gfs-bifrost/types use "sftp", so provisioning skipped every connector (not_sftp, seen in dev on conn_176c7d97...) and the connectorId lookup's type=SFTP got a 400, leaving sftp_login events without a connectorId. Three review rounds missed it because the fakes used the host's own constant; the fakes now use config-service's real values. Also: since about 16:20 UTC, merge-async merges to master have started no workflows, so dev was deployed with host-manual-deploy.

PR: gfs-bifrost/sftp-connector#347

## 2026-10-22 — Harden host provisioning after review (Plan B inc 1, #343)

Harden host provisioning after review (Plan B inc 1, #343)

Fixes from three independent reviews:
- claim fencing: a 90 s work deadline under the 2-minute lease, and a generation check before the users.json write and before the publish
- shutdown-safe publish (WithoutCancel; claim kept and message nacked on an unknown outcome)
- re-read the connector after claiming
- background Config API key read with backoff
- takeover metric tagged held|released|unreadable
- supplied public keys must parse as one optionless authorized_keys line (the VM copies them verbatim)
- https-only Config API, no redirects
- IAM gated per mode (live subscriber only for live)
- connectorId cache capped at 4096
- a Terraform precondition refusing live while create_sftp_user still pushes to Cloud Run
AC 2 holds unless config-service lags by more than the 1-minute settle.

PR: gfs-bifrost/sftp-connector#343

## 2026-10-22 — Claim each connector before the host provisions it (Plan B inc 1, #342)

Claim each connector before the host provisions it (Plan B inc 1, #342)

Two replicas pulling duplicate create_sftp_user messages could both mint a key. Fixed with a per-connector claim: a create-only GCS object at .provisioning-claims/<escaped connectorId> holding {holder,state,expires}, with a 2-minute lease. A replica that loses re-reads the connector and acks if it's no longer PENDING, else nacks. An expired or unreadable claim is taken over with a generation precondition. On success it's kept released for a 1-minute settle, so a duplicate arriving before config-service records ACTIVE can't mint a second key; on failure it's deleted. Not reachable over SFTP and ignored by the connector's 4-segment ingest. The stack also merged master (#330-#333) in, wired internal/audit for sftp_user, and fed sftp_login's connectorId through a Config API lookup (10-minute cache).

PR: gfs-bifrost/sftp-connector#342

## 2026-10-22 — Provision SFTP users from the Go host, dormant (Plan B inc 1, draft stack)

Provision SFTP users from the Go host, dormant (Plan B inc 1, draft stack)

Five stacked draft PRs (GitHub stack #340): #335 raw users.json upsert (keeps unchanged bytes, ifGenerationMatch + 412 retry); #336 pull adapter (one in flight per replica, retries FAILED_PRECONDITION); #337 contracts (username, keys, strict decode, UserCreationResponse golden fixture byte-identical to the connector's publisher, sftp_user audit, Config API client using core-infra's existing API key); #338 the consumer; #339 wiring behind PROVISIONING_ENABLED (default off) plus Terraform tfvar sftp_host_provisioning = off|test|live (dev: test topic/sub + 4 IAM; prod plan no-op). Open: two replicas pulling duplicate create_sftp_user messages at once can both see PENDING and mint two keys (AC 2), so a per-connector claim is needed before S4. Conflicts with the inc 2 stack (#330-#333) in remote.tf core_pubsub, the cloud-init ExecStart, config.go and main.go.

PR: gfs-bifrost/sftp-connector#335

## 2026-10-22 — Audit SFTP logins from the Go host (Plan B inc 2, draft stack)

Audit SFTP logins from the Go host (Plan B inc 2, draft stack)

Four stacked draft PRs (GitHub stack #334): #330 internal/audit publisher (generated AuditMessage + sftp_login details from @gfs-bifrost/audit, pubsub v2 adapter; never errors, caller counts outcomes); #331 the SSH layer passes the credential and connection identity to the observer, and SSH 'none' is enabled only to tell known from unknown users (callback always denies, pinned by tests); #332 one sftp_login per connection with a deterministic eventId (instance id + per-process conn counter + accept time); #333 cmd/host wiring, the connectorId cache (no source until inc 1's Config API client lands), and Terraform behind new tfvar sftp_host_login_audit (dev only; prod plan no-op). Unknown usernames only bump fuse.sftp_host.sftp_login.unknown_user. Dev checks are owed after merge.

PR: gfs-bifrost/sftp-connector#330

## 2026-10-22 — Stand up the multi-zone Go SFTP host in dev (Plan A complete)

Stand up the multi-zone Go SFTP host in dev (Plan A complete)

sftp-host Plan A shipped as #317-#327 + #329: monorepo (apps/connector, apps/host), connector prep (awaited users.json write, publish rethrow, ack 60s, DLT sub, VM unmanaged group, admin IP reserved, SFTP_ADMIN_HOST seam unset in prod), the Go host (x/crypto/ssh + pkg/sftp over GCS, distroless, SFTP-only), and dev infra (3-zone COS MIG behind a passthrough NLB on temp sftp-next.integrations.freightops.dev). Prod: connector 3/2/0 and host SA+secrets only; host dormant. Dev evidence: VM host keys lifted (fingerprints match); ssh-audit parity after #329 (gaps = x/crypto-unimplemented only; ML-KEM stands in for sntrup761); replica kill kept service; client IPs preserved; provisioning e2e (FUSE_9ABEDC586D); ingest through the host via OpenSSH, psftp and WinSCP (Matt). Host accepts SETSTAT as a no-op where the VM refuses it. Next: Plan B. See [[known-context]] 'SFTP host migration (2026-10)', architecture G5/G6.

PR: gfs-bifrost/sftp-connector#329

## 2026-10-21 — Pin the SFTP host's algorithms to the VM's sshd

Pin the SFTP host's algorithms to the VM's sshd

ssh-audit from sftp-next against the dev VM showed the host offering x/crypto's SHA-1 defaults (group14-sha1, ssh-rsa host sig, hmac-sha1-96, ssh-rsa client sig) that OpenSSH 9.2 never offered. Pinned kex/cipher/MAC/pubkey lists to the VM's sshd -T minus unimplemented algos; RSA host key restricted to rsa-sha2-* in hostkeys.parse. Gotcha: x/crypto skips MAC agreement under AEAD ciphers, so MAC tests need a CTR cipher.

PR: gfs-bifrost/sftp-connector#329

## 2026-10-21 — Bump follow-redirects to 1.16.1

Bump follow-redirects to 1.16.1

CI fix off master: two new high advisories against follow-redirects 1.16.0 (GHSA-q3jh-wrc6-jgq8 and a sensitiveHeaders regex flaw), transitive via axios, were failing the dependency audit and image scan on every PR. Lockfile-only bump within ranges; audit-ci passes. Kept out of the SFTP host stack so it can merge first.

PR: gfs-bifrost/sftp-connector#328

## 2026-10-21 — Stand up the SFTP host behind a load balancer in dev

Stand up the SFTP host behind a load balancer in dev

Plan A inc 5b. Regional MIG (3x COS, a/b/c, sshd stopped, no external IP), autohealing on :8080, two passthrough backend services on one TCP:22 check with CLIENT_IP affinity: sftp-test (temp IP + sftp-next DNS) and sftp (vm_backend/host_backend/serve_static_ip switches, all off). Cloud NAT on default subnet (no PGA; reverses FUSE-953's NAT removal for this workload only). Prod dormant. Datadog deferred to Plan B. Merge only after dev host keys are in Secret Manager.

PR: gfs-bifrost/sftp-connector#327

## 2026-10-21 — Add the SFTP host's deploy workflows and Terraform shell

Add the SFTP host's deploy workflows and Terraform shell

Plan A inc 5a, stacked on #325. host-on-push/host-manual-deploy (tree-hash image tag so non-host commits never roll instances), tf-plan + secops host legs, iac/projects/sftp-host: least-privilege SA + three host-key secrets (europe-west2, prevent_destroy, versions by hand). Reads bucket from connector state. Plans: dev and prod 11 to add. Next: lift dev VM host keys into the secrets after merge.

PR: gfs-bifrost/sftp-connector#326

## 2026-10-20 — Serve SFTP over GCS from the Go host

Serve SFTP over GCS from the Go host

Plan A inc 4 part 2. sftpfs: /home/<u>/{to_ilg,from_ilg} mapped to <u>/... with path containment; staged uploads committed on clean close, discarded on TransferError (no partial objects), resume via download-into-staging, MAX_UPLOAD_MB; sequential ranged reads; rename/posix-rename/mkdir/rmdir/setstat semantics. Real image passed OpenSSH sftp/scp, paramiko, ssh2-sftp-client against fake GCS; WinSCP/FileZilla left for inc 5.

PR: gfs-bifrost/sftp-connector#325

## 2026-10-20 — Add the GCS object store for SFTP and send exit-status

Add the GCS object store for SFTP and send exit-status

Plan A inc 4 part 1, stacked on #323. Bucket adapter implements sftpfs.Store (fs.ErrNotExist / fs.ErrExist sentinels); no-overwrite copy checks the target first (fake-gcs ignores copy preconditions). SSH server sends exit-status 0 at SFTP session end: modern scp reported failure (-1) without it.

PR: gfs-bifrost/sftp-connector#324

## 2026-10-20 — Serve SSH logins from the Go SFTP host

Serve SSH logins from the Go SFTP host

Plan A inc 3 (3b part 4), stacked on #322. Host keys (files or Secret Manager), SSH server (sftp subsystem only; shell/exec/pty/forwarding refused), per-connection login outcome (logged_in only after signature; auth_failed/too_many_attempts/closed_before_auth; unknown usernames never logged), limits, /healthz 503 until users.json loaded + listening, distroless nonroot image, container scan. SFTP subsystem refused until inc 4 adds sftpfs.

PR: gfs-bifrost/sftp-connector#323

## 2026-10-20 — Declare per-user SFTP folders in the Go host

Declare per-user SFTP folders in the Go host

Plan A inc 3 (3b part 3). internal/directories/directories.json is the per-user folder list (today's 10); create-only reconcile behind a flag; GCS adapter (generation read, does-not-exist placeholder create). fake-gcs-server needs -backend memory for folder placeholders.

PR: gfs-bifrost/sftp-connector#322

## 2026-10-20 — Read users.json and authenticate SFTP logins in the Go host

Read users.json and authenticate SFTP logins in the Go host

Plan A inc 3 (3b part 2). Per-record users.json validation (bad record skipped+counted, key options fail the load, unsafe usernames refused), generation-polled cache keeping last good users, miss re-read rate-limited. Auth: public key implemented, password seam behind AUTH_PASSWORD_ENABLED with no store. A PublicKey callback success is not a login (query before signature).

PR: gfs-bifrost/sftp-connector#321

## 2026-10-20 — Scaffold the Go SFTP host in apps/host

Scaffold the Go SFTP host in apps/host

Plan A inc 3 (3b part 1), stacked on #318. Go module apps/host following wms-gateway's apps/gateway: env config, fleet-shape JSON logs, statsd metrics, host-code-quality CI (fake GCS for tests), secops Go dep audit. Binary only validates config so far.

PR: gfs-bifrost/sftp-connector#320

## 2026-10-20 — Prepare the connector for the SFTP host cutover

Prepare the connector for the SFTP host cutover

Plan A inc 2 (sftp-host-a), stacked on #317. create_sftp_user_consumer var makes push_config dynamic (host = same sub as pull + exactly-once; rehearsed in place, Pull refused ~60s after the switch). Ack deadline 20->60s (double-key hazard), DLT gets a subscription, publish failure now fails the config event, users.json write awaited. Inert cut plumbing: VM unmanaged instance group, sftp_vm_admin_ip, SFTP_ADMIN_HOST (dynamic env). prevent_destroy on bucket + static IP; access_config ignored. Dev login-audit stage back to off.

PR: gfs-bifrost/sftp-connector#318

## 2026-10-20 — Move the connector into apps/connector

Move the connector into apps/connector

First increment of the SFTP host migration (Plan A, sftp-host-a). code/, tests/, compose and the connector CLAUDE.md move under apps/connector following snap-adapter's per-app layout; workflows become connector-* with paths filters; manual deploy refuses branches behind master and notifies. iac/projects/bifrost-sftp-connector unchanged (its path is its state key). Blackbox ingest suites test zero records on master too (pre-existing, separate fix).

PR: gfs-bifrost/sftp-connector#317

## 2026-10-19 — FUSE-1238

Prove work-order carrierId survives translation end to end in dev

Dev end to end proven on 2026-10-19: a kitting DESADV on HJF (connector conn_1435…) with a temporary carrierId = OWN header default became simulator S10 HJFD4AC7656638E carrying CarrierId OWN (correlation 9172b3b8-258b-4336-ae52-764b6afcf6f5). The mapping default was removed afterwards. Real SnapFulfil does not keep it. GADG's dev work order WO-20261016-AP005 reached snap-adapter with carrierId OWN (dedupe's canonical shows it), but GADG dev Snap stored CarrierId NETCOURIER, the only value in its CARRIER lookup. Getting OWN to land is Snap-side lookup config, not Fuse code.

Plan: [[FUSE-1238-work-orders-keep-identifiers-carrierid-through-t]].

## 2026-10-19 — FUSE-1253

Sign off EDIFACT confirmation egress (E8-E11)

Plan closed. All four messages (RECADV, DESADV, OSTRPT, INVRPT) were proven live in dev on the HJF test connector: mock-send for most of them, and the Snap simulator for FGR/WOC. AC 7 is narrowed to a missing SSCC when requireSscc is set (Harry, 2026-10-19). Nothing in @gfs-bifrost/edi or sftp's EDI schemas can make a batch mandatory, so a line with no batch writes no GIN+BX instead of failing; that is EDI Support unit E16 (requireBatch). Gap: an invalid stock-adjustment INVRPT is lost. It writes no file and gets no confirmation_data_failure, and since the poller clears the outbound queue on publish (snap-adapter #291/#294), withholding made no longer triggers a re-announce. The comment at stock-adjustment.service.ts:156 still claims it does.

Plan: [[edifact-confirmation-egress-desadv-recadv-behind]].

## 2026-10-15 — Prepare the SFTP VM for login auditing

Prepare the SFTP VM for login auditing

UJ inc 1: sftp_login_audit_stage (off/prep/agent/removing) gates OS Config API, VM SA logWriter/metricWriter and the VM label + enable-osconfig metadata. Dev prep, prod off. Stage drives the agent's desired_state later, never count, so rollback can't orphan the agent. Plan: uj-sftp-login-audit-events-from-the-vm-via-ops-a.

PR: gfs-bifrost/sftp-connector#312

## 2026-10-14 — FUSE-1256

Turn FEATURE_FLAG_EDI on in prod

prod.tfvars feature_flag_edi false -> true. Prod plan 0/1/0 on sftp-connector-prod-cr only (image + the flag env + standing sidecar drift); both terraform-prod gates approved on the newest Deploy run. Live: sftp-connector-prod-cr-00109-qvm Ready, image prod-4e1593e, FEATURE_FLAG_EDI=true. Gates EDI ingest and EDIFACT egress for connectors set to edi. Not yet proven in prod: any EdiFileWritten or filetype:edi forward; Charlotte Tilbury's prod connector is still open on FUSE-1256.

PR: gfs-bifrost/sftp-connector#310

## 2026-10-13 — Report SFTP user creation to audit-service

Report SFTP user creation to audit-service

Audit Service unit UG: createCustomer publishes an sftp_user/created AuditMessage after provisioning (eventId = UUIDv5 of the Pub/Sub messageId; key fingerprint, never the private key; never blocks the ack). IaC adds PUBSUB_TOPIC__AUDIT_EVENT and a publisher grant on bifrost-pubsub's audit_fuse topic.

PR: gfs-bifrost/sftp-connector#309

## 2026-10-12 — FUSE-1255

Write returns confirmations as EDIFACT, RECADV by default

Returns had no EDIFACT message and were skipped as edi_unsupported_type. They now go out as a RECADV echoing the RMA, or an INVRPT return adjustment when the connector's returns mapping sets a constant messageType header rule. Partners differ on the message, so it is config. Dev-verified on the HJF EDIFACT connector; EDI Support unit E12.

PR: gfs-bifrost/sftp-connector#307

## 2026-10-09 — Bump transitive proxy-addr to 2.0.8 (GHSA-jqcg-44mw-7w3h)

Bump transitive proxy-addr to 2.0.8 (GHSA-jqcg-44mw-7w3h)

Lockfile-only bump of proxy-addr 2.0.7 to 2.0.8 (via express) to clear the critical advisory failing dependency_audit and image_scan on master's scheduled scans. Merged.

PR: gfs-bifrost/sftp-connector#305

## 2026-10-09 — FUSE-1238

Work orders: keep identifiers.carrierId through the inbound translator

Raised the @gfs-bifrost/types floor to ^10.12.0 (lockfile now resolves 10.12.0) so a mapping default for identifiers.carrierId survives WorkOrderTranslator validation; added a translator test. Merged and deployed to dev; prod parked at the gate.

PR: gfs-bifrost/sftp-connector#304

## 2026-10-02 — Broadcast legs reach a terminal outcome

Broadcast legs reach a terminal outcome

Two stacked PRs on E5 (#299). #300: a fan-out confirmation_made that can't be published rejects (500, unmapped ConfirmationMadeNotRecordedException) instead of acking; routed still records write_failed. #301: a fan-out reads each connector's use case first — none = benign; has it but fails a gate, or lookup fails = one failure per record with the leg's connectorId on body + envelope (source sftp); targets written independently, made then failed legs; fan-out lookup failure and invalid records name no connector. Dev-verified on GADG scoped to sftp (1 written, 2 inactive legs recorded, 4 benign; redrive routed to the leg only). Poller Clear-Down E1.

PR: gfs-bifrost/sftp-connector#300
PR: gfs-bifrost/sftp-connector#301

## 2026-10-01 — Bound confirmation_ready redelivery with a retry budget

Bound confirmation_ready redelivery with a retry budget

Poller Clear-Down E5. The seven confirmation_ready subs get retry_policy 10s-600s and a dead_letter_policy (max 10) so Pub/Sub sends deliveryAttempt; the DLT has no publisher grant. On attempt 10 any error errorHandler would 5xx (isNackedError) is recorded as one retryable redelivery_exhausted failure per record and acked; unpublishable keeps rejecting. Master (A5 #297/#298) merged in. Verified on dev: attempts 1-11 rejected, exhaustion logged at 10-11, recorded and 204 at 12 once restored (replay 594e596f). Draft, awaiting review.

PR: gfs-bifrost/sftp-connector#299

## 2026-10-01 — Close A2's gaps: config 4xx and window overwrite

Close A2's gaps: config 4xx and window overwrite

Two PRs. #298: getConnectorUseCaseMapping now returns null only on 404 and throws ConfigApiException on other non-2xx (handleAxiosError_ resolves 4xx, so a 401/403/429 body used to read as 'use case not present' — a silent drop once E1 makes no-mapping benign); routed lookup catch widened to any error (a ValidationException on the connector read was acked 204, a 5xx nacked uncapped) so it records a retryable failure; fan-out and stock adjustments skip only the failing connector (use_case_lookup_failed). #297: upsertWindowFile no longer overwrites the window when download fails after getMetadata — only 404 means new window, else CloudStorageException. Dev-verified both (unknown-business routed goods-in now recorded; GADG pick appended/deduped). In prod 2026-10-02 (sftp-connector-prod-cr 79dbd5e). Poller Clear-Down A5.

PR: gfs-bifrost/sftp-connector#298
PR: gfs-bifrost/sftp-connector#297

## 2026-10-01 — Scope the RGA confirmation subscription to SFTP and broadcasts

Scope the RGA confirmation subscription to SFTP and broadcasts

RGA sub was recordType-only (stale comment: 'poller RGA is broadcast-only'), so every REST/Shopify-routed RGA reached sftp-connector and since #290 recorded a spurious connector_unresolvable failure — 36 in dev on 2026-10-01 for GADG's REST-routed RGAs, none after the fix. Added local.channel_filter; also dropped the stale FGR 'inert until #223' comment. In-place replace, must precede Poller Clear-Down C2. In prod 2026-10-01 (sftp-connector-prod-cr 8d2d270, shipped with #290). Poller Clear-Down A4.

PR: gfs-bifrost/sftp-connector#296

## 2026-09-30 — FUSE-1259

Gate EDI ingest and confirmations behind one FEATURE_FLAG_EDI

FEATURE_FLAG_EDI_EGRESS was renamed FEATURE_FLAG_EDI (Terraform var feature_flag_edi) and now also gates ingest: while off, storage.service's isFileTypeAccepted treats .edi as an unaccepted type (warn 'File is not a valid type', file left in place). Before this, ingest was on everywhere via ACCEPTED_FILE_TYPES alone. Off in dev and prod (Harry: one flag for both directions), so dev EDI tests in either direction need a short-lived flag-on deploy. The metric reason edi_egress_not_enabled is unchanged. Prod revision 00103 on 75bd776.

PR: gfs-bifrost/sftp-connector#293

## 2026-09-30 — FUSE-1259

Ingest inbound DESADV as purchase orders and work orders

EDI action directories accept sets of message types: create_purchase_order takes ORDERS or DESADV, create_work_order takes DESADV. The UNH picks the normalizer; outside the set, the file fails as EdiMessageTypeMismatchError naming the accepted types; no UNH in a multi-type folder means rejection. Only lines fan out into rows (a DESADV's packages reach rules through line.package/line.sscc). Kit vs component roles and references are mapping config: a desadv_line_role dictionary keyed on line.item.codeList, if/eq rules for quantities. Takes edi ^0.8.0 (minimumReleaseAgeExclude entry needed). Dev e2e on HJF/simulator: ASN receipts, kitting S10, misroutes to error/, dedupe hold, 16-char PO 'Invalid Length', ORDERS/INSDES unchanged. HJF purchase_order/work_order mappings are left in place as the H3 harness. See [[known-context]] (EDI routing entries).

PR: gfs-bifrost/sftp-connector#292

## 2026-09-30 — FUSE-1238

Record a routed confirmation that sftp-connector cannot deliver

A routed confirmation (names a connector, not broadcast) with no eligible target (connector gone, inactive, or failing a mapping gate) was only counted and logged, and a config-service error reading the connector was acked with a 202. Both now publish a confirmation_data_failure per record to replay, carrying the gate reason. If that failure cannot be published the push is rejected with an exception that reaches the generic 500, because PubsubException and ConfirmationException are both acked. Broadcast and unrouted confirmations are unchanged. Verified in dev with the real attribute shape. Poller Clear-Down unit A2.

PR: gfs-bifrost/sftp-connector#290

## 2026-09-30 — Allowlist the node:24 npm-bundled brace-expansion and undici CVEs

Allowlist the node:24 npm-bundled brace-expansion and undici CVEs

CVE-2026-102276/102278 (brace-expansion 5.0.7) and CVE-2026-19534 (undici 6.27.0) turned the image scan red on master's nightly; all three are the npm CLI's bundled copies in the node:24 base image (app pins brace-expansion 5.0.6, has no undici; pnpm at runtime). Same triage as the existing .trivyignore entries.

PR: gfs-bifrost/sftp-connector#289

## 2026-09-30 — FUSE-1088

Drive stock adjustment CSV/JSONL from the connector's mapping when it has rules

stock-adjustment.service: csv/jsonl targets with a stock_adjustment mapping of ≥1 rule go through transformConfirmations (defaults, dictionaries, columnOrder) — e.g. EntityID ← identifiers.movementRef, BatchID ← from/to batch; no rules → fixed 15-column file byte-identical; rules fetch fails → skipped (no_mapping_rules), never a wrong-shape fallback; dynamic mapping off → fixed. Prod audit: 0/28 prod SFTP connectors have a stock_adjustment mapping. fuse-ui standard template seeds a 15-rule mapping that renders differently (ISO TrnDate, rule-order columns, stringy JSONL) — FUSE-1279. Also cleared a red image scan with #289 (node:24 npm-bundled brace-expansion/undici CVEs).

PR: gfs-bifrost/sftp-connector#288

## 2026-09-29 — FUSE-1253

Write stock adjustments as EDIFACT INVRPT behind the EDI egress flag

stock-adjustment.service: edi targets (flag + dynamic mapping + envelope + stock_adjustment mapping) → buildEdiFiles (one INVRPT per movement, grouped by identifiers.id) → createFile into stock_adjustment_confirmations. Batch → GIN BX, expiry → DTM 36 via mapping over the new types 10.8.0 from/to fields; movementRef → BGM. Invalid INVRPT withholds stock_adjustment_made (no failure topic for stock adjustments) so SNAP re-announces. types ^10.8.0. Dev-verified on HJF test connector; CSV/JSONL byte-identical.

PR: gfs-bifrost/sftp-connector#287

## 2026-09-24 — FUSE-1254

Adopt types 10.x and reject records without a customer reference

types ^9.5.0 → ^10.4.0. Factories no longer emit customerRef/workOrder/businessRgaNumber, so only the mapping can supply them and an unmapped/blank ref fails ingest validation → error/ (never a "" placeholder, which would collide in dedupe). EDI config now uses shared SFTPIngress/SFTPEdiEnvelope; a preprocess drops a malformed/blank-party ediEnvelope so ingest-by-username never fails on it. Prod audit: 26/26 SFTP sales-order connectors map OrdRef1 → order.customerRef. Conflicts with #282 in confirmation-egress.service.ts.

PR: gfs-bifrost/sftp-connector#283

## 2026-09-24 — FUSE-1265

Route confirmation records that fail validation to the retry queue

decodeConfirmations returns {valid, invalid}; egress publishes invalid records to confirmation_data_failure (validation errors per issue) once a target exists, counts fuse.confirmation.forward result:zod_dropped, and an all-invalid batch writes nothing and emits no confirmation_made. Mixed batch: valid flow unchanged. Stock adjustments validate the whole envelope (separate gap). Reuses import/translators validateRecords.

PR: gfs-bifrost/sftp-connector#282

## 2026-09-24 — FUSE-1253

Tag confirmation forward metric with fileType; pick → OSTRPT verified

fuse.confirmation.forward gains fileType (csv|jsonl|edi); delivered counted once per distinct file type per batch (no observability dashboard/monitor reads the bare metric). Pick → OSTRPT egress-service tests + dev OSTRPT file. Found: an all-dropped decode batch emits an empty confirmation_made and counts as delivered with no confirmation_data_failure — pre-existing, needs its own fix.

PR: gfs-bifrost/sftp-connector#281

## 2026-09-24 — FUSE-1253

Write EDIFACT confirmations behind FEATURE_FLAG_EDI_EGRESS

confirmation-egress.service: EdiTarget (mapping + envelope) → buildEdiFiles → createFile into from_ilg/<type>. Flag off = unchanged edi_egress_not_enabled. Flag on reasons: edi_unsupported_type / edi_envelope_missing / edi_requires_dynamic_mapping; EdiMessageInvalid rides WriteFailed → confirmation_data_failure after sibling targets write. New iac env var FEATURE_FLAG_EDI_EGRESS false both envs. Dev-verified RECADV/DESADV/pack on HJF test connector.

PR: gfs-bifrost/sftp-connector#280

## 2026-09-24 — FUSE-1221

Pass mapping dictionaries into confirmation egress translation

transformConfirmations (core/confirmation-transformer.ts) called applyTranslationRules without mapping.dictionaries; rules-engine 2.1 throws on lookup() against an unknown dictionary, so any egress mapping using lookup() failed the write. Ingress (import/translators/router.ts) already passed them. Stock adjustments use a fixed transformer, unaffected. Found building FUSE-1253 EDI assembly.

PR: gfs-bifrost/sftp-connector#279

## 2026-09-24 — FUSE-1253

Assemble EDIFACT interchanges from confirmation mappings (unwired core)

confirmations/edi/: buildEdiFiles → one UNB…UNZ per confirmation (per movement for stock adj). Dispatch: PO/FGR→RECADV, SO/pack→DESADV, pick→OSTRPT, stock adj/WOC(components)→INVRPT; returns unsupported. Rule from = message path; line rules prefixed lines./packages.; partner codes via codes.* (config, never code). ctrlRef = sha256(conn|type|docRef|queueId)[0:14]; file <MSG>_<docRef>_<ctrlRef>.edi. Gotcha: transformConfirmations drops dotted keys and never passes dictionaries (lookup() dead in CSV egress).

PR: gfs-bifrost/sftp-connector#278

## 2026-09-24 — FUSE-1253

Tolerate the edi egress file type and add create-only file writes

Groundwork for EDIFACT confirmation egress, safe in prod before anything can save edi. A local SFTP config schema accepts egressFiletype "edi" + a lenient ediEnvelope (malformed reads as absent), because the shared types 9.x schema rejects edi and the same parse gates ingest-by-username. edi connectors write no confirmation/stock-adjustment file yet (EdiEgressNotEnabled + unroutable edi_egress_not_enabled) and never fall back to CSV. New ICloudStorageService.createFile (ifGenerationMatch 0, 412 → "exists"). Must reach prod before config-service accepts edi; it's the rollback floor once any connector is edi.

PR: gfs-bifrost/sftp-connector#277

## 2026-09-23 — FUSE-1221

Pass mapping dictionaries into ingress translation

Threaded mapping dictionaries from the config-API response onto ResolvedConfig (beside columnOrder), through the mapping-rules cache schema, and from the router into every ingress translator so lookup() works for SFTP customers. rules-engine ^2.1.1 (types as a peer range, since this service is still on types 9.x). Unknown dictionary fails the file via the existing hard-failure path. Egress untouched. Verified end-to-end on dev with real CSV drops.

PR: gfs-bifrost/sftp-connector#276

## 2026-09-23 — FUSE-1231

Ingest EDIFACT files through the existing mapping pipeline

.edi uploads are now accepted for SFTP ingress. The action directory declares the EDIFACT message type (create_sales_order→INSDES, create_master_data→PRICAT, create_purchase_order→ORDERS), and @gfs-bifrost/edi normalizes each file. Each intermediary line is flattened into a lined-CSV-shaped row: header slots at their dotted path, line slots under `line.`. Flattening is required because the rules engine only reads top-level scalar keys. The rows then go through the connector's unchanged mapping, business rules and create_record_request path. Misroutes and parse errors reuse the file-level create_data_failure and error/ routing. ACCEPTED_FILE_TYPES gains edi in cloud-run.tf. Known gaps: there is no EDI_PROFILE, so CT's extra NAD roles are dropped and QTY+113 is raw-keyed; ingress decodes as UTF-8, not UNOC.

PR: gfs-bifrost/sftp-connector#275

## 2026-09-16 — FUSE-1059

Cross-entity PO/SO confirmation-ready subscriptions and made-side naming normalisation

Three-PR slice of the legacy PO/SO confirmation-topic decommission. First: swapped the legacy per-entity purchase_order_confirmation / sales_order_confirmation ready subscriptions for two cross-entity confirmation_ready subs (recordType filters: purchase_order OR goods_in_confirmation for PO, goods_out_confirmation for SO — the both-value PO filter meant this didn't need to wait on the poller rename deploying first), each still gated on sftp's channel clause (source=sftp OR broadcast=true). A swap rather than an add-only change, since the poller is the sole publisher and its cross-entity PO/SO dual-publish was already live in prod, so keeping the legacy subs would have only delivered each confirmation twice. Second: the made side now stamps goods_in_confirmation/goods_out_confirmation on confirmation_made for goods-in/out (previously purchase_order/sales_order), via a new getMadeRecordType that remaps only goods-in/out — RGA and everything else pass through unchanged. Deliberately not reusing the existing getUseCaseNameForConfirmation, which maps RGA's made recordType to the failure-side return_goods_confirmation value and would have broken RGA clear-down. Third: sftp stopped dual-publishing PO/SO made confirmations to the legacy per-entity made topics, publishing once to the cross-entity confirmation_made topic only; removed the two now-unused required env vars, their remote-state locals, and their Publisher IAM grants. One of three sibling repos retiring the same legacy publish (fapi, shopify-connector).

PR: gfs-bifrost/sftp-connector#264
PR: gfs-bifrost/sftp-connector#265
PR: gfs-bifrost/sftp-connector#269

## 2026-08-24 — FUSE-1010

Multi-parcel goods-out tracking: re-pointed 14 prod mappings, then released the dynamic-mapping flip

The code was already merged; the risk was in the *sequencing*. A merged-but-undeployed `#246` had set `feature_flag_use_dynamic_confirmation_mapping = true` in prod tfvars while 22 Deploy runs sat parked — so the next person to approve any of them would have flipped 14 customers onto mappings that still read `Carrier`/`TrackingNumber` from the shipment header, emitting the NetCourier ref instead of the carrier's tracking number.

- Survey found **15** connectors with a `goods_out_confirmation` mapping, not the 12 on record. **14** in scope; SAIRA's is a Shopify-shaped mapping on shopify-connector and is out of scope for this flag.
- All 14 re-pointed to `despatches[].carrier.*`, in `rules.lines` (not `header` — that placement comes from #255's own spec).
- **DRSAMS and DRSAMSPL have a different `columnOrder`** to the other twelve. Read each mapping immediately before its write; template-stamping would have silently reordered two customers' CSVs with nothing to catch it.
- Flip released on run 32697238099; `0 added, 1 changed, 0 destroyed`. **Two gates** on `terraform-prod` (docker-push-prod *and* terraform-apply-prod). 21 stale parked runs cancelled — each would have deployed an older sha over prod.
- Verified on real prod traffic: STUBBLE file at 15:34Z shows `Carrier=GFS_HERMES` + real Evri tracking, per-row SSCC, column order intact.

Gotchas worth keeping: the prod plan **redacts** the flag change (both env blocks are sensitive) so it proves one in-place change, never which var; and Datadog's service is `sftp_connector` with an underscore — the hyphenated query returns a confident zero.

Ledger note: this plan had no PR and no code diff, so `wp signoff` couldn't gate it — see the plan's Decisions section.
## 2026-08-13 — FUSE-871

Write Finished Good Receipts

Added a new confirmation-egress record type, finished_good_receipt — subscribes to the shared confirmation_ready topic filtered on attributes.recordType = "finished_good_receipt", decodes against CanonicalFinishedGoodReceiptSchema, and registers the shared confirmation_made topic for egress clear-down. Mirrors the existing return_goods_authorization/pick_confirmation/pack_confirmation wiring exactly — no new topics or IAM grants. Dynamic-mapping-only by design, like RGA/pick/pack: no hardcoded transformer is registered, so it writes nothing while useDynamicConfirmationMapping is off (false in prod, true in dev at the time). CSV column ordering (FUSE-954) came along for free, since confirmation-egress.service.ts already reads columnOrder generically for every dynamic-mapping confirmation type — verified live with a deliberately scrambled column order, not assumed.

PR: gfs-bifrost/sftp-connector#248

## 2026-08-03 — FUSE-1078

Stop per-record round trips on the SFTP ingest path

A file's records are now published concurrently rather than one round trip at a time, and business rules (DDP + warehouse routing) are resolved once per file instead of once per record — they key only on actionType + businessId, so a 2,896-record sales order file was doing 5,792 sequential config lookups to get two distinct results. TranslatorRouter.applyBusinessRules now takes the whole batch rather than a single record, so no per-record call site can reintroduce the problem. Fixes a real prod redelivery loop: a ~2,896-record master data file was reprocessed ~20 times over ~100 minutes (~58k records emitted for 2,896 real ones) because serial publishing pushed past the push subscription's 20s ack deadline (later raised to 600s as a stopgap in a separate commit). Companion fix: GCS file-event notifications without a contentType (gcsfuse omits it for unrecognised extensions; the connector's own confirmation-egress writes don't set one either) previously failed schema decode and were silently 204-dropped before file-type triage — the schema field is now optional, since nothing reads contentType from the notification anyway. Reproduced live in Datadog: 233 decode-error occurrences over 14 days, all in dev, correlating with the connector's own confirmation-egress writes.

PR: gfs-bifrost/sftp-connector#240
PR: gfs-bifrost/sftp-connector#237

## 2026-07-27 — FUSE-960

Emit file-level create_data_failure for files that fail before row validation

Files that hard-fail during ingest (malformed JSONL, stream errors, unexpected mid-processing exceptions) now publish a file-level create_data_failure (stage ingest, recordType from the file path) before the error propagates — previously these published nothing, leaving the file silently stuck in root with no support visibility. This event is the trigger FUSE-959 uses to route failed files to /error. The failure envelope carries the file's SftpCapture (the GCS payload pointer stamped since FUSE-991), built before any fallible I/O so it's always available; row-level canonical-validation failures now carry the same capture. Failure-emission errors are now counted via a new fuse.failures.emit_failed{level:file|record} metric, alerted on since a swallowed publish means a file stuck in root now drives routing.

PR: gfs-bifrost/sftp-connector#229

## 2026-07-24 — FUSE-959

Route acknowledged and failed SFTP files to /archive and /error

Stacked pair adding file-routing after ingest. First PR: the connector subscribes to create_acknowledge (unfiltered — sftp consumes every ingress use case, so metadata.capture is the real in-code discriminator) and moves each file to <use-case>/archive/ on the first accepted record, resolved from the event's metadata.capture GCS pointer. Placement uses per-upload claim keys ({bucket}/{object}:{correlationId}) with two-phase pending→done values, a freshness guard, and generation-pinned moves so a stale event can't touch a newer same-named re-upload; GCS location stays authoritative, the cache is only an efficiency knob. New route POST /events/v1/create_acknowledge, new fuse.file_routing.{moved,skipped,move.failure,fail_open} metrics. Second PR: the connector also subscribes to create_data_failure and moves the file (from root or already-archived) to <use-case>/error/ — escalation from /archive is sticky, a later acknowledgement never downgrades a file out of /error. New route POST /events/v1/create_data_failure and a Datadog monitor on fuse.file_routing.move.failure, load-bearing since neither subscription has a dead-letter topic. Both subscriptions deliberately dropped the recordType filter, since sftp is the exclusive consumer of every ingress use case and the real filter is metadata.capture, decided in code.

PR: gfs-bifrost/sftp-connector#228
PR: gfs-bifrost/sftp-connector#230

## 2026-07-20 — FUSE-1049

Fix RGA mapping template grouping key and drop stale OrdType default

RGA mapping template now groups by OrdRef1 + ExpDelDate, matching the Confluence "Return Goods CSV Mapping" doc and the live GADG connector mapping fixed under this ticket — previously grouped by OrdRef1 alone. Removed the order.type: "R01" default, since snap-adapter hardcodes Snap OrderType to S01 for every RGA create and never reads this field — the stale default is what led the Confluence doc to document the same wrong default. The corrected shape was applied to GADG's real dev connector mapping and verified end to end against Snap.

PR: gfs-bifrost/sftp-connector#216

## 2026-07-17 — FUSE-991

Stamp SftpCapture on the create envelope

SFTP ingest now stamps SftpCapture on the create envelope — every create_record_request (and legacy per-entity create) message carries {username, dir, filename, filetype, payload: {store: "gcs", bucket, object}} pointing at the landed GCS object, so the FUSE-796 movers and Customer Transaction History can trace a record back to its source file. Capture rides the shared create metadata fanned out to all create topics; confirmation/failure envelopes are untouched, since capture is create-flow only. Uses the already-published @gfs-bifrost/types BifrostCreateRequestMetadata. One of a 4-PR FUSE-991 set opened together across sftp/dedupe/fapi/shopify.

PR: gfs-bifrost/sftp-connector#212

## 2026-07-16 — FUSE-1000

Fill confirmation defaults on the canonical before mapping

Confirmation mapping defaults now fill the canonical record before mapping runs, rather than being applied after mapping keyed as if they were an output column — a default's key is a canonical field path (same namespace as rule.to), so it now populates the canonical value a rule reads instead of surfacing as its own stray CSV/JSONL column with the raw dotted path as header and no value. A default only applies when the canonical field is absent/empty; a present value still wins. Verified against GADG's live goods_out_confirmation config: before, 28 columns with a stray trailing empty product.unitOfMeasure column; after, exactly the 27 configured/mapped columns.

PR: gfs-bifrost/sftp-connector#214

## 2026-07-15 — FUSE-890

Write pick/pack confirmation files

Added two new confirmation_ready subscriptions (recordType=pick_confirmation / pack_confirmation), each filtered at the Terraform level, flowing through the existing generic :recordType route and ConfirmationEgressService — same generic mapping-resolution and file-write path already used by PO/SO/RGA. On success, publishes to confirmation_made with the matching recordType; that topic's config collapsed from 3 separate env vars (all pointing at the identical topic) to one PUBSUB_TOPIC__CONFIRMATION_MADE. Irrecoverable confirmation-write failures now publish to a new confirmation_data_failure topic instead of throwing past the ack — generalised across every confirmation type ConfirmationEgressService handles, not just pick/pack, since they share one process() method; this is a real behaviour change for existing PO/SO/RGA confirmations, which previously threw uncaught on a write failure. Added confirmation-egress metrics (sftp_connector.confirmations.{processed,skipped,failure}) mirroring shopify-connector's convention. Bumped @gfs-bifrost/types to ^7.5.0 for CanonicalPickConfirmation/CanonicalPackConfirmation and the pick/pack config-domain use cases.

PR: gfs-bifrost/sftp-connector#211

## 2026-07-07 — FUSE-952

Robust JSON-Lines parsing for json/jsonl ingress

Replaced the fragile `jsonlines` package with a direct line parser for SFTP json/jsonl ingress: split on \r?\n, skip blank lines, JSON.parse each line. Gives a clear, line-numbered error on a malformed line instead of an unhandled SyntaxError, and fixes the crash on well-formed JSON-Lines files that end with a newline or use CRLF. Root-caused from a GADG upload that threw an unhandled exception in dev (FUSE-994). Does not make whole-file pretty-printed JSON arrays (not line-delimited) parse — those files need re-authoring as one JSON object per line.

PR: gfs-bifrost/sftp-connector#200

## 2026-07-03 — FUSE-954

Apply configured CSV column order to confirmation egress

Confirmation CSV columns now follow the connector's configured columnOrder — configured columns lead in the given order, unlisted columns append in derivation order, duplicates de-duped. Applies only on the dynamic-mapping path and only to CSV egress; JSON/JSONL output is unaffected. columnOrder is threaded onto the local ResolvedConfig and allowed through MappingConfigSchema so it survives the mapping cache round-trip. Enabled feature_flag_use_dynamic_confirmation_mapping in dev (prod stayed false). Stayed on types ^6.3.0 rather than bumping to 7.2.0, which would have pulled the unrelated 7.0.0 businessId-required major.

PR: gfs-bifrost/sftp-connector#202

## 2026-06-23 — FUSE-794

Shared BifrostMessageMetadata + recordType on egress

Collapsed the local EventMetadata fork (stamped by FUSE-946's #189) onto the shared @gfs-bifrost/types BifrostMessageMetadata, which now carries source/connectorId/recordId/recordType. Bumped types ^6.0.0 → ^6.3.0. recordType is now stamped on all egress metadata — new records, made-confirmations, validation failures, and user-creation events. connectorId deliberately left unpopulated: sftp resolves it inside the cached mapping_rules:{username}|{useCase} path which discards it after lookup, so surfacing it reliably needs a separate cache-contract change. recordId stays per-record on the logger rather than the envelope, since sftp publishes batches and a single envelope recordId would be ill-defined.

PR: gfs-bifrost/sftp-connector#192

## 2026-06-18 — FUSE-946

Per-record reference + filename logging at ingress

Ingress logs now carry the customer's own per-record reference (sales order customerRef/shipmentId, PO number/supplier ref, master-data SKU) via a new getRecordReference, best-effort even for records that fail canonical validation, so ILG support can trace a record by the customer's own reference instead of the correlationId they don't hold. Every log line's requestor block gained flow/recordType/filePath/fileName (parity with snap-adapter), and support-facing lines (no-mapping-rules skips, confirmation/validation-failure errors, connector-not-found) are now tagged audience:support + integration:sftp. All outbound Bifrost message metadata now carries source: "sftp-connector" — FUSE-794 traceability groundwork applied from the emit side to ingress records, confirmations, user-creation and validation-failure messages.

PR: gfs-bifrost/sftp-connector#189

## 2026-06-12 — FUSE-844

Skip confirmation file write when records produce no rows

A confirmation event whose records produce zero rows (all records dropped by schema validation, or schema-valid goods-out records with no consignments) previously crashed toCsv with a TypeError, so Pub/Sub redelivered the message indefinitely — 486 occurrences of a 500 on POST /events/v1/confirmation/ready/sales_order for one smoke-test record. The handler now logs, skips the file write, and acks 204; applies to both CSV and JSONL egress (JSONL previously wrote a zero-byte file for the same input).

PR: gfs-bifrost/sftp-connector#183

## 2026-06-11 — FUSE-953

Replace VPC connector + NAT with Direct VPC egress

Cloud Run switched to Direct VPC egress (network_interfaces on the existing subnet) instead of a Serverless VPC Access connector, with egress mode changed from ALL_TRAFFIC to PRIVATE_RANGES_ONLY — same private-range reachability, zero fixed cost. The Cloud Router, NAT gateway and VPC connector were deleted; the VPC/subnet, the Memorystore PSA pair, and the SFTP GCE VM (with its own public IP, on the default network) were left untouched. Part of the fleet-wide FUSE-953 network-cost rollout, piloted on dedupe-service.

PR: gfs-bifrost/sftp-connector#181

## 2026-06-05 — FUSE-827

Subscribe to and ack RGA confirmations

Added a filtered Pub/Sub subscription on the cross-entity confirmation_ready topic (filter = attributes.recordType = "return_goods_authorization") — the first subscription-level recordType filter in this repo. RGA joined the generic confirmations flow (canonical validation via ConfirmationsService.decodeConfirmations); the mapping-rules gate means RGA messages ack 204 without writing files until the mapping use case and transformer land separately. All push routes moved onto the Events API v1 grammar (/events/v1/<domain>/<stage>/:recordType) in the same PR, with no legacy aliases. RGA's record type is return_goods_authorization platform-wide (route, ConfirmationType, use-case name, subscription filter) — the RGA mnemonic retired before any publisher existed. Confirmation metric/log type tags changed value (kebab-case to snake_case, e.g. purchase-order → purchase_order).

PR: gfs-bifrost/sftp-connector#177

## 2026-06-04 — FUSE-833

Emit validation failures to the create_data_failure topic

Records that fail canonical validation at SFTP ingress now publish to create_data_failure as BifrostFailure events (recordType attribute per use case) instead of being dropped after logging, carrying per-field validation problems plus the original record so ILG support can see exactly what was rejected. Valid records are unaffected, even if the failure publish itself fails (publish errors log, never throw). Added the PUBSUB_TOPIC__CREATE_DATA_FAILURE env var and publisher IAM grant, and the /debug translate endpoint now also reports invalid records. Follows the platform's single cross-entity create_data_failure topic discriminated by recordType, rather than the ticket's originally suggested per-use-case topic naming.

PR: gfs-bifrost/sftp-connector#176

## 2026-06-03 — FUSE-673

Write confirmation files in the connector's configured egress format

Added JSON-Lines egress alongside CSV. Bumped @gfs-bifrost/types to ^4.2.0 for the new required egressFiletype ("csv" | "jsonl") on SFTPIngressSchema, added FileType.JSONL + fileTypeForEgress(), and a toJsonl() that runs the same registered transformer as toCsv() before writing one JSON object per line. confirmationsHandler now groups connectors by egressFiletype and writes each user's file in their configured format instead of hardcoding CSV; the stock-adjustment path gained the same per-user format routing. upsertJsonl() mirrors upsertCsv()'s same-window append semantics (no header row to strip).

PR: gfs-bifrost/sftp-connector#174

## 2026-06-02 — FUSE-748

Handle stock adjustment confirmations end to end

Adds the stock-adjustment confirmation flow, stacked across two PRs. First bumped @gfs-bifrost/types to v4 (adding the STOCK_ADJUSTMENT use case and CanonicalStockAdjustment) and added a dedicated stockAdjustmentHandler / POST /confirmations/stock-adjustment route with Terraform wiring for the stock_adjustment_ready push subscription and stock_adjustment_made publish IAM — ack-only, no processing yet. Second PR added the transformer mapping CanonicalStockAdjustment to a CSV row per the published default mapping, a StockAdjustmentService that resolves the business's SFTP connectors, gates on the stock_adjustment use case being active and mapped (logging an error if active-but-unmapped), appends to an hourly CSV, and emits stock_adjustment_made.

PR: gfs-bifrost/sftp-connector#170
PR: gfs-bifrost/sftp-connector#171

## 2026-01-06 — FUSE-614

Add business ID to correlation info

Updates namespace handlers and controllers to include and append business ID where appropriate, and removes unnecessary mocks to make tests more consistent.

PR: gfs-bifrost/sftp-connector#92

## 2025-12-31 — FUSE-505

Switch to new DDP rules

Adds DDP handling to the SFTP service and removes a large amount of unused code and exports. Adds unit tests for the sales order transformer and an integration test for the use-case router.

PR: gfs-bifrost/sftp-connector#91

## 2025-12-09 — FUSE-556

Flip mappings based on ILG requirements

Corrected the OrdRef2/OrdRef3 mapping across the sales order translator configs — OrdRef2 to customer.order, OrdRef3 to identifiers.salesOrder — across academicallyGifted, byoma, lisaPL, lisaUk, nuzest, shackletonUk, ilgLegacy and ilgStandard CSV configs, plus the OrdRef2 fix alone on ilgLite.

PR: gfs-bifrost/sftp-connector#79

## 2025-11-14 — FUSE-326

Emits logs to ILG

Adds a sidecar for shipping logs to ILG and updates the pipelines to support it.

PR: gfs-bifrost/sftp-connector#74

## 2025-10-31 — FUSE-455

Uses line-level batchId and other values

Fixes incorrect date mapping in purchaseOrderTransformer by reading batchId/production/expiry off the line rather than the goodIn record, and adds an UNKNOWN_BATCH_ID fallback.

PR: gfs-bifrost/sftp-connector#71

## 2025-10-03 — FUSE-186

Migrate to dedicated types module

Migrates the service onto a dedicated types module, removing duplicated local type definitions, and refactors STU grouping for readability and type safety.

PR: gfs-bifrost/sftp-connector#53

## 2025-09-24 — FUSE-241

Obfuscates usernames and adds folder permissions to avoid data leaks

Obfuscates SFTP usernames so users can't be identified from their login, and adds per-folder permissions so a user can't download another user's files. Maintains an obfuscation lookup so the same public key still works for existing un-obfuscated users.

PR: gfs-bifrost/sftp-connector#49

## 2025-09-22 — FUSE-214

Adds ID from payload in to event

Adds the ID from the event payload into the output log file.

PR: gfs-bifrost/sftp-connector#48

## 2025-09-15 — FUSE-163

Write incoming exceptions to the SFTP server

Added a temporary exception-handling endpoint and a support-facing exception log. Entity errors land on a dedicated Pub/Sub subscription and get written as CSV to Cloud Storage via a new SupportLogWriter, readable by a new `support` SFTP user provisioned in both dev and prod.

PR: gfs-bifrost/sftp-connector#38

