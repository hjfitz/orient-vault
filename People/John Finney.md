---
tags: [person]
role: Platform engineer
org: GFS
relationship: internal-partner
team: Carrier Integrations
reports_to: "[[Chris Mulder]]"
title: John Finney
---
# John Finney
> Cross-team platform engineering colleague — `ilg-platform`/`github-actions` steer, proposed weekly platform-eng sync.

## Coordinates
- Slack: <@U09A6VDKV5M>
- Email: john.finney@gfsdeliver.com

## Open loops
**I owe**
- [ ] apiky: answer his "Entra ID support?" question (may be aimed at John Clarke, so confirm) and chase the go-ahead to ship the green stacked PRs #5 to #10 and #12 — [thread](https://gfsdeliver-eng.slack.com/archives/C0C7YE2H6CE/p1791554784228559)
- [ ] Confirm a day for the proposed weekly platform-eng meeting — he's given his availability (Wed or Fri, not this Friday)
- [ ] Reply on `ilg-platform/github-actions` PR #8 steer + bulletin-move perms (carried from 07-09)
- [ ] Diagnose the secops-dep-node.yaml@0.2-bonbon dependency_audit failure on gfs-hybrid-services/slipway PR 14 — [job link](https://gfsdeliver-eng.slack.com/archives/D09A700MPCP/p1784712809940399)
	- likely cause: the fleet-wide new HIGH fast-uri advisories (GHSA-4c8g-83qw-93j6 / GHSA-v2hh-gcrm-f6hx, transitive via ajv > fast-uri) that tripped 8 gfs-bifrost repos' nightly DevSecOps scans last night — same audit, needs an allowlist entry

## Standing context
- ✍️

## Together (newest first)
- 2026-10-12 — Asked in the apiky group DM whether Entra ID support is coming. Unanswered, possibly aimed at John Clarke
- 2026-07-22 — handed over the slipway dep-audit failure for diagnosis (DM with the job link)
- 2026-07-21 — group DM (w/ Darren Rielly, Kyle): gave his availability for the weekly platform-eng meeting, waiting on me to pick a day

## Links
- (no dedicated 1:1 note yet)
