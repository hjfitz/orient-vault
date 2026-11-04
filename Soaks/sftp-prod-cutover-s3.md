---
tags: [soak-test]
status: running
programme: none
unit: Plan C inc 4 (S3 dwell)
started: "2026-11-03T09:46:30Z"
next_checkpoint: "2026-11-18T00:00:00Z"
subjects: [FUSE_033BE0B235, FUSE_15ADCA408F, FUSE_447A6A12D5, FUSE_84B6F5A152, FUSE_8B8F319605, FUSE_C062E5C41B, FUSE_C232BE3BCC, FUSE_DD2AF79592, FUSE_E5A356978A, FUSE_ABDAD7F392, FUSE_BF65660F94, FUSE_59DC37CB09]
queued: []
monitors: [335786575, 335786576, 335786578, 335786579, 335786581, 335786586, 335786587, 335786589, 335786590, 335786595, 335786600]
verdict: ""
---
# Prod SFTP on the Go host at 100% (cut S3)

Since 2026-11-03 09:46:30Z every prod SFTP customer has logged in to the multi-zone Go SFTP host (MIG `sftp-host-prod`, 3 instances in europe-west2 a/b/c) behind the static IP 34.89.6.210. The old VM `sftp-connector-prod-sftp` is out of the backend service. It is still running on its admin IP 34.147.133.18 as the rollback target. Plan: [[Engineering/sftp-connector/plans/sftp-host-c-prod-cutover-and-vm-decommission|Plan C]] (inc 4). Dashboard: `[FUSE][SFTP Connector] Overview`, **SFTP Host** tab (`rnw-pit-a9v`).

## In the soak

| Step | Done | Change |
|---|---|---|
| S2: host joins the backend at size 1 | 2026-11-03 08:12:55Z | sftp-connector#390 (`dd046fc`) |
| Ramp to 3 instances | 2026-11-03 09:05:12Z | sftp-connector#391 (`5616f7e`) |
| S3: VM leaves the backend (host 100%) | 2026-11-03 09:46:30Z, VM drained 09:51:18Z | sftp-connector#392 (`72984d4`) |

Harry chose 100% today ("100% is what I had in mind").

## What passing looks like

- Every customer that logged in to the VM in the 10-29→11-02 baseline logs in to the host, all accepted. 9 of 12 seen by midday. ABDAD7F392, BF65660F94 and 59DC37CB09 log in 2–6 times a week and may not show today.
- Login rates stay in line with the VM's. C062E5C41B logs in from 2 IPs at about 2 a minute each (every 30 s).
- 0 known-user login failures from a customer IP, 0 refused scp, shell or exec from a customer, 0 handshake failures from a customer IP, and 0 upload, audit or session failures.
- Uploads committed match connector files and records emitted, and audit-service stores one `sftp_login` per login.
- No prod SFTP Host monitor (list above) goes non-OK. Monitor 335786576's VM-group alert at the S3 health-check switch was expected and has cleared.

## Breakglass: roll back on any of these

- A real customer failing logins on the host from an IP that worked on the VM.
- A refused scp, shell or exec from a real customer.
- A handshake failure from a customer IP: one with a successful login in the last 7 days, on the VM baseline or the host.
- An ingest drop.
- Any prod SFTP Host monitor in Alert or Warn on a host group.

**Not breakglass (decided 2026-11-03):**
- `support` with `closed_before_auth`: about 25 internet IPs a week try it.
- Handshake failures from IPs that have never logged in: scanners.
- The PuTTY/WinSCP `simple@putty.projects.tartarus.org` refusal: harmless.
- Unknown-user spray: counted only.

## Rollback

`cut.sh prod rollback-s3 --apply --pr <n>` (`apps/host/scripts/cut.sh` in sftp-connector), where `<n>` is a tfvars PR setting `sftp_vm_backend = true` in `iac/env/prod.tfvars`. It is Terraform only and takes about 10 minutes. There's no faster gcloud path, because the VM can't pass the host's HTTP health check.

`cut.sh` merges the PR itself and never approves gates. Approve the run's two `terraform-prod` gates (env 6942708256) only after reading that run's plan. Then DM Harry.

## Running the watch

The kit is `~/sftp-cutover/` (laptop scratchpad or workstation `rc-hjf`). Start with `. ./env.sh`, which exports the Datadog keys from `~/.secrets`.

