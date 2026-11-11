---
tags: [datadog-triage]
date: 2026-11-11
monitor: "[FUSE][SFTP Host] SFTP canary failing at key — dev"
service: sftp-connector
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794383326623519"
opened_at: "2026-11-11T07:47:21Z"
resolved_at: "2026-11-11T08:02:21Z"
minutes_spent: 15
severity_assessed: P4
flapping: false
outcome: self_resolved
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# Dev SFTP canary run failed at the key stage: one Secret Manager read timed out at 07:31Z, next run green, no prod involvement

## Fired
Monitor 335786601 (priority 4, Terraform-managed, critical > 0, evaluation delay 900 s): `sum(last_15m)` of `gcp.logging.user.sftp_canary_runs{project_id:bifrost-dev-global1,outcome:failure} by {stage,side}`. Triggered on `side:none,stage:key` at 07:47:21Z (Slack post 07:48:46Z) and recovered at 08:02:21Z (Slack post 08:03:44Z, value 0.0). `service:sftp_host` is the Datadog tag; the code is `apps/host` in the sftp-connector repo (Fuse MCP `lookup-service sftp-connector`). Dev only: the canary is dev-only by design.

## Investigation
- Cloud Logging, job `sftp-host-dev-canary` (europe-west2), `gcloud logging read`, 07:00-08:20Z: one failed run, execution `sftp-host-dev-canary-xxdc6`, started 07:30:07Z, failed 07:31:23Z (execution completed 07:31:26Z, 1 failed task). Line: `stage=key side=none addr=34.142.66.200:22`, error `access canary key projects/bifrost-dev-global1/secrets/sftp-host-dev-canary-key/versions/latest: context deadline exceeded`. The code (`apps/host/cmd/canary/main.go`, `loadSigner`) logs this when the canary cannot read its own key from Secret Manager, before it dials the server. Every other run from 07:00 to 08:15 logged `success side=host`. The runs either side (07:25, 07:35) succeeded; a normal run takes about 16 s (07:35:05 to 07:35:21), this one took 78 s.
- Counts, same query over 2026-11-04T08:00Z to 2026-11-11T08:15Z: 2019 runs, 2017 success (side=host), 2 failures, both `stage=key side=none` with the identical error. The other failure is execution `sftp-host-dev-canary-vpsjn`, 2026-11-08 21:40:05Z to 21:41:13Z.
- Monitor events (`source:alert`, 14 days): triggers at 2026-11-03 16:01Z (`side:host,stage:cleanup`, a different stage), 2026-11-08 21:57Z (`side:none,stage:key`, recovered 22:12Z) and 2026-11-11 07:47Z (recovered 08:02Z). No trigger in the preceding 24 h, so not a flapper today; the key-stage signature has now occurred twice in 4 days.
- The canary SA's Secret Manager audit log (`AccessSecretVersion` on `sftp-host-dev-canary-key`) has entries at 07:20:21, 07:25:16, 07:35:17 and 07:40:19Z and none between 07:26 and 07:34Z. The 8 Nov failure has the same shape: entries at 21:30:20, 21:35:13 and 21:45:18Z, none at 21:40. The secret is unchanged: `gcloud secrets versions list` shows version 1, enabled, created 2026-10-22T19:40:41, nothing destroyed. No Secret Manager audit entry with a non-zero status in the project from 07:00 to 08:20Z.
- Dev change or cut step at 07:30Z: none found. Cloud Audit admin-activity log for `bifrost-dev-global1`, 06:30-08:00Z today, holds only `cloudsql.instances.connect` by config-service-dev (no Cloud Run, Compute, MIG or IAM write); 21:00-22:00Z on 8 Nov holds `v1.compute.addresses.delete` by the serverless robot at 21:26Z and the same Cloud SQL connects. The dev MIG `sftp-host-dev` has 3 instances, all RUNNING and HEALTHY on template `sftp-host-dev-20261110133158514500000001`, created 2026-11-10T13:32:17-18Z, none started since. The canary job is at generation 10, image `sftp-host:dev-9f782e1cb1bf`, last modified by github-integration. GitHub `sftp-connector`: the last runs on master are the 10 Nov Manual Deploy sftp-host (13:28:56-13:32:41Z, branch hjf/fuse-1351-standard-confirmation-folders, i.e. the dev deploy) and Deploy sftp-host (13:55:42-14:01:38Z, prod, 91d70dea, FUSE-1351 #408); since 14:01Z yesterday there are only the 06:05-06:11Z scheduled scans today. Nothing at 21:40Z on 8 Nov. Datadog `get_change_stories` for sftp_host dev (11 Nov 06:30-08:00Z and 10 Nov 12:00Z to 11 Nov 08:00Z) returned no stories (APM service change tracking only, so the GCP audit log above is the stronger evidence). So today's failure came 18 h after the dev deploy, and the 8 Nov one predates it.
- Waypoint `Engineering/sftp-connector/`: Plan B records the dev cut complete (dev S4 done 2026-10-28); Plan C (prod) is active with S4 done in prod 2026-11-04 and inc 5 held until on or after 2026-11-18; the ledger's latest entry is FUSE-1351 (2026-11-10). No Handovers/ or Monitors/ record mentions an in-progress cut, and `~/.local/state/sftp-cut/` does not exist on this machine. grep for `cut.sh`, `canary`, `335786601` finds only Waypoint plan/ledger, soak and explainer notes and today's digest. So not an expected cut step.
- Dev host (Datadog `service:sftp_host @environment:dev`): 07:00-08:20Z 375 logs, all info (0 warn, 0 error); last 24 h 7764 logs, all info; no warn/error since the 10 Nov 13:30Z deploy. The canary user `FUSE_525C87DEB7` logged in on host `sftp-host-dev-0pm4` at 07:15, 07:20, 07:25, 07:35, 07:40 and 07:45Z and not at 07:30Z, which fits a run that never dialled. Two other dev users logged in 17 times between 07:29 and 07:33Z. In the window there were 5 info-level `sftp login failed` (all `closed_before_auth` from one dev user, none between 07:30 and 07:33Z) and 3 `ssh handshake failed` (`no_common_algorithm`). Dev backend `sftp-host-dev`: 3 of 3 HEALTHY now. "SFTP canary not running — dev" (335786602) is OK.
- Prod: no prod canary exists (the only Cloud Run job in `bifrost-prod-global1` is `config-service-prod-migrate`). Datadog `source:alert` events matching sftp from 06:00 to 08:20Z today are only this monitor's trigger and recovery. No SFTP monitor is in Alert or Warn now (`title:SFTP status:(alert OR warn)` returned nothing); the prod ones listed are OK, bar two log-metric "backend went unhealthy" monitors on No Data. Prod host logs: 434 info, 0 warn/error from 07:00 to 08:20Z, and 8602 info, 0 warn/error in 24 h; sftp-connector prod error logs in the window: none. Prod backend `sftp-host-prod`: 3 of 3 HEALTHY now.
- Impact: only the canary's own run failed. The dev host kept serving logins through 07:30-07:33Z (above), the host and backend are healthy, and the monitor and canary exist only in dev. No business or customer is touched: the canary user is a dev-only test connector.

## Not established
- Why the Secret Manager read timed out. Verified: key secret unchanged, no admin write in the dev project, no audit entry for the call at 07:30Z or 21:40Z on 8 Nov (the call either never reached Secret Manager or never completed). Not checked: Cloud Run job network or egress logs, Google Cloud status for 07:30Z. The error text only says the deadline passed.
- Whether the 11-08 and 11-11 failures share a cause beyond the identical error.

## Outcome
self_resolved, P4: one dev canary run failed at `key` (Secret Manager read, deadline exceeded), the next run was green, the monitor recovered by itself, and nothing in prod was involved. No ticket: 2 failures in 2019 runs, dev only. If the key-stage failure recurs, a retry around the key read in the canary, or a longer Secret Manager call deadline, is the lever to look at (design suggestion, untested). The 10 Nov dev and prod deploys are unrelated to this failure.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794383326623519
- Monitor: https://app.datadoghq.com/monitors/335786601
