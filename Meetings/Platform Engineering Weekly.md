---
tags: [meeting]
series: Platform Engineering Weekly
title: Platform Engineering Weekly
---
# Platform Engineering Weekly

## 2026-07-29
_14:00–14:30 · Slack huddle · attendees: [[Darren Rielly]], [[Kyle Chandler]], [[John Finney]]_

### Context

**Agenda (from Confluence)**
- Walk the team through the new **Platform Engineering** space — what moved in from ECS, and how it's organised
- UI Toolkit updates — [[Darren Rielly]]
- **SecOps updates — Harry** (this is my item)

**My SecOps update — what to cover**
- `gfs-bifrost/secops` was transferred to `ilg-platform/secops-reporting` on 2026-07-28, same Cloud Run/Mongo infra — the commitment made to [[John Clarke]] to move it out of Bifrost "within this week" landed early
- The fleet-wide `brace-expansion` CVE remediation (11 repos, merged 07-27) went fully green in last night's nightly batch — first clean run since the advisory broke everything on 07-25
- Open thread: I've asked SRE for a dedicated platform-engineering GCP project — still pending
- `ilg-platform`'s org `GH_TOKEN` PAT was 403ing on GitHub Packages as of 07-27 ~14:38 UTC (`ui-toolkit` fetch failures) — worth checking whether it's been rotated, since [[Darren Rielly]]'s UI Toolkit update may intersect

**Owed by you**
- The IaC/SRE boundary model agreed with [[Kyle Chandler]] + Oliver Wilders (07-27 huddle) — sequence was: (1) protect main/gate apply/ref-scope WIF bindings, (2) merge PR#9+#10 and tag+pin all 10 module refs, (3) Terragrunt migration PR gated on a zero-diff plan — worth a status check with Kyle here

### Carried from last time
- (no prior occurrence note)

### Notes
- ✍️ 