- `s2-guard.py '<stop UTC>' s2-prod/guard.log` polls every 5 minutes. It exits 3 with `SIGNAL …` on a breakglass signal, or 0 at the stop time.
- `s2-watch.py '<from UTC>'` gives the full report. Per-user/IP accepted counts come from raw events and sum to `login.accepted`.
- `prod-vm-logins.sh '<since>' '<until>'` reads the VM's journal over IAP, read-only. `vm-ip.sh '<since>' '<until>' <ip>` gives one IP's lines.
- `shipdm.py <file>` DMs Harry as Bifrost Support Bot.

## Checkpoints

- **2026-11-03 10:20Z:** clean. 208 logins accepted, 0 failures.
- **2026-11-03 11:45Z (midday DM):** clean. 710 logins accepted from 12 user/IP pairs (9 customers). 41 uploads, 0 failed. 712 audit events stored. The guard woke three times (`support` scanner, DD2AF79592 closed before auth after a good 10:24Z login, a scanner handshake), none for a customer failure. The host's ED25519, ECDSA and RSA keys are identical to the VM's.
- **2026-11-03 13:52Z:** clean on both the laptop and the workstation guards. VM idle since 09:47Z.
- **2026-11-03 13:57Z:** clean. The watch moved from the laptop to the workstation `rc-hjf`. The laptop guard stopped after its 13:57Z check, and its log was copied to `~/sftp-cutover/s2-prod/guard.log` there.
- **2026-11-03 17:00Z (DM'd at 17:04Z): clean. Recommended keeping it overnight.** 2,585 logins accepted from 16 user/IP pairs (11 of 12 customers: ABDAD7F392 and 59DC37CB09 arrived after midday, and BF65660F94 is still unseen). 3 known-user failures, none new since midday (`support` scanner ×2, DD2AF79592 at 11:32Z with no repeat). 200 uploads, 0 failed. 2,590 audit events stored. All monitors OK, and the VM had 0 customer logins. The guard ran 13:58–17:00Z with 0 signals. Afternoon alerts, none breakglass: the dev canary cleanup `connection lost` at 15:45Z (1 in about 2,200 runs), ESCENTRIC CSV content validation ×3, and 1 invalid-type file.
- **2026-11-04 08:23Z (overnight, 17:00Z → 08:23Z): clean, with no guard running.** 5,134 logins accepted from 13 user/IP pairs (per-pair counts sum exactly to `login.accepted`). FUSE_BF65660F94 seen at last (34.96.62.130), so all 12 baseline customers have now logged in to the host. Known-user failures: 4, all `support` closed_before_auth from 4 scanner IPs. 2 handshake failures, both from IPs that have never logged in. 0 upload, audit or session failures, and all monitors OK. The VM had 0 customer logins. The C062 poller moved from 3.64.142.243 to 3.64.131.199 around 00:00Z at the same rate. 145 commits against 144 connector files: the extra one is C062's daily `FUSE_BOMREP_EPARFUM_*` that its staff write into `from_ilg/sales_order_confirmations/` with a second RSA key (`kbTM8YB2…`) from India and its poller then archives. The VM journal shows the same on 11-03 at 03:19Z. It isn't ingest, so it's not a drop.
- **2026-11-04 10:38Z: S4 done**, so the host provisions prod SFTP users (#394, #395). Backlog and DLT 0. Customers were clean across the MIG roll. The first new prod connector through the host is still to be seen.
- **2026-11-04 17:15Z: S4 verify closed in dev** (Harry's call). A new HJF dev connector went ACTIVE in ~10 s through the host on the image prod runs (`40c2285dce9e`). Its key logged in and uploaded through the dev LB. Prod's subscription has 3 open pulls, exactly-once on, backlog and DLT 0.
- **Next:** the inc 5 gate (2 weeks after S4 with no rollback) opens 2026-11-18. Until then rollback-S4 stays available.

## Open

- Watch for DD2AF79592 failing again with no login in between.
- S4 (provisioning moves to the host) is not today.
- **S4 prep done 2026-11-04 (before S4, per Plan C inc 4):** VM startup script re-run at 09:05Z (rc=0; #376's `getent` fix live; 41 users resynced; the 2026-11-02 `sftp-server -l INFO` logging reverted in the file), and a daily `sftp-sync-users.timer` (03:30Z) on the VM. **If the VM ever serves customers again (rollback-S3), disable that timer first**, because each run remounts every user. S4 PRs: sftp-connector#394 (consumer → host) and #395 (host provisioning live), via `cut.sh prod s4`.
- **Plan C inc 2 verify items still owed:** ingest rates, and the first provisioning through `SFTP_ADMIN_HOST`.
- **Not verified:** a real login as `support`, which needs Harry's key.
