---
tags: [adhoc-task]
date: 2026-10-19
tldr: "orient's ctrl+k: pages now lead and are ranked; a ticket-shaped query (fuse-1232, any case) shows a Jira card; live on :3000"
session_id: 8f82d53a-e1be-4eb5-9f77-1b4a271218bd
status: done
---
# Quick switch: pages first, and Jira for tickets

## Outcome
Commit `48c90e8` in `~/projects/orient`, deployed. Pages ("Pages") lead the palette and are ranked (name prefix, word prefix, contains); empty groups draw no heading. When the whole term is a ticket key, a Ticket row shows at once and fills in from Jira via `/api/palette/ticket` (status chip, summary, assignee, priority, type, points, parent, age, PRs shipped per the ledger); Enter opens `/jira/KEY`, a second row opens Jira. Design note in `Engineering/orient/design.md` § Quick switch.
Owed: nothing. Only the FUSE project is treated as a ticket key (`lib/ticket-key.ts` PROJECTS).
