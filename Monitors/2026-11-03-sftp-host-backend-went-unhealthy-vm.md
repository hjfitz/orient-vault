---
tags: [datadog-triage]
date: 2026-11-03
monitor: "[FUSE][SFTP Host] SFTP backend went unhealthy: sftp-connector-prod-sftp-vm"
service: sftp-host
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793699522737549"
opened_at: "2026-11-03T09:50:56Z"
severity_assessed: P4
flapping: false
outcome: false_positive
ticket:
session_id: 7198be0e-f4de-4cae-8e32-ef4ac0c4cdb9
status: open
---
# SFTP VM backend went unhealthy: prod cut step S3 took the VM out of the backend service by design

## Fired
Monitor 335786576 (`sum(last_10m):sum:gcp.logging.user.sftp_host_backend_unhealthy{project_id:bifrost-prod-global1} by {instance_group} > 0`, a log-based metric over LB health-check HEALTHY to UNHEALTHY transitions) went Alert for group `sftp-connector-prod-sftp-vm`. Slack parent post 09:52:02Z. Its own message says taking the VM out of the backend at S3 fires it once.

## Investigation
- Waypoint plan `sftp-host-c-prod-cutover-and-vm-decommission`: step 4 is "S3 then S4: drain the VM"; S3 is `sftp_vm_backend = false`. The plan has no 2026-11-03 S3 entry yet (file last modified 09:17Z); the S3 evidence below is from GitHub and GCP.
- gfs-bifrost/sftp-connector PR #392 "Take the prod SFTP VM out of the backend service (cut S3)", author and merger Harry, merged 09:41:35Z as `72984d4`. Body: removes the VM backend, `sftp-host-prod` keeps only the host MIG, health check becomes HTTP `/healthz` 8080 (the VM cannot pass it); VM keeps running for provisioning until S4. "Deploy sftp-host" run 41613083576 and "Deploy sftp-connector" run 41613083543 both success (09:46:41Z / 09:46:18Z).
- Audit log: `regionBackendServices.update` on `sftp-host-prod` by github-runner at 09:46:03Z with backends = host MIG only and healthChecks = `sftp-host-prod-http`, and again 09:46:34Z. No instance stop/delete since 08:12Z (only the S2 MIG scale-down deletes, then 09:02Z ramp inserts).
- Health-check log: one HEALTHY to UNHEALTHY transition for group `sftp-connector-prod-sftp-vm` (10.154.0.3, TCP probe, TIMEOUT) at 09:46:43Z, 40 s after the backend removal. That is the metric's trigger; the alert fired at 09:50:56Z (10 m window).
- Live now (~09:53Z): `backend-services get-health sftp-host-prod` lists only the host MIG, 3/3 HEALTHY (x0rl, cbm5, w78r). `instanceGroups` shows `sftp-connector-prod-sftp-vm` is still a group but no backend service references it (listed both prod sftp backend services). VM instance `sftp-connector-prod-sftp` is RUNNING (last start 2026-10-20, no stop).
- Customers: host `sftp login` lines per user 09:00 to 09:55Z: C062E5C41B 118, E5A356978A 12, C232BE3BCC 12, 447A6A12D5 5, 15ADCA408F 1, 8B8F319605 1, 84B6F5A152 1. C232 (first host login 09:47:21Z), 15ADCA408F (09:46:36Z), 84B6F5A152 (09:47:40Z) and 8B8F319605 (09:51:47Z) had no host logins before the S3 apply. The plan's 09:03 to 09:15Z check had the VM serving C062 (3.64.142.243), C232 and DD2A. Logins per minute rose from 2 to 6-8 from 09:47Z.
- Host warn/error/failed/mismatch: 0 lines 09:00 to 10:00Z. Two `sftp request refused` info lines (type `simple@putty.projects.tartarus.org`, users 84B6F5A152 at 09:47:40Z and 8B8F319605 at 09:51:47Z); both users logged in on the same second.
- sftp-connector prod logs: present most minutes 09:30 to 09:53Z, 0 error-status lines; spikes 09:35-09:36 and 09:50Z.
- Slack thread: parent only, no replies. Monitor events 3 d: only the publish edit on 2026-11-02 18:54Z, so not a flapper (the monitor is new).

## Not established
- Whether every customer that used the VM has reconnected on the host: VM sshd logs are not in Cloud Logging. DD2A (VM-side at 09:15Z) has no host login 09:00-09:55Z; the PR itself says five VM-side users had not yet connected to the host. Plan AC says every baseline username logs in to the host within 24 h.
- Whether any upload was missed: no per-file reconciliation run.
- The meaning and impact of the two refused putty requests (no failure observed).
- Monitor clear time (10 m window, expected about 09:57Z).

## Outcome
Expected by design: planned S3, merged by Harry 09:41Z, fires once as the VM leaves the backend. No customer outage evidenced, host serving, no errors. Not escalated. Worth a follow-up: the plan lacks an S3 entry; check DD2A within 24 h.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793699522737549
- PR: https://github.com/gfs-bifrost/sftp-connector/pull/392
- Monitor: https://app.datadoghq.com/monitors/335786576
