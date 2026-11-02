---
tags: [explain]
date: 2026-10-28
thesis: "The dev SFTP cut is complete: the multi-zone Go host has served every dev login since S3 and provisioned every new user since S4 (12:19Z). Both rollbacks are drilled. The S4 drill found two bugs, and both fixes (#376, #377) are merged and live on dev."
confidence: high
---
# SFTP host dev cut: complete, with both rollbacks drilled

```orient-bluf
{ "v": 1, "bluf": "The dev SFTP cut is complete: the multi-zone Go host has served every dev login since S3 and provisioned every new user since S4 (12:19Z). Both rollbacks are drilled. The S4 drill found two bugs, and both fixes (#376, #377) are merged and live on dev.", "confidence": "high", "action": "none; the dev soak ends on exit criteria, earliest end of day 2026-10-29" }
```

## Situation
- **CONFIRMED** Dev S1 put the VM behind the load balancer on 2026-10-25. S2 added the host beside it on 2026-10-27 at 13:35–13:47Z. Prod has not changed: one VM, no load balancer [1].
- **CONFIRMED** Both sides share keys and storage. An upload through either side lands in the same archive [1].
- **CONFIRMED** Each client IP sticks to one side. This is per IP, not per user. MANUCURIST's three IPs sat on both sides at first [1].

## What we ran on 2026-10-27
| Step | PR | Result |
|---|---|---|
| S2 split at size 1 | #359 | 0 added, 2 changed; real partners on the host [1] [2] |
| Ramp to 2 | #360 | One new instance in zone c [1] |
| Rollback-S2 drill | #361 | Host out in 179 s; EPARFUM missed no login [1] |
| Rejoin | #362 | Same split as before [1] |
| Ramp to 3 | #363 | Zones a, b and c HEALTHY; some IPs re-hashed [1] |
| Health-check fix | #364 #365 | Below [3] [4] |

## Assessment
- **CONFIRMED** The defect: the TCP:22 check passed a booting instance. The OS's own sshd answers port 22 for 20–30 s, then stops for 70–90 s until the container listens [1].
- **CONFIRMED** One customer saw it: EPARFUM got 2 of 4 logins at 15:24Z during the ramp to 2 [1].
- **CONFIRMED** The fix probes the container's HTTP 8080 `/healthz` instead. The live backend keeps TCP:22 while the VM is a backend, now needing about 50 s of passes. At S3 it switches to HTTP [5].
- **CONFIRMED** #364's HTTP check first timed out: the firewall omitted the load balancer's two 209.85 probe ranges. #365 added them [6]. All 3 test-backend instances went HEALTHY at 19:24:41Z [4].
- **CONFIRMED** Neither PR changed prod. Both prod applies were "No changes" [4].

## Dwell check-in, 2026-10-28 00:30Z
- **CONFIRMED** Live backend 4/4 HEALTHY, MIG 3/3 on one template. No health-check transitions since 19:30Z [7].
- **CONFIRMED** Canary: 130 of 130 runs green since 13:40Z, all on the VM side [8].
- **CONFIRMED** Host logins since 13:40Z: EPARFUM ×2,574, MANUCURIST ×108, nuzest ×43, ESCENTRIC ×10. The host logged no warning or error [9].
- **CONFIRMED** The rejoin and the ramp to 3 moved MANUCURIST's two VM IPs onto the host, at 15:58Z and 16:08Z. All three now land on the host. Clients notice nothing [9].
- **CONFIRMED** Both dev SFTP Host monitors are OK [10].
- **UNKNOWN** The VM side's real-partner logins since the ramp to 3. The VM's sshd lines are not in Cloud Logging, so reading them needs the admin route.

## Update @ 10:15 — S3 run early, drilled, re-applied
- **CONFIRMED** Harry called S3 at about 20 h into S2. The ramp to 3 finished the dwell's job, raising the host share, on day one [1].
- **CONFIRMED** S3 took 269 s. The live backend became host-only on HTTP `/healthz`, and the instances passed it about 20 s after the swap [11].
- **CONFIRMED** EPARFUM made 4 logins a minute through all three changes. The canary passed on each side it landed on [9] [8].
- **CONFIRMED** The VM's sshd logged no customer session after 09:35:22Z, so the host serves everything [1].
- **CONFIRMED** The rollback-S3 drill restored host+VM in 257 s. S3 went forward again in 240 s [12] [13].
- **ASSESSED** The "backend went unhealthy" alert on the VM's group is cut noise. The VM logged one UNHEALTHY probe on leaving the backend.

| Step | PR | Done (UTC) | Time |
|---|---|---|---|
| S3 | #367 | 09:37:18 | 269 s |
| Rollback-S3 | #368 | 09:52:31 | 257 s |
| S3 again | #369 | 10:02:05 | 240 s |

