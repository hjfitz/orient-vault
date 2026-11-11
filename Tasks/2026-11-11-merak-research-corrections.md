---
tags: [adhoc-task]
date: 2026-11-11
tldr: "Resumed the Merak replacement-pages handover on rc-hjf and, on Harry's approval, applied four edits to MPK pages: Polling Connectors v12, Tracking Events and Webhooks v5, ECM Platform v3 and the Tracking group page v3. No feedback was owed. Only access-gated answers remain. Also wrote the deep-research skill (uncommitted, in orient-writers) and built the book \"Following a Consignment\" from the MPK pages (local, confidential)."
session_id: d94837dd-a7bc-4aac-99e6-6a3f03c9f046
status: done
---
# Apply the owed Merak research corrections

## Outcome
Resumed [[Handovers/2026-11-09-merak-replacement-pages]] on `rc-hjf` (live MPK tree matched the record) and applied what Harry approved on 2026-11-11, all as ADF through the MCP update tool with no API token. Polling Connectors (353697880, v12) now puts the `FindOneAndUpdate` lease in batch-creator. Tracking Events and Webhooks (355074077, v5) now says `raw_tracking.v1` carries the raw code only, counts the delivered definitions as researched and says `tracking-core` keeps its own mapping (the last two on Harry's yes). ECM Platform (357662721, v3) points at Central Firebird. The Tracking group page (357597186, v3) lost two owed-correction notes the edits made stale. Each page was re-fetched, and the Lucid macro on Polling Connectors survived. Vault copies and [[Systems/ecm/known-context]] match.

Owed: access-gated answers only, as listed in the handover. The ConfigMap claim on Polling Connectors is still an owed correction.

Also wrote the `deep-research` skill at `~/projects/orient-writers/skills/deep-research/` (SKILL.md plus five references), linked into `~/.claude/skills/deep-research`. It codifies the loop this research ran: a short grill, waves of right-sized agents, a digest and one-click steer after each wave, vault layers first, pages only on request. A two-agent review-panel found five real defects and five leaks of real material in its first draft. All were fixed and re-checked with a grep. The skill is **uncommitted** in orient-writers, which also holds other uncommitted work and has diverged from origin, so it reaches other machines only once Harry commits it. It has not yet been run on a live topic.

Also built the book from the Merak research pages, with `docs-to-epub`: **"Following a Consignment"**, at `~/books/gfs-delivery-stack/` (EPUB in `build/following-a-consignment.epub`, about 58,250 words, 17 chapter files, 13 figures, 14 open gaps). Harry chose one hypothetical parcel as the thread. EPUBCheck 5.4.0 VALID. A citation audit checked about 1,500 claims against the live pages and changed about 190. It is marked confidential, local only, and was not sent, published or committed. Not opened on a real e-reader. Owed: Harry's read of the book. The pages that still say older things are listed in `notes/pages-to-fix.md` (nothing edited on Confluence). The skill findings from the first Confluence run are in `SKILL-FEEDBACK.md` beside the book, for the `docs-to-epub` handover (`Handovers/2026-11-11-docs-to-epub`), whose record belongs to another session and was not edited.
