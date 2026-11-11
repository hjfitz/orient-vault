---
tags: [person]
role: Tech Services Manager
org: Tech Services
relationship: internal-partner
team: Tech Services
reports_to: "[[Oli Denton]]"
title: Oliver Wilders
---
# Oliver Wilders
> Tech Services side of the `ilg-tech-services` IaC work; optional attendee on Bifrost standup + Refinement.

## Coordinates
- Slack DM: `D0ALESDKC86`
- Email: (not captured)

## Open loops
**I owe**
- [ ] Reply on the five Merak portal gaps against TCA's DespatchCloud process (his 4 Nov DM), and get the ingestion UI to a decent state, then ping him to hand it over — [DM](https://gfsdeliver-eng.slack.com/archives/D0ALESDKC86/p1793815377255709)
- [ ] Take G6–G9 of the Merak portal and have the call today; send the plan, design docs and the US customer Jira epic (due 29 Oct) — [DM](https://gfsdeliver-eng.slack.com/archives/D0ALESDKC86/p1793205004687309)
- [ ] Hold the informal system design session on Fuse's database-per-service setup and what happens if a single database dies; it was due on 22 Oct and nothing shows it happened — [recording](http://localhost:3000/recordings/20261022-091411-e0eb)
- [ ] Send him the reading on database storage and retrieval (chapters 2, 3 and 5) — [recording](http://localhost:3000/recordings/20261022-091411-e0eb)
- [ ] Feed the US data-residency requirement into the GCP project creation request, with Ronnie — [recording](http://localhost:3000/recordings/20261022-091411-e0eb)
- [ ] Confirm the 10:00 huddle he proposed for this morning — I replied "I think 10 works, but I'll get back to you" and never came back — [Slack](https://gfsdeliver-eng.slack.com/archives/D0ALESDKC86/p1785773977979209)
- [x] Run the tech-services IaC walkthrough he asked for — held 10:48–11:07 Mon 27 Jul, no canvas, notes typed in the thread

**Owed to me**
- [ ] FedEx test account is still on sandbox: test runs on Thursday 12 Nov and a live test order next week (his DM, to which I replied on 10 Nov at 16:43 that this is my focus for the week) — [[Digests/2026-11/2026-11-11]]
- [ ] Real automated SRE guardrails and protected branches — one of the four conditions the teams' looser deploy permissions are contingent on
- [ ] Step 2 of the agreed sequence: merge #9 and #10, tag the module branch, pin all ten module refs
- [ ] The link to the PR he flagged for review on 07-13 — I asked for it and it never came

## Standing context
- Works the `ilg-tech-services` IaC with [[Kyle Chandler]] — the repo I security-reviewed on 07-25
- Optional attendee on the Bifrost standup and [[Meetings/Bifrost Refinement]]
- **Agreed ownership model** (27/07 huddle): SRE guards the big boundaries — networks, org policy, project walls — and each team owns risk inside its own project
- Teams accept slightly looser deploy permissions on four conditions, including real automated SRE guardrails and protected branches
- **Agreed sequence**: (1) protect `main`, gate the apply, ref-scope the WIF bindings, drop unneeded permissions; (2) merge #9 and #10, tag the module branch, pin all ten module refs; (3) then the Terragrunt migration PR, with a zero-diff plan as the pass/fail gate
- My two blocking concerns on record: `run.sh` wipes `backend.tf` and can nuke infra (Terragrunt avoids this), and modules living on various branches means commit-and-apply can wipe infra (git tagging resolves it)
- ✍️ 

## Together (newest first)
- 2026-11-11 — 09:30 Merak Tech Catchup today → [[Digests/2026-11/2026-11-11]]
- 2026-11-11 — He proposes FedEx test runs on Thursday 12 Nov and a live test order next week
- 2026-11-11 — He also proposes a CarrierService XML change and a configurable route list
- 2026-11-04 — Merak and TCA huddle (notes posted by Oli in #merak-tech-twats): Wilders owes me the replacement for Alex's manual database mapping and the redone Google rollout plan → [notes](https://gfsdeliver-eng.slack.com/archives/C0CASK7S4M9/p1793797801500129)
- 2026-11-02 — 09:30 Merak Tech Catchup today; you still owe him the portal plan, design docs and epic (due 29 Oct)
- 2026-10-29 — Asked you to take G6–G9 (logins, manifest, printing, view) and a call today; 28 Oct recordings: you owe the plan, design docs and the Jira epic for the US customer UI
- 2026-10-22 — 18-minute call about the new system's database: you pushed back on choosing Postgres before there is a design, agreed the US GCP region must go into the project request now, and planned a system design session that day (not saved to the meeting notes)
- 2026-07-28 — the tech-services IaC huddle happened (10:48–11:07 Mon 27 Jul, no canvas, notes typed in thread) and settled the ownership model, the four conditions for looser team deploy permissions, and the three-step sequence ending in a Terragrunt migration PR gated on a zero-diff plan, with my `run.sh`/`backend.tf` and untagged-module-branch concerns both recorded as blocking
- 2026-07-27 — asked (group DM w/ [[Kyle Chandler]]) for a huddle after his InPost meeting to go through the tech-services IaC; I offered 10:30–11:00 today
- 2026-07-13 — flagged a PR for review in a DM; I replied asking for the link and it was never supplied

## Links
- (no Fuse Jira / GitHub captured)
