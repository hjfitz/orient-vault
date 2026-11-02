---
tags: [meeting]
series: 1-1 Schuster Efigenio
counterpart: "[[Schuster Efigenio]]"
title: 1-1 Schuster Efigenio
---
# 1-1 Schuster Efigenio

## 2026-10-29
_10:30–11:00 GMT · Regus Southampton (in person) · no agenda_

### Context

**Open PRs**
- [core-infra#16](https://github.com/gfs-bifrost/core-infra/pull/16) (FUSE-1302): awaiting review, CI green, idle 2d
- [sftp-connector#345](https://github.com/gfs-bifrost/sftp-connector/pull/345) (FUSE-1302): awaiting review, CI green, idle 2d
- [snap-adapter#313](https://github.com/gfs-bifrost/snap-adapter/pull/313) (FUSE-1328): draft, CI red on the image and dependency audit legs, opened yesterday
- [snap-adapter#203](https://github.com/gfs-bifrost/snap-adapter/pull/203) (FUSE-1050): draft, idle 61d
- [pkg-node#278](https://github.com/gfs-bifrost/pkg-node/pull/278) (FUSE-1277): draft, idle 5d

**Active Jira**
- [FUSE-1302](https://globalfreight.atlassian.net/browse/FUSE-1302) Consume stock_sync and write the mapped export file (Code Review)
- [FUSE-1328](https://globalfreight.atlassian.net/browse/FUSE-1328) Batch absent on finished good receipt and work order component lines (In Progress, Sev 3)

**Owed by you**
- Approve his leave for 30 Oct (tomorrow), his holiday for 16–18 Nov, and the new requests for 24 Dec and 29–31 Dec
- Complete the 6-month probation review form and send it to him plus HR (long overdue)
- Hold his start-of-year PDR meeting
- Weigh in on his Snap UI Automation proposal to [[Oli Denton]]
- Chase his overdue training: antitrust and the Sustainability e-learning by 5 Nov

### To raise
- [ ] snap-adapter#203 is a 61-day-old draft: ready, or close it? (carried ×2)
- [ ] FUSE-1302's two PRs have waited 2 days for review: who is reviewing?
- [ ] FUSE-1328's draft is red only on the audit legs, which is the fleet advisory wave rather than his change?
- [ ] Distraction Duty moved to [[Matt Shaw]] this sprint: any handover notes from his week?

### Carried from last time
- [ ] Probation Final Review — still outstanding, now materially overdue
- [ ] Reply on GFS-side SNAPDowntime mailing-list access (his ask from 07-17)

### Notes
- ✍️

## 2026-10-22
_10:30–11:00 BST · Regus Southampton (in person) · no agenda. Harry/Oli ends at 10:30 in Epsilon House, so check where you will be_

### Context

**Open PRs**
- [snap-adapter#246](https://github.com/gfs-bifrost/snap-adapter/pull/246) (FUSE-1077): awaiting review, CI green
- [snap-adapter#203](https://github.com/gfs-bifrost/snap-adapter/pull/203) (FUSE-1050): draft, idle 54d
- [pkg-node#278](https://github.com/gfs-bifrost/pkg-node/pull/278) (FUSE-1277): draft, CI green

**Active Jira**
- [FUSE-1314](https://globalfreight.atlassian.net/browse/FUSE-1314) Sprint 16 Distraction Duty (In Progress)
- [FUSE-1302](https://globalfreight.atlassian.net/browse/FUSE-1302) Consume stock_sync and write the mapped export file (In Progress, no open PR)
- [FUSE-1077](https://globalfreight.atlassian.net/browse/FUSE-1077) Attribute each goods-in confirmation line its own batch by SKU (Code Review)
- [FUSE-1010](https://globalfreight.atlassian.net/browse/FUSE-1010) Multi-parcel goods-out confirmations (In QA)
- Done yesterday: FUSE-1293, FUSE-1272 and FUSE-828

**Owed by you**
- Approve his leave request for 30 Oct and his holiday request for 16–18 Nov
- Complete the 6-month probation review form and send it to him plus HR (long overdue)
- Hold his start-of-year PDR meeting
- Weigh in on his Snap UI Automation proposal to [[Oli Denton]]
- Chase his overdue training: antitrust and the Sustainability e-learning by 5 Nov

### To raise
- [ ] Distraction Duty is his this sprint: 9 nightlies are red, with `follow-redirects` still failing in fapi and dedupe-service, base-image CVEs in the image scans, and `proxy-addr` and the MCP SDK in snap-mcp and fuse-mcp. sftp-connector fixed it with a lockfile bump (#328)
- [ ] FUSE-1302 is In Progress with no open PR
- [ ] snap-adapter#203 is 54d old: ready, or close it? (carried ×1)
- [ ] [[Harry Humby]] opened four PRs on his Distraction Duty ticket FUSE-1314

### Carried from last time
- [ ] Probation Final Review — still outstanding, now materially overdue
- [ ] Reply on GFS-side SNAPDowntime mailing-list access (his ask from 07-17)

### Notes
- ✍️

## 2026-10-15
_10:30–11:00 BST · Regus Southampton (in person) · no agenda_

### Context

**Open PRs**
- [snap-adapter#203](https://github.com/gfs-bifrost/snap-adapter/pull/203) (FUSE-1050): draft, open 47d, stale
- [snap-adapter#246](https://github.com/gfs-bifrost/snap-adapter/pull/246) (FUSE-1077): draft, open 22d, stale

**Active Jira**
- [FUSE-1077](https://globalfreight.atlassian.net/browse/FUSE-1077) Attribute each goods-in confirmation line its own batch by SKU (In Progress)
- [FUSE-1035](https://globalfreight.atlassian.net/browse/FUSE-1035) Serve customer GET /stock by proxying to the WMS gateway (Code Review)
- [FUSE-1210](https://globalfreight.atlassian.net/browse/FUSE-1210) Route get stock requests to the WMS gateway (Code Review)
- [FUSE-828](https://globalfreight.atlassian.net/browse/FUSE-828) Write RGA confirmations and clear down (In QA, 26d)
- [FUSE-1010](https://globalfreight.atlassian.net/browse/FUSE-1010) Multi-parcel goods-out confirmations stamp the first parcel's tracking (In QA, 22d)
- [FUSE-1272](https://globalfreight.atlassian.net/browse/FUSE-1272) Verify returns confirmation batch attribution (In QA)

**Other context**
- The standup is at Harry's Desk 30 minutes earlier, so check where you will be

### To raise
- FUSE-1035 and FUSE-1210 are still in Code Review, but fapi#169 and fapi#170 have merged: move them to QA?
- snap-adapter#203 is 47d old: ready, or close it?
- FUSE-828 and FUSE-1010 have sat In QA for 26d and 22d
- His PDR meeting is owed

### Carried from last time
- [ ] Probation Final Review — still outstanding, now materially overdue
- [ ] Reply on GFS-side SNAPDowntime mailing-list access (his ask from 07-17)

### Notes
- ✍️

## 2026-10-12
_no meeting today_

### To raise
- [snap-adapter#203](https://github.com/gfs-bifrost/snap-adapter/pull/203) (FUSE-1050): draft open 44d, idle 44d. It was flagged for re-verification against rules-engine 2.0.2
- [snap-adapter#246](https://github.com/gfs-bifrost/snap-adapter/pull/246) (FUSE-1077): draft open 19d, idle 12d
- [FUSE-1035](https://globalfreight.atlassian.net/browse/FUSE-1035) and [FUSE-1210](https://globalfreight.atlassian.net/browse/FUSE-1210) are In Progress with no PR, held 3d and 5d: status?
- FUSE-642 and FUSE-828 have sat in QA for 23d, FUSE-1010 for 19d. They are merged and waiting for sign-off
- His PDR meeting is owed

### Carried from last time
- [ ] Probation Final Review — still outstanding, now materially overdue
- [ ] Reply on GFS-side SNAPDowntime mailing-list access (his ask from 07-17)

### Notes
- ✍️

## 2026-10-08
_no meeting today_

### To raise
- [FUSE-1210](https://globalfreight.atlassian.net/browse/FUSE-1210) is In Progress with no open PR: where is the work?
- [snap-adapter#203](https://github.com/gfs-bifrost/snap-adapter/pull/203) ([FUSE-1050](https://globalfreight.atlassian.net/browse/FUSE-1050)) is a draft idle 40d: ready, or dead?
- [snap-adapter#246](https://github.com/gfs-bifrost/snap-adapter/pull/246) ([FUSE-1077](https://globalfreight.atlassian.net/browse/FUSE-1077)) is a draft idle 8d
- [FUSE-642](https://globalfreight.atlassian.net/browse/FUSE-642) and [FUSE-828](https://globalfreight.atlassian.net/browse/FUSE-828) have been In QA for about 19 days
- His PDR meeting is owed

### Carried from last time
- [ ] Probation Final Review — still outstanding, now materially overdue
- [ ] Reply on GFS-side SNAPDowntime mailing-list access (his ask from 07-17)

### Notes
- ✍️

## 2026-10-05
_no meeting today_

### Context

**Open PRs**
- [snap-adapter#203](https://github.com/gfs-bifrost/snap-adapter/pull/203) — [FUSE-1050](https://globalfreight.atlassian.net/browse/FUSE-1050) — draft, open 37d, idle 37d
- [snap-adapter#246](https://github.com/gfs-bifrost/snap-adapter/pull/246) — [FUSE-1077](https://globalfreight.atlassian.net/browse/FUSE-1077) — draft, CI green 19/19, open 12d, idle 5d
- [fuse-ui#286](https://github.com/gfs-bifrost/fuse-ui/pull/286) — [FUSE-1280](https://globalfreight.atlassian.net/browse/FUSE-1280) — awaiting review, CI green
- [fuse-ui#285](https://github.com/gfs-bifrost/fuse-ui/pull/285) — [FUSE-1275](https://globalfreight.atlassian.net/browse/FUSE-1275) — draft, CI green 11/11

**Active Jira**
- [FUSE-1273](https://globalfreight.atlassian.net/browse/FUSE-1273) [Snap] Attribute per-batch expiry and production date on goods-in confirmation lines (Ready for Refinement, assigned to him)
- [FUSE-1280](https://globalfreight.atlassian.net/browse/FUSE-1280), [FUSE-1275](https://globalfreight.atlassian.net/browse/FUSE-1275) and [FUSE-1077](https://globalfreight.atlassian.net/browse/FUSE-1077) In Progress
- Merged and awaiting QA: [FUSE-1010](https://globalfreight.atlassian.net/browse/FUSE-1010), [FUSE-1191](https://globalfreight.atlassian.net/browse/FUSE-1191), [FUSE-1272](https://globalfreight.atlassian.net/browse/FUSE-1272), [FUSE-642](https://globalfreight.atlassian.net/browse/FUSE-642) (held 16d) and [FUSE-828](https://globalfreight.atlassian.net/browse/FUSE-828) (held 16d)

**Owed by you**
- Approve his 16–18 Nov holiday request in the HR system (carried ×3)
- Hold his start-of-year PDR meeting (Kate Meadows' 10-01 email)
- Weigh in on his Snap UI Automation proposal (to Oli, carried ×5)

### To raise
- [snap-adapter#203](https://github.com/gfs-bifrost/snap-adapter/pull/203) (FUSE-1050) has been a draft for 37 days: ready, or dead?
- [snap-adapter#246](https://github.com/gfs-bifrost/snap-adapter/pull/246) (FUSE-1077) is green and a draft for 12 days: ready to come out?
- [FUSE-1273](https://globalfreight.atlassian.net/browse/FUSE-1273) is assigned to him: where does it sit after this morning's standup ordering?
- Book the start-of-year PDR meeting
- His 16–18 Nov holiday is awaiting my approval
- Overdue mandatory training: antitrust and the Sustainability e-learning, due 5 Nov

### Carried from last time
- [ ] Probation Final Review — still outstanding, now materially overdue
- [ ] Reply on GFS-side SNAPDowntime mailing-list access (his ask from 07-17)

### Notes
- ✍️

## 2026-10-01
_10:30–11:00 · Regus Southampton · ⚠️ no agenda · ⚠️ clashes with People Update (Teams, tentative)_

### Context

**Open PRs**
- [snap-adapter#203](https://github.com/gfs-bifrost/snap-adapter/pull/203) — [FUSE-1050](https://globalfreight.atlassian.net/browse/FUSE-1050) — draft, idle 33d
- [snap-adapter#246](https://github.com/gfs-bifrost/snap-adapter/pull/246) — [FUSE-1077](https://globalfreight.atlassian.net/browse/FUSE-1077) — draft, CI green 19/19, open 8d
- [fuse-ui#281](https://github.com/gfs-bifrost/fuse-ui/pull/281) — [FUSE-1191](https://globalfreight.atlassian.net/browse/FUSE-1191) — awaiting review, CI green
- [config-service#231](https://github.com/gfs-bifrost/config-service/pull/231) — [FUSE-1191](https://globalfreight.atlassian.net/browse/FUSE-1191) — draft, CI red on the fleet-wide dependency audit and image scan

**Active Jira**
- [FUSE-1191](https://globalfreight.atlassian.net/browse/FUSE-1191) [UI] Configure and validate Shopify stock sync scheduling (In Progress)
- [FUSE-1077](https://globalfreight.atlassian.net/browse/FUSE-1077) [Snap] Attribute each goods-in confirmation line its own batch by SKU (In Progress)
- [FUSE-642](https://globalfreight.atlassian.net/browse/FUSE-642) and [FUSE-828](https://globalfreight.atlassian.net/browse/FUSE-828) in QA 12d, [FUSE-1010](https://globalfreight.atlassian.net/browse/FUSE-1010) 8d

**Owed by you**
- Approve his 16–18 Nov holiday request (HR system)
- Probation Final Review and the 6-Month Probation Review Meeting Form, still outstanding

**Other context**
- His e-learning task is stuck at 100% (your 09-29 email to Julie Fleming, no answer yet)

### To raise
- snap-adapter#203 has been a draft for 33 days: ready, or dead?
- snap-adapter#246 is green and 8 days old in draft: ready to come out?
- FUSE-642 and FUSE-828 have sat in QA for 12 days: who is chasing QA?
- (added 2026-10-02) Hold his start-of-year PDR meeting (Kate Meadows' 10-01 email)
- (added 2026-10-02) [FUSE-1275](https://globalfreight.atlassian.net/browse/FUSE-1275) and [FUSE-1280](https://globalfreight.atlassian.net/browse/FUSE-1280) are picked up as drafts [fuse-ui#285](https://github.com/gfs-bifrost/fuse-ui/pull/285) and [fuse-ui#286](https://github.com/gfs-bifrost/fuse-ui/pull/286)

### Carried from last time
- [ ] Probation Final Review — still outstanding, now materially overdue
- [ ] Reply on GFS-side SNAPDowntime mailing-list access (his ask from 07-17)

### Notes
- ✍️ 

## 2026-09-17
_09:30–10:00 · Regus Southampton · ⚠️ no agenda_

### Context

**Open PRs**
- [snap-adapter#231](https://github.com/gfs-bifrost/snap-adapter/pull/231) — [FUSE-1055](https://globalfreight.atlassian.net/browse/FUSE-1055) — draft, CI green 19/19, idle 1d — worth asking if ready to come out
- Approved my [shopify-connector#268](https://github.com/gfs-bifrost/shopify-connector/pull/268) (FUSE-1228) same afternoon it opened yesterday

### To raise
- 6-Month Probation Review Meeting Form — still outstanding on me, well overdue
- snap-adapter#231 — fully green, is it ready to come out of draft?

### Carried from last time
- [ ] Probation Final Review — still outstanding, now materially overdue
- [ ] Reply on GFS-side SNAPDowntime mailing-list access (his ask from 07-17)

### Notes
- ✍️ 

## 2026-09-03
_09:30–10:00 · Regus Southampton · ⚠️ no agenda_

### Context

**Open PRs**
- [sftp-connector#262](https://github.com/gfs-bifrost/sftp-connector/pull/262) — [FUSE-1055](https://globalfreight.atlassian.net/browse/FUSE-1055) — draft, idle 2d, CI failing (image_scan / Container Image Scan) — likely the fleet-wide overnight DevSecOps failure, not his own bug
- [snap-adapter#203](https://github.com/gfs-bifrost/snap-adapter/pull/203) — [FUSE-1050](https://globalfreight.atlassian.net/browse/FUSE-1050) — draft, idle 4d, CI green 25/25 — worth asking if it's ready to come out of draft

**Active Jira**
- [FUSE-1055](https://globalfreight.atlassian.net/browse/FUSE-1055) [SFTP] Subscribe to confirmation_ready/confirmation_made filtered by source (In Progress)
- [FUSE-828](https://globalfreight.atlassian.net/browse/FUSE-828) [SFTP] Write RGA confirmations and clear down (In QA)
- [FUSE-642](https://globalfreight.atlassian.net/browse/FUSE-642) [SFTP] Enable Work Order use-cases (In QA)
- [FUSE-1142](https://globalfreight.atlassian.net/browse/FUSE-1142) [Types] Make purchase order line purchaseOrderId optional (Ready for QA)
- [FUSE-1077](https://globalfreight.atlassian.net/browse/FUSE-1077) [Snap] Attribute each goods-in confirmation line its own batch by SKU (Backlog)

**To raise**
- sftp-connector's overnight DevSecOps Scans run failed (image_scan / dependency_audit) — same leg failed across ~9 repos, so likely a fleet-wide issue rather than something in his branch specifically
- snap-adapter#203 is fully green and 4 days idle in draft — good moment to ask if it's ready

### Carried from last time
- [ ] Probation Final Review — still outstanding, now materially overdue
- [ ] Reply on GFS-side SNAPDowntime mailing-list access (his ask from 07-17)

### Notes
- ✍️ 

## 2026-08-27
_13:00–13:30 · Regus Southampton_

### Context

**Open PRs**
- [snap-adapter#198](https://github.com/gfs-bifrost/snap-adapter/pull/198) — FUSE-1050 - fix(snap-queue-polling-service): source RGA carrier tracking from the RET_TRACK attachment
- [fuse-mcp#34](https://github.com/gfs-bifrost/fuse-mcp/pull/34) — data: record collector as a subscriber on create_acknowledge and create_data_failure
- [fuse-mcp#15](https://github.com/gfs-bifrost/fuse-mcp/pull/15) — data: work_order flows end to end (fapi → collector/dedupe → snap-adapter) (FUSE-857)

**Active Jira**
- [FUSE-1077](https://globalfreight.atlassian.net/browse/FUSE-1077) [Snap] Attribute each goods-in confirmation line its own batch by SKU (Backlog)
- [FUSE-1024](https://globalfreight.atlassian.net/browse/FUSE-1024) [Collector] Record processed/failed lifecycle status from create_acknowledge and create_data_failure (In Progress)
- [FUSE-938](https://globalfreight.atlassian.net/browse/FUSE-938) [Shopify] - Clean Logging (Backlog)

**Carried from last time**
- [ ] Probation Final Review — still outstanding, now materially overdue
- [ ] Reply on GFS-side SNAPDowntime mailing-list access (his ask from 07-17)

### Notes
- ✍️ 

## 2026-08-20
_09:30–10:00 · in person (Regus Southampton) · ⚠️ no agenda_

### Context

**Open PRs**
- [sftp-connector#251](https://github.com/gfs-bifrost/sftp-connector/pull/251) — [FUSE-642](https://globalfreight.atlassian.net/browse/FUSE-642) enable work order ingress use case — out of draft since yesterday, 🔵 awaiting review, CI green 14/14, Jira at Code Review
- [fuse-mcp#15](https://github.com/gfs-bifrost/fuse-mcp/pull/15) — [FUSE-857](https://globalfreight.atlassian.net/browse/FUSE-857) work_order flows end to end — still 🟠 draft, ⚠️ stale (idle 16d now), CI green 13/13

**Active Jira**
- [FUSE-642](https://globalfreight.atlassian.net/browse/FUSE-642) — [SFTP] Enable Work Order use-cases (Code Review)
- [FUSE-828](https://globalfreight.atlassian.net/browse/FUSE-828) — [SFTP] Write RGA confirmations and clear down (Rework Required)
- [FUSE-1077](https://globalfreight.atlassian.net/browse/FUSE-1077) — [Snap] Attribute each goods-in confirmation line its own batch by SKU (Backlog)

**Owed by you**
- **Complete his 6-Month Probation Review Meeting Form and send to him + HR** — [[Laura Bockling]]'s chase, now 28 days since probation ended, still not done
- Nudge him on his overdue antitrust/competition-law training — flagged again by HR this morning

**To raise**
- fuse-mcp#15 is now 16 days idle despite being fully green — same open question raised at the last three 1:1s: what's blocking him from marking it ready?
- Good news: sftp-connector#251 came out of draft since yesterday — worth acknowledging

### Carried from last time
- [ ] Probation Final Review — still outstanding, now materially overdue
- [ ] Reply on GFS-side SNAPDowntime mailing-list access (his ask from 07-17)

### Notes
- ✍️ 

## 2026-08-13
_09:30–10:00 · in person (Regus Southampton) · ⚠️ no agenda_

### Context

**Open PRs**
- [fuse-mcp#15](https://github.com/gfs-bifrost/fuse-mcp/pull/15) — [FUSE-857](https://globalfreight.atlassian.net/browse/FUSE-857) work_order flows end to end — still 🟠 draft, ⚠️ stale (idle 11d now), CI green 13/13

**Active Jira**
- None open-assigned — his work is currently PR-shaped

**Owed by you**
- **Complete his 6-Month Probation Review Meeting Form and send to him + HR** — [[Laura Bockling]]'s chase carried since 2026-07-23 (~3 weeks now), still not done

**To raise**
- fuse-mcp#15 is now 11 days idle despite being fully green — same open question as last time: what's blocking him from marking it ready?
- Antitrust training assignment flagged as overdue in this morning's HR digest — worth a quick nudge

### Carried from last time
- [ ] Probation Final Review — still outstanding, now materially overdue
- [ ] Reply on GFS-side SNAPDowntime mailing-list access (his ask from 07-17)

### Notes
- ✍️ 

## 2026-08-06
_10:30–11:00 · in person (Regus Southampton) · ⚠️ no agenda_

### Context

**Open PRs**
- [fuse-mcp#15](https://github.com/gfs-bifrost/fuse-mcp/pull/15) — [FUSE-857](https://globalfreight.atlassian.net/browse/FUSE-857) work_order flows end to end — 🟠 draft, ⚠️ stale (idle 6d), CI green 13/13

**Closed since last time**
- [collector#75](https://github.com/gfs-bifrost/collector/pull/75) — [FUSE-857](https://globalfreight.atlassian.net/browse/FUSE-857) re-land work orders — merged 2026-08-03

**Active Jira**
- None open-assigned — his work is currently PR-shaped

**Owed by you**
- **Complete his 6-Month Probation Review Meeting Form and send to him + HR** — [[Laura Bockling]]'s chase is well past due (carried since 2026-07-23, ~2 weeks); this slot is the natural close-out

**To raise**
- fuse-mcp#15 is now the stalest PR of his in the fleet at 6 idle days despite being fully green — worth understanding what's blocking him from marking it ready
- collector#75 landed 2026-08-03 — good moment to confirm the work-order re-land is behaving in dev

### Carried from last time
- [ ] Probation Final Review — still outstanding, now materially overdue
- [ ] Reply on GFS-side SNAPDowntime mailing-list access (his ask from 07-17)

### Notes
- ✍️ 

## 2026-07-30
_10:30–11:00 · in person (Regus Southampton) · no agenda_

### Context

**Open PRs**
- [config-service#189](https://github.com/gfs-bifrost/config-service/pull/189) — [FUSE-774](https://globalfreight.atlassian.net/browse/FUSE-774) persist businessId on connector — 🟢 approved + green + mergeable; agree who lands it
- [collector#75](https://github.com/gfs-bifrost/collector/pull/75) — [FUSE-857](https://globalfreight.atlassian.net/browse/FUSE-857) re-land work orders with the correct upsert key — 🔵 needs a reviewer, CI green
- [fuse-mcp#15](https://github.com/gfs-bifrost/fuse-mcp/pull/15) — FUSE-857 work_order flow data — 🟠 draft
- [collector#73](https://github.com/gfs-bifrost/collector/pull/73) merged 07-29 — the re-land in #75 supersedes its upsert key; worth asking what was wrong

**Active Jira**
- None open-assigned — his work is currently PR-shaped

**Owed by you**
- **Probation review form** — [[Laura Bockling]]'s high-importance chase is 3 days unanswered and the probation end date has passed; complete the form and send to him + HR **today** — this slot is the natural close-out

**Other context**
- No agenda on the invite (normal for a 1:1)

### Carried from last time
- [ ] Probation Final Review (ends 26/07) — **now overdue; close out today**
- [ ] Reply on GFS-side SNAPDowntime mailing-list access (his ask from 07-17, still open)

### Notes
- ✍️ 

## 2026-07-23
_09:30–10:00 · in person (Regus Southampton) · no agenda_

### Context

**Open PRs**
- [shopify-connector#175](https://github.com/gfs-bifrost/shopify-connector/pull/175) — [[FUSE-1068]] — 🔴 changes requested by Harry (idle 1d)
- [renovate-runner#6](https://github.com/gfs-bifrost/renovate-runner/pull/6) — (no ticket) — 🔵 awaiting review, CI green (idle 2d)

**Active Jira**
- None in-progress by email lookup — his work is currently PR-shaped

**Owed by you**
- **Probation Final Review** — ends this Sunday 26/07, still not confirmed to HR (Jennifer Pugliese chasing again). ⚠️ This slot double-books today's Bifrost Refinement — worth confirming whether this 1:1 IS the Final Review before moving it.
- Reply on GFS-side SNAPDowntime mailing-list access ahead of the 22–31 July Snap maintenance window (his Friday ask, still open)

**Other context**
- No agenda on the invite (normal for a 1:1)

### Carried from last time
- [ ] Probation Final Review (ends 26/07) — arrange this week

### Notes
- ✍️ 

## 2026-07-16
_10:30–11:00 · in person (Regus Southampton) · no agenda_

### Context

**Open PRs**
- None open — [collector#58](https://github.com/gfs-bifrost/collector/pull/58) ([[FUSE-895]] Pick/Pack persist) merged 2026-07-10

**Active Jira**
- None in-progress by email lookup — his work is currently PR-shaped

**Owed by you**
- **Probation Final Review** — ends 26/07; still not booked (carried since 09/07). Now urgent — 10 days out; Jennifer Pugliese (People) is waiting to arrange under the new policy.

**Other context**
- No agenda on the invite (normal for a 1:1)

### Carried from last time
- [ ] Probation Final Review (ends 26/07) — arrange this week

### Notes
- ✍️ 

## 2026-07-09
_10:30–11:00 · in person (Regus Southampton) · no agenda_

### Context

**Open PRs**
- [collector#58](https://github.com/gfs-bifrost/collector/pull/58) — [[FUSE-895]] Collector subscribe + persist Pick/Pack confirmations — awaiting review, CI green (in today's #bifrost-forge PR status)

**Active Jira**
- None in-progress by email lookup — his work is currently PR-shaped (collector#58)

**To raise**
- **Probation Final Review** — ends 26/07; Jennifer Pugliese (People) emailed to arrange it under the new policy. Book it this week.
- collector#58 needs a reviewer — confirm who's picking it up
- His earlier fuse-ui ui-toolkit stack (#153/#154/#155) — confirm it landed clean and closed out

### Carried from last time
- [ ] Probation check-in (raised 25/06, ends 26/07) → now the formal **Final Review** to schedule

### Notes
- ✍️ 

## 2026-07-02
_10:30–11:00 · in person (Regus Southampton) · no agenda_

### Context

**Open PRs**
- [fuse-ui#153](https://github.com/gfs-bifrost/fuse-ui/pull/153) — ui-toolkit migration 1/3 (core) — needs review, CI green (in today's #bifrost-forge PR status)
- [fuse-ui#154](https://github.com/gfs-bifrost/fuse-ui/pull/154) — ui-toolkit migration 2/3 (theming) — needs review, stacked on #153
- [fuse-ui#155](https://github.com/gfs-bifrost/fuse-ui/pull/155) — ui-toolkit migration 3/3 (sidebars) — needs review, stacked on #154

**To raise**
- His [shopify-connector#156](https://github.com/gfs-bifrost/shopify-connector/pull/156) ([[FUSE-678]]) has merged out — confirm it landed clean and close the loop on his re-review bump
- The 3-PR fuse-ui stack has no linked ticket — ask whether it wants a FUSE ticket for tracking
- Probation ends 26/07 — ~3 weeks out; informal check-in on how he's settling

### Carried from last time
- [ ] Probation check-in (raised 25/06, ends 26/07)

### Notes
- ✍️ 

## 2026-06-25
_10:30–11:00 · in person (Regus Southampton) · no agenda_

### Context

**Open PRs**
- [sftp-connector#193](https://github.com/gfs-bifrost/sftp-connector/pull/193) — [[FUSE-828]] register RGA made-confirmation topic — awaiting review, CI green (in today's #bifrost-forge PR status)

**Active Jira**
- [[FUSE-828]] [↗](https://globalfreight.atlassian.net/browse/FUSE-828) [SFTP] Write RGA confirmations + clear down (Code Review)
- [[FUSE-813]] [↗](https://globalfreight.atlassian.net/browse/FUSE-813) [SFTP] Handle input of return goods files (Ready for QA)
- [[FUSE-938]] [↗](https://globalfreight.atlassian.net/browse/FUSE-938) [Shopify] Clean Logging (Backlog)

**To raise**
- Probation ends 26/07 — ~1 month out (reminder on tomorrow's calendar); informal check-in on how he's settling
- He asked in #bifrost-forge to confirm the PR process ("approver also merges, author takes it from there") — confirm + point at the convention
- His FUSE-794 work landed in yesterday's stack 🎉

### Notes
- ✍️ 

## 2026-06-18

### Context

**Open PRs**
- [renovate-runner#2](https://github.com/gfs-bifrost/renovate-runner/pull/2) — trial Renovate automerge on a scoped repo allowlist (draft)

**Active Jira**
- [[FUSE-947]] [↗](https://globalfreight.atlassian.net/browse/FUSE-947) [Shopify] Log record ID at ingress (In Progress)
- [[FUSE-952]] [↗](https://globalfreight.atlassian.net/browse/FUSE-952) [Sprint 12] Distraction Duty (In Progress)
- [[FUSE-938]] [↗](https://globalfreight.atlassian.net/browse/FUSE-938) [Shopify] Clean Logging (Backlog)

**Other context**
- No agenda on the invite (normal for a 1:1)

### Notes
- ✍️ 
