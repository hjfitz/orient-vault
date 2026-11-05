---
tags: [meeting]
series: 1-1 Harry Humby
counterpart: "[[Harry Humby]]"
title: 1-1 Harry Humby
---
# 1-1 Harry Humby


## 2026-11-05
_11:30–12:00 GMT · Teams · no agenda_

### Context

**Open PRs**
- [shopify-connector#346](https://github.com/gfs-bifrost/shopify-connector/pull/346) (FUSE-1305): approved, green and mergeable, idle 5d
- [config-service#206](https://github.com/gfs-bifrost/config-service/pull/206) (FUSE-1078): merge conflicts and CI failing, idle 51d
- [snap-adapter#170](https://github.com/gfs-bifrost/snap-adapter/pull/170) and [pkg-node#201](https://github.com/gfs-bifrost/pkg-node/pull/201) (FUSE-1078): drafts, idle 86d

**Active Jira**
- [FUSE-1325](https://globalfreight.atlassian.net/browse/FUSE-1325) Spike: reducing GitHub Actions usage across gfs-bifrost (In Progress, no PR, which is normal for a spike)

**Owed by you**
- Answer his "priority?" on [FUSE-1325](https://globalfreight.atlassian.net/browse/FUSE-1325), the GitHub Actions usage spike; Jack called it "high if it blocks actions" and left the call to me — [Slack](https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1792576768095089?thread_ts=1792576768.095089&cid=C098LD5PS95)
- Approve his leave requests: 15–16 Oct (he is off today), 21–24 Dec and 29–31 Dec — [digest](../Digests/2026-10/2026-10-16.md)
- Confirm who covers Sprint 15 Distraction Duty and hand over the 3 red nightlies: fuse-mocker, tracking-service and snap-mcp, no fix PR exists. Jira has [FUSE-1238](https://globalfreight.atlassian.net/browse/FUSE-1238) on [[Nylah Klasson]], who has resigned, not on him as yesterday's note said — [snap-mcp run](https://github.com/gfs-bifrost/snap-mcp/actions/runs/38356564636)
- Review his [replay-service#116](https://github.com/gfs-bifrost/replay-service/pull/116), the [FUSE-1238](https://globalfreight.atlassian.net/browse/FUSE-1238) replay startup-probe fix: he asked for priority review, and Replay dev deployment failed 4 times on 12 Oct — [Slack thread](https://gfsdeliver-eng.slack.com/archives/C09PBES3MHT/p1791803919997439)
- Run the Shopify "Line item" repair he is waiting on. Monitor 303425509 is Warn with 360 SAIRA failures in 24h; classify before repairing, since an interface-errored order is a poison record and must not be repaired — [monitor](https://app.datadoghq.com/monitors/303425509)
- Review his [shopify-connector#295](https://github.com/gfs-bifrost/shopify-connector/pull/295) and [#296](https://github.com/gfs-bifrost/shopify-connector/pull/296) ([FUSE-1199](https://globalfreight.atlassian.net/browse/FUSE-1199)): awaiting review, CI green
- Hold his start-of-year PDR meeting — [email](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAHCN1rQAAA%3D&exvsurl=1&viewmodel=ReadMessageItem)
- Go/no-go on backfilling the Shopify "Line item has no fulfillment ID" orders (~15 stuck); 10-06: he said again in #bifrost-notifications (Mon 13:27) that running my repair skill should stop the alert — also — [thread](https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790769656403539?thread_ts=1790768033.804159&cid=C099WKQTE8G) — 10-05: the loop stopped Fri and the ~15-order batch was cleared; confirm the question is closed
- Look at his comment on PR 5-of-8 of my fuse-ui stack — he approved the stack but flagged that comment as possibly blocking, still unreplied — [Slack](https://gfsdeliver-eng.slack.com/archives/C09PBES3MHT/p1788514445586199?thread_ts=1788500428.906389&cid=C09PBES3MHT)
- Chase his "IMS Basic Course 2026" training — overdue since 01 Sep per the Yusen Advance notification
- Decide on the **ui-toolkit support proposal** (13/07 leadership huddle) — him helping on ui-toolkit while [[Nylah Klasson]] is out til mid-Aug; no formal decision yet
- Have one coaching conversation about PR evidence expectations — 4 of his 5 open drafts are outstanding purely on uncaptured screenshots / dev e2e, so this is one conversation rather than five PR comments

**Other context**
- ⚠️ overlaps the 11:30 1:1 with [[Matt Shaw]]

### To raise
- [ ] shopify-connector#346 is approved, green and mergeable: why unmerged?
- [ ] FUSE-1078 has three PRs open for 50 days or more (config-service#206 conflicting with CI red, and two drafts at 86d): revive or close?
- [ ] How is he after being off sick on 28 Oct? (carried ×1)
- [ ] config-service#206: rebase and fix, or close? (carried ×3)
- [ ] snap-adapter#170 and pkg-node#201 are drafts idle 79d: finish or close? (carried ×3)
- [ ] dedupe-service#160 has been approved and green for 8 days: why unmerged? (carried ×1)
- [ ] FUSE-1314 is Matt's Distraction Duty ticket, but he opened two PRs on it: should they sit under their own tickets? (carried ×1)
- [ ] His PDR meeting is owed (carried ×3)

### Carried from last time
- [ ] Chase his "IMS Basic Course 2026" training

### Notes
- ✍️ 

## 2026-10-29
_11:30–12:00 GMT · Teams · no agenda · he was off sick on 28 Oct_

### Context

**Open PRs**
- [config-service#206](https://github.com/gfs-bifrost/config-service/pull/206) (FUSE-1078): merge conflicts and CI failing, open 48d, idle 44d
- [snap-adapter#170](https://github.com/gfs-bifrost/snap-adapter/pull/170) and [pkg-node#201](https://github.com/gfs-bifrost/pkg-node/pull/201): drafts, idle 79d
- [dedupe-service#160](https://github.com/gfs-bifrost/dedupe-service/pull/160) (FUSE-1311): approved, mergeable, CI green, idle 8d
- [snap-adapter#304](https://github.com/gfs-bifrost/snap-adapter/pull/304) (FUSE-1311): approved, mergeable, CI green
- [snap-adapter#310](https://github.com/gfs-bifrost/snap-adapter/pull/310), [sftp-connector#354](https://github.com/gfs-bifrost/sftp-connector/pull/354) and [shopify-connector#353](https://github.com/gfs-bifrost/shopify-connector/pull/353) (FUSE-1325): approved, mergeable, CI green
- [replay-service#127](https://github.com/gfs-bifrost/replay-service/pull/127) and [fuse-ui#347](https://github.com/gfs-bifrost/fuse-ui/pull/347): approved and green, opened on Matt's FUSE-1314
- [shopify-connector#346](https://github.com/gfs-bifrost/shopify-connector/pull/346) and [replay-service#126](https://github.com/gfs-bifrost/replay-service/pull/126) (FUSE-1305): drafts, idle 7d

**Active Jira**
- [FUSE-1305](https://globalfreight.atlassian.net/browse/FUSE-1305) Preserve the connector type when redriving a stock sync run (In Progress)
- [FUSE-1325](https://globalfreight.atlassian.net/browse/FUSE-1325) Reduce GitHub Actions usage (Code Review)
- [FUSE-1204](https://globalfreight.atlassian.net/browse/FUSE-1204) and [FUSE-1209](https://globalfreight.atlassian.net/browse/FUSE-1209) are Ready for QA, [FUSE-1205](https://globalfreight.atlassian.net/browse/FUSE-1205) is In QA, all merged

**Owed by you**
- Answer his "priority?" on FUSE-1325; its three PRs are approved and green
- Approve his leave requests for 21–24 Dec and 29–31 Dec
- Hold his start-of-year PDR meeting
- Chase his overdue "IMS Basic Course 2026" training
- Look at his comment on PR 5-of-8 of your fuse-ui stack, still unreplied

### To raise
- [ ] How is he after being off sick on 28 Oct?
- [ ] config-service#206: rebase and fix, or close? (carried ×2)
- [ ] snap-adapter#170 and pkg-node#201 are drafts idle 79d: finish or close? (carried ×2)
- [ ] dedupe-service#160 has been approved and green for 8 days: why unmerged?
- [ ] FUSE-1314 is Matt's Distraction Duty ticket, but he opened two PRs on it: should they sit under their own tickets?
- [ ] His PDR meeting is owed (carried ×2)

### Carried from last time
- [ ] Chase his "IMS Basic Course 2026" training

### Notes
- ✍️

## 2026-10-22
_11:30–12:00 BST · Teams · no agenda_

### Context

**Open PRs**
- [dedupe-service#160](https://github.com/gfs-bifrost/dedupe-service/pull/160) (FUSE-1311): approved, mergeable, CI green, idle 2d
- [config-service#206](https://github.com/gfs-bifrost/config-service/pull/206) (FUSE-1078): merge conflicts and CI failing, idle 37d
- [snap-adapter#170](https://github.com/gfs-bifrost/snap-adapter/pull/170) and [pkg-node#201](https://github.com/gfs-bifrost/pkg-node/pull/201): drafts, idle 72d

**Active Jira**
- [FUSE-1305](https://globalfreight.atlassian.net/browse/FUSE-1305) Preserve the connector type when redriving a stock sync run (In Progress)
- [FUSE-1204](https://globalfreight.atlassian.net/browse/FUSE-1204), [FUSE-1205](https://globalfreight.atlassian.net/browse/FUSE-1205) and [FUSE-1209](https://globalfreight.atlassian.net/browse/FUSE-1209) are Ready for QA
- Done yesterday: FUSE-1152

**Owed by you**
- Answer his "priority?" on [FUSE-1325](https://globalfreight.atlassian.net/browse/FUSE-1325), the GitHub Actions usage spike (Jack left the call to you)
- Approve his leave requests for 21–24 Dec and 29–31 Dec
- Hold his start-of-year PDR meeting
- Chase his overdue "IMS Basic Course 2026" training
- Look at his comment on PR 5-of-8 of your fuse-ui stack, still unreplied

### To raise
- [ ] config-service#206: rebase and fix, or close? (carried ×1)
- [ ] snap-adapter#170 and pkg-node#201 are drafts idle 72d: finish or close? (carried ×1)
- [ ] He opened four PRs on [[Schuster Efigenio]]'s Distraction Duty ticket FUSE-1314: should they sit under their own tickets?
- [ ] His PDR meeting is owed (carried ×1)

### Carried from last time
- [ ] Chase his "IMS Basic Course 2026" training

### Notes
- ✍️

## 2026-10-15
_11:30–12:00 BST · Teams · no agenda_

### Context

**Open PRs**
- [dedupe-service#160](https://github.com/gfs-bifrost/dedupe-service/pull/160) (FUSE-1311): awaiting review, CI green, opened today
- [config-service#206](https://github.com/gfs-bifrost/config-service/pull/206) (FUSE-1078): merge conflicts and CI failing, open 34d, idle 30d
- [snap-adapter#170](https://github.com/gfs-bifrost/snap-adapter/pull/170) and [pkg-node#201](https://github.com/gfs-bifrost/pkg-node/pull/201): drafts, open 65d

**Active Jira**
- [FUSE-1204](https://globalfreight.atlassian.net/browse/FUSE-1204), [FUSE-1205](https://globalfreight.atlassian.net/browse/FUSE-1205) and [FUSE-1209](https://globalfreight.atlassian.net/browse/FUSE-1209) are all Ready for QA (2d)

**Other context**
- His holiday request for 15–16 Oct (per yesterday's digest) covers today, so check this 1:1 is still on
- He asked in #bifrost-forge to bring FUSE-1308 into Sprint 15, because it blocks FUSE-1302. No reply from you yet

### To raise
- FUSE-1308: into Sprint 15 or not
- config-service#206: rebase and fix, or close?
- snap-adapter#170 and pkg-node#201 are drafts idle 65d: finish or close?
- His holiday requests for 21–24 Dec and 29–31 Dec are pending
- His PDR meeting is owed

### Carried from last time
- [ ] Confirm his 23–25 Sept holiday request was actually approved (never confirmed closed)
- [ ] Chase his "IMS Basic Course 2026" training

### Notes
- ✍️

## 2026-10-12
_no meeting today_

### To raise
- [config-service#206](https://github.com/gfs-bifrost/config-service/pull/206) (FUSE-1078): merge conflicts and CI failing, open 31d and idle 27d. Rebase and fix, or close?
- [snap-adapter#170](https://github.com/gfs-bifrost/snap-adapter/pull/170) and [pkg-node#201](https://github.com/gfs-bifrost/pkg-node/pull/201) are drafts idle 62d: finish or close?
- [shopify-connector#318](https://github.com/gfs-bifrost/shopify-connector/pull/318) (FUSE-1202) has merge conflicts. Its stack is on a base branch that is not the default, and #319 and #320 are approved and green
- [FUSE-1199](https://globalfreight.atlassian.net/browse/FUSE-1199) is in Code Review with no open PR for 4d: where is the PR?
- 3 red nightlies are his on Distraction Duty ([FUSE-1238](https://globalfreight.atlassian.net/browse/FUSE-1238)): fuse-mocker, tracking-service and snap-mcp container scans and audit
- His PDR meeting is owed

### Carried from last time
- [ ] Confirm his 23–25 Sept holiday request was actually approved (never confirmed closed)
- [ ] Chase his "IMS Basic Course 2026" training

### Notes
- ✍️

## 2026-10-08
_no meeting today_

### To raise
- [config-service#206](https://github.com/gfs-bifrost/config-service/pull/206) (FUSE-1078) has merge conflicts and failing CI, open 27d and idle 23d: rebase and fix, or close?
- [snap-adapter#170](https://github.com/gfs-bifrost/snap-adapter/pull/170) and [pkg-node#201](https://github.com/gfs-bifrost/pkg-node/pull/201) are drafts idle 58d: finish or close?
- He is on Distraction Duty ([FUSE-1238](https://globalfreight.atlassian.net/browse/FUSE-1238)), so the nightly dependency_audit and image_scan break across 11 repos is his this sprint
- His PDR meeting is owed
- [shopify-connector#295](https://github.com/gfs-bifrost/shopify-connector/pull/295) and [#296](https://github.com/gfs-bifrost/shopify-connector/pull/296) ([FUSE-1199](https://globalfreight.atlassian.net/browse/FUSE-1199)) are awaiting review

### Carried from last time
- [ ] Confirm his 23–25 Sept holiday request was actually approved (never confirmed closed)
- [ ] Chase his "IMS Basic Course 2026" training

### Notes
- ✍️

## 2026-10-05
_no meeting today_

### Context

**Blocked PRs**
- [snap-adapter#248](https://github.com/gfs-bifrost/snap-adapter/pull/248) (FUSE-1195): merge conflicts, CI failing and changes requested, open 12d, idle 2d
- [observability#56](https://github.com/gfs-bifrost/observability/pull/56) (FUSE-1195): merge conflicts, open 4d, idle 3d
- [collector#121](https://github.com/gfs-bifrost/collector/pull/121) (FUSE-1200): merge conflicts, open 3d, idle 3d

**Stale PRs**
- [config-service#206](https://github.com/gfs-bifrost/config-service/pull/206) (FUSE-1078): merge conflicts and CI failing, open 24d, idle 20d
- [snap-adapter#170](https://github.com/gfs-bifrost/snap-adapter/pull/170) (FUSE-1078): draft, idle 55d
- [pkg-node#201](https://github.com/gfs-bifrost/pkg-node/pull/201) (FUSE-1078): draft, idle 55d

**Other**
- [FUSE-1160](https://globalfreight.atlassian.net/browse/FUSE-1160) is in Code Review with no open PR
- [snap-adapter#271](https://github.com/gfs-bifrost/snap-adapter/pull/271) has no ticket and is awaiting review, CI green
- [ui-toolkit#35](https://github.com/ilg-platform/ui-toolkit/pull/35) is a review request waiting on me

**Owed by you**
- Approve or reject his 23–25 Sept holiday request (carried ×18)
- Hold his start-of-year PDR meeting (Kate Meadows' 10-01 email)
- Confirm the Shopify "no fulfillment ID" backfill question is closed (the loop stopped Fri and the ~15-order batch was cleared)

### To raise
- [snap-adapter#248](https://github.com/gfs-bifrost/snap-adapter/pull/248) (FUSE-1195) has merge conflicts, failing CI and changes requested: what is the plan to unblock it?
- [observability#56](https://github.com/gfs-bifrost/observability/pull/56) and [collector#121](https://github.com/gfs-bifrost/collector/pull/121) both have merge conflicts: rebase order
- [config-service#206](https://github.com/gfs-bifrost/config-service/pull/206) (FUSE-1078) is conflicted, red and 20d idle: rebase and fix, or close?
- [snap-adapter#170](https://github.com/gfs-bifrost/snap-adapter/pull/170) and [pkg-node#201](https://github.com/gfs-bifrost/pkg-node/pull/201) have sat idle for 55 days: finish or close?
- Book the start-of-year PDR meeting
- Distraction Duty: the #bifrost-general topic reads "W/C 5 Oct: Humby" but Jira FUSE-1238 is still assigned to me. Confirm, and reassign the ticket if it is his
- [FUSE-1160](https://globalfreight.atlassian.net/browse/FUSE-1160) is in Code Review with no PR: where is it?

### Carried from last time
- [ ] Confirm his 23–25 Sept holiday request was actually approved (never confirmed closed)
- [ ] Chase his "IMS Basic Course 2026" training

### Notes
- ✍️

## 2026-10-01
_11:30–12:00 · Microsoft Teams · ⚠️ no agenda_

### Context

**Open PRs**
- [config-service#206](https://github.com/gfs-bifrost/config-service/pull/206) (FUSE-1078) — 🔴 merge conflicts + CI failing, open 20d, idle 16d
- [snap-adapter#170](https://github.com/gfs-bifrost/snap-adapter/pull/170) and [pkg-node#201](https://github.com/gfs-bifrost/pkg-node/pull/201) (FUSE-1078) — drafts, idle 51d
- [snap-adapter#248](https://github.com/gfs-bifrost/snap-adapter/pull/248) and [observability#56](https://github.com/gfs-bifrost/observability/pull/56) (FUSE-1195) — drafts; snap-adapter#248's checks are red on the fleet-wide audit and image scan

**Owed by you**
- A go/no-go on backfilling the Shopify "Line item has no fulfillment ID" orders (about 15 stuck, about 116 created this way). He asked on 09-30 and got a holding reply

### To raise
- config-service#206 (FUSE-1078): rebase and fix CI, or close?
- The 51-day drafts snap-adapter#170 and pkg-node#201: dead, or superseded by [snap-adapter#264](https://github.com/gfs-bifrost/snap-adapter/pull/264)?
- FUSE-1195 now has two drafts, both quiet
- IMS Basic Course 2026 training is still unchecked, and confirm the 23–25 Sep holiday was closed out
- (added 2026-10-02) [snap-adapter#248](https://github.com/gfs-bifrost/snap-adapter/pull/248) (FUSE-1195) is out of draft and blocked: merge conflicts, plus red audit and image-scan legs
- (added 2026-10-02) [snap-adapter#271](https://github.com/gfs-bifrost/snap-adapter/pull/271) (axios and grpc-js override floors) has no ticket
- (added 2026-10-02) Hold his start-of-year PDR meeting (Kate Meadows' 10-01 email)

### Carried from last time
- [ ] Confirm his 23–25 Sept holiday request was actually approved (never confirmed closed)
- [ ] Chase his "IMS Basic Course 2026" training

### Notes
- ✍️

## 2026-09-24
_no meeting today_

### Context

**Open PRs**
- [config-service#206](https://github.com/gfs-bifrost/config-service/pull/206) (FUSE-1078) — 🔴 merge conflicts + CI failing, now idle 9d (open 13d)
- [snap-adapter#170](https://github.com/gfs-bifrost/snap-adapter/pull/170) + [pkg-node#201](https://github.com/gfs-bifrost/pkg-node/pull/201) (FUSE-1078) — both drafts, idle 44d
- [snap-adapter#244](https://github.com/gfs-bifrost/snap-adapter/pull/244) (FUSE-1192) — new 🔴 merge conflict

**To raise**
- FUSE-1078 now has 4 open PRs against it, one blocked 9d and two drafts untouched 44 days — worth checking whether this ticket has stalled or just needs a push to close out
- Snap Poller stock-sync stack (FUSE-1192/1193/1195) picking up pace — 5 PRs open across pkg-node/snap-adapter this week, two already approved

### To raise
- (added 2026-09-30) [config-service#206](https://github.com/gfs-bifrost/config-service/pull/206) (FUSE-1078) has merge conflicts and red CI, 15d idle. His drafts [snap-adapter#170](https://github.com/gfs-bifrost/snap-adapter/pull/170) and [pkg-node#201](https://github.com/gfs-bifrost/pkg-node/pull/201) are 50d idle: finish or close? [snap-adapter#248](https://github.com/gfs-bifrost/snap-adapter/pull/248) (FUSE-1195) is a draft with no checks run

### Notes
- ✍️

## 2026-09-23
_no meeting today_

### Context

**Open PRs**
- [config-service#206](https://github.com/gfs-bifrost/config-service/pull/206) (FUSE-1078) — 🔴 merge conflicts + CI failing, idle 8d
- [snap-adapter#244](https://github.com/gfs-bifrost/snap-adapter/pull/244) (FUSE-1192) — 🔴 merge conflicts, opened today

### To raise
- His 23–25 Sept holiday (carried unresolved on 09-17) covers today — if he's out, these two blocked PRs are worth flagging as waiting for him rather than chasing today
- Two PRs now blocked on conflicts — worth a nudge on rebase order once he's back, since #244 conflicted same-day it opened

### Carried from last time
- [ ] Confirm his 23–25 Sept holiday request was actually approved (never confirmed closed)
- [ ] Chase his "IMS Basic Course 2026" training

### Notes
- ✍️

## 2026-09-17
_10:30–11:00 · Microsoft Teams · ⚠️ no agenda_

### Context

**Open PRs**
- 7 fresh FUSE-1078 drafts, all CI-green, all idle 1d: [replay-service#87](https://github.com/gfs-bifrost/replay-service/pull/87), [dedupe-service#146](https://github.com/gfs-bifrost/dedupe-service/pull/146), [snap-adapter#230](https://github.com/gfs-bifrost/snap-adapter/pull/230), [shopify-connector#266](https://github.com/gfs-bifrost/shopify-connector/pull/266), [sftp-connector#268](https://github.com/gfs-bifrost/sftp-connector/pull/268), [fapi#133](https://github.com/gfs-bifrost/fapi/pull/133), [fuse-ui#250](https://github.com/gfs-bifrost/fuse-ui/pull/250)

### To raise
- All 7 drafts landed at once, all green — worth asking if they're ready to come out together, or whether they're deliberately staged
- Holiday 23–25 Sep — confirm this got approved last time, still shows unchecked
- Overdue IMS Basic Course 2026 training

### Carried from last time
- [ ] Approve/reject his Holiday Approval Required request for 23–25 Sept
- [ ] Chase his "IMS Basic Course 2026" training

### Notes
- ✍️ 

## 2026-09-10
_13:00–13:30 · Microsoft Teams_

### Context

**Open PRs**
- [fuse-ui#217](https://github.com/gfs-bifrost/fuse-ui/pull/217) — [FUSE-1078](https://globalfreight.atlassian.net/browse/FUSE-1078) — 🔴 merge conflicts + Terraform Plan/terragrunt red, 7d idle (⚠️ stale)
- [pkg-node#201](https://github.com/gfs-bifrost/pkg-node/pull/201) + [snap-adapter#170](https://github.com/gfs-bifrost/snap-adapter/pull/170) — FUSE-1078 drafts, 23d idle
- [fuse-ui#245](https://github.com/gfs-bifrost/fuse-ui/pull/245) + [replay-service#82](https://github.com/gfs-bifrost/replay-service/pull/82) — fresh drafts (0–1d)

### To raise
- His holiday 23–25 Sep — approve/reject in the 1:1 (still pending my action)
- The evidence-expectations pattern — fuse-ui#217 red for 7d, two 23d-idle drafts still parked
- Overdue IMS Basic Course 2026 training

### Carried from last time
- (09-03 section had no unchecked action items)

### Notes
- ✍️ 

## 2026-09-03
_10:30–11:00 · Microsoft Teams · ⚠️ no agenda_

### Context

**Open PRs**
- [dedupe-service#129](https://github.com/gfs-bifrost/dedupe-service/pull/129) — [FUSE-1078](https://globalfreight.atlassian.net/browse/FUSE-1078) — 🔵 awaiting review, CI green, idle 2d
- [replay-service#78](https://github.com/gfs-bifrost/replay-service/pull/78) — [FUSE-1078](https://globalfreight.atlassian.net/browse/FUSE-1078) — 🔵 awaiting review, CI green, idle 2d
- [fuse-ui#217](https://github.com/gfs-bifrost/fuse-ui/pull/217) — [FUSE-1078](https://globalfreight.atlassian.net/browse/FUSE-1078) — 🔴 blocked, CI failing (Terraform Plan / terragrunt), idle 2d
- [shopify-connector#229](https://github.com/gfs-bifrost/shopify-connector/pull/229) — [FUSE-1054](https://globalfreight.atlassian.net/browse/FUSE-1054) — 🔴 blocked, CI failing (image_scan, dependency_audit_app), idle 5d — same leg as the fleet-wide overnight DevSecOps failure

**Active Jira**
- [FUSE-1054](https://globalfreight.atlassian.net/browse/FUSE-1054) [Snap + Connectors] Publish PO/SO confirmations onto the cross-entity confirmation_ready/made vein (Code Review)
- [FUSE-1069](https://globalfreight.atlassian.net/browse/FUSE-1069) [FUSE-UI] Surface structured failure errors in the retry queue detail (Ready for Refinement)

**To raise**
- Two PRs (dedupe-service#129, replay-service#78) are green and just waiting on a reviewer — worth finding him one if nothing's moving
- fuse-ui#217's Terraform Plan failure is worth a quick look — distinct from the DevSecOps leg failing elsewhere, so may be a real issue in that branch
- shopify-connector#229's failure matches the fleet-wide overnight DevSecOps Scans break (image_scan/dependency_audit) — probably not his to fix

### Carried from last time
- [ ] (none unchecked)

### Notes
- ✍️ 

## 2026-08-27
_10:30–11:00 · Microsoft Teams_

### Context

**Open PRs**
- [snap-adapter#197](https://github.com/gfs-bifrost/snap-adapter/pull/197) — fix(snap-queue-polling-service): emit only produced lines on a finished good receipt (FUSE-871)
- [snap-adapter#196](https://github.com/gfs-bifrost/snap-adapter/pull/196) — [FUSE-1009] Scope the goods-out StU read to the consignment
- [shopify-connector#229](https://github.com/gfs-bifrost/shopify-connector/pull/229) — FUSE-1054: dual-publish SO made confirmations onto confirmation_made

**Active Jira**
- [FUSE-1069](https://globalfreight.atlassian.net/browse/FUSE-1069) [FUSE-UI] Surface structured failure errors (field + reason) in the retry queue detail (Ready for Refinement)
- [FUSE-1054](https://globalfreight.atlassian.net/browse/FUSE-1054) [Snap + Connectors] Publish PO/SO confirmations onto the cross-entity confirmation_ready/made vein (In Progress)
- [FUSE-1009](https://globalfreight.atlassian.net/browse/FUSE-1009) [Snap Poller] Goods-out confirmation consignments ship with empty weight & dimensions (In Progress)

### Notes
- ✍️ 

## 2026-08-20
_10:30–11:00 · Microsoft Teams · ⚠️ no agenda_

### Context

**Open PRs** (all currently drafts)
- [pkg-node#201](https://github.com/gfs-bifrost/pkg-node/pull/201) — [FUSE-1078](https://globalfreight.atlassian.net/browse/FUSE-1078) reject a text body on a Snap write — 🟠 draft, CI green 8/8, idle 8d — worth a nudge to mark ready
- [snap-adapter#180](https://github.com/gfs-bifrost/snap-adapter/pull/180) — [FUSE-1062](https://globalfreight.atlassian.net/browse/FUSE-1062) clear WOC from the Snap outbound queue — 🟠 draft, CI green 21/21, idle 5d — worth a nudge to mark ready
- [snap-adapter#170](https://github.com/gfs-bifrost/snap-adapter/pull/170) — FUSE-1078 assert every Snap create response — 🟠 draft, CI failing (Matrix audit, Matrix lint), idle 8d
- [fuse-ui#210](https://github.com/gfs-bifrost/fuse-ui/pull/210) — [FUSE-1029](https://globalfreight.atlassian.net/browse/FUSE-1029) surface WO/WOC/FGR failures in the Retry Queue — 🟠 draft, CI green 11/11, idle 3d — fresh

**Active Jira**
- [FUSE-1028](https://globalfreight.atlassian.net/browse/FUSE-1028) — [Collector] Collect FGR and WOC messages (Ready for QA)
- [FUSE-1032](https://globalfreight.atlassian.net/browse/FUSE-1032) — [Replay] Subscribe to and save WO/WOC/FGR failures (Ready for QA)
- [FUSE-871](https://globalfreight.atlassian.net/browse/FUSE-871) — [SFTP] Write Finished Good Receipts (Ready for QA)

**To raise**
- Good news to lead with: all three active tickets (FUSE-1028/1032/871) are now sitting at Ready for QA
- Two CI-green drafts (pkg-node#201 at 8d, snap-adapter#180 at 5d) are worth marking ready if actually done
- snap-adapter#170 is CI-red on Matrix audit/lint — worth understanding whether that's a real failure or the fleet-wide platform issue before he pushes more on the stack

### Carried from last time
- [ ] (none unchecked)

### Notes
- ✍️ 

## 2026-08-13
_10:30–11:00 · Microsoft Teams · ⚠️ no agenda_

### Context

**Open PRs**
- [snap-mcp#13](https://github.com/gfs-bifrost/snap-mcp/pull/13) — [FUSE-1078](https://globalfreight.atlassian.net/browse/FUSE-1078) — 🟢 approved, mergeable, CI green — ready to merge
- [sftp-connector#246](https://github.com/gfs-bifrost/sftp-connector/pull/246) — [FUSE-722](https://globalfreight.atlassian.net/browse/FUSE-722) enable dynamic confirmation mapping in prod — 🟢 approved, mergeable, CI green — ready to merge
- [sftp-connector#244](https://github.com/gfs-bifrost/sftp-connector/pull/244) — FUSE-1078 discard empty CSV rows — 🔴 CI failing (image_scan)
- [shopify-connector#190](https://github.com/gfs-bifrost/shopify-connector/pull/190) — FUSE-1078 js-yaml override floor — 🔴 CI failing (Matrix (test))
- 4 more open (pkg-node#201, snap-adapter#170, replay-service#69, fuse-ui#207) — all drafts, capped here at the top 4 by state

**Active Jira**
- [FUSE-1078](https://globalfreight.atlassian.net/browse/FUSE-1078) — Distraction Duty log, still his active sprint work

**To raise**
- Two of his PRs ready to merge today (snap-mcp#13, sftp-connector#246) — good news to lead with
- sftp-connector#244 and shopify-connector#190 are both CI-red on real check failures (image_scan / Matrix test), not mechanical — worth understanding what's failing before he pushes more on the stack
- His PR count in-flight (8 open, mostly FUSE-1078) is climbing — worth checking he isn't blocked waiting on reviews rather than genuinely still working all of them

### Carried from last time
- [ ] (none unchecked)

### Notes
- ✍️ 

## 2026-08-06
_11:30–12:00 · MS Teams · ⚠️ no agenda · ⚠️ overlaps Aether Whiteboard 11:30–12:00_

### Context

**Open PRs**
- [fuse-ui#199](https://github.com/gfs-bifrost/fuse-ui/pull/199) — [FUSE-1078](https://globalfreight.atlassian.net/browse/FUSE-1078) — 🟢 approved, mergeable, CI green — ready to merge
- [fuse-ui#200](https://github.com/gfs-bifrost/fuse-ui/pull/200) — FUSE-1078, "stop logging Next redirect control-flow as client errors" — 🔵 awaiting review, CI green
- [fuse-ui#180](https://github.com/gfs-bifrost/fuse-ui/pull/180) — 🔴 blocked, CI failing (Terraform Apply)
- [fuse-ui#181](https://github.com/gfs-bifrost/fuse-ui/pull/181), [#191](https://github.com/gfs-bifrost/fuse-ui/pull/191)–[#197](https://github.com/gfs-bifrost/fuse-ui/pull/197), [replay-service#56](https://github.com/gfs-bifrost/replay-service/pull/56)/[#57](https://github.com/gfs-bifrost/replay-service/pull/57)/[#60](https://github.com/gfs-bifrost/replay-service/pull/60)/[#63](https://github.com/gfs-bifrost/replay-service/pull/63)–[#66](https://github.com/gfs-bifrost/replay-service/pull/66) — FUSE-599 Retry Queue stack, all 🔵 awaiting review, CI green

**Active Jira**
- [FUSE-1078](https://globalfreight.atlassian.net/browse/FUSE-1078) — Distraction Duty log — he's been logging Renovate sweeps, the support Datadog doc, and connector credential audit trail work this sprint

**To raise**
- The support-team Datadog self-serve doc he wrote is done and reviewed (by Thomas Dunn and Matt Shaw) — good to close that loop and confirm scope was what he expected
- The FUSE-599 Retry Queue stack is now 9 PRs deep, all green — a good moment to plan a dedicated review pass rather than letting it grow further
- fuse-ui#199 is ready to merge today

### Carried from last time
- [ ] (none unchecked)

### Notes
- ✍️ 

## 2026-07-30
_11:30–12:00 · Teams · no agenda_

### Context

**Open PRs**
- [fuse-ui#180](https://github.com/gfs-bifrost/fuse-ui/pull/180) — UI consistency pass — 🟠 draft, screenshots "to follow", plus a failing `Terraform Apply / terragrunt` check (idle 2d)
- [fuse-ui#181](https://github.com/gfs-bifrost/fuse-ui/pull/181) — [FUSE-599](https://globalfreight.atlassian.net/browse/FUSE-599) Retry Queue triage worklist — 🟠 draft stacked on #180, screenshots pending (idle 2d)
- [sftp-connector#232](https://github.com/gfs-bifrost/sftp-connector/pull/232) merged 07-29 — the stuck `image_scan` finally cleared; acknowledge it landed

**Active Jira**
- None open-assigned — his work is currently PR-shaped

**To raise**
- **Evidence-expectations conversation** (carried a week): #180/#181 are still draft on the same screenshots-pending gap — agree what "evidence complete" looks like for UI PRs
- **ui-toolkit support proposal** (from 13/07 huddle) — still no decision, and [[Nylah Klasson]] is back mid-Aug; decide or drop

**Other context**
- No agenda on the invite (normal for a 1:1)

### Carried from last time
- [ ] (none unchecked)

### Notes
- ✍️ 

## 2026-07-23
_10:30–11:00 · Teams · no agenda_

### Context

**Open PRs**
- None currently open in today's sweep — [sftp-connector#213](https://github.com/gfs-bifrost/sftp-connector/pull/213) ([[FUSE-998]]) no longer appears (was 🟢 ready-to-merge, idle 4d as of 07-20) — confirm it landed.

**Active Jira**
- None in-progress by email lookup — his work is currently PR-shaped

**To raise**
- Confirm sftp-connector#213 merged (dropped out of the open sweep since last 1:1)
- Still no decision on the **ui-toolkit support proposal** (13/07 huddle) — him helping while [[Nylah Klasson]] is out til mid-Aug
- Close the loop on snap-queue#92 ([[FUSE-820]]) — dropped out of the sweep, likely merged

**Other context**
- No agenda on the invite (normal for a 1:1)

### Carried from last time
- [ ] (none unchecked)

### Notes
- ✍️ 

## 2026-07-16
_11:30–12:00 · Teams · no agenda_

### Context

**Open PRs**
- [replay-service#47](https://github.com/gfs-bifrost/replay-service/pull/47) — [[FUSE-902]] — approved, CI green, mergeable (🟢 ready)
- [replay-service#48](https://github.com/gfs-bifrost/replay-service/pull/48) — [[FUSE-903]] — approved, stacked on #47 (🟢 ready)
- [replay-service#49](https://github.com/gfs-bifrost/replay-service/pull/49) — [[FUSE-904]] — approved, stacked on #48 (🟢 ready)
- [fuse-ui#169](https://github.com/gfs-bifrost/fuse-ui/pull/169) — [[FUSE-905]] — approved, CI green, mergeable (🟢 ready)

**Active Jira**
- None in-progress by email lookup — work is PR-shaped

**To raise**
- His whole 4-PR stack is approved + green — agree merge order (replay #47→#48→#49, then fuse-ui#169) and who lands them
- He reviewed/approved [fuse-mcp#10](https://github.com/gfs-bifrost/fuse-mcp/pull/10) ([[Matt Shaw]], [[FUSE-894]]) — acknowledge the quick review turnaround
- **ui-toolkit support proposal** (from 13/07 leadership huddle): him helping on ui-toolkit given front-end aptitude while [[Nylah Klasson]] is out til mid-Aug — no formal decision yet; gauge interest, keep current priorities protected

**Other context**
- Last time's [fuse-ui#158](https://github.com/gfs-bifrost/fuse-ui/pull/158) ([[FUSE-988]] Test Mapping tab) merged 2026-07-09
- No agenda on the invite (normal for a 1:1)

### Carried from last time
- [ ] (none unchecked)

### Notes
- ✍️ 

## 2026-07-09
_11:30–12:00 · Teams · no agenda_

### Context

**Open PRs**
- [fuse-ui#158](https://github.com/gfs-bifrost/fuse-ui/pull/158) — [[FUSE-988]] Test Mapping tab (dry-run a sample CSV) — awaiting review, CI green (in today's #bifrost-forge PR status)

**Active Jira**
- None in-progress by email lookup — his work is currently PR-shaped (fuse-ui#158)

**To raise**
- ⚠️ This 11:30 slot double-books my [[Oli Denton]] "Hot girl walk" — sort which moves at the top of the call
- fuse-ui#158 review — ~1.3k-line PR (Test Mapping tab); agree a reviewer + timeline

**Other context**
- Last time's open items appear closed — snap-adapter#117 and replay #40/#43 are no longer in his open PRs; confirm they landed

### Carried from last time
- [ ] (none unchecked)

### Notes
- ✍️ 

## 2026-07-02
_11:30–12:00 · Teams · no agenda_

### Context

**Open PRs**
- [snap-adapter#117](https://github.com/gfs-bifrost/snap-adapter/pull/117) — [[FUSE-973]] — clean, all checks green; he added more evidence after my earlier question — awaiting my re-review/approval
- [replay-service#43](https://github.com/gfs-bifrost/replay-service/pull/43) — [[FUSE-733]] — CI red (image_scan container scan); declares it supersedes my [replay#40](https://github.com/gfs-bifrost/replay-service/pull/40)

**To raise**
- Decide replay #40 vs #43 — his #43 supersedes my #40; both fail the same shared `image_scan` — agree who fixes the base-image advisory and close #40
- Approve snap-adapter#117 once I've re-read the evidence he added

### Carried from last time
- [ ] (none unchecked)

### Notes
- ✍️ 

## 2026-06-25
_11:30–12:00 · Teams · no agenda_

### Context

**Active Jira**
- [[FUSE-820]] [↗](https://globalfreight.atlassian.net/browse/FUSE-820) [Snap Polling] Create RGA confirmations + handle receipt confirmations (In Progress)

**Other context**
- [[FUSE-772]] (prod Datadog metrics) looks resolved — no longer in his active list; the datadog-integration#4 PR has likely merged
- Possible thread: this week's recurring prod error-rate / Snap-latency alerts touch the Datadog observability he set up

### Notes
- ✍️ 

## 2026-06-18

### Context

**Open PRs**
- [datadog-integration#4](https://github.com/gfs-bifrost/datadog-integration/pull/4) — [[FUSE-772]]: fix prod Datadog-integration deploy (runner SA + prod tfstate bucket)

**Active Jira**
- [[FUSE-820]] [↗](https://globalfreight.atlassian.net/browse/FUSE-820) [Snap Polling] Create RGA confirmations + handle receipt confirmations (In Progress)
- [[FUSE-772]] [↗](https://globalfreight.atlassian.net/browse/FUSE-772) [Observability] Ensure prod metrics flow into Datadog (Code Review — matches PR #4)

**Other context**
- Has been editing the Fuse changelog Confluence pages this week (Confluence daily digest)
- No agenda on the invite (normal for a 1:1)

### Notes
- ✍️ 
