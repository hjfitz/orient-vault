---
tags: [adhoc-task]
date: 2026-10-09
tldr: "Escentric engraving thread: no new ticket needed, FUSE-1293 (line item properties) covers it; commented, moved to Sprint 16; verified canonical, fuse-ui and snap-adapter need no change"
session_id: 222547d4-184b-4a5a-9809-6924c3210210
status: open
---
# Scope Escentric engraving line attributes into Sprint 16

## Outcome
FUSE-1293 already covered reading Shopify line item properties; added the Escentric context as a comment and moved it to Sprint 16. Verified the rest of the chain already exists: canonical line `customisations[]`, fuse-ui line keys (free-text "From", no source field list), snap-adapter SHL attachments (`Type`=name, `AttachmentText`=value). No UI ticket raised (no gap found).
Owed: reply to ILG (Tom Dunn) that it is in Sprint 16; optional follow-up comment on FUSE-1293 (key case, constant `name` for VAS_INS2, Shopify standard template line rules).
