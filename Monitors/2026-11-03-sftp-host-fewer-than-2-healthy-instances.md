---
tags: [datadog-triage]
date: 2026-11-03
monitor: "[FUSE][SFTP Host] Fewer than 2 healthy instances"
service: sftp-host
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "none found"
opened_at: "2026-11-03T08:22:06Z"
severity_assessed: P4
flapping: false
outcome: false_positive
ticket:
session_id: 7198be0e-f4de-4cae-8e32-ef4ac0c4cdb9
status: open
---
# SFTP Host fewer than 2 healthy instances: prod S2 cut step runs the host MIG at size 1 by design

## Fired
Monitor 335786586 (`max(last_5m):sum:network.http.can_connect{service:sftp_host,environment:prod} < 2`, the Datadog Agent http_check on each instance's `/healthz`) went Alert at 08:22:06Z. Its message says it fires by design during a cut step that runs one host instance.

## Investigation
- Metric by host: 3 instances (cbm5, rk3q, sdsf) each reported 1 from 20:24Z to about 08:16Z; from then on only `sftp-host-prod-cbm5` reports, so the sum is 1.
- Waypoint plan `sftp-host-c-prod-cutover-and-vm-decommission`, 2026-11-03 entry: prod S2 ran this morning. #390 (`sftp_host_backend = true`, `sftp_host_size = 1`) merged as `dd046fc` at 08:00:50Z, MIG 3 to 1, host apply done 08:07:05Z, S2 done 08:12:37Z. GitHub runs "Deploy sftp-host" and "Deploy sftp-connector" on `dd046fc` both success; #bifrost-notifications shows both prod deploy-succeeded posts at 08:06Z. The same entry records that Harry muted this monitor to 17:30Z because size 1 trips it, and held the ramp back to size 3 (#391) until 09:00Z.
- Monitor definition shows `muted_until_ts` 1793727000 = 17:30:00Z, matching the plan.
- `gcloud compute backend-services get-health sftp-host-prod` at about 08:25Z: VM backend (`sftp-connector-prod-sftp`) HEALTHY, host backend `sftp-host-prod-cbm5` HEALTHY; MIG list shows 1 instance, RUNNING, HEALTHY, no last error.
- Host logs `service:sftp_host @environment:prod` 08:00 to now: 40 lines, all info, all from cbm5; the warn/error/failed/refused/mismatch search from 07:30Z returned 0. No Datadog events for the host.
- Customer service: host `sftp login` lines run every minute 08:07 to 08:24Z, mostly FUSE_C062E5C41B, plus FUSE_447A6A12D5 (08:20:49Z) and FUSE_E5A356978A (08:17 and 08:19Z). sftp-connector prod logs are present in every minute bucket from 07:50 to 08:24Z except 08:08, 08:09 and 08:13Z (low-volume minutes, not a gap in service).
- Other SFTP Host monitors: of the 11 prod ones, 9 OK, "backend went unhealthy" No Data (no no-data alerting, as the plan records), and "/healthz failing on host" is muted indefinitely.
- No thread for this alert exists in #bifrost-notifications (channel read from 08:03Z shows nothing after 08:06:54Z; a search for the alert text found no post). Likely related to the mute but not checked.

## Not established
- Whether files were missed: no per-file reconciliation run; sftp-connector log volume and host login cadence look normal.
- Whether the Slack post was suppressed by the mute (no thread found).
- Customers on the VM side were not checked directly (VM sshd lines are not in Cloud Logging); the VM backend reads HEALTHY.

## Outcome
Expected by design: S2 deliberately runs one host instance beside the VM. SFTP is available (both backends HEALTHY, host accepting logins). It clears when the ramp to size 3 (#391, held to 09:00Z) lands. Worth retuning the monitor so a planned cut step does not need a mute (e.g. a downtime keyed to the cut).

## Links
- Monitor: https://app.datadoghq.com/monitors/335786586
- Plan: Engineering/sftp-connector/plans/sftp-host-c-prod-cutover-and-vm-decommission.md
