---
tags: [adhoc-task]
date: 2026-10-05
tldr: "Built snap-maintenance skill (Outlook → BLUF post in #bifrost-general as support bot, pinned) and its orient /maintenance page; bot gained pins:write; 08 Oct notice posted, pinned and recorded"
session_id: a5c13c58-d367-4e4e-83ac-c991a3ea7b9b
status: done
---
# Build the snap-maintenance announcement skill

## Outcome
Skill `~/.claude/skills/snap-maintenance/`: finds the newest planned Snap maintenance email, posts a BLUF notice to #bifrost-general as Bifrost Support Bot, pins it, unpins finished windows. Its state is one `Maintenance/<date>-<slug>.md` vault record per notice.
orient `/maintenance` (chord g z, Operations): Ahead/Past from those records. Commits eaebb76, 7e94941; type `maintenance`, classify rule 29; deployed.
Bot app A0C2EJ3FMFD gained `pins:write`. First notice: 08 Oct 15:00–16:30 BST (ts 1791190729.024759).
Backfilled 11 past notices into Maintenance/ (commit 37ae717 prints start-only windows as "from HH:MM").
Notice tracked per window (notified_at, announced_at; commits 2340ab2, 4885de6): three September migrations (DB2, DB1, DB5) reached the mailbox only after they had run.
ux-review pass done (commits 3e5106c, a21f29c): prod-scoped notice summary, notice bars, record bodies as bullets. Open nits: bar labels for the two Snap OS rows truncate alike; Env column is mostly dashes; relative ages show hours past 100 days.
