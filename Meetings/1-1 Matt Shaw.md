---
tags: [meeting]
series: 1-1 Matt Shaw
counterpart: "[[Matt Shaw]]"
title: 1-1 Matt Shaw
---
# 1-1 Matt Shaw

## 2026-11-03
_10:30–11:00 GMT · Teams / Slack huddle · ⚠️ no agenda (normal for a 1:1) · ⚠️ Matt is on leave 2 to 4 Nov and the slot clashes with the Northstar all-hands · [event](https://outlook.office365.com/owa/?itemid=AAkBOQAICN85PWdfgAAuAAAAAB2EAxGqZhHNm8gAqgAvxFoNAAEuyBCkV09NrJc5lNWutosAAANLx5iUAABA%3D&exvsurl=1&path=/calendar/item)_

### Context

**Open PRs**
- [fapi#181](https://github.com/gfs-bifrost/fapi/pull/181) — [FUSE-1324](https://globalfreight.atlassian.net/browse/FUSE-1324) — approved, green, mergeable, idle 6d
- [shopify-connector#351](https://github.com/gfs-bifrost/shopify-connector/pull/351) — FUSE-1324 — approved, green, mergeable, idle 6d
- [dedupe-service#165](https://github.com/gfs-bifrost/dedupe-service/pull/165) — FUSE-1324 — merge conflicts
- FUSE-1314 duty drafts: [collector#131](https://github.com/gfs-bifrost/collector/pull/131), [fuse-mocker#35](https://github.com/gfs-bifrost/fuse-mocker/pull/35), [fapi#182](https://github.com/gfs-bifrost/fapi/pull/182) and [dedupe-service#166](https://github.com/gfs-bifrost/dedupe-service/pull/166) (all CI-green drafts, 6d idle; snap-adapter#311 merged via Schuster)

**Active Jira**
- [FUSE-1324](https://globalfreight.atlassian.net/browse/FUSE-1324) Redis hang (Code Review)
- [FUSE-1314](https://globalfreight.atlassian.net/browse/FUSE-1314) Sprint 16 Distraction Duty (In Progress)

**Owed by you**
- Approve his holiday request for 2–4 Nov (3 days) — starts Monday
- Approve his access request to the "Fuse EDI Evidence" artifact (10-06, still open 10-08)
- Sign and send on his start-of-year PDR once he finishes the form
- Sequence the confirmation defects he triaged (FUSE-1272, 1273, 1274, 1276, 1281 backlog; 1275 and 1280 are L2 mapping fixes) — [group DM](https://gfsdeliver-eng.slack.com/archives/C0BC33H8QMT/p1790783612714759) — 10-05: FUSE-1281 is Done, 1272 is Ready for QA, 1275/1280 are Schuster's; 1273, 1274 and 1276 are left to order at the 10:00 standup
- Assign and prioritise FUSE-1272 to FUSE-1276, the QA defects he raised from Tom Dunn's list
- Agree the next-rules-engine-publish plan now that he's merged [pkg-node#240](https://github.com/gfs-bifrost/pkg-node/pull/240) (peer floor `>=10.5.0` re-breaks sftp-connector on `types` ^9.5)
- Ask where the FUSE-995 diff actually lives — Code Review status but no open PR against it in the sweep for a full week now
- Review his FUSE-995 structured-logging stack — 6 PRs across 5 repos, all 🔵 needs-review, CI green: [replay-service#84](https://github.com/gfs-bifrost/replay-service/pull/84), [shopify-connector#256](https://github.com/gfs-bifrost/shopify-connector/pull/256)/[#257](https://github.com/gfs-bifrost/shopify-connector/pull/257)/[#263](https://github.com/gfs-bifrost/shopify-connector/pull/263), [sftp-connector#267](https://github.com/gfs-bifrost/sftp-connector/pull/267), [fapi#136](https://github.com/gfs-bifrost/fapi/pull/136)
- Review his 5 green PRs awaiting review
- Ask why 7 approved/green/mergeable PRs (replay-service#56/57/60/63/65/66, fuse-ui#191) are sitting unmerged 3d
- Answer his #bifrost-private question — scope the nightly gitleaks/secops scan to `main` only? He says a decision might unblock nightlies (carried ×5 since 07-21)
- Take him up on his offer to review my PRs
- FUSE-999 catch-up **today in the office** — he has early findings on the blockers, and I promised to share where I think the perf issue is
- Pre-review his FUSE-999/1012 pkg-node stack [#178–#182](https://github.com/gfs-bifrost/pkg-node/pulls) + [fapi#90](https://github.com/gfs-bifrost/fapi/pull/90) before wider review (carried ×3)
- Review [pkg-node#174](https://github.com/gfs-bifrost/pkg-node/pull/174) (FUSE-999) — CI green, awaiting review
- Resolve the merge conflicts on [fuse-ui#166](https://github.com/gfs-bifrost/fuse-ui/pull/166) (8d idle, ⚠️ stale) + [fuse-ui#170](https://github.com/gfs-bifrost/fuse-ui/pull/170) (7d idle, ⚠️ stale) — both still draft

**Other context**
- On leave 2 to 4 Nov; the holiday request still has no approval seen in any source
- A Spectrum IT recruiter CV for a Senior Developer shares his name (cc'd to him), so check it is not a mix-up; Monday's leadership catch-up agreed he gets final say on candidates and is read in on strategy

### To raise
- [ ] Who covers Distraction Duty while he is away, and which of the duty drafts should merge or close
- [ ] Is the FUSE-792 Get Stock API ready for Thomas Dunn to test? (carried ×1)
- [ ] pkg-node#282 is the last of the `types` v11 train and the five red majors are open: what does he want to do about fapi#178, dedupe-service#163, snap-adapter#302, sftp-connector#315 and fuse-mocker#34? (carried ×1)
- [ ] Where do the draft advisory-fix PRs stand, and which red repos (config-service, fuse-ui, fuse-mcp, secrets-hub, shopify-connector, snap-mcp) have no fix PR yet? (carried ×1)
- [ ] FUSE-1296 (stock sync QA, Ready for QA, unassigned): who runs it? (carried ×2)
- [ ] I will refine and estimate the webhook epic and the status webhook so he can lead it. Does he want to? (carried ×2)
- [ ] Is his start-of-year PDR form ready to sign? (carried ×3)

### Carried from last time
- [ ] (nothing recorded)

### Notes
- ✍️ 

## 2026-10-27
_10:30–11:00 GMT · Teams / Epsilon House / Slack huddle · ⚠️ no agenda (normal for a 1:1) · [event](https://outlook.office365.com/owa/?itemid=AAkBOQAICN8zvT57QAAuAAAAAB2EAxGqZhHNm8gAqgAvxFoNAANLx5iUAABA%3D&exvsurl=1&path=/calendar/item)_

### Context

**Open PRs**
- [fapi#181](https://github.com/gfs-bifrost/fapi/pull/181), [shopify-connector#351](https://github.com/gfs-bifrost/shopify-connector/pull/351), [dedupe-service#165](https://github.com/gfs-bifrost/dedupe-service/pull/165) — https://globalfreight.atlassian.net/browse/FUSE-1324 stack, awaiting review, CI green, idle 2d
- [fapi#182](https://github.com/gfs-bifrost/fapi/pull/182), [collector#131](https://github.com/gfs-bifrost/collector/pull/131), [snap-adapter#311](https://github.com/gfs-bifrost/snap-adapter/pull/311), [dedupe-service#166](https://github.com/gfs-bifrost/dedupe-service/pull/166), [fuse-mocker#35](https://github.com/gfs-bifrost/fuse-mocker/pull/35) — Distraction Duty advisory fixes, drafts, CI green

**Active Jira**
- [FUSE-1324](https://globalfreight.atlassian.net/browse/FUSE-1324) [Cache] Network cache writes and deletes hang forever when Redis is unreachable (Code Review)
- [FUSE-1314](https://globalfreight.atlassian.net/browse/FUSE-1314) [Sprint 16] Distraction Duty (In Progress; he took it from Schuster on Mon 26 Oct)

**Owed by you**
- Approve his holiday request for 2 to 4 Nov (Selima email waiting since Mon 16:30)
- Hear his agency engineering candidate (about £70K) before he progresses it
- Review his FUSE-1324 PRs
- Place [FUSE-1296](https://globalfreight.atlassian.net/browse/FUSE-1296) (Ready for QA, unassigned)

**Other context**
- He merged five of the six green `types` ^11.2.0 Renovate majors on Monday (wms-gateway, collector, shopify-connector, replay-service, fuse-ui); pkg-node#282 is still open
- Jack's Monday huddle notes: he wants Orion, the support bot and the PR skill tooling shared before the Merak transition
- Thomas Dunn asked him on Monday whether FUSE-792 (Get Stock API) is ready to test

### To raise
- [ ] Is the FUSE-792 Get Stock API ready for Thomas Dunn to test?
- [ ] pkg-node#282 is the last of the `types` v11 train and the five red majors are open: what does he want to do about fapi#178, dedupe-service#163, snap-adapter#302, sftp-connector#315 and fuse-mocker#34?
- [ ] Where do the draft advisory-fix PRs stand, and which red repos (config-service, fuse-ui, fuse-mcp, secrets-hub, shopify-connector, snap-mcp) have no fix PR yet?
- [ ] FUSE-1296 (stock sync QA, Ready for QA, unassigned): who runs it? (carried ×1)
- [ ] I will refine and estimate the webhook epic and the status webhook so he can lead it. Does he want to? (carried ×1)
- [ ] Is his start-of-year PDR form ready to sign? (carried ×2)

### Carried from last time
- [ ] Reply to his muninn-huginn SDK cookbook DM (open since 07-14; check it isn't already superseded)

### Notes
- ✍️ 

## 2026-10-20
_10:30–11:00 BST · Teams / Epsilon House / Slack huddle · ⚠️ no agenda (normal for a 1:1) · [event](https://outlook.office365.com/owa/?itemid=AAkBOQAICN8uPRWXAAAuAAAAAB2EAxGqZhHNm8gAqgAvxFoNAAEuyBCkV09NrJc5lNWutosAANLx5iUAABA%3D&exvsurl=1&path=/calendar/item)_

### Context

**Open PRs**
- Nothing open: his FUSE-1300 work has no PR yet

**Active Jira**
- [FUSE-1300](https://globalfreight.atlassian.net/browse/FUSE-1300) [Config] Persist and validate the SFTP stock sync schedule and stock_sync mapping (In Progress, no open PR)

**Owed by you**
- Place [FUSE-1296](https://globalfreight.atlassian.net/browse/FUSE-1296) (Ready for QA, the only in-flight ticket with no assignee)
- Approve his access request to the "Fuse EDI Evidence" artifact
- Sign and send on his start-of-year PDR once he finishes the form
- Sequence the confirmation defects he triaged (FUSE-1272, 1273, 1274, 1276, 1281)

**Other context**
- His comment on FUSE-1300: FUSE-1299 publishes `@gfs-bifrost/types` as a major (11.0.0, or 12.0.0 if FUSE-1277 publishes first), so config-service will not compile until `stock_sync: undefined` is added to its `ConnectorConfigService` literals
- He wants the types bump to merge last, after fapi, shopify-connector, sftp-connector, snap-adapter and the poller have moved
- The 11.0.0 Renovate PRs opened overnight in 12 repos; config-service#244 and sftp-connector#315 are red on the new key
- Yesterday's stock sync catch-up gave him one QA check: multiple Shopify connectors on one store must not cause duplicate stock mutations

### To raise
- [ ] FUSE-1299/1300/1302: agree the merge order for the types 11.0.0 train, with config-service last and shopify-connector held while the prod stall is open
- [ ] FUSE-1296 (stock sync QA, Ready for QA, unassigned): who runs it?
- [ ] I will refine and estimate the webhook epic and the status webhook so he can lead it. Does he want to?
- [ ] Is his start-of-year PDR form ready to sign? (carried ×1)

### Carried from last time
- [ ] Reply to his muninn-huginn SDK cookbook DM (open since 07-14; check it isn't already superseded)

### Notes
- ✍️ 

## 2026-10-13
_10:30–11:00 BST · Teams / Epsilon House / Slack huddle · ⚠️ no agenda (normal for a 1:1) · [event](https://outlook.office365.com/owa/?itemid=AAkBOQAICN8ovOyywAAuAAAAAB2EAxGqZhHNm8gAqgAvxFoNAAEuyBCkV09NrJc5lNWutosAANLx5iUAABA%3D&exvsurl=1&path=/calendar/item)_

### Context

**Open PRs**
- [observability#62](https://github.com/gfs-bifrost/observability/pull/62) — [FUSE-1198](https://globalfreight.atlassian.net/browse/FUSE-1198) — draft, idle 4d

**Active Jira**
- [FUSE-1292](https://globalfreight.atlassian.net/browse/FUSE-1292) [Snap] Spike: load-test how Snap responds to Shopify stock sync (In Progress)
- FUSE-1292 has no open PR, which is normal for a spike
- [FUSE-1198](https://globalfreight.atlassian.net/browse/FUSE-1198) held 1d, with observability#62 as its only open PR

**Owed by you**
- Answer [[Lee Simmons]]: does the blank SFTP status-mapping fix apply to all SFTP customers or only Byoma?
- Approve his holiday for 9 and 12 Oct, still pending in the HR system
- Sign his start-of-year PDR form
- Approve his artifact access request for Fuse EDI Evidence

**Other context**
- He traced the blank SFTP status column behind the goods-in confirmation change
- The goods-in confirmation change ships Mon 19 Oct

### To raise
- What did his trace of the blank SFTP status column show: does the fix apply to every SFTP customer or only Byoma? I need it to answer Lee Simmons today
- FUSE-1292: what does the load-test spike need to show, and when does it report back?
- FUSE-1198: [observability#62](https://github.com/gfs-bifrost/observability/pull/62) has sat as a draft for 4 idle days: what is left?
- Is his start-of-year PDR form ready to sign?

### Carried from last time
- [ ] Reply to his muninn-huginn SDK cookbook DM (open since 07-14; check it isn't already superseded)

### Notes
- ✍️ 

## 2026-10-12
_no meeting today_ (off today, 12 Oct)

### To raise
- He has no in-progress sprint ticket. His only open work is [observability#62](https://github.com/gfs-bifrost/observability/pull/62), a 4d draft on FUSE-1198: what is he on, and are his sprint tickets being moved through Jira?
- His holiday for 9 and 12 Oct is still pending approval
- His PDR form needs signing

### Carried from last time
- [ ] Reply to his muninn-huginn SDK cookbook DM (open since 07-14; check it isn't already superseded)

### Notes
- ✍️

## 2026-10-08
_no meeting today_

### To raise
- [FUSE-1198](https://globalfreight.atlassian.net/browse/FUSE-1198) is a stack of 8 draft PRs ([shopify-connector#305](https://github.com/gfs-bifrost/shopify-connector/pull/305), [#311](https://github.com/gfs-bifrost/shopify-connector/pull/311), [#312](https://github.com/gfs-bifrost/shopify-connector/pull/312), [#314](https://github.com/gfs-bifrost/shopify-connector/pull/314), [#315](https://github.com/gfs-bifrost/shopify-connector/pull/315), [#316](https://github.com/gfs-bifrost/shopify-connector/pull/316), [#317](https://github.com/gfs-bifrost/shopify-connector/pull/317), [observability#62](https://github.com/gfs-bifrost/observability/pull/62)) and he hopes to close it out today
- [core-infra#15](https://github.com/gfs-bifrost/core-infra/pull/15) review: his bump on 10-06 has no replies
- Holiday requests for 9 Oct and 12 Oct are pending my approval
- His PDR form is waiting for my signature

### Carried from last time
- [ ] Reply to his muninn-huginn SDK cookbook DM (open since 07-14; check it isn't already superseded)

### Notes
- ✍️

## 2026-10-06
_10:30–11:00 BST · Teams / Epsilon House / Slack huddle · ⚠️ no agenda (normal for a 1:1) · [event](https://outlook.office365.com/owa/?itemid=AAkBOQAICN8jPMPOgAAuAAAAAB2EAxGqZhHNm8gAqgAvxFoNAAEuyBCkV09NrJc5lNWutosAANLx5iUAABA%3D&exvsurl=1&path=/calendar/item)_

### Context

**Open PRs**
- [shopify-connector#305](https://github.com/gfs-bifrost/shopify-connector/pull/305) — [FUSE-1198](https://globalfreight.atlassian.net/browse/FUSE-1198) — draft, idle 3d

**Active Jira**
- [FUSE-1283](https://globalfreight.atlassian.net/browse/FUSE-1283) [Shopify] Move the Shopify apps to Admin API 2026-04 (Code Review; [shopify-connector#309](https://github.com/gfs-bifrost/shopify-connector/pull/309) merged yesterday 13:35Z, so no open PR now)
- [FUSE-1198](https://globalfreight.atlassian.net/browse/FUSE-1198) [Egress] Consume, bulk-update Shopify inventory, and confirm stock sync, happy path (In Progress, held 5d)

**Other context**
- He is cc'd on Ryan Ellis's "Snap production capacity ahead of stock sync" thread, where the stock-sync rollout and DB5 strain are the subject, a likely topic
- The 10:00 standup comes first and its order for FUSE-1273, FUSE-1274 and FUSE-1276 is still open

**Owed by you**
- Order FUSE-1273, FUSE-1274 and FUSE-1276 with him and [[Tom Dunn]] at the 10:00 standup (open since 09-30)
- Sign and send on his start-of-year PDR once he finishes the form (Kate Meadows' 10-01 email)

### To raise
- FUSE-1283 merged yesterday: what is left before QA and Shopify's 16 Oct cutover?
- FUSE-1198: [shopify-connector#305](https://github.com/gfs-bifrost/shopify-connector/pull/305) is still a draft with 3 idle days: what is left?
- His view on Ryan Ellis's concern about Snap production capacity ahead of the stock sync
- Finish his start-of-year PDR form

### Carried from last time
- [ ] Reply to his muninn-huginn SDK cookbook DM (open since 07-14; check it isn't already superseded)

### Notes
- ✍️

## 2026-10-05
_no meeting today · next 1:1 tomorrow 10:30_

### Context

**Open PRs**
- [shopify-connector#305](https://github.com/gfs-bifrost/shopify-connector/pull/305) — [FUSE-1198](https://globalfreight.atlassian.net/browse/FUSE-1198) — draft, CI green 25/25, idle 2d
- [shopify-connector#309](https://github.com/gfs-bifrost/shopify-connector/pull/309) — [FUSE-1283](https://globalfreight.atlassian.net/browse/FUSE-1283) — draft, CI green 20/20, idle 2d

**Active Jira**
- [FUSE-1283](https://globalfreight.atlassian.net/browse/FUSE-1283) [Shopify] Move the Shopify apps to Admin API 2026-04 (In Progress, pointed and pulled into the sprint)
- Needed before Shopify's 16 Oct cutover
- [FUSE-1198](https://globalfreight.atlassian.net/browse/FUSE-1198) [Egress] Consume, bulk-update Shopify inventory, and confirm stock sync, happy path (In Progress, held 4d)

**Other context**
- [shopify-connector#306](https://github.com/gfs-bifrost/shopify-connector/pull/306) (FUSE-1282, bulk-query fix) merged 10-02
- FUSE-1282 is Done

**Owed by you**
- Order FUSE-1273, FUSE-1274 and FUSE-1276 with him and [[Tom Dunn]] at the 10:00 standup. He says the order is my call (open since 09-30)
- Sign and send on his start-of-year PDR once he finishes the form (Kate Meadows' 10-01 email)

### To raise
- FUSE-1283: what remains on the draft before the 16 Oct cutover?
- FUSE-1198: [shopify-connector#305](https://github.com/gfs-bifrost/shopify-connector/pull/305) is still a draft: what is left?
- Which of FUSE-1273, FUSE-1274 and FUSE-1276 go first after this morning's standup
- Finish his start-of-year PDR form

### Carried from last time
- [ ] Reply to his muninn-huginn SDK cookbook DM (open since 07-14; check it isn't already superseded)

### Notes
- ✍️

## 2026-09-29
_10:30–11:00 BST · Teams / Epsilon House / Slack huddle · ⚠️ no agenda (normal for a 1:1) · [event](https://outlook.office365.com/owa/?itemid=AAkBOQAICN8dvJrqQAAuAAAAAB2EAxGqZhHNm8gAqgAvxFoNAAEuyBCkV09NrJc5lNWutosAANLx5iUAABA%3D&exvsurl=1&path=/calendar/item)_

### Context

**Open PRs**
- None open. He merged [snap-adapter#259](https://github.com/gfs-bifrost/snap-adapter/pull/259) (stops logging serialised transport errors, which is the plaintext Basic-auth-in-logs finding) and [shopify-connector#286](https://github.com/gfs-bifrost/shopify-connector/pull/286) on 09-28, both under [FUSE-1238](https://globalfreight.atlassian.net/browse/FUSE-1238)

**Active Jira**
- [FUSE-1197](https://globalfreight.atlassian.net/browse/FUSE-1197) [Egress] Resolve Shopify connector config via remote-config (In Progress, held 4d, no PR yet)

**Owed by you**
- Assign and prioritise FUSE-1272 to FUSE-1276, the 5 QA defects he raised from Tom Dunn's list — [email](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAHBMDI8AAA%3D&exvsurl=1&viewmodel=ReadMessageItem)

**Other context**
- He ran Dock & Bay go-live prep while you were out: prod load on 09-28, a go-live dashboard, and 9 D1–D11 watch monitors
- He merged Renovate [pkg-node#240](https://github.com/gfs-bifrost/pkg-node/pull/240) on 09-28. It raises rules-engine's `types` peer floor to `>=10.5.0`, which re-breaks sftp-connector (still on `types` ^9.5) on the next rules-engine publish

### To raise
- pkg-node#240: rules-engine hasn't been republished yet (source is still 2.1.1). Agree who stops or sequences the next rules-engine publish, or who moves sftp-connector onto `types` 10.x first
- The 9 Dock & Bay watch monitors have no recipients and trip every morning on the overnight 4h zero-traffic window (all 9 were in Alert at 08:00). Retune them, add recipients, or delete them after go-live
- Monitor 303425509 (Shopify confirmation delivery) flapped about 73× in 24h, driven by one PURDYFIGG shipment `PURD133D2FB4FD8` looping on "Line item has no fulfillment ID". Who picks it up?
- FUSE-1197 has had no PR for 4 days. Is he blocked on the egress scaffold?
- Carried: snap-adapter#164 and shopify-connector#187, the untracked drafts from earlier. Are they still wanted?
- (added 2026-10-02) [FUSE-1198](https://globalfreight.atlassian.net/browse/FUSE-1198) (stock sync egress, happy path) is In Progress with no PR yet
- (added 2026-10-02) He needs to finish his start-of-year PDR form so you can sign it and send it on (Kate Meadows' 10-01 email)

### Carried from last time
- [ ] Reply to his muninn-huginn SDK cookbook DM (open since 07-14; check it isn't already superseded)

### Notes
- ✍️

## 2026-09-22
_09:30 · Teams/Slack huddle · ⚠️ no agenda_

### Context

**Open PRs**
- No open PR against his own active ticket — [FUSE-995](https://globalfreight.atlassian.net/browse/FUSE-995) has sat in Code Review with nothing attached for a week now
- Untracked drafts [snap-adapter#164](https://github.com/gfs-bifrost/snap-adapter/pull/164) + [shopify-connector#187](https://github.com/gfs-bifrost/shopify-connector/pull/187) — both now **47d idle**, no ticket key on either

**Active Jira**
- [FUSE-995](https://globalfreight.atlassian.net/browse/FUSE-995) [Observability] Adopt canonical structured-logging field spec across Fuse services — still Code Review, unchanged since 09-15

**To raise**
- FUSE-995 has been in Code Review a full week with no PR visible in the sweep — where does the actual diff live, and is it stuck on review or just not linked
- snap-adapter#164 / shopify-connector#187 now 47d idle — same open question as last time, getting more overdue: still wanted, or close them?
- Today's 11:30 Observability catch-up follows from his own talk (Signoz decision, capabilities used across dev teams) — good chance to align on what he wants to land there beforehand

### Carried from last time
- [ ] Reply to his muninn-huginn SDK cookbook DM — open since 07-14 (verify not already superseded)

### Notes
- ✍️ 

## 2026-09-15
_10:30 · Teams/Slack huddle · ⚠️ no agenda_

### Context

**Open PRs**
- [replay-service#84](https://github.com/gfs-bifrost/replay-service/pull/84) — [FUSE-995](https://globalfreight.atlassian.net/browse/FUSE-995) — 🔴 blocked, CI red on the fleet-wide DevSecOps `dependency_audit`/`image_scan` break (1d idle)
- Drafts: [shopify-connector#256](https://github.com/gfs-bifrost/shopify-connector/pull/256) (FUSE-995 1/2) + [#257](https://github.com/gfs-bifrost/shopify-connector/pull/257) (FUSE-995 2/2) — service-local log catalogues, both fresh (1d)
- Older drafts [shopify-connector#187](https://github.com/gfs-bifrost/shopify-connector/pull/187) + [snap-adapter#164](https://github.com/gfs-bifrost/snap-adapter/pull/164) now **29d idle**, still red on the same audit break — flagged since 08-06

**Active Jira**
- [FUSE-995](https://globalfreight.atlassian.net/browse/FUSE-995) [Observability] Adopt canonical structured-logging field spec across Fuse services — Code Review
- [FUSE-1078](https://globalfreight.atlassian.net/browse/FUSE-1078) [Sprint 14] Distraction Duty — In Progress (**his this sprint**)

**To raise**
- He's on Distraction Duty (FUSE-1078) — the fleet-wide DevSecOps `dependency_audit`/`image_scan` break is still red across 8 repos in the nightlies; carried on the todo for weeks — agree a plan to actually clear it, not just re-triage
- fuse-ui#184 has finally dropped off his open PRs — the month-long rebase saga looks resolved; confirm
- FUSE-995 structured-logging stack: replay-service#84 red on that same audit break, shopify#256/#257 the next slices — where's the whole thing landing
- shopify-connector#187 + snap-adapter#164 drafts now 29d idle, unchanged red CI — still wanted, or close them?

### Carried from last time
- [ ] Reply to his muninn-huginn SDK cookbook DM — open since 07-14 (verify not already superseded)

### Notes
- ✍️ 

## 2026-09-08
_09:30–10:00 · Teams/Slack huddle, Epsilon House · ⚠️ no agenda_

### Context

**Open PRs**
- [fuse-ui#184](https://github.com/gfs-bifrost/fuse-ui/pull/184) — FUSE-999 — 🔴 blocked, merge conflicts + CI failing, ⚠️ stale at **29d idle** — same rebase-only fix flagged since 08-11, now essentially a month old
- [fuse-ui#234](https://github.com/gfs-bifrost/fuse-ui/pull/234) — FUSE-999 — new 🔴, CI failing (docker-push-dev / build-push), 1d idle
- [observability#24](https://github.com/gfs-bifrost/observability/pull/24) — FUSE-999 — new 🔵, awaiting review, CI green, 1d idle
- Drafts still open: [shopify-connector#187](https://github.com/gfs-bifrost/shopify-connector/pull/187) (24d idle, CI red — image_scan/dependency_audit, unchanged since 08-25), [snap-adapter#164](https://github.com/gfs-bifrost/snap-adapter/pull/164) (24d idle, CI red, same story); new drafts [dedupe-service#135](https://github.com/gfs-bifrost/dedupe-service/pull/135) (1d, CI green 16/16), [pkg-node#221](https://github.com/gfs-bifrost/pkg-node/pull/221) (1d, CI green 8/8)

**Active Jira**
- [FUSE-999](https://globalfreight.atlassian.net/browse/FUSE-999) [Observability] Instrument fuse.* operational metrics — still In Progress

**To raise**
- fuse-ui#184 is now 29 days idle — same rebase-only fix flagged since 08-11; worth understanding the real blocker rather than assuming it resolves itself
- shopify-connector#187 and snap-adapter#164 drafts are both 24d idle with the same red CI unchanged since 08-25 — worth a direct check on whether these are still wanted
- New: dedupe-service#135 and pkg-node#221 opened as drafts, CI green — ask if these are close to ready for review
- fuse-ui#234's Docker build failure is fresh — quick to check

### Carried from last time
- [ ] Reply to his muninn-huginn SDK cookbook DM — open since 07-14 (verify not already superseded)

### Notes
- ✍️ 

## 2026-08-25
_10:30–11:00 BST · Teams · no agenda on invite (Teams join blob only, normal)_

### Context

**Open PRs**
- [fuse-ui#184](https://github.com/gfs-bifrost/fuse-ui/pull/184) — FUSE-999 — 🔴 blocked, merge conflicts + CI failing, ⚠️ stale at 19d idle — "N/A — no visual changes" Evidence section unchanged for weeks
- [dedupe-service#110](https://github.com/gfs-bifrost/dedupe-service/pull/110) — FUSE-999 — 🔴 blocked, merge conflicts, ⚠️ stale at 15d idle — still just needs a rebase
- Drafts still open: [shopify-connector#185](https://github.com/gfs-bifrost/shopify-connector/pull/185)/[#186](https://github.com/gfs-bifrost/shopify-connector/pull/186) (15d idle, CI green), [#187](https://github.com/gfs-bifrost/shopify-connector/pull/187) (14d idle, CI red), [snap-adapter#164](https://github.com/gfs-bifrost/snap-adapter/pull/164) (14d idle, CI red)

**Active Jira**
- [FUSE-999](https://globalfreight.atlassian.net/browse/FUSE-999) [Observability] Instrument fuse.* operational metrics — still In Progress
- [FUSE-1097](https://globalfreight.atlassian.net/browse/FUSE-1097) [Infra] Load-test the ingest chain to peak and agree a back-pressure contract — **new since last 1:1**, In Progress

**To raise**
- New ticket FUSE-1097 — what's the load-test/back-pressure scope, and how it lands relative to FUSE-999
- fuse-ui#184 and dedupe-service#110 have now sat 19d/15d — same rebase-only fix flagged for weeks; worth understanding what's blocking him from just doing it
- The 7 previously-flagged ready-to-merge PRs (replay-service#56 etc.) have dropped out of the open sweep — looks resolved, worth a quick confirm

### Carried from last time
- [ ] Reply to his muninn-huginn SDK cookbook DM — open since 07-14 (verify not already superseded)

### Notes
- ✍️ 

## 2026-08-11
_09:30 · Teams · no agenda on invite (Teams join blob only, normal)_

### Context

**Open PRs** (ticket key showing as FUSE-599 in today's sweep on the FUSE-999 stack — likely a ticket-key extraction glitch since FUSE-599 is the unrelated "Event Remediation & Replay" epic; content matches FUSE-999 metrics-adoption work, treat as FUSE-999 until confirmed)
- **7 PRs sitting 🟢 ready-to-merge, idle 3d**: [replay-service#56](https://github.com/gfs-bifrost/replay-service/pull/56)/[#57](https://github.com/gfs-bifrost/replay-service/pull/57)/[#60](https://github.com/gfs-bifrost/replay-service/pull/60)/[#63](https://github.com/gfs-bifrost/replay-service/pull/63)/[#65](https://github.com/gfs-bifrost/replay-service/pull/65)/[#66](https://github.com/gfs-bifrost/replay-service/pull/66), [fuse-ui#191](https://github.com/gfs-bifrost/fuse-ui/pull/191) — all approved, mergeable, CI green. Worth asking why these haven't gone in.
- [fuse-ui#184](https://github.com/gfs-bifrost/fuse-ui/pull/184) — still 🔴 blocked, merge conflicts + CI failing, now ⚠️ stale at 9d idle (was 6d on 08-06) — the "N/A — no visual changes" Evidence conversation is now overdue
- [dedupe-service#110](https://github.com/gfs-bifrost/dedupe-service/pull/110) — still 🔴 blocked, merge conflicts, idle 5d
- New 🔴: [fuse-ui#180](https://github.com/gfs-bifrost/fuse-ui/pull/180) (CI failing, Terraform Apply/terragrunt), [fuse-ui#181](https://github.com/gfs-bifrost/fuse-ui/pull/181) (changes requested), [replay-service#64](https://github.com/gfs-bifrost/replay-service/pull/64) (changes requested)
- New 🔵: [fuse-ui#192](https://github.com/gfs-bifrost/fuse-ui/pull/192)–[#197](https://github.com/gfs-bifrost/fuse-ui/pull/197), awaiting review, CI green, idle 4d
- Drafts still open: [shopify-connector#185](https://github.com/gfs-bifrost/shopify-connector/pull/185)/[#186](https://github.com/gfs-bifrost/shopify-connector/pull/186)/[#187](https://github.com/gfs-bifrost/shopify-connector/pull/187), [snap-adapter#164](https://github.com/gfs-bifrost/snap-adapter/pull/164)
- **New workstream**: [FUSE-1092](https://globalfreight.atlassian.net/browse/FUSE-1092) (Mongo ledger/watermark/lease + ingest FSM) — [#199](https://github.com/gfs-bifrost/shopify-connector/pull/199)/[#200](https://github.com/gfs-bifrost/shopify-connector/pull/200), Code Review; [FUSE-1093](https://globalfreight.atlassian.net/browse/FUSE-1093) (Shopify bulk-operation JSONL fetch) — [#202](https://github.com/gfs-bifrost/shopify-connector/pull/202)/[#203](https://github.com/gfs-bifrost/shopify-connector/pull/203)/[#204](https://github.com/gfs-bifrost/shopify-connector/pull/204), In Progress — all 5 🔵 awaiting review, CI green, idle 1d

**Active Jira**
- [FUSE-999](https://globalfreight.atlassian.net/browse/FUSE-999) [Observability] Instrument fuse.* operational metrics — still In Progress
- [FUSE-1092](https://globalfreight.atlassian.net/browse/FUSE-1092) — Code Review
- [FUSE-1093](https://globalfreight.atlassian.net/browse/FUSE-1093) — In Progress

**To raise**
- Why are 7 approved/green/mergeable PRs sitting unmerged for 3 days? Worth checking if he's deliberately batching a merge order or just hasn't gotten to it
- fuse-ui#184's Evidence still literally reads "N/A — no visual changes" — now 9 days stale, the evidence-bar conversation keeps getting carried
- New shift onto FUSE-1092/1093 (Shopify bulk-ingest rearchitecture) — worth understanding how this interacts with the shopify-connector-rearchitecture programme already in flight
- dedupe-service#110 still just needs a rebase — quick win to unblock, unchanged since 08-06

### Carried from last time
- [ ] Reply to his muninn-huginn SDK cookbook DM — open since 07-14 (verify not already superseded)

### Notes
- ✍️ 

## 2026-08-06
_09:30–10:00 · Southampton_Boardroom / Epsilon House Boardroom · agenda: "Fulfilment bug + batch ingestion"_

### Context

**Open PRs**
- [dedupe-service#110](https://github.com/gfs-bifrost/dedupe-service/pull/110) — [FUSE-999](https://globalfreight.atlassian.net/browse/FUSE-999) fuse.* metrics adoption — 🔴 blocked, merge conflicts (idle 2d) — per memory, this one just needs a rebase onto master
- [fuse-ui#184](https://github.com/gfs-bifrost/fuse-ui/pull/184) — FUSE-999 metrics catalog adoption — 🔴 blocked, merge conflicts + CI failing, ⚠️ stale (idle 6d) — also needs a rebase, and still pins `@gfs-bifrost/observability@^0.2.0` against the now-published 1.0.0
- [shopify-connector#186](https://github.com/gfs-bifrost/shopify-connector/pull/186) (stacked 1/2) + [#185](https://github.com/gfs-bifrost/shopify-connector/pull/185) (stacked 2/2) — FUSE-999 — both draft, CI green (21/21, 12/12)
- [shopify-connector#187](https://github.com/gfs-bifrost/shopify-connector/pull/187) — draft, no ticket, CI red on the fleet-wide dependency_audit/image_scan break
- [snap-adapter#164](https://github.com/gfs-bifrost/snap-adapter/pull/164) — draft, no ticket, same fleet-wide audit break

**Active Jira**
- [FUSE-999](https://globalfreight.atlassian.net/browse/FUSE-999) [Observability] Instrument `fuse.*` operational metrics — his umbrella task under epic FUSE-945

**To raise**
- **FUSE-999 rollout status**: 5 services merged + prod-deployed today (replay-service, collector, config-service, sftp-connector, fuse-mcp) — worth confirming with him directly since this is his umbrella ticket
- **The Datadog rewire is still outstanding** and is the real risk now — every merged service renamed its prod metrics on deploy, so any dashboard/monitor still on the old `*_service.*` names has gone blind. Worth agreeing who owns closing this before more services roll
- dedupe-service#110 and fuse-ui#184 both just need a rebase onto master to clear their conflicts — quick wins to unblock
- fuse-ui#184's Evidence section reads "N/A — no visual changes" — plausible for a constants-only Phase 1 PR, but worth agreeing what a substantiated "N/A" claim looks like (e.g. "no UI diff, tsc clean, N tests") vs a bare dismissal

### Carried from last time
- [ ] Reply to his muninn-huginn SDK cookbook DM — open since 07-14 (verify not already superseded)

### Notes
- ✍️ 

## 2026-07-28
_10:30–11:00 · Teams · no agenda on invite (Teams join blob only, normal)_

### Context

**Open PRs**
- [pkg-node#187](https://github.com/gfs-bifrost/pkg-node/pull/187) (FUSE-999 / FUSE-1012) — the observability framework: adaptor + `fuse.*` catalogue — non-draft, CI green, mergeable, **awaiting my review**
- [fapi#90](https://github.com/gfs-bifrost/fapi/pull/90) (FUSE-999) — draft, **stale at 7 working days idle**, CI red (`black-box-tests`, `Prepare Cache`, `image_scan`) — blocked waiting on `@gfs-bifrost/observability@0.2.0`, which is exactly what #187 publishes

**Closed since last time**
- [pkg-node#184](https://github.com/gfs-bifrost/pkg-node/pull/184) — the `FuseLogger` RFC/PoC — closed 2026-07-27 20:19, superseded by #187

**Active Jira**
- [FUSE-999](https://globalfreight.atlassian.net/browse/FUSE-999) [Observability] Instrument `fuse.*` operational metrics across Fuse services — In Progress — his most recent real activity, updated 07-27 18:13
- [FUSE-894](https://globalfreight.atlassian.net/browse/FUSE-894) [Config/UI] Add Pick/Pack outbound mapping settings — Ready for QA

**Owed by you**
- Review [pkg-node#187](https://github.com/gfs-bifrost/pkg-node/pull/187) — he DM'd asking for it and I said I'd prioritise it today
- Weigh in on his nightly-secops-scan-scoping proposal — carried ×5 since 07-21
- Approve his holiday request — carried ×3, now overdue

**To raise**
- #187 → #90 is a publish-gated chain, and #90 is the stalest non-bot PR in the fleet: reviewing and merging #187 unblocks his own work, so it's the highest-leverage thing I can do today
- `fuse.request.failure` has emitted **no datapoints for two consecutive days** — so Fuse API availability is currently **unverifiable, not 100%**, and monitor 302685705 only reads OK because it wraps the metric in `default_zero()`. If the metric has genuinely stopped reporting, that monitor cannot fire. This is squarely his FUSE-999 territory and the most useful thing to surface
- snap-adapter's `Code Quality` → `Matrix (audit)` job audits **dev** dependencies (it isn't `--prod`), so it gates on `vitest > vite > postcss` that the DevSecOps `--prod` gate ignores — a real inconsistency between the two gates, and relevant to his secops-scoping proposal
- The advisory remediation he'll have seen: 11 repos merged 07-27, and most took the **proper fix** (`pnpm-workspace.yaml` overrides / floor bumps to `brace-expansion >=5.0.8`) rather than an allowlist — worth confirming that's the pattern he wants standardised
- His new monitor ([FUSE][SFTP] errorHandler double-response guard, created 07-22) is sitting at No Data — expected for an error-path metric, but worth saying so it isn't mistaken for a gap

### Carried from last time
- [ ] Reply to his muninn-huginn SDK cookbook DM — open since 07-14, and arguably now superseded by the #187 package; close it out either way

### Notes
- ✍️ 

## 2026-07-14
_09:30–10:00 · Teams · no agenda on invite (normal)_

### Context

**Open PRs**
- [fuse-ui#165](https://github.com/gfs-bifrost/fuse-ui/pull/165) (FUSE-894) — 🟢 approved + CI green + mergeable, ready to merge today
- [config-service#184](https://github.com/gfs-bifrost/config-service/pull/184) (FUSE-894) — 🟢 approved + CI green + mergeable, ready to merge today
- [sftp-connector#204](https://github.com/gfs-bifrost/sftp-connector/pull/204) (FUSE-1000) — draft, observability-SDK migration in flight
- [fuse-ui#166](https://github.com/gfs-bifrost/fuse-ui/pull/166) (FUSE-1000) — draft, RGA ingress-mapping fix; held pending [[Tom Dunn]] confirming `location.owner`
- [fuse-mcp#8](https://github.com/gfs-bifrost/fuse-mcp/pull/8) (FUSE-894) — awaiting review, idle 4 days, no CI configured on this repo

**Owed by you**
- Reply to his muninn-huginn SDK cookbook DM (Huginn approaching RC) — still open

**To raise**
- Two PRs (fuse-ui#165, config-service#184) are ready to merge — good moment to land them today
- [[Tom Dunn]] has chased him directly across 4 separate RGA/SFTP-ingest email threads since 07-13 09:07 (JSON SFTP, CSV Gadgets, RGA CSV confirmations, RGA API feedback) — check his bandwidth/plan
- The P1/P2 alert debrief he asked for yesterday ("anyone on this, need me to jump on it?" DM, still unanswered directly) — Harry replied in #bifrost-notifications proposing a debrief "tomorrow" (= today)
- fuse-ui#166 status — is Tom's `location.owner` confirmation in yet?

### Carried from last time
- [ ] Reply to his muninn-huginn SDK cookbook DM

### Notes
- ✍️ 

## 2026-06-30

### Context

**Open PRs**
- [fapi#64](https://github.com/gfs-bifrost/fapi/pull/64) — adopt the three-signal observability SDK (logs + metrics + tracing); awaiting review, CI green, mergeable (idle 1d) — fapi is the pilot consumer hardening the SDK toward RC

**Active Jira**
- Nothing assigned & open (FUSE-976 SFTP provisioning no longer on his open list)

**Owed by you**
- Reply to his muninn-huginn SDK cookbook DM (Huginn approaching RC)

**Other context**
- ⚠️ **Breaking metric rename** rides fapi#64 (`rest_connector.* → fuse.*{service}`, `errors.* → fuse.errors{errorType}`) — Datadog dashboards/monitors must be rebuilt before prod cutover; worth flagging
- fapi#64 rebased onto FUSE-616 (types 7.0.0, businessId required) — so it carries the keystone bump too
- No agenda on the invite (normal for a 1:1)

### Carried from last time
- (no prior series note)

### Notes
- ✍️ 