## Update @ 12:30 — S4 run, drilled, re-applied
- **CONFIRMED** Harry moved the scoped-key gate to the prod plan. The dev host already held the dev key for login audit [1].
- **CONFIRMED** The S4 roll proved the health-check fix. New instances stayed out of the load balancer until their containers were up [14] [15].
- **CONFIRMED** A new connector went PENDING → ACTIVE in about 10 s, provisioned by the host. Its key logged in through the load balancer and uploaded [15].
- **CONFIRMED** EPARFUM made 4 logins in each of the 56 minutes across all three rolls [9].
- **CONFIRMED** Rollback-S4 handed provisioning back to the connector, which provisioned a new user in 13 s. S4 went forward again at 12:19Z [16] [17].
- **CONFIRMED** The VM's sync script set a new user's home before creating the account. A host-made user could not log in on the VM until a second sync [18].
- **CONFIRMED** `cut.sh` stopped mid-roll each time, after Terraform had deleted the old template. Each re-run resumed cleanly [19].
- **UNKNOWN** Why GCP stopped reporting the canary's execution count at about 00:45Z. Every execution succeeded, but the "canary not running" monitor alerts.

| Step | PRs | Done (UTC) | Time |
|---|---|---|---|
| S4 | #370, #371 | 11:17 | about 15 min including the roll |
| Rollback-S4 | #372, #373 | 11:46 | 531 s |
| S4 again | #374, #375 | 12:19 | about 20 min including the roll |

## Update @ 14:55 — both fixes merged and live on dev
- **CONFIRMED** #378 cleared the red image scans: go-jose 4.1.6 for the host, and the bundled undici CVEs allowlisted to 2026-11-04 [20].
- **CONFIRMED** #376 is live. The VM's startup script was re-run at 14:36–14:43Z with no warnings. A host-made user got its key in the right home on its first VM sync [18].
- **CONFIRMED** #377 landed too. The dev host rolled twice, for #378 and #377, and ended 3/3 HEALTHY at 14:50:43Z [19].
- **CONFIRMED** EPARFUM made 4 logins in every minute from 14:20 to 14:51Z. The canary passed on the host every 5 minutes [9] [8].
- **CONFIRMED** Nobody approved a prod gate. #376's and #377's runs wait at prod.

## Open items
| Item | Owner | By |
|---|---|---|
| Canary monitor: read the canary's log outcome, not the GCP metric | agent | next |
| Scoped config-service key (now a prod gate) | Fuse | before prod host |
| Revisit who owns an SFTP user | Harry | after the migration |
| Dev soak exit criteria met (Plan C inc 1 gate): clean to EOD, canary monitor, quiet roll | agent | 2026-10-29 |
| "Backend went unhealthy" monitor fires on ramps | agent | before prod |
| pkg-node zod peer pin (allowlist expiry) | Fuse | 2026-11-01 |

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "doc", "ref": "Engineering/sftp-connector/plans/sftp-host-b-provisioning-login-audit-and-dev-cut.md", "note": "### Evidence, 2026-10-25 and 2026-10-27 entries" },
  { "id": 2, "kind": "pr", "ref": "gfs-bifrost/sftp-connector#359" },
  { "id": 3, "kind": "pr", "ref": "gfs-bifrost/sftp-connector#364" },
  { "id": 4, "kind": "pr", "ref": "gfs-bifrost/sftp-connector#365", "note": "Deploy run 40568361993; dev 0/1/0; prod No changes" },
  { "id": 5, "kind": "code", "ref": "iac/projects/sftp-host/lb.tf@3a0e936:L10-80" },
  { "id": 6, "kind": "code", "ref": "iac/projects/sftp-host/compute.tf@3a0e936:L106-111" },
  { "id": 7, "kind": "log", "ref": "logName=\"projects/bifrost-dev-global1/logs/compute.googleapis.com%2Fhealthchecks\" AND timestamp>=\"2026-10-27T19:30:00Z\"", "note": "zero entries at 00:30Z" },
  { "id": 8, "kind": "log", "ref": "resource.labels.job_name=\"sftp-host-dev-canary\" AND jsonPayload.message=\"sftp canary\"", "note": "vm:success x130" },
  { "id": 9, "kind": "log", "ref": "jsonPayload.message=\"sftp login\" AND jsonPayload.service=\"sftp_host\"", "note": "grouped by raw_username and source IP" },
  { "id": 10, "kind": "url", "ref": "https://app.datadoghq.com/monitors/335786592", "note": "and 335786598; both OK at 00:30Z" },
  { "id": 11, "kind": "pr", "ref": "gfs-bifrost/sftp-connector#367" },
  { "id": 12, "kind": "pr", "ref": "gfs-bifrost/sftp-connector#368" },
  { "id": 13, "kind": "pr", "ref": "gfs-bifrost/sftp-connector#369" },
  { "id": 14, "kind": "pr", "ref": "gfs-bifrost/sftp-connector#370" },
  { "id": 15, "kind": "pr", "ref": "gfs-bifrost/sftp-connector#371" },
  { "id": 16, "kind": "pr", "ref": "gfs-bifrost/sftp-connector#373" },
  { "id": 17, "kind": "pr", "ref": "gfs-bifrost/sftp-connector#375" },
  { "id": 18, "kind": "pr", "ref": "gfs-bifrost/sftp-connector#376" },
  { "id": 19, "kind": "pr", "ref": "gfs-bifrost/sftp-connector#377" },
  { "id": 20, "kind": "pr", "ref": "gfs-bifrost/sftp-connector#378" }
] }
```
