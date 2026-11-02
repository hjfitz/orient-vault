---
tags: [adhoc-task]
date: 2026-10-08
tldr: "Built the self-contained create-carrier-proxy-epic skill and used it to file Veho Onboarding (CID-335) with 19 Stories (CID-336–354); Stories sit in To Do because Refining isn't in the CID workflow"
session_id: 62856fa0-7d71-4a74-800b-0dacd3a38b8f
status: open
---
# Build the create-carrier-proxy-epic skill and file the Veho epic

## Outcome
New self-contained skill at `~/code/.claude/skills/create-carrier-proxy-epic/` with the FUSE ticket and epic formats written in, ready to hand to someone without the other skills. Its flow is contract → static-payload stub → implementation, with a sign-off gate before any Jira write.
First real run, on the Veho spec v0.1: epic CID-335 "Veho Onboarding" and 19 Stories, CID-336 to CID-354. All 67 VEHO-* requirement IDs map to a ticket except RET-002 (blocked) and RET-003 (not v1). 20 Blocks links, read back and correct.
Owed: the Stories are in To Do, because Refining (status 10262) isn't in the CID workflow; a Jira admin has to add it, then they can be transitioned. The spec is still an unreviewed draft.
