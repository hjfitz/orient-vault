---
tags: [person]
role: CTO
org: GFS
relationship: internal-partner
reports_to: "[[Peter Liu]]"
title: John Clarke
---
# John Clarke
> GFS colleague; built the Sec Ops dependency-audit reporter and wants to roll it out across teams.

## Coordinates
- Slack: <@U056A91JPV2>
- Email: john.clarke@gfsdeliver.com

## Open loops
**I owe**
- [ ] Give him, [[Darren Rielly]] and [[Oli Denton]] your review of the SRE VM-image work: what exists and which defaults are missing — [group DM](https://gfsdeliver-eng.slack.com/archives/C0A33D92C76/p1793981617640289)
- [x] **Migrate the SecOps work out of Bifrost into the platform-engineering org "within this week"** — done early: `gfs-bifrost/secops` transferred to `ilg-platform/secops-reporting` on 07-28
- [ ] Get SRE to provision a dedicated platform-engineering GCP project — asked, still pending
- [ ] Review [secops#2](https://github.com/gfs-bifrost/secops/pull/2) (Neon support) + give the go/no-go on rolling the Sec Ops reporter out — CI red, now idle ~25 days

**Owed to me**
- [ ] Go/no-go on rolling the Sec Ops reporter out to other teams + his offer to raise a PR wiring it up with EntraID auth — [DM](https://gfsdeliver-eng.slack.com/archives/D0990E3U2F4/p1782979254853619)

## Standing context
- Owns the Sec Ops reporting tooling; looking to expand it beyond his team
- `gfs-bifrost/secops` has already been transferred to `ilg-platform/secops-reporting` (GitHub confirmed the transfer) — the repo move is done, the rest of the migration isn't
- The org `GH_TOKEN` PAT started 403ing on GitHub Packages ~2026-07-27 14:38 UTC and is holding a secops-reporting Deploy — needs human rotation
- ✍️ 

## Together (newest first)
- 2026-07-29 — the SecOps-migration commitment landed early: `gfs-bifrost/secops` was transferred to `ilg-platform/secops-reporting` yesterday (07-28), closing out most of this loop; I've since asked SRE for a dedicated platform-engineering GCP project, still pending
- 2026-07-28 — asked in the group DM with [[Oli Denton]] how long it would take to move the SecOps work out of Bifrost into the platform-engineering org, and I committed to migrating it within this week — a live deadline, with the repo transfer to `ilg-platform/secops-reporting` already done and his own secops#2 still idle ~25 days on red CI
- 2026-07-20 — [secops#2](https://github.com/gfs-bifrost/secops/pull/2) still awaiting my review, now well past 2 weeks stale; secops' own nightly `DevSecOps Scans` hit a fresh `startup_failure` overnight — self-inflicted from Harry's own 07-17 SecOps 0.2 breaking-change commit, not John's PR
- 2026-07-10 — John requested my review on [secops#2](https://github.com/gfs-bifrost/secops/pull/2) (Neon support); still waiting on my go/no-go for the Sec Ops reporter rollout + EntraID-auth PR; praised the dup-shipments PIR
- 2026-07-07 — secops nightly DevSecOps red again (a `gitleaks` hit in the secops repo — real-leak vs action-error unconfirmed); folds into the secops#2 review + go/no-go I owe
- 2026-07-06 — his [secops#2](https://github.com/gfs-bifrost/secops/pull/2) (Neon support) is up for my review (CI red — gitleaks/ui checks/image-scan); flagged an "incoming mini-PR @Fitz" in the Oli/Darren group DM (07-03)
- 2026-07-02 — DM: proposed rolling the Sec Ops reporter out more widely + offered a PR to set it up with EntraID auth (awaiting my answer)

## Links
- (GFS internal — resolve Jira/GitHub if he starts contributing to Fuse repos)
